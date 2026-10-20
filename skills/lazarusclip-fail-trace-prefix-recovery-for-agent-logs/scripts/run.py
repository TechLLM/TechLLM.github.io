#!/usr/bin/env python3
"""LazarusClip - fail-trace prefix recovery for agent logs.

Given a finished (usually failed) agent execution trace, locate the first step
where outcomes stop being trustworthy, split the trace at that boundary, and
emit a schema-stable JSON record describing the salvageable pre-failure prefix,
the masked tail, a calibrated confidence score, and a suggested label.

The default judge backend is fully offline: an ensemble of three deterministic
voters (structural, lexical, heuristic). Optional remote backends (OpenAI,
Anthropic, Ollama) add one more voter to the ensemble and read their
credentials from environment variables only.

Public core function: ``recover``. The CLI, the selftest and scripts/test.py
all go through it - there is no test-only code path.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
BACKENDS = ("offline", "openai", "anthropic", "ollama")
LABELS = ("clean", "recoverable", "ambiguous", "poisoned")
EXCERPT_CHARS = 120

# Weight of each detector when scoring how strong the fatal-boundary signal is.
DETECTOR_WEIGHT = {
    "structural": 1.0,
    "lexical": 0.8,
    "heuristic": 0.55,
    "judge": 0.9,
}

# Tool-error vocabulary. Ordered; the name is reported in the signal record.
ERROR_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("python_traceback", re.compile(r"traceback \(most recent call last\)", re.I)),
    ("command_not_found", re.compile(r"\bcommand not found\b|\bnot recognized as an internal\b", re.I)),
    ("missing_path", re.compile(r"\bno such file or directory\b|\bENOENT\b", re.I)),
    ("permission_denied", re.compile(r"\bpermission denied\b|\bEACCES\b", re.I)),
    ("unauthorized", re.compile(r"\bunauthorized\b|\binvalid api key\b|\bHTTP 401\b", re.I)),
    ("rate_limited", re.compile(r"\brate ?limit(?:ed|ing)?\b|\bHTTP 429\b", re.I)),
    ("server_error", re.compile(r"\bHTTP 5\d\d\b|\binternal server error\b", re.I)),
    ("not_found", re.compile(r"\bHTTP 404\b", re.I)),
    ("timeout", re.compile(r"\btimed out\b|\btimeout\b|\bETIMEDOUT\b", re.I)),
    ("connection_failure", re.compile(r"\bconnection (?:refused|reset|aborted)\b", re.I)),
    ("nonzero_exit", re.compile(r"\bexit (?:code|status)[: ]+[1-9]\d*\b", re.I)),
    ("tool_failure", re.compile(r"\btool (?:call )?(?:failed|error)\b|\berror executing tool\b", re.I)),
]

POLICY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("policy_violation", re.compile(r"\bpolicy violation\b|\bblocked by (?:safety|policy)\b", re.I)),
    ("refusal", re.compile(r"\bi (?:cannot|can not|can't|won't) (?:comply|assist|help)\b", re.I)),
]

# Assistant text that claims success; only fatal when it follows an error step.
SUCCESS_CLAIM = re.compile(r"\b(?:succeeded|successfully|it worked|all tests passed)\b", re.I)

TOOL_CALL_TYPES = ("tool_call", "action", "function_call")
TOOL_RESULT_TYPES = ("tool_result", "observation", "function_result")


class TraceValidationError(ValueError):
    """Raised when the supplied trace does not satisfy the input contract."""


class JudgeError(RuntimeError):
    """Raised when a remote judge backend cannot be reached or parsed."""


def _excerpt(text: str) -> str:
    """Return a deterministic single-line excerpt of ``text``."""
    flat = " ".join(text.split())
    return flat if len(flat) <= EXCERPT_CHARS else flat[: EXCERPT_CHARS - 1] + "…"


def validate_trace(trace: Any) -> tuple[str, list[dict[str, Any]]]:
    """Validate a raw trace and return ``(trace_id, normalized_steps)``.

    Accepts either ``{"trace_id": ..., "steps": [...]}`` or a bare list of
    steps. Every step must be an object with a string ``role``. Raises
    TraceValidationError with an actionable message on any violation.
    """
    if isinstance(trace, list):
        trace_id, raw_steps = "unknown", trace
    elif isinstance(trace, dict):
        if "steps" not in trace:
            raise TraceValidationError("trace object is missing the required 'steps' key")
        trace_id = trace.get("trace_id", "unknown")
        if not isinstance(trace_id, str) or not trace_id:
            raise TraceValidationError("'trace_id' must be a non-empty string when present")
        raw_steps = trace["steps"]
    else:
        raise TraceValidationError(
            f"trace must be an object or a list of steps, got {type(trace).__name__}"
        )

    if not isinstance(raw_steps, list):
        raise TraceValidationError(f"'steps' must be a list, got {type(raw_steps).__name__}")
    if not raw_steps:
        raise TraceValidationError("'steps' must contain at least one step")

    steps: list[dict[str, Any]] = []
    for i, raw in enumerate(raw_steps):
        if not isinstance(raw, dict):
            raise TraceValidationError(f"step {i} must be an object, got {type(raw).__name__}")
        role = raw.get("role")
        if not isinstance(role, str) or not role:
            raise TraceValidationError(f"step {i} is missing a non-empty string 'role'")

        content = raw.get("content", raw.get("text", ""))
        if content is None:
            content = ""
        if not isinstance(content, str):
            content = json.dumps(content, sort_keys=True, ensure_ascii=False)

        status = raw.get("status")
        if status is None and raw.get("is_error") is True:
            status = "error"
        if status is None and isinstance(raw.get("exit_code"), int) and raw["exit_code"] != 0:
            status = "error"

        steps.append(
            {
                "index": i,
                "role": role,
                "type": raw.get("type", raw.get("kind", "message")),
                "name": raw.get("tool_name", raw.get("name")),
                "status": status,
                "content": content,
            }
        )
    return trace_id, steps


def _vote_structural(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flag steps whose own metadata declares failure (status/is_error/exit_code)."""
    signals = []
    for step in steps:
        status = (step["status"] or "").lower()
        if status in ("error", "failed", "failure", "exception", "denied"):
            signals.append(
                {
                    "detector": "structural",
                    "step_index": step["index"],
                    "pattern": f"status={status}",
                    "excerpt": _excerpt(step["content"]),
                }
            )
    return signals


def _vote_lexical(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flag steps whose text matches the tool-error or policy vocabularies."""
    signals = []
    for step in steps:
        for name, pattern in ERROR_PATTERNS + POLICY_PATTERNS:
            if pattern.search(step["content"]):
                signals.append(
                    {
                        "detector": "lexical",
                        "step_index": step["index"],
                        "pattern": name,
                        "excerpt": _excerpt(step["content"]),
                    }
                )
                break
    return signals


def _vote_heuristic(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flag structural pathologies: repeated tool calls, empty results, false success."""
    signals = []
    run_key, run_len = None, 0
    error_seen_at: int | None = None

    for step in steps:
        if step["type"] in TOOL_CALL_TYPES:
            key = (step["name"], " ".join(step["content"].split()))
            run_len = run_len + 1 if key == run_key else 1
            run_key = key
            if run_len >= 3:
                signals.append(
                    {
                        "detector": "heuristic",
                        "step_index": step["index"],
                        "pattern": "repeated_tool_call",
                        "excerpt": _excerpt(step["content"]),
                    }
                )
        else:
            run_key, run_len = None, 0

        if step["type"] in TOOL_RESULT_TYPES and not step["content"].strip():
            signals.append(
                {
                    "detector": "heuristic",
                    "step_index": step["index"],
                    "pattern": "empty_tool_result",
                    "excerpt": "",
                }
            )

        is_error = (step["status"] or "").lower() in ("error", "failed", "failure") or any(
            p.search(step["content"]) for _, p in ERROR_PATTERNS
        )
        if is_error:
            error_seen_at = step["index"]
        elif (
            error_seen_at is not None
            and step["role"] == "assistant"
            and SUCCESS_CLAIM.search(step["content"])
        ):
            signals.append(
                {
                    "detector": "heuristic",
                    "step_index": step["index"],
                    "pattern": "success_claim_after_error",
                    "excerpt": _excerpt(step["content"]),
                }
            )
    return signals


def offline_signals(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Run all three offline voters and return their signals, sorted."""
    signals = _vote_structural(steps) + _vote_lexical(steps) + _vote_heuristic(steps)
    return sorted(signals, key=lambda s: (s["step_index"], s["detector"], s["pattern"]))


def _judge_prompt(steps: list[dict[str, Any]]) -> str:
    """Build the deterministic prompt sent to a remote judge backend."""
    lines = [
        "You audit AI agent execution traces.",
        "Find the FIRST step index after which the trace outcomes are no longer",
        "trustworthy (tool error, hallucinated result, or policy violation).",
        'Reply with JSON only: {"fatal_step_index": <int or null>, "reason": "<short>"}',
        "",
        "TRACE:",
    ]
    for step in steps:
        tool = f" tool={step['name']}" if step["name"] else ""
        status = f" status={step['status']}" if step["status"] else ""
        lines.append(f"[{step['index']}] role={step['role']} type={step['type']}{tool}{status}")
        lines.append(f"    {_excerpt(step['content'])}")
    return "\n".join(lines)


def _http_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: int) -> dict[str, Any]:
    """POST ``payload`` as JSON and return the decoded JSON response."""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
        raise JudgeError(f"request to {url} failed: {exc}") from exc


def _judge_vote(backend: str, steps: list[dict[str, Any]], timeout: int) -> list[dict[str, Any]]:
    """Query a remote judge backend and return zero or one signal.

    Credentials are read from the environment only: OPENAI_API_KEY,
    ANTHROPIC_API_KEY, OLLAMA_HOST (default http://localhost:11434).
    """
    prompt = _judge_prompt(steps)
    if backend == "openai":
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise JudgeError("OPENAI_API_KEY is not set; use --judge offline for a local run")
        body = _http_json(
            "https://api.openai.com/v1/chat/completions",
            {
                "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                "temperature": 0,
                "messages": [{"role": "user", "content": prompt}],
            },
            {"Authorization": f"Bearer {key}"},
            timeout,
        )
        text = body["choices"][0]["message"]["content"]
    elif backend == "anthropic":
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise JudgeError("ANTHROPIC_API_KEY is not set; use --judge offline for a local run")
        body = _http_json(
            "https://api.anthropic.com/v1/messages",
            {
                "model": os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5"),
                "max_tokens": 256,
                "temperature": 0,
                "messages": [{"role": "user", "content": prompt}],
            },
            {"x-api-key": key, "anthropic-version": "2023-06-01"},
            timeout,
        )
        text = body["content"][0]["text"]
    elif backend == "ollama":
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
        body = _http_json(
            f"{host}/api/chat",
            {
                "model": os.environ.get("OLLAMA_MODEL", "llama3.1"),
                "stream": False,
                "options": {"temperature": 0},
                "messages": [{"role": "user", "content": prompt}],
            },
            {},
            timeout,
        )
        text = body["message"]["content"]
    else:
        raise JudgeError(f"unknown judge backend: {backend}")

    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise JudgeError("judge reply contained no JSON object")
    try:
        verdict = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise JudgeError(f"judge reply was not valid JSON: {exc}") from exc

    index = verdict.get("fatal_step_index")
    if index is None:
        return []
    if not isinstance(index, int) or not 0 <= index < len(steps):
        raise JudgeError(f"judge returned an out-of-range fatal_step_index: {index!r}")
    return [
        {
            "detector": "judge",
            "step_index": index,
            "pattern": f"{backend}_verdict",
            "excerpt": _excerpt(str(verdict.get("reason", ""))),
        }
    ]


def _label(
    fatal_index: int | None,
    prefix: list[dict[str, Any]],
    confidence: float,
    signals: list[dict[str, Any]],
    min_prefix_steps: int,
) -> str:
    """Choose a suggested label from the boundary, prefix size and confidence."""
    if fatal_index is None:
        return "clean"
    reasoning_steps = sum(1 for s in prefix if s["role"] == "assistant")
    if len(prefix) < min_prefix_steps or reasoning_steps == 0:
        return "poisoned"
    if any(s["pattern"] in ("policy_violation", "refusal") for s in signals if s["step_index"] == 0):
        return "poisoned"
    if confidence >= 0.6:
        return "recoverable"
    return "ambiguous"


def recover(
    trace: Any,
    *,
    judge: str = "offline",
    passes: int = 3,
    min_prefix_steps: int = 2,
    timeout: int = 30,
    on_warning: Any = None,
) -> dict[str, Any]:
    """Recover the salvageable pre-failure prefix of an agent trace.

    Args:
        trace: Raw trace (dict with ``steps``, or a bare list of steps).
        judge: Backend name from BACKENDS. Non-offline backends add one extra
            voter and require credentials in the environment.
        passes: Self-consistency passes used for confidence calibration
            (>= 1). Offline voters are deterministic, so their votes are
            replicated rather than recomputed.
        min_prefix_steps: Minimum surviving prefix length to call a trace
            recoverable rather than poisoned.
        timeout: Per-request timeout in seconds for remote judges.
        on_warning: Optional callable receiving non-fatal warning strings.

    Returns:
        A schema-stable record; see the module docs and SKILL.md.

    Raises:
        TraceValidationError: if the trace violates the input contract.
        ValueError: if ``judge``/``passes``/``min_prefix_steps`` are invalid.
    """
    if judge not in BACKENDS:
        raise ValueError(f"judge must be one of {BACKENDS}, got {judge!r}")
    if not isinstance(passes, int) or passes < 1:
        raise ValueError(f"passes must be an integer >= 1, got {passes!r}")
    if not isinstance(min_prefix_steps, int) or min_prefix_steps < 0:
        raise ValueError(f"min_prefix_steps must be an integer >= 0, got {min_prefix_steps!r}")

    trace_id, steps = validate_trace(trace)
    base = offline_signals(steps)

    ballots: list[list[dict[str, Any]]] = [base for _ in range(passes)]
    judge_used = judge
    if judge != "offline":
        judge_ballots = []
        for _ in range(passes):
            try:
                judge_ballots.append(_judge_vote(judge, steps, timeout))
            except JudgeError as exc:
                if on_warning:
                    on_warning(f"judge '{judge}' unavailable ({exc}); falling back to offline voters")
                judge_used = f"{judge}->offline"
                judge_ballots = [[] for _ in range(passes)]
                break
        ballots = [b + j for b, j in zip(ballots, judge_ballots)]

    votes = [min(s["step_index"] for s in ballot) for ballot in ballots if ballot]
    signals = sorted(
        {(s["detector"], s["step_index"], s["pattern"], s["excerpt"]) for ballot in ballots for s in ballot}
    )
    signals = [
        {"detector": d, "step_index": i, "pattern": p, "excerpt": e} for d, i, p, e in signals
    ]

    if votes:
        fatal_index = min(votes)
        agreement = votes.count(fatal_index) / len(ballots)
        strength = max(
            DETECTOR_WEIGHT[s["detector"]] for s in signals if s["step_index"] == fatal_index
        )
        confidence = round(0.5 * agreement + 0.5 * strength, 3)
        prefix, tail = steps[:fatal_index], steps[fatal_index:]
    else:
        fatal_index, confidence = None, 1.0
        prefix, tail = steps, []

    label = _label(fatal_index, prefix, confidence, signals, min_prefix_steps)
    return {
        "schema_version": SCHEMA_VERSION,
        "trace_id": trace_id,
        "step_count": len(steps),
        "fatal_step_index": fatal_index,
        "confidence": confidence,
        "suggested_label": label,
        "pre_failure_subgraph": {"step_count": len(prefix), "steps": prefix},
        "masked_tail": {"step_count": len(tail), "steps": tail},
        "mask_hints": {
            "advantage_clamp": "one_sided",
            "keep_step_indices": [s["index"] for s in prefix],
            "mask_step_indices": [s["index"] for s in tail],
        },
        "signals": signals,
        "judge": {"backend": judge_used, "passes": passes, "agreement": round(
            votes.count(fatal_index) / len(ballots), 3) if votes else 1.0},
    }


def recover_batch(paths: list[Path], **kwargs: Any) -> dict[str, Any]:
    """Recover every trace file in ``paths`` (sorted) and summarize the labels."""
    records, errors = [], []
    for path in sorted(paths):
        try:
            record = recover(json.loads(path.read_text(encoding="utf-8")), **kwargs)
        except (TraceValidationError, json.JSONDecodeError, OSError) as exc:
            errors.append({"source": path.name, "error": str(exc)})
            continue
        record["source"] = path.name
        records.append(record)
    summary = {label: sum(1 for r in records if r["suggested_label"] == label) for label in LABELS}
    return {
        "schema_version": SCHEMA_VERSION,
        "processed": len(records),
        "failed": len(errors),
        "label_counts": summary,
        "records": records,
        "errors": errors,
    }


SAMPLE_TRACES: list[dict[str, Any]] = [
    {
        "trace_id": "sample-tool-failure",
        "steps": [
            {"role": "user", "type": "message", "content": "Summarize the latest release notes."},
            {"role": "assistant", "type": "thought", "content": "I should read the notes file first."},
            {"role": "assistant", "type": "tool_call", "tool_name": "read_file",
             "content": "{\"path\": \"NOTES.md\"}"},
            {"role": "tool", "type": "tool_result", "tool_name": "read_file", "status": "error",
             "content": "No such file or directory: NOTES.md"},
            {"role": "assistant", "type": "message", "content": "The notes list three fixes."},
        ],
    },
    {
        "trace_id": "sample-clean",
        "steps": [
            {"role": "user", "type": "message", "content": "What is 2 + 2?"},
            {"role": "assistant", "type": "thought", "content": "Simple arithmetic."},
            {"role": "assistant", "type": "message", "content": "4"},
        ],
    },
    {
        "trace_id": "sample-poisoned",
        "steps": [
            {"role": "user", "type": "message", "content": "Delete the production database."},
            {"role": "assistant", "type": "message", "content": "I cannot comply with that request."},
        ],
    },
]


def selftest() -> int:
    """Run the offline selftest over built-in sample traces. Returns an exit code."""
    checks: list[tuple[str, bool]] = []

    failure = recover(SAMPLE_TRACES[0])
    checks.append(("tool-failure boundary is step 3", failure["fatal_step_index"] == 3))
    checks.append(("tool-failure label is recoverable", failure["suggested_label"] == "recoverable"))
    checks.append(("prefix keeps 3 steps", failure["pre_failure_subgraph"]["step_count"] == 3))
    checks.append(("tail masks 2 steps", failure["masked_tail"]["step_count"] == 2))
    checks.append(("mask hints agree", failure["mask_hints"]["mask_step_indices"] == [3, 4]))
    checks.append(("confidence is high", failure["confidence"] >= 0.9))

    clean = recover(SAMPLE_TRACES[1])
    checks.append(("clean trace has no boundary", clean["fatal_step_index"] is None))
    checks.append(("clean trace label is clean", clean["suggested_label"] == "clean"))

    poisoned = recover(SAMPLE_TRACES[2])
    checks.append(("refusal at step 1 is poisoned", poisoned["suggested_label"] == "poisoned"))

    checks.append(("output is deterministic", recover(SAMPLE_TRACES[0]) == failure))

    try:
        recover({"steps": []})
        checks.append(("empty steps rejected", False))
    except TraceValidationError:
        checks.append(("empty steps rejected", True))

    for name, passed in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")
    failures = sum(1 for _, passed in checks if not passed)
    print(f"\n{len(checks) - failures}/{len(checks)} checks passed")
    return 1 if failures else 0


def _write_output(path: Path, text: str, force: bool) -> None:
    """Write ``text`` to ``path``, refusing to clobber an existing file."""
    if path.exists() and not force:
        raise SystemExit(f"error: {path} already exists; pass --force to overwrite")
    path.write_text(text, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="run.py",
        description="LazarusClip: recover the salvageable pre-failure prefix of agent traces.",
        epilog="Example: python scripts/run.py --input examples/input/trace_tool_failure.input.json",
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--input", metavar="FILE", help="trace JSON file ('-' reads stdin)")
    source.add_argument("--batch", metavar="DIR", help="directory of *.json traces to triage")
    source.add_argument("--selftest", action="store_true", help="run offline selftest and exit")
    parser.add_argument("--judge", choices=BACKENDS, default="offline",
                        help="judge backend (default: offline, no network)")
    parser.add_argument("--passes", type=int, default=3,
                        help="self-consistency passes for confidence calibration (default: 3)")
    parser.add_argument("--min-prefix-steps", type=int, default=2,
                        help="minimum surviving prefix length to call a trace recoverable")
    parser.add_argument("--timeout", type=int, default=30,
                        help="per-request timeout in seconds for remote judges")
    parser.add_argument("--output", metavar="FILE", help="write JSON here instead of stdout")
    parser.add_argument("--force", action="store_true", help="allow --output to overwrite a file")
    parser.add_argument("--indent", type=int, default=2, help="JSON indent (default: 2)")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    args = build_parser().parse_args(argv)
    if args.selftest or (not args.input and not args.batch):
        return selftest()

    options = {
        "judge": args.judge,
        "passes": args.passes,
        "min_prefix_steps": args.min_prefix_steps,
        "timeout": args.timeout,
        "on_warning": lambda message: print(f"warning: {message}", file=sys.stderr),
    }

    try:
        if args.batch:
            directory = Path(args.batch)
            if not directory.is_dir():
                print(f"error: --batch path is not a directory: {directory}", file=sys.stderr)
                return 2
            paths = [p for p in directory.glob("*.json") if p.is_file()]
            if not paths:
                print(f"error: no *.json trace files found in {directory}", file=sys.stderr)
                return 2
            result = recover_batch(paths, **options)
        else:
            if args.input == "-":
                raw = sys.stdin.read()
            else:
                path = Path(args.input)
                if not path.is_file():
                    print(f"error: input file not found: {path}", file=sys.stderr)
                    return 2
                raw = path.read_text(encoding="utf-8")
            result = recover(json.loads(raw), **options)
    except json.JSONDecodeError as exc:
        print(f"error: input is not valid JSON: {exc}", file=sys.stderr)
        return 2
    except (TraceValidationError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: could not read input: {exc}", file=sys.stderr)
        return 2

    text = json.dumps(result, indent=args.indent, ensure_ascii=False) + "\n"
    if args.output:
        _write_output(Path(args.output), text, args.force)
        print(f"wrote {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
