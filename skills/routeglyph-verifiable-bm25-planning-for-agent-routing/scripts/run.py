#!/usr/bin/env python3
"""RouteGlyph: deterministic BM25-style planning for agent/tool routing.

The module exposes route_query() for tests and automation, plus a small CLI
that can run on built-in sample data without API keys or network access.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple


PLAN_VERSION = "routeglyph.v1"
TOKENIZER = "routeglyph-tokenizer.v1"

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

DEFAULT_SYNONYMS = {
    "agent": ["assistant", "worker"],
    "bm25": ["sparse", "idf", "retrieval"],
    "build": ["create", "implement", "write"],
    "code": ["programming", "script", "implementation"],
    "current": ["latest", "fresh", "recent", "today"],
    "debug": ["fix", "repair", "troubleshoot"],
    "document": ["doc", "markdown", "pdf"],
    "evaluate": ["test", "verify", "regression"],
    "image": ["picture", "visual", "graphic"],
    "local": ["offline", "deterministic"],
    "plan": ["planning", "workflow", "decompose"],
    "route": ["routing", "router", "orchestrator", "tool"],
    "search": ["find", "lookup", "retrieve", "web"],
    "tool": ["agent", "function", "connector"],
}

CONSTRAINT_PATTERNS = {
    "local_only": ["local", "offline", "no api key", "without api key", "no internet", "deterministic"],
    "freshness_required": ["latest", "current", "fresh", "today", "news", "recent", "price"],
    "code_required": ["code", "build", "script", "implementation", "debug", "python"],
    "regression_testable": ["test", "tests", "verify", "ci", "regression", "snapshot", "deterministic"],
    "visual_output": ["image", "picture", "graphic", "visual", "design"],
}

SAMPLE_QUERY = "Route an agent request to build a local regression-testable BM25 router with no API key."

SAMPLE_CATALOG = [
    {
        "id": "code_agent",
        "name": "Code Agent",
        "description": "Builds and debugs local scripts, command line tools, tests, and deterministic reference implementations.",
        "keywords": ["python", "implementation", "test", "local", "script"],
        "synonyms": ["code", "build", "debug", "programming"],
        "exclusions": ["marketing", "image"],
        "constraints": ["local_only", "code_required", "regression_testable"],
    },
    {
        "id": "web_research",
        "name": "Web Research Agent",
        "description": "Searches the public web for current facts, sources, news, prices, and recent changes.",
        "keywords": ["search", "web", "latest", "sources"],
        "synonyms": ["lookup", "find", "fresh", "current"],
        "exclusions": ["offline", "no internet", "no api key"],
        "constraints": ["freshness_required", "internet_required"],
    },
    {
        "id": "route_planner",
        "name": "Route Planner",
        "description": "Plans tool and agent routing using BM25 style sparse matching, rare terms, constraints, score rationales, and regression snapshots.",
        "keywords": ["routing", "bm25", "agent", "tool", "plan", "constraints", "idf"],
        "synonyms": ["router", "orchestrator", "planning"],
        "exclusions": ["image generation"],
        "constraints": ["regression_testable", "local_only"],
    },
    {
        "id": "image_designer",
        "name": "Image Designer",
        "description": "Creates visual concepts, image prompts, graphics, and design directions for creative assets.",
        "keywords": ["image", "visual", "prompt", "design", "creative"],
        "synonyms": ["picture", "graphic", "art"],
        "exclusions": ["local router", "bm25"],
        "constraints": ["visual_output"],
    },
]


class RouteGlyphError(ValueError):
    """Raised for clear user-facing RouteGlyph input errors."""


def tokenize(text: str) -> List[str]:
    """Return deterministic lowercase tokens with common stopwords removed."""

    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [token for token in tokens if token not in STOPWORDS]


def as_list(value: Any) -> List[str]:
    """Normalize strings, lists, tuples, and missing values into a string list."""

    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        if not value.strip():
            return []
        if "," in value:
            return [part.strip() for part in value.split(",") if part.strip()]
        return [value.strip()]
    return [str(value).strip()]


def slugify(value: str) -> str:
    """Create a stable id-like slug from a display value."""

    slug = "_".join(tokenize(value))
    return slug or "tool"


def normalize_tool(raw_tool: Mapping[str, Any], index: int) -> Dict[str, Any]:
    """Normalize one catalog entry into RouteGlyph's internal tool shape."""

    name = str(raw_tool.get("name") or raw_tool.get("id") or f"Tool {index + 1}").strip()
    tool_id = str(raw_tool.get("id") or raw_tool.get("tool_id") or slugify(name)).strip()
    description = str(raw_tool.get("description") or raw_tool.get("desc") or "").strip()
    if not description:
        raise RouteGlyphError(f"Tool '{tool_id}' is missing a non-empty description.")
    return {
        "id": tool_id,
        "name": name,
        "description": description,
        "keywords": as_list(raw_tool.get("keywords")),
        "synonyms": as_list(raw_tool.get("synonyms")),
        "exclusions": as_list(raw_tool.get("exclusions")),
        "constraints": as_list(raw_tool.get("constraints")),
    }


def parse_scalar(value: str) -> Any:
    """Parse a tiny YAML scalar subset used by catalog fixtures."""

    value = value.strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part.strip()) for part in inner.split(",")]
    return value


def parse_simple_yaml(text: str) -> Any:
    """Parse a small YAML subset: top-level tools list with scalar/list fields."""

    items: List[Dict[str, Any]] = []
    current: Dict[str, Any] | None = None
    pending_list_key: str | None = None

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        line = raw_line.split("#", 1)[0].rstrip()
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        if stripped == "tools:":
            continue
        if stripped.startswith("- ") and indent <= 2:
            if current:
                items.append(current)
            current = {}
            pending_list_key = None
            rest = stripped[2:].strip()
            if rest:
                if ":" not in rest:
                    raise RouteGlyphError(f"YAML line {line_number}: expected 'key: value' after '-'.")
                key, value = rest.split(":", 1)
                current[key.strip()] = parse_scalar(value)
            continue
        if current is None:
            raise RouteGlyphError(f"YAML line {line_number}: expected a tool item starting with '-'.")
        if stripped.startswith("- ") and pending_list_key:
            current.setdefault(pending_list_key, []).append(parse_scalar(stripped[2:]))
            continue
        if ":" not in stripped:
            raise RouteGlyphError(f"YAML line {line_number}: expected 'key: value'.")
        key, value = stripped.split(":", 1)
        key = key.strip()
        parsed = parse_scalar(value)
        if parsed == "":
            current[key] = []
            pending_list_key = key
        else:
            current[key] = parsed
            pending_list_key = None

    if current:
        items.append(current)
    if not items:
        raise RouteGlyphError("YAML catalog did not contain any tools.")
    return {"tools": items}


def load_catalog(path: str | None = None, inline_tools: Sequence[str] | None = None) -> List[Dict[str, Any]]:
    """Load and normalize tools from JSON, simple YAML, inline CLI values, or sample data."""

    raw_tools: List[Mapping[str, Any]] = []
    if path:
        catalog_path = Path(path)
        if not catalog_path.exists():
            raise RouteGlyphError(f"Catalog file not found: {path}")
        text = catalog_path.read_text(encoding="utf-8")
        suffix = catalog_path.suffix.lower()
        try:
            if suffix == ".json":
                parsed = json.loads(text)
            elif suffix in {".yaml", ".yml"}:
                parsed = parse_simple_yaml(text)
            else:
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    parsed = parse_simple_yaml(text)
        except json.JSONDecodeError as exc:
            raise RouteGlyphError(f"Invalid JSON catalog: {exc}") from exc
        if isinstance(parsed, list):
            raw_tools.extend(parsed)
        elif isinstance(parsed, dict) and isinstance(parsed.get("tools"), list):
            raw_tools.extend(parsed["tools"])
        else:
            raise RouteGlyphError("Catalog must be a list of tools or an object with a 'tools' list.")
    if inline_tools:
        for value in inline_tools:
            parts = [part.strip() for part in value.split("|")]
            if len(parts) < 3:
                raise RouteGlyphError("Inline tools must use 'id|name|description' or 'id|name|description|keywords'.")
            raw_tools.append(
                {
                    "id": parts[0],
                    "name": parts[1],
                    "description": parts[2],
                    "keywords": parts[3] if len(parts) > 3 else "",
                }
            )
    if not raw_tools:
        raw_tools = SAMPLE_CATALOG
    tools = [normalize_tool(tool, index) for index, tool in enumerate(raw_tools)]
    if not tools:
        raise RouteGlyphError("No tools were loaded.")
    return tools


def load_synonyms(env: Mapping[str, str] | None = None) -> Dict[str, List[str]]:
    """Load deterministic synonyms, optionally extending them from ROUTEGLYPH_SYNONYMS_JSON."""

    merged = {key: list(values) for key, values in DEFAULT_SYNONYMS.items()}
    env = env or os.environ
    raw = env.get("ROUTEGLYPH_SYNONYMS_JSON")
    if not raw:
        return merged
    try:
        extra = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RouteGlyphError(f"ROUTEGLYPH_SYNONYMS_JSON is not valid JSON: {exc}") from exc
    if not isinstance(extra, dict):
        raise RouteGlyphError("ROUTEGLYPH_SYNONYMS_JSON must be a JSON object mapping terms to lists.")
    for key, values in extra.items():
        key_tokens = tokenize(str(key))
        if not key_tokens:
            continue
        clean_values: List[str] = []
        for value in as_list(values):
            clean_values.extend(tokenize(value))
        merged[key_tokens[0]] = sorted(set(merged.get(key_tokens[0], []) + clean_values))
    return merged


def expand_query_terms(query_terms: Sequence[str], synonyms: Mapping[str, Sequence[str]]) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
    """Return weighted query terms plus an inspectable synonym expansion plan."""

    weights: Dict[str, float] = {}
    expansions: List[Dict[str, Any]] = []
    for term in query_terms:
        weights[term] = max(weights.get(term, 0.0), 1.0)
        related = set(synonyms.get(term, []))
        for canonical, values in synonyms.items():
            if term in values:
                related.add(canonical)
                related.update(values)
        related.discard(term)
        expanded = sorted({token for value in related for token in tokenize(value)})
        if expanded:
            expansions.append({"source": term, "expanded": expanded})
        for expanded_term in expanded:
            weights[expanded_term] = max(weights.get(expanded_term, 0.0), 0.65)
    return weights, expansions


def tool_document(tool: Mapping[str, Any]) -> List[str]:
    """Build the searchable token document for a normalized tool."""

    parts = [
        str(tool["name"]),
        str(tool["description"]),
        " ".join(as_list(tool.get("keywords"))),
        " ".join(as_list(tool.get("synonyms"))),
        " ".join(as_list(tool.get("constraints"))),
    ]
    return tokenize(" ".join(parts))


def compute_idf(documents: Sequence[Sequence[str]]) -> Dict[str, float]:
    """Compute BM25 inverse document frequency for all document terms."""

    document_count = len(documents)
    df: Counter[str] = Counter()
    for document in documents:
        df.update(set(document))
    return {
        term: math.log(1.0 + (document_count - count + 0.5) / (count + 0.5))
        for term, count in df.items()
    }


def phrase_or_token_present(query_text: str, query_terms: Sequence[str], pattern: str) -> bool:
    """Check whether a phrase or token pattern appears in the query."""

    pattern = pattern.lower().strip()
    if " " in pattern:
        return pattern in query_text
    return pattern in set(query_terms)


def extract_constraints(query: str, query_terms: Sequence[str]) -> List[str]:
    """Infer coarse required constraints from query phrases and terms."""

    query_text = query.lower()
    required = []
    for constraint, patterns in CONSTRAINT_PATTERNS.items():
        if any(phrase_or_token_present(query_text, query_terms, pattern) for pattern in patterns):
            required.append(constraint)
    return sorted(required)


def score_tool(
    tool: Mapping[str, Any],
    document: Sequence[str],
    query_weights: Mapping[str, float],
    idf: Mapping[str, float],
    average_document_length: float,
    required_constraints: Sequence[str],
    query_text: str,
    query_terms: Sequence[str],
) -> Dict[str, Any]:
    """Score one tool and return the full inspectable candidate plan."""

    k1 = 1.2
    b = 0.75
    term_counts = Counter(document)
    doc_length = max(len(document), 1)
    matched_terms: List[Dict[str, Any]] = []
    base_score = 0.0

    for term in sorted(query_weights):
        tf = term_counts.get(term, 0)
        if not tf:
            continue
        term_idf = idf.get(term, 0.0)
        norm = tf + k1 * (1.0 - b + b * doc_length / max(average_document_length, 1.0))
        contribution = query_weights[term] * term_idf * ((tf * (k1 + 1.0)) / norm)
        base_score += contribution
        matched_terms.append(
            {
                "term": term,
                "query_weight": round(query_weights[term], 2),
                "tool_tf": tf,
                "idf": round(term_idf, 4),
                "contribution": round(contribution, 4),
            }
        )

    configured_exclusions = as_list(tool.get("exclusions"))
    triggered_exclusions = [
        exclusion
        for exclusion in configured_exclusions
        if phrase_or_token_present(query_text, query_terms, exclusion)
    ]
    tool_constraints = sorted(as_list(tool.get("constraints")))
    matched_constraints = sorted(set(required_constraints).intersection(tool_constraints))
    missing_constraints = sorted(set(required_constraints).difference(tool_constraints))

    constraint_bonus = 0.2 * len(matched_constraints)
    exclusion_penalty = 1.5 * len(triggered_exclusions)
    final_score = max(0.0, base_score + constraint_bonus - exclusion_penalty)

    rare_terms = [
        item["term"]
        for item in sorted(matched_terms, key=lambda item: (-item["idf"], -item["contribution"], item["term"]))[:5]
    ]

    rationales = []
    if matched_terms:
        top_terms = ", ".join(item["term"] for item in sorted(matched_terms, key=lambda item: -item["contribution"])[:3])
        rationales.append(f"Matched high-value terms: {top_terms}.")
    if matched_constraints:
        rationales.append(f"Satisfied required constraints: {', '.join(matched_constraints)}.")
    if missing_constraints:
        rationales.append(f"Missing required constraints: {', '.join(missing_constraints)}.")
    if triggered_exclusions:
        rationales.append(f"Penalized by exclusions: {', '.join(triggered_exclusions)}.")
    if not rationales:
        rationales.append("No strong lexical or constraint match found.")

    return {
        "tool_id": str(tool["id"]),
        "tool_name": str(tool["name"]),
        "score": round(final_score, 4),
        "rare_terms": rare_terms,
        "matched_terms": matched_terms,
        "exclusions": {
            "configured": configured_exclusions,
            "triggered": triggered_exclusions,
        },
        "constraints": {
            "required": list(required_constraints),
            "matched": matched_constraints,
            "missing": missing_constraints,
        },
        "rationales": rationales,
    }


def route_query(
    query: str,
    tools: Sequence[Mapping[str, Any]],
    limit: int = 10,
    min_score: float = 0.0,
    synonyms: Mapping[str, Sequence[str]] | None = None,
) -> Dict[str, Any]:
    """Create a deterministic RouteGlyph routing plan for one query and catalog."""

    query = query.strip()
    if not query:
        raise RouteGlyphError("Query must be non-empty.")
    if limit < 1:
        raise RouteGlyphError("Limit must be at least 1.")
    normalized_tools = [normalize_tool(tool, index) for index, tool in enumerate(tools)]
    query_terms = tokenize(query)
    if not query_terms:
        raise RouteGlyphError("Query did not contain any searchable terms.")

    synonyms = synonyms or load_synonyms()
    query_weights, synonym_plan = expand_query_terms(query_terms, synonyms)
    documents = [tool_document(tool) for tool in normalized_tools]
    idf = compute_idf(documents)
    average_document_length = sum(len(document) for document in documents) / max(len(documents), 1)
    required_constraints = extract_constraints(query, query_terms)
    query_text = query.lower()

    candidates = [
        score_tool(
            tool=tool,
            document=document,
            query_weights=query_weights,
            idf=idf,
            average_document_length=average_document_length,
            required_constraints=required_constraints,
            query_text=query_text,
            query_terms=query_terms,
        )
        for tool, document in zip(normalized_tools, documents)
    ]
    filtered = [candidate for candidate in candidates if candidate["score"] >= min_score]
    ranked = sorted(filtered, key=lambda candidate: (-candidate["score"], candidate["tool_id"]))[:limit]
    for rank, candidate in enumerate(ranked, start=1):
        candidate["rank"] = rank
        candidate["synonyms"] = synonym_plan

    ordered_candidates = []
    for candidate in ranked:
        ordered_candidates.append(
            {
                "rank": candidate["rank"],
                "tool_id": candidate["tool_id"],
                "tool_name": candidate["tool_name"],
                "score": candidate["score"],
                "rare_terms": candidate["rare_terms"],
                "matched_terms": candidate["matched_terms"],
                "synonyms": candidate["synonyms"],
                "exclusions": candidate["exclusions"],
                "constraints": candidate["constraints"],
                "rationales": candidate["rationales"],
            }
        )

    return {
        "plan_version": PLAN_VERSION,
        "tokenizer": TOKENIZER,
        "query": query,
        "query_terms": query_terms,
        "required_constraints": required_constraints,
        "candidates": ordered_candidates,
    }


def env_int(name: str, default: int) -> int:
    """Read a positive integer from an environment variable."""

    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise RouteGlyphError(f"{name} must be an integer.") from exc
    if value < 1:
        raise RouteGlyphError(f"{name} must be at least 1.")
    return value


def env_float(name: str, default: float) -> float:
    """Read a non-negative float from an environment variable."""

    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise RouteGlyphError(f"{name} must be a number.") from exc
    if value < 0:
        raise RouteGlyphError(f"{name} must be non-negative.")
    return value


def read_query(args: argparse.Namespace) -> str:
    """Read the query from CLI flags or return the built-in sample query."""

    if args.query and args.query_file:
        raise RouteGlyphError("Use either --query or --query-file, not both.")
    if args.query_file:
        query_path = Path(args.query_file)
        if not query_path.exists():
            raise RouteGlyphError(f"Query file not found: {args.query_file}")
        return query_path.read_text(encoding="utf-8").strip()
    if args.query:
        return args.query
    return SAMPLE_QUERY


def build_parser() -> argparse.ArgumentParser:
    """Build the RouteGlyph command-line parser."""

    parser = argparse.ArgumentParser(
        description="Generate deterministic BM25-style routing plans for agent/tool catalogs.",
    )
    parser.add_argument("--query", help="User request to route.")
    parser.add_argument("--query-file", help="Text file containing the user request to route.")
    parser.add_argument("--catalog", help="Tool catalog as JSON or a small supported YAML subset.")
    parser.add_argument(
        "--tool",
        action="append",
        help="Inline tool as 'id|name|description' or 'id|name|description|keyword1,keyword2'. May be repeated.",
    )
    parser.add_argument("--limit", type=int, default=env_int("ROUTEGLYPH_LIMIT", 10), help="Maximum candidates to emit.")
    parser.add_argument(
        "--min-score",
        type=float,
        default=env_float("ROUTEGLYPH_MIN_SCORE", 0.0),
        help="Drop candidates below this score.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    parser.add_argument("--selftest", action="store_true", help="Run on built-in sample data with no API key.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the RouteGlyph CLI and return a process status code."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.selftest:
            tools = load_catalog()
            query = SAMPLE_QUERY
        else:
            tools = load_catalog(args.catalog, args.tool)
            query = read_query(args)
        plan = route_query(
            query=query,
            tools=tools,
            limit=args.limit,
            min_score=args.min_score,
            synonyms=load_synonyms(),
        )
    except RouteGlyphError as exc:
        print(f"routeglyph error: {exc}", file=sys.stderr)
        return 2
    indent = 2 if args.pretty or args.selftest or (not args.catalog and not args.tool and not args.query and not args.query_file) else None
    print(json.dumps(plan, indent=indent, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
