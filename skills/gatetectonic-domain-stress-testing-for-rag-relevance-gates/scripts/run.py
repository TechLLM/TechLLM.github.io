#!/usr/bin/env python3
"""GateTectonic reference CLI.

This is a self-contained benchmark harness for RAG relevance gates. It uses a
local lexical scorer by default, then evaluates robustness by source domain and
stress variants.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
from collections import defaultdict
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable, Iterable


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "do",
    "does",
    "for",
    "from",
    "has",
    "have",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}


@dataclass(frozen=True)
class Example:
    question: str
    document: str
    label: int
    source_domain: str
    document_type: str
    question_type: str
    variant: str = "clean"
    row_id: str = ""


class RelevanceGate:
    """Minimal pluggable relevance gate interface."""

    name = "base"

    def score(self, question: str, document: str) -> float:
        raise NotImplementedError

    def predict(self, question: str, document: str, threshold: float) -> int:
        return int(self.score(question, document) >= threshold)


class LexicalOverlapGate(RelevanceGate):
    """Small local baseline gate that works without API keys."""

    name = "lexical_overlap_gate"

    def score(self, question: str, document: str) -> float:
        query_tokens = tokenize(question)
        doc_tokens = tokenize(document)
        if not query_tokens or not doc_tokens:
            return 0.0

        query_set = set(query_tokens)
        doc_set = set(doc_tokens)
        coverage = len(query_set & doc_set) / len(query_set)
        jaccard = len(query_set & doc_set) / max(1, len(query_set | doc_set))
        bigram_bonus = bigram_overlap(query_tokens, doc_tokens)
        return clamp((0.7 * coverage) + (0.2 * jaccard) + (0.1 * bigram_bonus))


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


def bigram_overlap(query_tokens: list[str], doc_tokens: list[str]) -> float:
    if len(query_tokens) < 2 or len(doc_tokens) < 2:
        return 0.0
    query_bigrams = set(zip(query_tokens, query_tokens[1:]))
    doc_bigrams = set(zip(doc_tokens, doc_tokens[1:]))
    return len(query_bigrams & doc_bigrams) / max(1, len(query_bigrams))


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def built_in_examples() -> list[Example]:
    rows = [
        {
            "question": "What notice is required before terminating a lease?",
            "document": "The lease requires a written notice 30 days before termination.",
            "label": "1",
            "source_domain": "legal",
            "document_type": "contract",
            "question_type": "policy",
        },
        {
            "question": "What notice is required before terminating a lease?",
            "document": "The recipe calls for flour, salt, yeast, and warm water.",
            "label": "0",
            "source_domain": "legal",
            "document_type": "contract",
            "question_type": "policy",
        },
        {
            "question": "Which lab value indicates elevated glucose?",
            "document": "The metabolic panel shows glucose at 188 mg/dL, above the reference range.",
            "label": "1",
            "source_domain": "health",
            "document_type": "clinical_note",
            "question_type": "factual",
        },
        {
            "question": "Which lab value indicates elevated glucose?",
            "document": "The travel memo lists baggage limits and check-in times.",
            "label": "0",
            "source_domain": "health",
            "document_type": "clinical_note",
            "question_type": "factual",
        },
        {
            "question": "When does the refund window close?",
            "document": "Customers may request a refund within 14 days of purchase.",
            "label": "1",
            "source_domain": "commerce",
            "document_type": "policy_page",
            "question_type": "short_factual",
        },
        {
            "question": "When does the refund window close?",
            "document": "The system status page reports database latency and uptime.",
            "label": "0",
            "source_domain": "commerce",
            "document_type": "policy_page",
            "question_type": "short_factual",
        },
        {
            "question": "What caused the quarterly margin change?",
            "document": "Quarterly margin improved after lower shipping costs and higher renewal rates.",
            "label": "1",
            "source_domain": "finance",
            "document_type": "earnings_note",
            "question_type": "causal",
        },
        {
            "question": "What caused the quarterly margin change?",
            "document": "The employee handbook explains badge replacement and office access.",
            "label": "0",
            "source_domain": "finance",
            "document_type": "earnings_note",
            "question_type": "causal",
        },
    ]
    return [row_to_example(row, str(index + 1)) for index, row in enumerate(rows)]


def parse_label(value: str) -> int:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "relevant", "positive"}:
        return 1
    if normalized in {"0", "false", "no", "n", "irrelevant", "negative"}:
        return 0
    raise ValueError(f"Unsupported label value: {value!r}")


def row_to_example(row: dict[str, str], fallback_id: str) -> Example:
    required = [
        "question",
        "document",
        "label",
        "source_domain",
        "document_type",
        "question_type",
    ]
    missing = [field for field in required if field not in row or row[field] == ""]
    if missing:
        raise ValueError(f"Missing required CSV field(s): {', '.join(missing)}")

    return Example(
        question=row["question"].strip(),
        document=row["document"].strip(),
        label=parse_label(row["label"]),
        source_domain=row["source_domain"].strip(),
        document_type=row["document_type"].strip(),
        question_type=row["question_type"].strip(),
        row_id=row.get("id", fallback_id).strip() or fallback_id,
    )


def load_examples(path: Path | None) -> tuple[list[Example], str]:
    if path is None:
        return built_in_examples(), "built_in_sample"

    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        examples = [row_to_example(row, str(index + 1)) for index, row in enumerate(reader)]

    if not examples:
        raise ValueError(f"No examples found in {path}")
    return examples, str(path)


def corrupt_text(text: str) -> str:
    """Deterministic OCR-like corruption for repeatable stress reports."""
    replacements = str.maketrans({"o": "0", "O": "0", "l": "1", "I": "1", "e": "3"})
    words = text.translate(replacements).split()
    kept_words = [word for index, word in enumerate(words) if index % 7 != 3]
    return " ".join(kept_words)


def make_stress_examples(examples: list[Example], include_stress: bool) -> list[Example]:
    if not include_stress:
        return examples

    stressed: list[Example] = []
    for example in examples:
        stressed.append(example)
        stressed.append(
            replace(
                example,
                document="",
                label=0,
                variant="missing_context",
                row_id=f"{example.row_id}:missing",
            )
        )
        stressed.append(
            replace(
                example,
                document=corrupt_text(example.document),
                variant="corrupted_input",
                row_id=f"{example.row_id}:corrupt",
            )
        )
    return stressed


def metrics_for(examples: list[Example], predictor: Callable[[Example], int]) -> dict[str, float | int]:
    counts = {"tp": 0, "tn": 0, "fp": 0, "fn": 0}
    for example in examples:
        prediction = predictor(example)
        if prediction == 1 and example.label == 1:
            counts["tp"] += 1
        elif prediction == 0 and example.label == 0:
            counts["tn"] += 1
        elif prediction == 1 and example.label == 0:
            counts["fp"] += 1
        else:
            counts["fn"] += 1

    total = sum(counts.values())
    accuracy = (counts["tp"] + counts["tn"]) / total if total else 0.0
    precision = counts["tp"] / (counts["tp"] + counts["fp"]) if counts["tp"] + counts["fp"] else 0.0
    recall = counts["tp"] / (counts["tp"] + counts["fn"]) if counts["tp"] + counts["fn"] else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0

    return {
        "n": total,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        **counts,
    }


def candidate_thresholds() -> list[float]:
    return [round(index / 20, 2) for index in range(0, 21)]


def tune_threshold(gate: RelevanceGate, train_examples: list[Example]) -> tuple[float, dict[str, float | int]]:
    best_threshold = 0.0
    best_metrics: dict[str, float | int] | None = None
    best_key = (-1.0, -1.0, -1.0)

    for threshold in candidate_thresholds():
        result = metrics_for(
            train_examples,
            lambda example, t=threshold: gate.predict(example.question, example.document, t),
        )
        key = (
            float(result["accuracy"]),
            float(result["f1"]),
            -abs(threshold - 0.5),
        )
        if key > best_key:
            best_key = key
            best_threshold = threshold
            best_metrics = result

    return best_threshold, best_metrics or {}


def group_by(examples: Iterable[Example], field: str) -> dict[str, list[Example]]:
    grouped: dict[str, list[Example]] = defaultdict(list)
    for example in examples:
        grouped[str(getattr(example, field))].append(example)
    return dict(sorted(grouped.items()))


def slice_metrics(
    examples: list[Example],
    predictor: Callable[[Example], int],
    fields: list[str],
) -> dict[str, dict[str, dict[str, float | int]]]:
    report: dict[str, dict[str, dict[str, float | int]]] = {}
    for field in fields:
        report[field] = {
            value: metrics_for(items, predictor)
            for value, items in group_by(examples, field).items()
        }
    return report


def accuracy_delta(
    fixed_slices: dict[str, dict[str, dict[str, float | int]]],
    baseline_slices: dict[str, dict[str, dict[str, float | int]]],
) -> dict[str, dict[str, float]]:
    deltas: dict[str, dict[str, float]] = {}
    for field, values in fixed_slices.items():
        deltas[field] = {}
        for value, fixed_metrics in values.items():
            baseline_metrics = baseline_slices.get(field, {}).get(value)
            if baseline_metrics:
                delta = float(fixed_metrics["accuracy"]) - float(baseline_metrics["accuracy"])
                deltas[field][value] = round(delta, 4)
    return deltas


def evaluate(gate: RelevanceGate, examples: list[Example], fixed_threshold: float) -> dict[str, object]:
    domains = sorted({example.source_domain for example in examples})
    fixed_predictor = lambda example: gate.predict(example.question, example.document, fixed_threshold)
    erm_threshold, erm_train_metrics = tune_threshold(gate, examples)
    erm_predictor = lambda example: gate.predict(example.question, example.document, erm_threshold)

    fixed_overall = metrics_for(examples, fixed_predictor)
    erm_overall = metrics_for(examples, erm_predictor)
    fixed_slices = slice_metrics(
        examples,
        fixed_predictor,
        ["source_domain", "document_type", "question_type", "variant"],
    )
    erm_slices = slice_metrics(
        examples,
        erm_predictor,
        ["source_domain", "document_type", "question_type", "variant"],
    )

    leave_one_domain_out = []
    for domain in domains:
        train = [example for example in examples if example.source_domain != domain]
        test = [example for example in examples if example.source_domain == domain]
        if not train or not test:
            continue

        domain_threshold, train_metrics = tune_threshold(gate, train)
        domain_erm_predictor = lambda example, t=domain_threshold: gate.predict(
            example.question,
            example.document,
            t,
        )
        fixed_metrics = metrics_for(test, fixed_predictor)
        baseline_metrics = metrics_for(test, domain_erm_predictor)
        fixed_domain_slices = slice_metrics(test, fixed_predictor, ["document_type", "question_type", "variant"])
        baseline_domain_slices = slice_metrics(
            test,
            domain_erm_predictor,
            ["document_type", "question_type", "variant"],
        )
        absolute_gain = float(fixed_metrics["accuracy"]) - float(baseline_metrics["accuracy"])
        baseline_accuracy = float(baseline_metrics["accuracy"])
        relative_gain = absolute_gain / baseline_accuracy if baseline_accuracy else math.inf

        leave_one_domain_out.append(
            {
                "held_out_domain": domain,
                "train_domains": [candidate for candidate in domains if candidate != domain],
                "erm_threshold": domain_threshold,
                "erm_train_metrics": train_metrics,
                "fixed_gate": fixed_metrics,
                "erm_baseline": baseline_metrics,
                "absolute_gain_vs_erm": round(absolute_gain, 4),
                "relative_gain_vs_erm": "inf" if math.isinf(relative_gain) else round(relative_gain, 4),
                "per_slice_accuracy_delta_vs_erm": accuracy_delta(
                    fixed_domain_slices,
                    baseline_domain_slices,
                ),
            }
        )

    absolute_gain = float(fixed_overall["accuracy"]) - float(erm_overall["accuracy"])
    erm_accuracy = float(erm_overall["accuracy"])
    relative_gain = absolute_gain / erm_accuracy if erm_accuracy else math.inf

    return {
        "gate": gate.name,
        "fixed_threshold": fixed_threshold,
        "erm_threshold": erm_threshold,
        "fixed_gate": fixed_overall,
        "erm_baseline": erm_overall,
        "erm_training_metrics": erm_train_metrics,
        "absolute_gain_vs_erm": round(absolute_gain, 4),
        "relative_gain_vs_erm": "inf" if math.isinf(relative_gain) else round(relative_gain, 4),
        "slices": {
            "fixed_gate": fixed_slices,
            "erm_baseline": erm_slices,
            "accuracy_delta_vs_erm": accuracy_delta(fixed_slices, erm_slices),
        },
        "leave_one_domain_out": leave_one_domain_out,
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def format_metrics(metrics: dict[str, float | int]) -> str:
    return (
        f"n={metrics['n']}, accuracy={metrics['accuracy']}, precision={metrics['precision']}, "
        f"recall={metrics['recall']}, f1={metrics['f1']}"
    )


def write_markdown(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GateTectonic Report",
        "",
        f"- Gate: `{payload['gate']}`",
        f"- Fixed threshold: `{payload['fixed_threshold']}`",
        f"- ERM threshold: `{payload['erm_threshold']}`",
        f"- Absolute gain vs ERM: `{payload['absolute_gain_vs_erm']}`",
        f"- Relative gain vs ERM: `{payload['relative_gain_vs_erm']}`",
        "",
        "## Overall Metrics",
        "",
        f"- Fixed gate: {format_metrics(payload['fixed_gate'])}",
        f"- ERM baseline: {format_metrics(payload['erm_baseline'])}",
        "",
        "## Leave-One-Domain-Out",
        "",
    ]

    for item in payload["leave_one_domain_out"]:
        lines.extend(
            [
                f"### Held Out: {item['held_out_domain']}",
                "",
                f"- Train domains: {', '.join(item['train_domains'])}",
                f"- ERM threshold: `{item['erm_threshold']}`",
                f"- Fixed gate: {format_metrics(item['fixed_gate'])}",
                f"- ERM baseline: {format_metrics(item['erm_baseline'])}",
                f"- Absolute gain vs ERM: `{item['absolute_gain_vs_erm']}`",
                f"- Relative gain vs ERM: `{item['relative_gain_vs_erm']}`",
                "",
            ]
        )

    lines.extend(["## Stress Slices", ""])
    fixed_slices = payload["slices"]["fixed_gate"]
    baseline_slices = payload["slices"]["erm_baseline"]
    deltas = payload["slices"]["accuracy_delta_vs_erm"]
    for field, values in fixed_slices.items():
        lines.extend([f"### {field}", "", "| Slice | Fixed Accuracy | ERM Accuracy | Delta | n |", "| --- | ---: | ---: | ---: | ---: |"])
        for value, metrics in values.items():
            baseline_metrics = baseline_slices.get(field, {}).get(value, {})
            delta = deltas.get(field, {}).get(value, 0.0)
            lines.append(
                f"| {value} | {metrics['accuracy']} | {baseline_metrics.get('accuracy', 0.0)} | {delta} | {metrics['n']} |"
            )
        lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stress test a RAG relevance gate across domains and failure-mode slices.",
    )
    parser.add_argument("--input", type=Path, help="CSV with question, document, label, and metadata columns.")
    parser.add_argument("--out-json", type=Path, default=Path("reports/gatetectonic_report.json"))
    parser.add_argument("--out-md", type=Path, default=Path("reports/gatetectonic_report.md"))
    parser.add_argument("--threshold", type=float, default=0.35, help="Fixed gate threshold from 0.0 to 1.0.")
    parser.add_argument("--no-stress", action="store_true", help="Disable generated stress variants.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not 0.0 <= args.threshold <= 1.0:
        raise SystemExit("--threshold must be between 0.0 and 1.0")

    api_key_present = bool(os.getenv("GATETECTONIC_API_KEY") or os.getenv("OPENAI_API_KEY"))
    clean_examples, data_source = load_examples(args.input)
    examples = make_stress_examples(clean_examples, include_stress=not args.no_stress)
    gate = LexicalOverlapGate()
    report = evaluate(gate, examples, fixed_threshold=args.threshold)
    report["metadata"] = {
        "data_source": data_source,
        "clean_examples": len(clean_examples),
        "evaluated_examples": len(examples),
        "stress_enabled": not args.no_stress,
        "api_key_present": api_key_present,
        "api_key_used": False,
        "note": "Reference run uses a local lexical scorer; API keys are optional and are not sent anywhere.",
    }

    write_json(args.out_json, report)
    write_markdown(args.out_md, report)

    print("GateTectonic report written")
    print(f"- JSON: {args.out_json}")
    print(f"- Markdown: {args.out_md}")
    print(f"- Data source: {data_source}")
    print(f"- Evaluated examples: {len(examples)}")
    print(f"- Fixed accuracy: {report['fixed_gate']['accuracy']}")
    print(f"- ERM accuracy: {report['erm_baseline']['accuracy']}")


if __name__ == "__main__":
    main()
