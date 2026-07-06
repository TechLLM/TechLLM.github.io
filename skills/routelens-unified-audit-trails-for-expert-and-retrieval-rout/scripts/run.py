"""RouteLens route-audit CLI for unified retrieval and expert routing logs.

The script reads JSONL query logs, normalizes common routing fields, and emits
deterministic JSON reports for domain failures, route confusion, expert-subset
quality gaps, and index/model degradation signals.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "routelens.audit.v1"
DEFAULT_SUCCESS_THRESHOLD = 0.7
DEFAULT_OUTPUT_FORMAT = "json"

SAMPLE_RECORDS: list[dict[str, Any]] = [
    {
        "query_id": "q-001",
        "intended_domain": "billing",
        "selected_index": "billing_faq",
        "selected_model_path": "expert:billing-lite",
        "quality_score": 0.91,
        "selected_path_score": 0.88,
        "full_model_score": 0.93,
        "fallback_attempts": [],
        "outcome": "success",
    },
    {
        "query_id": "q-002",
        "intended_domain": "billing",
        "selected_index": "general_docs",
        "selected_model_path": "expert:general-lite",
        "quality_score": 0.52,
        "selected_path_score": 0.50,
        "full_model_score": 0.84,
        "fallback_attempts": [{"reason": "low_similarity", "selected_index": "billing_faq"}],
        "outcome": "failure",
    },
    {
        "query_id": "q-003",
        "intended_domain": "security",
        "selected_index": "security_runbook",
        "selected_model_path": "expert:security-lite",
        "quality_score": 0.86,
        "selected_path_score": 0.82,
        "full_model_score": 0.90,
        "fallback_attempts": [],
        "outcome": "success",
    },
    {
        "query_id": "q-004",
        "intended_domain": "security",
        "selected_index": "security_runbook",
        "selected_model_path": "full-model",
        "quality_score": 0.78,
        "selected_path_score": 0.78,
        "full_model_score": 0.78,
        "fallback_attempts": [{"reason": "expert_low_confidence", "selected_model_path": "full-model"}],
        "outcome": "success",
    },
    {
        "query_id": "q-005",
        "intended_domain": "support",
        "selected_index": "support_kb",
        "selected_model_path": "expert:support-lite",
        "quality_score": 0.64,
        "selected_path_score": 0.62,
        "full_model_score": 0.79,
        "fallback_attempts": [],
        "outcome": "failure",
    },
    {
        "query_id": "q-006",
        "intended_domain": "support",
        "selected_index": "product_docs",
        "selected_model_path": "expert:support-lite",
        "quality_score": 0.58,
        "selected_path_score": 0.56,
        "full_model_score": 0.76,
        "fallback_attempts": [
            {"reason": "retrieval_empty", "selected_index": "support_kb"},
            {"reason": "expert_timeout", "selected_model_path": "full-model"},
        ],
        "outcome": "failure",
    },
]


def first_present(record: dict[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    """Return the first non-empty value from a record for the provided keys."""

    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return value
    return default


def to_float(value: Any, field_name: str) -> float | None:
    """Convert a value to float, raising a clear error when conversion fails."""

    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a number, got {value!r}") from exc


def nested_score(record: dict[str, Any]) -> Any:
    """Return a nested evaluation score if one is present."""

    evaluation = record.get("evaluation")
    if isinstance(evaluation, dict):
        return first_present(evaluation, ["quality_score", "score", "eval_score"])
    return None


def normalize_outcome(record: dict[str, Any], quality_score: float | None, threshold: float) -> str:
    """Normalize an explicit outcome label or derive one from quality score."""

    raw_outcome = first_present(record, ["outcome", "final_outcome", "label", "result"])
    if raw_outcome is not None:
        outcome = str(raw_outcome).strip().lower()
        if outcome in {"success", "pass", "passed", "correct", "ok", "true", "1"}:
            return "success"
        if outcome in {"failure", "fail", "failed", "incorrect", "error", "false", "0"}:
            return "failure"
        raise ValueError(
            "outcome must be one of success/pass/correct or failure/fail/incorrect; "
            f"got {raw_outcome!r}"
        )
    if quality_score is None:
        raise ValueError("record needs outcome or quality_score to determine success")
    return "success" if quality_score >= threshold else "failure"


def has_fallback(record: dict[str, Any]) -> bool:
    """Return whether a record indicates at least one fallback attempt."""

    attempts = record.get("fallback_attempts")
    if isinstance(attempts, list) and attempts:
        return True
    fallback_count = record.get("fallback_count")
    if isinstance(fallback_count, int) and fallback_count > 0:
        return True
    return bool(record.get("fallback_used"))


def normalize_record(record: dict[str, Any], threshold: float) -> dict[str, Any]:
    """Normalize a raw log record into the RouteLens audit schema."""

    if not isinstance(record, dict):
        raise ValueError("each JSONL line must be a JSON object")

    quality_raw = first_present(record, ["quality_score", "evaluation_score", "eval_score"], nested_score(record))
    quality_score = to_float(quality_raw, "quality_score")
    selected_path_score = to_float(
        first_present(record, ["selected_path_score", "subset_score", "model_score"]),
        "selected_path_score",
    )
    full_model_score = to_float(first_present(record, ["full_model_score", "baseline_score"]), "full_model_score")

    outcome = normalize_outcome(record, quality_score, threshold)

    return {
        "query_id": str(first_present(record, ["query_id", "id"], "")),
        "intended_domain": str(first_present(record, ["intended_domain", "domain", "query_domain"], "unknown")),
        "selected_index": str(first_present(record, ["selected_index", "retrieval_index", "index"], "unknown")),
        "selected_model_path": str(
            first_present(
                record,
                ["selected_model_path", "selected_expert_path", "expert_path", "model_path"],
                "unknown",
            )
        ),
        "quality_score": quality_score,
        "selected_path_score": selected_path_score,
        "full_model_score": full_model_score,
        "fallback_used": has_fallback(record),
        "outcome": outcome,
    }


def average(values: Iterable[float]) -> float:
    """Return a rounded average for a sequence, or 0.0 for an empty sequence."""

    collected = list(values)
    if not collected:
        return 0.0
    return round(sum(collected) / len(collected), 4)


def failure_rate(records: list[dict[str, Any]]) -> float:
    """Return the rounded failure rate for normalized records."""

    if not records:
        return 0.0
    failures = sum(1 for record in records if record["outcome"] == "failure")
    return round(failures / len(records), 4)


def audit_records(records: Iterable[dict[str, Any]], threshold: float = DEFAULT_SUCCESS_THRESHOLD) -> dict[str, Any]:
    """Analyze routing records and return a deterministic RouteLens report."""

    normalized = [normalize_record(record, threshold) for record in records]
    if not normalized:
        raise ValueError("no records found; provide at least one JSONL object")

    successes = sum(1 for record in normalized if record["outcome"] == "success")
    failures = len(normalized) - successes
    quality_scores = [record["quality_score"] for record in normalized if record["quality_score"] is not None]
    gaps = [
        record["full_model_score"] - record["selected_path_score"]
        for record in normalized
        if record["full_model_score"] is not None and record["selected_path_score"] is not None
    ]

    by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
    confusion_counts: dict[tuple[str, str, str, str], int] = defaultdict(int)
    by_model_path: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_index_model: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for record in normalized:
        by_domain[record["intended_domain"]].append(record)
        confusion_key = (
            record["intended_domain"],
            record["selected_index"],
            record["selected_model_path"],
            record["outcome"],
        )
        confusion_counts[confusion_key] += 1
        by_model_path[record["selected_model_path"]].append(record)
        by_index_model[(record["selected_index"], record["selected_model_path"])].append(record)

    domain_failure_rates = []
    for domain, domain_records in by_domain.items():
        domain_failures = sum(1 for record in domain_records if record["outcome"] == "failure")
        fallback_used = sum(1 for record in domain_records if record["fallback_used"])
        fallback_on_failures = sum(
            1 for record in domain_records if record["outcome"] == "failure" and record["fallback_used"]
        )
        domain_failure_rates.append(
            {
                "domain": domain,
                "total": len(domain_records),
                "failures": domain_failures,
                "failure_rate": round(domain_failures / len(domain_records), 4),
                "fallback_used": fallback_used,
                "fallback_coverage": round(fallback_on_failures / domain_failures, 4) if domain_failures else 0.0,
            }
        )
    domain_failure_rates.sort(key=lambda item: (-item["failure_rate"], item["domain"]))

    routing_confusion_matrix = [
        {
            "intended_domain": intended_domain,
            "selected_index": selected_index,
            "selected_model_path": selected_model_path,
            "outcome": outcome,
            "count": count,
        }
        for (intended_domain, selected_index, selected_model_path, outcome), count in sorted(confusion_counts.items())
    ]

    subset_vs_full_model_gaps = []
    for model_path, path_records in by_model_path.items():
        paired = [
            record
            for record in path_records
            if record["full_model_score"] is not None and record["selected_path_score"] is not None
        ]
        if not paired:
            continue
        subset_vs_full_model_gaps.append(
            {
                "selected_model_path": model_path,
                "samples": len(paired),
                "average_full_model_score": average(record["full_model_score"] for record in paired),
                "average_selected_path_score": average(record["selected_path_score"] for record in paired),
                "average_gap": average(
                    record["full_model_score"] - record["selected_path_score"] for record in paired
                ),
            }
        )
    subset_vs_full_model_gaps.sort(key=lambda item: (-item["average_gap"], item["selected_model_path"]))

    index_model_quality = []
    degradation_reports = []
    for (selected_index, selected_model_path), combo_records in by_index_model.items():
        combo_quality = average(
            record["quality_score"] for record in combo_records if record["quality_score"] is not None
        )
        combo_failure_rate = failure_rate(combo_records)
        degradation_flag = combo_quality < threshold or combo_failure_rate > 0.25
        item = {
            "selected_index": selected_index,
            "selected_model_path": selected_model_path,
            "queries": len(combo_records),
            "average_quality_score": combo_quality,
            "failure_rate": combo_failure_rate,
            "degradation_flag": degradation_flag,
        }
        index_model_quality.append(item)
        if degradation_flag:
            reasons = []
            if combo_quality < threshold:
                reasons.append("average quality below threshold")
            if combo_failure_rate > 0.25:
                reasons.append("failure rate above 25%")
            degradation_reports.append({**item, "reason": "; ".join(reasons)})

    index_model_quality.sort(key=lambda item: (item["selected_index"], item["selected_model_path"]))
    degradation_reports.sort(
        key=lambda item: (item["average_quality_score"], -item["failure_rate"], item["selected_index"])
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "summary": {
            "total_queries": len(normalized),
            "successes": successes,
            "failures": failures,
            "fallback_used": sum(1 for record in normalized if record["fallback_used"]),
            "average_quality_score": average(quality_scores),
            "average_subset_quality_gap": average(gaps),
        },
        "domain_failure_rates": domain_failure_rates,
        "routing_confusion_matrix": routing_confusion_matrix,
        "subset_vs_full_model_gaps": subset_vs_full_model_gaps,
        "index_model_quality": index_model_quality,
        "degradation_reports": degradation_reports,
    }


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load JSONL records from a path with line-numbered error messages."""

    if not path.exists():
        raise ValueError(f"input file not found: {path}")
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON on line {line_number}: {exc.msg}") from exc
    return records


def env_float(name: str, default: float) -> float:
    """Read a float environment variable or return a default."""

    raw = os.environ.get(name)
    if raw in (None, ""):
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number, got {raw!r}") from exc


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the route-audit CLI."""

    default_threshold = env_float("ROUTELENS_SUCCESS_THRESHOLD", DEFAULT_SUCCESS_THRESHOLD)
    default_format = os.environ.get("ROUTELENS_OUTPUT_FORMAT", DEFAULT_OUTPUT_FORMAT).strip().lower()
    if default_format != "json":
        raise ValueError("ROUTELENS_OUTPUT_FORMAT currently supports only 'json'")

    parser = argparse.ArgumentParser(
        prog="route-audit",
        description="Audit JSONL logs for unified retrieval-index and expert/model-path routing decisions.",
    )
    parser.add_argument("--input", type=Path, help="Path to a JSONL routing log file.")
    parser.add_argument("--output", type=Path, help="Optional path to write the JSON audit report.")
    parser.add_argument(
        "--threshold",
        type=float,
        default=default_threshold,
        help="Quality score threshold used when deriving outcomes. Defaults to 0.7 or ROUTELENS_SUCCESS_THRESHOLD.",
    )
    parser.add_argument(
        "--format",
        choices=["json"],
        default=default_format,
        help="Output format. Only deterministic JSON is currently supported.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run the built-in sample audit without reading input files.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""

    try:
        args = parse_args(argv)
        if not 0 <= args.threshold <= 1:
            raise ValueError("--threshold must be between 0 and 1")

        if args.selftest or args.input is None:
            records = SAMPLE_RECORDS
        else:
            records = load_jsonl(args.input)

        report = audit_records(records, threshold=args.threshold)
        output = json.dumps(report, indent=2, sort_keys=False) + "\n"
        if args.output:
            args.output.write_text(output, encoding="utf-8")
        else:
            sys.stdout.write(output)
        return 0
    except ValueError as exc:
        sys.stderr.write(f"route-audit error: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
