---
name: gatetrace-domain-aware-rag-gate-benchmark
description: Evaluates RAG relevance gates and retrieval systems with domain-sliced metrics; use for GateTrace, RAG gate benchmark, retrieval eval, domain-aware RAG, false-pass, false-block, and missing-evidence analysis.
version: 0.1.0
license: MIT
---

# GateTrace - Domain-Aware RAG Gate Benchmark

Auto-generated and experimental reference skill; review results before relying on them in production.

## Overview

GateTrace evaluates retrieval and relevance-gate behavior beyond a single aggregate score. It reads simple JSONL query records, computes overall and sliced retrieval/gate metrics, and reports where evidence was missed, irrelevant context passed, or relevant context blocked.

The approach is intentionally small and reproducible: domain tags, OOD-like tags, question types, and document metadata become report slices that expose fragile behavior hidden by average recall.

## When to use

- Use when benchmarking a RAG retriever, relevance gate, retrieval agent, or search-planning system.
- Use when a pipeline has acceptable average recall but may fail on specific domains, rare terms, source families, document types, or long-tail intents.
- Use when preparing pull request evidence, model-card notes, CI evaluation artifacts, or dashboard-ready JSON for retrieval quality.
- Use for trigger keywords such as `GateTrace`, `RAG gate benchmark`, `domain-aware RAG`, `retrieval eval`, `false pass`, `false block`, `missing evidence`, and `OOD query`.
- When NOT to use: do not use this as a replacement for human relevance labeling, generator-quality evaluation, security review, or production observability.

## Workflow

1. Prepare a JSONL file with one query record per line using the input contract below.
2. Include `required_doc_ids` for required supporting evidence and `retrieved` documents with `doc_id`, `relevant`, and `gate_pass` labels.
3. Add optional metadata such as `domain_tags`, `ood_tags`, `question_type`, `doc_type`, `source_family`, and `evidence_density` to enable slices.
4. Run `python scripts/run.py --input path/to/input.jsonl --format both --json-out report.json --markdown-out report.md`.
5. Review `missing_evidence`, `false_passes`, and `false_blocks` first; these are usually the highest-signal failure lists.
6. Compare `overall`, `query_slices`, and `document_slices` to identify fragile domains, question types, source families, and evidence patterns.
7. Optional: set `GATETRACE_OOD_TAGS` or pass `--ood-tags` to control which tags count as OOD-like, and use `--fail-under-recall` for CI gating.

## Inputs & Outputs

Input is JSONL. Each line is one object:

```json
{
  "query_id": "q1",
  "query": "What does the refund policy require?",
  "domain_tags": ["billing"],
  "ood_tags": ["rare_terms"],
  "question_type": "policy_lookup",
  "required_doc_ids": ["doc-1"],
  "retrieved": [
    {
      "doc_id": "doc-1",
      "relevant": true,
      "gate_pass": true,
      "doc_type": "policy",
      "source_family": "knowledge_base",
      "domain_tags": ["billing"],
      "evidence_density": "high"
    }
  ]
}
```

Required query fields: `query_id`, `required_doc_ids`, and `retrieved`.

Required retrieved document fields: `doc_id`, `relevant`, and `gate_pass`.

Output is deterministic JSON with this shape:

```json
{
  "summary": {
    "query_count": 0,
    "document_count": 0,
    "required_evidence_count": 0,
    "missing_evidence_query_count": 0,
    "false_pass_count": 0,
    "false_block_count": 0,
    "ood_query_count": 0
  },
  "overall": {
    "required_evidence_count": 0,
    "required_evidence_retrieved_count": 0,
    "retrieved_document_count": 0,
    "relevant_retrieved_count": 0,
    "retrieval_recall": 0.0,
    "retrieval_precision": 0.0,
    "retrieval_f1": 0.0,
    "gate_pass_rate": 0.0,
    "gate_precision": 0.0,
    "gate_recall": 0.0,
    "gate_f1": 0.0,
    "false_pass_rate": 0.0,
    "false_block_rate": 0.0
  },
  "query_slices": {
    "domain_tag": {},
    "question_type": {},
    "ood_tag": {}
  },
  "document_slices": {
    "doc_type": {},
    "source_family": {},
    "evidence_density": {}
  },
  "missing_evidence": [],
  "false_passes": [],
  "false_blocks": [],
  "ood_queries": []
}
```

Markdown output contains the same report summarized as tables and failure lists for human review.

## Installation

Copy this folder into your local skills directory or keep it in a project and run the bundled script directly:

```bash
python scripts/run.py --help
python scripts/test.py
```

No third-party packages are required.

## Usage

Show help:

```bash
python scripts/run.py --help
```

Run the built-in self-test sample:

```bash
python scripts/run.py --selftest
```

Run the example input and write both report formats:

```bash
python scripts/run.py --input examples/sample.jsonl --format both --json-out gatetrace-report.json --markdown-out gatetrace-report.md
```

Use custom OOD-like tags:

```bash
GATETRACE_OOD_TAGS=rare_terms,unfamiliar_domain,long_tail_intent python scripts/run.py --input examples/sample.jsonl --format json
```

Fail CI if aggregate retrieval recall is too low:

```bash
python scripts/run.py --input examples/sample.jsonl --fail-under-recall 0.85
```

## Example

Command:

```bash
python scripts/run.py --input examples/sample.jsonl --format json
```

Expected high-level output:

```json
{
  "summary": {
    "query_count": 4,
    "document_count": 9,
    "required_evidence_count": 5,
    "missing_evidence_query_count": 1,
    "false_pass_count": 2,
    "false_block_count": 1,
    "ood_query_count": 2
  },
  "overall": {
    "retrieval_recall": 0.8,
    "retrieval_precision": 0.5556,
    "gate_pass_rate": 0.6667,
    "false_pass_rate": 0.5,
    "false_block_rate": 0.2
  }
}
```

The full expected output for the sample is stored in `examples/expected-output.json`.

## Limitations

- Metrics depend on the quality and consistency of the provided relevance and gate labels.
- Document-level slices describe observed retrieved documents; they do not infer labels for documents that were never retrieved.
- OOD-like detection is tag-based and configurable, not a learned distribution-shift detector.
- This reference implementation is small by design and does not replace larger evaluation suites, annotation workflows, or live monitoring.

## Verification
Automated execution check: **passed ✅**.

- Steps: structure=ok · syntax=ok · help=ok · selftest=ok · test=ok
- Commands and outputs shown in `README.md` are captured from these real runs.
