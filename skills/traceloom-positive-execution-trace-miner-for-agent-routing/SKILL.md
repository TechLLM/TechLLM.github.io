---
name: traceloom-positive-execution-trace-miner-for-agent-routing
description: TraceLoom mines verified successful LLM agent execution traces into positive routing datasets; use for triggers like traceloom, positive trace mining, agent routing data, verifier logs, JSONL traces, and prompt selector training.
version: 0.1.0
license: MIT
---

# TraceLoom - Positive Execution Trace Miner for Agent Routing

Auto-generated and experimental; review outputs before using them for production training or policy updates.

## Overview

TraceLoom helps convert successful LLM agent executions into clean, reusable training records for routing and prompt-selection workflows. It ingests execution trace JSONL plus verifier or grader JSON, keeps only verified successful runs, and emits positive examples with tool order, normalized tool names, argument summaries, file usage patterns, retrieval paths, and success conditions.

The included reference CLI is intentionally small and self-contained. It avoids raw prompt or file-content export by summarizing text-heavy fields and preserving routing-relevant structure.

## When to use

- Use when a team has agent execution logs and grader results and wants positive-only datasets for routers, prompt selectors, policy heuristics, retrieval planners, or evaluation workflows.
- Use when the user mentions TraceLoom, positive trace mining, successful rollout mining, verifier logs, execution trace JSONL, agent routing data, routing corpus, tool sequence extraction, or prompt selector training.
- Use when successful traces should be exported to JSONL or CSV without copying sensitive prompts, private file contents, or internal raw context.
- Use when the user wants a deterministic local CLI that can run without API keys or network access.
- When NOT to use: do not use this skill to mine negative examples, label failure taxonomies, assign penalties to failed tool calls, or expose raw private trace contents.

## Workflow

1. Collect execution trace events as JSONL. Each line should include at least `task_id`, `run_id`, `event`, and event-specific fields such as `tool`, `args`, `source`, or `step`.
2. Collect grader or verifier results as JSON. Use either a list, a mapping keyed by task id, or an object containing a `results` list. Each result should include `task_id`, optionally `run_id`, and pass evidence such as `passed`, `status`, or `score`.
3. Run the TraceLoom CLI with both files and choose `jsonl` or `csv` output.
4. Inspect the mined records. Confirm that only successful runs are present and that argument summaries contain no raw sensitive prompts or file contents.
5. Feed the exported positive corpus into downstream router training, prompt selection analysis, policy heuristic tuning, or evaluation dashboards.
6. Re-run the CLI whenever new verified successful traces are available, keeping the same input schema for deterministic output.

## Inputs & Outputs

Input contract:

- Trace file: newline-delimited JSON, one event per line.
- Required trace fields: `task_id` and `run_id`.
- Common trace fields: `event`, `step`, `tool`, `args`, `source`, `query`, `path`, `paths`.
- Grader file: JSON list, JSON object with `results`, or mapping from task id to result object.
- Required grader field: `task_id` unless the result is provided inside a task-id mapping.
- Success fields: `passed: true`, `status: "passed"` or `"success"`, or `score` greater than or equal to `--min-score`.

Exact JSONL output shape:

```json
{
  "task_id": "string",
  "run_id": "string",
  "success_condition": "string",
  "tool_sequence": ["normalized.tool.name"],
  "tool_calls": [
    {
      "order": 1,
      "tool": "normalized.tool.name",
      "argument_summary": {}
    }
  ],
  "file_patterns": {
    "read": ["relative/path.ext"],
    "write": ["relative/path.ext"],
    "touched": ["relative/path.ext"]
  },
  "retrieval_paths": [
    {
      "order": 1,
      "source": "relative/source.md",
      "query_summary": {
        "chars": 26,
        "words": 3
      }
    }
  ],
  "routing_signals": {
    "tool_count": 4,
    "retrieval_count": 1,
    "file_count": 1,
    "normalized_tool_path": "file.read>search.query>file.write>test.run"
  }
}
```

CSV output uses these columns: `task_id`, `run_id`, `success_condition`, `tool_sequence`, `files_read`, `files_written`, `retrieval_sources`, `routing_signals_json`.

## Installation

Copy or install this skill folder into a Claude Code or OpenClaw-compatible skills directory. No third-party Python packages are required.

```bash
python3 --version
python3 scripts/run.py --help
python3 scripts/test.py
```

## Usage

Run the built-in self-test sample:

```bash
python3 scripts/run.py --selftest
```

Run on example files:

```bash
python3 scripts/run.py --traces examples/traces.jsonl --graders examples/graders.json --format jsonl
python3 scripts/run.py --traces examples/traces.jsonl --graders examples/graders.json --format csv
python3 scripts/run.py --traces examples/traces.jsonl --graders examples/graders.json --format jsonl --output mined.jsonl
python3 scripts/run.py --help
```

Optional environment variables:

```bash
TRACELOOM_MIN_SCORE=0.95 python3 scripts/run.py --traces examples/traces.jsonl --graders examples/graders.json
TRACELOOM_OUTPUT_FORMAT=csv python3 scripts/run.py --traces examples/traces.jsonl --graders examples/graders.json
```

## Example

Command:

```bash
python3 scripts/run.py --traces examples/traces.jsonl --graders examples/graders.json --format jsonl
```

Expected output:

```jsonl
{"task_id":"task-alpha","run_id":"run-001","success_condition":"passed=true; score=1.0","tool_sequence":["file.read","search.query","file.write","test.run"],"tool_calls":[{"order":2,"tool":"file.read","argument_summary":{"path":"src/router.py"}},{"order":3,"tool":"search.query","argument_summary":{"query":{"chars":23,"words":3},"top_k":3}},{"order":4,"tool":"file.write","argument_summary":{"content":{"redacted":true,"chars":30},"path":"src/router.py"}},{"order":5,"tool":"test.run","argument_summary":{"command":{"program":"python","arg_count":3,"chars":37}}}],"file_patterns":{"read":["src/router.py"],"write":["src/router.py"],"touched":["src/router.py"]},"retrieval_paths":[{"order":1,"source":"docs/router-policy.md","query_summary":{"chars":26,"words":3}}],"routing_signals":{"tool_count":4,"retrieval_count":1,"file_count":1,"normalized_tool_path":"file.read>search.query>file.write>test.run"}}
```

## Limitations

- TraceLoom mines positive examples only; it does not explain why failed runs failed.
- The reference parser supports common JSONL trace shapes but may need adapters for highly custom logging schemas.
- Argument summaries are conservative and may omit useful semantic detail to avoid leaking raw prompts or file contents.
- The CLI is deterministic and local, but downstream training quality still depends on verifier quality and trace consistency.

## Verification
Automated execution check: **passed ✅**.

- Steps: structure=ok · syntax=ok · help=ok · selftest=ok · test=ok
- Commands and outputs shown in `README.md` are captured from these real runs.
