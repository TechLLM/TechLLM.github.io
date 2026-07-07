# TraceMint — Positive Trace Mining for Agent Improvement

TraceMint is an installable experimental skill with a small CLI that mines grader-passing AI agent execution logs into reusable positive trace datasets.

## Install

Place this directory in your skills folder, or run the reference CLI directly:

```bash
python scripts/run.py --help
```

No dependencies are required beyond Python 3.

## Usage

Run the built-in self-test:

```bash
python scripts/run.py --selftest
```

Mine the included example:

```bash
python scripts/run.py \
  --input examples/sample.jsonl \
  --out-jsonl build/traces.jsonl \
  --out-md build/traces.md
```

Expected summary:

```json
{"input_runs": 2, "markdown_path": "build/traces.md", "output_path": "build/traces.jsonl", "passing_traces": 1, "status": "ok"}
```

Run the import-level test:

```bash
python scripts/test.py
```

Expected output:

```text
scripts/test.py: ok
```

## Redaction

TraceMint includes basic redaction for secret-like assignments and absolute paths. Add project-specific patterns with:

```bash
python scripts/run.py \
  --input examples/sample.jsonl \
  --out-jsonl build/traces.jsonl \
  --redact-regex "internal-project-[0-9]+"
```

You can also set:

```bash
TRACEMINT_REDACT_PATTERNS='["customer-[0-9]+", "private-team-name"]' \
python scripts/run.py --input examples/sample.jsonl --out-jsonl build/traces.jsonl
```

## Example Files

- `examples/sample.jsonl`: tiny input log with one passing run and one failing run.
- `examples/expected.jsonl`: expected machine-readable positive trace output.
- `examples/expected.md`: expected Markdown review output.
