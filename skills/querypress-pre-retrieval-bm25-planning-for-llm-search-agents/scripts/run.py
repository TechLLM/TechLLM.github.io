#!/usr/bin/env python3
"""QueryPress: deterministic pre-retrieval BM25 planning for local corpora.

The module exposes ``build_plan`` for import-based use and a small CLI for
turning a question plus a local document folder into search-plan JSON. It uses
only the Python standard library and never requires API keys.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence


SUPPORTED_SUFFIXES = {".txt", ".md", ".rst"}

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
    "below",
    "between",
    "both",
    "but",
    "by",
    "can",
    "could",
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
    "now",
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
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
}

SYNONYMS = {
    "agent": ["assistant", "worker"],
    "agents": ["assistants", "workers"],
    "bm25": ["lexical ranking", "term scoring"],
    "corpus": ["document collection", "local files"],
    "document": ["file", "source"],
    "documents": ["files", "sources"],
    "evidence": ["sources", "matches"],
    "first-pass": ["initial retrieval", "first retrieval"],
    "llm": ["language model", "AI model"],
    "planning": ["query planning", "retrieval planning"],
    "query": ["question", "prompt"],
    "retrieval": ["search", "lookup"],
    "search": ["retrieval", "lookup"],
    "synonym": ["alternate term", "variant"],
    "tool": ["search tool", "retriever"],
}

SAMPLE_QUESTION = (
    "How can BM25 planning improve first-pass retrieval for LLM search agents "
    "and reduce noisy tool retries?"
)

SAMPLE_DOCUMENTS = {
    "querypress.md": (
        "QueryPress builds BM25 retrieval plans for LLM search agents. "
        "It highlights rare lexical anchors, query decomposition, and synonym "
        "slots before the first retrieval call."
    ),
    "retry-loop.md": (
        "Repeated tool retries often happen when the initial search query misses "
        "domain terms or retrieves noisy documents. Better pre retrieval planning "
        "can improve evidence gathering."
    ),
    "marketing-search.md": (
        "Marketing search dashboards track campaigns, rankings, impressions, and "
        "audience segments. They may add noise when the user needs technical "
        "retrieval evidence."
    ),
}


def tokenize(text: str, min_length: int = 2) -> list[str]:
    """Return lowercase lexical tokens while preserving simple hyphenated terms."""
    tokens = re.findall(r"[a-z0-9]+(?:[-_][a-z0-9]+)*", text.lower())
    return [token for token in tokens if len(token) >= min_length]


def content_tokens(text: str, min_length: int = 2) -> list[str]:
    """Return non-stopword tokens suitable for query planning."""
    return [token for token in tokenize(text, min_length) if token not in STOPWORDS]


def read_corpus(corpus_dir: Path) -> dict[str, str]:
    """Read supported plain-text documents from a local corpus directory."""
    if not corpus_dir.exists():
        raise ValueError(f"Corpus folder does not exist: {corpus_dir}")
    if not corpus_dir.is_dir():
        raise ValueError(f"Corpus path is not a folder: {corpus_dir}")

    documents: dict[str, str] = {}
    for path in sorted(corpus_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError(f"Could not read {path} as UTF-8 text") from exc
            relative = path.relative_to(corpus_dir).as_posix()
            if text.strip():
                documents[relative] = text

    if not documents:
        suffixes = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise ValueError(f"No readable documents found in {corpus_dir} with suffixes: {suffixes}")
    return documents


def compute_statistics(
    documents: dict[str, str], min_length: int = 2
) -> tuple[dict[str, int], Counter[str], dict[str, float], list[list[str]]]:
    """Compute document frequency, corpus frequency, approximate IDF, and tokenized docs."""
    tokenized_docs: list[list[str]] = [content_tokens(text, min_length) for text in documents.values()]
    corpus_frequency: Counter[str] = Counter(token for doc in tokenized_docs for token in doc)
    document_frequency: dict[str, int] = {}
    for token in sorted(corpus_frequency):
        document_frequency[token] = sum(1 for doc in tokenized_docs if token in set(doc))

    document_count = len(documents)
    idf = {
        token: math.log(1.0 + (document_count - df + 0.5) / (df + 0.5))
        for token, df in document_frequency.items()
    }
    return document_frequency, corpus_frequency, idf, tokenized_docs


def ngrams(tokens: Sequence[str], sizes: Iterable[int] = (2, 3)) -> list[tuple[str, ...]]:
    """Build consecutive token n-grams from a token sequence."""
    result: list[tuple[str, ...]] = []
    for size in sizes:
        if len(tokens) < size:
            continue
        for index in range(0, len(tokens) - size + 1):
            result.append(tuple(tokens[index : index + size]))
    return result


def unique_preserve_order(items: Iterable[str]) -> list[str]:
    """Return unique strings while preserving first occurrence order."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def select_anchors(
    question_tokens: Sequence[str],
    document_frequency: dict[str, int],
    idf: dict[str, float],
    max_anchors: int,
) -> list[dict[str, object]]:
    """Select rare question terms likely to improve lexical retrieval precision."""
    candidates = []
    for token in unique_preserve_order(question_tokens):
        if token in document_frequency:
            candidates.append(
                {
                    "term": token,
                    "idf": round(idf[token], 3),
                    "document_frequency": document_frequency[token],
                }
            )
    candidates.sort(key=lambda item: (-float(item["idf"]), str(item["term"])))
    return candidates[:max_anchors]


def select_ngram_candidates(
    question_tokens: Sequence[str], idf: dict[str, float], max_items: int = 6
) -> list[dict[str, object]]:
    """Score question n-grams by average available IDF."""
    scored = []
    for gram in ngrams(question_tokens):
        known_scores = [idf[token] for token in gram if token in idf]
        if not known_scores:
            continue
        score = sum(known_scores) / len(gram)
        scored.append({"ngram": " ".join(gram), "score": round(score, 3), "terms": list(gram)})
    scored.sort(key=lambda item: (-float(item["score"]), str(item["ngram"])))
    return scored[:max_items]


def select_synonym_slots(question_tokens: Sequence[str]) -> list[dict[str, object]]:
    """Return built-in synonym slots for terms present in the question."""
    slots = []
    for token in unique_preserve_order(question_tokens):
        if token in SYNONYMS:
            slots.append({"term": token, "alternatives": SYNONYMS[token]})
    return slots


def select_exclusions(
    question_tokens: Sequence[str],
    document_frequency: dict[str, int],
    corpus_frequency: Counter[str],
    document_count: int,
    max_terms: int = 5,
) -> list[str]:
    """Suggest corpus-common non-question terms that may add noise."""
    question_set = set(question_tokens)
    candidates = []
    for token, count in corpus_frequency.items():
        if token in question_set or token in STOPWORDS:
            continue
        df = document_frequency.get(token, 0)
        if df >= max(2, math.ceil(document_count * 0.5)) or count >= 2:
            candidates.append((token, df, count))
    candidates.sort(key=lambda item: (-item[1], -item[2], item[0]))
    return [token for token, _, _ in candidates[:max_terms]]


def split_question(question: str) -> list[str]:
    """Split a broad question into deterministic smaller clauses."""
    parts = re.split(r"\b(?:and|then|while|versus|vs)\b|[;?]", question, flags=re.IGNORECASE)
    cleaned = [" ".join(part.strip().split()) for part in parts if part.strip()]
    return cleaned or [question.strip()]


def build_queries(
    question: str,
    question_tokens: Sequence[str],
    anchors: Sequence[dict[str, object]],
    ngram_candidates: Sequence[dict[str, object]],
    exclusions: Sequence[str],
    max_queries: int,
) -> list[dict[str, object]]:
    """Create decomposed BM25 query specifications from anchors and clauses."""
    anchor_terms = [str(item["term"]) for item in anchors]
    queries: list[dict[str, object]] = []

    if anchor_terms:
        base_terms = unique_preserve_order(anchor_terms[:5] + list(question_tokens[:4]))
        queries.append(
            {
                "id": "q1",
                "purpose": "Anchor rare corpus-matching terms from the user question.",
                "query": " ".join(base_terms),
                "required_terms": anchor_terms[:2],
                "optional_terms": base_terms[2:],
                "exclude_terms": list(exclusions),
            }
        )

    for gram_item in ngram_candidates[:2]:
        terms = [str(term) for term in gram_item["terms"]]
        query_terms = unique_preserve_order(terms + anchor_terms[:3])
        if query_terms and len(queries) < max_queries:
            queries.append(
                {
                    "id": f"q{len(queries) + 1}",
                    "purpose": f"Test phrase-like candidate: {gram_item['ngram']}",
                    "query": " ".join(query_terms),
                    "required_terms": terms[:1],
                    "optional_terms": query_terms[1:],
                    "exclude_terms": list(exclusions[:3]),
                }
            )

    for clause in split_question(question):
        clause_tokens = content_tokens(clause)
        clause_terms = [token for token in clause_tokens if token in anchor_terms or token in question_tokens]
        query_terms = unique_preserve_order(clause_terms + anchor_terms[:2])
        if query_terms and len(queries) < max_queries:
            queries.append(
                {
                    "id": f"q{len(queries) + 1}",
                    "purpose": "Retrieve evidence for one decomposed question clause.",
                    "query": " ".join(query_terms),
                    "required_terms": query_terms[:1],
                    "optional_terms": query_terms[1:],
                    "exclude_terms": list(exclusions[:3]),
                }
            )

    if not queries:
        fallback_terms = unique_preserve_order(list(question_tokens[:6]))
        queries.append(
            {
                "id": "q1",
                "purpose": "Fallback lexical query from the question terms.",
                "query": " ".join(fallback_terms),
                "required_terms": fallback_terms[:1],
                "optional_terms": fallback_terms[1:],
                "exclude_terms": list(exclusions),
            }
        )

    return queries[:max_queries]


def build_plan(
    question: str,
    documents: dict[str, str],
    *,
    max_anchors: int = 8,
    max_queries: int = 4,
    min_token_length: int = 2,
) -> dict[str, object]:
    """Build a deterministic QueryPress BM25 search plan."""
    clean_question = " ".join(question.strip().split())
    if not clean_question:
        raise ValueError("Question is empty.")
    if not documents:
        raise ValueError("Document corpus is empty.")
    if max_anchors < 1:
        raise ValueError("max_anchors must be at least 1.")
    if max_queries < 1:
        raise ValueError("max_queries must be at least 1.")
    if min_token_length < 1:
        raise ValueError("min_token_length must be at least 1.")

    document_frequency, corpus_frequency, idf, tokenized_docs = compute_statistics(
        documents, min_token_length
    )
    question_tokens = content_tokens(clean_question, min_token_length)
    anchors = select_anchors(question_tokens, document_frequency, idf, max_anchors)
    ngram_candidates = select_ngram_candidates(question_tokens, idf)
    synonym_slots = select_synonym_slots(question_tokens)
    exclusions = select_exclusions(
        question_tokens, document_frequency, corpus_frequency, len(documents)
    )
    decomposed_queries = build_queries(
        clean_question, question_tokens, anchors, ngram_candidates, exclusions, max_queries
    )

    total_tokens = sum(len(doc) for doc in tokenized_docs)
    top_terms = [
        {
            "term": token,
            "document_frequency": document_frequency[token],
            "corpus_frequency": corpus_frequency[token],
        }
        for token in sorted(
            corpus_frequency,
            key=lambda item: (-document_frequency[item], -corpus_frequency[item], item),
        )[:8]
    ]

    return {
        "question": clean_question,
        "corpus": {
            "documents": len(documents),
            "tokens": total_tokens,
            "average_document_length": round(total_tokens / len(documents), 2),
            "top_terms": top_terms,
        },
        "plan": {
            "rare_term_anchors": anchors,
            "ngram_candidates": ngram_candidates,
            "synonym_slots": synonym_slots,
            "exclusion_terms": exclusions,
            "decomposed_queries": decomposed_queries,
        },
        "execution_notes": [
            "Run decomposed_queries in order against a BM25-compatible backend.",
            "Treat rare_term_anchors as precision boosters, not mandatory proof.",
            "Review exclusion_terms before applying them to strict search syntax.",
        ],
    }


def env_int(name: str, default: int, minimum: int = 1) -> int:
    """Read a positive integer from the environment with validation."""
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}.") from exc
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}, got {value}.")
    return value


def load_question(args: argparse.Namespace) -> str:
    """Load the question from CLI text or a question file."""
    if args.question and args.question_file:
        raise ValueError("Use either --question or --question-file, not both.")
    if args.question_file:
        path = Path(args.question_file)
        if not path.exists():
            raise ValueError(f"Question file does not exist: {path}")
        return path.read_text(encoding="utf-8")
    if args.question:
        return args.question
    return SAMPLE_QUESTION


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse command-line arguments for the QueryPress CLI."""
    parser = argparse.ArgumentParser(
        description="Generate deterministic BM25 pre-retrieval plans for local documents."
    )
    parser.add_argument("--question", help="Natural-language question to plan retrieval for.")
    parser.add_argument("--question-file", help="Path to a UTF-8 text file containing the question.")
    parser.add_argument("--corpus", help="Folder containing .txt, .md, or .rst documents.")
    parser.add_argument("--output", help="Optional path to write JSON output instead of stdout.")
    parser.add_argument("--max-anchors", type=int, help="Maximum rare-term anchors to emit.")
    parser.add_argument("--max-queries", type=int, help="Maximum decomposed BM25 queries to emit.")
    parser.add_argument("--min-token-length", type=int, help="Minimum token length to keep.")
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run on built-in sample data without external files or API keys.",
    )
    return parser.parse_args(argv)


def plan_from_args(args: argparse.Namespace, argv_was_empty: bool = False) -> dict[str, object]:
    """Build a plan from parsed CLI arguments, using sample data for self-tests."""
    max_anchors = args.max_anchors or env_int("QUERYPRESS_MAX_ANCHORS", 8)
    max_queries = args.max_queries or env_int("QUERYPRESS_MAX_QUERIES", 4)
    min_token_length = args.min_token_length or env_int("QUERYPRESS_MIN_TOKEN_LENGTH", 2)

    use_sample = args.selftest or argv_was_empty
    if use_sample:
        question = SAMPLE_QUESTION
        documents = SAMPLE_DOCUMENTS
    else:
        if not args.corpus:
            raise ValueError("Missing --corpus. Use --selftest for the built-in sample.")
        question = load_question(args)
        documents = read_corpus(Path(args.corpus))

    return build_plan(
        question,
        documents,
        max_anchors=max_anchors,
        max_queries=max_queries,
        min_token_length=min_token_length,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    actual_argv = list(sys.argv[1:] if argv is None else argv)
    try:
        args = parse_args(actual_argv)
        plan = plan_from_args(args, argv_was_empty=not actual_argv)
        output = json.dumps(plan, indent=2, sort_keys=True) + "\n"
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
        else:
            sys.stdout.write(output)
        return 0
    except ValueError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
