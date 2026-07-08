---
name: diffsentinel-state-change-grading-for-ai-agents
description: Grades before-and-after workspace state changes for AI agents; use for trigger keywords diff grading, state-change grading, agent benchmark, RAG evaluation, CI verification.
version: 0.1.0
license: MIT
---

# DiffSentinel - State-Change Grading for AI Agents

Auto-generated and experimental; review expectations before using results as a hard quality gate.

## Overview

DiffSentinel grades whether an AI agent actually changed files, directories, and structured artifacts as expected, instead of grading only the final natural-language response. It compares a before workspace snapshot, an after workspace snapshot, and an expectation file to produce a deterministic JSON report. The bundled script is dependency-free and intended as a small reference implementation for CI, benchmark suites, and agent development loops.

## When to use

- Use when evaluating agents that create, modify, or delete files.
- Use when a RAG or research workflow must leave citations, logs, or generated artifacts behind.
- Use when benchmark correctness depends on observable state changes rather than one exact answer string.
- Use when CI should fail if required files, JSON fields, citations, or task logs are missing.
- Use trigger keywords such as `diff grading`, `state-change grading`, `agent benchmark`, `workspace verification`, `RAG evaluation`, and `CI verification`.
- When NOT to use: do not use this as the only judge for subjective prose quality, factual correctness beyond explicit assertions, or security review.

## Workflow

1. Capture or preserve a `before` directory that represents the workspace before the agent runs.
2. Run the agent or automation under test and save the resulting `after` directory.
3. Write an expectation YAML file listing required files, created files, deleted files, modified files, forbidden changes, content assertions, JSON assertions, and task-log requirements.
4. Run `python3 scripts/run.py --before BEFORE --after AFTER --expect EXPECTATIONS.yaml`.
5. Read the JSON report fields `pass`, `score`, `summary`, `checks`, and `warnings`.
6. In CI, treat exit code `0` as pass, `1` as grading failure, and `2` as invalid input or usage error.
7. If a check fails, update the agent workflow or expectation file and rerun the same command.

## Inputs & Outputs

Input contract:

- `--before DIR`: directory snapshot before the agent ran.
- `--after DIR`: directory snapshot after the agent ran.
- `--expect FILE`: expectation file in the supported YAML subset.
- Optional `--threshold FLOAT`: minimum score needed to pass; default is `1.0` or `DIFFSENTINEL_SCORE_THRESHOLD`.
- Optional `--output FILE`: also write the JSON report to a file.
- Optional environment variables: `DIFFSENTINEL_EXPECTATIONS`, `DIFFSENTINEL_OUTPUT`, and `DIFFSENTINEL_SCORE_THRESHOLD`.

Supported expectation keys:

```yaml
required_files:
  - report.md
created_files:
  - report.md
deleted_files:
  - draft.txt
modified_files:
  - data.json
forbidden_changes:
  - notes.md
content_contains:
  report.md:
    - "Citation: [source:A]"
content_not_contains:
  report.md:
    - "uncited claim"
task_log:
  file: logs/task.log
  required_strings:
    - "updated report.md"
json_assertions:
  data.json:
    - path: status
      before_equals: draft
      equals: complete
    - path: citations.0
      added: true
      equals: "source:A"
```

JSON path assertions support dot paths and numeric list indexes, such as `citations.0`. Each JSON assertion may use `exists`, `equals`, `not_equals`, `before_equals`, `added`, and `removed`.

Exact output shape:

```json
{
  "pass": true,
  "score": 1.0,
  "earned_points": 1,
  "max_score": 1,
  "summary": {
    "passed": 1,
    "failed": 0,
    "warnings": 0
  },
  "checks": [
    {
      "id": "required_files:report.md",
      "kind": "required_files",
      "target": "report.md",
      "status": "pass",
      "detail": "File exists in after snapshot."
    }
  ],
  "warnings": [],
  "metadata": {
    "schema_version": "1.0",
    "threshold": 1.0,
    "created_count": 1,
    "deleted_count": 0,
    "modified_count": 0,
    "unchanged_count": 0
  }
}
```

## Installation

Copy this skill directory into a Claude Code or OpenClaw-compatible skills directory. No third-party packages are required.

```bash
python3 scripts/run.py --help
python3 scripts/test.py
```

## Usage

Run the built-in self-test:

```bash
python3 scripts/run.py --selftest
```

Run against the bundled example:

```bash
python3 scripts/run.py \
  --before examples/before \
  --after examples/after \
  --expect examples/expectations.yaml
```

Write a report file:

```bash
python3 scripts/run.py \
  --before examples/before \
  --after examples/after \
  --expect examples/expectations.yaml \
  --output report.json
```

Set a non-perfect pass threshold:

```bash
DIFFSENTINEL_SCORE_THRESHOLD=0.8 python3 scripts/run.py \
  --before examples/before \
  --after examples/after \
  --expect examples/expectations.yaml
```

Show CLI help:

```bash
python3 scripts/run.py --help
```

## Example

Command:

```bash
python3 scripts/run.py --before examples/before --after examples/after --expect examples/expectations.yaml
```

Expected output is the JSON report in `examples/expected-output.json`. It passes with score `1.0`, thirteen passing checks, zero warnings, and exit code `0`.

## Limitations

- The YAML reader supports a small, practical subset: mappings, lists, quoted strings, booleans, numbers, and null values.
- Binary files are compared by hash only; content assertions read files as UTF-8 with replacement characters.
- JSON path support is intentionally small and only handles dot-separated object keys and numeric list indexes.
- This reference script does not prove semantic correctness beyond the explicit expectations supplied.

## Verification
Automated execution check: **passed ✅**.

- Steps: structure=ok · syntax=ok · help=ok · selftest=ok · test=ok
- Commands and outputs shown in `README.md` are captured from these real runs.
