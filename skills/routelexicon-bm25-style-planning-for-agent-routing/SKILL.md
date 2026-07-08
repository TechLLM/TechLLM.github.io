---
name: routelexicon-bm25-style-planning-for-agent-routing
description: Builds transparent BM25-style routing plans for multi-agent requests and should be used for RouteLexicon, BM25 routing, agent routing, manifest selection, keyword evidence, and subquery decomposition.
version: 0.1.0
license: MIT
---

# RouteLexicon - BM25-Style Planning for Agent Routing

Auto-generated and experimental.

## Overview

RouteLexicon helps route user requests across multiple agents by turning plain JSON agent manifests into explicit lexical routing evidence. It uses standard-library tokenization, corpus IDF, BM25-inspired scoring, keyword boosts, exclusion penalties, and subquery decomposition so a router can explain why an agent matched.

The approach is intentionally small and inspectable: first plan the lexical evidence, then pass the ranked plan to an orchestrator, logger, test harness, or LLM-powered router.

## When to use

- Use when choosing among multiple agents from natural-language requests.
- Use when you need transparent evidence for why an agent was selected or rejected.
- Use when agent manifests are available as JSON descriptions, capabilities, keywords, synonyms, exclusions, and optional term weights.
- Use when trigger keywords appear: RouteLexicon, BM25 routing, agent routing, routing plan, manifest selection, keyword evidence, rare terms, exclusions, subquery decomposition.
- When NOT to use: do not use this as a semantic embedding replacement for tasks that require deep reasoning over hidden context or private tools.

## Workflow

1. Create a JSON manifest with an `agents` array.
2. Give each agent an `id`, `name`, `description`, and optional `capabilities`, `keywords`, `synonyms`, `exclude_terms`, and `term_weights`.
3. Provide a request with `--query` or `--query-file`.
4. Run `python scripts/run.py --manifest <manifest.json> --query "<request>" --pretty`.
5. Inspect `ranked_agents` for BM25-style scores, matched terms, rare terms, exclusion evidence, and rationale.
6. Use `routing_plan.selected_agent_ids` for a simple route, or use `routing_plan.decomposed_subqueries` for multi-agent orchestration.
7. Add tests around expected selected agents and exclusion behavior before using the route in production.

## Inputs & Outputs

Input contract:

```json
{
  "agents": [
    {
      "id": "research-agent",
      "name": "Research Agent",
      "description": "Finds evidence and compares sources.",
      "capabilities": ["internet research", "source comparison"],
      "keywords": ["research", "sources", "evidence"],
      "synonyms": {"look up": ["research"]},
      "exclude_terms": ["code"],
      "term_weights": {"evidence": 1.4}
    }
  ]
}
```

Output shape:

```json
{
  "version": "0.1.0",
  "request": "user request text",
  "query_terms": ["sorted", "expanded", "terms"],
  "idf": {
    "agent_count": 3,
    "average_document_length": 24.67
  },
  "ranked_agents": [
    {
      "agent_id": "research-agent",
      "name": "Research Agent",
      "score": 3.1234,
      "matched_terms": [{"term": "research", "idf": 0.47, "tf": 3}],
      "rare_terms": [{"term": "evidence", "idf": 0.98}],
      "excluded_by": [],
      "weights": {
        "bm25": 2.7,
        "keyword_boost": 0.4234,
        "exclusion_penalty": 0.0,
        "final": 3.1234
      },
      "rationale": "Matched research and evidence; rare clues: evidence."
    }
  ],
  "routing_plan": {
    "selected_agent_ids": ["research-agent"],
    "decomposed_subqueries": [
      {
        "id": "q1",
        "text": "research competitors",
        "terms": ["competitors", "research"],
        "candidate_agent_ids": ["research-agent"]
      }
    ],
    "excluded_agents": [
      {"agent_id": "coding-agent", "terms": ["market"]}
    ]
  }
}
```

## Installation

Copy or install this skill directory into your skills folder, then run it with Python 3.10 or newer. No external packages are required.

```bash
python --version
python scripts/run.py --help
python scripts/test.py
```

## Usage

Run the built-in deterministic self-test:

```bash
python scripts/run.py --selftest
```

Route a request against the example manifest:

```bash
python scripts/run.py --manifest examples/agents.json --query-file examples/request.txt --pretty
```

Save JSON output:

```bash
python scripts/run.py --manifest examples/agents.json --query "Research competitors and summarize current market evidence" --output route-plan.json
```

Optional environment variables:

```bash
ROUTELEXICON_K1=1.5 ROUTELEXICON_B=0.75 ROUTELEXICON_TOP_K=2 python scripts/run.py --selftest
```

Help:

```bash
python scripts/run.py --help
```

## Example

Command:

```bash
python scripts/run.py --manifest examples/agents.json --query-file examples/request.txt --pretty
```

Expected first selected agent:

```json
{
  "routing_plan": {
    "selected_agent_ids": ["research-agent"]
  }
}
```

The full expected output is in `examples/expected_output.json`.

## Limitations

- This is lexical routing, not semantic understanding.
- BM25-style scores are comparable within one manifest, not across unrelated manifests.
- Synonym expansion is simple and manifest-driven.
- Exclusion terms are hard lexical penalties and may be too strict for ambiguous requests.
- The CLI is intended as a reference implementation, not a high-throughput routing service.

## Verification
Automated execution check: **passed ✅**.

- Steps: structure=ok · syntax=ok · help=ok · selftest=ok · test=ok
- Commands and outputs shown in `README.md` are captured from these real runs.
