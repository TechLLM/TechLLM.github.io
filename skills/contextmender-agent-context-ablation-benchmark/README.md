# ContextMender Agent Context Ablation Benchmark

ContextMender is a small installable skill and CLI for generating missing-context benchmark variants for LLM agent task datasets.

## Install

Copy this folder into a Claude Code or OpenClaw-compatible skills directory.

No dependency installation is required. The CLI uses only the Python standard library.

## Run

Use built-in sample data:

```bash
python scripts/run.py
```

Use the example dataset:

```bash
python scripts/run.py --input examples/tasks.jsonl --output-dir outputs/example-run
```

Generate variants for selected fields:

```bash
python scripts/run.py --input examples/tasks.jsonl --fields retrieval,memory,tools,dialogue,policies
```

Outputs are written under the selected output directory:

- `baseline.full_context.jsonl`
- `variants/missing_<field>.jsonl`
- `grading_templates/missing_<field>.md`
- `manifest.json`

## Input Format

Each line in the input file is one JSON object. Plain field names in `--fields` are resolved under the `context` object when it exists. Dotted field names target exact nested paths.

See `examples/tasks.jsonl` for a tiny dataset.
