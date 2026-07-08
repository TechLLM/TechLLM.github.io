#!/usr/bin/env python3
"""PathLoom reference CLI for critical-path prioritization of agent traces.

The script reads local JSONL trace items, builds dependency edges, scores each
item for critical-path relevance, and emits deterministic JSON recommendations.
It uses only the Python standard library and reads optional non-secret settings
from environment variables.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import deque
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


DEFAULT_WEIGHTS = {
    "recency": 0.20,
    "dependency": 0.45,
    "explicit": 0.25,
    "type": 0.10,
}

DEFAULT_TYPE_SCORES = {
    "next_action": 1.00,
    "constraint": 0.95,
    "tool_result": 0.90,
    "observation": 0.85,
    "tool_call": 0.80,
    "result": 0.75,
    "message": 0.55,
    "memory": 0.45,
    "note": 0.35,
    "archive": 0.20,
}

DEPENDENCY_FIELDS = (
    "depends_on",
    "references",
    "input_ids",
    "source_ids",
    "parent_id",
    "tool_call_id",
    "observation_id",
)

SAMPLE_TRACE = [
    {
        "id": "u1",
        "type": "message",
        "timestamp": "2026-01-01T10:00:00Z",
        "content": "User asks to fix the export bug.",
    },
    {
        "id": "c1",
        "type": "constraint",
        "timestamp": "2026-01-01T10:01:00Z",
        "content": "Do not change the public API.",
    },
    {
        "id": "t1",
        "type": "tool_call",
        "timestamp": "2026-01-01T10:02:00Z",
        "content": "Inspect exporter module.",
        "depends_on": ["u1", "c1"],
    },
    {
        "id": "o1",
        "type": "observation",
        "timestamp": "2026-01-01T10:03:00Z",
        "content": "export_csv fails when rows are empty.",
        "depends_on": ["t1"],
    },
    {
        "id": "m1",
        "type": "memory",
        "timestamp": "2026-01-01T10:04:00Z",
        "content": "Old design discussion about report colors.",
    },
    {
        "id": "m2",
        "type": "note",
        "timestamp": "2026-01-01T10:05:00Z",
        "content": "Old design discussion about report colors.",
    },
    {
        "id": "t2",
        "type": "tool_call",
        "timestamp": "2026-01-01T10:06:00Z",
        "content": "Patch exporter using observation @o1 and constraint @c1.",
        "depends_on": ["o1", "c1"],
    },
    {
        "id": "next",
        "type": "next_action",
        "timestamp": "2026-01-01T10:07:00Z",
        "content": "Run tests for patch t2 using evidence o1 and constraint c1.",
        "references": ["t2", "o1", "c1"],
    },
]


class PathLoomError(ValueError):
    """Raised when trace input or CLI configuration is invalid."""


def normalize_weight_map(raw: Mapping[str, float]) -> Dict[str, float]:
    """Return a complete weight map normalized to sum to one."""
    weights = dict(DEFAULT_WEIGHTS)
    for key, value in raw.items():
        if key not in DEFAULT_WEIGHTS:
            raise PathLoomError(f"unknown weight '{key}'; expected one of {sorted(DEFAULT_WEIGHTS)}")
        if value < 0:
            raise PathLoomError(f"weight '{key}' must be non-negative")
        weights[key] = value
    total = sum(weights.values())
    if total <= 0:
        raise PathLoomError("at least one scoring weight must be greater than zero")
    return {key: value / total for key, value in weights.items()}


def parse_weights(text: Optional[str]) -> Dict[str, float]:
    """Parse comma-separated weights such as 'recency=0.2,dependency=0.45'."""
    if not text:
        return normalize_weight_map({})
    parsed: Dict[str, float] = {}
    for part in text.split(","):
        piece = part.strip()
        if not piece:
            continue
        if "=" not in piece:
            raise PathLoomError(f"invalid weight '{piece}'; use key=value")
        key, raw_value = piece.split("=", 1)
        key = key.strip()
        try:
            parsed[key] = float(raw_value.strip())
        except ValueError as exc:
            raise PathLoomError(f"invalid numeric weight for '{key}': {raw_value!r}") from exc
    return normalize_weight_map(parsed)


def parse_threshold(value: Optional[str], default: float, name: str) -> float:
    """Parse a threshold from text, enforcing the inclusive range 0..1."""
    if value is None or value == "":
        return default
    try:
        parsed = float(value)
    except ValueError as exc:
        raise PathLoomError(f"{name} must be a number between 0 and 1") from exc
    if not 0 <= parsed <= 1:
        raise PathLoomError(f"{name} must be between 0 and 1")
    return parsed


def read_jsonl(path: Optional[str]) -> List[Dict[str, Any]]:
    """Read trace items from a JSONL file, stdin, or built-in sample data."""
    if not path:
        return [dict(item) for item in SAMPLE_TRACE]
    if path == "-":
        lines = sys.stdin.read().splitlines()
    else:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                lines = handle.read().splitlines()
        except OSError as exc:
            raise PathLoomError(f"could not read input file '{path}': {exc}") from exc

    items: List[Dict[str, Any]] = []
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PathLoomError(f"line {number} is not valid JSON: {exc.msg}") from exc
        if not isinstance(value, dict):
            raise PathLoomError(f"line {number} must contain a JSON object")
        items.append(value)
    return items


def validate_items(items: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Validate trace items and return normalized shallow copies."""
    if not items:
        raise PathLoomError("trace is empty; provide at least one JSONL item")
    normalized: List[Dict[str, Any]] = []
    seen = set()
    for index, item in enumerate(items, start=1):
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id.strip():
            raise PathLoomError(f"item {index} is missing a non-empty string 'id'")
        if item_id in seen:
            raise PathLoomError(f"duplicate item id '{item_id}'")
        seen.add(item_id)
        copied = dict(item)
        copied["id"] = item_id.strip()
        copied["type"] = str(copied.get("type", "message")).strip() or "message"
        normalized.append(copied)
    return normalized


def as_list(value: Any) -> List[str]:
    """Coerce a scalar or list-like dependency field into a string list."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return [str(part) for part in value if str(part)]
    return [str(value)]


def item_text(item: Mapping[str, Any]) -> str:
    """Return the best-effort human text attached to a trace item."""
    for key in ("content", "text", "message", "summary", "action"):
        value = item.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def ids_mentioned_in_text(text: str, ids: Iterable[str], strict_marker: bool = True) -> List[str]:
    """Find ids mentioned in text, optionally requiring @id or #id markers."""
    found = []
    for item_id in sorted(ids, key=lambda value: (-len(value), value)):
        if strict_marker:
            pattern = rf"(?<![\w.-])[@#]{re.escape(item_id)}(?![\w.-])"
        else:
            pattern = rf"(?<![\w.-])(?:[@#])?{re.escape(item_id)}(?![\w.-])"
        if re.search(pattern, text):
            found.append(item_id)
    return found


def dependency_values(item: Mapping[str, Any], known_ids: Iterable[str]) -> List[Tuple[str, str]]:
    """Extract dependency ids and their source field from one trace item."""
    known = set(known_ids)
    values: List[Tuple[str, str]] = []
    for field in DEPENDENCY_FIELDS:
        for raw in as_list(item.get(field)):
            if raw in known and raw != item.get("id"):
                values.append((raw, field))
    for mentioned in ids_mentioned_in_text(item_text(item), known, strict_marker=True):
        if mentioned != item.get("id"):
            values.append((mentioned, "text_marker"))

    deduped: List[Tuple[str, str]] = []
    seen = set()
    for dep_id, reason in values:
        key = (dep_id, reason)
        if key not in seen:
            seen.add(key)
            deduped.append((dep_id, reason))
    return deduped


def build_edges(items: Sequence[Mapping[str, Any]]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]], List[Dict[str, str]]]:
    """Build dependency maps and edge records from normalized trace items."""
    ids = [str(item["id"]) for item in items]
    depends_on: Dict[str, List[str]] = {item_id: [] for item_id in ids}
    referenced_by: Dict[str, List[str]] = {item_id: [] for item_id in ids}
    edges: List[Dict[str, str]] = []

    for item in items:
        source = str(item["id"])
        for dep_id, reason in dependency_values(item, ids):
            if dep_id not in depends_on[source]:
                depends_on[source].append(dep_id)
                referenced_by[dep_id].append(source)
                edges.append({"from": source, "to": dep_id, "reason": reason})
    return depends_on, referenced_by, edges


def find_next_action_context(items: Sequence[Mapping[str, Any]], next_action: Optional[str]) -> Tuple[str, List[str]]:
    """Return next-action text and ids directly referenced by the next action."""
    ids = [str(item["id"]) for item in items]
    explicit_refs: List[str] = []
    text_parts: List[str] = []

    if next_action:
        text_parts.append(next_action)
        explicit_refs.extend(ids_mentioned_in_text(next_action, ids, strict_marker=False))

    for item in items:
        if item.get("type") == "next_action" or item.get("next_action") is True:
            text = item_text(item)
            if text:
                text_parts.append(text)
            explicit_refs.extend(dep_id for dep_id, _reason in dependency_values(item, ids))

    if not explicit_refs and ids:
        explicit_refs.append(ids[-1])

    deduped: List[str] = []
    seen = set()
    for item_id in explicit_refs:
        if item_id in ids and item_id not in seen:
            seen.add(item_id)
            deduped.append(item_id)
    return " ".join(text_parts).strip(), deduped


def dependency_distances(seeds: Sequence[str], depends_on: Mapping[str, Sequence[str]]) -> Dict[str, int]:
    """Compute distance from seed ids backward through dependencies."""
    distances: Dict[str, int] = {}
    queue: deque[Tuple[str, int]] = deque((seed, 0) for seed in seeds)
    while queue:
        item_id, distance = queue.popleft()
        if item_id in distances and distances[item_id] <= distance:
            continue
        distances[item_id] = distance
        for dep_id in depends_on.get(item_id, []):
            queue.append((dep_id, distance + 1))
    return distances


def duplicate_map(items: Sequence[Mapping[str, Any]]) -> Dict[str, str]:
    """Return a map from duplicate item id to the first item id with same content."""
    first_by_text: Dict[str, str] = {}
    duplicates: Dict[str, str] = {}
    for item in items:
        normalized = re.sub(r"\s+", " ", item_text(item).strip().lower())
        if not normalized:
            continue
        item_id = str(item["id"])
        if normalized in first_by_text:
            duplicates[item_id] = first_by_text[normalized]
        else:
            first_by_text[normalized] = item_id
    return duplicates


def recommendation_for(score: float, duplicate_of: Optional[str], prefetch_threshold: float, prune_threshold: float) -> str:
    """Convert a priority score and duplicate status into a recommendation label."""
    if duplicate_of and score < prefetch_threshold:
        return "prune"
    if score >= prefetch_threshold:
        return "prefetch"
    if score <= prune_threshold:
        return "prune"
    if score < 0.50:
        return "delay"
    return "keep"


def prioritize_trace(
    items: Sequence[Mapping[str, Any]],
    *,
    weights: Optional[Mapping[str, float]] = None,
    next_action: Optional[str] = None,
    prefetch_threshold: float = 0.72,
    prune_threshold: float = 0.28,
) -> Dict[str, Any]:
    """Score trace items and return sorted critical-path recommendations."""
    normalized = validate_items(items)
    weight_map = normalize_weight_map(weights or {})
    depends_on, referenced_by, edges = build_edges(normalized)
    next_action_text, explicit_refs = find_next_action_context(normalized, next_action)
    distances = dependency_distances(explicit_refs, depends_on)
    duplicates = duplicate_map(normalized)
    total_items = len(normalized)
    rows: List[Dict[str, Any]] = []

    for index, item in enumerate(normalized):
        item_id = str(item["id"])
        item_type = str(item.get("type", "message"))
        recency_score = (index + 1) / total_items
        distance = distances.get(item_id)
        dependency_score = 0.0 if distance is None else 1 / (1 + distance)
        explicit_score = 1.0 if item_id in explicit_refs else min(1.0, len(referenced_by[item_id]) / 2)
        type_score = DEFAULT_TYPE_SCORES.get(item_type, 0.50)
        duplicate_of = duplicates.get(item_id)
        score = (
            weight_map["recency"] * recency_score
            + weight_map["dependency"] * dependency_score
            + weight_map["explicit"] * explicit_score
            + weight_map["type"] * type_score
        )
        if duplicate_of:
            score = min(score, 0.30)
        score = round(score, 3)

        reasons = []
        if item_id in explicit_refs:
            reasons.append("directly referenced by next action")
        if distance == 0:
            reasons.append("seed item for critical path")
        elif distance is not None:
            reasons.append(f"dependency path distance {distance} from next action")
        if referenced_by[item_id]:
            reasons.append(f"referenced by {len(referenced_by[item_id])} item(s)")
        if recency_score >= 0.75:
            reasons.append("recent trace item")
        reasons.append(f"type score {type_score:.2f} for {item_type}")
        if duplicate_of:
            reasons.append(f"duplicate content of {duplicate_of}")

        recommendation = recommendation_for(score, duplicate_of, prefetch_threshold, prune_threshold)
        rows.append(
            {
                "id": item_id,
                "type": item_type,
                "critical_path_priority": score,
                "recommendation": recommendation,
                "depends_on": depends_on[item_id],
                "referenced_by": referenced_by[item_id],
                "reasons": reasons,
                "_index": index,
            }
        )

    rows.sort(key=lambda row: (-row["critical_path_priority"], row["_index"], row["id"]))
    for row in rows:
        del row["_index"]

    recommendations = {"prefetch": [], "keep": [], "delay": [], "prune": []}
    for row in rows:
        label = row["recommendation"]
        recommendations[label].append(
            {
                "id": row["id"],
                "priority": row["critical_path_priority"],
                "why": row["reasons"][0] if row["reasons"] else "scored by PathLoom rules",
            }
        )

    return {
        "summary": {
            "item_count": total_items,
            "edge_count": len(edges),
            "next_action": next_action_text,
            "weights": {key: round(value, 3) for key, value in weight_map.items()},
            "thresholds": {
                "prefetch": prefetch_threshold,
                "prune": prune_threshold,
            },
        },
        "items": rows,
        "edges": edges,
        "recommendations": recommendations,
    }


def write_output(result: Mapping[str, Any], output_path: Optional[str]) -> None:
    """Write result JSON to stdout or a file."""
    text = json.dumps(result, indent=2, sort_keys=False) + "\n"
    if output_path:
        try:
            with open(output_path, "w", encoding="utf-8") as handle:
                handle.write(text)
        except OSError as exc:
            raise PathLoomError(f"could not write output file '{output_path}': {exc}") from exc
    else:
        sys.stdout.write(text)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Prioritize agent trace JSONL by critical-path relevance.",
    )
    parser.add_argument("--input", "-i", help="Trace JSONL file path, or '-' for stdin. Defaults to built-in sample data.")
    parser.add_argument("--output", "-o", help="Optional path for JSON output. Defaults to stdout.")
    parser.add_argument("--next-action", help="Optional text describing the next action to score against.")
    parser.add_argument(
        "--weights",
        help="Comma-separated score weights, for example 'recency=0.2,dependency=0.45,explicit=0.25,type=0.1'.",
    )
    parser.add_argument("--prefetch-threshold", help="Recommendation threshold for prefetch, default 0.72.")
    parser.add_argument("--prune-threshold", help="Recommendation threshold for prune, default 0.28.")
    parser.add_argument("--selftest", action="store_true", help="Run on built-in sample data with no API key or external files.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        weights = parse_weights(args.weights or os.environ.get("PATHLOOM_WEIGHTS"))
        next_action = args.next_action or os.environ.get("PATHLOOM_NEXT_ACTION")
        prefetch_threshold = parse_threshold(
            args.prefetch_threshold or os.environ.get("PATHLOOM_PREFETCH_THRESHOLD"),
            0.72,
            "prefetch threshold",
        )
        prune_threshold = parse_threshold(
            args.prune_threshold or os.environ.get("PATHLOOM_PRUNE_THRESHOLD"),
            0.28,
            "prune threshold",
        )
        input_path = None if args.selftest else args.input
        items = read_jsonl(input_path)
        result = prioritize_trace(
            items,
            weights=weights,
            next_action=next_action,
            prefetch_threshold=prefetch_threshold,
            prune_threshold=prune_threshold,
        )
        write_output(result, args.output)
        return 0
    except PathLoomError as exc:
        sys.stderr.write(f"PathLoom error: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
