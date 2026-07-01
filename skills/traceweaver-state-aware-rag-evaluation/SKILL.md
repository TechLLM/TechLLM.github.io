---
name: traceweaver-state-aware-rag-evaluation
description: Evaluates RAG and agent workflow traces as state transitions with retrieval, citation, action, diff, and answer scoring; use for rag-state-grader, RAG evaluation, trace grading, state-aware RAG, and agent evaluation.
license: MIT
---

# TraceWeaver - State-Aware RAG Evaluation

Auto-generated & experimental skill for evaluating RAG and agent runs as state transitions.

## Overview

TraceWeaver grades a RAG or agentic AI run from a structured JSONL execution trace. It checks whether the run retrieved required evidence, cited the expected sources, performed expected actions, applied expected state changes, and produced an answer aligned with the evidence.

The bundled CLI, `rag-state-grader`, is implemented as `scripts/run.py`. It works offline with deterministic scoring and uses built-in sample data when no input files are provided.

## When to use

Use this skill when you need to evaluate:

- RAG traces with retrieval events, citations, and final answers.
- Agent runs that call tools, edit files, update records, or change graph nodes.
- Test cases where a correct-looking final answer is not enough.
- Failures involving missing evidence, weak citations, incorrect edits, or hallucinated claims.

Trigger keywords include `rag-state-grader`, `RAG evaluation`, `trace grading`, `state-aware RAG`, `agent evaluation`, `retrieval grading`, and `post-run diff grading`.

## Installation

Copy this folder into your local skills directory, then run the script with Python 3. No third-party Python packages are required.

```bash
python scripts/run.py
```

Optional environment variables are detected but not required:

```bash
OPENAI_API_KEY=optional python scripts/run.py
TRACEWEAVER_API_KEY=optional python scripts/run.py
```

The current implementation does not send data to external services; API keys are only detected so downstream users can extend the scorer without hardcoding secrets.

## Usage

Run with built-in mock data:

```bash
python scripts/run.py
```

Run against the bundled example files:

```bash
python scripts/run.py --trace examples/sample_trace.jsonl --expected examples/expected.json
```

Run through the named CLI wrapper:

```bash
./scripts/rag-state-grader --trace examples/sample_trace.jsonl --expected examples/expected.json
```

Emit machine-readable JSON:

```bash
python scripts/run.py --trace examples/sample_trace.jsonl --expected examples/expected.json --format json
```

Fail a CI step when the overall score is too low:

```bash
python scripts/run.py --trace examples/sample_trace.jsonl --expected examples/expected.json --fail-under 0.9
```

## Example

Trace event:

```json
{"type":"retrieval","documents":[{"doc_id":"kb:return-policy","passage_id":"p1","text":"Customers may return eligible items within 30 days."}]}
```

Expected evidence:

```json
{
  "required_evidence": [
    {"doc_id": "kb:return-policy", "passage_id": "p1"}
  ],
  "answer_requirements": {
    "must_include": ["30 days"],
    "must_cite": ["kb:return-policy"]
  }
}
```

Command:

```bash
python scripts/run.py --trace examples/sample_trace.jsonl --expected examples/expected.json --format json
```

## Limitations

- Scoring is deterministic and heuristic, not a substitute for human review.
- Citation matching is based on document and passage identifiers, not semantic entailment.
- Diff grading supports common file, record, and node update shapes but may need adapters for custom event schemas.
- Answer fidelity checks exact required and forbidden phrases; it does not perform model-based claim verification.
