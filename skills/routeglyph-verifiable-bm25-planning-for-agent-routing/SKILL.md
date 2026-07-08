---
name: routeglyph-verifiable-bm25-planning-for-agent-routing
description: Generates verifiable BM25-style routing plans for multi-agent/tool selection when requests mention RouteGlyph, agent routing, BM25 planning, tool catalogs, or routing regression tests.
version: 0.1.0
license: MIT
---

# RouteGlyph — Verifiable BM25 Planning for Agent Routing
Auto-generated and experimental; review outputs before using them in production routing.

## Overview
RouteGlyph helps make agent and tool routing inspectable by turning a user request and a catalog of tools into explicit BM25-style candidate plans. It uses deterministic tokenization, inverse document frequency scoring, synonym expansion, exclusions, and constraint checks so routing behavior can be logged, reviewed, and regression-tested.

The included reference script is intentionally small and local. It does not replace an LLM router; it prepares transparent ranked candidates for a router, policy engine, or orchestrator to consume.

## When to use
- Use when building or debugging multi-agent routing, tool selection, or orchestration logic.
- Use when a team needs routing decisions that can be versioned, diffed, snapshotted, or tested in CI.
- Use when a request mentions trigger terms such as `RouteGlyph`, `BM25 routing`, `agent routing`, `tool catalog`, `routing plan`, `sparse retrieval`, or `routing regression`.
- Use before an LLM router when you want a deterministic shortlist and score rationale.
- When NOT to use: do not use this as the only decision layer for high-risk actions without policy checks, permissions, and human or system validation.

## Workflow
1. Prepare a tool catalog with `id`, `name`, `description`, and optional `keywords`, `synonyms`, `exclusions`, and `constraints`.
2. Provide a user query directly with `--query` or through a text file with `--query-file`.
3. Run `scripts/run.py` against the catalog to generate ranked JSON candidates.
4. Inspect each candidate's `score`, `rare_terms`, `matched_terms`, `synonyms`, `exclusions`, `constraints`, and `rationales`.
5. Feed the candidate JSON to an LLM router, rules engine, test harness, or orchestrator.
6. Store expected JSON snapshots for important routing cases and compare them during regression tests.

## Inputs & Outputs
Input contract:
- `query`: a non-empty natural-language user request.
- `catalog`: JSON, a small supported YAML subset, inline CLI tools, or the built-in self-test catalog.
- Each catalog tool accepts:
  - `id`: stable machine-readable identifier.
  - `name`: display name.
  - `description`: searchable natural-language description.
  - `keywords`: optional list or comma-separated string.
  - `synonyms`: optional list or comma-separated string.
  - `exclusions`: optional list or comma-separated string that penalizes a candidate when matched.
  - `constraints`: optional list of capability flags such as `local_only`, `code_required`, `freshness_required`, or `regression_testable`.

Exact output shape:

```json
{
  "plan_version": "routeglyph.v1",
  "tokenizer": "routeglyph-tokenizer.v1",
  "query": "original query",
  "query_terms": ["token"],
  "required_constraints": ["constraint_id"],
  "candidates": [
    {
      "rank": 1,
      "tool_id": "tool_id",
      "tool_name": "Tool Name",
      "score": 0.0,
      "rare_terms": ["term"],
      "matched_terms": [
        {
          "term": "term",
          "query_weight": 1.0,
          "tool_tf": 1,
          "idf": 0.0,
          "contribution": 0.0
        }
      ],
      "synonyms": [
        {
          "source": "query_term",
          "expanded": ["expanded_term"]
        }
      ],
      "exclusions": {
        "configured": ["term"],
        "triggered": ["term"]
      },
      "constraints": {
        "required": ["constraint_id"],
        "matched": ["constraint_id"],
        "missing": ["constraint_id"]
      },
      "rationales": ["short explanation"]
    }
  ]
}
```

## Installation
Copy or install this skill directory into a Claude Code/OpenClaw-compatible skills folder.

```bash
python3 --version
python3 scripts/run.py --help
python3 scripts/test.py
```

No external Python packages are required.

## Usage
Show the CLI help:

```bash
python3 scripts/run.py --help
```

Run the built-in deterministic self-test:

```bash
python3 scripts/run.py --selftest
```

Run against the included examples:

```bash
python3 scripts/run.py --catalog examples/tools.json --query-file examples/query.txt --pretty
```

Use inline tool definitions:

```bash
python3 scripts/run.py \
  --query "Route this to a local Python test writer" \
  --tool "code_agent|Code Agent|Writes local Python scripts and tests|python,tests,local" \
  --tool "research_agent|Research Agent|Finds current facts on the public web|web,current,sources" \
  --pretty
```

Optionally configure defaults through environment variables:

```bash
ROUTEGLYPH_LIMIT=2 python3 scripts/run.py --selftest
ROUTEGLYPH_SYNONYMS_JSON='{"router":["routing","orchestrator"]}' python3 scripts/run.py --selftest
```

## Example
Command:

```bash
python3 scripts/run.py --catalog examples/tools.json --query-file examples/query.txt --pretty
```

Expected top-level result:

```json
{
  "plan_version": "routeglyph.v1",
  "tokenizer": "routeglyph-tokenizer.v1",
  "query": "Route an agent request to build a local regression-testable BM25 router with no API key.",
  "candidates": [
    {
      "rank": 1,
      "tool_id": "route_planner",
      "tool_name": "Route Planner"
    }
  ]
}
```

See `examples/expected_output.json` for the full expected output.

## Limitations
- The YAML loader supports only a small catalog-friendly subset, not arbitrary YAML.
- Tokenization is intentionally simple and English-focused.
- Synonym expansion is local and deterministic, so domain teams should version their own synonym maps.
- Scores are useful for ranking and regression snapshots, not as calibrated probabilities.
- This reference implementation is a candidate generator, not a full authorization or policy layer.

## Verification
Automated execution check: **passed ✅**.

- Steps: structure=ok · syntax=ok · help=ok · selftest=ok · test=ok
- Commands and outputs shown in `README.md` are captured from these real runs.
