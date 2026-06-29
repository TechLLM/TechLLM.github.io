#!/usr/bin/env python3
"""TraceWeave reference CLI.

This script enriches Markdown note graphs with local execution-log evidence.
It uses only the Python standard library and falls back to built-in sample data
when no input paths are provided.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
TAG_RE = re.compile(r"(?<![\w/])#([A-Za-z][A-Za-z0-9_/-]*)")
MD_REF_RE = re.compile(
    r"(?P<path>(?:[A-Za-z0-9_.-]+/)*(?:[A-Za-z0-9_.-]+(?: [A-Za-z0-9_.-]+){0,5})\.md)"
)
ISO_RE = re.compile(r"(\d{4}-\d{2}-\d{2}[T ][0-9:]{8}(?:Z|[+-][0-9:]{5})?)")


BUILTIN_NOTES = {
    "Retrieval Pipeline.md": """---
aliases: [Retriever, RAG Pipeline]
tags: [retrieval, agents]
---
# Retrieval Pipeline

The retrieval pipeline ranks candidate notes for agent context.
It should consider [[Agent Resume]] evidence and source quality.
""",
    "Agent Resume.md": """---
aliases:
  - Resume Points
tags: [agents, reliability]
---
# Agent Resume

Resume points help long-running workflows continue from stable checkpoints.
""",
    "Source Quality.md": """---
tags: [quality]
---
# Source Quality

Source quality combines usage, freshness, and failure history.
""",
}

BUILTIN_LOGS = [
    {
        "timestamp": "2026-06-01T10:00:00Z",
        "status": "success",
        "message": "Processed [[Retrieval Pipeline]] with notes/Source Quality.md",
        "sources": ["Retrieval Pipeline.md", "Source Quality.md"],
    },
    {
        "timestamp": "2026-06-02T11:30:00Z",
        "status": "failed",
        "message": "Agent failed while using [[Retrieval Pipeline]] and Missing Note.md",
        "sources": ["Retrieval Pipeline.md", "Missing Note.md"],
    },
    {
        "timestamp": "2026-06-03T15:45:00Z",
        "status": "resumed",
        "message": "Resumed workflow from [[Agent Resume]] then reused [[Retrieval Pipeline]]",
        "sources": ["Agent Resume.md", "Retrieval Pipeline.md"],
    },
]


@dataclass
class Note:
    title: str
    path: str
    frontmatter: dict[str, object] = field(default_factory=dict)
    wikilinks: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    aliases: set[str] = field(default_factory=set)


@dataclass
class LogEvent:
    timestamp: str | None
    status: str
    text: str
    refs: set[str] = field(default_factory=set)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enrich Markdown notes with execution-log quality signals."
    )
    parser.add_argument("--notes", help="Markdown notes directory. Uses sample data if omitted.")
    parser.add_argument("--logs", help="Log file or directory with .jsonl, .log, or .txt files.")
    parser.add_argument("--out", help="Write Markdown report to this file instead of stdout.")
    parser.add_argument("--metadata-dir", help="Directory for optional sidecar metadata JSON files.")
    parser.add_argument("--write-sidecar", action="store_true", help="Write sidecar metadata files.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write sidecars. This is the default unless --write-sidecar is set.")
    parser.add_argument("--diff", action="store_true", help="Print unified diffs for sidecar metadata changes.")
    parser.add_argument("--strict", action="store_true", help="Exit with an error when references cannot be resolved.")
    parser.add_argument("--min-cooccurrence", type=int, default=1, help="Minimum log co-occurrence count for backlink recommendations.")
    return parser.parse_args(argv)


def split_frontmatter(text: str) -> tuple[dict[str, object], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = index
            break
    if end is None:
        return {}, text
    return parse_simple_yaml(lines[1:end]), "\n".join(lines[end + 1 :])


def parse_simple_yaml(lines: list[str]) -> dict[str, object]:
    data: dict[str, object] = {}
    current_key: str | None = None
    for raw_line in lines:
        line = raw_line.rstrip()
        if not line.strip():
            continue
        list_item = re.match(r"\s*-\s*(.+)", line)
        if list_item and current_key:
            data.setdefault(current_key, [])
            if isinstance(data[current_key], list):
                data[current_key].append(clean_scalar(list_item.group(1)))
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        current_key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            items = [clean_scalar(item) for item in value[1:-1].split(",") if item.strip()]
            data[current_key] = items
        elif value == "":
            data[current_key] = []
        else:
            data[current_key] = clean_scalar(value)
    return data


def clean_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] in {"'", '"'} and value[-1] == value[0]:
        return value[1:-1]
    return value


def as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def load_notes(notes_dir: str | None) -> dict[str, Note]:
    if notes_dir:
        root = Path(notes_dir)
        if not root.exists() or not root.is_dir():
            raise SystemExit(f"Notes directory not found: {notes_dir}")
        raw_notes = {
            str(path.relative_to(root)): path.read_text(encoding="utf-8")
            for path in sorted(root.rglob("*.md"))
        }
    else:
        raw_notes = BUILTIN_NOTES

    notes: dict[str, Note] = {}
    for rel_path, text in raw_notes.items():
        frontmatter, body = split_frontmatter(text)
        title = Path(rel_path).stem
        aliases = set(as_list(frontmatter.get("aliases")) + as_list(frontmatter.get("alias")))
        tags = set(as_list(frontmatter.get("tags")) + as_list(frontmatter.get("tag")))
        tags.update(TAG_RE.findall(body))
        links = {normalize_ref(match) for match in WIKILINK_RE.findall(body)}
        note = Note(
            title=title,
            path=rel_path,
            frontmatter=frontmatter,
            wikilinks=links,
            tags=tags,
            aliases=aliases,
        )
        notes[rel_path] = note
    return notes


def load_log_events(logs_path: str | None) -> list[LogEvent]:
    if not logs_path:
        return [event_from_mapping(item) for item in BUILTIN_LOGS]

    path = Path(logs_path)
    if not path.exists():
        raise SystemExit(f"Logs path not found: {logs_path}")

    files: list[Path]
    if path.is_dir():
        files = [
            item
            for item in sorted(path.rglob("*"))
            if item.is_file() and item.suffix.lower() in {".jsonl", ".log", ".txt"}
        ]
    else:
        files = [path]

    events: list[LogEvent] = []
    for file_path in files:
        if file_path.suffix.lower() == ".jsonl":
            events.extend(read_jsonl_events(file_path))
        else:
            events.extend(read_text_events(file_path))
    return events


def read_jsonl_events(path: Path) -> list[LogEvent]:
    events: list[LogEvent] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            events.append(event_from_mapping(json.loads(line)))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSONL in {path}:{line_number}: {exc}") from exc
    return events


def read_text_events(path: Path) -> list[LogEvent]:
    events: list[LogEvent] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(event_from_text(line))
    return events


def event_from_mapping(item: dict[str, object]) -> LogEvent:
    fields = [
        str(item.get(key, ""))
        for key in ("message", "event", "command", "tool", "error")
        if item.get(key) is not None
    ]
    sources = [str(source) for source in as_list(item.get("sources")) + as_list(item.get("notes"))]
    text = " ".join(fields)
    status = infer_status(str(item.get("status", "")) + " " + text)
    timestamp = normalize_timestamp(str(item.get("timestamp", "")) or None)
    refs = extract_raw_refs(text)
    refs.update(normalize_ref(source) for source in sources)
    return LogEvent(timestamp=timestamp, status=status, text=text, refs=refs)


def event_from_text(text: str) -> LogEvent:
    timestamp_match = ISO_RE.search(text)
    timestamp = normalize_timestamp(timestamp_match.group(1)) if timestamp_match else None
    return LogEvent(
        timestamp=timestamp,
        status=infer_status(text),
        text=text,
        refs=extract_raw_refs(text),
    )


def infer_status(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ("fail", "failed", "error", "exception", "timeout")):
        return "failure"
    if any(token in lowered for token in ("resume", "resumed", "checkpoint", "continued")):
        return "resume"
    if any(token in lowered for token in ("success", "succeeded", "complete", "completed", "processed")):
        return "success"
    return "unknown"


def normalize_timestamp(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip().replace(" ", "T")
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        return value.strip()
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def extract_raw_refs(text: str) -> set[str]:
    refs = {normalize_ref(match) for match in WIKILINK_RE.findall(text)}
    refs.update(normalize_ref(match.group("path")) for match in MD_REF_RE.finditer(text))
    return {ref for ref in refs if ref}


def normalize_ref(value: str) -> str:
    value = value.strip().replace("\\", "/")
    value = re.sub(r"^(and|with|using|from|read|opened|processed)\s+", "", value, flags=re.IGNORECASE)
    if value.endswith(".md"):
        value = Path(value).stem
    return value.strip()


def build_resolver(notes: dict[str, Note]) -> dict[str, str]:
    resolver: dict[str, str] = {}
    for path, note in notes.items():
        candidates = {note.title, Path(path).stem, path, Path(path).name}
        candidates.update(note.aliases)
        for candidate in candidates:
            resolver[normalize_key(candidate)] = path
    return resolver


def normalize_key(value: str) -> str:
    return normalize_ref(value).lower().strip()


def resolve_event_refs(event: LogEvent, resolver: dict[str, str], notes: dict[str, Note]) -> tuple[set[str], set[str]]:
    resolved: set[str] = set()
    unresolved: set[str] = set()

    for ref in event.refs:
        target = resolver.get(normalize_key(ref))
        if target:
            resolved.add(target)
        else:
            unresolved.add(ref)

    lowered_text = event.text.lower()
    for key, path in resolver.items():
        if len(key) >= 4 and re.search(rf"(?<!\w){re.escape(key)}(?!\w)", lowered_text):
            resolved.add(path)

    return resolved, unresolved


def analyze(notes: dict[str, Note], events: list[LogEvent]) -> tuple[dict[str, dict[str, object]], list[str], dict[tuple[str, str], int]]:
    resolver = build_resolver(notes)
    metrics = {
        path: {
            "title": note.title,
            "path": path,
            "last_seen": None,
            "run_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "resume_points": 0,
            "quality_score": 0,
        }
        for path, note in notes.items()
    }
    unresolved: list[str] = []
    cooccurrence: dict[tuple[str, str], int] = {}

    for event in events:
        resolved, missing = resolve_event_refs(event, resolver, notes)
        unresolved.extend(sorted(missing))
        for path in resolved:
            entry = metrics[path]
            entry["run_count"] = int(entry["run_count"]) + 1
            if event.status == "success":
                entry["success_count"] = int(entry["success_count"]) + 1
            elif event.status == "failure":
                entry["failure_count"] = int(entry["failure_count"]) + 1
            elif event.status == "resume":
                entry["resume_points"] = int(entry["resume_points"]) + 1
            if event.timestamp:
                current = entry["last_seen"]
                if current is None or str(event.timestamp) > str(current):
                    entry["last_seen"] = event.timestamp

        ordered = sorted(resolved)
        for left_index, left in enumerate(ordered):
            for right in ordered[left_index + 1 :]:
                pair = tuple(sorted((left, right)))
                cooccurrence[pair] = cooccurrence.get(pair, 0) + 1

    for path, entry in metrics.items():
        entry["quality_score"] = score_entry(entry, notes[path])
    return metrics, unresolved, cooccurrence


def score_entry(entry: dict[str, object], note: Note) -> int:
    run_count = int(entry["run_count"])
    success_count = int(entry["success_count"])
    failure_count = int(entry["failure_count"])
    resume_points = int(entry["resume_points"])
    score = 40
    score += min(run_count * 8, 32)
    score += min(success_count * 10, 25)
    score += min(resume_points * 6, 18)
    score += min(len(note.wikilinks) * 2, 8)
    score -= min(failure_count * 14, 35)
    if entry["last_seen"]:
        score += 5
    return max(0, min(100, score))


def backlink_recommendations(
    notes: dict[str, Note],
    cooccurrence: dict[tuple[str, str], int],
    min_cooccurrence: int,
) -> list[tuple[str, str, int]]:
    recommendations: list[tuple[str, str, int]] = []
    for (left, right), count in sorted(cooccurrence.items(), key=lambda item: (-item[1], item[0])):
        if count < min_cooccurrence:
            continue
        left_links = {normalize_key(link) for link in notes[left].wikilinks}
        right_links = {normalize_key(link) for link in notes[right].wikilinks}
        left_title = notes[left].title
        right_title = notes[right].title
        already_linked = (
            normalize_key(right_title) in left_links
            or normalize_key(left_title) in right_links
        )
        if not already_linked:
            recommendations.append((left, right, count))
    return recommendations


def render_report(
    notes: dict[str, Note],
    metrics: dict[str, dict[str, object]],
    unresolved: list[str],
    recommendations: list[tuple[str, str, int]],
    using_sample: bool,
    api_key_present: bool,
) -> str:
    lines = [
        "# TraceWeave Report",
        "",
        f"- Mode: {'built-in sample data' if using_sample else 'local files'}",
        f"- Optional API key present: {'yes' if api_key_present else 'no'}",
        f"- Notes analyzed: {len(notes)}",
        "",
        "## Per-note Quality Signals",
        "",
        "| Note | Last Seen | Runs | Success | Failures | Resume Points | Score |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for path, entry in sorted(metrics.items(), key=lambda item: (-int(item[1]["quality_score"]), item[0])):
        note = notes[path]
        lines.append(
            "| {note} | {last_seen} | {runs} | {success} | {failures} | {resume} | {score} |".format(
                note=escape_table(note.title),
                last_seen=entry["last_seen"] or "-",
                runs=entry["run_count"],
                success=entry["success_count"],
                failures=entry["failure_count"],
                resume=entry["resume_points"],
                score=entry["quality_score"],
            )
        )

    lines.extend(["", "## Backlink Recommendations", ""])
    if recommendations:
        for left, right, count in recommendations:
            lines.append(f"- Link `[[{notes[left].title}]]` with `[[{notes[right].title}]]` based on {count} shared log event(s).")
    else:
        lines.append("- No new backlink recommendations found.")

    lines.extend(["", "## Unresolved References", ""])
    unique_unresolved = sorted(set(unresolved))
    if unique_unresolved:
        for ref in unique_unresolved:
            lines.append(f"- `{ref}`")
    else:
        lines.append("- None.")

    lines.extend(["", "## Sidecar Metadata Preview", ""])
    for path, entry in sorted(metrics.items()):
        preview = {
            key: entry[key]
            for key in ("last_seen", "run_count", "success_count", "failure_count", "resume_points", "quality_score")
        }
        lines.append(f"- `{path}`: `{json.dumps(preview, sort_keys=True)}`")

    return "\n".join(lines) + "\n"


def escape_table(value: str) -> str:
    return value.replace("|", "\\|")


def sidecar_payloads(metrics: dict[str, dict[str, object]]) -> dict[str, str]:
    payloads: dict[str, str] = {}
    for path, entry in metrics.items():
        sidecar_name = Path(path).with_suffix(".traceweave.json").name
        payload = {
            "last_seen": entry["last_seen"],
            "run_count": entry["run_count"],
            "success_count": entry["success_count"],
            "failure_count": entry["failure_count"],
            "resume_points": entry["resume_points"],
            "quality_score": entry["quality_score"],
        }
        payloads[sidecar_name] = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    return payloads


def emit_sidecar_diff(metadata_dir: str, payloads: dict[str, str]) -> str:
    root = Path(metadata_dir)
    chunks: list[str] = []
    for name, new_text in sorted(payloads.items()):
        target = root / name
        old_text = target.read_text(encoding="utf-8") if target.exists() else ""
        diff = difflib.unified_diff(
            old_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile=str(target),
            tofile=str(target),
        )
        chunks.extend(diff)
    return "".join(chunks)


def write_sidecars(metadata_dir: str, payloads: dict[str, str]) -> None:
    root = Path(metadata_dir)
    root.mkdir(parents=True, exist_ok=True)
    for name, text in payloads.items():
        (root / name).write_text(text, encoding="utf-8")


def write_report(report: str, out_path: str | None) -> None:
    if out_path:
        Path(out_path).write_text(report, encoding="utf-8")
        print(f"Wrote report: {out_path}")
    else:
        print(report, end="")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    api_key_present = bool(os.getenv("TRACEWEAVE_API_KEY"))
    using_sample = not args.notes and not args.logs

    notes = load_notes(args.notes)
    events = load_log_events(args.logs)
    metrics, unresolved, cooccurrence = analyze(notes, events)
    recommendations = backlink_recommendations(notes, cooccurrence, args.min_cooccurrence)

    report = render_report(
        notes=notes,
        metrics=metrics,
        unresolved=unresolved,
        recommendations=recommendations,
        using_sample=using_sample,
        api_key_present=api_key_present,
    )
    write_report(report, args.out)

    if args.metadata_dir:
        payloads = sidecar_payloads(metrics)
        if args.diff:
            diff_text = emit_sidecar_diff(args.metadata_dir, payloads)
            print(diff_text if diff_text else "No sidecar metadata changes.")
        if args.write_sidecar and not args.dry_run:
            write_sidecars(args.metadata_dir, payloads)
            print(f"Wrote sidecar metadata: {args.metadata_dir}")
        elif not args.diff:
            print("Dry run: sidecar metadata was not written. Use --write-sidecar to write files.")

    if args.strict and unresolved:
        print(f"Strict mode failed: {len(set(unresolved))} unresolved reference(s).", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
