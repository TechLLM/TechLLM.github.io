#!/usr/bin/env python3
"""Build hub-aware, budgeted context bundles from Markdown notes.

This module implements a small, deterministic reference version of
ContextTrellis. It parses Obsidian-style Markdown notes, builds a simple link
graph, compresses central hub notes, preserves execution-heavy long-tail notes,
and emits an auditable JSON or Markdown bundle.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


BUNDLE_VERSION = "0.1"

SAMPLE_VAULT: Dict[str, str] = {
    "Architecture.md": """---
title: Architecture Hub
tags: [architecture, index]
---
# Architecture Hub

ContextTrellis builds prompt bundles from [[API Polling]], [[CLI Commands]], and [[Dry Run Log]].
It explains why hub notes should orient the model without using the entire context budget.
See [Error Handling](Error Handling.md) for failure behavior.
""",
    "API Polling.md": """# API Polling

Tags: #api #execution

Use this when a job returns `queued` or `running`.
Poll `GET /v1/jobs/{job_id}` every 5 seconds until status becomes `succeeded` or `failed`.
Do not poll faster than once per second.

```bash
curl -s "$BASE_URL/v1/jobs/$JOB_ID"
```

If the API returns 429, wait 30 seconds before retrying.
""",
    "CLI Commands.md": """# CLI Commands

Tags: #cli #execution

Run the compressor locally before calling an LLM:

```bash
python scripts/run.py --input examples/vault --budget 620 --reserve 80
```

Use `--format markdown` only when the next step expects plain prompt text.
""",
    "Dry Run Log.md": """# Dry Run Log

Tags: #dry-run #execution

Dry run observed that the hub note was initially selected first and consumed too much budget.
After hub compression, the API polling note and CLI command note both fit.
Status transition: planned -> packed -> verified.
""",
    "Error Handling.md": """# Error Handling

Tags: #errors #execution

If a note cannot be read, report the path and continue with other readable Markdown files.
If the available budget is zero or negative, exit with a clear error.
For transient command failures, retry once after checking the exact error message.
""",
}


@dataclass(frozen=True)
class Note:
    """Parsed Markdown note with graph and retrieval signals."""

    note_id: str
    path: str
    title: str
    body: str
    links: Tuple[str, ...]
    tags: Tuple[str, ...]
    headings: Tuple[str, ...]
    token_estimate: int


def estimate_tokens(text: str) -> int:
    """Estimate token cost deterministically from visible non-space chunks."""

    chunks = re.findall(r"\S+", text.strip())
    if not chunks:
        return 0
    return max(1, int(math.ceil(len(chunks) * 1.3)))


def strip_front_matter(text: str) -> Tuple[str, str]:
    """Return `(front_matter, body)` from a Markdown string."""

    if not text.startswith("---"):
        return "", text
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", text
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[1:index]), "\n".join(lines[index + 1 :]).lstrip()
    return "", text


def normalize_link(target: str) -> Optional[str]:
    """Normalize a Markdown or wikilink target into a note id."""

    cleaned = target.strip()
    if not cleaned or cleaned.startswith(("#", "http://", "https://", "mailto:")):
        return None
    cleaned = cleaned.split("|", 1)[0].split("#", 1)[0].strip()
    if not cleaned:
        return None
    if not cleaned.lower().endswith(".md"):
        cleaned = f"{cleaned}.md"
    return cleaned.replace("\\", "/")


def extract_links(text: str) -> Tuple[str, ...]:
    """Extract Obsidian wikilinks and Markdown links from text."""

    found: List[str] = []
    for raw in re.findall(r"\[\[([^\]]+)\]\]", text):
        normalized = normalize_link(raw)
        if normalized:
            found.append(normalized)
    for raw in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text):
        normalized = normalize_link(raw)
        if normalized:
            found.append(normalized)
    return tuple(sorted(dict.fromkeys(found)))


def extract_tags(front_matter: str, body: str) -> Tuple[str, ...]:
    """Extract inline tags and simple front-matter tags."""

    tags = set(re.findall(r"(?<!\w)#([A-Za-z0-9_/-]+)", body))
    for match in re.findall(r"(?im)^tags:\s*(.+)$", front_matter):
        cleaned = match.strip().strip("[]")
        for part in re.split(r"[, ]+", cleaned):
            tag = part.strip().strip("'\"")
            if tag:
                tags.add(tag.lstrip("#"))
    return tuple(sorted(tags))


def extract_headings(body: str) -> Tuple[str, ...]:
    """Extract Markdown headings without heading markers."""

    headings = []
    for line in body.splitlines():
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", line)
        if match:
            headings.append(match.group(1).strip())
    return tuple(headings)


def extract_title(front_matter: str, body: str, note_id: str) -> str:
    """Choose a stable title from front matter, H1, or filename."""

    title_match = re.search(r"(?im)^title:\s*(.+)$", front_matter)
    if title_match:
        return title_match.group(1).strip().strip("'\"")
    for heading in extract_headings(body):
        return heading
    return Path(note_id).stem.replace("-", " ").replace("_", " ").strip() or note_id


def parse_note(note_id: str, text: str) -> Note:
    """Parse one Markdown note into a `Note` object."""

    front_matter, body = strip_front_matter(text)
    title = extract_title(front_matter, body, note_id)
    links = extract_links(body)
    tags = extract_tags(front_matter, body)
    headings = extract_headings(body)
    return Note(
        note_id=note_id,
        path=note_id,
        title=title,
        body=body.strip(),
        links=links,
        tags=tags,
        headings=headings,
        token_estimate=estimate_tokens(body),
    )


def load_notes(source: Optional[str]) -> Tuple[List[Note], str, str]:
    """Load notes from a file, folder, or built-in sample.

    Returns `(notes, input_label, mode)`.
    """

    if source is None:
        notes = [parse_note(name, text) for name, text in sorted(SAMPLE_VAULT.items())]
        return notes, "built-in-sample", "selftest"

    root = Path(source)
    if not root.exists():
        raise ValueError(f"Input path does not exist: {source}")

    if root.is_file():
        if root.suffix.lower() != ".md":
            raise ValueError(f"Input file must be Markdown with .md extension: {source}")
        return [parse_note(root.name, root.read_text(encoding="utf-8"))], root.name, "vault"

    markdown_paths = sorted(path for path in root.rglob("*.md") if path.is_file())
    if not markdown_paths:
        raise ValueError(f"No Markdown files found under input folder: {source}")

    notes = []
    for path in markdown_paths:
        relative = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Could not read Markdown as UTF-8: {relative}") from exc
        notes.append(parse_note(relative, text))
    return notes, root.as_posix(), "vault"


def compute_centrality(notes: Sequence[Note]) -> Tuple[Dict[str, float], int]:
    """Compute normalized degree centrality and edge count for known notes."""

    note_ids = {note.note_id for note in notes}
    degree = {note.note_id: 0 for note in notes}
    edge_count = 0
    for note in notes:
        for target in note.links:
            if target in note_ids:
                degree[note.note_id] += 1
                degree[target] += 1
                edge_count += 1
    max_degree = max(degree.values(), default=0)
    if max_degree == 0:
        return {note_id: 0.0 for note_id in degree}, edge_count
    return {note_id: round(value / max_degree, 3) for note_id, value in degree.items()}, edge_count


def execution_score(note: Note) -> float:
    """Score whether a note contains execution-critical operational detail."""

    body = note.body
    tags = set(note.tags)
    code_blocks = len(re.findall(r"```", body)) // 2
    command_lines = len(
        re.findall(
            r"(?im)^\s*(?:curl|python|pip|npm|npx|node|git|docker|kubectl|make|pytest|uv)\b",
            body,
        )
    )
    api_terms = len(re.findall(r"\b(?:GET|POST|PUT|PATCH|DELETE)\s+/|\bAPI\b|\bendpoint\b", body))
    status_terms = len(
        re.findall(
            r"\b(?:queued|running|succeeded|failed|failure|retry|timeout|429|error|status|poll)\b",
            body,
            flags=re.IGNORECASE,
        )
    )
    procedure_terms = len(
        re.findall(
            r"\b(?:use|run|wait|until|before|after|check|must|do not|cannot|continue|observed)\b",
            body,
            flags=re.IGNORECASE,
        )
    )
    score = (
        min(code_blocks, 4) * 2.0
        + min(command_lines, 4) * 1.5
        + min(api_terms, 6) * 0.8
        + min(status_terms, 8) * 0.5
        + min(procedure_terms, 8) * 0.25
    )
    if "execution" in tags:
        score += 1.2
    score += min(len(tags & {"api", "cli", "dry-run", "errors", "incident", "ops"}), 3) * 0.35
    return round(score, 2)


def first_sentence(text: str) -> str:
    """Return a compact first sentence or first non-empty line."""

    useful_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^#{1,6}\s+", stripped):
            continue
        if re.match(r"(?i)^tags:\s*", stripped):
            continue
        if stripped.startswith("```"):
            continue
        useful_lines.append(stripped)
    compact = " ".join(useful_lines)
    if not compact:
        return ""
    match = re.search(r"(.+?[.!?])(?:\s|$)", compact)
    return match.group(1).strip() if match else compact


def clip_words(text: str, max_tokens: int) -> str:
    """Clip text to an approximate token budget while preserving word order."""

    if estimate_tokens(text) <= max_tokens:
        return text.strip()
    max_words = max(1, int(max_tokens / 1.3))
    words = re.findall(r"\S+", text.strip())
    clipped = " ".join(words[:max_words]).strip()
    return f"{clipped} ..."


def make_hub_summary(note: Note, max_tokens: int) -> str:
    """Build a deterministic orientation summary for a hub note."""

    parts = [f"# {note.title}", f"Purpose: {first_sentence(note.body)}"]
    if note.links:
        parts.append(f"Links: {', '.join(note.links)}")
    if note.tags:
        parts.append(f"Tags: {', '.join(note.tags)}")
    return clip_words("\n".join(parts), max_tokens)


def make_support_excerpt(note: Note, max_tokens: int) -> str:
    """Build a small deterministic excerpt for a non-hub support note."""

    parts = [f"# {note.title}"]
    sentence = first_sentence(note.body)
    if sentence:
        parts.append(sentence)
    if note.tags:
        parts.append(f"Tags: {', '.join(note.tags)}")
    return clip_words("\n".join(parts), max_tokens)


def classify_note(
    note: Note,
    centrality: float,
    score: float,
    hub_threshold: float,
    min_execution_score: float,
) -> Tuple[str, str]:
    """Return `(role, reason)` for a note."""

    if centrality >= hub_threshold and centrality > 0:
        return "hub_summary", "high-centrality orientation note; compressed"
    if score >= min_execution_score:
        return "preserved_detail", "execution-heavy long-tail note; preserved"
    return "support_excerpt", "low execution signal; included only if budget remains"


def build_context_bundle(
    source: Optional[object] = None,
    *,
    requested_tokens: int = 900,
    reserve_tokens: int = 100,
    min_execution_score: float = 3.0,
    hub_summary_tokens: int = 90,
    max_note_tokens: int = 220,
    support_excerpt_tokens: int = 70,
    input_label: Optional[str] = None,
) -> Dict[str, object]:
    """Build a deterministic hub-aware context bundle.

    `source` may be `None` for sample data, a path string, or a mapping of
    `{relative_note_path: markdown_text}` for tests and embedding.
    """

    if requested_tokens <= 0:
        raise ValueError("Budget must be a positive integer.")
    if reserve_tokens < 0:
        raise ValueError("Reserve tokens must be zero or greater.")
    available_tokens = requested_tokens - reserve_tokens
    if available_tokens <= 0:
        raise ValueError("Available budget must be positive after reserve tokens.")

    if isinstance(source, Mapping):
        notes = [parse_note(str(name), str(text)) for name, text in sorted(source.items())]
        label = input_label or "mapping-input"
        mode = "selftest" if label in {"built-in-sample", "test-sample"} else "vault"
    else:
        notes, label, mode = load_notes(None if source is None else str(source))
        if input_label:
            label = input_label

    centrality, edge_count = compute_centrality(notes)
    scores = {note.note_id: execution_score(note) for note in notes}
    max_centrality = max(centrality.values(), default=0.0)
    hub_threshold = max(0.67, max_centrality) if max_centrality else 1.0

    candidates = []
    for note in notes:
        role, reason = classify_note(
            note,
            centrality[note.note_id],
            scores[note.note_id],
            hub_threshold,
            min_execution_score,
        )
        if role == "hub_summary":
            content = make_hub_summary(note, hub_summary_tokens)
            priority = (0, -centrality[note.note_id], note.note_id)
        elif role == "preserved_detail":
            content = clip_words(note.body, max_note_tokens)
            priority = (1, -scores[note.note_id], note.note_id)
        else:
            content = make_support_excerpt(note, support_excerpt_tokens)
            priority = (2, note.note_id)
        candidates.append(
            {
                "id": note.note_id,
                "path": note.path,
                "role": role,
                "tokens": estimate_tokens(content),
                "centrality": centrality[note.note_id],
                "execution_score": scores[note.note_id],
                "reason": reason,
                "content": content,
                "_priority": priority,
            }
        )

    used_tokens = 0
    items = []
    decisions = []
    for candidate in sorted(candidates, key=lambda item: item["_priority"]):
        token_cost = int(candidate["tokens"])
        public_candidate = {key: value for key, value in candidate.items() if key != "_priority"}
        if token_cost <= available_tokens - used_tokens:
            items.append(public_candidate)
            used_tokens += token_cost
            decisions.append(
                {
                    "id": candidate["id"],
                    "role": candidate["role"],
                    "action": "included",
                    "tokens": token_cost,
                    "reason": candidate["reason"],
                }
            )
        else:
            decisions.append(
                {
                    "id": candidate["id"],
                    "role": candidate["role"],
                    "action": "skipped_budget",
                    "tokens": token_cost,
                    "reason": "not enough available budget after earlier inclusions",
                }
            )

    hubs = [item["id"] for item in sorted(candidates, key=lambda item: item["id"]) if item["role"] == "hub_summary"]
    long_tail = [
        item["id"]
        for item in sorted(candidates, key=lambda item: item["id"])
        if item["role"] == "preserved_detail" and item["centrality"] < hub_threshold
    ]

    return {
        "bundle_version": BUNDLE_VERSION,
        "mode": mode,
        "input": label,
        "budget": {
            "requested_tokens": requested_tokens,
            "reserve_tokens": reserve_tokens,
            "available_tokens": available_tokens,
            "used_tokens": used_tokens,
        },
        "graph": {
            "notes": len(notes),
            "edges": edge_count,
            "hubs": hubs,
            "long_tail": long_tail,
        },
        "items": items,
        "decisions": decisions,
    }


def env_int(name: str, default: int) -> int:
    """Read an integer environment variable with a clear error."""

    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {value!r}.") from exc


def env_choice(name: str, default: str, allowed: Sequence[str]) -> str:
    """Read a string environment variable constrained to allowed values."""

    value = os.getenv(name, default)
    if value not in allowed:
        allowed_text = ", ".join(allowed)
        raise ValueError(f"{name} must be one of: {allowed_text}.")
    return value


def render_markdown(bundle: Mapping[str, object]) -> str:
    """Render a context bundle as plain Markdown prompt text."""

    budget = bundle["budget"]  # type: ignore[index]
    graph = bundle["graph"]  # type: ignore[index]
    lines = [
        "# ContextTrellis Bundle",
        "",
        f"- Input: {bundle['input']}",
        f"- Used tokens: {budget['used_tokens']} / {budget['available_tokens']}",  # type: ignore[index]
        f"- Notes: {graph['notes']}; Edges: {graph['edges']}",  # type: ignore[index]
        "",
    ]
    for item in bundle["items"]:  # type: ignore[index]
        lines.extend(
            [
                f"## {item['id']} ({item['role']})",
                f"Reason: {item['reason']}",
                "",
                item["content"],
                "",
            ]
        )
    return "\n".join(str(line) for line in lines).rstrip() + "\n"


def make_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="Build a hub-aware, budgeted LLM context bundle from Markdown notes.",
    )
    parser.add_argument("--input", help="Markdown file or folder. Omit for built-in sample data.")
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run on built-in sample data with no API key or external services.",
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=env_int("CONTEXTTRELLIS_BUDGET", 900),
        help="Requested token budget before reserve. Env: CONTEXTTRELLIS_BUDGET.",
    )
    parser.add_argument(
        "--reserve",
        type=int,
        default=env_int("CONTEXTTRELLIS_RESERVE_TOKENS", 100),
        help="Tokens to reserve for the caller's surrounding prompt. Env: CONTEXTTRELLIS_RESERVE_TOKENS.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default=env_choice("CONTEXTTRELLIS_OUTPUT_FORMAT", "json", ("json", "markdown")),
        help="Output format. Env: CONTEXTTRELLIS_OUTPUT_FORMAT.",
    )
    parser.add_argument("--min-execution-score", type=float, default=3.0)
    parser.add_argument("--hub-summary-tokens", type=int, default=90)
    parser.add_argument("--max-note-tokens", type=int, default=220)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entrypoint."""

    try:
        parser = make_parser()
        args = parser.parse_args(argv)
        source = None if args.selftest or not args.input else args.input
        bundle = build_context_bundle(
            source,
            requested_tokens=args.budget,
            reserve_tokens=args.reserve,
            min_execution_score=args.min_execution_score,
            hub_summary_tokens=args.hub_summary_tokens,
            max_note_tokens=args.max_note_tokens,
        )
        if args.format == "markdown":
            sys.stdout.write(render_markdown(bundle))
        else:
            sys.stdout.write(json.dumps(bundle, indent=2, sort_keys=False) + "\n")
        return 0
    except ValueError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
