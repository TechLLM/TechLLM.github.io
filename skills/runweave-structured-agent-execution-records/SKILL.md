---
name: runweave-structured-agent-execution-records
description: Converts shell logs and lightweight YAML plans into structured agent_run_record.json files; use for RunWeave, shell log parsing, YAML execution plans, failed agent runs, retry candidates, replay, audit trails, and agent debugging.
license: MIT
---

# RunWeave - Structured Agent Execution Records
Auto-generated and experimental; review outputs before using them as audit evidence.

## Overview
Tool-using agents often leave behind terminal transcripts that are hard to replay, compare, or use in evaluations. RunWeave turns ordinary shell logs and lightweight YAML plans into a normalized `agent_run_record.json` that captures planned actions, executed commands, failures, retry candidates, and repair evidence. The bundled CLI is intentionally small and dependency-free so it can run inside agent workspaces without a GUI automation stack.

## When to use
- Use when a shell transcript needs to become a durable agent execution record.
- Use when comparing a lightweight YAML plan against the commands that actually ran.
- Use when debugging failed autonomous workflows, retries, repairs, or recovery evidence.
- Use when preparing run artifacts for replay, evaluation harnesses, incident review, or regression comparison.
- Use when trigger keywords appear: RunWeave, `agent_run_record.json`, shell log parsing, YAML plan, retry candidates, failed agent run, audit trail, replay, reproducibility.
- When NOT to use: do not use this for live GUI automation, interactive desktop control, or security-grade forensics.

## Workflow
1. Save the intended workflow as a lightweight YAML plan with a `steps` list containing `id`, `command`, and optional `expect` fields.
2. Save the terminal transcript as a plain text shell log. Prefix command lines with `$`, `>`, or `COMMAND:` when possible.
3. Run `python scripts/run.py --plan PLAN --log LOG --output agent_run_record.json`.
4. Inspect `summary.failed_steps`, `failures`, and `repair_candidates` in the generated JSON.
5. For long-running workflows, add `--append-run-log runs.jsonl` to preserve append-only records.
6. Feed the resulting JSON into a human review, replay script, comparison tool, or evaluation harness.

## Inputs & Outputs
Input contract:
- `--log`: optional plain text shell transcript. Commands are detected from `$ command`, `> command`, or `COMMAND: command` lines. Exit status is detected from lines such as `exit code: 1`, `status: 1`, or `[exit 1]`.
- `--plan`: optional lightweight YAML or JSON plan. YAML support is limited to top-level scalar keys and a `steps:` list of scalar fields.
- `RUNWEAVE_RUN_ID`: optional environment override for the output run id.
- `RUNWEAVE_GENERATED_AT`: optional environment override for the deterministic timestamp.
- `RUNWEAVE_FAILURE_PATTERNS`: optional comma-separated extra regex patterns used for failure detection.
- `RUNWEAVE_ENV_HINTS`: optional comma-separated environment hints copied into repair candidates.

Output shape:
```json
{
  "schema_version": "runweave.agent_run_record.v1",
  "run_id": "string",
  "generated_at": "string",
  "source": {"log": "string|null", "plan": "string|null"},
  "summary": {
    "planned_steps": 0,
    "executed_steps": 0,
    "matched_steps": 0,
    "failed_steps": 0,
    "missing_planned_steps": 0,
    "repair_candidates": 0
  },
  "planned_steps": [
    {
      "id": "string",
      "command": "string",
      "expect": "string",
      "status": "missing|completed|failed",
      "matched_executed_step_id": "string|null"
    }
  ],
  "executed_steps": [
    {
      "id": "string",
      "command": "string",
      "planned_step_id": "string|null",
      "exit_code": 0,
      "status": "completed|failed",
      "failure_signals": ["string"],
      "stdout_excerpt": ["string"],
      "stderr_excerpt": ["string"]
    }
  ],
  "timeline": [
    {"phase": "plan|execute|repair", "step_id": "string", "status": "string", "message": "string"}
  ],
  "failures": [
    {
      "executed_step_id": "string",
      "planned_step_id": "string|null",
      "command": "string",
      "exit_code": 1,
      "signals": ["string"],
      "stderr_excerpt": ["string"]
    }
  ],
  "repair_candidates": [
    {
      "id": "string",
      "failure_step_id": "string",
      "command_template": "string",
      "environment_hints": ["string"],
      "confidence": 0.55,
      "rationale": "string"
    }
  ],
  "environment_hints": ["string"]
}
```

## Installation
Copy this folder into a skill directory supported by your agent runtime, then run from the skill root:
```bash
python scripts/run.py --help
python scripts/test.py
```

No third-party dependencies are required.

## Usage
Create a record from a plan and log:
```bash
python scripts/run.py \
  --plan examples/sample_plan.yaml \
  --log examples/sample_log.txt \
  --output agent_run_record.json
```

Append the same record to an append-only JSONL run log:
```bash
python scripts/run.py \
  --plan examples/sample_plan.yaml \
  --log examples/sample_log.txt \
  --append-run-log runs.jsonl
```

Run the built-in deterministic sample:
```bash
python scripts/run.py --selftest
```

Show CLI help:
```bash
python scripts/run.py --help
```

## Example
Input plan:
```yaml
run_id: sample-run
objective: validate package
steps:
  - id: lint
    command: python -m py_compile scripts/run.py
    expect: success
  - id: test
    command: python scripts/test.py
    expect: success
```

Input log:
```text
$ python -m py_compile scripts/run.py
stdout: compiled scripts/run.py
exit code: 0
$ python scripts/test.py
stderr: AssertionError: missing field agent_run_record
exit code: 1
```

Expected output summary:
```json
{
  "schema_version": "runweave.agent_run_record.v1",
  "run_id": "sample-run",
  "summary": {
    "planned_steps": 2,
    "executed_steps": 2,
    "matched_steps": 2,
    "failed_steps": 1,
    "missing_planned_steps": 0,
    "repair_candidates": 1
  }
}
```

The full expected output is in `examples/expected_agent_run_record.json`.

## Limitations
- The YAML parser intentionally supports only a small, common subset.
- Failure detection is heuristic and should be reviewed before automated remediation.
- Repair candidates are templates, not guaranteed fixes.
- Timestamp output is deterministic by default and should be overridden with `RUNWEAVE_GENERATED_AT` or `--generated-at` when wall-clock time matters.
