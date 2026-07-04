#!/usr/bin/env python3
"""TraceLoom failure-recovery knowledge graph extractor.

This module provides a deterministic, standard-library CLI that converts messy
agent or automation traces into compact failure-recovery graph candidates.
It is intentionally offline; optional API keys are only read from environment
variables so external wrappers can detect whether richer summarization is
available without hardcoding secrets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


SAMPLE_TRACE = """[10:00] RUN $ python worker.py
[10:00] ERROR ModuleNotFoundError: No module named 'yaml'
[10:01] $ python -m pip install pyyaml
[10:02] CHECKPOINT resume from step parse-config
[10:02] $ python worker.py
[10:03] SUCCESS completed job
"""


FAILURE_RE = re.compile(
    r"\b(error|exception|traceback|failed|failure|exit code [1-9]\d*|nonzero|"
    r"module not found|no module named|cannot find module|permission denied|"
    r"timed out|timeout|connection refused|enoent|eacces|syntaxerror)\b",
    re.IGNORECASE,
)
SUCCESS_RE = re.compile(
    r"\b(success|succeeded|passed|completed|fixed|recovered|exit code 0|ok)\b",
    re.IGNORECASE,
)
CHECKPOINT_RE = re.compile(
    r"\b(checkpoint|resume|resumed|continuing from|restart from|retry from)\b",
    re.IGNORECASE,
)
RECOVERY_COMMAND_RE = re.compile(
    r"(^|\s)(python -m pip install|pip install|uv add|poetry add|npm install|"
    r"pnpm install|yarn add|brew install|apt(-get)? install|chmod|chown|mkdir|"
    r"touch|export|rm -rf|git clean|git checkout|git restore|retry|rerun)\b",
    re.IGNORECASE,
)
COMMAND_PATTERNS = [
    re.compile(r"^\s*(?:\[[^\]]+\]\s*)?(?:RUN|CMD|COMMAND|EXEC|RETRY)\s+\$?\s*(.+?)\s*$", re.IGNORECASE),
    re.compile(r"^\s*(?:\[[^\]]+\]\s*)?(?:\$|>)\s+(.+?)\s*$"),
    re.compile(r"^\s*\d+\s+(.+?)\s*$"),
    re.compile(r"\b(?:command|cmd|run|running|executing|exec)\s*[:=]\s*(.+?)\s*$", re.IGNORECASE),
]
FAILED_COMMAND_RE = re.compile(
    r"\bcommand\s+failed\s*[:=]\s*(.+?)(?:\s+(?:exit|status|with exit)\b|$)",
    re.IGNORECASE,
)
ERROR_SIGNATURE_RE = re.compile(
    r"([A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception):\s*.+)$"
)


def load_settings(env: Optional[Dict[str, str]] = None) -> Dict[str, bool]:
    """Return non-secret runtime settings derived from environment variables."""
    source = os.environ if env is None else env
    llm_key_available = bool(source.get("TRACELOOM_LLM_API_KEY") or source.get("OPENAI_API_KEY"))
    llm_requested = source.get("TRACELOOM_USE_LLM", "").strip().lower() in {"1", "true", "yes"}
    return {"llm_key_available": llm_key_available, "llm_requested": llm_requested}


def sanitize_text(value: Any) -> str:
    """Normalize text and redact obvious absolute paths for safer notes."""
    text = "" if value is None else str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"(?<![\w.-])/(?:[A-Za-z0-9._-]+/)+([A-Za-z0-9._-]+)", r"<path>/\1", text)
    return text


def stable_hash(*parts: Any, length: int = 12) -> str:
    """Create a stable lowercase hexadecimal hash for IDs."""
    payload = "\n".join(sanitize_text(part).lower() for part in parts)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:length]


def stable_id(prefix: str, *parts: Any, length: int = 12) -> str:
    """Create a stable graph identifier with a readable prefix."""
    return f"{prefix}-{stable_hash(*parts, length=length)}"


def command_fingerprint(command: Optional[str]) -> Optional[str]:
    """Return a normalized command fingerprint suitable for deduplication."""
    if not command:
        return None
    normalized = sanitize_text(command).lower()
    normalized = re.sub(r"(['\"]).*?\1", "<arg>", normalized)
    normalized = re.sub(r"\b\d+\b", "<num>", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized or None


def extract_command(line: str) -> Optional[str]:
    """Extract a shell command from a trace line when one is visible."""
    text = sanitize_text(line)
    failed_match = FAILED_COMMAND_RE.search(text)
    if failed_match:
        return sanitize_text(failed_match.group(1))
    for pattern in COMMAND_PATTERNS:
        match = pattern.search(text)
        if match:
            command = sanitize_text(match.group(1))
            command = re.sub(r"\s+(?:exit code|status)\s+\d+.*$", "", command, flags=re.IGNORECASE)
            return command or None
    return None


def record_to_line(record: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """Convert a JSONL record into a normalized trace line and command."""
    command = sanitize_text(record.get("command") or record.get("cmd") or "")
    status = record.get("status", record.get("exit_code", ""))
    fragments = []
    for key in ("event", "type", "level"):
        if record.get(key):
            fragments.append(str(record[key]))
    if command:
        fragments.append(f"command: {command}")
    for key in ("error", "message", "stderr", "stdout", "output"):
        if record.get(key):
            fragments.append(str(record[key]))
            break
    if status != "":
        fragments.append(f"status: {status}")
    line = sanitize_text(" ".join(fragments) or record)
    return line, command or extract_command(line)


def parse_trace(raw_text: str) -> List[Dict[str, Any]]:
    """Parse plain text, shell history, or JSONL into normalized events."""
    events: List[Dict[str, Any]] = []
    for line_no, raw_line in enumerate(raw_text.splitlines(), start=1):
        if not raw_line.strip():
            continue
        line = sanitize_text(raw_line)
        command = extract_command(line)
        try:
            parsed = json.loads(raw_line)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            line, command = record_to_line(parsed)
        events.append({"line_no": line_no, "line": line, "command": command})
    return events


def is_failure_event(line: str) -> bool:
    """Return True when a normalized trace line looks like a failure."""
    return bool(FAILURE_RE.search(line))


def is_success_event(line: str) -> bool:
    """Return True when a normalized trace line looks like a successful outcome."""
    return bool(SUCCESS_RE.search(line))


def is_checkpoint_event(line: str) -> bool:
    """Return True when a normalized trace line mentions a checkpoint or resume."""
    return bool(CHECKPOINT_RE.search(line))


def looks_like_recovery_command(command: Optional[str]) -> bool:
    """Return True when a command commonly repairs failed execution."""
    return bool(command and RECOVERY_COMMAND_RE.search(command))


def extract_error_signature(line: str) -> str:
    """Extract a compact, normalized error signature from a failure line."""
    text = sanitize_text(line)
    match = ERROR_SIGNATURE_RE.search(text)
    if match:
        return trim_signature(match.group(1))
    text = re.sub(r"^\[[^\]]+\]\s*", "", text)
    text = re.sub(r"^(error|failed|failure|exception)\s*[:=-]?\s*", "", text, flags=re.IGNORECASE)
    return trim_signature(text)


def trim_signature(signature: str, max_length: int = 160) -> str:
    """Trim long signatures while preserving deterministic output."""
    compact = sanitize_text(signature)
    compact = re.sub(r"\b0x[0-9a-fA-F]+\b", "0x<hex>", compact)
    compact = re.sub(r"\bline \d+\b", "line <num>", compact, flags=re.IGNORECASE)
    if len(compact) > max_length:
        return compact[: max_length - 3].rstrip() + "..."
    return compact


def signature_score(signature: str) -> int:
    """Score signatures so specific exception lines replace generic errors."""
    score = 0
    if re.search(r"(Error|Exception):", signature):
        score += 10
    if ":" in signature:
        score += 2
    score += min(len(signature), 80) // 20
    return score


def classify_cause(signature: str, evidence: Iterable[str]) -> str:
    """Classify the most likely cause from a signature and supporting evidence."""
    haystack = " ".join([signature, *evidence]).lower()
    if re.search(r"module not found|no module named|cannot find module|modulenotfounderror", haystack):
        return "missing_dependency"
    if re.search(r"permission denied|eacces|operation not permitted", haystack):
        return "permission_denied"
    if re.search(r"timeout|timed out|deadline exceeded", haystack):
        return "timeout"
    if re.search(r"connection refused|network unreachable|dns|econnrefused|connection reset", haystack):
        return "connectivity"
    if re.search(r"syntaxerror|parse error|unexpected token|invalid syntax", haystack):
        return "syntax_error"
    if re.search(r"no such file|enoent|file not found", haystack):
        return "missing_file"
    if re.search(r"assertion|test failed|failed tests?", haystack):
        return "test_failure"
    return "unknown_failure"


def choose_recovery_command(failure: Dict[str, Any]) -> Optional[str]:
    """Choose the best repair command observed after a failure."""
    candidates = failure.get("_recovery_candidates", [])
    if candidates:
        ranked = sorted(candidates, key=lambda item: (-item[0], item[1], item[2]))
        return ranked[0][2]
    failed = command_fingerprint(failure.get("failed_command"))
    for _, command in failure.get("_commands_after", []):
        if command_fingerprint(command) != failed:
            return command
    return None


def choose_resume_point(failure: Dict[str, Any], recovery_command: Optional[str]) -> Optional[str]:
    """Choose the command or checkpoint where execution resumed."""
    recovery_seen = recovery_command is None
    for _, command in failure.get("_commands_after", []):
        if command == recovery_command and not recovery_seen:
            recovery_seen = True
            continue
        if recovery_seen and command != recovery_command:
            return command
    checkpoints = failure.get("_checkpoints", [])
    if checkpoints:
        return checkpoints[-1][1]
    return None


def extract_failures(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract deduplicated failure-recovery records from normalized events."""
    failures: List[Dict[str, Any]] = []
    active: Optional[Dict[str, Any]] = None
    last_command: Optional[str] = None

    for event in events:
        line = event["line"]
        command = event.get("command")
        failure_hit = is_failure_event(line)
        success_hit = is_success_event(line)
        checkpoint_hit = is_checkpoint_event(line)

        if command:
            last_command = command

        if failure_hit:
            signature = extract_error_signature(line)
            if active and not active.get("_recovery_candidates"):
                active["evidence"].append(line)
                if signature_score(signature) > signature_score(active["error_signature"]):
                    active["error_signature"] = signature
                    active["likely_cause"] = classify_cause(signature, active["evidence"])
                continue
            active = {
                "id": "",
                "error_signature": signature,
                "likely_cause": classify_cause(signature, [line]),
                "failed_command": command or last_command,
                "recovery_command": None,
                "resume_point": None,
                "outcome": "unresolved",
                "evidence": [line],
                "_commands_after": [],
                "_recovery_candidates": [],
                "_checkpoints": [],
            }
            failures.append(active)
            continue

        if active:
            if command:
                active["_commands_after"].append((event["line_no"], command))
                if looks_like_recovery_command(command):
                    active["_recovery_candidates"].append((2, event["line_no"], command))
            if checkpoint_hit:
                active["_checkpoints"].append((event["line_no"], line))
                active["evidence"].append(line)
            if success_hit:
                active["outcome"] = "recovered"
                active["evidence"].append(line)
                active = None

    finalized: List[Dict[str, Any]] = []
    seen_clusters: Dict[Tuple[str, Optional[str], str], Dict[str, Any]] = {}
    for failure in failures:
        failure["likely_cause"] = classify_cause(failure["error_signature"], failure["evidence"])
        recovery = choose_recovery_command(failure)
        failure["recovery_command"] = recovery
        failure["resume_point"] = choose_resume_point(failure, recovery)
        failure["id"] = stable_id(
            "failure",
            failure["likely_cause"],
            failure["error_signature"],
            command_fingerprint(failure.get("failed_command")),
            length=10,
        )
        cluster_key = (
            failure["likely_cause"],
            command_fingerprint(failure.get("failed_command")),
            stable_hash(failure["error_signature"], length=8),
        )
        public_failure = {
            key: failure[key]
            for key in (
                "id",
                "error_signature",
                "likely_cause",
                "failed_command",
                "recovery_command",
                "resume_point",
                "outcome",
                "evidence",
            )
        }
        if cluster_key not in seen_clusters:
            seen_clusters[cluster_key] = public_failure
            finalized.append(public_failure)
        elif seen_clusters[cluster_key]["outcome"] != "recovered" and public_failure["outcome"] == "recovered":
            seen_clusters[cluster_key].update(public_failure)
    return finalized


def add_node(nodes: Dict[str, Dict[str, Any]], node_id: str, node_type: str, label: str, **properties: Any) -> None:
    """Add a graph node if it has not already been added."""
    nodes.setdefault(
        node_id,
        {
            "id": node_id,
            "type": node_type,
            "label": sanitize_text(label),
            "properties": {key: value for key, value in properties.items() if value not in (None, "")},
        },
    )


def add_edge(edges: List[Dict[str, Any]], source: str, target: str, edge_type: str, **properties: Any) -> None:
    """Add a graph edge when the same triple is not already present."""
    edge = {
        "source": source,
        "target": target,
        "type": edge_type,
        "properties": {key: value for key, value in properties.items() if value not in (None, "")},
    }
    if edge not in edges:
        edges.append(edge)


def build_graph(failures: List[Dict[str, Any]], source: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    """Build graph nodes, graph edges, and wikilink candidates from failures."""
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []
    wikilinks = ["[[TraceLoom]]", "[[failure recovery]]"]
    artifact_id = stable_id("artifact", source, length=10)
    add_node(nodes, artifact_id, "artifact", source)

    for failure in failures:
        failure_id = failure["id"]
        cause_id = stable_id("cause", failure["likely_cause"], length=10)
        outcome_id = stable_id("outcome", failure["outcome"], length=10)
        add_node(nodes, failure_id, "failure", failure["error_signature"], likely_cause=failure["likely_cause"])
        add_node(nodes, cause_id, "cause", failure["likely_cause"])
        add_node(nodes, outcome_id, "outcome", failure["outcome"])
        add_edge(edges, artifact_id, failure_id, "CONTAINS")
        add_edge(edges, failure_id, cause_id, "HAS_CAUSE")
        add_edge(edges, failure_id, outcome_id, "ENDED_AS")
        wikilinks.append(f"[[{failure['likely_cause'].replace('_', ' ')}]]")

        failed_command = failure.get("failed_command")
        if failed_command:
            failed_id = stable_id("command", command_fingerprint(failed_command), length=10)
            add_node(nodes, failed_id, "command", failed_command, fingerprint=command_fingerprint(failed_command))
            add_edge(edges, failed_id, failure_id, "FAILED_WITH")
            wikilinks.append(f"[[{command_fingerprint(failed_command)}]]")

        recovery_command = failure.get("recovery_command")
        if recovery_command:
            recovery_id = stable_id("command", command_fingerprint(recovery_command), length=10)
            add_node(nodes, recovery_id, "command", recovery_command, fingerprint=command_fingerprint(recovery_command))
            add_edge(edges, recovery_id, failure_id, "RECOVERED_FROM")
            wikilinks.append("[[recovery command]]")

        resume_point = failure.get("resume_point")
        if resume_point:
            checkpoint_id = stable_id("checkpoint", resume_point, length=10)
            add_node(nodes, checkpoint_id, "checkpoint", resume_point)
            add_edge(edges, failure_id, checkpoint_id, "RESUMED_AT")
            wikilinks.append("[[resume point]]")

    unique_wikilinks = sorted(dict.fromkeys(wikilinks))
    ordered_nodes = sorted(nodes.values(), key=lambda node: (node["type"], node["id"]))
    ordered_edges = sorted(edges, key=lambda edge: (edge["source"], edge["type"], edge["target"]))
    return ordered_nodes, ordered_edges, unique_wikilinks


def build_summary(failures: List[Dict[str, Any]]) -> str:
    """Build a compact deterministic summary for extracted failures."""
    if not failures:
        return "No failure-recovery candidates detected."
    recovered = sum(1 for failure in failures if failure["outcome"] == "recovered")
    main = failures[0]
    repair = main.get("recovery_command") or "no repair command"
    return (
        f"Recovered {recovered} of {len(failures)} detected failure(s). "
        f"Main pattern: {main['likely_cause']} repaired with {repair}."
    )


def build_markdown(result: Dict[str, Any]) -> str:
    """Render an Obsidian-ready Markdown recovery note from a result object."""
    failures = result["failures"]
    outcome = "recovered" if failures and all(item["outcome"] == "recovered" for item in failures) else "review"
    lines = [
        "---",
        f"trace_id: {result['trace_id']}",
        f"source: {result['source']}",
        f"failure_count: {len(failures)}",
        f"outcome: {outcome}",
        "tags:",
        "  - traceloom",
        "  - failure-recovery",
        "---",
        "",
        "# TraceLoom Recovery Note",
        "",
        "## Recovery Summary",
        result["summary"],
        "",
    ]
    for index, failure in enumerate(failures, start=1):
        lines.extend(
            [
                f"### Failure {index}",
                f"- Failure: `{failure['error_signature']}`",
                f"- Likely cause: `{failure['likely_cause']}`",
                f"- Failed command: `{failure['failed_command'] or 'unknown'}`",
                f"- Recovery command: `{failure['recovery_command'] or 'unknown'}`",
                f"- Resume point: `{failure['resume_point'] or 'unknown'}`",
                f"- Outcome: `{failure['outcome']}`",
                "",
            ]
        )
    lines.extend(["## Wikilink Candidates"])
    lines.extend(f"- {link}" for link in result["wikilinks"])
    lines.extend(["", "## Graph Edges"])
    if result["edges"]:
        lines.extend(
            f"- `{edge['source']}` -{edge['type']}-> `{edge['target']}`"
            for edge in result["edges"]
        )
    else:
        lines.append("- No graph edges detected.")
    lines.extend(["", "## Evidence"])
    if failures:
        for failure in failures:
            for evidence in failure["evidence"]:
                lines.append(f"> {evidence}")
    else:
        lines.append("> No failure evidence detected.")
    lines.append("")
    return "\n".join(lines)


def extract_trace(raw_text: str, source: str = "trace") -> Dict[str, Any]:
    """Extract a full TraceLoom JSON-compatible result from raw trace text."""
    settings = load_settings()
    events = parse_trace(raw_text)
    failures = extract_failures(events)
    nodes, edges, wikilinks = build_graph(failures, source)
    result: Dict[str, Any] = {
        "trace_id": stable_id("trace", source, raw_text, length=12),
        "source": sanitize_text(source),
        "summary": build_summary(failures),
        "failures": failures,
        "wikilinks": wikilinks,
        "nodes": nodes,
        "edges": edges,
        "markdown": "",
    }
    if settings["llm_requested"] and not settings["llm_key_available"]:
        result["summary"] = result["summary"] + " LLM summarization was requested but no environment key was available."
    elif settings["llm_requested"] and settings["llm_key_available"]:
        result["summary"] = result["summary"] + " External summarization key detected; offline rule summary used by this script."
    result["markdown"] = build_markdown(result)
    return result


def read_input(path: Optional[str]) -> Tuple[str, str]:
    """Read input text and return raw content plus a display source label."""
    if not path:
        return SAMPLE_TRACE, "sample-trace"
    input_path = Path(path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    if not input_path.is_file():
        raise ValueError(f"Input path is not a file: {path}")
    return input_path.read_text(encoding="utf-8"), input_path.name


def write_output(text: str, output_path: Optional[str]) -> None:
    """Write output text to a file or stdout."""
    if output_path:
        Path(output_path).write_text(text, encoding="utf-8")
        return
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")


def run_selftest() -> Dict[str, Any]:
    """Run the built-in sample and validate the main extraction fields."""
    result = extract_trace(SAMPLE_TRACE, "sample-trace")
    if len(result["failures"]) != 1:
        raise AssertionError("Expected exactly one failure in self-test sample.")
    failure = result["failures"][0]
    expected = {
        "error_signature": "ModuleNotFoundError: No module named 'yaml'",
        "likely_cause": "missing_dependency",
        "failed_command": "python worker.py",
        "recovery_command": "python -m pip install pyyaml",
        "resume_point": "python worker.py",
        "outcome": "recovered",
    }
    for key, value in expected.items():
        if failure.get(key) != value:
            raise AssertionError(f"Self-test mismatch for {key}: expected {value!r}, got {failure.get(key)!r}")
    return result


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Extract failure-recovery knowledge graph candidates from logs, shell history, or JSONL traces."
    )
    parser.add_argument("--input", "-i", help="Path to a UTF-8 trace file. Omit with --selftest to use sample data.")
    parser.add_argument("--output", "-o", help="Optional output file. Defaults to stdout.")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format. Default: json.")
    parser.add_argument("--selftest", action="store_true", help="Run built-in sample extraction and validate expected fields.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.selftest or not args.input:
            result = run_selftest()
        else:
            raw_text, source = read_input(args.input)
            result = extract_trace(raw_text, source)
        if args.format == "markdown":
            write_output(result["markdown"], args.output)
        else:
            write_output(json.dumps(result, indent=2, sort_keys=True), args.output)
        return 0
    except (OSError, ValueError, AssertionError) as exc:
        sys.stderr.write(f"TraceLoom error: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
