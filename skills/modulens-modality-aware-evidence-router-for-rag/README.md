# ModuLens

ModuLens is a minimal, installable skill and reference CLI for modality-aware evidence routing in RAG pipelines. It detects tables, code blocks, formulas, citations, dates, and benchmark spans, then emits structured relevance feature JSON.

## Install

No third-party dependencies are required.

```bash
python --version
python scripts/run.py
```

To install as a skill, copy this folder into your agent's skills directory and reload the agent.

## Usage

Run with the built-in mock sample:

```bash
python scripts/run.py --pretty
```

Run against the included example:

```bash
python scripts/run.py --question "Which system has better F1 and latency?" --input examples/sample.md --pretty
```

Batch score a directory:

```bash
python scripts/run.py --question "Find benchmark evidence with citations" --input examples --pretty
```

Use custom modality weights:

```bash
python scripts/run.py --question "Find implementation detail evidence" --input examples/sample.md --weights examples/weights.json --profile software --pretty
```

Write JSON output:

```bash
python scripts/run.py --question "Which result was reported in 2024?" --input examples/sample.md --output scores.json
```

## Python API

```python
from scripts.run import route_evidence

docs = [{"id": "note", "text": "The benchmark reached 91.2% accuracy in 2024 [1]."}]
result = route_evidence("Which benchmark improved in 2024?", docs)
print(result["documents"][0]["features"])
```

## Notes

This implementation is intentionally small and heuristic. It is useful as a working reference, a local feature generator, or a starting point for a richer reranking pipeline.
