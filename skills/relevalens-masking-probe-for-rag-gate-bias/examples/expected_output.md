# RelevaLens Report

## Summary
- query_count: 1
- candidate_count: 3
- score_count: 12
- mean_normalized_entropy: 0.8693
- mean_top1_concentration: 0.5027
- mean_mask_sensitivity: 0.1778
- mean_rank_instability: 0.2222
- mean_position_skew: 0.1694
- flags: position_skew, rank_instability

## Query Findings
| query_id | normalized_entropy | top1_concentration | mask_sensitivity | rank_instability | position_skew | flags |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| q1 | 0.8693 | 0.5027 | 0.1778 | 0.2222 | 0.1694 | position_skew; rank_instability |

## Candidate Sensitivity
| query_id | candidate_id | baseline_rank | position | baseline_score | masked_mean | mask_delta | concentration_share |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| q1 | d1 | 1 | 1 | 0.9200 | 0.5133 | 0.4067 | 0.5027 |
| q1 | d2 | 2 | 2 | 0.7100 | 0.6100 | 0.1000 | 0.3880 |
| q1 | d3 | 3 | 3 | 0.2000 | 0.1733 | 0.0267 | 0.1093 |
