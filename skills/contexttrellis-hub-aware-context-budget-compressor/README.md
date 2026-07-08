# ContextTrellis — Hub-Aware Context Budget Compressor

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> Build compact LLM context bundles without losing critical long-tail notes.

> 🤖 Auto-generated & self-verified skill. A minimal, runnable reference — review before production use.

## What is this?

ContextTrellis is a proposed open-source library and CLI for turning large Markdown knowledge vaults into high-signal context bundles for LLMs.

It solves a common retrieval problem in agentic systems: central hub notes often consume most of the prompt budget, while smaller notes with the exact execution details are left out. Those overlooked notes may contain API behavior, polling rules, dry-run findings, command quirks, or constraints that determine whether an agent succeeds.

ContextTrellis keeps the broad map without burying the operational details. It compresses highly connected hub notes into short orientation summaries and preserves execution-heavy long-tail notes closer to their original form.

**Who is this for.** ContextTrellis is for developers, agent builders, technical writers, and knowledge-management teams who maintain large Markdown or Obsidian-style vaults and need reliable, auditable context packages for LLM workflows.

## ⏱ 30-Second Quick Start

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/contexttrellis-hub-aware-context-budget-compressor
python scripts/run.py --selftest
```

**Expected output:**

```text
{
  "bundle_version": "0.1",
  "mode": "selftest",
  "input": "built-in-sample",
  "budget": {
    "requested_tokens": 900,
    "reserve_tokens": 100,
    "available_tokens": 800,
    "used_tokens": 269
  },
  "graph": {
    "notes": 5,
    "edges": 4,
    "hubs": [
      "Architecture.md"
    ],
    "long_tail": [
      "API Polling.md",
      "CLI Commands.md",
      "Dry Run Log.md",
      "Error Handling.md"
    ]
  },
  "items": [
    {
      "id": "Architecture.md",
      "path": "Architecture.md",
      "role": "hub_summary",
      "tokens": 39,
      "centrality": 1.0,
      "execution_score": 2.55,
      "reason": "high-centrality orientation note; compressed",
      "content": "# Architecture Hub\nPurpose: ContextTrellis builds prompt bundles from [[API Polling]], [[CLI Commands]], and [[Dry Run Log]].\nLinks: API Polling.md, CLI Commands.md, Dry Run Log.md, Error Handling.md\nTags: architecture, index"
    },
    {
      "id": "API Polling.md",
      "path": "API Polling.md",
      "role": "preserved_detail",
      "tokens": 65,
      "centrality": 0.25,
      "execution_score": 12.7,
      "reason": "execution-heavy long-tail note; preserved",
      "content": "# API Polling\n\nTags: #api #execution\n\nUse this when a job returns `queued` or `running`.\nPoll `GET /v1/jobs/{job_id}` every 5 seconds until status becomes `succeeded` or `failed`.\nDo not poll faster than once per second.\n\n```bash\ncurl -s \"$BASE_URL/v1/jobs/$JOB_ID\"\n```\n\nIf the API returns 429, wait 30 seconds before retrying."
    },
    {
      "id": "CLI Commands.md",
      "path": "CLI Commands.md",
      "role": "preserved_detail",
      "tokens": 47,
      "centrality": 0.25,
      "execution_score": 6.05,
      "reason": "execution-heavy long-tail note; preserved",
      "content": "# CLI Commands\n\nTags: #cli #execution\n\nRun the compressor locally before calling an LLM:\n\n```bash\npython scripts/run.py --input examples/vault --budget 620 --reserve 80\n```\n\nUse `--format 
… (+2119 chars truncated)
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
mkdir -p ~/.claude/skills/contexttrellis-hub-aware-context-budget-compressor
cp -r /tmp/techllm-skills/skills/contexttrellis-hub-aware-context-budget-compressor/* ~/.claude/skills/contexttrellis-hub-aware-context-budget-compressor/

# Project-local
mkdir -p .claude/skills/contexttrellis-hub-aware-context-budget-compressor
cp -r /tmp/techllm-skills/skills/contexttrellis-hub-aware-context-budget-compressor/* .claude/skills/contexttrellis-hub-aware-context-budget-compressor/
```

**2) As a standalone CLI**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/contexttrellis-hub-aware-context-budget-compressor
python scripts/run.py --help
```

**3) Manual download**

On GitHub, open the `skills/contexttrellis-hub-aware-context-budget-compressor/` folder and download the files, or download the repo ZIP and copy that one folder.

## ⚡ Usage

Full `--help` output:

```text
usage: run.py [-h] [--input INPUT] [--selftest] [--budget BUDGET]
              [--reserve RESERVE] [--format {json,markdown}]
              [--min-execution-score MIN_EXECUTION_SCORE]
              [--hub-summary-tokens HUB_SUMMARY_TOKENS]
              [--max-note-tokens MAX_NOTE_TOKENS]

Build a hub-aware, budgeted LLM context bundle from Markdown notes.

options:
  -h, --help            show this help message and exit
  --input INPUT         Markdown file or folder. Omit for built-in sample
                        data.
  --selftest            Run on built-in sample data with no API key or
                        external services.
  --budget BUDGET       Requested token budget before reserve. Env:
                        CONTEXTTRELLIS_BUDGET.
  --reserve RESERVE     Tokens to reserve for the caller's surrounding prompt.
                        Env: CONTEXTTRELLIS_RESERVE_TOKENS.
  --format {json,markdown}
                        Output format. Env: CONTEXTTRELLIS_OUTPUT_FORMAT.
  --min-execution-score MIN_EXECUTION_SCORE
  --hub-summary-tokens HUB_SUMMARY_TOKENS
  --max-note-tokens MAX_NOTE_TOKENS
```

## Examples

See the `examples/` folder in this skill (sample input + expected output).

## 🧠 How it works

- Parses Markdown notes, links, tags, headings, front matter, and related concepts into a knowledge graph.
- Scores notes by graph centrality, execution signals, and estimated token cost.
- Compresses over-central hub notes into concise orientation blocks instead of letting them dominate the prompt.
- Preserves low-centrality notes that contain commands, API details, errors, procedures, status transitions, or operational constraints.
- Assembles a deterministic context bundle with transparent inclusion decisions and configurable token reserves.

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Important operational notes are still missing from the bundle. | The execution-signal scoring may not be tuned to the language or structure used in the vault. | Adjust the execution-signal configuration so the planner recognizes the terms, headings, code patterns, and procedural markers used in your notes. |
| The bundle feels too abstract or summary-heavy. | The token budget may be too small, or hub compression may be too aggressive for the task. | Increase the available budget, reduce the reserve, or relax compression settings for notes that should remain more detailed. |
| A hub note is included too verbosely. | The note may have strong execution signals as well as high centrality, causing it to be treated as operationally important. | Review the inclusion rationale and tune the balance between centrality compression and execution preservation. |

## FAQ

**Is ContextTrellis only for Obsidian vaults?**

No. It is designed to work well with Obsidian-style Markdown folders, including wikilinks and front matter, but the underlying graph-based budgeting approach can apply to other Markdown knowledge bases.

**Does it replace vector search?**

Not necessarily. ContextTrellis can be used before or alongside retrieval. Its focus is budget allocation: deciding what should be summarized, preserved, or omitted once candidate knowledge is available.

**Why not just summarize everything?**

Uniform summarization can remove the exact details an agent needs to act correctly. ContextTrellis treats orientation and execution differently, compressing broad hub material while preserving notes that contain operational specifics.

**Can it be used inside an agent framework?**

Yes. The proposed design supports both a standalone CLI workflow and Python library integration for agent frameworks, retrieval pipelines, and knowledge-management tools.

## ✅ Verification

Passed automated structure / syntax / selftest checks (see `SKILL.md`).

## Uninstall

Delete the skill folder (`~/.claude/skills/contexttrellis-hub-aware-context-budget-compressor/` or `.claude/skills/contexttrellis-hub-aware-context-budget-compressor/`). Nothing else on your system is touched.

## 📜 Versioning

This skill uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## 🤝 Contributing

This is an auto-generated reference skill. Issues and PRs that improve it are welcome.

## License

MIT
