---
name: traceshepherd-execution-evidence-grader-for-llm-agents
description: Local-first grader for LLM agent execution evidence; use for traceshepherd, execution evidence, agent trace JSONL, artifact verification, manifest checks, and CI evaluation.
version: 0.1.0
license: MIT
---

# TraceShepherd — Execution Evidence Grader for LLM Agents

Auto-generated and experimental; verify outputs before using them as a release gate.

## Overview

TraceShepherd grades LLM agent runs by inspecting observable side effects instead of only reading the final natural-language answer. It compares local trace JSONL events, workspace files, and a declared manifest of evidence rules to produce deterministic pass/fail JSON for audits, regression tests, and CI checks.

## When to use

- Use when an agent claims it searched, read, edited, wrote, linked, or created artifacts and you need to verify those claims from local evidence.
- Use for coding agents, research assistants, knowledge-base automation, benchmark harnesses, and workflow agents that leave files or event logs behind.
- Use when trigger keywords appear: `traceshepherd`, `execution evidence`, `agent trace`, `trace JSONL`, `evidence grader`, `artifact verification`, `manifest checks`.
- When NOT to use: do not use it to judge subjective answer quality when there are no trace logs, expected files, or auditable side effects.

## Workflow

1. Collect the agent run trace as JSONL, with one JSON object per event.
2. Write a manifest describing required events, allowed or forbidden paths, and expected output file checks.
3. Run `python scripts/run.py --trace <trace.jsonl> --manifest <manifest.yaml> --workspace <workspace>`.
4. Inspect the JSON report fields `status`, `summary`, `evidence`, `files`, `policy`, and `errors`.
5. Fail CI or the benchmark run when `status` is `fail`; use the reported missing events, failed file checks, or path policy violations to debug the agent.

## Inputs & Outputs

Input contract:

- `trace.jsonl`: newline-delimited JSON objects. Common fields are `type`, `tool`, `action`, `path`, `query`, and `message`; extra fields are allowed.
- `manifest.yaml` or `manifest.json`: local rule pack with a top-level `rules` object. The bundled CLI supports JSON and a small YAML subset with mappings, lists, booleans, numbers, and quoted strings.
- `workspace`: local directory whose files are checked against manifest rules.
- Optional environment variables: `TRACESHEPHERD_STRICT=1` treats load and validation errors as hard failures, and `TRACESHEPHERD_MAX_READ_BYTES` limits text read for content checks.

Manifest shape:

```yaml
version: 1
rules:
  required_events:
    - type: search
      pattern: project plan
    - type: write
      path: docs/agent-report.md
  allowed_paths:
    - docs/**
  forbidden_paths:
    - secrets/**
  files:
    - path: docs/agent-report.md
      must_exist: true
      min_size: 40
      contains:
        - TraceShepherd demo report
      regex:
        - "Result: docs updated\\."
```

Output shape:

```json
{
  "tool": "traceshepherd",
  "version": "0.1.0",
  "status": "pass",
  "summary": {
    "checks": 8,
    "passed": 8,
    "failed": 0
  },
  "evidence": {
    "required_events": [],
    "missing_events": []
  },
  "files": [],
  "policy": {
    "changed_paths": [],
    "unexpected_modified_files": [],
    "forbidden_modified_files": []
  },
  "errors": []
}
```

## Installation

Copy this folder into your local skills directory, then run the self-test:

```bash
python scripts/run.py --selftest
python scripts/test.py
```

No package installation is required; the reference implementation uses only the Python standard library.

## Usage

Show CLI options:

```bash
python scripts/run.py --help
```

Run the built-in sample:

```bash
python scripts/run.py --selftest
```

Grade the bundled example:

```bash
python scripts/run.py --trace examples/trace.jsonl --manifest examples/manifest.yaml --workspace examples/workspace
```

Write a report to a file:

```bash
python scripts/run.py --trace examples/trace.jsonl --manifest examples/manifest.yaml --workspace examples/workspace --output report.json
```

## Example

Command:

```bash
python scripts/run.py --trace examples/trace.jsonl --manifest examples/manifest.yaml --workspace examples/workspace
```

Expected output is deterministic JSON. The bundled complete version is in `examples/expected-output.json`; the key result is:

```json
{
  "status": "pass",
  "summary": {
    "checks": 10,
    "failed": 0,
    "passed": 10
  }
}
```

## Limitations

- The YAML reader is intentionally small and only supports the subset used by the examples; use JSON for complex manifests.
- The grader is rule-based and deterministic, so it does not infer semantic correctness beyond declared events, paths, hashes, sizes, and patterns.
- Content checks read text as UTF-8 with replacement for invalid bytes.
- The tool validates local evidence only; it does not call external APIs or verify remote service state.

## Verification
Automated execution check: **passed ✅**.

- Steps: structure=ok · syntax=ok · help=ok · selftest=ok · test=ok
- Commands and outputs shown in `README.md` are captured from these real runs.
