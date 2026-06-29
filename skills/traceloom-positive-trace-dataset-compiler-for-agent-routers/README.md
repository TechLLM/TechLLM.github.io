# TraceLoom - Positive-Trace Dataset Compiler for Agent Routers

TraceLoom is a small installable skill that compiles successful agent and RAG execution traces into positive-only router training data.

## Install

Copy this directory into your Claude Code or OpenClaw skills directory.

No external Python dependencies are required.

## Run

Use built-in sample data:

```bash
python scripts/run.py
```

Use the included example file:

```bash
python scripts/run.py --input examples/sample_traces.jsonl --output out
```

Generated files:

- `out/positive_routes.jsonl`
- `out/node_success_matrix.csv`
- `out/report.md`

## Input format

TraceLoom expects newline-delimited JSON. A trace should include a success indicator such as `success`, `passed`, `validated`, or `is_correct`, plus route evidence in fields such as `steps`, `tool_calls`, `retriever_hits`, `scorer_choices`, `cited_documents`, `documents`, `nodes`, or `route`.

## Configuration

Flags:

```bash
python scripts/run.py --help
```

Environment variables:

- `TRACELOOM_INPUT`
- `TRACELOOM_OUTPUT`
- `TRACELOOM_SUCCESS_FIELDS`
