#!/usr/bin/env python3
"""TraceLoom reference CLI for mining positive agent execution traces.

The tool reads JSONL execution events and JSON grader results, keeps only
verified successful runs, and emits deterministic JSONL or CSV records suitable
for router, prompt-selector, or evaluation workflow experiments.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import PurePosixPath
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple


PASS_STATUSES = {"pass", "passed", "success", "successful", "ok", "verified"}
TEXT_HEAVY_KEYS = {
    "body",
    "content",
    "context",
    "message",
    "prompt",
    "raw",
    "secret",
    "system_prompt",
    "text",
    "token",
    "transcript",
}
PATH_KEYS = {"file", "filepath", "filename", "path", "paths", "source"}


SAMPLE_TRACE_EVENTS: List[Dict[str, Any]] = [
    {
        "task_id": "task-alpha",
        "run_id": "run-001",
        "event": "retrieval",
        "step": 1,
        "source": "docs/router-policy.md",
        "query": "router selection checklist",
    },
    {
        "task_id": "task-alpha",
        "run_id": "run-001",
        "event": "tool_call",
        "step": 2,
        "tool": "File Read",
        "args": {"path": "src/router.py"},
    },
    {
        "task_id": "task-alpha",
        "run_id": "run-001",
        "event": "tool_call",
        "step": 3,
        "tool": "search/query",
        "args": {"query": "routing policy examples", "top_k": 3},
    },
    {
        "task_id": "task-alpha",
        "run_id": "run-001",
        "event": "tool_call",
        "step": 4,
        "tool": "file.write",
        "args": {"path": "src/router.py", "content": "private patch contents omitted"},
    },
    {
        "task_id": "task-alpha",
        "run_id": "run-001",
        "event": "tool_call",
        "step": 5,
        "tool": "test.run",
        "args": {"command": "python -m pytest tests/test_router.py"},
    },
    {
        "task_id": "task-beta",
        "run_id": "run-002",
        "event": "tool_call",
        "step": 1,
        "tool": "file.read",
        "args": {"path": "src/legacy.py"},
    },
]


SAMPLE_GRADER_RESULTS: List[Dict[str, Any]] = [
    {
        "task_id": "task-alpha",
        "run_id": "run-001",
        "passed": True,
        "score": 1.0,
        "summary": "All checks passed.",
    },
    {
        "task_id": "task-beta",
        "run_id": "run-002",
        "passed": False,
        "score": 0.25,
        "summary": "Regression test failed.",
    },
]


def sample_trace_events() -> List[Dict[str, Any]]:
    """Return a deep copy of built-in sample trace events."""
    return json.loads(json.dumps(SAMPLE_TRACE_EVENTS))


def sample_grader_results() -> List[Dict[str, Any]]:
    """Return a deep copy of built-in sample grader results."""
    return json.loads(json.dumps(SAMPLE_GRADER_RESULTS))


def normalize_tool_name(name: Any) -> str:
    """Normalize a tool name into a stable lowercase dotted token."""
    text = str(name or "unknown").strip().lower()
    text = re.sub(r"[^a-z0-9]+", ".", text)
    text = re.sub(r"\.+", ".", text).strip(".")
    return text or "unknown"


def normalize_path(value: Any) -> str:
    """Normalize a file or source path while redacting absolute path prefixes."""
    text = str(value).strip().replace("\\", "/")
    if not text:
        return ""
    if text.startswith("/") or re.match(r"^[a-zA-Z]:/", text):
        name = PurePosixPath(text).name or "path"
        return f"<absolute-path>/{name}"
    clean = str(PurePosixPath(text))
    if clean == ".":
        return text
    return clean


def summarize_text(value: Any) -> Dict[str, int]:
    """Return a deterministic length summary for text without exposing content."""
    text = str(value)
    words = re.findall(r"\S+", text)
    return {"chars": len(text), "words": len(words)}


def summarize_command(value: Any) -> Dict[str, Any]:
    """Summarize a command by executable, argument count, and total length."""
    text = str(value).strip()
    parts = text.split()
    program = parts[0] if parts else ""
    return {"program": program, "arg_count": max(len(parts) - 1, 0), "chars": len(text)}


def summarize_argument_value(key: str, value: Any) -> Any:
    """Summarize one argument value for routing without leaking raw text."""
    lowered = key.lower()
    if lowered in PATH_KEYS:
        if isinstance(value, list):
            return [normalize_path(item) for item in value]
        return normalize_path(value)
    if lowered == "command":
        return summarize_command(value)
    if any(token in lowered for token in TEXT_HEAVY_KEYS):
        text = str(value)
        return {"redacted": True, "chars": len(text)}
    if lowered in {"query", "search", "question"}:
        return summarize_text(value)
    if isinstance(value, Mapping):
        return summarize_args(value)
    if isinstance(value, list):
        return [summarize_argument_value(key, item) for item in value[:5]]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return {"type": type(value).__name__}


def summarize_args(args: Any) -> Dict[str, Any]:
    """Return a deterministic summary of a tool argument mapping."""
    if not isinstance(args, Mapping):
        return {"value": summarize_argument_value("value", args)}
    return {
        str(key): summarize_argument_value(str(key), args[key])
        for key in sorted(args.keys(), key=lambda item: str(item))
    }


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    """Load JSONL trace events from a file path with line-numbered errors."""
    events: List[Dict[str, Any]] = []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    value = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_no}: invalid JSON: {exc.msg}") from exc
                if not isinstance(value, dict):
                    raise ValueError(f"{path}:{line_no}: expected a JSON object")
                events.append(value)
    except FileNotFoundError as exc:
        raise ValueError(f"trace file not found: {path}") from exc
    return events


def load_grader_results(path: str) -> List[Dict[str, Any]]:
    """Load grader results from a JSON list, results object, or task mapping."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except FileNotFoundError as exc:
        raise ValueError(f"grader file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc.msg}") from exc

    if isinstance(raw, list):
        results = raw
    elif isinstance(raw, dict) and isinstance(raw.get("results"), list):
        results = raw["results"]
    elif isinstance(raw, dict):
        results = []
        for task_id, result in raw.items():
            if isinstance(result, dict):
                item = dict(result)
                item.setdefault("task_id", task_id)
                results.append(item)
            else:
                results.append({"task_id": task_id, "passed": bool(result)})
    else:
        raise ValueError("grader JSON must be a list, an object with results, or a task mapping")

    normalized: List[Dict[str, Any]] = []
    for index, result in enumerate(results):
        if not isinstance(result, dict):
            raise ValueError(f"grader result at index {index} must be an object")
        if "task_id" not in result:
            raise ValueError(f"grader result at index {index} is missing task_id")
        normalized.append(result)
    return normalized


def result_is_success(result: Mapping[str, Any], min_score: float) -> bool:
    """Return whether a grader result qualifies as verified successful."""
    score = result.get("score")
    score_ok = True
    if score is not None:
        try:
            score_ok = float(score) >= min_score
        except (TypeError, ValueError):
            score_ok = False

    if "passed" in result:
        return bool(result.get("passed")) and score_ok

    status = str(result.get("status", "")).strip().lower()
    if status:
        return status in PASS_STATUSES and score_ok

    return score is not None and score_ok


def success_condition(result: Mapping[str, Any]) -> str:
    """Build a compact success-condition string from a grader result."""
    parts: List[str] = []
    if "passed" in result:
        parts.append(f"passed={str(bool(result.get('passed'))).lower()}")
    if result.get("status") is not None:
        parts.append(f"status={result.get('status')}")
    if result.get("score") is not None:
        parts.append(f"score={result.get('score')}")
    return "; ".join(parts) if parts else "verified"


def event_order(event: Mapping[str, Any], fallback: int) -> int:
    """Return the event's integer order using step/order/index when available."""
    for key in ("step", "order", "index"):
        if key in event:
            try:
                return int(event[key])
            except (TypeError, ValueError):
                break
    return fallback


def event_args(event: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return an event argument mapping, accepting args or arguments keys."""
    args = event.get("args", event.get("arguments", {}))
    return args if isinstance(args, Mapping) else {"value": args}


def extract_paths(value: Any) -> List[str]:
    """Extract normalized paths from strings, lists, or mappings."""
    if value is None:
        return []
    if isinstance(value, str):
        path = normalize_path(value)
        return [path] if path else []
    if isinstance(value, list):
        paths: List[str] = []
        for item in value:
            paths.extend(extract_paths(item))
        return paths
    if isinstance(value, Mapping):
        paths = []
        for key in PATH_KEYS:
            if key in value:
                paths.extend(extract_paths(value[key]))
        return paths
    return []


def unique_sorted(values: Iterable[str]) -> List[str]:
    """Return unique non-empty strings in stable sorted order."""
    return sorted({value for value in values if value})


def build_success_indexes(
    grader_results: Sequence[Mapping[str, Any]], min_score: float
) -> Tuple[Dict[Tuple[str, str], Mapping[str, Any]], Dict[str, Mapping[str, Any]]]:
    """Build exact run and task-level success lookup tables."""
    by_run: Dict[Tuple[str, str], Mapping[str, Any]] = {}
    by_task: Dict[str, Mapping[str, Any]] = {}
    for result in grader_results:
        if not result_is_success(result, min_score):
            continue
        task_id = str(result.get("task_id", ""))
        run_id = result.get("run_id")
        if run_id is not None:
            by_run[(task_id, str(run_id))] = result
        else:
            by_task[task_id] = result
    return by_run, by_task


def mine_positive_traces(
    trace_events: Sequence[Mapping[str, Any]],
    grader_results: Sequence[Mapping[str, Any]],
    min_score: float = 1.0,
) -> List[Dict[str, Any]]:
    """Mine verified successful trace groups into positive routing records."""
    by_run_success, by_task_success = build_success_indexes(grader_results, min_score)
    grouped: MutableMapping[Tuple[str, str], List[Mapping[str, Any]]] = defaultdict(list)

    for event in trace_events:
        task_id = event.get("task_id")
        run_id = event.get("run_id")
        if task_id is None or run_id is None:
            continue
        grouped[(str(task_id), str(run_id))].append(event)

    records: List[Dict[str, Any]] = []
    for key in sorted(grouped.keys()):
        task_id, run_id = key
        result = by_run_success.get(key) or by_task_success.get(task_id)
        if result is None:
            continue

        events = sorted(
            enumerate(grouped[key], start=1),
            key=lambda pair: (event_order(pair[1], pair[0]), pair[0]),
        )
        tool_calls: List[Dict[str, Any]] = []
        retrieval_paths: List[Dict[str, Any]] = []
        reads: List[str] = []
        writes: List[str] = []

        for fallback_order, event in events:
            order = event_order(event, fallback_order)
            event_type = str(event.get("event", "")).lower()

            if event_type in {"retrieval", "retrieve", "context", "search_result"} or event.get("source"):
                source = normalize_path(event.get("source", event.get("path", "")))
                if source:
                    retrieval_paths.append(
                        {
                            "order": order,
                            "source": source,
                            "query_summary": summarize_text(event.get("query", "")),
                        }
                    )

            if event_type not in {"tool_call", "tool", "action"} and not event.get("tool"):
                continue

            tool = normalize_tool_name(event.get("tool", event.get("name", "")))
            args = event_args(event)
            tool_calls.append(
                {
                    "order": order,
                    "tool": tool,
                    "argument_summary": summarize_args(args),
                }
            )

            paths = extract_paths(args)
            if "read" in tool or tool in {"open", "view"}:
                reads.extend(paths)
            if any(token in tool for token in ("write", "edit", "patch", "save", "create")):
                writes.extend(paths)

        tool_sequence = [call["tool"] for call in tool_calls]
        read_files = unique_sorted(reads)
        write_files = unique_sorted(writes)
        touched_files = unique_sorted([*read_files, *write_files])

        records.append(
            {
                "task_id": task_id,
                "run_id": run_id,
                "success_condition": success_condition(result),
                "tool_sequence": tool_sequence,
                "tool_calls": tool_calls,
                "file_patterns": {
                    "read": read_files,
                    "write": write_files,
                    "touched": touched_files,
                },
                "retrieval_paths": retrieval_paths,
                "routing_signals": {
                    "tool_count": len(tool_calls),
                    "retrieval_count": len(retrieval_paths),
                    "file_count": len(touched_files),
                    "normalized_tool_path": ">".join(tool_sequence),
                },
            }
        )

    return records


def records_to_jsonl(records: Sequence[Mapping[str, Any]]) -> str:
    """Serialize records as compact deterministic JSONL."""
    return "".join(json.dumps(record, ensure_ascii=True, separators=(",", ":")) + "\n" for record in records)


def records_to_csv(records: Sequence[Mapping[str, Any]]) -> str:
    """Serialize records as deterministic CSV with JSON-encoded nested fields."""
    output = io.StringIO()
    fields = [
        "task_id",
        "run_id",
        "success_condition",
        "tool_sequence",
        "files_read",
        "files_written",
        "retrieval_sources",
        "routing_signals_json",
    ]
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for record in records:
        file_patterns = record["file_patterns"]
        retrieval_paths = record["retrieval_paths"]
        writer.writerow(
            {
                "task_id": record["task_id"],
                "run_id": record["run_id"],
                "success_condition": record["success_condition"],
                "tool_sequence": ">".join(record["tool_sequence"]),
                "files_read": "|".join(file_patterns["read"]),
                "files_written": "|".join(file_patterns["write"]),
                "retrieval_sources": "|".join(item["source"] for item in retrieval_paths),
                "routing_signals_json": json.dumps(
                    record["routing_signals"], ensure_ascii=True, separators=(",", ":")
                ),
            }
        )
    return output.getvalue()


def parse_min_score(value: Optional[str]) -> float:
    """Parse a minimum score value from CLI or environment configuration."""
    raw = value if value is not None else os.getenv("TRACELOOM_MIN_SCORE", "1.0")
    try:
        return float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid minimum score: {raw!r}") from exc


def default_output_format() -> str:
    """Return the configured default output format."""
    value = os.getenv("TRACELOOM_OUTPUT_FORMAT", "jsonl").strip().lower()
    if value not in {"jsonl", "csv"}:
        return "jsonl"
    return value


def render_records(records: Sequence[Mapping[str, Any]], output_format: str) -> str:
    """Render mined records in the requested output format."""
    if output_format == "jsonl":
        return records_to_jsonl(records)
    if output_format == "csv":
        return records_to_csv(records)
    raise ValueError(f"unsupported output format: {output_format}")


def run_selftest(output_format: str) -> str:
    """Run the built-in sample path and return rendered positive records."""
    records = mine_positive_traces(sample_trace_events(), sample_grader_results())
    if len(records) != 1:
        raise ValueError(f"selftest expected 1 positive record, got {len(records)}")
    if records[0]["task_id"] != "task-alpha":
        raise ValueError("selftest mined the wrong task")
    return render_records(records, output_format)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Mine verified successful LLM agent traces into positive routing datasets."
    )
    parser.add_argument("--traces", help="Path to execution trace JSONL input.")
    parser.add_argument("--graders", help="Path to grader or verifier JSON input.")
    parser.add_argument(
        "--format",
        choices=["jsonl", "csv"],
        default=default_output_format(),
        help="Output format. Defaults to TRACELOOM_OUTPUT_FORMAT or jsonl.",
    )
    parser.add_argument("--output", help="Optional output file path. Defaults to stdout.")
    parser.add_argument(
        "--min-score",
        help="Minimum score for success when score is present. Defaults to TRACELOOM_MIN_SCORE or 1.0.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run on built-in mock data with no API key or external files.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the TraceLoom CLI and return a process exit code."""
    args = build_parser().parse_args(argv)

    try:
        min_score = parse_min_score(args.min_score)
        if args.selftest or (not args.traces and not args.graders):
            rendered = run_selftest(args.format)
        else:
            if not args.traces:
                raise ValueError("missing --traces; provide a JSONL trace file or use --selftest")
            if not args.graders:
                raise ValueError("missing --graders; provide a verifier JSON file or use --selftest")
            records = mine_positive_traces(
                load_jsonl(args.traces),
                load_grader_results(args.graders),
                min_score=min_score,
            )
            rendered = render_records(records, args.format)

        if args.output:
            with open(args.output, "w", encoding="utf-8", newline="") as handle:
                handle.write(rendered)
        else:
            sys.stdout.write(rendered)
        return 0
    except ValueError as exc:
        print(f"traceloom: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
