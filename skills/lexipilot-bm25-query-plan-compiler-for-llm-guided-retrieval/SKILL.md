---
name: lexipilot-bm25-query-plan-compiler-for-llm-guided-retrieval
description: Compile natural-language questions into BM25-friendly retrieval plans for local Markdown or text corpora; use for LexiPilot, BM25, lexical retrieval, query planning, sparse identifiers, wikilinks, arXiv IDs, technical docs, and LLM-guided retrieval.
license: MIT
---

# LexiPilot

Auto-generated and experimental installable skill.

## Overview

LexiPilot compiles a natural-language question into a structured retrieval plan for lexical search. It is designed for local Markdown and plain text corpora where exact wording, titles, aliases, paper IDs, wiki links, and technical terms matter.

The bundled reference CLI uses only the Python standard library. It extracts Markdown headings, wiki links, aliases, identifiers, rare terms, and section-level subqueries, then emits a JSON plan and executable BM25-style query strings. When SQLite FTS5 is available, it can also build an in-memory full-text index and run the generated queries directly.

## When to use

Use this skill when a task involves:

- BM25 query planning for a local corpus.
- LLM-guided retrieval where the model should plan searches instead of answer directly.
- Technical docs, paper notes, research notebooks, or wiki-style Markdown.
- Long-tail terms, sparse identifiers, arXiv IDs, RFCs, CVEs, DOIs, function names, and exact titles.
- Retrieval pipelines that need JSON query plans before search execution.

## Installation

Copy this folder into your skills directory and keep its relative layout intact:

```bash
mkdir -p skills
cp -R . skills/lexipilot-bm25-query-plan-compiler-for-llm-guided-retrieval
```

No Python dependencies are required.

## Usage

Run with built-in sample data:

```bash
python scripts/run.py
```

Plan and search a local Markdown or text corpus:

```bash
python scripts/run.py --question "Which notes compare BM25 with dense retrieval for arXiv:2305.10403?" --corpus examples/corpus --search
```

Write the machine-readable plan to a file:

```bash
python scripts/run.py --question-file examples/question.txt --corpus examples/corpus --out examples/plan.json
```

Print only the generated query strings:

```bash
python scripts/run.py --question-file examples/question.txt --corpus examples/corpus --queries-only
```

## Example

```bash
python scripts/run.py --question-file examples/question.txt --corpus examples/corpus --search --top-k 3
```

The command emits JSON with:

- `signals`: extracted titles, headings, wiki links, aliases, identifiers, rare terms, exclusions, and technical terms.
- `section_queries`: decomposed subqueries for broad or multi-hop questions.
- `queries`: executable lexical query strings.
- `search_results`: optional SQLite FTS5 results when search is enabled.

## Limitations

- The reference implementation is a deterministic local planner, not a hosted LLM integration.
- SQLite FTS5 availability depends on the local Python SQLite build.
- It is optimized for small to medium local corpora, not large production search clusters.
- Query compilation is heuristic and should be reviewed before use in high-stakes retrieval workflows.
