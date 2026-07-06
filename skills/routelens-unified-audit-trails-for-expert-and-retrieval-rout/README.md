# RouteLens

RouteLens is an experimental installable skill and small reference CLI for auditing routing decisions across retrieval-augmented generation and expert/model-path execution.

## Install

Copy this folder into a Claude Code or OpenClaw-compatible skills directory. No third-party dependencies are required.

```bash
python --version
python scripts/run.py --help
```

## Usage

Run the built-in self-test sample:

```bash
python scripts/run.py --selftest
```

Audit the included example JSONL logs:

```bash
python scripts/run.py --input examples/sample_logs.jsonl
```

Write output to a file:

```bash
python scripts/run.py --input examples/sample_logs.jsonl --output audit.json
```

Run the import-based test:

```bash
python scripts/test.py
```

## Expected Output

The command below:

```bash
python scripts/run.py --input examples/sample_logs.jsonl
```

prints JSON matching `examples/expected_output.json`. The summary is:

```json
{
  "total_queries": 6,
  "successes": 3,
  "failures": 3,
  "fallback_used": 3,
  "average_quality_score": 0.715,
  "average_subset_quality_gap": 0.14
}
```

## Input Format

Use JSONL with one query per line. Include fields such as `intended_domain`, `selected_index`, `selected_model_path`, `quality_score`, `selected_path_score`, `full_model_score`, `fallback_attempts`, and `outcome`.
