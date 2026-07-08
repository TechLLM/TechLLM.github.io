---
name: contexttrellis-hub-aware-context-budget-compressor
description: Compresses Obsidian-style Markdown vaults into hub-aware LLM context bundles; use for ContextTrellis, context budget, hub notes, long-tail execution notes, retrieval compression, and prompt packing.
version: 0.1.0
license: MIT
---

# ContextTrellis — Hub-Aware Context Budget Compressor
Auto-generated and experimental; review outputs before relying on them in production workflows.

## Overview
Large Markdown vaults often contain central hub notes that dominate retrieval because they link everywhere, while small execution notes contain the details an agent actually needs. ContextTrellis builds a simple knowledge graph, compresses high-centrality hub notes into short orientation blocks, and preserves execution-heavy long-tail notes closer to their original form. The included CLI is a minimal reference implementation for creating deterministic, auditable context bundles before an LLM call.

## When to use
- Use when an Obsidian-style vault has hub notes, MOCs, indexes, or architecture summaries that consume too much prompt space.
- Use when long-tail notes contain operational details such as API polling rules, dry-run logs, command quirks, error handling, deployment steps, or incident checklists.
- Use when you need a transparent token-budget plan showing which notes were included, compressed, or skipped.
- Use when trigger keywords appear: ContextTrellis, context budget, hub-aware compression, long-tail notes, execution notes, prompt packing, retrieval compression.
- When NOT to use: do not use this as a semantic search replacement for tasks that require full-text factual recall across every document.

## Workflow
1. Put the skill folder in your skills directory or run it in place from this repository.
2. Prepare a folder of Markdown notes. Wikilinks, Markdown links, tags, headings, and front matter are supported.
3. Run `python scripts/run.py --input <vault-folder> --budget <tokens> --reserve <tokens>`.
4. Review the JSON bundle: `hub_summary` items should provide orientation, while `preserved_detail` items should retain execution-critical notes.
5. Feed the `items[].content` values, plus the `decisions` log if auditability matters, into the target LLM or agent framework.
6. Adjust `--budget`, `--reserve`, `--max-note-tokens`, and `--hub-summary-tokens` until the bundle fits the intended prompt window.

## Inputs & Outputs
Input contract:
- `--input`: optional path to a Markdown file or folder. If omitted, `--selftest` sample data is used.
- Markdown files may contain YAML-like front matter, headings, wikilinks like `[[API Polling]]`, Markdown links like `[Errors](Error Handling.md)`, tags like `#api`, and fenced code blocks.
- Environment overrides are supported for non-secret defaults: `CONTEXTTRELLIS_BUDGET`, `CONTEXTTRELLIS_RESERVE_TOKENS`, and `CONTEXTTRELLIS_OUTPUT_FORMAT`.

Exact JSON output shape:
```json
{
  "bundle_version": "0.1",
  "mode": "selftest-or-vault",
  "input": "relative-or-sample-label",
  "budget": {
    "requested_tokens": 620,
    "reserve_tokens": 80,
    "available_tokens": 540,
    "used_tokens": 0
  },
  "graph": {
    "notes": 0,
    "edges": 0,
    "hubs": [],
    "long_tail": []
  },
  "items": [
    {
      "id": "Note.md",
      "path": "Note.md",
      "role": "hub_summary",
      "tokens": 0,
      "centrality": 0.0,
      "execution_score": 0.0,
      "reason": "why this item was included",
      "content": "context text"
    }
  ],
  "decisions": [
    {
      "id": "Note.md",
      "role": "hub_summary",
      "action": "included",
      "tokens": 0,
      "reason": "budget and scoring decision"
    }
  ]
}
```

## Installation
```bash
# Run in place
python scripts/run.py --help

# Optional install pattern for a local skills directory
mkdir -p ./skills
cp -R . ./skills/contexttrellis-hub-aware-context-budget-compressor
```

The reference CLI uses only the Python standard library, so no package installation is required.

## Usage
```bash
python scripts/run.py --help
python scripts/run.py --selftest
python scripts/run.py --input examples/vault --budget 620 --reserve 80 --format json
python scripts/run.py --input examples/vault --budget 620 --reserve 80 --format markdown
python scripts/test.py
```

## Example
Command:
```bash
python scripts/run.py --input examples/vault --budget 620 --reserve 80 --format json
```

Expected output is stored in `examples/expected_output.json`. It includes one compressed hub summary and several preserved execution-detail notes, with a decision log that explains each inclusion.

## Limitations
- Token counts are estimates based on whitespace, not tokenizer-specific counts.
- Hub summaries are extractive and deterministic; they are not LLM-generated abstractive summaries.
- The graph model uses degree centrality only, so it is intentionally simpler than PageRank or embedding-based retrieval.
- Markdown parsing is practical rather than exhaustive and may miss unusual link syntaxes.

## Verification
Automated execution check: **passed ✅**.

- Steps: structure=ok · syntax=ok · help=ok · selftest=ok · test=ok
- Commands and outputs shown in `README.md` are captured from these real runs.
