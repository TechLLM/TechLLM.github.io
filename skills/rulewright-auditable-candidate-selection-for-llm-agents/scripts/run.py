#!/usr/bin/env python3
"""Rulewright reference CLI for auditable candidate selection.

The implementation is intentionally small, deterministic, and standard-library
only. It builds a structured comparison policy, scores each candidate against
that policy, and emits machine-readable selection artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple


STOPWORDS = {
    "a",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "best",
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
    "use",
    "with",
}

RISK_TERMS = {
    "api key",
    "password",
    "private",
    "secret",
    "ssn",
    "token",
}


def sample_input() -> Dict[str, Any]:
    """Return built-in sample data for self-tests and examples."""
    return {
        "query": "Select the best candidate for auditable LLM retrieval reranking with explicit rules and reproducible decision traces.",
        "max_selected": 1,
        "candidates": [
            {
                "id": "doc-rules-first",
                "title": "Rule-first retrieval reranking",
                "text": (
                    "Defines explicit comparison rules before scoring retrieval "
                    "candidates. Produces rules.yaml, decision_matrix.json, "
                    "selected_ids, and reproducible audit traces for LLM agents."
                ),
                "tags": ["retrieval", "reranking", "audit", "llm"],
            },
            {
                "id": "doc-fast-summary",
                "title": "Fast summary generation",
                "text": (
                    "Summarizes long documents quickly and returns a concise "
                    "answer, but does not preserve per-candidate selection "
                    "evidence or deterministic replay artifacts."
                ),
                "tags": ["summarization", "latency"],
            },
            {
                "id": "doc-secret-cache",
                "title": "Private cache shortcut",
                "text": (
                    "Uses a private token and secret cache to choose an answer "
                    "without exposing rules or auditable scoring details."
                ),
                "tags": ["shortcut", "private"],
            },
        ],
    }


def load_runtime_config(env: Mapping[str, str] | None = None) -> Dict[str, Any]:
    """Read optional provider settings from environment variables.

    The API key is converted to a boolean presence flag so secret values are not
    returned, logged, or written to artifacts.
    """
    env = env or os.environ
    return {
        "provider": env.get("RULEWRIGHT_PROVIDER", "deterministic-local"),
        "model": env.get("RULEWRIGHT_MODEL", "local-heuristic-v1"),
        "api_key_present": bool(env.get("RULEWRIGHT_API_KEY")),
    }


def tokenize(value: Any) -> List[str]:
    """Tokenize strings, lists, and simple values into lowercase word tokens."""
    if isinstance(value, list):
        value = " ".join(str(item) for item in value)
    text = str(value or "").lower()
    return [token for token in re.findall(r"[a-z0-9]+", text) if token not in STOPWORDS]


def unique_terms(tokens: Iterable[str]) -> List[str]:
    """Return sorted unique tokens for deterministic evidence fields."""
    return sorted(set(tokens))


def generate_rules(payload: Mapping[str, Any], config: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    """Generate a deterministic comparison policy for a candidate selection task."""
    query = require_string(payload.get("query"), "query")
    max_selected = payload.get("max_selected", 1)
    if not isinstance(max_selected, int) or max_selected < 1:
        raise ValueError("max_selected must be a positive integer")
    config = config or load_runtime_config()
    return {
        "version": 1,
        "query": query,
        "selection": {
            "max_selected": max_selected,
            "min_score": 0.55,
            "tie_breakers": ["total_score_desc", "candidate_id_asc"],
        },
        "dimensions": [
            {
                "name": "relevance",
                "weight": 0.5,
                "description": "Overlap with query terms and stated task intent.",
            },
            {
                "name": "specificity",
                "weight": 0.25,
                "description": "Concrete implementation details, artifacts, and operational signals.",
            },
            {
                "name": "source_fit",
                "weight": 0.15,
                "description": "Title and tags align with the query context.",
            },
            {
                "name": "low_risk",
                "weight": 0.1,
                "description": "Candidate avoids secrets, private data, and opaque shortcuts.",
            },
        ],
        "constraints": {
            "require_id": True,
            "require_nonempty_text": True,
            "allow_external_calls": False,
        },
        "rejection_conditions": [
            {
                "code": "missing_id",
                "description": "Candidate lacks a stable id.",
            },
            {
                "code": "empty_text",
                "description": "Candidate has no text to evaluate.",
            },
            {
                "code": "unsafe_secret_handling",
                "description": "Candidate appears to rely on secrets or private data exposure.",
            },
        ],
        "metadata": {
            "policy_builder": config.get("provider", "deterministic-local"),
            "model": config.get("model", "local-heuristic-v1"),
        },
    }


def evaluate_candidates(payload: Mapping[str, Any], rules: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    """Score candidates with a policy and return the full decision matrix."""
    query = require_string(payload.get("query"), "query")
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("candidates must be a list")
    rules = dict(rules or generate_rules(payload))
    validate_rules(rules)

    dimensions = rules["dimensions"]
    min_score = float(rules["selection"]["min_score"])
    max_selected = int(rules["selection"]["max_selected"])
    query_terms = unique_terms(tokenize(query))
    rows = []

    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            raise ValueError(f"candidate at index {index} must be an object")
        row = score_candidate(candidate, query_terms, dimensions, min_score)
        rows.append(row)

    selectable = [row for row in rows if row["passed"]]
    selectable.sort(key=lambda row: (-row["total_score"], str(row["id"])))
    selected_ids = [row["id"] for row in selectable[:max_selected]]

    return {
        "query": query,
        "rules_fingerprint": rules_fingerprint(rules),
        "selected_ids": selected_ids,
        "candidates": rows,
    }


def score_candidate(
    candidate: Mapping[str, Any],
    query_terms: Sequence[str],
    dimensions: Sequence[Mapping[str, Any]],
    min_score: float,
) -> Dict[str, Any]:
    """Score one candidate and return an auditable decision row."""
    candidate_id = str(candidate.get("id", "")).strip()
    title = str(candidate.get("title", "") or "")
    text = str(candidate.get("text", "") or "")
    tags = candidate.get("tags", [])
    tags_text = " ".join(str(tag) for tag in tags) if isinstance(tags, list) else str(tags or "")

    candidate_tokens = unique_terms(tokenize([title, text, tags_text]))
    title_tag_tokens = unique_terms(tokenize([title, tags_text]))
    matched_terms = [term for term in query_terms if term in candidate_tokens]
    matched_title_tag_terms = [term for term in query_terms if term in title_tag_tokens]

    rejection_reasons: List[str] = []
    if not candidate_id:
        rejection_reasons.append("missing_id")
    if not text.strip():
        rejection_reasons.append("empty_text")
    if contains_risk_phrase(text) and ("secret" in text.lower() or "private" in text.lower()):
        rejection_reasons.append("unsafe_secret_handling")

    relevance = ratio(len(matched_terms), len(query_terms))
    specificity = specificity_score(text)
    source_fit = min(1.0, 0.35 + ratio(len(matched_title_tag_terms), max(1, len(query_terms))) * 1.3)
    low_risk = low_risk_score(text)

    raw_scores = {
        "relevance": round(relevance, 3),
        "specificity": round(specificity, 3),
        "source_fit": round(source_fit, 3),
        "low_risk": round(low_risk, 3),
    }
    weighted_scores: Dict[str, float] = {}
    total = 0.0
    for dimension in dimensions:
        name = str(dimension["name"])
        weight = float(dimension["weight"])
        value = raw_scores[name]
        weighted = round(value * weight, 4)
        weighted_scores[name] = weighted
        total += weighted

    total_score = round(total, 3)
    rejected = bool(rejection_reasons)
    passed = (not rejected) and total_score >= min_score
    return {
        "id": candidate_id or None,
        "passed": passed,
        "rejected": rejected,
        "rejection_reasons": rejection_reasons,
        "total_score": total_score,
        "dimension_scores": raw_scores,
        "weighted_scores": weighted_scores,
        "evidence": {
            "matched_query_terms": matched_terms,
            "matched_title_or_tag_terms": matched_title_tag_terms,
            "excerpt": excerpt(text),
        },
    }


def specificity_score(text: str) -> float:
    """Estimate whether a candidate contains concrete, operational detail."""
    tokens = tokenize(text)
    if not tokens:
        return 0.0
    unique_count = len(set(tokens))
    artifact_hits = sum(1 for marker in ("json", "yaml", "ids", "rules", "matrix", "trace") if marker in text.lower())
    length_component = min(0.8, unique_count / 32.0)
    artifact_component = min(0.2, artifact_hits * 0.05)
    return round(min(1.0, length_component + artifact_component), 3)


def low_risk_score(text: str) -> float:
    """Return a high score when the candidate avoids risky secret handling."""
    lower = text.lower()
    penalty = 0.0
    for phrase in RISK_TERMS:
        if phrase in lower:
            penalty += 0.2
    if "without exposing" in lower or "does not expose" in lower:
        penalty = max(0.0, penalty - 0.2)
    return round(max(0.0, 1.0 - penalty), 3)


def contains_risk_phrase(text: str) -> bool:
    """Detect obvious risk phrases used by the reference rejection policy."""
    lower = text.lower()
    return any(phrase in lower for phrase in RISK_TERMS)


def ratio(numerator: int, denominator: int) -> float:
    """Return a bounded ratio with zero-safe denominator handling."""
    if denominator <= 0:
        return 0.0
    return max(0.0, min(1.0, numerator / denominator))


def excerpt(text: str, max_chars: int = 160) -> str:
    """Create a short deterministic evidence excerpt."""
    normalized = " ".join(text.split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 3].rstrip() + "..."


def rules_fingerprint(rules: Mapping[str, Any]) -> str:
    """Return a stable short fingerprint for a rules object."""
    canonical = json.dumps(rules, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def rules_to_yaml(rules: Mapping[str, Any]) -> str:
    """Serialize the Rulewright policy shape to simple YAML."""
    lines = [
        f"version: {int(rules['version'])}",
        f"query: {json.dumps(str(rules['query']))}",
        "selection:",
        f"  max_selected: {int(rules['selection']['max_selected'])}",
        f"  min_score: {float(rules['selection']['min_score'])}",
        f"  tie_breakers: {json.dumps(list(rules['selection']['tie_breakers']))}",
        "dimensions:",
    ]
    for dimension in rules["dimensions"]:
        lines.extend(
            [
                f"  - name: {json.dumps(str(dimension['name']))}",
                f"    weight: {float(dimension['weight'])}",
                f"    description: {json.dumps(str(dimension['description']))}",
            ]
        )
    lines.append("constraints:")
    for key in sorted(rules["constraints"]):
        lines.append(f"  {key}: {scalar_to_yaml(rules['constraints'][key])}")
    lines.append("rejection_conditions:")
    for condition in rules["rejection_conditions"]:
        lines.extend(
            [
                f"  - code: {json.dumps(str(condition['code']))}",
                f"    description: {json.dumps(str(condition['description']))}",
            ]
        )
    lines.append("metadata:")
    for key in sorted(rules.get("metadata", {})):
        lines.append(f"  {key}: {scalar_to_yaml(rules['metadata'][key])}")
    return "\n".join(lines) + "\n"


def rules_from_yaml(text: str) -> Dict[str, Any]:
    """Parse the simple YAML shape emitted by ``rules_to_yaml``."""
    stripped = text.strip()
    if not stripped:
        raise ValueError("rules file is empty")
    if stripped.startswith("{"):
        loaded = json.loads(stripped)
        validate_rules(loaded)
        return loaded

    rules: Dict[str, Any] = {}
    section = ""
    current_item: MutableMapping[str, Any] | None = None
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if indent == 0:
            key, value = split_key_value(line)
            if value == "":
                section = key
                if key in {"dimensions", "rejection_conditions"}:
                    rules[key] = []
                else:
                    rules[key] = {}
            else:
                rules[key] = parse_scalar(value)
                section = ""
            current_item = None
            continue

        if section in {"selection", "constraints", "metadata"}:
            key, value = split_key_value(line)
            rules[section][key] = parse_scalar(value)
            continue

        if section in {"dimensions", "rejection_conditions"}:
            if line.startswith("- "):
                current_item = {}
                rules[section].append(current_item)
                remainder = line[2:].strip()
                if remainder:
                    key, value = split_key_value(remainder)
                    current_item[key] = parse_scalar(value)
            elif current_item is not None:
                key, value = split_key_value(line)
                current_item[key] = parse_scalar(value)
            else:
                raise ValueError(f"invalid list item in rules YAML: {raw_line}")
            continue

        raise ValueError(f"unsupported rules YAML line: {raw_line}")

    validate_rules(rules)
    return rules


def scalar_to_yaml(value: Any) -> str:
    """Serialize a scalar or list to a YAML-compatible literal."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return json.dumps(value)
    return json.dumps(str(value))


def split_key_value(line: str) -> Tuple[str, str]:
    """Split a simple ``key: value`` line with a helpful error on failure."""
    if ":" not in line:
        raise ValueError(f"expected 'key: value' in rules YAML line: {line}")
    key, value = line.split(":", 1)
    return key.strip(), value.strip()


def parse_scalar(value: str) -> Any:
    """Parse a YAML-compatible scalar emitted by this script."""
    if value in {"true", "false"}:
        return value == "true"
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            return value


def validate_rules(rules: Mapping[str, Any]) -> None:
    """Validate the minimal Rulewright policy shape."""
    required = {"version", "query", "selection", "dimensions", "constraints", "rejection_conditions"}
    missing = sorted(required - set(rules))
    if missing:
        raise ValueError(f"rules missing required field(s): {', '.join(missing)}")
    dimensions = rules.get("dimensions")
    if not isinstance(dimensions, list) or not dimensions:
        raise ValueError("rules.dimensions must be a non-empty list")
    names = {dimension.get("name") for dimension in dimensions if isinstance(dimension, dict)}
    expected = {"relevance", "specificity", "source_fit", "low_risk"}
    if names != expected:
        raise ValueError("rules.dimensions must contain relevance, specificity, source_fit, and low_risk")
    total_weight = sum(float(dimension["weight"]) for dimension in dimensions)
    if round(total_weight, 6) != 1.0:
        raise ValueError("rules.dimension weights must sum to 1.0")
    selection = rules.get("selection")
    if not isinstance(selection, dict):
        raise ValueError("rules.selection must be an object")
    if int(selection.get("max_selected", 0)) < 1:
        raise ValueError("rules.selection.max_selected must be at least 1")
    min_score = float(selection.get("min_score", -1))
    if not 0 <= min_score <= 1:
        raise ValueError("rules.selection.min_score must be between 0 and 1")


def require_string(value: Any, field_name: str) -> str:
    """Return a non-empty string field or raise a clear ValueError."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON object from disk with clear error messages."""
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise ValueError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"input JSON must be an object: {path}")
    return data


def write_text(path: Path, text: str) -> None:
    """Write UTF-8 text to a path, creating parent directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the Rulewright command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate auditable candidate-selection artifacts for LLM agents."
    )
    parser.add_argument("--input", type=Path, help="JSON file containing query and candidates.")
    parser.add_argument("--rules-in", type=Path, help="Replay with an existing rules.yaml file.")
    parser.add_argument("--rules-out", type=Path, help="Write generated rules.yaml to this path.")
    parser.add_argument("--matrix-out", type=Path, help="Write decision_matrix.json to this path.")
    parser.add_argument("--selected-out", type=Path, help="Write selected_ids.json to this path.")
    parser.add_argument("--selftest", action="store_true", help="Run the built-in sample without external services.")
    return parser


def run_cli(argv: Sequence[str] | None = None) -> int:
    """Execute the CLI and return a process exit code."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        payload = sample_input() if args.selftest or not args.input else load_json_file(args.input)
        if args.rules_in:
            rules = rules_from_yaml(args.rules_in.read_text(encoding="utf-8"))
        else:
            rules = generate_rules(payload)

        matrix = evaluate_candidates(payload, rules)
        if args.rules_out and not args.rules_in:
            write_text(args.rules_out, rules_to_yaml(rules))
        if args.matrix_out:
            write_text(args.matrix_out, json.dumps(matrix, indent=2, sort_keys=True) + "\n")
        if args.selected_out:
            write_text(args.selected_out, json.dumps(matrix["selected_ids"], indent=2) + "\n")

        if args.selftest or not (args.matrix_out or args.selected_out):
            selected_score = None
            if matrix["selected_ids"]:
                selected_id = matrix["selected_ids"][0]
                selected_row = next(row for row in matrix["candidates"] if row["id"] == selected_id)
                selected_score = selected_row["total_score"]
            summary = {
                "selected_ids": matrix["selected_ids"],
                "top_score": selected_score,
            }
            print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def main() -> None:
    """CLI entry point."""
    raise SystemExit(run_cli())


if __name__ == "__main__":
    main()
