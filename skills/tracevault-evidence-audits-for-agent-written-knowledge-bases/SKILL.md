---
name: tracevault-evidence-audits-for-agent-written-knowledge-bases
description: Run TraceVault evidence audits for agent-written Markdown knowledge bases when checking vault diffs, wikilinks, citations, frontmatter, broken references, or required output fields.
license: MIT
---

# TraceVault - Evidence Audits for Agent-Written Knowledge Bases

Auto-generated and experimental; validate results before using them as a release or benchmark gate.

## Overview

TraceVault is a local audit workflow for Markdown knowledge bases. It compares a pre-task vault directory with a post-task vault directory, inspects observable file changes, and checks those changes against a small YAML expectation file.

The bundled CLI reports created, modified, deleted, and unchanged notes; new wikilinks; backlinks; broken references; orphaned notes; frontmatter fields; required headings; required structured output fields; cited evidence nodes; and simple unsupported `Claim:` lines.

## When to use

Use this skill when an agent or LLM workflow has edited a Markdown vault and you need evidence of what changed rather than a polished final answer. Trigger keywords include TraceVault, evidence audit, vault audit, Markdown knowledge base, wikilink audit, broken references, citation tracking, frontmatter validation, and agent-written notes.

Good fits:

- Agentic research and synthesis notes.
- Paper review vaults.
- Wiki maintenance tasks.
- CI checks for required sections, evidence links, or broken wikilinks.
- Benchmark harnesses that need a machine-readable `evidence_audit.json`.

## Installation

Copy this skill folder into your Claude Code or OpenClaw-compatible skills directory using the skill name as the folder name:

```sh
mkdir -p ../skills
cp -R . ../skills/tracevault-evidence-audits-for-agent-written-knowledge-bases
```

No Python packages are required. The script uses only the Python standard library.

## Usage

Run the built-in sample audit:

```sh
python scripts/run.py
```

Audit the included example vaults and write a report:

```sh
python scripts/run.py \
  --before examples/before_vault \
  --after examples/after_vault \
  --expectations examples/audit.yaml \
  --out evidence_audit.json
```

Fail the process when the audit does not pass:

```sh
python scripts/run.py \
  --before examples/before_vault \
  --after examples/after_vault \
  --expectations examples/audit.yaml \
  --out evidence_audit.json \
  --fail-on-fail
```

## Example

`examples/audit.yaml` defines a task contract:

```yaml
task: Build a cited synthesis note
rules:
  required_created_notes:
    - synthesis.md
  required_modified_notes:
    - index.md
  required_frontmatter_fields:
    - title
    - evidence_status
  required_sections:
    - Summary
    - Evidence
  required_output_fields:
    - Decision
  required_evidence_nodes:
    - sources/paper-a.md
  min_new_wikilinks: 2
  max_broken_links: 0
  max_unsupported_claims: 0
```

The output is JSON with a score, rule verdicts, changed files, new links, broken references, orphaned notes, backlinks, and unsupported claims.

## Limitations

- The YAML reader intentionally supports a small subset: nested mappings, scalar values, and lists of scalars.
- Markdown parsing is lightweight and regex-based.
- Wikilink resolution uses direct paths and note stems; duplicate note names can be ambiguous.
- Unsupported-claim detection only checks lines beginning with `Claim:`.
- This tool audits local Markdown evidence; it does not verify the truth of cited sources.
