# RouteQuake Skill

RouteQuake is a minimal installable skill for stress testing LLM, agent, model, and tool routers under distribution shift.

## Install

Copy this directory into your Claude Code, OpenClaw, or Codex-compatible skills directory.

## Run

Use the built-in sample data:

```bash
python scripts/run.py
```

Run with the included CSV example:

```bash
python scripts/run.py --input examples/router_eval.csv --output-dir reports
```

The script writes:

- `reports/routequake_report.md`
- `reports/routequake_report.json`

## CSV Format

Required columns:

- `selected_router`
- `correct_router`
- at least two numeric router score columns named `score_<router_name>`

Recommended metadata columns:

- `task`
- `intent`
- `difficulty`
- `cohort`
- `perturbation`
- `rare_case`

## CI Gate Example

```bash
python scripts/run.py \
  --input examples/router_eval.csv \
  --min-worst-slice-accuracy 0.55 \
  --output-dir reports
```

The command exits with status code `2` if the minimum worst-slice accuracy threshold is not met.
