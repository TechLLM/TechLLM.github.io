#!/usr/bin/env python3
"""Queryloom: compile a question and local corpus into a BM25-ready query plan."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


VERSION = "0.1.0"

STOPWORDS = {
    "a",
    "about",
    "above",
    "after",
    "again",
    "against",
    "all",
    "am",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "between",
    "both",
    "but",
    "by",
    "can",
    "did",
    "do",
    "does",
    "doing",
    "down",
    "during",
    "each",
    "few",
    "for",
    "from",
    "further",
    "had",
    "has",
    "have",
    "having",
    "he",
    "her",
    "here",
    "hers",
    "herself",
    "him",
    "himself",
    "his",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "itself",
    "just",
    "me",
    "more",
    "most",
    "my",
    "myself",
    "no",
    "nor",
    "not",
    "of",
    "off",
    "on",
    "once",
    "only",
    "or",
    "other",
    "our",
    "ours",
    "ourselves",
    "out",
    "over",
    "own",
    "same",
    "she",
    "should",
    "so",
    "some",
    "such",
    "than",
    "that",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "to",
    "too",
    "under",
    "until",
    "up",
    "very",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "who",
    "whom",
    "why",
    "will",
    "with",
    "without",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
}

ALIAS_TABLE = {
    "agent": ["assistant", "orchestrator", "workflow"],
    "agents": ["assistants", "orchestrators", "agent workflows"],
    "alias": ["synonym", "alternate term", "variant"],
    "aliases": ["synonyms", "alternate terms", "variants"],
    "bm25": ["lexical search", "keyword ranking", "sparse retrieval"],
    "boost": ["weight", "promote", "prioritize"],
    "boosted": ["weighted", "promoted", "prioritized"],
    "constraint": ["filter", "requirement", "condition"],
    "constraints": ["filters", "requirements", "conditions"],
    "corpus": ["document set", "collection", "local documents"],
    "cost": ["expense", "token usage", "rate limit"],
    "exclusion": ["negative term", "filter out", "must not include"],
    "exclusions": ["negative terms", "filters", "must not include"],
    "idf": ["inverse document frequency", "rare term score"],
    "latency": ["delay", "response time", "runtime"],
    "llm": ["language model", "chat model", "model"],
    "query": ["search string", "retrieval query", "keyword query"],
    "ranking": ["scoring", "ordering", "retrieval rank"],
    "rare": ["discriminative", "specific", "uncommon"],
    "retrieval": ["search", "lookup", "document retrieval"],
    "search": ["retrieval", "lookup", "document search"],
    "subquery": ["focused query", "query shard", "retrieval pass"],
    "subqueries": ["focused queries", "query shards", "retrieval passes"],
    "tfidf": ["tf-idf", "term frequency inverse document frequency"],
    "vector": ["embedding", "semantic search", "dense retrieval"],
}

NEGATIVE_FILLER_TERMS = {
    "based",
    "depending",
    "depend",
    "only",
    "rely",
    "relying",
    "using",
    "use",
}

GENERIC_NEGATIVE_TERMS = {
    "query",
    "retrieval",
    "search",
}

SAMPLE_QUESTION = (
    "How can search agents reduce wasted BM25 retrieval calls without relying only on vector search?"
)

SAMPLE_CORPUS = [
    {
        "id": "sample-1",
        "text": (
            "BM25 retrieval improves when a query includes rare, discriminative terms. "
            "Agents waste calls when they begin with broad natural language questions."
        ),
    },
    {
        "id": "sample-2",
        "text": (
            "A query compiler can add aliases, boosted terms, negative constraints, "
            "and focused subqueries before the search stage begins."
        ),
    },
    {
        "id": "sample-3",
        "text": (
            "Vector search and embedding retrieval help with semantic similarity, "
            "but lexical search is often better for exact identifiers and uncommon vocabulary."
        ),
    },
    {
        "id": "sample-4",
        "text": (
            "Rate limits, latency, and context churn matter in agent orchestration. "
            "A stronger first retrieval query can reduce repeated inspect and rewrite loops."
        ),
    },
]


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9][a-z0-9_-]*", text.lower())


def content_tokens(text: str) -> List[str]:
    return [token for token in tokenize(text) if token not in STOPWORDS and len(token) > 1]


def ordered_unique(items: Iterable[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def read_question(args: argparse.Namespace) -> str:
    if args.question:
        return args.question.strip()
    if args.question_file:
        return Path(args.question_file).read_text(encoding="utf-8").strip()
    return SAMPLE_QUESTION


def normalize_document(raw: Any, fallback_id: str) -> Dict[str, str]:
    if isinstance(raw, str):
        return {"id": fallback_id, "text": raw}
    if isinstance(raw, dict):
        doc_id = str(raw.get("id") or raw.get("path") or fallback_id)
        text_parts = []
        for key in ("title", "summary", "body", "content", "text"):
            value = raw.get(key)
            if isinstance(value, str):
                text_parts.append(value)
        if not text_parts:
            text_parts = [str(value) for value in raw.values() if isinstance(value, (str, int, float))]
        return {"id": doc_id, "text": "\n".join(text_parts)}
    return {"id": fallback_id, "text": str(raw)}


def load_json_documents(path: Path) -> List[Dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [normalize_document(item, f"doc-{idx + 1}") for idx, item in enumerate(data)]
    if isinstance(data, dict):
        if isinstance(data.get("documents"), list):
            return [
                normalize_document(item, f"doc-{idx + 1}")
                for idx, item in enumerate(data["documents"])
            ]
        return [normalize_document(data, "doc-1")]
    raise ValueError(f"Unsupported JSON corpus shape in {path}")


def load_jsonl_documents(path: Path) -> List[Dict[str, str]]:
    documents = []
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        line = line.strip()
        if line:
            documents.append(normalize_document(json.loads(line), f"doc-{idx + 1}"))
    return documents


def load_text_documents(path: Path) -> List[Dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]
    if not chunks:
        return []
    return [{"id": f"{path.name}#{idx + 1}", "text": chunk} for idx, chunk in enumerate(chunks)]


def load_directory_documents(path: Path) -> List[Dict[str, str]]:
    documents = []
    supported = {".md", ".txt", ".json", ".jsonl"}
    for file_path in sorted(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in supported):
        if file_path.suffix.lower() == ".json":
            documents.extend(load_json_documents(file_path))
        elif file_path.suffix.lower() == ".jsonl":
            documents.extend(load_jsonl_documents(file_path))
        else:
            for doc in load_text_documents(file_path):
                doc["id"] = str(file_path.relative_to(path)) + ":" + doc["id"]
                documents.append(doc)
    return documents


def safe_source_label(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return path.name


def load_corpus(corpus_path: Optional[str]) -> Tuple[List[Dict[str, str]], str]:
    if not corpus_path:
        return SAMPLE_CORPUS, "built-in-sample"
    path = Path(corpus_path)
    if not path.exists():
        raise FileNotFoundError(f"Corpus path does not exist: {corpus_path}")
    if path.is_dir():
        documents = load_directory_documents(path)
    elif path.suffix.lower() == ".json":
        documents = load_json_documents(path)
    elif path.suffix.lower() == ".jsonl":
        documents = load_jsonl_documents(path)
    else:
        documents = load_text_documents(path)
    documents = [doc for doc in documents if doc["text"].strip()]
    if not documents:
        raise ValueError(f"No readable documents found in corpus: {corpus_path}")
    return documents, safe_source_label(path)


def compute_idf(doc_tokens: Sequence[Sequence[str]]) -> Dict[str, float]:
    doc_count = len(doc_tokens)
    document_frequency: Counter[str] = Counter()
    for tokens in doc_tokens:
        document_frequency.update(set(tokens))
    return {
        term: math.log(1 + (doc_count - freq + 0.5) / (freq + 0.5))
        for term, freq in document_frequency.items()
    }


def extract_negative_constraints(question: str) -> List[str]:
    constraints: List[str] = []
    pattern = re.compile(r"\b(?:without|excluding|exclude|avoid|except|not)\s+([^.;,:!?]+)", re.I)
    for match in pattern.finditer(question):
        phrase = match.group(1)
        phrase = re.split(r"\b(?:and|but|or)\b", phrase, maxsplit=1, flags=re.I)[0]
        tokens = [token for token in content_tokens(phrase) if token not in NEGATIVE_FILLER_TERMS]
        if len(tokens) > 1:
            constraints.append(" ".join(tokens[:3]))
        constraints.extend(token for token in tokens if token not in GENERIC_NEGATIVE_TERMS)
    return ordered_unique(constraints)


def phrase_matches_corpus(phrase: str, corpus_text: str) -> bool:
    return phrase.lower() in corpus_text


def build_aliases(seed_terms: Sequence[str], corpus_text: str) -> List[Dict[str, Any]]:
    alias_rows = []
    for term in seed_terms:
        aliases = []
        if term in ALIAS_TABLE:
            aliases.extend(ALIAS_TABLE[term])
        if "_" in term:
            aliases.append(term.replace("_", " "))
        if "-" in term:
            aliases.append(term.replace("-", " "))
        if term.endswith("s") and len(term) > 4 and not term.endswith(("ss", "us", "is")):
            aliases.append(term[:-1])
        aliases = ordered_unique(alias for alias in aliases if alias != term)
        if aliases:
            alias_rows.append(
                {
                    "source": term,
                    "aliases": aliases,
                    "corpus_hits": [
                        alias for alias in aliases if phrase_matches_corpus(alias, corpus_text)
                    ],
                }
            )
    return alias_rows


def score_terms(
    question_terms: Sequence[str],
    doc_tokens: Sequence[Sequence[str]],
    idf: Dict[str, float],
    exclusions: Sequence[str],
) -> Dict[str, Dict[str, Any]]:
    excluded = set(exclusions)
    question_set = set(question_terms) - excluded
    scores: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"score": 0.0, "idf": 0.0, "question_term": False, "from_relevant_doc": False}
    )

    for term in question_terms:
        if term in excluded:
            continue
        term_idf = idf.get(term, 0.0)
        scores[term]["score"] += 2.5 + term_idf * 2.0
        scores[term]["idf"] = round(term_idf, 4)
        scores[term]["question_term"] = True

    for tokens in doc_tokens:
        counts = Counter(tokens)
        overlap = len(question_set.intersection(counts))
        if not overlap:
            continue
        for term, count in counts.items():
            if term in STOPWORDS or term in excluded or len(term) < 3:
                continue
            term_idf = idf.get(term, 0.0)
            tf_weight = 1 + math.log(count)
            scores[term]["score"] += overlap * tf_weight * term_idf * 0.7
            scores[term]["idf"] = round(term_idf, 4)
            scores[term]["from_relevant_doc"] = True

    return scores


def reason_for(row: Dict[str, Any]) -> str:
    if row["question_term"] and row["from_relevant_doc"]:
        return "question term found in relevant corpus documents"
    if row["question_term"]:
        return "question term"
    return "corpus rare term from matching documents"


def select_weighted_terms(
    term_scores: Dict[str, Dict[str, Any]], top_k: int
) -> List[Dict[str, Any]]:
    ranked = sorted(
        term_scores.items(),
        key=lambda item: (-item[1]["score"], -item[1]["idf"], item[0]),
    )
    if not ranked:
        return []
    max_score = max(row["score"] for _, row in ranked) or 1.0
    weighted_terms = []
    for term, row in ranked[:top_k]:
        weight = 1.0 + 4.0 * (row["score"] / max_score)
        weighted_terms.append(
            {
                "term": term,
                "weight": round(weight, 2),
                "idf": row["idf"],
                "reason": reason_for(row),
            }
        )
    return weighted_terms


def compile_primary_query(
    weighted_terms: Sequence[Dict[str, Any]],
    aliases: Sequence[Dict[str, Any]],
    exclusions: Sequence[str],
) -> str:
    terms = [row["term"] for row in weighted_terms[:8]]
    alias_terms: List[str] = []
    for row in aliases[:3]:
        alias_terms.extend(row["aliases"][:2])
    positive = ordered_unique(terms + alias_terms)
    negative = [f"-{term}" for term in exclusions]
    negative = [f'-"{term}"' if " " in term else f"-{term}" for term in exclusions]
    return " ".join(positive + negative)


def build_subqueries(
    question_terms: Sequence[str],
    weighted_terms: Sequence[Dict[str, Any]],
    aliases: Sequence[Dict[str, Any]],
    exclusions: Sequence[str],
    max_subqueries: int,
) -> List[Dict[str, Any]]:
    excluded_terms = set(exclusions)
    rare_terms = [row["term"] for row in weighted_terms if row["reason"] != "question term"][:6]
    top_terms = [row["term"] for row in weighted_terms[:6] if row["term"] not in excluded_terms]
    alias_terms: List[str] = []
    for row in aliases:
        alias_terms.extend(row["aliases"][:2])
    negative_terms = [f'-"{term}"' if " " in term else f"-{term}" for term in exclusions]
    candidates = [
        {
            "name": "high_precision",
            "purpose": "Favor discriminative corpus terms and boosted exact vocabulary.",
            "terms": ordered_unique(top_terms[:4] + rare_terms[:4]),
        },
        {
            "name": "recall_expansion",
            "purpose": "Broaden recall with aliases and spelling variants.",
            "terms": ordered_unique(
                [term for term in question_terms[:4] if term not in excluded_terms] + alias_terms[:6]
            ),
        },
        {
            "name": "exclusion_aware",
            "purpose": "Apply negative constraints extracted from the question.",
            "terms": ordered_unique(top_terms[:6] + negative_terms),
        },
    ]
    subqueries = []
    for candidate in candidates:
        if not candidate["terms"]:
            continue
        if candidate["name"] == "exclusion_aware" and not exclusions:
            continue
        candidate["query"] = " ".join(candidate["terms"])
        subqueries.append(candidate)
        if len(subqueries) >= max_subqueries:
            break
    return subqueries


def compile_query_plan(question: str, documents: Sequence[Dict[str, str]], source: str, top_k: int, max_subqueries: int) -> Dict[str, Any]:
    doc_tokens = [content_tokens(doc["text"]) for doc in documents]
    idf = compute_idf(doc_tokens)
    question_terms = ordered_unique(content_tokens(question))
    exclusions = extract_negative_constraints(question)
    term_scores = score_terms(question_terms, doc_tokens, idf, exclusions)
    weighted_terms = select_weighted_terms(term_scores, top_k)
    corpus_text = "\n".join(doc["text"].lower() for doc in documents)
    alias_seed_terms = ordered_unique(question_terms + [row["term"] for row in weighted_terms[:8]])
    aliases = build_aliases(alias_seed_terms, corpus_text)
    primary_query = compile_primary_query(weighted_terms, aliases, exclusions)
    subqueries = build_subqueries(question_terms, weighted_terms, aliases, exclusions, max_subqueries)
    rare_terms = [
        {
            "term": row["term"],
            "idf": row["idf"],
            "weight": row["weight"],
        }
        for row in weighted_terms
        if "corpus rare term" in row["reason"] or row["idf"] > 0.0
    ][:top_k]

    api_key_present = bool(os.environ.get("QUERYLOOM_API_KEY"))

    return {
        "tool": "queryloom",
        "version": VERSION,
        "mode": "local-standard-library",
        "input": {
            "question": question,
            "corpus_source": source,
            "documents": len(documents),
        },
        "primary_query": primary_query,
        "weighted_terms": weighted_terms,
        "rare_terms": rare_terms,
        "aliases": aliases,
        "exclusions": exclusions,
        "focused_subqueries": subqueries,
        "diagnostics": {
            "tokenized_question_terms": question_terms,
            "idf_terms": len(idf),
            "external_api_used": False,
            "api_key_env_present": api_key_present,
        },
    }


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return parsed


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile a question and local corpus into a BM25-ready query plan."
    )
    parser.add_argument("--question", help="Question to compile into a query plan.")
    parser.add_argument("--question-file", help="Text file containing the question.")
    parser.add_argument("--corpus", help="Corpus path: JSON, JSONL, text, Markdown, or directory.")
    parser.add_argument("--top-k", type=positive_int, default=10, help="Number of weighted terms.")
    parser.add_argument(
        "--max-subqueries",
        type=positive_int,
        default=3,
        help="Maximum number of focused subqueries.",
    )
    parser.add_argument("--output", help="Write JSON output to this file.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    question = read_question(args)
    documents, source = load_corpus(args.corpus)
    plan = compile_query_plan(question, documents, source, args.top_k, args.max_subqueries)
    output = json.dumps(plan, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
