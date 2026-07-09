#!/usr/bin/env python3
"""GateWeave: a small multislice evaluator for RAG relevance gates.

The CLI reads labeled question-document rows and one or more scorer-output
CSV files, then emits deterministic JSON or Markdown reports. It needs no API
key and uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple


PROTOCOL = "gateweave-v0"
DEFAULT_SLICE_COLUMNS = ["domain", "doc_type", "evidence_field"]
DEFAULT_MISSING_FIELD_COLUMNS = ["evidence_field"]
MISSING_BUCKET = "__MISSING__"
TRUE_VALUES = {"1", "true", "t", "yes", "y", "relevant", "pass", "passed"}
FALSE_VALUES = {"0", "false", "f", "no", "n", "irrelevant", "fail", "failed"}


Row = Dict[str, str]
Metrics = Dict[str, Any]
PredictionMap = Dict[Tuple[str, str], Dict[str, Any]]


SAMPLE_LABEL_ROWS: List[Row] = [
    {"qid": "q1", "doc_id": "d1", "label": "1", "domain": "support", "doc_type": "faq", "evidence_field": "body", "region": "us"},
    {"qid": "q2", "doc_id": "d2", "label": "0", "domain": "support", "doc_type": "faq", "evidence_field": "body", "region": "us"},
    {"qid": "q3", "doc_id": "d3", "label": "1", "domain": "legal", "doc_type": "policy", "evidence_field": "metadata", "region": "eu"},
    {"qid": "q4", "doc_id": "d4", "label": "0", "domain": "legal", "doc_type": "policy", "evidence_field": "metadata", "region": "eu"},
    {"qid": "q5", "doc_id": "d5", "label": "1", "domain": "sales", "doc_type": "case_study", "evidence_field": "summary", "region": "us"},
    {"qid": "q6", "doc_id": "d6", "label": "0", "domain": "sales", "doc_type": "case_study", "evidence_field": "summary", "region": "us"},
    {"qid": "q7", "doc_id": "d7", "label": "1", "domain": "support", "doc_type": "faq", "evidence_field": "", "region": "apac"},
    {"qid": "q8", "doc_id": "d8", "label": "0", "domain": "legal", "doc_type": "policy", "evidence_field": "", "region": "apac"},
]

SAMPLE_SCORER_ROWS: Dict[str, List[Row]] = {
    "baseline": [
        {"qid": "q1", "doc_id": "d1", "score": "0.8", "scorer": "baseline"},
        {"qid": "q2", "doc_id": "d2", "score": "0.6", "scorer": "baseline"},
        {"qid": "q3", "doc_id": "d3", "score": "0.7", "scorer": "baseline"},
        {"qid": "q4", "doc_id": "d4", "score": "0.2", "scorer": "baseline"},
        {"qid": "q5", "doc_id": "d5", "score": "0.4", "scorer": "baseline"},
        {"qid": "q6", "doc_id": "d6", "score": "0.1", "scorer": "baseline"},
        {"qid": "q7", "doc_id": "d7", "score": "0.3", "scorer": "baseline"},
        {"qid": "q8", "doc_id": "d8", "score": "0.2", "scorer": "baseline"},
    ],
    "candidate": [
        {"qid": "q1", "doc_id": "d1", "score": "0.9", "scorer": "candidate"},
        {"qid": "q2", "doc_id": "d2", "score": "0.4", "scorer": "candidate"},
        {"qid": "q3", "doc_id": "d3", "score": "0.3", "scorer": "candidate"},
        {"qid": "q4", "doc_id": "d4", "score": "0.2", "scorer": "candidate"},
        {"qid": "q5", "doc_id": "d5", "score": "0.8", "scorer": "candidate"},
        {"qid": "q6", "doc_id": "d6", "score": "0.4", "scorer": "candidate"},
        {"qid": "q7", "doc_id": "d7", "score": "0.7", "scorer": "candidate"},
        {"qid": "q8", "doc_id": "d8", "score": "0.6", "scorer": "candidate"},
    ],
}


class GateWeaveError(ValueError):
    """Raised when input files or arguments are invalid."""


def load_env_config(env: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    """Read optional environment configuration without exposing secrets."""

    source = env if env is not None else os.environ
    threshold_text = source.get("GATEWEAVE_DEFAULT_THRESHOLD", "0.5").strip()
    try:
        threshold = float(threshold_text)
    except ValueError as exc:
        raise GateWeaveError("GATEWEAVE_DEFAULT_THRESHOLD must be a number between 0 and 1.") from exc
    if not 0.0 <= threshold <= 1.0:
        raise GateWeaveError("GATEWEAVE_DEFAULT_THRESHOLD must be between 0 and 1.")
    return {
        "default_threshold": threshold,
        "api_key_present": bool(source.get("GATEWEAVE_API_KEY")),
    }


def parse_list(value: Optional[str], default: Sequence[str]) -> List[str]:
    """Parse a comma-separated CLI value into a clean list."""

    if value is None or value.strip() == "":
        return list(default)
    return [part.strip() for part in value.split(",") if part.strip()]


def normalize_key(row: Mapping[str, str], row_number: int, source: str) -> Tuple[str, str]:
    """Return the `(qid, doc_id)` join key for a CSV row."""

    qid = str(row.get("qid", "")).strip()
    doc_id = str(row.get("doc_id", "")).strip()
    if not qid or not doc_id:
        raise GateWeaveError(f"{source}: row {row_number} must include non-empty qid and doc_id.")
    return qid, doc_id


def parse_bool(value: Any, field: str) -> bool:
    """Parse a human-friendly boolean or relevance label."""

    text = str(value).strip().lower()
    if text in TRUE_VALUES:
        return True
    if text in FALSE_VALUES:
        return False
    raise GateWeaveError(f"Invalid {field} value {value!r}; expected one of {sorted(TRUE_VALUES | FALSE_VALUES)}.")


def parse_score(value: Any, row_number: int, source: str) -> float:
    """Parse a scorer score and validate it is finite enough for thresholding."""

    try:
        score = float(str(value).strip())
    except ValueError as exc:
        raise GateWeaveError(f"{source}: row {row_number} has invalid score {value!r}.") from exc
    if score != score:
        raise GateWeaveError(f"{source}: row {row_number} has NaN score.")
    return score


def bucket_value(value: Any) -> str:
    """Normalize a slice value, assigning blank values to the missing bucket."""

    text = "" if value is None else str(value).strip()
    return text if text else MISSING_BUCKET


def field_text(row: Mapping[str, Any], field: str) -> str:
    """Return a stripped string value for an optional CSV field."""

    value = row.get(field, "")
    return "" if value is None else str(value).strip()


def read_csv_rows(path: Path) -> List[Row]:
    """Load a CSV file as dictionaries with clear errors for missing files."""

    if not path.exists():
        raise GateWeaveError(f"Input file not found: {path}")
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise GateWeaveError(f"{path}: CSV must include a header row.")
            return [dict(row) for row in reader]
    except OSError as exc:
        raise GateWeaveError(f"Could not read {path}: {exc}") from exc


def write_csv_rows(path: Path, rows: Sequence[Row]) -> None:
    """Write rows to CSV using the field order from the first row."""

    if not rows:
        raise GateWeaveError(f"Cannot write empty CSV fixture: {path}")
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def label_map_from_rows(rows: Sequence[Row], source: str) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """Validate label rows and return them keyed by `(qid, doc_id)`."""

    labels: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for index, row in enumerate(rows, start=2):
        if "label" not in row:
            raise GateWeaveError(f"{source}: missing required label column.")
        key = normalize_key(row, index, source)
        if key in labels:
            raise GateWeaveError(f"{source}: duplicate label row for qid={key[0]!r}, doc_id={key[1]!r}.")
        labels[key] = {"label": parse_bool(row.get("label"), "label"), "row": dict(row)}
    if not labels:
        raise GateWeaveError(f"{source}: label CSV has no data rows.")
    return labels


def scorer_maps_from_rows(rows: Sequence[Row], source: str, threshold: float, fallback_name: str) -> Dict[str, PredictionMap]:
    """Validate scorer rows and return prediction maps grouped by scorer name."""

    grouped: Dict[str, PredictionMap] = defaultdict(dict)
    for index, row in enumerate(rows, start=2):
        key = normalize_key(row, index, source)
        scorer_name = bucket_value(row.get("scorer") or fallback_name)
        decision_text = field_text(row, "decision") or field_text(row, "gate")
        if decision_text:
            predicted = parse_bool(decision_text, "decision")
            score = None
        elif field_text(row, "score"):
            score = parse_score(row.get("score"), index, source)
            predicted = score >= threshold
        else:
            raise GateWeaveError(f"{source}: row {index} must include score, decision, or gate.")
        if key in grouped[scorer_name]:
            raise GateWeaveError(f"{source}: duplicate prediction for scorer={scorer_name!r}, qid={key[0]!r}, doc_id={key[1]!r}.")
        grouped[scorer_name][key] = {"predicted": predicted, "score": score}
    if not grouped:
        raise GateWeaveError(f"{source}: scorer CSV has no data rows.")
    return dict(grouped)


def merge_scorer_maps(maps: Iterable[Dict[str, PredictionMap]]) -> Dict[str, PredictionMap]:
    """Merge scorer maps from several files while preventing duplicate names."""

    merged: Dict[str, PredictionMap] = {}
    for scorer_map in maps:
        for name, predictions in scorer_map.items():
            if name in merged:
                overlap = set(merged[name]).intersection(predictions)
                if overlap:
                    sample = sorted(overlap)[0]
                    raise GateWeaveError(f"Duplicate prediction for scorer={name!r}, qid={sample[0]!r}, doc_id={sample[1]!r}.")
                merged[name].update(predictions)
            else:
                merged[name] = dict(predictions)
    if not merged:
        raise GateWeaveError("At least one scorer output is required.")
    return merged


def compute_metrics(pairs: Sequence[Tuple[bool, bool]]) -> Metrics:
    """Compute confusion counts and common binary classification metrics."""

    tp = fp = fn = tn = 0
    for label, predicted in pairs:
        if label and predicted:
            tp += 1
        elif not label and predicted:
            fp += 1
        elif label and not predicted:
            fn += 1
        else:
            tn += 1
    count = tp + fp + fn + tn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    accuracy = (tp + tn) / count if count else 0.0
    return {
        "count": count,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "accuracy": round(accuracy, 6),
    }


def joined_records(
    labels: Mapping[Tuple[str, str], Dict[str, Any]],
    predictions: PredictionMap,
) -> Tuple[List[Dict[str, Any]], int, int]:
    """Join labels with predictions and count missing or extra prediction rows."""

    records: List[Dict[str, Any]] = []
    label_keys = set(labels)
    prediction_keys = set(predictions)
    for key in sorted(label_keys.intersection(prediction_keys)):
        label_entry = labels[key]
        records.append(
            {
                "key": key,
                "label": label_entry["label"],
                "predicted": predictions[key]["predicted"],
                "row": label_entry["row"],
            }
        )
    return records, len(label_keys - prediction_keys), len(prediction_keys - label_keys)


def slice_report(records: Sequence[Dict[str, Any]], slice_columns: Sequence[str]) -> Dict[str, List[Dict[str, Any]]]:
    """Compute metrics for every requested slice column and value."""

    reports: Dict[str, List[Dict[str, Any]]] = {}
    for column in slice_columns:
        groups: MutableMapping[str, List[Tuple[bool, bool]]] = defaultdict(list)
        for record in records:
            value = bucket_value(record["row"].get(column))
            groups[value].append((record["label"], record["predicted"]))
        reports[column] = [
            {"value": value, "metrics": compute_metrics(groups[value])}
            for value in sorted(groups)
        ]
    return reports


def missing_field_report(records: Sequence[Dict[str, Any]], columns: Sequence[str]) -> List[Dict[str, Any]]:
    """Compare rows with blank metadata fields against rows where the field is present."""

    report: List[Dict[str, Any]] = []
    for column in columns:
        missing: List[Tuple[bool, bool]] = []
        present: List[Tuple[bool, bool]] = []
        for record in records:
            target = missing if bucket_value(record["row"].get(column)) == MISSING_BUCKET else present
            target.append((record["label"], record["predicted"]))
        missing_metrics = compute_metrics(missing)
        present_metrics = compute_metrics(present)
        report.append(
            {
                "column": column,
                "missing_count": missing_metrics["count"],
                "present_count": present_metrics["count"],
                "missing_f1": missing_metrics["f1"],
                "present_f1": present_metrics["f1"],
                "stress_score": missing_metrics["f1"],
                "stress_delta": round(missing_metrics["f1"] - present_metrics["f1"], 6),
            }
        )
    return report


def worst_slice(slices: Mapping[str, Sequence[Dict[str, Any]]], slice_columns: Sequence[str]) -> Dict[str, Any]:
    """Return the lowest-F1 slice using deterministic tie-breaking."""

    candidates: List[Tuple[float, int, str, Dict[str, Any]]] = []
    order = {column: index for index, column in enumerate(slice_columns)}
    for column in slice_columns:
        for item in slices.get(column, []):
            candidates.append((item["metrics"]["f1"], order[column], item["value"], {"column": column, **item}))
    if not candidates:
        return {"column": None, "value": None, "metrics": compute_metrics([])}
    return sorted(candidates, key=lambda item: (item[0], item[1], item[2]))[0][3]


def comparison_report(scorer_reports: Sequence[Dict[str, Any]], missing_field_columns: Sequence[str]) -> List[Dict[str, Any]]:
    """Build side-by-side comparison rows for aggregate and stress metrics."""

    comparisons: List[Dict[str, Any]] = []

    def add_comparison(metric: str, scores: Dict[str, float]) -> None:
        best_score = max(scores.values()) if scores else 0.0
        best = sorted(name for name, value in scores.items() if value == best_score)
        comparisons.append({"metric": metric, "best": best, "scores": dict(sorted(scores.items()))})

    add_comparison("aggregate_f1", {item["name"]: item["aggregate"]["f1"] for item in scorer_reports})
    add_comparison("worst_slice_score", {item["name"]: item["worst_slice_score"] for item in scorer_reports})
    for column in missing_field_columns:
        scores: Dict[str, float] = {}
        for item in scorer_reports:
            for stress in item["missing_field_stress"]:
                if stress["column"] == column:
                    scores[item["name"]] = stress["stress_score"]
        if scores:
            add_comparison(f"missing_field_stress_score:{column}", scores)
    return comparisons


def evaluate(
    label_rows: Sequence[Row],
    scorer_rows_by_name: Mapping[str, Sequence[Row]],
    *,
    threshold: float = 0.5,
    slice_columns: Sequence[str] = DEFAULT_SLICE_COLUMNS,
    missing_field_columns: Sequence[str] = DEFAULT_MISSING_FIELD_COLUMNS,
    label_source: str = "builtin",
) -> Dict[str, Any]:
    """Evaluate scorer outputs against labels and return a JSON-ready report."""

    if not 0.0 <= threshold <= 1.0:
        raise GateWeaveError("threshold must be between 0 and 1.")
    labels = label_map_from_rows(label_rows, label_source)
    scorer_maps = merge_scorer_maps(
        scorer_maps_from_rows(rows, name, threshold, name)
        for name, rows in scorer_rows_by_name.items()
    )
    scorer_reports: List[Dict[str, Any]] = []
    for scorer_name in sorted(scorer_maps):
        records, missing_predictions, extra_predictions = joined_records(labels, scorer_maps[scorer_name])
        if not records:
            raise GateWeaveError(f"Scorer {scorer_name!r} has no rows matching the label file.")
        aggregate = compute_metrics([(record["label"], record["predicted"]) for record in records])
        slices = slice_report(records, slice_columns)
        stress = missing_field_report(records, missing_field_columns)
        worst = worst_slice(slices, slice_columns)
        scorer_reports.append(
            {
                "name": scorer_name,
                "rows_evaluated": len(records),
                "missing_predictions": missing_predictions,
                "extra_predictions": extra_predictions,
                "aggregate": aggregate,
                "slices": slices,
                "missing_field_stress": stress,
                "worst_slice": worst,
                "worst_slice_score": worst["metrics"]["f1"],
            }
        )
    return {
        "protocol": PROTOCOL,
        "threshold": round(threshold, 6),
        "slice_columns": list(slice_columns),
        "missing_field_columns": list(missing_field_columns),
        "labels": {"rows": len(labels), "source": label_source},
        "scorers": scorer_reports,
        "comparisons": comparison_report(scorer_reports, missing_field_columns),
    }


def sample_report() -> Dict[str, Any]:
    """Return the deterministic built-in sample report."""

    return evaluate(
        SAMPLE_LABEL_ROWS,
        SAMPLE_SCORER_ROWS,
        threshold=0.5,
        slice_columns=DEFAULT_SLICE_COLUMNS,
        missing_field_columns=DEFAULT_MISSING_FIELD_COLUMNS,
        label_source="builtin",
    )


def load_report_from_files(
    label_path: Path,
    scorer_paths: Sequence[Path],
    *,
    threshold: float,
    slice_columns: Sequence[str],
    missing_field_columns: Sequence[str],
) -> Dict[str, Any]:
    """Load CSV files and evaluate them with the requested protocol settings."""

    label_rows = read_csv_rows(label_path)
    scorer_rows: Dict[str, List[Row]] = {}
    for path in scorer_paths:
        fallback_name = path.stem
        if fallback_name in scorer_rows:
            raise GateWeaveError(f"Duplicate scorer path stem {fallback_name!r}; add a scorer column or rename a file.")
        scorer_rows[fallback_name] = read_csv_rows(path)
    return evaluate(
        label_rows,
        scorer_rows,
        threshold=threshold,
        slice_columns=slice_columns,
        missing_field_columns=missing_field_columns,
        label_source=str(label_path),
    )


def to_json(report: Mapping[str, Any]) -> str:
    """Serialize a report as deterministic pretty JSON."""

    return json.dumps(report, indent=2, sort_keys=False) + "\n"


def format_number(value: Any) -> str:
    """Format report values for compact Markdown tables."""

    if isinstance(value, float):
        return str(round(value, 6))
    return str(value)


def to_markdown(report: Mapping[str, Any]) -> str:
    """Render a report as Markdown for pull request review."""

    lines: List[str] = [
        "# GateWeave Report",
        "",
        f"Protocol: `{report['protocol']}`",
        f"Threshold: `{format_number(report['threshold'])}`",
        f"Rows: `{report['labels']['rows']}`",
        "Slice columns: " + ", ".join(f"`{column}`" for column in report["slice_columns"]),
        "",
        "## Aggregate Metrics",
        "",
        "| scorer | rows | precision | recall | f1 | accuracy | worst_slice_score |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for scorer in report["scorers"]:
        aggregate = scorer["aggregate"]
        lines.append(
            "| {name} | {rows} | {precision} | {recall} | {f1} | {accuracy} | {worst} |".format(
                name=scorer["name"],
                rows=scorer["rows_evaluated"],
                precision=format_number(aggregate["precision"]),
                recall=format_number(aggregate["recall"]),
                f1=format_number(aggregate["f1"]),
                accuracy=format_number(aggregate["accuracy"]),
                worst=format_number(scorer["worst_slice_score"]),
            )
        )
    lines.extend(["", "## Worst Slices", "", "| scorer | column | value | count | precision | recall | f1 |", "|---|---|---|---:|---:|---:|---:|"])
    for scorer in report["scorers"]:
        worst = scorer["worst_slice"]
        metrics = worst["metrics"]
        lines.append(
            "| {name} | {column} | {value} | {count} | {precision} | {recall} | {f1} |".format(
                name=scorer["name"],
                column=worst["column"],
                value=worst["value"],
                count=metrics["count"],
                precision=format_number(metrics["precision"]),
                recall=format_number(metrics["recall"]),
                f1=format_number(metrics["f1"]),
            )
        )
    lines.extend(["", "## Missing-Field Stress", "", "| scorer | column | missing_count | present_count | missing_f1 | present_f1 | stress_delta |", "|---|---|---:|---:|---:|---:|---:|"])
    for scorer in report["scorers"]:
        for stress in scorer["missing_field_stress"]:
            lines.append(
                "| {name} | {column} | {missing_count} | {present_count} | {missing_f1} | {present_f1} | {stress_delta} |".format(
                    name=scorer["name"],
                    column=stress["column"],
                    missing_count=stress["missing_count"],
                    present_count=stress["present_count"],
                    missing_f1=format_number(stress["missing_f1"]),
                    present_f1=format_number(stress["present_f1"]),
                    stress_delta=format_number(stress["stress_delta"]),
                )
            )
    lines.extend(["", "## Side-by-Side", "", "| metric | best | scores |", "|---|---|---|"])
    for comparison in report["comparisons"]:
        score_text = ", ".join(f"{name}={format_number(value)}" for name, value in comparison["scores"].items())
        lines.append(f"| {comparison['metric']} | {', '.join(comparison['best'])} | {score_text} |")
    return "\n".join(lines) + "\n"


def write_text(path: Path, text: str) -> None:
    """Write text output, creating parent directories when needed."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_example_inputs(directory: Path) -> None:
    """Write the bundled example CSV inputs."""

    directory.mkdir(parents=True, exist_ok=True)
    write_csv_rows(directory / "labels.csv", SAMPLE_LABEL_ROWS)
    write_csv_rows(directory / "baseline_scores.csv", SAMPLE_SCORER_ROWS["baseline"])
    write_csv_rows(directory / "candidate_scores.csv", SAMPLE_SCORER_ROWS["candidate"])


def build_parser(default_threshold: float) -> argparse.ArgumentParser:
    """Build the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="Evaluate RAG relevance gates across aggregate, slice, and missing-field stress metrics.",
    )
    parser.add_argument("--labels", type=Path, help="Labeled CSV with qid, doc_id, label, and optional slice columns.")
    parser.add_argument("--scorers", type=Path, nargs="+", help="One or more scorer CSV files with qid, doc_id, and score or decision.")
    parser.add_argument("--threshold", type=float, default=None, help=f"Score threshold for positive predictions. Default: {default_threshold}.")
    parser.add_argument("--slice-columns", default=",".join(DEFAULT_SLICE_COLUMNS), help="Comma-separated slice columns. Default: domain,doc_type,evidence_field.")
    parser.add_argument("--missing-field-columns", default=",".join(DEFAULT_MISSING_FIELD_COLUMNS), help="Comma-separated columns for missing-field stress tests.")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Format printed to stdout. Default: json.")
    parser.add_argument("--output-json", type=Path, help="Optional path for the JSON report.")
    parser.add_argument("--output-md", type=Path, help="Optional path for the Markdown report.")
    parser.add_argument("--write-example-inputs", type=Path, help="Write sample CSV inputs to the given directory and exit.")
    parser.add_argument("--selftest", action="store_true", help="Run the built-in sample with no external files.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the command-line interface."""

    try:
        env_config = load_env_config()
        parser = build_parser(env_config["default_threshold"])
        args = parser.parse_args(argv)
        threshold = args.threshold if args.threshold is not None else env_config["default_threshold"]
        if not 0.0 <= threshold <= 1.0:
            raise GateWeaveError("--threshold must be between 0 and 1.")

        if args.write_example_inputs:
            write_example_inputs(args.write_example_inputs)
            print(f"Wrote example inputs to {args.write_example_inputs}")
            return 0

        slice_columns = parse_list(args.slice_columns, DEFAULT_SLICE_COLUMNS)
        missing_field_columns = parse_list(args.missing_field_columns, DEFAULT_MISSING_FIELD_COLUMNS)

        if args.selftest or (args.labels is None and args.scorers is None):
            report = sample_report()
        else:
            if args.labels is None:
                raise GateWeaveError("--labels is required unless --selftest is used.")
            if not args.scorers:
                raise GateWeaveError("--scorers is required unless --selftest is used.")
            report = load_report_from_files(
                args.labels,
                args.scorers,
                threshold=threshold,
                slice_columns=slice_columns,
                missing_field_columns=missing_field_columns,
            )

        json_text = to_json(report)
        markdown_text = to_markdown(report)
        if args.output_json:
            write_text(args.output_json, json_text)
        if args.output_md:
            write_text(args.output_md, markdown_text)
        sys.stdout.write(markdown_text if args.format == "markdown" else json_text)
        return 0
    except GateWeaveError as exc:
        print(f"gateweave error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
