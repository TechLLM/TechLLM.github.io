---
name: failwise-worst-case-token-budget-tuning-for-llm-agents
description: Tune LLM agent token budgets, retrieval depth, and retry policies against worst-case failure slices; use for Failwise, token budget tuning, agent regression analysis, Pareto policy ranking, and worst-slice reliability reviews.
license: MIT
---

# Failwise - Worst-Case Token Budget Tuning for LLM Agents

Auto-generated and experimental; review outputs before using them for production budget decisions.

## Overview

Failwise is a small CLI-oriented skill for evaluating LLM agent execution budget policies against historical task logs. It compares candidate token limits, retrieval depths, and tool retry counts, then ranks policies by reliability, estimated cost, latency impact, and worst-slice failure behavior.

The bundled reference implementation is self-contained and framework-agnostic. It reads JSONL execution logs and a simple YAML or JSON policy file, computes policy outcomes, reports Pareto-efficient candidates, and can export a JSON report for CI or local review.

## When to use

Use this skill when you need to:

- Tune LLM agent token limits, retrieval depth, or tool retry counts.
- Compare budget policies before a deployment.
- Analyze regressions in long-context, tool-heavy, low-confidence, or flaky workflows.
- Find Pareto-efficient policies across reliability, cost, and latency.
- Review worst-case failure slices instead of relying only on average cost or latency.

Trigger keywords include Failwise, token budget tuning, worst-case agent evaluation, LLM budget policy, Pareto policy ranking, retrieval depth tuning, tool retry tuning, and worst-slice failure rate.

## Installation

Copy this folder into your Claude Code, OpenClaw, or compatible skills directory.

```bash
python scripts/run.py
```

No third-party Python package is required. The optional `FAILWISE_DEFAULT_MODEL` environment variable can label reports when logs omit a model name.

## Usage

Run with built-in sample data:

```bash
python scripts/run.py
```

Run with example files:

```bash
python scripts/run.py --logs examples/sample_logs.jsonl --policies examples/policies.yaml
```

Write a machine-readable report:

```bash
python scripts/run.py --logs examples/sample_logs.jsonl --policies examples/policies.yaml --output examples/report.json
```

Focus failure slices on specific fields:

```bash
python scripts/run.py --slice-fields task_type tool_name retrieval_band context_band metadata.workflow
```

## Example

```bash
python scripts/run.py --logs examples/sample_logs.jsonl --policies examples/policies.yaml --output failwise-report.json
```

The command prints a ranked table with success rate, estimated cost, latency, worst-slice failure rate, and Pareto status. The JSON report includes per-policy metrics and the worst slices that drove each ranking.

## Limitations

- The YAML parser intentionally supports a small policy-file subset: top-level `policies`, list items, scalar values, and `key: value` pairs.
- Metrics are estimates derived from historical logs, not a simulator of every possible future agent behavior.
- Policy effects use transparent heuristics for token, retrieval, and retry constraints; adapt the script if your system has richer execution traces.
- It does not call model APIs or require orchestration-framework-specific logs.
