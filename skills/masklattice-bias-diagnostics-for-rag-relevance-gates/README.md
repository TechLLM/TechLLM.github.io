# MaskLattice: Bias Diagnostics for RAG Relevance Gates

MaskLattice is a small installable skill for auditing RAG relevance gates and rerankers with controlled document masking. It produces a CSV dataset and Markdown report showing score variance and ranking shifts across original and perturbed candidate documents.

## Quick Start

Run the bundled example:

```bash
python scripts/run.py
```

Run with explicit inputs:

```bash
python scripts/run.py --queries examples/questions.jsonl --docs examples/docs --out reports/masklattice
```

Run with a stdin/stdout scorer adapter:

```bash
python scripts/run.py --adapter-cmd "python examples/simple_adapter.py"
```

Run with precomputed scores:

```bash
python scripts/run.py --queries examples/one_question.jsonl --docs examples/docs/rag_gate_evaluation.md --score-file examples/precomputed_scores.jsonl
```

## Input Format

Questions are JSONL:

```json
{"id":"q1","question":"How should a RAG relevance gate avoid metadata bias?"}
```

Documents are Markdown or JSON files in a directory. JSON documents may be a single object or a list of objects with fields such as `id`, `title`, `metadata`, `summary`, `body`, `content`, `text`, or `sections`.

## Adapter Protocol

The runner sends a JSON array to the adapter on stdin. Each item includes:

- `case_id`
- `query_id`
- `doc_id`
- `mask_name`
- `question`
- `document`

The adapter returns either a JSON array of numbers, a JSON array of `{ "case_id": "...", "score": 0.5 }` objects, or JSONL objects with `case_id` and `score`.

## Outputs

By default, outputs are written to `masklattice_output/`:

- `diagnostics.csv`
- `report.md`

No third-party Python dependencies are required.
