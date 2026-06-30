# LedgerLens State-Change Evaluation for AI Agents

LedgerLens is a small installable skill with a runnable reference CLI for evaluating AI agent tool traces as auditable state-change ledgers.

## Install

Copy this folder into your Claude Code, OpenClaw, or compatible skills directory.

## Run

Use the built-in sample:

```bash
python scripts/run.py
```

Use the included example:

```bash
python scripts/run.py --trace examples/sample_trace.jsonl --spec examples/sample_task.yaml --out reports
```

The command writes:

```text
reports/ledgerlens_report.json
```

No third-party dependencies are required. `LEDGERLENS_API_KEY` is read if present, but the reference implementation runs fully offline.
