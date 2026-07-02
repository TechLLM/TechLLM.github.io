#!/usr/bin/env python3
"""FailForge: turn social publishing failure logs into agent evaluation scenarios."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


SAMPLE_LOGS = """\
{"timestamp":"2026-06-30T10:15:05Z","platform":"instagram","level":"ERROR","request_id":"req_sample_auth_001","account_id":"acct_123456","status_code":401,"error":"OAuthException: Error validating access token: Session has expired","headers":{"Authorization":"Bearer sample_access_token_abc123"}}
2026-06-30T10:20:11Z platform=tiktok request_id=req_sample_rate_002 status=429 error="Rate limit exceeded; retry after 60 seconds" account_id=acct_789000
2026-06-30T10:22:40Z platform=facebook request_id=req_sample_media_003 status=400 error="Media container is not ready for publishing; please retry later" media_container_id=container_555
[DRY-RUN] 2026-06-30T10:25:09Z platform=linkedin request_id=req_sample_dry_004 would publish post_url=https://example.invalid account_id=acct_111222
2026-06-30T10:27:31Z platform=x request_id=req_sample_timeout_005 error="Network timeout while calling publish endpoint after 30 seconds"
"""


SENSITIVE_KEYS = {
    "access_token",
    "api_key",
    "authorization",
    "cookie",
    "headers",
    "password",
    "refresh_token",
    "secret",
    "token",
}

ACCOUNT_ID_KEYS = {
    "account",
    "account_id",
    "business_id",
    "ig_user_id",
    "media_container_id",
    "organization_id",
    "page_id",
    "profile_id",
    "user_id",
}


@dataclass(frozen=True)
class Rule:
    family: str
    pattern: re.Pattern[str]
    root_cause: str
    retryable: bool
    severity: str
    recovery: str
    expected_diagnosis: str


RULES = [
    Rule(
        family="authentication",
        pattern=re.compile(r"\b(401|403|oauth|auth|access token|refresh token|expired|permission|unauthorized|forbidden)\b", re.I),
        root_cause="Credential, token, permission, or authorization state is invalid.",
        retryable=False,
        severity="high",
        recovery="Refresh or re-authorize credentials before another publish attempt.",
        expected_diagnosis="The publish attempt failed because authentication or permissions are invalid.",
    ),
    Rule(
        family="rate_limit",
        pattern=re.compile(r"\b(429|rate limit|too many requests|throttl|retry[- ]after|quota)\b", re.I),
        root_cause="The platform or gateway is throttling publish attempts.",
        retryable=True,
        severity="medium",
        recovery="Wait for the retry window, apply backoff, and avoid immediate repeated retries.",
        expected_diagnosis="The publish attempt was throttled by the platform or API gateway.",
    ),
    Rule(
        family="media_container_delay",
        pattern=re.compile(r"\b(media container|container.*not ready|not ready for publishing|processing|transcod|upload.*incomplete)\b", re.I),
        root_cause="A required media asset or container is still processing or incomplete.",
        retryable=True,
        severity="medium",
        recovery="Poll or wait until the media container is ready before publishing.",
        expected_diagnosis="The publish attempt failed because media preparation has not completed.",
    ),
    Rule(
        family="validation",
        pattern=re.compile(r"\b(400|invalid parameter|validation|missing|required|malformed|unsupported|bad request)\b", re.I),
        root_cause="The publish payload is invalid or missing required data.",
        retryable=False,
        severity="medium",
        recovery="Fix the request payload, media metadata, or required publishing fields before retrying.",
        expected_diagnosis="The publish attempt failed because the request payload is invalid.",
    ),
    Rule(
        family="network_timeout",
        pattern=re.compile(r"\b(timeout|timed out|econnreset|connection reset|dns|network|socket|temporarily unavailable)\b", re.I),
        root_cause="The client could not reliably reach the publishing endpoint.",
        retryable=True,
        severity="medium",
        recovery="Retry with bounded exponential backoff and preserve idempotency safeguards.",
        expected_diagnosis="The publish attempt failed because of a transient network or timeout condition.",
    ),
    Rule(
        family="api_error",
        pattern=re.compile(r"\b(500|502|503|504|internal server error|bad gateway|service unavailable|gateway timeout|api error|graph api)\b", re.I),
        root_cause="The remote API returned an upstream or platform error.",
        retryable=True,
        severity="high",
        recovery="Retry with backoff if idempotent; escalate if the platform error persists.",
        expected_diagnosis="The publish attempt failed because the platform API returned an upstream error.",
    ),
    Rule(
        family="dry_run_trace",
        pattern=re.compile(r"\b(dry[-_ ]run|would publish|simulation|preview only)\b", re.I),
        root_cause="The trace is a dry run rather than a failed live publish.",
        retryable=False,
        severity="low",
        recovery="Do not retry as a live publish unless explicitly requested and all prerequisites are valid.",
        expected_diagnosis="The trace is a dry run and should not be treated as a live publish failure.",
    ),
]


PLATFORMS = {
    "facebook": re.compile(r"\b(facebook|fb|graph api)\b", re.I),
    "instagram": re.compile(r"\b(instagram|ig)\b", re.I),
    "linkedin": re.compile(r"\b(linkedin)\b", re.I),
    "tiktok": re.compile(r"\b(tiktok)\b", re.I),
    "x": re.compile(r"\b(twitter|x\.com|\bx\b)\b", re.I),
    "youtube": re.compile(r"\b(youtube|yt)\b", re.I),
}


def redact_text(value: str) -> str:
    """Redact common sensitive values while preserving diagnostic shape."""
    value = re.sub(r"(?i)(authorization\s*[:=]\s*bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1[REDACTED_TOKEN]", value)
    value = re.sub(r"(?i)(access[_-]?token|refresh[_-]?token|api[_-]?key|secret|password|cookie)=([^&\s\"']+)", r"\1=[REDACTED_SECRET]", value)
    value = re.sub(r"(?i)\b(bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1[REDACTED_TOKEN]", value)
    value = re.sub(r"https?://[^\s\"')]+", "[REDACTED_URL]", value)
    value = re.sub(r"(?i)\b(account_id|user_id|page_id|profile_id|business_id|ig_user_id|media_container_id)=([A-Za-z0-9_.:-]+)", r"\1=[REDACTED_ID]", value)
    return value


def redact_obj(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            normalized = key_text.lower()
            if normalized in SENSITIVE_KEYS or any(part in normalized for part in SENSITIVE_KEYS):
                redacted[key_text] = "[REDACTED_SECRET]"
            elif normalized in ACCOUNT_ID_KEYS or normalized.endswith("_account_id"):
                redacted[key_text] = "[REDACTED_ID]"
            else:
                redacted[key_text] = redact_obj(item)
        return redacted
    if isinstance(value, list):
        return [redact_obj(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def parse_json_payload(content: str) -> list[Any] | None:
    stripped = content.strip()
    if not stripped:
        return []
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return None

    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("logs", "events", "records", "items"):
            if isinstance(payload.get(key), list):
                return payload[key]
        return [payload]
    return [payload]


def parse_lines(content: str) -> list[Any]:
    records: list[Any] = []
    for line_no, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            value = json.loads(stripped)
            if isinstance(value, (dict, list)):
                records.append(value)
            else:
                records.append({"message": str(value), "line": line_no})
        except json.JSONDecodeError:
            records.append({"message": stripped, "line": line_no})
    return records


def parse_content(content: str) -> list[Any]:
    parsed = parse_json_payload(content)
    if parsed is not None:
        return parsed
    return parse_lines(content)


def flatten_records(records: Iterable[Any]) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for item in records:
        if isinstance(item, list):
            flattened.extend(flatten_records(item))
        elif isinstance(item, dict):
            flattened.append(item)
        else:
            flattened.append({"message": str(item)})
    return flattened


def infer_platform(text: str) -> str:
    for platform, pattern in PLATFORMS.items():
        if pattern.search(text):
            return platform
    return "unknown"


def first_value(record: dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return None


def extract_timestamp(text: str) -> str | None:
    match = re.search(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?\b", text)
    return match.group(0) if match else None


def extract_status_code(record: dict[str, Any], text: str) -> int | None:
    value = first_value(record, ("status_code", "status", "http_status", "code"))
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        match = re.search(r"\b([1-5]\d{2})\b", value)
        if match:
            return int(match.group(1))
    match = re.search(r"\b(?:status|http_status|code)[=: ]+([1-5]\d{2})\b", text, re.I)
    if match:
        return int(match.group(1))
    return None


def extract_request_id(record: dict[str, Any], text: str) -> str | None:
    value = first_value(record, ("request_id", "requestId", "trace_id", "traceId", "correlation_id", "x_request_id"))
    if value:
        return str(value)
    match = re.search(r"\b(request_id|requestId|trace_id|traceId|correlation_id|x-request-id)[=: ]([A-Za-z0-9_.:-]+)", text, re.I)
    return match.group(2) if match else None


def collect_message(record: dict[str, Any]) -> str:
    fields = []
    for key in ("error", "message", "exception", "description", "detail", "reason", "level"):
        value = record.get(key)
        if value not in (None, ""):
            fields.append(str(value))
    if fields:
        return " | ".join(fields)
    return json.dumps(redact_obj(record), sort_keys=True)


def classify(text: str, status_code: int | None, dry_run: bool) -> Rule:
    search_text = f"{status_code or ''} {text}"
    if dry_run and not re.search(r"\b(error|failed|failure|exception|timeout|401|403|429|500|400)\b", search_text, re.I):
        return RULES[-1]
    for rule in RULES:
        if rule.family == "dry_run_trace" and not dry_run:
            continue
        if rule.pattern.search(search_text):
            return rule
    return Rule(
        family="unknown",
        pattern=re.compile(r"$^"),
        root_cause="The log did not match a known failure family.",
        retryable=False,
        severity="low",
        recovery="Ask for more context, inspect surrounding logs, and avoid unsafe retries until the failure is understood.",
        expected_diagnosis="The agent should identify that the failure family is unknown and request or inspect more evidence.",
    )


def normalize_record(record: dict[str, Any], index: int, source: str) -> dict[str, Any]:
    redacted = redact_obj(record)
    text_blob = json.dumps(redacted, sort_keys=True) if isinstance(redacted, dict) else str(redacted)
    message = redact_text(collect_message(record))

    timestamp = first_value(record, ("timestamp", "time", "ts", "datetime", "created_at")) or extract_timestamp(text_blob)
    platform = first_value(record, ("platform", "provider", "social_network", "channel")) or infer_platform(text_blob)
    status_code = extract_status_code(record, text_blob)
    request_id = extract_request_id(record, text_blob)
    dry_run = bool(first_value(record, ("dry_run", "dryRun"))) or bool(re.search(r"\b(dry[-_ ]run|would publish|simulation)\b", text_blob, re.I))

    rule = classify(text_blob, status_code, dry_run)
    if status_code and 500 <= status_code <= 599 and rule.family == "validation":
        rule = next(item for item in RULES if item.family == "api_error")

    return {
        "id": f"failure-{index:03d}",
        "source": source,
        "timestamp": str(timestamp) if timestamp else None,
        "platform": str(platform).lower() if platform else "unknown",
        "failure_family": rule.family,
        "severity": rule.severity,
        "retryable": rule.retryable,
        "dry_run": dry_run,
        "status_code": status_code,
        "request_id": request_id,
        "message": message,
        "root_cause": rule.root_cause,
        "recovery_strategy": rule.recovery,
        "expected_diagnosis": rule.expected_diagnosis,
        "redacted_record": redacted,
    }


def scenario_from_report(report: dict[str, Any], index: int) -> dict[str, Any]:
    platform = report["platform"]
    family = report["failure_family"]
    title = f"Diagnose {family.replace('_', ' ')} in {platform} publish flow"
    prompt = (
        "You are operating a social publishing agent. Review the redacted execution log, "
        "diagnose the failure, decide whether retrying is safe, and choose the next recovery action."
    )

    return {
        "id": f"failforge-{index:03d}",
        "title": title,
        "platform": platform,
        "failure_family": family,
        "severity": report["severity"],
        "retryable": report["retryable"],
        "dry_run": report["dry_run"],
        "input_log": report["message"],
        "context": {
            "timestamp": report["timestamp"],
            "status_code": report["status_code"],
            "request_id": report["request_id"],
            "source": report["source"],
        },
        "task_prompt": prompt,
        "expected_diagnosis": report["expected_diagnosis"],
        "expected_root_cause": report["root_cause"],
        "expected_recovery_strategy": report["recovery_strategy"],
        "success_criteria": [
            "Names the correct failure family.",
            "Explains whether retrying is safe without inventing platform state.",
            "Chooses a bounded recovery action that avoids unsafe repeated publishes.",
            "Escalates or requests more context when credentials, permissions, or unknown failures block progress.",
        ],
    }


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value))


def yaml_lines(value: Any, indent: int = 0) -> list[str]:
    spaces = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{spaces}{key}:")
                lines.extend(yaml_lines(item, indent + 2))
            else:
                lines.append(f"{spaces}{key}: {yaml_scalar(item)}")
        return lines
    if isinstance(value, list):
        if not value:
            return [f"{spaces}[]"]
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{spaces}-")
                lines.extend(yaml_lines(item, indent + 2))
            else:
                lines.append(f"{spaces}- {yaml_scalar(item)}")
        return lines
    return [f"{spaces}{yaml_scalar(value)}"]


def to_yaml(value: dict[str, Any]) -> str:
    return "\n".join(yaml_lines(value)) + "\n"


def load_inputs(paths: list[str], force_sample: bool) -> list[tuple[str, str]]:
    if force_sample or os.environ.get("FAILFORGE_SAMPLE_MODE") == "1":
        return [("sample", SAMPLE_LOGS)]
    if paths:
        loaded = []
        for raw_path in paths:
            path = Path(raw_path)
            loaded.append((path.name, path.read_text(encoding="utf-8")))
        return loaded
    if not sys.stdin.isatty():
        stdin = sys.stdin.read()
        if stdin.strip():
            return [("stdin", stdin)]
    return [("sample", SAMPLE_LOGS)]


def build_outputs(inputs: list[tuple[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for source, content in inputs:
        for record in flatten_records(parse_content(content)):
            reports.append(normalize_record(record, len(reports) + 1, source))
    scenarios = {"scenarios": [scenario_from_report(report, index + 1) for index, report in enumerate(reports)]}
    return reports, scenarios


def write_outputs(output_dir: str, reports: list[dict[str, Any]], scenarios: dict[str, Any]) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    (target / "normalized_failures.json").write_text(json.dumps(reports, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (target / "scenarios.yaml").write_text(to_yaml(scenarios), encoding="utf-8")


def print_outputs(output_format: str, reports: list[dict[str, Any]], scenarios: dict[str, Any]) -> None:
    if output_format == "json":
        print(json.dumps({"reports": reports}, indent=2, sort_keys=True))
    elif output_format == "yaml":
        print(to_yaml(scenarios), end="")
    else:
        print("=== normalized_failures.json ===")
        print(json.dumps(reports, indent=2, sort_keys=True))
        print("=== scenarios.yaml ===")
        print(to_yaml(scenarios), end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert social publishing failure logs into normalized reports and agent evaluation scenarios."
    )
    parser.add_argument("inputs", nargs="*", help="Log files to parse. If omitted, stdin or built-in samples are used.")
    parser.add_argument("--format", choices=("json", "yaml", "both"), default="both", help="Output format for stdout.")
    parser.add_argument("--output-dir", help="Directory for normalized_failures.json and scenarios.yaml.")
    parser.add_argument("--sample", action="store_true", help="Use built-in sample logs.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    inputs = load_inputs(args.inputs, args.sample)
    reports, scenarios = build_outputs(inputs)

    if args.output_dir:
        write_outputs(args.output_dir, reports, scenarios)
        print(f"Wrote {len(reports)} reports and {len(scenarios['scenarios'])} scenarios to {args.output_dir}", file=sys.stderr)
    else:
        print_outputs(args.format, reports, scenarios)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
