#!/usr/bin/env python3
"""RouteQuake: distribution shift stress testing for router evaluation logs."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable


SAMPLE_ROWS: list[dict[str, str]] = [
    {
        "id": "1",
        "query": "Reset my password",
        "task": "account",
        "intent": "password_reset",
        "difficulty": "easy",
        "cohort": "consumer",
        "perturbation": "none",
        "rare_case": "false",
        "selected_router": "fast",
        "correct_router": "fast",
        "score_fast": "0.92",
        "score_balanced": "0.80",
        "score_deep": "0.66",
    },
    {
        "id": "2",
        "query": "Find my invoice",
        "task": "billing",
        "intent": "invoice_lookup",
        "difficulty": "easy",
        "cohort": "consumer",
        "perturbation": "none",
        "rare_case": "false",
        "selected_router": "fast",
        "correct_router": "fast",
        "score_fast": "0.88",
        "score_balanced": "0.82",
        "score_deep": "0.70",
    },
    {
        "id": "3",
        "query": "Explain a contract indemnity clause",
        "task": "legal",
        "intent": "contract_analysis",
        "difficulty": "hard",
        "cohort": "enterprise",
        "perturbation": "paraphrase",
        "rare_case": "true",
        "selected_router": "balanced",
        "correct_router": "deep",
        "score_fast": "0.48",
        "score_balanced": "0.74",
        "score_deep": "0.91",
    },
    {
        "id": "4",
        "query": "Diagnose API latency spike",
        "task": "ops",
        "intent": "incident_debug",
        "difficulty": "hard",
        "cohort": "enterprise",
        "perturbation": "typo",
        "rare_case": "true",
        "selected_router": "fast",
        "correct_router": "deep",
        "score_fast": "0.55",
        "score_balanced": "0.70",
        "score_deep": "0.89",
    },
    {
        "id": "5",
        "query": "Route a refund exception",
        "task": "billing",
        "intent": "refund_exception",
        "difficulty": "medium",
        "cohort": "small_business",
        "perturbation": "none",
        "rare_case": "false",
        "selected_router": "balanced",
        "correct_router": "balanced",
        "score_fast": "0.63",
        "score_balanced": "0.84",
        "score_deep": "0.78",
    },
    {
        "id": "6",
        "query": "Classify unknown webhook failure",
        "task": "ops",
        "intent": "webhook_debug",
        "difficulty": "rare",
        "cohort": "enterprise",
        "perturbation": "paraphrase",
        "rare_case": "true",
        "selected_router": "balanced",
        "correct_router": "deep",
        "score_fast": "0.40",
        "score_balanced": "0.69",
        "score_deep": "0.90",
    },
    {
        "id": "7",
        "query": "Summarize product feedback",
        "task": "support",
        "intent": "feedback_summary",
        "difficulty": "easy",
        "cohort": "consumer",
        "perturbation": "none",
        "rare_case": "false",
        "selected_router": "fast",
        "correct_router": "fast",
        "score_fast": "0.85",
        "score_balanced": "0.77",
        "score_deep": "0.64",
    },
    {
        "id": "8",
        "query": "Handle payroll compliance edge case",
        "task": "hr",
        "intent": "compliance_edge",
        "difficulty": "rare",
        "cohort": "enterprise",
        "perturbation": "adversarial",
        "rare_case": "true",
        "selected_router": "balanced",
        "correct_router": "deep",
        "score_fast": "0.38",
        "score_balanced": "0.65",
        "score_deep": "0.88",
    },
]


WeightFn = Callable[[dict[str, Any]], float]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stress test router evaluation logs under simple distribution shifts."
    )
    parser.add_argument(
        "--input",
        help="CSV evaluation log. Uses built-in sample data when omitted.",
    )
    parser.add_argument(
        "--output-dir",
        default=os.environ.get("ROUTEQUAKE_OUTPUT_DIR", "reports"),
        help="Directory for Markdown and JSON reports. Default: reports",
    )
    parser.add_argument(
        "--slice-columns",
        default="task,intent,difficulty,cohort",
        help="Comma-separated metadata columns used for worst-slice analysis.",
    )
    parser.add_argument(
        "--rare-multiplier",
        type=float,
        default=4.0,
        help="Weight multiplier for rare or hard examples. Default: 4.0",
    )
    parser.add_argument(
        "--perturbation-multiplier",
        type=float,
        default=3.0,
        help="Weight multiplier for non-none perturbation labels. Default: 3.0",
    )
    parser.add_argument(
        "--min-worst-slice-accuracy",
        type=float,
        help="Exit with status 2 if any scenario falls below this worst-slice threshold.",
    )
    return parser.parse_args()


def load_rows(input_path: str | None) -> tuple[list[dict[str, str]], str]:
    if not input_path:
        return [row.copy() for row in SAMPLE_ROWS], "built_in_sample"

    path = Path(input_path)
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = [dict(row) for row in reader]

    if not rows:
        raise ValueError(f"No rows found in {input_path}")

    return rows, str(path)


def as_float(value: Any, column: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Column {column!r} must contain numeric values, got {value!r}") from exc
    if math.isnan(number) or math.isinf(number):
        raise ValueError(f"Column {column!r} must contain finite values, got {value!r}")
    return number


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "rare"}


def infer_routers(rows: list[dict[str, str]]) -> list[str]:
    columns = set().union(*(row.keys() for row in rows))
    score_columns = sorted(column for column in columns if column.startswith("score_"))
    routers = [column.removeprefix("score_") for column in score_columns]
    if len(routers) < 2:
        raise ValueError("Expected at least two numeric score_<router> columns.")
    return routers


def validate_rows(rows: list[dict[str, str]], routers: list[str]) -> list[dict[str, Any]]:
    required = {"selected_router", "correct_router"}
    missing = sorted(column for column in required if column not in rows[0])
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")

    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        record: dict[str, Any] = dict(row)
        selected = str(row.get("selected_router", "")).strip()
        correct = str(row.get("correct_router", "")).strip()
        if not selected or not correct:
            raise ValueError(f"Row {index} must include selected_router and correct_router.")
        if selected not in routers:
            raise ValueError(f"Row {index} selected_router {selected!r} has no score column.")
        if correct not in routers:
            raise ValueError(f"Row {index} correct_router {correct!r} has no score column.")

        scores = {router: as_float(row.get(f"score_{router}"), f"score_{router}") for router in routers}
        best_router = max(scores, key=scores.get)
        selected_score = scores[selected]
        best_score = scores[best_router]

        record["_scores"] = scores
        record["_selected_score"] = selected_score
        record["_best_score"] = best_score
        record["_best_router"] = best_router
        record["_accuracy"] = 1.0 if selected == correct else 0.0
        record["_regret"] = max(0.0, best_score - selected_score)
        normalized.append(record)

    return normalized


def weighted_mean(rows: list[dict[str, Any]], weight_fn: WeightFn, value_fn: Callable[[dict[str, Any]], float]) -> float:
    weighted_sum = 0.0
    total_weight = 0.0
    for row in rows:
        weight = max(0.0, float(weight_fn(row)))
        weighted_sum += weight * value_fn(row)
        total_weight += weight
    if total_weight == 0:
        return 0.0
    return weighted_sum / total_weight


def is_rare_case(row: dict[str, Any]) -> bool:
    difficulty = str(row.get("difficulty", "")).strip().lower()
    cohort = str(row.get("cohort", "")).strip().lower()
    intent = str(row.get("intent", "")).strip().lower()
    return (
        truthy(row.get("rare_case"))
        or difficulty in {"hard", "rare", "edge"}
        or "rare" in cohort
        or "edge" in intent
    )


def has_perturbation(row: dict[str, Any]) -> bool:
    label = str(row.get("perturbation", "none")).strip().lower()
    return label not in {"", "none", "original", "base", "clean"}


def build_scenarios(rows: list[dict[str, Any]], rare_multiplier: float, perturbation_multiplier: float) -> dict[str, WeightFn]:
    task_counts: dict[str, int] = defaultdict(int)
    for row in rows:
        task_counts[str(row.get("task", "unknown"))] += 1
    max_task_count = max(task_counts.values()) if task_counts else 1

    return {
        "baseline": lambda row: 1.0,
        "class_reweight_task": lambda row: max_task_count / task_counts[str(row.get("task", "unknown"))],
        "rare_case_amplification": lambda row: rare_multiplier if is_rare_case(row) else 1.0,
        "query_perturbation_focus": lambda row: perturbation_multiplier if has_perturbation(row) else 1.0,
    }


def scenario_metrics(
    rows: list[dict[str, Any]],
    scenarios: dict[str, WeightFn],
    routers: list[str],
    slice_columns: list[str],
) -> dict[str, Any]:
    results: dict[str, Any] = {}

    for scenario_name, weight_fn in scenarios.items():
        weighted_accuracy = weighted_mean(rows, weight_fn, lambda row: row["_accuracy"])
        weighted_regret = weighted_mean(rows, weight_fn, lambda row: row["_regret"])
        worst_slice = compute_worst_slice(rows, weight_fn, slice_columns)
        router_scores = {
            router: weighted_mean(rows, weight_fn, lambda row, router=router: row["_scores"][router])
            for router in routers
        }
        results[scenario_name] = {
            "accuracy": round(weighted_accuracy, 6),
            "mean_regret": round(weighted_regret, 6),
            "worst_slice": worst_slice,
            "router_scores": {router: round(score, 6) for router, score in router_scores.items()},
        }

    return results


def compute_worst_slice(rows: list[dict[str, Any]], weight_fn: WeightFn, slice_columns: list[str]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for column in slice_columns:
        if column not in rows[0]:
            continue
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[str(row.get(column, "unknown"))].append(row)
        for value, group_rows in grouped.items():
            weight = sum(max(0.0, float(weight_fn(row))) for row in group_rows)
            accuracy = weighted_mean(group_rows, weight_fn, lambda row: row["_accuracy"])
            regret = weighted_mean(group_rows, weight_fn, lambda row: row["_regret"])
            candidates.append(
                {
                    "column": column,
                    "value": value,
                    "rows": len(group_rows),
                    "weight": round(weight, 6),
                    "accuracy": round(accuracy, 6),
                    "mean_regret": round(regret, 6),
                }
            )

    if not candidates:
        return {
            "column": "all",
            "value": "all",
            "rows": len(rows),
            "weight": round(sum(weight_fn(row) for row in rows), 6),
            "accuracy": round(weighted_mean(rows, weight_fn, lambda row: row["_accuracy"]), 6),
            "mean_regret": round(weighted_mean(rows, weight_fn, lambda row: row["_regret"]), 6),
        }

    return sorted(candidates, key=lambda item: (item["accuracy"], -item["mean_regret"], item["rows"]))[0]


def instability_ranking(metrics: dict[str, Any], routers: list[str]) -> list[dict[str, Any]]:
    ranking = []
    baseline_scores = metrics["baseline"]["router_scores"]
    for router in routers:
        scores = [scenario["router_scores"][router] for scenario in metrics.values()]
        drop_from_baseline = baseline_scores[router] - min(scores)
        score_range = max(scores) - min(scores)
        ranking.append(
            {
                "router": router,
                "baseline_score": round(baseline_scores[router], 6),
                "minimum_scenario_score": round(min(scores), 6),
                "drop_from_baseline": round(drop_from_baseline, 6),
                "score_range": round(score_range, 6),
            }
        )
    return sorted(ranking, key=lambda item: (item["drop_from_baseline"], item["score_range"]), reverse=True)


def top_regret_rows(rows: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    sorted_rows = sorted(rows, key=lambda row: row["_regret"], reverse=True)
    output = []
    for row in sorted_rows[:limit]:
        output.append(
            {
                "id": row.get("id", ""),
                "query": row.get("query", ""),
                "selected_router": row.get("selected_router", ""),
                "best_router_by_score": row["_best_router"],
                "correct_router": row.get("correct_router", ""),
                "regret": round(row["_regret"], 6),
                "task": row.get("task", ""),
                "difficulty": row.get("difficulty", ""),
                "perturbation": row.get("perturbation", ""),
            }
        )
    return output


def make_report(
    rows: list[dict[str, Any]],
    routers: list[str],
    data_source: str,
    metrics: dict[str, Any],
    instability: list[dict[str, Any]],
    regret_rows: list[dict[str, Any]],
    api_key_detected: bool,
) -> dict[str, Any]:
    worst_scenario = min(metrics.items(), key=lambda item: item[1]["worst_slice"]["accuracy"])
    return {
        "tool": "RouteQuake",
        "data_source": data_source,
        "row_count": len(rows),
        "routers": routers,
        "api_key_detected": api_key_detected,
        "summary": {
            "baseline_accuracy": metrics["baseline"]["accuracy"],
            "worst_scenario": worst_scenario[0],
            "worst_slice_accuracy": worst_scenario[1]["worst_slice"]["accuracy"],
            "baseline_mean_regret": metrics["baseline"]["mean_regret"],
        },
        "scenarios": metrics,
        "instability_ranking": instability,
        "top_regret_rows": regret_rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# RouteQuake Report",
        "",
        f"- Data source: `{report['data_source']}`",
        f"- Rows: {report['row_count']}",
        f"- Routers: {', '.join(report['routers'])}",
        f"- API key detected: {str(report['api_key_detected']).lower()}",
        "",
        "## Summary",
        "",
        f"- Baseline accuracy: {report['summary']['baseline_accuracy']:.3f}",
        f"- Baseline mean regret: {report['summary']['baseline_mean_regret']:.3f}",
        f"- Worst scenario: `{report['summary']['worst_scenario']}`",
        f"- Worst-slice accuracy: {report['summary']['worst_slice_accuracy']:.3f}",
        "",
        "## Scenario Metrics",
        "",
        "| Scenario | Accuracy | Mean Regret | Worst Slice | Worst-Slice Accuracy |",
        "| --- | ---: | ---: | --- | ---: |",
    ]

    for name, scenario in report["scenarios"].items():
        worst = scenario["worst_slice"]
        slice_name = f"{worst['column']}={worst['value']}"
        lines.append(
            f"| {name} | {scenario['accuracy']:.3f} | {scenario['mean_regret']:.3f} | "
            f"{slice_name} | {worst['accuracy']:.3f} |"
        )

    lines.extend(
        [
            "",
            "## Router Instability Ranking",
            "",
            "| Rank | Router | Baseline Score | Minimum Scenario Score | Drop From Baseline | Score Range |",
            "| ---: | --- | ---: | ---: | ---: | ---: |",
        ]
    )

    for index, item in enumerate(report["instability_ranking"], start=1):
        lines.append(
            f"| {index} | {item['router']} | {item['baseline_score']:.3f} | "
            f"{item['minimum_scenario_score']:.3f} | {item['drop_from_baseline']:.3f} | "
            f"{item['score_range']:.3f} |"
        )

    lines.extend(
        [
            "",
            "## Highest-Regret Rows",
            "",
            "| ID | Selected | Best By Score | Correct | Regret | Task | Difficulty | Perturbation |",
            "| --- | --- | --- | --- | ---: | --- | --- | --- |",
        ]
    )

    for item in report["top_regret_rows"]:
        lines.append(
            f"| {item['id']} | {item['selected_router']} | {item['best_router_by_score']} | "
            f"{item['correct_router']} | {item['regret']:.3f} | {item['task']} | "
            f"{item['difficulty']} | {item['perturbation']} |"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Accuracy is computed as `selected_router == correct_router`.",
            "- Regret is `best_score - selected_score` using the numeric `score_<router>` columns.",
            "- Shift scenarios are transparent weighting schemes over existing rows.",
        ]
    )

    return "\n".join(lines) + "\n"


def write_outputs(report: dict[str, Any], output_dir: str) -> tuple[Path, Path]:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    markdown_path = path / "routequake_report.md"
    json_path = path / "routequake_report.json"
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return markdown_path, json_path


def main() -> int:
    args = parse_args()
    rows_raw, data_source = load_rows(args.input)
    routers = infer_routers(rows_raw)
    rows = validate_rows(rows_raw, routers)
    slice_columns = [column.strip() for column in args.slice_columns.split(",") if column.strip()]
    scenarios = build_scenarios(rows, args.rare_multiplier, args.perturbation_multiplier)
    metrics = scenario_metrics(rows, scenarios, routers, slice_columns)
    instability = instability_ranking(metrics, routers)
    regret_rows = top_regret_rows(rows)
    report = make_report(
        rows=rows,
        routers=routers,
        data_source=data_source,
        metrics=metrics,
        instability=instability,
        regret_rows=regret_rows,
        api_key_detected=bool(os.environ.get("ROUTEQUAKE_API_KEY")),
    )
    markdown_path, json_path = write_outputs(report, args.output_dir)

    print(f"RouteQuake analyzed {len(rows)} rows across {len(routers)} routers.")
    print(f"Markdown report: {markdown_path}")
    print(f"JSON report: {json_path}")
    print(
        "Worst-slice accuracy: "
        f"{report['summary']['worst_slice_accuracy']:.3f} "
        f"({report['summary']['worst_scenario']})"
    )

    threshold = args.min_worst_slice_accuracy
    if threshold is not None and report["summary"]["worst_slice_accuracy"] < threshold:
        print(
            f"Release gate failed: worst-slice accuracy "
            f"{report['summary']['worst_slice_accuracy']:.3f} < {threshold:.3f}",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"RouteQuake error: {exc}", file=sys.stderr)
        raise SystemExit(1)
