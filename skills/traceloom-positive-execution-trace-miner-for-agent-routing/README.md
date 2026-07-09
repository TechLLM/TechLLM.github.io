# TraceLoom — Positive Execution Trace Miner for Agent Routing

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> Mine verified agent wins into routing-ready training data.

> 🤖 Auto-generated & self-verified skill. A minimal, runnable reference — review before production use.

## What is this?

TraceLoom is a proposed open-source CLI for turning successful LLM agent executions into clean, reusable datasets. It focuses on traces that passed verification, so teams can learn from workflows that are already known to work.

Instead of starting with failure taxonomies, negative rollout labels, or detailed penalties for every bad action, TraceLoom extracts the positive signal from completed runs. It helps identify which tools were used, in what order, which files or context sources mattered, and what conditions were associated with success.

The output is designed for practical downstream use: improving routers, prompt selectors, policy heuristics, retrieval planners, and evaluation workflows without exposing sensitive prompts, private file contents, or internal system details.

**Who is this for.** TraceLoom is for teams building, evaluating, or operating AI agents that already produce execution logs and verifier results. It is especially useful for agent platform engineers, evaluation teams, applied researchers, and open-source maintainers who want training-ready routing data from real successful runs.

## ⏱ 30-Second Quick Start

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/traceloom-positive-execution-trace-miner-for-agent-routing
python scripts/run.py --selftest
```

**Expected output:**

```text
{"task_id":"task-alpha","run_id":"run-001","success_condition":"passed=true; score=1.0","tool_sequence":["file.read","search.query","file.write","test.run"],"tool_calls":[{"order":2,"tool":"file.read","argument_summary":{"path":"src/router.py"}},{"order":3,"tool":"search.query","argument_summary":{"query":{"chars":23,"words":3},"top_k":3}},{"order":4,"tool":"file.write","argument_summary":{"content":{"redacted":true,"chars":30},"path":"src/router.py"}},{"order":5,"tool":"test.run","argument_summary":{"command":{"program":"python","arg_count":3,"chars":37}}}],"file_patterns":{"read":["src/router.py"],"write":["src/router.py"],"touched":["src/router.py"]},"retrieval_paths":[{"order":1,"source":"docs/router-policy.md","query_summary":{"chars":26,"words":3}}],"routing_signals":{"tool_count":4,"retrieval_count":1,"file_count":1,"normalized_tool_path":"file.read>search.query>file.write>test.run"}}
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
mkdir -p ~/.claude/skills/traceloom-positive-execution-trace-miner-for-agent-routing
cp -r /tmp/techllm-skills/skills/traceloom-positive-execution-trace-miner-for-agent-routing/* ~/.claude/skills/traceloom-positive-execution-trace-miner-for-agent-routing/

# Project-local
mkdir -p .claude/skills/traceloom-positive-execution-trace-miner-for-agent-routing
cp -r /tmp/techllm-skills/skills/traceloom-positive-execution-trace-miner-for-agent-routing/* .claude/skills/traceloom-positive-execution-trace-miner-for-agent-routing/
```

**2) As a standalone CLI**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/traceloom-positive-execution-trace-miner-for-agent-routing
python scripts/run.py --help
```

**3) Manual download**

On GitHub, open the `skills/traceloom-positive-execution-trace-miner-for-agent-routing/` folder and download the files, or download the repo ZIP and copy that one folder.

## ⚡ Usage

Full `--help` output:

```text
usage: run.py [-h] [--traces TRACES] [--graders GRADERS]
              [--format {jsonl,csv}] [--output OUTPUT] [--min-score MIN_SCORE]
              [--selftest]

Mine verified successful LLM agent traces into positive routing datasets.

options:
  -h, --help            show this help message and exit
  --traces TRACES       Path to execution trace JSONL input.
  --graders GRADERS     Path to grader or verifier JSON input.
  --format {jsonl,csv}  Output format. Defaults to TRACELOOM_OUTPUT_FORMAT or
                        jsonl.
  --output OUTPUT       Optional output file path. Defaults to stdout.
  --min-score MIN_SCORE
                        Minimum score for success when score is present.
                        Defaults to TRACELOOM_MIN_SCORE or 1.0.
  --selftest            Run on built-in mock data with no API key or external
                        files.
```

## Examples

See the `examples/` folder in this skill (sample input + expected output).

## 🧠 How it works

- Ingests execution trace records and grader or verifier results.
- Matches completed tasks with their verification outcomes.
- Filters for successful executions before extracting routing signals.
- Summarizes tool sequences, normalized tool names, argument patterns, file usage, retrieval paths, and success conditions.
- Exports structured datasets suitable for router training, prompt selection, analysis, or evaluation workflows.

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| No successful traces are exported. | The trace records may not match the verifier results, or the verifier data may not mark any runs as passing. | Check that task identifiers are consistent across inputs and confirm that successful outcomes are represented in the verifier results. |
| Tool names appear inconsistent across the dataset. | Different agents or logging layers may record the same tool under different names. | Use a consistent normalization strategy so equivalent tools are grouped under stable names. |
| Exported rows contain less detail than expected. | TraceLoom is designed to avoid relying on sensitive prompts, raw file contents, or private internal context. | Review which metadata is available in the source traces and include safe routing-relevant fields in the logs before mining them. |

## FAQ

**Why does TraceLoom focus only on successful executions?**

Successful executions provide a cleaner and easier-to-trust signal. They show which routes, tools, files, and retrieval choices led to verified outcomes without requiring teams to design a full failure labeling system first.

**Can this be used for model training?**

Yes, the exported JSONL or CSV data can support router training, prompt selection, heuristic tuning, retrieval planning, and evaluation analysis. It is intended as structured training data for agent decision systems rather than a replacement for full rollout evaluation.

**Does TraceLoom require storing private prompts or file contents?**

No. The project is designed around summaries, metadata, tool order, file interaction patterns, retrieval paths, and success conditions, so teams can mine useful routing data without exposing sensitive content.

**Is this only useful for large agent teams?**

No. Smaller teams can use it to understand which workflows are working, while larger teams can use it to build repeatable datasets for routing, policy, and evaluation improvements.

## ✅ Verification

Passed automated structure / syntax / selftest checks (see `SKILL.md`).

## Uninstall

Delete the skill folder (`~/.claude/skills/traceloom-positive-execution-trace-miner-for-agent-routing/` or `.claude/skills/traceloom-positive-execution-trace-miner-for-agent-routing/`). Nothing else on your system is touched.

## 📜 Versioning

This skill uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## 🤝 Contributing

This is an auto-generated reference skill. Issues and PRs that improve it are welcome.

## License

MIT
