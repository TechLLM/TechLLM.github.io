#!/usr/bin/env python3
"""TraceMint: mine grader-passing agent logs into positive trace datasets.

The CLI reads JSONL agent run records, keeps runs with explicit passing
grader/status signals, normalizes execution events, redacts sensitive text, and
writes deterministic JSONL and Markdown corpora. It has no network dependency
and requires no API key.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple


JsonObject = Dict[str, Any]


class TraceMintError(Exception):
    """Raised for user-facing TraceMint CLI errors."""


SAMPLE_RUNS: List[JsonObject] = [
    {
        "run_id": "run-pass-001",
        "task": "Update parser to handle quoted values",
        "grader": {"passed": True, "score": 1.0},
        "events": [
            {
                "type": "retrieval",
                "source": "docs/parser.md",
                "snippet": "Quoted values may include escaped commas.",
                "metadata": {"section": "CSV"},
            },
            {
                "type": "tool_call",
                "name": "read_file",
                "args": {"path": "repo/src/parser.py"},
                "result": "loaded parser implementation",
            },
            {
                "type": "tool_call",
                "name": "edit_file",
                "args": {"change": "add quote handling", "path": "repo/src/parser.py"},
                "result": {"lines_changed": 12, "status": "ok"},
            },
            {
                "type": "file_edit",
                "path": "repo/src/parser.py",
                "summary": "Added quote-aware tokenization.",
                "diff": "+ handle quoted values\n- split on comma only",
            },
            {"type": "state", "key": "tests", "value": "unit tests passed"},
            {
                "type": "final_artifact",
                "kind": "patch_summary",
                "summary": "Parser now preserves commas inside quotes.",
            },
        ],
    },
    {
        "run_id": "run-fail-001",
        "task": "Update parser to handle multiline cells",
        "grader": {"passed": False, "score": 0.25},
        "events": [
            {
                "type": "tool_call",
                "name": "edit_file",
                "args": {"path": "repo/src/parser.py"},
                "result": "tests failed",
            }
        ],
    },
]


SECRET_PATTERN = re.compile(
    r"(?i)\b(api[_-]?key|token|secret|password)\b\s*[:=]\s*['\"]?[^'\"\s,}]+"
)
ABSOLUTE_PATH_PATTERN = re.compile(
    r"(?<![\w.-])(?:[A-Za-z]:[\\/]|[\\/])(?:[^\\/\s]+[\\/])+[^\\/\s,;]*"
)


def summarize_text(value: Any, limit: int = 240) -> str:
    """Return a compact single-line summary for arbitrary JSON-like values."""

    if value is None:
        text = ""
    elif isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, sort_keys=True, ensure_ascii=True)
    text = " ".join(text.split())
    if len(text) > limit:
        return text[: max(0, limit - 3)].rstrip() + "..."
    return text


def parse_env_redaction_patterns() -> List[str]:
    """Read optional redaction regexes from TRACEMINT_REDACT_PATTERNS."""

    raw = os.environ.get("TRACEMINT_REDACT_PATTERNS", "").strip()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return [item.strip() for item in raw.split(",") if item.strip()]
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise TraceMintError("TRACEMINT_REDACT_PATTERNS must be a JSON list of regex strings")
    return parsed


def parse_max_snippet_chars(default: int = 240) -> int:
    """Read the optional TRACEMINT_MAX_SNIPPET_CHARS integer setting."""

    raw = os.environ.get("TRACEMINT_MAX_SNIPPET_CHARS", "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise TraceMintError("TRACEMINT_MAX_SNIPPET_CHARS must be an integer") from exc
    if value < 20:
        raise TraceMintError("TRACEMINT_MAX_SNIPPET_CHARS must be at least 20")
    return value


def compile_user_patterns(patterns: Sequence[str]) -> List[re.Pattern[str]]:
    """Compile user-supplied redaction regexes with clear error messages."""

    compiled: List[re.Pattern[str]] = []
    for pattern in patterns:
        try:
            compiled.append(re.compile(pattern))
        except re.error as exc:
            raise TraceMintError(f"invalid redaction regex {pattern!r}: {exc}") from exc
    return compiled


def redact_text(text: str, user_patterns: Sequence[re.Pattern[str]]) -> str:
    """Redact secrets, absolute paths, and user-configured regex matches."""

    redacted = SECRET_PATTERN.sub(lambda match: f"{match.group(1)}=[REDACTED_SECRET]", text)
    redacted = ABSOLUTE_PATH_PATTERN.sub("[REDACTED_PATH]", redacted)
    for pattern in user_patterns:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def redact_value(value: Any, user_patterns: Sequence[re.Pattern[str]]) -> Any:
    """Recursively redact strings inside JSON-like values."""

    if isinstance(value, str):
        return redact_text(value, user_patterns)
    if isinstance(value, list):
        return [redact_value(item, user_patterns) for item in value]
    if isinstance(value, dict):
        return {
            str(redact_value(key, user_patterns)): redact_value(val, user_patterns)
            for key, val in sorted(value.items(), key=lambda item: str(item[0]))
        }
    return value


def read_jsonl(path: Path) -> List[JsonObject]:
    """Read a JSONL file as a list of JSON objects."""

    if not path.exists():
        raise TraceMintError(f"input file does not exist: {path}")
    runs: List[JsonObject] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise TraceMintError(f"invalid JSON on line {line_number}: {exc.msg}") from exc
            if not isinstance(record, dict):
                raise TraceMintError(f"line {line_number} must contain a JSON object")
            runs.append(record)
    return runs


def write_jsonl(path: Path, records: Sequence[JsonObject]) -> None:
    """Write JSON records as deterministic JSONL."""

    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, ensure_ascii=True) + "\n")


def get_nested_mapping(run: Mapping[str, Any], names: Sequence[str]) -> Mapping[str, Any]:
    """Return the first mapping value found under one of the provided names."""

    for name in names:
        value = run.get(name)
        if isinstance(value, Mapping):
            return value
    return {}


def is_passing_run(run: Mapping[str, Any]) -> bool:
    """Return True when a run has an explicit passing grader or status signal."""

    for field in ("grader", "grade", "verifier", "verification", "evaluation"):
        value = run.get(field)
        if isinstance(value, Mapping):
            for key in ("passed", "pass", "verified", "success", "ok"):
                if value.get(key) is True:
                    return True
    if run.get("passed") is True or run.get("verified") is True or run.get("success") is True:
        return True
    status = run.get("status")
    if isinstance(status, str) and status.lower() in {"passed", "pass", "success", "succeeded", "verified", "ok"}:
        return True
    return False


def extract_score(run: Mapping[str, Any]) -> Optional[float]:
    """Extract a numeric grader score when present."""

    for source in (
        get_nested_mapping(run, ("grader", "grade", "verifier", "verification", "evaluation")),
        run,
    ):
        score = source.get("score") if isinstance(source, Mapping) else None
        if isinstance(score, (int, float)) and not isinstance(score, bool):
            return float(score)
    return None


def event_label(event: Mapping[str, Any]) -> str:
    """Return a short human label for a normalized event."""

    event_type = str(event.get("type", "event"))
    if event_type == "tool_call":
        return str(event.get("name", "tool"))
    if event_type == "evidence":
        return str(event.get("source", "evidence"))
    if event_type == "file_edit":
        return str(event.get("path", "file"))
    if event_type == "state_change":
        return str(event.get("key", "state"))
    if event_type == "final_artifact":
        return str(event.get("kind", "artifact"))
    return event_type


def normalize_event(raw_event: Mapping[str, Any], index: int, user_patterns: Sequence[re.Pattern[str]], max_chars: int) -> JsonObject:
    """Normalize a raw execution event into a compact deterministic event."""

    redacted = redact_value(dict(raw_event), user_patterns)
    raw_type = str(redacted.get("type", redacted.get("event_type", "event"))).lower()

    if raw_type in {"retrieval", "retrieved", "evidence"}:
        return {
            "index": index,
            "metadata": redacted.get("metadata", {}),
            "snippet": summarize_text(redacted.get("snippet", redacted.get("text", "")), max_chars),
            "source": summarize_text(redacted.get("source", redacted.get("url", "unknown")), max_chars),
            "type": "evidence",
        }

    if raw_type in {"tool", "tool_call", "function_call"}:
        return {
            "args": redacted.get("args", redacted.get("arguments", {})),
            "index": index,
            "name": summarize_text(redacted.get("name", redacted.get("tool", "unknown_tool")), max_chars),
            "result_summary": summarize_text(redacted.get("result", redacted.get("output", "")), max_chars),
            "status": summarize_text(redacted.get("status", ""), max_chars),
            "type": "tool_call",
        }

    if raw_type in {"file_edit", "edit", "diff"}:
        return {
            "diff_summary": summarize_text(redacted.get("diff", ""), max_chars),
            "index": index,
            "path": summarize_text(redacted.get("path", redacted.get("file", "unknown_file")), max_chars),
            "summary": summarize_text(redacted.get("summary", ""), max_chars),
            "type": "file_edit",
        }

    if raw_type in {"state", "state_change", "transition"}:
        return {
            "index": index,
            "key": summarize_text(redacted.get("key", redacted.get("name", "state")), max_chars),
            "type": "state_change",
            "value": summarize_text(redacted.get("value", redacted.get("to", "")), max_chars),
        }

    if raw_type in {"final_artifact", "artifact", "answer"}:
        return {
            "index": index,
            "kind": summarize_text(redacted.get("kind", redacted.get("name", "artifact")), max_chars),
            "summary": summarize_text(redacted.get("summary", redacted.get("content", "")), max_chars),
            "type": "final_artifact",
        }

    payload = {
        str(key): value
        for key, value in redacted.items()
        if key not in {"type", "event_type"} and isinstance(key, str)
    }
    return {"index": index, "payload": payload, "type": raw_type or "event"}


def normalize_top_level_event(raw: Any, event_type: str) -> Optional[JsonObject]:
    """Convert a top-level evidence, artifact, diff, or state item into an event."""

    if isinstance(raw, Mapping):
        event = dict(raw)
    elif isinstance(raw, str):
        event = {"summary": raw}
    else:
        return None
    event.setdefault("type", event_type)
    return event


def collect_raw_events(run: Mapping[str, Any]) -> List[JsonObject]:
    """Collect ordered raw events from common run-level fields."""

    raw_events: List[JsonObject] = []
    for field, event_type in (
        ("retrieved_evidence", "evidence"),
        ("evidence", "evidence"),
        ("events", "event"),
        ("file_diffs", "file_edit"),
        ("state_changes", "state_change"),
        ("artifacts", "final_artifact"),
    ):
        value = run.get(field)
        if isinstance(value, list):
            for item in value:
                if field == "events" and isinstance(item, Mapping):
                    raw_events.append(dict(item))
                else:
                    event = normalize_top_level_event(item, event_type)
                    if event is not None:
                        raw_events.append(event)
    final_artifact = run.get("final_artifact")
    event = normalize_top_level_event(final_artifact, "final_artifact")
    if event is not None:
        raw_events.append(event)
    return raw_events


def mine_positive_traces(
    runs: Iterable[Mapping[str, Any]],
    redaction_patterns: Optional[Sequence[str]] = None,
    max_snippet_chars: int = 240,
) -> List[JsonObject]:
    """Mine passing runs into normalized positive trace records."""

    user_patterns = compile_user_patterns(list(redaction_patterns or []))
    traces: List[JsonObject] = []
    for ordinal, run in enumerate(runs, start=1):
        if not is_passing_run(run):
            continue

        trace_id = summarize_text(run.get("run_id", run.get("id", f"trace-{ordinal}")), max_snippet_chars)
        task = summarize_text(run.get("task", run.get("prompt", "")), max_snippet_chars)
        trace_id = redact_text(trace_id, user_patterns)
        task = redact_text(task, user_patterns)

        raw_events = collect_raw_events(run)
        normalized_events = [
            normalize_event(raw_event, index, user_patterns, max_snippet_chars)
            for index, raw_event in enumerate(raw_events)
        ]

        tools: List[str] = []
        evidence: List[JsonObject] = []
        evidence_keys = set()
        artifacts: List[JsonObject] = []
        for event in normalized_events:
            if event.get("type") == "tool_call":
                name = str(event.get("name", "unknown_tool"))
                if name not in tools:
                    tools.append(name)
            elif event.get("type") == "evidence":
                item = {
                    "metadata": event.get("metadata", {}),
                    "snippet": event.get("snippet", ""),
                    "source": event.get("source", "unknown"),
                }
                key = (item["source"], item["snippet"])
                if key not in evidence_keys:
                    evidence_keys.add(key)
                    evidence.append(item)
            elif event.get("type") == "final_artifact":
                artifacts.append(
                    {
                        "kind": event.get("kind", "artifact"),
                        "summary": event.get("summary", ""),
                    }
                )

        record: JsonObject = {
            "artifacts": artifacts,
            "event_count": len(normalized_events),
            "events": normalized_events,
            "evidence": evidence,
            "score": extract_score(run),
            "task": task,
            "tools": tools,
            "trace_id": trace_id,
        }
        traces.append(record)
    traces.sort(key=lambda item: str(item.get("trace_id", "")))
    return traces


def render_markdown(traces: Sequence[Mapping[str, Any]]) -> str:
    """Render positive traces as review-friendly Markdown."""

    lines: List[str] = ["# TraceMint Positive Trace Dataset", "", "Generated by TraceMint.", ""]
    for trace in traces:
        trace_id = trace.get("trace_id", "")
        tools = trace.get("tools", [])
        tool_text = ", ".join(str(tool) for tool in tools) if tools else "none"
        lines.extend(
            [
                f"## Trace {trace_id}",
                f"- Task: {trace.get('task', '')}",
                f"- Score: {trace.get('score')}",
                f"- Events: {trace.get('event_count', 0)}",
                f"- Tools: {tool_text}",
                "",
                "### Evidence",
            ]
        )
        evidence = trace.get("evidence", [])
        if isinstance(evidence, list) and evidence:
            for index, item in enumerate(evidence, start=1):
                if isinstance(item, Mapping):
                    source = item.get("source", "unknown")
                    snippet = item.get("snippet", "")
                    lines.append(f"{index}. `{source}` - {snippet}")
        else:
            lines.append("- none")

        lines.extend(["", "### Event Sequence"])
        events = trace.get("events", [])
        if isinstance(events, list) and events:
            for index, event in enumerate(events, start=1):
                if isinstance(event, Mapping):
                    lines.append(f"{index}. {event.get('type', 'event')}: {event_label(event)}")
        else:
            lines.append("- none")

        lines.extend(["", "### Artifacts"])
        artifacts = trace.get("artifacts", [])
        if isinstance(artifacts, list) and artifacts:
            for item in artifacts:
                if isinstance(item, Mapping):
                    lines.append(f"- {item.get('kind', 'artifact')}: {item.get('summary', '')}")
        else:
            lines.append("- none")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_markdown(path: Path, traces: Sequence[Mapping[str, Any]]) -> None:
    """Write Markdown output, creating parent directories as needed."""

    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(traces), encoding="utf-8", newline="\n")


def run_selftest() -> JsonObject:
    """Run TraceMint on the built-in sample and validate core behavior."""

    traces = mine_positive_traces(SAMPLE_RUNS)
    if len(traces) != 1:
        raise TraceMintError(f"selftest expected 1 passing trace, got {len(traces)}")
    trace = traces[0]
    expected_keys = {"artifacts", "event_count", "events", "evidence", "score", "task", "tools", "trace_id"}
    if set(trace.keys()) != expected_keys:
        raise TraceMintError(f"selftest output keys changed: {sorted(trace.keys())}")
    if trace["trace_id"] != "run-pass-001":
        raise TraceMintError("selftest trace_id mismatch")
    if trace["tools"] != ["read_file", "edit_file"]:
        raise TraceMintError("selftest tool sequence mismatch")
    return {
        "input_runs": len(SAMPLE_RUNS),
        "jsonl_records": len(traces),
        "markdown_sections": render_markdown(traces).count("## Trace "),
        "status": "ok",
    }


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description="Mine grader-passing AI agent JSONL logs into positive trace datasets.",
    )
    parser.add_argument("--input", type=Path, help="Path to input JSONL agent log file.")
    parser.add_argument("--out-jsonl", type=Path, help="Path for machine-readable positive trace JSONL output.")
    parser.add_argument("--out-md", type=Path, help="Path for review-friendly Markdown output.")
    parser.add_argument(
        "--redact-regex",
        action="append",
        default=[],
        help="Additional regex to redact. May be repeated.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run on built-in sample data without reading files or requiring API keys.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.selftest or not args.input:
            result = run_selftest()
            print(json.dumps(result, sort_keys=True))
            return 0

        redaction_patterns = parse_env_redaction_patterns() + list(args.redact_regex)
        traces = mine_positive_traces(
            read_jsonl(args.input),
            redaction_patterns=redaction_patterns,
            max_snippet_chars=parse_max_snippet_chars(),
        )

        if args.out_jsonl:
            write_jsonl(args.out_jsonl, traces)
        if args.out_md:
            write_markdown(args.out_md, traces)

        summary: JsonObject = {
            "input_runs": len(read_jsonl(args.input)),
            "passing_traces": len(traces),
            "status": "ok",
        }
        if args.out_md:
            summary["markdown_path"] = str(args.out_md)
        if args.out_jsonl:
            summary["output_path"] = str(args.out_jsonl)
        print(json.dumps(summary, sort_keys=True))
        return 0
    except TraceMintError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
