# LedgerSpan — Evidence Ledger for Agentic AI Runs

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> Portable evidence for what agentic AI actually changed, touched, and verified.

> 🤖 Auto-generated & self-verified skill. A minimal, runnable reference — review before production use.

## What is this?

LedgerSpan is a proposed open-source CLI for collecting durable evidence from AI agent runs, LLM tools, and autonomous workflows. It focuses on the observable work behind an answer: changed files, executed commands, tool activity, generated artifacts, touched resources, and completed checks.

This matters because a final response can sound convincing while the workspace tells a different story. The agent may have edited the wrong files, skipped a required verification step, failed to create an expected artifact, or cited resources it never accessed.

LedgerSpan gives reviewers and graders a portable evidence package that can be inspected by humans, stored with benchmark results, attached to CI runs, or consumed by custom evaluation systems without adopting a dedicated benchmark platform.

**Who is this for.** LedgerSpan is for benchmark authors, developer tooling teams, documentation automation maintainers, workspace copilot builders, and AI research groups that need to evaluate real-world side effects instead of only judging final answer text.

## ⏱ 30-Second Quick Start

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/ledgerspan-evidence-ledger-for-agentic-ai-runs
python scripts/run.py --selftest
```

**Expected output:**

_See the `examples/` folder in this skill (sample input + expected output)._

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
mkdir -p ~/.claude/skills/ledgerspan-evidence-ledger-for-agentic-ai-runs
cp -r /tmp/techllm-skills/skills/ledgerspan-evidence-ledger-for-agentic-ai-runs/* ~/.claude/skills/ledgerspan-evidence-ledger-for-agentic-ai-runs/

# Project-local
mkdir -p .claude/skills/ledgerspan-evidence-ledger-for-agentic-ai-runs
cp -r /tmp/techllm-skills/skills/ledgerspan-evidence-ledger-for-agentic-ai-runs/* .claude/skills/ledgerspan-evidence-ledger-for-agentic-ai-runs/
```

**2) As a standalone CLI**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/ledgerspan-evidence-ledger-for-agentic-ai-runs
python scripts/run.py --help
```

**3) Manual download**

On GitHub, open the `skills/ledgerspan-evidence-ledger-for-agentic-ai-runs/` folder and download the files, or download the repo ZIP and copy that one folder.

## ⚡ Usage

Full `--help` output:

_See the `examples/` folder in this skill (sample input + expected output)._

## Examples

See the `examples/` folder in this skill (sample input + expected output).

## 🧠 How it works

- Snapshots the workspace before and after an agent run to record file metadata, timestamps, sizes, and content hashes.
- Classifies file changes so reviewers can see what was created, modified, deleted, renamed, or left unchanged.
- Ingests command logs and tool-call traces to connect workspace changes with the actions that produced them.
- Hashes generated artifacts so reports, datasets, documents, code files, and structured outputs can be identified reliably.
- Emits a portable Markdown or JSON evidence package for review, storage, benchmarking, or downstream grading.

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| The evidence package shows no workspace changes. | The agent may not have modified the workspace, or LedgerSpan may have captured snapshots around the wrong execution window. | Confirm that evidence collection starts before the agent run and finishes only after all expected work has completed. |
| Some tool activity is missing from the report. | The agent harness may not be exporting tool-call traces in a format LedgerSpan can parse. | Enable structured trace export in the harness or provide a compatible JSON trace for LedgerSpan to ingest. |
| Generated artifacts cannot be matched across runs. | The artifact may be regenerated with non-deterministic content, timestamps, or embedded metadata. | Normalize generated outputs where possible and rely on hashes together with file metadata and change classification. |

## FAQ

**Is LedgerSpan a grader?**

Not by itself. LedgerSpan collects and packages evidence. A human reviewer, benchmark harness, CI workflow, or custom grader can then decide whether that evidence satisfies the task.

**Does LedgerSpan replace existing agent harnesses?**

No. It is designed as a lightweight evidence layer around existing harnesses, tools, and workflows.

**Why not just evaluate the final answer?**

Many agent tasks are only successful if the workspace changed correctly. LedgerSpan makes those side effects visible so fluent but incomplete answers are easier to detect.

**Can the output be used in CI or benchmark pipelines?**

Yes. LedgerSpan is intended to emit portable Markdown or JSON evidence packages that can be archived, reviewed, or consumed by automated systems.

## ✅ Verification

Passed automated structure / syntax / selftest checks (see `SKILL.md`).

## Uninstall

Delete the skill folder (`~/.claude/skills/ledgerspan-evidence-ledger-for-agentic-ai-runs/` or `.claude/skills/ledgerspan-evidence-ledger-for-agentic-ai-runs/`). Nothing else on your system is touched.

## 📜 Versioning

This skill uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## 🤝 Contributing

This is an auto-generated reference skill. Issues and PRs that improve it are welcome.

## License

MIT
