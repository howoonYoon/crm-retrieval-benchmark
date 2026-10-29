> Historical broad-label evaluation. Current core-only results: [core_evaluation_summary.md](core_evaluation_summary.md).

# Official HTML expansion — 2026-10-23

Requested 25 official URLs; extracted 24 article bodies; excluded 1 source. Added 240 section-based HTML chunks to the existing 354 PDF chunks, for 594 total documents.

The 20 query strings are unchanged. Reviewed HTML sections add 103 relevance assignments, giving 170 labels and 49 evidence aspects. URL hints are not relevance labels. [Rules](../data/raw/html_label_rules.json) and [exact assignments](html_label_review.json) record the review.

| config | document recall@5 | MRR@5 | aspect recall@5 | p95 ms |
| --- | ---: | ---: | ---: | ---: |
| bm25 | 0.205 | 0.443 | 0.321 | 3.9 |
| dense | 0.375 | 0.621 | 0.512 | 16.0 |
| hybrid_rrf | 0.379 | 0.610 | 0.562 | 17.1 |
| hybrid_rerank | 0.323 | 0.571 | 0.496 | 164.3 |

`hybrid_rrf` has the highest mean evidence-aspect coverage in this run. Corpus, relevance labels and evidence groups changed together; score differences from the previous scope are not a model improvement. Latencies were measured again.

Document recall@5 theoretical mean ceiling: 0.718228. More valid alternative documents increase the recall denominator. Aspect recall macro-averages the fraction of evidence groups hit within each query; it measures evidence coverage, not full answer correctness.

Excluded source: the OTT API reference root exposed an empty component and its official schema URL returned 404. OAuth and send/delivery event articles were ingested, but endpoint/payload coverage remains incomplete. The Case.AccountId update example is in the corpus but is not a q12 answer because the write direction differs.

Validation: all 354 original PDF chunks preserved; all HTML chunks exactly regenerated from checked-in page snapshots; all 80 per-query score rows and aggregate metrics independently recalculated; 9 unit tests pass. Raw HTML/rendered DOM caches are local; cleaned snapshots and metadata are checked in.

[Acquisition report](../data/processed/html_ingestion_report.json), [pipeline and reproduction](../docs/html_ingestion.md), [current answers](../docs/query_answers.md), [baseline](before_html_sources/).
