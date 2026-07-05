---
name: queryloom-verifiable-bm25-planning-for-rag
description: Creates verifiable BM25 retrieval plans for local RAG corpora when you need query decomposition, TF-IDF rare-term targeting, synonym slots, exclusion terms, retrieval_plan.json, or RAG retrieval debugging.
license: MIT
---

# QueryLoom - Verifiable BM25 Planning for RAG

Auto-generated and experimental; review retrieval plans before using them in production pipelines.

## Overview

QueryLoom helps teams debug retrieval before answer generation by turning a user question and a local text corpus into an explicit `retrieval_plan.json`. It analyzes corpus vocabulary with TF-IDF, selects rare-term candidates, decomposes the question into BM25-ready subqueries, and records synonym slots, exclusions, and evidence requirements.

The goal is to make retrieval strategy testable, versionable, and inspectable before a RAG system performs search.

## When to use

- Use when a RAG answer fails because the retriever may have searched for the wrong terms.
- Use when you need BM25, lexical search, sparse retrieval, TF-IDF, rare-term targeting, query decomposition, synonym slots, or exclusion terms.
- Use when building documentation assistants, research copilots, local knowledge-base search, or agentic retrieval control planes.
- Use when you want a `retrieval_plan.json` artifact that can be reviewed in code review or compared across experiments.
- When NOT to use: do not use this as a final answer generator or as a substitute for running and evaluating the actual retriever.

## Workflow

1. Collect the user question and the local Markdown or plain-text corpus.
2. Run `scripts/run.py` on the corpus to compute token statistics and TF-IDF rare-term candidates.
3. Review the generated synonym slots and exclusion terms for domain fit.
4. Inspect each subquery's `bm25_query`, `required_terms`, `optional_terms`, and `evidence_requirements`.
5. Run the BM25 queries in your retrieval pipeline.
6. Compare retrieved passages against the evidence requirements.
7. Revise the corpus, question, or retrieval plan when important evidence is missing.
8. Commit the plan with retrieval tests when it represents useful retrieval behavior.

## Inputs & Outputs

Input contract:

- `question`: a single natural-language question supplied with `--question` or `--question-file`.
- `corpus`: a file or directory supplied with `--corpus`; supported file types are `.md`, `.txt`, and `.text`.
- Optional configuration: `--max-terms` controls rare-term candidate count and `--top-k` records the intended retrieval depth.
- Optional environment keys: `OPENAI_API_KEY` or `QUERYLOOM_API_KEY` may exist for future external planner integrations, but the bundled script does not require or transmit them.

Exact output shape:

```json
{
  "schema_version": "1.0",
  "planner": {
    "name": "queryloom-local-heuristic",
    "mode": "local",
    "external_llm_used": false
  },
  "question": "string",
  "corpus": {
    "document_count": 0,
    "token_count": 0,
    "vocabulary_size": 0,
    "top_k": 5
  },
  "rare_term_candidates": [
    {
      "term": "string",
      "tf_idf": 0.0,
      "document_frequency": 0
    }
  ],
  "synonym_slots": [
    {
      "slot": "string",
      "terms": ["string"]
    }
  ],
  "subqueries": [
    {
      "id": "q1",
      "intent": "string",
      "bm25_query": "string",
      "required_terms": ["string"],
      "optional_terms": ["string"],
      "exclusion_terms": ["string"],
      "evidence_requirements": ["string"]
    }
  ]
}
```

## Installation

Copy this folder into your skills directory, then run the local self-test:

```bash
python3 scripts/run.py --selftest
python3 scripts/test.py
```

No third-party packages are required.

## Usage

Show command help:

```bash
python3 scripts/run.py --help
```

Run the built-in deterministic sample:

```bash
python3 scripts/run.py --selftest
```

Create a retrieval plan from example files:

```bash
python3 scripts/run.py \
  --question-file examples/question.txt \
  --corpus examples/corpus.md \
  --output retrieval_plan.json
```

Create a retrieval plan from an inline question and a corpus directory:

```bash
python3 scripts/run.py \
  --question "How can BM25 planning reduce RAG retrieval failures?" \
  --corpus docs \
  --max-terms 8 \
  --top-k 5 \
  --output retrieval_plan.json
```

## Example

Command:

```bash
python3 scripts/run.py --question-file examples/question.txt --corpus examples/corpus.md
```

Expected output excerpt:

```json
{
  "schema_version": "1.0",
  "planner": {
    "name": "queryloom-local-heuristic",
    "mode": "local",
    "external_llm_used": false
  },
  "question": "How can QueryLoom reduce RAG retrieval failures with BM25 planning?"
}
```

The full expected output is stored in `examples/expected_output.json`.

## Limitations

- The bundled implementation is a deterministic local planner, not a full LLM planner.
- TF-IDF rare-term selection is lexical and does not understand meaning beyond simple synonym slots.
- BM25 query syntax is generic and may need adaptation for a specific search engine.
- The script does not run retrieval or judge final answer quality.
- Small corpora can produce unstable rare-term rankings because every term may be rare.
