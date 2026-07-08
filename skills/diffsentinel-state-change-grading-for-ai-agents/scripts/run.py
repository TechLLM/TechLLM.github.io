#!/usr/bin/env python3
"""DiffSentinel reference CLI for deterministic state-change grading.

The script compares before-and-after directory snapshots against a small
expectation file and emits a machine-readable JSON grading report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Tuple


SUPPORTED_KEYS = {
    "required_files",
    "created_files",
    "deleted_files",
    "modified_files",
    "forbidden_changes",
    "content_contains",
    "content_not_contains",
    "task_log",
    "json_assertions",
}


class DiffSentinelError(Exception):
    """Raised for user-facing DiffSentinel input and parsing errors."""


class MissingValue:
    """Sentinel object used when a JSON path does not exist."""


MISSING = MissingValue()


def parse_scalar(value: str) -> Any:
    """Parse a scalar from the supported YAML subset."""

    text = value.strip()
    if text == "":
        return ""
    if (text.startswith('"') and text.endswith('"')) or (
        text.startswith("'") and text.endswith("'")
    ):
        return text[1:-1]
    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none", "~"}:
        return None
    if lowered == "[]":
        return []
    if lowered == "{}":
        return {}
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return text


def strip_inline_comment(line: str) -> str:
    """Remove comments that start outside quoted strings."""

    in_single = False
    in_double = False
    for index, char in enumerate(line):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            if index == 0 or line[index - 1].isspace():
                return line[:index].rstrip()
    return line.rstrip()


def parse_simple_yaml(text: str) -> Any:
    """Parse a minimal YAML subset sufficient for expectation files."""

    lines: List[Tuple[int, str]] = []
    for number, raw_line in enumerate(text.splitlines(), start=1):
        if "\t" in raw_line:
            raise DiffSentinelError(f"YAML line {number}: tabs are not supported")
        without_comment = strip_inline_comment(raw_line)
        if not without_comment.strip():
            continue
        indent = len(without_comment) - len(without_comment.lstrip(" "))
        lines.append((indent, without_comment.strip()))

    if not lines:
        return {}

    def parse_block(index: int, indent: int) -> Tuple[Any, int]:
        if index >= len(lines):
            return {}, index
        current_indent, current_text = lines[index]
        if current_indent < indent:
            return {}, index
        if current_indent != indent:
            raise DiffSentinelError(
                f"YAML indentation error near: {current_text!r}"
            )
        if current_text.startswith("- "):
            return parse_list(index, indent)
        return parse_mapping(index, indent)

    def parse_list(index: int, indent: int) -> Tuple[List[Any], int]:
        items: List[Any] = []
        while index < len(lines):
            current_indent, current_text = lines[index]
            if current_indent != indent or not current_text.startswith("- "):
                break
            item_text = current_text[2:].strip()
            index += 1
            if item_text == "":
                item, index = parse_block(index, indent + 2)
                items.append(item)
                continue
            if looks_like_inline_mapping(item_text):
                key, value = split_key_value(item_text)
                item_map: Dict[str, Any] = {}
                if value == "":
                    if index < len(lines) and lines[index][0] > indent:
                        nested, index = parse_block(index, indent + 2)
                        item_map[key] = nested
                    else:
                        item_map[key] = {}
                else:
                    item_map[key] = parse_scalar(value)
                if index < len(lines) and lines[index][0] == indent + 2:
                    nested, index = parse_mapping(index, indent + 2)
                    item_map.update(nested)
                items.append(item_map)
            else:
                items.append(parse_scalar(item_text))
        return items, index

    def parse_mapping(index: int, indent: int) -> Tuple[Dict[str, Any], int]:
        mapping: Dict[str, Any] = {}
        while index < len(lines):
            current_indent, current_text = lines[index]
            if current_indent < indent:
                break
            if current_indent != indent:
                raise DiffSentinelError(
                    f"YAML indentation error near: {current_text!r}"
                )
            if current_text.startswith("- "):
                break
            key, value = split_key_value(current_text)
            index += 1
            if value == "":
                if index < len(lines) and lines[index][0] > indent:
                    nested, index = parse_block(index, indent + 2)
                    mapping[key] = nested
                else:
                    mapping[key] = {}
            else:
                mapping[key] = parse_scalar(value)
        return mapping, index

    parsed, final_index = parse_block(0, lines[0][0])
    if final_index != len(lines):
        raise DiffSentinelError("YAML parser stopped before end of file")
    return parsed


def split_key_value(text: str) -> Tuple[str, str]:
    """Split a YAML key-value line into key and value text."""

    if ":" not in text:
        raise DiffSentinelError(f"Expected 'key: value' entry, got {text!r}")
    key, value = text.split(":", 1)
    key = key.strip()
    if not key:
        raise DiffSentinelError(f"Missing YAML key in {text!r}")
    return key, value.strip()


def looks_like_inline_mapping(text: str) -> bool:
    """Return true when a list item looks like a compact `key: value` mapping."""

    stripped = text.strip()
    if not stripped or stripped[0] in {"'", '"'}:
        return False
    if ":" not in stripped:
        return False
    key = stripped.split(":", 1)[0].strip()
    return bool(key) and all(char not in key for char in " \r\n\t")


def load_expectations(path: Path) -> Dict[str, Any]:
    """Load an expectation file as JSON or the supported YAML subset."""

    if not path.exists():
        raise DiffSentinelError(f"Expectation file not found: {path}")
    text = path.read_text(encoding="utf-8")
    try:
        if path.suffix.lower() == ".json":
            parsed = json.loads(text)
        else:
            parsed = parse_simple_yaml(text)
    except json.JSONDecodeError as exc:
        raise DiffSentinelError(f"Invalid JSON expectation file: {exc}") from exc

    if not isinstance(parsed, dict):
        raise DiffSentinelError("Expectation file must contain a top-level mapping")
    return parsed


def normalize_path(value: Any) -> str:
    """Normalize a relative expectation path to POSIX-style text."""

    if not isinstance(value, str):
        raise DiffSentinelError(f"Expected a path string, got {value!r}")
    cleaned = value.strip().replace("\\", "/")
    if cleaned.startswith("/") or cleaned == "" or ".." in Path(cleaned).parts:
        raise DiffSentinelError(f"Unsafe or invalid relative path: {value!r}")
    return cleaned


def ensure_list(value: Any, key: str) -> List[Any]:
    """Return a value as a list or raise a clear schema error."""

    if value is None:
        return []
    if not isinstance(value, list):
        raise DiffSentinelError(f"Expectation key {key!r} must be a list")
    return value


def ensure_mapping(value: Any, key: str) -> Mapping[str, Any]:
    """Return a value as a mapping or raise a clear schema error."""

    if value is None:
        return {}
    if not isinstance(value, dict):
        raise DiffSentinelError(f"Expectation key {key!r} must be a mapping")
    return value


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest for a file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_directory(root: Path) -> Dict[str, Dict[str, Any]]:
    """Create a deterministic snapshot of all files below a directory."""

    if not root.exists():
        raise DiffSentinelError(f"Directory not found: {root}")
    if not root.is_dir():
        raise DiffSentinelError(f"Expected a directory: {root}")

    snapshot: Dict[str, Dict[str, Any]] = {}
    for current_root, dirs, files in os.walk(root):
        dirs.sort()
        files.sort()
        for name in files:
            full_path = Path(current_root) / name
            relative = full_path.relative_to(root).as_posix()
            snapshot[relative] = {
                "sha256": sha256_file(full_path),
                "size": full_path.stat().st_size,
            }
    return snapshot


def read_text_file(root: Path, relative_path: str) -> str:
    """Read a relative file as UTF-8 text with replacement characters."""

    path = root / relative_path
    if not path.exists():
        raise DiffSentinelError(f"File not found in after snapshot: {relative_path}")
    return path.read_text(encoding="utf-8", errors="replace")


def load_json_file(root: Path, relative_path: str) -> Any:
    """Load a relative JSON file and return parsed data."""

    path = root / relative_path
    if not path.exists():
        return MISSING
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DiffSentinelError(f"Invalid JSON in {relative_path}: {exc}") from exc


def get_json_path(document: Any, path: str) -> Any:
    """Read a dot-separated object/list path from a JSON document."""

    if document is MISSING:
        return MISSING
    current = document
    if path == "":
        return current
    for part in path.split("."):
        if isinstance(current, list):
            try:
                index = int(part)
            except ValueError:
                return MISSING
            if index < 0 or index >= len(current):
                return MISSING
            current = current[index]
        elif isinstance(current, dict):
            if part not in current:
                return MISSING
            current = current[part]
        else:
            return MISSING
    return current


def json_value_for_report(value: Any) -> Any:
    """Convert internal sentinel values into stable report-friendly values."""

    if value is MISSING:
        return "<missing>"
    return value


def add_check(
    checks: List[Dict[str, Any]],
    kind: str,
    target: str,
    passed: bool,
    detail: str,
    observed: Any | None = None,
    expected: Any | None = None,
) -> None:
    """Append one deterministic check entry to the report."""

    entry: Dict[str, Any] = {
        "id": f"{kind}:{target}",
        "kind": kind,
        "target": target,
        "status": "pass" if passed else "fail",
        "detail": detail,
    }
    if expected is not None:
        entry["expected"] = expected
    if observed is not None:
        entry["observed"] = observed
    checks.append(entry)


def grade_state_change(
    before_dir: Path,
    after_dir: Path,
    expectations: Mapping[str, Any],
    threshold: float = 1.0,
) -> Dict[str, Any]:
    """Grade state changes between two directories against expectations."""

    before = snapshot_directory(before_dir)
    after = snapshot_directory(after_dir)
    before_paths = set(before)
    after_paths = set(after)
    created = sorted(after_paths - before_paths)
    deleted = sorted(before_paths - after_paths)
    modified = sorted(
        path
        for path in before_paths & after_paths
        if before[path]["sha256"] != after[path]["sha256"]
    )
    unchanged = sorted(
        path
        for path in before_paths & after_paths
        if before[path]["sha256"] == after[path]["sha256"]
    )
    changed_paths = set(created) | set(deleted) | set(modified)

    checks: List[Dict[str, Any]] = []
    warnings: List[str] = []
    for key in sorted(expectations):
        if key not in SUPPORTED_KEYS:
            warnings.append(f"Unsupported expectation key ignored: {key}")

    for item in ensure_list(expectations.get("required_files", []), "required_files"):
        path = normalize_path(item)
        add_check(
            checks,
            "required_files",
            path,
            path in after_paths,
            "File exists in after snapshot."
            if path in after_paths
            else "File is missing from after snapshot.",
        )

    for item in ensure_list(expectations.get("created_files", []), "created_files"):
        path = normalize_path(item)
        add_check(
            checks,
            "created_files",
            path,
            path in created,
            "File was created."
            if path in created
            else "File was not newly created.",
            observed=path in after_paths,
            expected="absent before and present after",
        )

    for item in ensure_list(expectations.get("deleted_files", []), "deleted_files"):
        path = normalize_path(item)
        add_check(
            checks,
            "deleted_files",
            path,
            path in deleted,
            "File was deleted."
            if path in deleted
            else "File was not deleted.",
            observed=path not in after_paths,
            expected="present before and absent after",
        )

    for item in ensure_list(expectations.get("modified_files", []), "modified_files"):
        path = normalize_path(item)
        add_check(
            checks,
            "modified_files",
            path,
            path in modified,
            "File content changed."
            if path in modified
            else "File content did not change.",
            observed=path in modified,
            expected=True,
        )

    for item in ensure_list(
        expectations.get("forbidden_changes", []), "forbidden_changes"
    ):
        path = normalize_path(item)
        add_check(
            checks,
            "forbidden_changes",
            path,
            path not in changed_paths,
            "File did not change."
            if path not in changed_paths
            else "File changed but was forbidden.",
            observed=path in changed_paths,
            expected=False,
        )

    contains = ensure_mapping(
        expectations.get("content_contains", {}), "content_contains"
    )
    for raw_path in sorted(contains):
        path = normalize_path(raw_path)
        text = read_text_file(after_dir, path) if path in after_paths else ""
        for needle in ensure_list(contains[raw_path], f"content_contains.{path}"):
            if not isinstance(needle, str):
                raise DiffSentinelError(
                    f"Content assertion for {path} must be a string"
                )
            target = f"{path} contains {needle!r}"
            add_check(
                checks,
                "content_contains",
                target,
                needle in text,
                "Required string found."
                if needle in text
                else "Required string missing.",
                expected=needle,
            )

    not_contains = ensure_mapping(
        expectations.get("content_not_contains", {}), "content_not_contains"
    )
    for raw_path in sorted(not_contains):
        path = normalize_path(raw_path)
        text = read_text_file(after_dir, path) if path in after_paths else ""
        for needle in ensure_list(
            not_contains[raw_path], f"content_not_contains.{path}"
        ):
            if not isinstance(needle, str):
                raise DiffSentinelError(
                    f"Negative content assertion for {path} must be a string"
                )
            target = f"{path} excludes {needle!r}"
            add_check(
                checks,
                "content_not_contains",
                target,
                needle not in text,
                "Forbidden string absent."
                if needle not in text
                else "Forbidden string present.",
                expected=f"not {needle}",
            )

    task_log = expectations.get("task_log")
    if task_log is not None:
        task_mapping = ensure_mapping(task_log, "task_log")
        log_path = normalize_path(task_mapping.get("file", "logs/task.log"))
        log_exists = log_path in after_paths
        add_check(
            checks,
            "task_log",
            log_path,
            log_exists,
            "Task log exists." if log_exists else "Task log is missing.",
        )
        log_text = read_text_file(after_dir, log_path) if log_exists else ""
        for needle in ensure_list(
            task_mapping.get("required_strings", []), "task_log.required_strings"
        ):
            if not isinstance(needle, str):
                raise DiffSentinelError("Task log required strings must be strings")
            target = f"{log_path} contains {needle!r}"
            add_check(
                checks,
                "task_log",
                target,
                needle in log_text,
                "Task log string found."
                if needle in log_text
                else "Task log string missing.",
                expected=needle,
            )

    json_assertions = ensure_mapping(
        expectations.get("json_assertions", {}), "json_assertions"
    )
    for raw_path in sorted(json_assertions):
        path = normalize_path(raw_path)
        rules = ensure_list(json_assertions[raw_path], f"json_assertions.{path}")
        before_json = load_json_file(before_dir, path)
        after_json = load_json_file(after_dir, path)
        for index, rule in enumerate(rules):
            if not isinstance(rule, dict):
                raise DiffSentinelError(
                    f"JSON assertion for {path} at index {index} must be a mapping"
                )
            json_path = rule.get("path")
            if not isinstance(json_path, str):
                raise DiffSentinelError(
                    f"JSON assertion for {path} at index {index} needs string path"
                )
            before_value = get_json_path(before_json, json_path)
            after_value = get_json_path(after_json, json_path)
            failures: List[str] = []

            if "exists" in rule:
                expected_exists = bool(rule["exists"])
                actual_exists = after_value is not MISSING
                if actual_exists != expected_exists:
                    failures.append(
                        f"exists expected {expected_exists}, got {actual_exists}"
                    )
            if "equals" in rule and after_value != rule["equals"]:
                failures.append(
                    f"after value expected {rule['equals']!r}, got {json_value_for_report(after_value)!r}"
                )
            if "not_equals" in rule and after_value == rule["not_equals"]:
                failures.append(f"after value unexpectedly equals {rule['not_equals']!r}")
            if "before_equals" in rule and before_value != rule["before_equals"]:
                failures.append(
                    f"before value expected {rule['before_equals']!r}, got {json_value_for_report(before_value)!r}"
                )
            if rule.get("added") is True:
                if before_value is not MISSING or after_value is MISSING:
                    failures.append("path was not added")
            if rule.get("removed") is True:
                if before_value is MISSING or after_value is not MISSING:
                    failures.append("path was not removed")

            target = f"{path}:{json_path}"
            add_check(
                checks,
                "json_assertions",
                target,
                not failures,
                "JSON assertion passed." if not failures else "; ".join(failures),
                observed={
                    "before": json_value_for_report(before_value),
                    "after": json_value_for_report(after_value),
                },
                expected={key: value for key, value in rule.items() if key != "path"},
            )

    passed = sum(1 for check in checks if check["status"] == "pass")
    failed = sum(1 for check in checks if check["status"] == "fail")
    max_score = len(checks)
    score = round(passed / max_score, 4) if max_score else 1.0
    report_pass = failed == 0 and score >= threshold

    return {
        "pass": report_pass,
        "score": score,
        "earned_points": passed,
        "max_score": max_score,
        "summary": {
            "passed": passed,
            "failed": failed,
            "warnings": len(warnings),
        },
        "checks": checks,
        "warnings": warnings,
        "metadata": {
            "schema_version": "1.0",
            "threshold": threshold,
            "created_count": len(created),
            "deleted_count": len(deleted),
            "modified_count": len(modified),
            "unchanged_count": len(unchanged),
        },
    }


def sample_expectations() -> Dict[str, Any]:
    """Return built-in sample expectations used by self-test."""

    return {
        "required_files": ["report.md"],
        "created_files": ["report.md", "logs/task.log"],
        "deleted_files": ["draft.txt"],
        "modified_files": ["data.json"],
        "forbidden_changes": ["notes.md"],
        "content_contains": {
            "report.md": ["Summary: Work completed.", "[source:A]"],
        },
        "task_log": {
            "file": "logs/task.log",
            "required_strings": ["updated report.md", "set data.json status"],
        },
        "json_assertions": {
            "data.json": [
                {
                    "path": "status",
                    "before_equals": "draft",
                    "equals": "complete",
                },
                {
                    "path": "citations.0",
                    "added": True,
                    "equals": "source:A",
                },
            ]
        },
    }


def write_sample_workspace(root: Path) -> Tuple[Path, Path]:
    """Create deterministic before-and-after sample directories."""

    before = root / "before"
    after = root / "after"
    before.mkdir(parents=True)
    (before / "data.json").write_text(
        json.dumps(
            {"status": "draft", "citations": [], "owner": "agent-benchmark"},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (before / "draft.txt").write_text("obsolete note\n", encoding="utf-8")
    (before / "notes.md").write_text("Unchanged baseline\n", encoding="utf-8")

    shutil.copytree(before, after)
    (after / "data.json").write_text(
        json.dumps(
            {
                "status": "complete",
                "citations": ["source:A"],
                "owner": "agent-benchmark",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (after / "draft.txt").unlink()
    (after / "report.md").write_text(
        "# Final Report\n\nSummary: Work completed.\n\nCitation: [source:A]\n",
        encoding="utf-8",
    )
    (after / "logs").mkdir()
    (after / "logs" / "task.log").write_text(
        "updated report.md\nset data.json status\ndeleted draft.txt\n",
        encoding="utf-8",
    )
    return before, after


def run_selftest() -> Dict[str, Any]:
    """Run the built-in sample and return its grading report."""

    with tempfile.TemporaryDirectory(prefix="diffsentinel-") as temp:
        before, after = write_sample_workspace(Path(temp))
        return grade_state_change(before, after, sample_expectations(), threshold=1.0)


def parse_threshold(value: str | None) -> float:
    """Parse and validate the score threshold."""

    if value is None or value == "":
        return 1.0
    try:
        threshold = float(value)
    except ValueError as exc:
        raise DiffSentinelError(f"Invalid threshold value: {value!r}") from exc
    if threshold < 0.0 or threshold > 1.0:
        raise DiffSentinelError("Threshold must be between 0.0 and 1.0")
    return threshold


def render_json(report: Mapping[str, Any]) -> str:
    """Render a report as deterministic pretty JSON."""

    return json.dumps(report, indent=2, ensure_ascii=True) + "\n"


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description=(
            "DiffSentinel grades observable before-and-after workspace state changes."
        )
    )
    parser.add_argument("--before", help="Directory snapshot before the agent ran")
    parser.add_argument("--after", help="Directory snapshot after the agent ran")
    parser.add_argument(
        "--expect",
        help=(
            "Expectation YAML or JSON file. Defaults to DIFFSENTINEL_EXPECTATIONS."
        ),
    )
    parser.add_argument(
        "--output",
        help="Optional report output path. Defaults to DIFFSENTINEL_OUTPUT.",
    )
    parser.add_argument(
        "--threshold",
        help=(
            "Minimum score needed to pass. Defaults to DIFFSENTINEL_SCORE_THRESHOLD or 1.0."
        ),
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run built-in sample data with no API key and print the report",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    """Run the CLI and return a CI-friendly exit code."""

    args = build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        env_threshold = os.environ.get("DIFFSENTINEL_SCORE_THRESHOLD")
        threshold = parse_threshold(args.threshold or env_threshold)

        if args.selftest or not any([args.before, args.after, args.expect]):
            report = run_selftest()
        else:
            before = Path(args.before) if args.before else None
            after = Path(args.after) if args.after else None
            expect_value = args.expect or os.environ.get("DIFFSENTINEL_EXPECTATIONS")
            if before is None or after is None or not expect_value:
                raise DiffSentinelError(
                    "Provide --before, --after, and --expect, or run --selftest"
                )
            expectations = load_expectations(Path(expect_value))
            report = grade_state_change(
                before,
                after,
                expectations,
                threshold=threshold,
            )

        output_text = render_json(report)
        output_path = args.output or os.environ.get("DIFFSENTINEL_OUTPUT")
        if output_path:
            Path(output_path).write_text(output_text, encoding="utf-8")
        sys.stdout.write(output_text)
        return 0 if report["pass"] else 1
    except DiffSentinelError as exc:
        sys.stderr.write(f"diffsentinel error: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
