#!/usr/bin/env python3
"""ClaimWeaver reference CLI and library.

This module implements a small, deterministic consensus reducer for outputs
from multiple agents. It extracts claims, groups duplicate or near-duplicate
claims, scores each selected claim against rubric principles, and emits
auditable JSON or Markdown.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from difflib import SequenceMatcher
from typing import Any, Dict, Iterable, List, Sequence, Tuple


VERSION = "0.1.0"

DEFAULT_ACCEPT_THRESHOLD = 0.62
DEFAULT_REVIEW_THRESHOLD = 0.45
DEFAULT_SIMILARITY_THRESHOLD = 0.86

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
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "with",
}


def sample_input() -> Dict[str, Any]:
    """Return built-in sample data used by --selftest and scripts/test.py."""
    return {
        "task": "Merge agent findings about a prototype reducer.",
        "agents": [
            {
                "id": "agent-alpha",
                "output": (
                    "- The reducer extracts claims from Markdown bullets and plain sentences. "
                    "Source: design-note.md\n"
                    "- The reducer uses only the Python standard library for the deterministic path.\n"
                    "- The cache setting probably improves speed."
                ),
            },
            {
                "id": "agent-beta",
                "output": (
                    "- Claim extraction supports Markdown bullet lines, plain text sentences, "
                    "and JSON claim lists. Source: agent-beta-report.md\n"
                    "- The deterministic reducer can run without API keys.\n"
                    "- The cache setting probably improves speed."
                ),
            },
            {
                "id": "agent-gamma",
                "output": {
                    "claims": [
                        {
                            "text": "An optional evaluator interface lets teams plug in local or hosted model scorers.",
                            "evidence": "Architecture note says evaluators are swappable.",
                        },
                        {"text": "All agent outputs are always correct."},
                    ]
                },
            },
        ],
    }


def default_principles() -> List[Dict[str, Any]]:
    """Return deterministic default scoring principles."""
    return [
        {
            "id": "grounded",
            "description": "Prefer claims tied to evidence or concrete implementation details.",
            "weight": 0.4,
            "positive_keywords": [
                "source",
                "evidence",
                "supports",
                "uses",
                "deterministic",
                "without api keys",
                "standard library",
                "architecture",
            ],
            "negative_keywords": ["probably", "maybe", "always", "never"],
        },
        {
            "id": "actionable",
            "description": "Prefer claims that are specific enough to audit or reuse.",
            "weight": 0.35,
            "positive_keywords": [
                "extracts",
                "supports",
                "uses",
                "run",
                "interface",
                "plug",
                "markdown",
                "json",
                "standard library",
            ],
            "negative_keywords": ["correct", "improves"],
        },
        {
            "id": "cautious",
            "description": "Penalize unsupported absolutes and speculation.",
            "weight": 0.25,
            "positive_keywords": ["optional", "deterministic", "can", "source"],
            "negative_keywords": ["probably", "always", "never", "guaranteed"],
        },
    ]


def env_float(name: str, default: float) -> float:
    """Read a float from the environment with a clear error on bad values."""
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number, got {raw!r}") from exc


def parse_inline_list(value: str) -> List[str]:
    """Parse a tiny YAML-style inline list such as [source, evidence]."""
    value = value.strip()
    if not (value.startswith("[") and value.endswith("]")):
        return [parse_scalar(value)]
    inner = value[1:-1].strip()
    if not inner:
        return []
    return [parse_scalar(part.strip()) for part in inner.split(",")]


def parse_scalar(value: str) -> Any:
    """Parse a small scalar subset used by the example YAML rubric."""
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        return parse_inline_list(value)
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def load_rubric(path: str) -> List[Dict[str, Any]]:
    """Load principle definitions from JSON or a simple YAML rubric file."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            content = handle.read()
    except OSError as exc:
        raise ValueError(f"could not read rubric file {path!r}: {exc}") from exc

    stripped = content.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"rubric JSON is invalid: {exc}") from exc
        principles = data.get("principles", data) if isinstance(data, dict) else data
        return normalize_principles(principles)

    principles: List[Dict[str, Any]] = []
    current: Dict[str, Any] | None = None
    in_principles = False

    for raw_line in content.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        stripped_line = line.strip()
        if stripped_line == "principles:":
            in_principles = True
            continue
        if not in_principles:
            continue
        if stripped_line.startswith("- "):
            if current:
                principles.append(current)
            current = {}
            remainder = stripped_line[2:].strip()
            if remainder:
                key, value = split_key_value(remainder)
                current[key] = parse_scalar(value)
            continue
        if current is not None and ":" in stripped_line:
            key, value = split_key_value(stripped_line)
            current[key] = parse_scalar(value)
            continue
        if not raw_line.startswith((" ", "\t")):
            break
    if current:
        principles.append(current)

    return normalize_principles(principles)


def split_key_value(text: str) -> Tuple[str, str]:
    """Split a YAML-like key/value line."""
    if ":" not in text:
        raise ValueError(f"expected key: value in rubric line {text!r}")
    key, value = text.split(":", 1)
    return key.strip(), value.strip()


def normalize_principles(principles: Any) -> List[Dict[str, Any]]:
    """Validate and normalize principle dictionaries."""
    if not isinstance(principles, list) or not principles:
        raise ValueError("rubric must define a non-empty principles list")
    normalized = []
    for index, item in enumerate(principles, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"principle {index} must be an object")
        principle_id = str(item.get("id", f"principle-{index}")).strip()
        if not principle_id:
            raise ValueError(f"principle {index} has an empty id")
        try:
            weight = float(item.get("weight", 1.0))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"principle {principle_id!r} has invalid weight") from exc
        if weight <= 0:
            raise ValueError(f"principle {principle_id!r} weight must be positive")
        normalized.append(
            {
                "id": principle_id,
                "description": str(item.get("description", "")).strip(),
                "weight": weight,
                "positive_keywords": list(item.get("positive_keywords", [])),
                "negative_keywords": list(item.get("negative_keywords", [])),
            }
        )
    return normalized


def load_input(path: str) -> Dict[str, Any]:
    """Load JSON, Markdown, or plain text agent output input."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            content = handle.read()
    except OSError as exc:
        raise ValueError(f"could not read input file {path!r}: {exc}") from exc

    stripped = content.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"input JSON is invalid: {exc}") from exc
        if isinstance(data, list):
            return {"task": "Reduce agent outputs.", "agents": data}
        if not isinstance(data, dict):
            raise ValueError("input JSON must be an object or list")
        return data

    return {
        "task": f"Reduce claims from {os.path.basename(path)}.",
        "agents": [{"id": "input-1", "output": content}],
    }


def normalize_agents(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize supported input shapes into agent dictionaries."""
    if "agents" in data:
        agents = data["agents"]
    elif "outputs" in data:
        agents = data["outputs"]
    else:
        agents = [{"id": data.get("id", "input-1"), "output": data.get("output", data)}]
    if not isinstance(agents, list) or not agents:
        raise ValueError("input must contain a non-empty agents array")

    normalized = []
    for index, agent in enumerate(agents, start=1):
        if isinstance(agent, str):
            normalized.append({"id": f"agent-{index}", "output": agent})
            continue
        if not isinstance(agent, dict):
            raise ValueError(f"agent {index} must be a string or object")
        agent_id = str(agent.get("id") or agent.get("name") or f"agent-{index}").strip()
        output = agent.get("output", agent.get("text", agent.get("claims", "")))
        normalized.append({"id": agent_id or f"agent-{index}", "output": output})
    return normalized


def extract_claims(data: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract claim records with agent provenance and source passage text."""
    claims: List[Dict[str, str]] = []
    for agent in normalize_agents(data):
        claims.extend(extract_from_output(agent["id"], agent["output"]))
    if not claims:
        raise ValueError("no claims were found in the input")
    return claims


def extract_from_output(agent_id: str, output: Any) -> List[Dict[str, str]]:
    """Extract claims from text, lists, or JSON-like claim objects."""
    claims: List[Dict[str, str]] = []
    if isinstance(output, dict):
        if "claims" in output:
            return extract_from_output(agent_id, output["claims"])
        text_parts = [str(value) for value in output.values() if isinstance(value, str)]
        return extract_from_text(agent_id, "\n".join(text_parts))
    if isinstance(output, list):
        for item in output:
            if isinstance(item, dict):
                text = str(item.get("text") or item.get("claim") or "").strip()
                evidence = str(item.get("evidence") or item.get("source") or "").strip()
                if text:
                    passage = text if not evidence else f"{text} Evidence: {evidence}"
                    claims.append({"agent": agent_id, "text": text, "passage": passage})
            elif isinstance(item, str):
                claims.extend(extract_from_text(agent_id, item))
        return claims
    return extract_from_text(agent_id, str(output))


def extract_from_text(agent_id: str, text: str) -> List[Dict[str, str]]:
    """Extract claim-like sentences from Markdown or plain text."""
    claims: List[Dict[str, str]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        line = re.sub(r"^([-*+]|\d+[.)])\s+", "", line).strip()
        if not line:
            continue
        if re.search(r"\bsource\s*:", line, flags=re.IGNORECASE):
            claim_text = re.sub(r"\s+source\s*:.*$", "", line, flags=re.IGNORECASE).strip()
            if is_claim_like(claim_text):
                claims.append({"agent": agent_id, "text": claim_text, "passage": line})
            continue
        for sentence in split_sentences(line):
            if is_claim_like(sentence):
                claims.append({"agent": agent_id, "text": sentence, "passage": sentence})
    return claims


def split_sentences(text: str) -> List[str]:
    """Split plain text into simple sentence candidates."""
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def is_claim_like(text: str) -> bool:
    """Return True when text is long enough to be treated as a claim."""
    return len(re.findall(r"[A-Za-z0-9]+", text)) >= 4


def normalize_for_similarity(text: str) -> str:
    """Normalize claim text for deterministic similarity checks."""
    tokens = []
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        if token in STOPWORDS:
            continue
        if len(token) > 3 and token.endswith("s"):
            token = token[:-1]
        tokens.append(token)
    return " ".join(tokens)


def claim_similarity(left: str, right: str) -> float:
    """Compute a standard-library similarity score between two claims."""
    left_norm = normalize_for_similarity(left)
    right_norm = normalize_for_similarity(right)
    if not left_norm or not right_norm:
        return 0.0
    sequence = SequenceMatcher(None, left_norm, right_norm).ratio()
    left_tokens = set(left_norm.split())
    right_tokens = set(right_norm.split())
    overlap = len(left_tokens & right_tokens) / max(1, len(left_tokens | right_tokens))
    return max(sequence, overlap)


def group_claims(
    claims: Sequence[Dict[str, str]], similarity_threshold: float
) -> List[List[Dict[str, str]]]:
    """Group duplicate and near-duplicate claims."""
    groups: List[List[Dict[str, str]]] = []
    for claim in claims:
        for group in groups:
            if any(
                claim_similarity(claim["text"], existing["text"]) >= similarity_threshold
                for existing in group
            ):
                group.append(claim)
                break
        else:
            groups.append([claim])
    return groups


def score_claim(
    text: str, sources: Sequence[Dict[str, str]], principles: Sequence[Dict[str, Any]]
) -> Tuple[float, List[Dict[str, Any]]]:
    """Score a claim against rubric principles and return confidence details."""
    principle_scores = []
    total_weight = 0.0
    weighted = 0.0
    content = " ".join([text] + [source["passage"] for source in sources]).lower()
    word_count = len(re.findall(r"[A-Za-z0-9]+", text))
    has_evidence_marker = bool(
        re.search(r"\b(source|evidence|according to|reported|observed)\b", content)
    )

    for principle in principles:
        positive = [
            str(keyword)
            for keyword in principle.get("positive_keywords", [])
            if str(keyword).lower() in content
        ]
        negative = [
            str(keyword)
            for keyword in principle.get("negative_keywords", [])
            if str(keyword).lower() in content
        ]
        score = 0.5
        if positive:
            score += min(0.35, 0.18 + 0.06 * len(positive))
        if negative:
            score -= min(0.45, 0.22 + 0.08 * len(negative))
        if 7 <= word_count <= 40:
            score += 0.1
        elif word_count < 4:
            score -= 0.2
        elif word_count > 60:
            score -= 0.1

        principle_text = f"{principle['id']} {principle.get('description', '')}".lower()
        if has_evidence_marker:
            score += 0.15 if any(
                term in principle_text for term in ("evidence", "source", "ground", "support")
            ) else 0.05
        if any(term in content for term in ("always", "never", "guaranteed")) and any(
            term in principle_text for term in ("cautious", "speculation", "absolute")
        ):
            score -= 0.2

        score = round(max(0.0, min(1.0, score)), 2)
        rationale_parts = []
        if positive:
            rationale_parts.append("positive: " + ", ".join(sorted(set(positive))))
        if negative:
            rationale_parts.append("negative: " + ", ".join(sorted(set(negative))))
        if has_evidence_marker:
            rationale_parts.append("evidence marker present")
        if not rationale_parts:
            rationale_parts.append("baseline heuristic score")

        weight = float(principle["weight"])
        total_weight += weight
        weighted += score * weight
        principle_scores.append(
            {
                "id": principle["id"],
                "score": score,
                "rationale": "; ".join(rationale_parts),
            }
        )

    confidence = round(weighted / total_weight, 2) if total_weight else 0.0
    return confidence, principle_scores


def unique_sources(group: Sequence[Dict[str, str]]) -> List[Dict[str, str]]:
    """Return stable unique source passages for a claim group."""
    seen = set()
    sources = []
    for claim in group:
        key = (claim["agent"], claim["passage"])
        if key in seen:
            continue
        seen.add(key)
        sources.append({"agent": claim["agent"], "passage": claim["passage"]})
    return sources


def status_for_score(score: float, accept_threshold: float, review_threshold: float) -> str:
    """Map a confidence score to an acceptance status."""
    if score >= accept_threshold:
        return "accepted"
    if score >= review_threshold:
        return "needs_review"
    return "rejected"


def build_rationale(
    status: str, confidence: float, accept_threshold: float, source_count: int
) -> str:
    """Create a concise deterministic rationale for the final decision."""
    if status == "accepted":
        decision = f"met acceptance threshold {accept_threshold:.2f}"
    elif status == "needs_review":
        decision = "fell between the review and acceptance thresholds"
    else:
        decision = f"fell below acceptance threshold {accept_threshold:.2f}"
    return (
        f"Selected trace scored {confidence:.2f}, {decision}, "
        f"with {source_count} supporting source passage(s)."
    )


def reduce_agent_outputs(
    data: Dict[str, Any],
    principles: Sequence[Dict[str, Any]] | None = None,
    accept_threshold: float | None = None,
    review_threshold: float | None = None,
    similarity_threshold: float | None = None,
) -> Dict[str, Any]:
    """Reduce multiple agent outputs into auditable claim consensus JSON."""
    principles = list(principles or default_principles())
    accept_threshold = (
        accept_threshold
        if accept_threshold is not None
        else env_float("CLAIMWEAVER_ACCEPT_THRESHOLD", DEFAULT_ACCEPT_THRESHOLD)
    )
    review_threshold = (
        review_threshold
        if review_threshold is not None
        else env_float("CLAIMWEAVER_REVIEW_THRESHOLD", DEFAULT_REVIEW_THRESHOLD)
    )
    similarity_threshold = (
        similarity_threshold
        if similarity_threshold is not None
        else env_float("CLAIMWEAVER_SIMILARITY_THRESHOLD", DEFAULT_SIMILARITY_THRESHOLD)
    )
    if not 0 <= review_threshold <= accept_threshold <= 1:
        raise ValueError("thresholds must satisfy 0 <= review <= accept <= 1")
    if not 0 <= similarity_threshold <= 1:
        raise ValueError("similarity threshold must be between 0 and 1")

    raw_claims = extract_claims(data)
    groups = group_claims(raw_claims, similarity_threshold)
    claim_records = []

    for index, group in enumerate(groups, start=1):
        sources = unique_sources(group)
        candidates = []
        for claim in group:
            confidence, principle_scores = score_claim(claim["text"], sources, principles)
            candidates.append(
                (confidence, len(claim["text"]), claim["text"], claim, principle_scores)
            )
        confidence, _, selected_text, _selected_claim, principle_scores = max(
            candidates, key=lambda item: (item[0], item[1], item[2])
        )
        status = status_for_score(confidence, accept_threshold, review_threshold)
        supporting_agents = sorted({source["agent"] for source in sources})
        claim_records.append(
            {
                "claim_id": f"cw-{index:03d}",
                "status": status,
                "confidence": confidence,
                "text": selected_text,
                "rationale": build_rationale(
                    status, confidence, accept_threshold, len(sources)
                ),
                "supporting_agents": supporting_agents,
                "supporting_sources": sources,
                "principle_scores": principle_scores,
            }
        )

    accepted = [claim["claim_id"] for claim in claim_records if claim["status"] == "accepted"]
    needs_review = [
        claim["claim_id"] for claim in claim_records if claim["status"] == "needs_review"
    ]
    rejected = [claim["claim_id"] for claim in claim_records if claim["status"] == "rejected"]

    return {
        "metadata": {
            "tool": "ClaimWeaver",
            "version": VERSION,
            "evaluator": "rule",
            "claim_count": len(claim_records),
            "accepted": len(accepted),
            "needs_review": len(needs_review),
            "rejected": len(rejected),
        },
        "task": str(data.get("task", "Reduce agent outputs.")),
        "principles": [
            {
                "id": principle["id"],
                "description": principle.get("description", ""),
                "weight": float(principle["weight"]),
            }
            for principle in principles
        ],
        "claims": claim_records,
        "accepted": accepted,
        "needs_review": needs_review,
        "rejected": rejected,
    }


def render_markdown(result: Dict[str, Any]) -> str:
    """Render reduction output as readable Markdown."""
    meta = result["metadata"]
    lines = [
        "# ClaimWeaver Reduction",
        "",
        f"Task: {result['task']}",
        "",
        (
            f"Summary: {meta['claim_count']} claims, {meta['accepted']} accepted, "
            f"{meta['needs_review']} needs review, {meta['rejected']} rejected."
        ),
        "",
    ]
    for status, title in [
        ("accepted", "Accepted"),
        ("needs_review", "Needs Review"),
        ("rejected", "Rejected"),
    ]:
        lines.append(f"## {title}")
        matching = [claim for claim in result["claims"] if claim["status"] == status]
        if not matching:
            lines.append("")
            lines.append("None.")
            lines.append("")
            continue
        for claim in matching:
            lines.append("")
            lines.append(f"- {claim['claim_id']} ({claim['confidence']:.2f}): {claim['text']}")
            lines.append(f"  Rationale: {claim['rationale']}")
            agents = ", ".join(claim["supporting_agents"])
            lines.append(f"  Agents: {agents}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Merge multiple agent outputs into principle-scored claim consensus."
    )
    parser.add_argument("input", nargs="?", help="JSON, Markdown, or plain text input file")
    parser.add_argument("--rubric", help="Optional JSON or simple YAML principle rubric")
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="Output format, default: json",
    )
    parser.add_argument("--output", help="Optional output file")
    parser.add_argument(
        "--accept-threshold",
        type=float,
        help=f"Acceptance threshold, default: {DEFAULT_ACCEPT_THRESHOLD}",
    )
    parser.add_argument(
        "--review-threshold",
        type=float,
        help=f"Review threshold, default: {DEFAULT_REVIEW_THRESHOLD}",
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        help=f"Duplicate grouping threshold, default: {DEFAULT_SIMILARITY_THRESHOLD}",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run built-in sample data without requiring an API key",
    )
    parser.add_argument("--version", action="version", version=f"ClaimWeaver {VERSION}")
    return parser


def run_cli(argv: Sequence[str] | None = None) -> int:
    """Run the ClaimWeaver command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        os.environ.get("CLAIMWEAVER_API_KEY")
        os.environ.get("CLAIMWEAVER_EVALUATOR", "rule")
        data = sample_input() if args.selftest or not args.input else load_input(args.input)
        principles = load_rubric(args.rubric) if args.rubric else default_principles()
        result = reduce_agent_outputs(
            data,
            principles=principles,
            accept_threshold=args.accept_threshold,
            review_threshold=args.review_threshold,
            similarity_threshold=args.similarity_threshold,
        )
        rendered = (
            json.dumps(result, indent=2, ensure_ascii=False)
            + "\n"
            if args.format == "json"
            else render_markdown(result)
        )
        if args.output:
            with open(args.output, "w", encoding="utf-8") as handle:
                handle.write(rendered)
        else:
            sys.stdout.write(rendered)
        return 0
    except ValueError as exc:
        sys.stderr.write(f"ClaimWeaver error: {exc}\n")
        return 2
    except OSError as exc:
        sys.stderr.write(f"ClaimWeaver file error: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(run_cli())
