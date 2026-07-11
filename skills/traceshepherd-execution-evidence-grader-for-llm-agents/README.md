# TraceShepherd — Execution Evidence Grader for LLM Agents

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> Grade LLM agent work by verifying the evidence it leaves behind.

> 🤖 Auto-generated & self-verified skill. A minimal, runnable reference — review before production use.

## What is this?

TraceShepherd is a local-first grader for LLM agent executions where the result is more than a final chat response. It checks the observable work an agent performed, including retrieved evidence, file changes, generated artifacts, link updates, and final workspace state.

It solves a common evaluation gap: agents can claim they searched, edited, created, or verified something, but ordinary response scoring cannot prove those side effects happened. TraceShepherd compares trace events, filesystem state, manifests, and rule-based requirements to produce a deterministic pass/fail report.

Because it uses local files, deterministic hashing, JSONL traces, and YAML rules, TraceShepherd is well suited to private workflows, repeatable benchmarks, CI checks, and regression testing without relying on external services.

**Who is this for.** TraceShepherd is for teams and individuals evaluating coding agents, research assistants, knowledge-base automations, workflow agents, and benchmark runs where correctness depends on auditable side effects rather than polished prose.

## ⏱ 30-Second Quick Start

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/traceshepherd-execution-evidence-grader-for-llm-agents
python scripts/run.py --selftest
```

**Expected output:**

```text
{
  "errors": [],
  "evidence": {
    "missing_events": [],
    "required_events": [
      {
        "matched": true,
        "matched_event_index": 0,
        "rule": {
          "pattern": "project plan",
          "type": "search"
        }
      },
      {
        "matched": true,
        "matched_event_index": 1,
        "rule": {
          "path": "sources/project-plan.md",
          "type": "read"
        }
      },
      {
        "matched": true,
        "matched_event_index": 2,
        "rule": {
          "path": "docs/agent-report.md",
          "type": "write"
        }
      }
    ]
  },
  "files": [
    {
      "checks": [
        {
          "expected": true,
          "name": "exists",
          "pass": true
        },
        {
          "expected": 40,
          "name": "min_size",
          "pass": true
        },
        {
          "expected": "TraceShepherd demo report",
          "name": "contains",
          "pass": true
        },
        {
          "expected": "Evidence: project plan was read.",
          "name": "contains",
          "pass": true
        },
        {
          "expected": "Result: docs updated\\.",
          "name": "regex",
          "pass": true
        }
      ],
      "exists": true,
      "pass": true,
      "path": "docs/agent-report.md",
      "sha256": "52885658e8b360e25bcdb8f9d14195cc03469363ac7bdbc302630305dc9fabf0",
      "size_bytes": 82
    }
  ],
  "policy": {
    "changed_paths": [
      "docs/agent-report.md"
    ],
    "forbidden_modified_files": [],
    "unexpected_modified_files": []
  },
  "status": "pass",
  "summary": {
    "checks": 10,
    "failed": 0,
    "passed": 10
  },
  "tool": "traceshepherd",
  "version": "0.1.0"
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
mkdir -p ~/.claude/skills/traceshepherd-execution-evidence-grader-for-llm-agents
cp -r /tmp/techllm-skills/skills/traceshepherd-execution-evidence-grader-for-llm-agents/* ~/.claude/skills/traceshepherd-execution-evidence-grader-for-llm-agents/

# Project-local
mkdir -p .claude/skills/traceshepherd-execution-evidence-grader-for-llm-agents
cp -r /tmp/techllm-skills/skills/traceshepherd-execution-evidence-grader-for-llm-agents/* .claude/skills/traceshepherd-execution-evidence-grader-for-llm-agents/
```

**2) As a standalone CLI**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/traceshepherd-execution-evidence-grader-for-llm-agents
python scripts/run.py --help
```

**3) Manual download**

On GitHub, open the `skills/traceshepherd-execution-evidence-grader-for-llm-agents/` folder and download the files, or download the repo ZIP and copy that one folder.

## ⚡ Usage

Full `--help` output:

```text
usage: run.py [-h] [--trace TRACE] [--manifest MANIFEST]
              [--workspace WORKSPACE] [--output OUTPUT] [--selftest]
              [--compact] [--version]

Grade LLM agent execution evidence from local trace JSONL and workspace files.

options:
  -h, --help            show this help message and exit
  --trace TRACE         Path to trace JSONL file.
  --manifest MANIFEST   Path to manifest YAML or JSON file.
  --workspace WORKSPACE
                        Workspace directory to inspect. Defaults to current
                        directory.
  --output OUTPUT       Optional path to write the JSON report.
  --selftest            Run a built-in deterministic sample with no API key or
                        external service.
  --compact             Emit compact one-line JSON.
  --version             show program's version number and exit
```

## Examples

See the `examples/` folder in this skill (sample input + expected output).

## 🧠 How it works

- Reads trace JSONL events to understand what the agent actually searched, opened, edited, wrote, or invoked.
- Compares the final workspace against a declared manifest of expected artifacts, hashes, sizes, and content patterns.
- Applies YAML rule packs that define required evidence, allowed changes, forbidden paths, regex assertions, and audit policies.
- Flags missing evidence, unexpected files, forbidden modifications, and artifacts that do not match the expected state.
- Emits deterministic JSON reports that can be consumed by CI systems, dashboards, and benchmark aggregators.

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| The report says required evidence is missing. | The agent may have completed the visible task but did not produce the trace events required by the rule pack. | Review the rule pack and the trace log together. Either adjust the rule to match the intended workflow or update the agent harness so required searches, reads, edits, or writes are recorded. |
| An expected artifact fails validation. | The file may be missing, too small, unexpectedly changed, or different from the declared hash or content pattern. | Inspect the generated artifact and the manifest expectation. Regenerate the artifact if it is wrong, or update the manifest only when the new state is intentionally correct. |
| Valid work is reported as an unexpected file change. | The allowed path policy may be narrower than the work the agent legitimately performed. | Expand the allowed paths or artifact manifest to include the intended outputs, while keeping unrelated workspace areas forbidden. |

## FAQ

**Does TraceShepherd judge the quality of the final natural-language answer?**

Not primarily. TraceShepherd focuses on execution evidence and final state. It verifies whether the agent did the required observable work and left behind the expected artifacts.

**Can it run in privacy-sensitive environments?**

Yes. TraceShepherd is designed to operate locally using files, hashes, trace logs, and rules, so evaluations do not need to be sent to an external service.

**What kinds of agents can it evaluate?**

It can evaluate agents that perform auditable actions such as searching, reading files, editing code, writing knowledge-base pages, updating links, or producing structured artifacts.

**Why use rule packs instead of only snapshots?**

Snapshots show the final state, but rule packs can require process evidence. For example, they can verify that a required source was read or that only approved areas were modified.

## ✅ Verification

Passed automated structure / syntax / selftest checks (see `SKILL.md`).

## Uninstall

Delete the skill folder (`~/.claude/skills/traceshepherd-execution-evidence-grader-for-llm-agents/` or `.claude/skills/traceshepherd-execution-evidence-grader-for-llm-agents/`). Nothing else on your system is touched.

## 📜 Versioning

This skill uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## 🤝 Contributing

This is an auto-generated reference skill. Issues and PRs that improve it are welcome.

## License

MIT
