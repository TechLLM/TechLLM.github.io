---
name: claimweaver-principle-guided-consensus-reducer-for-agent-out
description: Merge multiple agent outputs into auditable claim-level consensus when using trigger keywords like ClaimWeaver, consensus reducer, agent output merge, claim scoring, or principle-guided review.
license: MIT
---

# ClaimWeaver - Principle-Guided Consensus Reducer for Agent Outputs
Auto-generated and experimental; review outputs before using them for high-stakes decisions.

## Overview
Parallel agents often produce overlapping, conflicting, or weakly supported findings, and a final answer is only as good as the reduction step. ClaimWeaver decomposes agent outputs into individual claims, scores each claim against explicit principles, deduplicates near matches, and preserves source passages for auditability. The included CLI is a deterministic standard-library reference implementation with optional rubric input.

## When to use
- Use when several LLM agents independently research, review, summarize, or analyze the same task and their outputs must be merged.
- Use for claim-level consensus, source-aware synthesis, agent provenance tracking, principle-guided review, or reducing parallel agent outputs.
- Use when trigger keywords appear: `ClaimWeaver`, `consensus reducer`, `agent output merge`, `claim scoring`, `principle-guided review`, `evidence-aware merging`.
- When NOT to use: do not use this as a substitute for expert judgment, legal review, medical review, or direct source verification.

## Workflow
1. Collect agent outputs in JSON, Markdown, or plain text. For multiple agents, prefer JSON with an `agents` array containing `id` and `output`.
2. Define review principles in a small YAML or JSON rubric, or use the built-in deterministic default principles.
3. Run `python scripts/run.py INPUT --rubric RUBRIC --format json` to produce machine-readable reduction output.
4. Inspect each claim's `status`, `confidence`, `principle_scores`, `rationale`, and `supporting_sources`.
5. Re-run with `--format markdown` when a readable review document is needed.
6. Treat `needs_review` and `rejected` claims as prompts for manual verification or another agent pass.

## Inputs & Outputs
Input contract:
- JSON input may contain `task` and `agents`.
- Each agent object should contain `id` or `name`, plus `output`, `text`, or `claims`.
- `output` may be Markdown/plain text, a list of claim strings, or JSON claim objects with `text` and optional `evidence`.
- Plain text input is accepted as one anonymous agent.
- Rubrics may be JSON or a simple YAML file with `principles`, where each principle has `id`, `description`, optional `weight`, optional `positive_keywords`, and optional `negative_keywords`.

Exact JSON output shape:
```json
{
  "metadata": {
    "tool": "ClaimWeaver",
    "version": "0.1.0",
    "evaluator": "rule",
    "claim_count": 0,
    "accepted": 0,
    "needs_review": 0,
    "rejected": 0
  },
  "task": "",
  "principles": [
    {"id": "", "description": "", "weight": 1.0}
  ],
  "claims": [
    {
      "claim_id": "cw-001",
      "status": "accepted",
      "confidence": 0.0,
      "text": "",
      "rationale": "",
      "supporting_agents": [],
      "supporting_sources": [
        {"agent": "", "passage": ""}
      ],
      "principle_scores": [
        {"id": "", "score": 0.0, "rationale": ""}
      ]
    }
  ],
  "accepted": [],
  "needs_review": [],
  "rejected": []
}
```

## Installation
Copy this folder into a Claude Code or OpenClaw-compatible skills directory, then verify the reference CLI:

```bash
python3 scripts/run.py --selftest
python3 scripts/test.py
```

No third-party packages are required.

## Usage
Show help:

```bash
python3 scripts/run.py --help
```

Run the built-in self-test sample:

```bash
python3 scripts/run.py --selftest
```

Reduce example agent outputs to JSON:

```bash
python3 scripts/run.py examples/agent_outputs.json --rubric examples/rubric.yaml --format json
```

Reduce example agent outputs to Markdown:

```bash
python3 scripts/run.py examples/agent_outputs.json --rubric examples/rubric.yaml --format markdown
```

Write output to a file:

```bash
python3 scripts/run.py examples/agent_outputs.json --rubric examples/rubric.yaml --output examples/actual_output.json
```

Optional environment variables:
- `CLAIMWEAVER_ACCEPT_THRESHOLD`: numeric acceptance threshold, default `0.62`.
- `CLAIMWEAVER_REVIEW_THRESHOLD`: numeric review threshold, default `0.45`.
- `CLAIMWEAVER_SIMILARITY_THRESHOLD`: duplicate threshold, default `0.86`.
- `CLAIMWEAVER_EVALUATOR`: currently read for future plugin compatibility; this reference implementation always uses deterministic `rule` scoring.
- `CLAIMWEAVER_API_KEY`: may be present for external wrappers, but this script never prints or requires it.

## Example
Command:

```bash
python3 scripts/run.py examples/agent_outputs.json --rubric examples/rubric.yaml --format json
```

Expected output summary:

```json
{
  "metadata": {
    "tool": "ClaimWeaver",
    "version": "0.1.0",
    "evaluator": "rule",
    "claim_count": 7,
    "accepted": 5,
    "needs_review": 0,
    "rejected": 2
  }
}
```

The full expected output is in `examples/expected_output.json`.

## Limitations
- The reference scorer is deterministic and heuristic; it is not a semantic truth verifier.
- The YAML parser intentionally supports only simple rubric files.
- Near-duplicate detection uses standard-library similarity heuristics and may miss paraphrases.
- Source passages are provenance links from agent outputs, not proof that the underlying claim is true.
