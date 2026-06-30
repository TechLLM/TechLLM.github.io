#!/usr/bin/env python3
"""SparrowPlan reference CLI: compile questions into BM25 query plans."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple


VERSION = "0.1.0"

DEFAULT_QUESTION = "How can agents improve BM25 retrieval over Markdown documentation without embeddings?"

STOPWORDS = {
    "a",
    "about",
    "after",
    "all",
    "also",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "do",
    "does",
    "for",
    "from",
    "had",
    "has",
    "have",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "our",
    "over",
    "should",
    "than",
    "that",
    "the",
    "their",
    "then",
    "there",
    "this",
    "to",
    "use",
    "using",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
    "without",
    "would",
}

EXPANSIONS = {
    "agent": ["planner", "workflow"],
    "agentic": ["agent", "planner", "workflow"],
    "bm25": ["lexical", "sparse"],
    "corpus": ["documents", "collection"],
    "document": ["markdown", "text"],
    "embeddings": ["dense", "vector"],
    "lexical": ["bm25", "sparse"],
    "markdown": ["documentation", "docs"],
    "query": ["terms", "search"],
    "rag": ["retrieval", "grounding"],
    "rare": ["specific", "low-frequency"],
    "retrieval": ["search", "ranking"],
    "sparse": ["bm25", "lexical"],
}

SAMPLE_DOCS = [
    {
        "id": "sample/guides/bm25.md",
        "collection": "guides",
        "text": """# BM25 Retrieval

BM25 is a sparse lexical ranking function. It rewards exact term overlap, rare document terms, and moderate term frequency. For local documentation search, BM25 can be easier to debug than dense embeddings.

Good query plans keep weighted terms short, preserve rare identifiers, and avoid long natural-language prompts.""",
    },
    {
        "id": "sample/guides/agentic-rag.md",
        "collection": "guides",
        "text": """# Agentic RAG Planning

Agentic RAG systems can separate planning from retrieval execution. A planner can select collections, compile query terms, inspect results, and request follow-up searches.

Transparent retrieval plans are easier to log, test, and tune than one-off generated search strings.""",
    },
    {
        "id": "sample/notes/passage-search.txt",
        "collection": "notes",
        "text": """Passage search is a coarse-to-fine step. First rank collections, then rank documents, then split promising documents into passages.

Short passages often surface high-signal evidence for answer generation and reduce context waste.""",
    },
    {
        "id": "sample/notes/rare-terms.txt",
        "collection": "notes",
        "text": """Rare terms improve lexical precision when they are meaningful. Product names, error codes, method names, and acronyms can sharply narrow BM25 results.

Stopwords and vague verbs should usually receive little or no query weight.""",
    },
]


@dataclass(frozen=True)
class Document:
    doc_id: str
    collection: str
    text: str


@dataclass(frozen=True)
class Unit:
    unit_id: str
    text: str
    collection: str
    doc_id: str


def tokenize(text: str, stopwords: Optional[Set[str]] = None) -> List[str]:
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]*", text.lower())
    if stopwords is None:
        return tokens
    return [token for token in tokens if token not in stopwords and len(token) > 1]


def load_question(args: argparse.Namespace) -> str:
    if args.question_file:
        return Path(args.question_file).read_text(encoding="utf-8").strip()
    if args.question:
        return args.question.strip()
    return DEFAULT_QUESTION


def load_documents(corpus_path: Optional[str]) -> Tuple[List[Document], str]:
    if not corpus_path:
        return [Document(item["id"], item["collection"], item["text"]) for item in SAMPLE_DOCS], "sample"

    root = Path(corpus_path)
    if not root.exists():
        raise FileNotFoundError(f"Corpus path not found: {corpus_path}")

    files: List[Path]
    if root.is_file():
        files = [root] if root.suffix.lower() in {".md", ".txt"} else []
        base = root.parent
    else:
        files = sorted(path for path in root.rglob("*") if path.suffix.lower() in {".md", ".txt"})
        base = root

    docs: List[Document] = []
    for path in files:
        rel = path.relative_to(base)
        parts = rel.parts
        collection = parts[0] if len(parts) > 1 else "root"
        text = path.read_text(encoding="utf-8", errors="replace")
        docs.append(Document(rel.as_posix(), collection, text))

    if not docs:
        raise ValueError("Corpus must contain at least one .md or .txt file.")
    return docs, "local"


def document_frequency(units: Sequence[Unit]) -> Dict[str, int]:
    df: Dict[str, int] = defaultdict(int)
    for unit in units:
        for token in set(tokenize(unit.text, STOPWORDS)):
            df[token] += 1
    return dict(df)


def weighted_query_plan(question: str, docs: Sequence[Document]) -> Dict[str, object]:
    doc_units = [Unit(doc.doc_id, doc.text, doc.collection, doc.doc_id) for doc in docs]
    df = document_frequency(doc_units)
    total_docs = max(1, len(docs))
    question_terms = tokenize(question, STOPWORDS)
    counts = Counter(question_terms)

    weighted_terms = []
    for term, count in sorted(counts.items()):
        doc_count = df.get(term, 0)
        idf = math.log(1 + (total_docs - doc_count + 0.5) / (doc_count + 0.5))
        corpus_boost = 1.0 + min(idf, 2.0) * 0.45
        repeat_boost = 1.0 + min(count - 1, 2) * 0.25
        oov_boost = 1.25 if doc_count == 0 else 1.0
        weight = round(corpus_boost * repeat_boost * oov_boost, 3)
        reason = "rare_or_specific" if doc_count <= max(1, total_docs // 4) else "query_term"
        if doc_count == 0:
            reason = "out_of_corpus_candidate"
        weighted_terms.append(
            {
                "term": term,
                "weight": weight,
                "question_frequency": count,
                "document_frequency": doc_count,
                "reason": reason,
            }
        )

    weighted_terms.sort(key=lambda item: (-item["weight"], item["term"]))

    rare_candidates = [
        item
        for item in weighted_terms
        if item["document_frequency"] <= max(1, math.ceil(total_docs * 0.25))
    ][:10]

    expansion_hints = []
    seen_expansions = set(question_terms)
    for term in question_terms:
        for expansion in EXPANSIONS.get(term, []):
            if expansion not in seen_expansions:
                seen_expansions.add(expansion)
                expansion_hints.append(
                    {
                        "source_term": term,
                        "candidate": expansion,
                        "weight_hint": 0.55,
                        "reason": "conservative_domain_expansion",
                    }
                )

    return {
        "weighted_terms": weighted_terms,
        "rare_term_candidates": rare_candidates,
        "expansion_hints": expansion_hints[:12],
        "bm25_query": " ".join(f'{item["term"]}^{item["weight"]}' for item in weighted_terms),
        "stages": [
            "rank_collections",
            "rank_documents_within_top_collections",
            "split_top_documents_and_rank_passages",
        ],
    }


class BM25Index:
    def __init__(self, units: Sequence[Unit]) -> None:
        self.units = list(units)
        self.term_frequencies = [Counter(tokenize(unit.text, STOPWORDS)) for unit in self.units]
        self.lengths = [sum(tf.values()) for tf in self.term_frequencies]
        self.average_length = sum(self.lengths) / max(1, len(self.lengths))
        self.df = document_frequency(self.units)
        self.total = len(self.units)

    def idf(self, term: str) -> float:
        doc_count = self.df.get(term, 0)
        return math.log(1 + (self.total - doc_count + 0.5) / (doc_count + 0.5))

    def score(self, weighted_terms: Sequence[Dict[str, object]], index: int) -> float:
        k1 = 1.5
        b = 0.75
        tf = self.term_frequencies[index]
        doc_len = self.lengths[index] or 1
        score = 0.0
        for item in weighted_terms:
            term = str(item["term"])
            freq = tf.get(term, 0)
            if freq == 0:
                continue
            weight = float(item["weight"])
            denom = freq + k1 * (1 - b + b * doc_len / max(self.average_length, 1.0))
            score += weight * self.idf(term) * (freq * (k1 + 1)) / denom
        return score

    def rank(self, weighted_terms: Sequence[Dict[str, object]], limit: int) -> List[Tuple[Unit, float]]:
        scored = [(unit, self.score(weighted_terms, index)) for index, unit in enumerate(self.units)]
        scored.sort(key=lambda item: (-item[1], item[0].unit_id))
        return [(unit, score) for unit, score in scored[:limit] if score > 0]


def collection_units(docs: Sequence[Document]) -> List[Unit]:
    grouped: Dict[str, List[str]] = defaultdict(list)
    for doc in docs:
        grouped[doc.collection].append(doc.text)
    return [
        Unit(f"collection:{collection}", "\n\n".join(texts), collection, f"collection:{collection}")
        for collection, texts in sorted(grouped.items())
    ]


def document_units(docs: Sequence[Document], collections: Optional[Set[str]] = None) -> List[Unit]:
    selected = docs if not collections else [doc for doc in docs if doc.collection in collections]
    return [Unit(doc.doc_id, doc.text, doc.collection, doc.doc_id) for doc in selected]


def split_passages(text: str, size: int) -> List[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    passages: List[str] = []
    for paragraph in paragraphs:
        tokens = paragraph.split()
        if len(tokens) <= size:
            passages.append(paragraph)
            continue
        for start in range(0, len(tokens), size):
            chunk = " ".join(tokens[start : start + size])
            if chunk:
                passages.append(chunk)
    return passages


def passage_units(docs: Sequence[Document], doc_ids: Set[str], passage_size: int) -> List[Unit]:
    units: List[Unit] = []
    for doc in docs:
        if doc.doc_id not in doc_ids:
            continue
        for index, passage in enumerate(split_passages(doc.text, passage_size), start=1):
            units.append(Unit(f"{doc.doc_id}#passage-{index}", passage, doc.collection, doc.doc_id))
    return units


def result_row(unit: Unit, score: float, include_text: bool = False) -> Dict[str, object]:
    row: Dict[str, object] = {
        "id": unit.unit_id,
        "collection": unit.collection,
        "document": unit.doc_id,
        "score": round(score, 6),
    }
    if include_text:
        row["text"] = compact(unit.text)
    else:
        row["snippet"] = compact(unit.text, 220)
    return row


def compact(text: str, limit: int = 500) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def compile_and_search(args: argparse.Namespace) -> Dict[str, object]:
    question = load_question(args)
    docs, mode = load_documents(args.corpus)
    plan = weighted_query_plan(question, docs)
    weighted_terms = plan["weighted_terms"]

    collection_index = BM25Index(collection_units(docs))
    collection_hits = collection_index.rank(weighted_terms, args.top_collections)
    top_collections = {unit.collection for unit, _score in collection_hits}

    doc_index = BM25Index(document_units(docs, top_collections or None))
    doc_hits = doc_index.rank(weighted_terms, args.top_docs)
    top_doc_ids = {unit.doc_id for unit, _score in doc_hits}

    passage_index = BM25Index(passage_units(docs, top_doc_ids, args.passage_size))
    passage_hits = passage_index.rank(weighted_terms, args.top_passages)

    key_detected = bool(os.getenv("SPARROWPLAN_API_KEY") or os.getenv("OPENAI_API_KEY"))
    planner_mode = "local_heuristic_env_key_available" if key_detected else "local_heuristic"

    return {
        "tool": "sparrowplan",
        "version": VERSION,
        "planner_mode": planner_mode,
        "network_used": False,
        "corpus_mode": mode,
        "question": question,
        "plan": {
            **plan,
            "controls": {
                "top_collections": args.top_collections,
                "top_docs": args.top_docs,
                "top_passages": args.top_passages,
                "passage_size_words": args.passage_size,
                "stopwords": "built_in_english",
            },
        },
        "results": {
            "collections": [result_row(unit, score) for unit, score in collection_hits],
            "documents": [result_row(unit, score) for unit, score in doc_hits],
            "passages": [result_row(unit, score, include_text=args.include_text) for unit, score in passage_hits],
        },
    }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile a natural-language question into a BM25-ready query plan and staged retrieval JSON."
    )
    parser.add_argument("--question", help="Question to compile. Defaults to built-in sample question.")
    parser.add_argument("--question-file", help="Read the question from a UTF-8 text file.")
    parser.add_argument("--corpus", help="Directory or file containing .md and .txt corpus documents.")
    parser.add_argument("--top-collections", type=positive_int, default=3, help="Collection stage limit.")
    parser.add_argument("--top-docs", type=positive_int, default=5, help="Document stage limit.")
    parser.add_argument("--top-passages", type=positive_int, default=5, help="Passage stage limit.")
    parser.add_argument("--passage-size", type=positive_int, default=80, help="Maximum words per generated passage chunk.")
    parser.add_argument("--include-text", action="store_true", help="Include longer passage text instead of short snippets.")
    parser.add_argument("--json-out", help="Write JSON output to this file as well as stdout.")
    return parser.parse_args(argv)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        output = compile_and_search(args)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, indent=2), file=sys.stderr)
        return 1

    encoded = json.dumps(output, indent=2, sort_keys=True)
    print(encoded)
    if args.json_out:
        Path(args.json_out).write_text(encoded + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
