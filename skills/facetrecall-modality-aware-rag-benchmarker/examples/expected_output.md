# FacetRecall Report

## Overall

| metric | value |
| --- | ---: |
| queries | 5 |
| recall | 0.600 |
| hit_rate | 0.600 |
| false_pass_rate | 0.600 |
| missing_context_failure_rate | 0.400 |

## Slices

| facet | value | queries | recall | false_pass_rate | missing_context_failures |
| --- | --- | ---: | ---: | ---: | ---: |
| modality | academic_table | 1 | 0.000 | 1.000 | 1 |
| modality | code | 1 | 1.000 | 1.000 | 0 |
| modality | table | 1 | 0.000 | 1.000 | 1 |
| modality | text | 1 | 1.000 | 0.000 | 0 |
| modality | wiki_link | 1 | 1.000 | 0.000 | 0 |
| domain | engineering_logs | 1 | 1.000 | 1.000 | 0 |
| domain | knowledge_base | 1 | 1.000 | 0.000 | 0 |
| domain | policies | 1 | 0.000 | 1.000 | 1 |
| domain | product_docs | 1 | 1.000 | 0.000 | 0 |
| domain | research_notes | 1 | 0.000 | 1.000 | 1 |
| document_type | experiment | 1 | 0.000 | 1.000 | 1 |
| document_type | linked_page | 1 | 1.000 | 0.000 | 0 |
| document_type | note | 1 | 1.000 | 0.000 | 0 |
| document_type | reference | 1 | 0.000 | 1.000 | 1 |
| document_type | snippet | 1 | 1.000 | 1.000 | 0 |
| corruption | clean | 4 | 0.750 | 0.500 | 1 |
| corruption | truncated | 1 | 0.000 | 1.000 | 1 |
| context_condition | complete | 4 | 0.750 | 0.500 | 1 |
| context_condition | partial | 1 | 0.000 | 1.000 | 1 |

## Missing Context Failures

| query_id | missing_gold_doc_ids | missing_facets |
| --- | --- | --- |
| q2 | doc_table_eval | doc_table_eval: modality=academic_table, domain=research_notes, document_type=experiment, corruption=clean, context_condition=complete |
| q5 | doc_policy_table | doc_policy_table: modality=table, domain=policies, document_type=reference, corruption=truncated, context_condition=partial |

## False Passes

| query_id | accepted_non_gold_doc_ids |
| --- | --- |
| q2 | doc_wiki_link |
| q3 | doc_text_pricing |
| q5 | doc_wiki_link |
