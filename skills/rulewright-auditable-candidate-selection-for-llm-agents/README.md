# Rulewright — Auditable Candidate Selection for LLM Agents

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> Make LLM candidate selection explicit, inspectable, and reproducible.

> 🤖 Auto-generated & self-verified skill. A minimal, runnable reference — review before production use.

## What is this?

Rulewright is a proposed library and CLI for making LLM candidate selection easier to understand and audit. It helps replace silent model choices with a visible selection process that can be inspected after the fact.

Instead of asking a model to choose the best document, tool, answer, or action in one opaque step, Rulewright separates the work into two passes. First, it creates a structured comparison policy. Then it applies that policy to each candidate and returns machine-readable selections.

This gives teams a durable decision trace without requiring them to store private reasoning text. It is useful when agent behavior needs to be debugged, compared across model versions, replayed, or explained later.

**Who is this for.** Rulewright is for teams building retrieval systems, tool-routing agents, answer evaluators, dataset curation pipelines, and other LLM workflows where candidate selection needs to be explainable, repeatable, and safe to review.

## ⏱ 30-Second Quick Start

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/rulewright-auditable-candidate-selection-for-llm-agents
python scripts/run.py --selftest
```

**Expected output:**

```text
{
  "selected_ids": [
    "doc-rules-first"
  ],
  "top_score": 0.775
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
mkdir -p ~/.claude/skills/rulewright-auditable-candidate-selection-for-llm-agents
cp -r /tmp/techllm-skills/skills/rulewright-auditable-candidate-selection-for-llm-agents/* ~/.claude/skills/rulewright-auditable-candidate-selection-for-llm-agents/

# Project-local
mkdir -p .claude/skills/rulewright-auditable-candidate-selection-for-llm-agents
cp -r /tmp/techllm-skills/skills/rulewright-auditable-candidate-selection-for-llm-agents/* .claude/skills/rulewright-auditable-candidate-selection-for-llm-agents/
```

**2) As a standalone CLI**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/rulewright-auditable-candidate-selection-for-llm-agents
python scripts/run.py --help
```

**3) Manual download**

On GitHub, open the `skills/rulewright-auditable-candidate-selection-for-llm-agents/` folder and download the files, or download the repo ZIP and copy that one folder.

## ⚡ Usage

Full `--help` output:

```text
usage: run.py [-h] [--input INPUT] [--rules-in RULES_IN]
              [--rules-out RULES_OUT] [--matrix-out MATRIX_OUT]
              [--selected-out SELECTED_OUT] [--selftest]

Generate auditable candidate-selection artifacts for LLM agents.

options:
  -h, --help            show this help message and exit
  --input INPUT         JSON file containing query and candidates.
  --rules-in RULES_IN   Replay with an existing rules.yaml file.
  --rules-out RULES_OUT
                        Write generated rules.yaml to this path.
  --matrix-out MATRIX_OUT
                        Write decision_matrix.json to this path.
  --selected-out SELECTED_OUT
                        Write selected_ids.json to this path.
  --selftest            Run the built-in sample without external services.
```

## Examples

See the `examples/` folder in this skill (sample input + expected output).

## 🧠 How it works

- A user query and candidate set are provided as the selection context.
- Rulewright generates an explicit comparison policy with dimensions, weights, constraints, and rejection conditions.
- Each candidate is evaluated against the saved policy in a separate decision pass.
- The result is a structured decision matrix with scores, evidence, and pass/fail judgments.
- Selected candidate identifiers are returned in a machine-readable form for downstream systems.

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Selections seem inconsistent across runs. | The comparison policy may be regenerated each time, allowing the model to change the criteria before scoring. | Use a saved rule artifact for replay so candidates are evaluated against the same policy. |
| A candidate with a high score is still rejected. | The policy may include hard constraints or rejection conditions that override weighted scoring. | Inspect the rule artifact and decision matrix to see which condition caused the rejection. |
| The decision trace is hard to interpret. | The generated policy may be too broad, vague, or missing domain-specific criteria. | Refine the selection context so the rule generation pass has clearer expectations and constraints. |

## FAQ

**Why split rule generation from candidate scoring?**

Separating the steps makes the selection criteria visible before they are applied. That makes it easier to debug unexpected choices, compare behavior across models, and replay decisions later.

**Does Rulewright store model reasoning?**

No. The goal is to preserve structured artifacts such as rules, scores, evidence references, and selected identifiers, rather than private chain-of-thought text.

**Can the same rules be reused?**

Yes. Saved rules can be used to evaluate the same candidates again or to score a changed candidate set under the same policy.

**What kinds of candidates can it rank?**

Rulewright is designed for documents, tools, generated answers, proposed actions, dataset records, or any candidate objects that can be represented with structured metadata and content.

## ✅ Verification

Passed automated structure / syntax / selftest checks (see `SKILL.md`).

## Uninstall

Delete the skill folder (`~/.claude/skills/rulewright-auditable-candidate-selection-for-llm-agents/` or `.claude/skills/rulewright-auditable-candidate-selection-for-llm-agents/`). Nothing else on your system is touched.

## 📜 Versioning

This skill uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## 🤝 Contributing

This is an auto-generated reference skill. Issues and PRs that improve it are welcome.

## License

MIT
