"""StateLens reference CLI for transition-aware agent evaluation.

The CLI compares a before directory, an after directory, an expectation spec,
and an optional trace of evidence access. It emits a deterministic JSON report
that can be used by CI systems or local regression suites.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple


READ_ACTIONS = {"read", "open", "inspect", "evidence", "source_read", "file_read"}


class EvaluationError(Exception):
    """Raised when inputs or expectation specs cannot be evaluated."""


def hash_file(path: Path) -> str:
    """Return the SHA-256 hash for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_directory(root: Path) -> Dict[str, Dict[str, Any]]:
    """Return a deterministic file snapshot for a directory."""
    if not root.is_dir():
        raise EvaluationError(f"Directory not found: {root}")

    snapshot: Dict[str, Dict[str, Any]] = {}
    for file_path in sorted(path for path in root.rglob("*") if path.is_file()):
        rel_path = file_path.relative_to(root).as_posix()
        stat = file_path.stat()
        snapshot[rel_path] = {
            "sha256": hash_file(file_path),
            "size": stat.st_size,
        }
    return snapshot


def compare_snapshots(
    before: Mapping[str, Mapping[str, Any]],
    after: Mapping[str, Mapping[str, Any]],
) -> Dict[str, List[str]]:
    """Return added, deleted, modified, and unchanged relative paths."""
    before_paths = set(before)
    after_paths = set(after)
    common_paths = before_paths & after_paths
    modified = sorted(
        path for path in common_paths if before[path]["sha256"] != after[path]["sha256"]
    )
    unchanged = sorted(
        path for path in common_paths if before[path]["sha256"] == after[path]["sha256"]
    )
    return {
        "added": sorted(after_paths - before_paths),
        "deleted": sorted(before_paths - after_paths),
        "modified": modified,
        "unchanged": unchanged,
    }


def normalize_spec_path(value: Any) -> str:
    """Validate and normalize a relative path from a spec."""
    if not isinstance(value, str) or not value.strip():
        raise EvaluationError("Spec paths must be non-empty strings.")
    normalized = value.strip().replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts:
        raise EvaluationError(f"Spec path must be relative and stay inside the fixture: {value}")
    return path.as_posix()


def fixture_path(root: Path, rel_path: str) -> Path:
    """Return a platform path inside a fixture directory for a normalized path."""
    return root.joinpath(*rel_path.split("/"))


def read_text(path: Path, max_bytes: int = 500_000) -> Optional[str]:
    """Read UTF-8 text from a file, returning None for binary or very large files."""
    if not path.exists():
        return ""
    data = path.read_bytes()
    if len(data) > max_bytes:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def unified_diff_for_file(
    before_root: Path,
    after_root: Path,
    rel_path: str,
    max_lines: int,
) -> Dict[str, Any]:
    """Return a compact unified diff entry for a changed file."""
    before_text = read_text(fixture_path(before_root, rel_path))
    after_text = read_text(fixture_path(after_root, rel_path))
    if before_text is None or after_text is None:
        return {"path": rel_path, "binary": True, "diff": ""}

    diff_lines = list(
        difflib.unified_diff(
            before_text.splitlines(),
            after_text.splitlines(),
            fromfile=f"before/{rel_path}",
            tofile=f"after/{rel_path}",
            lineterm="",
        )
    )
    if len(diff_lines) > max_lines:
        omitted = len(diff_lines) - max_lines
        diff_lines = diff_lines[:max_lines] + [f"... ({omitted} diff lines omitted)"]
    return {"path": rel_path, "binary": False, "diff": "\n".join(diff_lines)}


def strip_yaml_comment(line: str) -> str:
    """Strip a YAML-style inline comment outside quotes."""
    quote: Optional[str] = None
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote:
            escaped = True
            continue
        if char in {"'", '"'}:
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
        if char == "#" and quote is None and (index == 0 or line[index - 1].isspace()):
            return line[:index].rstrip()
    return line.rstrip()


def split_yaml_key_value(text: str) -> Optional[Tuple[str, str]]:
    """Split a YAML key/value pair at the first unquoted colon."""
    quote: Optional[str] = None
    escaped = False
    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote:
            escaped = True
            continue
        if char in {"'", '"'}:
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
        if char == ":" and quote is None:
            key = text[:index].strip()
            value = text[index + 1 :].strip()
            if not key:
                return None
            return key, value
    return None


def parse_yaml_scalar(raw: str) -> Any:
    """Parse a scalar value from the supported YAML subset."""
    value = raw.strip()
    if value == "":
        return None
    if value in {"[]", "{}"}:
        return [] if value == "[]" else {}
    lower = value.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower in {"null", "none", "~"}:
        return None
    if (
        len(value) >= 2
        and value[0] == value[-1]
        and value[0] in {"'", '"'}
    ):
        inner = value[1:-1]
        return (
            inner.replace("\\n", "\n")
            .replace("\\t", "\t")
            .replace("\\'", "'")
            .replace('\\"', '"')
            .replace("\\\\", "\\")
        )
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def parse_simple_yaml(text: str) -> Any:
    """Parse a small YAML subset used by StateLens specs."""
    lines: List[Tuple[int, str]] = []
    for raw_line in text.splitlines():
        without_comment = strip_yaml_comment(raw_line)
        if not without_comment.strip():
            continue
        leading = without_comment[: len(without_comment) - len(without_comment.lstrip(" "))]
        if "\t" in leading:
            raise EvaluationError("YAML indentation must use spaces, not tabs.")
        lines.append((len(leading), without_comment.strip()))

    def parse_block(index: int, indent: int) -> Tuple[Any, int]:
        if index >= len(lines):
            return None, index
        actual_indent, content = lines[index]
        if actual_indent < indent:
            return None, index
        if content.startswith("- "):
            return parse_list(index, actual_indent)
        return parse_map(index, actual_indent)

    def parse_map(index: int, indent: int) -> Tuple[Dict[str, Any], int]:
        result: Dict[str, Any] = {}
        while index < len(lines):
            current_indent, content = lines[index]
            if current_indent < indent:
                break
            if current_indent > indent:
                raise EvaluationError(f"Unexpected YAML indentation near: {content}")
            if content.startswith("- "):
                break
            split = split_yaml_key_value(content)
            if split is None:
                raise EvaluationError(f"Expected YAML key/value pair near: {content}")
            key, raw_value = split
            if raw_value == "":
                next_index = index + 1
                if next_index < len(lines) and lines[next_index][0] > current_indent:
                    value, index = parse_block(next_index, lines[next_index][0])
                else:
                    value, index = None, next_index
            else:
                value = parse_yaml_scalar(raw_value)
                index += 1
            result[key] = value
        return result, index

    def parse_list(index: int, indent: int) -> Tuple[List[Any], int]:
        result: List[Any] = []
        while index < len(lines):
            current_indent, content = lines[index]
            if current_indent < indent:
                break
            if current_indent > indent:
                raise EvaluationError(f"Unexpected YAML indentation near: {content}")
            if not content.startswith("- "):
                break
            item_text = content[2:].strip()
            if item_text == "":
                next_index = index + 1
                if next_index < len(lines) and lines[next_index][0] > current_indent:
                    item, index = parse_block(next_index, lines[next_index][0])
                else:
                    item, index = None, next_index
            else:
                split = split_yaml_key_value(item_text)
                if split is None:
                    item = parse_yaml_scalar(item_text)
                    index += 1
                else:
                    key, raw_value = split
                    item = {}
                    if raw_value == "":
                        next_index = index + 1
                        if next_index < len(lines) and lines[next_index][0] > current_indent:
                            nested, index = parse_block(next_index, lines[next_index][0])
                        else:
                            nested, index = None, next_index
                        item[key] = nested
                    else:
                        item[key] = parse_yaml_scalar(raw_value)
                        index += 1
                    if index < len(lines) and lines[index][0] > current_indent:
                        extra, index = parse_map(index, lines[index][0])
                        item.update(extra)
            result.append(item)
        return result, index

    if not lines:
        return {}
    parsed, final_index = parse_block(0, lines[0][0])
    if final_index != len(lines):
        raise EvaluationError("Could not parse entire YAML document.")
    return parsed


def load_spec(path: Path) -> Dict[str, Any]:
    """Load a JSON or simple YAML expectation spec."""
    if not path.is_file():
        raise EvaluationError(f"Spec file not found: {path}")
    text = path.read_text(encoding="utf-8")
    try:
        if path.suffix.lower() == ".json" or text.lstrip().startswith(("{", "[")):
            data = json.loads(text)
        else:
            data = parse_simple_yaml(text)
    except json.JSONDecodeError as exc:
        raise EvaluationError(f"Invalid JSON spec: {exc}") from exc
    if not isinstance(data, dict):
        raise EvaluationError("Spec must be a JSON or YAML object.")
    return data


def as_list(value: Any, field_name: str) -> List[Any]:
    """Return a spec value as a list, accepting a single scalar for convenience."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, (str, int, float, bool)):
        return [value]
    raise EvaluationError(f"Spec field '{field_name}' must be a list or scalar.")


def spec_path_list(spec: Mapping[str, Any], field_name: str) -> List[str]:
    """Return a normalized list of paths from a spec field."""
    return [normalize_spec_path(item) for item in as_list(spec.get(field_name), field_name)]


def add_check(
    checks: List[Dict[str, Any]],
    name: str,
    passed: bool,
    details: str,
    path: Optional[str] = None,
    field: Optional[str] = None,
) -> None:
    """Append one deterministic check result to the report."""
    check: Dict[str, Any] = {"name": name, "pass": bool(passed)}
    if path is not None:
        check["path"] = path
    if field is not None:
        check["field"] = field
    check["details"] = details
    checks.append(check)


def get_json_path(document: Any, field_path: str) -> Tuple[bool, Any]:
    """Look up a dotted JSON path, including numeric list indexes."""
    current = document
    for part in field_path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            return False, None
    return True, current


def clean_trace_path(value: Any) -> Optional[str]:
    """Normalize a path-like value from a trace event for suffix matching."""
    if not isinstance(value, str) or not value.strip():
        return None
    cleaned = value.strip().replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned.lstrip("/")


def parse_trace_line(line: str) -> Optional[str]:
    """Parse one text trace line and return a read path if present."""
    stripped = line.strip()
    if not stripped:
        return None
    lowered = stripped.lower()
    for prefix in ("read ", "open ", "inspect ", "read:", "open:", "inspect:"):
        if lowered.startswith(prefix):
            return clean_trace_path(stripped[len(prefix) :].strip())
    return None


def load_trace_reads(path: Optional[Path]) -> Set[str]:
    """Load read/open/inspect paths from a JSON or text trace file."""
    if path is None:
        return set()
    if not path.is_file():
        raise EvaluationError(f"Trace file not found: {path}")
    text = path.read_text(encoding="utf-8")
    reads: Set[str] = set()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        for line in text.splitlines():
            parsed = parse_trace_line(line)
            if parsed:
                reads.add(parsed)
        return reads

    events: Iterable[Any]
    if isinstance(data, dict) and isinstance(data.get("events"), list):
        events = data["events"]
    elif isinstance(data, list):
        events = data
    else:
        events = []

    for event in events:
        if isinstance(event, str):
            parsed = parse_trace_line(event)
            if parsed:
                reads.add(parsed)
            continue
        if not isinstance(event, dict):
            continue
        action = str(
            event.get("action")
            or event.get("event")
            or event.get("op")
            or event.get("type")
            or ""
        ).lower()
        path_value = event.get("path") or event.get("file") or event.get("target")
        if (action in READ_ACTIONS or action.startswith("read")) and path_value:
            parsed = clean_trace_path(path_value)
            if parsed:
                reads.add(parsed)
    return reads


def evidence_was_read(read_paths: Set[str], required_path: str) -> bool:
    """Return true when a required relative path appears in the trace reads."""
    return required_path in read_paths or any(
        candidate.endswith(f"/{required_path}") for candidate in read_paths
    )


def changed_paths_from_diff(diff: Mapping[str, Sequence[str]]) -> Set[str]:
    """Return the set of all added, deleted, and modified paths."""
    return set(diff["added"]) | set(diff["deleted"]) | set(diff["modified"])


def evaluate_state_transition(
    before_dir: Path,
    after_dir: Path,
    spec: Mapping[str, Any],
    trace_path: Optional[Path] = None,
    max_diff_lines: int = 80,
) -> Dict[str, Any]:
    """Evaluate a before/after state transition against an expectation spec."""
    before_snapshot = snapshot_directory(before_dir)
    after_snapshot = snapshot_directory(after_dir)
    diff = compare_snapshots(before_snapshot, after_snapshot)
    changed_paths = changed_paths_from_diff(diff)
    read_paths = load_trace_reads(trace_path)

    file_diffs = [
        unified_diff_for_file(before_dir, after_dir, rel_path, max_diff_lines)
        for rel_path in sorted(changed_paths)
    ]

    checks: List[Dict[str, Any]] = []

    for rel_path in spec_path_list(spec, "required_paths_exist"):
        exists = rel_path in after_snapshot
        add_check(
            checks,
            "required_path_exists",
            exists,
            "exists in post-task directory" if exists else "missing from post-task directory",
            path=rel_path,
        )

    required_change_paths: Set[str] = set()
    for index, raw_entry in enumerate(as_list(spec.get("required_changes"), "required_changes")):
        if isinstance(raw_entry, str):
            entry: Dict[str, Any] = {"path": raw_entry}
        elif isinstance(raw_entry, dict):
            entry = dict(raw_entry)
        else:
            raise EvaluationError(f"required_changes[{index}] must be a string or object.")

        rel_path = normalize_spec_path(entry.get("path"))
        required_change_paths.add(rel_path)
        is_changed = rel_path in diff["added"] or rel_path in diff["modified"]
        add_check(
            checks,
            "required_change",
            is_changed,
            "file is added or modified" if is_changed else "file was not added or modified",
            path=rel_path,
        )

        text = read_text(fixture_path(after_dir, rel_path))
        contains_values = [str(item) for item in as_list(entry.get("contains"), "contains")]
        regex_values = [str(item) for item in as_list(entry.get("regex"), "regex")]
        for expected in contains_values:
            passed = text is not None and expected in text
            add_check(
                checks,
                "required_contains",
                passed,
                "found required string" if passed else f"missing required string: {expected}",
                path=rel_path,
            )
        for pattern in regex_values:
            try:
                compiled = re.compile(pattern, re.MULTILINE)
            except re.error as exc:
                raise EvaluationError(f"Invalid regex for {rel_path}: {exc}") from exc
            passed = text is not None and compiled.search(text) is not None
            add_check(
                checks,
                "required_regex",
                passed,
                "matched required regex" if passed else f"missing regex match: {pattern}",
                path=rel_path,
            )

    for index, raw_entry in enumerate(
        as_list(spec.get("structured_assertions"), "structured_assertions")
    ):
        if not isinstance(raw_entry, dict):
            raise EvaluationError(f"structured_assertions[{index}] must be an object.")
        rel_path = normalize_spec_path(raw_entry.get("path"))
        assertion_type = str(raw_entry.get("type", "json")).lower()
        if assertion_type != "json":
            raise EvaluationError(f"Unsupported structured assertion type: {assertion_type}")

        text = read_text(fixture_path(after_dir, rel_path))
        try:
            document = json.loads(text or "")
            parsed = True
        except json.JSONDecodeError:
            document = None
            parsed = False
        add_check(
            checks,
            "structured_json_parse",
            parsed,
            "valid JSON document" if parsed else "invalid JSON document",
            path=rel_path,
        )
        if not parsed:
            continue

        for field_name in [str(item) for item in as_list(raw_entry.get("exists"), "exists")]:
            found, _ = get_json_path(document, field_name)
            add_check(
                checks,
                "structured_json_exists",
                found,
                "JSON path exists" if found else "JSON path is missing",
                path=rel_path,
                field=field_name,
            )

        equals = raw_entry.get("equals") or {}
        if not isinstance(equals, dict):
            raise EvaluationError("structured_assertions[].equals must be an object.")
        for field_name in sorted(equals):
            found, actual = get_json_path(document, str(field_name))
            expected = equals[field_name]
            passed = found and actual == expected
            add_check(
                checks,
                "structured_json_equals",
                passed,
                "value matched expected JSON path"
                if passed
                else f"expected {expected!r}, got {actual!r}",
                path=rel_path,
                field=str(field_name),
            )

    for rel_path in spec_path_list(spec, "forbidden_changes"):
        before_meta = before_snapshot.get(rel_path)
        after_meta = after_snapshot.get(rel_path)
        unchanged = before_meta == after_meta
        add_check(
            checks,
            "forbidden_change",
            unchanged,
            "file unchanged" if unchanged else "file changed, appeared, or disappeared",
            path=rel_path,
        )

    for rel_path in spec_path_list(spec, "forbidden_deletions"):
        not_deleted = rel_path not in diff["deleted"]
        add_check(
            checks,
            "forbidden_deletion",
            not_deleted,
            "file was not deleted" if not_deleted else "file was deleted",
            path=rel_path,
        )

    for rel_path in spec_path_list(spec, "evidence_required"):
        was_read = evidence_was_read(read_paths, rel_path)
        add_check(
            checks,
            "evidence_read",
            was_read,
            "required evidence path was read" if was_read else "required evidence path was not read",
            path=rel_path,
        )

    allow_unlisted = bool(spec.get("allow_unlisted_changes", True))
    allowed_paths = set(spec_path_list(spec, "allowed_changes")) | required_change_paths
    unexpected_changes = sorted(changed_paths - allowed_paths)
    if not allow_unlisted:
        add_check(
            checks,
            "allowed_change_scope",
            not unexpected_changes,
            "all changed files are allowed"
            if not unexpected_changes
            else "unexpected changed files: " + ", ".join(unexpected_changes),
        )

    checks_passed = sum(1 for check in checks if check["pass"])
    checks_failed = len(checks) - checks_passed
    if checks_failed:
        confidence = "low"
    elif spec_path_list(spec, "evidence_required"):
        confidence = "high"
    else:
        confidence = "medium"

    report = {
        "task_id": str(spec.get("task_id") or "statelens-evaluation"),
        "pass": checks_failed == 0,
        "summary": {
            "confidence": confidence,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "files_added": len(diff["added"]),
            "files_deleted": len(diff["deleted"]),
            "files_modified": len(diff["modified"]),
            "unexpected_changes": len(unexpected_changes),
        },
        "checks": checks,
        "diffs": {
            "added": diff["added"],
            "deleted": diff["deleted"],
            "modified": diff["modified"],
            "file_diffs": file_diffs,
        },
    }
    return report


def write_sample_case(root: Path) -> Dict[str, Path]:
    """Create a deterministic before/after fixture, spec, and trace under root."""
    before = root / "before"
    after = root / "after"
    before_notes = before / "notes"
    after_notes = after / "notes"
    before_notes.mkdir(parents=True)
    after_notes.mkdir(parents=True)

    (before_notes / "source.md").write_text(
        "Source evidence: SQLite is approved for the prototype.\n"
        "Risk: keep scope small.\n",
        encoding="utf-8",
    )
    (after_notes / "source.md").write_text(
        "Source evidence: SQLite is approved for the prototype.\n"
        "Risk: keep scope small.\n",
        encoding="utf-8",
    )
    (before_notes / "summary.md").write_text(
        "Status: draft\n"
        "Decision: undecided.\n",
        encoding="utf-8",
    )
    (after_notes / "summary.md").write_text(
        "Status: approved\n"
        "Decision: keep SQLite for the prototype.\n",
        encoding="utf-8",
    )
    (before / "metadata.json").write_text(
        '{"owner":"agent","status":"draft"}\n',
        encoding="utf-8",
    )
    (after / "metadata.json").write_text(
        '{"owner":"agent","status":"approved"}\n',
        encoding="utf-8",
    )

    spec = root / "spec.yaml"
    spec.write_text(
        "\n".join(
            [
                "task_id: demo-note-update",
                "allow_unlisted_changes: false",
                "required_paths_exist:",
                "  - notes/summary.md",
                "required_changes:",
                "  - path: notes/summary.md",
                "    contains:",
                "      - 'Decision: keep SQLite for the prototype.'",
                "    regex:",
                "      - 'Status:\\s+approved'",
                "structured_assertions:",
                "  - path: metadata.json",
                "    type: json",
                "    equals:",
                "      owner: agent",
                "      status: approved",
                "forbidden_changes:",
                "  - notes/source.md",
                "evidence_required:",
                "  - notes/source.md",
                "allowed_changes:",
                "  - notes/summary.md",
                "  - metadata.json",
                "",
            ]
        ),
        encoding="utf-8",
    )
    trace = root / "trace.json"
    trace.write_text(
        json.dumps(
            {
                "events": [
                    {"action": "read", "path": "notes/source.md"},
                    {"action": "write", "path": "notes/summary.md"},
                    {"action": "write", "path": "metadata.json"},
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return {"before": before, "after": after, "spec": spec, "trace": trace}


def run_selftest(output_path: Optional[Path] = None) -> int:
    """Run the built-in deterministic sample and print or write the report."""
    with tempfile.TemporaryDirectory(prefix="statelens_") as temp_dir:
        paths = write_sample_case(Path(temp_dir))
        spec = load_spec(paths["spec"])
        report = evaluate_state_transition(
            paths["before"],
            paths["after"],
            spec,
            trace_path=paths["trace"],
        )
    rendered = json.dumps(report, indent=2) + "\n"
    if output_path:
        output_path.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0 if report["pass"] else 1


def env_int(name: str, default: int) -> int:
    """Read an integer environment variable with a deterministic fallback."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def build_parser() -> argparse.ArgumentParser:
    """Build the StateLens command-line parser."""
    parser = argparse.ArgumentParser(
        description="Evaluate an agent run by comparing before/after state transitions.",
    )
    parser.add_argument("--before", default=os.getenv("STATELENS_BEFORE"), help="Pre-task directory.")
    parser.add_argument("--after", default=os.getenv("STATELENS_AFTER"), help="Post-task directory.")
    parser.add_argument("--spec", default=os.getenv("STATELENS_SPEC"), help="JSON or YAML expectation spec.")
    parser.add_argument("--trace", default=os.getenv("STATELENS_TRACE"), help="Optional JSON or text trace file.")
    parser.add_argument("--output", default=os.getenv("STATELENS_OUTPUT"), help="Optional JSON report output path.")
    parser.add_argument(
        "--max-diff-lines",
        type=int,
        default=env_int("STATELENS_MAX_DIFF_LINES", 80),
        help="Maximum unified diff lines per changed file.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run the built-in sample with no API key or external service.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the command-line interface and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    no_input_args = args.before is None and args.after is None and args.spec is None
    if args.selftest or no_input_args:
        return run_selftest(Path(args.output) if args.output else None)

    missing = [
        name
        for name in ("before", "after", "spec")
        if getattr(args, name) is None
    ]
    if missing:
        parser.error("missing required arguments: " + ", ".join(f"--{name}" for name in missing))

    try:
        spec = load_spec(Path(args.spec))
        report = evaluate_state_transition(
            Path(args.before),
            Path(args.after),
            spec,
            trace_path=Path(args.trace) if args.trace else None,
            max_diff_lines=args.max_diff_lines,
        )
    except EvaluationError as exc:
        print(f"statelens: error: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
