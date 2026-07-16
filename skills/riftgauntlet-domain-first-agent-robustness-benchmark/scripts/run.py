#!/usr/bin/env python3
"""Replay agent traces under deterministic perturbations and report robustness slices."""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


SCHEMA_VERSION = "1.0"
SUPPORTED_OPERATIONS = {
    "delay",
    "domain_shift",
    "duplicate",
    "malformed",
    "missing",
    "reorder",
    "tool_failure",
    "truncate",
}


class ValidationError(ValueError):
    """Raised when a trace or perturbation specification violates the input contract."""


@dataclass(frozen=True)
class BenchmarkResult:
    """Hold the public JSON report and detailed replay cases used for fixture export."""

    report: Dict[str, Any]
    cases: Tuple[Dict[str, Any], ...]


BUILTIN_TRACES: List[Dict[str, Any]] = [
    {
        "id": "finance-001",
        "domain": "finance",
        "success": True,
        "confidence": 0.92,
        "observations": [
            {
                "id": "context",
                "tool": "account_lookup",
                "content": "account=verified",
                "latency_ms": 80,
            },
            {
                "id": "result",
                "tool": "market_quote",
                "content": "quote=AAPL:195.20",
                "latency_ms": 140,
            },
        ],
        "replay_oracle": {
            "required_observations": ["context", "result"],
            "required_content": {"result": ["quote=AAPL"]},
            "expected_order": ["context", "result"],
            "max_total_latency_ms": 300,
        },
    },
    {
        "id": "support-001",
        "domain": "support",
        "success": True,
        "risk_score": 0.75,
        "observations": [
            {
                "id": "context",
                "tool": "identity_check",
                "content": "customer=verified",
                "latency_ms": 50,
            },
            {
                "id": "result",
                "tool": "reset_service",
                "content": "reset_status=issued",
                "latency_ms": 90,
            },
        ],
        "replay_oracle": {
            "required_observations": ["context", "result"],
            "required_content": {"result": ["reset_status=issued"]},
            "expected_order": ["context", "result"],
            "max_total_latency_ms": 250,
        },
    },
    {
        "id": "travel-001",
        "domain": "travel",
        "success": True,
        "abstained": False,
        "observations": [
            {
                "id": "context",
                "tool": "location_lookup",
                "content": "airport=ICN",
                "latency_ms": 60,
            },
            {
                "id": "result",
                "tool": "weather_service",
                "content": "forecast=clear;temperature_c=22",
                "latency_ms": 100,
            },
        ],
        "replay_oracle": {
            "required_observations": ["context", "result"],
            "required_content": {"result": ["temperature_c=22"]},
            "expected_order": ["context", "result"],
            "max_total_latency_ms": 220,
        },
    },
]


BUILTIN_SPEC: Dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "scenarios": [
        {
            "name": "missing-result",
            "match_domains": ["finance"],
            "operations": [{"type": "missing", "observation_id": "result"}],
        },
        {
            "name": "truncated-result",
            "match_domains": ["travel"],
            "operations": [
                {"type": "truncate", "observation_id": "result", "max_chars": 14}
            ],
        },
        {
            "name": "malformed-result",
            "match_domains": ["support"],
            "operations": [
                {
                    "type": "malformed",
                    "observation_id": "result",
                    "replacement": "{invalid",
                }
            ],
        },
        {
            "name": "delayed-result",
            "match_domains": ["travel"],
            "operations": [
                {"type": "delay", "observation_id": "result", "milliseconds": 100}
            ],
        },
        {
            "name": "duplicated-result",
            "match_domains": ["finance"],
            "operations": [{"type": "duplicate", "observation_id": "result"}],
        },
        {
            "name": "reordered-observations",
            "match_domains": ["support"],
            "operations": [{"type": "reorder", "mode": "reverse"}],
        },
        {
            "name": "unknown-domain-shift",
            "match_domains": ["finance"],
            "operations": [{"type": "domain_shift", "domain": "unknown"}],
        },
    ],
}


def _require(condition: bool, message: str) -> None:
    """Raise a validation error with a stable message when a condition is false."""

    if not condition:
        raise ValidationError(message)


def _is_number(value: Any) -> bool:
    """Return true for JSON numbers while excluding booleans."""

    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _rate(values: Sequence[bool]) -> Optional[float]:
    """Return a six-decimal success rate, or null semantics for an empty sequence."""

    if not values:
        return None
    return round(sum(bool(value) for value in values) / len(values), 6)


def _delta(current: Optional[float], baseline: Optional[float]) -> Optional[float]:
    """Return a rounded difference when both rates are available."""

    if current is None or baseline is None:
        return None
    return round(current - baseline, 6)


def _validate_observation(observation: Any, location: str) -> None:
    """Validate one portable tool-observation record."""

    _require(isinstance(observation, dict), f"{location} must be an object")
    _require(
        isinstance(observation.get("id"), str) and bool(observation["id"]),
        f"{location}.id must be a non-empty string",
    )
    _require(
        isinstance(observation.get("tool"), str) and bool(observation["tool"]),
        f"{location}.tool must be a non-empty string",
    )
    _require(
        isinstance(observation.get("content"), str),
        f"{location}.content must be a string",
    )
    latency = observation.get("latency_ms")
    _require(
        isinstance(latency, int) and not isinstance(latency, bool) and latency >= 0,
        f"{location}.latency_ms must be a non-negative integer",
    )
    for field in ("malformed", "error"):
        if field in observation:
            _require(
                isinstance(observation[field], bool),
                f"{location}.{field} must be a boolean",
            )


def _evaluate_oracle(
    trace: Mapping[str, Any], observations: Sequence[Mapping[str, Any]]
) -> List[str]:
    """Evaluate mutated observations against a trace's deterministic replay oracle."""

    oracle = trace["replay_oracle"]
    ids = [observation["id"] for observation in observations]
    reasons: List[str] = []

    for required_id in oracle.get("required_observations", []):
        if required_id not in ids:
            reasons.append(f"missing_observation:{required_id}")

    for observation_id, tokens in oracle.get("required_content", {}).items():
        contents = [
            observation["content"]
            for observation in observations
            if observation["id"] == observation_id
        ]
        for token in tokens:
            if not any(token in content for content in contents):
                reasons.append(f"missing_content:{observation_id}:{token}")

    if not oracle.get("allow_malformed", False):
        malformed_ids = sorted(
            {observation["id"] for observation in observations if observation.get("malformed")}
        )
        reasons.extend(f"malformed_observation:{item}" for item in malformed_ids)

    if oracle.get("fail_on_tool_error", True):
        error_ids = sorted(
            {observation["id"] for observation in observations if observation.get("error")}
        )
        reasons.extend(f"tool_error:{item}" for item in error_ids)

    if not oracle.get("allow_duplicates", False):
        duplicate_ids = sorted(item for item, count in Counter(ids).items() if count > 1)
        reasons.extend(f"duplicate_observation:{item}" for item in duplicate_ids)

    expected_order = oracle.get("expected_order")
    if expected_order is not None and ids != expected_order:
        reasons.append("observation_order_mismatch")

    maximum_latency = oracle.get("max_total_latency_ms")
    if maximum_latency is not None:
        total_latency = sum(observation["latency_ms"] for observation in observations)
        if total_latency > maximum_latency:
            reasons.append(f"latency_budget_exceeded:{total_latency}>{maximum_latency}")

    return reasons


def _validate_trace(trace: Any, index: int) -> None:
    """Validate one trace and confirm that successful baseline traces satisfy their oracle."""

    location = f"trace[{index}]"
    _require(isinstance(trace, dict), f"{location} must be an object")
    _require(
        isinstance(trace.get("id"), str) and bool(trace["id"]),
        f"{location}.id must be a non-empty string",
    )
    _require(
        isinstance(trace.get("domain"), str) and bool(trace["domain"]),
        f"{location}.domain must be a non-empty string",
    )
    _require(isinstance(trace.get("success"), bool), f"{location}.success must be a boolean")

    observations = trace.get("observations")
    _require(
        isinstance(observations, list) and bool(observations),
        f"{location}.observations must be a non-empty array",
    )
    for observation_index, observation in enumerate(observations):
        _validate_observation(observation, f"{location}.observations[{observation_index}]")
    observation_ids = [observation["id"] for observation in observations]
    _require(
        len(observation_ids) == len(set(observation_ids)),
        f"{location}.observations must have unique ids at baseline",
    )

    oracle = trace.get("replay_oracle")
    _require(isinstance(oracle, dict), f"{location}.replay_oracle must be an object")
    required = oracle.get("required_observations", [])
    _require(
        isinstance(required, list)
        and all(isinstance(item, str) and item for item in required)
        and len(required) == len(set(required)),
        f"{location}.replay_oracle.required_observations must contain unique strings",
    )
    _require(
        set(required).issubset(observation_ids),
        f"{location}.replay_oracle requires an unknown baseline observation",
    )

    required_content = oracle.get("required_content", {})
    _require(
        isinstance(required_content, dict),
        f"{location}.replay_oracle.required_content must be an object",
    )
    for observation_id, tokens in required_content.items():
        _require(
            isinstance(observation_id, str) and observation_id in observation_ids,
            f"{location}.replay_oracle.required_content references an unknown observation",
        )
        _require(
            isinstance(tokens, list)
            and bool(tokens)
            and all(isinstance(token, str) and token for token in tokens),
            f"{location}.replay_oracle.required_content values must be non-empty string arrays",
        )

    expected_order = oracle.get("expected_order")
    if expected_order is not None:
        _require(
            isinstance(expected_order, list) and expected_order == observation_ids,
            f"{location}.replay_oracle.expected_order must equal the baseline observation order",
        )
    maximum_latency = oracle.get("max_total_latency_ms")
    if maximum_latency is not None:
        _require(
            isinstance(maximum_latency, int)
            and not isinstance(maximum_latency, bool)
            and maximum_latency >= 0,
            f"{location}.replay_oracle.max_total_latency_ms must be a non-negative integer",
        )
    for field in ("allow_malformed", "allow_duplicates", "fail_on_tool_error"):
        if field in oracle:
            _require(
                isinstance(oracle[field], bool),
                f"{location}.replay_oracle.{field} must be a boolean",
            )

    for field in ("confidence", "risk_score"):
        if field in trace:
            _require(
                _is_number(trace[field]) and 0.0 <= trace[field] <= 1.0,
                f"{location}.{field} must be a number from 0 to 1",
            )
    if "abstained" in trace:
        _require(
            isinstance(trace["abstained"], bool),
            f"{location}.abstained must be a boolean",
        )

    baseline_reasons = _evaluate_oracle(trace, observations)
    _require(
        not trace["success"] or not baseline_reasons,
        f"{location} is marked successful but fails its replay oracle: {', '.join(baseline_reasons)}",
    )


def _validate_operation(operation: Any, location: str) -> None:
    """Validate one declarative mutation operation and reject unknown keys."""

    _require(isinstance(operation, dict), f"{location} must be an object")
    operation_type = operation.get("type")
    _require(
        operation_type in SUPPORTED_OPERATIONS,
        f"{location}.type must be one of: {', '.join(sorted(SUPPORTED_OPERATIONS))}",
    )
    allowed_keys = {
        "missing": {"type", "observation_id"},
        "truncate": {"type", "observation_id", "max_chars"},
        "malformed": {"type", "observation_id", "replacement"},
        "delay": {"type", "observation_id", "milliseconds"},
        "duplicate": {"type", "observation_id"},
        "reorder": {"type", "mode"},
        "domain_shift": {"type", "domain"},
        "tool_failure": {"type", "observation_id", "message"},
    }[operation_type]
    unknown_keys = sorted(set(operation) - allowed_keys)
    _require(not unknown_keys, f"{location} has unknown keys: {', '.join(unknown_keys)}")

    if operation_type in {"missing", "truncate", "malformed", "delay", "duplicate", "tool_failure"}:
        _require(
            isinstance(operation.get("observation_id"), str)
            and bool(operation["observation_id"]),
            f"{location}.observation_id must be a non-empty string",
        )
    if operation_type == "truncate":
        max_chars = operation.get("max_chars")
        _require(
            isinstance(max_chars, int) and not isinstance(max_chars, bool) and max_chars >= 0,
            f"{location}.max_chars must be a non-negative integer",
        )
    if operation_type == "malformed" and "replacement" in operation:
        _require(
            isinstance(operation["replacement"], str),
            f"{location}.replacement must be a string",
        )
    if operation_type == "delay":
        milliseconds = operation.get("milliseconds")
        _require(
            isinstance(milliseconds, int)
            and not isinstance(milliseconds, bool)
            and milliseconds >= 0,
            f"{location}.milliseconds must be a non-negative integer",
        )
    if operation_type == "reorder":
        _require(operation.get("mode") == "reverse", f"{location}.mode must be 'reverse'")
    if operation_type == "domain_shift":
        _require(
            isinstance(operation.get("domain"), str) and bool(operation["domain"]),
            f"{location}.domain must be a non-empty string",
        )
    if operation_type == "tool_failure" and "message" in operation:
        _require(isinstance(operation["message"], str), f"{location}.message must be a string")


def validate_inputs(traces: Any, specification: Any) -> None:
    """Validate the complete trace collection and perturbation specification."""

    _require(isinstance(traces, list) and bool(traces), "traces must be a non-empty array")
    for index, trace in enumerate(traces):
        _validate_trace(trace, index)
    trace_ids = [trace["id"] for trace in traces]
    _require(len(trace_ids) == len(set(trace_ids)), "trace ids must be unique")

    _require(isinstance(specification, dict), "perturbation specification must be an object")
    _require(
        specification.get("schema_version") == SCHEMA_VERSION,
        f"perturbation specification schema_version must be '{SCHEMA_VERSION}'",
    )
    scenarios = specification.get("scenarios")
    _require(
        isinstance(scenarios, list) and bool(scenarios),
        "perturbation specification scenarios must be a non-empty array",
    )
    names: List[str] = []
    for scenario_index, scenario in enumerate(scenarios):
        location = f"scenario[{scenario_index}]"
        _require(isinstance(scenario, dict), f"{location} must be an object")
        _require(
            set(scenario).issubset({"name", "match_domains", "operations"}),
            f"{location} has unknown keys",
        )
        _require(
            isinstance(scenario.get("name"), str) and bool(scenario["name"]),
            f"{location}.name must be a non-empty string",
        )
        names.append(scenario["name"])
        match_domains = scenario.get("match_domains")
        _require(
            isinstance(match_domains, list)
            and bool(match_domains)
            and all(isinstance(domain, str) and domain for domain in match_domains),
            f"{location}.match_domains must be a non-empty string array",
        )
        operations = scenario.get("operations")
        _require(
            isinstance(operations, list) and bool(operations),
            f"{location}.operations must be a non-empty array",
        )
        for operation_index, operation in enumerate(operations):
            _validate_operation(operation, f"{location}.operations[{operation_index}]")
    _require(len(names) == len(set(names)), "scenario names must be unique")


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Load trace objects from a UTF-8 JSONL file with line-specific errors."""

    traces: List[Dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ValidationError(f"cannot read trace file '{path}': {error}") from error
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValidationError(
                f"invalid JSON in trace file '{path}' at line {line_number}: {error.msg}"
            ) from error
        _require(
            isinstance(value, dict),
            f"trace file '{path}' line {line_number} must contain a JSON object",
        )
        traces.append(value)
    _require(bool(traces), f"trace file '{path}' contains no trace objects")
    return traces


def load_specification(path: Path) -> Dict[str, Any]:
    """Load a perturbation specification from a UTF-8 JSON file."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValidationError(f"cannot read specification '{path}': {error}") from error
    except json.JSONDecodeError as error:
        raise ValidationError(f"invalid JSON in specification '{path}': {error.msg}") from error
    _require(isinstance(value, dict), f"specification '{path}' must contain a JSON object")
    return value


def _matching_observations(
    observations: Sequence[Mapping[str, Any]], observation_id: str
) -> List[int]:
    """Return indexes of observations with a requested id."""

    return [index for index, item in enumerate(observations) if item["id"] == observation_id]


def _apply_scenario(
    trace: Mapping[str, Any], scenario: Mapping[str, Any]
) -> Tuple[str, List[Dict[str, Any]]]:
    """Apply a validated scenario to one trace without mutating caller-owned data."""

    domain = trace["domain"]
    observations = copy.deepcopy(trace["observations"])
    for operation_index, operation in enumerate(scenario["operations"]):
        operation_type = operation["type"]
        if operation_type == "domain_shift":
            domain = operation["domain"]
            continue
        if operation_type == "reorder":
            observations.reverse()
            continue

        observation_id = operation["observation_id"]
        matches = _matching_observations(observations, observation_id)
        _require(
            bool(matches),
            f"scenario '{scenario['name']}' operation {operation_index} targets missing observation "
            f"'{observation_id}' in trace '{trace['id']}'",
        )
        if operation_type == "missing":
            observations = [item for item in observations if item["id"] != observation_id]
        elif operation_type == "truncate":
            for index in matches:
                observations[index]["content"] = observations[index]["content"][: operation["max_chars"]]
        elif operation_type == "malformed":
            for index in matches:
                observations[index]["content"] = operation.get("replacement", "{malformed")
                observations[index]["malformed"] = True
        elif operation_type == "delay":
            for index in matches:
                observations[index]["latency_ms"] += operation["milliseconds"]
        elif operation_type == "duplicate":
            duplicated: List[Dict[str, Any]] = []
            for item in observations:
                duplicated.append(item)
                if item["id"] == observation_id:
                    duplicate = copy.deepcopy(item)
                    duplicate["duplicated"] = True
                    duplicated.append(duplicate)
            observations = duplicated
        elif operation_type == "tool_failure":
            for index in matches:
                observations[index]["content"] = operation.get("message", "tool failure")
                observations[index]["error"] = True
    return domain, observations


def _detection_signal(trace: Mapping[str, Any]) -> Tuple[Optional[float], Optional[str]]:
    """Map risk, abstention, or inverse confidence to a higher-means-failure score."""

    if "risk_score" in trace:
        return float(trace["risk_score"]), "risk_score"
    if "abstained" in trace:
        return (1.0 if trace["abstained"] else 0.0), "abstention"
    if "confidence" in trace:
        return 1.0 - float(trace["confidence"]), "confidence"
    return None, None


def _auroc_proxy(cases: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Estimate AUROC by pairwise ordering of failed and successful replay cases."""

    scorable = [case for case in cases if case["detection_score"] is not None]
    failures = [case for case in scorable if not case["success"]]
    successes = [case for case in scorable if case["success"]]
    source_counts = Counter(case["detection_source"] for case in scorable)
    auc: Optional[float] = None
    if failures and successes:
        credit = 0.0
        comparisons = 0
        for failure in failures:
            for success in successes:
                comparisons += 1
                if failure["detection_score"] > success["detection_score"]:
                    credit += 1.0
                elif failure["detection_score"] == success["detection_score"]:
                    credit += 0.5
        auc = round(credit / comparisons, 6)
    return {
        "auroc_proxy": auc,
        "failure_cases": len(failures),
        "scorable_cases": len(scorable),
        "score_sources": dict(sorted(source_counts.items())),
        "success_cases": len(successes),
    }


def run_benchmark(
    traces: Sequence[Mapping[str, Any]],
    specification: Mapping[str, Any],
    worst_limit: int = 5,
) -> BenchmarkResult:
    """Validate, replay, and aggregate a deterministic robustness benchmark."""

    _require(
        isinstance(worst_limit, int) and not isinstance(worst_limit, bool) and worst_limit > 0,
        "worst_limit must be a positive integer",
    )
    trace_list = copy.deepcopy(list(traces))
    spec = copy.deepcopy(dict(specification))
    validate_inputs(trace_list, spec)

    cases: List[Dict[str, Any]] = []
    for scenario in spec["scenarios"]:
        match_domains = scenario["match_domains"]
        matched_traces = [
            trace
            for trace in trace_list
            if "*" in match_domains or trace["domain"] in match_domains
        ]
        _require(
            bool(matched_traces),
            f"scenario '{scenario['name']}' does not match any trace domain",
        )
        for trace in matched_traces:
            effective_domain, observations = _apply_scenario(trace, scenario)
            reasons = _evaluate_oracle(trace, observations)
            if not trace["success"]:
                reasons.insert(0, "recorded_baseline_failure")
            score, source = _detection_signal(trace)
            cases.append(
                {
                    "baseline_success": trace["success"],
                    "detection_score": None if score is None else round(score, 6),
                    "detection_source": source,
                    "domain": effective_domain,
                    "failure_reasons": reasons,
                    "observations": observations,
                    "operation_types": [item["type"] for item in scenario["operations"]],
                    "scenario": scenario["name"],
                    "source_domain": trace["domain"],
                    "success": bool(trace["success"] and not reasons),
                    "trace_id": trace["id"],
                }
            )

    baseline_by_domain: Dict[str, List[bool]] = defaultdict(list)
    for trace in trace_list:
        baseline_by_domain[trace["domain"]].append(trace["success"])
    perturbed_by_domain: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for case in cases:
        perturbed_by_domain[case["domain"]].append(case)

    domains: List[Dict[str, Any]] = []
    for domain in sorted(set(baseline_by_domain) | set(perturbed_by_domain)):
        baseline_values = baseline_by_domain.get(domain, [])
        domain_cases = perturbed_by_domain.get(domain, [])
        perturbed_values = [case["success"] for case in domain_cases]
        matched_baseline_values = [case["baseline_success"] for case in domain_cases]
        perturbed_rate = _rate(perturbed_values)
        matched_rate = _rate(matched_baseline_values)
        domains.append(
            {
                "baseline_samples": len(baseline_values),
                "baseline_success_rate": _rate(baseline_values),
                "baseline_successes": sum(baseline_values),
                "domain": domain,
                "matched_baseline_success_rate": matched_rate,
                "perturbed_samples": len(perturbed_values),
                "perturbed_success_rate": perturbed_rate,
                "perturbed_successes": sum(perturbed_values),
                "robustness_delta": _delta(perturbed_rate, matched_rate),
                "source_domains": sorted({case["source_domain"] for case in domain_cases}),
            }
        )

    cases_by_slice: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for case in cases:
        cases_by_slice[(case["scenario"], case["domain"])].append(case)
    slices: List[Dict[str, Any]] = []
    for scenario_name, domain in sorted(cases_by_slice):
        slice_cases = cases_by_slice[(scenario_name, domain)]
        success_values = [case["success"] for case in slice_cases]
        baseline_values = [case["baseline_success"] for case in slice_cases]
        success_rate = _rate(success_values)
        baseline_rate = _rate(baseline_values)
        slices.append(
            {
                "baseline_success_rate": baseline_rate,
                "domain": domain,
                "perturbations": slice_cases[0]["operation_types"],
                "robustness_delta": _delta(success_rate, baseline_rate),
                "samples": len(slice_cases),
                "scenario": scenario_name,
                "source_domains": sorted({case["source_domain"] for case in slice_cases}),
                "success_rate": success_rate,
                "successes": sum(success_values),
            }
        )

    ranked = sorted(
        slices,
        key=lambda item: (
            item["success_rate"],
            -item["samples"],
            item["robustness_delta"],
            item["scenario"],
            item["domain"],
        ),
    )
    worst_slices = []
    for rank, item in enumerate(ranked[:worst_limit], start=1):
        ranked_item = copy.deepcopy(item)
        ranked_item["rank"] = rank
        worst_slices.append(ranked_item)

    baseline_values = [trace["success"] for trace in trace_list]
    replay_values = [case["success"] for case in cases]
    matched_baseline_values = [case["baseline_success"] for case in cases]
    baseline_rate = _rate(baseline_values)
    perturbed_rate = _rate(replay_values)
    matched_rate = _rate(matched_baseline_values)
    report = {
        "domains": domains,
        "failure_detection": _auroc_proxy(cases),
        "schema_version": SCHEMA_VERSION,
        "slices": slices,
        "summary": {
            "baseline_success_rate": baseline_rate,
            "matched_baseline_success_rate": matched_rate,
            "perturbed_cases": len(cases),
            "perturbed_success_rate": perturbed_rate,
            "robustness_delta": _delta(perturbed_rate, matched_rate),
            "total_traces": len(trace_list),
            "worst_slice_success_rate": worst_slices[0]["success_rate"] if worst_slices else None,
        },
        "worst_slices": worst_slices,
    }
    return BenchmarkResult(report=report, cases=tuple(cases))


def _slug(value: str) -> str:
    """Convert a slice label into a portable deterministic filename component."""

    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "slice"


def _write_json(path: Path, value: Mapping[str, Any], force: bool) -> None:
    """Write formatted JSON, refusing to overwrite unless force was explicitly requested."""

    if path.exists() and not force:
        raise ValidationError(f"refusing to overwrite existing path '{path}'; pass --force")
    if path.exists() and path.is_dir():
        raise ValidationError(f"output path '{path}' is a directory")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as error:
        raise ValidationError(f"cannot write '{path}': {error}") from error


def export_regression_fixtures(
    result: BenchmarkResult,
    specification: Mapping[str, Any],
    directory: Path,
    force: bool = False,
) -> List[Path]:
    """Export the report's worst slices as deterministic standalone JSON fixtures."""

    if directory.exists() and not directory.is_dir():
        raise ValidationError(f"fixture path '{directory}' is not a directory")
    if directory.exists() and any(directory.iterdir()) and not force:
        raise ValidationError(
            f"refusing to write into non-empty fixture directory '{directory}'; pass --force"
        )
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise ValidationError(f"cannot create fixture directory '{directory}': {error}") from error

    scenario_by_name = {scenario["name"]: scenario for scenario in specification["scenarios"]}
    written: List[Path] = []
    for slice_item in result.report["worst_slices"]:
        matching_cases = [
            case
            for case in result.cases
            if case["scenario"] == slice_item["scenario"] and case["domain"] == slice_item["domain"]
        ]
        fixture_cases = [
            {
                "baseline_success": case["baseline_success"],
                "effective_domain": case["domain"],
                "expected_replay_success": case["success"],
                "failure_reasons": case["failure_reasons"],
                "observations": case["observations"],
                "source_domain": case["source_domain"],
                "trace_id": case["trace_id"],
            }
            for case in sorted(matching_cases, key=lambda item: item["trace_id"])
        ]
        fixture = {
            "cases": fixture_cases,
            "fixture_type": "riftgauntlet-regression",
            "scenario": scenario_by_name[slice_item["scenario"]],
            "schema_version": SCHEMA_VERSION,
            "slice": slice_item,
        }
        filename = (
            f"{slice_item['rank']:02d}-{_slug(slice_item['scenario'])}-"
            f"{_slug(slice_item['domain'])}.json"
        )
        path = directory / filename
        _write_json(path, fixture, force=force)
        written.append(path)
    return written


def run_selftest(worst_limit: int = 5) -> BenchmarkResult:
    """Run the public benchmark core on built-in data and assert stable headline metrics."""

    result = run_benchmark(BUILTIN_TRACES, BUILTIN_SPEC, worst_limit=worst_limit)
    summary = result.report["summary"]
    expected = {
        "baseline_success_rate": 1.0,
        "matched_baseline_success_rate": 1.0,
        "perturbed_cases": 7,
        "perturbed_success_rate": 0.142857,
        "robustness_delta": -0.857143,
        "total_traces": 3,
        "worst_slice_success_rate": 0.0,
    }
    if summary != expected:
        raise RuntimeError(f"self-test metric mismatch: expected {expected}, got {summary}")
    if result.report["failure_detection"]["auroc_proxy"] != 0.5:
        raise RuntimeError("self-test AUROC proxy mismatch")
    return result


def _positive_integer(raw: str) -> int:
    """Parse a positive integer for argparse and environment-backed defaults."""

    try:
        value = int(raw)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a positive integer") from error
    if value <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser used by the executable entry point."""

    parser = argparse.ArgumentParser(
        description=(
            "Replay JSONL agent traces under declarative perturbations and report domain-first "
            "robustness metrics. No network or API key is required."
        )
    )
    parser.add_argument("--input", type=Path, help="path to a JSONL trace file")
    parser.add_argument("--spec", type=Path, help="path to a JSON perturbation specification")
    parser.add_argument(
        "--worst-limit",
        type=_positive_integer,
        default=os.getenv("RIFTGAUNTLET_WORST_LIMIT", "5"),
        help="number of worst slices to rank (default: env RIFTGAUNTLET_WORST_LIMIT or 5)",
    )
    parser.add_argument("--output", type=Path, help="write the report to this file instead of stdout")
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        help="export worst slices as regression fixture JSON files",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="allow explicitly requested output or fixture files to be overwritten",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="run the offline built-in sample and verify stable metrics",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the CLI and return a process exit code."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.selftest:
            _require(
                args.input is None and args.spec is None,
                "--selftest cannot be combined with --input or --spec",
            )
            result = run_selftest(args.worst_limit)
            specification = BUILTIN_SPEC
        else:
            _require(args.input is not None, "--input is required unless --selftest is used")
            _require(args.spec is not None, "--spec is required unless --selftest is used")
            traces = load_jsonl(args.input)
            specification = load_specification(args.spec)
            result = run_benchmark(traces, specification, worst_limit=args.worst_limit)

        if args.force and args.output is None and args.fixtures_dir is None:
            raise ValidationError("--force requires --output or --fixtures-dir")
        if args.output is None:
            print(json.dumps(result.report, indent=2, sort_keys=True))
        else:
            _write_json(args.output, result.report, force=args.force)
        if args.fixtures_dir is not None:
            export_regression_fixtures(
                result,
                specification,
                args.fixtures_dir,
                force=args.force,
            )
        return 0
    except (ValidationError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
