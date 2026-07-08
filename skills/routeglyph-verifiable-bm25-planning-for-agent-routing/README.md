# RouteGlyph — Verifiable BM25 Planning for Agent Routing

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> Transparent BM25-style routing plans for agent and tool selection.

> 🤖 Auto-generated & self-verified skill. A minimal, runnable reference — review before production use.

## What is this?

RouteGlyph is a proposed open-source routing layer for making agent and tool routing easier to inspect, test, and trust. It turns user requests and tool descriptions into explicit BM25-style candidate plans instead of leaving routing decisions hidden inside an LLM prompt.

The problem it solves is routing opacity. In many multi-agent systems, it is hard to tell why one tool was chosen over another, whether the decision can be reproduced, or how a change in a tool description affected behavior. RouteGlyph creates a structured routing surface that can be reviewed, logged, versioned, and regression-tested like normal software.

RouteGlyph does not replace an LLM router. It prepares transparent, ranked candidates before any generative decision is made, so an LLM, rules engine, policy layer, or orchestrator can make the final choice with better evidence.

**Who is this for.** RouteGlyph is for teams building multi-agent systems, tool-using assistants, RAG pipelines, evaluation harnesses, and production AI workflows where routing mistakes are expensive, difficult to debug, or subject to review.

## ⏱ 30-Second Quick Start

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/routeglyph-verifiable-bm25-planning-for-agent-routing
python scripts/run.py --selftest
```

**Expected output:**

```text
{
  "plan_version": "routeglyph.v1",
  "tokenizer": "routeglyph-tokenizer.v1",
  "query": "Route an agent request to build a local regression-testable BM25 router with no API key.",
  "query_terms": [
    "route",
    "agent",
    "request",
    "build",
    "local",
    "regression",
    "testable",
    "bm25",
    "router",
    "no",
    "api",
    "key"
  ],
  "required_constraints": [
    "code_required",
    "local_only",
    "regression_testable"
  ],
  "candidates": [
    {
      "rank": 1,
      "tool_id": "route_planner",
      "tool_name": "Route Planner",
      "score": 11.0619,
      "rare_terms": [
        "bm25",
        "route",
        "router",
        "routing",
        "tool"
      ],
      "matched_terms": [
        {
          "term": "agent",
          "query_weight": 1.0,
          "tool_tf": 2,
          "idf": 0.3567,
          "contribution": 0.4648
        },
        {
          "term": "bm25",
          "query_weight": 1.0,
          "tool_tf": 2,
          "idf": 1.204,
          "contribution": 1.5689
        },
        {
          "term": "idf",
          "query_weight": 0.65,
          "tool_tf": 1,
          "idf": 1.204,
          "contribution": 0.7244
        },
        {
          "term": "local",
          "query_weight": 1.0,
          "tool_tf": 1,
          "idf": 0.6931,
          "contribution": 0.6416
        },
        {
          "term": "orchestrator",
          "query_weight": 0.65,
          "tool_tf": 1,
          "idf": 1.204,
          "contribution": 0.7244
        },
        {
          "term": "regression",
          "query_weight": 1.0,
          "tool_tf": 2,
          "idf": 0.6931,
          "contribution": 0.9032
        },
        {
          "term": "route",
          "query_weight": 1.0,
          "tool_tf": 1,
          "idf": 1.204,
          "contribution": 1.1145
        },
        {
          "term": "router",
          "query_weight": 1.0,
          "tool_tf": 1,
          "idf": 1.204,
          "
… (+9902 chars truncated)
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
mkdir -p ~/.claude/skills/routeglyph-verifiable-bm25-planning-for-agent-routing
cp -r /tmp/techllm-skills/skills/routeglyph-verifiable-bm25-planning-for-agent-routing/* ~/.claude/skills/routeglyph-verifiable-bm25-planning-for-agent-routing/

# Project-local
mkdir -p .claude/skills/routeglyph-verifiable-bm25-planning-for-agent-routing
cp -r /tmp/techllm-skills/skills/routeglyph-verifiable-bm25-planning-for-agent-routing/* .claude/skills/routeglyph-verifiable-bm25-planning-for-agent-routing/
```

**2) As a standalone CLI**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/routeglyph-verifiable-bm25-planning-for-agent-routing
python scripts/run.py --help
```

**3) Manual download**

On GitHub, open the `skills/routeglyph-verifiable-bm25-planning-for-agent-routing/` folder and download the files, or download the repo ZIP and copy that one folder.

## ⚡ Usage

Full `--help` output:

```text
usage: run.py [-h] [--query QUERY] [--query-file QUERY_FILE]
              [--catalog CATALOG] [--tool TOOL] [--limit LIMIT]
              [--min-score MIN_SCORE] [--pretty] [--selftest]

Generate deterministic BM25-style routing plans for agent/tool catalogs.

options:
  -h, --help            show this help message and exit
  --query QUERY         User request to route.
  --query-file QUERY_FILE
                        Text file containing the user request to route.
  --catalog CATALOG     Tool catalog as JSON or a small supported YAML subset.
  --tool TOOL           Inline tool as 'id|name|description' or
                        'id|name|description|keyword1,keyword2'. May be
                        repeated.
  --limit LIMIT         Maximum candidates to emit.
  --min-score MIN_SCORE
                        Drop candidates below this score.
  --pretty              Pretty-print JSON output.
  --selftest            Run on built-in sample data with no API key.
```

## Examples

See the `examples/` folder in this skill (sample input + expected output).

## 🧠 How it works

- Tokenizes user requests and tool or agent descriptions into routing signals.
- Estimates term importance with BM25-style inverse document frequency scoring.
- Expands each candidate plan with rare terms, synonyms, exclusions, required constraints, scores, and rationales.
- Ranks candidate tools or agents before they are passed to an LLM router, policy engine, or orchestrator.
- Emits structured JSON snapshots that can be reviewed in pull requests, stored in logs, and compared in regression tests.

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| The wrong tool is ranked too highly. | The tool description may contain broad or overlapping terms that make it look relevant to many unrelated requests. | Tighten the description with more specific capabilities, add clearer exclusions, and include distinctive terms that separate it from neighboring tools. |
| A relevant tool is missing from the candidate set. | The catalog entry may not include the vocabulary used by real user requests, or required constraints may be too narrow. | Add representative synonyms, domain terms, and constraint wording that matches how users actually ask for the task. |
| Scores changed after editing a catalog. | IDF-style scoring depends on the full catalog, so adding or changing descriptions can alter term rarity across candidates. | Review the generated plan snapshot and treat the score change like any other intentional behavioral change. |

## FAQ

**Is RouteGlyph an LLM router?**

No. RouteGlyph is a transparent candidate-generation layer. It creates inspectable routing plans that an LLM router, rules engine, policy layer, or orchestrator can use downstream.

**Why use BM25-style planning for agent routing?**

Sparse retrieval is good at matching distinctive terms, constraints, and decomposed queries. Those same properties are useful when deciding which tool or agent is likely to fit a request.

**Can RouteGlyph make routing deterministic?**

It can make candidate generation deterministic and reproducible. The final routing decision may still be probabilistic if it is handed to an LLM.

**How does this help with evaluation?**

RouteGlyph produces structured snapshots of routing plans, scores, and rationales. Those snapshots can be compared over time to catch regressions when prompts, tool descriptions, or catalogs change.

## ✅ Verification

Passed automated structure / syntax / selftest checks (see `SKILL.md`).

## Uninstall

Delete the skill folder (`~/.claude/skills/routeglyph-verifiable-bm25-planning-for-agent-routing/` or `.claude/skills/routeglyph-verifiable-bm25-planning-for-agent-routing/`). Nothing else on your system is touched.

## 📜 Versioning

This skill uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## 🤝 Contributing

This is an auto-generated reference skill. Issues and PRs that improve it are welcome.

## License

MIT
