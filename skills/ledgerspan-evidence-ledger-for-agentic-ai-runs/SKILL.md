---
name: ledgerspan-evidence-ledger-for-agentic-ai-runs
description: Builds a durable evidence ledger for agentic AI runs; use when you need LedgerSpan, evidence ledger, agent benchmark, tool trace, workspace diff, artifact hash, or verification checklist outputs.
version: 0.1.0
license: MIT
---

# LedgerSpan — Evidence Ledger for Agentic AI Runs
Auto-generated and experimental.

## Overview
Agent runs can produce fluent final answers while leaving the workspace unchanged, touching the wrong files, or skipping promised verification. LedgerSpan creates a compact evidence package from observable side effects: before/after file snapshots, command logs, JSON tool traces, artifact hashes, and checklist results.

The bundled CLI is intentionally small and self-contained. It can run on deterministic fixture data, snapshot real directories, or combine supplied JSON inputs into Markdown or JSON output for review, CI storage, or custom grading.

## When to use
- Use when evaluating an AI agent, LLM tool, autonomous workflow, or workspace copilot by the files and resources it actually touched.
- Use when benchmark scoring needs evidence beyond final answer text, such as created files, modified files, deleted files, commands, tool calls, and artifact hashes.
- Use when documentation automation or developer tooling needs a portable JSON or Markdown run record.
- Use when you have command logs, JSONL tool traces, and a verification checklist that should be normalized into one evidence package.
- When NOT to use: do not use LedgerSpan as a security sandbox, policy engine, or proof that external systems behaved correctly when no observable trace was captured.

## Workflow
1. Capture or provide a pre-run snapshot with file paths, sizes, timestamps, and hashes.
2. Run the agent or workflow under the harness of your choice.
3. Capture or provide a post-run snapshot using the same <internal> path convention.
4. Export command logs as JSON or JSONL with command, exit code, duration, working directory, and stdout/stderr references.
5. Export tool calls as JSON or JSONL with kind, tool, action, resource, and status fields.
6. Write a checklist JSON file with required files, declared artifacts, and pass/fail assertions.
7. Run `python scripts/run.py` with the snapshots and optional traces to emit a JSON or Markdown ledger.
8. Review the ledger manually, attach it to a benchmark run, store it in CI, or pass it to a custom grader.

## Inputs & Outputs
Input paths must be relative to the workspace root inside snapshot and trace data.

Snapshot input:
```json
{
  "files": [
    {
      "path": "docs/evidence.md",
      "size": 31,
      "mtime": 1700000100,
      "sha256": "64 lowercase hex characters"
    }
  ]
}
```

Command log input:
```json
{"command":"python -m pytest","exit_code":0,"duration_ms":1240,"cwd":".","stdout_ref":"logs/pytest.stdout.txt","stderr_ref":"logs/pytest.stderr.txt"}
```

Tool trace input:
```json
{"id":"tool-001","kind":"search","tool":"local_search","action":"query","resource":"README.md","status":"ok"}
```

Checklist input:
```json
{
  "required_files": ["docs/evidence.md"],
  "artifacts": ["docs/evidence.md"],
  "assertions": [
    {"name":"tests passed","type":"command_exit_zero","command_contains":"pytest"}
  ]
}
```

Exact output shape:
```json
{
  "ledger_version": "0.1.0",
  "run": {"id": "string", "actor": "string", "source": "ledgerspan"},
  "workspace": {"before_file_count": 0, "after_file_count": 0},
  "changes": {
    "created": [],
    "modified": [],
    "deleted": [],
    "renamed": [],
    "unchanged_count": 0
  },
  "commands": {
    "summary": {"total": 0, "succeeded": 0, "failed": 0, "duration_ms": 0},
    "entries": []
  },
  "tool_calls": {
    "summary": {"total": 0, "by_kind": {}, "resources_touched": []},
    "entries": []
  },
  "artifacts": [],
  "verification": {
    "status": "pass",
    "passed": 0,
    "failed": 0,
    "checks": []
  }
}
```

Supported assertion types are `file_exists`, `file_created`, `file_modified`, `file_deleted`, `command_seen`, `command_exit_zero`, `tool_kind_seen`, and `artifact_hashed`.

## Installation
Copy or install this skill directory into your Claude Code or OpenClaw-compatible skills location. The reference CLI uses only Python standard library modules.

```bash
python --version
python scripts/run.py --help
python scripts/test.py
```

Optional metadata can be supplied with environment variables:

```bash
LEDGERSPAN_RUN_ID=run-042 LEDGERSPAN_ACTOR=agent-name python scripts/run.py --before examples/before_snapshot.json --after examples/after_snapshot.json
```

## Usage
Run the deterministic built-in sample:

```bash
python scripts/run.py --selftest
```

The no-argument path also runs the built-in sample:

```bash
python scripts/run.py
```

Generate an evidence ledger from example files:

```bash
python scripts/run.py \
  --before examples/before_snapshot.json \
  --after examples/after_snapshot.json \
  --commands examples/commands.jsonl \
  --tools examples/tool_trace.jsonl \
  --checklist examples/checklist.json \
  --format json
```

Generate Markdown:

```bash
python scripts/run.py \
  --before examples/before_snapshot.json \
  --after examples/after_snapshot.json \
  --commands examples/commands.jsonl \
  --tools examples/tool_trace.jsonl \
  --checklist examples/checklist.json \
  --format markdown
```

Snapshot a live directory:

```bash
python scripts/run.py --snapshot examples
```

Show CLI options:

```bash
python scripts/run.py --help
```

## Example
Command:

```bash
python scripts/run.py --selftest
```

Expected output begins with:

```json
{
  "ledger_version": "0.1.0",
  "run": {
    "id": "sample-run-001",
    "actor": "sample-agent",
    "source": "ledgerspan"
  },
  "workspace": {
    "before_file_count": 4,
    "after_file_count": 4
  }
}
```

The full expected JSON for the fixture command is in `examples/expected_output.json`.

## Limitations
- LedgerSpan records observable evidence only; it does not prove intent, correctness, or security by itself.
- Rename detection is hash-based and conservative.
- Live directory snapshots depend on filesystem metadata, so fixture snapshots are better for deterministic tests.
- Tool trace parsing supports a small normalized schema and simple inference for common fields.
- The reference CLI is a minimal implementation intended for extension, not a dedicated benchmark platform.

## Verification
Automated execution check: **passed ✅**.

- Steps: structure=ok · syntax=ok · help=fail · selftest=fail · test=ok
- Commands and outputs shown in `README.md` are captured from these real runs.
