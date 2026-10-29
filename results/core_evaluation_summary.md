# Core-only relevance evaluation — 2026-10-23

20 unchanged questions and 594 unchanged corpus documents. Gold labels decrease from 170 to 60; 99 references remain supplementary and 11 navigation/See Also blocks are excluded from gold. All sources remain in the corpus.

Rescored archived top-5 retrieval results. Corpus and query strings are identical; original measured latency is reused, not measured again.

Rankings identical to the archived broad-label run: 80/80 config-query rows. Metric differences are label-policy differences, not retrieval/model improvements.

| config | core recall@5 | core MRR@5 | p95 ms |
| --- | ---: | ---: | ---: |
| bm25 | 0.377 | 0.418 | 3.9 |
| dense | 0.507 | 0.546 | 16.0 |
| hybrid_rrf | 0.522 | 0.539 | 17.1 |
| hybrid_rerank | 0.518 | 0.471 | 164.3 |

`dense` has the highest MRR@5 under the core-only policy. The label policy does not enforce a five-label cap; document recall@5 has a mean theoretical ceiling of 0.977381. q19 and q20 retain more than five genuine direct passages.

The broad answer_aspects metric is retired for this version. Only relevant_doc_ids count toward Recall/MRR. Admin/developer alternatives remain gold when they directly answer the wording (for example, Apex Account merge and SQL non-engagement selection). Generic OAuth, metadata deployment, execution order, migration and permissions unrelated to the actual question receive no credit.

A core passage can provide a necessary answer component rather than a complete end-to-end example. q12 still lacks an exact complete Case-to-Account sample; q16 engagement tracking has limitations. These are retrieval labels, not a claim that generated answers are fully correct or executable.

## Comparison with broad labels

| config | previous recall@5 | core recall@5 | previous MRR | core MRR |
| --- | ---: | ---: | ---: | ---: |
| bm25 | 0.205 | 0.377 | 0.443 | 0.418 |
| dense | 0.375 | 0.507 | 0.621 | 0.546 |
| hybrid_rrf | 0.379 | 0.522 | 0.610 | 0.539 |
| hybrid_rerank | 0.323 | 0.518 | 0.571 | 0.471 |

[Explicit content-locked review](../data/raw/core_labels.json), [label changes](core_label_review.json), [answers](../docs/query_answers.md), [baseline](before_core_labels/). All 80 per-query and four aggregate scores were independently verified.
