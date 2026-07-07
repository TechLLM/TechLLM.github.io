# ClaimWeaver

ClaimWeaver is an installable experimental skill for reducing multiple agent outputs into an auditable claim-level consensus. It includes a deterministic standard-library CLI and a tiny test script.

## Install

Copy this folder into your Claude Code or OpenClaw-compatible skills directory. No third-party packages are required.

Verify:

```bash
python3 scripts/run.py --selftest
python3 scripts/test.py
```

## Usage

Show help:

```bash
python3 scripts/run.py --help
```

Run the built-in sample:

```bash
python3 scripts/run.py --selftest
```

Run the included example:

```bash
python3 scripts/run.py examples/agent_outputs.json --rubric examples/rubric.yaml --format json
```

Create Markdown output:

```bash
python3 scripts/run.py examples/agent_outputs.json --rubric examples/rubric.yaml --format markdown
```

## Expected Output

The example should produce a JSON object with this metadata summary:

```json
{
  "tool": "ClaimWeaver",
  "version": "0.1.0",
  "evaluator": "rule",
  "claim_count": 7,
  "accepted": 5,
  "needs_review": 0,
  "rejected": 2
}
```

The full expected example output is in `examples/expected_output.json`.
