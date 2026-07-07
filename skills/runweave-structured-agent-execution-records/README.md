# RunWeave - Structured Agent Execution Records

RunWeave converts shell execution logs and lightweight YAML plans into a normalized `agent_run_record.json` for debugging, replay, comparison, and audit-oriented agent development.

## Install

Place this folder in your agent runtime's skills directory, then verify the bundled CLI:

```bash
python scripts/run.py --help
python scripts/test.py
```

No third-party dependencies are required.

## Usage

Run the deterministic built-in sample:

```bash
python scripts/run.py --selftest
```

Create a record from the included example files:

```bash
python scripts/run.py \
  --plan examples/sample_plan.yaml \
  --log examples/sample_log.txt \
  --output agent_run_record.json
```

Append a compact JSONL entry for long-running workflows:

```bash
python scripts/run.py \
  --plan examples/sample_plan.yaml \
  --log examples/sample_log.txt \
  --append-run-log runs.jsonl
```

## Expected Output

The example command emits a JSON object with this summary:

```json
{
  "planned_steps": 2,
  "executed_steps": 2,
  "matched_steps": 2,
  "failed_steps": 1,
  "missing_planned_steps": 0,
  "repair_candidates": 1
}
```

The full expected output is stored at `examples/expected_agent_run_record.json`.
