# Maskwright — Sensitivity Auditor for RAG and Tool Routing

Maskwright is a small installable skill for diagnosing RAG and tool-routing failures with leave-one-out candidate masking and span masking. It runs without dependencies using a deterministic lexical scorer, or it can call your scorer through a simple stdin/stdout JSON contract.

## Quick Install

Copy this directory into your skills folder, then verify:

```bash
python3 scripts/run.py --help
python3 scripts/run.py --selftest
python3 scripts/test.py
```

## Usage

Run the sample:

```bash
python3 scripts/run.py --input examples/sample_input.json
```

Write CSV artifacts:

```bash
python3 scripts/run.py --input examples/sample_input.json --output-dir maskwright_out
```

Use an external scorer command:

```bash
MASKWRIGHT_SCORER_COMMAND="python3 examples/mock_scorer.py" python3 scripts/run.py --input examples/sample_input.json
```

Show all options:

```bash
python3 scripts/run.py --help
```

## Expected Output

```json
{
  "artifacts": {},
  "base_correct_rank": 1,
  "base_entropy": 1.059277,
  "base_margin": 0.45581,
  "base_top_id": "tool-password-reset",
  "correct_id": "tool-password-reset",
  "failure_labels": [
    "keyword-overreliance"
  ],
  "most_sensitive_candidate": {
    "entropy_change": -0.416189,
    "failure_signal": "low-impact",
    "margin_change": 0.193583,
    "removed_candidate_id": "tool-user-search"
  },
  "most_sensitive_span": {
    "candidate_id": "tool-user-search",
    "candidate_score_delta": -0.361333,
    "failure_signal": "keyword-overreliance",
    "span_end": 8,
    "span_start": 4,
    "span_text": "admin console by email"
  },
  "query": "reset user password admin console"
}
```

## Input Shape

```json
{
  "query": "reset user password admin console",
  "correct_id": "tool-password-reset",
  "candidates": [
    {
      "id": "tool-password-reset",
      "text": "Reset a user's password from the admin console and send a temporary login link."
    }
  ]
}
```

## Environment Variables

- `MASKWRIGHT_SCORER_COMMAND`: external scorer command.
- `MASKWRIGHT_SPAN_SIZE`: token count for each masked span.
- `MASKWRIGHT_SCORE_TIMEOUT`: scorer timeout in seconds.
