"""Apply reviewed section predicates; URL query hints alone never establish relevance."""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from build_html_corpus import read_jsonl, write_jsonl
from evaluate import validate_inputs


def main():
    if any(q.get('benchmark_scope') == 'admin_agent_core_v1' for q in read_jsonl(ROOT / 'data/processed/queries.jsonl')):
        raise SystemExit('Core-only labels are active. Use scripts/apply_core_labels.py; broad HTML rules are historical.')
    baseline = ROOT / 'results/before_html_sources'
    queries = read_jsonl(baseline / 'queries.jsonl')
    by_id = {q['query_id']: q for q in queries}
    documents = read_jsonl(ROOT / 'data/processed/documents.jsonl')
    docs = {d['doc_id']: d for d in documents}
    html = [d for d in documents if d.get('document_type') == 'html']
    rules = json.loads((ROOT / 'data/raw/html_label_rules.json').read_text(encoding='utf-8'))
    selected = []
    for rule in rules:
        matches = [d for d in html if rule['url_contains'] in d['url'] and re.search(rule.get('section_regex', '.*'), d['section'], re.I) and re.search(rule.get('text_regex', '.*'), d['text'], re.I)]
        if not matches:
            raise ValueError(f'No reviewed section matched rule: {rule}')
        q = by_id[rule['query_id']]
        aspect = next((a for a in q['answer_aspects'] if a['aspect_id'] == rule['aspect_id']), None)
        if aspect is None:
            aspect = {'aspect_id': rule['aspect_id'], 'description': rule['description'], 'relevant_doc_ids': []}
            q['answer_aspects'].append(aspect)
        for d in matches:
            if d['doc_id'] not in aspect['relevant_doc_ids']:
                aspect['relevant_doc_ids'].append(d['doc_id'])
            selected.append({'query_id': q['query_id'], 'aspect_id': aspect['aspect_id'], 'doc_id': d['doc_id'], 'url': d['url'], 'section': d['section'], 'content_sha256': d['content_sha256']})
    updates = {
        ('q05', 'relationship_model'): 'Account Contact Relationship의 direct/indirect 구조를 확인한다. 구체적인 지원 호출·필드 속성은 새 Object/Field Reference의 object_api 항목을 참조한다.',
        ('q06', 'admin_quote_setup'): 'Quote Settings 활성화, Customize Application 권한과 Opportunity 관련 목록을 확인한다. Quote/QuoteLineItem API 조건은 quote_api 근거를 함께 참조한다.',
        ('q09', 'apex_dml_support'): 'Profile은 일반 sObject DML update 미지원이다. Metadata API 타입·배포와 구분하며 Apex native Metadata API가 같은 변경을 지원한다고 추론하지 않는다.',
        ('q10', 'availability_flow'): 'Check Availability for Routing의 online reps·backlog·wait time 결과로 Decision과 Route Work를 구성한다. online이라는 값이 추가 작업을 받을 여유까지 보장하지는 않는다.',
    }
    for q in queries:
        for key in ('user_role', 'agent_role', 'answer_constraints', 'expected_source'):
            q.pop(key, None)
        q['benchmark_scope'] = 'admin_agent_html_v1'
        for a in q['answer_aspects']:
            if (q['query_id'], a['aspect_id']) in updates:
                a['description'] = updates[q['query_id'], a['aspect_id']]
        q['relevant_doc_ids'] = list(dict.fromkeys(i for a in q['answer_aspects'] for i in a['relevant_doc_ids']))
        q['notes'] = 'Admin-agent PDF + HTML evidence: ' + ' '.join(a['description'] for a in q['answer_aspects'])
    validate_inputs(documents, queries)
    write_jsonl(ROOT / 'data/processed/queries.jsonl', queries)
    report = {'scope': 'admin_agent_html_v1', 'baseline': 'results/before_html_sources', 'rules': 'data/raw/html_label_rules.json', 'reviewed_additions': selected, 'excluded_as_q12_answer': {'url_id': '000387888', 'reason': 'Updates Case.AccountId from the related Contact; does not update a field on the related Account record.'}}
    (ROOT / 'results/html_label_review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    old_guide = (baseline / 'query_answers.md').read_text(encoding='utf-8')
    sections = {m.group(1): m.group(0).split('**Admin/개발 관점')[0].rstrip() for m in re.finditer(r'^## (q\d{2}) .*?(?=^## q\d{2} |\Z)', old_guide, re.M | re.S)}
    guide = ['# Admin agent용 문제별 정답과 PDF·HTML 근거', '', '2026-10-23: 모든 질문의 admin/developer 관점을 유지하며 공식 HTML 문서를 추가했다. 기본 해결 경로는 기존 PDF 검토 내용이며 현재 정답 ID는 아래 각 항목의 목록이다. URL 후보만으로 라벨링하지 않고 검토한 section/text 조건을 적용했다.', '', '수집 범위: 제공 링크 25개 중 24개 본문 확보. OTT API root는 공식 schema URL이 404라 제외했다. 인증·이벤트 문서만으로 발송 payload를 검증했다고 주장하지 않는다. PDF와 HTML은 문서/API 버전이 다를 수 있으므로 chunk의 source_version을 함께 확인한다.', '', 'Case 연결 변경 예제(000387888)는 수집했지만 q12의 Account 필드 갱신과 방향이 달라 정답으로 지정하지 않았다. 생성 답변 정확도는 이 검색 벤치마크로 검증되지 않는다.', '']
    urls = ['# Current PDF and HTML label sources', '', '2026-10-23 — admin_agent_html_v1', '']
    for q in queries:
        guide.extend([sections[q['query_id']], '', '**현재 admin/개발 답변 항목과 근거:**', ''])
        for a in q['answer_aspects']:
            guide.extend([f"- **{a['aspect_id']}**: {a['description']}", '  - ' + ', '.join(f'`{i}`' for i in a['relevant_doc_ids'])])
        guide.extend(['', '현재 정답 문서:', ''])
        urls.extend([f"## {q['query_id']}", '', q['query'], ''])
        for i in q['relevant_doc_ids']:
            d = docs[i]
            context = d.get('section') or f"PDF p{d['page_start']}–{d['page_end']}"
            line = f"- `{i}` — {d['title']} / {context}: {d['url']}"
            guide.append(line)
            urls.append(line)
        guide.append('')
        urls.append('')
    (ROOT / 'docs/query_answers.md').write_text('\n'.join(guide), encoding='utf-8')
    (ROOT / 'data/processed/query_label_urls.md').write_text('\n'.join(urls), encoding='utf-8')
    with (ROOT / 'data/processed/label_candidates.csv').open(encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        fields, candidates = reader.fieldnames, list(reader)
    present = {(r['query_id'], r['doc_id']) for r in candidates}
    for q in queries:
        rank = max(int(r['rank']) for r in candidates if r['query_id'] == q['query_id'])
        for i in q['relevant_doc_ids']:
            if (q['query_id'], i) not in present:
                rank += 1
                d = docs[i]
                candidates.append(dict(query_id=q['query_id'], rank=rank, doc_id=i, is_labeled_relevant='True', source_file=d['source_file'], page=d.get('page_start', ''), page_end=d.get('page_end', ''), score='', matched_terms='', title=d['title'], snippet=' '.join(d['text'].split())[:220].rstrip()))
    candidates.sort(key=lambda r: (r['query_id'], int(r['rank'])))
    with (ROOT / 'data/processed/label_candidates.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(candidates)
    path = ROOT / 'docs/query_set.md'
    lines = path.read_text(encoding='utf-8').splitlines()
    for index, line in enumerate(lines):
        if line.startswith('| q'):
            cells = line.split('|')
            q = by_id[cells[1].strip()]
            cells[5], cells[6] = f" {len(q['relevant_doc_ids'])} ", f" {len(q['answer_aspects'])} "
            lines[index] = '|'.join(cells)
    note = 'Current scope: admin_agent_html_v1. Sources include the existing PDF corpus and verified official HTML bodies; see docs/html_ingestion.md for acquisition and exclusion details.'
    if note not in lines:
        lines.extend(['', note])
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f"Reviewed {len(selected)} HTML relevance assignments; {sum(len(q['relevant_doc_ids']) for q in queries)} total labels; {sum(len(q['answer_aspects']) for q in queries)} aspects")


if __name__ == '__main__':
    main()
