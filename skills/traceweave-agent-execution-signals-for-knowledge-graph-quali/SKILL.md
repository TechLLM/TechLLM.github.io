---
name: traceweave-agent-execution-signals-for-knowledge-graph-quali
description: Enrich Markdown knowledge graphs with agent execution signals and use it when trigger keywords include TraceWeave, execution logs, knowledge graph quality, Obsidian metadata, retrieval trust, backlinks, and resume points.
license: MIT
---

# TraceWeave - Agent Execution Signals for Knowledge Graph Quality

Auto-generated & experimental: this skill is a small working reference implementation, not a production data pipeline.

## Overview

TraceWeave helps agents evaluate Markdown knowledge bases using operational evidence from execution logs. It reads a folder of Markdown notes and JSONL or plain-text logs, resolves note mentions, counts successful and failed use, records resume evidence, and produces a reviewable Markdown report with per-note quality metadata and backlink recommendations.

The bundled script is intentionally local and self-contained. It does not require external services, and it uses built-in sample data when run without input paths.

## When to use

Use this skill when a user wants to:

- Improve retrieval quality for an Obsidian-style vault or Markdown note graph.
- Analyze agent execution logs for which sources were used, trusted, failed, or resumed.
- Generate metadata such as `last_seen`, `run_count`, `success_count`, `failure_count`, and `resume_points`.
- Find candidate backlinks from log evidence, file references, wikilinks, and co-occurrence.
- Produce a human-reviewable report before changing a knowledge base.

Trigger keywords: TraceWeave, execution logs, knowledge graph quality, Obsidian, retrieval trust, note metadata, backlinks, agent traces, resume points.

## Installation

Copy this folder into your skill directory or install it using your agent runtime's local skill installation flow.

No Python dependencies are required. The script uses only the Python standard library.

## Usage

Run with built-in sample notes and logs:

```bash
python scripts/run.py
```

Analyze the included example folder and write a report:

```bash
python scripts/run.py --notes examples/notes --logs examples/logs --out traceweave-report.md
```

Preview sidecar metadata changes as a unified diff:

```bash
python scripts/run.py --notes examples/notes --logs examples/logs --metadata-dir .traceweave --diff
```

Write sidecar metadata JSON files:

```bash
python scripts/run.py --notes examples/notes --logs examples/logs --metadata-dir .traceweave --write-sidecar
```

Fail if log references cannot be resolved to notes:

```bash
python scripts/run.py --notes examples/notes --logs examples/logs --strict
```

Optional environment variable:

```bash
TRACEWEAVE_API_KEY=unused-local-placeholder python scripts/run.py
```

The key is read only to demonstrate secret-safe configuration. This reference implementation does not call external APIs.

## Example

Given Markdown notes in `examples/notes` and execution logs in `examples/logs`, TraceWeave resolves evidence such as `[[Retrieval Pipeline]]`, `notes/Agent Resume.md`, and repeated mentions in command text. It emits a Markdown report with:

- A per-note metrics table.
- Unresolved references.
- Candidate backlink recommendations.
- Sidecar metadata preview or files when requested.

## Limitations

- The frontmatter parser supports common simple YAML shapes, not every YAML feature.
- Mention resolution is heuristic and best suited to small or medium Markdown vaults.
- Plain-text log parsing uses pattern matching and may miss project-specific event formats.
- The bundled scoring model is a transparent baseline, not a statistically validated quality model.
- The script never mutates note frontmatter; it writes optional sidecar metadata only when `--write-sidecar` is used.
