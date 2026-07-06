#!/usr/bin/env python3
"""LexiPilot: deterministic BM25-style query planning for agent tool routing.

The module can be used as a CLI or imported as a small library. It intentionally
uses only the Python standard library so it can run inside installable skills
without API keys or network access.
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
from typing import Any, Dict, Iterable, List, Sequence, Tuple


DEFAULT_TOP_K = 3
DEFAULT_MIN_SCORE = 0.0

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "i",
    "in",
    "into",
    "is",
    "it",
    "me",
    "my",
    "need",
    "do",
    "hard",
    "not",
    "of",
    "on",
    "or",
    "our",
    "please",
    "that",
    "the",
    "this",
    "to",
    "use",
    "using",
    "with",
}

CAPABILITY_HINTS = {
    "audit": {"audit", "logs", "logging", "trace", "explain", "explanation", "debug", "debugging"},
    "bm25": {"bm25", "lexical", "keyword", "retrieval", "ranking"},
    "exclusion": {"exclude", "excludes", "exclusion", "exclusions", "negative", "without"},
    "planning": {"plan", "planner", "planning", "subquery", "subqueries", "decompose"},
    "routing": {"route", "router", "routing", "tool", "tools", "selection"},
}


SAMPLE_INPUT: Dict[str, Any] = {
    "request": "Need transparent BM25 tool routing with audit logs and hard exclusions; do not use email tools.",
    "tools": [
        {
            "id": "lexical-router",
            "name": "Lexical Tool Router",
            "description": "Routes agent tools with transparent BM25 lexical ranking, audit logs, and explicit exclusions.",
            "capabilities": ["routing", "bm25", "audit", "planning"],
        },
        {
            "id": "email-sender",
            "name": "Email Sender",
            "description": "Sends email messages and tracks delivery logs for outreach workflows.",
            "capabilities": ["email", "delivery"],
        },
        {
            "id": "embedding-router",
            "name": "Embedding Router",
            "description": "Selects tools through semantic embeddings and vector similarity for broad routing.",
            "capabilities": ["routing", "embeddings"],
        },
    ],
}


def normalize_text(text: str) -> str:
    """Return lowercase ASCII-ish text with punctuation collapsed to spaces."""

    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def tokenize(text: str, extra_stopwords: Iterable[str] | None = None) -> List[str]:
    """Tokenize text into non-stopword terms while preserving input order."""

    stopwords = set(STOPWORDS)
    if extra_stopwords:
        stopwords.update(term.strip().lower() for term in extra_stopwords if term.strip())
    return [term for term in normalize_text(text).split() if term and term not in stopwords]


def unique_sorted(items: Iterable[str]) -> List[str]:
    """Return sorted unique non-empty strings."""

    return sorted({item for item in items if item})


def extract_exclusions(request: str) -> List[str]:
    """Extract simple negative-intent spans from a request."""

    lowered = request.lower()
    exclusions: List[str] = []
    patterns = [
        r"\bdo not use\s+([a-z0-9 -]+?)(?:[.;,]|$)",
        r"\bdon't use\s+([a-z0-9 -]+?)(?:[.;,]|$)",
        r"\bexclude\s+([a-z0-9 -]+?)(?:[.;,]|$)",
        r"\bwithout\s+([a-z0-9 -]+?)(?:[.;,]|$)",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, lowered):
            phrase = normalize_text(match.group(1))
            if phrase:
                exclusions.append(phrase)
                exclusions.extend(term for term in tokenize(phrase) if term not in {"tool", "tools"})
    return unique_sorted(exclusions)


def extract_hard_constraints(request: str) -> List[str]:
    """Extract compact hard-constraint phrases from a request."""

    lowered = request.lower()
    constraints: List[str] = []
    phrase_patterns = [
        r"\bmust\s+([a-z0-9 -]+?)(?:[.;,]|$)",
        r"\brequired\s+([a-z0-9 -]+?)(?:[.;,]|$)",
        r"\bhard\s+([a-z0-9 -]+?)(?:[.;,]|$)",
    ]
    for pattern in phrase_patterns:
        for match in re.finditer(pattern, lowered):
            phrase = normalize_text(match.group(1))
            if phrase:
                constraints.append(f"hard {phrase}" if pattern.startswith(r"\bhard") else phrase)
    return unique_sorted(constraints)


def extract_required_capabilities(tokens: Sequence[str]) -> List[str]:
    """Map request tokens to coarse required capabilities."""

    token_set = set(tokens)
    capabilities = [
        capability
        for capability, hints in CAPABILITY_HINTS.items()
        if token_set.intersection(hints)
    ]
    return sorted(capabilities)


def extract_subqueries(request: str) -> List[str]:
    """Split a request into short lexical subqueries."""

    chunks = re.split(r"\s*(?:;|,|\band\b|\bthen\b|\balso\b|\bwith\b)\s*", request, flags=re.IGNORECASE)
    subqueries: List[str] = []
    for chunk in chunks:
        if re.search(r"\b(do not|don't|exclude|without)\b", chunk, flags=re.IGNORECASE):
            continue
        terms = tokenize(chunk)
        if terms:
            subqueries.append(" ".join(terms[:6]))
    return subqueries[:6]


def build_query_plan(request: str, extra_stopwords: Iterable[str] | None = None) -> Dict[str, Any]:
    """Build a deterministic routing query plan from a user request."""

    if not isinstance(request, str) or not request.strip():
        raise ValueError("request must be a non-empty string")
    tokens = tokenize(request, extra_stopwords)
    high_signal_terms = unique_sorted(tokens)
    return {
        "original_request": request,
        "normalized_request": normalize_text(request),
        "high_signal_terms": high_signal_terms,
        "required_capabilities": extract_required_capabilities(tokens),
        "hard_constraints": extract_hard_constraints(request),
        "exclusions": extract_exclusions(request),
        "subqueries": extract_subqueries(request),
    }


def tool_document(tool: Dict[str, Any]) -> str:
    """Combine searchable fields from a tool record into one document string."""

    parts = [
        str(tool.get("name", "")),
        str(tool.get("description", "")),
        " ".join(str(item) for item in tool.get("capabilities", []) if item is not None),
    ]
    return " ".join(parts)


def validate_tools(tools: Any) -> List[Dict[str, Any]]:
    """Validate and normalize a tool catalog."""

    if not isinstance(tools, list) or not tools:
        raise ValueError("tools must be a non-empty list")
    normalized: List[Dict[str, Any]] = []
    for index, tool in enumerate(tools):
        if not isinstance(tool, dict):
            raise ValueError(f"tools[{index}] must be an object")
        tool_id = tool.get("id")
        name = tool.get("name")
        description = tool.get("description")
        if not isinstance(tool_id, str) or not tool_id.strip():
            raise ValueError(f"tools[{index}].id must be a non-empty string")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"tools[{index}].name must be a non-empty string")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"tools[{index}].description must be a non-empty string")
        capabilities = tool.get("capabilities", [])
        if capabilities is None:
            capabilities = []
        if not isinstance(capabilities, list) or not all(isinstance(item, str) for item in capabilities):
            raise ValueError(f"tools[{index}].capabilities must be a list of strings when provided")
        normalized.append(
            {
                "id": tool_id,
                "name": name,
                "description": description,
                "capabilities": capabilities,
            }
        )
    return normalized


def build_bm25_index(tools: Sequence[Dict[str, Any]], extra_stopwords: Iterable[str] | None = None) -> Tuple[List[Counter], Dict[str, int], float]:
    """Build document term frequencies, document frequencies, and average length."""

    docs: List[Counter] = []
    document_frequencies: Dict[str, int] = {}
    lengths: List[int] = []
    for tool in tools:
        terms = tokenize(tool_document(tool), extra_stopwords)
        counter = Counter(terms)
        docs.append(counter)
        lengths.append(sum(counter.values()))
        for term in counter:
            document_frequencies[term] = document_frequencies.get(term, 0) + 1
    average_length = sum(lengths) / len(lengths) if lengths else 1.0
    return docs, document_frequencies, average_length or 1.0


def bm25_score(query_terms: Sequence[str], doc_terms: Counter, document_frequencies: Dict[str, int], doc_count: int, average_length: float) -> float:
    """Compute a compact BM25 score for one document."""

    k1 = 1.5
    b = 0.75
    score = 0.0
    doc_length = sum(doc_terms.values()) or 1
    for term in query_terms:
        frequency = doc_terms.get(term, 0)
        if not frequency:
            continue
        df = document_frequencies.get(term, 0)
        idf = math.log(1 + (doc_count - df + 0.5) / (df + 0.5))
        denominator = frequency + k1 * (1 - b + b * doc_length / average_length)
        score += idf * (frequency * (k1 + 1) / denominator)
    return score


def exclusion_reason(tool: Dict[str, Any], exclusions: Sequence[str], extra_stopwords: Iterable[str] | None = None) -> str | None:
    """Return an exclusion reason if a tool matches negative intent."""

    if not exclusions:
        return None
    normalized_doc = normalize_text(tool_document(tool))
    doc_tokens = set(tokenize(tool_document(tool), extra_stopwords))
    for exclusion in exclusions:
        normalized_exclusion = normalize_text(exclusion)
        exclusion_tokens = [
            term for term in tokenize(exclusion, extra_stopwords) if term not in {"tool", "tools"}
        ]
        if normalized_exclusion and normalized_exclusion in normalized_doc:
            return f"matched exclusion term: {normalized_exclusion}"
        if any(term in doc_tokens for term in exclusion_tokens):
            return f"matched exclusion term: {exclusion_tokens[0]}"
    return None


def make_evidence(matched_terms: Sequence[str], required_matches: Sequence[str]) -> List[str]:
    """Build human-readable evidence strings for a candidate."""

    evidence: List[str] = []
    if matched_terms:
        evidence.append(f"matched high-signal terms: {', '.join(matched_terms)}")
    if required_matches:
        evidence.append(f"matched required capabilities: {', '.join(required_matches)}")
    if not evidence:
        evidence.append("no direct lexical evidence above threshold")
    return evidence


def route_tools(
    request: str,
    tools: Sequence[Dict[str, Any]],
    top_k: int = DEFAULT_TOP_K,
    min_score: float = DEFAULT_MIN_SCORE,
    extra_stopwords: Iterable[str] | None = None,
) -> Dict[str, Any]:
    """Plan a query and rank tools with BM25-style lexical scoring."""

    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    if min_score < 0:
        raise ValueError("min_score must be zero or greater")

    validated_tools = validate_tools(list(tools))
    query_plan = build_query_plan(request, extra_stopwords)
    query_terms = query_plan["high_signal_terms"]
    docs, document_frequencies, average_length = build_bm25_index(validated_tools, extra_stopwords)

    candidates: List[Dict[str, Any]] = []
    excluded_tools: List[Dict[str, str]] = []

    for tool, doc_terms in zip(validated_tools, docs):
        reason = exclusion_reason(tool, query_plan["exclusions"], extra_stopwords)
        if reason:
            excluded_tools.append({"id": tool["id"], "name": tool["name"], "reason": reason})
            continue

        score = bm25_score(query_terms, doc_terms, document_frequencies, len(validated_tools), average_length)
        matched_terms = [term for term in query_terms if term in doc_terms]
        capability_set = {capability.lower() for capability in tool.get("capabilities", [])}
        required_matches = [capability for capability in query_plan["required_capabilities"] if capability in capability_set]

        if score >= min_score and matched_terms:
            candidates.append(
                {
                    "id": tool["id"],
                    "name": tool["name"],
                    "score": round(score, 4),
                    "matched_terms": matched_terms,
                    "evidence": make_evidence(matched_terms, required_matches),
                    "excluded": False,
                }
            )

    candidates.sort(key=lambda item: (-item["score"], item["id"]))

    return {
        "query_plan": query_plan,
        "candidates": candidates[:top_k],
        "excluded_tools": sorted(excluded_tools, key=lambda item: item["id"]),
        "metadata": {
            "algorithm": "bm25-lite",
            "top_k": top_k,
            "tool_count": len(validated_tools),
            "min_score": min_score,
        },
    }


def load_json_file(path: str) -> Any:
    """Load JSON from a file with clear CLI errors."""

    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise ValueError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"could not read {path}: {exc}") from exc


def write_json_file(path: str, data: Dict[str, Any]) -> None:
    """Write deterministic JSON to a file."""

    try:
        with Path(path).open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
    except OSError as exc:
        raise ValueError(f"could not write {path}: {exc}") from exc


def env_int(name: str, default: int) -> int:
    """Read an integer environment variable with validation."""

    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    return parsed


def env_float(name: str, default: float) -> float:
    """Read a float environment variable with validation."""

    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc
    return parsed


def env_stopwords() -> List[str]:
    """Read optional comma-separated stopwords from the environment."""

    value = os.getenv("LEXIPILOT_STOPWORDS", "")
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(
        description="Plan a request and rank agent tools with deterministic BM25-style lexical evidence."
    )
    parser.add_argument("--input", help="JSON file containing request and tools fields.")
    parser.add_argument("--request", help="User request to route.")
    parser.add_argument("--tools", help="JSON file containing a tool array, or an object with a tools field.")
    parser.add_argument("--top-k", type=int, default=None, help="Number of candidates to return. Defaults to LEXIPILOT_TOP_K or 3.")
    parser.add_argument("--min-score", type=float, default=None, help="Minimum BM25 score. Defaults to LEXIPILOT_MIN_SCORE or 0.")
    parser.add_argument("--output", help="Write JSON output to this file instead of stdout.")
    parser.add_argument("--selftest", action="store_true", help="Run on built-in sample data with no API key.")
    return parser.parse_args(argv)


def resolve_input(args: argparse.Namespace) -> Tuple[str, List[Dict[str, Any]]]:
    """Resolve request and tools from CLI arguments or the built-in sample."""

    if args.selftest or (not args.input and not args.request and not args.tools):
        return SAMPLE_INPUT["request"], SAMPLE_INPUT["tools"]

    if args.input:
        payload = load_json_file(args.input)
        if not isinstance(payload, dict):
            raise ValueError("--input must point to a JSON object with request and tools fields")
        return payload.get("request"), payload.get("tools")

    if not args.request:
        raise ValueError("--request is required when --input is not provided")
    if not args.tools:
        raise ValueError("--tools is required when --input is not provided")

    tools_payload = load_json_file(args.tools)
    tools = tools_payload.get("tools") if isinstance(tools_payload, dict) else tools_payload
    return args.request, tools


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint."""

    args = parse_args(argv if argv is not None else sys.argv[1:])
    try:
        top_k = args.top_k if args.top_k is not None else env_int("LEXIPILOT_TOP_K", DEFAULT_TOP_K)
        min_score = args.min_score if args.min_score is not None else env_float("LEXIPILOT_MIN_SCORE", DEFAULT_MIN_SCORE)
        request, tools = resolve_input(args)
        result = route_tools(request, tools, top_k=top_k, min_score=min_score, extra_stopwords=env_stopwords())
        if args.output:
            write_json_file(args.output, result)
        else:
            print(json.dumps(result, indent=2))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
