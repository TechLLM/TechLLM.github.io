# SurfacePilot — Failure-Surface Routing Profiler for LLM Agents

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> Profile where LLM agents fail, then turn evidence into better routing policy.

> 🤖 Auto-generated & self-verified skill. A minimal, runnable reference — review before production use.

## What is this?

SurfacePilot is a proposed open-source CLI for evaluating how well LLM and agent systems route work across models, tools, and safeguards. It focuses on execution evidence instead of judging a router only by whether the final answer looked correct.

The project treats routing as a failure-surface classification problem. A task may fail because retrieval was stale, a citation could not be supported, an API call was malformed, a file edit was risky, a calculation was unreliable, or an external state change needed stronger validation.

SurfacePilot helps teams turn those failures into structured insight. It ingests trace data and task metadata, builds pass/fail views by execution surface, detects repeated failure patterns, and produces routing policy output that can inform model choice, tool choice, fallbacks, guardrails, escalation, and evaluation coverage.

**Who is this for.** SurfacePilot is for engineers, evaluation teams, AI platform teams, and agent developers who need to understand why routing decisions fail in real systems and how to make those decisions safer, more reliable, and easier to test.

## ⏱ 30-Second Quick Start

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/surfacepilot-failure-surface-routing-profiler-for-llm-agents
python scripts/run.py --selftest
```

**Expected output:**

```text
summary:
  events: 5
  passed: 1
  failed: 4
  failure_rate: 0.8
  surfaces:
    api_call:
      events: 1
      passed: 0
      failed: 1
      fail_rate: 1.0
    citation:
      events: 1
      passed: 0
      failed: 1
      fail_rate: 1.0
    file_edit:
      events: 1
      passed: 0
      failed: 1
      fail_rate: 1.0
    retrieval:
      events: 2
      passed: 1
      failed: 1
      fail_rate: 0.5
matrix:
  - task_type: "code_edit"
    model: "small-router"
    route: "edit_direct"
    tool: "filesystem"
    surface: "file_edit"
    signal: "unsafe_edit"
    events: 1
    passed: 0
    failed: 1
    fail_rate: 1.0
  - task_type: "ops"
    model: "small-router"
    route: "api_direct"
    tool: "billing_api"
    surface: "api_call"
    signal: "malformed_api_call"
    events: 1
    passed: 0
    failed: 1
    fail_rate: 1.0
  - task_type: "support_qa"
    model: "large-router"
    route: "rag_verified"
    tool: "retriever"
    surface: "retrieval"
    signal: "fresh_retrieval"
    events: 1
    passed: 1
    failed: 0
    fail_rate: 0.0
  - task_type: "support_qa"
    model: "small-router"
    route: "rag_fast"
    tool: "citation_checker"
    surface: "citation"
    signal: "unsupported_citation"
    events: 1
    passed: 0
    failed: 1
    fail_rate: 1.0
  - task_type: "support_qa"
    model: "small-router"
    route: "rag_fast"
    tool: "retriever"
    surface: "retrieval"
    signal: "stale_retrieval"
    events: 1
    passed: 0
    failed: 1
    fail_rate: 1.0
patterns:
  - signal: "malformed_api_call"
    surface: "api_call"
    count: 1
    task_ids:
      - "task-004"
    routes:
      - "api_direct"
    tools:
      - "billing_api"
  - signal: "unsupported_citation"
    surface: "citation"
    count: 1
    task_ids:
      - "task-001"
    routes:
      - "rag_fast"
    tools:
      - "citation_checker"
  - signal: "unsafe_edit"
    surface: "file_edit"
    count: 1
    task_ids:
      - "task-003"
    routes:
      - "edit_direct"
    tools:
   
… (+2613 chars truncated)
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
mkdir -p ~/.claude/skills/surfacepilot-failure-surface-routing-profiler-for-llm-agents
cp -r /tmp/techllm-skills/skills/surfacepilot-failure-surface-routing-profiler-for-llm-agents/* ~/.claude/skills/surfacepilot-failure-surface-routing-profiler-for-llm-agents/

# Project-local
mkdir -p .claude/skills/surfacepilot-failure-surface-routing-profiler-for-llm-agents
cp -r /tmp/techllm-skills/skills/surfacepilot-failure-surface-routing-profiler-for-llm-agents/* .claude/skills/surfacepilot-failure-surface-routing-profiler-for-llm-agents/
```

**2) As a standalone CLI**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/surfacepilot-failure-surface-routing-profiler-for-llm-agents
python scripts/run.py --help
```

**3) Manual download**

On GitHub, open the `skills/surfacepilot-failure-surface-routing-profiler-for-llm-agents/` folder and download the files, or download the repo ZIP and copy that one folder.

## ⚡ Usage

Full `--help` output:

```text
usage: run.py [-h] [--input INPUT] [--output OUTPUT] [--format {yaml,json}]
              [--failure-threshold FAILURE_THRESHOLD]
              [--min-failures MIN_FAILURES] [--selftest] [--version]

Profile LLM agent failure surfaces from trace JSONL and export a routing
policy.

options:
  -h, --help            show this help message and exit
  --input INPUT, -i INPUT
                        Trace JSONL input file.
  --output OUTPUT, -o OUTPUT
                        Write profile to this file.
  --format {yaml,json}  Output format. Default: yaml.
  --failure-threshold FAILURE_THRESHOLD
                        Minimum group failure rate for policy rules. Default:
                        env or 0.34.
  --min-failures MIN_FAILURES
                        Minimum failed events for patterns and policy rules.
                        Default: env or 1.
  --selftest            Run the built-in sample with assertions and print the
                        resulting profile.
  --version             show program's version number and exit

Environment: SURFACEPILOT_FAILURE_THRESHOLD and SURFACEPILOT_MIN_FAILURES may
set default thresholds.
```

## Examples

See the `examples/` folder in this skill (sample input + expected output).

## 🧠 How it works

- Ingests structured agent traces, including runs, tool calls, observations, evaluator results, and task metadata.
- Labels each run across execution surfaces such as retrieval, file editing, API calls, calculations, citations, planning, state changes, and custom categories.
- Builds pass/fail matrices across task type, model, tool, route, surface, and evaluator signal so weak areas are visible instead of hidden inside aggregate scores.
- Clusters recurring failure patterns such as stale retrieval, unsafe edits, malformed API calls, unsupported citations, and unreliable calculations.
- Exports routing policy in YAML so findings can be translated into model selection, fallback behavior, guardrails, escalation rules, and evaluation priorities.

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| The profiler shows too many unknown or unlabeled surfaces. | The traces do not contain enough structured metadata for SurfacePilot to infer where each failure occurred. | Add clearer task labels, tool-call annotations, evaluator signals, or custom surface labels so the profiler can map evidence to the right execution surfaces. |
| A route appears accurate overall but still looks risky in the matrix. | Final-answer success can hide surface-specific failures, especially when the agent succeeds despite weak retrieval, missing citations, or fragile tool behavior. | Review the failing surfaces directly and add targeted routing rules, guardrails, fallback checks, or evaluation cases for those surfaces. |
| Failure clusters are too broad to act on. | Evaluator signals or error categories may be too generic, causing unrelated failures to be grouped together. | Use more specific evaluator labels and metadata so repeated patterns can be separated into actionable categories. |

## FAQ

**Is SurfacePilot an accuracy benchmark?**

Not exactly. It can use evaluator results, but its main purpose is to explain where routing succeeds or fails across execution surfaces rather than reduce the system to one final-answer score.

**Why focus on failure surfaces instead of just tasks or tools?**

Because the same task can fail for different reasons. A routing decision that is good for retrieval-heavy work may be unsafe for file edits, weak for calculations, or incomplete for citation-sensitive answers.

**What can the exported routing policy be used for?**

It can guide model selection, tool selection, fallback routing, guardrails, escalation paths, and evaluation coverage. The goal is to turn trace evidence into routing behavior that is easier to improve and verify.

**Does SurfacePilot require a specific agent framework?**

The concept is framework-agnostic. It is designed around trace and metadata ingestion, so any agent system that can emit structured run evidence should be able to adapt to it.

## ✅ Verification

Passed automated structure / syntax / selftest checks (see `SKILL.md`).

## Uninstall

Delete the skill folder (`~/.claude/skills/surfacepilot-failure-surface-routing-profiler-for-llm-agents/` or `.claude/skills/surfacepilot-failure-surface-routing-profiler-for-llm-agents/`). Nothing else on your system is touched.

## 📜 Versioning

This skill uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## 🤝 Contributing

This is an auto-generated reference skill. Issues and PRs that improve it are welcome.

## License

MIT
