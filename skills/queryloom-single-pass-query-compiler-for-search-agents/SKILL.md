---
name: queryloom-single-pass-query-compiler-for-search-agents
description: Compiles natural-language questions and local corpora into BM25-ready expanded query plans for search agents; use for Queryloom, BM25, query expansion, search-agent retrieval, rare terms, aliases, exclusions, and subqueries.
license: MIT
---

# Queryloom - Single-Pass Query Compiler for Search Agents

Auto-generated and experimental; review outputs before using them in production retrieval systems.

## Overview

Queryloom turns a user question and a local document corpus into a compact JSON query plan for lexical retrieval. It uses standard-library tokenization, BM25-style IDF, and lightweight TF-IDF scoring to identify discriminative terms, aliases, exclusions, weighted terms, and focused subqueries before search begins.

The bundled script is intentionally small and deterministic. It does not call external services and can run with built-in sample data.

## When to use

Use this skill when a task involves:

- Building BM25 or keyword-search queries for an agent.
- Reducing repeated search-inspect-rewrite loops.
- Expanding a natural-language question with corpus-aware rare terms.
- Creating aliases, synonym candidates, negative constraints, or staged subqueries.
- Preparing query JSON for retrieval orchestration.

Trigger keywords include `Queryloom`, `BM25`, `query expansion`, `search agent`, `retrieval query`, `rare terms`, `aliases`, `exclusions`, and `subqueries`.

## Installation

Copy this folder into your skills directory, then run the included script from the skill root:

```bash
python scripts/run.py
```

No Python packages are required.

## Usage

Run with built-in sample data:

```bash
python scripts/run.py
```

Run against the example corpus:

```bash
python scripts/run.py --question "How can search agents reduce wasted BM25 retrieval calls without relying only on vector search?" --corpus examples/corpus.json
```

Write the query plan to a file:

```bash
python scripts/run.py --question-file examples/question.txt --corpus examples/corpus.json --output query_plan.json
```

Tune output size:

```bash
python scripts/run.py --question "Find rate-limit friendly retrieval tactics for agents" --corpus examples/corpus.json --top-k 8 --max-subqueries 3
```

## Example

Input question:

```text
How can search agents reduce wasted BM25 retrieval calls without relying only on vector search?
```

Output shape:

```json
{
  "primary_query": "agents bm25 calls reduce search retrieval -\"vector search\" -vector",
  "weighted_terms": [
    {"term": "bm25", "weight": 5.0, "idf": 1.204, "reason": "question term found in relevant corpus documents"}
  ],
  "aliases": [
    {"source": "bm25", "aliases": ["lexical search", "keyword ranking"]}
  ],
  "exclusions": ["vector search", "vector"]
}
```

Actual output depends on the supplied corpus.

## Limitations

- Queryloom is lexical and corpus-local; it does not replace vector search, reranking, or full agent planning.
- Alias generation uses a small built-in synonym table plus simple spelling variants.
- Negative constraints are extracted from simple phrases such as `without`, `excluding`, `avoid`, and `not`.
- The scoring is designed as a reference implementation, not as a tuned production ranker.
