#!/usr/bin/env python3
"""QueryLens: deterministic BM25 query-plan generation for local corpora.

The script converts a natural-language question and a local text corpus into a
structured JSON plan containing include terms, optional expansion terms,
exclusions, preserved constraints, and verification checklist items. It uses
only the Python standard library and never calls a network service.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown", ".json", ".jsonl"}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "can",
    "could",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "should",
    "that",
    "the",
    "their",
    "then",
    "there",
    "this",
    "to",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}

NEGATION_CUES = {"without", "exclude", "excluding", "avoid", "avoiding", "not", "no"}

DEFAULT_SYNONYMS = {
    "agentic": ["agent-driven", "autonomous agent"],
    "api": ["service endpoint"],
    "apis": ["service endpoints"],
    "bm25": ["lexical ranking", "keyword search"],
    "corpus": ["document collection"],
    "evaluation": ["verification", "assessment"],
    "local": ["offline"],
    "planning": ["query rewriting", "retrieval planning"],
    "query": ["search string"],
    "retrieval": ["search", "document ranking"],
}

SELFTEST_PAYLOAD = {
    "question": "How can hybrid retrieval evaluation run on a local corpus without external APIs?",
    "documents": [
        {
            "id": "doc-1",
            "text": "Hybrid retrieval combines BM25 lexical search with vector search. Evaluation should keep a local corpus and repeatable relevance checks.",
        },
        {
            "id": "doc-2",
            "text": "BM25 scoring uses term frequency and inverse document frequency to rank documents for keyword queries.",
        },
        {
            "id": "doc-3",
            "text": "Offline research assistants avoid external APIs by planning query terms, exclusions, and verification checklists before search.",
        },
    ],
}


class QueryLensError(ValueError):
    """Raised when QueryLens receives invalid input or configuration."""


def tokenize(text: str) -> list[str]:
    """Return lower-case alphanumeric tokens while preserving terms like BM25."""

    return [match.group(0).lower() for match in re.finditer(r"[A-Za-z][A-Za-z0-9_+-]*|\d+(?:\.\d+)?", text)]


def content_tokens(text: str) -> list[str]:
    """Return non-stopword tokens for retrieval planning."""

    return [token for token in tokenize(text) if token not in STOPWORDS]


def ngrams(tokens: list[str], max_n: int = 3) -> list[tuple[str, str]]:
    """Return `(term, kind)` pairs for unigrams, bigrams, and trigrams."""

    result: list[tuple[str, str]] = []
    labels = {1: "unigram", 2: "bigram", 3: "trigram"}
    for n in range(1, max_n + 1):
        for index in range(0, max(0, len(tokens) - n + 1)):
            result.append((" ".join(tokens[index : index + n]), labels[n]))
    return result


def normalize_documents(raw_documents: Iterable[Any]) -> list[dict[str, str]]:
    """Normalize strings or document dictionaries into `{id, text}` dictionaries."""

    documents: list[dict[str, str]] = []
    for index, item in enumerate(raw_documents, start=1):
        if isinstance(item, str):
            text = item
            doc_id = f"doc-{index}"
        elif isinstance(item, dict):
            text = first_text_value(item)
            doc_id = str(item.get("id") or item.get("name") or f"doc-{index}")
        else:
            raise QueryLensError(f"document {index} must be a string or object, got {type(item).__name__}")

        text = text.strip()
        if text:
            documents.append({"id": doc_id, "text": text})

    if not documents:
        raise QueryLensError("corpus must contain at least one non-empty document")
    return documents


def first_text_value(data: dict[str, Any]) -> str:
    """Extract the first conventional text field from a JSON object."""

    for key in ("text", "content", "body", "markdown", "question"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value
    raise QueryLensError("document object must include a non-empty text, content, body, markdown, or question field")


def documents_from_json(data: Any) -> tuple[str | None, list[dict[str, str]] | None]:
    """Extract an optional question and documents from JSON-compatible data."""

    if isinstance(data, dict):
        question = data.get("question") if isinstance(data.get("question"), str) else None
        for key in ("documents", "corpus", "items"):
            if isinstance(data.get(key), list):
                return question, normalize_documents(data[key])
        if any(isinstance(data.get(key), str) for key in ("text", "content", "body", "markdown")):
            return question, normalize_documents([data])
        return question, None
    if isinstance(data, list):
        return None, normalize_documents(data)
    raise QueryLensError("JSON input must be an object or array")


def load_documents(path: Path) -> tuple[str | None, list[dict[str, str]]]:
    """Load corpus documents from a supported file or directory."""

    if not path.exists():
        raise QueryLensError(f"corpus path does not exist: {path}")

    if path.is_dir():
        documents: list[dict[str, str]] = []
        question: str | None = None
        files = [item for item in sorted(path.rglob("*")) if item.is_file() and item.suffix.lower() in SUPPORTED_SUFFIXES]
        if not files:
            raise QueryLensError(f"directory contains no supported corpus files: {path}")
        for file_path in files:
            loaded_question, loaded_docs = load_documents(file_path)
            if question is None and loaded_question:
                question = loaded_question
            for doc in loaded_docs:
                documents.append({"id": str(file_path), "text": doc["text"]})
        return question, normalize_documents(documents)

    suffix = path.suffix.lower()
    try:
        raw_text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise QueryLensError(f"could not read {path} as UTF-8 text") from exc

    if suffix == ".json":
        try:
            return_question, documents = documents_from_json(json.loads(raw_text))
        except json.JSONDecodeError as exc:
            raise QueryLensError(f"invalid JSON in {path}: {exc.msg}") from exc
        if documents is None:
            raise QueryLensError(f"JSON file has no documents/corpus/items/text fields: {path}")
        return return_question, documents

    if suffix == ".jsonl":
        rows: list[Any] = []
        for line_number, line in enumerate(raw_text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise QueryLensError(f"invalid JSONL at {path}:{line_number}: {exc.msg}") from exc
        return None, normalize_documents(rows)

    if suffix in {".txt", ".md", ".markdown"}:
        return None, normalize_documents([{"id": path.name, "text": raw_text}])

    raise QueryLensError(f"unsupported corpus file type: {path.suffix or '<none>'}")


def compute_idf(documents: list[dict[str, str]]) -> dict[str, float]:
    """Compute smoothed corpus IDF for document n-grams."""

    document_frequency: Counter[str] = Counter()
    for document in documents:
        terms = {term for term, _kind in ngrams(content_tokens(document["text"]))}
        document_frequency.update(terms)

    total_documents = len(documents)
    return {
        term: round(math.log((total_documents + 1) / (frequency + 0.5)) + 1, 6)
        for term, frequency in document_frequency.items()
    }


def detect_exclusions(question: str) -> list[str]:
    """Detect simple exclusion terms after negation cues such as `without`."""

    tokens = tokenize(question)
    exclusions: list[str] = []
    for index, token in enumerate(tokens):
        if token not in NEGATION_CUES:
            continue
        window = [item for item in tokens[index + 1 : index + 5] if item not in STOPWORDS and item not in NEGATION_CUES]
        if not window:
            continue
        phrase = " ".join(window[:2])
        if phrase and phrase not in exclusions:
            exclusions.append(phrase)
        for item in window[:2]:
            if item not in exclusions:
                exclusions.append(item)
    return exclusions


def detect_constraints(question: str, exclusions: list[str], selected_terms: list[str]) -> list[dict[str, str]]:
    """Extract quoted, numeric, acronym, negation, and key phrase constraints."""

    constraints: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(value: str, kind: str) -> None:
        value = value.strip()
        key = (value.lower(), kind)
        if value and key not in seen:
            constraints.append({"constraint": value, "type": kind})
            seen.add(key)

    for match in re.finditer(r'"([^"]+)"|\'([^\']+)\'', question):
        add(match.group(1) or match.group(2), "quoted_phrase")

    for match in re.finditer(r"\b\d+(?:\.\d+)?(?:%|x|k|m|gb|mb|ms|s|days?|years?)?\b", question, flags=re.IGNORECASE):
        add(match.group(0), "numeric")

    for match in re.finditer(r"\b[A-Z][A-Z0-9]{1,}\b", question):
        add(match.group(0), "acronym")

    lower_question = question.lower()
    for exclusion in exclusions:
        pattern = rf"\b(?:without|exclude|excluding|avoid|avoiding|not|no)\b(?:\W+\w+){{0,4}}"
        for match in re.finditer(pattern, lower_question):
            if exclusion in match.group(0):
                add(match.group(0).strip(" ?.,;:"), "negation")
                break

    for term in selected_terms:
        if " " in term and term in lower_question:
            add(term, "key_phrase")

    return constraints


def load_synonym_map(env: dict[str, str] | None = None) -> dict[str, list[str]]:
    """Load optional synonym templates from `QUERYLENS_SYNONYMS_JSON`."""

    env = env or os.environ
    custom = env.get("QUERYLENS_SYNONYMS_JSON")
    synonyms = {key: list(values) for key, values in DEFAULT_SYNONYMS.items()}
    if not custom:
        return synonyms

    try:
        parsed = json.loads(custom)
    except json.JSONDecodeError as exc:
        raise QueryLensError(f"QUERYLENS_SYNONYMS_JSON must be valid JSON: {exc.msg}") from exc

    if not isinstance(parsed, dict):
        raise QueryLensError("QUERYLENS_SYNONYMS_JSON must be a JSON object")
    for key, values in parsed.items():
        if not isinstance(key, str) or not isinstance(values, list) or not all(isinstance(value, str) for value in values):
            raise QueryLensError("QUERYLENS_SYNONYMS_JSON must map strings to arrays of strings")
        synonyms[key.lower()] = [value.lower() for value in values if value.strip()]
    return synonyms


def load_max_terms(env: dict[str, str] | None = None, default: int = 10) -> int:
    """Load optional include-term limit from `QUERYLENS_MAX_TERMS`."""

    env = env or os.environ
    value = env.get("QUERYLENS_MAX_TERMS")
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise QueryLensError("QUERYLENS_MAX_TERMS must be a positive integer") from exc
    if parsed <= 0:
        raise QueryLensError("QUERYLENS_MAX_TERMS must be a positive integer")
    return parsed


def build_query_plan(
    question: str,
    documents: Iterable[Any],
    *,
    source: str = "provided",
    max_terms: int = 10,
    synonym_map: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Build a deterministic BM25 query plan from a question and corpus."""

    question = question.strip()
    if not question:
        raise QueryLensError("question must be a non-empty string")
    normalized_documents = normalize_documents(documents)
    idf = compute_idf(normalized_documents)
    synonym_map = synonym_map or DEFAULT_SYNONYMS

    exclusions = detect_exclusions(question)
    excluded_terms = set(exclusions)
    question_terms = ngrams(content_tokens(question))

    candidates: list[dict[str, Any]] = []
    seen_terms: set[str] = set()
    for term, kind in question_terms:
        if term in seen_terms or term in excluded_terms:
            continue
        if any(part in excluded_terms for part in term.split()):
            continue
        if term not in idf:
            continue
        score = idf[term] * len(term.split())
        candidates.append(
            {
                "term": term,
                "kind": kind,
                "idf": idf[term],
                "score": round(score, 6),
                "reason": "rare question term found in corpus",
            }
        )
        seen_terms.add(term)

    candidates.sort(key=lambda item: (-item["score"], -len(item["term"].split()), item["term"]))
    include_terms = [
        {
            "term": item["term"],
            "kind": item["kind"],
            "idf": item["idf"],
            "reason": item["reason"],
        }
        for item in candidates[:max_terms]
    ]

    selected_term_strings = [item["term"] for item in include_terms]
    expansions = build_expansions(question, selected_term_strings, exclusions, synonym_map)
    constraints = detect_constraints(question, exclusions, selected_term_strings)
    bm25_query = build_bm25_query(selected_term_strings, exclusions)

    rare_terms = sorted(idf.items(), key=lambda item: (-item[1], -len(item[0].split()), item[0]))

    return {
        "question": question,
        "corpus": {
            "document_count": len(normalized_documents),
            "source": source,
        },
        "plan": {
            "bm25_query": bm25_query,
            "include_terms": include_terms,
            "optional_expansion_terms": expansions,
            "exclusion_terms": exclusions,
            "preserved_constraints": constraints,
            "verification_checklist": build_checklist(include_terms, exclusions, constraints),
        },
        "diagnostics": {
            "question_terms_considered": sorted({term for term, _kind in question_terms}),
            "corpus_top_rare_terms": [term for term, _score in rare_terms[:10]],
        },
    }


def build_expansions(
    question: str,
    include_terms: list[str],
    exclusions: list[str],
    synonym_map: dict[str, list[str]],
) -> list[dict[str, str]]:
    """Build optional expansion terms from deterministic synonym templates."""

    question_token_set = set(content_tokens(question))
    blocked = set(include_terms) | set(exclusions)
    expansions: list[dict[str, str]] = []
    seen: set[str] = set()
    for token in sorted(question_token_set):
        if token in exclusions:
            continue
        for expansion in synonym_map.get(token, []):
            normalized = expansion.lower()
            if normalized in blocked or normalized in seen:
                continue
            expansions.append({"term": normalized, "source": "template", "for": token})
            seen.add(normalized)
    return expansions


def build_bm25_query(include_terms: list[str], exclusions: list[str]) -> str:
    """Build a BM25-ready query string with phrases quoted."""

    parts: list[str] = []
    for term in include_terms:
        rendered = f'"{term}"' if " " in term else term
        if rendered not in parts:
            parts.append(rendered)
    for exclusion in exclusions:
        rendered = f'-"{exclusion}"' if " " in exclusion else f"-{exclusion}"
        if rendered not in parts:
            parts.append(rendered)
    return " ".join(parts)


def build_checklist(
    include_terms: list[dict[str, Any]],
    exclusions: list[str],
    constraints: list[dict[str, str]],
) -> list[str]:
    """Create review checklist items for the generated retrieval plan."""

    checklist = [
        "Confirm the top include terms are central to the user's question.",
        "Run BM25 with the quoted phrases preserved exactly where supported.",
    ]
    if exclusions:
        checklist.append("Filter or down-rank documents dominated by the exclusion terms.")
    if constraints:
        checklist.append("Verify every preserved constraint is still represented after query rewriting.")
    if include_terms:
        checklist.append("Check at least one retrieved document contains a high-IDF include term or phrase.")
    checklist.append("Record misses and revise include or expansion terms before answer generation.")
    return checklist


def load_input(args: argparse.Namespace) -> tuple[str, list[dict[str, str]], str]:
    """Load CLI question and corpus from `--input`, `--question`, and `--corpus`."""

    question: str | None = args.question
    documents: list[dict[str, str]] | None = None
    source = "provided"

    if args.input:
        input_path = Path(args.input)
        loaded_question, loaded_documents = load_documents(input_path)
        question = question or loaded_question
        documents = loaded_documents
        source = str(input_path)

    if args.corpus:
        corpus_path = Path(args.corpus)
        loaded_question, loaded_documents = load_documents(corpus_path)
        question = question or loaded_question
        documents = loaded_documents
        source = str(corpus_path)

    if question is None:
        raise QueryLensError("missing question; pass --question or use a JSON --input with a question field")
    if documents is None:
        raise QueryLensError("missing corpus; pass --corpus or --input with documents")
    return question, documents, source


def run_selftest() -> dict[str, Any]:
    """Run QueryLens on built-in sample data without reading files or env vars."""

    return build_query_plan(
        SELFTEST_PAYLOAD["question"],
        SELFTEST_PAYLOAD["documents"],
        source="built-in-sample",
        max_terms=10,
        synonym_map=DEFAULT_SYNONYMS,
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Generate deterministic BM25 query-plan JSON from a question and local corpus.",
    )
    parser.add_argument("--question", help="Natural-language question to plan for.")
    parser.add_argument("--corpus", help="Corpus file or directory: txt, md, json, jsonl, or directory.")
    parser.add_argument("--input", help="Combined JSON input containing question and documents/corpus/items.")
    parser.add_argument("--output", help="Write JSON output to this file instead of stdout.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON with indentation.")
    parser.add_argument("--selftest", action="store_true", help="Run built-in sample data with no files or API keys.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for QueryLens."""

    args = parse_args(argv or sys.argv[1:])
    try:
        if args.selftest or not any(vars(args).values()):
            result = run_selftest()
        else:
            question, documents, source = load_input(args)
            result = build_query_plan(
                question,
                documents,
                source=source,
                max_terms=load_max_terms(),
                synonym_map=load_synonym_map(),
            )

        output = json.dumps(result, indent=2 if args.pretty else None, sort_keys=True)
        if args.output:
            Path(args.output).write_text(output + "\n", encoding="utf-8")
        else:
            print(output)
        return 0
    except QueryLensError as exc:
        print(f"querylens error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
