---
name: modulens-modality-aware-evidence-router-for-rag
description: ModuLens routes and scores modality-aware evidence for RAG when working with scientific retrieval, technical retrieval, evidence routing, reranking features, tables, code, formulas, citations, dates, or benchmarks.
license: MIT
---

# ModuLens - Modality-Aware Evidence Router for RAG

Auto-generated & experimental: validate outputs before using them in production retrieval pipelines.

## Overview

ModuLens is a small CLI and Python reference implementation for producing structured relevance features from Markdown, plain text, and lightweight technical documents. It detects evidence spans such as tables, code blocks, formulas, citations, dates, and benchmark results, then scores those spans against a user question.

The output is JSON designed for downstream rerankers, agents, and retrieval-augmented generation systems.

## When to use

Use this skill when the task involves:

- Modality-aware RAG, evidence routing, or technical retrieval.
- Ranking documents where tables, code, formulas, citations, dates, or benchmarks matter.
- Creating machine-readable relevance features for a reranker or agent.
- Diagnosing why a technical document matched a query.
- Trigger keywords: ModuLens, modality-aware evidence, evidence router, RAG reranker, technical retrieval, benchmark evidence, citation support, table evidence, code evidence, formula evidence.

## Installation

No third-party Python packages are required.

```bash
python --version
python scripts/run.py
```

To install as an agent skill, copy this folder into your agent's skills directory and restart or reload the agent so it can discover `SKILL.md`.

## Usage

Run the built-in mock sample:

```bash
python scripts/run.py
```

Score the included example document:

```bash
python scripts/run.py --question "Which system has better F1 and latency?" --input examples/sample.md --pretty
```

Score every supported file in a directory:

```bash
python scripts/run.py --question "What implementation details support the benchmark result?" --input examples --pretty
```

Write feature JSON to a file:

```bash
python scripts/run.py --question "Does the paper cite evidence for the 2024 result?" --input examples/sample.md --output modulens-output.json
```

Use custom modality weights:

```bash
python scripts/run.py --question "Show code-level implementation evidence" --input examples/sample.md --weights examples/weights.json --profile software --pretty
```

Use it from Python:

```python
from scripts.run import route_evidence

docs = [{"id": "doc-1", "text": "Accuracy improved to 91.2% in 2024 [1]."}]
features = route_evidence("Which benchmark improved in 2024?", docs)
print(features["documents"][0]["score"])
```

Optional environment variables such as `MODULENS_API_KEY` or `OPENAI_API_KEY` are detected only to report whether an external key is present. This reference implementation does not call external services.

## Example

```bash
python scripts/run.py --question "Which method reports the strongest benchmark evidence?" --input examples/sample.md --pretty
```

Example output shape:

```json
{
  "query": "Which method reports the strongest benchmark evidence?",
  "question_profile": {
    "needs": ["numeric_comparison", "experimental_result"]
  },
  "documents": [
    {
      "id": "sample.md",
      "score": 0.73,
      "features": {
        "modality_counts": {
          "table": 1,
          "citation": 2,
          "date": 3,
          "benchmark": 4
        }
      }
    }
  ]
}
```

## Limitations

- Uses heuristic detection, not a full Markdown, PDF, LaTeX, or HTML parser.
- Scores are meant as reranker features, not final truth labels.
- Citation and formula detection can miss unusual formats.
- Table detection is optimized for simple Markdown pipe tables.
- No external embeddings or model calls are performed.
