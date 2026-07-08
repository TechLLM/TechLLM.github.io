# FailForge - SNS Failure Logs into Agent Evaluation Scenarios

FailForge is a small installable skill that turns social publishing failure logs into normalized failure reports and YAML evaluation scenarios for LLM agents.

## Install

Copy this directory into your Claude Code or OpenClaw compatible skills folder.

```bash
mkdir -p skills
cp -R failforge-sns-failure-logs-into-agent-evaluation-scenarios skills/
```

The included CLI has no third-party dependencies.

## Run

Use built-in sample logs:

```bash
python scripts/run.py
```

Parse the included example:

```bash
python scripts/run.py examples/social_publish_failures.log
```

Write outputs to files:

```bash
python scripts/run.py examples/social_publish_failures.log --output-dir out
```

This creates:

- `out/normalized_failures.json`
- `out/scenarios.yaml`

## Input formats

The parser accepts:

- JSON objects
- JSON arrays
- newline-delimited JSON
- plain-text log lines
- stdin

## Environment variables

No environment variables are required. If `FAILFORGE_SAMPLE_MODE=1` is set, the CLI uses built-in sample data even when stdin is present.
