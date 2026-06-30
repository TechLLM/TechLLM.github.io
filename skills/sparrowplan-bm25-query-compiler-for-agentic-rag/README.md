# SparrowPlan - BM25 Query Compiler for Agentic RAG

SparrowPlan is a small installable skill with a runnable reference CLI for compiling natural-language RAG questions into inspectable BM25 query plans.

## Install

Copy this folder into your skill directory, or run it directly from this directory.

No third-party Python packages are required.

## Usage

Run with built-in sample data:

```bash
python scripts/run.py
```

Run with the bundled example corpus:

```bash
python scripts/run.py --question-file examples/question.txt --corpus examples/corpus
```

Save JSON output:

```bash
python scripts/run.py --question "How do rare terms help BM25 retrieval?" --corpus examples/corpus --json-out examples/output.json
```

Optional alias:

```bash
alias rag-query-compiler='python scripts/run.py'
rag-query-compiler --question-file examples/question.txt --corpus examples/corpus
```

## What It Emits

The CLI prints JSON with:

- A weighted BM25 query plan.
- Rare-term candidates.
- Expansion hints.
- Collection, document, and passage retrieval results.

The implementation is deterministic, local-only, and standard-library only.
