---
name: pathloom-critical-path-prioritization-for-agent-memory
description: Prioritize agent trace memory by critical-path relevance; use for PathLoom, critical path, agent memory, context pruning, prefetch, trace JSONL, and memory prioritization workflows.
license: MIT
---

# PathLoom - Critical-Path Prioritization for Agent Memory

Auto-generated and experimental: validate recommendations before using them in production agent memory pipelines.

## Overview

Long-running agent traces often contain more context than the next model call can use. PathLoom ranks trace items by whether they sit on the next action's critical path, combining dependency edges, explicit references, recency, and item type into an explainable `critical_path_priority` score.

This skill helps an assistant or user inspect JSONL traces, identify high-value evidence to prefetch, and find low-value or redundant context that can be delayed or pruned.

## When to use

Use this skill when an agent workflow mentions critical-path memory, context pruning, memory prioritization, trace JSONL, prefetch recommendations, long-running agent traces, dependency-aware context management, or PathLoom.

Concrete trigger scenarios:

- You need to decide which messages, tool results, constraints, observations, or notes should stay in a constrained context window.
- You have agent trace JSONL and want deterministic `critical_path_priority` scores with reasons.
- You want pruning recommendations for redundant or low-priority memory items.
- You want prefetch recommendations for evidence that may block the next action.
- You are evaluating an agent framework's memory behavior and need an inspectable rule-based baseline.

When NOT to use: do not use this as a semantic search engine or as the only safety filter for sensitive, regulated, or production-critical data.

## Workflow

1. Prepare trace data as JSONL with one object per line. Each item should include `id`, `type`, and optional `content`, `depends_on`, `references`, `timestamp`, or `next_action` fields.
2. Run `python scripts/run.py --input TRACE.jsonl` to score the trace, or pipe JSONL into `python scripts/run.py --input -`.
3. Optionally provide the next action with `--next-action "..."` or `PATHLOOM_NEXT_ACTION` so PathLoom can detect directly referenced evidence.
4. Optionally tune scoring with `--weights "recency=0.2,dependency=0.45,explicit=0.25,type=0.1"` or `PATHLOOM_WEIGHTS`.
5. Review `items` sorted by `critical_path_priority`, then inspect `recommendations.prefetch`, `recommendations.keep`, `recommendations.delay`, and `recommendations.prune`.
6. Apply the recommendations to the agent memory layer, keeping the `reasons` field with any audit log or evaluation artifact.

## Inputs & Outputs

Input contract:

- Format: JSONL from a file or stdin.
- Required field: `id` as a unique string.
- Recommended fields: `type`, `content` or `text`, `depends_on`, `references`, `timestamp`.
- Dependency fields: `depends_on`, `references`, `input_ids`, `source_ids`, `parent_id`, `tool_call_id`, and `observation_id`.
- Next-action hints: a trace item with `type: "next_action"` or `next_action: true`, a `references` list, or CLI/env text containing `@item_id`, `#item_id`, or the raw item id.

Output shape:

```json
{
  "summary": {
    "item_count": 0,
    "edge_count": 0,
    "next_action": "",
    "weights": {
      "recency": 0.2,
      "dependency": 0.45,
      "explicit": 0.25,
      "type": 0.1
    },
    "thresholds": {
      "prefetch": 0.72,
      "prune": 0.28
    }
  },
  "items": [
    {
      "id": "item_id",
      "type": "tool_result",
      "critical_path_priority": 0.0,
      "recommendation": "prefetch",
      "depends_on": ["dependency_id"],
      "referenced_by": ["future_item_id"],
      "reasons": ["human-readable scoring reason"]
    }
  ],
  "edges": [
    {
      "from": "future_item_id",
      "to": "dependency_id",
      "reason": "depends_on"
    }
  ],
  "recommendations": {
    "prefetch": [{"id": "item_id", "priority": 0.0, "why": "reason"}],
    "keep": [],
    "delay": [],
    "prune": []
  }
}
```

## Installation

Copy the skill directory into your local skills folder:

```bash
mkdir -p ~/.claude/skills/pathloom-critical-path-prioritization-for-agent-memory
cp -R . ~/.claude/skills/pathloom-critical-path-prioritization-for-agent-memory/
```

No third-party Python dependencies are required.

## Usage

Show CLI help:

```bash
python scripts/run.py --help
```

Run the built-in self-test sample:

```bash
python scripts/run.py --selftest
```

Score an example trace:

```bash
python scripts/run.py --input examples/sample_trace.jsonl
```

Pipe JSONL through stdin:

```bash
cat examples/sample_trace.jsonl | python scripts/run.py --input -
```

Tune weights and thresholds:

```bash
PATHLOOM_PRUNE_THRESHOLD=0.3 python scripts/run.py \
  --input examples/sample_trace.jsonl \
  --weights "recency=0.2,dependency=0.45,explicit=0.25,type=0.1"
```

Run the tiny test suite:

```bash
python scripts/test.py
```

## Example

Input:

```bash
python scripts/run.py --input examples/sample_trace.jsonl
```

Expected output is deterministic JSON matching `examples/expected_output.json`. The highest-priority items include the next action, the tool call it references, and the evidence and constraint needed for the next action:

```json
{
  "id": "t2",
  "type": "tool_call",
  "recommendation": "prefetch"
}
```

## Limitations

- PathLoom is rule-based and does not understand semantic equivalence beyond simple duplicate content normalization.
- Dependency quality depends on trace quality; missing ids or omitted references reduce accuracy.
- Scores are meant for prioritization and inspection, not for access control, compliance decisions, or data-loss prevention.
- The CLI is a minimal reference implementation, not a distributed memory store or agent framework integration.
