#!/usr/bin/env python3
"""DeltaLoom reference CLI for incremental context diff planning."""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


SAMPLE_PREVIOUS = """# Agent Context

## Repository Map

The project has `src/app.py` and `tests/test_app.py`.

## API Notes

The CLI accepts `--input` and `--output`.

## Running Log

Last action: created baseline snapshot. Depends on [block:api-notes].
"""


SAMPLE_CURRENT = """# Agent Context

## Running Log

Last action: created baseline snapshot. Depends on [block:api-notes].

## Repository Map

The project has `src/app.py`, `src/diff.py`, and `tests/test_app.py`.

## API Notes

The CLI accepts `--input`, `--output`, and `--format`.

## Open Questions

Should JSON Patch output be compact or verbose?
"""


@dataclass(frozen=True)
class Block:
    id: str
    title: str
    kind: str
    index: int
    content: str
    fingerprint: str
    refs: list[str]

    def to_json(self, include_content: bool = True) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "kind": self.kind,
            "index": self.index,
            "fingerprint": self.fingerprint,
            "refs": self.refs,
        }
        if include_content:
            data["content"] = self.content
        return data


def slugify(text: str, fallback: str = "block") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or fallback


def normalize_content(text: str) -> str:
    lines = [line.rstrip() for line in text.strip().replace("\r\n", "\n").splitlines()]
    return "\n".join(lines)


def fingerprint(text: str) -> str:
    return hashlib.sha256(normalize_content(text).encode("utf-8")).hexdigest()[:16]


def unique_id(base: str, seen: dict[str, int]) -> str:
    count = seen.get(base, 0)
    seen[base] = count + 1
    if count == 0:
        return base
    return f"{base}-{count + 1}"


def extract_refs(text: str) -> list[str]:
    return sorted(set(re.findall(r"\[block:([A-Za-z0-9_.-]+)\]", text)))


def make_block(block_id: str, title: str, kind: str, index: int, content: str) -> Block:
    return Block(
        id=block_id,
        title=title,
        kind=kind,
        index=index,
        content=content.strip(),
        fingerprint=fingerprint(content),
        refs=extract_refs(content),
    )


def has_markdown_headings(text: str) -> bool:
    return bool(re.search(r"(?m)^#{1,6}\s+\S", text))


def has_code_symbols(text: str) -> bool:
    return bool(
        re.search(
            r"(?m)^\s*(def|class)\s+[A-Za-z_][A-Za-z0-9_]*|"
            r"^\s*(function|const|let|var)\s+[A-Za-z_$][A-Za-z0-9_$]*",
            text,
        )
    )


def chunk_headings(text: str) -> list[Block]:
    lines = text.replace("\r\n", "\n").splitlines()
    starts: list[tuple[int, str, str]] = []
    for idx, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            starts.append((idx, match.group(1), match.group(2)))

    if not starts:
        return chunk_paragraphs(text)

    seen: dict[str, int] = {}
    blocks: list[Block] = []
    if starts[0][0] > 0 and "\n".join(lines[: starts[0][0]]).strip():
        content = "\n".join(lines[: starts[0][0]])
        blocks.append(make_block("document-intro", "Document Intro", "intro", 0, content))

    for pos, (start, marker, title) in enumerate(starts):
        end = starts[pos + 1][0] if pos + 1 < len(starts) else len(lines)
        content = "\n".join(lines[start:end])
        base = slugify(title)
        block_id = unique_id(base, seen)
        kind = "heading" if len(marker) == 1 else "section"
        blocks.append(make_block(block_id, title, kind, len(blocks), content))

    return blocks


def chunk_paragraphs(text: str) -> list[Block]:
    parts = [part.strip() for part in re.split(r"\n\s*\n", text.replace("\r\n", "\n")) if part.strip()]
    blocks: list[Block] = []
    for idx, part in enumerate(parts):
        title = first_line_title(part, f"Paragraph {idx + 1}")
        blocks.append(make_block(f"paragraph-{idx + 1:03d}", title, "paragraph", idx, part))
    return blocks


def chunk_delimiter(text: str, delimiter: str) -> list[Block]:
    parts = [part.strip() for part in text.split(delimiter) if part.strip()]
    blocks: list[Block] = []
    for idx, part in enumerate(parts):
        title = first_line_title(part, f"Delimited Block {idx + 1}")
        blocks.append(make_block(f"delimited-{idx + 1:03d}", title, "delimited", idx, part))
    return blocks


def chunk_symbols(text: str) -> list[Block]:
    lines = text.replace("\r\n", "\n").splitlines()
    pattern = re.compile(
        r"^\s*(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)|"
        r"^\s*(?:function|const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)"
    )
    starts: list[tuple[int, str]] = []
    for idx, line in enumerate(lines):
        match = pattern.search(line)
        if match:
            starts.append((idx, match.group(1) or match.group(2) or "symbol"))

    if not starts:
        return chunk_paragraphs(text)

    seen: dict[str, int] = {}
    blocks: list[Block] = []
    if starts[0][0] > 0 and "\n".join(lines[: starts[0][0]]).strip():
        blocks.append(make_block("module-intro", "Module Intro", "intro", 0, "\n".join(lines[: starts[0][0]])))

    for pos, (start, name) in enumerate(starts):
        end = starts[pos + 1][0] if pos + 1 < len(starts) else len(lines)
        content = "\n".join(lines[start:end])
        block_id = unique_id(slugify(name, "symbol"), seen)
        blocks.append(make_block(block_id, name, "symbol", len(blocks), content))

    return blocks


def first_line_title(text: str, fallback: str) -> str:
    first = next((line.strip() for line in text.splitlines() if line.strip()), fallback)
    first = re.sub(r"^#{1,6}\s+", "", first)
    return first[:80] or fallback


def chunk_text(text: str, strategy: str, delimiter: str | None = None) -> tuple[str, list[Block]]:
    if strategy == "auto":
        if has_markdown_headings(text):
            return "headings", chunk_headings(text)
        if has_code_symbols(text):
            return "symbols", chunk_symbols(text)
        return "paragraphs", chunk_paragraphs(text)
    if strategy == "headings":
        return strategy, chunk_headings(text)
    if strategy == "paragraphs":
        return strategy, chunk_paragraphs(text)
    if strategy == "symbols":
        return strategy, chunk_symbols(text)
    if strategy == "delimiter":
        if not delimiter:
            raise ValueError("--delimiter is required when --chunk delimiter is used")
        return strategy, chunk_delimiter(text, delimiter)
    raise ValueError(f"Unsupported chunk strategy: {strategy}")


def load_input(path: str | None, sample: str) -> tuple[str, str]:
    if path:
        return path, Path(path).read_text(encoding="utf-8")
    return "<built-in-sample>", sample


def build_snapshot(source: str, text: str, strategy: str, delimiter: str | None) -> dict[str, Any]:
    actual_strategy, blocks = chunk_text(text, strategy, delimiter)
    return {
        "version": 1,
        "source": source,
        "chunk_strategy": actual_strategy,
        "blocks": [block.to_json(include_content=True) for block in blocks],
    }


def block_similarity(left: dict[str, Any], right: dict[str, Any]) -> float:
    return difflib.SequenceMatcher(None, normalize_content(left["content"]), normalize_content(right["content"])).ratio()


def detect_split_merge(
    unmatched_previous: Iterable[dict[str, Any]],
    unmatched_current: Iterable[dict[str, Any]],
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    previous = list(unmatched_previous)
    current = list(unmatched_current)
    splits: dict[str, list[str]] = {}
    merges: dict[str, list[str]] = {}

    for prev in previous:
        related = [cur["id"] for cur in current if block_similarity(prev, cur) >= 0.42]
        if len(related) >= 2:
            splits[prev["id"]] = related

    for cur in current:
        related = [prev["id"] for prev in previous if block_similarity(prev, cur) >= 0.42]
        if len(related) >= 2:
            merges[cur["id"]] = related

    return splits, merges


def plan_changes(previous_snapshot: dict[str, Any], current_snapshot: dict[str, Any]) -> dict[str, Any]:
    previous_blocks = previous_snapshot["blocks"]
    current_blocks = current_snapshot["blocks"]
    previous_by_id = {block["id"]: block for block in previous_blocks}
    previous_by_fp: dict[str, list[dict[str, Any]]] = {}
    for block in previous_blocks:
        previous_by_fp.setdefault(block["fingerprint"], []).append(block)

    matched_previous_ids: set[str] = set()
    matched_current_ids: set[str] = set()
    manifest: list[dict[str, Any]] = []

    for current in current_blocks:
        previous_same_id = previous_by_id.get(current["id"])
        if previous_same_id and previous_same_id["fingerprint"] == current["fingerprint"]:
            status = "reuse"
            reason = "same id and same fingerprint"
            if previous_same_id["index"] != current["index"]:
                reason = "same id and fingerprint; order changed"
            manifest.append(
                manifest_entry(status, current, previous_same_id, reason, matched=True)
            )
            matched_previous_ids.add(previous_same_id["id"])
            matched_current_ids.add(current["id"])
            continue

        same_fingerprint = next(
            (
                block
                for block in previous_by_fp.get(current["fingerprint"], [])
                if block["id"] not in matched_previous_ids
            ),
            None,
        )
        if same_fingerprint:
            manifest.append(
                manifest_entry(
                    "reuse",
                    current,
                    same_fingerprint,
                    f"fingerprint matched previous block {same_fingerprint['id']}",
                    matched=True,
                )
            )
            matched_previous_ids.add(same_fingerprint["id"])
            matched_current_ids.add(current["id"])
            continue

        if previous_same_id:
            manifest.append(
                manifest_entry("refresh", current, previous_same_id, "same id but content fingerprint changed")
            )
            matched_previous_ids.add(previous_same_id["id"])
            matched_current_ids.add(current["id"])
        else:
            manifest.append(manifest_entry("add", current, None, "new block id"))
            matched_current_ids.add(current["id"])

    unmatched_previous = [block for block in previous_blocks if block["id"] not in matched_previous_ids]
    unmatched_current = [block for block in current_blocks if block["id"] not in matched_current_ids]
    splits, merges = detect_split_merge(unmatched_previous, unmatched_current)

    for entry in manifest:
        block_id = entry["block_id"]
        if block_id in merges and entry["status"] == "add":
            entry["status"] = "merge"
            entry["decision"] = "refresh"
            entry["merged_from"] = merges[block_id]
            entry["reason"] = "new block resembles multiple previous blocks"

    for previous in unmatched_previous:
        entry = {
            "block_id": previous["id"],
            "title": previous["title"],
            "status": "delete",
            "decision": "delete",
            "previous_index": previous["index"],
            "current_index": None,
            "previous_fingerprint": previous["fingerprint"],
            "current_fingerprint": None,
            "reason": "block missing from current context",
        }
        if previous["id"] in splits:
            entry["status"] = "split"
            entry["decision"] = "delete"
            entry["split_into"] = splits[previous["id"]]
            entry["reason"] = "previous block resembles multiple current blocks"
        manifest.append(entry)

    summary_tasks = build_summary_tasks(manifest, current_blocks, previous_blocks)
    dependency_hints = build_dependency_hints(previous_blocks, current_blocks, manifest, summary_tasks)
    patch = build_json_patch(previous_snapshot, current_snapshot)

    return {
        "version": 1,
        "metadata": {
            "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
            "api_key_present": bool(os.getenv("DELTALOOM_API_KEY") or os.getenv("OPENAI_API_KEY")),
            "note": "Local reference implementation; no external service calls are made.",
        },
        "previous_snapshot": compact_snapshot(previous_snapshot),
        "current_snapshot": current_snapshot,
        "changed_block_manifest": manifest,
        "summary_tasks": summary_tasks,
        "dependency_hints": dependency_hints,
        "json_patch": patch,
    }


def manifest_entry(
    status: str,
    current: dict[str, Any],
    previous: dict[str, Any] | None,
    reason: str,
    matched: bool = False,
) -> dict[str, Any]:
    decision = "reuse" if status == "reuse" else "refresh"
    return {
        "block_id": current["id"],
        "title": current["title"],
        "status": status,
        "decision": decision,
        "previous_block_id": previous["id"] if previous else None,
        "previous_index": previous["index"] if previous else None,
        "current_index": current["index"],
        "previous_fingerprint": previous["fingerprint"] if previous else None,
        "current_fingerprint": current["fingerprint"],
        "order_changed": bool(previous and previous["index"] != current["index"]),
        "matched": matched,
        "reason": reason,
    }


def build_summary_tasks(
    manifest: list[dict[str, Any]],
    current_blocks: list[dict[str, Any]],
    previous_blocks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    current_by_id = {block["id"]: block for block in current_blocks}
    previous_by_id = {block["id"]: block for block in previous_blocks}
    tasks: list[dict[str, Any]] = []
    for entry in manifest:
        block = current_by_id.get(entry["block_id"]) or previous_by_id.get(entry["block_id"])
        tasks.append(
            {
                "block_id": entry["block_id"],
                "title": entry["title"],
                "action": entry["decision"],
                "status": entry["status"],
                "fingerprint": block["fingerprint"] if block else None,
                "reason": entry["reason"],
            }
        )
    return tasks


def build_dependency_hints(
    previous_blocks: list[dict[str, Any]],
    current_blocks: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
    summary_tasks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    changed_ids = {
        entry["block_id"]
        for entry in manifest
        if entry["status"] in {"refresh", "add", "delete", "split", "merge"}
    }
    changed_ids.update(
        entry["previous_block_id"]
        for entry in manifest
        if entry.get("previous_block_id") and entry["status"] in {"refresh", "delete", "split", "merge"}
    )
    task_by_id = {task["block_id"]: task for task in summary_tasks}
    hints: list[dict[str, Any]] = []

    for block in current_blocks + previous_blocks:
        invalidated_by = sorted(ref for ref in block.get("refs", []) if ref in changed_ids and ref != block["id"])
        if not invalidated_by:
            continue
        task = task_by_id.get(block["id"])
        if task and task["action"] == "reuse":
            task["action"] = "refresh"
            task["reason"] = f"depends on changed block(s): {', '.join(invalidated_by)}"
        hints.append(
            {
                "summary_id": f"summary:{block['id']}",
                "block_id": block["id"],
                "invalidated_by": invalidated_by,
                "reason": "block has explicit references to changed block ids",
            }
        )

    seen: set[tuple[str, tuple[str, ...]]] = set()
    deduped: list[dict[str, Any]] = []
    for hint in hints:
        key = (hint["block_id"], tuple(hint["invalidated_by"]))
        if key not in seen:
            deduped.append(hint)
            seen.add(key)
    return deduped


def build_json_patch(previous_snapshot: dict[str, Any], current_snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    patch: list[dict[str, Any]] = []
    for key in ("source", "chunk_strategy"):
        if previous_snapshot.get(key) != current_snapshot.get(key):
            patch.append({"op": "replace", "path": f"/{key}", "value": current_snapshot.get(key)})

    previous_blocks = previous_snapshot["blocks"]
    current_blocks = current_snapshot["blocks"]
    overlap = min(len(previous_blocks), len(current_blocks))
    for idx in range(overlap):
        if previous_blocks[idx] != current_blocks[idx]:
            patch.append({"op": "replace", "path": f"/blocks/{idx}", "value": current_blocks[idx]})
    for idx in range(len(previous_blocks) - 1, len(current_blocks) - 1, -1):
        patch.append({"op": "remove", "path": f"/blocks/{idx}"})
    for idx in range(overlap, len(current_blocks)):
        patch.append({"op": "add", "path": "/blocks/-", "value": current_blocks[idx]})
    return patch


def compact_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": snapshot["version"],
        "source": snapshot["source"],
        "chunk_strategy": snapshot["chunk_strategy"],
        "blocks": [
            {
                "id": block["id"],
                "title": block["title"],
                "index": block["index"],
                "fingerprint": block["fingerprint"],
                "refs": block["refs"],
            }
            for block in snapshot["blocks"]
        ],
    }


def format_summary(plan: dict[str, Any]) -> str:
    previous_count = len(plan["previous_snapshot"]["blocks"])
    current_count = len(plan["current_snapshot"]["blocks"])
    lines = [
        "DeltaLoom plan",
        f"Blocks: previous={previous_count} current={current_count}",
        "Manifest:",
    ]
    for entry in plan["changed_block_manifest"]:
        lines.append(f"- {entry['status']}: {entry['block_id']}")
    lines.append("Summary tasks:")
    for task in plan["summary_tasks"]:
        lines.append(f"- {task['action']}: {task['block_id']}")
    if plan["dependency_hints"]:
        lines.append("Dependency hints:")
        for hint in plan["dependency_hints"]:
            invalidated = ", ".join(hint["invalidated_by"])
            lines.append(f"- {hint['block_id']} invalidated by {invalidated}")
    lines.append(f"JSON Patch operations: {len(plan['json_patch'])}")
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a DeltaLoom context-diff plan from previous and current inputs."
    )
    parser.add_argument("--previous", "-p", help="Previous context file. Uses built-in sample when omitted.")
    parser.add_argument("--current", "-c", help="Current context file. Uses built-in sample when omitted.")
    parser.add_argument(
        "--chunk",
        choices=["auto", "headings", "paragraphs", "symbols", "delimiter"],
        default="auto",
        help="Chunking strategy. Default: auto.",
    )
    parser.add_argument("--delimiter", help="Delimiter string when --chunk delimiter is used.")
    parser.add_argument("--output", "-o", help="Write JSON plan to this file instead of stdout.")
    parser.add_argument("--format", choices=["json", "summary"], default="json", help="Output format. Default: json.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        previous_source, previous_text = load_input(args.previous, SAMPLE_PREVIOUS)
        current_source, current_text = load_input(args.current, SAMPLE_CURRENT)
        previous_snapshot = build_snapshot(previous_source, previous_text, args.chunk, args.delimiter)
        current_snapshot = build_snapshot(current_source, current_text, args.chunk, args.delimiter)
        plan = plan_changes(previous_snapshot, current_snapshot)

        if args.output:
            Path(args.output).write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            if args.format == "summary":
                print(format_summary(plan))
            else:
                print(f"Wrote DeltaLoom plan to {args.output}")
            return 0

        if args.format == "summary":
            print(format_summary(plan))
        else:
            print(json.dumps(plan, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
