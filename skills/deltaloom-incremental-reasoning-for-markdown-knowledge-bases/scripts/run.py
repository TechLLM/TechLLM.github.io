#!/usr/bin/env python3
"""DeltaLoom reference CLI for incremental Markdown reasoning packets."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SAMPLE_PREVIOUS = """# Project Alpha

Project Alpha tracks the first research sprint for [[Roadmap]].

The prototype depends on a small parser and a repeatable review loop.

Risks are currently listed in [[Risk Register]].
"""

SAMPLE_CURRENT = """# Project Alpha

Project Alpha tracks the first research sprint for [[Roadmap]] and [[Research Notes]].

The prototype depends on a small parser, a repeatable review loop, and a compact packet builder.

Risks are currently listed in [[Risk Register]].

The next milestone is a local-only CLI that can run inside CI.
"""

SAMPLE_GRAPH = {
    "Project Alpha": {
        "links": ["Roadmap", "Risk Register"],
        "backlinks": ["Research Inbox", "Team Plan"],
    },
    "Roadmap": {"links": ["Project Alpha"], "backlinks": ["Project Alpha"]},
    "Risk Register": {"links": [], "backlinks": ["Project Alpha"]},
    "Research Notes": {"links": ["Project Alpha"], "backlinks": []},
}

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
FENCE_RE = re.compile(r"^\s*(```|~~~)")


@dataclass
class Block:
    index: int
    start_line: int
    end_line: int
    kind: str
    text: str
    fingerprint: str
    wikilinks: list[str]


@dataclass
class Change:
    tag: str
    previous_indexes: list[int]
    current_indexes: list[int]
    previous_lines: list[list[int]]
    current_lines: list[list[int]]


def normalize_block(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def fingerprint(text: str) -> str:
    return hashlib.sha256(normalize_block(text).encode("utf-8")).hexdigest()[:16]


def extract_wikilinks(text: str) -> list[str]:
    seen: set[str] = set()
    links: list[str] = []
    for match in WIKILINK_RE.finditer(text):
        target = match.group(1).strip()
        if target and target not in seen:
            seen.add(target)
            links.append(target)
    return links


def classify_block(text: str) -> str:
    stripped = text.lstrip()
    if not stripped:
        return "blank"
    if stripped.startswith("#"):
        return "heading"
    if stripped.startswith(("```", "~~~")):
        return "code"
    if stripped.startswith(">"):
        return "quote"
    if stripped.startswith(("- ", "* ", "+ ")) or re.match(r"\d+\.\s+", stripped):
        return "list"
    if "|" in stripped and "\n" in stripped:
        return "table"
    return "paragraph"


def segment_markdown(markdown: str) -> list[Block]:
    """Split Markdown into paragraph-like blocks while preserving fenced code."""
    lines = markdown.splitlines()
    blocks: list[Block] = []
    buffer: list[str] = []
    start_line = 1
    fence_marker: str | None = None

    def flush(end_line: int) -> None:
        nonlocal buffer, start_line
        text = "\n".join(buffer).strip("\n")
        if not text.strip():
            buffer = []
            start_line = end_line + 1
            return
        blocks.append(
            Block(
                index=len(blocks),
                start_line=start_line,
                end_line=end_line,
                kind=classify_block(text),
                text=text,
                fingerprint=fingerprint(text),
                wikilinks=extract_wikilinks(text),
            )
        )
        buffer = []
        start_line = end_line + 1

    for line_number, line in enumerate(lines, start=1):
        fence_match = FENCE_RE.match(line)

        if fence_marker:
            buffer.append(line)
            if fence_match and fence_match.group(1) == fence_marker:
                fence_marker = None
                flush(line_number)
            continue

        if fence_match:
            if buffer:
                flush(line_number - 1)
            fence_marker = fence_match.group(1)
            start_line = line_number
            buffer.append(line)
            continue

        if not line.strip():
            if buffer:
                flush(line_number - 1)
            start_line = line_number + 1
            continue

        if not buffer:
            start_line = line_number
        buffer.append(line)

    if buffer:
        flush(len(lines))

    return blocks


def block_lines(blocks: list[Block], indexes: list[int]) -> list[list[int]]:
    return [[blocks[index].start_line, blocks[index].end_line] for index in indexes]


def detect_changes(previous: list[Block], current: list[Block]) -> list[Change]:
    previous_keys = [block.fingerprint for block in previous]
    current_keys = [block.fingerprint for block in current]
    matcher = difflib.SequenceMatcher(a=previous_keys, b=current_keys, autojunk=False)
    changes: list[Change] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        previous_indexes = list(range(i1, i2))
        current_indexes = list(range(j1, j2))
        changes.append(
            Change(
                tag=tag,
                previous_indexes=previous_indexes,
                current_indexes=current_indexes,
                previous_lines=block_lines(previous, previous_indexes),
                current_lines=block_lines(current, current_indexes),
            )
        )
    return changes


def load_graph(path: str | None) -> dict[str, Any]:
    if not path:
        return SAMPLE_GRAPH
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict) and isinstance(data.get("notes"), dict):
        return data["notes"]
    if isinstance(data, dict):
        return data
    raise ValueError("Link graph JSON must be an object keyed by note title or contain a 'notes' object.")


def read_markdown(path: str | None, fallback: str) -> str:
    if not path:
        return fallback
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def note_title_from_args(args: argparse.Namespace) -> str:
    if args.note_title:
        return args.note_title
    if args.current:
        return Path(args.current).stem.replace("-", " ").replace("_", " ").title()
    return "Project Alpha"


def collect_links(blocks: list[Block]) -> set[str]:
    links: set[str] = set()
    for block in blocks:
        links.update(block.wikilinks)
    return links


def impacted_backlinks(
    graph: dict[str, Any],
    note_title: str,
    added_links: set[str],
    removed_links: set[str],
) -> dict[str, list[str]]:
    note_entry = graph.get(note_title, {})
    direct_backlinks = sorted(as_string_list(note_entry.get("backlinks", [])))
    impacted: dict[str, list[str]] = {}

    if direct_backlinks:
        impacted[note_title] = direct_backlinks

    for target in sorted(added_links | removed_links):
        entry = graph.get(target, {})
        backlinks = sorted(as_string_list(entry.get("backlinks", [])))
        if backlinks:
            impacted[target] = backlinks

    return impacted


def as_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def reusable_blocks(previous: list[Block], current: list[Block]) -> list[dict[str, Any]]:
    previous_by_hash = {block.fingerprint: block for block in previous}
    reusable: list[dict[str, Any]] = []
    for block in current:
        old = previous_by_hash.get(block.fingerprint)
        if old is None:
            continue
        reusable.append(
            {
                "current_index": block.index,
                "current_lines": [block.start_line, block.end_line],
                "previous_index": old.index,
                "previous_lines": [old.start_line, old.end_line],
                "fingerprint": block.fingerprint,
                "summary_key": f"summary:{block.fingerprint}",
                "preview": preview(block.text),
            }
        )
    return reusable


def preview(text: str, limit: int = 100) -> str:
    collapsed = normalize_block(text)
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 1].rstrip() + "..."


def context_packet(
    current: list[Block],
    changes: list[Change],
    added_links: set[str],
    removed_links: set[str],
    impacted: dict[str, list[str]],
    context_window: int,
) -> dict[str, Any]:
    indexes: set[int] = set()
    changed_indexes: set[int] = set()
    for change in changes:
        for index in change.current_indexes:
            changed_indexes.add(index)
            lower = max(0, index - context_window)
            upper = min(len(current) - 1, index + context_window)
            indexes.update(range(lower, upper + 1))

    packet_blocks = []
    for index in sorted(indexes):
        block = current[index]
        packet_blocks.append(
            {
                "index": block.index,
                "lines": [block.start_line, block.end_line],
                "kind": block.kind,
                "changed": index in changed_indexes,
                "wikilinks": block.wikilinks,
                "text": block.text,
            }
        )

    return {
        "purpose": "Refresh only changed Markdown blocks and linked-note impacts.",
        "changed_current_block_indexes": sorted(changed_indexes),
        "context_window": context_window,
        "blocks": packet_blocks,
        "link_delta": {
            "added": sorted(added_links),
            "removed": sorted(removed_links),
        },
        "impacted_backlinks": impacted,
    }


def analyze(args: argparse.Namespace) -> dict[str, Any]:
    api_key_present = bool(os.getenv("DELTALOOM_API_KEY") or os.getenv("OPENAI_API_KEY"))
    using_builtin_sample = not args.previous and not args.current and not args.graph

    previous_text = read_markdown(args.previous, SAMPLE_PREVIOUS)
    current_text = read_markdown(args.current, SAMPLE_CURRENT)
    graph = load_graph(args.graph)
    note_title = note_title_from_args(args)

    previous_blocks = segment_markdown(previous_text)
    current_blocks = segment_markdown(current_text)
    changes = detect_changes(previous_blocks, current_blocks)

    previous_links = collect_links(previous_blocks)
    current_links = collect_links(current_blocks)
    added_links = current_links - previous_links
    removed_links = previous_links - current_links
    impacted = impacted_backlinks(graph, note_title, added_links, removed_links)

    packet = context_packet(
        current=current_blocks,
        changes=changes,
        added_links=added_links,
        removed_links=removed_links,
        impacted=impacted,
        context_window=max(args.context_window, 0),
    )

    return {
        "tool": "md-delta-reason",
        "note_title": note_title,
        "api_key_present": api_key_present,
        "external_calls_made": False,
        "using_builtin_sample": using_builtin_sample,
        "counts": {
            "previous_blocks": len(previous_blocks),
            "current_blocks": len(current_blocks),
            "changes": len(changes),
            "reusable_summary_blocks": len(reusable_blocks(previous_blocks, current_blocks)),
        },
        "changed_ranges": [asdict(change) for change in changes],
        "wikilinks": {
            "previous": sorted(previous_links),
            "current": sorted(current_links),
            "added": sorted(added_links),
            "removed": sorted(removed_links),
        },
        "impacted_backlinks": impacted,
        "reusable_summary_blocks": reusable_blocks(previous_blocks, current_blocks),
        "reasoning_packet": packet,
    }


def render_report(result: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("DeltaLoom incremental reasoning report")
    lines.append("=" * 42)
    lines.append(f"Note: {result['note_title']}")
    lines.append(f"Built-in sample: {result['using_builtin_sample']}")
    lines.append(f"API key present: {result['api_key_present']}")
    lines.append(f"External calls made: {result['external_calls_made']}")
    lines.append("")
    lines.append("Counts")
    for key, value in result["counts"].items():
        lines.append(f"- {key.replace('_', ' ')}: {value}")

    lines.append("")
    lines.append("Changed ranges")
    if result["changed_ranges"]:
        for change in result["changed_ranges"]:
            lines.append(
                "- "
                + change["tag"]
                + f" previous_blocks={change['previous_indexes']} previous_lines={change['previous_lines']}"
                + f" current_blocks={change['current_indexes']} current_lines={change['current_lines']}"
            )
    else:
        lines.append("- none")

    lines.append("")
    lines.append("Wikilink delta")
    lines.append(f"- added: {', '.join(result['wikilinks']['added']) or 'none'}")
    lines.append(f"- removed: {', '.join(result['wikilinks']['removed']) or 'none'}")

    lines.append("")
    lines.append("Impacted backlinks")
    if result["impacted_backlinks"]:
        for note, backlinks in result["impacted_backlinks"].items():
            lines.append(f"- {note}: {', '.join(backlinks)}")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("Reusable summary blocks")
    reusable = result["reusable_summary_blocks"]
    if reusable:
        for block in reusable:
            lines.append(
                f"- current block {block['current_index']} lines {block['current_lines']} "
                f"reuse {block['summary_key']}: {block['preview']}"
            )
    else:
        lines.append("- none")

    lines.append("")
    lines.append("Reasoning packet")
    packet = result["reasoning_packet"]
    lines.append(f"- purpose: {packet['purpose']}")
    lines.append(f"- changed current block indexes: {packet['changed_current_block_indexes']}")
    lines.append(f"- packet blocks: {len(packet['blocks'])}")
    for block in packet["blocks"]:
        marker = "changed" if block["changed"] else "context"
        links = ", ".join(block["wikilinks"]) or "none"
        lines.append(
            f"  - block {block['index']} ({marker}, {block['kind']}, lines {block['lines']}, links: {links})"
        )
        lines.append(f"    {preview(block['text'], 140)}")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="md-delta-reason",
        description="Build minimal reasoning packets from Markdown note deltas.",
    )
    parser.add_argument("--previous", help="Path to the previous Markdown file.")
    parser.add_argument("--current", help="Path to the current Markdown file.")
    parser.add_argument("--graph", help="Path to link graph JSON.")
    parser.add_argument("--note-title", help="Note title key to use in the link graph.")
    parser.add_argument(
        "--format",
        choices=["report", "json"],
        default="report",
        help="Output format. Defaults to report.",
    )
    parser.add_argument(
        "--context-window",
        type=int,
        default=1,
        help="Number of neighboring current blocks to include around each changed block.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = analyze(args)
    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(render_report(result))


if __name__ == "__main__":
    main()
