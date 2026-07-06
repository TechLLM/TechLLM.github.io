---
name: routelens-unified-audit-trails-for-expert-and-retrieval-rout
description: RouteLens audits JSONL routing logs for RAG index routing and expert/model-path routing when users mention route-audit, routing audit, RAG routing, expert routing, fallback analysis, or RouteLens.
license: MIT
---

# RouteLens — Unified Audit Trails for Expert and Retrieval Routing

Auto-generated and experimental.

## Overview

RouteLens helps inspect AI systems that make both retrieval-routing and inference-routing decisions. It treats vector index selection, model path selection, expert subset use, fallback attempts, and outcome labels as one audit trail so failures can be separated by route, domain, and quality gap.

The bundled `route-audit` reference CLI reads JSONL query logs and emits deterministic JSON reports with confusion matrices, domain failure rates, subset-versus-full-model gaps, and index/model degradation signals.

## When to use

Use this skill when a user asks to audit RAG routing, compare selected indexes with selected experts, inspect fallback behavior, debug bad answers from multi-index or multi-expert systems, analyze JSONL evaluation logs, or run `route-audit`.

Use it for trigger phrases such as "RouteLens", "routing audit", "RAG route logs", "expert routing", "retrieval fallback", "mixture-of-experts quality gap", "index/model interaction", and "route-audit".

When NOT to use: do not use this skill for live production tracing, secret log ingestion, or vendor-specific observability systems that require private APIs.

## Workflow

1. Collect routing logs as newline-delimited JSON where each line represents one query attempt.
2. Include at least an intended domain, selected retrieval index, selected model or expert path, a quality score, and an outcome label or enough score data to derive one.
3. Save logs to a local `.jsonl` file without secrets or personal data.
4. Run `python scripts/run.py --input <logs.jsonl>` from the skill directory.
5. Review `summary` first to understand global success, failure, fallback, and quality-gap rates.
6. Inspect `domain_failure_rates` to find weak domains and missing fallback coverage.
7. Inspect `routing_confusion_matrix` to see which intended domains were paired with which retrieval indexes and model paths.
8. Inspect `subset_vs_full_model_gaps` to quantify quality loss from narrower or cheaper expert paths.
9. Inspect `index_model_quality` and `degradation_reports` to identify route combinations that need retrieval fixes, model-path changes, or fallback policy changes.

## Inputs & Outputs

Input is a JSONL file, one object per line. Supported fields are:

```json
{
  "query_id": "q-001",
  "intended_domain": "billing",
  "selected_index": "billing_faq",
  "selected_model_path": "expert:billing-lite",
  "quality_score": 0.91,
  "selected_path_score": 0.88,
  "full_model_score": 0.93,
  "fallback_attempts": [],
  "outcome": "success"
}
```

Aliases are accepted for common fields: `domain`, `query_domain`, `retrieval_index`, `index`, `selected_expert_path`, `expert_path`, `model_path`, `evaluation_score`, `eval_score`, `subset_score`, and `model_score`.

Output is deterministic JSON with this shape:

```json
{
  "schema_version": "routelens.audit.v1",
  "summary": {
    "total_queries": 0,
    "successes": 0,
    "failures": 0,
    "fallback_used": 0,
    "average_quality_score": 0.0,
    "average_subset_quality_gap": 0.0
  },
  "domain_failure_rates": [
    {
      "domain": "billing",
      "total": 0,
      "failures": 0,
      "failure_rate": 0.0,
      "fallback_used": 0,
      "fallback_coverage": 0.0
    }
  ],
  "routing_confusion_matrix": [
    {
      "intended_domain": "billing",
      "selected_index": "billing_faq",
      "selected_model_path": "expert:billing-lite",
      "outcome": "success",
      "count": 1
    }
  ],
  "subset_vs_full_model_gaps": [
    {
      "selected_model_path": "expert:billing-lite",
      "samples": 1,
      "average_full_model_score": 0.93,
      "average_selected_path_score": 0.88,
      "average_gap": 0.05
    }
  ],
  "index_model_quality": [
    {
      "selected_index": "billing_faq",
      "selected_model_path": "expert:billing-lite",
      "queries": 1,
      "average_quality_score": 0.91,
      "failure_rate": 0.0,
      "degradation_flag": false
    }
  ],
  "degradation_reports": [
    {
      "selected_index": "general_docs",
      "selected_model_path": "expert:general-lite",
      "queries": 1,
      "average_quality_score": 0.52,
      "failure_rate": 1.0,
      "reason": "average quality below threshold; failure rate above 25%"
    }
  ]
}
```

## Installation

Copy this skill folder into a Claude Code or OpenClaw-compatible skills directory, then run commands from the skill root.

```bash
python --version
python scripts/run.py --help
```

No third-party packages are required.

## Usage

Run the built-in sample:

```bash
python scripts/run.py --selftest
```

Audit a JSONL log file:

```bash
python scripts/run.py --input examples/sample_logs.jsonl
```

Write output to a file:

```bash
python scripts/run.py --input examples/sample_logs.jsonl --output audit.json
```

Adjust the success threshold:

```bash
python scripts/run.py --input examples/sample_logs.jsonl --threshold 0.75
```

Show help:

```bash
python scripts/run.py --help
```

Optional environment variables:

```bash
ROUTELENS_SUCCESS_THRESHOLD=0.75 python scripts/run.py --input examples/sample_logs.jsonl
ROUTELENS_OUTPUT_FORMAT=json python scripts/run.py --selftest
```

## Example

Command:

```bash
python scripts/run.py --input examples/sample_logs.jsonl
```

Expected output is JSON matching `examples/expected_output.json`. The summary begins:

```json
{
  "schema_version": "routelens.audit.v1",
  "summary": {
    "total_queries": 6,
    "successes": 3,
    "failures": 3,
    "fallback_used": 3,
    "average_quality_score": 0.715,
    "average_subset_quality_gap": 0.14
  }
}
```

## Limitations

RouteLens is a local reference implementation, not a hosted observability service. It assumes scores are already computed by an evaluation process, uses simple deterministic aggregation, and does not infer causal blame beyond route-level correlation. It should be used on sanitized logs only.
