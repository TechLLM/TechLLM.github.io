#!/usr/bin/env python3
"""Failwise: tune LLM agent budgets against worst-case failure slices."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


SAMPLE_LOGS = [
    {
        "id": "sample-001",
        "task_type": "qa",
        "success": True,
        "tokens_used": 1700,
        "input_tokens": 900,
        "output_tokens": 400,
        "retrieval_depth_used": 1,
        "tool_retries_used": 0,
        "latency_ms": 2300,
        "retrieval_confidence": 0.86,
        "tool_name": "search",
        "model": "agent-small",
        "metadata": {"workflow": "stable"},
    },
    {
        "id": "sample-002",
        "task_type": "qa",
        "success": False,
        "tokens_used": 3900,
        "input_tokens": 2500,
        "output_tokens": 900,
        "retrieval_depth_used": 3,
        "tool_retries_used": 1,
        "latency_ms": 5600,
        "retrieval_confidence": 0.38,
        "tool_name": "search",
        "model": "agent-small",
        "metadata": {"workflow": "flaky"},
    },
    {
        "id": "sample-003",
        "task_type": "code",
        "success": True,
        "tokens_used": 6500,
        "input_tokens": 4100,
        "output_tokens": 1500,
        "retrieval_depth_used": 4,
        "tool_retries_used": 2,
        "latency_ms": 9300,
        "retrieval_confidence": 0.71,
        "tool_name": "shell",
        "model": "agent-medium",
        "metadata": {"workflow": "tool-heavy"},
    },
    {
        "id": "sample-004",
        "task_type": "research",
        "success": False,
        "tokens_used": 9800,
        "input_tokens": 8000,
        "output_tokens": 1300,
        "retrieval_depth_used": 6,
        "tool_retries_used": 2,
        "latency_ms": 16100,
        "retrieval_confidence": 0.31,
        "tool_name": "browser",
        "model": "agent-large",
        "metadata": {"workflow": "long-context"},
    },
    {
        "id": "sample-005",
        "task_type": "support",
        "success": True,
        "tokens_used": 3000,
        "input_tokens": 1500,
        "output_tokens": 700,
        "retrieval_depth_used": 2,
        "tool_retries_used": 1,
        "latency_ms": 4400,
        "retrieval_confidence": 0.78,
        "tool_name": "crm",
        "model": "agent-small",
        "metadata": {"workflow": "stable"},
    },
    {
        "id": "sample-006",
        "task_type": "code",
        "success": False,
        "tokens_used": 8400,
        "input_tokens": 5600,
        "output_tokens": 2200,
        "retrieval_depth_used": 5,
        "tool_retries_used": 3,
        "latency_ms": 13800,
        "retrieval_confidence": 0.49,
        "tool_name": "shell",
        "model": "agent-medium",
        "metadata": {"workflow": "flaky"},
    },
]


SAMPLE_POLICIES = [
    {
        "name": "lean",
        "max_tokens": 3000,
        "retrieval_depth": 2,
        "tool_retries": 1,
        "token_cost_per_1k": 0.002,
        "latency_penalty_ms": 80,
    },
    {
        "name": "balanced",
        "max_tokens": 6000,
        "retrieval_depth": 4,
        "tool_retries": 2,
        "token_cost_per_1k": 0.002,
        "latency_penalty_ms": 160,
    },
    {
        "name": "resilient",
        "max_tokens": 10000,
        "retrieval_depth": 6,
        "tool_retries": 4,
        "token_cost_per_1k": 0.002,
        "latency_penalty_ms": 320,
    },
]


@dataclass(frozen=True)
class Policy:
    name: str
    max_tokens: int
    retrieval_depth: int
    tool_retries: int
    token_cost_per_1k: float = 0.002
    latency_penalty_ms: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rank LLM agent budget policies against worst-case failure slices."
    )
    parser.add_argument("--logs", help="JSONL execution logs. Uses sample logs if omitted.")
    parser.add_argument(
        "--policies",
        help="YAML or JSON policy file. Uses sample policies if omitted.",
    )
    parser.add_argument(
        "--slice-fields",
        nargs="+",
        default=[
            "task_type",
            "tool_name",
            "retrieval_band",
            "context_band",
            "metadata.workflow",
        ],
        help="Fields used to compute worst-slice failure rates.",
    )
    parser.add_argument("--output", help="Write a JSON report to this path.")
    parser.add_argument(
        "--min-slice-size",
        type=int,
        default=1,
        help="Ignore slices with fewer than this many records.",
    )
    return parser.parse_args()


def load_logs(path: str | None) -> list[dict[str, Any]]:
    if not path:
        return list(SAMPLE_LOGS)

    records: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSONL record: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_number}: each JSONL record must be an object")
            records.append(record)
    if not records:
        raise ValueError(f"{path}: no log records found")
    return records


def load_policies(path: str | None) -> list[Policy]:
    raw = SAMPLE_POLICIES if not path else load_policy_file(Path(path))
    policies = [coerce_policy(item, index) for index, item in enumerate(raw, start=1)]
    names = [policy.name for policy in policies]
    if len(names) != len(set(names)):
        raise ValueError("policy names must be unique")
    return policies


def load_policy_file(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        data = parse_simple_yaml(text)

    if isinstance(data, dict) and "policies" in data:
        data = data["policies"]
    if not isinstance(data, list):
        raise ValueError("policy file must contain a top-level policies list")
    return data


def parse_simple_yaml(text: str) -> dict[str, Any]:
    """Parse the small YAML subset used by Failwise policy files."""
    root: dict[str, Any] = {}
    current_key: str | None = None
    current_item: dict[str, Any] | None = None

    for line_number, original in enumerate(text.splitlines(), start=1):
        line = original.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        if not line.startswith(" ") and line.endswith(":"):
            current_key = line[:-1].strip()
            root[current_key] = []
            current_item = None
            continue

        stripped = line.strip()
        if stripped.startswith("- "):
            if current_key is None:
                raise ValueError(f"line {line_number}: list item without parent key")
            current_item = {}
            root[current_key].append(current_item)
            remainder = stripped[2:].strip()
            if remainder:
                key, value = split_key_value(remainder, line_number)
                current_item[key] = parse_scalar(value)
            continue

        if current_item is not None:
            key, value = split_key_value(stripped, line_number)
            current_item[key] = parse_scalar(value)
            continue

        key, value = split_key_value(stripped, line_number)
        root[key] = parse_scalar(value)

    return root


def split_key_value(text: str, line_number: int) -> tuple[str, str]:
    if ":" not in text:
        raise ValueError(f"line {line_number}: expected key: value")
    key, value = text.split(":", 1)
    return key.strip(), value.strip()


def parse_scalar(value: str) -> Any:
    value = value.strip()
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
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def coerce_policy(raw: dict[str, Any], index: int) -> Policy:
    required = ("name", "max_tokens", "retrieval_depth", "tool_retries")
    missing = [key for key in required if key not in raw]
    if missing:
        raise ValueError(f"policy #{index} missing required fields: {', '.join(missing)}")
    return Policy(
        name=str(raw["name"]),
        max_tokens=int(raw["max_tokens"]),
        retrieval_depth=int(raw["retrieval_depth"]),
        tool_retries=int(raw["tool_retries"]),
        token_cost_per_1k=float(raw.get("token_cost_per_1k", 0.002)),
        latency_penalty_ms=int(raw.get("latency_penalty_ms", 0)),
    )


def evaluate_policy(
    policy: Policy,
    logs: list[dict[str, Any]],
    slice_fields: list[str],
    min_slice_size: int,
) -> dict[str, Any]:
    outcomes = [apply_policy(policy, record) for record in logs]
    total = len(outcomes)
    successes = sum(1 for item in outcomes if item["effective_success"])
    estimated_cost = sum(item["estimated_cost"] for item in outcomes)
    estimated_latency = sum(item["estimated_latency_ms"] for item in outcomes) / total
    retry_utilization = (
        sum(float(item["retry_utilization"]) for item in outcomes) / total if total else 0.0
    )
    failure_rate = 1.0 - (successes / total if total else 0.0)
    worst_slices = compute_worst_slices(outcomes, slice_fields, min_slice_size)

    return {
        "name": policy.name,
        "max_tokens": policy.max_tokens,
        "retrieval_depth": policy.retrieval_depth,
        "tool_retries": policy.tool_retries,
        "success_rate": successes / total if total else 0.0,
        "failure_rate": failure_rate,
        "estimated_cost": estimated_cost,
        "avg_latency_ms": estimated_latency,
        "retry_utilization": retry_utilization,
        "worst_slice_failure_rate": worst_slices[0]["failure_rate"] if worst_slices else failure_rate,
        "worst_slices": worst_slices[:5],
        "policy": policy.__dict__,
    }


def apply_policy(policy: Policy, record: dict[str, Any]) -> dict[str, Any]:
    tokens_used = int(record.get("tokens_used", record.get("total_tokens", 0)) or 0)
    retrieval_used = int(record.get("retrieval_depth_used", record.get("retrieval_depth", 0)) or 0)
    retries_used = int(record.get("tool_retries_used", record.get("tool_retries", 0)) or 0)
    base_success = bool(record.get("success", False))

    token_ok = tokens_used <= policy.max_tokens
    retrieval_ok = retrieval_used <= policy.retrieval_depth
    retry_ok = retries_used <= policy.tool_retries
    effective_success = base_success and token_ok and retrieval_ok and retry_ok

    capped_tokens = min(tokens_used, policy.max_tokens)
    estimated_cost = (capped_tokens / 1000.0) * policy.token_cost_per_1k
    estimated_latency = (
        float(record.get("latency_ms", 0) or 0)
        + policy.latency_penalty_ms
        + max(0, policy.retrieval_depth - retrieval_used) * 80
        + max(0, policy.tool_retries - retries_used) * 120
    )
    retry_utilization = retries_used / policy.tool_retries if policy.tool_retries else 0.0

    enriched = dict(record)
    enriched.update(
        {
            "effective_success": effective_success,
            "policy_failure_reasons": failure_reasons(base_success, token_ok, retrieval_ok, retry_ok),
            "estimated_cost": estimated_cost,
            "estimated_latency_ms": estimated_latency,
            "retry_utilization": min(retry_utilization, 1.0),
            "retrieval_band": retrieval_band(float(record.get("retrieval_confidence", 0.0) or 0.0)),
            "context_band": context_band(
                int(record.get("input_tokens", tokens_used) or tokens_used)
            ),
            "model": record.get("model") or os.getenv("FAILWISE_DEFAULT_MODEL", "unknown"),
        }
    )
    return enriched


def failure_reasons(
    base_success: bool,
    token_ok: bool,
    retrieval_ok: bool,
    retry_ok: bool,
) -> list[str]:
    reasons = []
    if not base_success:
        reasons.append("historical_failure")
    if not token_ok:
        reasons.append("token_cap")
    if not retrieval_ok:
        reasons.append("retrieval_depth_cap")
    if not retry_ok:
        reasons.append("retry_cap")
    return reasons


def retrieval_band(confidence: float) -> str:
    if confidence >= 0.75:
        return "high-confidence"
    if confidence >= 0.5:
        return "medium-confidence"
    return "low-confidence"


def context_band(input_tokens: int) -> str:
    if input_tokens >= 6000:
        return "long-context"
    if input_tokens >= 2500:
        return "medium-context"
    return "short-context"


def compute_worst_slices(
    outcomes: Iterable[dict[str, Any]],
    slice_fields: list[str],
    min_slice_size: int,
) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in outcomes:
        for field in slice_fields:
            value = dotted_get(record, field)
            if value is None:
                continue
            buckets[(field, str(value))].append(record)

    slices = []
    for (field, value), records in buckets.items():
        if len(records) < min_slice_size:
            continue
        failures = sum(1 for record in records if not record["effective_success"])
        slices.append(
            {
                "field": field,
                "value": value,
                "count": len(records),
                "failures": failures,
                "failure_rate": failures / len(records),
            }
        )

    return sorted(slices, key=lambda item: (-item["failure_rate"], -item["count"], item["field"]))


def dotted_get(record: dict[str, Any], field: str) -> Any:
    current: Any = record
    for part in field.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def mark_pareto(results: list[dict[str, Any]]) -> None:
    for candidate in results:
        candidate["pareto"] = not any(dominates(other, candidate) for other in results if other is not candidate)


def dominates(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_values = (
        left["success_rate"],
        -left["estimated_cost"],
        -left["avg_latency_ms"],
        -left["worst_slice_failure_rate"],
    )
    right_values = (
        right["success_rate"],
        -right["estimated_cost"],
        -right["avg_latency_ms"],
        -right["worst_slice_failure_rate"],
    )
    return all(a >= b for a, b in zip(left_values, right_values)) and any(
        a > b for a, b in zip(left_values, right_values)
    )


def rank_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        results,
        key=lambda item: (
            not item["pareto"],
            -item["success_rate"],
            item["worst_slice_failure_rate"],
            item["estimated_cost"],
            item["avg_latency_ms"],
        ),
    )


def print_table(results: list[dict[str, Any]]) -> None:
    headers = [
        "rank",
        "policy",
        "pareto",
        "success",
        "worst_fail",
        "cost",
        "avg_latency",
        "retry_use",
    ]
    rows = []
    for index, item in enumerate(results, start=1):
        rows.append(
            [
                str(index),
                item["name"],
                "yes" if item["pareto"] else "no",
                percent(item["success_rate"]),
                percent(item["worst_slice_failure_rate"]),
                f"${item['estimated_cost']:.4f}",
                f"{item['avg_latency_ms']:.0f}ms",
                percent(item["retry_utilization"]),
            ]
        )

    widths = [
        max(len(str(row[column])) for row in [headers, *rows])
        for column in range(len(headers))
    ]
    print("Failwise policy ranking")
    print(format_row(headers, widths))
    print(format_row(["-" * width for width in widths], widths))
    for row in rows:
        print(format_row(row, widths))

    print("\nWorst slices by top policy")
    top = results[0]
    for item in top["worst_slices"][:3]:
        print(
            f"- {item['field']}={item['value']}: "
            f"{percent(item['failure_rate'])} failures "
            f"({item['failures']}/{item['count']})"
        )


def format_row(values: list[str], widths: list[int]) -> str:
    return "  ".join(value.ljust(width) for value, width in zip(values, widths))


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def build_report(
    logs: list[dict[str, Any]],
    policies: list[Policy],
    results: list[dict[str, Any]],
    args: argparse.Namespace,
) -> dict[str, Any]:
    return {
        "tool": "failwise",
        "records_evaluated": len(logs),
        "policies_evaluated": len(policies),
        "slice_fields": args.slice_fields,
        "results": results,
    }


def main() -> int:
    args = parse_args()
    try:
        logs = load_logs(args.logs)
        policies = load_policies(args.policies)
        results = [
            evaluate_policy(policy, logs, args.slice_fields, args.min_slice_size)
            for policy in policies
        ]
        mark_pareto(results)
        ranked = rank_results(results)
        print_table(ranked)

        if args.output:
            report = build_report(logs, policies, ranked, args)
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            print(f"\nWrote JSON report: {output_path}")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"failwise: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
