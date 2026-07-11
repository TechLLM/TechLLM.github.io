---
name: surfacepilot-failure-surface-routing-profiler-for-llm-agents
description: SurfacePilot profiles LLM agent failure surfaces from trace JSONL and exports routing policies; use for router evals, RAG failures, agent traces, tool routing, guardrails, CI evals, and failure-surface profiling.
version: 0.1.0
license: MIT
---

# SurfacePilot - Failure-Surface Routing Profiler for LLM Agents
Auto-generated and experimental; review generated policies before using them in production routing.

## Overview
LLM and agent routers often look good when final answers pass, while hidden execution failures still cluster around retrieval, editing, API calls, citations, calculations, or state changes. SurfacePilot treats routing as a failure-surface classification problem: it reads trace JSONL, aggregates execution evidence, detects repeated failure signals, and exports a routing policy that can guide model selection, tools, guardrails, fallbacks, and eval coverage.

## When to use
- Use when evaluating an agent router from JSONL traces, especially for RAG routing, tool routing, CI evals, nightly benchmark runs, regression analysis, or guardrail design.
- Use when failures need to be explained by execution surface, such as retrieval, file_edit, api_call, calculation, citation, state_change, planning, or custom labels.
- Use when you need a deterministic YAML profile that turns raw evaluator signals into concrete routing rules.
- When NOT to use: do not use this as a replacement for task-specific correctness evaluation or human review of high-risk state-changing actions.

## Workflow
1. Export agent traces as JSONL, one event per line, with at least `surface` and a pass/fail signal such as `success`.
2. Include useful routing metadata when available: `task_id`, `task_type`, `model`, `route`, `tool`, `signal`, and `message`.
3. Run `python scripts/run.py --input trace.jsonl` to produce a YAML surface profile.
4. Inspect `summary`, `matrix`, and `patterns` to find surfaces and routes with repeated failures.
5. Review `routing_policy.rules` and copy only the rules that match your production router design.
6. Add new evaluator coverage for surfaces with high failure rates or weak evidence.
7. Re-run the profiler in CI, nightly evals, or benchmark pipelines after router or prompt changes.

## Inputs & Outputs
Input is JSONL. Each line must be a JSON object with this contract:

```json
{
  "task_id": "task-001",
  "task_type": "support_qa",
  "model": "small-router",
  "route": "rag_fast",
  "tool": "retriever",
  "surface": "retrieval",
  "success": false,
  "signal": "stale_retrieval",
  "message": "optional short evaluator note"
}
```

Required fields: `surface` plus one pass/fail field. Supported pass/fail fields are `success`, `passed`, `status`, `outcome`, or `result`. Missing metadata fields are normalized to `"unknown"`.

Default output is YAML with this shape:

```yaml
summary:
  events: int
  passed: int
  failed: int
  failure_rate: float
  surfaces:
    surface_name:
      events: int
      passed: int
      failed: int
      fail_rate: float
matrix:
  - task_type: string
    model: string
    route: string
    tool: string
    surface: string
    signal: string
    events: int
    passed: int
    failed: int
    fail_rate: float
patterns:
  - signal: string
    surface: string
    count: int
    task_ids:
      - string
    routes:
      - string
    tools:
      - string
routing_policy:
  version: string
  thresholds:
    failure_threshold: float
    min_failures: int
  rules:
    - id: string
      match:
        task_type: string
        surface: string
      when: string
      action:
        - string
      evidence:
        events: int
        failures: int
        fail_rate: float
        top_signals:
          - string
        routes:
          - string
        models:
          - string
```

Use `--format json` to emit the same fields as JSON.

## Installation
This skill is self-contained and uses only the Python standard library.

```bash
python --version
python scripts/run.py --help
python scripts/test.py
```

Optional environment variables:

```bash
export SURFACEPILOT_FAILURE_THRESHOLD=0.34
export SURFACEPILOT_MIN_FAILURES=1
```

## Usage
Run the built-in sample:

```bash
python scripts/run.py --selftest
```

Profile an example trace:

```bash
python scripts/run.py --input examples/trace.jsonl
```

Write YAML to a file:

```bash
python scripts/run.py --input examples/trace.jsonl --output surfacepilot-profile.yaml
```

Emit JSON:

```bash
python scripts/run.py --input examples/trace.jsonl --format json
```

Show CLI help:

```bash
python scripts/run.py --help
```

## Example
Command:

```bash
python scripts/run.py --input examples/trace.jsonl
```

Expected output is deterministic and is stored in `examples/expected_output.yaml`. It begins with:

```yaml
summary:
  events: 5
  passed: 1
  failed: 4
  failure_rate: 0.8
```

## Limitations
- SurfacePilot clusters failures by explicit evaluator signals; it does not infer semantic root cause from long natural-language traces.
- The generated routing policy is a recommendation artifact, not a production router.
- YAML output is generated by a small built-in serializer for deterministic, dependency-free output.
- The bundled profiler is intentionally minimal; production use should add schema validation and domain-specific evaluator signals.

## Verification
Automated execution check: **passed ✅**.

- Steps: structure=ok · syntax=ok · help=ok · selftest=ok · test=ok
- Commands and outputs shown in `README.md` are captured from these real runs.
