---
name: gateweave-multislice-rag-gate-evaluation
description: Evaluates RAG relevance gates across controlled slices and stress cases; use for trigger keywords RAG gate evaluation, slice metrics, relevance gate, reranker, router threshold, missing evidence.
version: 0.1.0
license: MIT
---

# GateWeave — Multislice RAG Gate Evaluation
Auto-generated and experimental; review results before using them for production decisions.

## Overview
GateWeave evaluates whether RAG relevance gates, rerankers, and router thresholds generalize beyond aggregate hit rate. It turns labeled question-document rows and scorer outputs into controlled slices by domain, document type, evidence field, and custom metadata columns. The bundled CLI produces deterministic JSON and Markdown reports with aggregate metrics, worst-slice scores, missing-field stress results, and side-by-side scorer comparisons.

## When to use
- Use when a RAG relevance gate looks strong on average but may fail on specific domains, document types, metadata patterns, question formats, or evidence fields.
- Use when comparing multiple relevance gates, rerankers, or router scorers under one offline protocol.
- Use when adding CI or pull request checks for retrieval gate regressions.
- Use when testing missing-evidence behavior, such as blank evidence fields or corrupted metadata.
- When NOT to use: do not use this skill as a replacement for human annotation quality checks, end-to-end answer evaluation, or live production monitoring.

## Workflow
1. Prepare a labeled CSV with one row per question-document pair and required columns `qid`, `doc_id`, and `label`.
2. Add optional slice columns such as `domain`, `doc_type`, `evidence_field`, `question_format`, or any project-specific metadata column.
3. Export one or more scorer CSV files with `qid`, `doc_id`, and either `score` or a boolean `decision`/`gate` column.
4. Run the CLI with the label file, scorer files, threshold, slice columns, and output paths.
5. Review aggregate precision, recall, F1, and accuracy for each scorer.
6. Inspect per-slice metrics and `worst_slice_score` to find hidden failures masked by aggregate results.
7. Inspect missing-field stress results to see whether blank evidence fields degrade gate quality.
8. Store the JSON report in CI or experiment tracking and use the Markdown report for pull request review.

## Inputs & Outputs
Input label CSV contract:

```text
qid,doc_id,label,domain,doc_type,evidence_field,<custom metadata columns>
```

Required label fields are `qid`, `doc_id`, and `label`. Labels accept `1`, `0`, `true`, `false`, `yes`, `no`, `relevant`, and `irrelevant`. Blank metadata values are treated as `__MISSING__` in slice reports.

Input scorer CSV contract:

```text
qid,doc_id,score,scorer
```

Each scorer row must include `qid` and `doc_id`. It may include `score`, which is converted to a prediction using the threshold, or a boolean `decision`/`gate` value, which overrides score thresholding. The optional `scorer` column names the scorer; otherwise the file stem is used.

Exact JSON output shape, where every `metrics` object contains `count`, `tp`, `fp`, `fn`, `tn`, `precision`, `recall`, `f1`, and `accuracy`:

```json
{
  "protocol": "gateweave-v0",
  "threshold": 0.5,
  "slice_columns": ["domain", "doc_type", "evidence_field"],
  "missing_field_columns": ["evidence_field"],
  "labels": {"rows": 8, "source": "examples/labels.csv"},
  "scorers": [
    {
      "name": "baseline",
      "rows_evaluated": 8,
      "missing_predictions": 0,
      "extra_predictions": 0,
      "aggregate": {"count": 8, "tp": 2, "fp": 1, "fn": 2, "tn": 3, "precision": 0.666667, "recall": 0.5, "f1": 0.571429, "accuracy": 0.625},
      "slices": {"<slice_column>": [{"value": "<slice_value>", "metrics": {"count": 3, "tp": 1, "fp": 1, "fn": 1, "tn": 0, "precision": 0.5, "recall": 0.5, "f1": 0.5, "accuracy": 0.333333}}]},
      "missing_field_stress": [{"column": "evidence_field", "missing_count": 2, "present_count": 6, "missing_f1": 0.0, "present_f1": 0.666667, "stress_score": 0.0, "stress_delta": -0.666667}],
      "worst_slice": {"column": "domain", "value": "sales", "metrics": {"count": 2, "tp": 0, "fp": 0, "fn": 1, "tn": 1, "precision": 0.0, "recall": 0.0, "f1": 0.0, "accuracy": 0.5}},
      "worst_slice_score": 0.0
    }
  ],
  "comparisons": [{"metric": "aggregate_f1", "best": ["candidate"], "scores": {"baseline": 0.571429, "candidate": 0.75}}]
}
```

Markdown output contains tables for aggregate metrics, worst slices, missing-field stress, and side-by-side comparisons.

## Installation
Copy this directory into your Claude Code, OpenClaw, or compatible skills directory:

```bash
cp -R gateweave-multislice-rag-gate-evaluation <skills-dir>/
```

No Python packages are required beyond the standard library.

## Usage
Show help:

```bash
python scripts/run.py --help
```

Run the built-in deterministic self-test sample:

```bash
python scripts/run.py --selftest
```

Run on example files and write both reports:

```bash
python scripts/run.py \
  --labels examples/labels.csv \
  --scorers examples/baseline_scores.csv examples/candidate_scores.csv \
  --slice-columns domain,doc_type,evidence_field \
  --missing-field-columns evidence_field \
  --threshold 0.5 \
  --output-json report.json \
  --output-md report.md
```

Optional environment variables:

```bash
GATEWEAVE_DEFAULT_THRESHOLD=0.6 python scripts/run.py --labels examples/labels.csv --scorers examples/baseline_scores.csv
```

`GATEWEAVE_API_KEY` is read only as a reserved future integration flag and is never required, printed, or stored.

## Example
Command:

```bash
python scripts/run.py \
  --labels examples/labels.csv \
  --scorers examples/baseline_scores.csv examples/candidate_scores.csv \
  --format markdown
```

Expected output excerpt:

```text
# GateWeave Report

Protocol: `gateweave-v0`
Threshold: `0.5`
Rows: `8`

| scorer | rows | precision | recall | f1 | accuracy | worst_slice_score |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 8 | 0.666667 | 0.5 | 0.571429 | 0.625 | 0.0 |
| candidate | 8 | 0.75 | 0.75 | 0.75 | 0.75 | 0.0 |
```

The full expected JSON and Markdown reports are in `examples/expected_output.json` and `examples/expected_output.md`.

## Limitations
- This is an offline benchmark helper, not a live RAG observability system.
- Metrics are only as reliable as the label quality and scorer export coverage.
- The missing-field stress test treats blank fields as missing; it does not synthesize corrupted documents.
- Thresholding is global per run; calibrate thresholds separately if each scorer needs its own operating point.
- The implementation is intentionally small and uses only CSV, JSON, Markdown, and the Python standard library.

## Verification
Automated execution check: **passed ✅**.

- Steps: structure=ok · syntax=ok · help=ok · selftest=ok · test=ok
- Commands and outputs shown in `README.md` are captured from these real runs.
