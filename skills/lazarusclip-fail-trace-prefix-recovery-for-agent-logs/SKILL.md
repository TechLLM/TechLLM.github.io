---
name: lazarusclip-fail-trace-prefix-recovery-for-agent-logs
description: Salvage the trustworthy pre-failure prefix of a failed agent trace by locating the fatal step and masking everything after it; use when triaging agent logs, replay buffers, rollout dumps, or postmortem directories for RLHF/GRPO/RFT training data, or when asked to recover, rescue, or filter failed traces instead of discarding them.
version: 0.1.0
license: MIT
---

# LazarusClip — fail-trace prefix recovery for agent logs

*Auto-generated and experimental. Treat the confidence scores and labels as triage hints, not ground truth.*

## Overview

Agent pipelines usually keep only the runs that succeeded, throwing away entire traces because of one tool error, hallucination, or refusal near the end — even though a long stretch of sound reasoning preceded the failure. LazarusClip takes the Fatal-aware GRPO insight (mask post-failure tokens, preserve pre-failure signal via one-sided advantage clamping) and moves it from the loss function into the data layer.

The library inspects a finished trace, locates the first step where outcomes stop being trustworthy, and splits the trace there. The surviving prefix comes back as a first-class, confidence-scored artifact with token-masking hints, so it can feed GRPO, PPO, or rejection-sampling loops alongside your existing positive-only filters rather than competing with them.

## When to use

- You have a directory of failed agent runs (replay buffer, rollout dump, postmortem archive) and want to know which ones still hold usable reasoning prefixes.
- You are assembling RLHF / RFT / GRPO training data and your positive-only filter is discarding too much volume.
- You need per-step masking hints (`keep_step_indices` / `mask_step_indices`) to feed a fine-tuning loop that supports one-sided advantage clamping.
- You are doing a postmortem and want the exact step index where a run went off the rails, with the evidence that pointed there.

**When NOT to use:** do not use it on traces that never failed (a positive-only filter is cheaper and exact), and do not use its label as an automatic training-set gate without human spot-checks — the offline detector is vocabulary-based and will miss silent semantic failures.

## Workflow

1. **Collect traces.** Export each run as a JSON file: `{"trace_id": "...", "steps": [...]}`, one file per run. Steps need at least a `role`; `type`, `tool_name`, `status`/`is_error`/`exit_code`, and `content` sharpen detection.
2. **Smoke-test the install.** Run `python scripts/run.py --selftest` — it exercises the same `recover()` function the CLI uses, on built-in samples, with no network and no API key.
3. **Recover one trace** to sanity-check the boundary: `python scripts/run.py --input <trace.json>` (see `examples/input/` for the file shape). Read `fatal_step_index` and the `signals` list to confirm the detector fired on the step you expect.
4. **Tune the boundary policy** if needed: raise `--min-prefix-steps` to demand a longer surviving prefix before a trace may be labelled `recoverable`.
5. **Optionally add an LLM judge** with `--judge openai|anthropic|ollama`. The judge becomes one more voter in the ensemble; `--passes N` runs it N times for self-consistency calibration. If it is unreachable, the run warns on stderr and falls back to the offline voters.
6. **Triage at scale** with `python scripts/run.py --batch <dir> --output triage.json`, then read `label_counts` to see the salvage envelope.
7. **Consume downstream.** Keep records labelled `recoverable`, feed `pre_failure_subgraph.steps` as the training sample, and apply `mask_hints.mask_step_indices` (with `advantage_clamp: "one_sided"`) to the tail. Route `ambiguous` to human review; drop `poisoned`.

## Inputs & Outputs

**Input contract** — a JSON object (or a bare list of steps):

| Field | Required | Notes |
| --- | --- | --- |
| `trace_id` | no | Non-empty string; defaults to `"unknown"`. |
| `steps` | **yes** | Non-empty list of step objects. |
| `steps[].role` | **yes** | Non-empty string, e.g. `user`, `assistant`, `tool`. |
| `steps[].type` | no | `thought`, `tool_call`, `tool_result`, `message`, … Defaults to `message`. |
| `steps[].content` | no | String; non-strings are JSON-encoded. Defaults to `""`. |
| `steps[].tool_name` | no | Used by the repeated-tool-call heuristic. |
| `steps[].status` / `is_error` / `exit_code` | no | Any of these drives the structural voter. |

Anything else raises `TraceValidationError`; the CLI prints the message and exits `2`.

**Output shape** — one JSON record per trace:

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | string | Currently `"1.0"`. |
| `trace_id`, `step_count` | string, int | Echoed identity and trace length. |
| `fatal_step_index` | int \| null | First untrustworthy step; `null` if the trace is clean. |
| `confidence` | float | `0.5 × voter agreement + 0.5 × strongest detector weight`, rounded to 3 places. |
| `suggested_label` | string | `clean`, `recoverable`, `ambiguous`, or `poisoned`. |
| `pre_failure_subgraph` | object | `{step_count, steps}` — the salvaged prefix. |
| `masked_tail` | object | `{step_count, steps}` — everything from the boundary onward. |
| `mask_hints` | object | `{advantage_clamp, keep_step_indices, mask_step_indices}`. |
| `signals` | list | `{detector, step_index, pattern, excerpt}` evidence records. |
| `judge` | object | `{backend, passes, agreement}`. |

Batch mode wraps these in `{schema_version, processed, failed, label_counts, records, errors}`; each record gains a `source` filename.

## Installation

```bash
# copy or clone this skill directory, then:
cd lazarusclip-fail-trace-prefix-recovery-for-agent-logs
python3 scripts/run.py --selftest
```

Python 3.9+ standard library only — no dependencies, no `requirements.txt`.

## Usage

```bash
python scripts/run.py --help                                   # full option list
python scripts/run.py --selftest                               # offline checks, no API key
python scripts/run.py --input examples/input/trace_tool_failure.input.json
cat trace.json | python scripts/run.py --input -               # read from stdin
python scripts/run.py --batch examples/input                   # triage a directory
python scripts/run.py --batch examples/input --output triage.json
python scripts/run.py --input trace.json --min-prefix-steps 4  # stricter salvage policy
python scripts/run.py --input trace.json --judge anthropic --passes 5   # needs ANTHROPIC_API_KEY
python scripts/test.py                                         # independent test suite
```

Credentials are read from the environment only — `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OLLAMA_HOST` (default `http://localhost:11434`), with optional `OPENAI_MODEL` / `ANTHROPIC_MODEL` / `OLLAMA_MODEL`. `--output` refuses to overwrite an existing file unless `--force` is passed.

## Examples

Every example is a pair sharing one `<name>`: the input trace at `examples/input/<name>.input.json` and the exact record it produces at `examples/output/<name>.output.json`. `scripts/test.py` runs `recover()` on every input and asserts it reproduces the committed output, and separately asserts that no input is left unpaired.

| Input | Expected output | What it covers |
| --- | --- | --- |
| `examples/input/trace_tool_failure.input.json` | `examples/output/trace_tool_failure.output.json` | 11-step run cut at step 8; label `recoverable`. |
| `examples/input/trace_clean_run.input.json` | `examples/output/trace_clean_run.output.json` | Successful run, no boundary; label `clean`. |

`examples/input/trace_tool_failure.input.json` is an agent that reads a file, writes a retry wrapper, then hits `pytest: command not found` and claims the tests passed anyway.

```bash
python scripts/run.py --input examples/input/trace_tool_failure.input.json
```

The first lines of the record:

```json
{
  "schema_version": "1.0",
  "trace_id": "agent-run-4417",
  "step_count": 11,
  "fatal_step_index": 8,
  "confidence": 1.0,
  "suggested_label": "recoverable",
```

Steps 0–7 (the file read, the design reasoning, the wrapper write) are returned in `pre_failure_subgraph`; steps 8–10 (the failed command, the rationalization, the false success claim) land in `masked_tail`. The `signals` list carries three pieces of evidence: `structural status=error` and `lexical command_not_found` at step 8, plus `heuristic success_claim_after_error` at step 10. The complete expected record is committed at `examples/output/trace_tool_failure.output.json`.

Batch triage over both example traces:

```bash
python scripts/run.py --batch examples/input
```

```json
{
  "schema_version": "1.0",
  "processed": 2,
  "failed": 0,
  "label_counts": {
    "clean": 1,
    "recoverable": 1,
    "ambiguous": 0,
    "poisoned": 0
  }
```

## Limitations

- The offline detector is vocabulary- and structure-driven: it catches tool errors, refusals, empty results, tool-call loops, and success claims that follow an error. It does **not** catch silent semantic failures (a plausible-looking wrong answer with no error marker).
- The boundary is the **earliest** voted index. A noisy false positive early in the trace shortens the prefix; inspect `signals` before trusting a surprisingly small `pre_failure_subgraph`.
- Confidence is a calibration heuristic over detector agreement and weight, not a probability. With the offline backend the voters are deterministic, so `--passes` only adds real information when a remote judge is enabled.
- Masking is step-level. `mask_hints` tells a training loop which steps to zero out; mapping steps to token spans is the caller's job and depends on your tokenizer and chat template.
- Remote judge backends are reference implementations against current public HTTP APIs; they are unexercised by the offline test suite and may need adjusting if a provider changes its response shape.
- Error recovery loops are treated as fatal. A trace where the agent hit an error and then genuinely recovered will still be cut at that error, understating the salvageable prefix.

## Verification
Automated execution check: **passed ✅**.

- Steps: structure=ok · contract=ok · syntax=ok · help=ok · selftest=ok · test=ok
- Commands and outputs shown in `README.md` are captured from these real runs.
