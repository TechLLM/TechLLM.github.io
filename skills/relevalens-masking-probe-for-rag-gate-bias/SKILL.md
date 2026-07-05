---
name: relevalens-masking-probe-for-rag-gate-bias
description: Diagnose relevance-gate shortcut bias in RAG systems with JSONL masking probes; use for trigger keywords RAG gate bias, relevance masking, retrieval evaluation, rank instability.
license: MIT
---

# RelevaLens - Masking Probe for RAG Gate Bias
Auto-generated and experimental skill for offline relevance-gate diagnostics.

## Overview
RAG relevance gates can appear accurate while over-relying on shortcuts such as repeated keywords, candidate position, familiar templates, or a few dominant passages. RelevaLens compares baseline relevance scores with masked score logs to separate evidence sensitivity from shortcut bias. The bundled CLI reads JSONL logs, computes deterministic bias metrics, and emits Markdown and CSV reports without requiring any model provider.

## When to use
- Use when a RAG relevance gate accepts the same early or keyword-heavy passages too often.
- Use when evaluating retrieval, reranking, passage gates, answer-gating, or citation-gating behavior.
- Use when you have baseline and masked relevance score logs and need entropy, concentration, position skew, mask sensitivity, and rank instability metrics.
- Use when generating repeatable prompt sets for masked relevance experiments before running a live model adapter.
- When NOT to use: do not use this as a replacement for human relevance labels, retrieval benchmarks, or end-to-end answer quality evaluation.

## Workflow
1. Export query records as JSONL with `query_id` and `text`.
2. Export candidate records as JSONL with `query_id`, `candidate_id`, `rank` or `position`, and optional `fields`.
3. Export relevance score logs as JSONL with `query_id`, `candidate_id`, `score`, and `mask`; use `mask: "none"` for baseline rows.
4. Run `python scripts/run.py --queries ... --candidates ... --scores ... --out-dir ...`.
5. Review the Markdown report for query-level flags and the CSV for candidate-level sensitivity.
6. If active probing is needed, run the prompt-set generator and send the resulting JSONL prompts through your own evaluation backend.
7. Re-run the analysis after adding new masking strategies, score logs, or query cohorts.

## Inputs & Outputs
Input files are newline-delimited JSON.

Queries:
```json
{"query_id":"q1","text":"What changed in warranty revenue recognition?"}
```

Candidates:
```json
{"query_id":"q1","candidate_id":"d1","rank":1,"position":1,"fields":{"title":"Warranty FAQ","body":"..."}}
```

Scores:
```json
{"query_id":"q1","candidate_id":"d1","score":0.92,"mask":"none"}
{"query_id":"q1","candidate_id":"d1","score":0.38,"mask":"keyword_mask"}
```

The CLI returns deterministic report data with this shape:
```json
{
  "summary": {
    "query_count": 1,
    "candidate_count": 3,
    "score_count": 12,
    "mean_normalized_entropy": 0.8693,
    "mean_top1_concentration": 0.5027,
    "mean_mask_sensitivity": 0.1778,
    "mean_rank_instability": 0.2222,
    "mean_position_skew": 0.1694,
    "flags": ["position_skew", "rank_instability"]
  },
  "queries": [
    {
      "query_id": "q1",
      "normalized_entropy": 0.8693,
      "top1_concentration": 0.5027,
      "mask_sensitivity": 0.1778,
      "rank_instability": 0.2222,
      "position_skew": 0.1694,
      "flags": ["position_skew", "rank_instability"]
    }
  ],
  "candidates": [
    {
      "query_id": "q1",
      "candidate_id": "d1",
      "baseline_rank": 1,
      "position": 1,
      "baseline_score": 0.92,
      "masked_mean": 0.5133,
      "mask_delta": 0.4067,
      "concentration_share": 0.5027
    }
  ]
}
```

With `--out-dir`, the CLI writes:
- `relevalens_report.md`: Markdown summary, query findings, and candidate sensitivity.
- `relevalens_metrics.csv`: candidate-level metrics with stable columns.

With `--prompt-set`, the CLI writes JSONL prompt records:
```json
{"prompt_id":"q1:d1:baseline","query_id":"q1","candidate_id":"d1","mask":"baseline","prompt":"..."}
```

## Installation
Copy or install this skill folder into your agent's skills directory, then run from the skill root:
```bash
python scripts/run.py --help
python scripts/test.py
```

No third-party Python packages are required.

## Usage
Self-test with built-in sample data:
```bash
python scripts/run.py --selftest
```

Analyze local JSONL files and write reports:
```bash
python scripts/run.py \
  --queries examples/queries.jsonl \
  --candidates examples/candidates.jsonl \
  --scores examples/scores.jsonl \
  --out-dir out
```

Print the machine-readable result:
```bash
python scripts/run.py \
  --queries examples/queries.jsonl \
  --candidates examples/candidates.jsonl \
  --scores examples/scores.jsonl \
  --json
```

Generate a prompt set for external active probing:
```bash
python scripts/run.py \
  --queries examples/queries.jsonl \
  --candidates examples/candidates.jsonl \
  --scores examples/scores.jsonl \
  --prompt-set out/prompts.jsonl
```

The script checks `RELEVALENS_ADAPTER_KEY` for optional external adapters, but the included offline workflow never requires or prints secrets.

## Example
Command:
```bash
python scripts/run.py --selftest
```

Expected output:
```text
# RelevaLens Report

## Summary
- query_count: 1
- candidate_count: 3
- score_count: 12
- mean_normalized_entropy: 0.8693
- mean_top1_concentration: 0.5027
- mean_mask_sensitivity: 0.1778
- mean_rank_instability: 0.2222
- mean_position_skew: 0.1694
- flags: position_skew, rank_instability
```

## Limitations
- Metrics depend on the quality and coverage of the supplied masked score logs.
- The bundled implementation analyzes scores; it does not call LLM providers or judge semantic correctness.
- Position skew is a lightweight heuristic and should be interpreted with cohort-level trends.
- Prompt generation is provider-neutral; teams must connect their own model or evaluator backend.
