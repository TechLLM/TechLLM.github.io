#!/usr/bin/env python3
"""Run an offline RelevaLens masking probe over RAG relevance score logs.

The CLI accepts JSONL query, candidate, and score files. It compares baseline
scores with masked scores to estimate entropy, candidate concentration,
position skew, mask sensitivity, and rank instability. It is deterministic and
requires no network access or API key.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

BASELINE_LABELS = {"", "none", "baseline", "unmasked"}

SAMPLE_QUERIES: List[Dict[str, Any]] = [
    {
        "query_id": "q1",
        "text": "How do warranty claims affect revenue recognition?",
    }
]

SAMPLE_CANDIDATES: List[Dict[str, Any]] = [
    {
        "query_id": "q1",
        "candidate_id": "d1",
        "rank": 1,
        "position": 1,
        "fields": {
            "title": "Warranty claims FAQ",
            "body": "Warranty claim claim claim notes with limited revenue context.",
        },
    },
    {
        "query_id": "q1",
        "candidate_id": "d2",
        "rank": 2,
        "position": 2,
        "fields": {
            "title": "Revenue recognition guide",
            "body": "Recognize revenue net of expected warranty liabilities.",
        },
    },
    {
        "query_id": "q1",
        "candidate_id": "d3",
        "rank": 3,
        "position": 3,
        "fields": {
            "title": "Support escalation memo",
            "body": "Customer support escalation notes unrelated to accounting policy.",
        },
    },
]

SAMPLE_SCORES: List[Dict[str, Any]] = [
    {"query_id": "q1", "candidate_id": "d1", "score": 0.92, "mask": "none"},
    {"query_id": "q1", "candidate_id": "d2", "score": 0.71, "mask": "none"},
    {"query_id": "q1", "candidate_id": "d3", "score": 0.20, "mask": "none"},
    {"query_id": "q1", "candidate_id": "d1", "score": 0.38, "mask": "keyword_mask"},
    {"query_id": "q1", "candidate_id": "d2", "score": 0.68, "mask": "keyword_mask"},
    {"query_id": "q1", "candidate_id": "d3", "score": 0.18, "mask": "keyword_mask"},
    {"query_id": "q1", "candidate_id": "d1", "score": 0.64, "mask": "field_mask"},
    {"query_id": "q1", "candidate_id": "d2", "score": 0.40, "mask": "field_mask"},
    {"query_id": "q1", "candidate_id": "d3", "score": 0.16, "mask": "field_mask"},
    {"query_id": "q1", "candidate_id": "d1", "score": 0.52, "mask": "position_mask"},
    {"query_id": "q1", "candidate_id": "d2", "score": 0.75, "mask": "position_mask"},
    {"query_id": "q1", "candidate_id": "d3", "score": 0.18, "mask": "position_mask"},
]


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Read a JSONL file and return a list of object records.

    Raises:
        ValueError: If a line is empty, invalid JSON, or not a JSON object.
    """

    records: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    value = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
                if not isinstance(value, dict):
                    raise ValueError(f"{path}:{line_number}: expected a JSON object")
                records.append(value)
    except OSError as exc:
        raise ValueError(f"could not read {path}: {exc}") from exc
    return records


def write_jsonl(path: Path, records: Iterable[Mapping[str, Any]]) -> None:
    """Write records as newline-delimited JSON with stable key ordering."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, ensure_ascii=True) + "\n")


def mean(values: Sequence[float]) -> float:
    """Return the arithmetic mean, or 0.0 for an empty sequence."""

    if not values:
        return 0.0
    return sum(values) / len(values)


def rounded(value: float) -> float:
    """Round floats to four decimals for deterministic reports."""

    if abs(value) < 0.00005:
        return 0.0
    return round(value, 4)


def numeric_score(record: Mapping[str, Any]) -> float:
    """Extract and validate a numeric score from a score record."""

    value = record.get("score")
    if not isinstance(value, (int, float)):
        raise ValueError(f"score record must contain numeric score: {record}")
    if not math.isfinite(float(value)):
        raise ValueError(f"score must be finite: {record}")
    return float(value)


def mask_label(record: Mapping[str, Any]) -> str:
    """Return the normalized mask label for a score record."""

    value = record.get("mask", record.get("mask_strategy", record.get("strategy", "")))
    return str(value).strip().lower()


def is_baseline_score(record: Mapping[str, Any]) -> bool:
    """Return True if a score record is a baseline or unmasked score."""

    return mask_label(record) in BASELINE_LABELS


def validate_records(
    queries: Sequence[Mapping[str, Any]],
    candidates: Sequence[Mapping[str, Any]],
    scores: Sequence[Mapping[str, Any]],
) -> None:
    """Validate the minimal input contract for RelevaLens records."""

    if not queries:
        raise ValueError("at least one query record is required")
    if not candidates:
        raise ValueError("at least one candidate record is required")
    if not scores:
        raise ValueError("at least one score record is required")

    query_ids = set()
    for record in queries:
        query_id = record.get("query_id")
        if not query_id:
            raise ValueError(f"query record missing query_id: {record}")
        if "text" not in record:
            raise ValueError(f"query record missing text: {record}")
        query_ids.add(str(query_id))

    candidate_keys = set()
    for record in candidates:
        query_id = record.get("query_id")
        candidate_id = record.get("candidate_id")
        if not query_id or not candidate_id:
            raise ValueError(f"candidate record requires query_id and candidate_id: {record}")
        if str(query_id) not in query_ids:
            raise ValueError(f"candidate references unknown query_id {query_id!r}")
        candidate_keys.add((str(query_id), str(candidate_id)))

    baseline_keys = set()
    for record in scores:
        query_id = record.get("query_id")
        candidate_id = record.get("candidate_id")
        if not query_id or not candidate_id:
            raise ValueError(f"score record requires query_id and candidate_id: {record}")
        key = (str(query_id), str(candidate_id))
        if key not in candidate_keys:
            raise ValueError(f"score references unknown candidate {key}")
        numeric_score(record)
        if is_baseline_score(record):
            baseline_keys.add(key)

    missing_baselines = sorted(candidate_keys - baseline_keys)
    if missing_baselines:
        first = missing_baselines[0]
        raise ValueError(f"missing baseline score for candidate {first[1]!r} in query {first[0]!r}")


def candidate_position(record: Mapping[str, Any]) -> int:
    """Return a stable candidate position from position, rank, or a fallback."""

    value = record.get("position", record.get("rank", 0))
    try:
        position = int(value)
    except (TypeError, ValueError):
        position = 0
    return position if position > 0 else 999999


def normalized_entropy(scores: Sequence[float]) -> Tuple[float, List[float]]:
    """Return normalized entropy and score shares for a score vector."""

    nonnegative = [max(0.0, score) for score in scores]
    total = sum(nonnegative)
    if not nonnegative:
        return 0.0, []
    if total <= 0.0:
        shares = [1.0 / len(nonnegative) for _ in nonnegative]
    else:
        shares = [score / total for score in nonnegative]
    entropy = -sum(share * math.log(share, 2) for share in shares if share > 0.0)
    max_entropy = math.log(len(shares), 2) if len(shares) > 1 else 1.0
    return entropy / max_entropy, shares


def pairwise_rank_instability(
    baseline: Mapping[str, float],
    masked_by_strategy: Mapping[str, Mapping[str, Sequence[float]]],
) -> float:
    """Estimate mean pairwise rank flips between baseline and masked scores."""

    candidate_ids = sorted(baseline)
    if len(candidate_ids) < 2:
        return 0.0

    strategy_rates: List[float] = []
    for strategy_scores in masked_by_strategy.values():
        masked = {candidate_id: mean(list(values)) for candidate_id, values in strategy_scores.items()}
        flips = 0
        comparisons = 0
        for left_index, left_id in enumerate(candidate_ids):
            for right_id in candidate_ids[left_index + 1 :]:
                if left_id not in masked or right_id not in masked:
                    continue
                baseline_order = (baseline[left_id] > baseline[right_id]) - (
                    baseline[left_id] < baseline[right_id]
                )
                masked_order = (masked[left_id] > masked[right_id]) - (
                    masked[left_id] < masked[right_id]
                )
                if baseline_order == 0 or masked_order == 0:
                    continue
                comparisons += 1
                if baseline_order != masked_order:
                    flips += 1
        if comparisons:
            strategy_rates.append(flips / comparisons)
    return mean(strategy_rates)


def run_probe(
    queries: Sequence[Mapping[str, Any]],
    candidates: Sequence[Mapping[str, Any]],
    scores: Sequence[Mapping[str, Any]],
    *,
    entropy_threshold: float = 0.72,
    concentration_threshold: float = 0.52,
    position_skew_threshold: float = 0.12,
    low_sensitivity_threshold: float = 0.08,
    rank_instability_threshold: float = 0.20,
) -> Dict[str, Any]:
    """Analyze baseline and masked relevance scores and return report data.

    The returned dictionary contains `summary`, `queries`, and `candidates`
    keys. All numeric metrics are rounded to four decimals for reproducibility.
    """

    validate_records(queries, candidates, scores)

    candidate_by_key: Dict[Tuple[str, str], Mapping[str, Any]] = {}
    candidates_by_query: MutableMapping[str, List[Mapping[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        query_id = str(candidate["query_id"])
        candidate_id = str(candidate["candidate_id"])
        candidate_by_key[(query_id, candidate_id)] = candidate
        candidates_by_query[query_id].append(candidate)

    baseline_scores: MutableMapping[str, MutableMapping[str, List[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    masked_scores: MutableMapping[
        str, MutableMapping[str, MutableMapping[str, List[float]]]
    ] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for record in scores:
        query_id = str(record["query_id"])
        candidate_id = str(record["candidate_id"])
        score = numeric_score(record)
        label = mask_label(record)
        if label in BASELINE_LABELS:
            baseline_scores[query_id][candidate_id].append(score)
        else:
            masked_scores[query_id][label][candidate_id].append(score)

    query_rows: List[Dict[str, Any]] = []
    candidate_rows: List[Dict[str, Any]] = []

    for query_id in sorted(candidates_by_query):
        ordered_candidates = sorted(
            candidates_by_query[query_id],
            key=lambda item: (candidate_position(item), str(item["candidate_id"])),
        )
        candidate_ids = [str(candidate["candidate_id"]) for candidate in ordered_candidates]
        baseline = {
            candidate_id: mean(baseline_scores[query_id][candidate_id])
            for candidate_id in candidate_ids
        }
        baseline_vector = [baseline[candidate_id] for candidate_id in candidate_ids]
        entropy, shares = normalized_entropy(baseline_vector)
        concentration = max(shares) if shares else 0.0

        early_count = max(1, math.ceil(len(candidate_ids) / 3))
        early_ids = set(candidate_ids[:early_count])
        early_share = sum(shares[index] for index, candidate_id in enumerate(candidate_ids) if candidate_id in early_ids)
        position_skew = early_share - (early_count / len(candidate_ids))

        all_masked_by_candidate: MutableMapping[str, List[float]] = defaultdict(list)
        for strategy_scores in masked_scores[query_id].values():
            for candidate_id, values in strategy_scores.items():
                all_masked_by_candidate[candidate_id].extend(values)

        deltas: List[float] = []
        for candidate_id in candidate_ids:
            masked_values = all_masked_by_candidate.get(candidate_id, [])
            masked_mean = mean(masked_values) if masked_values else baseline[candidate_id]
            delta = abs(baseline[candidate_id] - masked_mean)
            deltas.append(delta)
            baseline_rank = sorted(
                candidate_ids,
                key=lambda current_id: (-baseline[current_id], candidate_position(candidate_by_key[(query_id, current_id)]), current_id),
            ).index(candidate_id) + 1
            share = shares[candidate_ids.index(candidate_id)] if shares else 0.0
            candidate_rows.append(
                {
                    "query_id": query_id,
                    "candidate_id": candidate_id,
                    "baseline_rank": baseline_rank,
                    "position": candidate_position(candidate_by_key[(query_id, candidate_id)]),
                    "baseline_score": rounded(baseline[candidate_id]),
                    "masked_mean": rounded(masked_mean),
                    "mask_delta": rounded(delta),
                    "concentration_share": rounded(share),
                }
            )

        mask_sensitivity = mean(deltas)
        rank_instability = pairwise_rank_instability(baseline, masked_scores[query_id])
        flags: List[str] = []
        if entropy < entropy_threshold:
            flags.append("low_entropy")
        if concentration > concentration_threshold:
            flags.append("candidate_concentration")
        if position_skew > position_skew_threshold:
            flags.append("position_skew")
        if mask_sensitivity < low_sensitivity_threshold:
            flags.append("low_mask_sensitivity")
        if rank_instability > rank_instability_threshold:
            flags.append("rank_instability")

        query_rows.append(
            {
                "query_id": query_id,
                "normalized_entropy": rounded(entropy),
                "top1_concentration": rounded(concentration),
                "mask_sensitivity": rounded(mask_sensitivity),
                "rank_instability": rounded(rank_instability),
                "position_skew": rounded(position_skew),
                "flags": flags,
            }
        )

    summary_flags = sorted({flag for row in query_rows for flag in row["flags"]})
    summary = {
        "query_count": len(queries),
        "candidate_count": len(candidates),
        "score_count": len(scores),
        "mean_normalized_entropy": rounded(mean([row["normalized_entropy"] for row in query_rows])),
        "mean_top1_concentration": rounded(mean([row["top1_concentration"] for row in query_rows])),
        "mean_mask_sensitivity": rounded(mean([row["mask_sensitivity"] for row in query_rows])),
        "mean_rank_instability": rounded(mean([row["rank_instability"] for row in query_rows])),
        "mean_position_skew": rounded(mean([row["position_skew"] for row in query_rows])),
        "flags": summary_flags,
    }

    return {"summary": summary, "queries": query_rows, "candidates": candidate_rows}


def format_metric(value: Any) -> str:
    """Format a metric value for Markdown output."""

    if isinstance(value, float):
        return f"{value:.4f}"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "none"
    return str(value)


def render_markdown(result: Mapping[str, Any]) -> str:
    """Render RelevaLens result data as a Markdown report."""

    lines = ["# RelevaLens Report", "", "## Summary"]
    summary_order = [
        "query_count",
        "candidate_count",
        "score_count",
        "mean_normalized_entropy",
        "mean_top1_concentration",
        "mean_mask_sensitivity",
        "mean_rank_instability",
        "mean_position_skew",
        "flags",
    ]
    summary = result["summary"]
    for key in summary_order:
        lines.append(f"- {key}: {format_metric(summary[key])}")

    lines.extend(
        [
            "",
            "## Query Findings",
            "| query_id | normalized_entropy | top1_concentration | mask_sensitivity | rank_instability | position_skew | flags |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in result["queries"]:
        lines.append(
            "| {query_id} | {normalized_entropy:.4f} | {top1_concentration:.4f} | "
            "{mask_sensitivity:.4f} | {rank_instability:.4f} | {position_skew:.4f} | {flags} |".format(
                **{
                    **row,
                    "flags": "; ".join(row["flags"]) if row["flags"] else "none",
                }
            )
        )

    lines.extend(
        [
            "",
            "## Candidate Sensitivity",
            "| query_id | candidate_id | baseline_rank | position | baseline_score | masked_mean | mask_delta | concentration_share |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in result["candidates"]:
        lines.append(
            "| {query_id} | {candidate_id} | {baseline_rank} | {position} | "
            "{baseline_score:.4f} | {masked_mean:.4f} | {mask_delta:.4f} | "
            "{concentration_share:.4f} |".format(**row)
        )
    return "\n".join(lines) + "\n"


def write_csv(path: Path, candidate_rows: Sequence[Mapping[str, Any]]) -> None:
    """Write candidate-level metrics to CSV with stable columns."""

    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "query_id",
        "candidate_id",
        "baseline_rank",
        "position",
        "baseline_score",
        "masked_mean",
        "mask_delta",
        "concentration_share",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in candidate_rows:
            writer.writerow({column: row[column] for column in columns})


def generate_prompt_records(
    queries: Sequence[Mapping[str, Any]],
    candidates: Sequence[Mapping[str, Any]],
) -> List[Dict[str, str]]:
    """Generate deterministic prompt records for external relevance probes."""

    query_text = {str(query["query_id"]): str(query["text"]) for query in queries}
    masks = ["baseline", "field_mask", "keyword_mask", "position_mask"]
    records: List[Dict[str, str]] = []
    for candidate in sorted(
        candidates,
        key=lambda item: (str(item["query_id"]), candidate_position(item), str(item["candidate_id"])),
    ):
        query_id = str(candidate["query_id"])
        candidate_id = str(candidate["candidate_id"])
        fields = candidate.get("fields", {})
        if isinstance(fields, dict):
            passage = " ".join(str(fields[key]) for key in sorted(fields))
        else:
            passage = str(fields)
        for mask in masks:
            prompt = (
                "Score the candidate passage for relevance from 0.0 to 1.0.\n"
                f"Mask strategy: {mask}\n"
                f"Query: {query_text.get(query_id, '')}\n"
                f"Candidate ID: {candidate_id}\n"
                f"Passage: {passage}"
            )
            records.append(
                {
                    "prompt_id": f"{query_id}:{candidate_id}:{mask}",
                    "query_id": query_id,
                    "candidate_id": candidate_id,
                    "mask": mask,
                    "prompt": prompt,
                }
            )
    return records


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(
        description="Diagnose RAG relevance-gate shortcut bias from JSONL masking score logs."
    )
    parser.add_argument("--queries", type=Path, help="Path to query JSONL records.")
    parser.add_argument("--candidates", type=Path, help="Path to candidate JSONL records.")
    parser.add_argument("--scores", type=Path, help="Path to relevance score JSONL records.")
    parser.add_argument("--out-dir", type=Path, help="Directory for Markdown and CSV reports.")
    parser.add_argument("--prompt-set", type=Path, help="Optional JSONL path for generated prompt records.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of Markdown.")
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run on built-in mock data; this is also the no-argument behavior.",
    )
    return parser.parse_args(argv)


def load_inputs(args: argparse.Namespace) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Load input records from either built-in sample data or JSONL paths."""

    no_input_paths = not args.queries and not args.candidates and not args.scores
    if args.selftest or no_input_paths:
        return list(SAMPLE_QUERIES), list(SAMPLE_CANDIDATES), list(SAMPLE_SCORES)

    missing = [
        name
        for name, value in (
            ("--queries", args.queries),
            ("--candidates", args.candidates),
            ("--scores", args.scores),
        )
        if value is None
    ]
    if missing:
        raise ValueError(f"missing required input option(s): {', '.join(missing)}")

    return read_jsonl(args.queries), read_jsonl(args.candidates), read_jsonl(args.scores)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point."""

    args = parse_args(sys.argv[1:] if argv is None else argv)
    _adapter_key_present = bool(os.getenv("RELEVALENS_ADAPTER_KEY"))
    try:
        queries, candidates, scores = load_inputs(args)
        result = run_probe(queries, candidates, scores)
        if args.prompt_set:
            write_jsonl(args.prompt_set, generate_prompt_records(queries, candidates))
        if args.out_dir:
            args.out_dir.mkdir(parents=True, exist_ok=True)
            report_path = args.out_dir / "relevalens_report.md"
            csv_path = args.out_dir / "relevalens_metrics.csv"
            report_path.write_text(render_markdown(result), encoding="utf-8")
            write_csv(csv_path, result["candidates"])
            print(f"Wrote {report_path}")
            print(f"Wrote {csv_path}")
        elif args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(render_markdown(result), end="")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
