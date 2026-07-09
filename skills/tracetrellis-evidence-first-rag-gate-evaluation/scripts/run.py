#!/usr/bin/env python3
"""TraceTrellis reference CLI for offline evidence-first RAG gate evaluation.

The command reads JSONL traces and a JSON evidence manifest, then emits
deterministic retrieval, action, and data-accuracy scores. It does not call any
network services. Optional LLM judge output can be merged from a local file or
an environment variable, but deterministic evidence checks remain authoritative.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

VERSION = "0.1.0"
TOOL_NAME = "rag-evidence-grader"

SAMPLE_TRACES: List[Dict[str, Any]] = [
    {
        "run_id": "refund-window",
        "query": "How long does a US customer have to request a refund?",
        "selected_documents": [
            {"id": "policy/refunds-2026", "score": 0.94},
            {"id": "faq/refunds", "score": 0.81},
        ],
        "actions": [
            {"type": "retrieve", "target": "policy/refunds-2026"},
            {"type": "cite", "target": "policy/refunds-2026"},
        ],
        "artifacts": {
            "facts": {
                "refund_window_days": 30,
                "region": "US",
            }
        },
    }
]

SAMPLE_MANIFEST: Dict[str, Any] = {
    "cases": [
        {
            "run_id": "refund-window",
            "required_documents": ["policy/refunds-2026"],
            "optional_documents": ["faq/refunds"],
            "forbidden_documents": ["policy/refunds-2021"],
            "required_actions": [
                {"type": "retrieve", "target": "policy/refunds-2026"},
                {"type": "cite", "target": "policy/refunds-2026"},
            ],
            "expected_facts": {
                "refund_window_days": 30,
                "region": "US",
            },
        }
    ]
}


def round_score(value: float) -> float:
    """Round score values consistently for deterministic reports."""
    return round(float(value), 3)


def stable_unique(values: Iterable[str]) -> List[str]:
    """Return unique non-empty strings while preserving first-seen order."""
    seen = set()
    result: List[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def item_id(item: Any) -> Optional[str]:
    """Extract a document or node identifier from a trace item."""
    if isinstance(item, str):
        return item
    if isinstance(item, Mapping):
        for key in ("id", "doc_id", "document_id", "node_id", "source_id", "target"):
            value = item.get(key)
            if isinstance(value, str) and value:
                return value
    return None


def collect_document_ids(trace: Mapping[str, Any]) -> List[str]:
    """Collect selected or retrieved document identifiers from a trace record."""
    fields = (
        "selected_documents",
        "selected_nodes",
        "retrieved_documents",
        "retrieval_results",
        "documents",
    )
    found: List[str] = []
    for field in fields:
        value = trace.get(field)
        if isinstance(value, list):
            found.extend(doc_id for doc_id in (item_id(item) for item in value) if doc_id)
        elif isinstance(value, Mapping):
            found.extend(str(key) for key in value.keys())
    return stable_unique(found)


def normalize_action(action: Any) -> Optional[Dict[str, str]]:
    """Normalize an action record to a comparable type/target dictionary."""
    if isinstance(action, str):
        if ":" in action:
            action_type, target = action.split(":", 1)
            return {"type": action_type.strip(), "target": target.strip()}
        return {"type": action.strip(), "target": ""}
    if not isinstance(action, Mapping):
        return None
    action_type = action.get("type") or action.get("name") or action.get("action")
    target = (
        action.get("target")
        or action.get("document_id")
        or action.get("doc_id")
        or action.get("node_id")
        or action.get("id")
        or ""
    )
    if not isinstance(action_type, str):
        return None
    if not isinstance(target, str):
        target = str(target)
    return {"type": action_type, "target": target}


def collect_actions(trace: Mapping[str, Any]) -> List[Dict[str, str]]:
    """Collect normalized action records from a trace."""
    raw_actions = trace.get("actions", [])
    if not isinstance(raw_actions, list):
        raw_actions = []
    normalized = [normalize_action(action) for action in raw_actions]
    return [action for action in normalized if action is not None]


def action_key(action: Mapping[str, str]) -> Tuple[str, str]:
    """Return the comparison key for a normalized action."""
    return (str(action.get("type", "")), str(action.get("target", "")))


def collect_facts(trace: Mapping[str, Any]) -> Dict[str, Any]:
    """Collect fact artifacts from supported trace locations."""
    facts: Dict[str, Any] = {}
    top_level = trace.get("facts")
    if isinstance(top_level, Mapping):
        facts.update(top_level)
    artifacts = trace.get("artifacts")
    if isinstance(artifacts, Mapping) and isinstance(artifacts.get("facts"), Mapping):
        facts.update(artifacts["facts"])
    return facts


def index_by_run_id(records: Any) -> Dict[str, Dict[str, Any]]:
    """Index records by run_id with validation."""
    if isinstance(records, Mapping):
        if "cases" in records and isinstance(records["cases"], list):
            iterable = records["cases"]
        else:
            iterable = []
            for run_id, value in records.items():
                if isinstance(value, Mapping):
                    item = dict(value)
                else:
                    item = {"value": value}
                item.setdefault("run_id", run_id)
                iterable.append(item)
    elif isinstance(records, list):
        iterable = records
    else:
        raise ValueError("expected a JSON object or list of records")

    indexed: Dict[str, Dict[str, Any]] = {}
    for item in iterable:
        if not isinstance(item, Mapping):
            raise ValueError("each record must be a JSON object")
        run_id = item.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            raise ValueError("each record must include a non-empty string run_id")
        indexed[run_id] = dict(item)
    return indexed


def answer_summary(answer: Optional[Mapping[str, Any]], selected_docs: Sequence[str]) -> Optional[Dict[str, Any]]:
    """Summarize optional answer citations and unsupported citation failures."""
    if answer is None:
        return None
    citations = answer.get("citations", [])
    if isinstance(citations, str):
        citations = [citations]
    if not isinstance(citations, list):
        citations = []
    citation_ids = stable_unique(str(item) for item in citations if item)
    selected = set(selected_docs)
    unsupported = [citation for citation in citation_ids if citation not in selected]
    text = answer.get("text")
    return {
        "present": bool(text),
        "cited_documents": citation_ids,
        "unsupported_citations": unsupported,
    }


def score_case(
    case: Mapping[str, Any],
    trace: Optional[Mapping[str, Any]],
    answer: Optional[Mapping[str, Any]] = None,
    llm_judge: Optional[Mapping[str, Any]] = None,
    threshold: float = 0.8,
) -> Dict[str, Any]:
    """Score one manifest case against its trace, optional answer, and LLM judge."""
    run_id = str(case.get("run_id", ""))
    failures: List[str] = []

    if trace is None:
        failures.append("missing trace for run_id")
        selected_docs: List[str] = []
        observed_actions: List[Dict[str, str]] = []
        observed_facts: Dict[str, Any] = {}
    else:
        selected_docs = collect_document_ids(trace)
        observed_actions = collect_actions(trace)
        observed_facts = collect_facts(trace)

    required_docs = [str(value) for value in case.get("required_documents", [])]
    optional_docs = [str(value) for value in case.get("optional_documents", [])]
    forbidden_docs = [str(value) for value in case.get("forbidden_documents", [])]

    selected_set = set(selected_docs)
    required_found = [doc_id for doc_id in required_docs if doc_id in selected_set]
    required_missing = [doc_id for doc_id in required_docs if doc_id not in selected_set]
    optional_found = [doc_id for doc_id in optional_docs if doc_id in selected_set]
    forbidden_found = [doc_id for doc_id in forbidden_docs if doc_id in selected_set]

    required_coverage = 1.0 if not required_docs else len(required_found) / len(required_docs)
    forbidden_clear = 1.0 if not forbidden_found else 0.0
    retrieval_score = round_score((0.85 * required_coverage) + (0.15 * forbidden_clear))

    if required_missing:
        failures.append("missing required documents: " + ", ".join(required_missing))
    if forbidden_found:
        failures.append("forbidden documents selected: " + ", ".join(forbidden_found))

    required_actions = [
        action
        for action in (normalize_action(action) for action in case.get("required_actions", []))
        if action is not None
    ]
    observed_action_keys = {action_key(action) for action in observed_actions}
    required_actions_found = [
        action for action in required_actions if action_key(action) in observed_action_keys
    ]
    required_actions_missing = [
        action for action in required_actions if action_key(action) not in observed_action_keys
    ]
    action_score = (
        1.0
        if not required_actions
        else round_score(len(required_actions_found) / len(required_actions))
    )
    if required_actions_missing:
        readable = [f"{action['type']}:{action['target']}" for action in required_actions_missing]
        failures.append("missing required actions: " + ", ".join(readable))

    expected_facts = dict(case.get("expected_facts", {}))
    matched_facts: Dict[str, Any] = {}
    mismatched_facts: Dict[str, Dict[str, Any]] = {}
    missing_facts: List[str] = []
    for key, expected_value in expected_facts.items():
        if key not in observed_facts:
            missing_facts.append(str(key))
        elif observed_facts[key] == expected_value:
            matched_facts[str(key)] = expected_value
        else:
            mismatched_facts[str(key)] = {
                "expected": expected_value,
                "observed": observed_facts[key],
            }
    fact_total = len(expected_facts)
    data_accuracy_score = (
        1.0 if fact_total == 0 else round_score(len(matched_facts) / fact_total)
    )
    if missing_facts:
        failures.append("missing expected facts: " + ", ".join(missing_facts))
    if mismatched_facts:
        failures.append("mismatched expected facts: " + ", ".join(sorted(mismatched_facts)))

    answer_info = answer_summary(answer, selected_docs)
    if answer_info and answer_info["unsupported_citations"]:
        failures.append(
            "answer cites unselected documents: "
            + ", ".join(answer_info["unsupported_citations"])
        )

    overall = round_score((retrieval_score + action_score + data_accuracy_score) / 3)
    passed = overall >= threshold and not failures

    return {
        "run_id": run_id,
        "passed": passed,
        "scores": {
            "retrieval": retrieval_score,
            "action": action_score,
            "data_accuracy": data_accuracy_score,
            "overall": overall,
        },
        "documents": {
            "selected": selected_docs,
            "required_found": required_found,
            "required_missing": required_missing,
            "optional_found": optional_found,
            "forbidden_found": forbidden_found,
        },
        "actions": {
            "observed": observed_actions,
            "required_found": required_actions_found,
            "required_missing": required_actions_missing,
        },
        "facts": {
            "matched": matched_facts,
            "mismatched": mismatched_facts,
            "missing": missing_facts,
        },
        "answer": answer_info,
        "llm_judge": dict(llm_judge) if isinstance(llm_judge, Mapping) else None,
        "failures": failures,
    }


def grade_runs(
    traces: Sequence[Mapping[str, Any]],
    manifest: Mapping[str, Any],
    answers: Optional[Mapping[str, Mapping[str, Any]]] = None,
    llm_judges: Optional[Mapping[str, Mapping[str, Any]]] = None,
    threshold: float = 0.8,
) -> Dict[str, Any]:
    """Grade all manifest cases and return the structured report."""
    trace_index = index_by_run_id(list(traces))
    manifest_cases = manifest.get("cases")
    if not isinstance(manifest_cases, list):
        raise ValueError("manifest must contain a cases array")

    answer_index = dict(answers or {})
    judge_index = dict(llm_judges or {})
    case_reports = [
        score_case(
            case=case,
            trace=trace_index.get(str(case.get("run_id", ""))),
            answer=answer_index.get(str(case.get("run_id", ""))),
            llm_judge=judge_index.get(str(case.get("run_id", ""))),
            threshold=threshold,
        )
        for case in manifest_cases
    ]

    total = len(case_reports)
    passed = sum(1 for case in case_reports if case["passed"])
    failed = total - passed

    def average_score(name: str) -> float:
        if total == 0:
            return 0.0
        return round_score(sum(case["scores"][name] for case in case_reports) / total)

    return {
        "tool": TOOL_NAME,
        "version": VERSION,
        "summary": {
            "cases": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round_score(passed / total) if total else 0.0,
            "average_scores": {
                "retrieval": average_score("retrieval"),
                "action": average_score("action"),
                "data_accuracy": average_score("data_accuracy"),
                "overall": average_score("overall"),
            },
        },
        "cases": case_reports,
    }


def load_json_file(path: Path) -> Any:
    """Load a JSON file with a useful error message on invalid input."""
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise ValueError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc


def load_jsonl_file(path: Path) -> List[Dict[str, Any]]:
    """Load a JSONL file as a list of objects."""
    records: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    item = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid JSONL in {path} at line {line_number}: {exc}") from exc
                if not isinstance(item, dict):
                    raise ValueError(f"JSONL record at line {line_number} must be an object")
                records.append(item)
    except FileNotFoundError as exc:
        raise ValueError(f"file not found: {path}") from exc
    return records


def load_optional_index(path: Optional[str]) -> Dict[str, Dict[str, Any]]:
    """Load an optional JSON or JSONL file and index it by run_id."""
    if not path:
        return {}
    file_path = Path(path)
    if file_path.suffix.lower() == ".jsonl":
        return index_by_run_id(load_jsonl_file(file_path))
    return index_by_run_id(load_json_file(file_path))


def report_to_csv(report: Mapping[str, Any]) -> str:
    """Render a report as CSV for dashboard ingestion."""
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "run_id",
            "passed",
            "retrieval",
            "action",
            "data_accuracy",
            "overall",
            "failures",
        ],
    )
    writer.writeheader()
    for case in report.get("cases", []):
        scores = case["scores"]
        writer.writerow(
            {
                "run_id": case["run_id"],
                "passed": case["passed"],
                "retrieval": scores["retrieval"],
                "action": scores["action"],
                "data_accuracy": scores["data_accuracy"],
                "overall": scores["overall"],
                "failures": "; ".join(case["failures"]),
            }
        )
    return output.getvalue()


def default_threshold() -> float:
    """Read the default pass threshold from the environment when provided."""
    raw = os.environ.get("RAG_EVIDENCE_GRADER_THRESHOLD", "0.8")
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError("RAG_EVIDENCE_GRADER_THRESHOLD must be a number") from exc
    if not 0 <= value <= 1:
        raise ValueError("RAG_EVIDENCE_GRADER_THRESHOLD must be between 0 and 1")
    return value


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description="Offline evidence-first grader for RAG retrieval gates and traces.",
    )
    parser.add_argument("--traces", help="Path to JSONL trace records.")
    parser.add_argument("--manifest", help="Path to expected evidence manifest JSON.")
    parser.add_argument("--answers", help="Optional JSON or JSONL final-answer records.")
    parser.add_argument(
        "--llm-judge-json",
        default=os.environ.get("TRACE_TRELLIS_LLM_JUDGE_PATH"),
        help="Optional JSON or JSONL judge records; can also use TRACE_TRELLIS_LLM_JUDGE_PATH.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Overall pass threshold from 0 to 1. Defaults to RAG_EVIDENCE_GRADER_THRESHOLD or 0.8.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "csv"),
        default="json",
        help="Output format. Defaults to json.",
    )
    parser.add_argument("--output", help="Optional output file path.")
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run the built-in offline sample with no API key.",
    )
    parser.add_argument("--version", action="version", version=f"{TOOL_NAME} {VERSION}")
    return parser


def render_report(report: Mapping[str, Any], output_format: str) -> str:
    """Render a report to JSON or CSV."""
    if output_format == "csv":
        return report_to_csv(report)
    return json.dumps(report, indent=2) + "\n"


def run_selftest(output_format: str = "json") -> Tuple[int, str]:
    """Run the built-in sample and return a process-style exit code and output."""
    report = grade_runs(SAMPLE_TRACES, SAMPLE_MANIFEST, threshold=0.8)
    rendered = render_report(report, output_format)
    return (0 if report["summary"]["failed"] == 0 else 1, rendered)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point."""
    args_list = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    if not args_list:
        code, rendered = run_selftest()
        sys.stdout.write(rendered)
        return code

    args = parser.parse_args(args_list)
    try:
        threshold = args.threshold if args.threshold is not None else default_threshold()
        if not 0 <= threshold <= 1:
            raise ValueError("--threshold must be between 0 and 1")

        if args.selftest:
            code, rendered = run_selftest(args.format)
        else:
            if not args.traces or not args.manifest:
                raise ValueError("--traces and --manifest are required unless --selftest is used")
            traces = load_jsonl_file(Path(args.traces))
            manifest = load_json_file(Path(args.manifest))
            answers = load_optional_index(args.answers)
            llm_judges = load_optional_index(args.llm_judge_json)
            report = grade_runs(
                traces=traces,
                manifest=manifest,
                answers=answers,
                llm_judges=llm_judges,
                threshold=threshold,
            )
            code = 0 if report["summary"]["failed"] == 0 else 1
            rendered = render_report(report, args.format)

        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        return code
    except ValueError as exc:
        print(f"{TOOL_NAME}: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
