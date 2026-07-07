---
name: tracebloom-positive-trace-dataset-builder-for-rag-evaluation
description: Build positive-trace JSONL datasets from cited answers and retrieval logs for RAG evaluation, reranker training, hard-negative review, retriever audits, and Gate 2 relevance scoring; use for trigger keywords TraceBloom, positive traces, RAG evaluation, retrieval logs, citations, implicit negatives.
license: MIT
---

# TraceBloom — Positive-Trace Dataset Builder for RAG Evaluation

Auto-generated and experimental; validate the generated dataset before using it for production scoring or training.

## Overview

TraceBloom turns positive usage traces into practical datasets for retrieval-augmented generation evaluation. It starts from signals that are often cheaper to trust than full manual labeling, such as final-answer citations, saved answers, reviewed citation manifests, and retrieved documents that were not used. The bundled CLI aligns cited documents with retrieval logs, exports confirmed positive pairs, and creates guarded implicit negative candidates for review or downstream evaluation.

## When to use

Use this skill when you need to:

- Convert Markdown answers with citations into RAG evaluation JSONL.
- Curate positive query-document pairs from product traces, conversation exports, or citation manifests.
- Compare cited sources against retrieval logs to audit retriever behavior.
- Generate a small hard-negative review queue from retrieved-but-unused documents.
- Prepare deterministic seed data for reranker experiments, Gate 2 relevance checks, or regression tests.

When NOT to use: do not treat retrieved-but-unused documents as proven negatives without review, especially for high-recall retrieval systems or multi-hop answers.

## Workflow

1. Collect answer traces that include a `Query ID`, `Query`, and citations such as `[title](doc://doc-id#chunk=chunk-id)` or `[[doc-id#chunk=chunk-id]]`.
2. Export retrieval logs as JSONL with `query_id`, `query`, `run_id`, `rank`, `doc_id`, `chunk_id`, and `score`.
3. Run `scripts/run.py` with the answer traces and retrieval log.
4. Inspect the emitted JSONL dataset: records labeled `positive` are citation-backed, while records labeled `implicit_negative_candidate` are retrieved-but-unused candidates.
5. Optionally write a review queue for ambiguous citations, unmatched positives, and high-rank unused retrievals.
6. Use the dataset in retriever evaluation, reranker training, relevance scoring, or regression checks.

## Inputs & Outputs

Inputs:

- Markdown answer files: include `Query ID: ...`, `Query: ...`, and citations in `doc://` or `[[doc#chunk=...]]` form.
- JSONL answer files: one object per line with `query_id`, `query`, optional `answer`, and optional `citations`.
- Citation manifests: JSON or JSONL records with `query_id`, `query`, `doc_id`, optional `chunk_id`, and optional `confidence`.
- Retrieval logs: JSONL records with `query_id`, `query`, `run_id`, `rank`, `doc_id`, optional `chunk_id`, and optional `score`.

Dataset output is JSONL, one record per line:

```json
{
  "query_id": "q-001",
  "query": "User question text",
  "doc_id": "source-document",
  "chunk_id": "chunk-id",
  "label": "positive",
  "source": "citation+retrieval",
  "confidence": 0.95,
  "run_id": "run-001",
  "rank": 1,
  "score": 0.92,
  "evidence": {
    "citation": "doc://source-document#chunk=chunk-id",
    "input": "answers.md",
    "matched_retrieval": true
  }
}
```

Review queue output is JSONL with `query_id`, `doc_id`, `chunk_id`, `reason`, `severity`, and `evidence`.

## Installation

Copy this skill directory into your skills folder, then run the self-test:

```bash
python scripts/run.py --selftest
python scripts/test.py
```

No API key is required. Optional environment variables are `TRACEBLOOM_DEFAULT_CONFIDENCE` and `TRACEBLOOM_MIN_NEGATIVE_SCORE`.

## Usage

Show CLI options:

```bash
python scripts/run.py --help
```

Run the bundled example and print dataset JSONL:

```bash
python scripts/run.py \
  --answers examples/answers.md \
  --retrieval-log examples/retrieval_log.jsonl \
  --max-negatives-per-query 2
```

Write dataset and review queue files:

```bash
python scripts/run.py \
  --answers examples/answers.md \
  --retrieval-log examples/retrieval_log.jsonl \
  --output tracebloom_dataset.jsonl \
  --review-output tracebloom_review_queue.jsonl
```

## Example

Command:

```bash
python scripts/run.py --answers examples/answers.md --retrieval-log examples/retrieval_log.jsonl --max-negatives-per-query 2
```

Expected output:

```jsonl
{"chunk_id":"intro","confidence":0.95,"doc_id":"rag-handbook","evidence":{"citation":"doc://rag-handbook#chunk=intro","input":"examples/answers.md","matched_retrieval":true},"label":"positive","query":"How should we evaluate a RAG retriever from product traces?","query_id":"q-001","rank":1,"run_id":"run-001","score":0.92,"source":"citation+retrieval"}
{"chunk_id":"trace-signals","confidence":0.95,"doc_id":"support-notes","evidence":{"citation":"[[support-notes#chunk=trace-signals]]","input":"examples/answers.md","matched_retrieval":true},"label":"positive","query":"How should we evaluate a RAG retriever from product traces?","query_id":"q-001","rank":3,"run_id":"run-001","score":0.76,"source":"citation+retrieval"}
{"chunk_id":"overview","confidence":0.52,"doc_id":"unused-overview","evidence":{"reason":"retrieved for the query but absent from confirmed citations","safeguard":"candidate only; require review before treating as a true negative"},"label":"implicit_negative_candidate","query":"How should we evaluate a RAG retriever from product traces?","query_id":"q-001","rank":2,"run_id":"run-001","score":0.81,"source":"retrieved_unused"}
{"chunk_id":"draft","confidence":0.46,"doc_id":"weak-match","evidence":{"reason":"retrieved for the query but absent from confirmed citations","safeguard":"candidate only; require review before treating as a true negative"},"label":"implicit_negative_candidate","query":"How should we evaluate a RAG retriever from product traces?","query_id":"q-001","rank":4,"run_id":"run-001","score":0.41,"source":"retrieved_unused"}
```

## Limitations

- Citation parsing is intentionally conservative and supports `doc://...` links plus simple `[[doc#chunk=...]]` references.
- Implicit negatives are candidates, not ground truth negatives.
- The script does not fetch documents or call external services.
- Alignment is based on `query_id`, `doc_id`, and `chunk_id`; inconsistent IDs should be normalized before running the CLI.
