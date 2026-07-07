"""RunWeave CLI for converting shell logs and plans into agent run records.

The module is dependency-free and deterministic by default. It accepts raw shell
logs, a lightweight YAML or JSON plan, and emits a normalized
agent_run_record.json structure for debugging and replay-oriented workflows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


SCHEMA_VERSION = "runweave.agent_run_record.v1"
DEFAULT_GENERATED_AT = "1970-01-01T00:00:00Z"
DEFAULT_FAILURE_PATTERNS = [
    r"\bAssertionError\b",
    r"\bTraceback\b",
    r"\bException\b",
    r"\bERROR\b",
    r"\berror:",
    r"\bfailed\b",
    r"\bfailure\b",
    r"\bcommand not found\b",
    r"\bpermission denied\b",
    r"\btimeout\b",
    r"\btimed out\b",
]

SAMPLE_PLAN = """run_id: sample-run
objective: validate package
steps:
  - id: lint
    command: python -m py_compile scripts/run.py
    expect: success
  - id: test
    command: python scripts/test.py
    expect: success
"""

SAMPLE_LOG = """$ python -m py_compile scripts/run.py
stdout: compiled scripts/run.py
exit code: 0
$ python scripts/test.py
stderr: AssertionError: missing field agent_run_record
exit code: 1
"""


def parse_env_list(value: Optional[str]) -> List[str]:
    """Return a comma-separated environment value as a clean string list."""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def read_text(path: str, label: str) -> str:
    """Read a UTF-8 text file and raise a clear CLI error on failure."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SystemExit(f"RunWeave error: cannot read {label} file '{path}': not found") from exc
    except OSError as exc:
        raise SystemExit(f"RunWeave error: cannot read {label} file '{path}': {exc}") from exc


def parse_scalar(value: str) -> Any:
    """Parse a scalar from the small YAML subset supported by RunWeave."""
    value = value.strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none"}:
        return None
    return value


def split_key_value(text: str, line_no: int) -> Tuple[str, str]:
    """Split a simple YAML key-value line into key and value parts."""
    if ":" not in text:
        raise ValueError(f"unsupported YAML plan line {line_no}: expected 'key: value'")
    key, value = text.split(":", 1)
    key = key.strip()
    if not key:
        raise ValueError(f"unsupported YAML plan line {line_no}: empty key")
    return key, value.strip()


def parse_lightweight_plan(plan_text: str) -> Dict[str, Any]:
    """Parse a lightweight YAML or JSON execution plan into a dictionary.

    Supported YAML is intentionally small: top-level scalar keys plus a
    top-level `steps:` list where each item contains scalar `key: value` pairs.
    JSON objects with an equivalent shape are also accepted.
    """
    stripped_text = plan_text.strip()
    if not stripped_text:
        return {"steps": []}
    if stripped_text.startswith("{"):
        try:
            data = json.loads(stripped_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON plan: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("JSON plan must be an object")
        steps = data.get("steps", [])
        if not isinstance(steps, list):
            raise ValueError("plan field 'steps' must be a list")
        return data

    data: Dict[str, Any] = {}
    steps: List[Dict[str, Any]] = []
    current_step: Optional[Dict[str, Any]] = None
    in_steps = False

    for line_no, raw_line in enumerate(plan_text.splitlines(), start=1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        stripped = raw_line.strip()
        is_top_level = raw_line == raw_line.lstrip()

        if is_top_level and stripped == "steps:":
            in_steps = True
            data["steps"] = steps
            continue

        if is_top_level and not in_steps:
            key, value = split_key_value(stripped, line_no)
            data[key] = parse_scalar(value)
            continue

        if in_steps and stripped.startswith("- "):
            if current_step is not None:
                steps.append(current_step)
            current_step = {}
            rest = stripped[2:].strip()
            if rest:
                key, value = split_key_value(rest, line_no)
                current_step[key] = parse_scalar(value)
            continue

        if in_steps and current_step is not None:
            key, value = split_key_value(stripped, line_no)
            current_step[key] = parse_scalar(value)
            continue

        raise ValueError(f"unsupported YAML plan line {line_no}: {raw_line}")

    if current_step is not None:
        steps.append(current_step)
    data.setdefault("steps", steps)
    if not isinstance(data["steps"], list):
        raise ValueError("plan field 'steps' must be a list")
    return data


def extract_command(line: str) -> Optional[str]:
    """Extract a shell command from a transcript line if it has a known marker."""
    stripped = line.strip()
    for prefix in ("$ ", "> "):
        if stripped.startswith(prefix):
            command = stripped[len(prefix) :].strip()
            return command or None
    match = re.match(r"^COMMAND:\s*(.+)$", stripped, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def extract_exit_code(line: str) -> Optional[int]:
    """Extract an exit code from a transcript line when present."""
    patterns = [
        r"\[exit\s+(-?\d+)\]",
        r"\bexit(?:\s+code)?\s*[:=]?\s*(-?\d+)\b",
        r"\bstatus\s*[:=]\s*(-?\d+)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, line, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def classify_stream(line: str) -> str:
    """Classify a transcript line as stdout or stderr."""
    stripped = line.lstrip()
    if re.match(r"^(stderr|err):", stripped, flags=re.IGNORECASE):
        return "stderr"
    return "stdout"


def strip_stream_prefix(line: str) -> str:
    """Remove simple stdout/stderr prefixes from a transcript line."""
    return re.sub(r"^(stdout|stderr|err):\s*", "", line.strip(), flags=re.IGNORECASE)


def analyze_step(step: Dict[str, Any], failure_patterns: Sequence[str]) -> List[str]:
    """Return failure signals detected for an executed step."""
    signals: List[str] = []
    exit_code = step.get("exit_code")
    if exit_code is not None and exit_code != 0:
        signals.append(f"exit_code:{exit_code}")

    combined = "\n".join(step.get("stdout", []) + step.get("stderr", []))
    for pattern in failure_patterns:
        if re.search(pattern, combined, flags=re.IGNORECASE):
            signals.append(f"pattern:{pattern}")

    deduped: List[str] = []
    seen = set()
    for signal in signals:
        if signal not in seen:
            seen.add(signal)
            deduped.append(signal)
    return deduped


def parse_shell_log(log_text: str, failure_patterns: Sequence[str]) -> List[Dict[str, Any]]:
    """Parse a shell transcript into executed step records."""
    steps: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None

    for line_no, raw_line in enumerate(log_text.splitlines(), start=1):
        command = extract_command(raw_line)
        if command:
            if current is not None:
                finalize_executed_step(current, failure_patterns)
                steps.append(current)
            current = {
                "id": f"exec-{len(steps) + 1:03d}",
                "command": command,
                "planned_step_id": None,
                "started_at_line": line_no,
                "exit_code": None,
                "stdout": [],
                "stderr": [],
                "observations": [],
            }
            continue

        if current is None:
            continue

        exit_code = extract_exit_code(raw_line)
        if exit_code is not None:
            current["exit_code"] = exit_code
            current["observations"].append(
                {"line": line_no, "stream": "meta", "text": raw_line.strip()}
            )
            continue

        text = strip_stream_prefix(raw_line)
        stream = classify_stream(raw_line)
        current[stream].append(text)
        current["observations"].append({"line": line_no, "stream": stream, "text": text})

    if current is not None:
        finalize_executed_step(current, failure_patterns)
        steps.append(current)

    return steps


def finalize_executed_step(step: Dict[str, Any], failure_patterns: Sequence[str]) -> None:
    """Add status and failure metadata to one executed step in place."""
    signals = analyze_step(step, failure_patterns)
    step["failure_signals"] = signals
    step["status"] = "failed" if signals else "completed"


def normalize_command(command: str) -> str:
    """Normalize a command string for planned-vs-actual matching."""
    return " ".join(command.strip().split())


def build_planned_steps(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert parsed plan data into normalized planned step records."""
    planned_steps: List[Dict[str, Any]] = []
    for index, item in enumerate(plan.get("steps", []), start=1):
        if not isinstance(item, dict):
            raise ValueError(f"plan step {index} must be an object")
        command = str(item.get("command", "")).strip()
        if not command:
            raise ValueError(f"plan step {index} is missing required field 'command'")
        planned_steps.append(
            {
                "id": str(item.get("id") or f"plan-{index:03d}"),
                "command": command,
                "expect": str(item.get("expect") or "success"),
                "status": "missing",
                "matched_executed_step_id": None,
            }
        )
    return planned_steps


def match_plan_to_execution(
    planned_steps: List[Dict[str, Any]], executed_steps: List[Dict[str, Any]]
) -> int:
    """Match executed commands to planned commands and return the match count."""
    unused_by_command: Dict[str, List[Dict[str, Any]]] = {}
    for planned in planned_steps:
        unused_by_command.setdefault(normalize_command(planned["command"]), []).append(planned)

    matched = 0
    for executed in executed_steps:
        candidates = unused_by_command.get(normalize_command(executed["command"]), [])
        if not candidates:
            continue
        planned = candidates.pop(0)
        planned["matched_executed_step_id"] = executed["id"]
        planned["status"] = "failed" if executed["status"] == "failed" else "completed"
        executed["planned_step_id"] = planned["id"]
        matched += 1
    return matched


def make_failures(executed_steps: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build compact failure records from executed steps."""
    failures: List[Dict[str, Any]] = []
    for step in executed_steps:
        if step.get("status") != "failed":
            continue
        failures.append(
            {
                "executed_step_id": step["id"],
                "planned_step_id": step.get("planned_step_id"),
                "command": step["command"],
                "exit_code": step.get("exit_code"),
                "signals": step.get("failure_signals", []),
                "stderr_excerpt": step.get("stderr", [])[-5:],
            }
        )
    return failures


def propose_repair(failure: Dict[str, Any], environment_hints: Sequence[str]) -> Dict[str, Any]:
    """Create one deterministic repair candidate for a failed command."""
    command = failure["command"]
    signals = " ".join(failure.get("signals", []))
    stderr = "\n".join(failure.get("stderr_excerpt", []))
    combined = f"{signals}\n{stderr}".lower()

    if "command not found" in combined:
        executable = command.split()[0] if command.split() else "missing-command"
        template = f"install or expose '{executable}' on PATH, then rerun: {command}"
        confidence = 0.78
        rationale = "The log indicates the command executable was not found."
    elif "permission denied" in combined:
        template = f"check executable permissions and rerun: {command}"
        confidence = 0.72
        rationale = "The log indicates a filesystem permission failure."
    elif "timeout" in combined or "timed out" in combined:
        template = f"rerun with a longer timeout after checking for hangs: {command}"
        confidence = 0.68
        rationale = "The log indicates the command exceeded a time limit."
    elif "assertionerror" in combined or "traceback" in combined:
        template = f"inspect the failing assertion or traceback, patch the code, then rerun: {command}"
        confidence = 0.62
        rationale = "The log indicates a code-level test or runtime failure."
    elif failure.get("exit_code") not in (None, 0):
        template = f"inspect stderr and rerun after correction: {command}"
        confidence = 0.55
        rationale = "The command returned a non-zero exit code."
    else:
        template = f"review failure signals and rerun: {command}"
        confidence = 0.45
        rationale = "RunWeave detected heuristic failure signals."

    return {
        "command_template": template,
        "environment_hints": list(environment_hints),
        "confidence": confidence,
        "rationale": rationale,
    }


def make_repair_candidates(
    failures: Sequence[Dict[str, Any]], environment_hints: Sequence[str]
) -> List[Dict[str, Any]]:
    """Create deterministic repair candidate records for failures."""
    candidates: List[Dict[str, Any]] = []
    for index, failure in enumerate(failures, start=1):
        candidate = propose_repair(failure, environment_hints)
        candidate["id"] = f"repair-{index:03d}"
        candidate["failure_step_id"] = failure["executed_step_id"]
        ordered = {
            "id": candidate["id"],
            "failure_step_id": candidate["failure_step_id"],
            "command_template": candidate["command_template"],
            "environment_hints": candidate["environment_hints"],
            "confidence": candidate["confidence"],
            "rationale": candidate["rationale"],
        }
        candidates.append(ordered)
    return candidates


def make_timeline(
    planned_steps: Sequence[Dict[str, Any]],
    executed_steps: Sequence[Dict[str, Any]],
    repair_candidates: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Build a compact action-plan-execute-repair timeline."""
    timeline: List[Dict[str, Any]] = []
    for planned in planned_steps:
        timeline.append(
            {
                "phase": "plan",
                "step_id": planned["id"],
                "status": planned["status"],
                "message": f"Planned command: {planned['command']}",
            }
        )
    for executed in executed_steps:
        timeline.append(
            {
                "phase": "execute",
                "step_id": executed["id"],
                "status": executed["status"],
                "message": f"Executed command: {executed['command']}",
            }
        )
    for repair in repair_candidates:
        timeline.append(
            {
                "phase": "repair",
                "step_id": repair["failure_step_id"],
                "status": "candidate",
                "message": repair["command_template"],
            }
        )
    return timeline


def deterministic_run_id(log_text: str, plan_text: str) -> str:
    """Return a stable run id derived from input content."""
    digest = hashlib.sha256(f"{plan_text}\n---RUNWEAVE-LOG---\n{log_text}".encode("utf-8")).hexdigest()
    return f"run-{digest[:12]}"


def compact_executed_step(step: Dict[str, Any]) -> Dict[str, Any]:
    """Return the public executed-step representation for the output record."""
    return {
        "id": step["id"],
        "command": step["command"],
        "planned_step_id": step.get("planned_step_id"),
        "exit_code": step.get("exit_code"),
        "status": step["status"],
        "failure_signals": step.get("failure_signals", []),
        "stdout_excerpt": step.get("stdout", [])[-5:],
        "stderr_excerpt": step.get("stderr", [])[-5:],
    }


def build_agent_run_record(
    log_text: str = "",
    plan_text: str = "",
    *,
    source: Optional[Dict[str, Optional[str]]] = None,
    run_id: Optional[str] = None,
    generated_at: Optional[str] = None,
    failure_patterns: Optional[Sequence[str]] = None,
    environment_hints: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Build a normalized agent run record from log and plan text."""
    patterns = list(failure_patterns or DEFAULT_FAILURE_PATTERNS)
    hints = list(environment_hints or [])
    plan = parse_lightweight_plan(plan_text) if plan_text else {"steps": []}
    planned_steps = build_planned_steps(plan)
    executed_steps_internal = parse_shell_log(log_text, patterns) if log_text else []
    matched_steps = match_plan_to_execution(planned_steps, executed_steps_internal)
    executed_steps = [compact_executed_step(step) for step in executed_steps_internal]
    failures = make_failures(executed_steps_internal)
    repair_candidates = make_repair_candidates(failures, hints)
    timeline = make_timeline(planned_steps, executed_steps, repair_candidates)

    selected_run_id = run_id or plan.get("run_id") or deterministic_run_id(log_text, plan_text)
    record_source = source or {
        "log": "inline" if log_text else None,
        "plan": "inline" if plan_text else None,
    }
    summary = {
        "planned_steps": len(planned_steps),
        "executed_steps": len(executed_steps),
        "matched_steps": matched_steps,
        "failed_steps": len(failures),
        "missing_planned_steps": sum(1 for step in planned_steps if step["status"] == "missing"),
        "repair_candidates": len(repair_candidates),
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": str(selected_run_id),
        "generated_at": generated_at or DEFAULT_GENERATED_AT,
        "source": record_source,
        "summary": summary,
        "planned_steps": planned_steps,
        "executed_steps": executed_steps,
        "timeline": timeline,
        "failures": failures,
        "repair_candidates": repair_candidates,
        "environment_hints": hints,
    }


def write_record(record: Dict[str, Any], output_path: Optional[str]) -> None:
    """Write the record as pretty JSON to a file or stdout."""
    text = json.dumps(record, indent=2, ensure_ascii=True) + "\n"
    if output_path:
        try:
            Path(output_path).write_text(text, encoding="utf-8")
        except OSError as exc:
            raise SystemExit(f"RunWeave error: cannot write output file '{output_path}': {exc}") from exc
    else:
        sys.stdout.write(text)


def append_record(record: Dict[str, Any], append_path: Optional[str]) -> None:
    """Append the record as one JSON line when an append log path is provided."""
    if not append_path:
        return
    text = json.dumps(record, separators=(",", ":"), ensure_ascii=True) + "\n"
    try:
        with Path(append_path).open("a", encoding="utf-8") as handle:
            handle.write(text)
    except OSError as exc:
        raise SystemExit(f"RunWeave error: cannot append run log '{append_path}': {exc}") from exc


def build_parser() -> argparse.ArgumentParser:
    """Build the RunWeave command-line parser."""
    parser = argparse.ArgumentParser(
        description="Convert shell logs and lightweight plans into agent_run_record.json."
    )
    parser.add_argument("--log", help="Path to a plain text shell transcript.")
    parser.add_argument("--plan", help="Path to a lightweight YAML or JSON execution plan.")
    parser.add_argument("--output", "-o", help="Path for pretty JSON output. Defaults to stdout.")
    parser.add_argument(
        "--append-run-log",
        help="Append the record as one compact JSON line to this JSONL file.",
    )
    parser.add_argument(
        "--run-id",
        default=os.getenv("RUNWEAVE_RUN_ID"),
        help="Override run id. Defaults to RUNWEAVE_RUN_ID, plan run_id, or a content hash.",
    )
    parser.add_argument(
        "--generated-at",
        default=os.getenv("RUNWEAVE_GENERATED_AT", DEFAULT_GENERATED_AT),
        help="Timestamp string to place in the record. Defaults to a deterministic timestamp.",
    )
    parser.add_argument(
        "--failure-pattern",
        action="append",
        default=[],
        help="Additional regex pattern for failure detection. May be repeated.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run with built-in sample plan and log. Also used when no input paths are provided.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point for RunWeave."""
    parser = build_parser()
    args = parser.parse_args(argv)

    use_sample = args.selftest or (not args.log and not args.plan)
    if use_sample:
        log_text = SAMPLE_LOG
        plan_text = SAMPLE_PLAN
        source = {"log": "builtin:sample", "plan": "builtin:sample"}
    else:
        log_text = read_text(args.log, "log") if args.log else ""
        plan_text = read_text(args.plan, "plan") if args.plan else ""
        source = {"log": args.log if args.log else None, "plan": args.plan if args.plan else None}

    extra_patterns = parse_env_list(os.getenv("RUNWEAVE_FAILURE_PATTERNS")) + list(
        args.failure_pattern or []
    )
    failure_patterns = DEFAULT_FAILURE_PATTERNS + extra_patterns
    environment_hints = parse_env_list(os.getenv("RUNWEAVE_ENV_HINTS"))

    try:
        record = build_agent_run_record(
            log_text,
            plan_text,
            source=source,
            run_id=args.run_id,
            generated_at=args.generated_at,
            failure_patterns=failure_patterns,
            environment_hints=environment_hints,
        )
    except ValueError as exc:
        raise SystemExit(f"RunWeave error: {exc}") from exc

    write_record(record, args.output)
    append_record(record, args.append_run_log)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
