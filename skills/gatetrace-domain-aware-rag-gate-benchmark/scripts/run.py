#!/usr/bin/env python3
"""GateTrace CLI for domain-aware RAG retrieval and gate benchmarking.

The script reads JSONL query records, computes deterministic aggregate and
sliced metrics, and emits JSON and/or Markdown reports. It uses only the Python
standard library and can run on built-in sample data without API keys.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple


DEFAULT_OOD_TAGS = ("rare_terms", "unfamiliar_domain", "long_tail_intent")

SAMPLE_RECORDS: List[Dict[str, Any]] = [
    {
        "query_id": "q1",
        "query": "What reserve term is required for the billing policy?",
        "domain_tags": ["finance"],
        "ood_tags": ["rare_terms"],
        "question_type": "definition",
        "required_doc_ids": ["fin-1"],
        "retrieved": [
            {
                "doc_id": "fin-1",
                "relevant": True,
                "gate_pass": True,
                "doc_type": "manual",
                "source_family": "knowledge_base",
                "domain_tags": ["finance", "policy"],
                "evidence_density": "high",
            },
            {
                "doc_id": "fin-9",
                "relevant": False,
                "gate_pass": True,
                "doc_type": "faq",
                "source_family": "forum",
                "domain_tags": ["finance"],
                "evidence_density": "low",
            },
        ],
    },
    {
        "query_id": "q2",
        "query": "Which clinical escalation step is required?",
        "domain_tags": ["healthcare"],
        "ood_tags": [],
        "question_type": "procedural",
        "required_doc_ids": ["med-2"],
        "retrieved": [
            {
                "doc_id": "med-2",
                "relevant": True,
                "gate_pass": False,
                "doc_type": "guideline",
                "source_family": "knowledge_base",
                "domain_tags": ["healthcare"],
                "evidence_density": "high",
            },
            {
                "doc_id": "med-8",
                "relevant": False,
                "gate_pass": False,
                "doc_type": "blog",
                "source_family": "web",
                "domain_tags": ["healthcare"],
                "evidence_density": "low",
            },
        ],
    },
    {
        "query_id": "q3",
        "query": "Compare the two contract clauses that define renewal limits.",
        "domain_tags": ["legal"],
        "ood_tags": [],
        "question_type": "comparison",
        "required_doc_ids": ["law-1", "law-2"],
        "retrieved": [
            {
                "doc_id": "law-1",
                "relevant": True,
                "gate_pass": True,
                "doc_type": "statute",
                "source_family": "corpus",
                "domain_tags": ["legal"],
                "evidence_density": "medium",
            },
            {
                "doc_id": "law-9",
                "relevant": False,
                "gate_pass": False,
                "doc_type": "memo",
                "source_family": "drive",
                "domain_tags": ["legal", "contract"],
                "evidence_density": "low",
            },
        ],
    },
    {
        "query_id": "q4",
        "query": "Diagnose the actuator reset sequence for the long-tail maintenance case.",
        "domain_tags": ["aerospace"],
        "ood_tags": ["long_tail_intent"],
        "question_type": "diagnostic",
        "required_doc_ids": ["aero-1"],
        "retrieved": [
            {
                "doc_id": "aero-1",
                "relevant": True,
                "gate_pass": True,
                "doc_type": "incident_report",
                "source_family": "tickets",
                "domain_tags": ["aerospace", "maintenance"],
                "evidence_density": "high",
            },
            {
                "doc_id": "aero-7",
                "relevant": True,
                "gate_pass": True,
                "doc_type": "schematic",
                "source_family": "engineering",
                "domain_tags": ["aerospace", "maintenance"],
                "evidence_density": "medium",
            },
            {
                "doc_id": "aero-3",
                "relevant": False,
                "gate_pass": True,
                "doc_type": "chat",
                "source_family": "slack",
                "domain_tags": ["aerospace"],
                "evidence_density": "low",
            },
        ],
    },
]


def parse_csv(value: Optional[str]) -> List[str]:
    """Return a sorted list of non-empty comma-separated tokens."""
    if not value:
        return []
    return sorted({item.strip() for item in value.split(",") if item.strip()})


def configured_ood_tags(cli_value: Optional[str]) -> Set[str]:
    """Resolve OOD-like tags from CLI, environment, or defaults."""
    tags = parse_csv(cli_value)
    if not tags:
        tags = parse_csv(os.environ.get("GATETRACE_OOD_TAGS"))
    if not tags:
        tags = list(DEFAULT_OOD_TAGS)
    return set(tags)


def metric_ratio(numerator: int, denominator: int) -> float:
    """Return a four-decimal ratio, using zero for empty denominators."""
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)


def harmonic(precision: float, recall: float) -> float:
    """Return a four-decimal harmonic mean for precision and recall."""
    if precision + recall == 0:
        return 0.0
    return round((2 * precision * recall) / (precision + recall), 4)


def as_bool(value: Any, field: str, query_id: str, doc_id: str) -> bool:
    """Validate and normalize a boolean document label."""
    if isinstance(value, bool):
        return value
    raise ValueError(
        f"Document {doc_id!r} in query {query_id!r} has invalid {field!r}; expected true or false."
    )


def normalize_records(records: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Validate records and return normalized copies sorted by query id."""
    normalized: List[Dict[str, Any]] = []
    seen_query_ids: Set[str] = set()
    for index, raw in enumerate(records, start=1):
        if not isinstance(raw, Mapping):
            raise ValueError(f"Record {index} is not a JSON object.")
        query_id = str(raw.get("query_id", "")).strip()
        if not query_id:
            raise ValueError(f"Record {index} is missing required field 'query_id'.")
        if query_id in seen_query_ids:
            raise ValueError(f"Duplicate query_id {query_id!r}.")
        seen_query_ids.add(query_id)

        required_doc_ids_raw = raw.get("required_doc_ids")
        if not isinstance(required_doc_ids_raw, list):
            raise ValueError(f"Query {query_id!r} must contain list field 'required_doc_ids'.")
        required_doc_ids = [str(doc_id).strip() for doc_id in required_doc_ids_raw if str(doc_id).strip()]
        if len(required_doc_ids) != len(set(required_doc_ids)):
            raise ValueError(f"Query {query_id!r} has duplicate required_doc_ids.")

        retrieved_raw = raw.get("retrieved")
        if not isinstance(retrieved_raw, list):
            raise ValueError(f"Query {query_id!r} must contain list field 'retrieved'.")

        docs: List[Dict[str, Any]] = []
        seen_doc_ids: Set[str] = set()
        for doc_index, doc_raw in enumerate(retrieved_raw, start=1):
            if not isinstance(doc_raw, Mapping):
                raise ValueError(f"Retrieved item {doc_index} in query {query_id!r} is not an object.")
            doc_id = str(doc_raw.get("doc_id", "")).strip()
            if not doc_id:
                raise ValueError(f"Retrieved item {doc_index} in query {query_id!r} is missing 'doc_id'.")
            if doc_id in seen_doc_ids:
                raise ValueError(f"Query {query_id!r} has duplicate retrieved doc_id {doc_id!r}.")
            seen_doc_ids.add(doc_id)
            docs.append(
                {
                    "doc_id": doc_id,
                    "relevant": as_bool(doc_raw.get("relevant"), "relevant", query_id, doc_id),
                    "gate_pass": as_bool(doc_raw.get("gate_pass"), "gate_pass", query_id, doc_id),
                    "doc_type": str(doc_raw.get("doc_type", "unknown")).strip() or "unknown",
                    "source_family": str(doc_raw.get("source_family", "unknown")).strip() or "unknown",
                    "domain_tags": sorted(
                        {
                            str(tag).strip()
                            for tag in doc_raw.get("domain_tags", [])
                            if str(tag).strip()
                        }
                    ),
                    "evidence_density": str(doc_raw.get("evidence_density", "unknown")).strip()
                    or "unknown",
                }
            )

        normalized.append(
            {
                "query_id": query_id,
                "query": str(raw.get("query", "")).strip(),
                "domain_tags": sorted(
                    {str(tag).strip() for tag in raw.get("domain_tags", []) if str(tag).strip()}
                ),
                "ood_tags": sorted(
                    {str(tag).strip() for tag in raw.get("ood_tags", []) if str(tag).strip()}
                ),
                "question_type": str(raw.get("question_type", "unknown")).strip() or "unknown",
                "required_doc_ids": sorted(required_doc_ids),
                "retrieved": sorted(docs, key=lambda item: item["doc_id"]),
            }
        )
    return sorted(normalized, key=lambda item: item["query_id"])


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Load JSONL records from a file path with line-numbered errors."""
    records: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    records.append(json.loads(stripped))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
    except FileNotFoundError as exc:
        raise ValueError(f"Input file not found: {path}") from exc
    if not records:
        raise ValueError(f"Input file contains no records: {path}")
    return records


def flatten_docs(records: Sequence[Mapping[str, Any]]) -> List[Tuple[Mapping[str, Any], Mapping[str, Any]]]:
    """Return `(query, doc)` pairs for all retrieved documents."""
    pairs: List[Tuple[Mapping[str, Any], Mapping[str, Any]]] = []
    for record in records:
        for doc in record["retrieved"]:
            pairs.append((record, doc))
    return pairs


def query_metrics(records: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Compute retrieval and gate metrics for a set of query records."""
    required_total = 0
    required_retrieved = 0
    retrieved_total = 0
    relevant_retrieved = 0
    gate_pass_total = 0
    gate_pass_relevant = 0
    false_pass = 0
    false_block = 0
    irrelevant_retrieved = 0

    for record in records:
        required = set(record["required_doc_ids"])
        retrieved_ids = {doc["doc_id"] for doc in record["retrieved"]}
        required_total += len(required)
        required_retrieved += len(required & retrieved_ids)
        for doc in record["retrieved"]:
            retrieved_total += 1
            relevant = bool(doc["relevant"])
            gate_pass = bool(doc["gate_pass"])
            if relevant:
                relevant_retrieved += 1
            else:
                irrelevant_retrieved += 1
            if gate_pass:
                gate_pass_total += 1
                if relevant:
                    gate_pass_relevant += 1
                else:
                    false_pass += 1
            elif relevant:
                false_block += 1

    retrieval_recall = metric_ratio(required_retrieved, required_total)
    retrieval_precision = metric_ratio(relevant_retrieved, retrieved_total)
    gate_precision = metric_ratio(gate_pass_relevant, gate_pass_total)
    gate_recall = metric_ratio(gate_pass_relevant, relevant_retrieved)

    return {
        "required_evidence_count": required_total,
        "required_evidence_retrieved_count": required_retrieved,
        "retrieved_document_count": retrieved_total,
        "relevant_retrieved_count": relevant_retrieved,
        "retrieval_recall": retrieval_recall,
        "retrieval_precision": retrieval_precision,
        "retrieval_f1": harmonic(retrieval_precision, retrieval_recall),
        "gate_pass_rate": metric_ratio(gate_pass_total, retrieved_total),
        "gate_precision": gate_precision,
        "gate_recall": gate_recall,
        "gate_f1": harmonic(gate_precision, gate_recall),
        "false_pass_rate": metric_ratio(false_pass, irrelevant_retrieved),
        "false_block_rate": metric_ratio(false_block, relevant_retrieved),
    }


def document_metrics(pairs: Sequence[Tuple[Mapping[str, Any], Mapping[str, Any]]]) -> Dict[str, Any]:
    """Compute gate-oriented metrics for a set of observed retrieved documents."""
    total = len(pairs)
    relevant_total = 0
    irrelevant_total = 0
    pass_total = 0
    pass_relevant = 0
    false_pass = 0
    false_block = 0
    for _record, doc in pairs:
        relevant = bool(doc["relevant"])
        gate_pass = bool(doc["gate_pass"])
        if relevant:
            relevant_total += 1
        else:
            irrelevant_total += 1
        if gate_pass:
            pass_total += 1
            if relevant:
                pass_relevant += 1
            else:
                false_pass += 1
        elif relevant:
            false_block += 1
    gate_precision = metric_ratio(pass_relevant, pass_total)
    gate_recall = metric_ratio(pass_relevant, relevant_total)
    return {
        "retrieved_document_count": total,
        "relevant_retrieved_count": relevant_total,
        "gate_pass_rate": metric_ratio(pass_total, total),
        "gate_precision": gate_precision,
        "gate_recall": gate_recall,
        "gate_f1": harmonic(gate_precision, gate_recall),
        "false_pass_rate": metric_ratio(false_pass, irrelevant_total),
        "false_block_rate": metric_ratio(false_block, relevant_total),
    }


def build_query_slices(records: Sequence[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Build metrics grouped by query-level metadata."""
    domains = sorted({tag for record in records for tag in record["domain_tags"]})
    question_types = sorted({record["question_type"] for record in records})
    ood_tags = sorted({tag for record in records for tag in record["ood_tags"]})
    return {
        "domain_tag": {
            tag: query_metrics([record for record in records if tag in record["domain_tags"]])
            for tag in domains
        },
        "question_type": {
            tag: query_metrics([record for record in records if record["question_type"] == tag])
            for tag in question_types
        },
        "ood_tag": {
            tag: query_metrics([record for record in records if tag in record["ood_tags"]])
            for tag in ood_tags
        },
    }


def build_document_slices(records: Sequence[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Build gate metrics grouped by retrieved-document metadata."""
    pairs = flatten_docs(records)
    dimensions = {
        "doc_type": sorted({doc["doc_type"] for _record, doc in pairs}),
        "source_family": sorted({doc["source_family"] for _record, doc in pairs}),
        "evidence_density": sorted({doc["evidence_density"] for _record, doc in pairs}),
    }
    result: Dict[str, Dict[str, Any]] = {}
    for dimension, values in dimensions.items():
        result[dimension] = {
            value: document_metrics([(record, doc) for record, doc in pairs if doc[dimension] == value])
            for value in values
        }
    return result


def failure_lists(records: Sequence[Mapping[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Return missing-evidence, false-pass, and false-block lists."""
    missing_evidence: List[Dict[str, Any]] = []
    false_passes: List[Dict[str, Any]] = []
    false_blocks: List[Dict[str, Any]] = []
    for record in records:
        retrieved_ids = {doc["doc_id"] for doc in record["retrieved"]}
        missing = sorted(set(record["required_doc_ids"]) - retrieved_ids)
        if missing:
            missing_evidence.append(
                {
                    "query_id": record["query_id"],
                    "missing_doc_ids": missing,
                    "domain_tags": record["domain_tags"],
                    "question_type": record["question_type"],
                }
            )
        for doc in record["retrieved"]:
            failure = {
                "query_id": record["query_id"],
                "doc_id": doc["doc_id"],
                "doc_type": doc["doc_type"],
                "source_family": doc["source_family"],
                "evidence_density": doc["evidence_density"],
            }
            if bool(doc["gate_pass"]) and not bool(doc["relevant"]):
                false_passes.append({**failure, "reason": "gate_passed_irrelevant_document"})
            if not bool(doc["gate_pass"]) and bool(doc["relevant"]):
                false_blocks.append({**failure, "reason": "gate_blocked_relevant_document"})
    return (
        sorted(missing_evidence, key=lambda item: item["query_id"]),
        sorted(false_passes, key=lambda item: (item["query_id"], item["doc_id"])),
        sorted(false_blocks, key=lambda item: (item["query_id"], item["doc_id"])),
    )


def detect_ood_queries(records: Sequence[Mapping[str, Any]], ood_tags: Set[str]) -> List[Dict[str, Any]]:
    """Return queries whose tags match configured OOD-like tags."""
    matches: List[Dict[str, Any]] = []
    for record in records:
        all_tags = set(record["domain_tags"]) | set(record["ood_tags"])
        matched_tags = sorted(all_tags & ood_tags)
        if matched_tags:
            matches.append(
                {
                    "query_id": record["query_id"],
                    "matched_tags": matched_tags,
                    "domain_tags": record["domain_tags"],
                    "question_type": record["question_type"],
                }
            )
    return sorted(matches, key=lambda item: item["query_id"])


def build_report(records: Iterable[Mapping[str, Any]], ood_tags: Optional[Set[str]] = None) -> Dict[str, Any]:
    """Build the complete GateTrace JSON report."""
    resolved_ood_tags = ood_tags if ood_tags is not None else set(DEFAULT_OOD_TAGS)
    normalized = normalize_records(records)
    overall = query_metrics(normalized)
    missing_evidence, false_passes, false_blocks = failure_lists(normalized)
    ood_queries = detect_ood_queries(normalized, resolved_ood_tags)
    return {
        "summary": {
            "query_count": len(normalized),
            "document_count": sum(len(record["retrieved"]) for record in normalized),
            "required_evidence_count": sum(len(record["required_doc_ids"]) for record in normalized),
            "missing_evidence_query_count": len(missing_evidence),
            "false_pass_count": len(false_passes),
            "false_block_count": len(false_blocks),
            "ood_query_count": len(ood_queries),
        },
        "overall": overall,
        "query_slices": build_query_slices(normalized),
        "document_slices": build_document_slices(normalized),
        "missing_evidence": missing_evidence,
        "false_passes": false_passes,
        "false_blocks": false_blocks,
        "ood_queries": ood_queries,
    }


def render_metric_table(metrics: Mapping[str, Any]) -> str:
    """Render a single metric mapping as a Markdown table."""
    lines = ["| Metric | Value |", "| --- | ---: |"]
    for key in sorted(metrics):
        lines.append(f"| {key} | {metrics[key]} |")
    return "\n".join(lines)


def render_markdown(report: Mapping[str, Any]) -> str:
    """Render a GateTrace report as Markdown."""
    lines: List[str] = ["# GateTrace Report", ""]
    lines.extend(["## Summary", "", render_metric_table(report["summary"]), ""])
    lines.extend(["## Overall Metrics", "", render_metric_table(report["overall"]), ""])

    lines.extend(["## Query Slices", ""])
    for dimension, slices in report["query_slices"].items():
        lines.extend([f"### {dimension}", ""])
        if not slices:
            lines.extend(["No slices.", ""])
            continue
        for value, metrics in slices.items():
            lines.extend([f"#### {value}", "", render_metric_table(metrics), ""])

    lines.extend(["## Document Slices", ""])
    for dimension, slices in report["document_slices"].items():
        lines.extend([f"### {dimension}", ""])
        if not slices:
            lines.extend(["No slices.", ""])
            continue
        for value, metrics in slices.items():
            lines.extend([f"#### {value}", "", render_metric_table(metrics), ""])

    for title, key in (
        ("Missing Evidence", "missing_evidence"),
        ("False Passes", "false_passes"),
        ("False Blocks", "false_blocks"),
        ("OOD-like Queries", "ood_queries"),
    ):
        lines.extend([f"## {title}", ""])
        items = report[key]
        if not items:
            lines.extend(["None.", ""])
            continue
        lines.extend(["```json", json.dumps(items, indent=2, sort_keys=True), "```", ""])
    return "\n".join(lines).rstrip() + "\n"


def sample_records() -> List[Dict[str, Any]]:
    """Return a deep copy of the built-in sample records."""
    return json.loads(json.dumps(SAMPLE_RECORDS))


def write_text(path: Optional[str], content: str) -> None:
    """Write text to a path or standard output if no path is provided."""
    if path:
        Path(path).write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)


def positive_float(value: str) -> float:
    """Parse a recall threshold between zero and one."""
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("threshold must be a number between 0 and 1") from exc
    if parsed < 0 or parsed > 1:
        raise argparse.ArgumentTypeError("threshold must be between 0 and 1")
    return parsed


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Evaluate RAG retrieval and relevance-gate behavior with domain-aware slices."
    )
    parser.add_argument("--input", help="JSONL input file. If omitted, built-in sample data is used.")
    parser.add_argument(
        "--format",
        choices=("json", "markdown", "both"),
        default="json",
        help="Report format for stdout or output files.",
    )
    parser.add_argument("--json-out", help="Write JSON report to this file.")
    parser.add_argument("--markdown-out", help="Write Markdown report to this file.")
    parser.add_argument(
        "--ood-tags",
        help="Comma-separated tags treated as OOD-like. Defaults to GATETRACE_OOD_TAGS or built-ins.",
    )
    parser.add_argument(
        "--fail-under-recall",
        type=positive_float,
        default=None,
        help="Exit with code 2 if overall retrieval_recall is below this threshold.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run on built-in sample data and validate the resulting report shape.",
    )
    return parser.parse_args(argv)


def validate_report_shape(report: Mapping[str, Any]) -> None:
    """Raise ValueError if a report misses required top-level fields."""
    required_top_level = {
        "summary",
        "overall",
        "query_slices",
        "document_slices",
        "missing_evidence",
        "false_passes",
        "false_blocks",
        "ood_queries",
    }
    missing = sorted(required_top_level - set(report))
    if missing:
        raise ValueError(f"Report missing top-level fields: {', '.join(missing)}")
    if "retrieval_recall" not in report["overall"]:
        raise ValueError("Report missing overall.retrieval_recall")


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the GateTrace CLI."""
    args = parse_args(argv)
    try:
        ood_tags = configured_ood_tags(args.ood_tags)
        records = load_jsonl(Path(args.input)) if args.input else sample_records()
        report = build_report(records, ood_tags=ood_tags)
        if args.selftest or not args.input:
            validate_report_shape(report)

        json_report = json.dumps(report, indent=2, sort_keys=True) + "\n"
        markdown_report = render_markdown(report)

        if args.json_out:
            write_text(args.json_out, json_report)
        if args.markdown_out:
            write_text(args.markdown_out, markdown_report)

        if not args.json_out and not args.markdown_out:
            if args.format == "json":
                write_text(None, json_report)
            elif args.format == "markdown":
                write_text(None, markdown_report)
            else:
                write_text(None, json_report)
                write_text(None, "\n--- markdown ---\n\n")
                write_text(None, markdown_report)

        threshold = args.fail_under_recall
        if threshold is None and os.environ.get("GATETRACE_MIN_RECALL"):
            threshold = positive_float(os.environ["GATETRACE_MIN_RECALL"])
        if threshold is not None and report["overall"]["retrieval_recall"] < threshold:
            sys.stderr.write(
                "GateTrace recall check failed: "
                f"{report['overall']['retrieval_recall']} < {threshold}\n"
            )
            return 2
        return 0
    except (OSError, ValueError, argparse.ArgumentTypeError) as exc:
        sys.stderr.write(f"gatetrace error: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
