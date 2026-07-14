#!/usr/bin/env python3
"""Build deterministic, hub-bias-resistant evidence packs from graph candidates."""

import argparse
import copy
import json
import math
import os
import re
import statistics
import sys
from collections import Counter
from datetime import date
from pathlib import Path


DEFAULT_WEIGHTS = {
    "semantic_relevance": 0.45,
    "inverse_degree": 0.20,
    "recency": 0.15,
    "source_completeness": 0.10,
    "metadata_quality": 0.10,
}

SAMPLE_INPUT = {
    "query": "What recent checkout failures, rollback actions, and customer impact evidence should operators review?",
    "as_of": "2026-01-15",
    "graph": {
        "nodes": [
            "architecture-overview",
            "checkout-incident",
            "customer-impact",
            "general-platform",
            "rollback-runbook",
            "security-advisory",
        ],
        "edges": [
            ["general-platform", "architecture-overview"],
            ["general-platform", "checkout-incident"],
            ["general-platform", "customer-impact"],
            ["general-platform", "rollback-runbook"],
            ["general-platform", "security-advisory"],
        ],
    },
    "notes": [
        {
            "id": "general-platform",
            "title": "General platform overview",
            "text": "Broad background on services, deployment, checkout, and operations.",
            "community": "foundation",
            "updated_at": "2021-06-01",
            "sources": [],
            "tags": [],
            "semantic_score": 0.98,
        },
        {
            "id": "architecture-overview",
            "title": "Checkout architecture overview",
            "text": "Background description of the checkout API and service dependencies.",
            "community": "foundation",
            "updated_at": "2022-02-10",
            "sources": [
                {"title": "Architecture record", "uri": "kb://adr/checkout-architecture"}
            ],
            "tags": ["architecture"],
            "semantic_score": 0.92,
        },
        {
            "id": "checkout-incident",
            "title": "Checkout API timeout incident",
            "text": "A recent payment dependency timeout caused checkout failures and operator alerts.",
            "community": "operations",
            "updated_at": "2026-01-12",
            "sources": [
                {"title": "Incident timeline", "uri": "kb://incidents/inc-204"},
                {"title": "Metrics snapshot", "uri": "kb://metrics/checkout-204"},
            ],
            "tags": ["incident", "checkout"],
            "semantic_score": 0.88,
        },
        {
            "id": "rollback-runbook",
            "title": "Checkout rollback action log",
            "text": "Operators rolled back the payment adapter and verified checkout recovery.",
            "community": "operations",
            "updated_at": "2026-01-14",
            "sources": [
                {"title": "Rollback log", "uri": "kb://runs/rollback-88"},
                {"title": "Recovery check", "uri": "kb://checks/recovery-88"},
            ],
            "tags": ["rollback", "operations"],
            "semantic_score": 0.84,
        },
        {
            "id": "customer-impact",
            "title": "Customer reports during checkout degradation",
            "text": "Support recorded failed checkout attempts and the affected customer segments.",
            "community": "support",
            "updated_at": "2026-01-10",
            "sources": [
                {"title": "Anonymized support digest", "uri": "kb://support/digest-51"}
            ],
            "tags": ["customer-impact", "checkout"],
            "semantic_score": 0.81,
        },
        {
            "id": "security-advisory",
            "title": "Payment dependency security advisory",
            "text": "A recent advisory describes a dependency condition relevant to failure triage.",
            "community": "security",
            "updated_at": "2026-01-08",
            "sources": [
                {"title": "Vendor advisory", "uri": "kb://vendors/advisory-17"},
                {"title": "Internal assessment", "uri": "kb://security/assessment-17"},
            ],
            "tags": ["security", "dependency"],
            "semantic_score": 0.78,
        },
    ],
    "settings": {
        "top_k": 4,
        "per_community_cap": 2,
        "min_communities": 3,
        "redundancy_weight": 0.08,
    },
}


class ValidationError(ValueError):
    """Report malformed input or unsafe output requests to CLI callers."""


def _number(value, label):
    """Return a finite float or raise a field-specific validation error."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError("{} must be a number".format(label))
    result = float(value)
    if not math.isfinite(result):
        raise ValidationError("{} must be finite".format(label))
    return result


def _positive_int(value, label):
    """Return a positive integer or raise a field-specific validation error."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValidationError("{} must be a positive integer".format(label))
    return value


def _parse_date(value, label):
    """Parse a strict ISO calendar date."""
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValidationError("{} must use YYYY-MM-DD".format(label))
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError("{} is not a valid calendar date".format(label)) from exc


def _tokens(text):
    """Return deterministic lowercase alphanumeric tokens."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _similarity(left, right):
    """Return Jaccard similarity for two token sets."""
    union = left | right
    return 0.0 if not union else len(left & right) / len(union)


def _round(value):
    """Round public numeric output consistently."""
    return round(float(value), 6)


def _validate_and_prepare(data, overrides):
    """Validate raw input and derive candidates, settings, degrees, and weights."""
    if not isinstance(data, dict):
        raise ValidationError("input must be a JSON object")
    query = data.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValidationError("query must be a non-empty string")

    notes = data.get("notes")
    if not isinstance(notes, list) or not notes:
        raise ValidationError("notes must be a non-empty array")

    graph = data.get("graph")
    if not isinstance(graph, dict) or not isinstance(graph.get("edges"), list):
        raise ValidationError("graph.edges must be an array")

    declared_nodes = graph.get("nodes")
    if declared_nodes is not None:
        if not isinstance(declared_nodes, list) or any(
            not isinstance(node, str) or not node for node in declared_nodes
        ):
            raise ValidationError("graph.nodes must contain non-empty string IDs")
        if len(declared_nodes) != len(set(declared_nodes)):
            raise ValidationError("graph.nodes contains duplicate IDs")
        known_nodes = set(declared_nodes)
    else:
        known_nodes = set()

    neighbor_sets = {}
    for index, edge in enumerate(graph["edges"]):
        if (
            not isinstance(edge, list)
            or len(edge) != 2
            or any(not isinstance(node, str) or not node for node in edge)
        ):
            raise ValidationError("graph.edges[{}] must be two non-empty string IDs".format(index))
        left, right = edge
        if left == right:
            raise ValidationError("graph.edges[{}] must not be a self-loop".format(index))
        if declared_nodes is not None and (left not in known_nodes or right not in known_nodes):
            raise ValidationError("graph.edges[{}] references an undeclared node".format(index))
        known_nodes.update((left, right))
        neighbor_sets.setdefault(left, set()).add(right)
        neighbor_sets.setdefault(right, set()).add(left)

    seen_ids = set()
    parsed_notes = []
    parsed_dates = []
    for index, note in enumerate(notes):
        label = "notes[{}]".format(index)
        if not isinstance(note, dict):
            raise ValidationError("{} must be an object".format(label))
        note_id = note.get("id")
        if not isinstance(note_id, str) or not note_id:
            raise ValidationError("{}.id must be a non-empty string".format(label))
        if note_id in seen_ids:
            raise ValidationError("duplicate note id: {}".format(note_id))
        if declared_nodes is not None and note_id not in known_nodes:
            raise ValidationError("note id {} is missing from graph.nodes".format(note_id))
        seen_ids.add(note_id)
        known_nodes.add(note_id)

        for field in ("title", "community", "updated_at"):
            if not isinstance(note.get(field), str) or not note[field]:
                raise ValidationError("{}.{} must be a non-empty string".format(label, field))
        text = note.get("text", "")
        if not isinstance(text, str):
            raise ValidationError("{}.text must be a string".format(label))
        updated = _parse_date(note["updated_at"], "{}.updated_at".format(label))
        parsed_dates.append(updated)

        sources = note.get("sources", [])
        if not isinstance(sources, list):
            raise ValidationError("{}.sources must be an array".format(label))
        for source_index, source in enumerate(sources):
            source_label = "{}.sources[{}]".format(label, source_index)
            if not isinstance(source, dict):
                raise ValidationError("{} must be an object".format(source_label))
            for field in ("title", "uri"):
                if not isinstance(source.get(field), str) or not source[field]:
                    raise ValidationError("{}.{} must be a non-empty string".format(source_label, field))
            if "retrieved_at" in source:
                _parse_date(source["retrieved_at"], "{}.retrieved_at".format(source_label))

        tags = note.get("tags", [])
        if not isinstance(tags, list) or any(not isinstance(tag, str) or not tag for tag in tags):
            raise ValidationError("{}.tags must contain non-empty strings".format(label))

        semantic = note.get("semantic_score")
        if semantic is not None:
            semantic = _number(semantic, "{}.semantic_score".format(label))
            if not 0.0 <= semantic <= 1.0:
                raise ValidationError("{}.semantic_score must be between 0 and 1".format(label))

        parsed = copy.deepcopy(note)
        parsed["text"] = text
        parsed["sources"] = sources
        parsed["tags"] = tags
        parsed["_updated_date"] = updated
        parsed["_semantic_score"] = semantic
        parsed_notes.append(parsed)

    as_of_value = data.get("as_of")
    as_of = max(parsed_dates) if as_of_value is None else _parse_date(as_of_value, "as_of")
    for note in parsed_notes:
        if note["_updated_date"] > as_of:
            raise ValidationError("note {} is newer than as_of".format(note["id"]))

    settings = data.get("settings", {})
    if not isinstance(settings, dict):
        raise ValidationError("settings must be an object")
    resolved = {
        "top_k": overrides["top_k"]
        if overrides.get("top_k") is not None
        else settings.get("top_k", 5),
        "per_community_cap": overrides["per_community_cap"]
        if overrides.get("per_community_cap") is not None
        else settings.get("per_community_cap", 2),
        "min_communities": overrides["min_communities"]
        if overrides.get("min_communities") is not None
        else settings.get("min_communities", 3),
    }
    for key in tuple(resolved):
        resolved[key] = _positive_int(resolved[key], "settings.{}".format(key))
    resolved["top_k"] = min(resolved["top_k"], len(parsed_notes))

    redundancy_weight = _number(settings.get("redundancy_weight", 0.08), "settings.redundancy_weight")
    if not 0.0 <= redundancy_weight <= 1.0:
        raise ValidationError("settings.redundancy_weight must be between 0 and 1")
    resolved["redundancy_weight"] = redundancy_weight

    raw_weights = settings.get("weights", DEFAULT_WEIGHTS)
    if not isinstance(raw_weights, dict):
        raise ValidationError("settings.weights must be an object")
    unknown = set(raw_weights) - set(DEFAULT_WEIGHTS)
    if unknown:
        raise ValidationError("unknown weight keys: {}".format(", ".join(sorted(unknown))))
    weights = {}
    for key in DEFAULT_WEIGHTS:
        value = _number(raw_weights.get(key, DEFAULT_WEIGHTS[key]), "settings.weights.{}".format(key))
        if value < 0:
            raise ValidationError("settings.weights.{} must be non-negative".format(key))
        weights[key] = value
    total_weight = sum(weights.values())
    if total_weight <= 0:
        raise ValidationError("settings.weights must have a positive total")
    weights = {key: value / total_weight for key, value in weights.items()}

    query_tokens = _tokens(query)
    for note in parsed_notes:
        note_tokens = _tokens(note["title"] + " " + note["text"])
        semantic = note["_semantic_score"]
        if semantic is None:
            semantic = (
                0.0
                if not query_tokens or not note_tokens
                else len(query_tokens & note_tokens)
                / math.sqrt(len(query_tokens) * len(note_tokens))
            )
        degree = len(neighbor_sets.get(note["id"], set()))
        age_days = (as_of - note["_updated_date"]).days
        components = {
            "semantic_relevance": semantic,
            "inverse_degree": 1.0 / math.log2(degree + 2),
            "recency": 1.0 / (1.0 + age_days / 365.0),
            "source_completeness": min(1.0, len(note["sources"]) / 2.0),
            "metadata_quality": sum(
                (
                    bool(note["title"]),
                    bool(note["text"]),
                    bool(note["updated_at"]),
                    bool(note["community"]),
                    bool(note["sources"]),
                    bool(note["tags"]),
                )
            )
            / 6.0,
        }
        note["_tokens"] = note_tokens
        note["_degree"] = degree
        note["_components"] = components
        note["_base_score"] = sum(weights[key] * components[key] for key in weights)

    return query.strip(), as_of, parsed_notes, resolved, weights


def _candidate_choice(candidates, selected, redundancy_weight):
    """Choose the best candidate after applying similarity to selected notes."""
    scored = []
    for note in candidates:
        similarity = max(
            (_similarity(note["_tokens"], item["note"]["_tokens"]) for item in selected),
            default=0.0,
        )
        penalty = redundancy_weight * similarity
        scored.append((note["_base_score"] - penalty, note["id"], penalty, note))
    scored.sort(key=lambda item: (-item[0], item[1]))
    adjusted, _, penalty, note = scored[0]
    return note, adjusted, penalty


def _public_candidate(note, score, penalty, weights, rationale, rank=None):
    """Convert an internal candidate to the documented public result shape."""
    components = {key: _round(value) for key, value in note["_components"].items()}
    components["redundancy_penalty"] = _round(penalty)
    contributions = {
        key: _round(weights[key] * note["_components"][key]) for key in weights
    }
    contributions["redundancy_penalty"] = _round(-penalty)
    result = {
        "id": note["id"],
        "title": note["title"],
        "community": note["community"],
        "updated_at": note["updated_at"],
        "degree": note["_degree"],
        "score": _round(score),
        "score_components": components,
        "weighted_contributions": contributions,
        "provenance": copy.deepcopy(note["sources"]),
        "rationale": rationale,
    }
    if rank is not None:
        result = {"rank": rank, **result}
    return result


def _metrics(selected_notes, all_notes, as_of, hub_threshold):
    """Calculate comparison metrics for a selected candidate list."""
    if not selected_notes:
        return {
            "community_count": 0,
            "community_coverage": 0.0,
            "hub_concentration": 0.0,
            "average_degree": 0.0,
            "average_freshness": 0.0,
            "provenance_coverage": 0.0,
        }
    community_total = len({note["community"] for note in all_notes})
    communities = len({note["community"] for note in selected_notes})
    return {
        "community_count": communities,
        "community_coverage": _round(communities / community_total),
        "hub_concentration": _round(
            sum(note["_degree"] > hub_threshold for note in selected_notes) / len(selected_notes)
        ),
        "average_degree": _round(
            sum(note["_degree"] for note in selected_notes) / len(selected_notes)
        ),
        "average_freshness": _round(
            sum(note["_components"]["recency"] for note in selected_notes)
            / len(selected_notes)
        ),
        "provenance_coverage": _round(
            sum(bool(note["sources"]) for note in selected_notes) / len(selected_notes)
        ),
    }


def rerank_evidence(data, top_k=None, per_community_cap=None, min_communities=None):
    """Validate input and return a deterministic, diversity-aware evidence pack."""
    overrides = {
        "top_k": top_k,
        "per_community_cap": per_community_cap,
        "min_communities": min_communities,
    }
    query, as_of, notes, settings, weights = _validate_and_prepare(data, overrides)
    selected = []
    remaining = list(notes)
    community_counts = Counter()
    available_communities = {note["community"] for note in notes}
    coverage_target = min(
        settings["top_k"], settings["min_communities"], len(available_communities)
    )

    while len({item["note"]["community"] for item in selected}) < coverage_target:
        seen_communities = {item["note"]["community"] for item in selected}
        eligible = [
            note
            for note in remaining
            if note["community"] not in seen_communities
            and community_counts[note["community"]] < settings["per_community_cap"]
        ]
        if not eligible:
            break
        note, adjusted, penalty = _candidate_choice(
            eligible, selected, settings["redundancy_weight"]
        )
        selected.append(
            {"note": note, "score": adjusted, "penalty": penalty, "phase": "community coverage"}
        )
        remaining.remove(note)
        community_counts[note["community"]] += 1

    while len(selected) < settings["top_k"]:
        eligible = [
            note
            for note in remaining
            if community_counts[note["community"]] < settings["per_community_cap"]
        ]
        if not eligible:
            break
        note, adjusted, penalty = _candidate_choice(
            eligible, selected, settings["redundancy_weight"]
        )
        selected.append(
            {"note": note, "score": adjusted, "penalty": penalty, "phase": "score fill"}
        )
        remaining.remove(note)
        community_counts[note["community"]] += 1

    public_results = []
    for rank, item in enumerate(selected, start=1):
        note = item["note"]
        rationale = (
            "Selected during {}; base={:.6f}; redundancy_penalty={:.6f}; "
            "degree={}; community={}."
        ).format(
            item["phase"], note["_base_score"], item["penalty"], note["_degree"], note["community"]
        )
        public_results.append(
            _public_candidate(
                note, item["score"], item["penalty"], weights, rationale, rank=rank
            )
        )

    public_excluded = []
    for note in sorted(remaining, key=lambda item: item["id"]):
        penalty = settings["redundancy_weight"] * max(
            (_similarity(note["_tokens"], item["note"]["_tokens"]) for item in selected),
            default=0.0,
        )
        score = note["_base_score"] - penalty
        if community_counts[note["community"]] >= settings["per_community_cap"]:
            reason = "community cap {} reached".format(settings["per_community_cap"])
        else:
            reason = "below the top-k adjusted-score cutoff"
        rationale = "Excluded: {}; base={:.6f}; redundancy_penalty={:.6f}.".format(
            reason, note["_base_score"], penalty
        )
        public_excluded.append(
            _public_candidate(note, score, penalty, weights, rationale)
        )

    baseline = sorted(notes, key=lambda note: (-note["_components"]["semantic_relevance"], note["id"]))[
        : settings["top_k"]
    ]
    selected_notes = [item["note"] for item in selected]
    degrees = [note["_degree"] for note in notes]
    hub_threshold = statistics.mean(degrees) + statistics.pstdev(degrees)
    baseline_metrics = _metrics(baseline, notes, as_of, hub_threshold)
    reranked_metrics = _metrics(selected_notes, notes, as_of, hub_threshold)
    delta = {}
    for key in baseline_metrics:
        value = reranked_metrics[key] - baseline_metrics[key]
        delta[key] = int(value) if key == "community_count" else _round(value)

    return {
        "query": query,
        "as_of": as_of.isoformat(),
        "configuration": {
            "top_k": settings["top_k"],
            "per_community_cap": settings["per_community_cap"],
            "min_communities": settings["min_communities"],
            "effective_min_communities": coverage_target,
            "redundancy_weight": _round(settings["redundancy_weight"]),
            "weights": {key: _round(value) for key, value in weights.items()},
        },
        "summary": {
            "candidate_count": len(notes),
            "selected_count": len(selected),
            "excluded_count": len(remaining),
        },
        "baseline_comparison": {
            "baseline_policy": "semantic relevance descending, note ID tie-break",
            "hub_degree_threshold": _round(hub_threshold),
            "baseline": {
                "selected_ids": [note["id"] for note in baseline],
                "metrics": baseline_metrics,
            },
            "parallaxpack": {
                "selected_ids": [note["id"] for note in selected_notes],
                "metrics": reranked_metrics,
            },
            "delta": delta,
        },
        "results": public_results,
        "excluded": public_excluded,
    }


def render_markdown(pack):
    """Render an evidence-pack JSON object as deterministic Markdown."""
    baseline = pack["baseline_comparison"]["baseline"]["metrics"]
    reranked = pack["baseline_comparison"]["parallaxpack"]["metrics"]
    lines = [
        "# ParallaxPack Evidence Pack",
        "",
        "**Query:** {}".format(pack["query"]),
        "",
        "**As of:** {}".format(pack["as_of"]),
        "",
        "## Baseline comparison",
        "",
        "| Policy | Communities | Hub concentration | Freshness | Provenance |",
        "|---|---:|---:|---:|---:|",
        "| Semantic baseline | {} | {:.6f} | {:.6f} | {:.6f} |".format(
            baseline["community_count"],
            baseline["hub_concentration"],
            baseline["average_freshness"],
            baseline["provenance_coverage"],
        ),
        "| ParallaxPack | {} | {:.6f} | {:.6f} | {:.6f} |".format(
            reranked["community_count"],
            reranked["hub_concentration"],
            reranked["average_freshness"],
            reranked["provenance_coverage"],
        ),
        "",
        "## Selected evidence",
        "",
        "| Rank | ID | Community | Score | Degree | Updated |",
        "|---:|---|---|---:|---:|---|",
    ]
    for result in pack["results"]:
        lines.append(
            "| {rank} | `{id}` | {community} | {score:.6f} | {degree} | {updated_at} |".format(
                **result
            )
        )
    for result in pack["results"]:
        lines.extend(
            [
                "",
                "### {}. {}".format(result["rank"], result["title"]),
                "",
                result["rationale"],
                "",
                "- Components: `semantic={semantic_relevance:.6f}`, `inverse_degree={inverse_degree:.6f}`, "
                "`recency={recency:.6f}`, `sources={source_completeness:.6f}`, "
                "`metadata={metadata_quality:.6f}`, `redundancy={redundancy_penalty:.6f}`".format(
                    **result["score_components"]
                ),
            ]
        )
        if result["provenance"]:
            lines.append(
                "- Provenance: "
                + "; ".join(
                    "[{}]({})".format(source["title"], source["uri"])
                    for source in result["provenance"]
                )
            )
        else:
            lines.append("- Provenance: none supplied")

    lines.extend(["", "## Excluded candidates", ""])
    if pack["excluded"]:
        for item in pack["excluded"]:
            lines.append("- `{}`: {}".format(item["id"], item["rationale"]))
    else:
        lines.append("No candidates were excluded.")
    return "\n".join(lines) + "\n"


def _render_output(pack, output_format):
    """Serialize a pack in the requested public output format."""
    if output_format == "json":
        return json.dumps(pack, indent=2, ensure_ascii=False) + "\n"
    if output_format == "markdown":
        return render_markdown(pack)
    envelope = {"evidence_pack": pack, "markdown": render_markdown(pack)}
    return json.dumps(envelope, indent=2, ensure_ascii=False) + "\n"


def _write_or_print(content, output_path, force):
    """Print to stdout or explicitly write a non-existing/forced output file."""
    if output_path is None:
        sys.stdout.write(content)
        return
    path = Path(output_path)
    if not path.parent.exists():
        raise ValidationError("output directory does not exist: {}".format(path.parent))
    if path.exists() and not force:
        raise ValidationError("output file exists; use --force to overwrite: {}".format(path))
    try:
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise ValidationError("could not write output: {}".format(exc)) from exc


def build_parser():
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Rerank graph candidates into a hub-resistant evidence pack."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", help="Path to an input JSON file")
    source.add_argument(
        "--selftest", action="store_true", help="Run the built-in offline deterministic sample"
    )
    parser.add_argument(
        "--format",
        default=os.environ.get("PARALLAXPACK_DEFAULT_FORMAT", "json"),
        help="Output format: json, markdown, or both (default: json)",
    )
    parser.add_argument("--output", help="Write output to this file instead of stdout")
    parser.add_argument(
        "--force", action="store_true", help="Allow --output to overwrite an existing file"
    )
    parser.add_argument("--top-k", type=int, help="Override the number of selected notes")
    parser.add_argument(
        "--per-community-cap", type=int, help="Override the maximum notes per community"
    )
    parser.add_argument(
        "--min-communities", type=int, help="Override the minimum community coverage target"
    )
    return parser


def main(argv=None):
    """Run the CLI and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.format not in ("json", "markdown", "both"):
            raise ValidationError("--format must be json, markdown, or both")
        env_top_k = os.environ.get("PARALLAXPACK_TOP_K")
        top_k = args.top_k
        if top_k is None and env_top_k is not None:
            try:
                top_k = int(env_top_k)
            except ValueError as exc:
                raise ValidationError("PARALLAXPACK_TOP_K must be a positive integer") from exc

        if args.selftest:
            data = copy.deepcopy(SAMPLE_INPUT)
        else:
            try:
                with open(args.input, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
            except FileNotFoundError as exc:
                raise ValidationError("input file not found: {}".format(args.input)) from exc
            except json.JSONDecodeError as exc:
                raise ValidationError(
                    "invalid JSON in {} at line {} column {}".format(
                        args.input, exc.lineno, exc.colno
                    )
                ) from exc
            except OSError as exc:
                raise ValidationError("could not read input: {}".format(exc)) from exc

        pack = rerank_evidence(
            data,
            top_k=top_k,
            per_community_cap=args.per_community_cap,
            min_communities=args.min_communities,
        )
        if args.selftest:
            if pack["summary"]["selected_count"] != 4:
                raise ValidationError("selftest invariant failed: selected_count")
            if pack["baseline_comparison"]["parallaxpack"]["metrics"]["community_count"] < 3:
                raise ValidationError("selftest invariant failed: community coverage")
        _write_or_print(_render_output(pack, args.format), args.output, args.force)
        return 0
    except ValidationError as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
