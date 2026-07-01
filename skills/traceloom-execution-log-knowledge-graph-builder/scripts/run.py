#!/usr/bin/env python3
"""TraceLoom reference CLI: build a small graph from local execution logs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


VERSION = "0.1.0"

BUILTIN_LOGS = [
    {
        "timestamp": "2026-01-15T09:00:00Z",
        "type": "task_created",
        "source": "[[Research Plan]]",
        "target": "[[Crawler Prototype]]",
        "message": "Started crawler prototype from the research plan.",
    },
    {
        "timestamp": "2026-01-15T09:13:00Z",
        "type": "failure",
        "source": "[[Research Plan]]",
        "target": "[[Crawler Prototype]]",
        "message": "The crawler timed out while following the plan.",
    },
    {
        "timestamp": "2026-01-15T09:20:00Z",
        "type": "recovery",
        "source": "[[Crawler Prototype]]",
        "target": "[[Patch Notes]]",
        "message": "Patch notes describe the timeout guard that recovered the prototype.",
    },
    {
        "timestamp": "2026-01-15T09:40:00Z",
        "type": "artifact",
        "source": "[[Patch Notes]]",
        "target": "[[Demo Artifact]]",
        "message": "Generated a small demo artifact after the patch.",
    },
]

BUILTIN_NOTES = {
    "Research Plan": {
        "path": "built-in-notes/Research Plan.md",
        "aliases": ["trace plan"],
        "headings": ["Goal"],
    },
    "Crawler Prototype": {
        "path": "built-in-notes/Crawler Prototype.md",
        "aliases": ["crawler"],
        "headings": ["Failure"],
    },
    "Patch Notes": {
        "path": "built-in-notes/Patch Notes.md",
        "aliases": ["timeout patch"],
        "headings": ["Recovery"],
    },
    "Demo Artifact": {
        "path": "built-in-notes/Demo Artifact.md",
        "aliases": ["demo output"],
        "headings": ["Result"],
    },
}

RELATION_KEYWORDS = [
    ("recovered-by", ("recovery", "recovered", "fixed", "resolved", "mitigated")),
    ("retried", ("retry", "retried", "rerun", "reran", "again")),
    ("failed", ("failure", "failed", "error", "exception", "timeout", "blocked")),
    ("produced", ("artifact", "generated", "output", "wrote", "emitted")),
    ("updated", ("updated", "edited", "note_update", "changed")),
    ("created", ("created", "task_created", "plan_created", "started", "opened")),
    ("executed", ("command", "executed", "shell", "cli")),
]

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+?\.md)(?:#[^)]+)?\)")
MD_FILE_RE = re.compile(r"(?<![\w/.-])([A-Za-z0-9][A-Za-z0-9 _-]{1,80}\.md)(?![\w/.-])")


@dataclass
class NoteRef:
    title: str
    confidence: float
    evidence: str


@dataclass
class NoteIndex:
    notes: dict[str, dict[str, Any]]
    aliases: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_folder(cls, folder: Path) -> "NoteIndex":
        notes: dict[str, dict[str, Any]] = {}
        if folder.exists():
            for path in sorted(folder.rglob("*.md")):
                text = path.read_text(encoding="utf-8")
                title = path.stem
                aliases, headings = parse_note_metadata(text)
                rel_path = path.as_posix()
                notes[title] = {
                    "id": title,
                    "label": title,
                    "type": "note",
                    "path": rel_path,
                    "aliases": aliases,
                    "headings": headings,
                }
        if not notes:
            notes = {
                title: {
                    "id": title,
                    "label": title,
                    "type": "note",
                    "path": data["path"],
                    "aliases": data["aliases"],
                    "headings": data["headings"],
                }
                for title, data in BUILTIN_NOTES.items()
            }

        index = cls(notes=notes)
        for title, data in notes.items():
            index._add_alias(title, title)
            index._add_alias(Path(str(data.get("path", title))).stem, title)
            for alias in data.get("aliases", []):
                index._add_alias(str(alias), title)
            for heading in data.get("headings", []):
                index._add_alias(str(heading), title)
        return index

    def _add_alias(self, alias: str, title: str) -> None:
        cleaned = normalize_key(alias)
        if cleaned:
            self.aliases[cleaned] = title

    def resolve(self, raw: str, confidence: float = 0.8, evidence: str = "text") -> NoteRef:
        label = clean_ref(raw)
        key = normalize_key(label)
        if key in self.aliases:
            return NoteRef(self.aliases[key], confidence, evidence)
        if label.lower().endswith(".md"):
            stem_key = normalize_key(Path(label).stem)
            if stem_key in self.aliases:
                return NoteRef(self.aliases[stem_key], confidence, evidence)
        return NoteRef(label, min(confidence, 0.7), evidence)

    def extract_refs(self, text: str) -> list[NoteRef]:
        refs: list[NoteRef] = []
        seen: set[str] = set()

        def add(ref: NoteRef) -> None:
            if ref.title and ref.title not in seen:
                seen.add(ref.title)
                refs.append(ref)

        for match in WIKILINK_RE.findall(text):
            add(self.resolve(match, 0.95, "wikilink"))
        for match in MD_LINK_RE.findall(text):
            add(self.resolve(Path(match).stem, 0.85, "markdown-link"))
        for match in MD_FILE_RE.findall(text):
            add(self.resolve(Path(match).stem, 0.8, "filename"))

        lowered = f" {text.lower()} "
        for alias, title in sorted(self.aliases.items(), key=lambda item: (-len(item[0]), item[0])):
            if len(alias) < 4 or title in seen:
                continue
            if re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", lowered):
                add(NoteRef(title, 0.65, "title-or-alias"))
        return refs


def normalize_key(value: str) -> str:
    return re.sub(r"\s+", " ", clean_ref(value).lower()).strip()


def clean_ref(value: str) -> str:
    value = str(value).strip()
    if value.startswith("[[") and value.endswith("]]"):
        value = value[2:-2]
    value = value.split("|", 1)[0].split("#", 1)[0]
    value = value.replace("\\", "/").strip()
    if value.lower().endswith(".md"):
        value = Path(value).stem
    return value.strip("`'\" ")


def parse_note_metadata(text: str) -> tuple[list[str], list[str]]:
    aliases: list[str] = []
    headings: list[str] = []
    lines = text.splitlines()
    in_frontmatter = len(lines) > 0 and lines[0].strip() == "---"
    alias_block = False

    if in_frontmatter:
        for line in lines[1:]:
            stripped = line.strip()
            if stripped == "---":
                break
            if stripped.startswith("aliases:"):
                alias_block = True
                raw = stripped.split(":", 1)[1].strip()
                aliases.extend(parse_alias_value(raw))
                continue
            if alias_block and stripped.startswith("- "):
                aliases.append(stripped[2:].strip().strip("'\""))
                continue
            alias_block = False

    for line in lines:
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if match:
            headings.append(match.group(1).strip())

    return unique(aliases), unique(headings)


def parse_alias_value(raw: str) -> list[str]:
    if not raw:
        return []
    if raw.startswith("[") and raw.endswith("]"):
        return [part.strip().strip("'\"") for part in raw[1:-1].split(",") if part.strip()]
    return [raw.strip().strip("'\"")]


def unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        value = str(value).strip()
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def classify_relation(text: str) -> str:
    lowered = text.lower()
    for relation, keywords in RELATION_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return relation
    return "related-to"


def event_text(event: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("type", "action", "status", "message", "summary", "command", "source", "target", "from", "to", "note", "artifact"):
        value = event.get(key)
        if value is not None:
            parts.append(value_to_text(value))
    for key in ("files", "artifacts", "notes"):
        value = event.get(key)
        if value is not None:
            parts.append(value_to_text(value))
    return " ".join(parts)


def value_to_text(value: Any) -> str:
    if isinstance(value, (list, tuple, set)):
        return " ".join(value_to_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(f"{key} {value_to_text(val)}" for key, val in sorted(value.items()))
    return str(value)


def refs_from_value(value: Any, note_index: NoteIndex, confidence: float, evidence: str) -> list[NoteRef]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        refs: list[NoteRef] = []
        for item in value:
            refs.extend(refs_from_value(item, note_index, confidence, evidence))
        return dedupe_refs(refs)
    text = value_to_text(value)
    extracted = note_index.extract_refs(text)
    if extracted:
        return extracted
    return [note_index.resolve(text, confidence, evidence)]


def dedupe_refs(refs: Iterable[NoteRef]) -> list[NoteRef]:
    best: dict[str, NoteRef] = {}
    for ref in refs:
        current = best.get(ref.title)
        if current is None or ref.confidence > current.confidence:
            best[ref.title] = ref
    return [best[key] for key in sorted(best)]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            event = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON in {path.as_posix()}:{line_number}: {exc}") from exc
        if not isinstance(event, dict):
            raise SystemExit(f"Expected JSON object in {path.as_posix()}:{line_number}")
        event["_source_path"] = path.as_posix()
        event["_source_line"] = line_number
        events.append(event)
    return events


def load_markdown_events(path: Path, note_index: NoteIndex) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        refs = note_index.extract_refs(line)
        if len(refs) < 2:
            continue
        events.append(
            {
                "timestamp": None,
                "type": classify_relation(line),
                "source": refs[0].title,
                "target": refs[1].title,
                "message": line.strip(),
                "_source_path": path.as_posix(),
                "_source_line": line_number,
            }
        )
    return events


def load_events(paths: list[Path], note_index: NoteIndex) -> list[dict[str, Any]]:
    if not paths:
        events = []
        for index, event in enumerate(BUILTIN_LOGS, start=1):
            copied = dict(event)
            copied["_source_path"] = "built-in-sample.jsonl"
            copied["_source_line"] = index
            events.append(copied)
        return events

    events: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            raise SystemExit(f"Log file not found: {path.as_posix()}")
        suffix = path.suffix.lower()
        if suffix == ".jsonl":
            events.extend(load_jsonl(path))
        elif suffix in {".md", ".markdown", ".txt"}:
            events.extend(load_markdown_events(path, note_index))
        else:
            raise SystemExit(f"Unsupported log format: {path.as_posix()} (use .jsonl, .md, .markdown, or .txt)")
    return events


def edge_id(source: str, relation: str, target: str, path: str, line: int | None, timestamp: str | None) -> str:
    raw = json.dumps(
        {
            "source": source,
            "relation": relation,
            "target": target,
            "path": path,
            "line": line,
            "timestamp": timestamp,
        },
        sort_keys=True,
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def build_graph(events: list[dict[str, Any]], note_index: NoteIndex, min_confidence: float) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = dict(note_index.notes)
    edges: dict[str, dict[str, Any]] = {}

    for event in events:
        relation = classify_relation(event_text(event))
        explicit_sources = refs_from_value(event.get("source", event.get("from", event.get("note"))), note_index, 0.95, "explicit-source")
        explicit_targets = refs_from_value(event.get("target", event.get("to", event.get("artifact"))), note_index, 0.95, "explicit-target")

        if not explicit_targets and event.get("command"):
            command_label = "Command: " + " ".join(str(event["command"]).split())[:90]
            explicit_targets = [NoteRef(command_label, 0.8, "command")]

        if explicit_sources and explicit_targets:
            source_refs = explicit_sources
            target_refs = explicit_targets
        else:
            refs = note_index.extract_refs(event_text(event))
            if len(refs) < 2:
                continue
            source_refs = [refs[0]]
            target_refs = refs[1:]

        for ref in source_refs + target_refs:
            nodes.setdefault(
                ref.title,
                {
                    "id": ref.title,
                    "label": ref.title,
                    "type": "reference",
                    "path": None,
                    "aliases": [],
                    "headings": [],
                },
            )

        for source_ref in source_refs:
            for target_ref in target_refs:
                if source_ref.title == target_ref.title:
                    continue
                confidence = round(min(source_ref.confidence, target_ref.confidence), 2)
                if confidence < min_confidence:
                    continue
                source_path = str(event.get("_source_path", "unknown"))
                source_line = event.get("_source_line")
                timestamp = event.get("timestamp")
                eid = edge_id(source_ref.title, relation, target_ref.title, source_path, source_line, timestamp)
                edges[eid] = {
                    "id": eid,
                    "from": source_ref.title,
                    "to": target_ref.title,
                    "relation": relation,
                    "timestamp": timestamp,
                    "confidence": confidence,
                    "source": {"path": source_path, "line": source_line},
                    "event_type": event.get("type") or event.get("action") or event.get("status"),
                    "metadata": compact_metadata(event),
                }

    return {
        "metadata": {
            "generated_by": "TraceLoom reference CLI",
            "version": VERSION,
            "latest_event_timestamp": latest_event_timestamp(events),
            "api_key_configured": bool(os.environ.get("TRACELOOM_API_KEY")),
            "source_event_count": len(events),
            "note_count": len(note_index.notes),
        },
        "nodes": sorted(nodes.values(), key=lambda node: node["id"].lower()),
        "edges": sorted(edges.values(), key=lambda edge: (edge["from"].lower(), edge["relation"], edge["to"].lower(), edge["id"])),
    }


def latest_event_timestamp(events: list[dict[str, Any]]) -> str | None:
    timestamps = sorted(str(event["timestamp"]) for event in events if event.get("timestamp"))
    return timestamps[-1] if timestamps else None


def compact_metadata(event: dict[str, Any]) -> dict[str, Any]:
    skipped = {"_source_path", "_source_line", "source", "from", "target", "to", "timestamp"}
    metadata: dict[str, Any] = {}
    for key, value in sorted(event.items()):
        if key in skipped:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            metadata[key] = value
        elif isinstance(value, list):
            metadata[key] = [item for item in value if isinstance(item, (str, int, float, bool))]
    return metadata


def merge_graphs(existing: dict[str, Any], new_graph: dict[str, Any]) -> dict[str, Any]:
    nodes = {node["id"]: node for node in existing.get("nodes", []) if isinstance(node, dict) and "id" in node}
    edges = {edge["id"]: edge for edge in existing.get("edges", []) if isinstance(edge, dict) and "id" in edge}
    for node in new_graph["nodes"]:
        nodes[node["id"]] = node
    for edge in new_graph["edges"]:
        edges[edge["id"]] = edge
    merged = dict(new_graph)
    merged["nodes"] = sorted(nodes.values(), key=lambda node: node["id"].lower())
    merged["edges"] = sorted(edges.values(), key=lambda edge: (edge["from"].lower(), edge["relation"], edge["to"].lower(), edge["id"]))
    merged["metadata"]["incremental"] = True
    merged["metadata"]["previous_edge_count"] = len(existing.get("edges", []))
    return merged


def write_outputs(graph: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    graph_path = out_dir / "graph.json"
    edge_path = out_dir / "edge-index.md"
    graph_path.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    edge_path.write_text(render_edge_index(graph), encoding="utf-8")
    return graph_path, edge_path


def render_edge_index(graph: dict[str, Any]) -> str:
    lines = [
        "# TraceLoom Edge Index",
        "",
        f"Generated by TraceLoom reference CLI {graph['metadata'].get('version', VERSION)}.",
        "",
        "## Edges",
        "",
    ]
    if not graph["edges"]:
        lines.append("No edges detected.")
    for edge in graph["edges"]:
        source = render_wikilink(edge["from"])
        target = render_wikilink(edge["to"])
        pointer = edge.get("source", {})
        location = pointer.get("path", "unknown")
        if pointer.get("line"):
            location = f"{location}:{pointer['line']}"
        lines.append(
            f"- {source} --{edge['relation']}--> {target} "
            f"(confidence: {edge['confidence']:.2f}, source: {location})"
        )
    lines.append("")
    return "\n".join(lines)


def render_wikilink(title: str) -> str:
    safe = str(title).replace("[", "(").replace("]", ")")
    return f"[[{safe}]]"


def print_dry_run(graph: dict[str, Any]) -> None:
    print(f"TraceLoom dry run: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")
    for edge in graph["edges"]:
        print(f"{render_wikilink(edge['from'])} --{edge['relation']}--> {render_wikilink(edge['to'])} [{edge['confidence']:.2f}]")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a small knowledge graph from local execution logs.")
    parser.add_argument("--logs", nargs="*", default=[], help="JSONL, Markdown, or text log files to parse.")
    parser.add_argument("--notes", default="examples/notes", help="Folder containing Markdown notes used for reference matching.")
    parser.add_argument("--out", default="traceloom-output", help="Output directory for graph.json and edge-index.md.")
    parser.add_argument("--dry-run", action="store_true", help="Print detected edges without writing output files.")
    parser.add_argument("--incremental", action="store_true", help="Merge new edges with an existing graph.json in the output directory.")
    parser.add_argument("--min-confidence", type=float, default=0.45, help="Minimum edge confidence to include.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    note_index = NoteIndex.from_folder(Path(args.notes))
    events = load_events([Path(path) for path in args.logs], note_index)
    graph = build_graph(events, note_index, args.min_confidence)

    out_dir = Path(args.out)
    existing_path = out_dir / "graph.json"
    if args.incremental and existing_path.exists():
        existing = json.loads(existing_path.read_text(encoding="utf-8"))
        graph = merge_graphs(existing, graph)

    if args.dry_run:
        print_dry_run(graph)
        return 0

    graph_path, edge_path = write_outputs(graph, out_dir)
    print(f"Wrote {len(graph['nodes'])} nodes and {len(graph['edges'])} edges.")
    print(f"Graph JSON: {graph_path.as_posix()}")
    print(f"Edge index: {edge_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
