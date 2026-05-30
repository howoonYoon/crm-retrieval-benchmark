# Salesforce CRM Operations Retrieval Benchmark

Comparison of retrieval configurations (BM25 vs Dense vs Hybrid vs Reranker) on public Salesforce Service Cloud, Sales Cloud, Marketing Cloud, and Developer documentation.

# Why I Picked This Assignment

I chose this assignment because it is closely related to my previous experience operating and developing Salesforce-based CRM systems. At the time, Salesforce was a relatively new platform within the team, so we frequently relied on official documentation for feature implementation, configuration changes, troubleshooting, and new business requirements.

In a real CRM environment, finding the right information quickly is critical. Salesforce documentation is extensive and spans many areas, including Sales Cloud, Service Cloud, Marketing Cloud, Apex, Flow, and Security. Users also do not always search using official Salesforce terminology. They often describe business problems, operational issues, or desired outcomes in natural language.

Because of this, I wanted to evaluate how different retrieval approaches perform in a realistic CRM documentation search scenario. The goal was to compare whether different retrieval methods could handle both exact technical terminology and the natural language queries that arise during day-to-day CRM operations.

# Decisions I Made

## 1. Creating Queries from Multiple User Perspectives

The queries were designed from the perspectives of different Salesforce users rather than focusing only on developers.

The user groups included:

* CRM Administrators and Developers
* Sales Users
* Call Center Agents
* Marketing Users

For example, developers are more likely to search for technical topics such as Apex Triggers or Governor Limits, while sales users may search for Opportunity or Quote management. Call center agents are more likely to look for documentation related to Email-to-Case, case management, or access issues.

Because Salesforce is used by many different roles within an organization, I believed that including queries from multiple perspectives would create a more realistic retrieval benchmark.

## 2. Varying Query Difficulty

Some queries directly include official Salesforce terminology such as Email-to-Case or Governor Limits.

For harder queries, I described business scenarios and symptoms instead of naming the target feature directly. Examples include situations where an automation fails only for certain users or where a process breaks when handling large volumes of records.

This approach allows the evaluation to measure not only keyword matching performance but also the ability to retrieve relevant documentation from natural language descriptions.

## 3. Using PDF Documentation as the Corpus

I initially considered collecting Salesforce documentation directly from the web.

However, Salesforce documentation relies heavily on JavaScript-based dynamic rendering, which makes reliable collection more difficult. Since reproducibility was an important requirement for this assignment, I chose publicly available PDF documentation as the corpus so that the dataset could be recreated consistently on another machine.


## Corpus

The default corpus build currently writes 344 retrieval documents extracted
from public Salesforce PDF documentation related to customer support
workflows, account and contract-related records, customer communication
processes, and CRM automation. Long PDF pages and selected continuous sections
are split into focused retrieval documents so that the system retrieves
specific documentation passages rather than entire guides.

Salesforce CRM operations documentation is a good benchmark corpus because it
contains both exact product terminology and operational questions that users
often phrase indirectly. That makes it useful for comparing lexical retrieval,
dense retrieval, hybrid retrieval, and reranking.

Raw PDF source URLs are tracked in `data/raw/source_urls.txt`.
`src/build_corpus.py` downloads those PDFs into an ignored local cache, extracts
page text, filters CRM-operations-related chunks, and writes
`data/processed/documents.jsonl`.

## Data Format

`data/processed/documents.jsonl`:

```json
{"doc_id":"sales_core_p0096_002","title":"Sales Core Guide p96 chunk 2: Troubleshoot Lead Conversion","url":"https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sales_core.pdf#page=96","source_file":"sales_core.pdf","product_area":"Sales Lifecycle","page_start":96,"page_end":96,"text":"Documentation passage text..."}
```

`data/processed/queries.jsonl`:

```json
{"query_id":"q01","query":"I am converting a Lead, but Salesforce shows a duplicate Account warning. How should I handle the duplicate record during lead conversion?","relevant_doc_ids":["sales_core_p0096_002"],"difficulty":"easy","category":"natural_language_task_description"}
```

The 20 hand-written queries are grouped by retrieval category and difficulty in
[`docs/query_set.md`](docs/query_set.md). Machine-readable labels are stored in
`data/processed/queries.jsonl`.

## Retrieval Configurations

The benchmark evaluates four configurations on the same documents and queries:

- `bm25`: lexical BM25 retrieval.
- `dense`: dense retrieval with a SentenceTransformers embedding model.
- `hybrid_rrf`: reciprocal-rank-fusion blend of BM25 and dense retrieval.
- `hybrid_rerank`: hybrid RRF candidate generation followed by a CrossEncoder
  reranker over the top 20 candidates.

## Metrics

The evaluation reports:

- `recall@5`
- `MRR`
- `p95_latency_ms`

Latency is measured after indexes and embedding models are loaded. The target is
p95 retrieval latency under 1 second on a single laptop or free-tier VM.
Each query has between 1 and 5 labelled relevant documents, so recall@5 is not
artificially capped by having more than five relevant labels.

## Results

The benchmark was run on 344 retrieval documents and 20 labelled queries,
including 5 hard queries.

| config | recall@5 | MRR | p95 latency |
| --- | ---: | ---: | ---: |
| bm25 | 0.347 | 0.304 | 1.9 ms |
| dense | 0.588 | 0.567 | 8.9 ms |
| hybrid_rrf | 0.514 | 0.421 | 11.9 ms |
| hybrid_rerank | 0.598 | 0.497 | 111.4 ms |

I choose dense retrieval as the best practical configuration for this corpus.
Hybrid reranking has the highest recall@5 by a narrow margin, but dense has the
highest MRR, nearly the same recall@5, and much lower p95 latency. BM25 is the
fastest baseline, but it misses more paraphrased and cross-guide queries. Plain
hybrid RRF improves over BM25 but does not beat dense-only retrieval on this
corpus.

All configurations meet the p95 latency constraint. The reported latency
excludes corpus construction and dense embedding generation, and measures
retrieval after indexes and models are loaded.

## Category Analysis

| category | queries | best recall@5 | dense recall@5 | note |
| --- | --- | ---: | ---: | --- |
| `natural_language_task_description` | q01, q03, q07, q08, q10, q11 | 0.792 | 0.708 | Hybrid methods retrieved more of the top-five evidence, but dense kept the strongest MRR. |
| `exact_product_feature_lookup` | q02, q04, q05, q06, q09, q14 | 0.750 | 0.750 | Dense and reranking tied on recall; BM25 was weaker despite exact terms because chunks often contain repeated nearby terminology. |
| `cross_object_or_cross_system_workflow` | q12, q13, q16 | 0.289 | 0.222 | All methods struggled because answers span Flow, Apex, Contact Builder, Journey Builder, and synchronized data. |
| `symptom_based_troubleshooting` | q15, q19, q20 | 0.333 | 0.333 | Dense was best on recall, but failures remain when symptoms do not name the underlying feature. |
| `paraphrased_feature_discovery` | q17, q18 | 0.667 | 0.667 | Dense and hybrid RRF handled feature discovery better than BM25 and reranking. |

## Hard Queries

The five deliberately hard queries are q12, q13, q16, q17, and q19. Dense
retrieval has the best hard-query MRR at 0.300, while hybrid reranking has lower
MRR but slightly better hard-query recall@5.

| config | hard recall@5 | hard MRR | complete misses |
| --- | ---: | ---: | --- |
| bm25 | 0.040 | 0.067 | q13, q16, q17, q19 |
| dense | 0.200 | 0.300 | q12, q13, q19 |
| hybrid_rrf | 0.107 | 0.167 | q13, q16, q19 |
| hybrid_rerank | 0.173 | 0.200 | q17, q19 |

## Dense Failure Analysis

Dense retrieval completely missed five queries: q09, q12, q13, q15, and q19.
The q09 miss is an exact-looking Apex DML question, but dense retrieved
security-profile pages because the word `Profile` is heavily represented in
security documentation. q12 and q13 require connecting multiple Salesforce
areas, so dense retrieved nearby Flow, Email-to-Case, and Marketing Cloud pages
instead of the specific trigger and synchronized-data-source passages. q15
confuses page layout, record access, and field-level security language, causing
dense to retrieve adjacent setup and access-control pages. q19 is the clearest
failure: the user describes a bulk failure symptom, but the labelled answer uses
developer terms such as bulk triggers, SOQL query limits, and governor limits.
This is the main category where the best practical configuration still loses.


# If I Had One More Week

If I had one more week, I would improve both the corpus construction and the evaluation set.

For corpus construction, I would add more document context to each retrieval chunk. The current corpus contains 344 mostly text-based chunks, but Salesforce PDFs often depend on guide titles, section headings, tables, setup steps, diagrams, and screenshots. Without this context, chunks containing terms such as “routing address,” “debug options,” or “field permissions” can be difficult to distinguish across Email-to-Case, Flow Debug, and Field-Level Security documentation. I would therefore prepend guide titles and section headings to chunks, preserve table and step-by-step structures, generate short descriptions for visual content, and store parent document metadata. I would also test grouping results from the same page or section.

For evaluation, I would expand the 20-query benchmark, especially in the hardest categories: cross-object or cross-system workflows, symptom-based troubleshooting, and paraphrased feature discovery. I would also inspect hard misses to see whether they are caused by poor chunk boundaries, missing section context, ambiguous labels, or model limitations. This would make the benchmark more representative of real Salesforce documentation search, where users often describe their goal or problem without knowing the exact Salesforce feature name.

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

To rebuild the processed corpus from the raw source list before evaluation, run:

```bash
make build-corpus
make inspect
make run
```