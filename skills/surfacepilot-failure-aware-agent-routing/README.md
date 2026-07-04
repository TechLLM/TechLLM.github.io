# SurfacePilot - Failure-Aware Agent Routing

SurfacePilot is a small installable skill and CLI for routing LLM agent tasks by execution-surface failure risk. It scores retrieval, file editing, service calls, data transformations, and state verification, then emits a deterministic JSON routing recommendation.

## Install

```bash
mkdir -p skills
cp -R surfacepilot-failure-aware-agent-routing skills/
cd skills/surfacepilot-failure-aware-agent-routing
python scripts/run.py --help
python scripts/test.py
```

No dependencies are required.
If your system exposes Python 3 as `python3` instead of `python`, use `python3` for the same commands.

## Usage

```bash
python scripts/run.py --help
python scripts/run.py --selftest --pretty
python scripts/run.py --input examples/task.json --pretty
python scripts/run.py --input examples/task.json --policy examples/policy.yml --pretty
```

The CLI can also accept an inline task and tool list:

```bash
python scripts/run.py \
  --task "Update a CSV import script, call the billing sandbox, and verify row counts" \
  --tools-json '[{"name":"apply_patch","surfaces":["file_edit"],"risk":"high"},{"name":"billing_sandbox","surfaces":["service_call"],"risk":"medium"},{"name":"pytest","surfaces":["state_verification"],"risk":"low"}]' \
  --pretty
```

## Example

```bash
python scripts/run.py --input examples/task.json --pretty
```

Expected output is in `examples/expected-output.json`. For the included sample, the expected route is `human_review` because the task combines file editing, a service call, data transformation, and verification.

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
