# Failwise - Worst-Case Token Budget Tuning for LLM Agents

Failwise is a minimal installable skill with a runnable reference CLI for comparing LLM agent budget policies against historical execution logs.

## Install

Copy this directory into a Claude Code, OpenClaw, or compatible skills directory.

No third-party dependencies are required:

```bash
python scripts/run.py
```

## Use

Run the built-in demo:

```bash
python scripts/run.py
```

Run with included examples:

```bash
python scripts/run.py --logs examples/sample_logs.jsonl --policies examples/policies.yaml
```

Export JSON:

```bash
python scripts/run.py --logs examples/sample_logs.jsonl --policies examples/policies.yaml --output failwise-report.json
```

## Input Shape

Logs are JSONL records. Useful fields include `success`, `tokens_used`, `retrieval_depth_used`, `tool_retries_used`, `latency_ms`, `input_tokens`, `output_tokens`, `retrieval_confidence`, `task_type`, `tool_name`, `model`, and `metadata`.

Policies are YAML or JSON records with `name`, `max_tokens`, `retrieval_depth`, `tool_retries`, and optional `token_cost_per_1k` and `latency_penalty_ms`.

See `examples/` for runnable sample files.
