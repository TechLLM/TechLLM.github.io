# ProofLattice — Evidence Matrix Evaluator for RAG Systems

ProofLattice is a small, installable skill for deterministic first-pass RAG evaluation. It checks answer directness, evidence coverage, omission risk, freshness, citation support, and factual alignment without external services.

## Install

Use Python 3.9 or newer. No dependencies are required.

```bash
python scripts/run.py --help
python scripts/test.py
```

## Usage

Run the built-in sample:

```bash
python scripts/run.py --selftest
```

Evaluate the included example:

```bash
python scripts/run.py --input examples/sample_input.json --format yaml
```

Write a standalone JSON evidence map:

```bash
python scripts/run.py --input examples/sample_input.json --evidence-json examples/sample_evidence_map.json
```

## Example Expected Output

```yaml
checklist:
  evaluation_id: "35cc9128cd73"
  overall_status: "pass"
  overall_score: 0.978
```

Full expected outputs are included in:

- `examples/expected_output.yaml`
- `examples/expected_evidence_map.json`
