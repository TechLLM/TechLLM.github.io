#!/usr/bin/env python3
"""TraceLoom: compile positive agent/RAG traces into router-ready datasets."""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


DEFAULT_SUCCESS_FIELDS = ("success", "passed", "validated", "is_correct", "correct")
DEFAULT_OUTPUT_DIR = "out"

SAMPLE_TRACES = [
    {
        "trace_id": "sample-001",
        "success": True,
        "query": "How do I reset billing limits?",
        "steps": [
            {
                "type": "retriever",
                "name": "billing_docs",
                "documents": [{"id": "doc-billing-limits", "title": "Billing limits"}],
            },
            {"type": "tool", "name": "account_lookup"},
            {"type": "scorer", "name": "answer_faithfulness"},
        ],
        "citations": ["doc-billing-limits"],
    },
    {
        "trace_id": "sample-002",
        "success": False,
        "query": "What changed in invoice exports?",
        "steps": [{"type": "tool", "name": "invoice_exporter"}],
    },
    {
        "trace_id": "sample-003",
        "validated": True,
        "query": "Which docs explain SSO setup?",
        "route": [
            "retriever:identity_docs",
            "document:doc-sso-setup",
            "tool:workspace_settings",
            "scorer:citation_coverage",
        ],
        "nodes": [{"id": "policy-router", "kind": "router"}],
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile successful agent/RAG JSONL traces into positive-only routing datasets."
    )
    parser.add_argument(
        "--input",
        default=os.environ.get("TRACELOOM_INPUT"),
        help="Path to a JSONL trace file. Uses built-in sample data when omitted.",
    )
    parser.add_argument(
        "--output",
        default=os.environ.get("TRACELOOM_OUTPUT", DEFAULT_OUTPUT_DIR),
        help=f"Output directory. Defaults to {DEFAULT_OUTPUT_DIR}.",
    )
    parser.add_argument(
        "--success-fields",
        default=os.environ.get("TRACELOOM_SUCCESS_FIELDS", ",".join(DEFAULT_SUCCESS_FIELDS)),
        help="Comma-separated field names that mark a trace as successful.",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    traces: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_number}: expected a JSON object")
            traces.append(record)
    return traces


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value == 1
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "y", "1", "pass", "passed", "success"}
    return False


def success_field(trace: dict[str, Any], fields: Iterable[str]) -> str | None:
    for field in fields:
        if field in trace and truthy(trace[field]):
            return field
    metrics = trace.get("metrics")
    if isinstance(metrics, dict):
        for field in fields:
            if field in metrics and truthy(metrics[field]):
                return f"metrics.{field}"
    evaluation = trace.get("evaluation")
    if isinstance(evaluation, dict):
        for field in fields:
            if field in evaluation and truthy(evaluation[field]):
                return f"evaluation.{field}"
    return None


def add_component(components: list[dict[str, str]], seen: set[tuple[str, str]], kind: str, value: Any) -> None:
    component_id = normalize_id(value)
    if not component_id:
        return
    key = (kind, component_id)
    if key in seen:
        return
    seen.add(key)
    components.append({"kind": kind, "id": component_id})


def normalize_id(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("id", "name", "document_id", "doc_id", "node_id", "tool", "retriever", "scorer"):
            if key in value and value[key] is not None:
                return normalize_id(value[key])
    return ""


def infer_kind(text: str, fallback: str = "node") -> tuple[str, str]:
    if ":" in text:
        prefix, identifier = text.split(":", 1)
        prefix = prefix.strip().lower()
        identifier = identifier.strip()
        if prefix in {"tool", "retriever", "document", "doc", "scorer", "node", "router", "reranker"}:
            if prefix == "doc":
                prefix = "document"
            return prefix, identifier
    return fallback, text


def extract_documents_from_value(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("documents", "docs", "citations", "cited_documents"):
            docs = value.get(key)
            if isinstance(docs, list):
                return docs
    return []


def extract_components(trace: dict[str, Any]) -> list[dict[str, str]]:
    components: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for raw in as_list(trace.get("route")):
        if isinstance(raw, str):
            kind, identifier = infer_kind(raw)
            add_component(components, seen, kind, identifier)
        elif isinstance(raw, dict):
            kind = str(raw.get("kind") or raw.get("type") or "node").lower()
            add_component(components, seen, kind, raw)

    for step in as_list(trace.get("steps")):
        if not isinstance(step, dict):
            continue
        step_type = str(step.get("type") or step.get("kind") or "").lower()
        if step_type in {"tool", "tool_call"}:
            add_component(components, seen, "tool", step)
        elif step_type in {"retriever", "retrieval", "search"}:
            add_component(components, seen, "retriever", step)
        elif step_type in {"scorer", "score", "reranker", "ranker"}:
            add_component(components, seen, "scorer", step)
        elif step_type in {"router", "node"}:
            add_component(components, seen, "node", step)
        else:
            add_component(components, seen, "node", step)
        for document in extract_documents_from_value(step):
            add_component(components, seen, "document", document)

    for tool_call in as_list(trace.get("tool_calls")):
        add_component(components, seen, "tool", tool_call)

    for hit in as_list(trace.get("retriever_hits")):
        if isinstance(hit, dict):
            add_component(components, seen, "retriever", hit.get("retriever") or hit.get("name"))
            add_component(components, seen, "document", hit.get("document_id") or hit.get("doc_id") or hit)
        else:
            add_component(components, seen, "retriever", hit)

    for scorer in as_list(trace.get("scorer_choices")) + as_list(trace.get("scorers")):
        add_component(components, seen, "scorer", scorer)

    for key in ("cited_documents", "citations", "documents", "docs"):
        for document in as_list(trace.get(key)):
            add_component(components, seen, "document", document)

    for node in as_list(trace.get("nodes")):
        if isinstance(node, dict):
            kind = str(node.get("kind") or node.get("type") or "node").lower()
            add_component(components, seen, kind, node)
        else:
            add_component(components, seen, "node", node)

    return components


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def compile_routes(traces: list[dict[str, Any]], success_fields: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    positive_routes: list[dict[str, Any]] = []
    skipped_success_without_components = 0

    for index, trace in enumerate(traces, start=1):
        field = success_field(trace, success_fields)
        if not field:
            continue

        components = extract_components(trace)
        if not components:
            skipped_success_without_components += 1
            continue

        trace_id = str(trace.get("trace_id") or trace.get("id") or f"trace-{index:06d}")
        positive_routes.append(
            {
                "trace_id": trace_id,
                "query": trace.get("query") or trace.get("input") or trace.get("prompt") or "",
                "positive_route": [f"{item['kind']}:{item['id']}" for item in components],
                "components": components,
                "source_success_field": field,
            }
        )

    stats = {
        "total_traces": len(traces),
        "successful_traces": sum(1 for trace in traces if success_field(trace, success_fields)),
        "positive_routes": len(positive_routes),
        "skipped_success_without_components": skipped_success_without_components,
    }
    return positive_routes, stats


def write_positive_routes(routes: list[dict[str, Any]], output_dir: Path) -> None:
    path = output_dir / "positive_routes.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for route in routes:
            handle.write(json.dumps(route, ensure_ascii=False, sort_keys=True) + "\n")


def write_matrix(routes: list[dict[str, Any]], output_dir: Path) -> Counter[tuple[str, str]]:
    counter: Counter[tuple[str, str]] = Counter()
    examples: dict[tuple[str, str], set[str]] = defaultdict(set)
    for route in routes:
        trace_id = str(route["trace_id"])
        for component in route["components"]:
            key = (component["kind"], component["id"])
            counter[key] += 1
            examples[key].add(trace_id)

    path = output_dir / "node_success_matrix.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["component_kind", "component_id", "positive_trace_count", "example_trace_ids"])
        for (kind, component_id), count in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
            writer.writerow([kind, component_id, count, ";".join(sorted(examples[(kind, component_id)])[:5])])
    return counter


def write_report(
    routes: list[dict[str, Any]],
    stats: dict[str, Any],
    component_counts: Counter[tuple[str, str]],
    output_dir: Path,
    used_sample_data: bool,
) -> None:
    total = stats["total_traces"]
    success_rate = (stats["successful_traces"] / total * 100) if total else 0.0
    route_counts = Counter(" > ".join(route["positive_route"]) for route in routes)

    lines = [
        "# TraceLoom Report",
        "",
        f"- Input mode: {'built-in sample data' if used_sample_data else 'JSONL file'}",
        f"- Total traces: {stats['total_traces']}",
        f"- Successful traces: {stats['successful_traces']} ({success_rate:.1f}%)",
        f"- Positive routes emitted: {stats['positive_routes']}",
        f"- Successful traces skipped without route components: {stats['skipped_success_without_components']}",
        "",
        "## Top Components",
        "",
    ]

    if component_counts:
        lines.extend(["| Kind | Component | Positive traces |", "| --- | --- | ---: |"])
        for (kind, component_id), count in component_counts.most_common(10):
            lines.append(f"| {kind} | `{component_id}` | {count} |")
    else:
        lines.append("No components were extracted.")

    lines.extend(["", "## Top Routes", ""])
    if route_counts:
        lines.extend(["| Route | Count |", "| --- | ---: |"])
        for route, count in route_counts.most_common(10):
            lines.append(f"| `{route}` | {count} |")
    else:
        lines.append("No positive routes were emitted.")

    (output_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    success_fields = [field.strip() for field in args.success_fields.split(",") if field.strip()]
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.input:
        traces = read_jsonl(Path(args.input))
        used_sample_data = False
    else:
        traces = SAMPLE_TRACES
        used_sample_data = True

    routes, stats = compile_routes(traces, success_fields)
    write_positive_routes(routes, output_dir)
    component_counts = write_matrix(routes, output_dir)
    write_report(routes, stats, component_counts, output_dir, used_sample_data)

    print(f"TraceLoom compiled {len(routes)} positive routes from {len(traces)} traces.")
    print(f"Wrote {output_dir / 'positive_routes.jsonl'}")
    print(f"Wrote {output_dir / 'node_success_matrix.csv'}")
    print(f"Wrote {output_dir / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
