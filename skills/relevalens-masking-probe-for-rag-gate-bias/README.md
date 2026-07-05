# RelevaLens - Masking Probe for RAG Gate Bias

Minimal installable skill for diagnosing shortcut bias in RAG relevance gates with offline JSONL score logs.

## Install

No dependencies are required beyond Python 3.9 or newer.

```bash
python scripts/run.py --help
python scripts/test.py
```

## Quick Start

Run the built-in self-test:

```bash
python scripts/run.py --selftest
```

Analyze the included example files:

```bash
python scripts/run.py \
  --queries examples/queries.jsonl \
  --candidates examples/candidates.jsonl \
  --scores examples/scores.jsonl
```

Write Markdown and CSV reports:

```bash
python scripts/run.py \
  --queries examples/queries.jsonl \
  --candidates examples/candidates.jsonl \
  --scores examples/scores.jsonl \
  --out-dir out
```

Generate external evaluation prompts:

```bash
python scripts/run.py \
  --queries examples/queries.jsonl \
  --candidates examples/candidates.jsonl \
  --scores examples/scores.jsonl \
  --prompt-set out/prompts.jsonl
```

Optional adapter credentials can be supplied through `RELEVALENS_ADAPTER_KEY`, but the included offline analysis does not require a key and never prints secrets.

## Expected Output

The self-test and example data produce a Markdown report beginning with:

```text
# RelevaLens Report

## Summary
- query_count: 1
- candidate_count: 3
- score_count: 12
- mean_normalized_entropy: 0.8693
- mean_top1_concentration: 0.5027
- mean_mask_sensitivity: 0.1778
- mean_rank_instability: 0.2222
- mean_position_skew: 0.1694
- flags: position_skew, rank_instability
```

See `examples/expected_output.md` for the full expected report.
