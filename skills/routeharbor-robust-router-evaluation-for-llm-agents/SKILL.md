---
name: routeharbor-robust-router-evaluation-for-llm-agents
description: Evaluates LLM agent router robustness with worst-group regret and perturbation stability; use for route evaluation, tool routing, model routing, agent orchestration, query logs, and router CI.
license: MIT
---

# RouteHarbor - Robust Router Evaluation for LLM Agents

Auto-generated & experimental skill for small, auditable router evaluations.

## Overview

RouteHarbor evaluates how reliably an LLM agent router chooses tools, specialist models, or downstream agents across different query groups. It treats router quality as a robustness problem instead of a single average hit rate.

The bundled script compares candidate routers against labeled query logs and produces a structured JSON report with:

- Average accuracy.
- Per-group accuracy and loss.
- Worst-group loss.
- Worst-group regret versus the best router for each group.
- Perturbation-aware stability under group distribution shift.
- A recommended router configuration for production evaluation.

## When to use

Use this skill when evaluating:

- Tool routers for agent systems.
- Model routers for multi-model applications.
- Specialist-agent orchestration policies.
- Retrieval, tool-use, or modality-aware routing layers.
- Query logs grouped by modality, intent, cluster, customer segment, or custom metadata.

Trigger keywords include: route evaluation, router robustness, tool routing, model routing, agent routing, worst-group regret, perturbation stability, distribution shift, query log evaluation, routing CI.

## Installation

Copy this folder into your skills directory or keep it in a project repository as a runnable reference skill.

No Python packages are required. The script uses the Python standard library.

## Usage

Run the built-in mock evaluation:

```bash
python scripts/run.py
```

Evaluate example files:

```bash
python scripts/run.py \
  --queries examples/query_log.jsonl \
  --decisions examples/router_decisions.json \
  --output routeharbor-report.json
```

Evaluate custom groups:

```bash
python scripts/run.py \
  --queries examples/query_log.jsonl \
  --decisions examples/router_decisions.json \
  --group-fields intent,modality,cluster \
  --epsilon 0.25
```

Input query logs should be JSONL records with an `id`, an expected route label such as `expected_route`, and optional metadata fields:

```json
{"id":"q1","query":"Summarize this support thread","expected_route":"search","modality":"text","intent":"retrieval","cluster":"support"}
```

Router decisions can be a JSON object mapping router names to query-id predictions:

```json
{
  "router_a": {"q1": "search"},
  "router_b": {"q1": "tool_planner"}
}
```

## Example

```bash
python scripts/run.py --queries examples/query_log.jsonl --decisions examples/router_decisions.json
```

The script prints a short ranking and writes a JSON report to standard output unless `--output` is provided.

## Limitations

- The perturbation score is an approximate group reweighting stress test, not a full optimal transport solver.
- Ground-truth route labels are required.
- The evaluator does not call LLM APIs or generate router decisions.
- Small groups can dominate worst-group metrics, so review group counts before making production decisions.
