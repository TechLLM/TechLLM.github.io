---
name: biaslens-rag-diagnostic-reranking-probe-for-retrieval-candid
description: Diagnose RAG retrieval and reranking candidate bias with JSONL perturbation probes when trigger keywords include RAG, retrieval candidates, reranking, context selection, position bias, keyword bias, ambiguity bias, and precision bias.
license: MIT
---

# BiasLens RAG - Diagnostic Reranking Probe

Auto-generated and experimental; use it as a small diagnostic reference implementation, not as a final relevance judge.

## Overview

BiasLens RAG helps inspect why a retrieval-augmented generation system may choose the wrong context even when plausible candidates are present. It probes candidate passages through deterministic perturbations such as keyword masking, partial sampling, chunk hiding, and order-prior changes, then summarizes whether failures look like knowledge gaps, ambiguity bias, or precision bias.

The bundled CLI is intentionally minimal and self-contained. It uses lexical evidence rather than a hosted model so it can run without API keys and provide repeatable JSON diagnostics.

## When to use

- Use when a RAG, agent memory, note search, or knowledge-base workflow retrieves several candidates that all look partially relevant.
- Use when bad answers may come from reranking, candidate ordering, superficial keyword overlap, familiar phrasing, or near-match ambiguity.
- Use before changing chunking, indexing, reranking, or context assembly so the failure mode is explicit.
- Use in regression checks where deterministic JSON output is more useful than a one-off manual judgment.
- When NOT to use: do not use this as a replacement for task-specific human evaluation or production-grade semantic relevance modeling.

## Workflow

1. Export retrieved candidates as JSONL, one object per line, with at least `id` and `text` fields.
2. Choose the user question or retrieval query to diagnose.
3. Run `python scripts/run.py --query "<question>" --input <candidates.jsonl> --pretty`.
4. Inspect `baseline_ranking` to see which candidates win before perturbation.
5. Inspect each item in `diagnostics` for `keyword_reliance`, `partial_evidence_volatility`, `position_sensitivity`, and `diagnostic_label`.
6. Use `failure_modes` to separate likely knowledge-gap, ambiguity-bias, precision-bias, and position-bias risks.
7. Apply the `recommendations` to decide whether to expand indexing, regroup candidates, improve chunking, or tighten reranking criteria.
8. Re-run the probe after changes and compare the JSON report.

## Inputs & Outputs

Input contract:

- `--query`: the natural-language question or retrieval query.
- `--input`: path to a UTF-8 JSONL file.
- Each JSONL line must be an object with `id` as a string-like value and `text` as a string.
- Optional candidate fields are preserved only indirectly; `rank` or `position` may be used to set the original candidate position.
- Optional environment variables:
  - `BIASLENS_RAG_MAX_CANDIDATES`: positive integer limit for loaded candidates.
  - `BIASLENS_RAG_POSITION_PRIOR`: floating-point order-prior strength, default `0.06`.

Output shape:

```json
{
  "query": "string",
  "candidate_count": 0,
  "trials_per_candidate": 0,
  "baseline_ranking": [
    {"id": "string", "rank": 1, "score": 0.0}
  ],
  "diagnostics": [
    {
      "id": "string",
      "original_position": 1,
      "baseline_score": 0.0,
      "mean_perturbed_score": 0.0,
      "score_stddev": 0.0,
      "score_drop": 0.0,
      "keyword_reliance": 0.0,
      "partial_evidence_volatility": 0.0,
      "position_sensitivity": 0.0,
      "coverage": 0.0,
      "matched_terms": ["string"],
      "missing_terms": ["string"],
      "diagnostic_label": "knowledge-gap | ambiguity-bias | precision-bias | stable-evidence",
      "notes": ["string"]
    }
  ],
  "failure_modes": {
    "knowledge_gap": false,
    "ambiguity_bias": false,
    "precision_bias": false,
    "position_bias": false
  },
  "recommendations": ["string"],
  "metadata": {
    "engine": "biaslens-rag-lexical-probe",
    "version": "0.1.0",
    "position_prior": 0.06
  }
}
```

## Installation

Copy or install this folder as a skill, then run the bundled script with Python 3.10 or newer. No third-party packages are required.

```bash
python scripts/run.py --help
python scripts/test.py
```

## Usage

Run the built-in self-test sample:

```bash
python scripts/run.py --selftest --pretty
```

Run on your own JSONL candidates:

```bash
python scripts/run.py --query "How do I reset contractor MFA device approvals?" --input examples/candidates.jsonl --pretty
```

Write JSON output to a file:

```bash
python scripts/run.py --query "How do I reset contractor MFA device approvals?" --input examples/candidates.jsonl --output examples/expected-output.json
```

Show help:

```bash
python scripts/run.py --help
```

## Example

Command:

```bash
python scripts/run.py --query "How do I reset contractor MFA device approvals?" --input examples/candidates.jsonl --pretty
```

Expected output is a JSON report with `baseline_ranking`, per-candidate `diagnostics`, boolean `failure_modes`, and `recommendations`. See `examples/expected-output.json` for the full deterministic output.

## Limitations

- The reference CLI is lexical and deterministic; it does not understand meaning like an embedding model or reranker.
- Scores are diagnostic signals, not calibrated relevance probabilities.
- Perturbations approximate common bias patterns but cannot prove the internal behavior of a production language model.
- Very short queries, highly technical synonyms, or multilingual passages may need custom tokenization and scoring.
