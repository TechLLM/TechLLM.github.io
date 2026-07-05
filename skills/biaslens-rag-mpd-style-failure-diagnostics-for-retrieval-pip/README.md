# BiasLens RAG

BiasLens RAG is a small, installable skill for MPD-style failure diagnostics in retrieval-augmented generation pipelines. It separates cases where correct evidence is absent from the candidate set from cases where evidence is present but reranking appears unstable, position-biased, or keyword-attracted.

## Install

Use Python 3.9 or newer. No dependencies are required.

```bash
python3 scripts/run.py --help
python3 scripts/test.py
```

Use `python` instead of `python3` only when your system aliases `python` to Python 3.

## Usage

Run the built-in sample:

```bash
python3 scripts/run.py --selftest
```

Run the included example:

```bash
python3 scripts/run.py --candidates examples/candidates.jsonl
```

Save output:

```bash
python3 scripts/run.py --candidates examples/candidates.jsonl --output examples/actual_output.json
```

## Expected Output

The example emits deterministic JSON matching `examples/expected_output.json`. Summary:

```json
{
  "cases": 2,
  "correct_evidence_absent": 1,
  "reranker_instability_or_bias": 1,
  "no_failure_signal": 0,
  "mean_selection_stability": 0.75,
  "mean_position_bias_score": 0.5
}
```

## Input Format

Each JSONL line is one case:

```json
{"query_id":"q1","question":"What is the refund policy after cancellation?","selected_doc_ids":["billing_faq"],"relevant_doc_ids":["refund_policy"],"candidates":[{"doc_id":"billing_faq","text":"Billing invoices and upgrade charges.","score":0.95},{"doc_id":"refund_policy","text":"Refund policy for cancellation requests.","score":0.85}]}
```
