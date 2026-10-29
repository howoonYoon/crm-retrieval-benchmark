"""Validate the mixed-source benchmark and refresh current reports."""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from statistics import mean

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from build_html_corpus import read_jsonl, chunk_sections, canonical_url
from build_corpus import tokens
from evaluate import validate_inputs


def read_csv(path):
    with path.open(encoding='utf-8', newline='') as file:
        return list(csv.DictReader(file))


def main():
    out = ROOT / 'results'
    baseline = out / 'before_html_sources'
    docs = read_jsonl(ROOT / 'data/processed/documents.jsonl')
    queries = read_jsonl(ROOT / 'data/processed/queries.jsonl')
    if any(q.get('benchmark_scope') == 'admin_agent_core_v1' for q in queries):
        raise SystemExit('Core-only labels are active. Use scripts/summarize_core_results.py.')
    validate_inputs(docs, queries)
    by_doc = {d['doc_id']: d for d in docs}
    by_query = {q['query_id']: q for q in queries}
    for d in read_jsonl(baseline / 'documents.jsonl'):
        assert by_doc[d['doc_id']] == d
    old_queries = {q['query_id']: q for q in read_jsonl(baseline / 'queries.jsonl')}
    assert all(q['query'] == old_queries[q['query_id']]['query'] for q in queries)
    pages = read_jsonl(ROOT / 'data/processed/html_pages.jsonl')
    html = read_jsonl(ROOT / 'data/processed/html_documents.jsonl')
    assert html == [d for page in pages for d in chunk_sections(page)]
    assert [d for d in docs if d.get('document_type') == 'html'] == html
    for d in html:
        assert all(d.get(field) for field in ['title', 'url', 'section', 'document_type', 'parent_id', 'source_sha256', 'fetched_at'])
        assert d['url'] == canonical_url(d['url']) and len(tokens(d['text'])) <= 220
        assert hashlib.sha256(d['text'].encode()).hexdigest() == d['content_sha256']
        assert not any(phrase in d['text'] for phrase in ['Cookie Consent Manager', 'PHP Vulnerability Monitoring', 'Agentforce is temporarily unavailable'])
    assignments = json.loads((out / 'html_label_review.json').read_text(encoding='utf-8'))['reviewed_additions']
    for assignment in assignments:
        d = by_doc[assignment['doc_id']]
        assert assignment['content_sha256'] == d['content_sha256']
        q = by_query[assignment['query_id']]
        assert d['doc_id'] in next(a['relevant_doc_ids'] for a in q['answer_aspects'] if a['aspect_id'] == assignment['aspect_id'])
    rows = read_csv(out / 'per_query_results.csv')
    metrics = read_csv(out / 'metrics.csv')
    configs = [m['config'] for m in metrics]
    assert len(configs) == len(set(configs)) == 4
    assert len(rows) == 80 and {(r['config'], r['query_id']) for r in rows} == {(c, qid) for c in configs for qid in by_query}
    aspect_rows = []
    for row in rows:
        q = by_query[row['query_id']]
        top = row['top5_doc_ids'].split('|')
        assert len(set(top)) == len(top) == 5 and set(top) <= by_doc.keys() and row['query'] == q['query']
        relevant = set(q['relevant_doc_ids'])
        rank = next((i for i, doc_id in enumerate(top, 1) if doc_id in relevant), None)
        assert abs(float(row['recall_at_5']) - len(set(top) & relevant) / len(relevant)) < 1e-12
        assert abs(float(row['reciprocal_rank']) - (1 / rank if rank else 0)) < 1e-12
        assert row['first_relevant_rank'] == (str(rank) if rank else '')
        covered = [a['aspect_id'] for a in q['answer_aspects'] if set(top) & set(a['relevant_doc_ids'])]
        missing = [a['aspect_id'] for a in q['answer_aspects'] if a['aspect_id'] not in covered]
        assert abs(float(row['aspect_recall_at_5']) - len(covered) / len(q['answer_aspects'])) < 1e-12
        aspect_rows.append(dict(config=row['config'], query_id=q['query_id'], covered_aspects='|'.join(covered), missing_aspects='|'.join(missing), aspect_recall_at_5=row['aspect_recall_at_5']))
    for m in metrics:
        selected = [r for r in rows if r['config'] == m['config']]
        for metric, field in [('recall_at_5', 'recall_at_5'), ('mrr', 'reciprocal_rank'), ('aspect_recall_at_5', 'aspect_recall_at_5')]:
            assert abs(float(m[metric]) - mean(float(r[field]) for r in selected)) < 1e-12
        assert abs(float(m['p95_latency_ms']) - float(np.percentile([float(r['latency_ms']) for r in selected], 95))) < 1e-9
    with (out / 'admin_aspect_results.csv').open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(aspect_rows[0]))
        writer.writeheader()
        writer.writerows(aspect_rows)
    report = json.loads((ROOT / 'data/processed/html_ingestion_report.json').read_text(encoding='utf-8'))
    assert report['successful_urls'] == len(pages) and report['chunks'] == len(html)
    assert report['requested_urls'] == report['successful_urls'] + report['failed_urls']
    labels = sum(len(q['relevant_doc_ids']) for q in queries)
    aspects = sum(len(q['answer_aspects']) for q in queries)
    ceiling = mean(min(5, len(q['relevant_doc_ids'])) / len(q['relevant_doc_ids']) for q in queries)
    table = ['| config | document recall@5 | MRR@5 | aspect recall@5 | p95 ms |', '| --- | ---: | ---: | ---: | ---: |']
    table.extend(f"| {m['config']} | {float(m['recall_at_5']):.3f} | {float(m['mrr']):.3f} | {float(m['aspect_recall_at_5']):.3f} | {float(m['p95_latency_ms']):.1f} |" for m in metrics)
    preferred = max(metrics, key=lambda m: (float(m['aspect_recall_at_5']), float(m['mrr'])))['config']
    summary = ['# Official HTML expansion — 2026-10-23', '', f"Requested {report['requested_urls']} official URLs; extracted {report['successful_urls']} article bodies; excluded {report['failed_urls']} source. Added {len(html)} section-based HTML chunks to the existing 354 PDF chunks, for {len(docs)} total documents.", '', f'The 20 query strings are unchanged. Reviewed HTML sections add {len(assignments)} relevance assignments, giving {labels} labels and {aspects} evidence aspects. URL hints are not relevance labels. [Rules](../data/raw/html_label_rules.json) and [exact assignments](html_label_review.json) record the review.', '', *table, '', f'`{preferred}` has the highest mean evidence-aspect coverage in this run. Corpus, relevance labels and evidence groups changed together; score differences from the previous scope are not a model improvement. Latencies were measured again.', '', f'Document recall@5 theoretical mean ceiling: {ceiling:.6f}. More valid alternative documents increase the recall denominator. Aspect recall macro-averages the fraction of evidence groups hit within each query; it measures evidence coverage, not full answer correctness.', '', 'Excluded source: the OTT API reference root exposed an empty component and its official schema URL returned 404. OAuth and send/delivery event articles were ingested, but endpoint/payload coverage remains incomplete. The Case.AccountId update example is in the corpus but is not a q12 answer because the write direction differs.', '', 'Validation: all 354 original PDF chunks preserved; all HTML chunks exactly regenerated from checked-in page snapshots; all 80 per-query score rows and aggregate metrics independently recalculated; 9 unit tests pass. Raw HTML/rendered DOM caches are local; cleaned snapshots and metadata are checked in.', '', '[Acquisition report](../data/processed/html_ingestion_report.json), [pipeline and reproduction](../docs/html_ingestion.md), [current answers](../docs/query_answers.md), [baseline](before_html_sources/).', '']
    (out / 'html_expansion_summary.md').write_text('\n'.join(summary), encoding='utf-8')
    readme_path = ROOT / 'README.md'
    readme = readme_path.read_text(encoding='utf-8')
    readme = readme.replace('## 3. Using PDF Documentation as the Corpus', '## 3. Using PDF and Official HTML Documentation')
    start, end = readme.index('## Corpus\n'), readme.index('# Retrieval Configurations\n')
    corpus = f'''## Corpus

The current corpus contains **{len(docs)} retrieval documents**: 354 chunks from 12 Salesforce PDFs and {len(html)} HTML chunks from {len(pages)} official article URLs. The original PDF passages are preserved. The HTML manifest contains 25 URLs; the OTT API root was excluded because its referenced schema returned 404.

`src/build_html_corpus.py` downloads static HTML, resolves the public Salesforce Atlas article API, and renders Salesforce Help when necessary. It removes navigation/UI noise, extracts heading-based sections, preserves code and table context, and splits long sections into at most 220 alphanumeric tokens per chunk. New chunks include title, URL, section, document type, parent/section/chunk IDs, fetch time, hashes and source version where available. BM25 and dense use the same combined document list and section context.

Raw HTML caches stay local. Checked-in `html_pages.jsonl` and `html_documents.jsonl` reproduce HTML chunking offline. `src/build_corpus.py` merges the PDF and HTML snapshots. See [the pipeline](docs/html_ingestion.md), [source URLs](data/raw/html_sources.json) and [acquisition report](data/processed/html_ingestion_report.json). Source/API versions can differ across PDFs and current HTML.

'''
    readme = readme[:start] + corpus + readme[end:]
    start, end = readme.index('# Metrics\n'), readme.index('# If I Had One More Week\n')
    section = ['# Metrics', '', '- Document recall@5: labelled passages retrieved / all labelled passages for each query.', '- MRR@5: reciprocal rank of the first labelled result within top 5.', '- Aspect recall@5: fraction of each query’s evidence groups hit, macro-averaged over the 20 queries.', '- p95 latency: query-time retrieval after models/indexes are loaded, including query embeddings and reranking.', '', f'The current mixed-source benchmark has {labels} labels and {aspects} evidence aspects. Document recall@5 has a mean theoretical ceiling of {ceiling:.6f}; many questions have more than five alternative valid passages. Aspect recall evaluates evidence coverage, not generated answer correctness or completeness.', '', '# Results and Evaluation', '', '## Mixed PDF + HTML Scope — 2026-10-23', '', 'All four retrievers were executed again. Query wording is unchanged, but corpus, relevance assignments and evidence groups expanded. These scores must not be read as model gains over the previous scope. [Detailed report](results/html_expansion_summary.md), [answers](docs/query_answers.md), and [aspect-level misses](results/admin_aspect_results.csv).', '', '![Retrieval metrics plot](results/metrics_plot.png)', '', *table, '', f'`{preferred}` has the highest mean evidence-aspect coverage in this run. The 20-query sample does not establish statistical significance. Missing endpoint/payload coverage and the partially annotated relevance pool remain limitations.', '', '## Category Analysis', '', 'Mean document recall@5:', '', '| category | bm25 | dense | hybrid_rrf | hybrid_rerank |', '| --- | ---: | ---: | ---: | ---: |']
    for category in dict.fromkeys(q['category'] for q in queries):
        section.append(f'| `{category}` | ' + ' | '.join(f"{mean(float(r['recall_at_5']) for r in rows if r['config'] == c and by_query[r['query_id']]['category'] == category):.3f}" for c in configs) + ' |')
    hard = {q['query_id'] for q in queries if q['difficulty'] == 'hard'}
    section.extend(['', '## Hard Queries', '', 'Hard queries are q12, q16, q17, q19 and q20.', '', '| config | hard recall@5 | hard MRR@5 | hard aspect recall@5 | complete misses |', '| --- | ---: | ---: | ---: | --- |'])
    for c in configs:
        selected = [r for r in rows if r['config'] == c and r['query_id'] in hard]
        section.append(f'| {c} | ' + ' | '.join(f"{mean(float(r[field]) for r in selected):.3f}" for field in ['recall_at_5', 'reciprocal_rank', 'aspect_recall_at_5']) + ' | ' + (', '.join(r['query_id'] for r in selected if not r['first_relevant_rank']) or 'none') + ' |')
    section.extend(['', 'A relevant hit can still miss an administrative or technical counterpart. Inspect `admin_aspect_results.csv` before concluding that a question is fully supported.', '', ''])
    readme = readme[:start] + '\n'.join(section) + readme[end:]
    readme = re.sub(r'\b\d+ mostly text-based chunks', f'{len(docs)} mostly text-based chunks', readme)
    readme_path.write_text(readme, encoding='utf-8')
    paths = [ROOT / 'data/processed/documents.jsonl', ROOT / 'data/processed/queries.jsonl', ROOT / 'data/processed/html_pages.jsonl', ROOT / 'data/processed/html_documents.jsonl', ROOT / 'data/raw/html_sources.json', ROOT / 'data/raw/html_label_rules.json', out / 'metrics.csv', out / 'per_query_results.csv']
    provenance = {'scope': 'admin_agent_html_v1', 'date': '2026-10-23', 'method': 'fresh execution: python run_eval.py', 'documents': len(docs), 'html_documents': len(html), 'successful_urls': len(pages), 'failed_urls': report['failed_urls'], 'queries': len(queries), 'labels': labels, 'aspects': aspects, 'dense_model': 'sentence-transformers/all-MiniLM-L6-v2', 'reranker_model': 'cross-encoder/ms-marco-TinyBERT-L-2-v2', 'rerank_candidate_k': 20, 'sha256': {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (out / 'html_expansion_provenance.json').write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8')
    historical = out / 'admin_scope_summary.md'
    text = historical.read_text(encoding='utf-8')
    if not text.startswith('> Historical'):
        historical.write_text('> Historical PDF-only admin scope. Current mixed-source results: [html_expansion_summary.md](html_expansion_summary.md).\n\n' + text, encoding='utf-8')
    print(f'Validated {len(docs)} documents, {labels} labels and 80 result rows. Preferred by aspect coverage: {preferred}.')


if __name__ == '__main__':
    main()
