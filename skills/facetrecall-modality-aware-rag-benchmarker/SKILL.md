---
name: facetrecall-modality-aware-rag-benchmarker
description: Benchmark modality-aware RAG retrieval slices and use when evaluating RAG, retrieval, FacetRecall, modality, false-pass, missing-context, or mixed-document benchmarks.
license: MIT
---

# FacetRecall - Modality-Aware RAG Benchmarker
Auto-generated and experimental; review results before using them for release decisions.

## Overview
FacetRecall helps evaluate retrieval-augmented generation systems whose indexes contain mixed document types. It compares query gold documents with retrieved and accepted documents, then reports recall, false-pass rate, and missing-context failures across domain, modality, document type, corruption, and context-condition slices.

The bundled CLI is intentionally small and deterministic. It is useful as a reference benchmark harness, a pull request check, or a starting point for a more complete evaluation pipeline.

## When to use
- Use when a RAG system looks strong in aggregate but may fail on text notes, tables, code snippets, paper result tables, wiki links, or hybrid documents.
- Use when comparing retrieval behavior across product docs, research notes, engineering logs, policies, and knowledge-base areas.
- Use when you need a Markdown benchmark report for a pull request, model card, benchmark dashboard, or release note.
- Use when you have a query-to-gold-document CSV and a document metadata YAML file.
- When NOT to use: do not use this as a substitute for human answer-quality evaluation or end-to-end generation grading.

## Workflow
1. Prepare a CSV where each row contains a query, the required gold document IDs, the retrieved document IDs, and any accepted/plausible document IDs.
2. Prepare a YAML metadata file that maps each document ID to its domain, modality, document type, corruption state, and context condition.
3. Run `python3 scripts/run.py --queries examples/queries.csv --metadata examples/documents.yaml --output report.md`.
4. Read the overall metrics first, then inspect each facet slice to find weak modalities, domains, document types, corrupted documents, or partial-context cases.
5. Review the missing-context and false-pass sections to identify specific queries and document IDs that need retriever, index, chunking, or metadata fixes.
6. Re-run the benchmark after changing retrieval settings, data preparation, or ranking logic.

## Inputs & Outputs
Input CSV contract:

```text
query_id,query,gold_doc_ids,retrieved_doc_ids,accepted_doc_ids
```

- `query_id`: stable query identifier.
- `query`: natural-language query text.
- `gold_doc_ids`: required supporting document IDs separated by `|`.
- `retrieved_doc_ids`: retrieved document IDs in rank order, separated by `|`.
- `accepted_doc_ids`: optional IDs judged plausible or above an acceptance threshold, separated by `|`; non-gold accepted IDs count as false passes.

Input YAML contract:

```yaml
documents:
  - id: doc_id
    domain: product_docs
    modality: text
    document_type: note
    corruption: clean
    context_condition: complete
```

Output shape:

```text
# FacetRecall Report
## Overall
- query_count
- recall
- hit_rate
- false_pass_rate
- missing_context_failure_rate

## Slices
- facet
- value
- query_count
- recall
- false_pass_rate
- missing_context_failures

## Missing Context Failures
- query_id
- missing_gold_doc_ids
- missing_facets

## False Passes
- query_id
- accepted_non_gold_doc_ids
```

The CLI can also emit JSON with top-level fields `overall`, `slices`, `missing_context_failures`, `false_passes`, and `warnings`.

## Installation
Copy or install this skill folder into your skills directory, then run the CLI with Python 3. No third-party packages are required.

```bash
python3 scripts/run.py --help
python3 scripts/test.py
```

Optional environment variables:

```bash
export FACETRECALL_TOP_K=5
export FACETRECALL_LIST_DELIMITER='|'
```

## Usage
Run the built-in self-test:

```bash
python3 scripts/run.py --selftest
```

Run the example benchmark and write a Markdown report:

```bash
python3 scripts/run.py \
  --queries examples/queries.csv \
  --metadata examples/documents.yaml \
  --output report.md
```

Emit JSON instead of Markdown:

```bash
python3 scripts/run.py \
  --queries examples/queries.csv \
  --metadata examples/documents.yaml \
  --format json
```

Show help:

```bash
python3 scripts/run.py --help
```

## Example
Command:

```bash
python3 scripts/run.py --queries examples/queries.csv --metadata examples/documents.yaml
```

Expected output excerpt:

```text
# FacetRecall Report

## Overall

| metric | value |
| --- | ---: |
| queries | 5 |
| recall | 0.600 |
| hit_rate | 0.600 |
| false_pass_rate | 0.600 |
| missing_context_failure_rate | 0.400 |
```

See `examples/expected_output.md` for the complete deterministic report.

## Limitations
- The YAML parser supports the simple `documents:` list shape shown above, not arbitrary YAML.
- Recall is calculated from document IDs, not semantic answer correctness.
- False-pass detection depends on the supplied `accepted_doc_ids` field.
- The script does not call external APIs, score embeddings, or run a live retriever.
