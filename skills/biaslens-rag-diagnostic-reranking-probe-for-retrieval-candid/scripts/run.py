#!/usr/bin/env python3
"""BiasLens RAG diagnostic CLI.

This module implements a deterministic, dependency-free probe for retrieved RAG
candidates. It scores query-document overlap, applies simple perturbations, and
emits a JSON report that highlights possible keyword, precision, ambiguity, and
position-bias risks.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import statistics
import sys
from pathlib import Path
from typing import Any, Iterable


VERSION = "0.1.0"

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
    "how",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "this",
    "to",
    "what",
    "when",
    "where",
    "who",
    "why",
    "with",
}

SAMPLE_QUERY = "How do I reset contractor MFA device approvals?"

SAMPLE_CANDIDATES = [
    {
        "id": "kb-001",
        "text": (
            "Contractor MFA device reset procedure: open Admin Identity, find the "
            "contractor account, revoke old device approvals, then send a new "
            "enrollment link."
        ),
    },
    {
        "id": "kb-002",
        "text": (
            "Employee password reset guide: verify the user, reset the temporary "
            "password, and remind them to update recovery details."
        ),
    },
    {
        "id": "kb-003",
        "text": (
            "MFA enrollment policy overview for contractors: approvals expire after "
            "thirty days and devices must be registered through the identity portal."
        ),
    },
    {
        "id": "kb-004",
        "text": (
            "Facilities badge access changes are handled by office operations and "
            "do not change identity provider device settings."
        ),
    },
]


class BiasLensError(ValueError):
    """Raised when input data or configuration is invalid."""


def tokenize(text: str) -> list[str]:
    """Return lowercase alphanumeric tokens from text."""

    return re.findall(r"[a-z0-9]+", text.lower())


def query_terms(query: str) -> list[str]:
    """Return unique content-bearing query terms in original order."""

    terms: list[str] = []
    seen: set[str] = set()
    for token in tokenize(query):
        if token in STOPWORDS or len(token) <= 1:
            continue
        if token not in seen:
            terms.append(token)
            seen.add(token)
    return terms


def rounded(value: float) -> float:
    """Round a float for stable JSON output."""

    return round(float(value), 4)


def lexical_score(query: str, text: str) -> dict[str, Any]:
    """Score one candidate using transparent lexical evidence.

    The score combines query-term coverage, matched-term density, and adjacent
    query-term phrase matches. It returns both the numeric score and evidence
    fields used later by the diagnostics.
    """

    terms = query_terms(query)
    if not terms:
        raise BiasLensError("Query must contain at least one non-stopword token.")

    doc_tokens = tokenize(text)
    doc_set = set(doc_tokens)
    matched = [term for term in terms if term in doc_set]
    missing = [term for term in terms if term not in doc_set]
    match_count = sum(1 for token in doc_tokens if token in set(terms))

    coverage = len(matched) / len(terms)
    density = min(1.0, (match_count / max(1, len(doc_tokens))) * 4.0)

    doc_bigrams = set(zip(doc_tokens, doc_tokens[1:]))
    query_bigrams = list(zip(terms, terms[1:]))
    if query_bigrams:
        phrase_hits = sum(1 for pair in query_bigrams if pair in doc_bigrams)
        phrase_score = phrase_hits / len(query_bigrams)
    else:
        phrase_score = 0.0

    score = (coverage * 0.72) + (density * 0.20) + (phrase_score * 0.08)
    return {
        "score": rounded(min(1.0, score)),
        "coverage": rounded(coverage),
        "matched_terms": matched,
        "missing_terms": missing,
    }


def mask_query_terms(text: str, terms: Iterable[str]) -> str:
    """Replace exact query-term tokens in text with a neutral mask token."""

    term_set = set(terms)
    parts: list[str] = []
    last_end = 0
    for match in re.finditer(r"[A-Za-z0-9]+", text):
        parts.append(text[last_end : match.start()])
        token = match.group(0)
        if token.lower() in term_set:
            parts.append("[MASK]")
        else:
            parts.append(token)
        last_end = match.end()
    parts.append(text[last_end:])
    return "".join(parts)


def token_windows(tokens: list[str], count: int = 3) -> list[str]:
    """Return deterministic partial-document windows from tokenized text."""

    if not tokens:
        return [""]
    window_size = max(4, math.ceil(len(tokens) * 0.55))
    if len(tokens) <= window_size:
        return [" ".join(tokens)]

    starts = [0, max(0, (len(tokens) - window_size) // 2), len(tokens) - window_size]
    windows: list[str] = []
    for start in starts[:count]:
        window = " ".join(tokens[start : start + window_size])
        if window not in windows:
            windows.append(window)
    return windows


def hide_best_chunk(query: str, text: str) -> str:
    """Remove the sentence-like chunk with the most query-term matches."""

    chunks = [chunk.strip() for chunk in re.split(r"(?<=[.!?;:])\s+", text) if chunk.strip()]
    if len(chunks) <= 1:
        tokens = tokenize(text)
        if len(tokens) <= 4:
            return ""
        midpoint = len(tokens) // 2
        return " ".join(tokens[:midpoint])

    terms = set(query_terms(query))

    def chunk_hits(chunk: str) -> int:
        return sum(1 for token in tokenize(chunk) if token in terms)

    best_index = max(range(len(chunks)), key=lambda index: (chunk_hits(chunks[index]), -index))
    kept = [chunk for index, chunk in enumerate(chunks) if index != best_index]
    return " ".join(kept)


def mean(values: list[float]) -> float:
    """Return arithmetic mean, or 0.0 for an empty list."""

    if not values:
        return 0.0
    return sum(values) / len(values)


def stddev(values: list[float]) -> float:
    """Return population standard deviation, or 0.0 for fewer than two values."""

    if len(values) < 2:
        return 0.0
    return statistics.pstdev(values)


def position_prior(position: int, total: int, strength: float) -> float:
    """Return a small deterministic prior favoring earlier candidates."""

    if total <= 1:
        return strength
    normalized = 1.0 - ((position - 1) / (total - 1))
    return normalized * strength


def diagnose_candidate(
    query: str,
    candidate: dict[str, Any],
    total_candidates: int,
    position: int,
    top_score: float,
    trials_per_candidate: int,
    position_prior_strength: float,
) -> dict[str, Any]:
    """Run perturbation diagnostics for one candidate."""

    text = str(candidate.get("text", ""))
    candidate_id = str(candidate.get("id", f"candidate-{position}"))
    terms = query_terms(query)

    baseline = lexical_score(query, text)
    baseline_score = baseline["score"]

    masked = lexical_score(query, mask_query_terms(text, terms))["score"]
    window_scores = [lexical_score(query, window)["score"] for window in token_windows(tokenize(text))]
    hidden = lexical_score(query, hide_best_chunk(query, text))["score"]

    base_perturbations = [masked, hidden, *window_scores]
    if trials_per_candidate <= len(base_perturbations):
        perturbed_scores = base_perturbations[:trials_per_candidate]
    else:
        perturbed_scores = [
            base_perturbations[index % len(base_perturbations)]
            for index in range(trials_per_candidate)
        ]
    mean_perturbed = mean(perturbed_scores)
    partial_volatility = stddev(window_scores)

    reversed_position = total_candidates - position + 1
    normal_with_prior = baseline_score + position_prior(position, total_candidates, position_prior_strength)
    reversed_with_prior = baseline_score + position_prior(
        reversed_position, total_candidates, position_prior_strength
    )
    position_sensitivity = abs(normal_with_prior - reversed_with_prior)

    keyword_reliance = max(0.0, baseline_score - masked)
    score_drop = max(0.0, baseline_score - mean_perturbed)
    near_top = (top_score - baseline_score) <= 0.08

    notes: list[str] = []
    if baseline["coverage"] < 0.35:
        notes.append("Low query-term coverage after retrieval.")
    if keyword_reliance >= 0.30:
        notes.append("Score drops sharply when surface query terms are masked.")
    if partial_volatility >= 0.08:
        notes.append("Partial-document samples produce unstable relevance scores.")
    if position_sensitivity >= 0.04:
        notes.append("Candidate ordering can materially change the prior-adjusted score.")
    if not notes:
        notes.append("Perturbations did not expose a strong instability signal.")

    if baseline_score < 0.25 and baseline["coverage"] < 0.35:
        label = "knowledge-gap"
    elif baseline_score >= 0.40 and (keyword_reliance >= 0.30 or score_drop >= 0.18):
        label = "precision-bias"
    elif near_top and partial_volatility >= 0.08:
        label = "ambiguity-bias"
    else:
        label = "stable-evidence"

    return {
        "id": candidate_id,
        "original_position": position,
        "baseline_score": rounded(baseline_score),
        "mean_perturbed_score": rounded(mean_perturbed),
        "score_stddev": rounded(stddev(perturbed_scores)),
        "score_drop": rounded(score_drop),
        "keyword_reliance": rounded(keyword_reliance),
        "partial_evidence_volatility": rounded(partial_volatility),
        "position_sensitivity": rounded(position_sensitivity),
        "coverage": baseline["coverage"],
        "matched_terms": baseline["matched_terms"],
        "missing_terms": baseline["missing_terms"],
        "diagnostic_label": label,
        "notes": notes,
    }


def normalize_candidates(raw_candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate and normalize raw candidate objects."""

    if not raw_candidates:
        raise BiasLensError("No candidates were provided.")

    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(raw_candidates, start=1):
        if not isinstance(item, dict):
            raise BiasLensError(f"Candidate line {index} must be a JSON object.")
        if "text" not in item:
            raise BiasLensError(f"Candidate line {index} is missing required field 'text'.")
        text = str(item["text"]).strip()
        if not text:
            raise BiasLensError(f"Candidate line {index} has an empty 'text' field.")
        candidate_id = str(item.get("id", f"candidate-{index}"))
        normalized.append({"id": candidate_id, "text": text, "source": item})

    def position_key(item_with_index: tuple[int, dict[str, Any]]) -> tuple[int, int]:
        index, item = item_with_index
        source = item["source"]
        raw_position = source.get("rank", source.get("position", index))
        try:
            position = int(raw_position)
        except (TypeError, ValueError):
            position = index
        return (position, index)

    ordered = [item for _, item in sorted(enumerate(normalized, start=1), key=position_key)]
    for item in ordered:
        item.pop("source", None)
    return ordered


def diagnose(
    query: str,
    candidates: list[dict[str, Any]],
    trials_per_candidate: int = 5,
    position_prior_strength: float = 0.06,
) -> dict[str, Any]:
    """Diagnose retrieval candidates and return a JSON-serializable report."""

    if trials_per_candidate < 1:
        raise BiasLensError("trials_per_candidate must be a positive integer.")
    if position_prior_strength < 0:
        raise BiasLensError("position prior strength must be non-negative.")

    normalized = normalize_candidates(candidates)
    baseline_items: list[dict[str, Any]] = []
    for index, candidate in enumerate(normalized, start=1):
        score = lexical_score(query, candidate["text"])["score"]
        baseline_items.append({"id": candidate["id"], "rank": index, "score": score})

    baseline_ranking = sorted(baseline_items, key=lambda item: (-item["score"], item["rank"], item["id"]))
    top_score = baseline_ranking[0]["score"]

    diagnostics = [
        diagnose_candidate(
            query=query,
            candidate=candidate,
            total_candidates=len(normalized),
            position=index,
            top_score=top_score,
            trials_per_candidate=trials_per_candidate,
            position_prior_strength=position_prior_strength,
        )
        for index, candidate in enumerate(normalized, start=1)
    ]

    diagnostics_by_id = {item["id"]: item for item in diagnostics}
    ranked_diagnostics = [diagnostics_by_id[item["id"]] for item in baseline_ranking]

    knowledge_gap = top_score < 0.35
    ambiguity_bias = sum(1 for item in baseline_ranking if (top_score - item["score"]) <= 0.08) >= 2
    precision_bias = any(item["diagnostic_label"] == "precision-bias" for item in diagnostics)
    position_bias = any(item["position_sensitivity"] >= 0.04 for item in diagnostics)

    recommendations = build_recommendations(
        knowledge_gap=knowledge_gap,
        ambiguity_bias=ambiguity_bias,
        precision_bias=precision_bias,
        position_bias=position_bias,
        ranked_diagnostics=ranked_diagnostics,
    )

    return {
        "query": query,
        "candidate_count": len(normalized),
        "trials_per_candidate": trials_per_candidate,
        "baseline_ranking": [
            {"id": item["id"], "rank": rank, "score": rounded(item["score"])}
            for rank, item in enumerate(baseline_ranking, start=1)
        ],
        "diagnostics": ranked_diagnostics,
        "failure_modes": {
            "knowledge_gap": knowledge_gap,
            "ambiguity_bias": ambiguity_bias,
            "precision_bias": precision_bias,
            "position_bias": position_bias,
        },
        "recommendations": recommendations,
        "metadata": {
            "engine": "biaslens-rag-lexical-probe",
            "version": VERSION,
            "position_prior": rounded(position_prior_strength),
        },
    }


def build_recommendations(
    knowledge_gap: bool,
    ambiguity_bias: bool,
    precision_bias: bool,
    position_bias: bool,
    ranked_diagnostics: list[dict[str, Any]],
) -> list[str]:
    """Build compact shrink-search recommendations from failure-mode flags."""

    recommendations: list[str] = []
    if knowledge_gap:
        recommendations.append(
            "Expand indexing or query rewriting before reranking; the current pool has weak evidence."
        )
    if ambiguity_bias:
        recommendations.append(
            "Regroup near-top candidates by intent and rerank within smaller candidate clusters."
        )
    if precision_bias:
        top_precision_ids = [
            item["id"] for item in ranked_diagnostics if item["diagnostic_label"] == "precision-bias"
        ][:3]
        recommendations.append(
            "Require answer-bearing evidence beyond keyword overlap for candidates: "
            + ", ".join(top_precision_ids)
            + "."
        )
    if position_bias:
        recommendations.append(
            "Evaluate reranking with shuffled candidate order and reduce any fixed position prior."
        )
    if not recommendations:
        recommendations.append(
            "Current candidates look stable under the built-in perturbations; validate with task-specific labels."
        )
    return recommendations


def load_jsonl(path: Path, max_candidates: int | None = None) -> list[dict[str, Any]]:
    """Load candidates from a JSONL file with line-specific error messages."""

    candidates: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    item = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise BiasLensError(f"{path}: line {line_number} is not valid JSON: {exc.msg}") from exc
                candidates.append(item)
                if max_candidates is not None and len(candidates) >= max_candidates:
                    break
    except FileNotFoundError as exc:
        raise BiasLensError(f"Input file not found: {path}") from exc
    except OSError as exc:
        raise BiasLensError(f"Could not read input file {path}: {exc}") from exc
    return candidates


def positive_int(value: str, name: str) -> int:
    """Parse a positive integer for CLI and environment options."""

    try:
        parsed = int(value)
    except ValueError as exc:
        raise BiasLensError(f"{name} must be a positive integer, got {value!r}.") from exc
    if parsed <= 0:
        raise BiasLensError(f"{name} must be a positive integer, got {value!r}.")
    return parsed


def non_negative_float(value: str, name: str) -> float:
    """Parse a non-negative float for CLI and environment options."""

    try:
        parsed = float(value)
    except ValueError as exc:
        raise BiasLensError(f"{name} must be a non-negative number, got {value!r}.") from exc
    if parsed < 0:
        raise BiasLensError(f"{name} must be a non-negative number, got {value!r}.")
    return parsed


def env_options() -> dict[str, Any]:
    """Read optional non-secret configuration from environment variables."""

    options: dict[str, Any] = {"max_candidates": None, "position_prior": 0.06}
    if "BIASLENS_RAG_MAX_CANDIDATES" in os.environ:
        options["max_candidates"] = positive_int(
            os.environ["BIASLENS_RAG_MAX_CANDIDATES"], "BIASLENS_RAG_MAX_CANDIDATES"
        )
    if "BIASLENS_RAG_POSITION_PRIOR" in os.environ:
        options["position_prior"] = non_negative_float(
            os.environ["BIASLENS_RAG_POSITION_PRIOR"], "BIASLENS_RAG_POSITION_PRIOR"
        )
    return options


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description="Probe RAG retrieval candidates for reranking bias signals."
    )
    parser.add_argument("--query", help="Question or retrieval query to diagnose.")
    parser.add_argument("--input", type=Path, help="JSONL file containing candidate objects.")
    parser.add_argument("--output", type=Path, help="Optional path for JSON report output.")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON with indentation instead of compact JSON.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run the built-in sample without requiring input files or API keys.",
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=5,
        help="Number of perturbation scores to use per candidate; default: 5.",
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        help="Limit loaded candidates; overrides BIASLENS_RAG_MAX_CANDIDATES.",
    )
    parser.add_argument(
        "--position-prior",
        type=float,
        help="Order-prior strength; overrides BIASLENS_RAG_POSITION_PRIOR.",
    )
    return parser


def render_report(report: dict[str, Any], pretty: bool = False) -> str:
    """Serialize a diagnostic report as deterministic JSON text."""

    if pretty:
        return json.dumps(report, indent=2, sort_keys=True) + "\n"
    return json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n"


def write_or_print(text: str, output_path: Path | None) -> None:
    """Write output text to a file or stdout."""

    if output_path is None:
        sys.stdout.write(text)
        return
    try:
        output_path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise BiasLensError(f"Could not write output file {output_path}: {exc}") from exc


def run_from_args(args: argparse.Namespace) -> dict[str, Any]:
    """Create a diagnostic report from parsed CLI arguments."""

    options = env_options()
    max_candidates = args.max_candidates if args.max_candidates is not None else options["max_candidates"]
    position_prior_strength = (
        args.position_prior if args.position_prior is not None else options["position_prior"]
    )

    if args.max_candidates is not None and args.max_candidates <= 0:
        raise BiasLensError("--max-candidates must be a positive integer.")
    if args.position_prior is not None and args.position_prior < 0:
        raise BiasLensError("--position-prior must be non-negative.")
    if args.trials <= 0:
        raise BiasLensError("--trials must be a positive integer.")

    if args.selftest or (args.query is None and args.input is None):
        query = SAMPLE_QUERY
        candidates = SAMPLE_CANDIDATES
    else:
        if not args.query:
            raise BiasLensError("--query is required unless --selftest is used.")
        if not args.input:
            raise BiasLensError("--input is required unless --selftest is used.")
        query = args.query
        candidates = load_jsonl(args.input, max_candidates=max_candidates)

    if max_candidates is not None:
        candidates = candidates[:max_candidates]

    return diagnose(
        query=query,
        candidates=candidates,
        trials_per_candidate=args.trials,
        position_prior_strength=position_prior_strength,
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = run_from_args(args)
        write_or_print(render_report(report, pretty=args.pretty), args.output)
    except BiasLensError as exc:
        parser.exit(2, f"error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
