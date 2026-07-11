#!/usr/bin/env python3
"""SurfacePilot CLI for profiling LLM agent failure surfaces from JSONL traces.

The implementation is intentionally small, deterministic, and dependency-free.
It reads trace events, aggregates pass/fail evidence across execution surfaces,
detects repeated failure signals, and emits a YAML or JSON routing policy.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple


DEFAULT_FAILURE_THRESHOLD = 0.34
DEFAULT_MIN_FAILURES = 1

KNOWN_SURFACES = {
    "retrieval",
    "file_edit",
    "api_call",
    "calculation",
    "citation",
    "state_change",
    "planning",
}

PASS_VALUES = {"pass", "passed", "success", "successful", "ok", "true", "yes"}
FAIL_VALUES = {"fail", "failed", "failure", "error", "false", "no", "blocked"}

SAMPLE_JSONL = """
{"task_id":"task-001","task_type":"support_qa","model":"small-router","route":"rag_fast","tool":"retriever","surface":"retrieval","success":false,"signal":"stale_retrieval","message":"retrieved outdated policy text"}
{"task_id":"task-001","task_type":"support_qa","model":"small-router","route":"rag_fast","tool":"citation_checker","surface":"citation","success":false,"signal":"unsupported_citation","message":"answer cited a source that was not present"}
{"task_id":"task-002","task_type":"support_qa","model":"large-router","route":"rag_verified","tool":"retriever","surface":"retrieval","success":true,"signal":"fresh_retrieval","message":"retrieved current policy text"}
{"task_id":"task-003","task_type":"code_edit","model":"small-router","route":"edit_direct","tool":"filesystem","surface":"file_edit","success":false,"signal":"unsafe_edit","message":"patch touched an unrelated file"}
{"task_id":"task-004","task_type":"ops","model":"small-router","route":"api_direct","tool":"billing_api","surface":"api_call","success":false,"signal":"malformed_api_call","message":"request body missed a required field"}
""".strip()

SURFACE_ACTIONS = {
    "retrieval": [
        "prefer verified retrieval routes for this task type",
        "require freshness and coverage checks before answering",
        "fallback to an uncertainty response when evidence is weak",
    ],
    "citation": [
        "require citation support checks before final answer",
        "block claims that cannot be tied to retrieved evidence",
        "fallback to a model route with stricter attribution prompts",
    ],
    "file_edit": [
        "require diff validation before final answer",
        "prefer guarded edit routes with tests or dry-run checks",
        "escalate when edits touch unrelated files",
    ],
    "api_call": [
        "validate request schema before execution",
        "prefer routes with dry-run or idempotency safeguards",
        "verify external state after the call",
    ],
    "calculation": [
        "route calculations through a deterministic tool",
        "require unit checks for numeric outputs",
        "fallback to slower verified calculation mode",
    ],
    "state_change": [
        "require explicit user confirmation before state changes",
        "use reversible or dry-run execution when available",
        "verify state after execution",
    ],
    "planning": [
        "add plan quality checks before tool execution",
        "route ambiguous tasks to a stronger planner",
        "require task decomposition for multi-step work",
    ],
}


TraceEvent = Dict[str, Any]
Profile = Dict[str, Any]


def parse_boolish(value: Any, field_name: str) -> bool:
    """Convert common pass/fail field values into a boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in PASS_VALUES:
            return True
        if normalized in FAIL_VALUES:
            return False
    raise ValueError(
        f"field {field_name!r} must be a boolean or a pass/fail string; got {value!r}"
    )


def normalize_event(raw: Mapping[str, Any], line_no: Optional[int] = None) -> TraceEvent:
    """Normalize one raw trace event and validate required pass/fail evidence."""
    if not isinstance(raw, Mapping):
        location = f" on line {line_no}" if line_no is not None else ""
        raise ValueError(f"trace event{location} must be a JSON object")

    surface = str(raw.get("surface", "")).strip()
    if not surface:
        location = f" on line {line_no}" if line_no is not None else ""
        raise ValueError(f"trace event{location} is missing required field 'surface'")

    success_field = None
    success_value = None
    for candidate in ("success", "passed", "status", "outcome", "result"):
        if candidate in raw:
            success_field = candidate
            success_value = raw[candidate]
            break
    if success_field is None:
        location = f" on line {line_no}" if line_no is not None else ""
        raise ValueError(
            f"trace event{location} must include one pass/fail field: "
            "success, passed, status, outcome, or result"
        )

    success = parse_boolish(success_value, success_field)
    signal = str(
        raw.get("signal")
        or raw.get("failure_reason")
        or raw.get("error_type")
        or ("passed" if success else "unspecified_failure")
    ).strip()

    return {
        "task_id": str(raw.get("task_id") or raw.get("task") or "unknown").strip() or "unknown",
        "task_type": str(raw.get("task_type") or raw.get("type") or "unknown").strip()
        or "unknown",
        "model": str(raw.get("model") or "unknown").strip() or "unknown",
        "route": str(raw.get("route") or "unknown").strip() or "unknown",
        "tool": str(raw.get("tool") or "unknown").strip() or "unknown",
        "surface": surface,
        "success": success,
        "signal": signal or ("passed" if success else "unspecified_failure"),
        "message": str(raw.get("message") or raw.get("observation") or "").strip(),
        "is_custom_surface": surface not in KNOWN_SURFACES,
    }


def load_jsonl(path: Path) -> List[TraceEvent]:
    """Load and normalize trace events from a JSONL file."""
    if not path.exists():
        raise ValueError(f"input file does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"input path is not a file: {path}")

    events: List[TraceEvent] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                raw = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON on line {line_no}: {exc.msg}") from exc
            events.append(normalize_event(raw, line_no=line_no))

    if not events:
        raise ValueError(f"input file has no trace events: {path}")
    return events


def sample_events() -> List[TraceEvent]:
    """Return normalized built-in sample events for self-tests and demos."""
    return [
        normalize_event(json.loads(line), line_no=index)
        for index, line in enumerate(SAMPLE_JSONL.splitlines(), start=1)
    ]


def new_count() -> Dict[str, int]:
    """Create an empty pass/fail counter."""
    return {"events": 0, "passed": 0, "failed": 0}


def add_count(bucket: MutableMapping[str, int], success: bool) -> None:
    """Update a pass/fail counter with one event outcome."""
    bucket["events"] += 1
    if success:
        bucket["passed"] += 1
    else:
        bucket["failed"] += 1


def fail_rate(failed: int, total: int) -> float:
    """Return a rounded deterministic failure rate."""
    if total == 0:
        return 0.0
    return round(failed / total, 3)


def count_to_dict(bucket: Mapping[str, int]) -> Dict[str, Any]:
    """Convert an internal pass/fail counter to an output dictionary."""
    return {
        "events": bucket["events"],
        "passed": bucket["passed"],
        "failed": bucket["failed"],
        "fail_rate": fail_rate(bucket["failed"], bucket["events"]),
    }


def top_signals(events: Iterable[TraceEvent], limit: int = 3) -> List[str]:
    """Return the most frequent failed evaluator signals for a group."""
    counts = Counter(event["signal"] for event in events if not event["success"])
    return [
        signal
        for signal, _count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def actions_for_surface(surface: str) -> List[str]:
    """Return deterministic routing recommendations for an execution surface."""
    return SURFACE_ACTIONS.get(
        surface,
        [
            "add evaluator coverage for this custom surface",
            "route ambiguous cases to a safer model or toolchain",
            "escalate when evidence is missing or contradictory",
        ],
    )


def build_profile(
    events: Sequence[TraceEvent],
    failure_threshold: float = DEFAULT_FAILURE_THRESHOLD,
    min_failures: int = DEFAULT_MIN_FAILURES,
) -> Profile:
    """Build a pass/fail surface profile and routing policy from trace events."""
    if not events:
        raise ValueError("at least one trace event is required")
    if not 0 <= failure_threshold <= 1:
        raise ValueError("failure_threshold must be between 0 and 1")
    if min_failures < 1:
        raise ValueError("min_failures must be at least 1")

    total = new_count()
    surface_counts: Dict[str, Dict[str, int]] = defaultdict(new_count)
    matrix_counts: Dict[Tuple[str, str, str, str, str, str], Dict[str, int]] = defaultdict(
        new_count
    )
    policy_groups: Dict[Tuple[str, str], List[TraceEvent]] = defaultdict(list)
    pattern_groups: Dict[Tuple[str, str], List[TraceEvent]] = defaultdict(list)

    for event in events:
        add_count(total, event["success"])
        add_count(surface_counts[event["surface"]], event["success"])
        matrix_key = (
            event["task_type"],
            event["model"],
            event["route"],
            event["tool"],
            event["surface"],
            event["signal"],
        )
        add_count(matrix_counts[matrix_key], event["success"])
        policy_groups[(event["task_type"], event["surface"])].append(event)
        if not event["success"]:
            pattern_groups[(event["signal"], event["surface"])].append(event)

    summary = {
        "events": total["events"],
        "passed": total["passed"],
        "failed": total["failed"],
        "failure_rate": fail_rate(total["failed"], total["events"]),
        "surfaces": {
            surface: count_to_dict(surface_counts[surface])
            for surface in sorted(surface_counts)
        },
    }

    matrix = []
    for key in sorted(matrix_counts):
        task_type, model, route, tool, surface, signal = key
        row = {
            "task_type": task_type,
            "model": model,
            "route": route,
            "tool": tool,
            "surface": surface,
            "signal": signal,
        }
        row.update(count_to_dict(matrix_counts[key]))
        matrix.append(row)

    patterns = []
    for (signal, surface), grouped_events in sorted(
        pattern_groups.items(), key=lambda item: (-len(item[1]), item[0][1], item[0][0])
    ):
        if len(grouped_events) < min_failures:
            continue
        patterns.append(
            {
                "signal": signal,
                "surface": surface,
                "count": len(grouped_events),
                "task_ids": sorted({event["task_id"] for event in grouped_events})[:5],
                "routes": sorted({event["route"] for event in grouped_events}),
                "tools": sorted({event["tool"] for event in grouped_events}),
            }
        )

    candidate_rules = []
    for (task_type, surface), grouped_events in policy_groups.items():
        events_count = len(grouped_events)
        failures = sum(1 for event in grouped_events if not event["success"])
        rate = fail_rate(failures, events_count)
        if failures >= min_failures and rate >= failure_threshold:
            candidate_rules.append((rate, failures, task_type, surface, grouped_events))

    candidate_rules.sort(key=lambda item: (-item[0], -item[1], item[2], item[3]))
    rules = []
    for index, (rate, failures, task_type, surface, grouped_events) in enumerate(
        candidate_rules, start=1
    ):
        rules.append(
            {
                "id": f"surface-rule-{index:03d}",
                "match": {"task_type": task_type, "surface": surface},
                "when": f"fail_rate >= {failure_threshold:g} and failures >= {min_failures}",
                "action": actions_for_surface(surface),
                "evidence": {
                    "events": len(grouped_events),
                    "failures": failures,
                    "fail_rate": rate,
                    "top_signals": top_signals(grouped_events),
                    "routes": sorted({event["route"] for event in grouped_events}),
                    "models": sorted({event["model"] for event in grouped_events}),
                },
            }
        )

    return {
        "summary": summary,
        "matrix": matrix,
        "patterns": patterns,
        "routing_policy": {
            "version": "surfacepilot.policy.v1",
            "thresholds": {
                "failure_threshold": failure_threshold,
                "min_failures": min_failures,
            },
            "rules": rules,
        },
    }


def parse_env_float(name: str, default: float) -> float:
    """Read a float from an environment variable with a clear error."""
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"environment variable {name} must be a float") from exc
    return parsed


def parse_env_int(name: str, default: int) -> int:
    """Read an integer from an environment variable with a clear error."""
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"environment variable {name} must be an integer") from exc
    return parsed


def yaml_scalar(value: Any) -> str:
    """Render a scalar as conservative YAML."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value))


def is_scalar(value: Any) -> bool:
    """Return whether a value can be rendered on one YAML line."""
    return not isinstance(value, (dict, list))


def yaml_lines(value: Any, indent: int = 0) -> List[str]:
    """Render a Python dictionary/list/scalar into deterministic YAML lines."""
    prefix = " " * indent
    if isinstance(value, dict):
        if not value:
            return [prefix + "{}"]
        lines: List[str] = []
        for key, child in value.items():
            if is_scalar(child):
                lines.append(f"{prefix}{key}: {yaml_scalar(child)}")
            elif isinstance(child, list) and not child:
                lines.append(f"{prefix}{key}: []")
            elif isinstance(child, dict) and not child:
                lines.append(f"{prefix}{key}: {{}}")
            else:
                lines.append(f"{prefix}{key}:")
                lines.extend(yaml_lines(child, indent + 2))
        return lines
    if isinstance(value, list):
        if not value:
            return [prefix + "[]"]
        lines = []
        for item in value:
            if is_scalar(item):
                lines.append(f"{prefix}- {yaml_scalar(item)}")
            elif isinstance(item, dict):
                if not item:
                    lines.append(f"{prefix}- {{}}")
                    continue
                first = True
                for key, child in item.items():
                    item_prefix = f"{prefix}- " if first else f"{prefix}  "
                    if is_scalar(child):
                        lines.append(f"{item_prefix}{key}: {yaml_scalar(child)}")
                    elif isinstance(child, list) and not child:
                        lines.append(f"{item_prefix}{key}: []")
                    elif isinstance(child, dict) and not child:
                        lines.append(f"{item_prefix}{key}: {{}}")
                    else:
                        lines.append(f"{item_prefix}{key}:")
                        lines.extend(yaml_lines(child, indent + 4))
                    first = False
            else:
                lines.append(f"{prefix}-")
                lines.extend(yaml_lines(item, indent + 2))
        return lines
    return [prefix + yaml_scalar(value)]


def render_profile(profile: Profile, output_format: str) -> str:
    """Render a profile as YAML or JSON."""
    if output_format == "json":
        return json.dumps(profile, indent=2, ensure_ascii=True) + "\n"
    if output_format == "yaml":
        return "\n".join(yaml_lines(profile)) + "\n"
    raise ValueError(f"unsupported output format: {output_format}")


def assert_selftest_profile(profile: Profile) -> None:
    """Validate the built-in sample profile shape and key deterministic values."""
    required_top_keys = {"summary", "matrix", "patterns", "routing_policy"}
    if set(profile) != required_top_keys:
        raise AssertionError("profile top-level keys changed")
    if profile["summary"]["events"] != 5:
        raise AssertionError("sample event count changed")
    if profile["summary"]["failed"] != 4:
        raise AssertionError("sample failure count changed")
    if not profile["routing_policy"]["rules"]:
        raise AssertionError("sample should produce routing policy rules")


def build_arg_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Profile LLM agent failure surfaces from trace JSONL and export a routing policy.",
        epilog=(
            "Environment: SURFACEPILOT_FAILURE_THRESHOLD and "
            "SURFACEPILOT_MIN_FAILURES may set default thresholds."
        ),
    )
    parser.add_argument("--input", "-i", type=Path, help="Trace JSONL input file.")
    parser.add_argument("--output", "-o", type=Path, help="Write profile to this file.")
    parser.add_argument(
        "--format",
        choices=("yaml", "json"),
        default="yaml",
        help="Output format. Default: yaml.",
    )
    parser.add_argument(
        "--failure-threshold",
        type=float,
        default=None,
        help="Minimum group failure rate for policy rules. Default: env or 0.34.",
    )
    parser.add_argument(
        "--min-failures",
        type=int,
        default=None,
        help="Minimum failed events for patterns and policy rules. Default: env or 1.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run the built-in sample with assertions and print the resulting profile.",
    )
    parser.add_argument("--version", action="version", version="SurfacePilot 0.1.0")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the SurfacePilot command-line interface."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        failure_threshold = (
            args.failure_threshold
            if args.failure_threshold is not None
            else parse_env_float("SURFACEPILOT_FAILURE_THRESHOLD", DEFAULT_FAILURE_THRESHOLD)
        )
        min_failures = (
            args.min_failures
            if args.min_failures is not None
            else parse_env_int("SURFACEPILOT_MIN_FAILURES", DEFAULT_MIN_FAILURES)
        )

        events = sample_events() if args.selftest or args.input is None else load_jsonl(args.input)
        profile = build_profile(
            events,
            failure_threshold=failure_threshold,
            min_failures=min_failures,
        )
        if args.selftest:
            assert_selftest_profile(profile)

        rendered = render_profile(profile, args.format)
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        return 0
    except (OSError, ValueError, AssertionError) as exc:
        sys.stderr.write(f"surfacepilot: error: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
