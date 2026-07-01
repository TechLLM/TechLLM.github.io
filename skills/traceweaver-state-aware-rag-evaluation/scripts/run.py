#!/usr/bin/env python3
"""TraceWeaver rag-state-grader: deterministic state-aware RAG trace evaluation."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SAMPLE_TRACE_JSONL = """
{"type":"retrieval","query":"Can this customer return the laptop and what warranty applies?","documents":[{"doc_id":"kb:return-policy","passage_id":"p1","score":0.94,"text":"Customers may return eligible items within 30 days of delivery."},{"doc_id":"kb:warranty","passage_id":"p3","score":0.89,"text":"The standard laptop warranty covers defects for 12 months."}]}
{"type":"tool_call","tool":"record.update","target":"records/customer-123.json","operation":"update","input":{"status":"eligible_for_return"}}
{"type":"diff","target":"records/customer-123.json","changes":[{"path":"status","before":"unknown","after":"eligible_for_return"}]}
{"type":"edit","target":"workspace/answer.md","operation":"upsert","content":"The customer is eligible for the 30-day return window and has a 12-month warranty."}
{"type":"final_response","answer":"The customer is eligible for return within 30 days and the laptop has a 12-month warranty.","citations":["kb:return-policy#p1","kb:warranty#p3"],"claims":[{"text":"Return is allowed within 30 days.","supported_by":["kb:return-policy#p1"]},{"text":"Laptop warranty lasts 12 months.","supported_by":["kb:warranty#p3"]}]}
""".strip()

SAMPLE_EXPECTED = {
    "required_evidence": [
        {"doc_id": "kb:return-policy", "passage_id": "p1"},
        {"doc_id": "kb:warranty", "passage_id": "p3"},
    ],
    "expected_actions": [
        {
            "type": "tool_call",
            "tool": "record.update",
            "target": "records/customer-123.json",
            "operation": "update",
            "contains": "eligible_for_return",
        }
    ],
    "expected_diffs": [
        {
            "target": "records/customer-123.json",
            "path": "status",
            "after": "eligible_for_return",
        },
        {
            "target": "workspace/answer.md",
            "contains": "30-day return window",
        },
    ],
    "answer_requirements": {
        "must_include": ["30 days", "12-month warranty"],
        "must_cite": ["kb:return-policy", "kb:warranty"],
        "must_not_include": ["lifetime warranty"],
    },
}


@dataclass(frozen=True)
class EvidenceRef:
    doc_id: str
    passage_id: str | None = None
    text: str = ""

    @property
    def compact(self) -> str:
        if self.passage_id:
            return f"{self.doc_id}#{self.passage_id}"
        return self.doc_id


def load_trace(path: str | None) -> tuple[list[dict[str, Any]], str]:
    if path is None:
        raw = SAMPLE_TRACE_JSONL
        source = "built-in sample trace"
    else:
        raw = Path(path).read_text(encoding="utf-8")
        source = path

    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(raw.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            value = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSONL at line {line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise SystemExit(f"Trace line {line_number} must be a JSON object.")
        events.append(value)
    if not events:
        raise SystemExit("Trace is empty.")
    return events, source


def load_expected(path: str | None) -> tuple[dict[str, Any], str]:
    if path is None:
        return SAMPLE_EXPECTED, "built-in expected spec"
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid expected JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit("Expected specification must be a JSON object.")
    return value, path


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def stringify(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False).lower()


def canonical_doc_id(item: dict[str, Any]) -> str | None:
    for key in ("doc_id", "document_id", "source_id", "id", "doc"):
        value = item.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def canonical_passage_id(item: dict[str, Any]) -> str | None:
    for key in ("passage_id", "chunk_id", "node_id", "record_id", "section_id", "passage"):
        value = item.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def parse_citation(citation: Any) -> EvidenceRef | None:
    if isinstance(citation, dict):
        doc_id = canonical_doc_id(citation)
        if not doc_id:
            return None
        return EvidenceRef(doc_id=doc_id, passage_id=canonical_passage_id(citation))
    if not isinstance(citation, str) or not citation.strip():
        return None
    text = citation.strip()
    if "#" in text:
        doc_id, passage_id = text.split("#", 1)
        return EvidenceRef(doc_id=doc_id, passage_id=passage_id or None)
    return EvidenceRef(doc_id=text)


def extract_retrieved(events: list[dict[str, Any]]) -> list[EvidenceRef]:
    refs: list[EvidenceRef] = []
    for event in events:
        event_type = str(event.get("type", "")).lower()
        candidate_lists = []
        for key in ("documents", "results", "retrieved", "sources"):
            if key in event:
                candidate_lists.extend(as_list(event.get(key)))
        if event_type in {"retrieval", "retrieved", "search_result", "document_retrieved"}:
            candidate_lists.append(event)

        for item in candidate_lists:
            if not isinstance(item, dict):
                continue
            doc_id = canonical_doc_id(item)
            if doc_id:
                refs.append(
                    EvidenceRef(
                        doc_id=doc_id,
                        passage_id=canonical_passage_id(item),
                        text=str(item.get("text") or item.get("content") or ""),
                    )
                )
    return dedupe_refs(refs)


def extract_answer(events: list[dict[str, Any]]) -> tuple[str, list[EvidenceRef], list[Any]]:
    answer_parts: list[str] = []
    citations: list[EvidenceRef] = []
    claims: list[Any] = []
    for event in events:
        event_type = str(event.get("type", "")).lower()
        if event_type in {"final_response", "answer", "response", "final"} or "answer" in event:
            answer_text = event.get("answer") or event.get("text") or event.get("content")
            if isinstance(answer_text, str):
                answer_parts.append(answer_text)
                for raw in re.findall(r"([A-Za-z0-9_.:/-]+#[A-Za-z0-9_.:/-]+)", answer_text):
                    parsed = parse_citation(raw)
                    if parsed:
                        citations.append(parsed)
            for citation in as_list(event.get("citations")) + as_list(event.get("sources")):
                parsed = parse_citation(citation)
                if parsed:
                    citations.append(parsed)
            claims.extend(as_list(event.get("claims")))
    return "\n".join(answer_parts), dedupe_refs(citations), claims


def dedupe_refs(refs: list[EvidenceRef]) -> list[EvidenceRef]:
    seen: set[tuple[str, str | None]] = set()
    unique: list[EvidenceRef] = []
    for ref in refs:
        key = (ref.doc_id, ref.passage_id)
        if key not in seen:
            seen.add(key)
            unique.append(ref)
    return unique


def evidence_matches(spec: dict[str, Any], ref: EvidenceRef) -> bool:
    expected_doc = canonical_doc_id(spec)
    if expected_doc and expected_doc != ref.doc_id:
        return False
    expected_passage = canonical_passage_id(spec)
    if expected_passage and expected_passage != ref.passage_id:
        return False
    expected_contains = spec.get("contains")
    if isinstance(expected_contains, str) and expected_contains.lower() not in ref.text.lower():
        return False
    return True


def citation_matches(expected: Any, ref: EvidenceRef) -> bool:
    parsed = parse_citation(expected)
    if parsed:
        if parsed.doc_id != ref.doc_id:
            return False
        return parsed.passage_id is None or parsed.passage_id == ref.passage_id
    if isinstance(expected, str):
        return expected == ref.doc_id or expected == ref.compact
    return False


def event_target(event: dict[str, Any]) -> str:
    for key in ("target", "path", "file", "node_id", "record_id", "object_id"):
        value = event.get(key)
        if isinstance(value, str):
            return value
    return ""


def action_matches(spec: dict[str, Any], event: dict[str, Any]) -> bool:
    event_type = str(event.get("type", "")).lower()
    expected_type = str(spec.get("type", "")).lower()
    if expected_type and expected_type != event_type:
        return False

    for key in ("tool", "operation", "name", "action"):
        expected = spec.get(key)
        if expected is not None and str(event.get(key, "")).lower() != str(expected).lower():
            return False

    expected_target = spec.get("target")
    if isinstance(expected_target, str) and expected_target != event_target(event):
        return False

    expected_contains = spec.get("contains")
    if isinstance(expected_contains, str) and expected_contains.lower() not in stringify(event):
        return False

    return True


def diff_matches(spec: dict[str, Any], event: dict[str, Any]) -> bool:
    expected_target = spec.get("target")
    if isinstance(expected_target, str) and expected_target != event_target(event):
        return False

    expected_contains = spec.get("contains")
    if isinstance(expected_contains, str) and expected_contains.lower() not in stringify(event):
        return False

    expected_path = spec.get("path")
    expected_after = spec.get("after")
    if expected_path is None and expected_after is None:
        return True

    changes = as_list(event.get("changes"))
    if not changes and any(key in event for key in ("path", "after", "value", "new")):
        changes = [event]

    for change in changes:
        if not isinstance(change, dict):
            continue
        if expected_path is not None and change.get("path") != expected_path:
            continue
        if expected_after is not None:
            actual_after = change.get("after", change.get("value", change.get("new")))
            if actual_after != expected_after:
                continue
        return True
    return False


def ratio(matches: int, total: int) -> float:
    if total == 0:
        return 1.0
    return round(matches / total, 4)


def grade(events: list[dict[str, Any]], expected: dict[str, Any]) -> dict[str, Any]:
    retrieved = extract_retrieved(events)
    answer_text, citations, claims = extract_answer(events)
    expected_evidence = [item for item in as_list(expected.get("required_evidence")) if isinstance(item, dict)]
    expected_actions = [item for item in as_list(expected.get("expected_actions")) if isinstance(item, dict)]
    expected_diffs = [item for item in as_list(expected.get("expected_diffs")) if isinstance(item, dict)]
    answer_requirements = expected.get("answer_requirements") or {}
    if not isinstance(answer_requirements, dict):
        answer_requirements = {}

    missing_evidence = [
        spec for spec in expected_evidence if not any(evidence_matches(spec, ref) for ref in retrieved)
    ]
    retrieval_coverage = ratio(len(expected_evidence) - len(missing_evidence), len(expected_evidence))

    must_cite = as_list(answer_requirements.get("must_cite"))
    weak_citations = [item for item in must_cite if not any(citation_matches(item, ref) for ref in citations)]
    citation_score = ratio(len(must_cite) - len(weak_citations), len(must_cite))

    retrieval_score = round((0.7 * retrieval_coverage) + (0.3 * citation_score), 4)

    action_events = [
        event
        for event in events
        if str(event.get("type", "")).lower()
        in {"tool_call", "action", "edit", "diff", "file_edit", "node_update", "record_update"}
    ]
    missing_actions = [
        spec for spec in expected_actions if not any(action_matches(spec, event) for event in action_events)
    ]
    incorrect_diffs = [
        spec for spec in expected_diffs if not any(diff_matches(spec, event) for event in action_events)
    ]
    action_match_score = ratio(len(expected_actions) - len(missing_actions), len(expected_actions))
    diff_match_score = ratio(len(expected_diffs) - len(incorrect_diffs), len(expected_diffs))
    if expected_actions and expected_diffs:
        action_score = round((0.5 * action_match_score) + (0.5 * diff_match_score), 4)
    elif expected_actions:
        action_score = action_match_score
    else:
        action_score = diff_match_score

    answer_lower = answer_text.lower()
    must_include = [str(item) for item in as_list(answer_requirements.get("must_include"))]
    missing_answer_phrases = [phrase for phrase in must_include if phrase.lower() not in answer_lower]
    include_score = ratio(len(must_include) - len(missing_answer_phrases), len(must_include))

    forbidden = [str(item) for item in as_list(answer_requirements.get("must_not_include"))]
    forbidden_hits = [phrase for phrase in forbidden if phrase.lower() in answer_lower]
    forbidden_score = 0.0 if forbidden_hits else 1.0

    supported_claims = [str(item).lower() for item in as_list(answer_requirements.get("supported_claims"))]
    hallucinated_claims: list[Any] = []
    retrieved_compacts = {ref.compact for ref in retrieved} | {ref.doc_id for ref in retrieved}
    for claim in claims:
        if isinstance(claim, dict):
            support = [str(item) for item in as_list(claim.get("supported_by"))]
            if not support or not any(item in retrieved_compacts for item in support):
                hallucinated_claims.append(claim.get("text") or claim)
        elif isinstance(claim, str) and supported_claims and claim.lower() not in supported_claims:
            hallucinated_claims.append(claim)
    hallucinated_claims.extend(forbidden_hits)
    hallucination_score = 0.0 if hallucinated_claims else 1.0

    answer_score = round(
        (0.45 * include_score)
        + (0.25 * citation_score)
        + (0.15 * forbidden_score)
        + (0.15 * hallucination_score),
        4,
    )
    overall_score = round((0.4 * retrieval_score) + (0.35 * action_score) + (0.25 * answer_score), 4)

    return {
        "scores": {
            "retrieval": retrieval_score,
            "action": action_score,
            "answer": answer_score,
            "overall": overall_score,
        },
        "details": {
            "retrieved_evidence": [ref.compact for ref in retrieved],
            "citations": [ref.compact for ref in citations],
            "answer_excerpt": answer_text[:300],
            "coverage": {
                "required_evidence": retrieval_coverage,
                "required_citations": citation_score,
                "expected_actions": action_match_score,
                "expected_diffs": diff_match_score,
                "required_answer_phrases": include_score,
            },
        },
        "failure_report": {
            "missing_evidence": missing_evidence,
            "missing_actions": missing_actions,
            "incorrect_edits": incorrect_diffs,
            "weak_citations": weak_citations,
            "missing_answer_phrases": missing_answer_phrases,
            "hallucinated_claims": hallucinated_claims,
        },
        "environment": {
            "optional_api_key_detected": bool(
                os.getenv("OPENAI_API_KEY") or os.getenv("TRACEWEAVER_API_KEY")
            ),
            "external_scoring": "disabled",
        },
    }


def render_text(report: dict[str, Any], trace_source: str, expected_source: str) -> str:
    scores = report["scores"]
    failures = report["failure_report"]
    lines = [
        "TraceWeaver State-Aware RAG Evaluation",
        f"Trace: {trace_source}",
        f"Expected: {expected_source}",
        "",
        "Scores:",
        f"  retrieval: {scores['retrieval']:.2f}",
        f"  action:    {scores['action']:.2f}",
        f"  answer:    {scores['answer']:.2f}",
        f"  overall:   {scores['overall']:.2f}",
        "",
        "Failure report:",
    ]
    any_failure = False
    for key, value in failures.items():
        if value:
            any_failure = True
            lines.append(f"  {key}:")
            for item in value:
                lines.append(f"    - {json.dumps(item, sort_keys=True, ensure_ascii=False)}")
    if not any_failure:
        lines.append("  none")
    lines.extend(
        [
            "",
            "Environment:",
            f"  optional_api_key_detected: {report['environment']['optional_api_key_detected']}",
            "  external_scoring: disabled",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rag-state-grader",
        description="Grade RAG and agent traces as retrieval, action, and answer state transitions.",
    )
    parser.add_argument("--trace", help="Path to a JSONL execution trace.")
    parser.add_argument("--expected", help="Path to an expected evidence/action/diff JSON specification.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format.")
    parser.add_argument(
        "--fail-under",
        type=float,
        default=None,
        help="Exit with status 2 if the overall score is below this threshold.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    events, trace_source = load_trace(args.trace)
    expected, expected_source = load_expected(args.expected)
    report = grade(events, expected)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(render_text(report, trace_source, expected_source))

    if args.fail_under is not None and report["scores"]["overall"] < args.fail_under:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
