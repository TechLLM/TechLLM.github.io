---
name: prooflattice-evidence-matrix-evaluator-for-rag-systems
description: Use ProofLattice to evaluate RAG answers with an evidence matrix when trigger keywords include RAG evaluation, evidence map, citation support, retrieval audit, hallucination check, freshness, or CI regression.
license: MIT
---

# ProofLattice — Evidence Matrix Evaluator for RAG Systems
Auto-generated and experimental; review results before using them for policy, compliance, or release decisions.

## Overview
ProofLattice helps evaluate retrieval-augmented generation outputs without collapsing quality into one opaque relevance score. It decomposes a question, answer, and retrieved documents into auditable checks for directness, evidence coverage, omission risk, freshness, citation support, and factual alignment. The bundled script is a deterministic baseline that uses keyword overlap, citation ID validation, date inspection, and claim-to-source sentence matching.

## When to use
- Use when reviewing RAG answers before human evaluation or LLM-based judging.
- Use for CI regression tests that need repeatable pass, warn, or fail signals.
- Use when auditing citations, retrieved document coverage, stale sources, omissions, or possible hallucinations.
- Use when building dashboards that need a JSON evidence map linking answer claims to source snippets.
- When NOT to use: do not use as the only judge for legal, medical, financial, or high-stakes factual decisions.

## Workflow
1. Prepare a JSON input with `question`, `answer`, `documents`, and optional `config`.
2. Ensure every retrieved document has a stable `id`, `text`, and optionally `title` and ISO `date`.
3. Run `python scripts/run.py --input examples/sample_input.json --format yaml` to produce the human-readable checklist.
4. Add `--evidence-json evidence_map.json` when a separate machine-readable evidence graph is needed.
5. Review principle statuses, low-overlap claims, invalid citation IDs, missing question terms, and stale evidence.
6. Tighten or relax `min_claim_overlap`, `freshness_window_days`, and `citation_pattern` in input `config` or environment variables.
7. Use the result as a first-pass filter, then route warnings and failures to human or model-based review.

## Inputs & Outputs
Input JSON contract:

```json
{
  "question": "string, required",
  "answer": "string, required",
  "documents": [
    {
      "id": "string, required and unique",
      "title": "string, optional",
      "date": "YYYY-MM-DD, optional",
      "text": "string, required"
    }
  ],
  "config": {
    "evaluation_date": "YYYY-MM-DD, optional; defaults to 2026-01-01",
    "freshness_window_days": "integer, optional; defaults to 730",
    "min_claim_overlap": "float, optional; defaults to 0.25",
    "citation_pattern": "regex with one capture group, optional"
  }
}
```

Environment overrides are `PROOFLATTICE_TODAY`, `PROOFLATTICE_FRESHNESS_DAYS`, `PROOFLATTICE_MIN_OVERLAP`, and `PROOFLATTICE_CITATION_PATTERN`.

Output shape:

```yaml
checklist:
  evaluation_id: string
  overall_status: pass | warn | fail
  overall_score: number
  principles:
    - name: directness | evidence_coverage | citation_support | omission_risk | freshness | factual_alignment
      status: pass | warn | fail
      score: number
      rationale: string
      signals: object
  claims_reviewed: number
  recommendations:
    - string
evidence_map:
  evaluation_id: string
  claim_nodes:
    - id: string
      text: string
      citations: [string]
      valid_citations: [string]
      invalid_citations: [string]
      supported: boolean
      citation_supported: boolean
      best_support:
        document_id: string | null
        title: string | null
        date: string | null
        sentence: string | null
        overlap_score: number
        overlap_terms: [string]
  document_nodes:
    - id: string
      title: string
      date: string
      sentence_count: number
  edges:
    - claim_id: string
      document_id: string | null
      relationship: supports | weak_or_missing
      overlap_score: number
      overlap_terms: [string]
      citation_ids: [string]
      sentence: string | null
```

## Installation
Copy or clone this skill folder into your skills directory, then run the script with Python 3.9 or newer. No third-party packages are required.

```bash
python scripts/run.py --help
python scripts/test.py
```

## Usage
Show help:

```bash
python scripts/run.py --help
```

Run the built-in sample:

```bash
python scripts/run.py --selftest
```

Evaluate a JSON case and print YAML:

```bash
python scripts/run.py --input examples/sample_input.json --format yaml
```

Evaluate a JSON case, print YAML, and write a JSON evidence map:

```bash
python scripts/run.py --input examples/sample_input.json --format yaml --evidence-json examples/sample_evidence_map.json
```

Print the full result as JSON:

```bash
python scripts/run.py --input examples/sample_input.json --format json
```

## Example
Command:

```bash
python scripts/run.py --input examples/sample_input.json --format yaml
```

Expected output starts with:

```yaml
checklist:
  evaluation_id: "35cc9128cd73"
  overall_status: "pass"
  overall_score: 0.978
```

The full expected YAML and JSON evidence map are stored in `examples/expected_output.yaml` and `examples/expected_evidence_map.json`.

## Limitations
- This is a deterministic baseline, not a semantic entailment model.
- Keyword overlap can miss paraphrases and can over-credit lexical matches.
- Freshness checks depend on document dates being present and correctly formatted.
- Citation support only validates citation IDs and nearby text overlap.
- Human or LLM review is still needed for nuanced factuality, policy interpretation, and high-risk outputs.
