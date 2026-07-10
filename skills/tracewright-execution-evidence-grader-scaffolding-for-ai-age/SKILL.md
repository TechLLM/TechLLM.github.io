---
name: tracewright-execution-evidence-grader-scaffolding-for-ai-age
description: Generates deterministic execution-evidence grader scaffolds for AI agents when you need Tracewright, execution evidence, agent evaluation, audit trails, tool traces, diff checks, or CI grading.
version: 0.1.0
license: MIT
---

# Tracewright - Execution-Evidence Grader Scaffolding for AI Agents

Auto-generated and experimental reference skill for installable Claude Code / OpenClaw-style workflows.

## Overview

Tracewright addresses a common agent-evaluation gap: final answers can look plausible even when the agent skipped required evidence, touched forbidden files, or left no audit trail. This skill provides a small, working CLI that grades deterministic execution artifacts such as workspace files, JSONL tool traces, unified diffs, final output text, and audit logs. It can also scaffold a standalone Python grader plus pass/fail fixtures from a compact JSON or simple YAML specification.

## When to use

- Use when grading LLM or agent workflows by execution evidence instead of final text alone.
- Use when you need CI-friendly checks for required files, forbidden files, expected edits, forbidden edits, trace events, diff patterns, final output, and audit logs.
- Use when trigger keywords appear: Tracewright, execution evidence, agent evaluation, audit trail, tool trace, diff check, grader scaffold, benchmark grader, regression grader.
- Use when a maintainer wants a starter grader that can be adapted without building a custom evaluator from scratch.
- When NOT to use: do not use this when subjective product-quality judgment is the only signal and there are no files, traces, diffs, logs, or output artifacts to inspect.

## Workflow

1. Write a JSON or simple YAML task specification that names required files, forbidden files, expected edits, forbidden edits, trace requirements, diff regexes, output assertions, and audit-log assertions.
2. Collect artifacts from an agent run: the final workspace directory, JSONL trace, unified diff, final output text, and audit log.
3. Run `python scripts/run.py --spec ...` with the artifact paths to produce a deterministic JSON grade report.
4. Inspect failed checks and revise the agent workflow, task spec, or artifacts.
5. Optionally run `python scripts/run.py --spec ... --scaffold --out ...` to generate a standalone grader and sample pass/fail fixtures for CI, benchmark suites, or a local harness.
6. Run `python scripts/test.py` before publishing local modifications to confirm the reference implementation still works.

## Inputs & Outputs

Input contract:

- `spec`: JSON or simple YAML object with optional fields `task_id`, `required_files`, `forbidden_files`, `expected_edits`, `forbidden_edits`, `trace`, `diff`, `output`, and `audit`.
- `workspace`: directory containing the post-run file state.
- `trace`: JSONL file where each line is one tool event object.
- `diff`: unified diff text file.
- `output`: final answer or task output text file.
- `audit`: audit log text file.
- Environment variables: `TRACEWRIGHT_SPEC` may provide a default spec path, and `TRACEWRIGHT_OUTPUT_FORMAT=json` may provide the output format.

Exact output shape:

```json
{
  "task_id": "string",
  "passed": true,
  "score": 1.0,
  "summary": {
    "passed": 0,
    "failed": 0,
    "total": 0
  },
  "checks": [
    {
      "id": "category.check:target",
      "category": "files|diff|trace|output|audit",
      "passed": true,
      "message": "human-readable check result"
    }
  ]
}
```

## Installation

Copy or install this skill directory into a Claude Code / OpenClaw-compatible skills location. No third-party Python packages are required.

```bash
python --version
python scripts/run.py --help
python scripts/test.py
```

## Usage

Run the built-in self-test data:

```bash
python scripts/run.py --selftest
```

Grade the included example artifacts:

```bash
python scripts/run.py --spec examples/task_spec.json --workspace examples/pass/workspace --trace examples/pass/trace.jsonl --diff examples/pass/diff.patch --output examples/pass/output.txt --audit examples/pass/audit.log
```

Scaffold a standalone grader:

```bash
python scripts/run.py --spec examples/task_spec.json --scaffold --out generated/tracewright-sample
python generated/tracewright-sample/grader.py --workspace generated/tracewright-sample/fixtures/pass/workspace --trace generated/tracewright-sample/fixtures/pass/trace.jsonl --diff generated/tracewright-sample/fixtures/pass/diff.patch --output generated/tracewright-sample/fixtures/pass/output.txt --audit generated/tracewright-sample/fixtures/pass/audit.log
```

Use an environment-provided spec:

```bash
TRACEWRIGHT_SPEC=examples/task_spec.json python scripts/run.py --workspace examples/pass/workspace --trace examples/pass/trace.jsonl --diff examples/pass/diff.patch --output examples/pass/output.txt --audit examples/pass/audit.log
```

## Example

Command:

```bash
python scripts/run.py --selftest
```

Expected output:

```json
{
  "task_id": "sample-agent-edit",
  "passed": true,
  "score": 1.0,
  "summary": {
    "passed": 13,
    "failed": 0,
    "total": 13
  },
  "checks": [
    {
      "id": "file.required:src/feature.py",
      "category": "files",
      "passed": true,
      "message": "Required file exists: src/feature.py"
    }
  ]
}
```

The full expected example output is stored in `examples/expected_output.json`.

## Limitations

- YAML support intentionally covers a small, common subset; use JSON for complex specs.
- Regex-to-fixture generation is heuristic for scaffolded sample fixtures, although grading itself uses normal Python regular expressions.
- Semantic placeholders are deterministic keyword checks, not model-based semantic judging.
- Binary workspace files are treated as present but their text content is not inspected.
- This reference CLI is a scaffold for local and CI evaluation, not a hosted service.

## Verification
Automated execution check: **passed ✅**.

- Steps: structure=ok · syntax=ok · help=ok · selftest=ok · test=ok
- Commands and outputs shown in `README.md` are captured from these real runs.
