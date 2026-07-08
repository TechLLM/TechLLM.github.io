#!/usr/bin/env python3
"""FaultLoom reference CLI for building API failure benchmark YAML.

The implementation is deliberately dependency-free and deterministic. It
classifies social publishing API failures with simple rules, redacts common
secret-like fields, and emits benchmark-ready YAML for LLM-agent evaluations.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional


VERSION = "0.1"
GENERATOR = "faultloom-minimal-rule-engine"

SENSITIVE_KEYS = {
    "access_token",
    "token",
    "refresh_token",
    "client_secret",
    "app_secret",
    "authorization",
    "password",
    "secret",
}

IDENTIFIER_KEYS = {
    "account_id",
    "user_id",
    "page_id",
    "instagram_business_account",
    "ig_user_id",
    "fb_user_id",
}

SAMPLE_PAYLOAD: Dict[str, Any] = {
    "suite_name": "social-publishing-failures-demo",
    "events": [
        {
            "id": "auth-token-expired",
            "provider": "threads",
            "operation": "publish_text_post",
            "status_code": 401,
            "raw_error": {
                "access_token": "EAAB_SAMPLE_TOKEN",
                "error": {
                    "type": "OAuthException",
                    "code": 190,
                    "message": "Invalid OAuth access token",
                },
            },
        },
        {
            "id": "instagram-rate-limit",
            "provider": "instagram",
            "operation": "publish_media",
            "status_code": 429,
            "raw_error": "Rate limit exceeded. Retry after 60 seconds.",
        },
        {
            "id": "facebook-media-invalid",
            "provider": "facebook",
            "operation": "upload_media",
            "status_code": 400,
            "raw_error": {
                "error": {
                    "code": 36003,
                    "message": "Image aspect ratio is invalid. Minimum width is 320 pixels.",
                }
            },
        },
    ],
}


CLASSIFICATION_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "authentication": {
        "retryable": False,
        "user_action_required": True,
        "severity": "high",
        "confidence": 0.94,
        "summary": "Stop automatic retry and request credential refresh or reauthorization.",
        "actions": [
            "Mark the publishing attempt failed with an authentication cause.",
            "Ask the user or operator to reconnect the provider account.",
            "Retry only after a new credential is available.",
        ],
        "agent_should": [
            "Preserve the provider error code and status code in the diagnosis.",
            "State that human or operator action is required before retry.",
        ],
        "agent_must_not": [
            "Claim the post content caused the failure without evidence.",
            "Loop retries with the same credential.",
        ],
    },
    "rate_limit": {
        "retryable": True,
        "user_action_required": False,
        "severity": "medium",
        "confidence": 0.92,
        "summary": "Schedule a retry using provider-aware backoff.",
        "actions": [
            "Respect retry-after or rate-limit reset timing when available.",
            "Queue the publish attempt instead of retrying immediately.",
            "Surface a concise delay reason to the user or operator.",
        ],
        "agent_should": [
            "Use bounded exponential backoff or the provider retry-after value.",
            "Avoid changing content or credentials because the error is quota-related.",
        ],
        "agent_must_not": [
            "Retry in a tight loop.",
            "Ask the user to reconnect the account without supporting evidence.",
        ],
    },
    "permission": {
        "retryable": False,
        "user_action_required": True,
        "severity": "high",
        "confidence": 0.9,
        "summary": "Request missing permissions, scopes, or account access before retrying.",
        "actions": [
            "Identify the missing permission or scope when the provider exposes it.",
            "Ask an operator or user to grant access.",
            "Retry only after authorization state changes.",
        ],
        "agent_should": [
            "Distinguish permission denial from expired credentials.",
            "Preserve provider permission details in the remediation plan.",
        ],
        "agent_must_not": [
            "Retry without a permission change.",
            "Tell the user the provider is down without evidence.",
        ],
    },
    "media_validation": {
        "retryable": False,
        "user_action_required": True,
        "severity": "medium",
        "confidence": 0.88,
        "summary": "Request a corrected media asset before retrying.",
        "actions": [
            "Identify the provider media constraint that failed.",
            "Tell the user or upstream system exactly which asset property must change.",
            "Retry only after the asset is transformed or replaced.",
        ],
        "agent_should": [
            "Connect the failure to media validation rather than service availability.",
            "Give a concrete remediation for the invalid media.",
        ],
        "agent_must_not": [
            "Retry the identical upload repeatedly.",
            "Mislabel the failure as authentication or rate limiting.",
        ],
    },
    "transient_outage": {
        "retryable": True,
        "user_action_required": False,
        "severity": "medium",
        "confidence": 0.82,
        "summary": "Retry later with bounded backoff and preserve the failed attempt context.",
        "actions": [
            "Classify the failure as likely temporary.",
            "Retry with bounded backoff and jitter.",
            "Escalate only after retry budget exhaustion.",
        ],
        "agent_should": [
            "Mention service unavailability or network instability as the likely cause.",
            "Keep retries bounded and observable.",
        ],
        "agent_must_not": [
            "Ask for credential reconnection without evidence.",
            "Drop the failed publish request silently.",
        ],
    },
    "policy_block": {
        "retryable": False,
        "user_action_required": True,
        "severity": "critical",
        "confidence": 0.86,
        "summary": "Stop automation and request policy review or content revision.",
        "actions": [
            "Preserve the provider policy signal.",
            "Ask the user or reviewer to inspect the content and policy category.",
            "Retry only with revised content or an approved appeal path.",
        ],
        "agent_should": [
            "Avoid guessing unsupported policy details.",
            "Give a review-first recovery plan.",
        ],
        "agent_must_not": [
            "Bypass the policy block.",
            "Automatically repost the same content.",
        ],
    },
    "unknown_failure": {
        "retryable": False,
        "user_action_required": False,
        "severity": "low",
        "confidence": 0.35,
        "summary": "Preserve the raw signal and route for human or rule review.",
        "actions": [
            "Capture provider, operation, status code, and redacted error text.",
            "Avoid confident causal claims.",
            "Add a local classification rule if this failure repeats.",
        ],
        "agent_should": [
            "State uncertainty clearly.",
            "Recommend collecting more provider context.",
        ],
        "agent_must_not": [
            "Invent a cause not supported by the error.",
            "Retry automatically without a retryability signal.",
        ],
    },
}


def read_optional_config() -> Dict[str, bool]:
    """Read optional extension configuration without exposing secret values."""
    return {"llm_labeler_key_present": bool(os.environ.get("FAULTLOOM_LLM_LABELER_KEY"))}


def redact_text(text: str) -> str:
    """Redact common tokens, bearer credentials, and identifier assignments."""
    redacted = re.sub(
        r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+",
        "Bearer [REDACTED]",
        text,
    )
    redacted = re.sub(
        r"(?i)\b(access_token|refresh_token|client_secret|app_secret|token|authorization)"
        r"\s*[:=]\s*['\"]?[^'\"\s,}]+",
        lambda match: f'{match.group(1)}="[REDACTED]"',
        redacted,
    )
    redacted = re.sub(
        r"(?i)\b(account_id|user_id|page_id|ig_user_id|fb_user_id)"
        r"\s*[:=]\s*['\"]?[^'\"\s,}]+",
        lambda match: f'{match.group(1)}="[REDACTED_ID]"',
        redacted,
    )
    return redacted


def redact_value(value: Any) -> Any:
    """Recursively redact sensitive fields from JSON-like values."""
    if isinstance(value, Mapping):
        cleaned: Dict[str, Any] = {}
        for key, nested in value.items():
            lowered = str(key).lower()
            if lowered in SENSITIVE_KEYS:
                cleaned[str(key)] = "[REDACTED]"
            elif lowered in IDENTIFIER_KEYS:
                cleaned[str(key)] = "[REDACTED_ID]"
            else:
                cleaned[str(key)] = redact_value(nested)
        return cleaned
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def stringify_error(raw_error: Any) -> str:
    """Return a compact, redacted string representation of a raw error value."""
    redacted = redact_value(raw_error)
    if isinstance(redacted, (dict, list)):
        return json.dumps(redacted, sort_keys=True, separators=(",", ":"))
    if redacted is None:
        return ""
    return str(redacted)


def normalize_events(payload: Any) -> tuple[str, List[Dict[str, Any]]]:
    """Normalize supported input payloads into a suite name and event list."""
    if isinstance(payload, list):
        suite_name = "faultloom-benchmark"
        events = payload
    elif isinstance(payload, Mapping):
        suite_name = str(payload.get("suite_name") or "faultloom-benchmark")
        events = payload.get("events")
    else:
        raise ValueError("input must be a JSON array or an object with an 'events' array")

    if not isinstance(events, list):
        raise ValueError("input field 'events' must be an array")

    normalized: List[Dict[str, Any]] = []
    for index, event in enumerate(events, start=1):
        if not isinstance(event, Mapping):
            raise ValueError(f"event #{index} must be a JSON object")
        normalized.append(dict(event))
    return suite_name, normalized


def classify_failure(event: Mapping[str, Any]) -> str:
    """Classify a failure event into the FaultLoom portable taxonomy."""
    status_code = event.get("status_code")
    raw_text = stringify_error(event.get("raw_error", event)).lower()

    if status_code == 401 or any(term in raw_text for term in ("oauth", "access token", "expired token", "invalid token")):
        return "authentication"
    if status_code == 429 or any(term in raw_text for term in ("rate limit", "too many requests", "throttle", "quota exceeded")):
        return "rate_limit"
    if status_code == 403 or any(term in raw_text for term in ("missing scope", "permission", "not authorized", "insufficient access")):
        return "permission"
    if any(term in raw_text for term in ("community standards", "policy", "copyright", "content blocked", "violates")):
        return "policy_block"
    if any(term in raw_text for term in ("aspect ratio", "media", "image", "video", "codec", "resolution", "file size", "minimum width")):
        return "media_validation"
    if isinstance(status_code, int) and status_code >= 500:
        return "transient_outage"
    if any(term in raw_text for term in ("timeout", "temporarily unavailable", "service unavailable", "econnreset", "network")):
        return "transient_outage"
    return "unknown_failure"


def build_case(event: Mapping[str, Any], index: int) -> Dict[str, Any]:
    """Build one benchmark case from a normalized failure event."""
    category = classify_failure(event)
    template = CLASSIFICATION_TEMPLATES[category]
    status_code = event.get("status_code")
    if status_code is not None and not isinstance(status_code, int):
        raise ValueError(f"event #{index} field 'status_code' must be an integer when present")

    case_id = str(event.get("id") or f"case-{index:03d}")
    provider = str(event.get("provider") or "unknown_provider")
    operation = str(event.get("operation") or "unknown_operation")
    error_excerpt = stringify_error(event.get("raw_error", event))[:500]

    return {
        "id": case_id,
        "provider": provider,
        "operation": operation,
        "source": {
            "status_code": status_code,
            "error_excerpt": error_excerpt,
        },
        "classification": {
            "category": category,
            "retryable": template["retryable"],
            "user_action_required": template["user_action_required"],
            "severity": template["severity"],
            "confidence": template["confidence"],
        },
        "expected_recovery": {
            "summary": template["summary"],
            "actions": list(template["actions"]),
        },
        "evaluation": {
            "should_retry": template["retryable"],
            "agent_should": list(template["agent_should"]),
            "agent_must_not": list(template["agent_must_not"]),
        },
    }


def build_benchmark(payload: Any) -> Dict[str, Any]:
    """Build a complete benchmark suite from supported JSON-like input."""
    read_optional_config()
    suite_name, events = normalize_events(payload)
    cases = [build_case(event, index) for index, event in enumerate(events, start=1)]
    return {
        "benchmark_suite": {
            "name": suite_name,
            "version": VERSION,
            "generated_by": GENERATOR,
            "cases": cases,
        }
    }


def yaml_scalar(value: Any) -> str:
    """Format a Python scalar as a YAML-compatible scalar."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=True)


def to_yaml(value: Any, indent: int = 0) -> str:
    """Emit deterministic YAML for dictionaries, lists, and scalar values."""
    lines: List[str] = []
    space = " " * indent

    if isinstance(value, Mapping):
        for key, nested in value.items():
            if isinstance(nested, (Mapping, list)):
                lines.append(f"{space}{key}:")
                lines.append(to_yaml(nested, indent + 2))
            else:
                lines.append(f"{space}{key}: {yaml_scalar(nested)}")
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, (Mapping, list)):
                lines.append(f"{space}-")
                lines.append(to_yaml(item, indent + 2))
            else:
                lines.append(f"{space}- {yaml_scalar(item)}")
    else:
        lines.append(f"{space}{yaml_scalar(value)}")

    return "\n".join(line for line in lines if line != "")


def load_json_file(path: Path) -> Any:
    """Load JSON from a path and raise clear ValueError messages."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValueError(f"input file not found: {path}") from exc
    except OSError as exc:
        raise ValueError(f"could not read input file {path}: {exc}") from exc

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc


def write_output(path: Path, text: str) -> None:
    """Write CLI output, creating parent directories when needed."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"could not write output file {path}: {exc}") from exc


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments for the FaultLoom CLI."""
    parser = argparse.ArgumentParser(
        description="Build YAML benchmark cases from social publishing API failure logs.",
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        help="JSON file containing an array of failure events or an object with suite_name and events.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Optional YAML output path. Defaults to stdout.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run the built-in sample with no external API key or network access.",
    )
    return parser.parse_args(argv)


def run(argv: Optional[Iterable[str]] = None) -> int:
    """Execute the CLI and return a process exit code."""
    args = parse_args(argv)
    try:
        if args.selftest or args.input is None:
            payload = copy.deepcopy(SAMPLE_PAYLOAD)
        else:
            payload = load_json_file(args.input)

        yaml_text = to_yaml(build_benchmark(payload)) + "\n"
        if args.output:
            write_output(args.output, yaml_text)
        else:
            sys.stdout.write(yaml_text)
        return 0
    except ValueError as exc:
        sys.stderr.write(f"faultloom: error: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(run())
