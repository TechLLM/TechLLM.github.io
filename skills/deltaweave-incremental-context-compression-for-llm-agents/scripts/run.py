"""DeltaWeave reference CLI.

Compare previous and current text snapshots and emit compact delta packs for
LLM agents. The implementation is intentionally small, local-only, and based
on the Python standard library.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


SAMPLE_OLD = """# Project Notes

## Goal

Build a small local tool that compares document snapshots.

## Agent Memory

The agent should remember the project goal and current constraints.

## Risks

- Long notes can waste tokens.
- Repeated summaries can drift.
"""

SAMPLE_NEW = """# Project Notes

## Goal

Build a small local tool that compares document snapshots and creates compact delta packs.

## Agent Memory

The agent should remember the project goal, current constraints, and the last accepted summary.

## Output Formats

- JSON for pipelines.
- Markdown for reviewers.
- Prompt text for LLM resummarization.

## Risks

- Long notes can waste tokens.
- Repeated summaries can drift.
- Moved sections may need reviewer attention.
"""


@dataclass
class Segment:
    segment_id: str
    kind: str
    title: str
    start_line: int
    end_line: int
    text: str


@dataclass
class DeltaItem:
    change_type: str
    segment_id: str
    kind: str
    title: str
    old_range: list[int | None]
    new_range: list[int | None]
    changed_old: str
    changed_new: str
    context: str
    anchors: dict[str, str | None]
    note: str


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "untitled"


def unique_id(base: str, counts: dict[str, int]) -> str:
    counts[base] = counts.get(base, 0) + 1
    if counts[base] == 1:
        return base
    return f"{base}-{counts[base]}"


def numbered_snippet(lines: Iterable[str], start_line: int) -> str:
    return "\n".join(f"{line_no:>4}: {line}" for line_no, line in enumerate(lines, start_line))


def detect_kind(path: str | None, text: str, granularity: str) -> str:
    if granularity != "auto":
        return granularity
    suffix = Path(path).suffix.lower() if path else ""
    if suffix in {".md", ".markdown"} or re.search(r"(?m)^#{1,6}\s+\S", text):
        return "heading"
    if suffix in {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rb", ".php", ".cs", ".cpp", ".c", ".h"}:
        return "function"
    return "block"


def split_markdown_sections(text: str) -> list[Segment]:
    lines = text.splitlines()
    if not lines:
        return [Segment("empty", "heading", "Empty document", 1, 1, "")]

    sections: list[Segment] = []
    heading_stack: list[tuple[int, str]] = []
    current_start = 1
    current_title = "Document preamble"
    current_id = "preamble"
    counts: dict[str, int] = {}

    def close_section(end_line: int) -> None:
        section_lines = lines[current_start - 1 : end_line]
        if section_lines or current_start == 1:
            sections.append(
                Segment(
                    segment_id=unique_id(current_id, counts),
                    kind="heading",
                    title=current_title,
                    start_line=current_start,
                    end_line=max(current_start, end_line),
                    text="\n".join(section_lines),
                )
            )

    for index, line in enumerate(lines, start=1):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if not match:
            continue
        if index > current_start:
            close_section(index - 1)
        level = len(match.group(1))
        heading = match.group(2).strip()
        heading_stack = [(lvl, title) for lvl, title in heading_stack if lvl < level]
        heading_stack.append((level, heading))
        path_title = " > ".join(title for _, title in heading_stack)
        current_start = index
        current_title = path_title
        current_id = "heading:" + "/".join(slugify(title) for _, title in heading_stack)

    close_section(len(lines))
    return sections


CODE_PATTERNS = [
    re.compile(r"^\s*(?:async\s+def|def|class)\s+([A-Za-z_][A-Za-z0-9_]*)\b"),
    re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][A-Za-z0-9_$]*)\b"),
    re.compile(r"^\s*(?:export\s+)?class\s+([A-Za-z_$][A-Za-z0-9_$]*)\b"),
    re.compile(r"^\s*(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][A-Za-z0-9_$]*)\s*=>"),
    re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_][A-Za-z0-9_]*)\b"),
    re.compile(r"^\s*(?:public|private|protected|static|final|async|\s)+\s*[A-Za-z_<>,\[\]?]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)\s*\{?\s*$"),
]


def split_code_symbols(text: str) -> list[Segment]:
    lines = text.splitlines()
    if not lines:
        return [Segment("empty", "function", "Empty file", 1, 1, "")]

    starts: list[tuple[int, str]] = []
    for index, line in enumerate(lines, start=1):
        for pattern in CODE_PATTERNS:
            match = pattern.match(line)
            if match:
                starts.append((index, match.group(1)))
                break

    if not starts:
        return [Segment("file", "file", "Whole file", 1, len(lines), text)]

    counts: dict[str, int] = {}
    segments: list[Segment] = []
    if starts[0][0] > 1:
        preamble_text = "\n".join(lines[: starts[0][0] - 1])
        if preamble_text.strip():
            segments.append(Segment("preamble", "function", "File preamble", 1, starts[0][0] - 1, preamble_text))

    for position, (start_line, name) in enumerate(starts):
        end_line = starts[position + 1][0] - 1 if position + 1 < len(starts) else len(lines)
        text_slice = "\n".join(lines[start_line - 1 : end_line])
        segment_id = unique_id("symbol:" + slugify(name), counts)
        segments.append(Segment(segment_id, "function", name, start_line, end_line, text_slice))

    return segments


def split_blocks(text: str) -> list[Segment]:
    lines = text.splitlines()
    if not lines:
        return [Segment("empty", "block", "Empty document", 1, 1, "")]

    blocks: list[Segment] = []
    counts: dict[str, int] = {}
    start = 1
    buffer: list[str] = []

    def flush(end_line: int) -> None:
        nonlocal buffer, start
        if not buffer:
            return
        title = next((line.strip() for line in buffer if line.strip()), "Blank block")
        title = title[:80]
        block_id = unique_id("block:" + slugify(title), counts)
        blocks.append(Segment(block_id, "block", title, start, end_line, "\n".join(buffer)))
        buffer = []

    for index, line in enumerate(lines, start=1):
        if line.strip():
            if not buffer:
                start = index
            buffer.append(line)
        else:
            flush(index - 1)
    flush(len(lines))
    return blocks or [Segment("empty", "block", "Empty document", 1, 1, "")]


def split_lines(text: str) -> list[Segment]:
    lines = text.splitlines()
    if not lines:
        return [Segment("empty", "line", "Empty document", 1, 1, "")]
    return [
        Segment(f"line:{index}", "line", f"Line {index}", index, index, line)
        for index, line in enumerate(lines, start=1)
    ]


def split_file(text: str) -> list[Segment]:
    line_count = max(1, len(text.splitlines()))
    return [Segment("file", "file", "Whole file", 1, line_count, text)]


def split_segments(text: str, kind: str) -> list[Segment]:
    if kind == "heading":
        return split_markdown_sections(text)
    if kind == "function":
        return split_code_symbols(text)
    if kind == "line":
        return split_lines(text)
    if kind == "file":
        return split_file(text)
    return split_blocks(text)


def changed_window(old_text: str, new_text: str) -> tuple[int, int, int, int]:
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    changed = [op for op in matcher.get_opcodes() if op[0] != "equal"]
    if not changed:
        return (0, 0, 0, 0)
    old_start = min(op[1] for op in changed)
    old_end = max(op[2] for op in changed)
    new_start = min(op[3] for op in changed)
    new_end = max(op[4] for op in changed)
    return old_start, old_end, new_start, new_end


def anchors_for(lines: list[str], start: int, end: int) -> dict[str, str | None]:
    before = None
    after = None
    for line in reversed(lines[:start]):
        if line.strip():
            before = line.strip()
            break
    for line in lines[end:]:
        if line.strip():
            after = line.strip()
            break
    return {"before": before, "after": after}


def make_delta_item(
    change_type: str,
    old_segment: Segment | None,
    new_segment: Segment | None,
    context_lines: int,
) -> DeltaItem:
    segment = new_segment or old_segment
    assert segment is not None

    old_text = old_segment.text if old_segment else ""
    new_text = new_segment.text if new_segment else ""
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    if change_type == "added":
        old_start = old_end = 0
        new_start = 0
        new_end = len(new_lines)
    elif change_type == "removed":
        old_start = 0
        old_end = len(old_lines)
        new_start = new_end = 0
    else:
        old_start, old_end, new_start, new_end = changed_window(old_text, new_text)

    context_source = new_segment if new_segment else old_segment
    context_all_lines = context_source.text.splitlines() if context_source else []
    focus_start = new_start if new_segment else old_start
    focus_end = new_end if new_segment else old_end
    context_start = max(0, focus_start - context_lines)
    context_end = min(len(context_all_lines), max(focus_end, focus_start + 1) + context_lines)
    absolute_start = (context_source.start_line if context_source else 1) + context_start
    context = numbered_snippet(context_all_lines[context_start:context_end], absolute_start)

    old_abs_start = old_segment.start_line + old_start if old_segment and old_lines else None
    old_abs_end = old_segment.start_line + max(old_end - 1, old_start) if old_segment and old_lines and old_end else old_abs_start
    new_abs_start = new_segment.start_line + new_start if new_segment and new_lines else None
    new_abs_end = new_segment.start_line + max(new_end - 1, new_start) if new_segment and new_lines and new_end else new_abs_start

    changed_old = "\n".join(old_lines[old_start:old_end])
    changed_new = "\n".join(new_lines[new_start:new_end])
    anchor_lines = context_all_lines
    anchors = anchors_for(anchor_lines, focus_start, focus_end)

    if change_type == "added":
        note = "New segment added in the current snapshot."
    elif change_type == "removed":
        note = "Segment removed from the current snapshot."
    else:
        note = "Segment changed; update only the affected understanding unless context implies a broader revision."

    return DeltaItem(
        change_type=change_type,
        segment_id=segment.segment_id,
        kind=segment.kind,
        title=segment.title,
        old_range=[old_abs_start, old_abs_end],
        new_range=[new_abs_start, new_abs_end],
        changed_old=changed_old,
        changed_new=changed_new,
        context=context,
        anchors=anchors,
        note=note,
    )


def build_delta(old_text: str, new_text: str, old_path: str | None, new_path: str | None, granularity: str, context_lines: int) -> dict:
    kind = detect_kind(new_path or old_path, new_text or old_text, granularity)
    old_segments = {segment.segment_id: segment for segment in split_segments(old_text, kind)}
    new_segments = {segment.segment_id: segment for segment in split_segments(new_text, kind)}

    items: list[DeltaItem] = []
    for segment_id, new_segment in new_segments.items():
        old_segment = old_segments.get(segment_id)
        if old_segment is None:
            items.append(make_delta_item("added", None, new_segment, context_lines))
        elif old_segment.text != new_segment.text:
            items.append(make_delta_item("modified", old_segment, new_segment, context_lines))

    for segment_id, old_segment in old_segments.items():
        if segment_id not in new_segments:
            items.append(make_delta_item("removed", old_segment, None, context_lines))

    old_line_count = len(old_text.splitlines())
    new_line_count = len(new_text.splitlines())
    api_key_available = bool(os.getenv("DELTAWEAVE_API_KEY") or os.getenv("OPENAI_API_KEY"))

    return {
        "tool": "DeltaWeave",
        "version": "0.1.0",
        "mode": "local-reference",
        "granularity": kind,
        "old_path": old_path,
        "new_path": new_path,
        "old_line_count": old_line_count,
        "new_line_count": new_line_count,
        "changed_segments": len(items),
        "api_key_available": api_key_available,
        "items": [asdict(item) for item in items],
    }


def render_markdown(delta: dict) -> str:
    lines = [
        "# DeltaWeave Delta Pack",
        "",
        f"- Granularity: `{delta['granularity']}`",
        f"- Changed segments: `{delta['changed_segments']}`",
        f"- Previous lines: `{delta['old_line_count']}`",
        f"- Current lines: `{delta['new_line_count']}`",
        "",
    ]
    if not delta["items"]:
        lines.append("No meaningful changes detected.")
        return "\n".join(lines)

    for index, item in enumerate(delta["items"], start=1):
        lines.extend(
            [
                f"## {index}. {item['title']}",
                "",
                f"- Change: `{item['change_type']}`",
                f"- Segment: `{item['segment_id']}`",
                f"- Kind: `{item['kind']}`",
                f"- Old range: `{item['old_range'][0]}-{item['old_range'][1]}`",
                f"- New range: `{item['new_range'][0]}-{item['new_range'][1]}`",
                f"- Anchor before: `{item['anchors']['before']}`",
                f"- Anchor after: `{item['anchors']['after']}`",
                f"- Note: {item['note']}",
                "",
                "### Context",
                "",
                "```text",
                item["context"],
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def render_prompt(delta: dict) -> str:
    markdown = render_markdown(delta)
    return "\n".join(
        [
            "You are updating an existing working summary using a DeltaWeave delta pack.",
            "",
            "Instructions:",
            "1. Preserve stable understanding from the previous summary.",
            "2. Update only facts, constraints, risks, or code behavior affected by the changed segments.",
            "3. Use anchors and nearby context to avoid summary drift.",
            "4. If a removed segment invalidates prior memory, mark that memory as obsolete.",
            "5. Return a concise updated summary and a short list of changed assumptions.",
            "",
            markdown,
        ]
    )


def read_text(path: str | None) -> str:
    if path is None:
        return ""
    return Path(path).read_text(encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create compact delta packs for changed Markdown, code, or text snapshots.")
    parser.add_argument("--old", help="Previous snapshot path.")
    parser.add_argument("--new", help="Current snapshot path.")
    parser.add_argument("--format", choices=["json", "markdown", "prompt"], default="markdown", help="Output format.")
    parser.add_argument(
        "--granularity",
        choices=["auto", "line", "block", "heading", "function", "file"],
        default="auto",
        help="How to group changes before compression.",
    )
    parser.add_argument("--context-lines", type=int, default=2, help="Unchanged lines to keep around changed regions.")
    parser.add_argument("--output", "-o", help="Write output to a file instead of stdout.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.context_lines < 0:
        print("--context-lines must be zero or greater.", file=sys.stderr)
        return 2

    if args.old or args.new:
        if not args.old or not args.new:
            print("Provide both --old and --new, or neither to use sample data.", file=sys.stderr)
            return 2
        old_text = read_text(args.old)
        new_text = read_text(args.new)
        old_path = args.old
        new_path = args.new
    else:
        old_text = SAMPLE_OLD
        new_text = SAMPLE_NEW
        old_path = "built-in-sample-previous.md"
        new_path = "built-in-sample-current.md"

    delta = build_delta(old_text, new_text, old_path, new_path, args.granularity, args.context_lines)
    if args.format == "json":
        output = json.dumps(delta, indent=2, ensure_ascii=False)
    elif args.format == "prompt":
        output = render_prompt(delta)
    else:
        output = render_markdown(delta)

    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
