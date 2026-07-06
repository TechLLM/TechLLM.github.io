#!/usr/bin/env python3
"""FacetRecall: a small deterministic benchmarker for modality-aware RAG retrieval.

The script evaluates query-level gold document coverage against retrieved documents
and reports failures across document metadata facets. It is intentionally
dependency-free so the skill can run in isolated environments.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence


FACETS = ("modality", "domain", "document_type", "corruption", "context_condition")
REQUIRED_METADATA_FIELDS = ("id", "domain", "modality", "document_type", "corruption", "context_condition")
REQUIRED_CSV_FIELDS = ("query_id", "query", "gold_doc_ids", "retrieved_doc_ids")
DEFAULT_LIST_DELIMITER = "|"

SAMPLE_METADATA_YAML = """documents:
  - id: doc_text_pricing
    domain: product_docs
    modality: text
    document_type: note
    corruption: clean
    context_condition: complete
  - id: doc_table_eval
    domain: research_notes
    modality: academic_table
    document_type: experiment
    corruption: clean
    context_condition: complete
  - id: doc_code_api
    domain: engineering_logs
    modality: code
    document_type: snippet
    corruption: clean
    context_condition: complete
  - id: doc_wiki_link
    domain: knowledge_base
    modality: wiki_link
    document_type: linked_page
    corruption: clean
    context_condition: complete
  - id: doc_policy_table
    domain: policies
    modality: table
    document_type: reference
    corruption: truncated
    context_condition: partial
"""

SAMPLE_QUERY_ROWS = [
    {
        "query_id": "q1",
        "query": "What plan includes audit logs?",
        "gold_doc_ids": "doc_text_pricing",
        "retrieved_doc_ids": "doc_text_pricing|doc_code_api",
        "accepted_doc_ids": "doc_text_pricing",
    },
    {
        "query_id": "q2",
        "query": "Which model won the benchmark result table?",
        "gold_doc_ids": "doc_table_eval",
        "retrieved_doc_ids": "doc_wiki_link|doc_text_pricing",
        "accepted_doc_ids": "doc_wiki_link",
    },
    {
        "query_id": "q3",
        "query": "How do I call the SDK retry helper?",
        "gold_doc_ids": "doc_code_api",
        "retrieved_doc_ids": "doc_code_api|doc_text_pricing",
        "accepted_doc_ids": "doc_code_api|doc_text_pricing",
    },
    {
        "query_id": "q4",
        "query": "Where is the incident runbook linked?",
        "gold_doc_ids": "doc_wiki_link",
        "retrieved_doc_ids": "doc_wiki_link|doc_text_pricing",
        "accepted_doc_ids": "doc_wiki_link",
    },
    {
        "query_id": "q5",
        "query": "What policy row covers exemption expiry?",
        "gold_doc_ids": "doc_policy_table",
        "retrieved_doc_ids": "doc_wiki_link|doc_text_pricing",
        "accepted_doc_ids": "doc_wiki_link",
    },
]


def parse_simple_documents_yaml(text: str) -> Dict[str, Dict[str, str]]:
    """Parse the small YAML document-list shape used by FacetRecall.

    Supported shape:

    documents:
      - id: doc_id
        domain: product_docs
        modality: text
        document_type: note
        corruption: clean
        context_condition: complete
    """

    documents: List[Dict[str, str]] = []
    current: Dict[str, str] | None = None
    in_documents = False

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line_without_comment = raw_line.split("#", 1)[0].rstrip()
        if not line_without_comment.strip():
            continue

        stripped = line_without_comment.strip()
        if stripped == "documents:":
            in_documents = True
            continue

        if not in_documents:
            raise ValueError(f"metadata YAML line {line_number}: expected top-level 'documents:'")

        if stripped.startswith("- "):
            if current is not None:
                documents.append(current)
            current = {}
            remainder = stripped[2:].strip()
            if remainder:
                key, value = _parse_key_value(remainder, line_number)
                current[key] = value
            continue

        if current is None:
            raise ValueError(f"metadata YAML line {line_number}: expected a document item starting with '-'")

        key, value = _parse_key_value(stripped, line_number)
        current[key] = value

    if current is not None:
        documents.append(current)

    if not in_documents:
        raise ValueError("metadata YAML: missing top-level 'documents:'")
    if not documents:
        raise ValueError("metadata YAML: documents list is empty")

    by_id: Dict[str, Dict[str, str]] = {}
    for index, document in enumerate(documents, start=1):
        missing = [field for field in REQUIRED_METADATA_FIELDS if not document.get(field)]
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"metadata document #{index}: missing required field(s): {joined}")
        doc_id = document["id"]
        if doc_id in by_id:
            raise ValueError(f"metadata YAML: duplicate document id '{doc_id}'")
        by_id[doc_id] = {field: str(document[field]) for field in REQUIRED_METADATA_FIELDS}

    return by_id


def _parse_key_value(text: str, line_number: int) -> tuple[str, str]:
    """Parse one simple YAML key-value line."""

    if ":" not in text:
        raise ValueError(f"metadata YAML line {line_number}: expected 'key: value'")
    key, value = text.split(":", 1)
    key = key.strip()
    value = value.strip().strip("'\"")
    if not key or not value:
        raise ValueError(f"metadata YAML line {line_number}: expected non-empty key and value")
    return key, value


def load_metadata(path: str | Path) -> Dict[str, Dict[str, str]]:
    """Load document metadata from a simple YAML file."""

    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"could not read metadata file '{path}': {exc}") from exc
    return parse_simple_documents_yaml(text)


def split_ids(value: str | None, delimiter: str) -> List[str]:
    """Split a document-ID cell into a stable list of non-empty IDs."""

    if value is None:
        return []
    return [part.strip() for part in value.split(delimiter) if part.strip()]


def load_queries(path: str | Path) -> List[Dict[str, str]]:
    """Load query rows from a CSV file and validate required columns."""

    try:
        with Path(path).open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise ValueError(f"query CSV '{path}' is empty")
            missing = [field for field in REQUIRED_CSV_FIELDS if field not in reader.fieldnames]
            if missing:
                joined = ", ".join(missing)
                raise ValueError(f"query CSV '{path}' is missing required column(s): {joined}")
            return [dict(row) for row in reader]
    except OSError as exc:
        raise ValueError(f"could not read query CSV '{path}': {exc}") from exc


def evaluate(
    query_rows: Sequence[Mapping[str, str]],
    metadata_by_id: Mapping[str, Mapping[str, str]],
    *,
    delimiter: str = DEFAULT_LIST_DELIMITER,
    top_k: int | None = None,
) -> Dict[str, Any]:
    """Evaluate retrieval rows and return FacetRecall's structured result."""

    if not query_rows:
        raise ValueError("query CSV has no data rows")
    if top_k is not None and top_k <= 0:
        raise ValueError("top_k must be a positive integer when supplied")

    evaluated_queries: List[Dict[str, Any]] = []
    warnings: List[str] = []

    for row_index, row in enumerate(query_rows, start=1):
        query_id = (row.get("query_id") or "").strip()
        if not query_id:
            raise ValueError(f"query row {row_index}: missing query_id")

        gold_ids = split_ids(row.get("gold_doc_ids"), delimiter)
        retrieved_ids = split_ids(row.get("retrieved_doc_ids"), delimiter)
        accepted_ids = split_ids(row.get("accepted_doc_ids"), delimiter)

        if not gold_ids:
            raise ValueError(f"query '{query_id}': gold_doc_ids must contain at least one document ID")
        if top_k is not None:
            retrieved_ids = retrieved_ids[:top_k]

        for doc_id in sorted(set(gold_ids + retrieved_ids + accepted_ids)):
            if doc_id not in metadata_by_id:
                warnings.append(f"query '{query_id}': document '{doc_id}' has no metadata")

        gold_set = set(gold_ids)
        retrieved_set = set(retrieved_ids)
        accepted_set = set(accepted_ids)
        retrieved_gold = sorted(gold_set & retrieved_set)
        missing_gold = sorted(gold_set - retrieved_set)
        accepted_non_gold = sorted(accepted_set - gold_set)
        recall = len(retrieved_gold) / len(gold_set)

        evaluated_queries.append(
            {
                "query_id": query_id,
                "query": (row.get("query") or "").strip(),
                "gold_doc_ids": sorted(gold_set),
                "retrieved_doc_ids": retrieved_ids,
                "accepted_doc_ids": sorted(accepted_set),
                "recall": recall,
                "hit": bool(retrieved_gold),
                "missing_gold_doc_ids": missing_gold,
                "accepted_non_gold_doc_ids": accepted_non_gold,
                "facet_values": _query_facet_values(gold_set, metadata_by_id),
            }
        )

    result = {
        "overall": _summarize_queries(evaluated_queries),
        "slices": _build_slices(evaluated_queries),
        "missing_context_failures": _missing_failures(evaluated_queries, metadata_by_id),
        "false_passes": _false_passes(evaluated_queries),
        "warnings": sorted(set(warnings)),
    }
    return result


def _query_facet_values(
    gold_ids: Iterable[str], metadata_by_id: Mapping[str, Mapping[str, str]]
) -> Dict[str, List[str]]:
    """Return facet values represented by the gold documents for one query."""

    values: Dict[str, set[str]] = {facet: set() for facet in FACETS}
    for doc_id in gold_ids:
        metadata = metadata_by_id.get(doc_id)
        if not metadata:
            continue
        for facet in FACETS:
            value = str(metadata.get(facet, "")).strip()
            if value:
                values[facet].add(value)
    return {facet: sorted(facet_values) for facet, facet_values in values.items()}


def _summarize_queries(queries: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Summarize query-level metrics."""

    count = len(queries)
    return {
        "query_count": count,
        "recall": _round(sum(float(query["recall"]) for query in queries) / count),
        "hit_rate": _round(sum(1 for query in queries if query["hit"]) / count),
        "false_pass_rate": _round(
            sum(1 for query in queries if query["accepted_non_gold_doc_ids"]) / count
        ),
        "missing_context_failure_rate": _round(
            sum(1 for query in queries if query["missing_gold_doc_ids"]) / count
        ),
    }


def _build_slices(queries: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Build per-facet retrieval metrics from evaluated queries."""

    buckets: MutableMapping[tuple[str, str], List[Mapping[str, Any]]] = defaultdict(list)
    for query in queries:
        facet_values = query["facet_values"]
        for facet in FACETS:
            for value in facet_values.get(facet, []):
                buckets[(facet, value)].append(query)

    slices: List[Dict[str, Any]] = []
    for facet in FACETS:
        matching_keys = sorted(key for key in buckets if key[0] == facet)
        for _, value in matching_keys:
            bucket = buckets[(facet, value)]
            count = len(bucket)
            slices.append(
                {
                    "facet": facet,
                    "value": value,
                    "query_count": count,
                    "recall": _round(sum(float(query["recall"]) for query in bucket) / count),
                    "false_pass_rate": _round(
                        sum(1 for query in bucket if query["accepted_non_gold_doc_ids"]) / count
                    ),
                    "missing_context_failures": sum(
                        1 for query in bucket if query["missing_gold_doc_ids"]
                    ),
                }
            )
    return slices


def _missing_failures(
    queries: Sequence[Mapping[str, Any]],
    metadata_by_id: Mapping[str, Mapping[str, str]],
) -> List[Dict[str, Any]]:
    """Return query-level missing-context failure details."""

    failures: List[Dict[str, Any]] = []
    for query in queries:
        missing_ids = query["missing_gold_doc_ids"]
        if not missing_ids:
            continue
        failures.append(
            {
                "query_id": query["query_id"],
                "missing_gold_doc_ids": missing_ids,
                "missing_facets": [
                    _doc_facet_summary(doc_id, metadata_by_id.get(doc_id, {})) for doc_id in missing_ids
                ],
            }
        )
    return failures


def _false_passes(queries: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Return query-level false-pass details."""

    return [
        {
            "query_id": query["query_id"],
            "accepted_non_gold_doc_ids": query["accepted_non_gold_doc_ids"],
        }
        for query in queries
        if query["accepted_non_gold_doc_ids"]
    ]


def _doc_facet_summary(doc_id: str, metadata: Mapping[str, str]) -> str:
    """Format document metadata facets as a compact deterministic string."""

    if not metadata:
        return f"{doc_id}: metadata=missing"
    parts = [f"{facet}={metadata.get(facet, 'unknown')}" for facet in FACETS]
    return f"{doc_id}: " + ", ".join(parts)


def render_markdown(result: Mapping[str, Any]) -> str:
    """Render the structured result as a Markdown benchmark report."""

    overall = result["overall"]
    lines = [
        "# FacetRecall Report",
        "",
        "## Overall",
        "",
        "| metric | value |",
        "| --- | ---: |",
        f"| queries | {overall['query_count']} |",
        f"| recall | {_format_float(overall['recall'])} |",
        f"| hit_rate | {_format_float(overall['hit_rate'])} |",
        f"| false_pass_rate | {_format_float(overall['false_pass_rate'])} |",
        f"| missing_context_failure_rate | {_format_float(overall['missing_context_failure_rate'])} |",
        "",
        "## Slices",
        "",
        "| facet | value | queries | recall | false_pass_rate | missing_context_failures |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]

    for row in result["slices"]:
        lines.append(
            "| {facet} | {value} | {query_count} | {recall} | {false_pass_rate} | {missing} |".format(
                facet=row["facet"],
                value=row["value"],
                query_count=row["query_count"],
                recall=_format_float(row["recall"]),
                false_pass_rate=_format_float(row["false_pass_rate"]),
                missing=row["missing_context_failures"],
            )
        )

    lines.extend(["", "## Missing Context Failures", ""])
    missing_failures = result["missing_context_failures"]
    if missing_failures:
        lines.extend(
            [
                "| query_id | missing_gold_doc_ids | missing_facets |",
                "| --- | --- | --- |",
            ]
        )
        for row in missing_failures:
            lines.append(
                "| {query_id} | {missing_ids} | {facets} |".format(
                    query_id=row["query_id"],
                    missing_ids=", ".join(row["missing_gold_doc_ids"]),
                    facets="<br>".join(row["missing_facets"]),
                )
            )
    else:
        lines.append("No missing-context failures detected.")

    lines.extend(["", "## False Passes", ""])
    false_passes = result["false_passes"]
    if false_passes:
        lines.extend(
            [
                "| query_id | accepted_non_gold_doc_ids |",
                "| --- | --- |",
            ]
        )
        for row in false_passes:
            lines.append(
                f"| {row['query_id']} | {', '.join(row['accepted_non_gold_doc_ids'])} |"
            )
    else:
        lines.append("No false passes detected.")

    if result["warnings"]:
        lines.extend(["", "## Warnings", ""])
        for warning in result["warnings"]:
            lines.append(f"- {warning}")

    return "\n".join(lines) + "\n"


def sample_metadata() -> Dict[str, Dict[str, str]]:
    """Return built-in sample document metadata."""

    return parse_simple_documents_yaml(SAMPLE_METADATA_YAML)


def sample_queries() -> List[Dict[str, str]]:
    """Return built-in sample query rows."""

    return [dict(row) for row in SAMPLE_QUERY_ROWS]


def run_selftest() -> str:
    """Run FacetRecall on built-in sample data and return the Markdown report."""

    result = evaluate(sample_queries(), sample_metadata())
    return render_markdown(result)


def _format_float(value: float) -> str:
    """Format metric floats with three decimals."""

    return f"{float(value):.3f}"


def _round(value: float) -> float:
    """Round numeric metrics to a stable precision."""

    return round(value, 6)


def _env_int(name: str) -> int | None:
    """Read an optional positive integer from the environment."""

    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return None
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"environment variable {name} must be a positive integer") from exc
    if value <= 0:
        raise ValueError(f"environment variable {name} must be a positive integer")
    return value


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description="Evaluate modality-aware RAG retrieval slices and generate a FacetRecall report."
    )
    parser.add_argument("--queries", help="Path to query-to-gold CSV input.")
    parser.add_argument("--metadata", help="Path to document metadata YAML input.")
    parser.add_argument("--output", help="Optional output file. Defaults to stdout.")
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default=os.getenv("FACETRECALL_FORMAT", "markdown"),
        help="Output format. Defaults to FACETRECALL_FORMAT or markdown.",
    )
    parser.add_argument(
        "--list-delimiter",
        default=os.getenv("FACETRECALL_LIST_DELIMITER", DEFAULT_LIST_DELIMITER),
        help="Delimiter for document ID lists. Defaults to FACETRECALL_LIST_DELIMITER or '|'.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Evaluate only the first K retrieved document IDs. Defaults to FACETRECALL_TOP_K if set.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run on built-in sample data without API keys or external files.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        env_top_k = _env_int("FACETRECALL_TOP_K")
        top_k = args.top_k if args.top_k is not None else env_top_k

        if args.selftest or not argv:
            output_text = run_selftest()
        else:
            if not args.queries or not args.metadata:
                parser.error("--queries and --metadata are required unless --selftest is used")
            result = evaluate(
                load_queries(args.queries),
                load_metadata(args.metadata),
                delimiter=args.list_delimiter,
                top_k=top_k,
            )
            if args.format == "json":
                output_text = json.dumps(result, indent=2, sort_keys=True) + "\n"
            else:
                output_text = render_markdown(result)

        if args.output:
            Path(args.output).write_text(output_text, encoding="utf-8")
        else:
            sys.stdout.write(output_text)
        return 0
    except ValueError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
