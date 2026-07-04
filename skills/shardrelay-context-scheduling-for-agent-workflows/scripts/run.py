#!/usr/bin/env python3
"""ShardRelay reference CLI for deterministic context scheduling.

The script turns a workflow DAG and a directory of memory shards into
stage-specific Markdown context packs plus an audit manifest. It is small by
design and uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple


VERSION = "0.1.0"
DEFAULT_BUDGET = 120
DEFAULT_SOFT_LIMIT_RATIO = 0.85
SUPPORTED_EXTENSIONS = {".md", ".txt"}
WORD_RE = re.compile(r"[A-Za-z0-9_]+|[^\w\s]", re.UNICODE)
STOPWORDS = {
    "and",
    "are",
    "but",
    "each",
    "for",
    "from",
    "has",
    "into",
    "not",
    "the",
    "that",
    "this",
    "use",
    "with",
}


@dataclass(frozen=True)
class Shard:
    """A durable memory fragment that can be scheduled into a context pack."""

    id: str
    title: str
    content: str
    source_type: str = "note"
    priority: int = 1
    created_at: str = ""
    tags: Tuple[str, ...] = field(default_factory=tuple)
    path: str = ""
    recency_score: float = 0.0


@dataclass(frozen=True)
class Stage:
    """A workflow stage that receives a bounded context pack."""

    id: str
    title: str
    task: str
    depends_on: Tuple[str, ...] = field(default_factory=tuple)
    budget: int | None = None
    priority_terms: Tuple[str, ...] = field(default_factory=tuple)
    required_shards: Tuple[str, ...] = field(default_factory=tuple)


def approx_token_count(text: str) -> int:
    """Return a deterministic estimated token count for text."""

    if not text:
        return 0
    return len(WORD_RE.findall(text))


def normalize_terms(text: str) -> Tuple[str, ...]:
    """Normalize text into lowercase terms for transparent scoring."""

    return tuple(
        term.lower()
        for term in re.findall(r"[A-Za-z0-9_]+", text)
        if len(term) > 2 and term.lower() not in STOPWORDS
    )


def parse_simple_frontmatter(raw: str) -> Tuple[Dict[str, str], str]:
    """Parse a minimal Markdown frontmatter block and return metadata plus body."""

    if not raw.startswith("---\n"):
        return {}, raw
    end = raw.find("\n---\n", 4)
    if end == -1:
        return {}, raw
    meta_block = raw[4:end]
    body = raw[end + 5 :]
    meta: Dict[str, str] = {}
    for line in meta_block.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip().lower()] = value.strip().strip('"').strip("'")
    return meta, body


def parse_tags(value: str) -> Tuple[str, ...]:
    """Parse a frontmatter tag value from comma or bracket notation."""

    cleaned = value.strip()
    if cleaned.startswith("[") and cleaned.endswith("]"):
        cleaned = cleaned[1:-1]
    tags = [part.strip().strip('"').strip("'").lower() for part in cleaned.split(",")]
    return tuple(tag for tag in tags if tag)


def parse_priority(value: str, fallback: int = 1) -> int:
    """Parse a shard priority and clamp it to a small deterministic range."""

    try:
        return max(0, min(10, int(value)))
    except (TypeError, ValueError):
        return fallback


def infer_title(body: str, fallback: str) -> str:
    """Infer a readable title from the first non-empty content line."""

    for line in body.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped.lstrip("#").strip() or fallback
    return fallback


def parse_shard_file(path: Path) -> Shard:
    """Read one shard file and convert it into a Shard."""

    raw = path.read_text(encoding="utf-8")
    meta, body = parse_simple_frontmatter(raw)
    shard_id = meta.get("id") or path.stem
    title = meta.get("title") or infer_title(body, path.stem.replace("_", " ").title())
    return Shard(
        id=shard_id,
        title=title,
        content=body.strip(),
        source_type=(meta.get("source_type") or "note").lower(),
        priority=parse_priority(meta.get("priority", "1")),
        created_at=meta.get("created_at", ""),
        tags=parse_tags(meta.get("tags", "")),
        path=str(path.as_posix()),
    )


def parse_iso_date(value: str) -> date | None:
    """Parse an ISO date string, returning None when it is absent or invalid."""

    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def attach_recency_scores(shards: Sequence[Shard]) -> List[Shard]:
    """Assign a normalized 0..3 recency score to shards with valid dates."""

    parsed = [(shard, parse_iso_date(shard.created_at)) for shard in shards]
    valid_ordinals = [dt.toordinal() for _, dt in parsed if dt is not None]
    if not valid_ordinals:
        return list(shards)
    oldest = min(valid_ordinals)
    newest = max(valid_ordinals)
    span = max(1, newest - oldest)
    scored: List[Shard] = []
    for shard, dt in parsed:
        recency_score = 0.0
        if dt is not None:
            recency_score = round(((dt.toordinal() - oldest) / span) * 3.0, 2)
        scored.append(
            Shard(
                id=shard.id,
                title=shard.title,
                content=shard.content,
                source_type=shard.source_type,
                priority=shard.priority,
                created_at=shard.created_at,
                tags=shard.tags,
                path=shard.path,
                recency_score=recency_score,
            )
        )
    return scored


def index_memory_shards(memory_dir: Path) -> List[Shard]:
    """Index supported shard files from a memory directory."""

    if not memory_dir.exists():
        raise ValueError(f"memory directory does not exist: {memory_dir}")
    if not memory_dir.is_dir():
        raise ValueError(f"memory path is not a directory: {memory_dir}")

    paths = sorted(
        path
        for path in memory_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    if not paths:
        raise ValueError(f"no .md or .txt memory shards found in: {memory_dir}")

    shards = attach_recency_scores([parse_shard_file(path) for path in paths])
    seen: set[str] = set()
    duplicates: set[str] = set()
    for shard in shards:
        if shard.id in seen:
            duplicates.add(shard.id)
        seen.add(shard.id)
    if duplicates:
        names = ", ".join(sorted(duplicates))
        raise ValueError(f"duplicate shard id(s): {names}")
    return shards


def load_workflow(path: Path) -> List[Stage]:
    """Load and validate stages from a workflow JSON file."""

    if not path.exists():
        raise ValueError(f"workflow file does not exist: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"workflow file is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("stages"), list):
        raise ValueError("workflow JSON must be an object with a 'stages' array")

    stages: List[Stage] = []
    seen: set[str] = set()
    for item in payload["stages"]:
        if not isinstance(item, dict):
            raise ValueError("each workflow stage must be an object")
        stage_id = str(item.get("id") or "").strip()
        if not stage_id:
            raise ValueError("each workflow stage requires a non-empty 'id'")
        if stage_id in seen:
            raise ValueError(f"duplicate stage id: {stage_id}")
        seen.add(stage_id)
        depends_on = tuple(str(dep) for dep in item.get("depends_on", []) or [])
        priority_terms = tuple(str(term) for term in item.get("priority_terms", []) or [])
        required_shards = tuple(str(shard) for shard in item.get("required_shards", []) or [])
        budget = item.get("budget")
        parsed_budget = int(budget) if budget is not None else None
        if parsed_budget is not None and parsed_budget <= 0:
            raise ValueError(f"stage {stage_id} has non-positive budget")
        stages.append(
            Stage(
                id=stage_id,
                title=str(item.get("title") or stage_id),
                task=str(item.get("task") or ""),
                depends_on=depends_on,
                budget=parsed_budget,
                priority_terms=priority_terms,
                required_shards=required_shards,
            )
        )
    return topological_order(stages)


def topological_order(stages: Sequence[Stage]) -> List[Stage]:
    """Return stages in dependency-safe order while preserving input order."""

    stage_by_id = {stage.id: stage for stage in stages}
    for stage in stages:
        missing = [dep for dep in stage.depends_on if dep not in stage_by_id]
        if missing:
            raise ValueError(f"stage {stage.id} depends on unknown stage(s): {', '.join(missing)}")

    ordered: List[Stage] = []
    temporary: set[str] = set()
    permanent: set[str] = set()

    def visit(stage: Stage) -> None:
        if stage.id in permanent:
            return
        if stage.id in temporary:
            raise ValueError(f"workflow contains a dependency cycle at stage: {stage.id}")
        temporary.add(stage.id)
        for dep_id in stage.depends_on:
            visit(stage_by_id[dep_id])
        temporary.remove(stage.id)
        permanent.add(stage.id)
        ordered.append(stage)

    for stage in stages:
        visit(stage)
    return ordered


def source_type_weight(source_type: str) -> float:
    """Return a small deterministic weight for source type usefulness."""

    weights = {
        "brief": 4.0,
        "summary": 4.0,
        "spec": 3.0,
        "decision": 3.0,
        "output": 2.5,
        "log": 2.0,
        "note": 1.5,
    }
    return weights.get(source_type.lower(), 1.0)


def stage_terms(stage: Stage) -> set[str]:
    """Return normalized terms describing a stage."""

    joined = " ".join([stage.id, stage.title, stage.task, *stage.priority_terms])
    return set(normalize_terms(joined))


def shard_terms(shard: Shard) -> set[str]:
    """Return normalized terms describing a shard."""

    joined = " ".join([shard.id, shard.title, shard.source_type, *shard.tags, shard.content])
    return set(normalize_terms(joined))


def render_shard_block(shard: Shard, reasons: Sequence[str] | None = None) -> str:
    """Render one shard as a Markdown block for a context pack."""

    reason_text = "; ".join(reasons or [])
    lines = [
        f"### {shard.id} - {shard.title}",
        f"Source: {shard.source_type}; priority: {shard.priority}; created_at: {shard.created_at or 'unknown'}",
    ]
    if shard.tags:
        lines.append(f"Tags: {', '.join(shard.tags)}")
    if reason_text:
        lines.append(f"Included because: {reason_text}")
    lines.extend(["", shard.content.strip(), ""])
    return "\n".join(lines)


def render_context_header(stage: Stage, budget: int) -> str:
    """Render the fixed Markdown header for a stage context pack."""

    dependencies = ", ".join(stage.depends_on) if stage.depends_on else "none"
    return "\n".join(
        [
            f"# Context Pack: {stage.id} - {stage.title}",
            "",
            f"Task: {stage.task}",
            f"Depends on: {dependencies}",
            f"Budget: {budget} estimated tokens",
            "",
            "## Scheduled Memory Shards",
            "",
        ]
    )


def score_shard(
    stage: Stage,
    shard: Shard,
    dependency_shard_ids: Iterable[str],
) -> Tuple[float, List[str]]:
    """Score a shard for a stage and explain the score."""

    dependency_set = set(dependency_shard_ids)
    terms = stage_terms(stage)
    shard_term_set = shard_terms(shard)
    matches = sorted(terms.intersection(shard_term_set))
    tag_matches = sorted(terms.intersection(set(shard.tags)))
    required = shard.id in set(stage.required_shards)

    score = 0.0
    reasons: List[str] = []
    if required:
        score += 50.0
        reasons.append("explicitly required")
    if matches:
        score += len(matches) * 4.0
        reasons.append("matches: " + ", ".join(matches[:6]))
    if tag_matches:
        score += len(tag_matches) * 3.0
    if shard.id in dependency_set:
        score += 6.0
        reasons.append("dependency continuity")
    priority_score = shard.priority * 3.0
    score += priority_score
    if shard.priority >= 4:
        reasons.append(f"high priority: {shard.priority}")
    source_score = source_type_weight(shard.source_type)
    score += source_score
    if source_score >= 3.0:
        reasons.append(f"source type: {shard.source_type}")
    if shard.recency_score:
        score += shard.recency_score
        if shard.recency_score >= 2.0:
            reasons.append("recent shard")
    if not reasons:
        reasons.append("low relevance fallback")
    return round(score, 2), reasons


def select_shards_for_stage(
    stage: Stage,
    shards: Sequence[Shard],
    dependency_shard_ids: Iterable[str],
    default_budget: int,
    soft_limit_ratio: float,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int, int]:
    """Select shards for a stage without exceeding the hard budget."""

    budget = stage.budget or default_budget
    if budget <= 0:
        raise ValueError(f"stage {stage.id} has non-positive effective budget")
    header_tokens = approx_token_count(render_context_header(stage, budget))
    hard_available = max(0, budget - header_tokens)
    soft_limit = max(0, math.floor(budget * soft_limit_ratio))
    soft_available = max(0, soft_limit - header_tokens)

    candidates: List[Dict[str, Any]] = []
    for shard in shards:
        score, reasons = score_shard(stage, shard, dependency_shard_ids)
        block_tokens = approx_token_count(render_shard_block(shard, reasons))
        candidates.append(
            {
                "shard": shard,
                "score": score,
                "estimated_tokens": block_tokens,
                "reasons": reasons,
            }
        )
    candidates.sort(key=lambda item: (-item["score"], item["estimated_tokens"], item["shard"].id))

    selected: List[Dict[str, Any]] = []
    omitted: List[Dict[str, Any]] = []
    used_tokens = header_tokens
    required_ids = set(stage.required_shards)

    for candidate in candidates:
        shard = candidate["shard"]
        candidate_tokens = candidate["estimated_tokens"]
        would_use = used_tokens + candidate_tokens
        is_required = shard.id in required_ids
        fits_hard = would_use <= budget
        fits_soft = would_use <= soft_limit
        should_take = fits_hard and (fits_soft or is_required or not selected)
        if should_take:
            selected.append(candidate)
            used_tokens = would_use
        else:
            reason = "over hard limit" if not fits_hard else "below selected candidates or over soft limit"
            omitted.append(
                {
                    "id": shard.id,
                    "score": candidate["score"],
                    "estimated_tokens": candidate_tokens,
                    "reason": reason,
                }
            )

    selected_manifest = [
        {
            "id": item["shard"].id,
            "title": item["shard"].title,
            "score": item["score"],
            "estimated_tokens": item["estimated_tokens"],
            "reasons": item["reasons"],
        }
        for item in selected
    ]
    return selected_manifest, omitted, used_tokens, soft_limit


def render_context(stage: Stage, selected: Sequence[Dict[str, Any]], shard_by_id: Dict[str, Shard], budget: int) -> str:
    """Render a full stage context pack as Markdown."""

    parts = [render_context_header(stage, budget)]
    for item in selected:
        shard = shard_by_id[item["id"]]
        parts.append(render_shard_block(shard, item["reasons"]))
    if not selected:
        parts.append("_No shards fit this stage budget._\n")
    return "\n".join(parts).rstrip() + "\n"


def schedule_contexts(
    stages: Sequence[Stage],
    shards: Sequence[Shard],
    default_budget: int = DEFAULT_BUDGET,
    soft_limit_ratio: float = DEFAULT_SOFT_LIMIT_RATIO,
) -> Dict[str, Any]:
    """Schedule memory shards into context packs for every stage."""

    if not 0 < soft_limit_ratio <= 1:
        raise ValueError("soft limit ratio must be greater than 0 and less than or equal to 1")
    if default_budget <= 0:
        raise ValueError("default budget must be positive")

    shard_by_id = {shard.id: shard for shard in shards}
    dependency_selected: Dict[str, List[str]] = {}
    manifest_stages: List[Dict[str, Any]] = []
    contexts: Dict[str, str] = {}

    for stage in stages:
        dependency_shard_ids: List[str] = []
        for dep_id in stage.depends_on:
            dependency_shard_ids.extend(dependency_selected.get(dep_id, []))
        selected, omitted, estimated_tokens, soft_limit = select_shards_for_stage(
            stage,
            shards,
            dependency_shard_ids,
            default_budget,
            soft_limit_ratio,
        )
        budget = stage.budget or default_budget
        output_file = f"{stage.id}_context.md"
        contexts[output_file] = render_context(stage, selected, shard_by_id, budget)
        selected_ids = [item["id"] for item in selected]
        dependency_selected[stage.id] = selected_ids
        manifest_stages.append(
            {
                "id": stage.id,
                "title": stage.title,
                "depends_on": list(stage.depends_on),
                "budget": budget,
                "soft_limit": soft_limit,
                "estimated_tokens": estimated_tokens,
                "output_file": output_file,
                "selected_shards": selected,
                "omitted_shards": omitted,
            }
        )

    return {
        "tool": "ShardRelay",
        "version": VERSION,
        "default_budget": default_budget,
        "soft_limit_ratio": soft_limit_ratio,
        "stages": manifest_stages,
        "contexts": contexts,
    }


def write_outputs(result: Dict[str, Any], out_dir: Path) -> None:
    """Write context packs and a manifest to an output directory."""

    out_dir.mkdir(parents=True, exist_ok=True)
    contexts = result.get("contexts", {})
    for filename, content in contexts.items():
        (out_dir / filename).write_text(content, encoding="utf-8")
    manifest = {key: value for key, value in result.items() if key != "contexts"}
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def sample_stages() -> List[Stage]:
    """Return built-in sample stages used by self-test and unit tests."""

    return topological_order(
        [
            Stage(
                id="stage_001",
                title="Plan shard index",
                task="Plan a workflow DAG parser and memory shard index for context scheduling.",
                budget=230,
                priority_terms=("workflow", "dag", "shard"),
                required_shards=("project_brief",),
            ),
            Stage(
                id="stage_002",
                title="Emit review handoff",
                task="Create deterministic manifest output and handoff context for the next agent.",
                depends_on=("stage_001",),
                budget=230,
                priority_terms=("manifest", "handoff", "deterministic"),
            ),
        ]
    )


def sample_shards() -> List[Shard]:
    """Return built-in sample shards used by self-test and unit tests."""

    shards = [
        Shard(
            id="project_brief",
            title="Project brief",
            content=(
                "ShardRelay builds context bundles from memory shards for each workflow stage. "
                "It preserves dependency handoffs and token budgets."
            ),
            source_type="brief",
            priority=5,
            created_at="2026-01-01",
            tags=("shardrelay", "context", "workflow"),
        ),
        Shard(
            id="dag_notes",
            title="DAG notes",
            content=(
                "Workflow input is a DAG. Each stage has an id, task, dependencies, budget, "
                "priority terms, and required shards."
            ),
            source_type="note",
            priority=4,
            created_at="2026-01-02",
            tags=("dag", "workflow", "json"),
        ),
        Shard(
            id="handoff_log",
            title="Handoff log",
            content=(
                "Prior agent output defined manifest fields for selected shards, estimated tokens, "
                "inclusion reasons, output files, and deterministic review handoff."
            ),
            source_type="log",
            priority=4,
            created_at="2026-01-03",
            tags=("manifest", "handoff", "deterministic"),
        ),
        Shard(
            id="unrelated_note",
            title="Unrelated note",
            content="Billing notes and launch calendar details that do not affect context scheduling.",
            source_type="note",
            priority=1,
            created_at="2025-12-15",
            tags=("billing",),
        ),
    ]
    return attach_recency_scores(shards)


def summarize_for_stdout(result: Dict[str, Any], selftest: bool = False) -> Dict[str, Any]:
    """Create a compact deterministic summary for command-line output."""

    summary: Dict[str, Any] = {}
    if selftest:
        summary["selftest"] = "passed"
    summary["stages"] = [
        {
            "id": stage["id"],
            "selected_shards": [item["id"] for item in stage["selected_shards"]],
        }
        for stage in result["stages"]
    ]
    return summary


def run_selftest() -> Dict[str, Any]:
    """Run a no-network self-test on built-in sample data."""

    result = schedule_contexts(sample_stages(), sample_shards())
    expected = [
        {"id": "stage_001", "selected_shards": ["project_brief", "dag_notes"]},
        {"id": "stage_002", "selected_shards": ["handoff_log", "project_brief"]},
    ]
    actual = summarize_for_stdout(result)["stages"]
    if actual != expected:
        raise AssertionError(f"selftest selection mismatch: expected {expected}, got {actual}")
    return result


def env_int(name: str, default: int) -> int:
    """Read a positive integer from an environment variable."""

    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def env_float(name: str, default: float) -> float:
    """Read a bounded float from an environment variable."""

    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc
    if not 0 < value <= 1:
        raise ValueError(f"{name} must be greater than 0 and less than or equal to 1")
    return value


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description="ShardRelay context scheduler for agent workflow stages.",
    )
    parser.add_argument("--workflow", type=Path, help="Path to workflow JSON input.")
    parser.add_argument("--memory-dir", type=Path, help="Directory containing .md or .txt memory shards.")
    parser.add_argument("--out-dir", type=Path, default=Path("shardrelay_out"), help="Output directory.")
    parser.add_argument(
        "--budget",
        type=int,
        default=None,
        help="Default estimated-token hard budget per stage. Overrides SHARDRELAY_DEFAULT_BUDGET.",
    )
    parser.add_argument(
        "--soft-ratio",
        type=float,
        default=None,
        help="Soft packing ratio in the range (0, 1]. Overrides SHARDRELAY_SOFT_LIMIT_RATIO.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run built-in sample data without API keys or external files.",
    )
    parser.add_argument(
        "--print-manifest",
        action="store_true",
        help="Print the full manifest JSON instead of the compact summary.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the ShardRelay CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        default_budget = args.budget or env_int("SHARDRELAY_DEFAULT_BUDGET", DEFAULT_BUDGET)
        soft_ratio = args.soft_ratio or env_float("SHARDRELAY_SOFT_LIMIT_RATIO", DEFAULT_SOFT_LIMIT_RATIO)
        if not 0 < soft_ratio <= 1:
            raise ValueError("--soft-ratio must be greater than 0 and less than or equal to 1")
        if default_budget <= 0:
            raise ValueError("--budget must be positive")

        if args.selftest or (args.workflow is None and args.memory_dir is None):
            result = run_selftest()
            output = (
                {key: value for key, value in result.items() if key != "contexts"}
                if args.print_manifest
                else summarize_for_stdout(result, selftest=True)
            )
            print(json.dumps(output, indent=2))
            return 0

        if args.workflow is None or args.memory_dir is None:
            parser.error("--workflow and --memory-dir must be provided together, or use --selftest")

        stages = load_workflow(args.workflow)
        shards = index_memory_shards(args.memory_dir)
        result = schedule_contexts(stages, shards, default_budget=default_budget, soft_limit_ratio=soft_ratio)
        write_outputs(result, args.out_dir)
        output = (
            {key: value for key, value in result.items() if key != "contexts"}
            if args.print_manifest
            else summarize_for_stdout(result)
        )
        print(json.dumps(output, indent=2))
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
