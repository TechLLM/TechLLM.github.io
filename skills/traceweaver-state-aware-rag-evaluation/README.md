# TraceWeaver - State-Aware RAG Evaluation

Minimal installable skill for grading RAG and agent traces as state transitions.

## Install

Copy this folder into your skills directory. It uses only the Python standard library.

## Run

Built-in sample:

```bash
python scripts/run.py
```

Bundled example:

```bash
python scripts/run.py --trace examples/sample_trace.jsonl --expected examples/expected.json
```

Named CLI wrapper:

```bash
./scripts/rag-state-grader --trace examples/sample_trace.jsonl --expected examples/expected.json
```

JSON output:

```bash
python scripts/run.py --trace examples/sample_trace.jsonl --expected examples/expected.json --format json
```

CI threshold:

```bash
python scripts/run.py --trace examples/sample_trace.jsonl --expected examples/expected.json --fail-under 0.85
```

## Input Format

The trace is JSONL. Common event types are `retrieval`, `tool_call`, `edit`, `diff`, and `final_response`.

The expected spec is JSON with optional `required_evidence`, `expected_actions`, `expected_diffs`, and `answer_requirements`.
