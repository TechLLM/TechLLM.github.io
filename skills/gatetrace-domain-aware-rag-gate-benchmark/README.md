# GateTrace — Domain-Aware RAG Gate Benchmark

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> Expose where RAG relevance gates fail, not just how they score on average.

> 🤖 Auto-generated & self-verified skill. A minimal, runnable reference — review before production use.

## What is this?

GateTrace is a proposed benchmarking CLI for evaluating RAG relevance gates, retrieval agents, and search-planning systems with domain-aware detail. Instead of reducing evaluation to one aggregate recall score, it shows how performance changes across document types, question patterns, source categories, terminology, and domain tags.

This matters because retrieval systems can look strong on average while failing on the cases that matter most: rare terms, unfamiliar domains, long-tail intents, sparse evidence, or documents that do not resemble the dominant training or test examples. GateTrace is designed to make those hidden failure modes visible before they reach production.

The tool accepts simple structured evaluation data and produces both human-readable and machine-readable reports, making it suitable for pull request review, model cards, CI gates, and evaluation dashboards.

**Who is this for.** GateTrace is for teams building, testing, or maintaining RAG systems, relevance gates, retrieval agents, and search-planning workflows who need to understand not only whether retrieval works, but where it breaks and why.

## ⏱ 30-Second Quick Start

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/gatetrace-domain-aware-rag-gate-benchmark
python scripts/run.py --selftest
```

**Expected output:**

```text
{
  "document_slices": {
    "doc_type": {
      "blog": {
        "false_block_rate": 0.0,
        "false_pass_rate": 0.0,
        "gate_f1": 0.0,
        "gate_pass_rate": 0.0,
        "gate_precision": 0.0,
        "gate_recall": 0.0,
        "relevant_retrieved_count": 0,
        "retrieved_document_count": 1
      },
      "chat": {
        "false_block_rate": 0.0,
        "false_pass_rate": 1.0,
        "gate_f1": 0.0,
        "gate_pass_rate": 1.0,
        "gate_precision": 0.0,
        "gate_recall": 0.0,
        "relevant_retrieved_count": 0,
        "retrieved_document_count": 1
      },
      "faq": {
        "false_block_rate": 0.0,
        "false_pass_rate": 1.0,
        "gate_f1": 0.0,
        "gate_pass_rate": 1.0,
        "gate_precision": 0.0,
        "gate_recall": 0.0,
        "relevant_retrieved_count": 0,
        "retrieved_document_count": 1
      },
      "guideline": {
        "false_block_rate": 1.0,
        "false_pass_rate": 0.0,
        "gate_f1": 0.0,
        "gate_pass_rate": 0.0,
        "gate_precision": 0.0,
        "gate_recall": 0.0,
        "relevant_retrieved_count": 1,
        "retrieved_document_count": 1
      },
      "incident_report": {
        "false_block_rate": 0.0,
        "false_pass_rate": 0.0,
        "gate_f1": 1.0,
        "gate_pass_rate": 1.0,
        "gate_precision": 1.0,
        "gate_recall": 1.0,
        "relevant_retrieved_count": 1,
        "retrieved_document_count": 1
      },
      "manual": {
        "false_block_rate": 0.0,
        "false_pass_rate": 0.0,
        "gate_f1": 1.0,
        "gate_pass_rate": 1.0,
        "gate_precision": 1.0,
        "gate_recall": 1.0,
        "relevant_retrieved_count": 1,
        "retrieved_document_count": 1
      },
      "memo": {
        "false_block_rate": 0.0,
        "false_pass_rate": 0.0,
        "gate_f1": 0.0,
        "gate_pass_rate": 0.0,
        "gate_precision": 0.0,
        "gate_recall": 0.0,
        "relevant_retrieved_count": 0,
        "retrieved_d
… (+10547 chars truncated)
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
mkdir -p ~/.claude/skills/gatetrace-domain-aware-rag-gate-benchmark
cp -r /tmp/techllm-skills/skills/gatetrace-domain-aware-rag-gate-benchmark/* ~/.claude/skills/gatetrace-domain-aware-rag-gate-benchmark/

# Project-local
mkdir -p .claude/skills/gatetrace-domain-aware-rag-gate-benchmark
cp -r /tmp/techllm-skills/skills/gatetrace-domain-aware-rag-gate-benchmark/* .claude/skills/gatetrace-domain-aware-rag-gate-benchmark/
```

**2) As a standalone CLI**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/gatetrace-domain-aware-rag-gate-benchmark
python scripts/run.py --help
```

**3) Manual download**

On GitHub, open the `skills/gatetrace-domain-aware-rag-gate-benchmark/` folder and download the files, or download the repo ZIP and copy that one folder.

## ⚡ Usage

Full `--help` output:

```text
usage: run.py [-h] [--input INPUT] [--format {json,markdown,both}]
              [--json-out JSON_OUT] [--markdown-out MARKDOWN_OUT]
              [--ood-tags OOD_TAGS] [--fail-under-recall FAIL_UNDER_RECALL]
              [--selftest]

Evaluate RAG retrieval and relevance-gate behavior with domain-aware slices.

options:
  -h, --help            show this help message and exit
  --input INPUT         JSONL input file. If omitted, built-in sample data is
                        used.
  --format {json,markdown,both}
                        Report format for stdout or output files.
  --json-out JSON_OUT   Write JSON report to this file.
  --markdown-out MARKDOWN_OUT
                        Write Markdown report to this file.
  --ood-tags OOD_TAGS   Comma-separated tags treated as OOD-like. Defaults to
                        GATETRACE_OOD_TAGS or built-ins.
  --fail-under-recall FAIL_UNDER_RECALL
                        Exit with code 2 if overall retrieval_recall is below
                        this threshold.
  --selftest            Run on built-in sample data and validate the resulting
                        report shape.
```

## Examples

See the `examples/` folder in this skill (sample input + expected output).

## 🧠 How it works

- Slices retrieval and gate metrics by domain tags, document categories, question types, source families, evidence density, and custom metadata.
- Reports recall, precision, F1, and pass-rate behavior separately for retrieval and relevance-gate decisions.
- Highlights false passes, where irrelevant context is allowed through, and false blocks, where useful evidence is stopped before generation.
- Identifies missing-evidence cases where required supporting documents were not retrieved for a query.
- Flags OOD-like query groups using configurable tags such as rare terminology, unfamiliar domains, and long-tail intents.

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| The benchmark looks good overall, but domain slices show weak performance. | Aggregate metrics can hide failures concentrated in specific tags, document types, or query patterns. | Review the weakest slices first and compare false-block, false-pass, and missing-evidence patterns before changing the retriever or gate. |
| Some queries appear in missing-evidence reports unexpectedly. | The required supporting evidence for those queries was not retrieved or was not labeled consistently in the input data. | Check that the evaluation labels identify the required evidence clearly and that domain metadata is attached to the relevant records. |
| OOD-like reports are noisy or too broad. | The tags used to identify rare terms, unfamiliar domains, or long-tail intents may be too general for the dataset. | Refine the tag definitions so they capture meaningful risk groups rather than broad topical categories. |

## FAQ

**Is GateTrace a replacement for standard retrieval metrics?**

No. It complements standard metrics by showing where those metrics come from and which domains, document types, or evidence patterns are driving success or failure.

**Why evaluate relevance gates separately from retrieval?**

A retriever can find useful evidence while a gate blocks it, or a gate can pass irrelevant context that later confuses the generator. Measuring those decisions separately makes the failure mode easier to diagnose.

**Can this be used in CI?**

Yes. GateTrace is intended to produce machine-readable JSON for automated checks as well as Markdown reports for reviewers.

**What kinds of systems can it evaluate?**

It is designed for RAG retrievers, relevance gates, retrieval agents, and search-planning systems where queries, retrieved documents, labels, and metadata can be represented as structured evaluation records.

## ✅ Verification

Passed automated structure / syntax / selftest checks (see `SKILL.md`).

## Uninstall

Delete the skill folder (`~/.claude/skills/gatetrace-domain-aware-rag-gate-benchmark/` or `.claude/skills/gatetrace-domain-aware-rag-gate-benchmark/`). Nothing else on your system is touched.

## 📜 Versioning

This skill uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## 🤝 Contributing

This is an auto-generated reference skill. Issues and PRs that improve it are welcome.

## License

MIT
