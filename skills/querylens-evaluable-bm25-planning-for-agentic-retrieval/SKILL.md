---
name: querylens-evaluable-bm25-planning-for-agentic-retrieval
description: Builds deterministic BM25 query plan JSON for agentic retrieval when prompts mention QueryLens, BM25 planning, query planning, retrieval evaluation, local corpus search, or auditable RAG.
license: MIT
---

# QueryLens — Evaluable BM25 Planning for Agentic Retrieval

Auto-generated and experimental; review plans before using them in production retrieval pipelines.

## Overview

QueryLens turns a natural-language question and a local text corpus into a structured BM25 retrieval plan. It keeps planning focused on the retrieval layer by extracting rare terms, useful phrase candidates, exclusions, preserved constraints, and verification checklist items without calling an LLM.

The bundled script uses corpus-level IDF statistics over unigrams, bigrams, and trigrams, plus lightweight rule-based synonym and constraint heuristics. The output is deterministic JSON that an assistant, agent, or local RAG workflow can inspect before search is executed.

## When to use

- Use when a user asks for QueryLens, BM25 planning, evaluable query plans, auditable retrieval, transparent RAG search, local corpus search, or agentic retrieval preparation.
- Use before running BM25 or lexical search when the question must be rewritten into include terms, optional expansion terms, exclusions, and preserved constraints.
- Use when search quality needs a checklist that can be reviewed separately from answer generation.
- Use for offline research workflows where no API key, embedding model, or network dependency should be required.
- When NOT to use: do not use this skill as a final answer generator or semantic embedding retriever.

## Workflow

1. Collect a natural-language question and a local corpus as a text file, Markdown file, JSON file, JSONL file, or directory of those files.
2. Run `python3 scripts/run.py --question "..." --corpus path/to/corpus --pretty` or provide a combined JSON input with `--input`.
3. Inspect `include_terms` for rare unigrams, bigrams, and trigrams that should drive BM25 matching.
4. Inspect `optional_expansion_terms` and remove any expansion that changes intent.
5. Inspect `exclusion_terms` and `preserved_constraints` to make sure negations, quoted phrases, dates, numbers, and acronyms survived planning.
6. Use `bm25_query` as the first-pass lexical query, and apply exclusions or checklist items in the caller's retrieval/evaluation layer.
7. Run `python3 scripts/test.py` after edits to confirm the bundled reference implementation still works.

## Inputs & Outputs

Input contract:

- `question`: a non-empty natural-language question.
- `documents`: one or more local text documents, supplied directly in JSON or loaded from a file/directory.
- Optional environment variables:
  - `QUERYLENS_MAX_TERMS`: positive integer limit for include terms.
  - `QUERYLENS_SYNONYMS_JSON`: JSON object mapping lower-case terms to arrays of expansion terms.

Exact output shape:

```json
{
  "question": "string",
  "corpus": {
    "document_count": 0,
    "source": "string"
  },
  "plan": {
    "bm25_query": "string",
    "include_terms": [
      {
        "term": "string",
        "kind": "unigram|bigram|trigram",
        "idf": 0.0,
        "reason": "string"
      }
    ],
    "optional_expansion_terms": [
      {
        "term": "string",
        "source": "template",
        "for": "string"
      }
    ],
    "exclusion_terms": ["string"],
    "preserved_constraints": [
      {
        "constraint": "string",
        "type": "quoted_phrase|numeric|acronym|negation|key_phrase"
      }
    ],
    "verification_checklist": ["string"]
  },
  "diagnostics": {
    "question_terms_considered": ["string"],
    "corpus_top_rare_terms": ["string"]
  }
}
```

## Installation

Copy this folder into a Claude Code, OpenClaw, or compatible skills directory, then run the script with Python 3.10 or newer. No third-party packages are required.

## Usage

```bash
python3 scripts/run.py --help
python3 scripts/run.py --selftest
python3 scripts/run.py --input examples/querylens_input.json --pretty
python3 scripts/run.py --question "How can hybrid retrieval evaluation run on a local corpus without external APIs?" --corpus examples/querylens_input.json --pretty
python3 scripts/test.py
```

Optional environment configuration:

```bash
QUERYLENS_MAX_TERMS=8 python3 scripts/run.py --input examples/querylens_input.json --pretty
QUERYLENS_SYNONYMS_JSON='{"retrieval":["lexical search"],"evaluation":["relevance audit"]}' python3 scripts/run.py --input examples/querylens_input.json --pretty
```

## Example

```bash
python3 scripts/run.py --input examples/querylens_input.json --pretty
```

Expected output is stored in `examples/querylens_expected_output.json`. It includes a `bm25_query` similar to:

```text
"external apis" "hybrid retrieval" "local corpus" corpus evaluation hybrid local retrieval
```

## Limitations

- QueryLens is a planning helper, not a full BM25 search engine.
- Synonyms are template-based and should be reviewed for domain fit.
- Rule-based negation detection only captures simple windows after terms like `without`, `exclude`, and `avoid`.
- Corpus IDF is only as reliable as the supplied local documents.
- The output is deterministic, but it does not measure downstream ranking quality by itself.
