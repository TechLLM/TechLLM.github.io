# ModuLens Example Evidence

The RetrieverMix study compared a keyword baseline with a modality-aware evidence router in 2024 [1].

| System | F1 | Recall | Latency ms |
| --- | ---: | ---: | ---: |
| KeywordBase | 71.2 | 78.5 | 31 |
| ModuLens-Router | 82.6 | 86.1 | 34 |

The benchmark result shows an 11.4 point F1 improvement while adding 3 ms of latency.

The scoring rule was written as $score = 0.5 * text + 0.5 * evidence$.

```python
def rerank(query, documents):
    spans = [detect_spans(doc) for doc in documents]
    return score_with_modalities(query, spans)
```

The paper was revised on 2024-04-18 and cites Doe et al. (2024).

Reference:

[1] Doe et al. (2024), doi:10.1000/modulens-example.
