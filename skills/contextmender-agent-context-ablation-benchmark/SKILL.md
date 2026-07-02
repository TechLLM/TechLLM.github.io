---
name: contextmender-agent-context-ablation-benchmark
description: Generates JSONL context ablation benchmark variants and evaluator templates for LLM agent workflows when you need context ablation, agent evaluation, prompt robustness, retrieval, memory, tools, dialogue, or policy testing.
license: MIT
---

# ContextMender Agent Context Ablation Benchmark

Auto-generated and experimental: use this as a small working reference implementation, then adapt it to your evaluation stack.

## Overview

ContextMender is a JSONL-first benchmark helper for testing how strongly an LLM agent depends on specific context components. It creates controlled ablation datasets by removing one context field at a time, such as retrieval results, memory, tool descriptions, recent dialogue, policies, environment state, or custom fields.

The bundled CLI writes:

- A full-context baseline JSONL dataset.
- One variant JSONL file per missing-context condition.
- Markdown grading templates for each condition.
- A manifest describing the generated files and run configuration.

## When to use

Use this skill when you need to:

- Run context ablation, agent evaluation, or prompt robustness checks.
- Compare failures when retrieval, memory, tools, dialogue, policies, or environment fields are missing.
- Prepare datasets for human review, LLM-as-judge review, or automated graders.
- Create evaluator-ready scoring templates from agent task datasets.

## Installation

Copy or install this skill folder into your Claude Code or OpenClaw-compatible skills directory.

No Python packages are required. The CLI uses only the Python standard library.

## Usage

Run with built-in sample data:

```bash
python scripts/run.py
```

Run with the included example file:

```bash
python scripts/run.py --input examples/tasks.jsonl --output-dir outputs/example-run
```

Ablate specific fields:

```bash
python scripts/run.py --input examples/tasks.jsonl --fields retrieval,memory,tools,policies
```

Ablate a custom dotted field:

```bash
python scripts/run.py --input examples/tasks.jsonl --fields context.retrieval,context.memory,metadata.priority
```

Choose how ablated fields are represented:

```bash
python scripts/run.py --mode remove
python scripts/run.py --mode empty
python scripts/run.py --mode marker
```

## Example

Input JSONL records should be JSON objects. A minimal record can look like this:

```json
{"id":"refund-001","task":"Draft a support reply for a refund request.","context":{"retrieval":["Refunds are available within 30 days."],"memory":["The customer prefers concise email replies."],"tools":[{"name":"lookup_order","description":"Fetch order status by order id."}],"dialogue":["User: I need a refund for order A100."],"policies":["Do not promise refunds before checking eligibility."]},"expected_output":"A concise reply that checks eligibility before promising a refund.","rubric":["Uses the refund policy","Does not invent order status","Keeps a professional tone"]}
```

Command:

```bash
python scripts/run.py --input examples/tasks.jsonl --output-dir outputs/contextmender-demo
```

Expected outputs include `outputs/contextmender-demo/variants/missing_retrieval.jsonl` and `outputs/contextmender-demo/grading_templates/missing_retrieval.md`.

## Limitations

- This reference implementation generates datasets and templates; it does not call external model APIs.
- It does not guarantee that an ablation is semantically equivalent across tasks.
- It removes one configured field at a time and does not generate combinatorial multi-field ablations.
- Local heuristic scoring is intentionally out of scope; connect the generated variants to your own human, LLM-as-judge, or automated grading pipeline.
