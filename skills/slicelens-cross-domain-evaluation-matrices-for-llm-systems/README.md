# SliceLens — Cross-Domain Evaluation Matrices for LLM Systems

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> Find where LLM systems fail to generalize, not just where they average well.

> 🤖 Auto-generated & self-verified skill. A minimal, runnable reference — review before production use.

## What is this?

SliceLens is a proposed open-source CLI for turning ordinary evaluation CSV files into diagnostic performance matrices for LLM, RAG, and agent systems. It is designed for teams that need to understand how results vary across domains, question types, document types, modalities, and robustness conditions.

Most evaluation summaries compress everything into one average score. That can hide serious failures: a system may look improved overall while getting worse on legal documents, ambiguous questions, missing metadata, or out-of-domain inputs. SliceLens makes those weak slices visible.

The goal is to treat benchmark reports as engineering diagnostics rather than leaderboards. SliceLens highlights mean performance, worst-slice performance, domain gaps, degradation under missing fields or corruption, and source-to-target transfer patterns in a report that can be used in model cards, pull requests, release notes, and regression reviews.

**Who is this for.** SliceLens is for ML engineers, evaluation teams, RAG builders, agent developers, technical writers, and open-source maintainers who need clearer evidence about where an LLM system works, where it fails, and whether a reported improvement actually generalizes.

## ⏱ 30-Second Quick Start

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/slicelens-cross-domain-evaluation-matrices-for-llm-systems
python scripts/run.py --selftest
```

**Expected output:**

```text
# SliceLens Evaluation Report

## Summary

| Metric | Value |
| --- | --- |
| Rows | 12 |
| Overall mean | 0.653 |
| Score column | score |
| Worst-slice min count | 2 |

## Worst Slice

| Dimension | Value | Mean | Count |
| --- | --- | --- | --- |
| condition | missing_metadata | 0.413 | 3 |

## Source-to-Target Transfer Matrix

| source_domain \ target_domain | finance | legal | medical |
| --- | --- | --- | --- |
| finance | 0.895 (n=2) | 0.580 (n=1) | 0.390 (n=1) |
| legal | 0.620 (n=1) | 0.800 (n=2) | 0.440 (n=1) |
| medical | 0.410 (n=1) | 0.550 (n=1) | 0.730 (n=2) |

## Domain Gaps

| Source domain | In-domain mean | In n | Out-domain mean | Out n | Gap |
| --- | --- | --- | --- | --- | --- |
| finance | 0.895 | 2 | 0.485 | 2 | 0.410 |
| legal | 0.800 | 2 | 0.530 | 2 | 0.270 |
| medical | 0.730 | 2 | 0.480 | 2 | 0.250 |

## Slice Tables

### condition

| Value | Mean | Count |
| --- | --- | --- |
| missing_metadata | 0.413 | 3 |
| format_shift | 0.610 | 3 |
| clean | 0.795 | 6 |

### document_type

| Value | Mean | Count |
| --- | --- | --- |
| (missing) | 0.410 | 1 |
| csv | 0.627 | 3 |
| pdf | 0.667 | 7 |
| html | 0.880 | 1 |

### modality

| Value | Mean | Count |
| --- | --- | --- |
| image | 0.600 | 1 |
| text | 0.658 | 11 |

### question_type

| Value | Mean | Count |
| --- | --- | --- |
| ambiguous | 0.460 | 4 |
| comparison | 0.613 | 4 |
| fact | 0.888 | 4 |

### source_domain

| Value | Mean | Count |
| --- | --- | --- |
| medical | 0.605 | 4 |
| legal | 0.665 | 4 |
| finance | 0.690 | 4 |

### target_domain

| Value | Mean | Count |
| --- | --- | --- |
| medical | 0.573 | 4 |
| legal | 0.683 | 4 |
| finance | 0.705 | 4 |

## Missing-Field Degradation

| Field | Present mean | Present n | Missing mean | Missing n | Degradation |
| --- | --- | --- | --- | --- | --- |
| source_domain | 0.653 | 12 | n/a | 0 | n/a |
| target_domain | 0.653 | 12 | n/a | 0 | n/a |
| question_type | 0.653 | 12 | n/a | 0 | n/a |
| document_type | 0.675 | 11 | 0.410 | 1 | 0.
… (+90 chars truncated)
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
mkdir -p ~/.claude/skills/slicelens-cross-domain-evaluation-matrices-for-llm-systems
cp -r /tmp/techllm-skills/skills/slicelens-cross-domain-evaluation-matrices-for-llm-systems/* ~/.claude/skills/slicelens-cross-domain-evaluation-matrices-for-llm-systems/

# Project-local
mkdir -p .claude/skills/slicelens-cross-domain-evaluation-matrices-for-llm-systems
cp -r /tmp/techllm-skills/skills/slicelens-cross-domain-evaluation-matrices-for-llm-systems/* .claude/skills/slicelens-cross-domain-evaluation-matrices-for-llm-systems/
```

**2) As a standalone CLI**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/slicelens-cross-domain-evaluation-matrices-for-llm-systems
python scripts/run.py --help
```

**3) Manual download**

On GitHub, open the `skills/slicelens-cross-domain-evaluation-matrices-for-llm-systems/` folder and download the files, or download the repo ZIP and copy that one folder.

## ⚡ Usage

Full `--help` output:

```text
usage: run.py [-h] [--input INPUT] [--output OUTPUT]
              [--score-column SCORE_COLUMN] [--source-column SOURCE_COLUMN]
              [--target-column TARGET_COLUMN] [--slice-columns SLICE_COLUMNS]
              [--min-count MIN_COUNT] [--precision PRECISION] [--json]
              [--selftest]

Generate cross-domain SliceLens evaluation matrices from a CSV file. Runs a
built-in no-key self-test when --selftest is provided or no input is set.

options:
  -h, --help            show this help message and exit
  --input INPUT         Evaluation CSV path. Defaults to SLICELENS_INPUT, then
                        built-in sample for self-test.
  --output OUTPUT       Markdown report path. Defaults to stdout or
                        SLICELENS_OUTPUT.
  --score-column SCORE_COLUMN
                        Numeric score column. Default: score.
  --source-column SOURCE_COLUMN
                        Source-domain column. Default: source_domain.
  --target-column TARGET_COLUMN
                        Target-domain column. Default: target_domain.
  --slice-columns SLICE_COLUMNS
                        Comma-separated optional categorical columns. Default:
                        question_type,document_type,modality,condition.
  --min-count MIN_COUNT
                        Minimum rows for worst-slice eligibility. Default: 2.
  --precision PRECISION
                        Decimal places for numeric output. Default: 3.
  --json                Emit the raw analysis dictionary as deterministic JSON
                        instead of Markdown.
  --selftest            Run on built-in sample data without any API key or
                        external service.
```

## Examples

See the `examples/` folder in this skill (sample input + expected output).

## 🧠 How it works

- Reads existing evaluation exports in CSV form, so teams can use results from their current benchmark or regression pipeline.
- Groups results into controlled slices such as source domain, target domain, question type, document type, modality, and robustness condition.
- Computes diagnostic metrics including mean score, worst-slice score, domain gaps, missing-field degradation, and source-to-target transfer patterns.
- Turns sliced results into performance matrices that make generalization failures easier to inspect and compare.
- Exports a polished Markdown narrative suitable for engineering reviews, model documentation, and release artifacts.

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| The report looks too broad to explain a failure clearly. | The input data may not include enough slice columns to separate domains, question types, document types, or conditions. | Add the relevant metadata columns to the evaluation export so SliceLens can compare performance across meaningful groups. |
| A system appears strong on the mean score but weak in the report. | The average is hiding uneven performance across domains or conditions. | Use the worst-slice, domain-gap, and transfer-matrix sections to identify the specific distribution where performance drops. |
| Missing-field or corruption analysis is empty. | The evaluation data does not label rows with missing metadata, corrupted inputs, or other robustness conditions. | Annotate affected examples with explicit condition labels before generating the report. |

## FAQ

**Is SliceLens a replacement for my existing evaluation pipeline?**

No. SliceLens is intended to sit after existing evaluation runs. It consumes exported results and turns them into cross-domain diagnostic reports.

**Why not just report average accuracy or hit rate?**

Averages are useful but incomplete. They can hide regressions in rare, difficult, or out-of-domain cases. SliceLens keeps the average while also showing where the system fails to generalize.

**Can this be used for RAG evaluations?**

Yes. SliceLens is especially useful for RAG systems because retrieval and answer quality often vary by document type, domain, question type, metadata quality, and input corruption.

**Can this help with agent or router evaluations?**

Yes. Agent routing and tool-selection systems can look accurate in aggregate while failing on specific domains or input formats. SliceLens is designed to expose those patterns.

**What kind of output does SliceLens produce?**

It produces a Markdown report that summarizes slice-level performance, weak distributions, domain gaps, robustness degradation, and transfer matrices in a format suitable for review and documentation.

## ✅ Verification

Passed automated structure / syntax / selftest checks (see `SKILL.md`).

## Uninstall

Delete the skill folder (`~/.claude/skills/slicelens-cross-domain-evaluation-matrices-for-llm-systems/` or `.claude/skills/slicelens-cross-domain-evaluation-matrices-for-llm-systems/`). Nothing else on your system is touched.

## 📜 Versioning

This skill uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## 🤝 Contributing

This is an auto-generated reference skill. Issues and PRs that improve it are welcome.

## License

MIT
