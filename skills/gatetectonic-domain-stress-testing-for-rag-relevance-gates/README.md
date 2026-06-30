# GateTectonic Skill

GateTectonic is an installable skill for stress testing RAG relevance gates across domains, document types, question types, missing context, and corrupted inputs.

## Install

Copy this directory into your Claude Code or OpenClaw-compatible skills folder.

No third-party Python packages are required.

## Run

```bash
python scripts/run.py
```

With the included example:

```bash
python scripts/run.py --input examples/sample.csv
```

Custom outputs:

```bash
python scripts/run.py --input examples/sample.csv --out-json reports/gatetectonic.json --out-md reports/gatetectonic.md
```

## Input Format

Use a CSV with these columns:

```text
question,document,label,source_domain,document_type,question_type
```

`label` accepts `1`, `true`, `yes`, or `relevant` for relevant pairs, and `0`, `false`, `no`, or `irrelevant` for irrelevant pairs.

## Output

The CLI writes a JSON report and a Markdown report containing:

- Aggregate fixed-gate and ERM baseline metrics
- Leave-one-domain-out evaluation
- Stress slices by domain, document type, question type, and variant
- Absolute and relative gain against the ERM baseline
