---
name: deltaloom-context-diff-planning-for-llm-agents
description: Generate incremental context-diff plans for LLM agent workflows; use for DeltaLoom, context diff, summary refresh, JSON Patch, incremental planning, changed-block manifests, and agent context reuse.
license: MIT
---

# DeltaLoom — Context Diff Planning for LLM Agents

Auto-generated & experimental reference skill.

## Overview

DeltaLoom helps an agent compare an older context snapshot with a newer input set and decide which blocks can be reused, refreshed, deleted, split, or merged. It is intended for long-running coding agents, research agents, note processors, retrieval pipelines, and CI jobs that need auditable incremental context updates instead of repeatedly re-summarizing everything.

The bundled CLI chunks Markdown, source code, or plain text; fingerprints each block; matches unchanged content even when order shifts; emits a changed-block manifest; creates summary refresh tasks; infers simple dependency invalidations from `[block:block-id]` references; and produces deterministic JSON Patch operations for updating a stored snapshot.

## When to use

Use this skill when the user mentions DeltaLoom, context diff planning, incremental agent context, summary refresh planning, JSON Patch context updates, changed-block manifests, reducing redundant LLM reasoning, summary drift, or dependency-aware invalidation.

## Installation

From this skill folder:

```bash
mkdir -p "$HOME/.claude/skills/deltaloom-context-diff-planning-for-llm-agents"
cp -R SKILL.md README.md scripts examples "$HOME/.claude/skills/deltaloom-context-diff-planning-for-llm-agents/"
```

No Python package installation is required. The reference CLI uses only the Python standard library.

## Usage

Run the built-in sample:

```bash
python scripts/run.py
```

Compare the included example snapshots and print a compact summary:

```bash
python scripts/run.py --previous examples/context_previous.md --current examples/context_current.md --format summary
```

Write a machine-readable plan to a file:

```bash
python scripts/run.py --previous examples/context_previous.md --current examples/context_current.md --output examples/plan.json
```

Use paragraph chunking for plain text:

```bash
python scripts/run.py --previous old_notes.txt --current new_notes.txt --chunk paragraphs
```

Use a custom delimiter:

```bash
python scripts/run.py --previous old.txt --current new.txt --chunk delimiter --delimiter "=== block ==="
```

The script reads optional `DELTALOOM_API_KEY` or `OPENAI_API_KEY` environment variables only to report whether external agent configuration is present. It does not send data to any external service.

## Example

```bash
python scripts/run.py --previous examples/context_previous.md --current examples/context_current.md --format summary
```

Example output:

```text
DeltaLoom plan
Blocks: previous=4 current=5
Manifest:
- reuse: agent-context
- reuse: running-log
- refresh: repository-map
- refresh: api-notes
- add: open-questions
Summary tasks:
- reuse: agent-context
- refresh: running-log
- refresh: repository-map
- refresh: api-notes
- refresh: open-questions
Dependency hints:
- running-log invalidated by api-notes
JSON Patch operations: 5
```

## Limitations

- Chunking is heuristic, not a full Markdown, language, or AST parser.
- Dependency invalidation is based on explicit `[block:block-id]` references.
- Split and merge detection uses lightweight text similarity.
- JSON Patch output is deterministic but not minimized for the fewest possible operations.
- This is a reference implementation for planning and integration, not a hosted service.
