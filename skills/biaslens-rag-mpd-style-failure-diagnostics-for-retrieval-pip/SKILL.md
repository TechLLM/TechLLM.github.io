---
name: biaslens-rag-mpd-style-failure-diagnostics-for-retrieval-pip
description: Diagnoses RAG retrieval pipeline failures by separating missing evidence from unstable or biased reranking when trigger keywords include RAG diagnostics, retrieval failure, reranker bias, position bias, candidate JSONL, and selected document IDs.
license: MIT
---

# BiasLens RAG -- MPD-Style Failure Diagnostics for Retrieval Pipelines
Auto-generated and experimental; validate findings against real retrieval logs before production decisions.

## Overview
RAG systems can fail because the right evidence never reached the candidate set, or because the right evidence was present but the selection stage favored unstable, positional, or keyword-biased choices. This skill provides a small CLI-first diagnostic workflow that applies mask, perturb, diagnose checks to candidate JSONL records and selected document IDs. The bundled script produces deterministic JSON so the results can be used in local debugging, CI checks, or issue reports.

## When to use
- Use when a RAG answer cites the wrong source and you need to know whether retrieval or reranking is responsible.
- Use when you have query logs, candidate documents, selected document IDs, and optional known-good evidence IDs.
- Use when trigger keywords appear: RAG diagnostics, retrieval failure, reranker bias, position bias, candidate JSONL, selected document IDs, masking tests, dropout tests, keyword attraction.
- Use before changing embedding models, reranker prompts, or score thresholds so you can classify the failure mode first.
- When NOT to use: do not use this as a replacement for human relevance judgment, offline eval sets, or production telemetry.

## Workflow
1. Export one JSONL record per query with `query_id`, `question`, `selected_doc_ids`, optional `relevant_doc_ids`, and a `candidates` array.
2. Run `python3 scripts/run.py --candidates examples/candidates.jsonl` to generate deterministic diagnostics.
3. Inspect `failure_category` for each case: `correct_evidence_absent`, `reranker_instability_or_bias`, or `no_failure_signal`.
4. Review `selection_stability`, `position_bias_score`, `unstable_alternatives`, and `keyword_attraction` to identify likely reranker behavior.
5. If evidence is absent, debug chunking, indexing, filtering, and recall. If evidence is present but unstable, debug reranker features, prompt wording, candidate order, or lexical shortcuts.
6. Save the JSON output beside the retrieval trace or attach it to the bug report.

## Inputs & Outputs
Input JSONL contract:

```json
{
  "query_id": "q1",
  "question": "What is the refund policy after cancellation?",
  "selected_doc_ids": ["billing_faq"],
  "relevant_doc_ids": ["refund_policy"],
  "candidates": [
    {"doc_id": "billing_faq", "text": "Billing invoices and upgrade charges.", "score": 0.95},
    {"doc_id": "refund_policy", "text": "Refund policy for cancellation requests.", "score": 0.85}
  ]
}
```

Output shape:

```json
{
  "tool": "biaslens-rag",
  "version": "0.1.0",
  "summary": {
    "cases": 0,
    "correct_evidence_absent": 0,
    "reranker_instability_or_bias": 0,
    "no_failure_signal": 0,
    "mean_selection_stability": 0.0,
    "mean_position_bias_score": 0.0
  },
  "cases": [
    {
      "query_id": "q1",
      "failure_category": "reranker_instability_or_bias",
      "selected_doc_ids": ["billing_faq"],
      "relevant_doc_ids": ["refund_policy"],
      "correct_evidence_present": true,
      "selection_stability": 0.5,
      "position_bias_score": 1.0,
      "masking_trials": 3,
      "unstable_alternatives": ["refund_policy"],
      "keyword_attraction": [{"term": "billing", "score": 1.0}],
      "signals": ["relevant evidence present but not selected"]
    }
  ]
}
```

## Installation
Copy this directory into your skills directory or keep it in a project checkout:

```bash
python3 --version
python3 scripts/run.py --help
python3 scripts/test.py
```

No package installation is required because the reference implementation uses only the Python standard library.
Use `python` instead of `python3` only when your system aliases `python` to Python 3.

## Usage
Run the built-in sample:

```bash
python3 scripts/run.py --selftest
```

Run against a candidate JSONL file:

```bash
python3 scripts/run.py --candidates examples/candidates.jsonl
```

Write diagnostics to a file:

```bash
python3 scripts/run.py --candidates examples/candidates.jsonl --output examples/actual_output.json
```

Show CLI options:

```bash
python3 scripts/run.py --help
```

Optional environment variables:

```bash
BIASLENS_RAG_KEYWORD_LIMIT=8 python3 scripts/run.py --candidates examples/candidates.jsonl
BIASLENS_RAG_STOPWORDS="what,is,the,after" python3 scripts/run.py --selftest
```

## Example
Command:

```bash
python3 scripts/run.py --candidates examples/candidates.jsonl
```

Expected output is the deterministic JSON in `examples/expected_output.json`. It reports one case where correct evidence is absent from the candidate set and one case where the relevant document is present but the selected document shows reranker instability, position bias, and keyword attraction.

## Limitations
- The bundled script is a lightweight diagnostic reference, not a full reranker emulator.
- `relevant_doc_ids` are optional, but failure classification is strongest when they are provided.
- Keyword attraction uses simple token statistics, so domain stopwords may need tuning with `BIASLENS_RAG_STOPWORDS`.
- Position bias is a heuristic based on candidate order and lexical evidence; validate it with reranker traces when available.
