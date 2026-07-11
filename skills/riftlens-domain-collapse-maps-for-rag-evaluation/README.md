# RiftLens — Domain Collapse Maps for RAG Evaluation

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> Find the source domains where your RAG system quietly fails.

> 🤖 Auto-generated & self-verified skill. A minimal, runnable reference — review before production use.

## What is this?

RiftLens is a proposed command-line benchmark for evaluating retrieval-augmented generation systems by source domain, not just by one blended score.

Mixed knowledge bases often contain notes, wiki pages, API references, research summaries, tickets, and policy documents. Aggregate relevance metrics can make a system look healthier than it is while hiding severe failures on one document type.

RiftLens turns those hidden failures into a reviewable Markdown report. It helps teams see which domains improved, which collapsed, and whether a retrieval or reranking change generalizes across the knowledge base it actually serves.

**Who is this for.** RiftLens is for RAG builders, evaluation engineers, AI platform teams, and technical reviewers who need clearer regression signals before shipping changes to retrievers, rerankers, relevance gates, or knowledge-base indexing pipelines.

## ⏱ 30-Second Quick Start

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/riftlens-domain-collapse-maps-for-rag-evaluation
python scripts/run.py --selftest
```

**Expected output:**

```text
# RiftLens Domain Collapse Report

- Threshold: `0.60`
- Top K: `all`
- Queries: `3`
- Retrieved items: `8`
- Overall hit rate: `75.0%`
- Overall false pass rate: `50.0%`
- Overall false reject rate: `25.0%`
- Worst-domain gap: `100.0 pp`
- Worst domain: `api_reference`

| Domain | Coverage | Hit rate | False pass | False reject | Relevant | Passed |
|---|---:|---:|---:|---:|---:|---:|
| api_reference | 66.7% | 0.0% | 0.0% | 100.0% | 1 | 0 |
| notes | 66.7% | 100.0% | 100.0% | 0.0% | 1 | 2 |
| tickets | 66.7% | 100.0% | 0.0% | 0.0% | 1 | 1 |
| wiki | 66.7% | 100.0% | 100.0% | 0.0% | 1 | 2 |

## Flags

- Collapse: `api_reference` trails the best domain by `100.0 pp`.
- Risk: `api_reference` has high false reject rate (`100.0%`).
- Risk: `notes` has high false pass rate (`100.0%`).
- Risk: `wiki` has high false pass rate (`100.0%`).
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
mkdir -p ~/.claude/skills/riftlens-domain-collapse-maps-for-rag-evaluation
cp -r /tmp/techllm-skills/skills/riftlens-domain-collapse-maps-for-rag-evaluation/* ~/.claude/skills/riftlens-domain-collapse-maps-for-rag-evaluation/

# Project-local
mkdir -p .claude/skills/riftlens-domain-collapse-maps-for-rag-evaluation
cp -r /tmp/techllm-skills/skills/riftlens-domain-collapse-maps-for-rag-evaluation/* .claude/skills/riftlens-domain-collapse-maps-for-rag-evaluation/
```

**2) As a standalone CLI**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/riftlens-domain-collapse-maps-for-rag-evaluation
python scripts/run.py --help
```

**3) Manual download**

On GitHub, open the `skills/riftlens-domain-collapse-maps-for-rag-evaluation/` folder and download the files, or download the repo ZIP and copy that one folder.

## ⚡ Usage

Full `--help` output:

```text
usage: run.py [-h] [--input INPUT] [--output OUTPUT] [--threshold THRESHOLD]
              [--top-k TOP_K] [--selftest]

Generate domain-split RAG retrieval diagnostics as Markdown.

options:
  -h, --help            show this help message and exit
  --input INPUT, -i INPUT
                        JSONL retrieval log. If omitted, RiftLens uses built-
                        in sample data.
  --output OUTPUT, -o OUTPUT
                        Optional Markdown output path. Defaults to stdout.
  --threshold THRESHOLD
                        Score threshold for pass/fail. Defaults to
                        RIFTLENS_THRESHOLD or 0.60.
  --top-k TOP_K         Evaluate only the first K retrieved documents per
                        query. Defaults to RIFTLENS_TOP_K or all.
  --selftest            Run on built-in sample data. This is also the default
                        when --input is omitted.
```

## Examples

See the `examples/` folder in this skill (sample input + expected output).

## 🧠 How it works

- Reads query, answer, and retrieval records from plain JSONL inputs.
- Uses domain tags on retrieved documents to split evaluation by source type.
- Computes per-domain diagnostics such as hit rate, false pass rate, false reject rate, and coverage.
- Highlights worst-domain gaps so strong averages do not hide localized regressions.
- Generates a Markdown report for pull requests, audits, experiment notes, and release gates.

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| A domain is missing from the report. | The retrieved documents for that domain were not tagged, or no evaluated records included that domain. | Check that each retrieved document has a consistent domain tag and that the evaluation input includes examples from the missing domain. |
| The overall score improves but one domain looks much worse. | The change may be improving common or easy domains while degrading performance on a smaller or harder source type. | Review the affected domain separately before shipping, and compare examples from that split against the previous run. |
| False pass and false reject rates look unexpected. | The relevance threshold may not match the score scale or behavior of the retriever, reranker, or gate being evaluated. | Confirm the threshold semantics and choose a cutoff that reflects the intended pass or reject decision. |

## FAQ

**Why evaluate by domain instead of using one relevance score?**

A single score can hide uneven behavior. Domain-level evaluation shows whether a system works across the different kinds of content users actually search.

**What kinds of domains can RiftLens compare?**

Any source type that can be tagged in the retrieval data, including notes, wiki nodes, tickets, research summaries, API documentation, policy documents, and internal docs.

**Is RiftLens meant to replace existing RAG metrics?**

No. It complements aggregate metrics by adding split-level diagnostics and worst-domain regression signals.

**Where is the report meant to be used?**

The Markdown report is designed for evaluation reviews, pull requests, release gates, audits, and experiment notes.

## ✅ Verification

Passed automated structure / syntax / selftest checks (see `SKILL.md`).

## Uninstall

Delete the skill folder (`~/.claude/skills/riftlens-domain-collapse-maps-for-rag-evaluation/` or `.claude/skills/riftlens-domain-collapse-maps-for-rag-evaluation/`). Nothing else on your system is touched.

## 📜 Versioning

This skill uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## 🤝 Contributing

This is an auto-generated reference skill. Issues and PRs that improve it are welcome.

## License

MIT
