---
name: statelens-transition-aware-agent-evaluation
description: Evaluates LLM agent workflows by comparing before and after state transitions, evidence access, and mutation rules; use for StateLens, transition-aware evaluation, agent evaluation, RAG, code edits, note editing, CI regression checks.
license: MIT
---

# StateLens - Transition-Aware Agent Evaluation
Auto-generated and experimental reference skill for evaluating agent state transitions.

## Overview
StateLens evaluates agent work by inspecting the state an agent actually changed, not just the final answer it wrote. It compares a pre-task directory, a post-task directory, and an expectation spec to verify required edits, forbidden mutations, evidence access, and structured assertions.

The bundled CLI is intentionally small and deterministic so it can be run in local development, CI, or regression suites for file-based agent workflows.

## When to use
- Use for mixed read/write agent workflows where correctness depends on changed files, records, notes, or generated artifacts.
- Use for RAG, note editing, code-modifying assistants, skill runners, and service orchestration agents.
- Use when you need machine-readable pass/fail reports for CI or regression tests.
- Use when you need to catch scope creep, deleted files, missing evidence reads, or fluent but incorrect final responses.
- When NOT to use: do not use this for purely conversational tasks where there is no inspectable state transition.

## Workflow
1. Save the original workspace or fixture as a `before` directory.
2. Run the agent under test and save the resulting workspace or fixture as an `after` directory.
3. Write an expectation spec in JSON or simple YAML that declares required paths, required strings or regexes, structured JSON assertions, forbidden changes, required evidence files, and allowed changed files.
4. Save an optional trace file containing read/write events from the agent run.
5. Run `python scripts/run.py --before BEFORE --after AFTER --spec SPEC --trace TRACE`.
6. Inspect the JSON report. Treat `"pass": true` as the CI success condition and use `checks` plus `diffs` to debug failures.
7. Add the command to a regression suite once the expectation spec describes the intended task boundary.

## Inputs & Outputs
Input contract:
- `--before`: directory containing the pre-task state.
- `--after`: directory containing the post-task state.
- `--spec`: JSON or simple YAML expectation spec.
- `--trace`: optional JSON or text trace of agent file access events.
- `--output`: optional file path for the JSON report.

Supported spec fields:
- `task_id`: optional string used in the report.
- `required_paths_exist`: list of relative paths that must exist after the run.
- `required_changes`: list of objects with `path`, optional `contains`, and optional `regex`.
- `structured_assertions`: list of JSON assertions with `path`, `type: json`, optional `exists`, and optional `equals`.
- `forbidden_changes`: list of relative paths that must remain byte-identical.
- `forbidden_deletions`: list of relative paths that must not be deleted.
- `evidence_required`: list of relative paths that must appear as read/open/inspect events in the trace.
- `allowed_changes`: list of relative paths allowed to be added, modified, or deleted.
- `allow_unlisted_changes`: boolean. Set to `false` to fail on scope creep outside `allowed_changes` and `required_changes`.

Exact output shape:

```json
{
  "task_id": "string",
  "pass": true,
  "summary": {
    "confidence": "high|medium|low",
    "checks_passed": 0,
    "checks_failed": 0,
    "files_added": 0,
    "files_deleted": 0,
    "files_modified": 0,
    "unexpected_changes": 0
  },
  "checks": [
    {
      "name": "string",
      "pass": true,
      "path": "relative/path",
      "field": "optional.field",
      "details": "string"
    }
  ],
  "diffs": {
    "added": ["relative/path"],
    "deleted": ["relative/path"],
    "modified": ["relative/path"],
    "file_diffs": [
      {
        "path": "relative/path",
        "binary": false,
        "diff": "unified diff text"
      }
    ]
  }
}
```

## Installation
Copy this skill directory into your Claude Code, OpenClaw, or compatible skills folder.

No package install is required because the reference CLI uses only the Python standard library.

## Usage
Run the help command:

```bash
python scripts/run.py --help
```

Run the built-in deterministic self-test:

```bash
python scripts/run.py --selftest
```

Run the example fixture:

```bash
python scripts/run.py --before examples/before --after examples/after --spec examples/spec.yaml --trace examples/trace.json
```

Run the Python self-test:

```bash
python scripts/test.py
```

If your system exposes Python as `python3` instead of `python`, use `python3` in the same commands.

Use environment defaults when desired:

```bash
STATELENS_SPEC=examples/spec.yaml STATELENS_TRACE=examples/trace.json python scripts/run.py --before examples/before --after examples/after
```

## Example
Command:

```bash
python scripts/run.py --before examples/before --after examples/after --spec examples/spec.yaml --trace examples/trace.json
```

Expected output is a JSON report with `"pass": true`, `"confidence": "high"`, ten passing checks, two modified files, and no unexpected changes. The full expected report is stored in `examples/expected-output.json`.

## Limitations
- Directory comparison is file-based and does not inspect databases, network calls, or external services.
- YAML support intentionally covers a small, common subset: maps, lists, strings, numbers, booleans, and nulls. Quote YAML list strings that contain colons.
- Structured assertions currently support JSON files only.
- Evidence validation depends on the trace file supplied by the agent harness.
- Large or binary files are hashed and compared, but text diffs are only emitted for UTF-8 text files.
