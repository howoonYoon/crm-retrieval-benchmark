"""Validate core-only scores, optionally rescoring an identical saved retrieval run."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from statistics import mean

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from build_html_corpus import read_jsonl
from evaluate import SearchResult, first_relevant_rank, recall_at_k, reciprocal_rank, validate_inputs, write_csv
from plot_results import plot_metrics
from summarize_admin_scope import csv_rows


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rescore-saved', action='store_true', help='Use the archived top-5 ranks and measured latencies, requiring unchanged corpus and query text')
    args = parser.parse_args()
    out = ROOT / 'results'
    base = out / 'before_core_labels'
    documents = read_jsonl(ROOT / 'data/processed/documents.jsonl')
    queries = read_jsonl(ROOT / 'data/processed/queries.jsonl')
    validate_inputs(documents, queries)
    by_q = {q['query_id']: q for q in queries}
    by_d = {d['doc_id']: d for d in documents}
    previous_q = {q['query_id']: q for q in read_jsonl(base / 'queries.jsonl')}
    assert all(q['query'] == previous_q[q['query_id']]['query'] for q in queries)
    previous_rows = csv_rows(base / 'per_query_results.csv')
    if args.rescore_saved:
        if sha(ROOT / 'data/processed/documents.jsonl') != sha(base / 'documents.jsonl'):
            raise ValueError('The corpus changed; rerun python run_eval.py instead of rescoring saved ranks')
        rows = []
        for old in previous_rows:
            q = by_q[old['query_id']]
            assert old['query'] == q['query'] and old['category'] == q['category']
            results = [SearchResult(i, 0) for i in old['top5_doc_ids'].split('|')]
            relevant = set(q['relevant_doc_ids'])
            row = {key: value for key, value in old.items() if key != 'aspect_recall_at_5'}
            row.update(recall_at_5=recall_at_k(results, relevant), reciprocal_rank=reciprocal_rank(results, relevant), first_relevant_rank=first_relevant_rank(results, relevant))
            rows.append(row)
        metrics = []
        for config in dict.fromkeys(row['config'] for row in rows):
            selected = [r for r in rows if r['config'] == config]
            metrics.append(dict(config=config, num_queries=len(selected), recall_at_5=mean(r['recall_at_5'] for r in selected), mrr=mean(r['reciprocal_rank'] for r in selected), p95_latency_ms=float(np.percentile([float(r['latency_ms']) for r in selected], 95))))
        write_csv(out / 'per_query_results.csv', rows)
        write_csv(out / 'metrics.csv', metrics)
    rows = csv_rows(out / 'per_query_results.csv')
    metrics = csv_rows(out / 'metrics.csv')
    configs = [m['config'] for m in metrics]
    assert len(rows) == 80 and len(set(configs)) == len(configs) == 4
    assert {(r['config'], r['query_id']) for r in rows} == {(c, qid) for c in configs for qid in by_q}
    for row in rows:
        q = by_q[row['query_id']]
        top = row['top5_doc_ids'].split('|')
        assert row['query'] == q['query'] and len(top) == len(set(top)) == 5 and set(top) <= by_d.keys()
        gold = set(q['relevant_doc_ids'])
        rank = next((i for i, doc_id in enumerate(top, 1) if doc_id in gold), None)
        assert abs(float(row['recall_at_5']) - len(set(top) & gold) / len(gold)) < 1e-12
        assert abs(float(row['reciprocal_rank']) - (1 / rank if rank else 0)) < 1e-12
        assert row['first_relevant_rank'] == (str(rank) if rank else '')
        assert 'aspect_recall_at_5' not in row
    for m in metrics:
        selected = [r for r in rows if r['config'] == m['config']]
        assert abs(float(m['recall_at_5']) - mean(float(r['recall_at_5']) for r in selected)) < 1e-12
        assert abs(float(m['mrr']) - mean(float(r['reciprocal_rank']) for r in selected)) < 1e-12
        assert abs(float(m['p95_latency_ms']) - float(np.percentile([float(r['latency_ms']) for r in selected], 95))) < 1e-9
    plot_metrics(out / 'metrics.csv', out / 'metrics_plot.png')
    old_by_key = {(r['config'], r['query_id']): r for r in previous_rows}
    unchanged = sum(r['top5_doc_ids'] == old_by_key[(r['config'], r['query_id'])]['top5_doc_ids'] for r in rows)
    labels = sum(len(q['relevant_doc_ids']) for q in queries)
    supplementary = sum(len(q['supplementary_doc_ids']) for q in queries)
    noise = sum(len(q['excluded_doc_ids']) for q in queries)
    ceiling = mean(min(5, len(q['relevant_doc_ids'])) / len(q['relevant_doc_ids']) for q in queries)
    best = max(metrics, key=lambda m: (float(m['mrr']), float(m['recall_at_5'])))['config']
    table = ['| config | core recall@5 | core MRR@5 | p95 ms |', '| --- | ---: | ---: | ---: |']
    table += [f"| {m['config']} | {float(m['recall_at_5']):.3f} | {float(m['mrr']):.3f} | {float(m['p95_latency_ms']):.1f} |" for m in metrics]
    method = 'Rescored archived top-5 retrieval results. Corpus and query strings are identical; original measured latency is reused, not measured again.' if args.rescore_saved else 'Validated the current result files against core-only labels. See provenance for hashes; validation alone does not establish a new timing measurement.'
    summary = ['# Core-only relevance evaluation — 2026-10-23', '', f'20 unchanged questions and {len(documents)} unchanged corpus documents. Gold labels decrease from 170 to {labels}; {supplementary} references remain supplementary and {noise} navigation/See Also blocks are excluded from gold. All sources remain in the corpus.', '', method, '', f'Rankings identical to the archived broad-label run: {unchanged}/80 config-query rows. Metric differences are label-policy differences, not retrieval/model improvements.', '', *table, '', f'`{best}` has the highest MRR@5 under the core-only policy. The label policy does not enforce a five-label cap; document recall@5 has a mean theoretical ceiling of {ceiling:.6f}. q19 and q20 retain more than five genuine direct passages.', '', 'The broad answer_aspects metric is retired for this version. Only relevant_doc_ids count toward Recall/MRR. Admin/developer alternatives remain gold when they directly answer the wording (for example, Apex Account merge and SQL non-engagement selection). Generic OAuth, metadata deployment, execution order, migration and permissions unrelated to the actual question receive no credit.', '', 'A core passage can provide a necessary answer component rather than a complete end-to-end example. q12 still lacks an exact complete Case-to-Account sample; q16 engagement tracking has limitations. These are retrieval labels, not a claim that generated answers are fully correct or executable.', '', '## Comparison with broad labels', '', '| config | previous recall@5 | core recall@5 | previous MRR | core MRR |', '| --- | ---: | ---: | ---: | ---: |']
    previous_metrics = {m['config']: m for m in csv_rows(base / 'metrics.csv')}
    for m in metrics:
        old = previous_metrics[m['config']]
        summary.append(f"| {m['config']} | {float(old['recall_at_5']):.3f} | {float(m['recall_at_5']):.3f} | {float(old['mrr']):.3f} | {float(m['mrr']):.3f} |")
    summary.extend(['', '[Explicit content-locked review](../data/raw/core_labels.json), [label changes](core_label_review.json), [answers](../docs/query_answers.md), [baseline](before_core_labels/). All 80 per-query and four aggregate scores were independently verified.', ''])
    (out / 'core_evaluation_summary.md').write_text('\n'.join(summary), encoding='utf-8')
    readme_path = ROOT / 'README.md'
    readme = readme_path.read_text(encoding='utf-8')
    readme = re.sub(r'Each query has reviewed `answer_aspects`.*?(?=\n\n)', 'Each query labels only passages that directly explain the core solution, implementation step or stated symptom. Admin/developer context remains available as `supplementary_doc_ids` but receives no evaluation credit. See [the reviewed answers](docs/query_answers.md).', readme, flags=re.S)
    start, end = readme.index('# Metrics\n'), readme.index('# If I Had One More Week\n')
    section = ['# Metrics', '', '- Core document recall@5: retrieved core-labelled passages / all core-labelled passages per query.', '- Core MRR@5: reciprocal rank of the first core-labelled passage in the returned top 5.', '- p95 latency: query-time latency; in the label-only rescore below it is reused from the archived retrieval run.', '', f'The 20 queries have {labels} core labels. All {len(documents)} PDF/HTML chunks remain searchable, including supplementary technical context. Authentication, generic deployment, navigation, broad reference catalogs and unrelated prerequisites are not gold merely because they are useful to an admin.', '', f'Core steps and direct alternatives can produce multiple labels. q19 has seven and q20 has six; the mean theoretical recall@5 ceiling is {ceiling:.6f}. No labels were selected using retrieval rank. The broader answer_aspects metric is not used in the current version.', '', '# Results and Evaluation', '', '## Core-only Labels — 2026-10-23', '', method, '', f'The saved rankings are unchanged in {unchanged}/80 config-query rows. Changes from the previous broad-label version are not model improvements. [Review and comparison](results/core_evaluation_summary.md), [gold source IDs](data/raw/core_labels.json), [question-by-question answers](docs/query_answers.md).', '', '![Retrieval metrics plot](results/metrics_plot.png)', '', *table, '', f'With MRR prioritized, `{best}` is the preferred configuration under this policy. This is a descriptive result on 20 questions, not a statistical significance claim or generated-answer evaluation.', '', '## Category Analysis', '', 'Mean core document recall@5:', '', '| category | bm25 | dense | hybrid_rrf | hybrid_rerank |', '| --- | ---: | ---: | ---: | ---: |']
    for category in dict.fromkeys(q['category'] for q in queries):
        section.append(f'| `{category}` | ' + ' | '.join(f"{mean(float(r['recall_at_5']) for r in rows if r['config'] == c and by_q[r['query_id']]['category'] == category):.3f}" for c in configs) + ' |')
    hard = {q['query_id'] for q in queries if q['difficulty'] == 'hard'}
    section.extend(['', '## Hard Queries', '', '| config | hard core recall@5 | hard core MRR@5 | complete misses |', '| --- | ---: | ---: | --- |'])
    for c in configs:
        selected = [r for r in rows if r['config'] == c and r['query_id'] in hard]
        section.append(f'| {c} | ' + ' | '.join(f"{mean(float(r[field]) for r in selected):.3f}" for field in ['recall_at_5', 'reciprocal_rank']) + ' | ' + (', '.join(r['query_id'] for r in selected if not r['first_relevant_rank']) or 'none') + ' |')
    section.extend(['', 'Some questions need multiple core passages and retain scope limitations. In particular, related-record update concepts do not constitute a complete tested Case-to-Account implementation. Technical supporting pages remain available for an admin agent, but retrieving them alone is not counted as a core answer.', '', ''])
    readme_path.write_text(readme[:start] + '\n'.join(section) + readme[end:], encoding='utf-8')
    paths = [ROOT / 'data/processed/documents.jsonl', ROOT / 'data/processed/queries.jsonl', ROOT / 'data/raw/core_labels.json', base / 'per_query_results.csv', out / 'metrics.csv', out / 'per_query_results.csv']
    provenance = {'scope': 'admin_agent_core_v1', 'review_date': '2026-10-23', 'method': method, 'corpus_unchanged': sha(ROOT / 'data/processed/documents.jsonl') == sha(base / 'documents.jsonl'), 'query_strings_unchanged': True, 'identical_ranking_rows': unchanged, 'labels': labels, 'supplementary_references': supplementary, 'excluded_navigation': noise, 'sha256': {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in paths}}
    (out / 'core_evaluation_provenance.json').write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8')
    historical = out / 'html_expansion_summary.md'
    text = historical.read_text(encoding='utf-8')
    if not text.startswith('> Historical'):
        historical.write_text('> Historical broad-label evaluation. Current core-only results: [core_evaluation_summary.md](core_evaluation_summary.md).\n\n' + text, encoding='utf-8')
    for m in metrics:
        print(f"{m['config']}: core recall@5={float(m['recall_at_5']):.3f}, MRR@5={float(m['mrr']):.3f}")
    print(f'Validated all 80 score rows; {unchanged}/80 rankings unchanged; latency reused: {args.rescore_saved}')


if __name__ == '__main__':
    main()
