"""SliceLens command-line evaluation matrix generator.

This module implements a small, deterministic CSV-first analyzer for LLM,
RAG, retrieval, and agent evaluation exports. It computes source-to-target
transfer matrices, slice means, worst-slice diagnostics, domain gaps, and
missing-field degradation without requiring network access or API keys.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence


MISSING = "(missing)"
DEFAULT_SLICE_COLUMNS = ["question_type", "document_type", "modality", "condition"]

SAMPLE_CSV = """id,source_domain,target_domain,question_type,document_type,modality,condition,score
1,legal,legal,fact,pdf,text,clean,0.90
2,legal,finance,comparison,pdf,text,clean,0.62
3,legal,medical,ambiguous,pdf,text,missing_metadata,0.44
4,finance,finance,fact,html,text,clean,0.88
5,finance,legal,comparison,csv,text,format_shift,0.58
6,finance,medical,ambiguous,csv,text,missing_metadata,0.39
7,medical,medical,fact,pdf,text,clean,0.86
8,medical,legal,comparison,pdf,text,format_shift,0.55
9,medical,finance,ambiguous,,text,missing_metadata,0.41
10,legal,legal,comparison,pdf,text,format_shift,0.70
11,finance,finance,fact,csv,text,clean,0.91
12,medical,medical,ambiguous,pdf,image,clean,0.60
"""


def parse_csv_text(text: str) -> List[Dict[str, str]]:
    """Parse CSV text into a list of row dictionaries."""
    reader = csv.DictReader(io.StringIO(text.strip()))
    if not reader.fieldnames:
        raise ValueError("CSV input has no header row.")
    return [dict(row) for row in reader]


def read_csv_file(path: str) -> List[Dict[str, str]]:
    """Read a CSV file from disk and return row dictionaries."""
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {path}")
    if not csv_path.is_file():
        raise ValueError(f"Input path is not a file: {path}")
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"Input CSV has no header row: {path}")
        return [dict(row) for row in reader]


def write_text(path: str, text: str) -> None:
    """Write UTF-8 text to a file, creating parent directories if needed."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def sample_rows() -> List[Dict[str, str]]:
    """Return built-in sample rows used by self-tests and examples."""
    return parse_csv_text(SAMPLE_CSV)


def mean(values: Sequence[float]) -> Optional[float]:
    """Return the arithmetic mean, or None for an empty sequence."""
    if not values:
        return None
    return sum(values) / len(values)


def fmt_number(value: Optional[float], precision: int) -> str:
    """Format a possibly missing number for Markdown output."""
    if value is None:
        return "n/a"
    return f"{value:.{precision}f}"


def clean_value(row: Mapping[str, Any], column: str) -> str:
    """Return a normalized cell value, replacing blank values with MISSING."""
    value = row.get(column, "")
    if value is None:
        return MISSING
    value = str(value).strip()
    return value if value else MISSING


def parse_score(row: Mapping[str, Any], score_column: str, row_number: int) -> float:
    """Parse and validate one score value from a row."""
    raw_value = row.get(score_column)
    if raw_value is None or str(raw_value).strip() == "":
        raise ValueError(f"Row {row_number} is missing score column '{score_column}'.")
    try:
        score = float(str(raw_value).strip())
    except ValueError as exc:
        raise ValueError(
            f"Row {row_number} has non-numeric score in column '{score_column}': {raw_value!r}"
        ) from exc
    if not math.isfinite(score):
        raise ValueError(f"Row {row_number} has a non-finite score: {raw_value!r}")
    return score


def active_columns(rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> List[str]:
    """Return requested columns that exist in at least one row."""
    available = set()
    for row in rows:
        available.update(row.keys())
    return [column for column in columns if column in available]


def bucket_scores(
    scored_rows: Sequence[Mapping[str, Any]], column: str
) -> Dict[str, List[float]]:
    """Group scores by one normalized column value."""
    buckets: Dict[str, List[float]] = defaultdict(list)
    for row in scored_rows:
        buckets[clean_value(row, column)].append(float(row["_score"]))
    return dict(buckets)


def summarize_buckets(
    buckets: Mapping[str, Sequence[float]], precision: int
) -> List[Dict[str, Any]]:
    """Summarize grouped scores into deterministic table rows."""
    rows = [
        {
            "value": value,
            "count": len(scores),
            "mean": round(mean(scores) or 0.0, precision),
        }
        for value, scores in buckets.items()
    ]
    return sorted(rows, key=lambda item: (item["mean"], item["value"]))


def analyze_rows(
    rows: Sequence[Mapping[str, Any]],
    score_column: str = "score",
    source_column: str = "source_domain",
    target_column: str = "target_domain",
    slice_columns: Optional[Sequence[str]] = None,
    min_count: int = 2,
    precision: int = 3,
) -> Dict[str, Any]:
    """Compute SliceLens diagnostics for evaluation rows.

    Args:
        rows: CSV rows represented as dictionaries.
        score_column: Name of the numeric performance score column.
        source_column: Name of the training/source domain column.
        target_column: Name of the evaluation/target domain column.
        slice_columns: Optional categorical columns for extra slicing.
        min_count: Minimum rows required for worst-slice eligibility.
        precision: Decimal places used in returned rounded numeric fields.

    Returns:
        A deterministic dictionary with overall metrics, matrix data, slice
        summaries, domain gaps, missing-field degradation, and warnings.
    """
    if not rows:
        raise ValueError("No evaluation rows found.")
    if min_count < 1:
        raise ValueError("--min-count must be at least 1.")
    if precision < 0 or precision > 9:
        raise ValueError("--precision must be between 0 and 9.")

    fieldnames = set()
    for row in rows:
        fieldnames.update(row.keys())
    required = [score_column, source_column, target_column]
    missing_required = [column for column in required if column not in fieldnames]
    if missing_required:
        joined = ", ".join(missing_required)
        raise ValueError(f"Input CSV is missing required column(s): {joined}")

    requested_slice_columns = list(slice_columns or DEFAULT_SLICE_COLUMNS)
    present_slice_columns = active_columns(rows, requested_slice_columns)
    ignored_slice_columns = [
        column for column in requested_slice_columns if column not in present_slice_columns
    ]
    dimensions = [source_column, target_column] + [
        column
        for column in present_slice_columns
        if column not in {source_column, target_column}
    ]

    scored_rows: List[Dict[str, Any]] = []
    for index, row in enumerate(rows, start=2):
        scored = dict(row)
        scored["_score"] = parse_score(row, score_column, index)
        scored_rows.append(scored)

    all_scores = [float(row["_score"]) for row in scored_rows]
    sources = sorted({clean_value(row, source_column) for row in scored_rows})
    targets = sorted({clean_value(row, target_column) for row in scored_rows})

    matrix_values: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for source in sources:
        matrix_values[source] = {}
        for target in targets:
            cell_scores = [
                float(row["_score"])
                for row in scored_rows
                if clean_value(row, source_column) == source
                and clean_value(row, target_column) == target
            ]
            matrix_values[source][target] = {
                "mean": round(mean(cell_scores), precision) if cell_scores else None,
                "count": len(cell_scores),
            }

    slice_tables: Dict[str, List[Dict[str, Any]]] = {}
    worst_candidates: List[Dict[str, Any]] = []
    for dimension in dimensions:
        summary = summarize_buckets(bucket_scores(scored_rows, dimension), precision)
        slice_tables[dimension] = summary
        for item in summary:
            if item["count"] >= min_count:
                worst_candidates.append(
                    {
                        "dimension": dimension,
                        "value": item["value"],
                        "count": item["count"],
                        "mean": item["mean"],
                    }
                )
    if not worst_candidates:
        for dimension, summary in slice_tables.items():
            for item in summary:
                worst_candidates.append(
                    {
                        "dimension": dimension,
                        "value": item["value"],
                        "count": item["count"],
                        "mean": item["mean"],
                    }
                )
    worst_slice = sorted(
        worst_candidates,
        key=lambda item: (item["mean"], -item["count"], item["dimension"], item["value"]),
    )[0]

    domain_gaps: List[Dict[str, Any]] = []
    for source in sources:
        in_scores = [
            float(row["_score"])
            for row in scored_rows
            if clean_value(row, source_column) == source
            and clean_value(row, target_column) == source
        ]
        out_scores = [
            float(row["_score"])
            for row in scored_rows
            if clean_value(row, source_column) == source
            and clean_value(row, target_column) != source
        ]
        in_mean = mean(in_scores)
        out_mean = mean(out_scores)
        gap = None if in_mean is None or out_mean is None else in_mean - out_mean
        domain_gaps.append(
            {
                "source_domain": source,
                "in_domain_mean": round(in_mean, precision) if in_mean is not None else None,
                "out_domain_mean": round(out_mean, precision) if out_mean is not None else None,
                "gap": round(gap, precision) if gap is not None else None,
                "in_domain_count": len(in_scores),
                "out_domain_count": len(out_scores),
            }
        )

    missing_field_degradation: List[Dict[str, Any]] = []
    for column in dimensions:
        present_scores = [
            float(row["_score"]) for row in scored_rows if clean_value(row, column) != MISSING
        ]
        missing_scores = [
            float(row["_score"]) for row in scored_rows if clean_value(row, column) == MISSING
        ]
        present_mean = mean(present_scores)
        missing_mean = mean(missing_scores)
        degradation = (
            None
            if present_mean is None or missing_mean is None
            else present_mean - missing_mean
        )
        missing_field_degradation.append(
            {
                "field": column,
                "present_mean": round(present_mean, precision)
                if present_mean is not None
                else None,
                "missing_mean": round(missing_mean, precision)
                if missing_mean is not None
                else None,
                "degradation": round(degradation, precision)
                if degradation is not None
                else None,
                "present_count": len(present_scores),
                "missing_count": len(missing_scores),
            }
        )

    warnings = []
    if ignored_slice_columns:
        warnings.append(
            "Ignored missing optional slice column(s): "
            + ", ".join(sorted(ignored_slice_columns))
        )
    if worst_slice["count"] < min_count:
        warnings.append(
            "No slice met min_count; worst-slice fallback used all available slices."
        )

    return {
        "row_count": len(scored_rows),
        "overall_mean": round(mean(all_scores) or 0.0, precision),
        "score_column": score_column,
        "source_column": source_column,
        "target_column": target_column,
        "slice_columns": present_slice_columns,
        "min_count": min_count,
        "transfer_matrix": {
            "rows": sources,
            "columns": targets,
            "values": matrix_values,
        },
        "worst_slice": worst_slice,
        "domain_gaps": domain_gaps,
        "slice_tables": slice_tables,
        "missing_field_degradation": missing_field_degradation,
        "warnings": warnings,
    }


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    """Render a simple GitHub-flavored Markdown table."""
    header = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join(["---"] * len(headers)) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header, separator] + body)


def render_markdown(report: Mapping[str, Any], precision: int = 3) -> str:
    """Render a SliceLens report dictionary as Markdown."""
    lines: List[str] = [
        "# SliceLens Evaluation Report",
        "",
        "## Summary",
        "",
        markdown_table(
            ["Metric", "Value"],
            [
                ["Rows", str(report["row_count"])],
                ["Overall mean", fmt_number(report["overall_mean"], precision)],
                ["Score column", str(report["score_column"])],
                ["Worst-slice min count", str(report["min_count"])],
            ],
        ),
        "",
        "## Worst Slice",
        "",
        markdown_table(
            ["Dimension", "Value", "Mean", "Count"],
            [
                [
                    str(report["worst_slice"]["dimension"]),
                    str(report["worst_slice"]["value"]),
                    fmt_number(report["worst_slice"]["mean"], precision),
                    str(report["worst_slice"]["count"]),
                ]
            ],
        ),
        "",
        "## Source-to-Target Transfer Matrix",
        "",
    ]

    matrix = report["transfer_matrix"]
    matrix_headers = [str(report["source_column"]) + " \\ " + str(report["target_column"])]
    matrix_headers.extend(matrix["columns"])
    matrix_rows = []
    for source in matrix["rows"]:
        row = [source]
        for target in matrix["columns"]:
            cell = matrix["values"][source][target]
            if cell["count"] == 0:
                row.append("n/a")
            else:
                row.append(f"{fmt_number(cell['mean'], precision)} (n={cell['count']})")
        matrix_rows.append(row)
    lines.extend([markdown_table(matrix_headers, matrix_rows), ""])

    gap_rows = []
    for item in report["domain_gaps"]:
        gap_rows.append(
            [
                str(item["source_domain"]),
                fmt_number(item["in_domain_mean"], precision),
                str(item["in_domain_count"]),
                fmt_number(item["out_domain_mean"], precision),
                str(item["out_domain_count"]),
                fmt_number(item["gap"], precision),
            ]
        )
    lines.extend(
        [
            "## Domain Gaps",
            "",
            markdown_table(
                [
                    "Source domain",
                    "In-domain mean",
                    "In n",
                    "Out-domain mean",
                    "Out n",
                    "Gap",
                ],
                gap_rows,
            ),
            "",
            "## Slice Tables",
            "",
        ]
    )

    for dimension in sorted(report["slice_tables"].keys()):
        rows = [
            [str(item["value"]), fmt_number(item["mean"], precision), str(item["count"])]
            for item in report["slice_tables"][dimension]
        ]
        lines.extend([f"### {dimension}", "", markdown_table(["Value", "Mean", "Count"], rows), ""])

    missing_rows = []
    for item in report["missing_field_degradation"]:
        missing_rows.append(
            [
                str(item["field"]),
                fmt_number(item["present_mean"], precision),
                str(item["present_count"]),
                fmt_number(item["missing_mean"], precision),
                str(item["missing_count"]),
                fmt_number(item["degradation"], precision),
            ]
        )
    lines.extend(
        [
            "## Missing-Field Degradation",
            "",
            markdown_table(
                [
                    "Field",
                    "Present mean",
                    "Present n",
                    "Missing mean",
                    "Missing n",
                    "Degradation",
                ],
                missing_rows,
            ),
        ]
    )

    if report["warnings"]:
        lines.extend(["", "## Warnings", ""])
        for warning in report["warnings"]:
            lines.append(f"- {warning}")

    return "\n".join(lines).rstrip() + "\n"


def parse_slice_columns(value: str) -> List[str]:
    """Parse a comma-separated list of slice columns."""
    columns = [part.strip() for part in value.split(",") if part.strip()]
    if not columns:
        raise argparse.ArgumentTypeError("slice column list cannot be empty")
    return columns


def env_int(name: str, default: int) -> int:
    """Read an integer from the environment with a deterministic fallback."""
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer.") from exc


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    default_slice_columns = os.getenv(
        "SLICELENS_SLICE_COLUMNS", ",".join(DEFAULT_SLICE_COLUMNS)
    )
    parser = argparse.ArgumentParser(
        description=(
            "Generate cross-domain SliceLens evaluation matrices from a CSV file. "
            "Runs a built-in no-key self-test when --selftest is provided or no input is set."
        )
    )
    parser.add_argument(
        "--input",
        default=os.getenv("SLICELENS_INPUT"),
        help="Evaluation CSV path. Defaults to SLICELENS_INPUT, then built-in sample for self-test.",
    )
    parser.add_argument(
        "--output",
        default=os.getenv("SLICELENS_OUTPUT"),
        help="Markdown report path. Defaults to stdout or SLICELENS_OUTPUT.",
    )
    parser.add_argument(
        "--score-column",
        default=os.getenv("SLICELENS_SCORE_COLUMN", "score"),
        help="Numeric score column. Default: score.",
    )
    parser.add_argument(
        "--source-column",
        default=os.getenv("SLICELENS_SOURCE_COLUMN", "source_domain"),
        help="Source-domain column. Default: source_domain.",
    )
    parser.add_argument(
        "--target-column",
        default=os.getenv("SLICELENS_TARGET_COLUMN", "target_domain"),
        help="Target-domain column. Default: target_domain.",
    )
    parser.add_argument(
        "--slice-columns",
        type=parse_slice_columns,
        default=parse_slice_columns(default_slice_columns),
        help=(
            "Comma-separated optional categorical columns. "
            "Default: question_type,document_type,modality,condition."
        ),
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=env_int("SLICELENS_MIN_COUNT", 2),
        help="Minimum rows for worst-slice eligibility. Default: 2.",
    )
    parser.add_argument(
        "--precision",
        type=int,
        default=env_int("SLICELENS_PRECISION", 3),
        help="Decimal places for numeric output. Default: 3.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the raw analysis dictionary as deterministic JSON instead of Markdown.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run on built-in sample data without any API key or external service.",
    )
    return parser


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    """Run the SliceLens CLI and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        use_sample = args.selftest or not args.input
        rows = sample_rows() if use_sample else read_csv_file(args.input)
        report = analyze_rows(
            rows,
            score_column=args.score_column,
            source_column=args.source_column,
            target_column=args.target_column,
            slice_columns=args.slice_columns,
            min_count=args.min_count,
            precision=args.precision,
        )
        if args.json:
            rendered = json.dumps(report, sort_keys=True, indent=2) + "\n"
        else:
            rendered = render_markdown(report, precision=args.precision)
        if args.output:
            write_text(args.output, rendered)
        else:
            sys.stdout.write(rendered)
    except Exception as exc:
        parser.exit(2, f"SliceLens error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli())
