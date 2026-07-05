"""BiasLens RAG diagnostic CLI.

This module implements a small, deterministic reference diagnostic for RAG
candidate selection failures. It separates cases where known-good evidence is
absent from the candidate set from cases where that evidence is present but the
selected document appears unstable, position-biased, or keyword-attracted.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence, Set, Tuple


VERSION = "0.1.0"

DEFAULT_STOPWORDS = {
    "a",
    "an",
    "and",
    "after",
    "are",
    "as",
    "at",
    "be",
    "by",
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


class DiagnosticError(ValueError):
    """Raised when user-provided diagnostic input is invalid."""


def _env_stopwords() -> Set[str]:
    """Return stopwords from defaults plus optional BIASLENS_RAG_STOPWORDS."""

    extra = os.getenv("BIASLENS_RAG_STOPWORDS", "")
    tokens = {item.strip().lower() for item in extra.split(",") if item.strip()}
    return DEFAULT_STOPWORDS | tokens


def _env_keyword_limit(default: int = 5) -> int:
    """Return keyword limit from BIASLENS_RAG_KEYWORD_LIMIT with validation."""

    raw = os.getenv("BIASLENS_RAG_KEYWORD_LIMIT")
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise DiagnosticError("BIASLENS_RAG_KEYWORD_LIMIT must be an integer") from exc
    if value < 0:
        raise DiagnosticError("BIASLENS_RAG_KEYWORD_LIMIT must be non-negative")
    return value


def tokenize(text: str, stopwords: Optional[Set[str]] = None) -> List[str]:
    """Tokenize text into lowercase alphanumeric terms without stopwords."""

    stop = stopwords if stopwords is not None else _env_stopwords()
    return [
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2 and token not in stop and not token.isdigit()
    ]


def _as_list(value: Any, field_name: str) -> List[str]:
    """Normalize a string or list-like field into a list of strings."""

    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        result = []
        for item in value:
            if not isinstance(item, str):
                raise DiagnosticError(f"{field_name} must contain only strings")
            result.append(item)
        return result
    raise DiagnosticError(f"{field_name} must be a string or list of strings")


def _doc_id(doc: Mapping[str, Any]) -> str:
    """Extract a document ID from a candidate object."""

    value = doc.get("doc_id", doc.get("id"))
    if not isinstance(value, str) or not value:
        raise DiagnosticError("Each candidate must include a non-empty doc_id or id")
    return value


def _doc_text(doc: Mapping[str, Any]) -> str:
    """Extract document text from a candidate object."""

    value = doc.get("text", doc.get("content", ""))
    if not isinstance(value, str):
        raise DiagnosticError("Candidate text/content must be a string")
    return value


def _doc_score(doc: Mapping[str, Any]) -> float:
    """Extract an optional numeric candidate score."""

    value = doc.get("score", 0.0)
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    raise DiagnosticError("Candidate score must be numeric when provided")


def _lexical_score(question: str, doc: Mapping[str, Any], stopwords: Set[str]) -> float:
    """Score a document by overlap with question terms."""

    query_terms = set(tokenize(question, stopwords))
    if not query_terms:
        return 0.0
    doc_terms = set(tokenize(_doc_text(doc), stopwords))
    return len(query_terms & doc_terms) / len(query_terms)


def _model_score(question: str, doc: Mapping[str, Any], stopwords: Set[str]) -> float:
    """Return a deterministic proxy score used for masking diagnostics."""

    return _lexical_score(question, doc, stopwords) + (0.01 * _doc_score(doc))


def model_select(
    question: str,
    candidates: Sequence[Mapping[str, Any]],
    top_k: int = 1,
    stopwords: Optional[Set[str]] = None,
) -> List[str]:
    """Select top document IDs using a deterministic lexical-plus-score proxy."""

    if top_k < 1:
        raise DiagnosticError("top_k must be at least 1")
    stop = stopwords if stopwords is not None else _env_stopwords()
    ranked = sorted(
        enumerate(candidates),
        key=lambda item: (-_model_score(question, item[1], stop), item[0], _doc_id(item[1])),
    )
    return [_doc_id(doc) for _, doc in ranked[:top_k]]


def _position_bias_score(
    question: str,
    candidates: Sequence[Mapping[str, Any]],
    selected_ids: Sequence[str],
    stopwords: Set[str],
) -> float:
    """Estimate whether selected evidence benefits from early exposure."""

    if not candidates or not selected_ids:
        return 0.0
    first_selected = selected_ids[0]
    index_by_id = {_doc_id(doc): index for index, doc in enumerate(candidates)}
    if first_selected not in index_by_id:
        return 0.0
    selected_index = index_by_id[first_selected]
    selected_doc = candidates[selected_index]
    selected_lex = _lexical_score(question, selected_doc, stopwords)
    later_docs = candidates[selected_index + 1 :]
    if not later_docs:
        return 0.0
    max_later_lex = max(_lexical_score(question, doc, stopwords) for doc in later_docs)
    if len(candidates) == 1:
        exposure = 1.0
    else:
        exposure = 1.0 - (selected_index / (len(candidates) - 1))
    return round(max(0.0, max_later_lex - selected_lex) * exposure, 3)


def _masking_trials(
    question: str,
    candidates: Sequence[Mapping[str, Any]],
    selected_ids: Sequence[str],
    top_k: int,
    stopwords: Set[str],
) -> Tuple[int, float, List[str]]:
    """Run leave-one-out masking trials and summarize selection stability."""

    if len(candidates) <= 1 or not selected_ids:
        return 0, 1.0, []

    selected_set = set(selected_ids[:top_k])
    available_runs = 0
    stable_runs = 0
    alternatives: Set[str] = set()

    for masked_index in range(len(candidates)):
        subset = [doc for index, doc in enumerate(candidates) if index != masked_index]
        subset_ids = {_doc_id(doc) for doc in subset}
        chosen = model_select(question, subset, top_k=top_k, stopwords=stopwords)
        alternatives.update(doc_id for doc_id in chosen if doc_id not in selected_set)
        if selected_set.issubset(subset_ids):
            available_runs += 1
            if selected_set == set(chosen[:top_k]):
                stable_runs += 1

    stability = 1.0 if available_runs == 0 else stable_runs / available_runs
    return len(candidates), round(stability, 3), sorted(alternatives)


def _keyword_attraction(
    candidates: Sequence[Mapping[str, Any]],
    selected_ids: Sequence[str],
    keyword_limit: int,
    stopwords: Set[str],
) -> List[Dict[str, Any]]:
    """Find terms overrepresented in selected documents compared with others."""

    if keyword_limit <= 0 or not candidates or not selected_ids:
        return []

    selected_set = set(selected_ids)
    selected_docs = [doc for doc in candidates if _doc_id(doc) in selected_set]
    other_docs = [doc for doc in candidates if _doc_id(doc) not in selected_set]
    if not selected_docs:
        return []

    selected_counts: Counter[str] = Counter()
    other_counts: Counter[str] = Counter()
    for doc in selected_docs:
        selected_counts.update(set(tokenize(_doc_text(doc), stopwords)))
    for doc in other_docs:
        other_counts.update(set(tokenize(_doc_text(doc), stopwords)))

    results: List[Dict[str, Any]] = []
    for term in sorted(selected_counts):
        selected_rate = selected_counts[term] / len(selected_docs)
        other_rate = other_counts[term] / len(other_docs) if other_docs else 0.0
        score = round(selected_rate - other_rate, 3)
        if score > 0:
            results.append({"term": term, "score": score})

    results.sort(key=lambda item: (-item["score"], item["term"]))
    return results[:keyword_limit]


def diagnose_case(
    case: Mapping[str, Any],
    top_k: int = 1,
    stability_threshold: float = 0.67,
    position_threshold: float = 0.35,
    keyword_limit: Optional[int] = None,
    stopwords: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """Diagnose one query/candidate case and return a JSON-serializable result."""

    query_id = case.get("query_id", case.get("id"))
    if not isinstance(query_id, str) or not query_id:
        raise DiagnosticError("Each case must include a non-empty query_id or id")

    question = case.get("question", case.get("query", ""))
    if not isinstance(question, str) or not question:
        raise DiagnosticError(f"Case {query_id} must include a non-empty question or query")

    candidates = case.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise DiagnosticError(f"Case {query_id} must include a non-empty candidates list")

    seen: Set[str] = set()
    normalized_candidates: List[Mapping[str, Any]] = []
    for doc in candidates:
        if not isinstance(doc, Mapping):
            raise DiagnosticError(f"Case {query_id} has a candidate that is not an object")
        doc_id = _doc_id(doc)
        if doc_id in seen:
            raise DiagnosticError(f"Case {query_id} has duplicate candidate doc_id {doc_id}")
        seen.add(doc_id)
        normalized_candidates.append(doc)

    stop = stopwords if stopwords is not None else _env_stopwords()
    limit = _env_keyword_limit() if keyword_limit is None else keyword_limit

    selected_ids = _as_list(case.get("selected_doc_ids", case.get("selected_doc_id")), "selected_doc_ids")
    if not selected_ids:
        selected_ids = model_select(question, normalized_candidates, top_k=top_k, stopwords=stop)
    relevant_ids = _as_list(case.get("relevant_doc_ids", case.get("relevant_doc_id")), "relevant_doc_ids")

    candidate_ids = {_doc_id(doc) for doc in normalized_candidates}
    relevant_set = set(relevant_ids)
    selected_set = set(selected_ids)
    correct_evidence_present = bool(relevant_set & candidate_ids) if relevant_set else False
    selected_relevant = bool(relevant_set & selected_set) if relevant_set else False

    masking_trials, stability, alternatives = _masking_trials(
        question,
        normalized_candidates,
        selected_ids,
        top_k,
        stop,
    )
    position_bias = _position_bias_score(question, normalized_candidates, selected_ids, stop)
    keyword_attraction = _keyword_attraction(normalized_candidates, selected_ids, limit, stop)

    signals: List[str] = []
    if relevant_set and not correct_evidence_present:
        category = "correct_evidence_absent"
        signals.append("relevant evidence absent from candidates")
    else:
        if relevant_set and correct_evidence_present and not selected_relevant:
            signals.append("relevant evidence present but not selected")
        if stability < stability_threshold:
            signals.append("selection changed under masking")
        if position_bias >= position_threshold:
            signals.append("selected document benefits from early position")
        if keyword_attraction:
            signals.append("selected document has overrepresented terms")

        if signals:
            category = "reranker_instability_or_bias"
        else:
            category = "no_failure_signal"
            signals.append("no strong failure signal detected")

    return {
        "query_id": query_id,
        "failure_category": category,
        "selected_doc_ids": selected_ids,
        "relevant_doc_ids": relevant_ids,
        "correct_evidence_present": correct_evidence_present,
        "selection_stability": stability,
        "position_bias_score": position_bias,
        "masking_trials": masking_trials,
        "unstable_alternatives": alternatives,
        "keyword_attraction": keyword_attraction,
        "signals": signals,
    }


def analyze_cases(
    cases: Sequence[Mapping[str, Any]],
    top_k: int = 1,
    stability_threshold: float = 0.67,
    position_threshold: float = 0.35,
    keyword_limit: Optional[int] = None,
    stopwords: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """Analyze multiple cases and return the full diagnostic report."""

    if not cases:
        raise DiagnosticError("No cases were provided")

    results = [
        diagnose_case(
            case,
            top_k=top_k,
            stability_threshold=stability_threshold,
            position_threshold=position_threshold,
            keyword_limit=keyword_limit,
            stopwords=stopwords,
        )
        for case in cases
    ]

    summary: MutableMapping[str, Any] = {
        "cases": len(results),
        "correct_evidence_absent": sum(
            1 for item in results if item["failure_category"] == "correct_evidence_absent"
        ),
        "reranker_instability_or_bias": sum(
            1 for item in results if item["failure_category"] == "reranker_instability_or_bias"
        ),
        "no_failure_signal": sum(1 for item in results if item["failure_category"] == "no_failure_signal"),
    }
    summary["mean_selection_stability"] = round(
        sum(float(item["selection_stability"]) for item in results) / len(results), 3
    )
    summary["mean_position_bias_score"] = round(
        sum(float(item["position_bias_score"]) for item in results) / len(results), 3
    )

    return {
        "tool": "biaslens-rag",
        "version": VERSION,
        "summary": dict(summary),
        "cases": results,
    }


def sample_cases() -> List[Dict[str, Any]]:
    """Return built-in sample cases that exercise both major failure classes."""

    return [
        {
            "query_id": "q_absent",
            "question": "What is the refund policy after cancellation?",
            "selected_doc_ids": ["billing_faq"],
            "relevant_doc_ids": ["refund_policy"],
            "candidates": [
                {
                    "doc_id": "billing_faq",
                    "text": "Billing invoices and upgrade charges.",
                    "score": 0.95,
                },
                {
                    "doc_id": "shipping_notice",
                    "text": "Shipping tracking windows and delivery timing.",
                    "score": 0.72,
                },
            ],
        },
        {
            "query_id": "q_present_biased",
            "question": "What is the refund policy after cancellation?",
            "selected_doc_ids": ["billing_faq"],
            "relevant_doc_ids": ["refund_policy"],
            "candidates": [
                {
                    "doc_id": "billing_faq",
                    "text": "Billing invoices and upgrade charges.",
                    "score": 0.95,
                },
                {
                    "doc_id": "shipping_notice",
                    "text": "Shipping tracking windows and delivery timing.",
                    "score": 0.72,
                },
                {
                    "doc_id": "refund_policy",
                    "text": "Refund policy for cancellation requests and account closure.",
                    "score": 0.85,
                },
            ],
        },
    ]


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Load candidate cases from a JSONL file."""

    cases: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise DiagnosticError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
                if not isinstance(record, dict):
                    raise DiagnosticError(f"{path}:{line_number}: each JSONL record must be an object")
                cases.append(record)
    except FileNotFoundError as exc:
        raise DiagnosticError(f"Candidate file not found: {path}") from exc
    return cases


def load_selected_ids(path: Path) -> Dict[str, List[str]]:
    """Load optional selected IDs from JSON or JSONL."""

    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise DiagnosticError(f"Selected IDs file not found: {path}") from exc

    stripped = text.strip()
    if not stripped:
        return {}

    if stripped.startswith("{"):
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise DiagnosticError(f"{path}: invalid JSON: {exc.msg}") from exc
        if not isinstance(data, dict):
            raise DiagnosticError(f"{path}: selected ID JSON must be an object mapping query IDs to IDs")
        return {str(key): _as_list(value, f"selected ids for {key}") for key, value in data.items()}

    mapping: Dict[str, List[str]] = {}
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#"):
            continue
        try:
            record = json.loads(stripped_line)
        except json.JSONDecodeError as exc:
            raise DiagnosticError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
        if not isinstance(record, dict):
            raise DiagnosticError(f"{path}:{line_number}: each selected IDs line must be an object")
        query_id = record.get("query_id", record.get("id"))
        if not isinstance(query_id, str) or not query_id:
            raise DiagnosticError(f"{path}:{line_number}: missing query_id")
        mapping[query_id] = _as_list(
            record.get("selected_doc_ids", record.get("selected_doc_id")),
            f"selected ids for {query_id}",
        )
    return mapping


def apply_selected_ids(cases: List[Dict[str, Any]], selected_ids: Mapping[str, List[str]]) -> List[Dict[str, Any]]:
    """Overlay selected document IDs onto cases by query ID."""

    if not selected_ids:
        return cases
    output: List[Dict[str, Any]] = []
    for case in cases:
        query_id = case.get("query_id", case.get("id"))
        updated = dict(case)
        if isinstance(query_id, str) and query_id in selected_ids:
            updated["selected_doc_ids"] = selected_ids[query_id]
        output.append(updated)
    return output


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description="Diagnose RAG candidate selection failures with deterministic masking checks.",
    )
    parser.add_argument(
        "--candidates",
        type=Path,
        help="JSONL file with one case per line. Omit with --selftest to use built-in sample data.",
    )
    parser.add_argument(
        "--selected-ids",
        type=Path,
        help="Optional JSON or JSONL file mapping query_id to selected_doc_ids.",
    )
    parser.add_argument("--output", type=Path, help="Write JSON diagnostics to this file instead of stdout.")
    parser.add_argument("--top-k", type=int, default=1, help="Number of selected documents to compare.")
    parser.add_argument(
        "--stability-threshold",
        type=float,
        default=0.67,
        help="Flag reranker instability below this masking stability score.",
    )
    parser.add_argument(
        "--position-threshold",
        type=float,
        default=0.35,
        help="Flag position bias at or above this heuristic score.",
    )
    parser.add_argument(
        "--keyword-limit",
        type=int,
        default=None,
        help="Maximum keyword attraction terms per case. Defaults to BIASLENS_RAG_KEYWORD_LIMIT or 5.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run diagnostics on built-in sample data with no external files or API keys.",
    )
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON instead of pretty JSON.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point."""

    args = build_parser().parse_args(argv)
    try:
        if args.selftest or args.candidates is None:
            cases = sample_cases()
        else:
            cases = load_jsonl(args.candidates)

        if args.selected_ids is not None:
            cases = apply_selected_ids(cases, load_selected_ids(args.selected_ids))

        report = analyze_cases(
            cases,
            top_k=args.top_k,
            stability_threshold=args.stability_threshold,
            position_threshold=args.position_threshold,
            keyword_limit=args.keyword_limit,
        )
        json_text = json.dumps(
            report,
            indent=None if args.compact else 2,
            sort_keys=False,
        )
        if not args.compact:
            json_text += "\n"
        if args.output:
            args.output.write_text(json_text, encoding="utf-8")
        else:
            sys.stdout.write(json_text)
        return 0
    except DiagnosticError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
