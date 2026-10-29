"""Validate admin-scope evidence/results and refresh the benchmark narrative."""
from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import re
import sys
from pathlib import Path
from statistics import mean

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from build_corpus import tokens
from evaluate import validate_inputs


def load(path):
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def csv_rows(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main():
    results = ROOT / 'results'
    baseline = results / 'before_admin_scope'
    queries = load(ROOT / 'data/processed/queries.jsonl')
    if any(q.get('benchmark_scope') in {'admin_agent_html_v1', 'admin_agent_core_v1'} for q in queries):
        raise SystemExit('A newer scope is active; use summarize_html_expansion.py or summarize_core_results.py.')
    documents = load(ROOT / 'data/processed/documents.jsonl')
    validate_inputs(documents, queries)
    by_id = {q['query_id']: q for q in queries}
    docs = {d['doc_id']: d for d in documents}
    old_q = {q['query_id']: q for q in load(baseline / 'queries.jsonl')}
    for q in queries:
        assert q['query'] == old_q[q['query_id']]['query']
        assert q['requester_role'] == old_q[q['query_id']]['user_role']
    for d in load(baseline / 'documents.jsonl'):
        assert docs[d['doc_id']] == d
    raw = {p.stem: load(p) for p in (ROOT / 'data/raw/pdf_text').glob('*.jsonl')}
    for i in {i for q in queries for i in q['relevant_doc_ids']}:
        d = docs[i]
        text = ' '.join(tokens(' '.join(r['text'] for r in raw[Path(d['source_file']).stem] if d['page_start'] <= r['page'] <= d['page_end'])))
        assert ' '.join(tokens(d['text'])) in text, i
        if d.get('curation_key'):
            source = ' '.join(r['text'] for r in raw[Path(d['source_file']).stem] if d['page_start'] <= r['page'] <= d['page_end'])
            assert d['text'] in source, i
    rows = csv_rows(results / 'per_query_results.csv')
    metrics = csv_rows(results / 'metrics.csv')
    configs = [m['config'] for m in metrics]
    assert len(configs) == len(set(configs)) == 4
    assert len(rows) == 80 and {(r['config'], r['query_id']) for r in rows} == {(c, qid) for c in configs for qid in by_id}
    coverage_rows = []
    for row in rows:
        q = by_id[row['query_id']]
        top = row['top5_doc_ids'].split('|')
        assert row['query'] == q['query'] and len(top) == len(set(top)) == 5 and set(top) <= docs.keys()
        relevant = set(q['relevant_doc_ids'])
        rank = next((i for i, d in enumerate(top, 1) if d in relevant), None)
        assert abs(float(row['recall_at_5']) - len(set(top) & relevant) / len(relevant)) < 1e-12
        assert abs(float(row['reciprocal_rank']) - (1 / rank if rank else 0)) < 1e-12
        assert row['first_relevant_rank'] == (str(rank) if rank else '')
        covered = [a['aspect_id'] for a in q['answer_aspects'] if set(a['relevant_doc_ids']) & set(top)]
        missing = [a['aspect_id'] for a in q['answer_aspects'] if a['aspect_id'] not in covered]
        assert abs(float(row['aspect_recall_at_5']) - len(covered) / len(q['answer_aspects'])) < 1e-12
        coverage_rows.append({'config': row['config'], 'query_id': q['query_id'], 'covered_aspects': '|'.join(covered), 'missing_aspects': '|'.join(missing), 'aspect_recall_at_5': row['aspect_recall_at_5']})
    for m in metrics:
        selected = [r for r in rows if r['config'] == m['config']]
        for metric, field in [('recall_at_5', 'recall_at_5'), ('mrr', 'reciprocal_rank'), ('aspect_recall_at_5', 'aspect_recall_at_5')]:
            assert abs(float(m[metric]) - mean(float(r[field]) for r in selected)) < 1e-12
        assert abs(float(m['p95_latency_ms']) - float(np.percentile([float(r['latency_ms']) for r in selected], 95))) < 1e-9
    with (results / 'admin_aspect_results.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(coverage_rows[0]))
        writer.writeheader()
        writer.writerows(coverage_rows)
    old_metrics = {m['config']: m for m in csv_rows(baseline / 'metrics.csv')}
    count_labels = sum(len(q['relevant_doc_ids']) for q in queries)
    ceiling = mean(min(5, len(q['relevant_doc_ids'])) / len(q['relevant_doc_ids']) for q in queries)
    max_labels = max(len(q['relevant_doc_ids']) for q in queries)
    preferred = max(metrics, key=lambda m: (float(m['aspect_recall_at_5']), float(m['mrr'])))['config']
    extra = sum(bool(d.get('curation_key')) for d in documents)
    summary = ['# Admin-agent benchmark update — 2026-10-23', '', f'All 20 queries target a CRM admin/developer agent. Original query strings, requester roles and all 344 original documents are preserved. The corpus now has {len(documents)} documents, {count_labels} relevance labels and {sum(len(q["answer_aspects"]) for q in queries)} answer-evidence aspects.', '', f'Nine reviewed PDF sections add {extra} passages with stable supplemental IDs. Supplemental passages preserve source punctuation and newlines, including Apex and SQL code. The original 344 passages retain their existing tokenized representation. Rebuilding from cached PDFs reproduces the complete corpus. Every current label was verified against its declared source PDF extraction.', '', '| config | recall@5 | MRR@5 | aspect recall@5 | p95 ms |', '| --- | ---: | ---: | ---: | ---: | ---: |']
    for m in metrics:
        summary.append(f"| {m['config']} | {float(m['recall_at_5']):.3f} | {float(m['mrr']):.3f} | {float(m['aspect_recall_at_5']):.3f} | {float(m['p95_latency_ms']):.1f} |")
    summary.extend(['', f'`{preferred}` has the highest mean evidence-aspect coverage in this run. Aspect recall measures retrieved evidence groups, including alternative implementation routes. It does not measure generated answer correctness or require that every route be executed.', '', f'There are 1–{max_labels} labels per query; document recall@5 has a dataset ceiling of {ceiling:.6f}. Aspect recall macro-averages groups within each query, then averages the 20 queries. A hit is any reviewed passage in a group. This avoids counting every overlapping document as a separate required answer; it can still overestimate complete evidence when a group contains several different details.', '', 'Corpus, labels and evaluation scope changed together. These scores are a new benchmark version and cannot be interpreted as model improvements over the previous scope. Latency is a fresh measurement.', '', '| config | previous recall@5 | current recall@5 | previous MRR | current MRR |', '| --- | ---: | ---: | ---: | ---: |'])
    for m in metrics:
        old = old_metrics[m['config']]
        summary.append(f"| {m['config']} | {float(old['recall_at_5']):.3f} | {float(m['recall_at_5']):.3f} | {float(old['mrr']):.3f} | {float(m['mrr']):.3f} |")
    summary.extend(['', 'Known evidence gaps: exact AccountContactRelation DML/API specification, Quote/QuoteLineItem APIs, Profile metadata-update APIs and WhatsApp REST sending APIs. The guide marks these gaps rather than inventing executable code. Supplemental Apex security passages describe API-version-dependent behavior; use the pinned source version rather than treating its defaults as universal.', '', '[Answers and aspect evidence](../docs/query_answers.md), [per-query aspect results](admin_aspect_results.csv), [changes](admin_scope_changes.json), [baseline](before_admin_scope/).', ''])
    (results / 'admin_scope_summary.md').write_text('\n'.join(summary), encoding='utf-8')

    readme_path = ROOT / 'README.md'
    readme = readme_path.read_text(encoding='utf-8')
    start, end = readme.index('## 1. '), readme.index('## 2. Varying Query Difficulty')
    readme = readme[:start] + '''## 1. Targeting a CRM Admin Agent

Every query is evaluated from the perspective of a CRM administrator/developer assisting users. The original requester can be a sales, service or marketing user; this is preserved in `requester_role`.

Answers cover configuration, permissions, data models, automation, integration and technical execution conditions. Relevant Apex, Flow and SQL implementation paths are included without requiring Apex when the task explicitly excludes it or the product uses another mechanism. Missing API-level evidence is documented rather than filled with unverified code.

Each query has reviewed `answer_aspects` and supporting document IDs. These groups measure evidence retrieval for administrative and technical answer components or alternative implementation paths. The [answer guide](docs/query_answers.md) explains each question and its evidence boundaries.

''' + readme[end:]
    readme = re.sub(r'\b\d+ retrieval documents', f'{len(documents)} retrieval documents', readme)
    readme = re.sub(r'\b\d+ mostly text-based chunks', f'{len(documents)} mostly text-based chunks', readme)
    start, end = readme.index('# Metrics\n'), readme.index('# If I Had One More Week\n')
    section = ['# Metrics', '', '- Document recall@5: retrieved labelled documents / all labelled documents for each query.', '- MRR@5: reciprocal rank of the first labelled result within the returned top 5.', '- Aspect recall@5: fraction of a query’s reviewed evidence groups with at least one result, macro-averaged over queries.', '- p95 latency: query-time retrieval after models and indexes are loaded, including query embeddings and reranking.', '', f'The admin-agent version contains {len(documents)} documents, 20 queries and {count_labels} labels (1–{max_labels} per query). Document recall@5 has a theoretical mean ceiling of {ceiling:.6f} because some queries have more than five valid documents. Aspect recall measures evidence coverage, not generated answer correctness; groups can represent alternative implementation routes.', '', '# Results and Evaluation', '', '## Admin-agent Scope — 2026-10-23', '', 'All four retrievers were executed again after corpus and label expansion. [Detailed changes and limitations](results/admin_scope_summary.md), [answers](docs/query_answers.md), [aspect-level misses](results/admin_aspect_results.csv), and [the previous version](results/before_admin_scope/) are available. The previous scope’s scores are not directly comparable as a model improvement.', '', '![Retrieval metrics plot](results/metrics_plot.png)', '', '| config | recall@5 | MRR@5 | aspect recall@5 | p95 latency |', '| --- | ---: | ---: | ---: | ---: | ---: |']
    section.extend(f"| {m['config']} | {float(m['recall_at_5']):.3f} | {float(m['mrr']):.3f} | {float(m['aspect_recall_at_5']):.3f} | {float(m['p95_latency_ms']):.1f} ms |" for m in metrics)
    section.extend(['', f'`{preferred}` has the highest mean evidence-aspect coverage in this run. All four p95 measurements are below one second.' if all(float(m['p95_latency_ms']) < 1000 for m in metrics) else f'`{preferred}` has the highest evidence-aspect coverage. Consult the measured latency table for the one-second target.', '', 'This is a 20-query retrieval benchmark. It does not establish that a deployed agent can safely or correctly execute configuration changes or code. Known gaps include exact AccountContactRelation/Quote APIs and Profile metadata-update instructions.', '', '## Category Analysis', '', 'Mean document recall@5:', '', '| category | bm25 | dense | hybrid_rrf | hybrid_rerank |', '| --- | ---: | ---: | ---: | ---: |'])
    for category in dict.fromkeys(q['category'] for q in queries):
        section.append(f'| `{category}` | ' + ' | '.join(f"{mean(float(r['recall_at_5']) for r in rows if r['config'] == c and by_id[r['query_id']]['category'] == category):.3f}" for c in configs) + ' |')
    hard_ids = {q['query_id'] for q in queries if q['difficulty'] == 'hard'}
    section.extend(['', '## Hard Queries', '', 'The hard subset is q12, q16, q17, q19 and q20. Expanded evidence includes Apex and Flow bulk processing, SQL non-engagement audiences, and Apex security context. q19 is no longer interpreted as necessarily Apex-only.', '', '| config | hard recall@5 | hard MRR@5 | hard aspect recall@5 | complete misses |', '| --- | ---: | ---: | ---: | --- |'])
    for c in configs:
        selected = [r for r in rows if r['config'] == c and r['query_id'] in hard_ids]
        section.append(f'| {c} | ' + ' | '.join(f"{mean(float(r[field]) for r in selected):.3f}" for field in ['recall_at_5', 'reciprocal_rank', 'aspect_recall_at_5']) + ' | ' + (', '.join(r['query_id'] for r in selected if not r['first_relevant_rank']) or 'none') + ' |')
    missing = [r['query_id'] for r in rows if r['config'] == preferred and not r['first_relevant_rank']]
    section.extend(['', f'`{preferred}` has no labelled result for: {", ".join(missing) or "none"}. Queries with a relevant hit can still miss their administrative or technical counterpart; inspect `admin_aspect_results.csv` for these partial-evidence failures.', '', ''])
    readme_path.write_text(readme[:start] + '\n'.join(section) + readme[end:], encoding='utf-8')
    paths = [ROOT / 'data/processed/documents.jsonl', ROOT / 'data/processed/queries.jsonl', ROOT / 'data/raw/admin_passages.json', results / 'metrics.csv', results / 'per_query_results.csv']
    provenance = {'date': '2026-10-23', 'scope': 'admin_agent_v1', 'method': 'fresh execution: python run_eval.py', 'original_documents_preserved': 344, 'documents': len(documents), 'queries': len(queries), 'labels': count_labels, 'answer_aspects': sum(len(q['answer_aspects']) for q in queries), 'validated_rows': len(rows), 'dense_model': 'sentence-transformers/all-MiniLM-L6-v2', 'reranker_model': 'cross-encoder/ms-marco-TinyBERT-L-2-v2', 'rerank_candidate_k': 20, 'packages': {name: importlib.metadata.version(name) for name in ['sentence-transformers', 'torch', 'numpy', 'rank-bm25']}, 'sha256': {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (results / 'admin_scope_provenance.json').write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8')
    historical = results / 'label_review_summary.md'
    banner = '> Historical 2026-10-22 label-only review. Current admin-agent results: [admin_scope_summary.md](admin_scope_summary.md).\n\n'
    old_text = historical.read_text(encoding='utf-8')
    if not old_text.startswith('> Historical'):
        historical.write_text(banner + old_text, encoding='utf-8')
    print(f'Validated {count_labels} labels against raw pages and all 80 result rows; refreshed README and admin reports.')


if __name__ == '__main__':
    main()
