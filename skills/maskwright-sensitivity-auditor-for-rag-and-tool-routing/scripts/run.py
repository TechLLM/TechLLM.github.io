#!/usr/bin/env python3
"""Maskwright sensitivity audit runner.

This module provides a small, deterministic reference implementation for
candidate leave-one-out and span-masking analysis. It can use a user-provided
scorer command, but defaults to a built-in lexical scorer so it runs without
API keys or network access.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


MASK_TOKEN = "[MASK]"


SAMPLE_DATA: Dict[str, Any] = {
    "query": "reset user password admin console",
    "correct_id": "tool-password-reset",
    "candidates": [
        {
            "id": "tool-user-search",
            "text": "Find users in the admin console by email, name, or account status.",
        },
        {
            "id": "tool-billing-reset",
            "text": "Reset billing cycle settings, invoices, and plan access.",
        },
        {
            "id": "tool-password-reset",
            "text": "Reset a user's password from the admin console and send a temporary login link.",
        },
    ],
}


def tokenize(text: str) -> List[str]:
    """Return lowercase alphanumeric tokens from text."""

    return re.findall(r"[a-z0-9]+", text.lower())


def stable_round(value: Optional[float], digits: int = 6) -> Optional[float]:
    """Round floats consistently while preserving null values."""

    if value is None:
        return None
    return round(float(value), digits)


def lexical_score(query: str, text: str, position: int, total: int) -> float:
    """Score a candidate with deterministic lexical overlap and a small position prior."""

    query_tokens = tokenize(query)
    text_tokens = tokenize(text)
    if not query_tokens or not text_tokens:
        return 0.0

    query_set = set(query_tokens)
    text_set = set(text_tokens)
    shared = query_set & text_set
    coverage = len(shared) / len(query_set)
    density = len(shared) / max(len(text_set), 1)
    phrase_bonus = 0.0
    normalized_text = " ".join(text_tokens)
    for i in range(len(query_tokens) - 1):
        phrase = f"{query_tokens[i]} {query_tokens[i + 1]}"
        if phrase in normalized_text:
            phrase_bonus += 0.035
    position_prior = 0.03 * ((total - position) / max(total, 1))
    return (0.72 * coverage) + (0.23 * density) + phrase_bonus + position_prior


def default_score(query: str, candidates: Sequence[Dict[str, Any]]) -> Dict[str, float]:
    """Score candidates with the built-in lexical scorer."""

    total = len(candidates)
    scores: Dict[str, float] = {}
    for index, candidate in enumerate(candidates):
        candidate_id = str(candidate["id"])
        position = int(candidate.get("position", index))
        scores[candidate_id] = lexical_score(query, str(candidate.get("text", "")), position, total)
    return scores


def parse_external_scores(output: str) -> Dict[str, float]:
    """Parse scorer JSON output into an id-to-score mapping."""

    try:
        payload = json.loads(output)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Scorer returned invalid JSON: {exc}") from exc

    if isinstance(payload, dict) and isinstance(payload.get("scores"), list):
        scores: Dict[str, float] = {}
        for item in payload["scores"]:
            if not isinstance(item, dict) or "id" not in item or "score" not in item:
                raise ValueError("Scorer scores must be objects with 'id' and 'score'.")
            scores[str(item["id"])] = float(item["score"])
        return scores

    if isinstance(payload, dict):
        try:
            return {str(key): float(value) for key, value in payload.items()}
        except (TypeError, ValueError) as exc:
            raise ValueError("Scorer score mapping values must be numeric.") from exc

    raise ValueError("Scorer output must be a JSON object or {'scores': [...]} object.")


def run_external_scorer(
    command: str,
    query: str,
    candidates: Sequence[Dict[str, Any]],
    timeout_seconds: float,
) -> Dict[str, float]:
    """Run an external scorer command using the Maskwright stdin/stdout contract."""

    args = shlex.split(command)
    if not args:
        raise ValueError("External scorer command is empty.")

    payload = {
        "query": query,
        "candidates": [
            {
                "id": str(candidate["id"]),
                "text": str(candidate.get("text", "")),
                "position": int(candidate.get("position", index)),
            }
            for index, candidate in enumerate(candidates)
        ],
    }
    try:
        completed = subprocess.run(
            args,
            input=json.dumps(payload, sort_keys=True),
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"Scorer command not found: {args[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Scorer command timed out after {timeout_seconds} seconds.") from exc

    if completed.returncode != 0:
        stderr = completed.stderr.strip() or "no stderr"
        raise RuntimeError(f"Scorer command failed with exit code {completed.returncode}: {stderr}")

    scores = parse_external_scores(completed.stdout)
    expected_ids = {str(candidate["id"]) for candidate in candidates}
    missing = sorted(expected_ids - set(scores))
    if missing:
        raise ValueError(f"Scorer output missing scores for candidate ids: {', '.join(missing)}")
    return {candidate_id: scores[candidate_id] for candidate_id in expected_ids}


def score_candidates(
    query: str,
    candidates: Sequence[Dict[str, Any]],
    scorer_command: Optional[str] = None,
    timeout_seconds: float = 10.0,
) -> Dict[str, float]:
    """Score candidates with an external command or the built-in scorer."""

    if scorer_command:
        return run_external_scorer(scorer_command, query, candidates, timeout_seconds)
    return default_score(query, candidates)


def entropy(scores: Iterable[float]) -> float:
    """Compute softmax entropy for a list of scores."""

    values = list(scores)
    if not values:
        return 0.0
    max_value = max(values)
    weights = [math.exp(value - max_value) for value in values]
    total = sum(weights)
    if total == 0:
        return 0.0
    probabilities = [weight / total for weight in weights]
    return -sum(prob * math.log(prob) for prob in probabilities if prob > 0)


def ranked(scores: Dict[str, float], ordered_ids: Sequence[str]) -> List[Dict[str, Any]]:
    """Return deterministic ranking records sorted by score descending and input order."""

    order_index = {candidate_id: index for index, candidate_id in enumerate(ordered_ids)}
    sorted_ids = sorted(scores, key=lambda candidate_id: (-scores[candidate_id], order_index[candidate_id]))
    return [
        {
            "id": candidate_id,
            "rank": index + 1,
            "score": scores[candidate_id],
        }
        for index, candidate_id in enumerate(sorted_ids)
    ]


def rank_of(scores: Dict[str, float], ordered_ids: Sequence[str], candidate_id: str) -> Optional[int]:
    """Return the one-based rank for a candidate id, or None if absent."""

    for row in ranked(scores, ordered_ids):
        if row["id"] == candidate_id:
            return int(row["rank"])
    return None


def top_id(scores: Dict[str, float], ordered_ids: Sequence[str]) -> Optional[str]:
    """Return the highest-scoring candidate id, or None when no candidates exist."""

    rows = ranked(scores, ordered_ids)
    return str(rows[0]["id"]) if rows else None


def margin(scores: Dict[str, float], correct_id: str) -> Optional[float]:
    """Return correct-score minus the best competing score."""

    if correct_id not in scores:
        return None
    competitor_scores = [score for candidate_id, score in scores.items() if candidate_id != correct_id]
    if not competitor_scores:
        return None
    return scores[correct_id] - max(competitor_scores)


def validate_input(data: Dict[str, Any]) -> Tuple[str, str, List[Dict[str, Any]]]:
    """Validate and normalize the Maskwright input payload."""

    if not isinstance(data, dict):
        raise ValueError("Input must be a JSON object.")
    query = data.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Input field 'query' must be a non-empty string.")
    correct_id = data.get("correct_id")
    if not isinstance(correct_id, str) or not correct_id.strip():
        raise ValueError("Input field 'correct_id' must be a non-empty string.")
    raw_candidates = data.get("candidates")
    if not isinstance(raw_candidates, list) or not raw_candidates:
        raise ValueError("Input field 'candidates' must be a non-empty list.")

    seen = set()
    candidates: List[Dict[str, Any]] = []
    for index, raw_candidate in enumerate(raw_candidates):
        if not isinstance(raw_candidate, dict):
            raise ValueError(f"Candidate at index {index} must be an object.")
        candidate_id = raw_candidate.get("id")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            raise ValueError(f"Candidate at index {index} must have a non-empty string id.")
        if candidate_id in seen:
            raise ValueError(f"Duplicate candidate id: {candidate_id}")
        seen.add(candidate_id)
        text = raw_candidate.get("text")
        if not isinstance(text, str):
            raise ValueError(f"Candidate '{candidate_id}' must have a string text field.")
        candidate = dict(raw_candidate)
        candidate["id"] = candidate_id
        candidate["text"] = text
        candidate["position"] = int(candidate.get("position", index))
        candidates.append(candidate)

    if correct_id not in seen:
        raise ValueError("Input field 'correct_id' must match one candidate id.")
    return query, correct_id, candidates


def make_spans(tokens: Sequence[str], span_size: int) -> List[Tuple[int, int, str]]:
    """Create non-overlapping token spans for masking."""

    if span_size < 1:
        raise ValueError("span_size must be at least 1.")
    spans = []
    for start in range(0, len(tokens), span_size):
        end = min(start + span_size, len(tokens))
        spans.append((start, end, " ".join(tokens[start:end])))
    return spans


def mask_span(text: str, span_start: int, span_end: int) -> str:
    """Replace a token span with the mask token."""

    tokens = tokenize(text)
    masked_tokens = tokens[:span_start] + [MASK_TOKEN] + tokens[span_end:]
    return " ".join(masked_tokens)


def classify_summary(
    candidates: Sequence[Dict[str, Any]],
    correct_id: str,
    base_scores: Dict[str, float],
    ordered_ids: Sequence[str],
    span_rows: Sequence[Dict[str, Any]],
) -> List[str]:
    """Assign high-level failure labels from ranking and sensitivity signals."""

    labels: List[str] = []
    correct_rank = rank_of(base_scores, ordered_ids, correct_id)
    correct_score = base_scores.get(correct_id, 0.0)
    current_margin = margin(base_scores, correct_id)
    current_top_id = top_id(base_scores, ordered_ids)

    if correct_score < 0.08 and correct_rank != 1:
        labels.append("knowledge-missing")

    if current_margin is not None and current_margin < 0.12 and correct_rank != 1:
        labels.append("ambiguity-bias")

    if current_top_id and current_top_id != correct_id:
        correct_position = next(int(c["position"]) for c in candidates if c["id"] == correct_id)
        top_position = next(int(c["position"]) for c in candidates if c["id"] == current_top_id)
        score_gap = base_scores[current_top_id] - base_scores[correct_id]
        if top_position < correct_position and score_gap < 0.18:
            labels.append("position-bias")

    max_span_delta = max((abs(float(row["candidate_score_delta"])) for row in span_rows), default=0.0)
    if max_span_delta >= 0.18:
        labels.append("keyword-overreliance")

    if not labels:
        labels.append("no-strong-failure-signal")
    return labels


def candidate_failure_signal(
    removed_candidate: Dict[str, Any],
    correct_id: str,
    base_correct_rank: Optional[int],
    masked_correct_rank: Optional[int],
    base_top: Optional[str],
) -> str:
    """Classify one leave-one-out candidate masking row."""

    removed_id = str(removed_candidate["id"])
    if removed_id == correct_id:
        return "knowledge-missing-check"
    if base_top == removed_id and masked_correct_rank == 1:
        if int(removed_candidate.get("position", 0)) == 0:
            return "position-bias"
        return "ambiguity-bias"
    if (
        base_correct_rank is not None
        and masked_correct_rank is not None
        and masked_correct_rank < base_correct_rank
    ):
        return "ambiguity-bias"
    return "low-impact"


def span_failure_signal(
    candidate: Dict[str, Any],
    correct_id: str,
    candidate_score_delta: float,
    correct_rank_delta: Optional[int],
) -> str:
    """Classify one span-masking row."""

    if abs(candidate_score_delta) >= 0.18:
        return "keyword-overreliance"
    if candidate["id"] != correct_id and correct_rank_delta is not None and correct_rank_delta < 0:
        return "ambiguity-bias"
    if candidate["id"] != correct_id and int(candidate.get("position", 0)) == 0 and candidate_score_delta < -0.08:
        return "position-bias"
    return "low-impact"


def analyze(
    data: Dict[str, Any],
    scorer_command: Optional[str] = None,
    span_size: int = 4,
    timeout_seconds: float = 10.0,
) -> Dict[str, Any]:
    """Run candidate and span sensitivity analysis and return structured results."""

    query, correct_id, candidates = validate_input(data)
    ordered_ids = [str(candidate["id"]) for candidate in candidates]
    base_scores = score_candidates(query, candidates, scorer_command, timeout_seconds)
    base_entropy = entropy(base_scores.values())
    base_correct_rank = rank_of(base_scores, ordered_ids, correct_id)
    base_top = top_id(base_scores, ordered_ids)
    base_margin = margin(base_scores, correct_id)

    candidate_rows: List[Dict[str, Any]] = []
    for removed in candidates:
        masked_candidates = [candidate for candidate in candidates if candidate["id"] != removed["id"]]
        masked_ordered_ids = [str(candidate["id"]) for candidate in masked_candidates]
        masked_scores = score_candidates(query, masked_candidates, scorer_command, timeout_seconds)
        masked_entropy = entropy(masked_scores.values())
        masked_correct_rank = rank_of(masked_scores, masked_ordered_ids, correct_id)
        masked_margin = margin(masked_scores, correct_id)
        correct_score_delta = None
        if correct_id in masked_scores:
            correct_score_delta = masked_scores[correct_id] - base_scores[correct_id]
        correct_rank_delta = None
        if base_correct_rank is not None and masked_correct_rank is not None:
            correct_rank_delta = masked_correct_rank - base_correct_rank

        row = {
            "removed_candidate_id": str(removed["id"]),
            "removed_was_correct": str(removed["id"]) == correct_id,
            "base_top_id": base_top,
            "masked_top_id": top_id(masked_scores, masked_ordered_ids),
            "base_correct_rank": base_correct_rank,
            "masked_correct_rank": masked_correct_rank,
            "correct_rank_delta": correct_rank_delta,
            "correct_score_delta": stable_round(correct_score_delta),
            "base_margin": stable_round(base_margin),
            "masked_margin": stable_round(masked_margin),
            "margin_change": stable_round(None if base_margin is None or masked_margin is None else masked_margin - base_margin),
            "base_entropy": stable_round(base_entropy),
            "masked_entropy": stable_round(masked_entropy),
            "entropy_change": stable_round(masked_entropy - base_entropy),
        }
        row["failure_signal"] = candidate_failure_signal(
            removed,
            correct_id,
            base_correct_rank,
            masked_correct_rank,
            base_top,
        )
        candidate_rows.append(row)

    span_rows: List[Dict[str, Any]] = []
    for candidate in candidates:
        tokens = tokenize(str(candidate["text"]))
        for span_start, span_end, span_text in make_spans(tokens, span_size):
            masked_candidates = []
            for other in candidates:
                if other["id"] == candidate["id"]:
                    replacement = dict(other)
                    replacement["text"] = mask_span(str(other["text"]), span_start, span_end)
                    masked_candidates.append(replacement)
                else:
                    masked_candidates.append(other)

            masked_scores = score_candidates(query, masked_candidates, scorer_command, timeout_seconds)
            masked_entropy = entropy(masked_scores.values())
            masked_correct_rank = rank_of(masked_scores, ordered_ids, correct_id)
            masked_margin = margin(masked_scores, correct_id)
            candidate_score_delta = masked_scores[str(candidate["id"])] - base_scores[str(candidate["id"])]
            correct_rank_delta = None
            if base_correct_rank is not None and masked_correct_rank is not None:
                correct_rank_delta = masked_correct_rank - base_correct_rank
            row = {
                "candidate_id": str(candidate["id"]),
                "span_start": span_start,
                "span_end": span_end,
                "span_text": span_text,
                "base_candidate_score": stable_round(base_scores[str(candidate["id"])]),
                "masked_candidate_score": stable_round(masked_scores[str(candidate["id"])]),
                "candidate_score_delta": stable_round(candidate_score_delta),
                "base_correct_rank": base_correct_rank,
                "masked_correct_rank": masked_correct_rank,
                "correct_rank_delta": correct_rank_delta,
                "margin_change": stable_round(None if base_margin is None or masked_margin is None else masked_margin - base_margin),
                "entropy_change": stable_round(masked_entropy - base_entropy),
            }
            row["failure_signal"] = span_failure_signal(
                candidate,
                correct_id,
                candidate_score_delta,
                correct_rank_delta,
            )
            span_rows.append(row)

    labels = classify_summary(candidates, correct_id, base_scores, ordered_ids, span_rows)
    most_sensitive_candidate = max(
        candidate_rows,
        key=lambda row: abs(float(row["margin_change"] or 0.0)) + abs(float(row["entropy_change"] or 0.0)),
    )
    most_sensitive_span = max(
        span_rows,
        key=lambda row: abs(float(row["candidate_score_delta"] or 0.0)),
    )

    summary = {
        "query": query,
        "correct_id": correct_id,
        "base_top_id": base_top,
        "base_correct_rank": base_correct_rank,
        "base_margin": stable_round(base_margin),
        "base_entropy": stable_round(base_entropy),
        "failure_labels": labels,
        "most_sensitive_candidate": {
            "removed_candidate_id": most_sensitive_candidate["removed_candidate_id"],
            "failure_signal": most_sensitive_candidate["failure_signal"],
            "margin_change": most_sensitive_candidate["margin_change"],
            "entropy_change": most_sensitive_candidate["entropy_change"],
        },
        "most_sensitive_span": {
            "candidate_id": most_sensitive_span["candidate_id"],
            "span_start": most_sensitive_span["span_start"],
            "span_end": most_sensitive_span["span_end"],
            "span_text": most_sensitive_span["span_text"],
            "candidate_score_delta": most_sensitive_span["candidate_score_delta"],
            "failure_signal": most_sensitive_span["failure_signal"],
        },
        "artifacts": {},
    }

    return {
        "summary": summary,
        "candidate_sensitivity": candidate_rows,
        "span_sensitivity": span_rows,
    }


def write_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    """Write dictionaries to CSV with a deterministic field order."""

    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_artifacts(output_dir: Path, result: Dict[str, Any]) -> Dict[str, str]:
    """Write summary JSON and heatmap-ready CSV artifacts."""

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    candidate_path = output_dir / "candidate_sensitivity.csv"
    span_path = output_dir / "span_sensitivity.csv"
    summary_path.write_text(json.dumps(result["summary"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(candidate_path, result["candidate_sensitivity"])
    write_csv(span_path, result["span_sensitivity"])
    return {
        "summary_json": str(summary_path),
        "candidate_csv": str(candidate_path),
        "span_csv": str(span_path),
    }


def load_input(path: Optional[str]) -> Dict[str, Any]:
    """Load input JSON from a file or return built-in sample data."""

    if path is None:
        return SAMPLE_DATA
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Input file is not valid JSON: {exc}") from exc


def env_float(name: str, default: float) -> float:
    """Read an optional float from the environment."""

    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be a number.") from exc


def env_int(name: str, default: int) -> int:
    """Read an optional integer from the environment."""

    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer.") from exc


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description="Audit ranking sensitivity for RAG candidates and tool-routing options.",
    )
    parser.add_argument("--input", help="Path to a Maskwright JSON input file. Defaults to built-in sample data.")
    parser.add_argument("--output-dir", help="Directory for summary JSON and CSV artifacts.")
    parser.add_argument(
        "--scorer-command",
        default=os.getenv("MASKWRIGHT_SCORER_COMMAND"),
        help="External scorer command. Also read from MASKWRIGHT_SCORER_COMMAND.",
    )
    parser.add_argument(
        "--span-size",
        type=int,
        default=env_int("MASKWRIGHT_SPAN_SIZE", 4),
        help="Token count per masked span. Also read from MASKWRIGHT_SPAN_SIZE.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=env_float("MASKWRIGHT_SCORE_TIMEOUT", 10.0),
        help="External scorer timeout in seconds. Also read from MASKWRIGHT_SCORE_TIMEOUT.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Console output format for the summary.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run against built-in sample data without external services.",
    )
    return parser


def print_text_summary(summary: Dict[str, Any]) -> None:
    """Print a compact human-readable summary."""

    print(f"query: {summary['query']}")
    print(f"correct_id: {summary['correct_id']}")
    print(f"base_top_id: {summary['base_top_id']}")
    print(f"base_correct_rank: {summary['base_correct_rank']}")
    print(f"failure_labels: {', '.join(summary['failure_labels'])}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entrypoint."""

    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        data = SAMPLE_DATA if args.selftest and args.input is None else load_input(args.input)
        result = analyze(
            data,
            scorer_command=args.scorer_command,
            span_size=args.span_size,
            timeout_seconds=args.timeout,
        )
        if args.output_dir:
            artifacts = write_artifacts(Path(args.output_dir), result)
            result["summary"]["artifacts"] = artifacts
            summary_path = Path(args.output_dir) / "summary.json"
            summary_path.write_text(
                json.dumps(result["summary"], indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        if args.format == "json":
            print(json.dumps(result["summary"], indent=2, sort_keys=True))
        else:
            print_text_summary(result["summary"])
        return 0
    except Exception as exc:
        print(f"maskwright error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
