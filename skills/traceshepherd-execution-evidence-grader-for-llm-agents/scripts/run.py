#!/usr/bin/env python3
"""TraceShepherd: deterministic local grading for LLM agent execution evidence.

The CLI reads a trace JSONL file, a small manifest, and a workspace directory.
It then verifies required events, expected file state, and path policies without
calling external services.
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


VERSION = "0.1.0"
MUTATING_EVENT_TYPES = {"create", "delete", "edit", "move", "patch", "write"}
PATH_FIELDS = ("path", "file", "target", "target_path", "output_path")
SAMPLE_FILE_CONTENT = (
    "TraceShepherd demo report\n\n"
    "Evidence: project plan was read.\n"
    "Result: docs updated.\n"
)


def sample_manifest() -> dict[str, Any]:
    """Return a built-in manifest used by --selftest and import tests."""

    return {
        "version": 1,
        "rules": {
            "required_events": [
                {"type": "search", "pattern": "project plan"},
                {"type": "read", "path": "sources/project-plan.md"},
                {"type": "write", "path": "docs/agent-report.md"},
            ],
            "allowed_paths": ["docs/**"],
            "forbidden_paths": ["secrets/**"],
            "files": [
                {
                    "path": "docs/agent-report.md",
                    "must_exist": True,
                    "min_size": 40,
                    "contains": [
                        "TraceShepherd demo report",
                        "Evidence: project plan was read.",
                    ],
                    "regex": ["Result: docs updated\\."],
                }
            ],
        },
    }


def sample_events() -> list[dict[str, Any]]:
    """Return built-in trace events used by --selftest and import tests."""

    return [
        {"type": "search", "query": "project plan evidence"},
        {"type": "read", "path": "sources/project-plan.md"},
        {"type": "write", "path": "docs/agent-report.md"},
    ]


def load_trace_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load newline-delimited JSON trace events from a local file."""

    events: list[dict[str, Any]] = []
    trace_path = Path(path)
    try:
        lines = trace_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError(f"Could not read trace file {trace_path}: {exc}") from exc

    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON in trace file {trace_path} on line {line_number}: {exc.msg}"
            ) from exc
        if not isinstance(event, dict):
            raise ValueError(
                f"Trace file {trace_path} line {line_number} must be a JSON object"
            )
        events.append(event)
    return events


def load_manifest(path: str | Path) -> dict[str, Any]:
    """Load a manifest from JSON or the small YAML subset supported here."""

    manifest_path = Path(path)
    try:
        text = manifest_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Could not read manifest file {manifest_path}: {exc}") from exc

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = parse_simple_yaml(text)

    if not isinstance(data, dict):
        raise ValueError(f"Manifest file {manifest_path} must contain an object")
    return data


def parse_simple_yaml(text: str) -> Any:
    """Parse a deliberately small YAML subset for local rule packs.

    Supported syntax: two-space indentation, mappings, lists, booleans, null,
    integers, floats, and quoted or unquoted scalar strings. This is not a full
    YAML parser; use JSON if you need anchors, multiline scalars, or advanced
    YAML features.
    """

    lines: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if "\t" in raw_line:
            raise ValueError("YAML tabs are not supported; use spaces")
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if indent % 2:
            raise ValueError("YAML indentation must use multiples of two spaces")
        lines.append((indent, raw_line.strip()))

    if not lines:
        return {}
    if lines[0][0] != 0:
        raise ValueError("YAML document must start at indentation level zero")

    value, index = _parse_yaml_block(lines, 0, 0)
    if index != len(lines):
        raise ValueError(f"Unexpected YAML content near line {index + 1}")
    return value


def _parse_yaml_block(
    lines: list[tuple[int, str]], index: int, indent: int
) -> tuple[Any, int]:
    """Parse one YAML block at the requested indentation."""

    if index >= len(lines) or lines[index][0] < indent:
        return None, index
    if lines[index][0] > indent:
        raise ValueError(f"Unexpected YAML indentation near line {index + 1}")
    if lines[index][1].startswith("- "):
        return _parse_yaml_list(lines, index, indent)
    return _parse_yaml_mapping(lines, index, indent)


def _parse_yaml_list(
    lines: list[tuple[int, str]], index: int, indent: int
) -> tuple[list[Any], int]:
    """Parse a YAML list block."""

    items: list[Any] = []
    while index < len(lines):
        line_indent, text = lines[index]
        if line_indent < indent:
            break
        if line_indent != indent or not text.startswith("- "):
            break

        item_text = text[2:].strip()
        index += 1
        if not item_text:
            child, index = _parse_yaml_block(lines, index, indent + 2)
            items.append(child)
            continue

        if _looks_like_mapping_item(item_text):
            item: dict[str, Any] = {}
            key, value = _split_yaml_key_value(item_text)
            if value == "":
                child, index = _parse_yaml_block(lines, index, indent + 2)
                item[key] = child
            else:
                item[key] = _parse_yaml_scalar(value)

            while (
                index < len(lines)
                and lines[index][0] == indent + 2
                and not lines[index][1].startswith("- ")
            ):
                child_key, child_value = _split_yaml_key_value(lines[index][1])
                index += 1
                if child_value == "":
                    child, index = _parse_yaml_block(lines, index, indent + 4)
                    item[child_key] = child
                else:
                    item[child_key] = _parse_yaml_scalar(child_value)
            items.append(item)
        else:
            items.append(_parse_yaml_scalar(item_text))
    return items, index


def _parse_yaml_mapping(
    lines: list[tuple[int, str]], index: int, indent: int
) -> tuple[dict[str, Any], int]:
    """Parse a YAML mapping block."""

    data: dict[str, Any] = {}
    while index < len(lines):
        line_indent, text = lines[index]
        if line_indent < indent:
            break
        if line_indent > indent:
            raise ValueError(f"Unexpected YAML indentation near line {index + 1}")
        if text.startswith("- "):
            break

        key, value = _split_yaml_key_value(text)
        index += 1
        if value == "":
            child, index = _parse_yaml_block(lines, index, indent + 2)
            data[key] = child
        else:
            data[key] = _parse_yaml_scalar(value)
    return data, index


def _looks_like_mapping_item(text: str) -> bool:
    """Return true when a YAML list item starts an inline mapping."""

    return ":" in text and not text.startswith(("http://", "https://", '"', "'"))


def _split_yaml_key_value(text: str) -> tuple[str, str]:
    """Split one YAML mapping line into key and value."""

    if ":" not in text:
        raise ValueError(f"Expected YAML key/value pair, got: {text}")
    key, value = text.split(":", 1)
    key = key.strip()
    if not key:
        raise ValueError(f"Expected non-empty YAML key in: {text}")
    return key, value.strip()


def _parse_yaml_scalar(value: str) -> Any:
    """Parse one YAML scalar value."""

    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none", "~"}:
        return None
    if value.startswith(('"', "'")) and value.endswith(('"', "'")):
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError) as exc:
            raise ValueError(f"Invalid quoted YAML scalar: {value}") from exc
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def grade_execution(
    trace_events: list[dict[str, Any]],
    manifest: dict[str, Any],
    workspace: str | Path = ".",
) -> dict[str, Any]:
    """Grade trace events and workspace state against a manifest.

    Returns a deterministic report with status, summary counts, evidence
    matches, file check results, path policy findings, and validation errors.
    """

    rules = manifest.get("rules", manifest)
    if not isinstance(rules, dict):
        raise ValueError("Manifest field 'rules' must be an object")

    errors: list[str] = []
    checks: list[bool] = []

    required_events = _list_of_dicts(rules.get("required_events", []), "required_events")
    required_event_results: list[dict[str, Any]] = []
    missing_events: list[dict[str, Any]] = []
    for rule in required_events:
        matched_index: int | None = None
        try:
            for index, event in enumerate(trace_events):
                if _event_matches(event, rule):
                    matched_index = index
                    break
        except re.error as exc:
            errors.append(f"Invalid required event regex in rule {rule}: {exc}")

        matched = matched_index is not None
        checks.append(matched)
        result = {
            "matched": matched,
            "matched_event_index": matched_index,
            "rule": rule,
        }
        required_event_results.append(result)
        if not matched:
            missing_events.append({"reason": "no matching trace event", "rule": rule})

    file_results = _grade_files(
        _list_of_dicts(rules.get("files", []), "files"), Path(workspace), errors
    )
    for file_result in file_results:
        for check in file_result["checks"]:
            checks.append(bool(check["pass"]))

    changed_paths = _changed_paths(trace_events, errors)
    allowed_paths = _list_of_strings(rules.get("allowed_paths", []), "allowed_paths")
    forbidden_paths = _list_of_strings(rules.get("forbidden_paths", []), "forbidden_paths")

    unexpected_modified_files: list[str] = []
    if allowed_paths:
        unexpected_modified_files = [
            path for path in changed_paths if not _matches_any(path, allowed_paths)
        ]
        checks.append(not unexpected_modified_files)

    forbidden_modified_files = [
        path for path in changed_paths if _matches_any(path, forbidden_paths)
    ]
    if forbidden_paths:
        checks.append(not forbidden_modified_files)

    strict = _env_flag("TRACESHEPHERD_STRICT", default=False)
    error_failed = bool(errors) and strict
    if error_failed:
        checks.append(False)

    failed = sum(1 for passed in checks if not passed)
    passed = len(checks) - failed
    status = "pass" if failed == 0 and not error_failed else "fail"

    return {
        "tool": "traceshepherd",
        "version": VERSION,
        "status": status,
        "summary": {"checks": len(checks), "passed": passed, "failed": failed},
        "evidence": {
            "required_events": required_event_results,
            "missing_events": missing_events,
        },
        "files": file_results,
        "policy": {
            "changed_paths": changed_paths,
            "unexpected_modified_files": unexpected_modified_files,
            "forbidden_modified_files": forbidden_modified_files,
        },
        "errors": errors,
    }


def _grade_files(
    file_rules: list[dict[str, Any]], workspace: Path, errors: list[str]
) -> list[dict[str, Any]]:
    """Grade workspace files against file rules."""

    results: list[dict[str, Any]] = []
    max_read_bytes = _env_int("TRACESHEPHERD_MAX_READ_BYTES", default=1_000_000)

    for rule in file_rules:
        checks: list[dict[str, Any]] = []
        raw_path = rule.get("path")
        if not raw_path:
            errors.append(f"File rule is missing path: {rule}")
            checks.append({"name": "path", "pass": False, "expected": "relative path"})
            results.append(
                {
                    "path": "",
                    "exists": False,
                    "size_bytes": None,
                    "sha256": None,
                    "checks": checks,
                    "pass": False,
                }
            )
            continue

        try:
            rel_path = normalize_rel_path(str(raw_path))
        except ValueError as exc:
            errors.append(str(exc))
            checks.append({"name": "path", "pass": False, "expected": "safe relative path"})
            results.append(
                {
                    "path": str(raw_path),
                    "exists": False,
                    "size_bytes": None,
                    "sha256": None,
                    "checks": checks,
                    "pass": False,
                }
            )
            continue

        file_path = workspace / rel_path
        exists = file_path.exists()
        size_bytes: int | None = None
        digest: str | None = None
        content: str | None = None

        must_exist = bool(rule.get("must_exist", True))
        checks.append(
            {"name": "exists", "pass": exists == must_exist, "expected": must_exist}
        )

        if exists and file_path.is_file():
            data = file_path.read_bytes()
            size_bytes = len(data)
            digest = hashlib.sha256(data).hexdigest()
            if "sha256" in rule:
                checks.append(
                    {
                        "name": "sha256",
                        "pass": digest == str(rule["sha256"]),
                        "expected": str(rule["sha256"]),
                    }
                )
            if "min_size" in rule:
                expected = int(rule["min_size"])
                checks.append(
                    {"name": "min_size", "pass": size_bytes >= expected, "expected": expected}
                )
            if "max_size" in rule:
                expected = int(rule["max_size"])
                checks.append(
                    {"name": "max_size", "pass": size_bytes <= expected, "expected": expected}
                )

            needs_text = bool(rule.get("contains")) or bool(rule.get("regex"))
            if needs_text:
                content = data[:max_read_bytes].decode("utf-8", errors="replace")

            for needle in _list_of_strings(rule.get("contains", []), "contains"):
                checks.append(
                    {
                        "name": "contains",
                        "pass": content is not None and needle in content,
                        "expected": needle,
                    }
                )

            for pattern in _list_of_strings(rule.get("regex", []), "regex"):
                try:
                    matched = content is not None and re.search(pattern, content, re.MULTILINE)
                except re.error as exc:
                    errors.append(f"Invalid file regex for {rel_path}: {exc}")
                    matched = False
                checks.append(
                    {"name": "regex", "pass": bool(matched), "expected": pattern}
                )
        else:
            for name in ("sha256", "min_size", "max_size"):
                if name in rule:
                    checks.append(
                        {"name": name, "pass": False, "expected": rule[name]}
                    )
            for needle in _list_of_strings(rule.get("contains", []), "contains"):
                checks.append(
                    {"name": "contains", "pass": False, "expected": needle}
                )
            for pattern in _list_of_strings(rule.get("regex", []), "regex"):
                checks.append({"name": "regex", "pass": False, "expected": pattern})

        results.append(
            {
                "path": rel_path,
                "exists": exists,
                "size_bytes": size_bytes,
                "sha256": digest,
                "checks": checks,
                "pass": all(bool(check["pass"]) for check in checks),
            }
        )

    return results


def normalize_rel_path(path: str) -> str:
    """Normalize and validate a manifest or trace path as a safe relative path."""

    normalized = path.replace("\\", "/").strip()
    pure = PurePosixPath(normalized)
    if not normalized or pure.is_absolute() or any(part == ".." for part in pure.parts):
        raise ValueError(f"Unsafe path; expected a relative path inside workspace: {path}")
    return str(pure)


def _event_matches(event: dict[str, Any], rule: dict[str, Any]) -> bool:
    """Return true when one trace event satisfies one required-event rule."""

    for field in ("type", "tool", "action"):
        if field in rule and event.get(field) != rule[field]:
            return False

    if "path" in rule:
        event_path = _event_path(event)
        if event_path is None or not fnmatch.fnmatch(event_path, str(rule["path"])):
            return False

    pattern = rule.get("pattern", rule.get("regex"))
    if pattern:
        blob = json.dumps(event, sort_keys=True, separators=(",", ":"))
        if re.search(str(pattern), blob) is None:
            return False
    return True


def _event_path(event: dict[str, Any]) -> str | None:
    """Extract and normalize a path from a trace event if one is present."""

    for field in PATH_FIELDS:
        if field in event and event[field] is not None:
            return normalize_rel_path(str(event[field]))
    return None


def _changed_paths(trace_events: list[dict[str, Any]], errors: list[str]) -> list[str]:
    """Return sorted unique paths changed by mutating trace events."""

    paths: set[str] = set()
    for event in trace_events:
        event_type = str(event.get("type", "")).lower()
        action = str(event.get("action", "")).lower()
        mutates = bool(event.get("mutates", False))
        if event_type not in MUTATING_EVENT_TYPES and action not in MUTATING_EVENT_TYPES and not mutates:
            continue
        try:
            path = _event_path(event)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if path:
            paths.add(path)
    return sorted(paths)


def _matches_any(path: str, patterns: list[str]) -> bool:
    """Return true when a path matches at least one glob pattern."""

    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _list_of_dicts(value: Any, field_name: str) -> list[dict[str, Any]]:
    """Validate a manifest field as a list of objects."""

    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError(f"Manifest field '{field_name}' must be a list of objects")
    return value


def _list_of_strings(value: Any, field_name: str) -> list[str]:
    """Validate a manifest field as a list of strings."""

    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"Manifest field '{field_name}' must be a list")
    return [str(item) for item in value]


def _env_flag(name: str, default: bool) -> bool:
    """Read a boolean flag from an environment variable."""

    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    """Read a positive integer from an environment variable."""

    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def build_selftest_report() -> dict[str, Any]:
    """Create a temporary sample workspace and grade the built-in sample."""

    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        report_path = workspace / "docs" / "agent-report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(SAMPLE_FILE_CONTENT, encoding="utf-8")
        return grade_execution(sample_events(), sample_manifest(), workspace)


def render_report(report: dict[str, Any], compact: bool = False) -> str:
    """Render a report as deterministic JSON."""

    if compact:
        return json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n"
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Run the TraceShepherd command-line interface."""

    parser = argparse.ArgumentParser(
        description="Grade LLM agent execution evidence from local trace JSONL and workspace files."
    )
    parser.add_argument("--trace", help="Path to trace JSONL file.")
    parser.add_argument("--manifest", help="Path to manifest YAML or JSON file.")
    parser.add_argument(
        "--workspace", default=".", help="Workspace directory to inspect. Defaults to current directory."
    )
    parser.add_argument("--output", help="Optional path to write the JSON report.")
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run a built-in deterministic sample with no API key or external service.",
    )
    parser.add_argument("--compact", action="store_true", help="Emit compact one-line JSON.")
    parser.add_argument("--version", action="version", version=f"TraceShepherd {VERSION}")
    args = parser.parse_args(argv)

    try:
        if args.selftest or (args.trace is None and args.manifest is None):
            report = build_selftest_report()
        else:
            if not args.trace or not args.manifest:
                parser.error("--trace and --manifest must be provided together")
            report = grade_execution(
                load_trace_jsonl(args.trace),
                load_manifest(args.manifest),
                Path(args.workspace),
            )
    except ValueError as exc:
        print(f"traceshepherd: error: {exc}", file=sys.stderr)
        return 2

    output = render_report(report, compact=args.compact)
    if args.output:
        try:
            Path(args.output).write_text(output, encoding="utf-8")
        except OSError as exc:
            print(f"traceshepherd: error: could not write output: {exc}", file=sys.stderr)
            return 2
    else:
        sys.stdout.write(output)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
