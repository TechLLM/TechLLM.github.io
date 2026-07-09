# GateWeave Report

Protocol: `gateweave-v0`
Threshold: `0.5`
Rows: `8`
Slice columns: `domain`, `doc_type`, `evidence_field`

## Aggregate Metrics

| scorer | rows | precision | recall | f1 | accuracy | worst_slice_score |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 8 | 0.666667 | 0.5 | 0.571429 | 0.625 | 0.0 |
| candidate | 8 | 0.75 | 0.75 | 0.75 | 0.75 | 0.0 |

## Worst Slices

| scorer | column | value | count | precision | recall | f1 |
|---|---|---|---:|---:|---:|---:|
| baseline | domain | sales | 2 | 0.0 | 0.0 | 0.0 |
| candidate | domain | legal | 3 | 0.0 | 0.0 | 0.0 |

## Missing-Field Stress

| scorer | column | missing_count | present_count | missing_f1 | present_f1 | stress_delta |
|---|---|---:|---:|---:|---:|---:|
| baseline | evidence_field | 2 | 6 | 0.0 | 0.666667 | -0.666667 |
| candidate | evidence_field | 2 | 6 | 0.666667 | 0.8 | -0.133333 |

## Side-by-Side

| metric | best | scores |
|---|---|---|
| aggregate_f1 | candidate | baseline=0.571429, candidate=0.75 |
| worst_slice_score | baseline, candidate | baseline=0.0, candidate=0.0 |
| missing_field_stress_score:evidence_field | candidate | baseline=0.0, candidate=0.666667 |
