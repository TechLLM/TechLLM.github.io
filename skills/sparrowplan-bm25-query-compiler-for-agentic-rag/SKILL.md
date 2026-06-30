---
name: sparrowplan-bm25-query-compiler-for-agentic-rag
description: Compiles natural-language RAG questions into transparent BM25 query plans for local Markdown/plain-text corpora; use it for SparrowPlan, BM25, lexical retrieval, sparse retrieval, agentic RAG, and query compiler workflows.
license: MIT
---

# SparrowPlan - BM25 Query Compiler for Agentic RAG

Auto-generated and experimental: treat this skill as a small working reference implementation, not a production retrieval stack.

## Overview

SparrowPlan compiles a natural-language question into an inspectable sparse retrieval plan for local Markdown and plain-text corpora. It treats BM25 queries as compilation targets: weighted lexical terms, rare-term candidates, expansion hints, and a staged coarse-to-fine retrieval path.

The bundled script, `scripts/run.py`, works as a minimal `rag-query-compiler` reference CLI. It uses deterministic local heuristics and a standard BM25 scorer to rank collections, documents, and passages, then emits JSON suitable for debugging, evaluation, or regression tests.

## When to use

Use this skill when you need:

- A BM25 or lexical retrieval plan for RAG.
- Sparse retrieval over local `.md` or `.txt` files.
- Transparent query weights and rare-term candidates.
- Coarse-to-fine retrieval across collections, documents, and passages.
- A small local baseline before adding embeddings or a hosted search service.

Trigger keywords include `SparrowPlan`, `BM25`, `query compiler`, `rag-query-compiler`, `agentic RAG`, `lexical retrieval`, `sparse retrieval`, `rare terms`, and `coarse-to-fine retrieval`.

## Installation

Copy this directory into your skills folder or run it directly from the checked-out skill directory.

No third-party Python packages are required.

```bash
python scripts/run.py
```

Optional shell alias:

```bash
alias rag-query-compiler='python scripts/run.py'
```

## Usage

Run with built-in sample data:

```bash
python scripts/run.py
```

Run against the bundled example corpus:

```bash
python scripts/run.py --question "How should an agent improve BM25 retrieval over Markdown docs?" --corpus examples/corpus
```

Read a question from a file and save JSON:

```bash
python scripts/run.py --question-file examples/question.txt --corpus examples/corpus --json-out examples/output.json
```

Tune retrieval stage limits:

```bash
python scripts/run.py --question "How do rare terms improve sparse retrieval?" --corpus examples/corpus --top-collections 2 --top-docs 3 --top-passages 5
```

## Example

```bash
python scripts/run.py --question-file examples/question.txt --corpus examples/corpus
```

The output contains:

- `plan.weighted_terms`: BM25-ready terms with numeric weights.
- `plan.rare_term_candidates`: low-document-frequency terms that may increase lexical precision.
- `plan.expansion_hints`: conservative synonym or related-term suggestions.
- `results.collections`: coarse collection matches.
- `results.documents`: document-level matches.
- `results.passages`: high-signal passage matches.

## Limitations

- The reference planner is heuristic and deterministic; it does not call an LLM.
- Optional API key environment variables are detected only to report local planning mode; no network calls are made.
- It supports Markdown and plain-text files, not PDFs, HTML, databases, or binary formats.
- BM25 scoring is implemented for clarity and portability, not maximum indexing performance.
- Expansion hints are conservative and small; domain teams should tune them for their corpus.
