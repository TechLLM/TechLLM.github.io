---
name: querypress-pre-retrieval-bm25-planning-for-llm-search-agents
description: Generate deterministic BM25 pre-retrieval search plans for LLM search agents when prompts mention QueryPress, BM25 planning, lexical retrieval, RAG search planning, rare-term anchors, query decomposition, or noisy search retries.
license: MIT
---

# QueryPress - Pre-Retrieval BM25 Planning

Auto-generated and experimental; inspect plans before using them in production retrieval pipelines.

## Overview

LLM search agents often fail before retrieval because the first query misses rare terms, domain constraints, synonyms, or decomposed sub-questions. QueryPress analyzes a natural-language question and a local document folder with deterministic token statistics, n-grams, and approximate IDF scoring. It emits a structured JSON BM25 plan that can guide first-pass retrieval before any LLM or external search API is used.

## When to use

- Use when an agent, RAG workflow, coding assistant, or research tool needs a high-signal first BM25 query plan.
- Use when the user mentions QueryPress, BM25 planning, lexical retrieval, rare-term anchors, query decomposition, synonym slots, exclusion terms, or noisy tool retries.
- Use when working offline against local `.txt`, `.md`, or `.rst` documents and deterministic output is important.
- Use when evaluating whether better pre-retrieval planning can reduce repeated search attempts.
- When NOT to use: do not use this for semantic embedding search, live web search, private APIs, or tasks that require an LLM to infer unstated domain knowledge.

## Workflow

1. Put the relevant local documents in a folder, preferably as `.txt`, `.md`, or `.rst` files.
2. Write the user's retrieval need as one natural-language question.
3. Run `python scripts/run.py --question-file <question-file> --corpus <document-folder>`.
4. Inspect the `rare_term_anchors`, `synonym_slots`, `exclusion_terms`, and `decomposed_queries` fields.
5. Execute the decomposed query strings with a BM25 backend, local search tool, or agent retrieval tool.
6. Feed retrieved evidence and the JSON plan to the downstream LLM only after the first retrieval pass completes.
7. If the plan is too broad, rerun with `--max-anchors` or `--max-queries` to constrain the output.

## Inputs & Outputs

Input contract:

- `question`: a single natural-language search or research question.
- `corpus`: a folder containing readable local documents with `.txt`, `.md`, or `.rst` extensions.
- Optional environment variables: `QUERYPRESS_MAX_ANCHORS`, `QUERYPRESS_MAX_QUERIES`, and `QUERYPRESS_MIN_TOKEN_LENGTH`.
- No API key is required. If other environment variables exist, the script ignores them.

Output shape:

```json
{
  "question": "string",
  "corpus": {
    "documents": 0,
    "tokens": 0,
    "average_document_length": 0.0,
    "top_terms": [
      {"term": "string", "document_frequency": 0, "corpus_frequency": 0}
    ]
  },
  "plan": {
    "rare_term_anchors": [
      {"term": "string", "idf": 0.0, "document_frequency": 0}
    ],
    "ngram_candidates": [
      {"ngram": "string", "score": 0.0, "terms": ["string"]}
    ],
    "synonym_slots": [
      {"term": "string", "alternatives": ["string"]}
    ],
    "exclusion_terms": ["string"],
    "decomposed_queries": [
      {
        "id": "q1",
        "purpose": "string",
        "query": "string",
        "required_terms": ["string"],
        "optional_terms": ["string"],
        "exclude_terms": ["string"]
      }
    ]
  },
  "execution_notes": ["string"]
}
```

## Installation

Copy or install this skill folder into your Claude Code or OpenClaw skills directory, then run the bundled script with Python 3.10 or newer. The reference implementation uses only the Python standard library, so no dependency installation is required.

## Usage

```bash
python scripts/run.py --help
python scripts/run.py --selftest
python scripts/run.py --question-file examples/question.txt --corpus examples/corpus
python scripts/run.py --question "How can BM25 planning improve LLM retrieval?" --corpus examples/corpus --max-queries 3
```

Optional environment configuration:

```bash
QUERYPRESS_MAX_ANCHORS=6 QUERYPRESS_MAX_QUERIES=4 python scripts/run.py --question-file examples/question.txt --corpus examples/corpus
```

## Example

Command:

```bash
python scripts/run.py --question-file examples/question.txt --corpus examples/corpus
```

Expected output is JSON with `question`, `corpus`, `plan`, and `execution_notes` fields. A complete deterministic sample is included in `examples/expected-output.json`.

## Limitations

- The planner is lexical and deterministic; it does not understand meaning beyond tokens, n-grams, and a small built-in synonym table.
- IDF values are approximate and intended for planning, not as a replacement for a full BM25 index.
- Only local plain-text style files are supported by the reference script.
- Exclusion terms are heuristic and should be reviewed before execution.
- The output improves first-pass query formulation but does not verify retrieved evidence.
