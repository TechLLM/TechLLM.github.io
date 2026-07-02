---
name: routequake-distribution-shift-stress-testing-for-agent-route
description: RouteQuake stress tests LLM and agent routers under distribution shift; use it for routequake, router audit, distribution shift, robustness, regret, worst-slice, and CI release-gate checks.
license: MIT
---

# RouteQuake - Distribution Shift Stress Testing for Agent Routers

Auto-generated and experimental; review results before using them as release gates.

## Overview

RouteQuake is a small, CSV-first CLI for stress testing LLM, agent, model, and tool routers under distribution shift. It reads logged routing evaluations, infers router score columns, applies controlled shift scenarios, and reports:

- Weighted routing accuracy by scenario
- Worst-slice accuracy across metadata columns
- Regret versus the best available router score per example
- Router instability rankings across scenarios
- Markdown and JSON reports for CI or evaluation records

The included script is intentionally dependency-free and runs with built-in mock data when no input CSV is supplied.

## When to Use

Use this skill when a user asks to:

- Audit an LLM, model, agent, or tool router
- Stress test routing decisions under distribution shift
- Compare average routing accuracy with worst-slice behavior
- Generate a robustness report for router release gates
- Analyze regret, rare-case amplification, task reweighting, query perturbation labels, or router score instability

Trigger keywords include: `routequake`, `router audit`, `agent routing`, `distribution shift`, `stress test`, `worst-slice`, `regret`, `instability`, `release gate`, and `robustness report`.

## Installation

Copy this skill directory into your skills folder, then run the script from the installed directory:

```bash
python scripts/run.py
```

No third-party Python packages are required.

## Usage

Run with built-in sample data:

```bash
python scripts/run.py
```

Run against an example CSV:

```bash
python scripts/run.py --input examples/router_eval.csv --output-dir reports
```

Use custom slice columns and a stricter rare-case multiplier:

```bash
python scripts/run.py \
  --input examples/router_eval.csv \
  --slice-columns task,intent,difficulty,cohort \
  --rare-multiplier 5 \
  --output-dir reports
```

Fail CI when the worst-slice accuracy drops below a threshold:

```bash
python scripts/run.py --input examples/router_eval.csv --min-worst-slice-accuracy 0.55
```

Optional environment variables:

- `ROUTEQUAKE_API_KEY`: detected but not required; the reference script does not call external services.
- `ROUTEQUAKE_OUTPUT_DIR`: default report directory when `--output-dir` is not provided.

## Example

Input CSV columns should include `selected_router`, `correct_router`, and at least two score columns named `score_<router_name>`.

```csv
id,query,task,intent,difficulty,cohort,perturbation,rare_case,selected_router,correct_router,score_fast,score_deep
1,Reset my password,account,password_reset,easy,consumer,none,false,fast,fast,0.91,0.72
2,Diagnose latency spike,ops,incident_debug,hard,enterprise,paraphrase,true,fast,deep,0.54,0.88
```

Command:

```bash
python scripts/run.py --input examples/router_eval.csv --output-dir reports
```

Outputs:

- `reports/routequake_report.md`
- `reports/routequake_report.json`

## Limitations

- This reference implementation does not retrain routers or call LLM APIs.
- Query perturbation is represented by labels in the input CSV; it does not generate new query text.
- Scenario weighting is intentionally simple and transparent, not a full Wasserstein optimizer.
- Accuracy assumes `selected_router == correct_router`; adapt the script if your logs use a different correctness label.
- Score columns must be numeric and named with the `score_` prefix.
