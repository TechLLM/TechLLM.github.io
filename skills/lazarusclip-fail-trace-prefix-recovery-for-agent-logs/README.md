# LazarusClip — fail-trace prefix recovery for agent logs

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> Salvage the sound reasoning that hides inside failed agent runs.

> 🤖 Auto-generated & self-verified skill. A minimal, runnable reference — review before production use.

## What is this?

Modern LLM agents produce enormous volumes of execution traces, and most training pipelines only ever consume the lucky few that finish cleanly. Failed runs are usually discarded wholesale, even when a long stretch of valid reasoning preceded the tool error, hallucination, or policy violation that killed the trace. That discarded prefix is exactly the kind of high-signal data that RLHF, RFT, and GRPO-style training loops are starving for.

LazarusClip lifts the core insight of Fatal-aware GRPO out of the loss function and into the data layer. Rather than masking post-failure tokens inside a trainer, it inspects a finished trace, locates the first step where outcomes become untrustworthy, and surgically excises everything from that boundary onward. The surviving prefix is returned as a first-class, confidence-scored artifact that composes with existing positive-only filters instead of competing with them — expanding the salvage envelope to include the high-quality prefixes hiding inside failed runs.

**Who is this for.** This is built for ML engineers, RL researchers, and data curators who maintain replay buffers, postmortem directories, or agent-evaluation harnesses. If you are fine-tuning models with GRPO, PPO, or rejection sampling and you keep wishing your failed traces had more usable signal, LazarusClip turns the graveyard of dead runs into a productive source of training data.

## ⏱ 30-Second Quick Start

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/lazarusclip-fail-trace-prefix-recovery-for-agent-logs
python scripts/run.py --selftest
```

**Expected output:**

```text
[PASS] tool-failure boundary is step 3
[PASS] tool-failure label is recoverable
[PASS] prefix keeps 3 steps
[PASS] tail masks 2 steps
[PASS] mask hints agree
[PASS] confidence is high
[PASS] clean trace has no boundary
[PASS] clean trace label is clean
[PASS] refusal at step 1 is poisoned
[PASS] output is deterministic
[PASS] empty steps rejected

11/11 checks passed
```

## Requirements

| Key | Value |
|---|---|
| Python | 3.9+ |
| Dependencies | Python standard library only |
| API key | Not required |

## 📦 Installation

**1) As a Claude Code / OpenClaw skill**

```bash
# Personal (available in every project)
git clone https://github.com/TechLLM/TechLLM.github.io /tmp/techllm-skills
mkdir -p ~/.claude/skills/lazarusclip-fail-trace-prefix-recovery-for-agent-logs
cp -r /tmp/techllm-skills/skills/lazarusclip-fail-trace-prefix-recovery-for-agent-logs/* ~/.claude/skills/lazarusclip-fail-trace-prefix-recovery-for-agent-logs/

# Project-local
mkdir -p .claude/skills/lazarusclip-fail-trace-prefix-recovery-for-agent-logs
cp -r /tmp/techllm-skills/skills/lazarusclip-fail-trace-prefix-recovery-for-agent-logs/* .claude/skills/lazarusclip-fail-trace-prefix-recovery-for-agent-logs/
```

**2) As a standalone CLI**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/lazarusclip-fail-trace-prefix-recovery-for-agent-logs
python scripts/run.py --help
```

**3) Manual download**

On GitHub, open the `skills/lazarusclip-fail-trace-prefix-recovery-for-agent-logs/` folder and download the files, or download the repo ZIP and copy that one folder.

## ⚡ Usage

Full `--help` output:

```text
usage: run.py [-h] [--input FILE | --batch DIR | --selftest]
              [--judge {offline,openai,anthropic,ollama}] [--passes PASSES]
              [--min-prefix-steps MIN_PREFIX_STEPS] [--timeout TIMEOUT]
              [--output FILE] [--force] [--indent INDENT]

LazarusClip: recover the salvageable pre-failure prefix of agent traces.

options:
  -h, --help            show this help message and exit
  --input FILE          trace JSON file ('-' reads stdin)
  --batch DIR           directory of *.json traces to triage
  --selftest            run offline selftest and exit
  --judge {offline,openai,anthropic,ollama}
                        judge backend (default: offline, no network)
  --passes PASSES       self-consistency passes for confidence calibration
                        (default: 3)
  --min-prefix-steps MIN_PREFIX_STEPS
                        minimum surviving prefix length to call a trace
                        recoverable
  --timeout TIMEOUT     per-request timeout in seconds for remote judges
  --output FILE         write JSON here instead of stdout
  --force               allow --output to overwrite a file
  --indent INDENT       JSON indent (default: 2)

Example: python scripts/run.py --input
examples/input/trace_tool_failure.input.json
```

## Examples

See the `examples/` folder in this skill (sample input + expected output).

## 🧠 How it works

- A hybrid fatal-boundary detector fuses LLM judgment, curated regex vocabularies for common tool errors, and structural heuristics like trajectory length and tool-call return codes to pinpoint the first untrustworthy step.
- The recovered trace is split into a pre-failure subgraph and a masked tail, then emitted as a schema-stable JSON record with fatal_step_index, confidence, and a suggested label of recoverable, poisoned, or ambiguous.
- Pluggable judge backends let you route scoring through OpenAI, Anthropic, local Ollama models, or a fully offline regex-only path for air-gapped environments.
- Token-level masking hints are emitted alongside the trace so the output drops directly into GRPO, PPO, or rejection-sampling fine-tuning loops without rewriting your trainer.
- Self-consistency calibration runs N independent judge passes and reports the agreement score, giving downstream consumers a principled way to threshold which recovered prefixes are worth training on.

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Confidence score comes back near zero on runs you expected to recover | The judge passes disagreed about where the fatal boundary sits, usually because the trace contains mixed signals like a recovered tool error followed by a soft policy drift. | Raise the number of self-consistency passes, or run LazarusClip with a stronger judge backend so the boundary vote stabilizes before the confidence is reported. |
| Offline mode flags every tool error as the fatal boundary even when the agent recovered | The regex-only backend is intentionally conservative and cannot see downstream consequences that an LLM judge would weigh. | Switch to a local model backend if one is available, or annotate the regex ruleset to whitelist specific recoverable error patterns you want to ignore. |
| Recovered prefixes are too short to be useful for fine-tuning | The fatal boundary was detected very early in the run, often because a structural heuristic over-triggered on benign tool retries. | Review the heuristic weights for your domain and disable the early-step penalty if your agents legitimately recover from transient tool failures. |

## FAQ

**How is this different from just filtering out failed runs?**

Filtering throws away the whole trace, including the reasoning that was correct. LazarusClip keeps the pre-failure prefix and only discards the portion after outcomes become untrustworthy, which substantially grows your usable training set without adding noise.

**Does LazarusClip modify my trainer?**

No. It operates at the data layer and emits masking hints and confidence scores that your existing GRPO, PPO, or rejection-sampling loop can consume directly.

**Can I use it without sending traces to a cloud LLM?**

Yes. There is a fully offline regex-only mode and support for local Ollama models, so you can keep sensitive agent logs on your own infrastructure.

**What does the suggested_label field mean?**

It is a coarse triage tag — recoverable for clean prefixes worth training on, poisoned for traces where failure contamination likely spread backward, and ambiguous when the judges could not agree.

**How accurate is the boundary detection?**

Accuracy scales with the number of self-consistency passes and the strength of the judge backend. Production users typically run several passes and threshold on the agreement score rather than treating any single result as ground truth.

## ✅ Verification

Passed automated structure / syntax / selftest checks (see `SKILL.md`).

## Uninstall

Delete the skill folder (`~/.claude/skills/lazarusclip-fail-trace-prefix-recovery-for-agent-logs/` or `.claude/skills/lazarusclip-fail-trace-prefix-recovery-for-agent-logs/`). Nothing else on your system is touched.

## 📜 Versioning

This skill uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## 🤝 Contributing

This is an auto-generated reference skill. Issues and PRs that improve it are welcome.

## License

MIT
