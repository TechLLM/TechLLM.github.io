---
name: maskloom-distributional-bias-probing-for-llm-and-agent-failu
description: Run MaskLoom distributional masking probes for prompts, RAG contexts, candidate answers, or agent tools when debugging LLM/agent failures, bias, instability, RAG selection, tool routing, or mask-probe regressions.
version: 0.1.0
license: MIT
---

# MaskLoom - Distributional Bias Probing for LLM and Agent Failures

Auto-generated and experimental.

## Overview

MaskLoom helps diagnose unstable or biased choices in LLMs, RAG pipelines, and tool-using agents by probing how selections change under repeated masking. Instead of replaying one failed input, it masks prompt and candidate-context spans across deterministic trials, reruns a selector, and reports whether outputs remain stable or collapse toward specific candidates.

The included reference CLI uses a local lexical selector by default and can also call an external command template, so it works without API keys while still fitting into real evaluation harnesses.

## When to use

- Use when an LLM, RAG pipeline, router, evaluator, or tool-using agent picks different answers, passages, tools, routes, or actions from similar inputs.
- Use when debugging whether a failure looks like missing knowledge versus over-weighting a misleading cue in the prompt, candidate context, answer choice, or tool description.
- Use for regression tests around trigger keywords such as `mask-probe`, `distributional bias`, `selection instability`, `RAG reranking`, `tool routing`, `agent failure`, `candidate normalization`, and `sensitive token attribution`.
- Use when you need a JSON-first audit artifact for CI, dashboards, experiment tracking, or human review.
- When NOT to use: do not use this as a proof of fairness, truthfulness, or causal attribution without a larger evaluation design and domain-specific validation.

## Workflow

1. Create a JSON input file with a `prompt` string and a `candidates` array. Each candidate should have an `id` and `text`.
2. Run the bundled CLI on the input with a fixed seed, trial count, and mask probability.
3. Review `selection_distribution` to see whether selections remain stable or collapse toward one candidate.
4. Review `sensitive_spans` to find prompt or candidate tokens whose masking often changes the selected output.
5. Review `bias_suspects` as leads for human inspection, not as final judgments.
6. If testing a real model or agent, pass `--command-template` and make the command return either a candidate id or JSON with `selected_id`.
7. Store the JSON report in your evaluation, regression, or incident-review workflow.

## Inputs & Outputs

Input JSON contract:

```json
{
  "prompt": "Question, instruction, routing request, or failed agent input.",
  "candidates": [
    {"id": "candidate_a", "text": "Candidate answer, passage, tool, route, or action description."}
  ]
}
```

Candidate strings are also accepted and are assigned ids like `candidate_1`.

Output JSON shape:

```json
{
  "schema_version": "maskloom.report.v1",
  "probe": {
    "trials_requested": 6,
    "trials_completed": 6,
    "mask_probability": 0.2,
    "seed": 11,
    "selector": "builtin"
  },
  "input_summary": {
    "prompt_token_count": 6,
    "candidate_count": 3
  },
  "baseline": {
    "selected_id": "billing",
    "scores": {"billing": 3.0}
  },
  "selection_distribution": [
    {"id": "billing", "count": 5, "rate": 0.8333}
  ],
  "sensitive_spans": [
    {"source": "prompt", "token": "refund", "masked_count": 2, "changed_count": 0, "change_rate": 0.0}
  ],
  "bias_suspects": [
    {"id": "billing", "selection_rate": 0.8333, "reason": "dominant_selection_under_masking"}
  ],
  "trials": [
    {
      "trial": 0,
      "masked_prompt": "Which route should handle invoice refund requests?",
      "masked_candidates": [{"id": "billing", "text": "Billing tool handles invoices, refunds, and receipts."}],
      "masked_spans": [{"source": "candidate:billing", "token": "Billing"}],
      "selected_id": "billing",
      "scores": {"billing": 3.0}
    }
  ]
}
```

## Installation

Copy this skill folder into your Claude Code or OpenClaw-style skills directory, then run from the skill root:

```bash
python3 scripts/run.py --help
python3 scripts/test.py
```

The reference implementation uses only the Python standard library. Use `python` instead of `python3` if your environment maps `python` to Python 3.

## Usage

Run the built-in self-test:

```bash
python3 scripts/run.py --selftest
```

Run the sample probe and write a report:

```bash
python3 scripts/run.py --input examples/sample_probe.json --trials 6 --mask-probability 0.2 --seed 11 --output report.json
```

Show CLI options:

```bash
python3 scripts/run.py --help
```

Call an external selector command. The command receives shell-quoted placeholder values and must print a candidate id or JSON containing `selected_id`:

```bash
python3 scripts/run.py --input examples/sample_probe.json --command-template 'python3 my_selector.py --trial {trial_json}'
```

Optional environment variables:

- `MASKLOOM_COMMAND_TIMEOUT`: timeout in seconds for external command probes.
- `MASKLOOM_API_KEY`: available for your external command or wrapper if it needs a key; the bundled code never prints it.

## Example

Command:

```bash
python3 scripts/run.py --input examples/sample_probe.json --trials 6 --mask-probability 0.2 --seed 11
```

Expected output is JSON matching `examples/expected_report.json`. The key result is:

```json
{
  "baseline": {"selected_id": "billing"},
  "selection_distribution": [
    {"id": "billing", "count": 5, "rate": 0.8333},
    {"id": "support", "count": 0, "rate": 0.0},
    {"id": "sales", "count": 1, "rate": 0.1667}
  ],
  "bias_suspects": [
    {"id": "billing", "selection_rate": 0.8333, "reason": "dominant_selection_under_masking"}
  ]
}
```

## Limitations

- The built-in selector is a deterministic lexical baseline, not a substitute for probing your production model or agent.
- Masking-based attribution is correlational and should be treated as a diagnostic lead.
- Results depend on candidates, masking policy, trial count, seed, and any external selector behavior.
- The command-template mode executes local commands; only use commands you trust.

## Verification
Automated execution check: **passed ✅**.

- Steps: structure=ok · syntax=ok · help=ok · selftest=ok · test=ok
- Commands and outputs shown in `README.md` are captured from these real runs.
