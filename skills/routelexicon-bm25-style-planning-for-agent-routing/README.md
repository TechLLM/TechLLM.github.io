# RouteLexicon — BM25-Style Planning for Agent Routing

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> Transparent BM25-style routing plans for multi-agent systems.

> 🤖 Auto-generated & self-verified skill. A minimal, runnable reference — review before production use.

## What is this?

RouteLexicon is a proposed open-source routing layer for multi-agent systems. It turns user requests and agent manifests into explicit routing plans built from concrete lexical evidence: keywords, rare terms, synonyms, exclusions, constraints, weights, and subqueries.

Instead of asking a language model to choose an agent from vague intent alone, RouteLexicon makes the matching process inspectable. It shows why an agent matched, which clues mattered, which similar agents were excluded, and how a request can be split across specialized agents.

The project is designed as a lightweight CLI and library that works with plain JSON manifests and the Python standard library. Its output is machine-readable JSON that can be logged, tested, reviewed, or passed into an LLM-powered orchestration layer.

**Who is this for.** RouteLexicon is for developers building agent routers, orchestration layers, internal automation systems, and evaluation harnesses where agent selection needs to be transparent, testable, and easier to debug than a single opaque model decision.

## ⏱ 30-Second Quick Start

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/routelexicon-bm25-style-planning-for-agent-routing
python scripts/run.py --selftest
```

**Expected output:**

```text
{"version": "0.1.0", "request": "Research competitors and summarize current market evidence", "query_terms": ["competitors", "current", "evidence", "market", "research", "summarize"], "idf": {"agent_count": 3, "average_document_length": 35.67}, "ranked_agents": [{"agent_id": "research-agent", "name": "Research Agent", "score": 7.6549, "matched_terms": [{"term": "competitors", "idf": 0.9808, "tf": 2}, {"term": "current", "idf": 0.9808, "tf": 1}, {"term": "evidence", "idf": 0.9808, "tf": 3}, {"term": "research", "idf": 0.9808, "tf": 6}, {"term": "market", "idf": 0.47, "tf": 3}], "rare_terms": [{"term": "competitors", "idf": 0.9808}, {"term": "current", "idf": 0.9808}, {"term": "evidence", "idf": 0.9808}, {"term": "research", "idf": 0.9808}, {"term": "market", "idf": 0.47}], "excluded_by": [], "weights": {"bm25": 6.5055, "keyword_boost": 1.1494, "exclusion_penalty": 0.0, "final": 7.6549}, "rationale": "Matched competitors, current, evidence, market, research; rare clues: competitors, current, evidence."}, {"agent_id": "finance-agent", "name": "Finance Agent", "score": 0.9685, "matched_terms": [{"term": "market", "idf": 0.47, "tf": 3}], "rare_terms": [{"term": "market", "idf": 0.47}], "excluded_by": [], "weights": {"bm25": 0.804, "keyword_boost": 0.1645, "exclusion_penalty": 0.0, "final": 0.9685}, "rationale": "Matched market; rare clues: market."}, {"agent_id": "coding-agent", "name": "Coding Agent", "score": -1.5, "matched_terms": [], "rare_terms": [], "excluded_by": ["market"], "weights": {"bm25": 0.0, "keyword_boost": 0.0, "exclusion_penalty": 1.5, "final": -1.5}, "rationale": "Penalized because the request contains exclusion terms: market."}], "routing_plan": {"selected_agent_ids": ["research-agent", "finance-agent"], "decomposed_subqueries": [{"id": "q1", "text": "Research competitors", "terms": ["competitors", "research"], "candidate_agent_ids": ["research-agent"]}, {"id": "q2", "text": "summarize current market evidence", "terms": ["current", "evidence", "market
… (+151 chars truncated)
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
mkdir -p ~/.claude/skills/routelexicon-bm25-style-planning-for-agent-routing
cp -r /tmp/techllm-skills/skills/routelexicon-bm25-style-planning-for-agent-routing/* ~/.claude/skills/routelexicon-bm25-style-planning-for-agent-routing/

# Project-local
mkdir -p .claude/skills/routelexicon-bm25-style-planning-for-agent-routing
cp -r /tmp/techllm-skills/skills/routelexicon-bm25-style-planning-for-agent-routing/* .claude/skills/routelexicon-bm25-style-planning-for-agent-routing/
```

**2) As a standalone CLI**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/routelexicon-bm25-style-planning-for-agent-routing
python scripts/run.py --help
```

**3) Manual download**

On GitHub, open the `skills/routelexicon-bm25-style-planning-for-agent-routing/` folder and download the files, or download the repo ZIP and copy that one folder.

## ⚡ Usage

Full `--help` output:

```text
usage: run.py [-h] [--manifest MANIFEST] [--query QUERY]
              [--query-file QUERY_FILE] [--top-k TOP_K] [--k1 K1] [--b B]
              [--output OUTPUT] [--pretty] [--selftest]

Create BM25-style routing plans from a user request and JSON agent manifest.

options:
  -h, --help            show this help message and exit
  --manifest MANIFEST   Path to a JSON manifest with an agents array.
  --query QUERY         Request text to route.
  --query-file QUERY_FILE
                        Path to a UTF-8 text file containing the request.
  --top-k TOP_K         Number of selected agents to return.
  --k1 K1               BM25 term saturation parameter.
  --b B                 BM25 document-length normalization parameter.
  --output OUTPUT       Write the JSON result to this file instead of stdout.
  --pretty              Pretty-print JSON output.
  --selftest            Run on built-in sample data without API keys.
```

## Examples

See the `examples/` folder in this skill (sample input + expected output).

## 🧠 How it works

- Reads plain JSON agent manifests that describe each agent's capabilities.
- Tokenizes agent descriptions and user requests with a standard-library tokenizer.
- Computes corpus-level IDF scores so rare, specific terms carry more routing weight.
- Builds BM25-style routing plans with keywords, rare terms, exclusions, weights, and subqueries.
- Returns ranked candidate agents with structured scoring details and a human-readable rationale.

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| The wrong agent ranks highly. | The agent manifest may contain broad or overlapping language that matches the request lexically but does not represent the right capability. | Tighten the manifest description, add more specific capability terms, and define exclusion terms for close-but-wrong matches. |
| Several agents receive very similar scores. | Their manifests likely use similar vocabulary or describe adjacent responsibilities without enough distinguishing terms. | Add clearer capability boundaries, rare domain terms, and task-specific constraints to each manifest. |
| A relevant agent does not appear in the top results. | The request and the agent manifest may use different wording for the same concept. | Add synonyms or alternate phrasing to the manifest so the planner can connect the request language to the agent's capability. |

## FAQ

**Is RouteLexicon a replacement for an LLM router?**

Not necessarily. It can be used on its own for lexical routing, or in front of an LLM router to provide explicit evidence, candidate rankings, exclusions, and subqueries.

**Why use BM25-style planning for agent routing?**

BM25-style scoring rewards specific, rare terms and makes lexical evidence explicit. That helps routing become easier to inspect, test, and debug than a direct natural-language classification step.

**Does RouteLexicon require external dependencies?**

The proposed core is designed around the Python standard library, plain JSON manifests, and simple tokenizer and IDF logic, so it can stay lightweight and easy to integrate.

**What does the routing output include?**

The output includes ranked agents, scoring details, matched terms, rare clues, exclusions, weights, subqueries, and rationale that downstream systems can inspect or log.

## ✅ Verification

Passed automated structure / syntax / selftest checks (see `SKILL.md`).

## Uninstall

Delete the skill folder (`~/.claude/skills/routelexicon-bm25-style-planning-for-agent-routing/` or `.claude/skills/routelexicon-bm25-style-planning-for-agent-routing/`). Nothing else on your system is touched.

## 📜 Versioning

This skill uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## 🤝 Contributing

This is an auto-generated reference skill. Issues and PRs that improve it are welcome.

## License

MIT
