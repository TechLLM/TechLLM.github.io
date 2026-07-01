# RouteHarbor

RouteHarbor is a minimal installable skill for evaluating LLM agent routers under group-level robustness checks.

## Install

Copy this directory into a Claude Code, OpenClaw, or Codex-style skills folder, or run it directly from this repository.

No dependencies are required beyond Python 3.

## Run

Built-in sample data:

```bash
python scripts/run.py
```

Example files:

```bash
python scripts/run.py \
  --queries examples/query_log.jsonl \
  --decisions examples/router_decisions.json \
  --output routeharbor-report.json
```

Custom group fields:

```bash
python scripts/run.py \
  --queries examples/query_log.jsonl \
  --decisions examples/router_decisions.json \
  --group-fields intent,modality,cluster
```

## Inputs

Query log JSONL records need:

- `id` or `query_id`
- `expected_route`, `label`, `ground_truth_route`, or `route`
- optional grouping metadata such as `intent`, `modality`, or `cluster`

Router decisions can be:

```json
{
  "router_a": {"q1": "search", "q2": "code_interpreter"},
  "router_b": {"q1": "tool_planner", "q2": "code_interpreter"}
}
```

The report is machine-readable JSON for CI, dashboards, or experiment tracking.
