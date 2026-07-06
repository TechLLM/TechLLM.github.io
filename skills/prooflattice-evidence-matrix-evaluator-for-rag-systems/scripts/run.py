"""ProofLattice: deterministic evidence matrix evaluator for RAG outputs.

This script evaluates a retrieval-augmented generation response with simple,
auditable heuristics: keyword overlap, citation ID validation, claim-to-source
sentence alignment, omission checks, and document freshness windows. It does
not call external services and does not require an API key.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


DEFAULT_CITATION_PATTERN = r"\[([A-Za-z0-9_.:-]+)\]"
DEFAULT_EVALUATION_DATE = "2026-01-01"
DEFAULT_FRESHNESS_DAYS = 730
DEFAULT_MIN_CLAIM_OVERLAP = 0.25

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
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
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}


def sample_input() -> Dict[str, Any]:
    """Return a built-in RAG evaluation case used by --selftest and no-arg runs."""
    return {
        "question": "What changed in the 2024 VectorDB retention policy?",
        "answer": (
            "The 2024 VectorDB retention policy changed audit log retention "
            "from 30 days to 90 days [policy-2024]. Customer content logs stay "
            "disabled by default [policy-2024]."
        ),
        "documents": [
            {
                "id": "policy-2024",
                "title": "VectorDB Retention Policy 2024",
                "date": "2024-05-15",
                "text": (
                    "In 2024, VectorDB changed audit log retention from 30 days "
                    "to 90 days. Customer content logs remain disabled by default. "
                    "The update applies to enterprise workspaces."
                ),
            },
            {
                "id": "faq-2023",
                "title": "VectorDB Data FAQ",
                "date": "2023-09-10",
                "text": (
                    "Before the 2024 update, audit logs were retained for 30 days. "
                    "Workspace billing exports are retained for 365 days."
                ),
            },
        ],
        "config": {
            "evaluation_date": "2026-01-01",
            "freshness_window_days": 900,
            "min_claim_overlap": 0.25,
            "citation_pattern": DEFAULT_CITATION_PATTERN,
        },
    }


def load_case(path: Path) -> Dict[str, Any]:
    """Load and validate a JSON input case from disk."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Input file is not valid JSON: {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Input JSON must be an object.")
    validate_case(data)
    return data


def validate_case(case: Mapping[str, Any]) -> None:
    """Validate the minimal input contract required by the evaluator."""
    if not isinstance(case.get("question"), str) or not case["question"].strip():
        raise ValueError("Input must include a non-empty string field: question.")
    if not isinstance(case.get("answer"), str) or not case["answer"].strip():
        raise ValueError("Input must include a non-empty string field: answer.")
    documents = case.get("documents")
    if not isinstance(documents, list) or not documents:
        raise ValueError("Input must include a non-empty array field: documents.")

    seen_ids = set()
    for index, doc in enumerate(documents, start=1):
        if not isinstance(doc, dict):
            raise ValueError(f"Document {index} must be an object.")
        doc_id = doc.get("id")
        if not isinstance(doc_id, str) or not doc_id.strip():
            raise ValueError(f"Document {index} must include a non-empty string id.")
        if doc_id in seen_ids:
            raise ValueError(f"Duplicate document id: {doc_id}")
        seen_ids.add(doc_id)
        if not isinstance(doc.get("text"), str) or not doc["text"].strip():
            raise ValueError(f"Document {doc_id} must include non-empty text.")


def config_value(
    case_config: Mapping[str, Any],
    key: str,
    env_name: str,
    default: Any,
    caster: Any,
) -> Any:
    """Read a config value from input config, then environment, then a default."""
    raw = case_config.get(key, os.environ.get(env_name, default))
    try:
        return caster(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid value for {key} / {env_name}: {raw!r}") from exc


def parse_date(value: Optional[str]) -> Optional[dt.date]:
    """Parse an ISO date string, returning None when the value is absent or invalid."""
    if not value:
        return None
    try:
        return dt.date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def split_sentences(text: str) -> List[str]:
    """Split text into stable sentence-like chunks without external NLP packages."""
    normalized = re.sub(r"\s+", " ", text.strip())
    if not normalized:
        return []
    parts = re.split(r"(?<=[.!?])\s+", normalized)
    return [part.strip() for part in parts if part.strip()]


def strip_citations(text: str, citation_pattern: str) -> str:
    """Remove citation markers from text using the configured citation pattern."""
    return re.sub(citation_pattern, " ", text)


def normalize_spacing(text: str) -> str:
    """Collapse extra whitespace and remove spaces before punctuation."""
    collapsed = re.sub(r"\s+", " ", text.strip())
    return re.sub(r"\s+([.,;:!?])", r"\1", collapsed)


def extract_citations(text: str, citation_pattern: str) -> List[str]:
    """Extract citation identifiers from a text span."""
    citations = re.findall(citation_pattern, text)
    return [match if isinstance(match, str) else match[0] for match in citations]


def tokenize(text: str) -> List[str]:
    """Tokenize text into lower-case terms used by overlap heuristics."""
    raw_tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]*", text.lower())
    return [token for token in raw_tokens if token not in STOPWORDS and len(token) > 1]


def overlap_score(left_terms: Iterable[str], right_terms: Iterable[str]) -> Tuple[float, List[str]]:
    """Return recall-style overlap score and sorted shared terms."""
    left = set(left_terms)
    right = set(right_terms)
    if not left:
        return 0.0, []
    shared = sorted(left & right)
    return len(shared) / len(left), shared


def stable_evaluation_id(case: Mapping[str, Any]) -> str:
    """Create a deterministic short identifier for the evaluated case."""
    payload = json.dumps(case, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def status_from_score(score: float, pass_at: float, warn_at: float) -> str:
    """Convert a numeric score into pass, warn, or fail."""
    if score >= pass_at:
        return "pass"
    if score >= warn_at:
        return "warn"
    return "fail"


def build_document_sentences(documents: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Expand source documents into sentence records for claim matching."""
    records: List[Dict[str, Any]] = []
    for doc in documents:
        doc_id = str(doc["id"])
        date_text = str(doc.get("date", "") or "")
        for sentence in split_sentences(str(doc.get("text", ""))):
            records.append(
                {
                    "document_id": doc_id,
                    "title": str(doc.get("title", "") or ""),
                    "date": date_text,
                    "sentence": sentence,
                    "tokens": tokenize(sentence),
                }
            )
    return records


def best_sentence_support(
    claim_text: str,
    sentence_records: Sequence[Mapping[str, Any]],
    citation_pattern: str,
    allowed_document_ids: Optional[set] = None,
) -> Dict[str, Any]:
    """Find the highest-overlap source sentence for one answer claim."""
    plain_claim = strip_citations(claim_text, citation_pattern)
    claim_terms = tokenize(plain_claim)
    best: Dict[str, Any] = {
        "document_id": None,
        "title": None,
        "date": None,
        "sentence": None,
        "overlap_score": 0.0,
        "overlap_terms": [],
    }

    for record in sentence_records:
        if allowed_document_ids is not None and record["document_id"] not in allowed_document_ids:
            continue
        score, shared_terms = overlap_score(claim_terms, record["tokens"])
        if score > best["overlap_score"]:
            best = {
                "document_id": record["document_id"],
                "title": record["title"],
                "date": record["date"],
                "sentence": record["sentence"],
                "overlap_score": round(score, 3),
                "overlap_terms": shared_terms,
            }
    return best


def evaluate_case(case: Mapping[str, Any]) -> Dict[str, Any]:
    """Evaluate one RAG case and return a checklist plus JSON-ready evidence map."""
    validate_case(case)
    config = case.get("config") if isinstance(case.get("config"), dict) else {}
    citation_pattern = str(
        config.get("citation_pattern", os.environ.get("PROOFLATTICE_CITATION_PATTERN", DEFAULT_CITATION_PATTERN))
    )
    min_overlap = config_value(
        config,
        "min_claim_overlap",
        "PROOFLATTICE_MIN_OVERLAP",
        DEFAULT_MIN_CLAIM_OVERLAP,
        float,
    )
    freshness_days = config_value(
        config,
        "freshness_window_days",
        "PROOFLATTICE_FRESHNESS_DAYS",
        DEFAULT_FRESHNESS_DAYS,
        int,
    )
    evaluation_date_text = str(
        config.get("evaluation_date", os.environ.get("PROOFLATTICE_TODAY", DEFAULT_EVALUATION_DATE))
    )
    evaluation_date = parse_date(evaluation_date_text)
    if evaluation_date is None:
        raise ValueError(f"Invalid evaluation date: {evaluation_date_text!r}")

    question = str(case["question"])
    answer = str(case["answer"])
    documents = list(case["documents"])
    docs_by_id = {str(doc["id"]): doc for doc in documents}
    sentence_records = build_document_sentences(documents)

    answer_claims = split_sentences(answer)
    if not answer_claims:
        answer_claims = [answer.strip()]

    question_terms = tokenize(question)
    answer_terms = tokenize(strip_citations(answer, citation_pattern))
    directness_score, directness_terms = overlap_score(question_terms, answer_terms)

    evidence_claims: List[Dict[str, Any]] = []
    supported_count = 0
    cited_supported_count = 0
    claims_with_citations = 0
    valid_citation_ids = set()
    invalid_citation_ids = set()
    freshness_checks: List[bool] = []
    support_scores: List[float] = []

    for index, claim in enumerate(answer_claims, start=1):
        citations = extract_citations(claim, citation_pattern)
        valid_for_claim = [citation for citation in citations if citation in docs_by_id]
        invalid_for_claim = [citation for citation in citations if citation not in docs_by_id]
        valid_citation_ids.update(valid_for_claim)
        invalid_citation_ids.update(invalid_for_claim)

        best = best_sentence_support(claim, sentence_records, citation_pattern)
        cited_best = best_sentence_support(
            claim,
            sentence_records,
            citation_pattern,
            allowed_document_ids=set(valid_for_claim) if valid_for_claim else set(),
        )
        supported = bool(best["document_id"] and best["overlap_score"] >= min_overlap)
        citation_supported = bool(
            citations
            and not invalid_for_claim
            and cited_best["document_id"]
            and cited_best["overlap_score"] >= min_overlap
        )
        if supported:
            supported_count += 1
        if citations:
            claims_with_citations += 1
        if citation_supported:
            cited_supported_count += 1

        support_scores.append(float(best["overlap_score"]))
        support_date = parse_date(str(best.get("date") or ""))
        if support_date is not None:
            freshness_checks.append((evaluation_date - support_date).days <= freshness_days)

        evidence_claims.append(
            {
                "id": f"C{index}",
                "text": normalize_spacing(strip_citations(claim, citation_pattern)),
                "citations": citations,
                "valid_citations": valid_for_claim,
                "invalid_citations": invalid_for_claim,
                "supported": supported,
                "citation_supported": citation_supported,
                "best_support": best,
            }
        )

    evidence_coverage_score = supported_count / len(evidence_claims)
    citation_support_score = (
        cited_supported_count / claims_with_citations if claims_with_citations else 0.0
    )
    missing_question_terms = sorted(set(question_terms) - set(answer_terms))
    omission_score = 1.0 - (len(missing_question_terms) / len(set(question_terms)) if question_terms else 0.0)
    freshness_score = (
        sum(1 for is_fresh in freshness_checks if is_fresh) / len(freshness_checks)
        if freshness_checks
        else 0.0
    )
    factual_alignment_score = sum(support_scores) / len(support_scores) if support_scores else 0.0

    principles = [
        {
            "name": "directness",
            "status": status_from_score(directness_score, 0.60, 0.35),
            "score": round(directness_score, 3),
            "rationale": "Answer terms cover the main question terms.",
            "signals": {
                "matched_question_terms": directness_terms,
                "missing_question_terms": missing_question_terms,
            },
        },
        {
            "name": "evidence_coverage",
            "status": status_from_score(evidence_coverage_score, 0.80, 0.50),
            "score": round(evidence_coverage_score, 3),
            "rationale": "Answer claims have source sentences above the overlap threshold.",
            "signals": {
                "supported_claims": supported_count,
                "total_claims": len(evidence_claims),
                "min_claim_overlap": round(min_overlap, 3),
            },
        },
        {
            "name": "citation_support",
            "status": status_from_score(citation_support_score, 0.80, 0.50),
            "score": round(citation_support_score, 3),
            "rationale": "Claim citations resolve to retrieved document IDs with supporting text.",
            "signals": {
                "valid_citation_ids": sorted(valid_citation_ids),
                "invalid_citation_ids": sorted(invalid_citation_ids),
                "claims_with_citations": claims_with_citations,
            },
        },
        {
            "name": "omission_risk",
            "status": status_from_score(omission_score, 0.85, 0.65),
            "score": round(omission_score, 3),
            "rationale": "Lower risk when the answer covers the key terms from the question.",
            "signals": {
                "missing_question_terms": missing_question_terms,
            },
        },
        {
            "name": "freshness",
            "status": status_from_score(freshness_score, 0.80, 0.50),
            "score": round(freshness_score, 3),
            "rationale": "Supporting documents fall within the configured freshness window.",
            "signals": {
                "evaluation_date": evaluation_date.isoformat(),
                "freshness_window_days": freshness_days,
                "dated_supports_checked": len(freshness_checks),
            },
        },
        {
            "name": "factual_alignment",
            "status": status_from_score(factual_alignment_score, max(0.55, min_overlap), min_overlap),
            "score": round(factual_alignment_score, 3),
            "rationale": "Average claim-to-source overlap across answer claims.",
            "signals": {
                "average_best_overlap": round(factual_alignment_score, 3),
            },
        },
    ]

    principle_scores = [float(item["score"]) for item in principles]
    overall_score = sum(principle_scores) / len(principle_scores)
    if any(item["status"] == "fail" for item in principles):
        overall_status = "fail"
    elif any(item["status"] == "warn" for item in principles):
        overall_status = "warn"
    else:
        overall_status = "pass"

    recommendations = build_recommendations(principles, evidence_claims)
    evaluation_id = stable_evaluation_id(case)
    document_nodes = [
        {
            "id": str(doc["id"]),
            "title": str(doc.get("title", "") or ""),
            "date": str(doc.get("date", "") or ""),
            "sentence_count": len(split_sentences(str(doc.get("text", "")))),
        }
        for doc in documents
    ]
    edges = [
        {
            "claim_id": claim["id"],
            "document_id": claim["best_support"]["document_id"],
            "relationship": "supports" if claim["supported"] else "weak_or_missing",
            "overlap_score": claim["best_support"]["overlap_score"],
            "overlap_terms": claim["best_support"]["overlap_terms"],
            "citation_ids": claim["citations"],
            "sentence": claim["best_support"]["sentence"],
        }
        for claim in evidence_claims
    ]

    return {
        "checklist": {
            "evaluation_id": evaluation_id,
            "overall_status": overall_status,
            "overall_score": round(overall_score, 3),
            "principles": principles,
            "claims_reviewed": len(evidence_claims),
            "recommendations": recommendations,
        },
        "evidence_map": {
            "evaluation_id": evaluation_id,
            "claim_nodes": evidence_claims,
            "document_nodes": document_nodes,
            "edges": edges,
        },
    }


def build_recommendations(
    principles: Sequence[Mapping[str, Any]], evidence_claims: Sequence[Mapping[str, Any]]
) -> List[str]:
    """Create deterministic remediation notes for failed or warning checks."""
    recommendations: List[str] = []
    principle_status = {str(item["name"]): str(item["status"]) for item in principles}
    if principle_status.get("directness") != "pass":
        recommendations.append("Rewrite the answer to address the question terms more directly.")
    if principle_status.get("evidence_coverage") != "pass":
        weak_claims = [claim["id"] for claim in evidence_claims if not claim["supported"]]
        recommendations.append(f"Add or retrieve stronger evidence for claims: {', '.join(weak_claims)}.")
    if principle_status.get("citation_support") != "pass":
        recommendations.append("Fix missing or unsupported citation IDs before release.")
    if principle_status.get("omission_risk") != "pass":
        recommendations.append("Check whether important question terms were omitted from the answer.")
    if principle_status.get("freshness") != "pass":
        recommendations.append("Review source dates or adjust the freshness window for this use case.")
    if principle_status.get("factual_alignment") != "pass":
        recommendations.append("Manually review low-overlap claims for possible factual drift.")
    return recommendations


def yaml_scalar(value: Any) -> str:
    """Render a scalar value in a conservative YAML-compatible form."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.3f}"
    if isinstance(value, int):
        return str(value)
    if value == []:
        return "[]"
    if value == {}:
        return "{}"
    return json.dumps(str(value), ensure_ascii=True)


def is_inline_yaml(value: Any) -> bool:
    """Return True when a value can be rendered on one YAML line."""
    return value is None or isinstance(value, (str, int, float, bool)) or value == [] or value == {}


def to_yaml(value: Any, indent: int = 0) -> str:
    """Serialize dictionaries and lists to deterministic, readable YAML."""
    prefix = " " * indent
    lines: List[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            if is_inline_yaml(item):
                lines.append(f"{prefix}{key}: {yaml_scalar(item)}")
            else:
                lines.append(f"{prefix}{key}:")
                lines.append(to_yaml(item, indent + 2))
    elif isinstance(value, list):
        if not value:
            lines.append(f"{prefix}[]")
        for item in value:
            if is_inline_yaml(item):
                lines.append(f"{prefix}- {yaml_scalar(item)}")
            else:
                lines.append(f"{prefix}-")
                lines.append(to_yaml(item, indent + 2))
    else:
        lines.append(f"{prefix}{yaml_scalar(value)}")
    return "\n".join(lines)


def write_evidence_map(path: Path, result: Mapping[str, Any]) -> None:
    """Write the JSON evidence map to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result["evidence_map"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Evaluate a RAG answer with deterministic ProofLattice checks."
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Path to a JSON file with question, answer, documents, and optional config.",
    )
    parser.add_argument(
        "--format",
        choices=("yaml", "json"),
        default="yaml",
        help="Write the full checklist and evidence map as YAML or JSON to stdout.",
    )
    parser.add_argument(
        "--evidence-json",
        type=Path,
        help="Optional path to also write only the evidence_map object as JSON.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run the built-in sample case. This is also the no-argument behavior.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point for running the ProofLattice evaluator."""
    args = parse_args(argv)
    try:
        case = load_case(args.input) if args.input else sample_input()
        result = evaluate_case(case)
        if args.evidence_json:
            write_evidence_map(args.evidence_json, result)
        if args.format == "json":
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(to_yaml(result))
        return 0
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
