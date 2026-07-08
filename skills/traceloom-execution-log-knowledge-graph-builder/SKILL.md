---
name: traceloom-execution-log-knowledge-graph-builder
description: Converts local AI agent execution logs into Markdown and JSON knowledge graphs; use for TraceLoom, execution logs, JSONL traces, Markdown run logs, Obsidian graph, agent memory, retries, failures, recoveries, and artifacts.
license: MIT
---

# TraceLoom Execution Log Knowledge Graph Builder

Auto-generated and experimental; review outputs before treating them as durable project memory.

## Overview

TraceLoom turns local AI agent run history into explicit graph relationships. It reads JSONL or Markdown execution logs, resolves references to Markdown notes, and writes:

- `graph.json`: machine-readable nodes, edges, timestamps, metadata, confidence scores, and source pointers.
- `edge-index.md`: an Obsidian-friendly Markdown index using edges such as `[[Research Plan]] --failed--> [[Crawler Prototype]]`.

The bundled script is intentionally small and self-contained. It uses only the Python standard library and does not call external services.

## When to use

Use this skill when a user asks to:

- Build a knowledge graph from agent logs, terminal transcripts, or automation traces.
- Convert JSONL traces or Markdown run notes into navigable relationships.
- Index failures, retries, recoveries, generated artifacts, and decision lineage.
- Create an Obsidian-friendly memory layer for agentic workflows, research vaults, or coding notebooks.

Trigger keywords include TraceLoom, execution log graph, JSONL trace, Markdown run log, Obsidian edge index, agent memory, failed attempt, retry, recovery, artifact lineage, and knowledge graph builder.

## Installation

From this skill directory, no dependency installation is required:

```bash
python --version
python scripts/run.py --help
```

To install as a local reusable skill, copy this folder into your skills directory. Example:

```bash
export SKILL_HOME="${SKILL_HOME:-.codex/skills}"
mkdir -p "$SKILL_HOME"
cp -R . "$SKILL_HOME/traceloom-execution-log-knowledge-graph-builder"
```

## Usage

Run with built-in sample data:

```bash
python scripts/run.py
```

Run against the included example files:

```bash
python scripts/run.py --logs examples/sample-run.jsonl --notes examples/notes --out traceloom-output
```

Preview detected relationships without writing files:

```bash
python scripts/run.py --logs examples/sample-run.jsonl --notes examples/notes --dry-run
```

Index multiple logs and merge with an existing output graph:

```bash
python scripts/run.py --logs path/to/run.jsonl path/to/run.md --notes path/to/notes --out path/to/output --incremental
```

Optional environment variables:

```bash
TRACELOOM_API_KEY=unused-by-reference-script python scripts/run.py --dry-run
```

The reference script only records whether an optional key was configured; it never prints or sends the secret.

## Example

Input JSONL event:

```json
{"timestamp":"2026-01-15T09:13:00Z","type":"failure","source":"[[Research Plan]]","target":"[[Crawler Prototype]]","message":"The crawler timed out while following the plan."}
```

Output edge:

```markdown
[[Research Plan]] --failed--> [[Crawler Prototype]]
```

Output files are written to `traceloom-output/` by default.

## Limitations

- Relationship extraction is heuristic and optimized for readable local logs, not arbitrary natural language.
- Markdown note matching is deterministic but simple: wikilinks, filenames, headings, aliases, and exact title mentions work best.
- The graph schema is compact and intended as a reference implementation, not a full graph database.
- Incremental mode merges by deterministic edge IDs but does not delete stale edges.
