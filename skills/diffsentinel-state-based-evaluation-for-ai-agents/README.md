# DiffSentinel — State-Based Evaluation for AI Agents

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> Evaluate AI agents by what they changed, not what they claimed.

> 🤖 Auto-generated & self-verified skill. A minimal, runnable reference — review before production use.

## What is this?

DiffSentinel is a proposed open-source evaluation toolkit for AI agents that work inside real workspaces. Instead of judging an agent by its final message, it examines the observable changes the agent made: what was created, edited, deleted, linked, referenced, accessed, or left untouched.

This solves a common problem in agent evaluation: polished summaries can hide incomplete work, missing citations, unsafe access, or broken structure. DiffSentinel treats the workspace diff and tool trace as the source of truth, making evaluation closer to code review, audit logging, and reproducible verification.

The result is a structured report that can be used by CI systems, benchmark harnesses, regression tests, dashboards, or human reviewers.

**Who is this for.** DiffSentinel is for teams building, testing, or auditing AI agents that operate in repositories, documentation systems, knowledge bases, and other structured workspaces where the quality of the final state matters more than the wording of the final response.

## ⏱ 30-Second Quick Start

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/diffsentinel-state-based-evaluation-for-ai-agents
python scripts/run.py --selftest
```

**Expected output:**

```text
{"evidence": {"changed_paths": ["docs/faq.md", "docs/guide.md"], "policy": {"allow_shell_without_approval": true, "fail_below_score": 80, "forbidden_path_patterns": ["../", "~", ".env", "secrets/", "private/"], "protected_paths": []}}, "findings": [], "graph": {"added_links": [{"source": "docs/faq.md", "target": "docs/guide.md"}], "orphaned_nodes": [], "removed_links": [], "unresolved_references": []}, "schema_version": "diffsentinel-report-v1", "state_diff": {"created": ["docs/faq.md"], "deleted": [], "modified": ["docs/guide.md"], "renamed": [], "unchanged": ["docs/index.md"]}, "summary": {"counts": {"created": 1, "deleted": 0, "modified": 1, "renamed": 0, "unchanged": 1, "violations": 0}, "graph_score": 100, "overall_score": 100, "state_score": 100, "status": "pass", "trace_score": 100}, "trace": {"actions": {"read": 1, "shell": 1, "write": 2}, "events": 4, "external_accesses": [], "paths_accessed": ["docs/faq.md", "docs/guide.md", "docs/index.md"], "shell_commands": ["python scripts/test.py"], "tools": {"read_file": 1, "shell": 1, "write_file": 2}}, "violations": []}
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
mkdir -p ~/.claude/skills/diffsentinel-state-based-evaluation-for-ai-agents
cp -r /tmp/techllm-skills/skills/diffsentinel-state-based-evaluation-for-ai-agents/* ~/.claude/skills/diffsentinel-state-based-evaluation-for-ai-agents/

# Project-local
mkdir -p .claude/skills/diffsentinel-state-based-evaluation-for-ai-agents
cp -r /tmp/techllm-skills/skills/diffsentinel-state-based-evaluation-for-ai-agents/* .claude/skills/diffsentinel-state-based-evaluation-for-ai-agents/
```

**2) As a standalone CLI**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/diffsentinel-state-based-evaluation-for-ai-agents
python scripts/run.py --help
```

**3) Manual download**

On GitHub, open the `skills/diffsentinel-state-based-evaluation-for-ai-agents/` folder and download the files, or download the repo ZIP and copy that one folder.

## ⚡ Usage

Full `--help` output:

```text
usage: run.py [-h] [--before BEFORE] [--after AFTER] [--trace TRACE]
              [--config CONFIG] [--output OUTPUT] [--pretty] [--selftest]

Evaluate AI agent workspace state diffs and JSONL tool traces.

options:
  -h, --help       show this help message and exit
  --before BEFORE  Before snapshot JSON file or directory
  --after AFTER    After snapshot JSON file or directory
  --trace TRACE    JSONL tool trace file
  --config CONFIG  Optional JSON config file
  --output OUTPUT  Write report JSON to this file
  --pretty         Print indented JSON output
  --selftest       Run built-in sample data with no API key or external
                   service
```

## Examples

See the `examples/` folder in this skill (sample input + expected output).

## 🧠 How it works

- Compares a before snapshot and an after snapshot to identify created, modified, deleted, renamed, and unchanged files.
- Analyzes a JSONL tool trace to inspect reads, writes, API calls, shell activity, and external accesses.
- Checks workspace policies such as forbidden areas, missing approvals, unsafe writes, and unexpected side effects.
- Evaluates graph and reference integrity, including added links, removed links, orphaned nodes, unresolved references, and citation gaps.
- Produces deterministic JSON findings with scores, violations, evidence, severities, and machine-readable results.

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| The report shows missing evidence for an expected change. | The workspace changed, but the available trace or snapshots do not contain enough information to prove why the change happened. | Ensure the evaluation includes complete before and after state data, plus the full tool trace for the agent run. |
| A task passes by summary but fails in DiffSentinel. | The agent’s final response described success, but the workspace state did not contain the required changes or preserved references. | Review the reported findings and update the task criteria or agent behavior so success is reflected in the actual workspace state. |
| Policy violations appear for files that seem unrelated to the task. | The agent accessed or modified areas outside the expected task boundary. | Tighten the allowed workspace scope, clarify the task boundary, or require explicit approval for broader access. |

## FAQ

**Why evaluate state instead of final text?**

Final text is easy for an agent to make sound correct. State-based evaluation checks whether the promised work actually happened and whether it respected the workspace rules.

**Can DiffSentinel be used in CI?**

Yes. Its structured JSON output is designed for automated pipelines, dashboards, benchmark suites, and long-term regression tracking.

**Is this only for code agents?**

No. It is also useful for documentation agents, knowledge-base agents, research assistants, and any agent that changes structured workspace content.

**What makes this different from a normal diff tool?**

A normal diff shows what changed. DiffSentinel interprets those changes against task criteria, tool activity, workspace policy, graph integrity, and required evidence.

## ✅ Verification

Passed automated structure / syntax / selftest checks (see `SKILL.md`).

## Uninstall

Delete the skill folder (`~/.claude/skills/diffsentinel-state-based-evaluation-for-ai-agents/` or `.claude/skills/diffsentinel-state-based-evaluation-for-ai-agents/`). Nothing else on your system is touched.

## 📜 Versioning

This skill uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## 🤝 Contributing

This is an auto-generated reference skill. Issues and PRs that improve it are welcome.

## License

MIT
