> Historical PDF-only admin scope. Current mixed-source results: [html_expansion_summary.md](html_expansion_summary.md).

# Admin-agent benchmark update — 2026-10-23

All 20 queries target a CRM admin/developer agent. Original query strings, requester roles and all 344 original documents are preserved. The corpus now has 354 documents, 67 relevance labels and 39 answer-evidence aspects.

Nine reviewed PDF sections add 10 passages with stable supplemental IDs. Supplemental passages preserve source punctuation and newlines, including Apex and SQL code. The original 344 passages retain their existing tokenized representation. Rebuilding from cached PDFs reproduces the complete corpus. Every current label was verified against its declared source PDF extraction.

| config | recall@5 | MRR@5 | aspect recall@5 | p95 ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| bm25 | 0.355 | 0.424 | 0.458 | 2.4 |
| dense | 0.501 | 0.629 | 0.558 | 15.9 |
| hybrid_rrf | 0.484 | 0.552 | 0.558 | 12.2 |
| hybrid_rerank | 0.544 | 0.564 | 0.642 | 181.7 |

`hybrid_rerank` has the highest mean evidence-aspect coverage in this run. Aspect recall measures retrieved evidence groups, including alternative implementation routes. It does not measure generated answer correctness or require that every route be executed.

There are 1–9 labels per query; document recall@5 has a dataset ceiling of 0.969444. Aspect recall macro-averages groups within each query, then averages the 20 queries. A hit is any reviewed passage in a group. This avoids counting every overlapping document as a separate required answer; it can still overestimate complete evidence when a group contains several different details.

Corpus, labels and evaluation scope changed together. These scores are a new benchmark version and cannot be interpreted as model improvements over the previous scope. Latency is a fresh measurement.

| config | previous recall@5 | current recall@5 | previous MRR | current MRR |
| --- | ---: | ---: | ---: | ---: |
| bm25 | 0.434 | 0.355 | 0.412 | 0.424 |
| dense | 0.559 | 0.501 | 0.592 | 0.629 |
| hybrid_rrf | 0.551 | 0.484 | 0.497 | 0.552 |
| hybrid_rerank | 0.638 | 0.544 | 0.547 | 0.564 |

Known evidence gaps: exact AccountContactRelation DML/API specification, Quote/QuoteLineItem APIs, Profile metadata-update APIs and WhatsApp REST sending APIs. The guide marks these gaps rather than inventing executable code. Supplemental Apex security passages describe API-version-dependent behavior; use the pinned source version rather than treating its defaults as universal.

[Answers and aspect evidence](../docs/query_answers.md), [per-query aspect results](admin_aspect_results.csv), [changes](admin_scope_changes.json), [baseline](before_admin_scope/).
