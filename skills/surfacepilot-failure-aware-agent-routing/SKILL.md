---
name: surfacepilot-failure-aware-agent-routing
description: Routes LLM agent tasks by execution-surface failure risk and should be used when prompts mention agent routing, tool risk, execution surface, retrieval gap, file edit, service call, data transform, state verification, sandbox, human review, or verification-first.
license: MIT
---

# SurfacePilot - Failure-Aware Agent Routing
Auto-generated and experimental; inspect policy choices before using them in production.

## Overview
SurfacePilot routes LLM agent tasks by estimating where execution is likely to fail, not just by classifying the prompt domain. It scores execution surfaces such as retrieval, file edits, service calls, data transformations, and state verification, then emits a JSON routing recommendation for agent runners, CI systems, or orchestration code.

The bundled CLI is intentionally small and auditable. It uses deterministic standard-library rules, tool metadata, keyword patterns, and an optional lightweight YAML policy file.

## When to use
- Use when deciding whether an agent task should run directly, cautiously, in a sandbox, with verification first, or behind human review.
- Use when a task may touch execution boundaries such as repository edits, external APIs, data migrations, generated files, tests, deployments, or stateful services.
- Use when an orchestrator needs a JSON-first routing decision before selecting a workflow or granting tools.
- Use when reviewing tool exposure risk for retrieval, file_edit, service_call, data_transform, or state_verification surfaces.
- When NOT to use: do not use this as a security boundary or as the only approval mechanism for irreversible production operations.

## Workflow
1. Write the agent task prompt as a plain string.
2. List the tools available to the agent, including each tool name, optional execution surfaces, and a risk label of `low`, `medium`, or `high`.
3. Optionally tune `examples/policy.yml` or another YAML policy file with custom surface keywords, thresholds, and route actions.
4. Run `python scripts/run.py --input examples/task.json --pretty` or pass `--task` and `--tools-json` directly.
5. Read the JSON output, especially `recommendation.route`, `risk.overall`, `risk.surfaces`, and `actions`.
6. Apply the recommended workflow in the surrounding agent runner, such as direct execution, cautious execution, sandboxing, verification-first, or human review.
7. Re-run after changing tool access, the task prompt, or the policy file.

## Inputs & Outputs
Input JSON file contract:

```json
{
  "task": "string describing the agent request",
  "tools": [
    {
      "name": "tool_name",
      "surfaces": ["retrieval", "file_edit", "service_call", "data_transform", "state_verification"],
      "risk": "low|medium|high"
    }
  ]
}
```

`surfaces` may be omitted when the tool name clearly implies a surface; `risk` defaults to `medium`. The optional policy path may come from `--policy` or the `SURFACEPILOT_POLICY` environment variable.

Output JSON shape:

```json
{
  "task": "string",
  "recommendation": {
    "route": "direct_execution|cautious_execution|verification_first|sandboxing|human_review",
    "confidence": 0.0,
    "reason": "string",
    "required_surfaces": ["surface_name"]
  },
  "risk": {
    "overall": 0.0,
    "level": "none|low|medium|high",
    "surfaces": {
      "surface_name": {
        "score": 0.0,
        "level": "none|low|medium|high",
        "signals": ["matched keyword or condition"],
        "available_tools": ["tool_name"],
        "missing_capability": false
      }
    }
  },
  "actions": ["recommended operator action"],
  "tools_considered": ["tool_name"],
  "policy": {
    "source": "default|path",
    "version": "surfacepilot-policy-v1"
  }
}
```

## Installation
Copy or clone this skill directory into a skills folder used by Claude Code, OpenClaw, or another compatible agent runtime:

```bash
mkdir -p skills
cp -R surfacepilot-failure-aware-agent-routing skills/
cd skills/surfacepilot-failure-aware-agent-routing
python scripts/run.py --help
python scripts/test.py
```

No package installation is required because the reference implementation uses only the Python standard library.
If your system exposes Python 3 as `python3` instead of `python`, use `python3` for the same commands.

## Usage
Show help:

```bash
python scripts/run.py --help
```

Run the built-in sample:

```bash
python scripts/run.py --selftest --pretty
```

Run the included example input:

```bash
python scripts/run.py --input examples/task.json --pretty
```

Run with an explicit task and tool list:

```bash
python scripts/run.py \
  --task "Update a CSV import script, call the billing sandbox, and verify row counts" \
  --tools-json '[{"name":"apply_patch","surfaces":["file_edit"],"risk":"high"},{"name":"billing_sandbox","surfaces":["service_call"],"risk":"medium"},{"name":"pytest","surfaces":["state_verification"],"risk":"low"}]' \
  --pretty
```

Run with a policy file:

```bash
python scripts/run.py --input examples/task.json --policy examples/policy.yml --pretty
```

## Example
Command:

```bash
python scripts/run.py --input examples/task.json --pretty
```

Expected output is stored in `examples/expected-output.json`. The route should be `human_review` for the included sample because it combines file editing, service calls, data transformation, and verification risk.

```json
{
  "task": "Update the billing migration script, call Stripe sandbox to verify invoices, and summarize the changed rows.",
  "recommendation": {
    "route": "human_review",
    "confidence": 0.95,
    "reason": "Highest risk surfaces: data_transform=0.71, service_call=0.69, file_edit=0.59.",
    "required_surfaces": [
      "file_edit",
      "service_call",
      "data_transform",
      "state_verification"
    ]
  },
  "risk": {
    "overall": 0.86,
    "level": "high",
    "surfaces": {
      "retrieval": {
        "score": 0.0,
        "level": "none",
        "signals": [
          "tool_available"
        ],
        "available_tools": [
          "repo_read"
        ],
        "missing_capability": false
      },
      "file_edit": {
        "score": 0.59,
        "level": "medium",
        "signals": [
          "keyword:changed",
          "keyword:update",
          "tool_available"
        ],
        "available_tools": [
          "apply_patch"
        ],
        "missing_capability": false
      },
      "service_call": {
        "score": 0.69,
        "level": "medium",
        "signals": [
          "keyword:stripe",
          "keyword:call",
          "keyword:sandbox",
          "tool_available"
        ],
        "available_tools": [
          "stripe_sandbox"
        ],
        "missing_capability": false
      },
      "data_transform": {
        "score": 0.71,
        "level": "high",
        "signals": [
          "keyword:migration",
          "keyword:summarize",
          "keyword:rows",
          "missing_tool_for_surface"
        ],
        "available_tools": [],
        "missing_capability": true
      },
      "state_verification": {
        "score": 0.32,
        "level": "low",
        "signals": [
          "keyword:verify",
          "tool_available"
        ],
        "available_tools": [
          "pytest"
        ],
        "missing_capability": false
      }
    }
  },
  "actions": [
    "Require human approval before state-changing steps.",
    "Separate planning from execution.",
    "Run verification after each execution surface completes.",
    "Add or enable tools for: data_transform."
  ],
  "tools_considered": [
    "repo_read",
    "apply_patch",
    "stripe_sandbox",
    "pytest"
  ],
  "policy": {
    "source": "default",
    "version": "surfacepilot-policy-v1"
  }
}
```

## Limitations
- The router is deterministic and rule-based; it does not understand all intent or all tool semantics.
- The YAML parser supports only the small mapping and list subset used by the included policy format.
- Scores are routing heuristics, not probabilities.
- This does not execute tools, validate credentials, or enforce permissions.
- Human review recommendations still require an external approval workflow.
