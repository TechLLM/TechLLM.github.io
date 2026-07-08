#!/usr/bin/env python3
"""RouteLexicon: BM25-style routing plans for JSON agent manifests.

The module can be used as a CLI or imported as a small library. It requires
only the Python standard library and does not call external services.
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
from typing import Any, Iterable


VERSION = "0.1.0"
TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")
SPLIT_RE = re.compile(r"\b(?:and|then|plus)\b|[,;]", re.IGNORECASE)
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "with",
}

SAMPLE_REQUEST = "Research competitors and summarize current market evidence"

SAMPLE_MANIFEST: dict[str, Any] = {
    "agents": [
        {
            "id": "research-agent",
            "name": "Research Agent",
            "description": (
                "Finds web evidence, compares sources, summarizes current "
                "information, competitors, and market research."
            ),
            "capabilities": [
                "internet research",
                "source comparison",
                "fact checking",
                "market analysis",
            ],
            "keywords": [
                "research",
                "sources",
                "evidence",
                "competitors",
                "market",
                "web",
            ],
            "synonyms": {
                "look up": ["research"],
                "compare": ["comparison", "evidence"],
            },
            "exclude_terms": ["code", "deploy", "database"],
            "term_weights": {"evidence": 1.4, "competitors": 1.25},
        },
        {
            "id": "coding-agent",
            "name": "Coding Agent",
            "description": (
                "Writes and edits code, fixes bugs, runs tests, and updates "
                "software repositories."
            ),
            "capabilities": [
                "python implementation",
                "bug fixing",
                "test repair",
                "repository changes",
            ],
            "keywords": ["code", "python", "bug", "tests", "repository", "implementation"],
            "exclude_terms": ["advertising", "market"],
            "term_weights": {"tests": 1.3, "code": 1.2},
        },
        {
            "id": "finance-agent",
            "name": "Finance Agent",
            "description": (
                "Reviews financial filings, market indicators, forecasts, "
                "risk, and investment context."
            ),
            "capabilities": [
                "financial analysis",
                "market indicators",
                "risk review",
                "forecast summaries",
            ],
            "keywords": ["finance", "filings", "market", "risk", "forecast"],
            "exclude_terms": ["code", "ui"],
            "term_weights": {"market": 1.2, "risk": 1.25},
        },
    ]
}


class RouteLexiconError(ValueError):
    """Raised for clear user-facing manifest, input, or configuration errors."""


def tokenize(value: Any) -> list[str]:
    """Return lowercase lexical tokens from strings, lists, tuples, or dicts."""
    if value is None:
        return []
    if isinstance(value, str):
        return [token for token in TOKEN_RE.findall(value.lower()) if token not in STOPWORDS]
    if isinstance(value, dict):
        tokens: list[str] = []
        for key, item in value.items():
            tokens.extend(tokenize(key))
            tokens.extend(tokenize(item))
        return tokens
    if isinstance(value, (list, tuple, set)):
        tokens = []
        for item in value:
            tokens.extend(tokenize(item))
        return tokens
    return tokenize(str(value))


def unique_sorted(tokens: Iterable[str]) -> list[str]:
    """Return unique tokens sorted for deterministic output."""
    return sorted(set(tokens))


def _as_agent_list(manifest: Any) -> list[dict[str, Any]]:
    """Validate and normalize a manifest object into a list of agent dicts."""
    if isinstance(manifest, dict):
        agents = manifest.get("agents")
    else:
        agents = manifest
    if not isinstance(agents, list) or not agents:
        raise RouteLexiconError("Manifest must contain a non-empty 'agents' array.")

    normalized: list[dict[str, Any]] = []
    for index, agent in enumerate(agents):
        if not isinstance(agent, dict):
            raise RouteLexiconError(f"Agent at index {index} must be an object.")
        agent_id = agent.get("id")
        if not isinstance(agent_id, str) or not agent_id.strip():
            raise RouteLexiconError(f"Agent at index {index} must have a non-empty string 'id'.")
        normalized.append(dict(agent))
    return normalized


def agent_document_terms(agent: dict[str, Any]) -> list[str]:
    """Build the searchable lexical document for one agent."""
    fields = {
        "id": agent.get("id"),
        "name": agent.get("name", agent.get("id")),
        "description": agent.get("description", ""),
        "capabilities": agent.get("capabilities", []),
        "keywords": agent.get("keywords", []),
        "synonyms": agent.get("synonyms", {}),
    }
    return tokenize(fields)


def compute_idf(documents: list[list[str]]) -> dict[str, float]:
    """Compute BM25-style inverse document frequency for tokenized documents."""
    if not documents:
        return {}
    doc_count = len(documents)
    document_frequency: Counter[str] = Counter()
    for terms in documents:
        document_frequency.update(set(terms))
    return {
        term: math.log(1.0 + (doc_count - df + 0.5) / (df + 0.5))
        for term, df in document_frequency.items()
    }


def _parse_float_env(name: str, default: float) -> float:
    """Read an optional float environment variable with a clear error."""
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise RouteLexiconError(f"Environment variable {name} must be a number.") from exc


def _parse_int_env(name: str, default: int) -> int:
    """Read an optional integer environment variable with a clear error."""
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise RouteLexiconError(f"Environment variable {name} must be an integer.") from exc
    if value <= 0:
        raise RouteLexiconError(f"Environment variable {name} must be greater than zero.")
    return value


def _synonym_expansions(request: str, agents: list[dict[str, Any]]) -> list[str]:
    """Collect manifest-driven synonym expansion tokens present in the request."""
    request_lower = request.lower()
    request_tokens = set(tokenize(request))
    expansions: list[str] = []
    for agent in agents:
        synonyms = agent.get("synonyms", {})
        if not isinstance(synonyms, dict):
            continue
        for phrase, replacements in synonyms.items():
            phrase_tokens = set(tokenize(phrase))
            phrase_text = " ".join(tokenize(phrase))
            if phrase_text and (phrase_text in request_lower or phrase_tokens <= request_tokens):
                expansions.extend(tokenize(replacements))
    return expansions


def _split_subqueries(request: str) -> list[dict[str, Any]]:
    """Split a request into simple lexical subqueries."""
    parts = [part.strip() for part in SPLIT_RE.split(request) if part.strip()]
    if not parts:
        parts = [request.strip()]
    return [
        {"id": f"q{index}", "text": part, "terms": unique_sorted(tokenize(part))}
        for index, part in enumerate(parts, start=1)
    ]


def _term_weights(agent: dict[str, Any]) -> dict[str, float]:
    """Normalize optional per-agent term weights into token-level weights."""
    raw = agent.get("term_weights", {})
    if not isinstance(raw, dict):
        return {}
    weights: dict[str, float] = {}
    for term, value in raw.items():
        try:
            weight = float(value)
        except (TypeError, ValueError):
            continue
        for token in tokenize(term):
            weights[token] = weight
    return weights


def _score_agent(
    agent: dict[str, Any],
    query_terms: list[str],
    document_terms: list[str],
    idf: dict[str, float],
    average_document_length: float,
    k1: float,
    b: float,
) -> dict[str, Any]:
    """Score one agent against query terms and return inspectable evidence."""
    tf = Counter(document_terms)
    doc_len = max(1, len(document_terms))
    denom_norm = k1 * (1.0 - b + b * (doc_len / max(1.0, average_document_length)))
    query_set = set(query_terms)
    keyword_terms = set(tokenize(agent.get("keywords", [])))
    exclusion_terms = set(tokenize(agent.get("exclude_terms", [])))
    per_term_weights = _term_weights(agent)

    bm25 = 0.0
    for term in query_terms:
        freq = tf.get(term, 0)
        if freq:
            bm25 += idf.get(term, 0.0) * ((freq * (k1 + 1.0)) / (freq + denom_norm))

    matched = sorted(query_set & set(tf))
    keyword_matches = sorted(query_set & keyword_terms)
    weighted_bonus = sum(idf.get(term, 0.0) * max(0.0, per_term_weights.get(term, 1.0) - 1.0) for term in matched)
    keyword_boost = float(sum(idf.get(term, 0.0) * 0.15 for term in keyword_matches) + weighted_bonus)
    excluded_by = sorted(query_set & exclusion_terms)
    exclusion_penalty = float(len(excluded_by)) * 1.5
    final_score = bm25 + keyword_boost - exclusion_penalty

    rare = sorted(matched, key=lambda term: (-idf.get(term, 0.0), term))[:5]
    matched_terms = [
        {"term": term, "idf": round(idf.get(term, 0.0), 4), "tf": tf.get(term, 0)}
        for term in sorted(matched, key=lambda item: (-idf.get(item, 0.0), item))
    ]
    rare_terms = [{"term": term, "idf": round(idf.get(term, 0.0), 4)} for term in rare]

    if excluded_by:
        rationale = "Penalized because the request contains exclusion terms: " + ", ".join(excluded_by) + "."
    elif matched:
        rare_text = ", ".join(term["term"] for term in rare_terms[:3]) or "none"
        rationale = "Matched " + ", ".join(matched[:5]) + "; rare clues: " + rare_text + "."
    else:
        rationale = "No direct lexical evidence matched this agent."

    return {
        "agent_id": agent["id"],
        "name": agent.get("name", agent["id"]),
        "score": round(final_score, 4),
        "matched_terms": matched_terms,
        "rare_terms": rare_terms,
        "excluded_by": excluded_by,
        "weights": {
            "bm25": round(bm25, 4),
            "keyword_boost": round(keyword_boost, 4),
            "exclusion_penalty": round(exclusion_penalty, 4),
            "final": round(final_score, 4),
        },
        "rationale": rationale,
    }


def route_request(
    request: str,
    manifest: Any,
    *,
    top_k: int = 3,
    k1: float = 1.5,
    b: float = 0.75,
) -> dict[str, Any]:
    """Return a deterministic BM25-style routing plan for a request and manifest."""
    if not isinstance(request, str) or not request.strip():
        raise RouteLexiconError("Request text must be a non-empty string.")
    if top_k <= 0:
        raise RouteLexiconError("top_k must be greater than zero.")
    if k1 <= 0:
        raise RouteLexiconError("k1 must be greater than zero.")
    if not 0 <= b <= 1:
        raise RouteLexiconError("b must be between 0 and 1.")

    agents = _as_agent_list(manifest)
    documents = [agent_document_terms(agent) for agent in agents]
    idf = compute_idf(documents)
    average_document_length = sum(len(document) for document in documents) / len(documents)
    query_terms = unique_sorted(tokenize(request) + _synonym_expansions(request, agents))

    scored = [
        _score_agent(agent, query_terms, document, idf, average_document_length, k1, b)
        for agent, document in zip(agents, documents)
    ]
    ranked = sorted(scored, key=lambda item: (-item["score"], item["agent_id"]))
    selected = [
        item["agent_id"]
        for item in ranked
        if item["score"] > 0 and not item["excluded_by"]
    ][:top_k]

    subqueries = _split_subqueries(request)
    decomposed = []
    for subquery in subqueries:
        subquery_scored = [
            _score_agent(agent, subquery["terms"], document, idf, average_document_length, k1, b)
            for agent, document in zip(agents, documents)
        ]
        subquery_ranked = sorted(subquery_scored, key=lambda item: (-item["score"], item["agent_id"]))
        candidates = [
            item["agent_id"]
            for item in subquery_ranked
            if item["score"] > 0 and not item["excluded_by"]
        ][:top_k]
        decomposed.append(
            {
                "id": subquery["id"],
                "text": subquery["text"],
                "terms": subquery["terms"],
                "candidate_agent_ids": candidates,
            }
        )

    excluded_agents = [
        {"agent_id": item["agent_id"], "terms": item["excluded_by"]}
        for item in ranked
        if item["excluded_by"]
    ]

    return {
        "version": VERSION,
        "request": request.strip(),
        "query_terms": query_terms,
        "idf": {
            "agent_count": len(agents),
            "average_document_length": round(average_document_length, 2),
        },
        "ranked_agents": ranked,
        "routing_plan": {
            "selected_agent_ids": selected,
            "decomposed_subqueries": decomposed,
            "excluded_agents": excluded_agents,
        },
    }


def load_manifest(path: str) -> dict[str, Any]:
    """Load a JSON manifest from a file path."""
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise RouteLexiconError(f"Manifest file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RouteLexiconError(f"Manifest is not valid JSON: {path}: {exc}") from exc


def read_text_file(path: str) -> str:
    """Read a UTF-8 text file with a clear error."""
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise RouteLexiconError(f"Request file not found: {path}") from exc


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Create BM25-style routing plans from a user request and JSON agent manifest."
    )
    parser.add_argument("--manifest", help="Path to a JSON manifest with an agents array.")
    parser.add_argument("--query", help="Request text to route.")
    parser.add_argument("--query-file", help="Path to a UTF-8 text file containing the request.")
    parser.add_argument("--top-k", type=int, default=None, help="Number of selected agents to return.")
    parser.add_argument("--k1", type=float, default=None, help="BM25 term saturation parameter.")
    parser.add_argument("--b", type=float, default=None, help="BM25 document-length normalization parameter.")
    parser.add_argument("--output", help="Write the JSON result to this file instead of stdout.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    parser.add_argument("--selftest", action="store_true", help="Run on built-in sample data without API keys.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        top_k = args.top_k if args.top_k is not None else _parse_int_env("ROUTELEXICON_TOP_K", 3)
        k1 = args.k1 if args.k1 is not None else _parse_float_env("ROUTELEXICON_K1", 1.5)
        b = args.b if args.b is not None else _parse_float_env("ROUTELEXICON_B", 0.75)

        if args.selftest or not argv:
            request = SAMPLE_REQUEST
            manifest = SAMPLE_MANIFEST
        else:
            if not args.manifest:
                raise RouteLexiconError("Missing --manifest. Use --selftest for built-in sample data.")
            if bool(args.query) == bool(args.query_file):
                raise RouteLexiconError("Provide exactly one of --query or --query-file.")
            request = args.query if args.query is not None else read_text_file(args.query_file)
            manifest = load_manifest(args.manifest)

        result = route_request(request, manifest, top_k=top_k, k1=k1, b=b)
        output = json.dumps(result, indent=2 if args.pretty else None, sort_keys=False)
        if args.output:
            Path(args.output).write_text(output + "\n", encoding="utf-8")
        else:
            print(output)
        return 0
    except RouteLexiconError as exc:
        print(f"routelexicon: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
