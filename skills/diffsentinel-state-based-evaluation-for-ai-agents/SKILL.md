---
name: diffsentinel-state-based-evaluation-for-ai-agents
description: Evaluates AI agent workspace state diffs and JSONL tool traces for files, links, policy boundaries, and evidence; use for DiffSentinel, state-based evaluation, agent audits, CI regression checks, workspace diff grading, and tool-trace review.
version: 0.1.0
license: MIT
---

# DiffSentinel — State-Based Evaluation for AI Agents

Auto-generated and experimental.

## Overview

DiffSentinel evaluates what an AI agent actually changed in a workspace instead of only scoring the final response. It compares a before snapshot, an after snapshot, and a JSONL tool trace to produce a deterministic JSON report covering file changes, link graph changes, policy violations, and supporting evidence.

This is useful when an agent works in repositories, documentation systems, knowledge bases, or structured workspaces where a polished summary can hide missing edits, unsafe access, broken references, or weak evidence.

## When to use

- Use when evaluating AI agents that create, modify, delete, or preserve files in a real workspace.
- Use when reviewing JSONL tool traces for file reads, writes, shell commands, external access, or missing approvals.
- Use when checking documentation or knowledge-base changes for added links, removed links, unresolved references, or orphaned markdown nodes.
- Use when building CI, benchmark, regression, or human-review workflows around observable workspace state.
- Use when trigger keywords appear: DiffSentinel, state-based evaluation, workspace diff grading, agent audit, tool-trace review, policy boundary check, graph integrity check.
- When NOT to use: do not use this when the only artifact to evaluate is a conversational answer with no workspace state or tool trace.

## Workflow

1. Capture or prepare a before snapshot and an after snapshot. Each snapshot may be a JSON file using the input contract below, or a directory to scan recursively.
2. Export the agent tool trace as JSONL, one JSON object per line. Include action, tool, path or paths, command, approval, and external-access fields when available.
3. Optionally create a config JSON file with required changes, required links, protected paths, forbidden path patterns, and score threshold.
4. Run `python scripts/run.py --before BEFORE --after AFTER --trace TRACE --pretty`.
5. Review `summary.status`, `summary.overall_score`, `violations`, and `findings`.
6. Use the structured report in CI, dashboards, benchmark harnesses, or manual review.

## Inputs & Outputs

Input contract:

- `--before`: path to a snapshot JSON file or a directory.
- `--after`: path to a snapshot JSON file or a directory.
- `--trace`: path to a JSONL tool trace.
- `--config`: optional JSON config file.
- `DIFFSENTINEL_FORBIDDEN_PATHS`: optional comma-separated forbidden path patterns.
- `DIFFSENTINEL_FAIL_BELOW_SCORE`: optional integer score threshold.
- `DIFFSENTINEL_ALLOW_SHELL_WITHOUT_APPROVAL`: optional boolean (`true` or `false`).

Snapshot JSON format:

```json
{
  "files": {
    "docs/index.md": {
      "content": "# Index\nSee [Guide](guide.md).\n"
    }
  }
}
```

The `files` value may also map paths directly to content strings.

Trace JSONL event shape:

```jsonl
{"tool":"read_file","action":"read","path":"docs/index.md"}
{"tool":"write_file","action":"write","path":"docs/guide.md","requires_approval":false}
```

Exact output shape:

```json
{
  "schema_version": "diffsentinel-report-v1",
  "summary": {
    "status": "pass",
    "overall_score": 100,
    "state_score": 100,
    "trace_score": 100,
    "graph_score": 100,
    "counts": {}
  },
  "state_diff": {
    "created": [],
    "modified": [],
    "deleted": [],
    "renamed": [],
    "unchanged": []
  },
  "trace": {
    "events": 0,
    "tools": {},
    "actions": {},
    "paths_accessed": [],
    "external_accesses": [],
    "shell_commands": []
  },
  "graph": {
    "added_links": [],
    "removed_links": [],
    "unresolved_references": [],
    "orphaned_nodes": []
  },
  "violations": [],
  "findings": [],
  "evidence": {
    "changed_paths": [],
    "policy": {}
  }
}
```

## Installation

Copy this directory into your Claude Code or OpenClaw-style skills directory, then run the scripts from the skill root.

No third-party packages are required.

## Usage

```bash
python scripts/run.py --help
python scripts/run.py --selftest
python scripts/run.py --before examples/before_snapshot.json --after examples/after_snapshot.json --trace examples/tool_trace.jsonl --pretty
python scripts/run.py --before examples/before_snapshot.json --after examples/after_snapshot.json --trace examples/tool_trace.jsonl --output report.json
python scripts/test.py
```

Optional environment configuration:

```bash
DIFFSENTINEL_FORBIDDEN_PATHS="../,.env,secrets/" python scripts/run.py --selftest
DIFFSENTINEL_FAIL_BELOW_SCORE=90 python scripts/run.py --selftest
DIFFSENTINEL_ALLOW_SHELL_WITHOUT_APPROVAL=false python scripts/run.py --selftest
```

## Example

```bash
python scripts/run.py --before examples/before_snapshot.json --after examples/after_snapshot.json --trace examples/tool_trace.jsonl --pretty
```

Expected output:

```json
{
  "schema_version": "diffsentinel-report-v1",
  "summary": {
    "counts": {
      "created": 1,
      "deleted": 0,
      "modified": 1,
      "renamed": 0,
      "unchanged": 1,
      "violations": 0
    },
    "graph_score": 100,
    "overall_score": 100,
    "state_score": 100,
    "status": "pass",
    "trace_score": 100
  }
}
```

The actual report also includes `state_diff`, `trace`, `graph`, `violations`, `findings`, and `evidence`.

## Limitations

- Rename detection is content-hash based, so renamed files that are also edited are reported as a deletion plus a creation.
- Link checks focus on markdown inline links and wikilinks; complex reference-style markdown links are not fully resolved.
- Tool-trace analysis depends on the fields present in the JSONL trace.
- Scoring is deterministic and rule-based, not a semantic judgment of task quality.

## Verification
Automated execution check: **passed ✅**.

- Steps: structure=ok · syntax=ok · help=ok · selftest=ok · test=ok
- Commands and outputs shown in `README.md` are captured from these real runs.
