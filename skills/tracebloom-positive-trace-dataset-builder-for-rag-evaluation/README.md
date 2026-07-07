# TraceBloom — Positive-Trace Dataset Builder for RAG Evaluation

TraceBloom is a small, dependency-free reference skill for building RAG evaluation datasets from positive usage traces. It extracts cited query-document pairs, aligns them with retrieval logs, and emits confirmed positives plus guarded implicit negative candidates.

## Install

Copy this directory into your skills folder. No package install is required because the script uses only the Python standard library.

Verify:

```bash
python scripts/run.py --selftest
python scripts/test.py
```

## Usage

Show help:

```bash
python scripts/run.py --help
```

Run the example:

```bash
python scripts/run.py \
  --answers examples/answers.md \
  --retrieval-log examples/retrieval_log.jsonl \
  --max-negatives-per-query 2
```

Write files:

```bash
python scripts/run.py \
  --answers examples/answers.md \
  --retrieval-log examples/retrieval_log.jsonl \
  --output tracebloom_dataset.jsonl \
  --review-output tracebloom_review_queue.jsonl
```

Optional environment variables:

- `TRACEBLOOM_DEFAULT_CONFIDENCE`: default confidence for extracted citations, default `0.95`.
- `TRACEBLOOM_MIN_NEGATIVE_SCORE`: minimum retrieval score for implicit negative candidates, default `0.0`.

## Expected Example Output

```jsonl
{"chunk_id":"intro","confidence":0.95,"doc_id":"rag-handbook","evidence":{"citation":"doc://rag-handbook#chunk=intro","input":"examples/answers.md","matched_retrieval":true},"label":"positive","query":"How should we evaluate a RAG retriever from product traces?","query_id":"q-001","rank":1,"run_id":"run-001","score":0.92,"source":"citation+retrieval"}
{"chunk_id":"trace-signals","confidence":0.95,"doc_id":"support-notes","evidence":{"citation":"[[support-notes#chunk=trace-signals]]","input":"examples/answers.md","matched_retrieval":true},"label":"positive","query":"How should we evaluate a RAG retriever from product traces?","query_id":"q-001","rank":3,"run_id":"run-001","score":0.76,"source":"citation+retrieval"}
{"chunk_id":"overview","confidence":0.52,"doc_id":"unused-overview","evidence":{"reason":"retrieved for the query but absent from confirmed citations","safeguard":"candidate only; require review before treating as a true negative"},"label":"implicit_negative_candidate","query":"How should we evaluate a RAG retriever from product traces?","query_id":"q-001","rank":2,"run_id":"run-001","score":0.81,"source":"retrieved_unused"}
{"chunk_id":"draft","confidence":0.46,"doc_id":"weak-match","evidence":{"reason":"retrieved for the query but absent from confirmed citations","safeguard":"candidate only; require review before treating as a true negative"},"label":"implicit_negative_candidate","query":"How should we evaluate a RAG retriever from product traces?","query_id":"q-001","rank":4,"run_id":"run-001","score":0.41,"source":"retrieved_unused"}
```
