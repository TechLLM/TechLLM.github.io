# RiftGauntlet — Domain-First Agent Robustness Benchmark

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> Expose where agents break—and turn every failure into a reproducible safeguard.

> 🤖 Auto-generated & self-verified skill. A minimal, runnable reference — review before production use.

## What is this?

RiftGauntlet is an open-source benchmark for testing how reliably agents behave when conditions depart from the expected. It evaluates failures caused by domain shift, incomplete context, corrupted observations, tool outages, latency, and reordered events.

Instead of hiding weak spots behind one average score, RiftGauntlet shows which domains and perturbation slices cause an agent or router to collapse. It also measures whether the system recognizes those failures through recorded confidence, abstention, or risk signals.

The resulting failure slices can become deterministic regression fixtures, helping teams reproduce weaknesses and prevent them from returning during later development.

**Who is this for.** RiftGauntlet benefits teams building tool-using agents, routers, parallel agent workflows, and adaptive planning systems—especially researchers, evaluation engineers, and platform teams that need evidence of robustness before deployment.

## ⏱ 30-Second Quick Start

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/riftgauntlet-domain-first-agent-robustness-benchmark
python scripts/run.py --selftest
```

**Expected output:**

```text
{
  "domains": [
    {
      "baseline_samples": 1,
      "baseline_success_rate": 1.0,
      "baseline_successes": 1,
      "domain": "finance",
      "matched_baseline_success_rate": 1.0,
      "perturbed_samples": 2,
      "perturbed_success_rate": 0.0,
      "perturbed_successes": 0,
      "robustness_delta": -1.0,
      "source_domains": [
        "finance"
      ]
    },
    {
      "baseline_samples": 1,
      "baseline_success_rate": 1.0,
      "baseline_successes": 1,
      "domain": "support",
      "matched_baseline_success_rate": 1.0,
      "perturbed_samples": 2,
      "perturbed_success_rate": 0.0,
      "perturbed_successes": 0,
      "robustness_delta": -1.0,
      "source_domains": [
        "support"
      ]
    },
    {
      "baseline_samples": 1,
      "baseline_success_rate": 1.0,
      "baseline_successes": 1,
      "domain": "travel",
      "matched_baseline_success_rate": 1.0,
      "perturbed_samples": 2,
      "perturbed_success_rate": 0.0,
      "perturbed_successes": 0,
      "robustness_delta": -1.0,
      "source_domains": [
        "travel"
      ]
    },
    {
      "baseline_samples": 0,
      "baseline_success_rate": null,
      "baseline_successes": 0,
      "domain": "unknown",
      "matched_baseline_success_rate": 1.0,
      "perturbed_samples": 1,
      "perturbed_success_rate": 1.0,
      "perturbed_successes": 1,
      "robustness_delta": 0.0,
      "source_domains": [
        "finance"
      ]
    }
  ],
  "failure_detection": {
    "auroc_proxy": 0.5,
    "failure_cases": 6,
    "scorable_cases": 7,
    "score_sources": {
      "abstention": 2,
      "confidence": 3,
      "risk_score": 2
    },
    "success_cases": 1
  },
  "schema_version": "1.0",
  "slices": [
    {
      "baseline_success_rate": 1.0,
      "domain": "travel",
      "perturbations": [
        "delay"
      ],
      "robustness_delta": -1.0,
      "samples": 1,
      "scenario": "delayed-result",
      "source_domains": [
        "travel"
      ],
      
… (+3946 chars truncated)
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
mkdir -p ~/.claude/skills/riftgauntlet-domain-first-agent-robustness-benchmark
cp -r /tmp/techllm-skills/skills/riftgauntlet-domain-first-agent-robustness-benchmark/* ~/.claude/skills/riftgauntlet-domain-first-agent-robustness-benchmark/

# Project-local
mkdir -p .claude/skills/riftgauntlet-domain-first-agent-robustness-benchmark
cp -r /tmp/techllm-skills/skills/riftgauntlet-domain-first-agent-robustness-benchmark/* .claude/skills/riftgauntlet-domain-first-agent-robustness-benchmark/
```

**2) As a standalone CLI**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/riftgauntlet-domain-first-agent-robustness-benchmark
python scripts/run.py --help
```

**3) Manual download**

On GitHub, open the `skills/riftgauntlet-domain-first-agent-robustness-benchmark/` folder and download the files, or download the repo ZIP and copy that one folder.

## ⚡ Usage

Full `--help` output:

```text
usage: run.py [-h] [--input INPUT] [--spec SPEC] [--worst-limit WORST_LIMIT]
              [--output OUTPUT] [--fixtures-dir FIXTURES_DIR] [--force]
              [--selftest]

Replay JSONL agent traces under declarative perturbations and report domain-
first robustness metrics. No network or API key is required.

options:
  -h, --help            show this help message and exit
  --input INPUT         path to a JSONL trace file
  --spec SPEC           path to a JSON perturbation specification
  --worst-limit WORST_LIMIT
                        number of worst slices to rank (default: env
                        RIFTGAUNTLET_WORST_LIMIT or 5)
  --output OUTPUT       write the report to this file instead of stdout
  --fixtures-dir FIXTURES_DIR
                        export worst slices as regression fixture JSON files
  --force               allow explicitly requested output or fixture files to
                        be overwritten
  --selftest            run the offline built-in sample and verify stable
                        metrics
```

## Examples

See the `examples/` folder in this skill (sample input + expected output).

## 🧠 How it works

- Replays portable JSONL execution traces without making live model calls.
- Applies declarative perturbations to tool results and observation sequences, including missing, malformed, delayed, duplicated, truncated, and reordered data.
- Groups outcomes by domain and perturbation slice, then compares success rates with the unperturbed baseline.
- Ranks weak slices using performance, sample size, and degradation so consequential failures remain visible.
- Estimates failure-detection quality from recorded confidence, abstention, or risk scores and exports weak slices as deterministic regression fixtures.

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| A perturbation produces no matching cases. | The specification targets events, domains, or observation shapes that do not appear in the supplied traces. | Check that the trace records contain the intended domain labels and event types, then align the perturbation criteria with the recorded structure. |
| Failure-detection results are unavailable or misleading. | The traces lack consistent confidence, abstention, or risk scores, or the score direction differs between records. | Record one clearly defined signal for every evaluated trace and keep its meaning and scale consistent across domains. |
| A worst-performing slice changes between evaluations. | The trace set, perturbation selection, randomization, or slice definition is not stable. | Use fixed inputs and deterministic perturbation settings, and preserve the exact slice definition in the regression fixture. |
| A slice looks severe but contains very few samples. | Its low success rate is based on insufficient evidence. | Review sample counts alongside performance, collect more representative traces, and avoid treating sparse slices as conclusive. |

## FAQ

**Does RiftGauntlet require live model or tool calls?**

No. It replays recorded execution traces and mutates their observations, making evaluations repeatable and suitable for offline use.

**Why report domain-level and slice-level results?**

Aggregate averages can conceal catastrophic failures in uncommon domains or conditions. Slice-level reporting makes those weaknesses visible.

**What does the failure-detection AUROC proxy measure?**

It estimates how well a recorded confidence, abstention, or risk signal separates successful executions from failures across evaluated traces.

**Can it compare agents or routing strategies?**

Yes. Systems evaluated on the same traces and perturbation definitions can be compared by baseline performance, robustness degradation, worst slices, and failure awareness.

**How do regression fixtures help?**

They preserve deterministic examples of observed weaknesses so continuous integration can detect when a domain-specific failure returns.

## ✅ Verification

Passed automated structure / syntax / selftest checks (see `SKILL.md`).

## Uninstall

Delete the skill folder (`~/.claude/skills/riftgauntlet-domain-first-agent-robustness-benchmark/` or `.claude/skills/riftgauntlet-domain-first-agent-robustness-benchmark/`). Nothing else on your system is touched.

## 📜 Versioning

This skill uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## 🤝 Contributing

This is an auto-generated reference skill. Issues and PRs that improve it are welcome.

## License

MIT
