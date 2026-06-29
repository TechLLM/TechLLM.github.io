---
name: traceloom-positive-trace-dataset-compiler-for-agent-routers
description: Compile successful agent and RAG JSONL traces into positive-only router datasets and reports when you need TraceLoom, positive traces, router training data, RAG routing evaluation, or trace log analysis.
license: MIT
---

# TraceLoom - Positive-Trace Dataset Compiler for Agent Routers

Auto-generated and experimental; review outputs before using them for model training or evaluation decisions.

## Overview

TraceLoom compiles evaluation logs from agent and RAG systems into positive-only routing datasets. It reads JSONL traces, keeps successful runs, extracts route components that contributed to the validated answer, and writes:

- `positive_routes.jsonl` for downstream router fine-tuning or preference learning
- `node_success_matrix.csv` for component-level contribution analysis
- `report.md` for a compact summary of success rate, route frequency, and top components

The bundled implementation is intentionally lightweight and self-contained. It supports common trace shapes such as `steps`, `route`, `tool_calls`, `retriever_hits`, `scorer_choices`, `cited_documents`, and `nodes`.

## When to use

Use this skill when you need to:

- Compile successful agent traces into router-ready supervision data
- Analyze which tools, retrievers, documents, scorers, or nodes appear in validated answers
- Bootstrap routing datasets without hand-labeling negative examples
- Compare route quality across evaluation runs, experiments, datasets, or deployments

Trigger keywords include `TraceLoom`, `positive trace`, `agent router`, `RAG routing`, `JSONL traces`, `positive_routes.jsonl`, and `node_success_matrix.csv`.

## Installation

Copy this skill directory into your Claude Code or OpenClaw skills folder, then run the script from the skill root.

No Python packages are required.

```bash
python scripts/run.py --help
```

## Usage

Run with built-in sample traces:

```bash
python scripts/run.py
```

Compile an input JSONL file:

```bash
python scripts/run.py --input examples/sample_traces.jsonl --output out
```

Customize success-field detection:

```bash
python scripts/run.py \
  --input examples/sample_traces.jsonl \
  --output out \
  --success-fields success,passed,validated,is_correct
```

Use environment variables instead of flags:

```bash
TRACELOOM_INPUT=examples/sample_traces.jsonl TRACELOOM_OUTPUT=out python scripts/run.py
```

## Example

Input JSONL record:

```json
{"trace_id":"trace-001","success":true,"query":"How do I reset billing limits?","steps":[{"type":"retriever","name":"billing_docs","documents":[{"id":"doc-billing-limits","title":"Billing limits"}]},{"type":"tool","name":"account_lookup"},{"type":"scorer","name":"answer_faithfulness"}],"answer":"Billing limits can be changed in workspace settings.","citations":["doc-billing-limits"]}
```

Output `positive_routes.jsonl` record:

```json
{"trace_id":"trace-001","query":"How do I reset billing limits?","positive_route":["retriever:billing_docs","document:doc-billing-limits","tool:account_lookup","scorer:answer_faithfulness"],"components":[{"kind":"retriever","id":"billing_docs"},{"kind":"document","id":"doc-billing-limits"},{"kind":"tool","id":"account_lookup"},{"kind":"scorer","id":"answer_faithfulness"}],"source_success_field":"success"}
```

## Limitations

- Positive-only data improves route imitation but does not replace negative evaluation.
- Trace extraction is schema-tolerant, not schema-complete; unusual logs may need normalization before compilation.
- The script treats cited or traversed components as positive contributors and cannot prove causal contribution by itself.
- Built-in mock data is for smoke testing only.
