# Tracewright — Execution-Evidence Grader Scaffolding for AI Agents

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> Deterministic execution-evidence graders for agent workflows.

> 🤖 Auto-generated & self-verified skill. A minimal, runnable reference — review before production use.

## What is this?

Tracewright is a proposed open-source CLI for scaffolding graders that evaluate how an AI agent completed a task, not just what answer it returned. It focuses on execution evidence: files, diffs, tool traces, logs, and final output.

This helps teams turn agent tasks into repeatable checks. Instead of writing a custom evaluator from scratch, a task author describes the expected evidence in a compact YAML or JSON specification, and Tracewright generates a runnable Python grader with sample fixtures.

Tracewright complements model-based judging by adding deterministic checks around the artifacts an agent leaves behind. It is meant for practical development, documentation, data, and workspace automation tasks where auditability matters.

**Who is this for.** Tracewright is for maintainers, benchmark authors, agent-platform teams, and developer-tool builders who need consistent grading for real agent work across local harnesses, regression suites, CI, or internal evaluations.

## ⏱ 30-Second Quick Start

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/tracewright-execution-evidence-grader-scaffolding-for-ai-age
python scripts/run.py --selftest
```

**Expected output:**

```text
{
  "task_id": "sample-agent-edit",
  "passed": true,
  "score": 1.0,
  "summary": {
    "passed": 13,
    "failed": 0,
    "total": 13
  },
  "checks": [
    {
      "id": "file.required:src/feature.py",
      "category": "files",
      "passed": true,
      "message": "Required file exists: src/feature.py"
    },
    {
      "id": "file.forbidden:secrets.txt",
      "category": "files",
      "passed": true,
      "message": "Forbidden file absent: secrets.txt"
    },
    {
      "id": "edit.expected:src/feature.py",
      "category": "diff",
      "passed": true,
      "message": "Expected edit observed: src/feature.py"
    },
    {
      "id": "edit.forbidden:config/prod.env",
      "category": "diff",
      "passed": true,
      "message": "Forbidden edit absent: config/prod.env"
    },
    {
      "id": "trace.required:1",
      "category": "trace",
      "passed": true,
      "message": "Required trace event observed: {'type': 'read', 'path': 'src/feature.py'}"
    },
    {
      "id": "trace.required:2",
      "category": "trace",
      "passed": true,
      "message": "Required trace event observed: {'type': 'write', 'path': 'src/feature.py'}"
    },
    {
      "id": "trace.required:3",
      "category": "trace",
      "passed": true,
      "message": "Required trace event observed: {'type': 'command', 'pattern': 'python\\\\s+scripts/test.py'}"
    },
    {
      "id": "trace.forbidden:1",
      "category": "trace",
      "passed": true,
      "message": "Forbidden trace event absent: {'type': 'api_call', 'pattern': 'production'}"
    },
    {
      "id": "diff.required_pattern:1",
      "category": "diff",
      "passed": true,
      "message": "Required diff pattern matched: \\+def calculate_total"
    },
    {
      "id": "diff.forbidden_pattern:1",
      "category": "diff",
      "passed": true,
      "message": "Forbidden diff pattern absent: API_KEY|password"
    },
    {
      "id": "output.must_contain:1",
      "category": "output",
      "passed"
… (+413 chars truncated)
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
mkdir -p ~/.claude/skills/tracewright-execution-evidence-grader-scaffolding-for-ai-age
cp -r /tmp/techllm-skills/skills/tracewright-execution-evidence-grader-scaffolding-for-ai-age/* ~/.claude/skills/tracewright-execution-evidence-grader-scaffolding-for-ai-age/

# Project-local
mkdir -p .claude/skills/tracewright-execution-evidence-grader-scaffolding-for-ai-age
cp -r /tmp/techllm-skills/skills/tracewright-execution-evidence-grader-scaffolding-for-ai-age/* .claude/skills/tracewright-execution-evidence-grader-scaffolding-for-ai-age/
```

**2) As a standalone CLI**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/tracewright-execution-evidence-grader-scaffolding-for-ai-age
python scripts/run.py --help
```

**3) Manual download**

On GitHub, open the `skills/tracewright-execution-evidence-grader-scaffolding-for-ai-age/` folder and download the files, or download the repo ZIP and copy that one folder.

## ⚡ Usage

Full `--help` output:

```text
usage: run.py [-h] [--selftest] [--spec SPEC] [--workspace WORKSPACE]
              [--trace TRACE] [--diff DIFF] [--output OUTPUT] [--audit AUDIT]
              [--scaffold] [--out OUT] [--format {json}]

Grade execution evidence or scaffold a deterministic Tracewright grader.

options:
  -h, --help            show this help message and exit
  --selftest            Run built-in sample data with no API key.
  --spec SPEC           Path to a JSON or simple YAML Tracewright spec. Can
                        also be set with TRACEWRIGHT_SPEC.
  --workspace WORKSPACE
                        Workspace directory after the agent run.
  --trace TRACE         JSONL tool trace file.
  --diff DIFF           Unified diff file.
  --output OUTPUT       Final answer or task output text file.
  --audit AUDIT         Audit log text file.
  --scaffold            Generate a standalone grader and sample fixtures.
  --out OUT             Output directory for --scaffold.
  --format {json}       Output format. TRACEWRIGHT_OUTPUT_FORMAT may also be
                        used.
```

## Examples

See the `examples/` folder in this skill (sample input + expected output).

## 🧠 How it works

- A task author describes expected execution evidence in a compact YAML or JSON specification.
- Tracewright scaffolds a Python grader that checks workspace state, tool traces, diffs, logs, and final output.
- The generated grader can verify required files, expected edits, forbidden modifications, required tool activity, and prohibited patterns.
- Sample passing, failing, and edge-case fixtures give maintainers a starting point for adapting the grader to their environment.
- Teams can use the grader alongside model-based evaluation to catch missing evidence, unsafe side effects, and unverifiable task completion.

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| A grader fails even though the final answer looks correct. | Tracewright grades execution evidence, so the agent may have produced acceptable text without inspecting required files, making expected edits, or leaving the required audit trail. | Review the task specification and the captured artifacts. Either update the agent workflow to produce the required evidence or revise the specification if the evidence requirement was too strict. |
| A trace check does not match the captured tool activity. | The trace format, event names, or recorded fields may differ from what the specification expects. | Align the specification with the actual structured trace schema, and keep trace assertions focused on stable evidence rather than incidental formatting. |
| Diff-pattern checks are noisy or brittle. | Regular expressions may be too broad, too narrow, or tied to formatting that changes between runs. | Prefer patterns that capture meaningful behavioral changes, and separate required edits from prohibited side effects so failures are easier to diagnose. |

## FAQ

**Does Tracewright replace human or model-based judging?**

No. Tracewright is designed to complement those approaches with deterministic checks over execution artifacts. It helps answer whether the agent followed an acceptable process and produced verifiable evidence.

**What kinds of tasks can Tracewright grade?**

It is intended for agent tasks that leave inspectable artifacts, such as code changes, documentation edits, data transformations, workspace automation, API interactions, and audited command or tool usage.

**Why generate a grader instead of using one generic evaluator?**

Agent tasks often have task-specific evidence requirements. Generated graders let each task define its own expected files, allowed changes, forbidden side effects, trace requirements, and output assertions while still sharing a common structure.

**Can teams adapt the generated grader?**

Yes. The scaffold is meant to be readable and editable, so maintainers can extend checks, integrate with their harness, or tune fixtures for CI and benchmark workflows.

## ✅ Verification

Passed automated structure / syntax / selftest checks (see `SKILL.md`).

## Uninstall

Delete the skill folder (`~/.claude/skills/tracewright-execution-evidence-grader-scaffolding-for-ai-age/` or `.claude/skills/tracewright-execution-evidence-grader-scaffolding-for-ai-age/`). Nothing else on your system is touched.

## 📜 Versioning

This skill uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## 🤝 Contributing

This is an auto-generated reference skill. Issues and PRs that improve it are welcome.

## License

MIT
