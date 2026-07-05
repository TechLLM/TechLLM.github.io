# BiasLens RAG - Diagnostic Reranking Probe

BiasLens RAG is a small, installable skill with a dependency-free CLI for probing why RAG retrieval candidates may be misranked. It uses deterministic lexical perturbations to flag keyword reliance, partial-evidence instability, position sensitivity, and likely failure modes.

## Install

Use Python 3.10 or newer. No third-party packages are required.

```bash
python scripts/run.py --help
python scripts/test.py
```

## Usage

Run the built-in sample:

```bash
python scripts/run.py --selftest --pretty
```

Run against the example JSONL file:

```bash
python scripts/run.py --query "How do I reset contractor MFA device approvals?" --input examples/candidates.jsonl --pretty
```

Write output to a JSON file:

```bash
python scripts/run.py --query "How do I reset contractor MFA device approvals?" --input examples/candidates.jsonl --output examples/expected-output.json
```

Optional environment variables:

```bash
BIASLENS_RAG_MAX_CANDIDATES=10 python scripts/run.py --selftest
BIASLENS_RAG_POSITION_PRIOR=0.04 python scripts/run.py --selftest
```

## Example Expected Output

The example command emits a JSON object with this shape:

```json
{
  "baseline_ranking": [
    {"id": "kb-001", "rank": 1, "score": 0.98}
  ],
  "failure_modes": {
    "ambiguity_bias": false,
    "knowledge_gap": false,
    "position_bias": true,
    "precision_bias": true
  }
}
```

See `examples/expected-output.json` for the full deterministic report.
