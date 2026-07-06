# FacetRecall - Modality-Aware RAG Benchmarker

FacetRecall is a small, dependency-free benchmark CLI for evaluating RAG retrieval across modality, domain, document type, corruption, and context-condition slices.

## Install

Use Python 3 from this directory:

```bash
python3 scripts/run.py --help
python3 scripts/test.py
```

No API key is required. Optional settings:

```bash
export FACETRECALL_TOP_K=5
export FACETRECALL_LIST_DELIMITER='|'
```

## Usage

Run the built-in sample:

```bash
python3 scripts/run.py --selftest
```

Run the example files:

```bash
python3 scripts/run.py \
  --queries examples/queries.csv \
  --metadata examples/documents.yaml
```

Write a report:

```bash
python3 scripts/run.py \
  --queries examples/queries.csv \
  --metadata examples/documents.yaml \
  --output report.md
```

Emit JSON:

```bash
python3 scripts/run.py \
  --queries examples/queries.csv \
  --metadata examples/documents.yaml \
  --format json
```

## Expected Output

The example starts with:

```text
# FacetRecall Report

## Overall

| metric | value |
| --- | ---: |
| queries | 5 |
| recall | 0.600 |
| hit_rate | 0.600 |
| false_pass_rate | 0.600 |
| missing_context_failure_rate | 0.400 |
```

The complete deterministic output is in `examples/expected_output.md`.
