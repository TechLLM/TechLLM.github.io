# ParallaxPack — Hub-Bias-Resistant Evidence Retrieval

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> Balanced, explainable evidence retrieval for graph-based RAG.

> 🤖 Auto-generated & self-verified skill. A minimal, runnable reference — review before production use.

## What is this?

ParallaxPack is a proposed open-source Python library and CLI that turns graph retrieval candidates into balanced, inspectable evidence packs. It works as a policy layer between candidate generation and prompt assembly, complementing existing vector databases and graph engines.

It addresses hub bias: highly connected nodes can overwhelm nearest-neighbor results with broad background material while recent notes, long-tail evidence, and relevant distant communities remain unseen. ParallaxPack reranks and selects evidence using semantic relevance, inverse hub degree, community diversity, recency, source completeness, and metadata quality.

**Who is this for.** ParallaxPack benefits teams building graph-based RAG, knowledge assistants, research tools, and operational search systems that need diverse evidence, reliable provenance, reproducible selection, and clear comparisons with an unchanged nearest-neighbor baseline.

## ⏱ 30-Second Quick Start

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/parallaxpack-hub-bias-resistant-evidence-retrieval
python scripts/run.py --selftest
```

**Expected output:**

```text
{
  "query": "What recent checkout failures, rollback actions, and customer impact evidence should operators review?",
  "as_of": "2026-01-15",
  "configuration": {
    "top_k": 4,
    "per_community_cap": 2,
    "min_communities": 3,
    "effective_min_communities": 3,
    "redundancy_weight": 0.08,
    "weights": {
      "semantic_relevance": 0.45,
      "inverse_degree": 0.2,
      "recency": 0.15,
      "source_completeness": 0.1,
      "metadata_quality": 0.1
    }
  },
  "summary": {
    "candidate_count": 6,
    "selected_count": 4,
    "excluded_count": 2
  },
  "baseline_comparison": {
    "baseline_policy": "semantic relevance descending, note ID tie-break",
    "hub_degree_threshold": 3.157379,
    "baseline": {
      "selected_ids": [
        "general-platform",
        "architecture-overview",
        "checkout-incident",
        "rollback-runbook"
      ],
      "metrics": {
        "community_count": 2,
        "community_coverage": 0.5,
        "hub_concentration": 0.25,
        "average_degree": 2.0,
        "average_freshness": 0.592399,
        "provenance_coverage": 0.75
      }
    },
    "parallaxpack": {
      "selected_ids": [
        "checkout-incident",
        "security-advisory",
        "customer-impact",
        "rollback-runbook"
      ],
      "metrics": {
        "community_count": 3,
        "community_coverage": 0.75,
        "hub_concentration": 0.0,
        "average_degree": 1.0,
        "average_freshness": 0.989196,
        "provenance_coverage": 1.0
      }
    },
    "delta": {
      "community_count": 1,
      "community_coverage": 0.25,
      "hub_concentration": -0.25,
      "average_degree": -1.0,
      "average_freshness": 0.396797,
      "provenance_coverage": 0.25
    }
  },
  "results": [
    {
      "rank": 1,
      "id": "checkout-incident",
      "title": "Checkout API timeout incident",
      "community": "operations",
      "updated_at": "2026-01-12",
      "degree": 1,
      "score": 0.870963,
      "score_compo
… (+5863 chars truncated)
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
mkdir -p ~/.claude/skills/parallaxpack-hub-bias-resistant-evidence-retrieval
cp -r /tmp/techllm-skills/skills/parallaxpack-hub-bias-resistant-evidence-retrieval/* ~/.claude/skills/parallaxpack-hub-bias-resistant-evidence-retrieval/

# Project-local
mkdir -p .claude/skills/parallaxpack-hub-bias-resistant-evidence-retrieval
cp -r /tmp/techllm-skills/skills/parallaxpack-hub-bias-resistant-evidence-retrieval/* .claude/skills/parallaxpack-hub-bias-resistant-evidence-retrieval/
```

**2) As a standalone CLI**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/parallaxpack-hub-bias-resistant-evidence-retrieval
python scripts/run.py --help
```

**3) Manual download**

On GitHub, open the `skills/parallaxpack-hub-bias-resistant-evidence-retrieval/` folder and download the files, or download the repo ZIP and copy that one folder.

## ⚡ Usage

Full `--help` output:

```text
usage: run.py [-h] (--input INPUT | --selftest) [--format FORMAT]
              [--output OUTPUT] [--force] [--top-k TOP_K]
              [--per-community-cap PER_COMMUNITY_CAP]
              [--min-communities MIN_COMMUNITIES]

Rerank graph candidates into a hub-resistant evidence pack.

options:
  -h, --help            show this help message and exit
  --input INPUT         Path to an input JSON file
  --selftest            Run the built-in offline deterministic sample
  --format FORMAT       Output format: json, markdown, or both (default: json)
  --output OUTPUT       Write output to this file instead of stdout
  --force               Allow --output to overwrite an existing file
  --top-k TOP_K         Override the number of selected notes
  --per-community-cap PER_COMMUNITY_CAP
                        Override the maximum notes per community
  --min-communities MIN_COMMUNITIES
                        Override the minimum community coverage target
```

## Examples

See the `examples/` folder in this skill (sample input + expected output).

## 🧠 How it works

- Accepts a knowledge graph, note metadata, a natural-language query, and candidates from an existing retrieval system.
- Calculates a composite score from semantic relevance, inverse degree, recency, source availability, and metadata quality.
- Selects a diverse evidence set using community caps, coverage targets, and redundancy penalties without automatically excluding hub nodes.
- Explains why each candidate was selected, penalized, or excluded, including score components, provenance, and community assignment.
- Produces LLM-ready Markdown, machine-readable JSON, or both, with baseline comparisons for coverage, hub concentration, freshness, and provenance.

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Results are still dominated by hub nodes. | Inverse-degree influence may be too weak relative to semantic relevance, or community constraints may be too permissive. | Increase the influence of inverse-degree scoring, tighten per-community caps, and review score explanations before comparing the evidence pack with the baseline. |
| Relevant evidence is missing from the final pack. | The candidate generator may never have retrieved it, or diversity and redundancy rules may be filtering it too aggressively. | Verify that the evidence appears in the input candidates, broaden upstream retrieval if necessary, and adjust coverage, cap, and redundancy settings. |
| Recency or provenance scores are unexpectedly low. | Notes may have missing, inconsistent, or invalid timestamps, source references, or metadata fields. | Normalize metadata before reranking and ensure each note includes valid dates, provenance details, community assignments, and source availability information. |
| Repeated runs produce different selections. | Candidate ordering, graph state, metadata, or tie handling may vary between runs. | Keep inputs and configuration fixed, use deterministic tie handling, and retain structured score explanations for comparison. |

## FAQ

**Does ParallaxPack replace a vector database or graph engine?**

No. It reranks and selects candidates produced by existing retrieval infrastructure, acting as a policy layer before prompt assembly.

**Does hub-aware reranking remove highly connected nodes?**

No. Hub nodes remain eligible when relevant, but their connectivity no longer gives them disproportionate influence.

**Why support both Markdown and JSON?**

Markdown is convenient for direct LLM context and human review, while JSON supports evaluation, automation, auditing, and integration with downstream systems.

**How can teams evaluate whether reranking helps?**

Compare the evidence pack with the unmodified nearest-neighbor baseline using community coverage, hub concentration, freshness, provenance completeness, and task-specific answer quality.

## ✅ Verification

Passed automated structure / syntax / selftest checks (see `SKILL.md`).

## Uninstall

Delete the skill folder (`~/.claude/skills/parallaxpack-hub-bias-resistant-evidence-retrieval/` or `.claude/skills/parallaxpack-hub-bias-resistant-evidence-retrieval/`). Nothing else on your system is touched.

## 📜 Versioning

This skill uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## 🤝 Contributing

This is an auto-generated reference skill. Issues and PRs that improve it are welcome.

## License

MIT
