# Core-answer Query Set

All 20 queries retain the CRM admin/developer perspective and their original wording, requester roles, category and difficulty. Only direct core-answer passages are gold. Useful prerequisites and implementation context are stored separately and receive no Recall/MRR credit.

`relevant_doc_ids`: scored core answers. `supplementary_doc_ids`: non-gold context. `excluded_doc_ids`: navigation or See Also blocks formerly labelled relevant. Broad `answer_aspects` are archived in the previous version; current evaluation reports document recall@5 and MRR@5 only.

Selection is independent of retrieval rank and has no artificial five-document cap. q19 and q20 can have more than five valid core passages; recall@5 still has a ceiling. See [answers](query_answers.md) and [the explicit review](../data/raw/core_labels.json).

| id | requester | category | difficulty | core labels | non-gold context |
| --- | --- | --- | --- | ---: | ---: |
| q01 | sales_user | natural_language_task_description | easy | 4 | 0 |
| q02 | marketing_user | exact_product_feature_lookup | easy | 4 | 0 |
| q03 | service_operations_user | natural_language_task_description | easy | 3 | 2 |
| q04 | crm_admin_or_developer | exact_product_feature_lookup | easy | 1 | 0 |
| q05 | sales_user | exact_product_feature_lookup | easy | 5 | 4 |
| q06 | sales_user | exact_product_feature_lookup | easy | 1 | 15 |
| q07 | crm_admin_or_developer | natural_language_task_description | medium | 2 | 0 |
| q08 | marketing_user | natural_language_task_description | medium | 2 | 13 |
| q09 | crm_admin_or_developer | exact_product_feature_lookup | easy | 1 | 6 |
| q10 | service_operations_user | natural_language_task_description | medium | 4 | 8 |
| q11 | crm_admin_or_developer | natural_language_task_description | medium | 1 | 1 |
| q12 | crm_admin_or_developer | natural_language_task_description | hard | 5 | 11 |
| q13 | marketing_user | paraphrased_feature_discovery | medium | 1 | 2 |
| q14 | marketing_user | exact_product_feature_lookup | medium | 1 | 2 |
| q15 | crm_admin_or_developer | symptom_based_troubleshooting | medium | 5 | 12 |
| q16 | marketing_user | paraphrased_feature_discovery | hard | 3 | 2 |
| q17 | crm_admin_or_developer | paraphrased_feature_discovery | hard | 2 | 1 |
| q18 | crm_admin_or_developer | paraphrased_feature_discovery | medium | 2 | 1 |
| q19 | crm_admin_or_developer | symptom_based_troubleshooting | hard | 7 | 7 |
| q20 | crm_admin_or_developer | symptom_based_troubleshooting | hard | 6 | 12 |
