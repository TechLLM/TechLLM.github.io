---
name: masklattice-bias-diagnostics-for-rag-relevance-gates
description: Diagnose bias in RAG relevance gates by masking document fields and paragraph windows; use for trigger keywords MaskLattice, RAG relevance, reranker audit, retrieval bias, relevance gate.
license: MIT
---

# MaskLattice: Bias Diagnostics for RAG Relevance Gates

Auto-generated and experimental; validate outputs before using them for production decisions.

## Overview

MaskLattice treats retrieval evaluation as a controlled perturbation problem. It takes a JSONL file of questions plus candidate documents in Markdown or JSON, creates masked document variants, scores each query-document pair, and reports how much scores and rankings move.

The bundled runner works without private infrastructure. By default it uses a deterministic lexical scorer. For real model or reranker audits, pass a stdin/stdout adapter command with `--adapter-cmd` or set `MASKLATTICE_SCORER_CMD`.

## When to use

Use this skill when you need to audit or regression-test:

- RAG relevance gates
- rerankers
- retrieval evaluation prompts
- score thresholds for answer grounding
- metadata or title leakage in retrieval systems
- ranking instability under irrelevant document perturbations

Good trigger keywords include `MaskLattice`, `RAG relevance`, `reranker audit`, `retrieval bias`, `relevance gate`, `ranking shift`, and `masked evaluation`.

## Installation

Copy this skill directory into your local skills directory, then run it from the copied folder:

```bash
python scripts/run.py
```

No Python package installation is required for the default runner.

## Usage

Run the built-in example:

```bash
python scripts/run.py
```

Run against explicit files:

```bash
python scripts/run.py --queries examples/questions.jsonl --docs examples/docs --out reports/masklattice
```

Use a scorer adapter:

```bash
python scripts/run.py --queries examples/questions.jsonl --docs examples/docs --adapter-cmd "python examples/simple_adapter.py"
```

Use a scorer adapter from the environment:

```bash
MASKLATTICE_SCORER_CMD="python examples/simple_adapter.py" python scripts/run.py
```

Use precomputed scores:

```bash
python scripts/run.py --queries examples/one_question.jsonl --docs examples/docs/rag_gate_evaluation.md --score-file examples/precomputed_scores.jsonl
```

The runner writes:

- `diagnostics.csv`: per-query, per-document, per-mask score and ranking data
- `report.md`: aggregate diagnostics and warnings

## Example

Question input is JSONL:

```json
{"id":"q1","question":"How should a RAG relevance gate avoid metadata bias?"}
```

Candidate documents can be Markdown:

```markdown
# RAG Gate Evaluation

Summary: Relevance gates should rely on evidence in retrieved passages.

Metadata labels can help route documents, but they should not dominate scoring.
```

Or JSON:

```json
{
  "id": "doc1",
  "title": "RAG Gate Evaluation",
  "metadata": {"topic": "retrieval"},
  "summary": "Relevance gates should rely on evidence.",
  "body": ["Metadata labels should not dominate scoring."]
}
```

## Limitations

- The built-in scorer is a deterministic lexical baseline, not a semantic model.
- Mask definitions are intentionally simple and may not match every document schema.
- A high warning score is a diagnostic signal, not proof of model bias.
- Adapter quality determines the usefulness of model-specific conclusions.
- The tool does not call hosted APIs directly; adapters must handle any API authentication through environment variables.
