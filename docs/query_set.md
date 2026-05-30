# Query Set

This benchmark uses 20 hand-written queries. Each query has labelled relevant documents in `data/processed/queries.jsonl`.

Difficulty is assigned by retrieval difficulty, not by Salesforce administration difficulty alone.

## User Perspectives

User perspective is tracked separately from retrieval category. This keeps role context visible without changing how recall@5 or MRR is computed.

| user perspective | queries |
| --- | --- |
| `crm_admin_or_developer` | q04, q07, q09, q11, q12, q15, q17, q18, q19, q20 |
| `sales_user` | q01, q05, q06 |
| `service_operations_user` | q03, q10 |
| `marketing_user` | q02, q08, q13, q14, q16 |

## exact_product_feature_lookup

The query directly names the product, feature, or API concept used by the target documentation.

| id | difficulty | relevant docs | query summary |
| --- | --- | ---: | --- |
| q02 | easy | 1 | Merge duplicate Accounts in Salesforce. |
| q04 | easy | 1 | Configure email warnings for Apex governor limit usage. |
| q05 | easy | 2 | Relate one Contact to multiple Accounts. |
| q06 | easy | 1 | Create multiple Quotes for one Opportunity. |
| q09 | easy | 1 | Check whether the Profile object supports Apex DML update. |
| q14 | medium | 2 | Create a filtered Data Extension for customers whose Country is UK. |

## natural_language_task_description

The query describes an operator task in natural language while still using some related product terms.

| id | difficulty | relevant docs | query summary |
| --- | --- | ---: | --- |
| q01 | easy | 1 | Handle a duplicate Account warning during Lead conversion. |
| q03 | easy | 4 | Automatically create Cases from support-address emails. |
| q07 | medium | 2 | Update an Opportunity field before save without Apex. |
| q08 | medium | 2 | Send approved WhatsApp template messages for a campaign. |
| q10 | medium | 2 | Route work to another queue based on agent availability. |
| q11 | medium | 2 | Estimate Knowledge capacity with article versions and translations. |
| q12 | hard | 5 | Update a related Account when a Case is created or updated. |

## symptom_based_troubleshooting

The query describes a symptom, failure, or access problem without naming the underlying feature directly.

| id | difficulty | relevant docs | query summary |
| --- | --- | ---: | --- |
| q15 | medium | 3 | Troubleshoot a custom field that does not appear on an Account page. |
| q19 | hard | 2 | Troubleshoot automation that fails only when many Cases are updated. |
| q20 | hard | 2 | Troubleshoot why a user can open but not edit some Account records. |

## paraphrased_feature_discovery

The query describes requirements and expects the system to discover the relevant feature name.

| id | difficulty | relevant docs | query summary |
| --- | --- | ---: | --- |
| q13 | medium | 3 | Use Salesforce CRM data in Marketing Cloud data extensions. |
| q16 | hard | 3 | Branch after email non-engagement before sending a mobile follow-up. |
| q17 | hard | 3 | Debug a guided Flow while preventing test records from being saved. |
| q18 | medium | 1 | Choose an import tool for high-volume loads, updates, and export. |
