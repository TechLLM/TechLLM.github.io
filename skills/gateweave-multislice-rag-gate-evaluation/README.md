# GateWeave — Multislice RAG Gate Evaluation

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> Find the RAG gate failures that average metrics hide.

> 🤖 Auto-generated & self-verified skill. A minimal, runnable reference — review before production use.

## What is this?

GateWeave is a proposed open-source benchmark CLI for evaluating whether RAG relevance gates generalize across realistic retrieval conditions. It helps teams move beyond average hit rate by showing where a scorer, router threshold, or reranker performs well overall but fails on specific slices.

The project adapts domain generalization ideas to RAG evaluation. Instead of testing modality combinations, GateWeave tests document fields, missing evidence, corrupted metadata, domain shifts, and document-type groups.

The output is a compact evaluation matrix that makes hidden relevance failures easier to review, compare, and discuss before they reach production.

**Who is this for.** GateWeave is for teams building production RAG systems, especially engineers, ML practitioners, and technical leads who need to compare relevance gates, rerankers, or routing scorers under conditions that resemble real retrieval traffic.

## ⏱ 30-Second Quick Start

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/gateweave-multislice-rag-gate-evaluation
python scripts/run.py --selftest
```

**Expected output:**

```text
{
  "protocol": "gateweave-v0",
  "threshold": 0.5,
  "slice_columns": [
    "domain",
    "doc_type",
    "evidence_field"
  ],
  "missing_field_columns": [
    "evidence_field"
  ],
  "labels": {
    "rows": 8,
    "source": "builtin"
  },
  "scorers": [
    {
      "name": "baseline",
      "rows_evaluated": 8,
      "missing_predictions": 0,
      "extra_predictions": 0,
      "aggregate": {
        "count": 8,
        "tp": 2,
        "fp": 1,
        "fn": 2,
        "tn": 3,
        "precision": 0.666667,
        "recall": 0.5,
        "f1": 0.571429,
        "accuracy": 0.625
      },
      "slices": {
        "domain": [
          {
            "value": "legal",
            "metrics": {
              "count": 3,
              "tp": 1,
              "fp": 0,
              "fn": 0,
              "tn": 2,
              "precision": 1.0,
              "recall": 1.0,
              "f1": 1.0,
              "accuracy": 1.0
            }
          },
          {
            "value": "sales",
            "metrics": {
              "count": 2,
              "tp": 0,
              "fp": 0,
              "fn": 1,
              "tn": 1,
              "precision": 0.0,
              "recall": 0.0,
              "f1": 0.0,
              "accuracy": 0.5
            }
          },
          {
            "value": "support",
            "metrics": {
              "count": 3,
              "tp": 1,
              "fp": 1,
              "fn": 1,
              "tn": 0,
              "precision": 0.5,
              "recall": 0.5,
              "f1": 0.5,
              "accuracy": 0.333333
            }
          }
        ],
        "doc_type": [
          {
            "value": "case_study",
            "metrics": {
              "count": 2,
              "tp": 0,
              "fp": 0,
              "fn": 1,
              "tn": 1,
              "precision": 0.0,
              "recall": 0.0,
              "f1": 0.0,
              "accuracy": 0.5
            }
          },
      
… (+7694 chars truncated)
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
mkdir -p ~/.claude/skills/gateweave-multislice-rag-gate-evaluation
cp -r /tmp/techllm-skills/skills/gateweave-multislice-rag-gate-evaluation/* ~/.claude/skills/gateweave-multislice-rag-gate-evaluation/

# Project-local
mkdir -p .claude/skills/gateweave-multislice-rag-gate-evaluation
cp -r /tmp/techllm-skills/skills/gateweave-multislice-rag-gate-evaluation/* .claude/skills/gateweave-multislice-rag-gate-evaluation/
```

**2) As a standalone CLI**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/gateweave-multislice-rag-gate-evaluation
python scripts/run.py --help
```

**3) Manual download**

On GitHub, open the `skills/gateweave-multislice-rag-gate-evaluation/` folder and download the files, or download the repo ZIP and copy that one folder.

## ⚡ Usage

Full `--help` output:

```text
usage: run.py [-h] [--labels LABELS] [--scorers SCORERS [SCORERS ...]]
              [--threshold THRESHOLD] [--slice-columns SLICE_COLUMNS]
              [--missing-field-columns MISSING_FIELD_COLUMNS]
              [--format {json,markdown}] [--output-json OUTPUT_JSON]
              [--output-md OUTPUT_MD]
              [--write-example-inputs WRITE_EXAMPLE_INPUTS] [--selftest]

Evaluate RAG relevance gates across aggregate, slice, and missing-field stress
metrics.

options:
  -h, --help            show this help message and exit
  --labels LABELS       Labeled CSV with qid, doc_id, label, and optional
                        slice columns.
  --scorers SCORERS [SCORERS ...]
                        One or more scorer CSV files with qid, doc_id, and
                        score or decision.
  --threshold THRESHOLD
                        Score threshold for positive predictions. Default:
                        0.5.
  --slice-columns SLICE_COLUMNS
                        Comma-separated slice columns. Default:
                        domain,doc_type,evidence_field.
  --missing-field-columns MISSING_FIELD_COLUMNS
                        Comma-separated columns for missing-field stress
                        tests.
  --format {json,markdown}
                        Format printed to stdout. Default: json.
  --output-json OUTPUT_JSON
                        Optional path for the JSON report.
  --output-md OUTPUT_MD
                        Optional path for the Markdown report.
  --write-example-inputs WRITE_EXAMPLE_INPUTS
                        Write sample CSV inputs to the given directory and
                        exit.
  --selftest            Run the built-in sample with no external files.
```

## Examples

See the `examples/` folder in this skill (sample input + expected output).

## 🧠 How it works

- Ingests labeled question-document-answer data alongside one or more scorer-output tables.
- Groups examples into controlled slices such as domain, document type, evidence field, and custom metadata categories.
- Measures precision, recall, missing-field stress behavior, and worst-slice performance for each scorer.
- Compares multiple gates or scorers side by side under the same evaluation protocol.
- Produces structured and readable reports for experiment review, CI checks, and pull request discussion.

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Scores look strong overall but weak in one report section. | The gate is likely overfitting to patterns that are common in the full dataset but unreliable in a specific slice. | Inspect the affected slice, review the examples behind it, and adjust the scorer, threshold, or training data to cover that retrieval condition. |
| Some slices appear empty or unexpectedly small. | The input labels or metadata may be missing values needed to form those slices. | Check that the relevant columns are populated consistently and that blank values represent intentional missing evidence rather than annotation drift. |
| Two scorer reports are hard to compare. | The scorer outputs may not refer to the same labeled examples or may use inconsistent identifiers. | Ensure each scorer output aligns to the same evaluation set and uses stable identifiers for matching examples. |

## FAQ

**Is GateWeave a replacement for end-to-end RAG evaluation?**

No. It focuses on relevance gates, rerankers, and routing scorers. It complements answer-quality and user-facing evaluations by isolating whether the retrieval decision layer is robust.

**Why use slice-based evaluation instead of one aggregate metric?**

Aggregate metrics can hide serious failures when a system performs well on common cases but poorly on rare domains, document types, metadata patterns, or missing-evidence situations.

**Can GateWeave compare multiple scorers?**

Yes. It is designed to compare several relevance gates, rerankers, or router scorers under the same labeled protocol so teams can see tradeoffs clearly.

**What kind of data does GateWeave expect?**

It is designed around a CSV-first workflow with labeled examples and scorer outputs, making it compatible with existing annotation pipelines, offline evaluation exports, and experiment logs.

## ✅ Verification

Passed automated structure / syntax / selftest checks (see `SKILL.md`).

## Uninstall

Delete the skill folder (`~/.claude/skills/gateweave-multislice-rag-gate-evaluation/` or `.claude/skills/gateweave-multislice-rag-gate-evaluation/`). Nothing else on your system is touched.

## 📜 Versioning

This skill uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## 🤝 Contributing

This is an auto-generated reference skill. Issues and PRs that improve it are welcome.

## License

MIT
