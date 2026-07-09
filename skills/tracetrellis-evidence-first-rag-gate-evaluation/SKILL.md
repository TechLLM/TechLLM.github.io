---
name: tracetrellis-evidence-first-rag-gate-evaluation
description: Offline evaluator for RAG relevance gates and evidence-routing traces; use when trigger keywords include rag-evidence-grader, RAG gate evaluation, retrieval trace scoring, evidence manifest, or CI regression.
version: 0.1.0
license: MIT
---

# TraceTrellis - Evidence-First RAG Gate Evaluation
Auto-generated and experimental; verify outputs before using for critical release decisions.

## Overview
RAG systems can produce plausible final answers while still routing the wrong evidence through a relevance gate. TraceTrellis evaluates observable execution evidence instead: selected documents, action logs, answer citations, and expected data artifacts. The bundled `rag-evidence-grader` reference CLI runs fully offline and emits deterministic retrieval, action, and data-accuracy scores.

## When to use
- Use when validating RAG relevance gates, Gate2-style filters, agentic retrieval policies, or evidence-routing layers.
- Use when a benchmark needs to detect missing required documents, forbidden document leakage, unsupported answer citations, or broken trace actions.
- Use in CI regression checks where JSONL traces and evidence manifests should pass before a retrieval change ships.
- Use when privacy or reproducibility requirements rule out LLM-only grading.
- When NOT to use: do not use this as the only judge of answer quality, fluency, or user satisfaction.

## Workflow
1. Export each RAG run as one JSON object per line with a stable `run_id`, selected evidence, actions, and any extracted facts.
2. Write an evidence manifest listing each case's `required_documents`, `optional_documents`, `forbidden_documents`, `required_actions`, and `expected_facts`.
3. Optionally provide final-answer records with citations or an LLM-judge JSON file as an additional signal.
4. Run `python scripts/run.py --traces <trace.jsonl> --manifest <manifest.json>`.
5. Inspect the JSON summary and each case's `failures` array.
6. Fail CI when the CLI exits nonzero or when any case has unacceptable retrieval, action, or data-accuracy scores.

## Inputs & Outputs
Input trace JSONL: each line is a JSON object with `run_id`, evidence fields such as `selected_documents`, `selected_nodes`, `retrieved_documents`, or `retrieval_results`, optional `actions`, and optional `artifacts.facts`.

Input manifest JSON:

```json
{
  "cases": [
    {
      "run_id": "refund-window",
      "required_documents": ["policy/refunds-2026"],
      "optional_documents": ["faq/refunds"],
      "forbidden_documents": ["policy/refunds-2021"],
      "required_actions": [{"type": "cite", "target": "policy/refunds-2026"}],
      "expected_facts": {"refund_window_days": 30}
    }
  ]
}
```

Optional answers JSON or JSONL: records keyed by `run_id` or containing `run_id`, `text`, and `citations`.

Output shape:

```json
{
  "tool": "rag-evidence-grader",
  "version": "0.1.0",
  "summary": {
    "cases": 1,
    "passed": 1,
    "failed": 0,
    "pass_rate": 1.0,
    "average_scores": {
      "retrieval": 1.0,
      "action": 1.0,
      "data_accuracy": 1.0,
      "overall": 1.0
    }
  },
  "cases": [
    {
      "run_id": "refund-window",
      "passed": true,
      "scores": {
        "retrieval": 1.0,
        "action": 1.0,
        "data_accuracy": 1.0,
        "overall": 1.0
      },
      "documents": {
        "selected": ["policy/refunds-2026"],
        "required_found": ["policy/refunds-2026"],
        "required_missing": [],
        "optional_found": [],
        "forbidden_found": []
      },
      "actions": {
        "observed": [{"type": "cite", "target": "policy/refunds-2026"}],
        "required_found": [{"type": "cite", "target": "policy/refunds-2026"}],
        "required_missing": []
      },
      "facts": {
        "matched": {"refund_window_days": 30},
        "mismatched": {},
        "missing": []
      },
      "answer": null,
      "llm_judge": null,
      "failures": []
    }
  ]
}
```

## Installation
Copy this folder into your skills directory, then run the bundled checks:

```bash
python scripts/run.py --selftest
python scripts/test.py
```

No third-party Python packages are required.

## Usage
Show CLI options:

```bash
python scripts/run.py --help
```

Run the example:

```bash
python scripts/run.py --traces examples/sample_traces.jsonl --manifest examples/evidence_manifest.json
```

Write JSON output to a file:

```bash
python scripts/run.py --traces examples/sample_traces.jsonl --manifest examples/evidence_manifest.json --output report.json
```

Emit CSV for dashboards:

```bash
python scripts/run.py --traces examples/sample_traces.jsonl --manifest examples/evidence_manifest.json --format csv
```

Optional environment defaults:

```bash
RAG_EVIDENCE_GRADER_THRESHOLD=0.9 python scripts/run.py --traces examples/sample_traces.jsonl --manifest examples/evidence_manifest.json
TRACE_TRELLIS_LLM_JUDGE_PATH=examples/llm_judge.json python scripts/run.py --traces examples/sample_traces.jsonl --manifest examples/evidence_manifest.json
```

## Example
Command:

```bash
python scripts/run.py --traces examples/sample_traces.jsonl --manifest examples/evidence_manifest.json
```

Expected output is stored in `examples/expected_output.json`. The summary should report one passing case with retrieval, action, data-accuracy, and overall scores of `1.0`.

## Limitations
- Exact fact comparison is intentionally strict and does not normalize units, dates, or paraphrases.
- The offline grader checks evidence routing and trace behavior, not natural-language answer quality.
- Cross-domain balance must come from the input evaluation set; the CLI does not generate benchmark cases.
- Optional LLM judge files are merged as metadata and never override deterministic scores.

## Verification
Automated execution check: **passed ✅**.

- Steps: structure=ok · syntax=ok · help=ok · selftest=ok · test=ok
- Commands and outputs shown in `README.md` are captured from these real runs.
