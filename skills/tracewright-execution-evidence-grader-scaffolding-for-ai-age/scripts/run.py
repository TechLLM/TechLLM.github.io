"""Tracewright reference CLI for execution-evidence grading.

This module implements a small, deterministic version of Tracewright: it can
grade an agent run against a compact evidence specification, run a built-in
self-test, and scaffold a standalone Python grader with sample fixtures. It
uses only the Python standard library and never requires an API key.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple


class TracewrightError(Exception):
    """Raised when Tracewright cannot parse input or load evidence."""


SAMPLE_SPEC: Dict[str, Any] = {
    "task_id": "sample-agent-edit",
    "required_files": ["src/feature.py"],
    "forbidden_files": ["secrets.txt"],
    "expected_edits": ["src/feature.py"],
    "forbidden_edits": ["config/prod.env"],
    "trace": {
        "required": [
            {"type": "read", "path": "src/feature.py"},
            {"type": "write", "path": "src/feature.py"},
            {"type": "command", "pattern": r"python\s+scripts/test.py"},
        ],
        "forbidden": [
            {"type": "api_call", "pattern": "production"},
        ],
    },
    "diff": {
        "required_patterns": [r"\+def calculate_total"],
        "forbidden_patterns": ["API_KEY|password"],
    },
    "output": {
        "must_contain": ["tests passed"],
        "must_match": [r"score:\s*1\.0"],
    },
    "audit": {
        "must_contain": ["tracewright: completed"],
    },
}


SAMPLE_ARTIFACTS: Dict[str, Any] = {
    "workspace_files": {
        "src/feature.py": "def calculate_total(items):\n    return sum(items)\n",
    },
    "changed_files": ["src/feature.py"],
    "trace_events": [
        {"type": "read", "path": "src/feature.py"},
        {"type": "write", "path": "src/feature.py"},
        {"type": "command", "command": "python scripts/test.py"},
    ],
    "diff_text": (
        "diff --git a/src/feature.py b/src/feature.py\n"
        "--- a/src/feature.py\n"
        "+++ b/src/feature.py\n"
        "@@\n"
        "+def calculate_total(items):\n"
        "+    return sum(items)\n"
    ),
    "final_output": "tests passed\nscore: 1.0\n",
    "audit_log": "tracewright: completed\n",
}


SEMANTIC_PLACEHOLDERS: Dict[str, str] = {
    "MENTIONS_FILES": r"\b(file|files|path|paths|workspace)\b",
    "MENTIONS_SUCCESS": r"\b(success|succeeded|passed|complete|completed)\b",
    "MENTIONS_TESTS": r"\b(test|tests|pytest|unittest|selftest)\b",
}


def _as_list(value: Any) -> List[Any]:
    """Return value as a list while treating None as an empty list."""

    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _read_text(path: Path, label: str) -> str:
    """Read UTF-8 text from path with a clear Tracewright error on failure."""

    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise TracewrightError(f"{label} not found: {path}") from exc
    except OSError as exc:
        raise TracewrightError(f"could not read {label} {path}: {exc}") from exc


def _write_text(path: Path, text: str) -> None:
    """Write UTF-8 text, creating parent directories as needed."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_scalar(value: str) -> Any:
    """Parse a small YAML scalar into a Python value."""

    value = value.strip()
    if value == "":
        return ""
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "None", "~"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if value.startswith("[") or value.startswith("{"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def _split_key_value(content: str) -> Tuple[str, str]:
    """Split a simple YAML key-value line into key and value text."""

    if ":" not in content:
        raise TracewrightError(f"invalid YAML line, expected key: value: {content}")
    key, value = content.split(":", 1)
    key = key.strip()
    if not key:
        raise TracewrightError(f"invalid YAML line with empty key: {content}")
    return key, value.strip()


def parse_simple_yaml(text: str) -> Dict[str, Any]:
    """Parse the small YAML subset used by Tracewright specs.

    Supported shapes are nested dictionaries, lists, list items like
    ``- key: value``, quoted or bare strings, numbers, booleans, nulls, and
    JSON-style inline lists or objects.
    """

    lines: List[Tuple[int, str]] = []
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        lines.append((indent, raw_line.strip()))

    if not lines:
        return {}

    def parse_block(index: int, indent: int) -> Tuple[Any, int]:
        if index >= len(lines):
            return {}, index

        is_list = lines[index][1].startswith("- ")
        if is_list:
            items: List[Any] = []
            while index < len(lines):
                current_indent, content = lines[index]
                if current_indent != indent or not content.startswith("- "):
                    break
                item_text = content[2:].strip()
                index += 1
                if not item_text:
                    if index < len(lines) and lines[index][0] > indent:
                        value, index = parse_block(index, lines[index][0])
                    else:
                        value = None
                    items.append(value)
                    continue

                if ":" in item_text and not item_text.startswith(("http://", "https://")):
                    key, scalar_text = _split_key_value(item_text)
                    item: Dict[str, Any] = {key: parse_scalar(scalar_text)}
                    if scalar_text == "" and index < len(lines) and lines[index][0] > indent:
                        nested, index = parse_block(index, lines[index][0])
                        item[key] = nested
                    if index < len(lines) and lines[index][0] > indent:
                        nested, index = parse_block(index, lines[index][0])
                        if isinstance(nested, dict):
                            item.update(nested)
                    items.append(item)
                else:
                    items.append(parse_scalar(item_text))
            return items, index

        result: Dict[str, Any] = {}
        while index < len(lines):
            current_indent, content = lines[index]
            if current_indent != indent or content.startswith("- "):
                break
            key, scalar_text = _split_key_value(content)
            index += 1
            if scalar_text == "":
                if index < len(lines) and lines[index][0] > indent:
                    value, index = parse_block(index, lines[index][0])
                else:
                    value = {}
            else:
                value = parse_scalar(scalar_text)
            result[key] = value
        return result, index

    parsed, next_index = parse_block(0, lines[0][0])
    if next_index != len(lines):
        raise TracewrightError("could not parse the complete YAML document")
    if not isinstance(parsed, dict):
        raise TracewrightError("Tracewright spec must be a mapping")
    return parsed


def load_spec(path: Path) -> Dict[str, Any]:
    """Load a Tracewright task specification from JSON or simple YAML."""

    text = _read_text(path, "spec")
    suffix = path.suffix.lower()
    try:
        if suffix == ".json":
            data = json.loads(text)
        elif suffix in {".yaml", ".yml"}:
            data = parse_simple_yaml(text)
        else:
            raise TracewrightError("spec must end with .json, .yaml, or .yml")
    except json.JSONDecodeError as exc:
        raise TracewrightError(f"invalid JSON spec {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise TracewrightError("Tracewright spec must decode to a JSON object")
    return data


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Load newline-delimited JSON tool trace events."""

    events: List[Dict[str, Any]] = []
    text = _read_text(path, "trace")
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TracewrightError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
        if not isinstance(event, dict):
            raise TracewrightError(f"trace event at {path}:{line_number} is not an object")
        events.append(event)
    return events


def collect_workspace_files(workspace: Path) -> Dict[str, str]:
    """Collect relative workspace file contents for deterministic grading."""

    if not workspace.exists():
        raise TracewrightError(f"workspace not found: {workspace}")
    if not workspace.is_dir():
        raise TracewrightError(f"workspace is not a directory: {workspace}")
    files: Dict[str, str] = {}
    for path in sorted(p for p in workspace.rglob("*") if p.is_file()):
        relative = path.relative_to(workspace).as_posix()
        try:
            files[relative] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            files[relative] = ""
        except OSError as exc:
            raise TracewrightError(f"could not read workspace file {relative}: {exc}") from exc
    return files


def changed_files_from_diff(diff_text: str) -> List[str]:
    """Extract changed file paths from a unified diff."""

    changed: List[str] = []
    seen = set()
    for line in diff_text.splitlines():
        path = None
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                candidate = parts[3]
                path = candidate[2:] if candidate.startswith("b/") else candidate
        elif line.startswith("+++ ") and not line.startswith("+++ /dev/null"):
            candidate = line[4:].strip()
            path = candidate[2:] if candidate.startswith("b/") else candidate
        if path and path not in seen:
            seen.add(path)
            changed.append(path)
    return changed


def event_matches(event: Mapping[str, Any], requirement: Mapping[str, Any]) -> bool:
    """Return True when a trace event satisfies a requirement mapping."""

    serialized = json.dumps(event, sort_keys=True)
    for key, expected in requirement.items():
        if key == "pattern":
            if re.search(str(expected), serialized) is None:
                return False
        elif event.get(key) != expected:
            return False
    return True


def _add_check(
    checks: List[Dict[str, Any]],
    check_id: str,
    category: str,
    passed: bool,
    message: str,
) -> None:
    """Append one normalized check result to the report."""

    checks.append(
        {
            "id": check_id,
            "category": category,
            "passed": bool(passed),
            "message": message,
        }
    )


def grade_artifacts(spec: Mapping[str, Any], artifacts: Mapping[str, Any]) -> Dict[str, Any]:
    """Grade execution artifacts against a Tracewright evidence specification."""

    checks: List[Dict[str, Any]] = []
    workspace_files = artifacts.get("workspace_files", {})
    changed_files = set(_as_list(artifacts.get("changed_files")))
    trace_events = _as_list(artifacts.get("trace_events"))
    diff_text = str(artifacts.get("diff_text", ""))
    final_output = str(artifacts.get("final_output", ""))
    audit_log = str(artifacts.get("audit_log", ""))

    if not isinstance(workspace_files, Mapping):
        raise TracewrightError("artifacts.workspace_files must be a mapping of path to text")

    for path in _as_list(spec.get("required_files")):
        exists = str(path) in workspace_files
        _add_check(
            checks,
            f"file.required:{path}",
            "files",
            exists,
            f"Required file exists: {path}" if exists else f"Required file missing: {path}",
        )

    for path in _as_list(spec.get("forbidden_files")):
        absent = str(path) not in workspace_files
        _add_check(
            checks,
            f"file.forbidden:{path}",
            "files",
            absent,
            f"Forbidden file absent: {path}" if absent else f"Forbidden file present: {path}",
        )

    for path in _as_list(spec.get("expected_edits")):
        edited = str(path) in changed_files
        _add_check(
            checks,
            f"edit.expected:{path}",
            "diff",
            edited,
            f"Expected edit observed: {path}" if edited else f"Expected edit missing: {path}",
        )

    for path in _as_list(spec.get("forbidden_edits")):
        untouched = str(path) not in changed_files
        _add_check(
            checks,
            f"edit.forbidden:{path}",
            "diff",
            untouched,
            f"Forbidden edit absent: {path}" if untouched else f"Forbidden edit observed: {path}",
        )

    trace_spec = spec.get("trace", spec.get("tool_trace", {}))
    if isinstance(trace_spec, Mapping):
        for index, requirement in enumerate(_as_list(trace_spec.get("required")), start=1):
            if not isinstance(requirement, Mapping):
                raise TracewrightError("trace.required entries must be objects")
            found = any(
                isinstance(event, Mapping) and event_matches(event, requirement)
                for event in trace_events
            )
            _add_check(
                checks,
                f"trace.required:{index}",
                "trace",
                found,
                f"Required trace event observed: {dict(requirement)}"
                if found
                else f"Required trace event missing: {dict(requirement)}",
            )
        for index, requirement in enumerate(_as_list(trace_spec.get("forbidden")), start=1):
            if not isinstance(requirement, Mapping):
                raise TracewrightError("trace.forbidden entries must be objects")
            found = any(
                isinstance(event, Mapping) and event_matches(event, requirement)
                for event in trace_events
            )
            _add_check(
                checks,
                f"trace.forbidden:{index}",
                "trace",
                not found,
                f"Forbidden trace event absent: {dict(requirement)}"
                if not found
                else f"Forbidden trace event observed: {dict(requirement)}",
            )

    diff_spec = spec.get("diff", {})
    if isinstance(diff_spec, Mapping):
        for index, pattern in enumerate(_as_list(diff_spec.get("required_patterns")), start=1):
            found = re.search(str(pattern), diff_text, flags=re.MULTILINE) is not None
            _add_check(
                checks,
                f"diff.required_pattern:{index}",
                "diff",
                found,
                f"Required diff pattern matched: {pattern}"
                if found
                else f"Required diff pattern missing: {pattern}",
            )
        for index, pattern in enumerate(_as_list(diff_spec.get("forbidden_patterns")), start=1):
            found = re.search(str(pattern), diff_text, flags=re.MULTILINE) is not None
            _add_check(
                checks,
                f"diff.forbidden_pattern:{index}",
                "diff",
                not found,
                f"Forbidden diff pattern absent: {pattern}"
                if not found
                else f"Forbidden diff pattern matched: {pattern}",
            )

    output_spec = spec.get("output", spec.get("final_output", {}))
    if isinstance(output_spec, Mapping):
        for index, needle in enumerate(_as_list(output_spec.get("must_contain")), start=1):
            found = str(needle) in final_output
            _add_check(
                checks,
                f"output.must_contain:{index}",
                "output",
                found,
                f"Output contains required text: {needle}"
                if found
                else f"Output missing required text: {needle}",
            )
        for index, pattern in enumerate(_as_list(output_spec.get("must_match")), start=1):
            found = re.search(str(pattern), final_output, flags=re.MULTILINE) is not None
            _add_check(
                checks,
                f"output.must_match:{index}",
                "output",
                found,
                f"Output pattern matched: {pattern}" if found else f"Output pattern missing: {pattern}",
            )
        for index, name in enumerate(_as_list(output_spec.get("semantic_placeholders")), start=1):
            pattern = SEMANTIC_PLACEHOLDERS.get(str(name))
            if pattern is None:
                _add_check(
                    checks,
                    f"output.semantic:{index}",
                    "output",
                    False,
                    f"Unknown semantic placeholder: {name}",
                )
            else:
                found = re.search(pattern, final_output, flags=re.IGNORECASE) is not None
                _add_check(
                    checks,
                    f"output.semantic:{index}",
                    "output",
                    found,
                    f"Semantic placeholder matched: {name}"
                    if found
                    else f"Semantic placeholder missing: {name}",
                )

    audit_spec = spec.get("audit", spec.get("audit_log", {}))
    if isinstance(audit_spec, Mapping):
        for index, needle in enumerate(_as_list(audit_spec.get("must_contain")), start=1):
            found = str(needle) in audit_log
            _add_check(
                checks,
                f"audit.must_contain:{index}",
                "audit",
                found,
                f"Audit log contains required text: {needle}"
                if found
                else f"Audit log missing required text: {needle}",
            )
        for index, pattern in enumerate(_as_list(audit_spec.get("must_match")), start=1):
            found = re.search(str(pattern), audit_log, flags=re.MULTILINE) is not None
            _add_check(
                checks,
                f"audit.must_match:{index}",
                "audit",
                found,
                f"Audit log pattern matched: {pattern}"
                if found
                else f"Audit log pattern missing: {pattern}",
            )

    passed_count = sum(1 for check in checks if check["passed"])
    failed_count = len(checks) - passed_count
    score = round(passed_count / len(checks), 3) if checks else 1.0
    return {
        "task_id": str(spec.get("task_id", "unnamed-task")),
        "passed": failed_count == 0,
        "score": score,
        "summary": {
            "passed": passed_count,
            "failed": failed_count,
            "total": len(checks),
        },
        "checks": checks,
    }


def load_artifacts_from_args(args: argparse.Namespace) -> Dict[str, Any]:
    """Load workspace, trace, diff, output, and audit artifacts from CLI args."""

    diff_text = _read_text(Path(args.diff), "diff") if args.diff else ""
    return {
        "workspace_files": collect_workspace_files(Path(args.workspace)) if args.workspace else {},
        "changed_files": changed_files_from_diff(diff_text),
        "trace_events": load_jsonl(Path(args.trace)) if args.trace else [],
        "diff_text": diff_text,
        "final_output": _read_text(Path(args.output), "output") if args.output else "",
        "audit_log": _read_text(Path(args.audit), "audit") if args.audit else "",
    }


def regex_to_sample_text(pattern: str) -> str:
    """Convert a simple regular expression into deterministic sample text."""

    text = pattern
    replacements = [
        (r"\s+", " "),
        (r"\s*", ""),
        (r"\d+", "1"),
        (r"\w+", "word"),
        (r"\+", "+"),
        (r"\.", "."),
        (r"\-", "-"),
        (r"\_", "_"),
        ("^", ""),
        ("$", ""),
        (".*", "sample"),
        (".+", "sample"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    text = text.replace("\\", "")
    text = re.sub(r"\([^)]*\|([^)]*)\)", r"\1", text)
    text = text.replace("?", "")
    return text or "sample"


def _trace_event_for_requirement(requirement: Mapping[str, Any]) -> Dict[str, Any]:
    """Build a sample trace event that satisfies a requirement where practical."""

    event = {key: value for key, value in requirement.items() if key != "pattern"}
    pattern = requirement.get("pattern")
    if pattern is not None:
        sample = regex_to_sample_text(str(pattern))
        event_type = str(event.get("type", "event"))
        if event_type == "command":
            event["command"] = sample
        elif event_type == "api_call":
            event["endpoint"] = sample
        else:
            event["detail"] = sample
    return event


def make_pass_fixture(spec: Mapping[str, Any]) -> Dict[str, str]:
    """Create deterministic passing fixture file contents for a spec."""

    files: Dict[str, str] = {}
    for path in _as_list(spec.get("required_files")):
        if str(path).endswith("feature.py"):
            files[f"workspace/{path}"] = "def calculate_total(items):\n    return sum(items)\n"
        else:
            files[f"workspace/{path}"] = f"sample evidence file for {path}\n"

    trace_spec = spec.get("trace", spec.get("tool_trace", {}))
    events = []
    if isinstance(trace_spec, Mapping):
        for requirement in _as_list(trace_spec.get("required")):
            if isinstance(requirement, Mapping):
                events.append(_trace_event_for_requirement(requirement))
    files["trace.jsonl"] = "".join(json.dumps(event, sort_keys=True) + "\n" for event in events)

    diff_lines: List[str] = []
    edited_paths = [str(path) for path in _as_list(spec.get("expected_edits"))]
    for path in edited_paths:
        diff_lines.extend(
            [
                f"diff --git a/{path} b/{path}",
                f"--- a/{path}",
                f"+++ b/{path}",
                "@@",
                "+tracewright generated evidence line",
            ]
        )
    diff_spec = spec.get("diff", {})
    if isinstance(diff_spec, Mapping):
        for pattern in _as_list(diff_spec.get("required_patterns")):
            diff_lines.append(regex_to_sample_text(str(pattern)))
    files["diff.patch"] = "\n".join(diff_lines).rstrip() + "\n"

    output_lines: List[str] = []
    output_spec = spec.get("output", spec.get("final_output", {}))
    if isinstance(output_spec, Mapping):
        output_lines.extend(str(item) for item in _as_list(output_spec.get("must_contain")))
        output_lines.extend(regex_to_sample_text(str(item)) for item in _as_list(output_spec.get("must_match")))
        for placeholder in _as_list(output_spec.get("semantic_placeholders")):
            if placeholder == "MENTIONS_TESTS":
                output_lines.append("tests completed")
            elif placeholder == "MENTIONS_FILES":
                output_lines.append("files checked")
            elif placeholder == "MENTIONS_SUCCESS":
                output_lines.append("success")
    files["output.txt"] = "\n".join(output_lines).rstrip() + "\n"

    audit_lines: List[str] = []
    audit_spec = spec.get("audit", spec.get("audit_log", {}))
    if isinstance(audit_spec, Mapping):
        audit_lines.extend(str(item) for item in _as_list(audit_spec.get("must_contain")))
        audit_lines.extend(regex_to_sample_text(str(item)) for item in _as_list(audit_spec.get("must_match")))
    files["audit.log"] = "\n".join(audit_lines).rstrip() + "\n"
    return files


def make_fail_fixture(spec: Mapping[str, Any]) -> Dict[str, str]:
    """Create deterministic failing fixture file contents for a spec."""

    files: Dict[str, str] = {"workspace/README.md": "This fixture intentionally misses required evidence.\n"}
    for path in _as_list(spec.get("forbidden_files")):
        files[f"workspace/{path}"] = "forbidden sample file\n"
        break
    forbidden_edits = _as_list(spec.get("forbidden_edits"))
    changed_path = str(forbidden_edits[0]) if forbidden_edits else "unexpected.txt"
    files["trace.jsonl"] = json.dumps({"type": "api_call", "endpoint": "production"}) + "\n"
    files["diff.patch"] = (
        f"diff --git a/{changed_path} b/{changed_path}\n"
        f"--- a/{changed_path}\n"
        f"+++ b/{changed_path}\n"
        "@@\n"
        "+API_KEY=example\n"
    )
    files["output.txt"] = "run failed\n"
    files["audit.log"] = "audit incomplete\n"
    return files


def generated_grader_source(spec: Mapping[str, Any]) -> str:
    """Return source code for a standalone generated grader."""

    spec_json = json.dumps(spec, indent=2, sort_keys=True)
    template = r'''"""Generated Tracewright grader.

This file is standalone and deterministic. It grades workspace files, a JSONL
trace, a unified diff, final output text, and an audit log against the embedded
Tracewright evidence specification.
"""

import argparse
import json
import re
import sys
from pathlib import Path

SPEC = __SPEC_JSON__

SEMANTIC_PLACEHOLDERS = {
    "MENTIONS_FILES": r"\b(file|files|path|paths|workspace)\b",
    "MENTIONS_SUCCESS": r"\b(success|succeeded|passed|complete|completed)\b",
    "MENTIONS_TESTS": r"\b(test|tests|pytest|unittest|selftest)\b",
}


def as_list(value):
    """Return value as a list while treating None as an empty list."""
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def read_text(path):
    """Read UTF-8 text from path."""
    return Path(path).read_text(encoding="utf-8")


def collect_workspace_files(workspace):
    """Collect relative file contents from a workspace directory."""
    root = Path(workspace)
    files = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        try:
            files[rel] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            files[rel] = ""
    return files


def load_jsonl(path):
    """Load newline-delimited JSON trace events."""
    events = []
    for line_number, line in enumerate(read_text(path).splitlines(), start=1):
        if not line.strip():
            continue
        event = json.loads(line)
        if not isinstance(event, dict):
            raise ValueError(f"trace event at line {line_number} is not an object")
        events.append(event)
    return events


def changed_files_from_diff(diff_text):
    """Extract changed paths from a unified diff."""
    changed = []
    seen = set()
    for line in diff_text.splitlines():
        path = None
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                path = parts[3][2:] if parts[3].startswith("b/") else parts[3]
        elif line.startswith("+++ ") and not line.startswith("+++ /dev/null"):
            candidate = line[4:].strip()
            path = candidate[2:] if candidate.startswith("b/") else candidate
        if path and path not in seen:
            seen.add(path)
            changed.append(path)
    return changed


def event_matches(event, requirement):
    """Return True when one event satisfies a requirement."""
    serialized = json.dumps(event, sort_keys=True)
    for key, expected in requirement.items():
        if key == "pattern":
            if re.search(str(expected), serialized) is None:
                return False
        elif event.get(key) != expected:
            return False
    return True


def add_check(checks, check_id, category, passed, message):
    """Append a normalized check result."""
    checks.append({"id": check_id, "category": category, "passed": bool(passed), "message": message})


def grade(spec, artifacts):
    """Grade execution artifacts and return a JSON-serializable report."""
    checks = []
    workspace_files = artifacts.get("workspace_files", {})
    changed_files = set(as_list(artifacts.get("changed_files")))
    trace_events = as_list(artifacts.get("trace_events"))
    diff_text = str(artifacts.get("diff_text", ""))
    final_output = str(artifacts.get("final_output", ""))
    audit_log = str(artifacts.get("audit_log", ""))

    for path in as_list(spec.get("required_files")):
        ok = str(path) in workspace_files
        add_check(checks, f"file.required:{path}", "files", ok, f"Required file exists: {path}" if ok else f"Required file missing: {path}")
    for path in as_list(spec.get("forbidden_files")):
        ok = str(path) not in workspace_files
        add_check(checks, f"file.forbidden:{path}", "files", ok, f"Forbidden file absent: {path}" if ok else f"Forbidden file present: {path}")
    for path in as_list(spec.get("expected_edits")):
        ok = str(path) in changed_files
        add_check(checks, f"edit.expected:{path}", "diff", ok, f"Expected edit observed: {path}" if ok else f"Expected edit missing: {path}")
    for path in as_list(spec.get("forbidden_edits")):
        ok = str(path) not in changed_files
        add_check(checks, f"edit.forbidden:{path}", "diff", ok, f"Forbidden edit absent: {path}" if ok else f"Forbidden edit observed: {path}")

    trace_spec = spec.get("trace", spec.get("tool_trace", {}))
    if isinstance(trace_spec, dict):
        for index, requirement in enumerate(as_list(trace_spec.get("required")), start=1):
            ok = any(isinstance(event, dict) and event_matches(event, requirement) for event in trace_events)
            add_check(checks, f"trace.required:{index}", "trace", ok, f"Required trace event observed: {dict(requirement)}" if ok else f"Required trace event missing: {dict(requirement)}")
        for index, requirement in enumerate(as_list(trace_spec.get("forbidden")), start=1):
            found = any(isinstance(event, dict) and event_matches(event, requirement) for event in trace_events)
            add_check(checks, f"trace.forbidden:{index}", "trace", not found, f"Forbidden trace event absent: {dict(requirement)}" if not found else f"Forbidden trace event observed: {dict(requirement)}")

    diff_spec = spec.get("diff", {})
    if isinstance(diff_spec, dict):
        for index, pattern in enumerate(as_list(diff_spec.get("required_patterns")), start=1):
            ok = re.search(str(pattern), diff_text, flags=re.MULTILINE) is not None
            add_check(checks, f"diff.required_pattern:{index}", "diff", ok, f"Required diff pattern matched: {pattern}" if ok else f"Required diff pattern missing: {pattern}")
        for index, pattern in enumerate(as_list(diff_spec.get("forbidden_patterns")), start=1):
            found = re.search(str(pattern), diff_text, flags=re.MULTILINE) is not None
            add_check(checks, f"diff.forbidden_pattern:{index}", "diff", not found, f"Forbidden diff pattern absent: {pattern}" if not found else f"Forbidden diff pattern matched: {pattern}")

    output_spec = spec.get("output", spec.get("final_output", {}))
    if isinstance(output_spec, dict):
        for index, text in enumerate(as_list(output_spec.get("must_contain")), start=1):
            ok = str(text) in final_output
            add_check(checks, f"output.must_contain:{index}", "output", ok, f"Output contains required text: {text}" if ok else f"Output missing required text: {text}")
        for index, pattern in enumerate(as_list(output_spec.get("must_match")), start=1):
            ok = re.search(str(pattern), final_output, flags=re.MULTILINE) is not None
            add_check(checks, f"output.must_match:{index}", "output", ok, f"Output pattern matched: {pattern}" if ok else f"Output pattern missing: {pattern}")
        for index, name in enumerate(as_list(output_spec.get("semantic_placeholders")), start=1):
            pattern = SEMANTIC_PLACEHOLDERS.get(str(name))
            if pattern is None:
                add_check(checks, f"output.semantic:{index}", "output", False, f"Unknown semantic placeholder: {name}")
            else:
                ok = re.search(pattern, final_output, flags=re.IGNORECASE) is not None
                add_check(checks, f"output.semantic:{index}", "output", ok, f"Semantic placeholder matched: {name}" if ok else f"Semantic placeholder missing: {name}")

    audit_spec = spec.get("audit", spec.get("audit_log", {}))
    if isinstance(audit_spec, dict):
        for index, text in enumerate(as_list(audit_spec.get("must_contain")), start=1):
            ok = str(text) in audit_log
            add_check(checks, f"audit.must_contain:{index}", "audit", ok, f"Audit log contains required text: {text}" if ok else f"Audit log missing required text: {text}")
        for index, pattern in enumerate(as_list(audit_spec.get("must_match")), start=1):
            ok = re.search(str(pattern), audit_log, flags=re.MULTILINE) is not None
            add_check(checks, f"audit.must_match:{index}", "audit", ok, f"Audit log pattern matched: {pattern}" if ok else f"Audit log pattern missing: {pattern}")

    passed = sum(1 for check in checks if check["passed"])
    failed = len(checks) - passed
    return {
        "task_id": str(spec.get("task_id", "unnamed-task")),
        "passed": failed == 0,
        "score": round(passed / len(checks), 3) if checks else 1.0,
        "summary": {"passed": passed, "failed": failed, "total": len(checks)},
        "checks": checks,
    }


def main(argv=None):
    """Run the generated grader CLI."""
    parser = argparse.ArgumentParser(description="Run a generated Tracewright grader.")
    parser.add_argument("--workspace", required=True, help="Workspace directory after the agent run.")
    parser.add_argument("--trace", required=True, help="JSONL tool trace file.")
    parser.add_argument("--diff", required=True, help="Unified diff file.")
    parser.add_argument("--output", required=True, help="Final answer or task output text file.")
    parser.add_argument("--audit", required=True, help="Audit log text file.")
    args = parser.parse_args(argv)
    diff_text = read_text(args.diff)
    artifacts = {
        "workspace_files": collect_workspace_files(args.workspace),
        "changed_files": changed_files_from_diff(diff_text),
        "trace_events": load_jsonl(args.trace),
        "diff_text": diff_text,
        "final_output": read_text(args.output),
        "audit_log": read_text(args.audit),
    }
    print(json.dumps(grade(SPEC, artifacts), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''
    return template.replace("__SPEC_JSON__", spec_json)


def scaffold_grader(spec: Mapping[str, Any], out_dir: Path) -> Dict[str, Any]:
    """Write a generated grader and sample fixtures to an output directory."""

    files_written: List[str] = []

    def write_relative(relative: str, text: str) -> None:
        target = out_dir / relative
        _write_text(target, text)
        files_written.append(relative)

    write_relative("grader.py", generated_grader_source(spec))
    write_relative("README.md", textwrap.dedent(
        """\
        # Generated Tracewright Grader

        Run the passing fixture:

        ```bash
        python grader.py --workspace fixtures/pass/workspace --trace fixtures/pass/trace.jsonl --diff fixtures/pass/diff.patch --output fixtures/pass/output.txt --audit fixtures/pass/audit.log
        ```

        Run the failing fixture:

        ```bash
        python grader.py --workspace fixtures/fail/workspace --trace fixtures/fail/trace.jsonl --diff fixtures/fail/diff.patch --output fixtures/fail/output.txt --audit fixtures/fail/audit.log
        ```
        """
    ))

    for relative, text in make_pass_fixture(spec).items():
        write_relative(f"fixtures/pass/{relative}", text)
    for relative, text in make_fail_fixture(spec).items():
        write_relative(f"fixtures/fail/{relative}", text)

    pass_artifacts = {
        "workspace_files": {
            key.removeprefix("workspace/"): value
            for key, value in make_pass_fixture(spec).items()
            if key.startswith("workspace/")
        },
        "changed_files": changed_files_from_diff(make_pass_fixture(spec)["diff.patch"]),
        "trace_events": [
            json.loads(line)
            for line in make_pass_fixture(spec)["trace.jsonl"].splitlines()
            if line.strip()
        ],
        "diff_text": make_pass_fixture(spec)["diff.patch"],
        "final_output": make_pass_fixture(spec)["output.txt"],
        "audit_log": make_pass_fixture(spec)["audit.log"],
    }
    write_relative("fixtures/pass/expected-report.json", json.dumps(grade_artifacts(spec, pass_artifacts), indent=2) + "\n")

    return {"generated": True, "out_dir": out_dir.as_posix(), "files": files_written}


def run_selftest() -> Dict[str, Any]:
    """Run the built-in sample spec and artifacts."""

    return grade_artifacts(SAMPLE_SPEC, SAMPLE_ARTIFACTS)


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the Tracewright CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="Grade execution evidence or scaffold a deterministic Tracewright grader."
    )
    parser.add_argument("--selftest", action="store_true", help="Run built-in sample data with no API key.")
    parser.add_argument(
        "--spec",
        default=os.environ.get("TRACEWRIGHT_SPEC"),
        help="Path to a JSON or simple YAML Tracewright spec. Can also be set with TRACEWRIGHT_SPEC.",
    )
    parser.add_argument("--workspace", help="Workspace directory after the agent run.")
    parser.add_argument("--trace", help="JSONL tool trace file.")
    parser.add_argument("--diff", help="Unified diff file.")
    parser.add_argument("--output", help="Final answer or task output text file.")
    parser.add_argument("--audit", help="Audit log text file.")
    parser.add_argument("--scaffold", action="store_true", help="Generate a standalone grader and sample fixtures.")
    parser.add_argument("--out", default="tracewright_grader", help="Output directory for --scaffold.")
    parser.add_argument(
        "--format",
        choices=["json"],
        default=os.environ.get("TRACEWRIGHT_OUTPUT_FORMAT", "json"),
        help="Output format. TRACEWRIGHT_OUTPUT_FORMAT may also be used.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Tracewright CLI."""

    raw_args = list(sys.argv[1:] if argv is None else argv)
    parser = build_arg_parser()
    args = parser.parse_args(raw_args)

    try:
        if args.selftest or not raw_args:
            print(json.dumps(run_selftest(), indent=2))
            return 0

        if not args.spec:
            parser.error("--spec is required unless --selftest is used")

        spec = load_spec(Path(args.spec))
        if args.scaffold:
            result = scaffold_grader(spec, Path(args.out))
            print(json.dumps(result, indent=2))
            return 0

        artifacts = load_artifacts_from_args(args)
        print(json.dumps(grade_artifacts(spec, artifacts), indent=2))
        return 0
    except TracewrightError as exc:
        print(f"tracewright error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
