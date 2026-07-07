---
name: maskwright-sensitivity-auditor-for-rag-and-tool-routing
description: Audits RAG and tool-routing candidate sensitivity with leave-one-out and span masking and should be used for trigger keywords including RAG debugging, tool routing, router failure, retrieval miss, candidate masking, sensitivity audit, and ranking shift.
license: MIT
---

# Maskwright — Sensitivity Auditor for RAG and Tool Routing
Auto-generated and experimental; validate findings before using them for production tuning.

## Overview
Maskwright helps diagnose why an LLM application selected the wrong document, memory, tool, action, or router option. It separates likely failure causes by masking candidates and text spans, rescoring the remaining set, and summarizing how ranks, margins, entropy, and labels change.

The bundled script is model-agnostic: it can call a user-provided scorer command or run a deterministic built-in lexical scorer for local smoke tests.

## When to use
- Use when a RAG pipeline retrieves the wrong document or ranks the known correct document too low.
- Use when an agent router selects the wrong tool, action, memory, policy, or workflow branch.
- Use when candidates look semantically similar and you need to distinguish ambiguity from missing knowledge.
- Use when you suspect position bias, brittle keyword reliance, or misleading tool descriptions.
- Use when you need CSV artifacts for dashboard, notebook, or heatmap inspection.

When NOT to use: do not use Maskwright as the primary scorer, retriever, or policy engine; it is a diagnostic layer around an existing scorer.

## Workflow
1. Collect the query, candidate list, and known correct candidate id from the failing RAG or routing case.
2. Put the data into the JSON input shape shown in Inputs & Outputs.
3. Decide whether to use the built-in lexical scorer or provide an external scorer command through `--scorer-command` or `MASKWRIGHT_SCORER_COMMAND`.
4. Run `scripts/run.py` with `--input` and optionally `--output-dir`.
5. Review the summary fields first: `base_top_id`, `base_correct_rank`, `base_margin`, `failure_labels`, `most_sensitive_candidate`, and `most_sensitive_span`.
6. Inspect `candidate_sensitivity.csv` for leave-one-out effects across documents, tools, memories, actions, or router options.
7. Inspect `span_sensitivity.csv` for phrase-level or description-level sensitivity.
8. Use the labels to choose the next intervention: add missing knowledge, reduce ambiguous candidates, rebalance candidate order, rewrite brittle descriptions, or tune the external scorer.

## Inputs & Outputs
Input JSON fields:

```json
{
  "query": "reset user password admin console",
  "correct_id": "tool-password-reset",
  "candidates": [
    {
      "id": "tool-password-reset",
      "text": "Reset a user's password from the admin console and send a temporary login link.",
      "position": 0
    }
  ]
}
```

Required fields are `query`, `correct_id`, and `candidates[].id` plus `candidates[].text`. `position` is optional and defaults to input order.

External scorer command contract:

- Maskwright sends JSON on stdin: `{"query": "...", "candidates": [{"id": "...", "text": "...", "position": 0}]}`
- The command returns JSON on stdout as either `{"scores": [{"id": "...", "score": 0.42}]}` or `{"candidate-id": 0.42}`
- Scores must be numeric and must cover every candidate id in the request.

Console summary output shape:

```json
{
  "artifacts": {},
  "base_correct_rank": 1,
  "base_entropy": 1.059277,
  "base_margin": 0.45581,
  "base_top_id": "tool-password-reset",
  "correct_id": "tool-password-reset",
  "failure_labels": ["keyword-overreliance"],
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

When `--output-dir` is provided, Maskwright also writes:

- `summary.json`
- `candidate_sensitivity.csv`
- `span_sensitivity.csv`

Candidate CSV fields are `removed_candidate_id`, `removed_was_correct`, `base_top_id`, `masked_top_id`, `base_correct_rank`, `masked_correct_rank`, `correct_rank_delta`, `correct_score_delta`, `base_margin`, `masked_margin`, `margin_change`, `base_entropy`, `masked_entropy`, `entropy_change`, and `failure_signal`.

Span CSV fields are `candidate_id`, `span_start`, `span_end`, `span_text`, `base_candidate_score`, `masked_candidate_score`, `candidate_score_delta`, `base_correct_rank`, `masked_correct_rank`, `correct_rank_delta`, `margin_change`, `entropy_change`, and `failure_signal`.

## Installation
Copy this skill directory into a Claude Code or OpenClaw-compatible skills location, then run the local checks:

```bash
python3 scripts/run.py --help
python3 scripts/run.py --selftest
python3 scripts/test.py
```

No package install is required because the reference implementation uses only the Python standard library.

## Usage
Run the built-in sample:

```bash
python3 scripts/run.py --selftest
```

Run an example input and write artifacts:

```bash
python3 scripts/run.py --input examples/sample_input.json --output-dir maskwright_out
```

Use an external scorer:

```bash
MASKWRIGHT_SCORER_COMMAND="python3 examples/mock_scorer.py" python3 scripts/run.py --input examples/sample_input.json
```

Get command help:

```bash
python3 scripts/run.py --help
```

## Example
Command:

```bash
python3 scripts/run.py --input examples/sample_input.json
```

Expected output:

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

## Limitations
- The built-in scorer is only a deterministic smoke-test scorer, not a substitute for your production retriever, reranker, or router.
- Labels are heuristic and should be treated as diagnostic hints.
- Span masking uses token chunks rather than linguistic phrases.
- External scorers must be deterministic if you want stable diffs and repeatable CSV artifacts.
