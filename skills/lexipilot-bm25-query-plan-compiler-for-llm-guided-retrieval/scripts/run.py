#!/usr/bin/env python3
"""LexiPilot: compile BM25-friendly retrieval plans for local text corpora."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


DEFAULT_QUESTION = (
    "Which notes compare BM25, SPLADE, and HyDE for exact technical "
    "identifiers like arXiv:2305.10403?"
)

SAMPLE_DOCS = {
    "retrieval-notes.md": """# Lexical Retrieval Notes
aliases:
  - BM25 planning
  - sparse retrieval

BM25 is useful when exact wording, RFC 9110 references, wiki links like
[[SPLADE]], and identifiers such as arXiv:2305.10403 need to survive search.

## Query planning
An LLM can propose rare terms, exclusions, and title candidates before lexical
search. This is planner mode, not answer mode.
""",
    "dense-retrieval.md": """# Dense Retrieval Caveats
aliases:
  - embedding retrieval

Dense vectors help with semantic matching, but they may smooth away sparse
signals like CVE-2024-3094, function names, or the original title of a paper.
HyDE can improve recall, but it should be compared with BM25 baselines.
""",
    "paper-index.txt": """Paper index
SPLADE: sparse lexical and expansion model.
HyDE: hypothetical document expansion for retrieval.
arXiv:2305.10403 appears in experiments that compare lexical and dense search.
""",
}

STOPWORDS = {
    "a",
    "about",
    "after",
    "all",
    "also",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "before",
    "by",
    "can",
    "compare",
    "compared",
    "does",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "it",
    "like",
    "local",
    "need",
    "not",
    "of",
    "on",
    "or",
    "should",
    "than",
    "that",
    "the",
    "their",
    "them",
    "these",
    "this",
    "to",
    "use",
    "used",
    "using",
    "when",
    "where",
    "which",
    "with",
    "without",
}

WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_./:+#-]{1,}")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|([^\]]+))?\]\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$", re.MULTILINE)
IDENTIFIER_RES = [
    re.compile(r"\b(?:arXiv:)?\d{4}\.\d{4,5}(?:v\d+)?\b", re.IGNORECASE),
    re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE),
    re.compile(r"\bRFC\s*-?\s*\d{3,5}\b", re.IGNORECASE),
    re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.IGNORECASE),
    re.compile(r"\bPEP\s*-?\s*\d{3,5}\b", re.IGNORECASE),
]


@dataclass(frozen=True)
class Document:
    path: str
    text: str

    @property
    def title(self) -> str:
        match = HEADING_RE.search(self.text)
        if match:
            return clean_phrase(match.group(2))
        return Path(self.path).stem.replace("-", " ").replace("_", " ").title()


def clean_phrase(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().strip("\"'`")).strip()


def unique(values: Iterable[str], limit: int | None = None) -> list[str]:
    seen = set()
    out = []
    for raw in values:
        value = clean_phrase(str(raw))
        key = value.lower()
        if not value or key in seen:
            continue
        seen.add(key)
        out.append(value)
        if limit is not None and len(out) >= limit:
            break
    return out


def tokenize(text: str) -> list[str]:
    tokens = []
    for match in WORD_RE.finditer(text):
        token = match.group(0).strip(".,;:!?()[]{}<>\"'`").lower()
        if len(token) < 2 or token in STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def extract_identifiers(text: str) -> list[str]:
    found = []
    for pattern in IDENTIFIER_RES:
        found.extend(match.group(0) for match in pattern.finditer(text))
    return unique(found)


def extract_headings(docs: list[Document]) -> list[str]:
    headings = []
    for doc in docs:
        headings.append(doc.title)
        headings.extend(match.group(2) for match in HEADING_RE.finditer(doc.text))
    return unique(headings, limit=40)


def extract_wikilinks(docs: list[Document]) -> list[str]:
    values = []
    for doc in docs:
        for target, alias in WIKILINK_RE.findall(doc.text):
            values.append(target)
            if alias:
                values.append(alias)
    return unique(values, limit=40)


def extract_aliases(docs: list[Document]) -> list[str]:
    aliases = []
    alias_block = re.compile(
        r"(?im)^(?:aliases?|aka)\s*:\s*(?P<value>.+(?:\n\s*-\s*.+)*)"
    )
    for doc in docs:
        for match in alias_block.finditer(doc.text):
            value = match.group("value")
            for line in value.splitlines():
                cleaned = re.sub(r"^\s*-\s*", "", line).strip()
                cleaned = cleaned.strip("[]\"'")
                if cleaned:
                    aliases.append(cleaned)
    return unique(aliases, limit=40)


def extract_technical_terms(text: str) -> list[str]:
    patterns = [
        r"\b[A-Z]{2,}(?:-[A-Z0-9]+)*\b",
        r"\b[a-z]+(?:_[a-z0-9]+)+\b",
        r"\b[A-Za-z]+(?:\.[A-Za-z0-9_]+){1,}\b",
        r"\b[A-Za-z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*\b",
        r"\b[A-Za-z]+-[A-Za-z0-9-]+\b",
    ]
    found = []
    for pattern in patterns:
        found.extend(re.findall(pattern, text))
    return unique(found, limit=50)


def extract_exclusions(question: str) -> list[str]:
    exclusions = []
    pattern = re.compile(
        r"\b(?:not|without|exclude|excluding|except|avoid)\s+([A-Za-z0-9_.:+#-]+)",
        re.IGNORECASE,
    )
    exclusions.extend(match.group(1) for match in pattern.finditer(question))
    return unique(exclusions, limit=10)


def load_documents(corpus: str | None) -> tuple[list[Document], str]:
    if not corpus:
        return [Document(path=path, text=text) for path, text in SAMPLE_DOCS.items()], "sample"

    root = Path(corpus)
    if not root.exists():
        raise FileNotFoundError(f"Corpus path not found: {corpus}")

    paths: list[Path]
    if root.is_file():
        paths = [root]
        base = root.parent
    else:
        base = root
        paths = sorted(
            p
            for p in root.rglob("*")
            if p.is_file() and p.suffix.lower() in {".md", ".markdown", ".txt"}
        )

    docs = []
    for path in paths:
        try:
            rel_path = str(path.relative_to(base))
        except ValueError:
            rel_path = path.name
        docs.append(Document(path=rel_path, text=path.read_text(encoding="utf-8", errors="replace")))

    if not docs:
        raise ValueError("No Markdown or text files found in corpus.")

    return docs, corpus


def compute_idf(docs: list[Document]) -> dict[str, float]:
    doc_freq: Counter[str] = Counter()
    for doc in docs:
        doc_freq.update(set(tokenize(doc.text)))
    total = max(len(docs), 1)
    return {term: math.log((total + 1) / (freq + 1)) + 1 for term, freq in doc_freq.items()}


def rare_question_terms(question: str, docs: list[Document], limit: int = 16) -> list[str]:
    idf = compute_idf(docs)
    scored = []
    for term in set(tokenize(question)):
        scored.append((idf.get(term, math.log(len(docs) + 1) + 1), term))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [term for _, term in scored[:limit]]


def corpus_rare_terms(question: str, docs: list[Document], limit: int = 12) -> list[str]:
    question_tokens = set(tokenize(question))
    idf = compute_idf(docs)
    scored = []
    for doc in docs:
        counts = Counter(tokenize(doc.text))
        for term, count in counts.items():
            if term in STOPWORDS:
                continue
            if term in question_tokens or any(term.startswith(q) or q.startswith(term) for q in question_tokens):
                scored.append((count * idf.get(term, 1.0), term))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return unique((term for _, term in scored), limit=limit)


def split_question(question: str) -> list[str]:
    normalized = re.sub(r"\b(?:versus|vs\.?|compared with|compared to)\b", " and ", question, flags=re.IGNORECASE)
    chunks = re.split(r"\s+\band\b\s+|[?;]", normalized)
    cleaned = []
    for chunk in chunks:
        words = tokenize(chunk)
        if words:
            cleaned.append(" ".join(words[:8]))
    return unique(cleaned, limit=6)


def relevant_phrases(question: str, candidates: Iterable[str], limit: int = 12) -> list[str]:
    q_terms = set(tokenize(question))
    scored = []
    for phrase in candidates:
        terms = set(tokenize(phrase))
        overlap = len(q_terms & terms)
        has_substring = any(term in phrase.lower() for term in q_terms)
        if overlap or has_substring:
            scored.append((overlap, len(phrase), phrase))
    scored.sort(key=lambda item: (-item[0], item[1], item[2].lower()))
    return unique((phrase for _, _, phrase in scored), limit=limit)


def fts_quote(term: str) -> str:
    escaped = clean_phrase(term).replace('"', '""')
    return f'"{escaped}"'


def make_query(terms: Iterable[str], limit: int = 12) -> str:
    selected = unique((term for term in terms if term), limit=limit)
    return " OR ".join(fts_quote(term) for term in selected)


def compile_plan(question: str, docs: list[Document], source: str, top_k: int, run_search: bool) -> dict[str, Any]:
    all_text = "\n\n".join(doc.text for doc in docs)
    headings = extract_headings(docs)
    wikilinks = extract_wikilinks(docs)
    aliases = extract_aliases(docs)
    identifiers = unique(extract_identifiers(question) + extract_identifiers(all_text), limit=30)
    technical_terms = unique(extract_technical_terms(question) + extract_technical_terms(all_text), limit=40)
    rare_terms = unique(rare_question_terms(question, docs) + corpus_rare_terms(question, docs), limit=24)
    title_candidates = relevant_phrases(question, headings + aliases + wikilinks, limit=12)
    exclusions = extract_exclusions(question)

    query_specs = [
        {
            "name": "broad_recall",
            "purpose": "High-recall OR query from rare question and corpus terms.",
            "query": make_query(rare_terms + technical_terms[:6] + identifiers[:4], limit=14),
        },
        {
            "name": "titles_aliases",
            "purpose": "Search likely titles, headings, aliases, and wiki link labels.",
            "query": make_query(title_candidates + aliases + wikilinks, limit=12),
        },
        {
            "name": "identifiers",
            "purpose": "Search exact paper, standards, vulnerability, or proposal identifiers.",
            "query": make_query(identifiers, limit=10),
        },
        {
            "name": "technical_terms",
            "purpose": "Search acronyms, code-like terms, hyphenated concepts, and symbols.",
            "query": make_query(technical_terms, limit=12),
        },
    ]
    query_specs = [spec for spec in query_specs if spec["query"]]

    section_queries = []
    for idx, chunk in enumerate(split_question(question), start=1):
        terms = unique(tokenize(chunk) + [term for term in technical_terms if term.lower() in chunk], limit=8)
        section_queries.append(
            {
                "label": f"section_{idx}",
                "focus": chunk,
                "query": make_query(terms, limit=8),
                "terms": terms,
            }
        )

    plan: dict[str, Any] = {
        "question": question,
        "corpus": {
            "source": source,
            "document_count": len(docs),
            "documents": [doc.path for doc in docs],
        },
        "planner": {
            "mode": "local-heuristic-standard-library",
            "external_api_key_detected": bool(os.getenv("OPENAI_API_KEY") or os.getenv("LEXIPILOT_API_KEY")),
            "note": "This reference implementation does not call external services.",
        },
        "signals": {
            "rare_terms": rare_terms,
            "title_candidates": title_candidates,
            "headings": headings,
            "wikilinks": wikilinks,
            "aliases": aliases,
            "identifiers": identifiers,
            "technical_terms": technical_terms,
            "exclusion_terms": exclusions,
        },
        "section_queries": section_queries,
        "queries": query_specs,
        "search_results": [],
    }

    if run_search:
        plan["search_results"] = search_with_sqlite_fts(docs, query_specs + section_queries, top_k=top_k)

    return plan


def search_with_sqlite_fts(docs: list[Document], queries: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
    try:
        connection = sqlite3.connect(":memory:")
        connection.execute("CREATE VIRTUAL TABLE docs USING fts5(path UNINDEXED, title, body)")
    except sqlite3.Error as exc:
        return [{"warning": f"SQLite FTS5 is not available: {exc}"}]

    with connection:
        connection.executemany(
            "INSERT INTO docs(path, title, body) VALUES (?, ?, ?)",
            [(doc.path, doc.title, doc.text) for doc in docs],
        )

    results = []
    for spec in queries:
        query = spec.get("query", "")
        if not query:
            continue
        try:
            rows = connection.execute(
                """
                SELECT
                    path,
                    title,
                    snippet(docs, 2, '[', ']', ' ... ', 16) AS snippet,
                    bm25(docs) AS bm25_score
                FROM docs
                WHERE docs MATCH ?
                ORDER BY bm25_score
                LIMIT ?
                """,
                (query, top_k),
            ).fetchall()
        except sqlite3.Error as exc:
            results.append({"query_name": spec.get("name") or spec.get("label"), "query": query, "error": str(exc)})
            continue

        results.append(
            {
                "query_name": spec.get("name") or spec.get("label"),
                "query": query,
                "matches": [
                    {
                        "path": path,
                        "title": title,
                        "score": round(float(score), 6),
                        "snippet": snippet,
                    }
                    for path, title, snippet, score in rows
                ],
            }
        )

    return results


def read_question(args: argparse.Namespace) -> str:
    if args.question_file:
        return Path(args.question_file).read_text(encoding="utf-8").strip()
    if args.question:
        return args.question.strip()
    return DEFAULT_QUESTION


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compile a BM25-friendly JSON retrieval plan for Markdown or text files."
    )
    parser.add_argument("--question", "-q", help="Natural-language retrieval question.")
    parser.add_argument("--question-file", help="Text file containing the retrieval question.")
    parser.add_argument("--corpus", "-c", help="Directory or file containing .md, .markdown, or .txt documents.")
    parser.add_argument("--out", "-o", help="Write JSON plan to this file.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of matches per query when search is enabled.")
    parser.add_argument("--search", action="store_true", help="Run generated queries with SQLite FTS5.")
    parser.add_argument("--no-search", action="store_true", help="Disable default sample search execution.")
    parser.add_argument("--queries-only", action="store_true", help="Print query strings instead of full JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        question = read_question(args)
        docs, source = load_documents(args.corpus)
        run_search = args.search or (not args.corpus and not args.no_search)
        plan = compile_plan(question, docs, source, top_k=max(args.top_k, 1), run_search=run_search)
    except Exception as exc:
        print(f"lexipilot error: {exc}", file=sys.stderr)
        return 1

    if args.queries_only:
        output = "\n".join(spec["query"] for spec in plan["queries"])
    else:
        output = json.dumps(plan, indent=2, ensure_ascii=False)

    if args.out:
        Path(args.out).write_text(output + "\n", encoding="utf-8")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
