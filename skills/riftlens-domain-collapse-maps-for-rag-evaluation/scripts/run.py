#!/usr/bin/env python3
"""RiftLens domain-split diagnostics for RAG retrieval evaluation.

The CLI reads JSONL rows containing retrieved documents with domain tags,
scores, and boolean relevance labels. It computes deterministic per-domain
metrics and renders a Markdown report for review notes or release gates.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


SAMPLE_RECORDS: List[Dict[str, Any]] = [
    {
        "query_id": "q1",
        "query": "How do I rotate the API token?",
        "retrieved": [
            {"doc_id": "wiki-auth", "domain": "wiki", "score": 0.82, "relevant": True},
            {"doc_id": "ticket-102", "domain": "tickets", "score": 0.44, "relevant": False},
            {"doc_id": "api-auth", "domain": "api_reference", "score": 0.51, "relevant": True},
        ],
    },
    {
        "query_id": "q2",
        "query": "What did the last incident review recommend?",
        "retrieved": [
            {"doc_id": "note-incident", "domain": "notes", "score": 0.77, "relevant": True},
            {"doc_id": "wiki-runbook", "domain": "wiki", "score": 0.68, "relevant": False},
        ],
    },
    {
        "query_id": "q3",
        "query": "Which customer ticket mentions webhook retries?",
        "retrieved": [
            {"doc_id": "ticket-219", "domain": "tickets", "score": 0.61, "relevant": True},
            {"doc_id": "api-webhooks", "domain": "api_reference", "score": 0.49, "relevant": False},
            {"doc_id": "note-roadmap", "domain": "notes", "score": 0.62, "relevant": False},
        ],
    },
]


def env_float(name: str, default: float) -> float:
    """Read a float from an environment variable with a clear error."""
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number, got {raw!r}") from exc


def env_int(name: str, default: Optional[int]) -> Optional[int]:
    """Read an optional positive integer from an environment variable."""
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero, got {value}")
    return value


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Load query records from a JSONL file and annotate malformed lines."""
    records: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                text = line.strip()
                if not text:
                    continue
                try:
                    row = json.loads(text)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_no}: invalid JSON: {exc.msg}") from exc
                if not isinstance(row, dict):
                    raise ValueError(f"{path}:{line_no}: each JSONL line must be an object")
                row["_line_no"] = line_no
                records.append(row)
    except FileNotFoundError as exc:
        raise ValueError(f"Input file not found: {path}") from exc
    if not records:
        raise ValueError(f"Input file has no records: {path}")
    return records


def _rate(numerator: int, denominator: int) -> float:
    """Return a stable zero-based rate for empty denominators."""
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _require_bool(value: Any, context: str) -> bool:
    """Validate and return a boolean field."""
    if isinstance(value, bool):
        return value
    raise ValueError(f"{context}: relevant must be true or false")


def _require_score(value: Any, context: str) -> float:
    """Validate and return a numeric score."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{context}: score must be numeric")
    return float(value)


def _query_id(row: Dict[str, Any], index: int) -> str:
    """Return a query identifier from supported input fields."""
    value = row.get("query_id", row.get("id"))
    if value is None or value == "":
        return f"row-{index}"
    return str(value)


def evaluate_records(
    records: Iterable[Dict[str, Any]],
    threshold: float = 0.6,
    top_k: Optional[int] = None,
    collapse_gap: float = 0.25,
    high_error_rate: float = 0.5,
) -> Dict[str, Any]:
    """Compute aggregate and per-domain RAG retrieval diagnostics.

    Args:
        records: Query records with a retrieved list of document objects.
        threshold: Score threshold at or above which a document is counted as passed.
        top_k: Optional maximum number of retrieved documents to evaluate per query.
        collapse_gap: Minimum best-minus-domain hit-rate gap that triggers a collapse flag.
        high_error_rate: False-pass or false-reject rate that triggers a risk flag.

    Returns:
        A dictionary containing overall metrics, sorted domain metrics, and flags.
    """
    if top_k is not None and top_k <= 0:
        raise ValueError(f"top_k must be greater than zero, got {top_k}")

    domain_counts: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "retrieved_items": 0,
            "relevant_items": 0,
            "non_relevant_items": 0,
            "passed_items": 0,
            "true_passes": 0,
            "false_passes": 0,
            "false_rejects": 0,
            "queries_seen": set(),
        }
    )
    overall = {
        "retrieved_items": 0,
        "relevant_items": 0,
        "non_relevant_items": 0,
        "passed_items": 0,
        "true_passes": 0,
        "false_passes": 0,
        "false_rejects": 0,
    }
    query_count = 0

    for index, row in enumerate(records, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"record {index}: each record must be an object")
        query_count += 1
        query_id = _query_id(row, index)
        retrieved = row.get("retrieved")
        if not isinstance(retrieved, list):
            raise ValueError(f"{query_id}: retrieved must be a list")
        docs = retrieved[:top_k] if top_k is not None else retrieved
        for doc_index, doc in enumerate(docs, start=1):
            context = f"{query_id}: retrieved[{doc_index}]"
            if not isinstance(doc, dict):
                raise ValueError(f"{context}: document must be an object")
            domain_raw = doc.get("domain")
            if domain_raw is None or str(domain_raw).strip() == "":
                raise ValueError(f"{context}: domain is required")
            domain = str(domain_raw).strip()
            score = _require_score(doc.get("score"), context)
            relevant = _require_bool(doc.get("relevant"), context)
            passed = score >= threshold

            bucket = domain_counts[domain]
            bucket["retrieved_items"] += 1
            bucket["queries_seen"].add(query_id)
            overall["retrieved_items"] += 1
            if relevant:
                bucket["relevant_items"] += 1
                overall["relevant_items"] += 1
                if passed:
                    bucket["true_passes"] += 1
                    overall["true_passes"] += 1
                else:
                    bucket["false_rejects"] += 1
                    overall["false_rejects"] += 1
            else:
                bucket["non_relevant_items"] += 1
                overall["non_relevant_items"] += 1
                if passed:
                    bucket["false_passes"] += 1
                    overall["false_passes"] += 1
            if passed:
                bucket["passed_items"] += 1
                overall["passed_items"] += 1

    if query_count == 0:
        raise ValueError("no records to evaluate")
    if not domain_counts:
        raise ValueError("no retrieved documents to evaluate")

    domain_rows: List[Dict[str, Any]] = []
    for domain in sorted(domain_counts):
        counts = domain_counts[domain]
        relevant_items = int(counts["relevant_items"])
        non_relevant_items = int(counts["non_relevant_items"])
        false_passes = int(counts["false_passes"])
        false_rejects = int(counts["false_rejects"])
        true_passes = int(counts["true_passes"])
        domain_rows.append(
            {
                "domain": domain,
                "retrieved_items": int(counts["retrieved_items"]),
                "queries_seen": len(counts["queries_seen"]),
                "coverage": _rate(len(counts["queries_seen"]), query_count),
                "relevant_items": relevant_items,
                "non_relevant_items": non_relevant_items,
                "passed_items": int(counts["passed_items"]),
                "true_passes": true_passes,
                "false_passes": false_passes,
                "false_rejects": false_rejects,
                "hit_rate": _rate(true_passes, relevant_items),
                "false_pass_rate": _rate(false_passes, non_relevant_items),
                "false_reject_rate": _rate(false_rejects, relevant_items),
            }
        )

    overall["hit_rate"] = _rate(overall["true_passes"], overall["relevant_items"])
    overall["false_pass_rate"] = _rate(overall["false_passes"], overall["non_relevant_items"])
    overall["false_reject_rate"] = _rate(overall["false_rejects"], overall["relevant_items"])

    best_row = max(domain_rows, key=lambda row: (row["hit_rate"], row["domain"]))
    worst_row = min(domain_rows, key=lambda row: (row["hit_rate"], row["domain"]))
    worst_domain_gap = best_row["hit_rate"] - worst_row["hit_rate"]

    flags: List[str] = []
    for row in domain_rows:
        hit_gap = best_row["hit_rate"] - row["hit_rate"]
        if row["relevant_items"] > 0 and hit_gap >= collapse_gap:
            flags.append(
                f"Collapse: `{row['domain']}` trails the best domain by `{_fmt_pp(hit_gap)}`."
            )
        if row["non_relevant_items"] > 0 and row["false_pass_rate"] >= high_error_rate:
            flags.append(
                f"Risk: `{row['domain']}` has high false pass rate (`{_fmt_pct(row['false_pass_rate'])}`)."
            )
        if row["relevant_items"] > 0 and row["false_reject_rate"] >= high_error_rate:
            flags.append(
                f"Risk: `{row['domain']}` has high false reject rate (`{_fmt_pct(row['false_reject_rate'])}`)."
            )
    if not flags:
        flags.append("No domain collapse or high error-rate flags at the configured thresholds.")

    return {
        "threshold": threshold,
        "top_k": top_k,
        "query_count": query_count,
        "domain_count": len(domain_rows),
        "overall": overall,
        "domains": domain_rows,
        "best_domain": best_row["domain"],
        "worst_domain": worst_row["domain"],
        "worst_domain_gap": worst_domain_gap,
        "flags": flags,
    }


def _fmt_pct(value: float) -> str:
    """Format a rate as a one-decimal percentage."""
    return f"{value * 100:.1f}%"


def _fmt_pp(value: float) -> str:
    """Format a rate difference as percentage points."""
    return f"{value * 100:.1f} pp"


def render_markdown(result: Dict[str, Any]) -> str:
    """Render an evaluation result dictionary as a Markdown report."""
    top_k = "all" if result["top_k"] is None else str(result["top_k"])
    overall = result["overall"]
    lines = [
        "# RiftLens Domain Collapse Report",
        "",
        f"- Threshold: `{result['threshold']:.2f}`",
        f"- Top K: `{top_k}`",
        f"- Queries: `{result['query_count']}`",
        f"- Retrieved items: `{overall['retrieved_items']}`",
        f"- Overall hit rate: `{_fmt_pct(overall['hit_rate'])}`",
        f"- Overall false pass rate: `{_fmt_pct(overall['false_pass_rate'])}`",
        f"- Overall false reject rate: `{_fmt_pct(overall['false_reject_rate'])}`",
        f"- Worst-domain gap: `{_fmt_pp(result['worst_domain_gap'])}`",
        f"- Worst domain: `{result['worst_domain']}`",
        "",
        "| Domain | Coverage | Hit rate | False pass | False reject | Relevant | Passed |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["domains"]:
        lines.append(
            "| {domain} | {coverage} | {hit_rate} | {false_pass_rate} | "
            "{false_reject_rate} | {relevant_items} | {passed_items} |".format(
                domain=row["domain"],
                coverage=_fmt_pct(row["coverage"]),
                hit_rate=_fmt_pct(row["hit_rate"]),
                false_pass_rate=_fmt_pct(row["false_pass_rate"]),
                false_reject_rate=_fmt_pct(row["false_reject_rate"]),
                relevant_items=row["relevant_items"],
                passed_items=row["passed_items"],
            )
        )
    lines.extend(["", "## Flags", ""])
    lines.extend(f"- {flag}" for flag in result["flags"])
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate domain-split RAG retrieval diagnostics as Markdown."
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        help="JSONL retrieval log. If omitted, RiftLens uses built-in sample data.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Optional Markdown output path. Defaults to stdout.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Score threshold for pass/fail. Defaults to RIFTLENS_THRESHOLD or 0.60.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Evaluate only the first K retrieved documents per query. Defaults to RIFTLENS_TOP_K or all.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run on built-in sample data. This is also the default when --input is omitted.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Run the command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        threshold = args.threshold if args.threshold is not None else env_float("RIFTLENS_THRESHOLD", 0.6)
        top_k = args.top_k if args.top_k is not None else env_int("RIFTLENS_TOP_K", None)
        records = SAMPLE_RECORDS if args.selftest or args.input is None else load_jsonl(args.input)
        result = evaluate_records(records, threshold=threshold, top_k=top_k)
        markdown = render_markdown(result)
        if args.output:
            args.output.write_text(markdown, encoding="utf-8")
        else:
            sys.stdout.write(markdown)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
