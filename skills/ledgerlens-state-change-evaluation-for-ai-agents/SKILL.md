---
name: ledgerlens-state-change-evaluation-for-ai-agents
description: Evaluates AI agent tool traces as auditable state-change ledgers; use for LedgerLens, state-change evaluation, agent-trace-verifier, RAG evals, coding-agent evals, false completion detection, Retrieve Modify Preserve Report scoring.
license: MIT
---

# LedgerLens State-Change Evaluation for AI Agents

Auto-generated and experimental; review results before using them as release gates.

## Overview

LedgerLens evaluates AI agent runs by inspecting state-change evidence instead of judging only the final answer. The bundled `agent-trace-verifier` reference CLI reads a JSONL tool trace, a YAML task specification, and an output directory, then writes a JSON report with principle-level pass/fail diagnostics.

It focuses on four principles:

- Retrieve: expected records, files, or services were accessed.
- Modify: required files, artifacts, or external resources were changed.
- Preserve: protected state was not modified or deleted.
- Report: final claims are supported by observed execution evidence.

## When to use

Use this skill when evaluating RAG systems, coding agents, tool-using assistants, automation pipelines, CI regressions, or false completion reports. Trigger keywords include `LedgerLens`, `state-change evaluation`, `agent-trace-verifier`, `tool trace`, `JSONL trace`, `RAG eval`, `coding-agent eval`, `false completion`, `Retrieve Modify Preserve Report`, and `state ledger`.

## Installation

Copy this skill folder into your skills directory, then run the verifier from the skill root:

```bash
python scripts/run.py
```

No third-party dependencies are required. The CLI reads `LEDGERLENS_API_KEY` if present, but it does not require a key and does not call any external service.

## Usage

Run with built-in sample data:

```bash
python scripts/run.py
```

Run against the included example files:

```bash
python scripts/run.py --trace examples/sample_trace.jsonl --spec examples/sample_task.yaml --out reports
```

Run with your own trace and task spec:

```bash
python scripts/run.py --trace path/to/trace.jsonl --spec path/to/task.yaml --out reports
```

The CLI writes `ledgerlens_report.json` in the output directory and prints a concise summary to stdout.

## Example

Task specification:

```yaml
task: Update export logic while preserving billing configuration.
expected_resources:
  - id: policy_lookup
    match: docs/export_policy.md
required_mutations:
  - id: export_update
    path: src/exporter.py
    operation: write
protected_state:
  - id: billing_config
    path: config/billing.yaml
reporting_obligations:
  - id: mention_tests
    claim: tests were run
    evidence: pytest
```

Verifier command:

```bash
python scripts/run.py --trace examples/sample_trace.jsonl --spec examples/sample_task.yaml --out reports
```

## Limitations

This is a compact reference implementation. It uses a small YAML subset parser when PyYAML is unavailable, applies heuristic matching to trace records, and does not prove semantic correctness of code changes. Treat the report as execution evidence for CI, dashboards, and regression checks, not as a complete replacement for tests, reviews, or human evaluation.
