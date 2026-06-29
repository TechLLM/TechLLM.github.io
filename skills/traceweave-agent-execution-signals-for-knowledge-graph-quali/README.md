# TraceWeave Skill

TraceWeave is a local reference CLI for enriching Markdown knowledge graphs with agent execution signals. It parses notes, reads JSONL or plain-text logs, computes evidence metrics, and produces a reviewable report with backlink recommendations.

## Install

Copy this folder into your agent runtime's skills directory, then run the script from the skill root.

No dependencies are required beyond Python 3.9 or newer.

## Quick Start

Run the built-in sample:

```bash
python scripts/run.py
```

Run against the included examples:

```bash
python scripts/run.py --notes examples/notes --logs examples/logs --out traceweave-report.md
```

Preview metadata sidecars:

```bash
python scripts/run.py --notes examples/notes --logs examples/logs --metadata-dir .traceweave --diff
```

Write metadata sidecars:

```bash
python scripts/run.py --notes examples/notes --logs examples/logs --metadata-dir .traceweave --write-sidecar
```

## Outputs

The report includes per-note `last_seen`, `run_count`, `success_count`, `failure_count`, `resume_points`, and `quality_score` values. It also lists unresolved references and candidate backlinks inferred from repeated co-occurrence in execution logs.

The optional `TRACEWEAVE_API_KEY` environment variable is read safely but not used for network calls in this self-contained implementation.
