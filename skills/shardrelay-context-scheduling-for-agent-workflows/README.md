# ShardRelay - Context Scheduling for Agent Workflows

ShardRelay is a small installable skill for turning workflow DAGs and memory shards into stage-specific context packs. It emits Markdown files for agent prompts and a deterministic manifest explaining why each shard was included.

## Install

Copy this folder into your Claude Code or OpenClaw-compatible skills directory, or run it directly:

```bash
python scripts/run.py --help
python scripts/test.py
```

No third-party packages are required.

## Usage

Run the built-in self-test:

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

Run the included example:

```bash
python scripts/run.py \
  --workflow examples/workflow.json \
  --memory-dir examples/memory \
  --out-dir out/example-run
```

Then inspect:

```bash
ls out/example-run
cat out/example-run/manifest.json
cat out/example-run/stage_001_context.md
```

## Input Shape

Workflow JSON:

```json
{
  "stages": [
    {
      "id": "stage_001",
      "title": "Plan shard index",
      "task": "Plan a workflow DAG parser and memory shard index.",
      "budget": 230,
      "priority_terms": ["workflow", "dag", "shard"],
      "required_shards": ["project_brief"]
    }
  ]
}
```

Shard files are `.md` or `.txt` files with optional frontmatter:

```markdown
---
id: project_brief
title: Project brief
source_type: brief
priority: 5
created_at: 2026-01-01
tags: [shardrelay, context, workflow]
---

ShardRelay builds context bundles from memory shards for each workflow stage.
```

## Environment Variables

- `SHARDRELAY_DEFAULT_BUDGET`: default estimated-token budget when a stage omits `budget`.
- `SHARDRELAY_SOFT_LIMIT_RATIO`: soft packing ratio from `0` to `1`.

No API keys are needed.
