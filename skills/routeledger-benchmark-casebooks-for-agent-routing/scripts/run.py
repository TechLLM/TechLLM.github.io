#!/usr/bin/env python3
"""RouteLedger benchmark casebook builder.

This script converts JSONL agent-routing logs into deterministic benchmark
casebooks with stratified train, validation, and test splits.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


VERSION = "0.1.0"
DEFAULT_RATIOS = (0.6, 0.2, 0.2)
REQUIRED_FIELDS = ("task", "modality", "domain", "selected_tool", "task_type")
STRATIFY_FIELDS = ("modality", "domain", "selected_tool", "task_type", "outcome")
OUTCOME_SUCCESS_VALUES = {"success", "succeeded", "pass", "passed", "ok", "true"}
OUTCOME_FAILURE_VALUES = {"failure", "failed", "fail", "error", "false"}


SAMPLE_RECORDS: List[Dict[str, Any]] = [
    {
        "id": "rl-001",
        "task": "Summarize a support ticket and choose the reply workflow.",
        "modality": "text",
        "domain": "support",
        "selected_tool": "ticket_summarizer",
        "task_type": "summarization",
        "outcome": "success",
    },
    {
        "id": "rl-002",
        "task": "Summarize a refund conversation before escalation.",
        "modality": "text",
        "domain": "support",
        "selected_tool": "ticket_summarizer",
        "task_type": "summarization",
        "outcome": "success",
    },
    {
        "id": "rl-003",
        "task": "Extract invoice fields from a scanned receipt.",
        "modality": "image",
        "domain": "finance",
        "selected_tool": "ocr_invoice",
        "task_type": "extraction",
        "outcome": "success",
    },
    {
        "id": "rl-004",
        "task": "Route a noisy invoice photo to the extraction path.",
        "modality": "image",
        "domain": "finance",
        "selected_tool": "ocr_invoice",
        "task_type": "extraction",
        "outcome": "failure",
    },
    {
        "id": "rl-005",
        "task": "Classify a sales call transcript for CRM update.",
        "modality": "audio",
        "domain": "sales",
        "selected_tool": "call_classifier",
        "task_type": "classification",
        "outcome": "success",
    },
    {
        "id": "rl-006",
        "task": "Classify a churn-risk call and select next action.",
        "modality": "audio",
        "domain": "sales",
        "selected_tool": "call_classifier",
        "task_type": "classification",
        "outcome": "failure",
    },
]


class RouteLedgerError(ValueError):
    """Raised for user-correctable RouteLedger input errors."""


def normalize_token(value: Any) -> str:
    """Return a stable lowercase token for categorical metadata."""
    return str(value).strip().lower().replace(" ", "_")


def normalize_outcome(record: Dict[str, Any]) -> Tuple[Optional[str], List[str]]:
    """Infer normalized success or failure outcome and collect validation errors."""
    errors: List[str] = []
    outcome_raw = record.get("outcome")
    success_raw = record.get("success")
    outcome: Optional[str] = None

    if outcome_raw is not None and str(outcome_raw).strip():
        token = normalize_token(outcome_raw)
        if token in OUTCOME_SUCCESS_VALUES:
            outcome = "success"
        elif token in OUTCOME_FAILURE_VALUES:
            outcome = "failure"
        else:
            errors.append(f"ambiguous outcome {outcome_raw!r}; expected success or failure")

    if success_raw is not None:
        if isinstance(success_raw, bool):
            success_outcome = "success" if success_raw else "failure"
        elif normalize_token(success_raw) in OUTCOME_SUCCESS_VALUES:
            success_outcome = "success"
        elif normalize_token(success_raw) in OUTCOME_FAILURE_VALUES:
            success_outcome = "failure"
        else:
            errors.append(f"ambiguous success value {success_raw!r}; expected boolean-like value")
            success_outcome = None

        if success_outcome is not None:
            if outcome is not None and outcome != success_outcome:
                errors.append("inconsistent outcome and success fields")
            outcome = outcome or success_outcome

    if outcome is None:
        errors.append("missing outcome or success signal")

    return outcome, errors


def validate_record(record: Dict[str, Any], index: int) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Validate and normalize one routing log record."""
    errors: List[str] = []
    if not isinstance(record, dict):
        return None, [f"line {index}: expected a JSON object"]

    normalized: Dict[str, Any] = dict(record)
    record_id = str(record.get("id") or record.get("task_id") or f"record-{index}")
    normalized["id"] = record_id

    for field in REQUIRED_FIELDS:
        value = record.get(field)
        if value is None or not str(value).strip():
            errors.append(f"missing required field {field!r}")
        else:
            normalized[field] = normalize_token(value) if field != "task" else str(value).strip()

    outcome, outcome_errors = normalize_outcome(record)
    errors.extend(outcome_errors)
    if outcome is not None:
        normalized["outcome"] = outcome
        normalized["success"] = outcome == "success"

    if errors:
        return None, errors
    return normalized, []


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Load routing logs from a JSONL file."""
    if not path.exists():
        raise RouteLedgerError(f"input file not found: {path}")
    if not path.is_file():
        raise RouteLedgerError(f"input path is not a file: {path}")

    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise RouteLedgerError(f"invalid JSON on line {line_number}: {exc.msg}") from exc
    if not records:
        raise RouteLedgerError(f"input file has no JSON records: {path}")
    return records


def stable_sort_key(seed: int, record_id: str) -> str:
    """Return a deterministic pseudo-random ordering key for a record id."""
    digest = hashlib.sha256(f"{seed}:{record_id}".encode("utf-8")).hexdigest()
    return digest


def split_counts(size: int, ratios: Sequence[float]) -> Tuple[int, int, int]:
    """Calculate train, validation, and test counts for one stratum."""
    if size <= 0:
        return 0, 0, 0
    if size == 1:
        return 1, 0, 0
    if size == 2:
        return 1, 0, 1

    targets = [size * ratio for ratio in ratios]
    counts = [int(target) for target in targets]
    while sum(counts) < size:
        remainders = [targets[i] - counts[i] for i in range(3)]
        winner = max(range(3), key=lambda i: (remainders[i], ratios[i], -i))
        counts[winner] += 1

    for i, ratio in enumerate(ratios):
        if ratio > 0 and counts[i] == 0:
            donor = max(range(3), key=lambda j: counts[j])
            if counts[donor] > 1:
                counts[donor] -= 1
                counts[i] += 1

    return counts[0], counts[1], counts[2]


def assign_splits(records: List[Dict[str, Any]], seed: int, ratios: Sequence[float]) -> List[Dict[str, Any]]:
    """Assign each validated record to a deterministic stratified split."""
    groups: Dict[Tuple[str, ...], List[Dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = tuple(str(record[field]) for field in STRATIFY_FIELDS)
        groups[key].append(record)

    split_records: List[Dict[str, Any]] = []
    for key in sorted(groups):
        group = sorted(groups[key], key=lambda item: stable_sort_key(seed, str(item["id"])))
        train_n, validation_n, test_n = split_counts(len(group), ratios)
        assignments = (
            ["train"] * train_n
            + ["validation"] * validation_n
            + ["test"] * test_n
        )
        for record, split in zip(group, assignments):
            enriched = dict(record)
            enriched["split"] = split
            enriched["route_slice"] = {
                "modality": record["modality"],
                "domain": record["domain"],
                "selected_tool": record["selected_tool"],
                "task_type": record["task_type"],
                "outcome": record["outcome"],
            }
            split_records.append(enriched)

    return sorted(split_records, key=lambda item: (item["split"], str(item["id"])))


def counter_to_dict(counter: Counter) -> Dict[str, int]:
    """Return a sorted regular dict from a Counter."""
    return {key: counter[key] for key in sorted(counter)}


def build_coverage(records: List[Dict[str, Any]], min_slice_size: int) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Build coverage counts and weak-slice warnings for casebook records."""
    coverage: Dict[str, Any] = {}
    weak_slices: List[Dict[str, Any]] = []

    for field in ("split", *STRATIFY_FIELDS):
        coverage[field] = counter_to_dict(Counter(str(record[field]) for record in records))

    strata_counter = Counter(
        " | ".join(str(record[field]) for field in STRATIFY_FIELDS) for record in records
    )
    coverage["strata"] = counter_to_dict(strata_counter)

    for field in ("domain", "modality", "selected_tool", "task_type", "outcome"):
        for value, count in coverage[field].items():
            if count < min_slice_size:
                weak_slices.append({"field": field, "value": value, "count": count})

    return coverage, weak_slices


def validate_ratios(ratios: Sequence[float]) -> Tuple[float, float, float]:
    """Validate split ratios and normalize tiny floating-point drift."""
    if len(ratios) != 3:
        raise RouteLedgerError("split ratios must include train, validation, and test values")
    if any(ratio < 0 for ratio in ratios):
        raise RouteLedgerError("split ratios must be non-negative")
    total = sum(ratios)
    if total <= 0:
        raise RouteLedgerError("at least one split ratio must be greater than zero")
    return tuple(ratio / total for ratio in ratios)  # type: ignore[return-value]


def parse_ratios(value: str) -> Tuple[float, float, float]:
    """Parse a comma-separated train,validation,test ratio string."""
    try:
        parts = tuple(float(part.strip()) for part in value.split(","))
    except ValueError as exc:
        raise RouteLedgerError("split ratios must be numbers like 0.6,0.2,0.2") from exc
    return validate_ratios(parts)


def build_casebook(
    raw_records: Iterable[Dict[str, Any]],
    *,
    seed: int = 13,
    ratios: Sequence[float] = DEFAULT_RATIOS,
    min_slice_size: int = 2,
    strict: bool = False,
) -> Dict[str, Any]:
    """Build a benchmark casebook manifest from routing records."""
    normalized_ratios = validate_ratios(ratios)
    valid_records: List[Dict[str, Any]] = []
    validation_errors: List[Dict[str, Any]] = []
    raw_list = list(raw_records)

    for index, record in enumerate(raw_list, start=1):
        normalized, errors = validate_record(record, index)
        if errors:
            validation_errors.append(
                {
                    "line": index,
                    "id": record.get("id") if isinstance(record, dict) else None,
                    "errors": errors,
                }
            )
        if normalized is not None:
            valid_records.append(normalized)

    if strict and validation_errors:
        raise RouteLedgerError(f"schema validation failed for {len(validation_errors)} record(s)")
    if not valid_records:
        raise RouteLedgerError("no valid routing records were available after validation")

    split_records = assign_splits(valid_records, seed, normalized_ratios)
    coverage, weak_slices = build_coverage(split_records, min_slice_size)

    split_ids: Dict[str, List[str]] = {"train": [], "validation": [], "test": []}
    for record in split_records:
        split_ids[record["split"]].append(str(record["id"]))

    return {
        "tool": "RouteLedger",
        "version": VERSION,
        "seed": seed,
        "ratios": {
            "train": normalized_ratios[0],
            "validation": normalized_ratios[1],
            "test": normalized_ratios[2],
        },
        "record_count": len(raw_list),
        "valid_record_count": len(valid_records),
        "invalid_record_count": len(validation_errors),
        "splits": split_ids,
        "coverage": coverage,
        "weak_slices": weak_slices,
        "validation_errors": validation_errors,
        "cases": split_records,
    }


def manifest_summary(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Return a compact deterministic summary for terminal output."""
    return {
        "tool": manifest["tool"],
        "version": manifest["version"],
        "seed": manifest["seed"],
        "record_count": manifest["record_count"],
        "valid_record_count": manifest["valid_record_count"],
        "invalid_record_count": manifest["invalid_record_count"],
        "splits": manifest["splits"],
        "weak_slices": manifest["weak_slices"],
    }


def write_jsonl(path: Path, records: List[Dict[str, Any]]) -> None:
    """Write records to a JSONL file."""
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def write_csv(path: Path, records: List[Dict[str, Any]]) -> None:
    """Write records to a CSV file."""
    fields = ["id", "split", "task", "modality", "domain", "selected_tool", "task_type", "outcome", "success"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def write_markdown(path: Path, manifest: Dict[str, Any]) -> None:
    """Write a compact Markdown coverage summary."""
    lines = [
        "# RouteLedger Casebook Summary",
        "",
        f"- Version: {manifest['version']}",
        f"- Seed: {manifest['seed']}",
        f"- Records: {manifest['valid_record_count']} valid / {manifest['record_count']} total",
        f"- Invalid records: {manifest['invalid_record_count']}",
        "",
        "## Splits",
        "",
    ]
    for split in ("train", "validation", "test"):
        ids = manifest["splits"][split]
        lines.append(f"- {split}: {len(ids)} ({', '.join(ids) if ids else 'none'})")

    lines.extend(["", "## Coverage", ""])
    for field in ("modality", "domain", "selected_tool", "task_type", "outcome"):
        entries = ", ".join(f"{key}={value}" for key, value in manifest["coverage"][field].items())
        lines.append(f"- {field}: {entries}")

    lines.extend(["", "## Weak Slices", ""])
    if manifest["weak_slices"]:
        for weak in manifest["weak_slices"]:
            lines.append(f"- {weak['field']}={weak['value']} count={weak['count']}")
    else:
        lines.append("- none")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_outputs(output_dir: Path, manifest: Dict[str, Any]) -> Dict[str, str]:
    """Write manifest, case records, CSV, and Markdown files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    cases_jsonl_path = output_dir / "cases.jsonl"
    cases_csv_path = output_dir / "cases.csv"
    summary_path = output_dir / "summary.md"

    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_jsonl(cases_jsonl_path, manifest["cases"])
    write_csv(cases_csv_path, manifest["cases"])
    write_markdown(summary_path, manifest)

    return {
        "manifest": str(manifest_path),
        "cases_jsonl": str(cases_jsonl_path),
        "cases_csv": str(cases_csv_path),
        "summary_markdown": str(summary_path),
    }


def default_seed_from_env() -> int:
    """Read the default seed from ROUTELEDGER_SEED, falling back to 13."""
    value = os.environ.get("ROUTELEDGER_SEED", "13")
    try:
        return int(value)
    except ValueError as exc:
        raise RouteLedgerError("ROUTELEDGER_SEED must be an integer") from exc


def default_ratios_from_env() -> Tuple[float, float, float]:
    """Read default split ratios from ROUTELEDGER_SPLIT_RATIOS."""
    value = os.environ.get("ROUTELEDGER_SPLIT_RATIOS")
    if not value:
        return DEFAULT_RATIOS
    return parse_ratios(value)


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    """Run the command-line interface."""
    parser = argparse.ArgumentParser(
        description="Build deterministic RouteLedger benchmark casebooks from routing-log JSONL."
    )
    parser.add_argument("--input", help="Path to a JSONL routing log file.")
    parser.add_argument("--output-dir", help="Directory for manifest.json, cases.jsonl, cases.csv, and summary.md.")
    parser.add_argument("--seed", type=int, default=None, help="Deterministic split seed. Defaults to ROUTELEDGER_SEED or 13.")
    parser.add_argument(
        "--ratios",
        default=None,
        help="Comma-separated train,validation,test ratios. Defaults to ROUTELEDGER_SPLIT_RATIOS or 0.6,0.2,0.2.",
    )
    parser.add_argument("--min-slice-size", type=int, default=2, help="Coverage count below this threshold is reported as weak.")
    parser.add_argument("--strict", action="store_true", help="Fail if any input record has schema errors.")
    parser.add_argument("--selftest", action="store_true", help="Run on built-in sample data without API keys or files.")
    parser.add_argument("--full", action="store_true", help="Print the full manifest instead of the compact summary.")
    args = parser.parse_args(argv)

    try:
        seed = args.seed if args.seed is not None else default_seed_from_env()
        ratios = parse_ratios(args.ratios) if args.ratios else default_ratios_from_env()
        if args.min_slice_size < 1:
            raise RouteLedgerError("--min-slice-size must be at least 1")

        if args.selftest or not args.input:
            records = SAMPLE_RECORDS
        else:
            records = load_jsonl(Path(args.input))

        manifest = build_casebook(
            records,
            seed=seed,
            ratios=ratios,
            min_slice_size=args.min_slice_size,
            strict=args.strict,
        )

        if args.output_dir:
            manifest["files"] = write_outputs(Path(args.output_dir), manifest)

        payload = manifest if args.full else manifest_summary(manifest)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    except RouteLedgerError as exc:
        print(f"RouteLedger error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(run_cli())
