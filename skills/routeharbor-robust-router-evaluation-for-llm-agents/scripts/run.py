#!/usr/bin/env python3
"""RouteHarbor: minimal robust router evaluation for LLM agent systems."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence, TextIO, Tuple


Query = Dict[str, Any]
DecisionMap = Dict[str, Dict[str, str]]
GroupKey = Tuple[str, str]


SAMPLE_QUERIES: List[Query] = [
    {
        "id": "q1",
        "query": "Find the refund policy in the docs.",
        "expected_route": "search",
        "modality": "text",
        "intent": "retrieval",
        "cluster": "support",
    },
    {
        "id": "q2",
        "query": "Run this SQL-like aggregation over the attached CSV.",
        "expected_route": "code_interpreter",
        "modality": "code",
        "intent": "analysis",
        "cluster": "data",
    },
    {
        "id": "q3",
        "query": "What objects are visible in this product image?",
        "expected_route": "image_analyzer",
        "modality": "image",
        "intent": "vision",
        "cluster": "catalog",
    },
    {
        "id": "q4",
        "query": "Transcribe this short customer voicemail.",
        "expected_route": "audio_transcriber",
        "modality": "audio",
        "intent": "transcription",
        "cluster": "support",
    },
    {
        "id": "q5",
        "query": "Use the calendar tool to schedule a follow-up.",
        "expected_route": "tool_planner",
        "modality": "tool-use",
        "intent": "action",
        "cluster": "operations",
    },
    {
        "id": "q6",
        "query": "Explain why this Python function raises an exception.",
        "expected_route": "code_interpreter",
        "modality": "code",
        "intent": "debugging",
        "cluster": "developer",
    },
    {
        "id": "q7",
        "query": "Compare this screenshot to the design spec.",
        "expected_route": "image_analyzer",
        "modality": "image",
        "intent": "vision",
        "cluster": "design",
    },
    {
        "id": "q8",
        "query": "Search the knowledge base, then draft a response.",
        "expected_route": "search",
        "modality": "mixed-intent",
        "intent": "retrieval",
        "cluster": "support",
    },
    {
        "id": "q9",
        "query": "Call the CRM lookup tool and summarize account status.",
        "expected_route": "tool_planner",
        "modality": "tool-use",
        "intent": "action",
        "cluster": "sales",
    },
    {
        "id": "q10",
        "query": "Detect the spoken language in this uploaded recording.",
        "expected_route": "audio_transcriber",
        "modality": "audio",
        "intent": "classification",
        "cluster": "research",
    },
    {
        "id": "q11",
        "query": "Plan a multi-step workflow using search and a ticketing tool.",
        "expected_route": "tool_planner",
        "modality": "mixed-intent",
        "intent": "action",
        "cluster": "operations",
    },
    {
        "id": "q12",
        "query": "Generate a chart from these numbers and explain the trend.",
        "expected_route": "code_interpreter",
        "modality": "code",
        "intent": "analysis",
        "cluster": "data",
    },
]


SAMPLE_DECISIONS: DecisionMap = {
    "keyword_router": {
        "q1": "search",
        "q2": "code_interpreter",
        "q3": "search",
        "q4": "audio_transcriber",
        "q5": "tool_planner",
        "q6": "code_interpreter",
        "q7": "search",
        "q8": "search",
        "q9": "search",
        "q10": "audio_transcriber",
        "q11": "search",
        "q12": "code_interpreter",
    },
    "semantic_router": {
        "q1": "search",
        "q2": "code_interpreter",
        "q3": "image_analyzer",
        "q4": "audio_transcriber",
        "q5": "tool_planner",
        "q6": "code_interpreter",
        "q7": "image_analyzer",
        "q8": "tool_planner",
        "q9": "tool_planner",
        "q10": "audio_transcriber",
        "q11": "tool_planner",
        "q12": "search",
    },
    "multimodal_router": {
        "q1": "search",
        "q2": "code_interpreter",
        "q3": "image_analyzer",
        "q4": "audio_transcriber",
        "q5": "tool_planner",
        "q6": "code_interpreter",
        "q7": "image_analyzer",
        "q8": "search",
        "q9": "tool_planner",
        "q10": "audio_transcriber",
        "q11": "tool_planner",
        "q12": "code_interpreter",
    },
}


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    default_group_fields = os.getenv("ROUTEHARBOR_DEFAULT_GROUP_FIELDS", "intent,modality")
    parser = argparse.ArgumentParser(
        description="Evaluate LLM agent router robustness across query groups."
    )
    parser.add_argument("--queries", type=Path, help="JSONL query log with ground-truth routes.")
    parser.add_argument("--decisions", type=Path, help="JSON router predictions.")
    parser.add_argument(
        "--group-fields",
        default=default_group_fields,
        help="Comma-separated metadata fields used for group analysis.",
    )
    parser.add_argument(
        "--epsilon",
        type=float,
        default=0.20,
        help="Mass budget for approximate group distribution perturbation.",
    )
    parser.add_argument("--output", type=Path, help="Write JSON report to this file.")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only emit JSON and suppress the human-readable summary.",
    )
    return parser.parse_args(argv)


def load_queries(path: Path | None) -> List[Query]:
    if path is None:
        return list(SAMPLE_QUERIES)

    queries: List[Query] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSONL record: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_number}: each query record must be an object")
            queries.append(record)
    return queries


def load_decisions(path: Path | None) -> DecisionMap:
    if path is None:
        return {name: dict(preds) for name, preds in SAMPLE_DECISIONS.items()}

    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    if isinstance(raw, dict):
        decisions: DecisionMap = {}
        for router_name, value in raw.items():
            if isinstance(value, dict):
                decisions[str(router_name)] = {str(k): str(v) for k, v in value.items()}
            elif isinstance(value, list):
                predictions: Dict[str, str] = {}
                for item in value:
                    if not isinstance(item, dict):
                        raise ValueError(f"Router {router_name} contains a non-object decision")
                    query_id = get_first(item, ["query_id", "id"])
                    predicted = get_first(item, ["predicted_route", "prediction", "route"])
                    if query_id is None or predicted is None:
                        raise ValueError(
                            f"Router {router_name} decision needs query_id/id and predicted_route"
                        )
                    predictions[str(query_id)] = str(predicted)
                decisions[str(router_name)] = predictions
            else:
                raise ValueError(f"Router {router_name} must map to an object or list")
        return decisions

    if isinstance(raw, list):
        decisions = defaultdict(dict)
        for item in raw:
            if not isinstance(item, dict):
                raise ValueError("Decision list entries must be objects")
            router = get_first(item, ["router", "router_name", "policy"])
            query_id = get_first(item, ["query_id", "id"])
            predicted = get_first(item, ["predicted_route", "prediction", "route"])
            if router is None or query_id is None or predicted is None:
                raise ValueError(
                    "Decision list entries need router, query_id/id, and predicted_route"
                )
            decisions[str(router)][str(query_id)] = str(predicted)
        return {str(name): dict(preds) for name, preds in decisions.items()}

    raise ValueError("Decision file must be a JSON object or list")


def get_first(record: Mapping[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return None


def normalize_queries(raw_queries: List[Query]) -> List[Query]:
    normalized: List[Query] = []
    seen_ids = set()
    for index, record in enumerate(raw_queries, start=1):
        query_id = get_first(record, ["id", "query_id"])
        expected = get_first(
            record, ["expected_route", "ground_truth_route", "label", "route"]
        )
        if query_id is None:
            raise ValueError(f"Query record {index} is missing id or query_id")
        if expected is None:
            raise ValueError(
                f"Query record {query_id} is missing expected_route, ground_truth_route, label, or route"
            )
        query_id = str(query_id)
        if query_id in seen_ids:
            raise ValueError(f"Duplicate query id: {query_id}")
        seen_ids.add(query_id)
        clean = dict(record)
        clean["id"] = query_id
        clean["expected_route"] = str(expected)
        normalized.append(clean)
    if not normalized:
        raise ValueError("At least one query is required")
    return normalized


def parse_group_fields(value: str) -> List[str]:
    fields = [field.strip() for field in value.split(",") if field.strip()]
    return fields or ["intent", "modality"]


def build_group_index(queries: Sequence[Query], group_fields: Sequence[str]) -> Dict[GroupKey, List[str]]:
    groups: Dict[GroupKey, List[str]] = defaultdict(list)
    for query in queries:
        query_id = str(query["id"])
        for field in group_fields:
            group_value = str(query.get(field, "unknown"))
            groups[(field, group_value)].append(query_id)
    return dict(groups)


def evaluate_router(
    router_name: str,
    predictions: Mapping[str, str],
    queries: Sequence[Query],
    groups: Mapping[GroupKey, Sequence[str]],
) -> Dict[str, Any]:
    expected_by_id = {str(query["id"]): str(query["expected_route"]) for query in queries}
    correct_by_id: Dict[str, bool] = {}
    errors: List[Dict[str, str]] = []

    for query_id, expected in expected_by_id.items():
        predicted = str(predictions.get(query_id, "__missing__"))
        is_correct = predicted == expected
        correct_by_id[query_id] = is_correct
        if not is_correct:
            errors.append(
                {
                    "query_id": query_id,
                    "expected_route": expected,
                    "predicted_route": "missing" if predicted == "__missing__" else predicted,
                }
            )

    total = len(expected_by_id)
    correct = sum(1 for value in correct_by_id.values() if value)
    group_scores: Dict[GroupKey, Dict[str, Any]] = {}

    for group_key, query_ids in groups.items():
        count = len(query_ids)
        group_correct = sum(1 for query_id in query_ids if correct_by_id[query_id])
        accuracy = safe_div(group_correct, count)
        group_scores[group_key] = {
            "count": count,
            "correct": group_correct,
            "accuracy": round_float(accuracy),
            "loss": round_float(1.0 - accuracy),
        }

    worst_group_loss = max((score["loss"] for score in group_scores.values()), default=0.0)

    return {
        "router": router_name,
        "count": total,
        "correct": correct,
        "accuracy": round_float(safe_div(correct, total)),
        "loss": round_float(1.0 - safe_div(correct, total)),
        "missing_predictions": sorted(
            query_id for query_id in expected_by_id if query_id not in predictions
        ),
        "errors": errors,
        "group_scores": group_scores,
        "worst_group_loss": round_float(worst_group_loss),
    }


def attach_regret(
    router_results: MutableMapping[str, Dict[str, Any]],
    groups: Mapping[GroupKey, Sequence[str]],
) -> None:
    best_by_group: Dict[GroupKey, float] = {}
    for group_key in groups:
        best_by_group[group_key] = max(
            float(result["group_scores"][group_key]["accuracy"])
            for result in router_results.values()
        )

    for result in router_results.values():
        worst_regret = 0.0
        for group_key, best_accuracy in best_by_group.items():
            score = result["group_scores"][group_key]
            regret = max(0.0, best_accuracy - float(score["accuracy"]))
            score["regret_vs_best"] = round_float(regret)
            worst_regret = max(worst_regret, regret)
        result["worst_group_regret"] = round_float(worst_regret)


def attach_perturbation_scores(
    router_results: MutableMapping[str, Dict[str, Any]],
    groups: Mapping[GroupKey, Sequence[str]],
    query_count: int,
    epsilon: float,
) -> None:
    total_memberships = sum(len(query_ids) for query_ids in groups.values()) or query_count
    group_weights = {
        group_key: len(query_ids) / total_memberships for group_key, query_ids in groups.items()
    }

    for result in router_results.values():
        group_accuracies = {
            group_key: float(result["group_scores"][group_key]["accuracy"])
            for group_key in groups
        }
        shifted_accuracy, drop = approximate_distribution_shift(
            group_accuracies, group_weights, epsilon
        )
        result["perturbation"] = {
            "epsilon": round_float(epsilon),
            "shifted_accuracy": round_float(shifted_accuracy),
            "accuracy_drop": round_float(drop),
            "sensitivity_per_epsilon": round_float(safe_div(drop, epsilon)),
            "stability_score": round_float(shifted_accuracy),
        }


def approximate_distribution_shift(
    accuracies: Mapping[GroupKey, float],
    weights: Mapping[GroupKey, float],
    epsilon: float,
) -> Tuple[float, float]:
    if not accuracies:
        return 0.0, 0.0

    epsilon = max(0.0, min(1.0, epsilon))
    shifted_weights = dict(weights)
    baseline = sum(shifted_weights[group_key] * accuracies[group_key] for group_key in accuracies)
    low_groups = sorted(accuracies, key=lambda key: accuracies[key])
    high_groups = sorted(accuracies, key=lambda key: accuracies[key], reverse=True)
    low_index = 0
    high_index = 0
    remaining = epsilon

    while remaining > 1e-12 and low_index < len(low_groups) and high_index < len(high_groups):
        low_key = low_groups[low_index]
        high_key = high_groups[high_index]
        if accuracies[high_key] <= accuracies[low_key]:
            break
        available = shifted_weights.get(high_key, 0.0)
        if available <= 1e-12:
            high_index += 1
            continue
        move = min(available, remaining)
        shifted_weights[high_key] -= move
        shifted_weights[low_key] = shifted_weights.get(low_key, 0.0) + move
        remaining -= move
        if shifted_weights[high_key] <= 1e-12:
            high_index += 1
        low_index = 0

    shifted_accuracy = sum(
        shifted_weights[group_key] * accuracies[group_key] for group_key in accuracies
    )
    drop = max(0.0, baseline - shifted_accuracy)
    return shifted_accuracy, drop


def format_per_group(
    group_scores: Mapping[GroupKey, Mapping[str, Any]],
    group_fields: Sequence[str],
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    nested: Dict[str, Dict[str, Dict[str, Any]]] = {field: {} for field in group_fields}
    for (field, value), score in sorted(group_scores.items()):
        nested.setdefault(field, {})[value] = dict(score)
    return nested


def worst_groups(
    group_scores: Mapping[GroupKey, Mapping[str, Any]],
    limit: int = 5,
) -> List[Dict[str, Any]]:
    rows = []
    for (field, value), score in group_scores.items():
        rows.append(
            {
                "field": field,
                "value": value,
                "count": score["count"],
                "accuracy": score["accuracy"],
                "loss": score["loss"],
                "regret_vs_best": score.get("regret_vs_best", 0.0),
            }
        )
    rows.sort(key=lambda row: (-row["loss"], -row["regret_vs_best"], row["field"], row["value"]))
    return rows[:limit]


def build_report(
    queries: Sequence[Query],
    decisions: DecisionMap,
    group_fields: Sequence[str],
    epsilon: float,
) -> Dict[str, Any]:
    groups = build_group_index(queries, group_fields)
    router_results: Dict[str, Dict[str, Any]] = {}
    for router_name, predictions in sorted(decisions.items()):
        router_results[router_name] = evaluate_router(router_name, predictions, queries, groups)

    attach_regret(router_results, groups)
    attach_perturbation_scores(router_results, groups, len(queries), epsilon)

    ranking = []
    for router_name, result in router_results.items():
        ranking.append(
            {
                "router": router_name,
                "average_accuracy": result["accuracy"],
                "worst_group_loss": result["worst_group_loss"],
                "worst_group_regret": result["worst_group_regret"],
                "perturbed_accuracy": result["perturbation"]["shifted_accuracy"],
                "stability_score": result["perturbation"]["stability_score"],
            }
        )

    ranking.sort(
        key=lambda row: (
            row["worst_group_regret"],
            -row["perturbed_accuracy"],
            -row["average_accuracy"],
            row["worst_group_loss"],
            row["router"],
        )
    )
    for index, row in enumerate(ranking, start=1):
        row["rank"] = index

    recommended = ranking[0]["router"] if ranking else None
    report = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "query_count": len(queries),
            "router_count": len(decisions),
            "routers": sorted(decisions),
            "group_fields": list(group_fields),
            "perturbation_epsilon": round_float(epsilon),
        },
        "recommendation": {
            "router": recommended,
            "reason": (
                "Lowest worst-group regret, then highest perturbed accuracy and average accuracy."
                if recommended
                else "No routers were evaluated."
            ),
        },
        "ranking": ranking,
        "routers": {},
    }

    for router_name, result in sorted(router_results.items()):
        report["routers"][router_name] = {
            "count": result["count"],
            "correct": result["correct"],
            "average_accuracy": result["accuracy"],
            "average_loss": result["loss"],
            "worst_group_loss": result["worst_group_loss"],
            "worst_group_regret": result["worst_group_regret"],
            "perturbation": result["perturbation"],
            "missing_predictions": result["missing_predictions"],
            "errors": result["errors"],
            "worst_groups": worst_groups(result["group_scores"]),
            "per_group": format_per_group(result["group_scores"], group_fields),
        }

    return report


def print_summary(report: Mapping[str, Any], stream: TextIO = sys.stdout) -> None:
    print("RouteHarbor router robustness ranking", file=stream)
    print(f"Queries: {report['input']['query_count']}", file=stream)
    print(f"Group fields: {', '.join(report['input']['group_fields'])}", file=stream)
    print(file=stream)
    for row in report["ranking"]:
        print(
            "#{rank} {router}: accuracy={average_accuracy:.3f} "
            "worst_group_regret={worst_group_regret:.3f} "
            "perturbed_accuracy={perturbed_accuracy:.3f}".format(**row),
            file=stream,
        )
    print(file=stream)
    print(f"Recommended router: {report['recommendation']['router']}", file=stream)


def write_report(report: Mapping[str, Any], output: Path | None, quiet: bool) -> None:
    encoded = json.dumps(report, indent=2, sort_keys=True)
    if output is not None:
        output.write_text(encoded + "\n", encoding="utf-8")
        if not quiet:
            print(f"Wrote JSON report: {output}")
    else:
        print(encoded)


def safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def round_float(value: float) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return round(float(value), 6)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        queries = normalize_queries(load_queries(args.queries))
        decisions = load_decisions(args.decisions)
        if not decisions:
            raise ValueError("At least one router decision set is required")
        group_fields = parse_group_fields(args.group_fields)
        report = build_report(queries, decisions, group_fields, args.epsilon)
        if not args.quiet:
            summary_stream = sys.stderr if args.output is None else sys.stdout
            print_summary(report, stream=summary_stream)
            print(file=summary_stream)
        write_report(report, args.output, args.quiet)
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
