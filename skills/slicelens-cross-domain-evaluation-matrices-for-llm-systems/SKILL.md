---
name: slicelens-cross-domain-evaluation-matrices-for-llm-systems
description: SliceLens turns evaluation CSVs into cross-domain matrices for LLM, RAG, and agent systems; use for benchmark illusion, domain gap, worst-slice, robustness, transfer, and missing-field diagnostics.
version: 0.1.0
license: MIT
---

# SliceLens — Cross-Domain Evaluation Matrices for LLM Systems

Auto-generated and experimental; validate the report against your evaluation design before using it for release decisions.

## Overview

LLM, RAG, retrieval, and agent evaluations often hide failure modes behind one average score. SliceLens treats evaluation CSV files as diagnostic instruments by turning them into source-to-target matrices, slice tables, worst-slice reports, domain-gap metrics, and missing-field degradation checks. The bundled CLI is intentionally small and self-contained so it can run inside an existing benchmark or regression workflow without external services.

## When to use

Use this skill when you need to diagnose benchmark illusions, domain gaps, source-to-target transfer failures, RAG relevance regressions, agent-router failures, worst-slice performance, missing metadata degradation, corruption robustness, modality shifts, document-type gaps, or question-type failures.

Use it when an evaluation CSV has a numeric score plus categorical fields such as source domain, target domain, question type, document type, modality, or condition.

When NOT to use: do not use SliceLens as a statistical significance tool or as a replacement for task-specific human evaluation.

## Workflow

1. Export evaluation results to CSV with one row per example and at least `score`, `source_domain`, and `target_domain`.
2. Add optional categorical columns such as `question_type`, `document_type`, `modality`, and `condition` to expose known risk distributions.
3. Run `python scripts/run.py --input path/to/eval.csv --output slicelens_report.md`.
4. Inspect the source-to-target transfer matrix to find generalization failures across domains.
5. Review the worst slice and slice tables before trusting the aggregate mean.
6. Use domain gaps to compare in-domain performance against out-of-domain transfer.
7. Use missing-field degradation to identify robustness failures caused by blank metadata or corrupted inputs.
8. Attach the Markdown report to a model card, pull request, release note, or regression review.

## Inputs & Outputs

Input contract:

- CSV with a header row.
- Required columns: `score`, `source_domain`, `target_domain`.
- `score` must be numeric and finite; values may be accuracy, hit rate, relevance, pass rate, or another scalar metric.
- Optional slice columns default to `question_type`, `document_type`, `modality`, and `condition`.
- Blank categorical cells are normalized to `(missing)`.
- Optional environment variables: `SLICELENS_INPUT`, `SLICELENS_OUTPUT`, `SLICELENS_SCORE_COLUMN`, `SLICELENS_SOURCE_COLUMN`, `SLICELENS_TARGET_COLUMN`, `SLICELENS_SLICE_COLUMNS`, `SLICELENS_MIN_COUNT`, and `SLICELENS_PRECISION`.

Output shape:

- Markdown report by default, or deterministic JSON with `--json`.
- Top-level fields in JSON: `row_count`, `overall_mean`, `score_column`, `source_column`, `target_column`, `slice_columns`, `min_count`, `transfer_matrix`, `worst_slice`, `domain_gaps`, `slice_tables`, `missing_field_degradation`, and `warnings`.
- `transfer_matrix`: `{rows, columns, values}` where each value contains `mean` and `count`.
- `worst_slice`: `{dimension, value, count, mean}`.
- `domain_gaps`: list of `{source_domain, in_domain_mean, out_domain_mean, gap, in_domain_count, out_domain_count}`.
- `slice_tables`: mapping from slice dimension to rows of `{value, count, mean}`.
- `missing_field_degradation`: list of `{field, present_mean, missing_mean, degradation, present_count, missing_count}`.

## Installation

Copy this skill directory into your Claude Code or OpenClaw-compatible skills directory. The reference CLI uses only the Python standard library.

```bash
python --version
python scripts/run.py --help
python scripts/test.py
```

## Usage

Run the built-in no-key sample:

```bash
python scripts/run.py --selftest
```

Analyze a CSV and write Markdown:

```bash
python scripts/run.py --input examples/sample_eval.csv --output slicelens_report.md
```

Customize column names:

```bash
python scripts/run.py \
  --input eval.csv \
  --score-column pass_rate \
  --source-column train_domain \
  --target-column eval_domain \
  --slice-columns question_type,document_type,condition \
  --output slicelens_report.md
```

Emit JSON for downstream automation:

```bash
python scripts/run.py --input examples/sample_eval.csv --json
```

Show CLI help:

```bash
python scripts/run.py --help
```

## Example

Input:

```bash
python scripts/run.py --input examples/sample_eval.csv --output examples/expected_report.md
```

Expected summary:

```text
Rows: 12
Overall mean: 0.653
Worst slice: condition=missing_metadata, mean 0.413, count 3
Largest sample domain gap: finance, gap 0.410
Missing document_type degradation: 0.265
```

The full expected Markdown output is in `examples/expected_report.md`.

## Limitations

- SliceLens reports descriptive diagnostics, not confidence intervals or causal claims.
- Small slices can be noisy; tune `--min-count` for your benchmark size.
- The CLI assumes one scalar score per row and does not merge multiple runs.
- Domain-gap calculations assume in-domain rows are those where source and target labels match exactly.
- Missing-field degradation only compares blank categorical cells against present cells.

## Verification
Automated execution check: **passed ✅**.

- Steps: structure=ok · syntax=ok · help=ok · selftest=ok · test=ok
- Commands and outputs shown in `README.md` are captured from these real runs.
