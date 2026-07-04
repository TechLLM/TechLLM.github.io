---
name: traceloom-failure-recovery-knowledge-graph-extractor
description: Extracts compact failure-recovery knowledge graph candidates from agent logs, shell history, and JSONL traces; use when trigger keywords include TraceLoom, failure recovery, recovery command, resume point, agent trace, log to knowledge graph, Obsidian note, or graph edges.
license: MIT
---

# TraceLoom - Failure-Recovery Knowledge Graph Extractor
Auto-generated and experimental: review outputs before using them as operational memory.

## Overview
TraceLoom turns noisy execution traces into compact recovery memory. It scans agent logs, shell history, or JSONL records for failures, likely causes, repair commands, resume points, and outcomes, then emits Markdown notes and JSON graph candidates that can be indexed or reviewed.

The bundled reference CLI is intentionally small and deterministic. It uses rule-based extraction by default and only reads optional environment keys so wrappers can add external summarization without hardcoding secrets.

## When to use
- Use when a user asks to convert failed agent runs, automation logs, shell history, or JSONL traces into reusable recovery notes.
- Use when the prompt mentions TraceLoom, failure recovery, recovery command, resume point, operational memory, Obsidian notes, wikilinks, knowledge graph extraction, or graph edges.
- Use when repeated tool or command failures need deduplicated signatures and compact procedural memory.
- Use when an assistant needs a local, no-network baseline before adding optional LLM summarization.
- When NOT to use: do not use for general log archiving, security incident response, or forensic analysis where every raw event must be preserved exactly.

## Workflow
1. Collect one trace file in plain text, shell-history style, or JSONL form.
2. Run `python scripts/run.py --input <trace-file> --format json` to extract structured candidates.
3. Review `failures`, `nodes`, `edges`, and `wikilinks` for false positives before importing them into a long-term memory store.
4. Run `python scripts/run.py --input <trace-file> --format markdown --output <note.md>` to create an Obsidian-ready recovery note.
5. Deduplicate across runs by comparing `error_signature`, `likely_cause`, and command node fingerprints.
6. Optionally set `TRACELOOM_LLM_API_KEY` or `OPENAI_API_KEY` for external wrappers; the bundled script reads these variables but never sends data over the network.
7. Verify local behavior with `python scripts/run.py --selftest` and `python scripts/test.py` before publishing changes to the skill.

## Inputs & Outputs
Input contract:
- `--input PATH` accepts UTF-8 plain text logs, shell history, or JSONL with fields such as `event`, `type`, `level`, `message`, `error`, `command`, `cmd`, `stdout`, `stderr`, `status`, or `exit_code`.
- No arguments or `--selftest` uses built-in sample data and requires no API key.
- `--format json` writes structured graph candidates; `--format markdown` writes only the recovery note.
- `--output PATH` writes the selected output to a file; otherwise output goes to stdout.

Exact JSON output shape:

```json
{
  "trace_id": "trace-<12 hex chars>",
  "source": "<input label>",
  "summary": "<compact recovery summary>",
  "failures": [
    {
      "id": "failure-<10 hex chars>",
      "error_signature": "<normalized failure signature>",
      "likely_cause": "<cause category>",
      "failed_command": "<command or null>",
      "recovery_command": "<command or null>",
      "resume_point": "<command/checkpoint or null>",
      "outcome": "recovered|unresolved",
      "evidence": ["<short sanitized trace line>"]
    }
  ],
  "wikilinks": ["[[TraceLoom]]", "[[failure recovery]]"],
  "nodes": [
    {
      "id": "<stable node id>",
      "type": "artifact|failure|cause|command|checkpoint|outcome",
      "label": "<human label>",
      "properties": {}
    }
  ],
  "edges": [
    {
      "source": "<source node id>",
      "target": "<target node id>",
      "type": "CONTAINS|HAS_CAUSE|FAILED_WITH|RECOVERED_FROM|RESUMED_AT|ENDED_AS",
      "properties": {}
    }
  ],
  "markdown": "<Obsidian-ready note with frontmatter>"
}
```

Markdown output shape:
- YAML frontmatter with `trace_id`, `source`, `failure_count`, `outcome`, and tags.
- `# TraceLoom Recovery Note`
- `## Recovery Summary`
- `## Wikilink Candidates`
- `## Graph Edges`
- `## Evidence`

## Installation
Copy or install this folder as a skill directory in any Claude Code or OpenClaw-style skills location. The reference script uses only the Python standard library.

```bash
python --version
python scripts/run.py --help
python scripts/run.py --selftest
python scripts/test.py
```

## Usage
Print help:

```bash
python scripts/run.py --help
```

Run the built-in sample:

```bash
python scripts/run.py --selftest
```

Extract JSON graph candidates from a trace:

```bash
python scripts/run.py --input examples/sample-trace.txt --format json
```

Write an Obsidian-ready note:

```bash
python scripts/run.py --input examples/sample-trace.txt --format markdown --output examples/recovery-note.md
```

Process JSONL:

```bash
python scripts/run.py --input examples/sample-trace.jsonl --format json
```

## Example
Input:

```text
[10:00] RUN $ python worker.py
[10:00] ERROR ModuleNotFoundError: No module named 'yaml'
[10:01] $ python -m pip install pyyaml
[10:02] CHECKPOINT resume from step parse-config
[10:02] $ python worker.py
[10:03] SUCCESS completed job
```

Expected compact JSON fields:

```json
{
  "summary": "Recovered 1 of 1 detected failure(s). Main pattern: missing_dependency repaired with python -m pip install pyyaml.",
  "failures": [
    {
      "error_signature": "ModuleNotFoundError: No module named 'yaml'",
      "likely_cause": "missing_dependency",
      "failed_command": "python worker.py",
      "recovery_command": "python -m pip install pyyaml",
      "resume_point": "python worker.py",
      "outcome": "recovered"
    }
  ]
}
```

See `examples/sample-trace.txt`, `examples/sample-trace.jsonl`, and `examples/expected-output.json` for runnable fixtures.

## Limitations
- The extractor is rule-based and intentionally conservative; ambiguous logs may need manual review.
- It does not call external LLMs, databases, or private services.
- It sanitizes obvious absolute paths, but users should still review outputs before sharing logs.
- It is designed for compact recovery memory, not full-fidelity log preservation.
