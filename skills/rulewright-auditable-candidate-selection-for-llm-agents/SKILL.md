---
name: rulewright-auditable-candidate-selection-for-llm-agents
description: Use Rulewright to make LLM agent candidate selection explicit, inspectable, and reproducible when trigger keywords include candidate selection, reranking, rules.yaml, decision_matrix.json, selected_ids, tool routing, retrieval evaluation, or answer selection.
version: 0.1.0
license: MIT
---

# Rulewright — Auditable Candidate Selection for LLM Agents
Auto-generated and experimental; review the policy and scores before using them in high-impact workflows.

## Overview
LLM agents often choose documents, tools, answers, or actions without leaving a clear decision trace. Rulewright separates selection into two inspectable passes: first create a structured comparison policy, then score each candidate against that policy. The bundled CLI implements a deterministic local reference path that emits `rules.yaml`, `decision_matrix.json`, and machine-readable `selected_ids`.

## When to use
- Use when an agent must select among retrieval results, tools, answer drafts, actions, or dataset items.
- Use when debugging why a candidate was selected or rejected.
- Use when comparing model versions, reranking policies, or deterministic replay behavior.
- Use when a team needs a compact audit artifact without storing private chain-of-thought text.
- When NOT to use: do not use this minimal reference implementation as the only control for legal, medical, financial, hiring, lending, or other high-impact decisions.

## Workflow
1. Prepare a JSON input file with a `query` string and a `candidates` array.
2. Run `python3 scripts/run.py --input examples/candidates.json --rules-out rules.yaml --matrix-out decision_matrix.json --selected-out selected_ids.json`.
3. Inspect `rules.yaml` to confirm the dimensions, weights, constraints, and rejection conditions match the task.
4. Inspect `decision_matrix.json` for per-candidate scores, pass/fail status, rejection reasons, and evidence.
5. Use `selected_ids.json` as the machine-readable selection output for the next agent step.
6. For deterministic replay, pass a saved policy with `--rules-in rules.yaml` and a new or unchanged candidate set.
7. Run `python3 scripts/test.py` before modifying the skill or script behavior.

## Inputs & Outputs
Input JSON contract:
```json
{
  "query": "string task or user question",
  "max_selected": 1,
  "candidates": [
    {
      "id": "stable unique id",
      "title": "optional short label",
      "text": "candidate content to evaluate",
      "tags": ["optional", "strings"]
    }
  ]
}
```

Output shape:
- `rules.yaml`: YAML object with `version`, `query`, `selection`, `dimensions`, `constraints`, and `rejection_conditions`.
- `decision_matrix.json`: JSON object with `query`, `rules_fingerprint`, `selected_ids`, and `candidates`.
- Each `decision_matrix.json.candidates[]` item has `id`, `passed`, `rejected`, `rejection_reasons`, `total_score`, `dimension_scores`, `weighted_scores`, and `evidence`.
- `selected_ids.json`: JSON array of selected candidate ids, ordered by score descending and candidate id ascending for ties.

## Installation
Copy this skill directory into a Claude Code or OpenClaw-compatible skills directory, then run commands from the skill root:
```bash
python3 --version
python3 scripts/run.py --help
python3 scripts/test.py
```

No package installation is required; the reference implementation uses only the Python standard library.

## Usage
Run the built-in self-test:
```bash
python3 scripts/run.py --selftest
```

Evaluate an example file and write all artifacts:
```bash
python3 scripts/run.py \
  --input examples/candidates.json \
  --rules-out rules.yaml \
  --matrix-out decision_matrix.json \
  --selected-out selected_ids.json
```

Replay with saved rules:
```bash
python3 scripts/run.py \
  --input examples/candidates.json \
  --rules-in rules.yaml \
  --matrix-out replay_matrix.json \
  --selected-out replay_selected_ids.json
```

Show CLI help:
```bash
python3 scripts/run.py --help
```

Optional environment variables are read but never required: `RULEWRIGHT_PROVIDER`, `RULEWRIGHT_MODEL`, and `RULEWRIGHT_API_KEY`. The local reference implementation does not call any external API and never prints API key values.

## Example
Command:
```bash
python3 scripts/run.py --selftest
```

Expected output:
```json
{
  "selected_ids": [
    "doc-rules-first"
  ],
  "top_score": 0.775
}
```

## Limitations
- The scoring implementation is a deterministic reference heuristic, not a learned reranker.
- The YAML parser only supports the `rules.yaml` format emitted by this script.
- Evidence excerpts are short audit aids, not private reasoning traces.
- The CLI does not contact model providers; provider environment variables are placeholders for future integrations.

## Verification
Automated execution check: **passed ✅**.

- Steps: structure=ok · syntax=ok · help=ok · selftest=ok · test=ok
- Commands and outputs shown in `README.md` are captured from these real runs.
