---
name: gatetectonic-domain-stress-testing-for-rag-relevance-gates
description: GateTectonic evaluates RAG relevance gates with leave-one-domain-out and stress-slice reports; use for RAG eval, relevance gate, domain shift, missing context, corrupted input, ERM baseline, and regression tracking.
license: MIT
---

# GateTectonic

Auto-generated and experimental; review outputs before using them for production decisions.

## Overview

GateTectonic is a small benchmarking workflow for stress testing Retrieval-Augmented Generation relevance gates. It reads a question-document-label CSV with domain metadata, runs leave-one-domain-out evaluation, creates missing-context and corrupted-input variants, compares a fixed gate against an empirical risk minimization baseline, and exports JSON plus Markdown reports.

The bundled reference CLI is intentionally local and simple. It uses a lexical overlap relevance gate so it can run without API keys or external services, while keeping the code structured so teams can replace the scorer with a local classifier, embedding threshold, reranker, or LLM judge.

## When To Use

Use this skill when evaluating or regression testing RAG relevance gates under domain shift or failure-mode stress, especially for:

- `RAG eval`
- `relevance gate`
- `domain shift`
- `leave-one-domain-out`
- `missing context`
- `corrupted input`
- `ERM baseline`
- `regression tracking`

## Installation

Copy this skill directory into your local skills folder or install it with the skill manager used by your Claude Code or OpenClaw-compatible environment.

No third-party Python dependencies are required.

## Usage

Run with built-in sample data:

```bash
python scripts/run.py
```

Run with the included CSV example:

```bash
python scripts/run.py --input examples/sample.csv
```

Write reports to custom locations:

```bash
python scripts/run.py \
  --input examples/sample.csv \
  --out-json reports/gatetectonic.json \
  --out-md reports/gatetectonic.md
```

Use a custom fixed-gate threshold:

```bash
python scripts/run.py --input examples/sample.csv --threshold 0.4
```

Expected CSV columns:

```text
question,document,label,source_domain,document_type,question_type
```

`label` must be `1`, `true`, `yes`, or `relevant` for relevant pairs, and `0`, `false`, `no`, or `irrelevant` for irrelevant pairs.

## Example

```bash
python scripts/run.py --input examples/sample.csv
```

The command creates:

- `reports/gatetectonic_report.json`
- `reports/gatetectonic_report.md`

The Markdown report highlights overall metrics, leave-one-domain-out results, stress-slice accuracy, and per-slice deltas against the ERM baseline.

## Limitations

- The bundled scorer is a reference lexical gate, not a production relevance model.
- Corruption generation is deterministic and intentionally small; extend it for real OCR, truncation, stale-source, or modality-specific tests.
- Leave-one-domain-out evaluation needs at least two source domains to be meaningful.
- The report is for engineering review and regression tracking, not a complete benchmark standard.
