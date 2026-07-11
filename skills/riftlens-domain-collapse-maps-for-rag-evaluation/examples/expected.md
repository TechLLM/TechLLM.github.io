# RiftLens Domain Collapse Report

- Threshold: `0.60`
- Top K: `all`
- Queries: `3`
- Retrieved items: `8`
- Overall hit rate: `75.0%`
- Overall false pass rate: `50.0%`
- Overall false reject rate: `25.0%`
- Worst-domain gap: `100.0 pp`
- Worst domain: `api_reference`

| Domain | Coverage | Hit rate | False pass | False reject | Relevant | Passed |
|---|---:|---:|---:|---:|---:|---:|
| api_reference | 66.7% | 0.0% | 0.0% | 100.0% | 1 | 0 |
| notes | 66.7% | 100.0% | 100.0% | 0.0% | 1 | 2 |
| tickets | 66.7% | 100.0% | 0.0% | 0.0% | 1 | 1 |
| wiki | 66.7% | 100.0% | 100.0% | 0.0% | 1 | 2 |

## Flags

- Collapse: `api_reference` trails the best domain by `100.0 pp`.
- Risk: `api_reference` has high false reject rate (`100.0%`).
- Risk: `notes` has high false pass rate (`100.0%`).
- Risk: `wiki` has high false pass rate (`100.0%`).
