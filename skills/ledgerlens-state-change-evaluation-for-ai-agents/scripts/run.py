#!/usr/bin/env python3
"""LedgerLens reference CLI: verify agent traces against a task state ledger."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TRACE_SAMPLE = [
    {
        "timestamp": "2026-01-01T10:00:00Z",
        "tool": "search",
        "action": "retrieve",
        "resource": "docs/export_policy.md",
        "summary": "Read export policy before editing.",
    },
    {
        "timestamp": "2026-01-01T10:01:00Z",
        "tool": "editor",
        "action": "write",
        "path": "src/exporter.py",
        "summary": "Updated export validation logic.",
    },
    {
        "timestamp": "2026-01-01T10:02:00Z",
        "tool": "shell",
        "action": "run",
        "command": "pytest tests/test_exporter.py",
        "summary": "pytest passed for exporter tests.",
    },
    {
        "timestamp": "2026-01-01T10:03:00Z",
        "tool": "final",
        "action": "report",
        "message": "Updated src/exporter.py and tests were run. Billing config was preserved.",
    },
]


SPEC_SAMPLE = {
    "task": "Update export logic while preserving billing configuration.",
    "expected_resources": [
        {"id": "policy_lookup", "match": "docs/export_policy.md"},
    ],
    "required_mutations": [
        {"id": "export_update", "path": "src/exporter.py", "operation": "write"},
    ],
    "protected_state": [
        {"id": "billing_config", "path": "config/billing.yaml"},
    ],
    "reporting_obligations": [
        {"id": "mention_tests", "claim": "tests were run", "evidence": "pytest"},
    ],
}


WRITE_ACTIONS = {"write", "edit", "modify", "patch", "delete", "remove", "create", "move"}
READ_ACTIONS = {"read", "retrieve", "search", "open", "fetch", "query", "lookup"}
REPORT_ACTIONS = {"report", "final", "answer", "respond", "summary"}


@dataclass
class CheckResult:
    id: str
    principle: str
    passed: bool
    expected: dict[str, Any]
    evidence: list[dict[str, Any]]
    missing_evidence: str | None = None
    diagnostic: str | None = None


def compact_record(record: dict[str, Any]) -> dict[str, Any]:
    keys = ("timestamp", "tool", "action", "path", "resource", "service", "command", "summary", "message")
    compact = {key: record[key] for key in keys if key in record}
    if not compact:
        compact = {key: record[key] for key in list(record)[:8]}
    return compact


def flatten_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(f"{key} {flatten_text(item)}" for key, item in value.items())
    if isinstance(value, list):
        return " ".join(flatten_text(item) for item in value)
    return str(value)


def normalize(value: Any) -> str:
    return flatten_text(value).lower()


def token_match(needle: str | None, record: dict[str, Any]) -> bool:
    if not needle:
        return True
    return needle.lower() in normalize(record)


def field_match(needle: str | None, record: dict[str, Any], fields: Iterable[str]) -> bool:
    if not needle:
        return True
    lowered = needle.lower()
    return any(lowered in str(record.get(field, "")).lower() for field in fields)


def action_matches(record: dict[str, Any], accepted: set[str]) -> bool:
    action = str(record.get("action", "")).lower()
    tool = str(record.get("tool", "")).lower()
    return action in accepted or tool in accepted


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
            if not isinstance(value, dict):
                raise SystemExit(f"Invalid JSONL at {path}:{line_number}: each line must be an object")
            records.append(value)
    return records


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"", "null", "Null", "NULL", "~"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    return value


def minimal_yaml_load(text: str) -> dict[str, Any]:
    """Parse the small YAML subset used by LedgerLens examples."""

    root: dict[str, Any] = {}
    current_list_key: str | None = None
    current_item: dict[str, Any] | None = None

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        if indent == 0:
            current_item = None
            if ":" not in line:
                raise ValueError(f"Expected key:value line: {raw_line}")
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value:
                root[key] = parse_scalar(value)
                current_list_key = None
            else:
                root[key] = []
                current_list_key = key
            continue

        if current_list_key is None:
            raise ValueError(f"Nested line has no parent list: {raw_line}")

        if line.startswith("- "):
            item_text = line[2:].strip()
            current_item = {}
            root[current_list_key].append(current_item)
            if item_text:
                if ":" not in item_text:
                    raise ValueError(f"Expected list item key:value: {raw_line}")
                key, value = item_text.split(":", 1)
                current_item[key.strip()] = parse_scalar(value)
            continue

        if current_item is None:
            raise ValueError(f"Expected list item before nested field: {raw_line}")
        if ":" not in line:
            raise ValueError(f"Expected nested key:value: {raw_line}")
        key, value = line.split(":", 1)
        current_item[key.strip()] = parse_scalar(value)

    return root


def load_spec(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(text)
    except ModuleNotFoundError:
        loaded = minimal_yaml_load(text)
    except Exception as exc:
        raise SystemExit(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise SystemExit(f"Task spec must be a YAML object: {path}")
    return loaded


def list_of_dicts(spec: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = spec.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise SystemExit(f"Spec field '{key}' must be a list of objects")
    return value


def evaluate_retrieve(spec: dict[str, Any], records: list[dict[str, Any]]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for index, item in enumerate(list_of_dicts(spec, "expected_resources"), start=1):
        match = str(item.get("match") or item.get("resource") or item.get("path") or "")
        evidence = [
            compact_record(record)
            for record in records
            if token_match(match, record) and action_matches(record, READ_ACTIONS | {"tool"})
        ]
        passed = bool(evidence)
        results.append(
            CheckResult(
                id=str(item.get("id", f"retrieve_{index}")),
                principle="Retrieve",
                passed=passed,
                expected=item,
                evidence=evidence,
                missing_evidence=None if passed else f"No retrieval evidence matched '{match}'.",
            )
        )
    return results


def evaluate_modify(spec: dict[str, Any], records: list[dict[str, Any]]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for index, item in enumerate(list_of_dicts(spec, "required_mutations"), start=1):
        path = str(item.get("path") or item.get("match") or "")
        operation = str(item.get("operation") or item.get("action") or "").lower()
        evidence = []
        for record in records:
            action_ok = action_matches(record, WRITE_ACTIONS)
            operation_ok = not operation or operation in normalize(record)
            path_ok = field_match(path, record, ("path", "resource", "summary", "message")) or token_match(path, record)
            if action_ok and operation_ok and path_ok:
                evidence.append(compact_record(record))
        passed = bool(evidence)
        results.append(
            CheckResult(
                id=str(item.get("id", f"modify_{index}")),
                principle="Modify",
                passed=passed,
                expected=item,
                evidence=evidence,
                missing_evidence=None if passed else f"No mutation evidence matched '{path}' and operation '{operation or 'any'}'.",
            )
        )
    return results


def evaluate_preserve(spec: dict[str, Any], records: list[dict[str, Any]]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for index, item in enumerate(list_of_dicts(spec, "protected_state"), start=1):
        path = str(item.get("path") or item.get("match") or "")
        violations = []
        for record in records:
            if action_matches(record, WRITE_ACTIONS) and token_match(path, record):
                violations.append(compact_record(record))
        passed = not violations
        results.append(
            CheckResult(
                id=str(item.get("id", f"preserve_{index}")),
                principle="Preserve",
                passed=passed,
                expected=item,
                evidence=[] if passed else violations,
                missing_evidence=None,
                diagnostic="Protected state was not modified." if passed else f"Protected state matched mutation evidence for '{path}'.",
            )
        )
    return results


def report_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reports = [record for record in records if action_matches(record, REPORT_ACTIONS)]
    if reports:
        return reports
    return records[-1:] if records else []


def evaluate_report(spec: dict[str, Any], records: list[dict[str, Any]]) -> list[CheckResult]:
    results: list[CheckResult] = []
    reports = report_records(records)
    report_text = " ".join(normalize(record) for record in reports)
    full_trace = normalize(records)

    for index, item in enumerate(list_of_dicts(spec, "reporting_obligations"), start=1):
        claim = str(item.get("claim") or item.get("must_report") or "")
        evidence_token = str(item.get("evidence") or item.get("match") or claim)
        claim_made = not claim or claim.lower() in report_text
        evidence_exists = not evidence_token or evidence_token.lower() in full_trace
        passed = claim_made and evidence_exists
        evidence = []
        if claim_made:
            evidence.extend(compact_record(record) for record in reports)
        if evidence_exists:
            evidence.extend(
                compact_record(record)
                for record in records
                if evidence_token and evidence_token.lower() in normalize(record)
            )
        results.append(
            CheckResult(
                id=str(item.get("id", f"report_{index}")),
                principle="Report",
                passed=passed,
                expected=item,
                evidence=evidence,
                missing_evidence=None
                if passed
                else f"Report claim '{claim}' was not backed by trace evidence '{evidence_token}'.",
                diagnostic=f"claim_made={claim_made}; evidence_exists={evidence_exists}",
            )
        )

    final_claims = list_of_dicts(spec, "final_claims")
    for index, item in enumerate(final_claims, start=1):
        claim = str(item.get("claim") or "")
        evidence_token = str(item.get("evidence") or item.get("match") or "")
        claim_made = claim.lower() in report_text
        evidence_exists = evidence_token.lower() in full_trace if evidence_token else True
        passed = (not claim_made) or evidence_exists
        results.append(
            CheckResult(
                id=str(item.get("id", f"false_completion_{index}")),
                principle="Report",
                passed=passed,
                expected=item,
                evidence=[compact_record(record) for record in reports] if claim_made else [],
                missing_evidence=None if passed else f"Final report claims '{claim}' but no evidence matched '{evidence_token}'.",
                diagnostic=f"false_completion_check; claim_made={claim_made}; evidence_exists={evidence_exists}",
            )
        )

    return results


def summarize(results: list[CheckResult]) -> dict[str, Any]:
    by_principle: dict[str, dict[str, int]] = {}
    for result in results:
        bucket = by_principle.setdefault(result.principle, {"passed": 0, "failed": 0, "total": 0})
        bucket["total"] += 1
        bucket["passed" if result.passed else "failed"] += 1
    passed = sum(1 for result in results if result.passed)
    total = len(results)
    return {
        "total_checks": total,
        "passed": passed,
        "failed": total - passed,
        "score": round(passed / total, 4) if total else 1.0,
        "by_principle": by_principle,
    }


def evaluate(spec: dict[str, Any], records: list[dict[str, Any]], trace_source: str, spec_source: str) -> dict[str, Any]:
    results = []
    results.extend(evaluate_retrieve(spec, records))
    results.extend(evaluate_modify(spec, records))
    results.extend(evaluate_preserve(spec, records))
    results.extend(evaluate_report(spec, records))

    api_key_present = bool(os.getenv("LEDGERLENS_API_KEY"))
    report = {
        "schema": "ledgerlens.report.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task": spec.get("task", "Unnamed task"),
        "inputs": {
            "trace_source": trace_source,
            "spec_source": spec_source,
            "records_observed": len(records),
            "api_key_present": api_key_present,
            "mode": "local-reference",
        },
        "summary": summarize(results),
        "checks": [
            {
                "id": result.id,
                "principle": result.principle,
                "passed": result.passed,
                "expected": result.expected,
                "evidence": result.evidence,
                "missing_evidence": result.missing_evidence,
                "diagnostic": result.diagnostic,
            }
            for result in results
        ],
    }
    return report


def write_report(report: dict[str, Any], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "ledgerlens_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report_path


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="agent-trace-verifier",
        description="Evaluate an AI agent JSONL tool trace against a YAML state-change task specification.",
    )
    parser.add_argument("--trace", help="Path to a JSONL tool trace.")
    parser.add_argument("--spec", help="Path to a YAML task specification.")
    parser.add_argument("--out", default="ledgerlens_report", help="Output directory for ledgerlens_report.json.")
    parser.add_argument("--fail-on-error", action="store_true", help="Exit non-zero when any check fails.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    if args.trace and not args.spec:
        raise SystemExit("--spec is required when --trace is provided")
    if args.spec and not args.trace:
        raise SystemExit("--trace is required when --spec is provided")

    if args.trace and args.spec:
        trace_path = Path(args.trace)
        spec_path = Path(args.spec)
        records = load_jsonl(trace_path)
        spec = load_spec(spec_path)
        trace_source = str(trace_path)
        spec_source = str(spec_path)
    else:
        records = TRACE_SAMPLE
        spec = SPEC_SAMPLE
        trace_source = "built-in sample"
        spec_source = "built-in sample"

    report = evaluate(spec, records, trace_source, spec_source)
    report_path = write_report(report, Path(args.out))
    summary = report["summary"]

    print(f"LedgerLens report: {report_path}")
    print(
        f"Checks: {summary['passed']}/{summary['total_checks']} passed "
        f"(score={summary['score']:.2f}, failed={summary['failed']})"
    )
    for principle, counts in summary["by_principle"].items():
        print(f"- {principle}: {counts['passed']}/{counts['total']} passed")

    if args.fail_on_error and summary["failed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
