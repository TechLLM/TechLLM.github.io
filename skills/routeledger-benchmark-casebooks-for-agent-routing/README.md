# RouteLedger — Benchmark Casebooks for Agent Routing

RouteLedger converts agent-routing JSONL logs into deterministic benchmark casebooks. It validates core router metadata, creates stratified train/validation/test splits, and exports JSON, JSONL, CSV, and Markdown summaries.

## Install

```bash
python --version
python scripts/run.py --help
```

No third-party packages are required.

## Usage

Run the built-in self-test sample:

```bash
python scripts/run.py --selftest
python scripts/test.py
```

Build a casebook from the bundled example:

```bash
python scripts/run.py --input examples/routing_logs.jsonl --seed 7 --output-dir out
```

This writes:

- `out/manifest.json`
- `out/cases.jsonl`
- `out/cases.csv`
- `out/summary.md`

Optional environment defaults:

```bash
ROUTELEDGER_SEED=7 python scripts/run.py --input examples/routing_logs.jsonl
ROUTELEDGER_SPLIT_RATIOS=0.6,0.2,0.2 python scripts/run.py --selftest
```

## Example Expected Output

For:

```bash
python scripts/run.py --input examples/routing_logs.jsonl --seed 7
```

Expected compact output is shown in `examples/expected_output.json`.

## Input JSONL Fields

Each line should be a JSON object with:

- `id` or `task_id`
- `task`
- `modality`
- `domain`
- `selected_tool`
- `task_type`
- `outcome` with success/failure text, or `success` as a boolean-like value

Invalid records are reported in the manifest. Use `--strict` to fail on any schema error.
