# Salesforce CRM Operations Retrieval Benchmark

Comparison of retrieval configurations (BM25 vs Dense vs Hybrid vs Reranker) on public Salesforce Service Cloud, Sales Cloud, Marketing Cloud, and Developer documentation.

# Why I Picked This Assignment

I chose this assignment because it is closely related to my previous experience operating and developing Salesforce-based CRM systems. At the time, Salesforce was a relatively new platform within the team, so we frequently relied on official documentation for feature implementation, configuration changes, troubleshooting, and new business requirements.

This made retrieval a natural choice for me. In practice, the first challenge was finding the correct source material from a large and fragmented documentation corpus. In a real CRM environment, this is critical because Salesforce documentation spans many areas, including Sales Cloud, Service Cloud, Marketing Cloud, Apex, Flow, and Security. Users also do not always search using official Salesforce terminology. They often describe business problems, operational issues, or desired outcomes in natural language.

Because of this, I wanted to evaluate how different retrieval approaches perform in a realistic CRM documentation search scenario. The goal was to compare whether different retrieval methods could handle both exact technical terminology and the natural language queries that arise during day-to-day CRM operations.

# Decisions I Made

## 1. Creating Queries from Multiple User Perspectives

The queries were inspired by real Salesforce CRM operational scenarios I had seen or handled across different user roles. This helped make the benchmark closer to how users actually search documentation in practice.

The user groups included:

- CRM administrators and developers
- Sales/Service users

The final query set keeps this as a separate user-perspective field instead of
mixing it with retrieval category:

| user perspective | queries |
| --- | --- |
| `admin/developer` | q03, q10, q04, q07, q09, q11, q12, q15, q17, q18, q19, q20 |
| `sales/service user` | q01, q05, q06, q02, q08, q13, q14, q16  |

For example, developers are more likely to search for technical topics such as Apex Triggers or Governor Limits, while sales users may search for Opportunity or Quote management. Service operations users are more likely to look for documentation related to Email-to-Case, routing, case management, or access issues.

Because Salesforce is used by many different roles within an organization, I believed that including queries from multiple perspectives would create a more realistic retrieval benchmark.

For each query, I manually checked the selected Salesforce PDF corpus and labelled the chunk or chunks that directly answered the question.

## 2. Varying Query Difficulty

Some queries directly include official Salesforce terminology such as Email-to-Case or Governor Limits.

For harder queries, I described business scenarios and symptoms instead of naming the target feature directly. Examples include situations where an automation fails only for certain users or where a process breaks when handling large volumes of records.

This approach allows the evaluation to measure not only keyword matching performance but also the ability to retrieve relevant documentation from natural language descriptions.

## 3. Using PDF Documentation as the Corpus

I initially considered collecting Salesforce documentation directly from the web.

However, Salesforce's online documentation is spread across many web pages and can be harder to collect consistently due to dynamic navigation, page structure changes, and rendering differences. Since reproducibility was an important requirement for this assignment, I chose PDF documentation as the corpus and checked in the processed JSONL corpus used for evaluation.


## Corpus

The evaluated corpus contains 344 retrieval documents extracted from 12 Salesforce PDF documents related to customer support workflows, account and contract-related records, customer communication processes, and CRM automation. Long PDF pages and selected continuous sections
are split into focused retrieval documents so that the system retrieves
specific documentation passages rather than entire guides.

Salesforce CRM operations documentation is a good benchmark corpus because it
contains both exact product terminology and operational questions that users
often phrase indirectly. That makes it useful for comparing lexical retrieval,
dense retrieval, hybrid retrieval, and reranking.

Raw PDF source references are tracked in `data/raw/source_urls.txt`. Most are
public Salesforce PDF URLs, while two are local downloaded Salesforce PDFs used
for Agentforce Contact Center and Marketing Cloud Contact Builder content.
`src/build_corpus.py` downloads or copies those PDFs into an ignored local
cache, extracts page text, filters CRM-operations-related chunks, and writes
`data/processed/documents.jsonl`. The checked-in `documents.jsonl` is the
corpus used to reproduce the reported retrieval results.


# Retrieval Configurations

The benchmark evaluates four configurations on the same documents and queries:

- `bm25`: lexical BM25 retrieval.
- `dense`: dense retrieval with a SentenceTransformers embedding model.
- `hybrid_rrf`: reciprocal-rank-fusion blend of BM25 and dense retrieval.
- `hybrid_rerank`: hybrid RRF candidate generation followed by a CrossEncoder
  reranker over the top 20 candidates.

# Metrics

The evaluation reports:

- `recall@5`
- `MRR`
- `p95_latency_ms`

Latency is measured after indexes and embedding models are loaded. The target is
p95 retrieval latency under 1 second on a single laptop or free-tier VM.
Each query has between 1 and 5 labelled relevant documents. Recall@5 is computed as fractional document-level recall: the number of labelled relevant documents retrieved in the top 5 divided by the total number of labelled relevant documents for that query.

# Results

## Overall Analysis

The benchmark was run on 344 retrieval documents and 20 labelled queries,
including 5 hard queries.

![Retrieval metrics plot](results/metrics_plot.png)
| config | recall@5 | MRR | p95 latency |
| --- | ---: | ---: | ---: |
| bm25 | 0.347 | 0.304 | **6.5 ms** |
| dense | 0.588 | **0.567** | 32.3 ms |
| hybrid_rrf | 0.514 | 0.421 | 31.6 ms |
| hybrid_rerank | **0.598** | 0.497 | 177.0 ms |


I define the best practical configuration as the one that gives the strongest quality-latency tradeoff for interactive documentation search, with MRR prioritized slightly over recall@5 because users are more likely to trust the system when a relevant document appears near the top of the results. Under this criterion, **dense retrieval** is the best choice: hybrid reranking improves recall@5 by only 0.010, but has lower MRR and about 6x higher p95 latency.

All configurations meet the p95 latency constraint. The reported latency
excludes offline corpus construction and document embedding generation.
Query-time processing was measured after indexes and models were loaded, so
dense query embedding and reranker scoring are included in the timed retrieval
calls.

## Category Analysis

Average recall@5 by retrieval category:

| category | queries | bm25 | dense | hybrid_rrf | hybrid_rerank |
| --- | --- | ---: | ---: | ---: | ---: |
| `natural_language_task_description` | q01, q03, q07, q08, q10, q11, q12 | 0.564 | 0.607 | **0.707** | **0.707** |
| `exact_product_feature_lookup` | q02, q04, q05, q06, q09, q14 | 0.333 | **0.750** | 0.583 | **0.750** |
| `paraphrased_feature_discovery` | q13, q16, q17, q18 | 0.250 | **0.500** | 0.333 | 0.417 |
| `symptom_based_troubleshooting` | q15, q19, q20 | 0.000 | **0.333** | 0.167 | 0.278 |

Dense Retrieval achieved the highest or joint-highest Recall@5 in the Exact Product Feature Lookup, Paraphrased Feature Discovery, and Symptom-Based Troubleshooting categories. In contrast, hybrid methods performed best on Natural Language Task Description queries. This suggests that combining lexical and semantic signals can help recover more relevant documents when users describe a business task or objective in broad natural language rather than using specific Salesforce terminology.

The most challenging categories were Symptom-Based Troubleshooting and Paraphrased Feature Discovery. These query types are difficult because users describe a problem or desired outcome without explicitly naming the relevant Salesforce feature. In particular, BM25 completely failed on the Symptom-Based Troubleshooting category, indicating that the user wording differed substantially from the technical terminology used in the documentation. Dense Retrieval was able to recover some relevant documents through semantic matching, but performance remained limited, suggesting that these queries remain challenging even for embedding-based retrieval.



## Hard Queries

The five deliberately hard queries are q12, q16, q17, q19, and q20. These queries were designed to avoid direct target-feature lookup. Instead, they describe natural-language automation tasks, paraphrased feature discovery, or symptom-based troubleshooting scenarios.


| query | category                                | why it is hard                                                                                                                                                                                                                                 |
| ----- | --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| q12   | `natural_language_task_description`    | The query describes a desired automation behavior in natural language rather than naming a specific feature or implementation. Because there are multiple valid solution paths, the relevant labels are spread across both Apex Trigger documentation and Flow documentation. |
| q16   | `paraphrased_feature_discovery`         | The query combines multiple workflow steps and does not directly mention the key terms used in the documentation, such as Engagement Split.                                   |
| q17   | `paraphrased_feature_discovery`         | The query describes the desired debugging behavior without using official feature names such as Flow Debug or rollback mode.                                                                                                                   |
| q19   | `symptom_based_troubleshooting`         | The query describes an operational symptom: automation works for a few records but fails during bulk updates. It does not mention the underlying concepts used in the documentation, such as bulk processing, SOQL limits, or governor limits. |
| q20   | `symptom_based_troubleshooting`         | The query describes an access-control symptom, but several explanations are possible, including object permissions, sharing rules, and record-level access. This makes it ambiguous which access-control documentation should be retrieved.    |


| config | hard recall@5 | hard MRR | complete misses among hard queries |
| --- | ---: | ---: | --- |
| bm25 | 0.040 | 0.067 | q16, q17, q19, q20 |
| dense | **0.400** | **0.500** | q12, q19 |
| hybrid_rrf | 0.207 | 0.233 | q16, q19 |
| hybrid_rerank | 0.207 | 0.350 | q17, q19 |

Dense retrieval performed best on the hard-query subset, with the highest hard-query Recall@5 and MRR. This suggests that semantic matching was more effective than lexical matching when the query described an operational problem without naming the target Salesforce feature directly.

Hybrid reranking did not outperform dense retrieval on aggregate hard-query scores. It recovered different hard cases than dense retrieval, but it did not consistently rank relevant chunks higher than dense retrieval, which explains its lower MRR.

The hardest case was q19, which every configuration missed. It requires recognizing a bulk-processing failure pattern and linking it to Apex trigger bulkification and governor limits. This failure shows that symptom-based troubleshooting remains the clearest area where the best practical configuration still loses.


## Where the Best Configuration Still Loses (Dense Retrieval)


Dense retrieval returned no labelled relevant document in the top 5 for five queries: q09, q12, q13, q15, and q19. These misses were useful because they show where semantic retrieval still breaks down in Salesforce documentation search.

| query | failure pattern | explanation |
| --- | --- | --- |
| q09 | Ambiguous Salesforce term | The query asks whether the `Profile` object can be updated in Apex. Dense retrieval matched the word `Profile` to security and permission documentation instead of the Apex documentation about sObjects that do not support DML operations. |
| q12 | Natural-language automation task | The query describes the desired behavior instead of naming Apex triggers or record-triggered Flow. Dense retrieval returned nearby Flow and Email-to-Case pages, but missed the more specific Apex trigger and record-triggered Flow passages. |
| q13 | Paraphrased Marketing Cloud feature discovery | The query asks how to use Salesforce CRM data in Marketing Cloud for messaging. The relevant documentation uses more specific terms such as `Synchronized Data Sources`, `Synchronized Data Extensions`, `Contact Builder`, and `Marketing Cloud Connect`, which were not present in the query. |
| q15 | Permission and layout ambiguity | The symptom sounds like a page layout issue because the field does not appear on the Account record page. The labelled answer is actually about field-level security and field permissions, so dense retrieval returned adjacent setup and access-control pages. |
| q19 | Symptom-based troubleshooting | The query describes an automation that works for a few Case records but fails in bulk. Dense retrieval did not connect this symptom to Apex bulk trigger patterns, SOQL limits, and governor limits. |

Overall, these errors suggest that dense retrieval is strong at capturing broad semantic similarity, but still struggles when the query requires Salesforce-specific disambiguation, hidden feature-name matching, or symptom-to-cause reasoning. These cases motivate improvements such as richer chunk context, query rewriting for troubleshooting queries, and more carefully tuned hybrid reranking.


# If I Had One More Week

If I had one more week, I would improve the corpus construction, the evaluation set, and the retrieval pipeline.

For corpus construction, I would add more document context to each retrieval chunk. The current corpus contains 344 mostly text-based chunks, but Salesforce PDFs often depend on guide titles, section headings, tables, setup steps, diagrams, and screenshots. Without this context, chunks containing terms such as `routing address`, `debug options`, or `field permissions` can be difficult to distinguish across Email-to-Case, Flow Debug, and Field-Level Security documentation. I would therefore prepend guide titles and section headings to chunks, preserve table and step-by-step structures, generate short descriptions for visual content, and store parent document metadata. I would also test grouping results from the same page or section.

For evaluation, I would expand the 20-query benchmark, especially in the hardest categories: symptom-based troubleshooting and paraphrased feature discovery. I would also add more natural-language automation cases to test whether dense retrieval can consistently handle broad, goal-oriented user phrasing.

I would also tune the hybrid retrieval and reranking pipeline rather than assuming the current hybrid settings are optimal. The current results show that hybrid methods recovered different hard cases from dense retrieval, so better weighting, candidate depth, or reranker calibration might improve robustness on difficult queries.

Finally, I would inspect hard misses to see whether they are caused by poor chunk boundaries, missing section context, ambiguous labels, or model limitations. This would make the benchmark more representative of real Salesforce documentation search, where users often describe their goal or problem without knowing the exact Salesforce feature name.


# Reproduce

Install dependencies:

```bash
pip install -r requirements.txt
```

Reproduce the reported benchmark results from the checked-in processed corpus:

```bash
make run
```

If `make` is not available on Windows, use the equivalent PowerShell command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run.ps1
```

Both commands write `results/metrics.csv`, `results/per_query_results.csv`, and
`results/metrics_plot.png`.

To rebuild the processed corpus from the raw source list before evaluation, the
local PDF references in `data/raw/source_urls.txt` must also be available on the
machine, or replaced with equivalent public PDF URLs. Then run:

```bash
make build-corpus
make inspect
make run
```
