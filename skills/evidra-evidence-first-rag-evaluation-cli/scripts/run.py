#!/usr/bin/env python3
"""Evidra reference CLI for evidence-first RAG evaluation.

This module evaluates observable RAG execution evidence: retrieval events,
citation events, forbidden source use, and post-state assertions. It is small,
offline, deterministic, and suitable as installable skill reference code.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


SAMPLE_TRACE_JSONL = """\
{"event":"retrieval","query_id":"q1","document_id":"policy-2026","passage_id":"P4","domain":"benefits","document_type":"policy","rank":1,"score":0.93}
{"event":"retrieval","query_id":"q1","document_id":"faq-2026","passage_id":"P1","domain":"benefits","document_type":"faq","rank":2,"score":0.88}
{"event":"citation","document_id":"policy-2026","passage_id":"P4"}
{"event":"citation","document_id":"faq-2026","passage_id":"P1"}
{"event":"tool_call","tool":"audit_log.create","status":"success","name":"post_state_check"}
"""

SAMPLE_SPEC_YAML = """\
evaluation_id: sample-benefits-rag
required_documents:
  - id: policy-2026
    type: policy
    domain: benefits
    must_cite: true
    required_passages:
      - P4
  - id: faq-2026
    type: faq
    domain: benefits
    must_cite: true
    required_passages:
      - P1
forbidden_sources:
  - deprecated-wiki-2020
post_state_assertions:
  - id: audit-log-written
    event: tool_call
    tool: audit_log.create
    status: success
"""

SAMPLE_ANSWER_TEXT = (
    "Employees can update benefits during open enrollment. "
    "Sources: policy-2026#P4 and faq-2026#P1."
)


Report = Dict[str, Any]
TraceEvent = Dict[str, Any]
Spec = Dict[str, Any]


def parse_scalar(value: str) -> Any:
    """Parse a small YAML scalar subset into a Python value."""
    value = value.strip()
    if value == "":
        return ""
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "Null", "none", "None", "~"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        body = value[1:-1].strip()
        if not body:
            return []
        return [parse_scalar(part.strip()) for part in body.split(",")]
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def parse_simple_yaml(text: str) -> Spec:
    """Parse the compact YAML subset used by Evidra evidence specs.

    If PyYAML is installed in the caller's environment, it is used. Otherwise
    this function supports root scalar keys, root lists, list items as
    dictionaries, and one nested list of scalar values inside each dictionary.
    """
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
        if isinstance(data, dict):
            return data
        raise ValueError("YAML root must be a mapping")
    except ModuleNotFoundError:
        pass

    root: Spec = {}
    current_section: Optional[str] = None
    current_item: Optional[Dict[str, Any]] = None
    current_sublist: Optional[str] = None

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()

        if indent == 0:
            current_item = None
            current_sublist = None
            if ":" not in stripped:
                raise ValueError(f"line {line_number}: expected 'key: value'")
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value:
                root[key] = parse_scalar(value)
                current_section = None
            else:
                root[key] = []
                current_section = key
            continue

        if current_section is None:
            raise ValueError(f"line {line_number}: indented value without section")

        section_value = root.setdefault(current_section, [])
        if not isinstance(section_value, list):
            raise ValueError(f"line {line_number}: section {current_section!r} is not a list")

        if indent == 2 and stripped.startswith("- "):
            current_sublist = None
            item_text = stripped[2:].strip()
            if ":" in item_text:
                key, value = item_text.split(":", 1)
                current_item = {key.strip(): parse_scalar(value.strip())}
                section_value.append(current_item)
            else:
                current_item = None
                section_value.append(parse_scalar(item_text))
            continue

        if indent == 4 and current_item is not None:
            if ":" not in stripped:
                raise ValueError(f"line {line_number}: expected nested 'key: value'")
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value:
                current_item[key] = parse_scalar(value)
                current_sublist = None
            else:
                current_item[key] = []
                current_sublist = key
            continue

        if indent == 6 and current_item is not None and current_sublist:
            if not stripped.startswith("- "):
                raise ValueError(f"line {line_number}: expected nested list item")
            current_item[current_sublist].append(parse_scalar(stripped[2:].strip()))
            continue

        raise ValueError(f"line {line_number}: unsupported YAML indentation")

    return root


def load_jsonl_text(text: str) -> List[TraceEvent]:
    """Load trace events from JSON Lines text."""
    events: List[TraceEvent] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"trace JSONL line {line_number}: {exc.msg}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"trace JSONL line {line_number}: each line must be an object")
        events.append(value)
    return events


def load_text_file(path: str) -> str:
    """Read a UTF-8 text file with a concise error on failure."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValueError(f"file not found: {path}") from exc
    except OSError as exc:
        raise ValueError(f"could not read {path}: {exc}") from exc


def source_id(event: TraceEvent) -> Optional[str]:
    """Return the best source identifier from a trace event."""
    for key in ("document_id", "source_id", "doc_id"):
        value = event.get(key)
        if value is not None:
            return str(value)
    return None


def answer_mentions(answer_text: str, token: str) -> bool:
    """Return true when answer text contains a source token as a separate identifier."""
    if not token:
        return False
    pattern = r"(?<![A-Za-z0-9_.-])" + re.escape(token) + r"(?![A-Za-z0-9_.-])"
    return re.search(pattern, answer_text) is not None


def fraction(numerator: int, denominator: int) -> float:
    """Return a rounded fraction, treating empty requirements as fully satisfied."""
    if denominator == 0:
        return 1.0
    return round(numerator / denominator, 4)


def group_rates(required_documents: Sequence[Dict[str, Any]], retrieved_ids: set[str], field: str) -> Dict[str, Dict[str, Any]]:
    """Compute retrieval rates grouped by a document field such as domain or type."""
    grouped: Dict[str, Dict[str, int]] = {}
    for doc in required_documents:
        group = str(doc.get(field) or "unknown")
        entry = grouped.setdefault(group, {"required": 0, "retrieved": 0})
        entry["required"] += 1
        if str(doc.get("id")) in retrieved_ids:
            entry["retrieved"] += 1
    return {
        group: {
            "required": counts["required"],
            "retrieved": counts["retrieved"],
            "retrieval_hit_rate": fraction(counts["retrieved"], counts["required"]),
        }
        for group, counts in sorted(grouped.items())
    }


def assertion_matches(assertion: Dict[str, Any], event: TraceEvent) -> bool:
    """Return true when a trace event satisfies a post-state assertion."""
    ignored = {"id", "description"}
    for key, expected in assertion.items():
        if key in ignored:
            continue
        if key == "kind":
            actual = event.get("event")
        else:
            actual = event.get(key)
        if str(actual) != str(expected):
            return False
    return True


def covered_citation_units(
    required_documents: Sequence[Dict[str, Any]],
    citation_pairs: set[Tuple[str, Optional[str]]],
    citation_doc_ids: set[str],
    answer_text: str,
) -> Tuple[int, int, List[Dict[str, Any]]]:
    """Count required citation units and return missing citation findings."""
    required_count = 0
    covered_count = 0
    findings: List[Dict[str, Any]] = []

    for doc in required_documents:
        if doc.get("must_cite", True) is False:
            continue
        doc_id = str(doc.get("id"))
        passages = doc.get("required_passages") or []
        if passages:
            for passage in passages:
                passage_id = str(passage)
                required_count += 1
                has_trace_citation = (doc_id, passage_id) in citation_pairs
                has_answer_reference = answer_mentions(answer_text, doc_id) and answer_mentions(
                    answer_text, passage_id
                )
                if has_trace_citation or has_answer_reference:
                    covered_count += 1
                else:
                    findings.append(
                        {
                            "code": "missing_required_citation",
                            "severity": "error",
                            "message": f"Missing citation for {doc_id}#{passage_id}.",
                            "evidence": {"document_id": doc_id, "passage_id": passage_id},
                        }
                    )
        else:
            required_count += 1
            if doc_id in citation_doc_ids or answer_mentions(answer_text, doc_id):
                covered_count += 1
            else:
                findings.append(
                    {
                        "code": "missing_required_citation",
                        "severity": "error",
                        "message": f"Missing citation for {doc_id}.",
                        "evidence": {"document_id": doc_id},
                    }
                )

    return required_count, covered_count, findings


def evaluate_run(events: Sequence[TraceEvent], spec: Spec, answer_text: str) -> Report:
    """Evaluate trace events, evidence expectations, and answer text."""
    required_documents = spec.get("required_documents") or []
    if not isinstance(required_documents, list):
        raise ValueError("spec field 'required_documents' must be a list")

    forbidden_sources = {str(item) for item in (spec.get("forbidden_sources") or [])}
    post_state_assertions = spec.get("post_state_assertions") or []
    if not isinstance(post_state_assertions, list):
        raise ValueError("spec field 'post_state_assertions' must be a list")

    retrieval_events = [event for event in events if event.get("event") == "retrieval"]
    citation_events = [event for event in events if event.get("event") == "citation"]

    retrieved_ids = {sid for sid in (source_id(event) for event in retrieval_events) if sid}
    all_trace_source_ids = {sid for sid in (source_id(event) for event in events) if sid}
    citation_doc_ids = {sid for sid in (source_id(event) for event in citation_events) if sid}
    citation_pairs = {
        (str(source_id(event)), str(event.get("passage_id")) if event.get("passage_id") is not None else None)
        for event in citation_events
        if source_id(event)
    }

    findings: List[Dict[str, Any]] = []
    retrieved_required = 0
    required_doc_ids: List[str] = []
    for doc in required_documents:
        if not isinstance(doc, dict):
            raise ValueError("each required_documents item must be a mapping")
        if "id" not in doc:
            raise ValueError("each required_documents item must include 'id'")
        doc_id = str(doc["id"])
        required_doc_ids.append(doc_id)
        if doc_id in retrieved_ids:
            retrieved_required += 1
        else:
            findings.append(
                {
                    "code": "missing_required_retrieval",
                    "severity": "error",
                    "message": f"Required document {doc_id} was not retrieved.",
                    "evidence": {"document_id": doc_id},
                }
            )

    required_citations, covered_citations, citation_findings = covered_citation_units(
        required_documents, citation_pairs, citation_doc_ids, answer_text
    )
    findings.extend(citation_findings)

    forbidden_used = sorted(
        source for source in forbidden_sources if source in all_trace_source_ids or answer_mentions(answer_text, source)
    )
    for source in forbidden_used:
        findings.append(
            {
                "code": "forbidden_source_used",
                "severity": "error",
                "message": f"Forbidden source {source} appeared in trace or answer.",
                "evidence": {"source_id": source},
            }
        )

    assertions_met = 0
    for assertion in post_state_assertions:
        if not isinstance(assertion, dict):
            raise ValueError("each post_state_assertions item must be a mapping")
        if any(assertion_matches(assertion, event) for event in events):
            assertions_met += 1
        else:
            assertion_id = str(assertion.get("id", "unnamed"))
            findings.append(
                {
                    "code": "missing_post_state_assertion",
                    "severity": "error",
                    "message": f"Post-state assertion {assertion_id} was not observed.",
                    "evidence": {"assertion": assertion},
                }
            )

    required_documents_count = len(required_documents)
    retrieval_hit_rate = fraction(retrieved_required, required_documents_count)
    citation_coverage = fraction(covered_citations, required_citations)
    forbidden_source_score = 1.0 if not forbidden_used else 0.0
    post_state_assertion_rate = fraction(assertions_met, len(post_state_assertions))
    overall = round(
        (retrieval_hit_rate + citation_coverage + forbidden_source_score + post_state_assertion_rate) / 4,
        4,
    )

    report: Report = {
        "evaluation_id": str(spec.get("evaluation_id", "evidra-evaluation")),
        "passed": overall == 1.0 and not findings,
        "scores": {
            "overall": overall,
            "retrieval_hit_rate": retrieval_hit_rate,
            "citation_coverage": citation_coverage,
            "forbidden_source_score": forbidden_source_score,
            "post_state_assertion_rate": post_state_assertion_rate,
        },
        "counts": {
            "required_documents": required_documents_count,
            "retrieved_required_documents": retrieved_required,
            "required_citations": required_citations,
            "covered_citations": covered_citations,
            "forbidden_sources_used": len(forbidden_used),
            "post_state_assertions": len(post_state_assertions),
            "post_state_assertions_met": assertions_met,
        },
        "by_domain": group_rates(required_documents, retrieved_ids, "domain"),
        "by_document_type": group_rates(required_documents, retrieved_ids, "type"),
        "findings": sorted(findings, key=lambda item: (item["code"], item["message"])),
    }
    return report


def sample_inputs() -> Tuple[List[TraceEvent], Spec, str]:
    """Return built-in sample inputs for self-testing and examples."""
    return load_jsonl_text(SAMPLE_TRACE_JSONL), parse_simple_yaml(SAMPLE_SPEC_YAML), SAMPLE_ANSWER_TEXT


def read_optional_env_keys() -> None:
    """Read optional environment keys without printing or requiring them."""
    _ = os.environ.get("EVIDRA_API_KEY")


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Evaluate RAG trace JSONL, evidence spec YAML, and answer text.",
    )
    parser.add_argument("--trace-jsonl", help="Path to RAG execution trace JSONL.")
    parser.add_argument("--spec-yaml", help="Path to evidence expectation YAML.")
    parser.add_argument("--answer", help="Path to generated answer text.")
    parser.add_argument("--output", help="Optional path to write the JSON report.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    parser.add_argument("--selftest", action="store_true", help="Run on built-in sample data.")
    return parser


def render_json(report: Report, pretty: bool = False) -> str:
    """Render a report as deterministic JSON."""
    if pretty:
        return json.dumps(report, indent=2, sort_keys=True) + "\n"
    return json.dumps(report, separators=(",", ":"), sort_keys=True) + "\n"


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    """Run the Evidra command-line interface."""
    read_optional_env_keys()
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        if args.selftest or not any((args.trace_jsonl, args.spec_yaml, args.answer)):
            events, spec, answer_text = sample_inputs()
        else:
            missing = [
                flag
                for flag, value in (
                    ("--trace-jsonl", args.trace_jsonl),
                    ("--spec-yaml", args.spec_yaml),
                    ("--answer", args.answer),
                )
                if not value
            ]
            if missing:
                raise ValueError("missing required arguments: " + ", ".join(missing))
            events = load_jsonl_text(load_text_file(args.trace_jsonl))
            spec = parse_simple_yaml(load_text_file(args.spec_yaml))
            answer_text = load_text_file(args.answer)

        report = evaluate_run(events, spec, answer_text)
        output = render_json(report, pretty=args.pretty)
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
        else:
            sys.stdout.write(output)
        return 0
    except ValueError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2
    except OSError as exc:
        sys.stderr.write(f"error: could not write output: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(run_cli())
