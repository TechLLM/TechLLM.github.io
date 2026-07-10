# SliceLens Evaluation Report

## Summary

| Metric | Value |
| --- | --- |
| Rows | 12 |
| Overall mean | 0.653 |
| Score column | score |
| Worst-slice min count | 2 |

## Worst Slice

| Dimension | Value | Mean | Count |
| --- | --- | --- | --- |
| condition | missing_metadata | 0.413 | 3 |

## Source-to-Target Transfer Matrix

| source_domain \ target_domain | finance | legal | medical |
| --- | --- | --- | --- |
| finance | 0.895 (n=2) | 0.580 (n=1) | 0.390 (n=1) |
| legal | 0.620 (n=1) | 0.800 (n=2) | 0.440 (n=1) |
| medical | 0.410 (n=1) | 0.550 (n=1) | 0.730 (n=2) |

## Domain Gaps

| Source domain | In-domain mean | In n | Out-domain mean | Out n | Gap |
| --- | --- | --- | --- | --- | --- |
| finance | 0.895 | 2 | 0.485 | 2 | 0.410 |
| legal | 0.800 | 2 | 0.530 | 2 | 0.270 |
| medical | 0.730 | 2 | 0.480 | 2 | 0.250 |

## Slice Tables

### condition

| Value | Mean | Count |
| --- | --- | --- |
| missing_metadata | 0.413 | 3 |
| format_shift | 0.610 | 3 |
| clean | 0.795 | 6 |

### document_type

| Value | Mean | Count |
| --- | --- | --- |
| (missing) | 0.410 | 1 |
| csv | 0.627 | 3 |
| pdf | 0.667 | 7 |
| html | 0.880 | 1 |

### modality

| Value | Mean | Count |
| --- | --- | --- |
| image | 0.600 | 1 |
| text | 0.658 | 11 |

### question_type

| Value | Mean | Count |
| --- | --- | --- |
| ambiguous | 0.460 | 4 |
| comparison | 0.613 | 4 |
| fact | 0.887 | 4 |

### source_domain

| Value | Mean | Count |
| --- | --- | --- |
| medical | 0.605 | 4 |
| legal | 0.665 | 4 |
| finance | 0.690 | 4 |

### target_domain

| Value | Mean | Count |
| --- | --- | --- |
| medical | 0.573 | 4 |
| legal | 0.682 | 4 |
| finance | 0.705 | 4 |

## Missing-Field Degradation

| Field | Present mean | Present n | Missing mean | Missing n | Degradation |
| --- | --- | --- | --- | --- | --- |
| source_domain | 0.653 | 12 | n/a | 0 | n/a |
| target_domain | 0.653 | 12 | n/a | 0 | n/a |
| question_type | 0.653 | 12 | n/a | 0 | n/a |
| document_type | 0.675 | 11 | 0.410 | 1 | 0.265 |
| modality | 0.653 | 12 | n/a | 0 | n/a |
| condition | 0.653 | 12 | n/a | 0 | n/a |
