> Historical 2026-10-22 label-only review. Current admin-agent results: [admin_scope_summary.md](admin_scope_summary.md).

# Label review evaluation — 2026-10-22

Fresh execution of all four retrievers after relevance-label changes. The 20 query strings and 344-document corpus are unchanged. Latencies below are separate measurements, not a label-change effect.

| config | old recall@5 | new recall@5 | old MRR | new MRR | old p95 ms | new p95 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| bm25 | 0.347 | 0.434 | 0.304 | 0.412 | 6.5 | 5.0 |
| dense | 0.588 | 0.559 | 0.567 | 0.592 | 32.3 | 25.2 |
| hybrid_rrf | 0.514 | 0.551 | 0.421 | 0.497 | 31.6 | 25.2 |
| hybrid_rerank | 0.598 | 0.638 | 0.497 | 0.547 | 177.0 | 199.2 |

Top-5 rankings changed in 0/80 config-query rows compared with the saved run. If rankings differ, score differences combine relevance-label changes and execution/environment differences.

q20 has 7 labels: maximum recall@5 = 5/7; dataset mean ceiling = 0.985714. All 80 per-query recalls, reciprocal ranks and first-relevant ranks, plus all aggregate metrics and p95 values, were independently recalculated and validated.

Manual additions to label_candidates.csv have blank lexical scores; their row ranks are review-list positions, not new retrieval scores.

[Questions, answers and evidence](../docs/query_answers.md). [Exact label changes](label_review_changes.json). [Original queries and results](before_label_review/).
