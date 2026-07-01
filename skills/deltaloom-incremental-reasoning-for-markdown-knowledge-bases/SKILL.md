---
name: deltaloom-incremental-reasoning-for-markdown-knowledge-bases
description: Incrementally analyzes Markdown knowledge-base edits, wikilinks, backlinks, and reusable summaries to build compact reasoning packets; use for triggers md-delta-reason, DeltaLoom, markdown diff, wikilinks, backlinks, incremental reasoning, and knowledge base summaries.
license: MIT
---

# DeltaLoom - Incremental Reasoning for Markdown Knowledge Bases

Auto-generated and experimental; review outputs before using them in production workflows.

## Overview

DeltaLoom helps agents and humans reason over Markdown notes without reprocessing an entire knowledge base after every edit. Its bundled CLI, `md-delta-reason`, compares a previous Markdown note, a current Markdown note, and an optional link graph JSON file.

It identifies changed Markdown blocks, impacted wikilinks and backlinks, reusable unchanged blocks, and compact context packets that can be sent to an LLM, indexing job, or review workflow.

## When to use

Use this skill when a task involves:

- Comparing two versions of a Markdown note.
- Detecting changed paragraphs or blocks before summarization.
- Finding wikilink and backlink impact from a note edit.
- Building a minimal reasoning context packet for an agent or LLM.
- Preserving stable summary blocks instead of regenerating all note summaries.

Useful trigger keywords include `DeltaLoom`, `md-delta-reason`, `incremental reasoning`, `markdown diff`, `wikilinks`, `backlinks`, `knowledge base summaries`, and `reasoning packet`.

## Installation

Copy this folder into a skills directory supported by the target agent runtime.

For direct CLI use, no third-party Python packages are required:

```bash
python scripts/run.py --help
```

Optionally make a shell alias:

```bash
alias md-delta-reason='python scripts/run.py'
```

## Usage

Run the built-in sample:

```bash
python scripts/run.py
```

Analyze example files and print a human-readable report:

```bash
python scripts/run.py \
  --previous examples/previous.md \
  --current examples/current.md \
  --graph examples/link-graph.json \
  --note-title "Project Alpha" \
  --format report
```

Emit machine-readable JSON:

```bash
python scripts/run.py \
  --previous examples/previous.md \
  --current examples/current.md \
  --graph examples/link-graph.json \
  --note-title "Project Alpha" \
  --format json
```

Use a wider context packet around changed blocks:

```bash
python scripts/run.py \
  --previous examples/previous.md \
  --current examples/current.md \
  --graph examples/link-graph.json \
  --context-window 2
```

The script reads optional API-key environment variables such as `DELTALOOM_API_KEY` or `OPENAI_API_KEY`, but it does not call any external service. Without a key, it runs in deterministic local sample mode.

## Example

Given a changed Markdown note, DeltaLoom reports:

- Changed block ranges in the current document.
- Deleted block ranges from the previous document.
- Wikilinks added or removed by the edit.
- Backlinks from the graph that may need refresh.
- Stable blocks that can reuse prior summary artifacts.
- A compact packet containing only changed blocks plus nearby context.

Example command:

```bash
python scripts/run.py --previous examples/previous.md --current examples/current.md --graph examples/link-graph.json --format report
```

## Limitations

- Markdown parsing is intentionally lightweight and standard-library only.
- The diff is block-oriented, so very large paragraphs may produce coarse results.
- Backlink impact depends on the completeness of the supplied link graph JSON.
- The tool builds local reasoning packets; it does not perform LLM summarization.
- Wikilink parsing supports common `[[Note]]`, `[[Note#Heading]]`, and `[[Note|Alias]]` forms, but not every wiki extension.
