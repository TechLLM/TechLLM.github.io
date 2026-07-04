# Evidra - Evidence-First RAG Evaluation CLI

Evidra is a small, offline CLI for evaluating RAG runs through observable evidence. It compares trace JSONL, evidence expectation YAML, and generated answer text, then emits a deterministic JSON report.

## Install

No third-party dependencies are required.

```bash
python3 scripts/run.py --help
python3 scripts/test.py
```

## Usage

Run the built-in sample:

```bash
python3 scripts/run.py --selftest
```

Run the bundled example:

```bash
python3 scripts/run.py \
  --trace-jsonl examples/trace.jsonl \
  --spec-yaml examples/evidence_spec.yaml \
  --answer examples/answer.txt \
  --pretty
```

Write output to a file:

```bash
python3 scripts/run.py \
  --trace-jsonl examples/trace.jsonl \
  --spec-yaml examples/evidence_spec.yaml \
  --answer examples/answer.txt \
  --output report.json
```

## Expected Output

`python3 scripts/run.py --selftest` prints:

```json
{"by_document_type":{"faq":{"required":1,"retrieval_hit_rate":1.0,"retrieved":1},"policy":{"required":1,"retrieval_hit_rate":1.0,"retrieved":1}},"by_domain":{"benefits":{"required":2,"retrieval_hit_rate":1.0,"retrieved":2}},"counts":{"covered_citations":2,"forbidden_sources_used":0,"post_state_assertions":1,"post_state_assertions_met":1,"required_citations":2,"required_documents":2,"retrieved_required_documents":2},"evaluation_id":"sample-benefits-rag","findings":[],"passed":true,"scores":{"citation_coverage":1.0,"forbidden_source_score":1.0,"overall":1.0,"post_state_assertion_rate":1.0,"retrieval_hit_rate":1.0}}
```
