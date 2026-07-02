# Sparse Retrieval Experiment

This note compares a prototype retriever against common benchmark tasks such as MMLU, GSM8K, and HumanEval. The scoring notes cite prior retrieval work [@lewis2020rag] and an internal mock citation [Smith et al., 2024].

## Result Table

| Method | MMLU | GSM8K | Notes |
| --- | ---: | ---: | --- |
| baseline | 62.1 | 48.0 | lexical only |
| routed | 68.4 | 55.7 | table-aware reranker |

## Parser Sketch

```python
def route_note(modalities):
    return [f"{name}_node" for name in modalities]
```

## Scoring Equation

The combined score is:

$$
score = 0.55 \cdot relevance + 0.30 \cdot structure + 0.15 \cdot freshness
$$

## Mock Run Log

2026-01-10T09:00:00Z INFO started mock evaluation run
2026-01-10T09:00:01Z INFO loaded 3 sample notes
2026-01-10T09:00:02Z WARN table parser used fallback alignment
2026-01-10T09:00:03Z INFO completed mock evaluation run
