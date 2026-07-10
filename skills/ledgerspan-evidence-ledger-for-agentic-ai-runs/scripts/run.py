#!/usr/bin/env python3
"""LedgerSpan evidence ledger CLI.

This module builds a portable evidence package for an agentic AI run by
comparing before/after workspace snapshots, ingesting command logs and tool
traces, hashing declared artifacts, and evaluating a small verification
checklist. It intentionally uses only the Python standard library so the skill
can run in isolated benchmark or CI environments.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


LEDGER_VERSION = "0.1.0"


def sha256_text(text: str) -> str:
    """Return the SHA-256 digest for UTF-8 text."""

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest for a file read in binary chunks."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_relative_path(value: str) -> str:
    """Normalize a <internal> path and reject absolute or parent paths."""

    if not isinstance(value, str) or not value.strip():
        raise ValueError("Path values must be non-empty strings.")

    value = value.replace("\\", "/")
    posix = PurePosixPath(value)
    if posix.is_absolute():
        raise ValueError(f"Snapshot path must be <internal>: {value}")

    parts = [part for part in posix.parts if part not in ("", ".")]
    if any(part == ".." for part in parts):
        raise ValueError(f"Snapshot path may not contain parent traversal: {value}")
    return "/".join(parts) if parts else "."


def snapshot_directory(root: Path) -> Dict[str, Any]:
    """Create a deterministic file snapshot for a workspace directory."""

    if not root.exists():
        raise ValueError(f"Workspace directory does not exist: {root}")
    if not root.is_dir():
        raise ValueError(f"Workspace path is not a directory: {root}")

    files: List[Dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel.startswith(".git/"):
            continue
        stat = path.stat()
        files.append(
            {
                "path": normalize_relative_path(rel),
                "size": stat.st_size,
                "mtime": int(stat.st_mtime),
                "sha256": sha256_file(path),
            }
        )

    return {"workspace": ".", "files": files}


def load_json_records(path: Path, label: str) -> List[Dict[str, Any]]:
    """Load records from a JSON array, JSON object with records, or JSONL file."""

    if not path.exists():
        raise ValueError(f"{label} file does not exist: {path}")

    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            records = parsed
        elif isinstance(parsed, dict):
            for key in ("records", "entries", "commands", "tool_calls", "files"):
                if key in parsed and isinstance(parsed[key], list):
                    records = parsed[key]
                    break
            else:
                records = [parsed]
        else:
            raise ValueError(f"{label} JSON must be an object or array.")
    except json.JSONDecodeError:
        records = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{label} JSONL parse error on line {line_number}: {exc}") from exc
            records.append(item)

    if not all(isinstance(item, dict) for item in records):
        raise ValueError(f"{label} records must be JSON objects.")
    return list(records)


def load_snapshot(path: Path) -> List[Dict[str, Any]]:
    """Load and normalize a snapshot from JSON."""

    records = load_json_records(path, "snapshot")
    normalized = []
    for record in records:
        if "path" not in record:
            raise ValueError(f"Snapshot record missing required field 'path': {record}")
        normalized.append(normalize_file_record(record))
    return sorted(normalized, key=lambda item: item["path"])


def normalize_file_record(record: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a normalized file metadata record."""

    path = normalize_relative_path(str(record["path"]))
    size = int(record.get("size", 0))
    mtime = int(record.get("mtime", 0))
    sha256 = str(record.get("sha256", "")).lower()
    if sha256 and (len(sha256) != 64 or any(char not in "0123456789abcdef" for char in sha256)):
        raise ValueError(f"Invalid sha256 for {path}: expected 64 lowercase hex characters.")
    return {"path": path, "size": size, "mtime": mtime, "sha256": sha256}


def index_files(files: Iterable[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Index normalized file records by path."""

    indexed: Dict[str, Dict[str, Any]] = {}
    for record in files:
        normalized = normalize_file_record(record)
        indexed[normalized["path"]] = normalized
    return indexed


def classify_changes(
    before_files: Sequence[Mapping[str, Any]],
    after_files: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    """Classify created, modified, deleted, renamed, and unchanged files."""

    before = index_files(before_files)
    after = index_files(after_files)

    created_paths = sorted(set(after) - set(before))
    deleted_paths = sorted(set(before) - set(after))
    common_paths = sorted(set(before) & set(after))

    renamed: List[Dict[str, Any]] = []
    remaining_created = set(created_paths)
    remaining_deleted = set(deleted_paths)

    created_by_hash: Dict[Tuple[str, int], List[str]] = {}
    for path in created_paths:
        record = after[path]
        key = (record["sha256"], record["size"])
        if record["sha256"]:
            created_by_hash.setdefault(key, []).append(path)

    for deleted_path in deleted_paths:
        deleted_record = before[deleted_path]
        key = (deleted_record["sha256"], deleted_record["size"])
        candidates = created_by_hash.get(key, [])
        if not candidates:
            continue
        new_path = candidates.pop(0)
        renamed.append(
            {
                "from": deleted_path,
                "to": new_path,
                "size": deleted_record["size"],
                "sha256": deleted_record["sha256"],
            }
        )
        remaining_deleted.discard(deleted_path)
        remaining_created.discard(new_path)

    modified = []
    unchanged_count = 0
    for path in common_paths:
        before_record = before[path]
        after_record = after[path]
        if before_record["sha256"] == after_record["sha256"] and before_record["size"] == after_record["size"]:
            unchanged_count += 1
            continue
        modified.append(
            {
                "path": path,
                "before": {
                    "size": before_record["size"],
                    "mtime": before_record["mtime"],
                    "sha256": before_record["sha256"],
                },
                "after": {
                    "size": after_record["size"],
                    "mtime": after_record["mtime"],
                    "sha256": after_record["sha256"],
                },
            }
        )

    return {
        "created": [after[path] for path in sorted(remaining_created)],
        "modified": modified,
        "deleted": [before[path] for path in sorted(remaining_deleted)],
        "renamed": sorted(renamed, key=lambda item: (item["from"], item["to"])),
        "unchanged_count": unchanged_count,
    }


def normalize_command_log(records: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Normalize command log records and compute summary counts."""

    entries: List[Dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        command = str(record.get("command", "")).strip()
        if not command:
            raise ValueError(f"Command record {index} missing required field 'command'.")
        cwd = normalize_relative_path(str(record.get("cwd", ".")))
        entry = {
            "command": command,
            "exit_code": int(record.get("exit_code", 0)),
            "duration_ms": int(record.get("duration_ms", 0)),
            "cwd": cwd,
            "stdout_ref": normalize_relative_path(str(record.get("stdout_ref", "")))
            if record.get("stdout_ref")
            else "",
            "stderr_ref": normalize_relative_path(str(record.get("stderr_ref", "")))
            if record.get("stderr_ref")
            else "",
        }
        entries.append(entry)

    total_duration = sum(item["duration_ms"] for item in entries)
    failed = sum(1 for item in entries if item["exit_code"] != 0)
    summary = {
        "total": len(entries),
        "succeeded": len(entries) - failed,
        "failed": failed,
        "duration_ms": total_duration,
    }
    return {"summary": summary, "entries": entries}


def infer_tool_kind(record: Mapping[str, Any]) -> str:
    """Infer a stable tool-call kind from common trace fields."""

    explicit = str(record.get("kind", "")).strip().lower()
    allowed = {"api_call", "file_operation", "search", "database_mutation", "external_resource", "other"}
    if explicit in allowed:
        return explicit

    combined = " ".join(str(record.get(key, "")).lower() for key in ("tool", "action", "operation", "resource"))
    if any(token in combined for token in ("search", "grep", "query")):
        return "search"
    if any(token in combined for token in ("write", "read", "edit", "delete", "file")):
        return "file_operation"
    if any(token in combined for token in ("insert", "update", "database", "sql", "postgres")):
        return "database_mutation"
    if any(token in combined for token in ("http", "api", "request")):
        return "api_call"
    if any(token in combined for token in ("url", "site", "resource")):
        return "external_resource"
    return "other"


def normalize_tool_traces(records: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Normalize JSON tool-call traces and summarize touched resources."""

    entries: List[Dict[str, Any]] = []
    by_kind: Dict[str, int] = {}
    resources = set()

    for index, record in enumerate(records, start=1):
        kind = infer_tool_kind(record)
        tool = str(record.get("tool", record.get("name", "unknown"))).strip() or "unknown"
        action = str(record.get("action", record.get("operation", ""))).strip()
        resource = str(record.get("resource", record.get("target", ""))).strip()
        status = str(record.get("status", "ok")).strip() or "ok"
        entry = {
            "id": str(record.get("id", f"tool-{index:03d}")),
            "kind": kind,
            "tool": tool,
            "action": action,
            "resource": resource,
            "status": status,
        }
        entries.append(entry)
        by_kind[kind] = by_kind.get(kind, 0) + 1
        if resource:
            resources.add(resource)

    return {
        "summary": {
            "total": len(entries),
            "by_kind": {key: by_kind[key] for key in sorted(by_kind)},
            "resources_touched": sorted(resources),
        },
        "entries": entries,
    }


def load_checklist(path: Optional[Path]) -> Dict[str, Any]:
    """Load a verification checklist, returning an empty checklist when omitted."""

    if path is None:
        return {"required_files": [], "artifacts": [], "assertions": []}
    records = load_json_records(path, "checklist")
    if len(records) != 1:
        raise ValueError("Checklist must be a single JSON object.")
    checklist = records[0]
    return {
        "required_files": list(checklist.get("required_files", [])),
        "artifacts": list(checklist.get("artifacts", [])),
        "assertions": list(checklist.get("assertions", [])),
    }


def build_artifacts(after_files: Sequence[Mapping[str, Any]], checklist: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Build artifact hash records from checklist artifact paths."""

    after = index_files(after_files)
    artifacts: List[Dict[str, Any]] = []
    for raw_path in checklist.get("artifacts", []):
        path = normalize_relative_path(str(raw_path))
        record = after.get(path)
        if record:
            artifacts.append(
                {
                    "path": path,
                    "status": "present",
                    "size": record["size"],
                    "sha256": record["sha256"],
                }
            )
        else:
            artifacts.append({"path": path, "status": "missing", "size": 0, "sha256": ""})
    return sorted(artifacts, key=lambda item: item["path"])


def check_command_contains(commands: Sequence[Mapping[str, Any]], needle: str) -> List[Mapping[str, Any]]:
    """Return command entries containing a case-sensitive substring."""

    return [command for command in commands if needle in str(command.get("command", ""))]


def evaluate_assertion(
    assertion: Mapping[str, Any],
    changes: Mapping[str, Any],
    after_files: Sequence[Mapping[str, Any]],
    commands: Mapping[str, Any],
    tools: Mapping[str, Any],
    artifacts: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    """Evaluate one verification assertion against collected evidence."""

    kind = str(assertion.get("type", "")).strip()
    name = str(assertion.get("name", kind or "unnamed assertion"))
    path = normalize_relative_path(str(assertion.get("path", "."))) if assertion.get("path") else ""
    command_contains = str(assertion.get("command_contains", ""))
    tool_kind = str(assertion.get("kind", ""))

    created_paths = {item["path"] for item in changes.get("created", [])}
    modified_paths = {item["path"] for item in changes.get("modified", [])}
    deleted_paths = {item["path"] for item in changes.get("deleted", [])}
    after_paths = {item["path"] for item in after_files}
    artifact_map = {item["path"]: item for item in artifacts}

    passed = False
    evidence = ""

    if kind == "file_exists":
        passed = path in after_paths
        evidence = path
    elif kind == "file_created":
        passed = path in created_paths
        evidence = path
    elif kind == "file_modified":
        passed = path in modified_paths
        evidence = path
    elif kind == "file_deleted":
        passed = path in deleted_paths
        evidence = path
    elif kind == "command_seen":
        matches = check_command_contains(commands.get("entries", []), command_contains)
        passed = bool(matches)
        evidence = matches[0]["command"] if matches else command_contains
    elif kind == "command_exit_zero":
        matches = check_command_contains(commands.get("entries", []), command_contains)
        passed = any(int(item.get("exit_code", 1)) == 0 for item in matches)
        evidence = matches[0]["command"] if matches else command_contains
    elif kind == "tool_kind_seen":
        passed = tool_kind in tools.get("summary", {}).get("by_kind", {})
        evidence = tool_kind
    elif kind == "artifact_hashed":
        artifact = artifact_map.get(path)
        passed = bool(artifact and artifact.get("status") == "present" and artifact.get("sha256"))
        evidence = path
    else:
        evidence = f"Unsupported assertion type: {kind}"

    return {
        "name": name,
        "type": kind,
        "status": "pass" if passed else "fail",
        "evidence": evidence,
    }


def evaluate_checklist(
    checklist: Mapping[str, Any],
    changes: Mapping[str, Any],
    after_files: Sequence[Mapping[str, Any]],
    commands: Mapping[str, Any],
    tools: Mapping[str, Any],
    artifacts: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    """Evaluate required files and explicit assertions into pass/fail checks."""

    checks: List[Dict[str, Any]] = []
    after_paths = {item["path"] for item in after_files}

    for raw_path in checklist.get("required_files", []):
        path = normalize_relative_path(str(raw_path))
        checks.append(
            {
                "name": f"required file exists: {path}",
                "type": "required_file",
                "status": "pass" if path in after_paths else "fail",
                "evidence": path,
            }
        )

    for assertion in checklist.get("assertions", []):
        if not isinstance(assertion, dict):
            raise ValueError("Checklist assertions must be JSON objects.")
        checks.append(evaluate_assertion(assertion, changes, after_files, commands, tools, artifacts))

    failed = sum(1 for check in checks if check["status"] != "pass")
    return {
        "status": "pass" if failed == 0 else "fail",
        "passed": len(checks) - failed,
        "failed": failed,
        "checks": checks,
    }


def create_evidence_ledger(
    before_files: Sequence[Mapping[str, Any]],
    after_files: Sequence[Mapping[str, Any]],
    command_records: Optional[Sequence[Mapping[str, Any]]] = None,
    tool_records: Optional[Sequence[Mapping[str, Any]]] = None,
    checklist: Optional[Mapping[str, Any]] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a complete LedgerSpan evidence package dictionary."""

    normalized_before = [normalize_file_record(record) for record in before_files]
    normalized_after = [normalize_file_record(record) for record in after_files]
    command_records = command_records or []
    tool_records = tool_records or []
    checklist = checklist or {"required_files": [], "artifacts": [], "assertions": []}
    metadata = metadata or {}

    changes = classify_changes(normalized_before, normalized_after)
    commands = normalize_command_log(command_records)
    tools = normalize_tool_traces(tool_records)
    artifacts = build_artifacts(normalized_after, checklist)
    verification = evaluate_checklist(checklist, changes, normalized_after, commands, tools, artifacts)

    return {
        "ledger_version": LEDGER_VERSION,
        "run": {
            "id": str(metadata.get("run_id") or os.environ.get("LEDGERSPAN_RUN_ID") or "local-run"),
            "actor": str(metadata.get("actor") or os.environ.get("LEDGERSPAN_ACTOR") or "unknown-agent"),
            "source": "ledgerspan",
        },
        "workspace": {
            "before_file_count": len(normalized_before),
            "after_file_count": len(normalized_after),
        },
        "changes": changes,
        "commands": commands,
        "tool_calls": tools,
        "artifacts": artifacts,
        "verification": verification,
    }


def render_markdown(ledger: Mapping[str, Any]) -> str:
    """Render an evidence package as compact Markdown."""

    lines = [
        "# LedgerSpan Evidence Ledger",
        "",
        f"- Ledger version: {ledger['ledger_version']}",
        f"- Run ID: {ledger['run']['id']}",
        f"- Actor: {ledger['run']['actor']}",
        f"- Verification: {ledger['verification']['status']}",
        "",
        "## Workspace",
        "",
        f"- Before files: {ledger['workspace']['before_file_count']}",
        f"- After files: {ledger['workspace']['after_file_count']}",
        "",
        "## Changes",
        "",
    ]

    changes = ledger["changes"]
    lines.extend(
        [
            f"- Created: {len(changes['created'])}",
            f"- Modified: {len(changes['modified'])}",
            f"- Deleted: {len(changes['deleted'])}",
            f"- Renamed: {len(changes['renamed'])}",
            f"- Unchanged: {changes['unchanged_count']}",
            "",
        ]
    )

    for heading, key in (("Created", "created"), ("Modified", "modified"), ("Deleted", "deleted")):
        if changes[key]:
            lines.append(f"### {heading}")
            for item in changes[key]:
                lines.append(f"- {item['path']}")
            lines.append("")

    if changes["renamed"]:
        lines.append("### Renamed")
        for item in changes["renamed"]:
            lines.append(f"- {item['from']} -> {item['to']}")
        lines.append("")

    lines.extend(
        [
            "## Commands",
            "",
            f"- Total: {ledger['commands']['summary']['total']}",
            f"- Succeeded: {ledger['commands']['summary']['succeeded']}",
            f"- Failed: {ledger['commands']['summary']['failed']}",
            "",
        ]
    )
    for command in ledger["commands"]["entries"]:
        lines.append(f"- `{command['command']}` exit={command['exit_code']} duration_ms={command['duration_ms']}")
    if ledger["commands"]["entries"]:
        lines.append("")

    lines.extend(["## Tool Calls", ""])
    for kind, count in ledger["tool_calls"]["summary"]["by_kind"].items():
        lines.append(f"- {kind}: {count}")
    if ledger["tool_calls"]["summary"]["resources_touched"]:
        lines.append("- Resources touched:")
        for resource in ledger["tool_calls"]["summary"]["resources_touched"]:
            lines.append(f"  - {resource}")
    lines.append("")

    lines.extend(["## Artifacts", ""])
    if ledger["artifacts"]:
        for artifact in ledger["artifacts"]:
            lines.append(f"- {artifact['path']} status={artifact['status']} sha256={artifact['sha256']}")
    else:
        lines.append("- none declared")
    lines.append("")

    lines.extend(["## Verification", ""])
    for check in ledger["verification"]["checks"]:
        lines.append(f"- {check['status']}: {check['name']} ({check['evidence']})")
    if not ledger["verification"]["checks"]:
        lines.append("- no checks declared")
    lines.append("")
    return "\n".join(lines)


def sample_before_files() -> List[Dict[str, Any]]:
    """Return deterministic built-in before snapshot records."""

    return [
        {"path": "README.md", "size": 18, "mtime": 1700000000, "sha256": sha256_text("LedgerSpan sample\n")},
        {"path": "data/input.csv", "size": 17, "mtime": 1700000000, "sha256": sha256_text("id,value\n1,alpha\n")},
        {"path": "notes/draft.txt", "size": 19, "mtime": 1700000000, "sha256": sha256_text("temporary notes\nv1\n")},
        {"path": "src/agent.py", "size": 23, "mtime": 1700000000, "sha256": sha256_text("print('old agent run')\n")},
    ]


def sample_after_files() -> List[Dict[str, Any]]:
    """Return deterministic built-in after snapshot records."""

    return [
        {"path": "README.md", "size": 18, "mtime": 1700000000, "sha256": sha256_text("LedgerSpan sample\n")},
        {"path": "data/source.csv", "size": 17, "mtime": 1700000100, "sha256": sha256_text("id,value\n1,alpha\n")},
        {"path": "docs/evidence.md", "size": 26, "mtime": 1700000100, "sha256": sha256_text("# Evidence\n\nTests passed.\n")},
        {"path": "src/agent.py", "size": 23, "mtime": 1700000100, "sha256": sha256_text("print('new agent run')\n")},
    ]


def sample_commands() -> List[Dict[str, Any]]:
    """Return deterministic built-in command log records."""

    return [
        {
            "command": "python -m pytest",
            "exit_code": 0,
            "duration_ms": 1240,
            "cwd": ".",
            "stdout_ref": "logs/pytest.stdout.txt",
            "stderr_ref": "logs/pytest.stderr.txt",
        }
    ]


def sample_tool_traces() -> List[Dict[str, Any]]:
    """Return deterministic built-in tool trace records."""

    return [
        {
            "id": "tool-001",
            "kind": "search",
            "tool": "local_search",
            "action": "query",
            "resource": "README.md",
            "status": "ok",
        },
        {
            "id": "tool-002",
            "kind": "file_operation",
            "tool": "editor",
            "action": "write",
            "resource": "docs/evidence.md",
            "status": "ok",
        },
        {
            "id": "tool-003",
            "kind": "api_call",
            "tool": "mock_llm",
            "action": "complete",
            "resource": "local/mock-model",
            "status": "ok",
        },
    ]


def sample_checklist() -> Dict[str, Any]:
    """Return deterministic built-in verification checklist records."""

    return {
        "required_files": ["docs/evidence.md", "src/agent.py"],
        "artifacts": ["docs/evidence.md"],
        "assertions": [
            {"name": "evidence document created", "type": "file_created", "path": "docs/evidence.md"},
            {"name": "agent source changed", "type": "file_modified", "path": "src/agent.py"},
            {"name": "draft notes removed", "type": "file_deleted", "path": "notes/draft.txt"},
            {
                "name": "test command passed",
                "type": "command_exit_zero",
                "command_contains": "pytest",
            },
            {"name": "search trace recorded", "type": "tool_kind_seen", "kind": "search"},
            {"name": "artifact hash recorded", "type": "artifact_hashed", "path": "docs/evidence.md"},
        ],
    }


def build_sample_ledger() -> Dict[str, Any]:
    """Build the deterministic self-test ledger."""

    return create_evidence_ledger(
        sample_before_files(),
        sample_after_files(),
        sample_commands(),
        sample_tool_traces(),
        sample_checklist(),
        {"run_id": "sample-run-001", "actor": "sample-agent"},
    )


def run_selftest() -> Dict[str, Any]:
    """Run minimal assertions over the built-in sample and return its ledger."""

    ledger = build_sample_ledger()
    changes = ledger["changes"]
    verification = ledger["verification"]
    assert len(changes["created"]) == 1
    assert len(changes["modified"]) == 1
    assert len(changes["deleted"]) == 1
    assert len(changes["renamed"]) == 1
    assert verification["status"] == "pass"
    assert ledger["commands"]["summary"]["failed"] == 0
    return ledger


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Build a durable evidence ledger for an agentic AI run.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--before", type=Path, help="Before snapshot JSON file.")
    parser.add_argument("--after", type=Path, help="After snapshot JSON file.")
    parser.add_argument("--<internal>", type=Path, help="Before workspace directory to snapshot.")
    parser.add_argument("--<internal>", type=Path, help="After workspace directory to snapshot.")
    parser.add_argument("--commands", type=Path, help="Command log JSON or JSONL file.")
    parser.add_argument("--tools", type=Path, help="Tool-call trace JSON or JSONL file.")
    parser.add_argument("--checklist", type=Path, help="Verification checklist JSON file.")
    parser.add_argument("--format", choices=("json", "markdown"), default="json", help="Output format.")
    parser.add_argument("--output", type=Path, help="Write output to this file instead of stdout.")
    parser.add_argument("--snapshot", type=Path, help="Create a snapshot JSON for one workspace directory and exit.")
    parser.add_argument("--selftest", action="store_true", help="Run the built-in deterministic sample.")
    return parser.parse_args(argv)


def load_files_from_args(args: argparse.Namespace) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Resolve before and after file records from CLI arguments."""

    if args.before and args.after:
        return load_snapshot(args.before), load_snapshot(args.after)
    if args.workspace_before and args.workspace_after:
        before_snapshot = snapshot_directory(args.workspace_before)
        after_snapshot = snapshot_directory(args.workspace_after)
        return before_snapshot["files"], after_snapshot["files"]
    raise ValueError("Provide --before and --after snapshots, --<internal> and --<internal>, or --selftest.")


def emit_output(text: str, output: Optional[Path]) -> None:
    """Write command output to stdout or an output file."""

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point."""

    raw_argv = list(sys.argv[1:] if argv is None else argv)
    args = parse_args(raw_argv)

    try:
        if args.snapshot:
            snapshot = snapshot_directory(args.snapshot)
            emit_output(json.dumps(snapshot, indent=2) + "\n", args.output)
            return 0

        if args.selftest or not raw_argv:
            ledger = run_selftest()
        else:
            before_files, after_files = load_files_from_args(args)
            commands = load_json_records(args.commands, "commands") if args.commands else []
            tools = load_json_records(args.tools, "tools") if args.tools else []
            checklist = load_checklist(args.checklist)
            ledger = create_evidence_ledger(before_files, after_files, commands, tools, checklist)

        if args.format == "markdown":
            rendered = render_markdown(ledger)
        else:
            rendered = json.dumps(ledger, indent=2) + "\n"
        emit_output(rendered, args.output)
        return 0
    except (OSError, ValueError, AssertionError) as exc:
        print(f"LedgerSpan error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
