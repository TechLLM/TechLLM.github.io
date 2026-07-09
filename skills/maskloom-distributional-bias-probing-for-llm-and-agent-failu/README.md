# MaskLoom — Distributional Bias Probing for LLM and Agent Failures

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> Probe unstable LLM and agent decisions with randomized masking diagnostics.

> 🤖 Auto-generated & self-verified skill. A minimal, runnable reference — review before production use.

## What is this?

MaskLoom is a diagnostic toolkit for understanding why LLMs, RAG systems, and tool-using agents make unstable or biased choices. Instead of investigating one failed example by hand, it runs many masked variations of the same input and measures how the output distribution changes.

This helps separate two common failure modes: the system may be missing the knowledge it needs, or it may be over-weighting a misleading cue, passage, answer choice, or tool description. That distinction matters because the right fix depends on the cause.

MaskLoom turns these probes into structured reports that can support evaluation pipelines, regression tests, dashboards, and human review workflows.

**Who is this for.** MaskLoom is for AI engineers, evaluation teams, RAG builders, agent developers, and researchers who need practical evidence about why model or agent behavior changes across prompts, contexts, candidates, routes, or tools.

## ⏱ 30-Second Quick Start

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/maskloom-distributional-bias-probing-for-llm-and-agent-failu
python scripts/run.py --selftest
```

**Expected output:**

```text
{
  "schema_version": "maskloom.report.v1",
  "probe": {
    "trials_requested": 12,
    "trials_completed": 12,
    "mask_probability": 0.25,
    "seed": 1337,
    "selector": "builtin"
  },
  "input_summary": {
    "prompt_token_count": 5,
    "candidate_count": 3
  },
  "baseline": {
    "selected_id": "billing",
    "scores": {
      "billing": 3.0,
      "support": 2.0,
      "sales": 2.0
    }
  },
  "selection_distribution": [
    {
      "id": "billing",
      "count": 8,
      "rate": 0.6667
    },
    {
      "id": "support",
      "count": 2,
      "rate": 0.1667
    },
    {
      "id": "sales",
      "count": 2,
      "rate": 0.1667
    }
  ],
  "sensitive_spans": [
    {
      "source": "candidate:support",
      "token": "login",
      "masked_count": 2,
      "changed_count": 2,
      "change_rate": 1.0
    },
    {
      "source": "candidate:billing",
      "token": "receipt",
      "masked_count": 3,
      "changed_count": 2,
      "change_rate": 0.6667
    },
    {
      "source": "prompt",
      "token": "refund",
      "masked_count": 3,
      "changed_count": 2,
      "change_rate": 0.6667
    },
    {
      "source": "candidate:billing",
      "token": "handle",
      "masked_count": 5,
      "changed_count": 3,
      "change_rate": 0.6
    },
    {
      "source": "candidate:support",
      "token": "support",
      "masked_count": 5,
      "changed_count": 3,
      "change_rate": 0.6
    },
    {
      "source": "prompt",
      "token": "invoice",
      "masked_count": 7,
      "changed_count": 4,
      "change_rate": 0.5714
    },
    {
      "source": "candidate:support",
      "token": "route",
      "masked_count": 4,
      "changed_count": 2,
      "change_rate": 0.5
    },
    {
      "source": "candidate:billing",
      "token": "invoice",
      "masked_count": 2,
      "changed_count": 1,
      "change_rate": 0.5
    },
    {
      "source": "candidate:billing",
      "token": "refund",
      "masked_count": 2,
      "changed_count":
… (+17770 chars truncated)
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
mkdir -p ~/.claude/skills/maskloom-distributional-bias-probing-for-llm-and-agent-failu
cp -r /tmp/techllm-skills/skills/maskloom-distributional-bias-probing-for-llm-and-agent-failu/* ~/.claude/skills/maskloom-distributional-bias-probing-for-llm-and-agent-failu/

# Project-local
mkdir -p .claude/skills/maskloom-distributional-bias-probing-for-llm-and-agent-failu
cp -r /tmp/techllm-skills/skills/maskloom-distributional-bias-probing-for-llm-and-agent-failu/* .claude/skills/maskloom-distributional-bias-probing-for-llm-and-agent-failu/
```

**2) As a standalone CLI**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/maskloom-distributional-bias-probing-for-llm-and-agent-failu
python scripts/run.py --help
```

**3) Manual download**

On GitHub, open the `skills/maskloom-distributional-bias-probing-for-llm-and-agent-failu/` folder and download the files, or download the repo ZIP and copy that one folder.

## ⚡ Usage

Full `--help` output:

```text
usage: mask-probe [-h] [--input INPUT] [--output OUTPUT] [--trials TRIALS]
                  [--mask-probability MASK_PROBABILITY] [--seed SEED]
                  [--command-template COMMAND_TEMPLATE] [--selftest]

Run deterministic MaskLoom masking probes for LLM, RAG, or agent selection
failures.

options:
  -h, --help            show this help message and exit
  --input INPUT, -i INPUT
                        Path to probe input JSON.
  --output OUTPUT, -o OUTPUT
                        Write JSON report to this path instead of stdout.
  --trials TRIALS       Number of masking trials to run.
  --mask-probability MASK_PROBABILITY
                        Probability of masking each token span in prompt and
                        candidates.
  --seed SEED           Random seed for deterministic masking.
  --command-template COMMAND_TEMPLATE
                        Optional local command template. Supported
                        placeholders: {prompt}, {masked_prompt},
                        {candidates_json}, {masked_candidates_json},
                        {trial_json}.
  --selftest            Run the built-in sample probe with no API key.
```

## Examples

See the `examples/` folder in this skill (sample input + expected output).

## 🧠 How it works

- Creates randomized masked variants of prompts, retrieved contexts, candidate answers, or tool descriptions.
- Reruns the target model, pipeline, or agent across repeated probe trials.
- Aggregates the observed selections to show whether behavior stays stable or collapses toward specific candidates.
- Estimates which tokens or spans are sensitive by measuring how masking them shifts output behavior.
- Produces JSON-first reports for audits, CI checks, experiment tracking, and review workflows.

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Probe results look noisy or inconsistent. | The target system may be nondeterministic, the probe count may be too low, or the masked spans may be too coarse. | Increase the number of trials, reduce model randomness where possible, and use smaller or more targeted masking units. |
| The report flags many bias-suspect candidates. | The candidate set may contain overlapping evidence, duplicated wording, or formatting differences that create selection artifacts. | Normalize candidate formatting, remove near-duplicates, and rerun the probe to see whether the sensitivity pattern remains. |
| Masking changes the task too much. | Some masked spans may remove essential information rather than isolate misleading cues. | Use narrower masks, preserve task-critical structure, and compare results against an unmasked baseline. |

## FAQ

**Is MaskLoom an evaluation benchmark?**

No. It is a diagnostic toolkit. It helps explain unstable or biased behavior in a target system, but it does not replace task-level accuracy, safety, or reliability evaluation.

**Can it work with agents and tools, not just plain LLM prompts?**

Yes. The command-template execution model is designed to probe local scripts, API wrappers, agent runners, benchmark harnesses, and tool-routing systems.

**What does a selection-distribution report tell me?**

It shows how often the system chooses each candidate, route, tool, answer, or action across masked trials. Large shifts can reveal brittle decision-making or over-reliance on specific cues.

**Does a sensitive token always mean the model is wrong?**

No. A sensitive token may be legitimate evidence. MaskLoom highlights where behavior changes so reviewers can decide whether that sensitivity reflects useful information or a misleading bias.

## ✅ Verification

Passed automated structure / syntax / selftest checks (see `SKILL.md`).

## Uninstall

Delete the skill folder (`~/.claude/skills/maskloom-distributional-bias-probing-for-llm-and-agent-failu/` or `.claude/skills/maskloom-distributional-bias-probing-for-llm-and-agent-failu/`). Nothing else on your system is touched.

## 📜 Versioning

This skill uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## 🤝 Contributing

This is an auto-generated reference skill. Issues and PRs that improve it are welcome.

## License

MIT
