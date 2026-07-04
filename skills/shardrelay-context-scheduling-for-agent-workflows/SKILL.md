---
name: shardrelay-context-scheduling-for-agent-workflows
description: Builds stage-specific context bundles from memory shards and workflow DAGs for agent workflows; use for ShardRelay, context scheduling, DAG packing, token budget, memory shard, and handoff prompt triggers.
license: MIT
---

# ShardRelay - Context Scheduling for Agent Workflows
Auto-generated and experimental; validate outputs before using them in production agent runs.

## Overview
Long-running agent workflows often accumulate more memory, logs, and documents than any single context window should carry. ShardRelay treats durable memory as a schedulable resource: it indexes small memory shards, reads a workflow DAG, and emits compact context packs for each execution stage. The bundled script is a deterministic reference implementation for token-budgeted, dependency-aware Markdown context assembly.

## When to use
- Use when a multi-agent workflow needs stage-specific context instead of a full project history dump.
- Use when trigger keywords appear: ShardRelay, context scheduling, context packing, memory shards, workflow DAG, staged agents, handoff prompts, token budget, manifest audit.
- Use when research pipelines, build agents, review agents, or autonomous loops need reproducible context bundles and a manifest explaining inclusion decisions.
- Use when logs, notes, summaries, and prior agent outputs need to be transformed into prompt-ready files such as `stage_001_context.md`.
- When NOT to use: do not use this for real-time retrieval over massive corpora or private hosted services; this skill is a small local scheduler, not a vector database.

## Workflow
1. Collect durable memory into small `.md` or `.txt` shard files. Prefer one idea, decision, log excerpt, or summary per file.
2. Add optional frontmatter to each shard with `id`, `title`, `source_type`, `priority`, `created_at`, and `tags`.
3. Write a workflow JSON file with a `stages` array. Each stage should include `id`, `title`, `task`, optional `depends_on`, optional `budget`, optional `priority_terms`, and optional `required_shards`.
4. Run `python scripts/run.py --workflow <workflow.json> --memory-dir <memory-dir> --out-dir <output-dir>`.
5. Review the emitted `manifest.json` to see selected shards, scores, token estimates, and reasons for inclusion or omission.
6. Use each `stage_###_context.md` file as the active context pack for that agent stage.
7. Re-run after changing shards, budgets, priority terms, or dependencies. The output is deterministic for the same inputs.

## Inputs & Outputs
Input contract:
- Workflow file: JSON object with `stages`, where each stage is an object with:
  - `id` string, required, unique.
  - `title` string, optional.
  - `task` string, required for useful scoring.
  - `depends_on` array of stage ids, optional.
  - `budget` integer estimated-token hard limit, optional.
  - `priority_terms` array of strings, optional.
  - `required_shards` array of shard ids, optional.
- Memory directory: local folder containing `.md` or `.txt` files.
- Shard frontmatter: optional `---` block with simple `key: value` lines. Supported keys are `id`, `title`, `source_type`, `priority`, `created_at`, and `tags`.
- Environment variables: `SHARDRELAY_DEFAULT_BUDGET` and `SHARDRELAY_SOFT_LIMIT_RATIO` may override default CLI values. No API keys are required.

Exact output shape:
- Output directory containing:
  - `manifest.json`
  - One Markdown context file per stage, named `<stage_id>_context.md`.
- `manifest.json` fields:
```json
{
  "tool": "ShardRelay",
  "version": "0.1.0",
  "default_budget": 120,
  "soft_limit_ratio": 0.85,
  "stages": [
    {
      "id": "stage_001",
      "title": "Stage title",
      "depends_on": [],
      "budget": 120,
      "soft_limit": 102,
      "estimated_tokens": 80,
      "output_file": "stage_001_context.md",
      "selected_shards": [
        {
          "id": "project_brief",
          "title": "Project brief",
          "score": 78.0,
          "estimated_tokens": 36,
          "reasons": ["explicitly required", "matches: workflow, shard"]
        }
      ],
      "omitted_shards": [
        {
          "id": "unrelated_note",
          "score": 4.0,
          "estimated_tokens": 22,
          "reason": "below selected candidates or over soft limit"
        }
      ]
    }
  ]
}
```

## Installation
Copy this folder into a Claude Code or OpenClaw-compatible skills directory, or run it directly from this folder.

```bash
python --version
python scripts/run.py --help
python scripts/test.py
```

No third-party dependencies are required.

## Usage
Self-test with built-in sample data:

```bash
python scripts/run.py --selftest
```

Run the example workflow:

```bash
python scripts/run.py \
  --workflow examples/workflow.json \
  --memory-dir examples/memory \
  --out-dir out/example-run
```

Show all CLI options:

```bash
python scripts/run.py --help
```

Tune defaults without editing files:

```bash
SHARDRELAY_DEFAULT_BUDGET=160 SHARDRELAY_SOFT_LIMIT_RATIO=0.8 \
python scripts/run.py --workflow examples/workflow.json --memory-dir examples/memory
```

## Example
Command:

```bash
python scripts/run.py --selftest
```

Expected output:

```json
{
  "selftest": "passed",
  "stages": [
    {
      "id": "stage_001",
      "selected_shards": [
        "project_brief",
        "dag_notes"
      ]
    },
    {
      "id": "stage_002",
      "selected_shards": [
        "handoff_log",
        "project_brief"
      ]
    }
  ]
}
```

The full example output is stored under `examples/expected_output/`.

## Limitations
- Token counts are deterministic estimates based on simple lexical segmentation, not model-specific tokenizer counts.
- Scoring is transparent and local; it does not call embeddings, rerankers, or hosted retrieval services.
- Frontmatter parsing intentionally supports only simple `key: value` lines and list-like `tags`.
- Very large corpora should be pre-sharded and filtered before using this minimal implementation.
- Context packs should be reviewed before use in high-risk or regulated workflows.
