---
name: evidra-evidence-first-rag-evaluation-cli
description: Evaluate RAG execution traces against evidence expectations and use when trigger keywords include RAG evaluation, evidence-first eval, retrieval traces, citation coverage, forbidden sources, and post-state assertions.
license: MIT
---

# Evidra - Evidence-First RAG Evaluation CLI

Auto-generated and experimental skill for evidence-first RAG evaluation.

## Overview

RAG answers can look correct while using the wrong source, skipping required evidence, citing deprecated documents, or claiming state changes that never happened. Evidra evaluates the observable run instead of only grading the final text. It compares JSONL execution traces, a YAML evidence specification, and generated answer text to produce deterministic JSON reports for CI and regression tracking.

## When to use

- Use when evaluating retrieval-augmented generation runs with trace JSONL, expected evidence YAML, and generated answer text.
- Use when checking retrieval hits, citation coverage, forbidden-source use, or post-state assertions.
- Use for trigger phrases such as "RAG evaluation", "evidence-first eval", "retrieval trace audit", "citation coverage", "forbidden source detection", and "post-state assertion check".
- When NOT to use: do not use this skill as a replacement for human factual review, model safety evaluation, or production-grade observability systems.

## Workflow

1. Prepare a JSONL trace file where each line is one event such as `retrieval`, `citation`, or `tool_call`.
2. Prepare a YAML evidence spec declaring required documents, passages, document types, domains, forbidden sources, and post-state assertions.
3. Save the generated RAG answer as plain text.
4. Run `python scripts/run.py --trace-jsonl examples/trace.jsonl --spec-yaml examples/evidence_spec.yaml --answer examples/answer.txt --pretty`.
5. Review the JSON report for `passed`, score fields, count fields, grouped results, and findings.
6. Add the command to CI or a regression suite when the report shape and thresholds match your team needs.

## Inputs & Outputs

Inputs:

- `--trace-jsonl`: JSON Lines file containing trace events. Supported fields include `event`, `document_id`, `source_id`, `passage_id`, `domain`, `document_type`, `tool`, and `status`.
- `--spec-yaml`: YAML evidence specification. The reference parser supports root scalars and lists of dictionaries for `required_documents`, `forbidden_sources`, and `post_state_assertions`.
- `--answer`: Plain text generated answer. Evidra checks whether required or forbidden source identifiers appear in the answer.
- Optional environment variable: `EVIDRA_API_KEY` may be present for future integrations, but this reference implementation never sends network requests and never prints secrets.

Output shape:

```json
{
  "evaluation_id": "string",
  "passed": true,
  "scores": {
    "overall": 1.0,
    "retrieval_hit_rate": 1.0,
    "citation_coverage": 1.0,
    "forbidden_source_score": 1.0,
    "post_state_assertion_rate": 1.0
  },
  "counts": {
    "required_documents": 0,
    "retrieved_required_documents": 0,
    "required_citations": 0,
    "covered_citations": 0,
    "forbidden_sources_used": 0,
    "post_state_assertions": 0,
    "post_state_assertions_met": 0
  },
  "by_domain": {},
  "by_document_type": {},
  "findings": []
}
```

## Installation

Copy or install this skill directory into a Claude Code or OpenClaw compatible skills folder. The reference CLI uses only the Python standard library.

```bash
python3 --version
python3 scripts/run.py --help
python3 scripts/test.py
```

## Usage

Run the built-in deterministic self-test:

```bash
python3 scripts/run.py --selftest
```

Run against the bundled example:

```bash
python3 scripts/run.py \
  --trace-jsonl examples/trace.jsonl \
  --spec-yaml examples/evidence_spec.yaml \
  --answer examples/answer.txt \
  --pretty
```

Write a report file:

```bash
python3 scripts/run.py \
  --trace-jsonl examples/trace.jsonl \
  --spec-yaml examples/evidence_spec.yaml \
  --answer examples/answer.txt \
  --output report.json
```

Show command help:

```bash
python3 scripts/run.py --help
```

## Example

Command:

```bash
python3 scripts/run.py --selftest
```

Expected output:

```json
{"by_document_type":{"faq":{"required":1,"retrieval_hit_rate":1.0,"retrieved":1},"policy":{"required":1,"retrieval_hit_rate":1.0,"retrieved":1}},"by_domain":{"benefits":{"required":2,"retrieval_hit_rate":1.0,"retrieved":2}},"counts":{"covered_citations":2,"forbidden_sources_used":0,"post_state_assertions":1,"post_state_assertions_met":1,"required_citations":2,"required_documents":2,"retrieved_required_documents":2},"evaluation_id":"sample-benefits-rag","findings":[],"passed":true,"scores":{"citation_coverage":1.0,"forbidden_source_score":1.0,"overall":1.0,"post_state_assertion_rate":1.0,"retrieval_hit_rate":1.0}}
```

## Limitations

- The YAML parser is intentionally small and supports the simple spec structure used by this skill.
- The evaluator checks source identifiers and trace events; it does not prove semantic truth.
- The reference implementation is deterministic and offline, so it does not call LLMs, embeddings, or external APIs.
- Scoring is minimal by design and should be adapted before use as a production quality gate.
