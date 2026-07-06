---
name: lexipilot-bm25-query-planning-for-agent-tool-routing
description: LexiPilot builds transparent BM25 query plans for agent tool routing when prompts mention tool selection, routing, BM25, lexical retrieval, query planning, audit logs, or router debugging.
license: MIT
---
# LexiPilot -- BM25 Query Planning for Agent Tool Routing

Auto-generated and experimental.

## Overview

Agent tool catalogs often contain overlapping descriptions, so embedding-only routing can choose a plausible but wrong tool. LexiPilot turns a user request into an explicit query plan with required capabilities, exclusions, hard constraints, rare terms, and subqueries, then ranks tools with deterministic BM25-style lexical evidence.

The included reference CLI is intentionally small and self-contained. It provides a working baseline for evaluation, audit logs, regression tests, and hybrid routers that combine lexical ranking with model-based reranking.

## When to use

- Use when choosing tools from a catalog needs transparent, reproducible routing evidence.
- Use when debugging why an agent selected one tool instead of another.
- Use when building regression tests for tool selection, query planning, or router audit logs.
- Use when user requests include exclusions such as "do not use email" or hard requirements such as "must support PDF export".
- Use when decomposing a complex request into multi-tool search subqueries before orchestration.
- When NOT to use: do not use this for final reasoning, task execution, or private data extraction; it only plans and ranks candidate tools.

## Workflow

1. Collect the user request and a tool catalog with stable tool IDs, names, descriptions, and optional capabilities.
2. Run `python scripts/run.py --input examples/sample_input.json` or call `route_tools()` from `scripts/run.py`.
3. Inspect the `query_plan` fields to verify required capabilities, exclusions, constraints, rare terms, and subqueries.
4. Review ranked `candidates`, including matched terms and human-readable evidence.
5. Pass the top candidates to the agent router, a human reviewer, or a downstream reranker.
6. Store the JSON artifact in logs or tests so routing behavior can be reproduced later.

## Inputs & Outputs

Input contract:

- `request`: string user request to route.
- `tools`: array of tool objects.
- Each tool should include `id`, `name`, and `description`.
- Each tool may include `capabilities` as an array of strings.
- CLI options may override `top_k`, `min_score`, and output path.

Exact output shape:

```json
{
  "query_plan": {
    "original_request": "string",
    "normalized_request": "string",
    "high_signal_terms": ["string"],
    "required_capabilities": ["string"],
    "hard_constraints": ["string"],
    "exclusions": ["string"],
    "subqueries": ["string"]
  },
  "candidates": [
    {
      "id": "string",
      "name": "string",
      "score": 0.0,
      "matched_terms": ["string"],
      "evidence": ["string"],
      "excluded": false
    }
  ],
  "excluded_tools": [
    {
      "id": "string",
      "name": "string",
      "reason": "string"
    }
  ],
  "metadata": {
    "algorithm": "bm25-lite",
    "top_k": 3,
    "tool_count": 0,
    "min_score": 0.0
  }
}
```

## Installation

Copy this folder into your Claude Code or OpenClaw skills directory, then run the scripts from the skill root.

```bash
python scripts/run.py --help
python scripts/test.py
```

No package install is required because the reference implementation uses only the Python standard library.

## Usage

Run the built-in self-test:

```bash
python scripts/run.py --selftest
```

Route a request from an input JSON file:

```bash
python scripts/run.py --input examples/sample_input.json
```

Write output to a file:

```bash
python scripts/run.py --input examples/sample_input.json --output examples/sample_output.json
```

Use inline input:

```bash
python scripts/run.py --request "Need transparent BM25 routing with audit logs; do not use email tools" --tools examples/tools.json --top-k 2
```

Environment variables:

- `LEXIPILOT_TOP_K`: default number of candidates when `--top-k` is omitted.
- `LEXIPILOT_MIN_SCORE`: default minimum score for returned candidates.
- `LEXIPILOT_STOPWORDS`: comma-separated extra stopwords to ignore.

## Example

Command:

```bash
python scripts/run.py --input examples/sample_input.json
```

Expected output:

```json
{
  "query_plan": {
    "original_request": "Need transparent BM25 tool routing with audit logs and hard exclusions; do not use email tools.",
    "normalized_request": "need transparent bm25 tool routing with audit logs and hard exclusions do not use email tools",
    "high_signal_terms": [
      "audit",
      "bm25",
      "email",
      "exclusions",
      "logs",
      "routing",
      "tool",
      "tools",
      "transparent"
    ],
    "required_capabilities": [
      "audit",
      "bm25",
      "exclusion",
      "routing"
    ],
    "hard_constraints": [
      "hard exclusions"
    ],
    "exclusions": [
      "email",
      "email tools"
    ],
    "subqueries": [
      "transparent bm25 tool routing",
      "audit logs",
      "exclusions"
    ]
  },
  "candidates": [
    {
      "id": "lexical-router",
      "name": "Lexical Tool Router",
      "score": 6.4926,
      "matched_terms": [
        "audit",
        "bm25",
        "exclusions",
        "logs",
        "routing",
        "tool",
        "tools",
        "transparent"
      ],
      "evidence": [
        "matched high-signal terms: audit, bm25, exclusions, logs, routing, tool, tools, transparent",
        "matched required capabilities: audit, bm25, routing"
      ],
      "excluded": false
    },
    {
      "id": "embedding-router",
      "name": "Embedding Router",
      "score": 1.1827,
      "matched_terms": [
        "routing",
        "tools"
      ],
      "evidence": [
        "matched high-signal terms: routing, tools",
        "matched required capabilities: routing"
      ],
      "excluded": false
    }
  ],
  "excluded_tools": [
    {
      "id": "email-sender",
      "name": "Email Sender",
      "reason": "matched exclusion term: email"
    }
  ],
  "metadata": {
    "algorithm": "bm25-lite",
    "top_k": 3,
    "tool_count": 3,
    "min_score": 0.0
  }
}
```

## Limitations

- The planner is deterministic and heuristic; it does not call an LLM.
- BM25-style lexical scoring cannot infer unstated capabilities or deep semantic equivalence.
- Tool catalog quality strongly affects ranking quality.
- This skill is a reference baseline, not a replacement for orchestration, permissions, or final task execution.
