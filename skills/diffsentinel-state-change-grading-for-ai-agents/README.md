# DiffSentinel — State-Change Grading for AI Agents

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> Grade agent work by verifying the files and data it actually changed.

> 🤖 Auto-generated & self-verified skill. A minimal, runnable reference — review before production use.

## What is this?

DiffSentinel is a proposed evaluation toolkit for AI agents and automation workflows that perform real work in a workspace. Instead of judging only the final written response, it checks the observable changes left behind after execution.

This matters because a plausible answer is not the same as completed work. An agent may describe a plan, claim success, or summarize edits, but reliable systems need evidence: files created, records updated, citations added, artifacts removed, and task logs written.

DiffSentinel compares the workspace before and after a run, applies expectation rules, and produces a deterministic grading report. The result can be used in CI, benchmark suites, regression tests, and iterative agent development.

**Who is this for.** DiffSentinel is for teams building or evaluating LLM agents, RAG workflows, coding assistants, document-editing agents, wiki-maintenance agents, research assistants, and automation systems where success depends on durable state changes rather than a single natural-language answer.

## ⏱ 30-Second Quick Start

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/diffsentinel-state-change-grading-for-ai-agents
python scripts/run.py --selftest
```

**Expected output:**

```text
{
  "pass": true,
  "score": 1.0,
  "earned_points": 13,
  "max_score": 13,
  "summary": {
    "passed": 13,
    "failed": 0,
    "warnings": 0
  },
  "checks": [
    {
      "id": "required_files:report.md",
      "kind": "required_files",
      "target": "report.md",
      "status": "pass",
      "detail": "File exists in after snapshot."
    },
    {
      "id": "created_files:report.md",
      "kind": "created_files",
      "target": "report.md",
      "status": "pass",
      "detail": "File was created.",
      "expected": "absent before and present after",
      "observed": true
    },
    {
      "id": "created_files:logs/task.log",
      "kind": "created_files",
      "target": "logs/task.log",
      "status": "pass",
      "detail": "File was created.",
      "expected": "absent before and present after",
      "observed": true
    },
    {
      "id": "deleted_files:draft.txt",
      "kind": "deleted_files",
      "target": "draft.txt",
      "status": "pass",
      "detail": "File was deleted.",
      "expected": "present before and absent after",
      "observed": true
    },
    {
      "id": "modified_files:data.json",
      "kind": "modified_files",
      "target": "data.json",
      "status": "pass",
      "detail": "File content changed.",
      "expected": true,
      "observed": true
    },
    {
      "id": "forbidden_changes:notes.md",
      "kind": "forbidden_changes",
      "target": "notes.md",
      "status": "pass",
      "detail": "File did not change.",
      "expected": false,
      "observed": false
    },
    {
      "id": "content_contains:report.md contains 'Summary: Work completed.'",
      "kind": "content_contains",
      "target": "report.md contains 'Summary: Work completed.'",
      "status": "pass",
      "detail": "Required string found.",
      "expected": "Summary: Work completed."
    },
    {
      "id": "content_contains:report.md contains '[source:A]'",
      "kind": "content_contains",
      "target": "report.md contai
… (+1781 chars truncated)
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
mkdir -p ~/.claude/skills/diffsentinel-state-change-grading-for-ai-agents
cp -r /tmp/techllm-skills/skills/diffsentinel-state-change-grading-for-ai-agents/* ~/.claude/skills/diffsentinel-state-change-grading-for-ai-agents/

# Project-local
mkdir -p .claude/skills/diffsentinel-state-change-grading-for-ai-agents
cp -r /tmp/techllm-skills/skills/diffsentinel-state-change-grading-for-ai-agents/* .claude/skills/diffsentinel-state-change-grading-for-ai-agents/
```

**2) As a standalone CLI**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/diffsentinel-state-change-grading-for-ai-agents
python scripts/run.py --help
```

**3) Manual download**

On GitHub, open the `skills/diffsentinel-state-change-grading-for-ai-agents/` folder and download the files, or download the repo ZIP and copy that one folder.

## ⚡ Usage

Full `--help` output:

```text
usage: run.py [-h] [--before BEFORE] [--after AFTER] [--expect EXPECT]
              [--output OUTPUT] [--threshold THRESHOLD] [--selftest]

DiffSentinel grades observable before-and-after workspace state changes.

options:
  -h, --help            show this help message and exit
  --before BEFORE       Directory snapshot before the agent ran
  --after AFTER         Directory snapshot after the agent ran
  --expect EXPECT       Expectation YAML or JSON file. Defaults to
                        DIFFSENTINEL_EXPECTATIONS.
  --output OUTPUT       Optional report output path. Defaults to
                        DIFFSENTINEL_OUTPUT.
  --threshold THRESHOLD
                        Minimum score needed to pass. Defaults to
                        DIFFSENTINEL_SCORE_THRESHOLD or 1.0.
  --selftest            Run built-in sample data with no API key and print the
                        report
```

## Examples

See the `examples/` folder in this skill (sample input + expected output).

## 🧠 How it works

- Captures or receives before-and-after workspace snapshots for a completed agent run.
- Reads expectation rules that define required files, deleted files, modified files, forbidden changes, citations, task logs, and generated artifacts.
- Checks file contents for required text, citation markers, and other evidence that the requested work was completed.
- Validates structured artifacts such as JSON records for expected field additions, removals, and value changes.
- Emits a machine-readable grading report with pass, fail, warning, and score details for automated evaluation pipelines.

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| The grading report fails even though the agent said the task was complete. | DiffSentinel grades observable state changes, not the agent's final message. The expected files, edits, citations, or structured updates were not present in the after-state. | Update the agent workflow so it writes the required artifacts, or adjust the expectation rules if they no longer match the intended task outcome. |
| A file is reported as changed when it should not be part of the evaluation. | The workspace comparison includes incidental or unrelated modifications that are not covered by the expectation rules. | Narrow the evaluated workspace, add explicit allowances for expected auxiliary files, or prevent the workflow from writing unrelated artifacts. |
| Structured validation fails for a generated JSON artifact. | The artifact exists, but its fields, values, or removals do not match the expected state-change rules. | Check that the agent writes the required structure consistently and that the expectation rules describe the intended final schema and values. |

## FAQ

**How is DiffSentinel different from grading the final answer?**

It evaluates the durable effects of an agent run. A final answer can be fluent but inaccurate; DiffSentinel checks whether the expected files, content, citations, logs, and structured updates actually exist after execution.

**What kinds of tasks is this best suited for?**

It is best for workflow benchmarks where correctness is a set of expected changes, such as editing documents, maintaining wikis, updating JSON records, creating research artifacts, modifying code, or producing cited outputs.

**Can DiffSentinel be used in CI?**

Yes. The grading model is designed to produce deterministic, machine-readable reports and CI-friendly pass or fail outcomes for benchmark and regression runs.

**Does DiffSentinel decide whether prose is high quality?**

Not by itself. Its core purpose is state-change verification. It can confirm that required text or citations appear, but qualitative writing assessment can be layered on separately.

## ✅ Verification

Passed automated structure / syntax / selftest checks (see `SKILL.md`).

## Uninstall

Delete the skill folder (`~/.claude/skills/diffsentinel-state-change-grading-for-ai-agents/` or `.claude/skills/diffsentinel-state-change-grading-for-ai-agents/`). Nothing else on your system is touched.

## 📜 Versioning

This skill uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## 🤝 Contributing

This is an auto-generated reference skill. Issues and PRs that improve it are welcome.

## License

MIT
