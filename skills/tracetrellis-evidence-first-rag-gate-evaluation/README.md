# TraceTrellis — Evidence-First RAG Gate Evaluation

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> Evaluate RAG gates by checking evidence, not just answers.

> 🤖 Auto-generated & self-verified skill. A minimal, runnable reference — review before production use.

## What is this?

TraceTrellis is a proposed open-source evaluation toolkit for testing whether RAG systems route the right evidence through their pipelines. Instead of judging only the final response, it inspects the execution trail behind that response: retrieval traces, selected documents, action logs, changed artifacts, and service-level outcomes.

This matters because many RAG evaluations reward plausible text even when the system used the wrong sources, skipped required evidence, or let unsupported context pass through a relevance gate. TraceTrellis moves the target from answer polish to observable evidence handling, so failures become easier to diagnose and reproduce.

The toolkit is designed around an offline CLI workflow that produces structured retrieval, action, and data-accuracy scores with failure explanations. Optional LLM judge results can be added as another signal, but deterministic evidence checks remain the core evaluation layer.

**Who is this for.** TraceTrellis is for teams building RAG applications, agentic retrieval systems, relevance gates, evidence routers, and benchmark suites who need repeatable evaluations that work in CI, offline environments, and privacy-sensitive settings.

## ⏱ 30-Second Quick Start

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/tracetrellis-evidence-first-rag-gate-evaluation
python scripts/run.py --selftest
```

**Expected output:**

```text
{
  "tool": "rag-evidence-grader",
  "version": "0.1.0",
  "summary": {
    "cases": 1,
    "passed": 1,
    "failed": 0,
    "pass_rate": 1.0,
    "average_scores": {
      "retrieval": 1.0,
      "action": 1.0,
      "data_accuracy": 1.0,
      "overall": 1.0
    }
  },
  "cases": [
    {
      "run_id": "refund-window",
      "passed": true,
      "scores": {
        "retrieval": 1.0,
        "action": 1.0,
        "data_accuracy": 1.0,
        "overall": 1.0
      },
      "documents": {
        "selected": [
          "policy/refunds-2026",
          "faq/refunds"
        ],
        "required_found": [
          "policy/refunds-2026"
        ],
        "required_missing": [],
        "optional_found": [
          "faq/refunds"
        ],
        "forbidden_found": []
      },
      "actions": {
        "observed": [
          {
            "type": "retrieve",
            "target": "policy/refunds-2026"
          },
          {
            "type": "cite",
            "target": "policy/refunds-2026"
          }
        ],
        "required_found": [
          {
            "type": "retrieve",
            "target": "policy/refunds-2026"
          },
          {
            "type": "cite",
            "target": "policy/refunds-2026"
          }
        ],
        "required_missing": []
      },
      "facts": {
        "matched": {
          "refund_window_days": 30,
          "region": "US"
        },
        "mismatched": {},
        "missing": []
      },
      "answer": null,
      "llm_judge": null,
      "failures": []
    }
  ]
}
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
mkdir -p ~/.claude/skills/tracetrellis-evidence-first-rag-gate-evaluation
cp -r /tmp/techllm-skills/skills/tracetrellis-evidence-first-rag-gate-evaluation/* ~/.claude/skills/tracetrellis-evidence-first-rag-gate-evaluation/

# Project-local
mkdir -p .claude/skills/tracetrellis-evidence-first-rag-gate-evaluation
cp -r /tmp/techllm-skills/skills/tracetrellis-evidence-first-rag-gate-evaluation/* .claude/skills/tracetrellis-evidence-first-rag-gate-evaluation/
```

**2) As a standalone CLI**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/tracetrellis-evidence-first-rag-gate-evaluation
python scripts/run.py --help
```

**3) Manual download**

On GitHub, open the `skills/tracetrellis-evidence-first-rag-gate-evaluation/` folder and download the files, or download the repo ZIP and copy that one folder.

## ⚡ Usage

Full `--help` output:

```text
usage: rag-evidence-grader [-h] [--traces TRACES] [--manifest MANIFEST]
                           [--answers ANSWERS]
                           [--llm-judge-json LLM_JUDGE_JSON]
                           [--threshold THRESHOLD] [--format {json,csv}]
                           [--output OUTPUT] [--selftest] [--version]

Offline evidence-first grader for RAG retrieval gates and traces.

options:
  -h, --help            show this help message and exit
  --traces TRACES       Path to JSONL trace records.
  --manifest MANIFEST   Path to expected evidence manifest JSON.
  --answers ANSWERS     Optional JSON or JSONL final-answer records.
  --llm-judge-json LLM_JUDGE_JSON
                        Optional JSON or JSONL judge records; can also use
                        TRACE_TRELLIS_LLM_JUDGE_PATH.
  --threshold THRESHOLD
                        Overall pass threshold from 0 to 1. Defaults to
                        RAG_EVIDENCE_GRADER_THRESHOLD or 0.8.
  --format {json,csv}   Output format. Defaults to json.
  --output OUTPUT       Optional output file path.
  --selftest            Run the built-in offline sample with no API key.
  --version             show program's version number and exit
```

## Examples

See the `examples/` folder in this skill (sample input + expected output).

## 🧠 How it works

- Reads standard JSONL traces produced by RAG or agentic retrieval runs.
- Compares retrieved and selected evidence against an expected evidence manifest.
- Scores retrieval behavior, downstream actions, and data accuracy as separate channels.
- Flags required, optional, and forbidden evidence handling failures with explanations.
- Allows optional LLM judge outputs to be merged without replacing deterministic checks.

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| A run scores poorly even though the final answer looks correct. | The answer may be plausible, but the trace shows missing required evidence, unsupported context, or incorrect document selection. | Review the failure explanations and update the retrieval gate, evidence manifest, or trace instrumentation so the required evidence is observable. |
| Scores vary across domains or corpora. | The relevance gate may be tuned to one document structure, vocabulary, or evidence density pattern. | Use domain-balanced evaluation sets and compare score channels by corpus to identify where retrieval policy changes are needed. |
| Action or data-accuracy scores are incomplete. | The trace may include retrieval events but omit action logs, artifact changes, or structured outcome data. | Extend instrumentation so downstream actions and produced artifacts are captured in the trace. |

## FAQ

**Does TraceTrellis require an LLM judge?**

No. Its core scoring is deterministic and can run fully offline. LLM judge outputs are optional and treated as an additional signal.

**What makes this different from final-answer evaluation?**

Final-answer evaluation asks whether the response sounds right. TraceTrellis asks whether the system selected, routed, and used the right evidence to produce it.

**Can it be used in CI?**

Yes. The design favors JSONL input, structured JSON or CSV output, deterministic scoring, and failure explanations that fit regression testing workflows.

**What kinds of RAG systems is it meant for?**

It is especially useful for relevance gates, Gate2-style filters, cross-domain retrieval policies, agentic retrieval pipelines, and evidence-routing layers.

## ✅ Verification

Passed automated structure / syntax / selftest checks (see `SKILL.md`).

## Uninstall

Delete the skill folder (`~/.claude/skills/tracetrellis-evidence-first-rag-gate-evaluation/` or `.claude/skills/tracetrellis-evidence-first-rag-gate-evaluation/`). Nothing else on your system is touched.

## 📜 Versioning

This skill uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## 🤝 Contributing

This is an auto-generated reference skill. Issues and PRs that improve it are welcome.

## License

MIT
