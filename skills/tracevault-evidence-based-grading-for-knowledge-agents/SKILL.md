---
name: tracevault-evidence-based-grading-for-knowledge-agents
description: Evidence-based grading for Markdown knowledge-base agents; use for TraceVault, kb-task-grader, vault evaluation, evidence grading, Markdown benchmark, and agent QA tasks.
license: MIT
---

# TraceVault — Evidence-Based Grading for Knowledge Agents

Auto-generated and experimental; review outputs before using them as authoritative benchmark results.

## Overview

TraceVault helps evaluate agents that work in Markdown knowledge bases, documentation vaults, and linked-note systems. Instead of grading only the final answer, it checks observable changes between before-and-after vault snapshots.

The bundled `kb-task-grader` reference script compares two Markdown vault directories against an expectation file and emits a deterministic JSON report. It checks created files, required file changes, forbidden edits, wiki links, Markdown links, citations, and frontmatter fields.

## When to use

Use this skill when you need to:

- Grade an agent's Markdown vault work with evidence-based checks.
- Test whether expected notes, links, citations, and metadata updates happened.
- Produce JSON reports for CI, benchmark dashboards, or local QA.
- Investigate unexpected mutations in a knowledge-base task.

Trigger keywords include: TraceVault, kb-task-grader, evidence grading, Markdown vault benchmark, linked-note evaluation, frontmatter validation, citation checks, and agent QA.

## Installation

Copy this folder into your skills directory, or install it with your agent runtime's local skill installation mechanism.

No Python packages are required. The reference script uses only the Python standard library.

## Usage

Run the built-in demo:

```bash
python scripts/run.py --pretty
```

Grade the included example vault:

```bash
python scripts/run.py \
  --before examples/before \
  --after examples/after \
  --expectations examples/expectations.yml \
  --pretty
```

Write a report to a file:

```bash
python scripts/run.py \
  --before examples/before \
  --after examples/after \
  --expectations examples/expectations.yml \
  --out report.json
```

The script optionally reads `TRACEVAULT_API_KEY` from the environment for compatibility with hosted harnesses, but the reference implementation does not call external services.

## Example

Expectation files use a small YAML subset:

```yaml
created_files:
  - notes/agent-evaluation.md
modified_files:
  - notes/index.md
forbidden_edits:
  - notes/source.md
required_links:
  - from: notes/agent-evaluation.md
    to: notes/source.md
required_citations:
  - file: notes/agent-evaluation.md
    contains: "[[source]]"
frontmatter:
  notes/agent-evaluation.md:
    status: reviewed
    tags:
      contains:
        - benchmark
```

## Limitations

- This is a compact reference implementation, not a complete Markdown parser.
- The YAML reader supports the simple expectation shapes shown in `examples/expectations.yml`.
- Link extraction covers common wiki links and inline Markdown links, not every Markdown extension.
- Binary files and non-Markdown assets are ignored.
- Frontmatter parsing supports simple scalar values, inline lists, and block lists.
