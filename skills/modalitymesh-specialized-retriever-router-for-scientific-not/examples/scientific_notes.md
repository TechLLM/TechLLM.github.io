# Superconductor Notes

Observed on 2024-03-12 during instrument sweep.

The transition estimate follows $T_c = 92K$ for sample A.

| sample | Tc_K | resistance_ohm |
| --- | ---: | ---: |
| A | 92 | 0.02 |
| B | 88 | 0.05 |

```python
def normalize(x):
    return x / max(x)
```

Smith et al. [Smith 2021] reported a comparable curve. DOI:10.1000/example

Benchmark: recall@10 improved from 0.71 to 0.83 with table-aware scoring.
