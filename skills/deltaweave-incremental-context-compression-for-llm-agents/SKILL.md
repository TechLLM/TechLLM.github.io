---
name: deltaweave-incremental-context-compression-for-llm-agents
description: Incrementally compresses changed Markdown/code/RAG context into JSON, Markdown, or agent prompts when users mention DeltaWeave, incremental context compression, delta packs, context diffing, or agent memory updates.
license: MIT
---

# DeltaWeave - Incremental Context Compression for LLM Agents

Auto-generated and experimental; validate outputs before using them in production agent workflows.

## Overview

DeltaWeave helps agents focus on what changed instead of rereading an entire document. It compares a previous snapshot with a current snapshot and emits a compact delta pack containing meaningful changed regions, nearby context, and stable anchors.

The bundled script supports Markdown heading-aware diffs, lightweight function/class boundary detection for common code files, and general line/block/file-level comparison. It can produce JSON for pipelines, Markdown reports for humans, or an agent-ready prompt for targeted resummarization.

## When to use

Use this skill when a task mentions:

- DeltaWeave
- incremental context compression
- delta packs
- context diffing
- agent memory updates
- RAG context updates
- summarizing only document changes
- reducing token cost after a file changes

## Installation

Copy this folder into a skill directory supported by your agent runtime.

For local CLI use, no third-party dependencies are required:

```bash
python scripts/run.py
```

## Usage

Run with built-in sample data:

```bash
python scripts/run.py
```

Compare two Markdown snapshots and emit Markdown:

```bash
python scripts/run.py --old examples/previous.md --new examples/current.md --format markdown
```

Emit structured JSON for an integration:

```bash
python scripts/run.py --old examples/previous.md --new examples/current.md --format json --granularity heading
```

Emit an agent-ready compression prompt:

```bash
python scripts/run.py --old examples/previous.md --new examples/current.md --format prompt --context-lines 3
```

Compare code by function/class boundaries:

```bash
python scripts/run.py --old examples/previous.py --new examples/current.py --granularity function --format markdown
```

Optional environment variables such as `DELTAWEAVE_API_KEY` or `OPENAI_API_KEY` may be present, but the bundled reference CLI never sends data to a network service and does not require an API key.

## Example

```bash
python scripts/run.py --old examples/previous.md --new examples/current.md --format prompt
```

The output includes changed sections, line ranges, nearby context, unchanged anchors, and instructions an LLM can use to update an existing working summary.

## Limitations

- Function and class extraction is heuristic, not a full parser.
- Markdown section tracking is heading-aware but does not understand every flavor of Markdown.
- Moved or heavily rewritten sections may appear as delete/add pairs.
- The script performs local text comparison only; it does not call LLM APIs.
- Delta packs reduce context size, but a reviewer or agent still needs the prior summary to apply updates correctly.
