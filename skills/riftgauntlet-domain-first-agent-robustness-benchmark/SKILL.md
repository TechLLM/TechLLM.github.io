---
name: riftgauntlet-domain-first-agent-robustness-benchmark
description: Replays JSONL agent traces under deterministic domain shifts and observation failures, ranks fragile slices, estimates failure-detection AUROC, and exports regression fixtures; use for agent robustness benchmarks, trace replay, domain-shift testing, perturbation testing, router evaluation, and CI regression safeguards.
version: 0.1.0
license: MIT
---

# RiftGauntlet — Domain-First Agent Robustness Benchmark

Auto-generated and experimental; inspect the replay oracle before using results for deployment decisions.

## Overview

Average task success can hide a complete collapse in one domain or failure mode. RiftGauntlet replays portable JSONL traces against declarative perturbations, evaluates mutated observations with trace-level replay oracles, and reports matched-baseline deltas by domain and slice without live model calls.

## When to use

- Use when evaluating an agent, router, planner, or parallel workflow across multiple domains.
- Use when testing missing, truncated, malformed, delayed, duplicated, reordered, or failed tool observations.
- Use when simulating unknown domains or converting weak slices into deterministic CI fixtures.
- Use when traces record `confidence`, `abstained`, or `risk_score` and failure-recognition quality matters.
- When NOT to use: do not treat replay-oracle results as a substitute for live end-to-end evaluation when the oracle cannot model the agent's adaptive behavior.

## Workflow

1. Add one JSON object per line to a trace file, including a unique `id`, `domain`, recorded `success`, ordered `observations`, and a deterministic `replay_oracle`.
2. Add optional detection signals: prefer `risk_score`, then `abstained`, then `confidence`; all numeric scores use the range 0 through 1.
3. Define scenarios in a JSON specification with `match_domains` and ordered `operations`. Supported operation types are `missing`, `truncate`, `malformed`, `delay`, `duplicate`, `reorder`, `tool_failure`, and `domain_shift`.
4. Run `python3 scripts/run.py --input TRACE.jsonl --spec PERTURBATIONS.json` and inspect `domains`, `slices`, `worst_slices`, and `failure_detection` before relying on the aggregate summary.
5. Correct invalid traces or overly permissive replay oracles; validation errors exit non-zero before replay.
6. Export weak slices only when desired with `--fixtures-dir DIR`. Commit those deterministic JSON fixtures to the project's regression suite.
7. Re-run after agent or routing changes and compare slice-level success rates and robustness deltas.

## Inputs & Outputs

Input contract:

- Trace JSONL: each line is an object with `id` (unique string), `domain` (string), `success` (boolean), `observations` (non-empty array), and `replay_oracle` (object). Each observation requires unique baseline `id`, `tool`, string `content`, and non-negative integer `latency_ms`.
- Replay oracle: supports `required_observations`, `required_content`, `expected_order`, `max_total_latency_ms`, `allow_malformed`, `allow_duplicates`, and `fail_on_tool_error`.
- Detection signal: optionally provide `risk_score`, `abstained`, or `confidence`. The failure score priority is risk score, abstention, then inverse confidence.
- Perturbation JSON: `{"schema_version":"1.0","scenarios":[...]}`. Each scenario requires a unique `name`, a non-empty `match_domains` array (`"*"` matches all), and a non-empty `operations` array.

The CLI emits one deterministic, pretty-printed JSON object with this exact top-level shape:

```text
{
  "domains": [domain metric objects],
  "failure_detection": {
    "auroc_proxy": number|null,
    "failure_cases": integer,
    "scorable_cases": integer,
    "score_sources": object,
    "success_cases": integer
  },
  "schema_version": "1.0",
  "slices": [slice metric objects],
  "summary": {
    "baseline_success_rate": number,
    "matched_baseline_success_rate": number,
    "perturbed_cases": integer,
    "perturbed_success_rate": number,
    "robustness_delta": number,
    "total_traces": integer,
    "worst_slice_success_rate": number|null
  },
  "worst_slices": [ranked slice metric objects]
}
```

Domain objects contain `domain`, baseline and perturbed sample/success fields, both success rates, `matched_baseline_success_rate`, `robustness_delta`, and `source_domains`. Slice objects contain `scenario`, `domain`, `source_domains`, `perturbations`, samples, successes, success rate, matched `baseline_success_rate`, and `robustness_delta`; worst slices add `rank`. Rates and deltas are rounded to six decimals. AUROC is `null` unless at least one successful and one failed replay case have detection signals.

## Installation

Requires Python 3.9 or newer and uses only the standard library.

```bash
mkdir -p ~/.claude/skills
cp -R . ~/.claude/skills/riftgauntlet-domain-first-agent-robustness-benchmark
```

For OpenClaw, copy the same directory under `~/.openclaw/skills/` instead.

## Usage

Run these commands from the installed skill directory:

```bash
python3 scripts/run.py --help
python3 scripts/run.py --selftest
python3 scripts/run.py --input examples/traces.jsonl --spec examples/perturbations.json
python3 scripts/run.py --input examples/traces.jsonl --spec examples/perturbations.json \
  --output report.json --fixtures-dir regression-fixtures
python3 scripts/test.py
```

Set `RIFTGAUNTLET_WORST_LIMIT` to change the default number of ranked slices. Existing output paths are never overwritten unless `--force` is explicitly passed with `--output` or `--fixtures-dir`.

## Example

```bash
python3 scripts/run.py --input examples/traces.jsonl --spec examples/perturbations.json
```

Expected headline output; the complete matching report is `examples/expected-report.json`:

```json
{
  "failure_detection": {"auroc_proxy": 0.5, "scorable_cases": 7},
  "summary": {
    "baseline_success_rate": 1.0,
    "matched_baseline_success_rate": 1.0,
    "perturbed_cases": 7,
    "perturbed_success_rate": 0.142857,
    "robustness_delta": -0.857143,
    "total_traces": 3,
    "worst_slice_success_rate": 0.0
  }
}
```

## Limitations

- Replay oracles approximate post-perturbation success; they do not execute the original agent or model.
- Detection scores are trace-level proxies and may not reflect scenario-aware confidence.
- Operations mutate JSON observations, not external tool side effects, streaming behavior, or real wall-clock latency.
- Domain and scenario coverage is only as representative as the supplied traces and specifications.

## Verification
Automated execution check: **passed ✅**.

- Steps: structure=ok · contract=ok · syntax=ok · help=ok · selftest=ok · test=ok
- Commands and outputs shown in `README.md` are captured from these real runs.
