---
name: routeledger-benchmark-casebooks-for-agent-routing
description: Converts agent routing logs into deterministic benchmark casebooks when auditing routers, creating routing evals, stratifying splits, or checking coverage keywords routeledger, agent routing, router benchmark, casebook, routing logs.
license: MIT
---

# RouteLedger — Benchmark Casebooks for Agent Routing

Auto-generated and experimental.

## Overview

Agent routers often decide which model, tool, or agent path handles a task, but those decisions are commonly left as short-lived logs. RouteLedger turns routing logs into durable benchmark casebooks by validating router metadata, stratifying examples, and exporting reproducible train, validation, and test splits. Use it to evaluate whether routing behavior generalizes across modality, domain, selected tool, task type, and outcome.

## When to use

- Use when a team has JSONL routing logs and wants benchmark-ready samples for router evaluation.
- Use when comparing router versions across domains, modalities, selected tools, task types, or success/failure outcomes.
- Use when publishing a small reproducible casebook with coverage and weak-slice summaries.
- Use when validating whether production routing logs have missing, inconsistent, or ambiguous metadata.
- When NOT to use: do not use this for sensitive production logs until private data has been removed or replaced with safe task descriptions.

## Workflow

1. Collect routing decisions as JSONL records with `task`, `modality`, `domain`, `selected_tool`, `task_type`, and either `outcome` or `success`.
2. Remove secrets, private data, and unnecessary raw payloads from the logs before processing.
3. Run `python scripts/run.py --input ROUTING_LOGS.jsonl --output-dir out` to build the casebook.
4. Review `out/manifest.json` for validation errors, split membership, coverage counts, and weak slices.
5. Inspect `out/summary.md` for a compact human-readable report.
6. Use `out/cases.jsonl` or `out/cases.csv` as benchmark inputs for router comparisons.
7. Re-run with a fixed `--seed` to reproduce the same casebook split.

## Inputs & Outputs

Input contract: a UTF-8 JSONL file where each non-empty line is a JSON object. Required fields are `task`, `modality`, `domain`, `selected_tool`, and `task_type`; each record also needs `outcome` set to success/failure text or `success` set to a boolean-like value. Optional identifiers may be provided as `id` or `task_id`; otherwise the script assigns a stable line-based id.

Output shape:

```json
{
  "tool": "RouteLedger",
  "version": "0.1.0",
  "seed": 13,
  "ratios": {"train": 0.6, "validation": 0.2, "test": 0.2},
  "record_count": 6,
  "valid_record_count": 6,
  "invalid_record_count": 0,
  "splits": {"train": ["id"], "validation": [], "test": ["id"]},
  "coverage": {
    "split": {},
    "modality": {},
    "domain": {},
    "selected_tool": {},
    "task_type": {},
    "outcome": {},
    "strata": {}
  },
  "weak_slices": [{"field": "domain", "value": "support", "count": 1}],
  "validation_errors": [],
  "cases": [
    {
      "id": "id",
      "task": "task text",
      "modality": "text",
      "domain": "support",
      "selected_tool": "ticket_summarizer",
      "task_type": "summarization",
      "outcome": "success",
      "success": true,
      "split": "train",
      "route_slice": {
        "modality": "text",
        "domain": "support",
        "selected_tool": "ticket_summarizer",
        "task_type": "summarization",
        "outcome": "success"
      }
    }
  ]
}
```

With `--output-dir`, the script writes `manifest.json`, `cases.jsonl`, `cases.csv`, and `summary.md`.

## Installation

Copy or install this skill directory into a compatible skills folder, then run the script with Python 3. No third-party dependencies are required.

```bash
python --version
python scripts/run.py --help
```

## Usage

```bash
python scripts/run.py --help
python scripts/run.py --selftest
python scripts/test.py
python scripts/run.py --input examples/routing_logs.jsonl --seed 7
python scripts/run.py --input examples/routing_logs.jsonl --seed 7 --output-dir out
python scripts/run.py --input examples/routing_logs.jsonl --strict --ratios 0.6,0.2,0.2
```

Optional environment defaults:

```bash
ROUTELEDGER_SEED=7 python scripts/run.py --input examples/routing_logs.jsonl
ROUTELEDGER_SPLIT_RATIOS=0.6,0.2,0.2 python scripts/run.py --selftest
```

## Example

Command:

```bash
python scripts/run.py --input examples/routing_logs.jsonl --seed 7
```

Expected output:

```json
{
  "invalid_record_count": 0,
  "record_count": 6,
  "seed": 7,
  "splits": {
    "test": [
      "ex-002"
    ],
    "train": [
      "ex-001",
      "ex-003",
      "ex-004",
      "ex-005",
      "ex-006"
    ],
    "validation": []
  },
  "tool": "RouteLedger",
  "valid_record_count": 6,
  "version": "0.1.0",
  "weak_slices": []
}
```

## Limitations

- Stratification is metadata-based and does not judge task semantic difficulty.
- Small strata cannot populate every split; one-record strata are assigned to train.
- The script validates required metadata but does not detect private data in task text.
- The benchmark is only as reliable as the outcome signals and evaluator annotations supplied upstream.
