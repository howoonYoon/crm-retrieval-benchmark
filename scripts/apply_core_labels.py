"""Apply an explicit, content-locked core-answer review without changing retrieval inputs."""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from build_html_corpus import read_jsonl, write_jsonl
from evaluate import validate_inputs

RATIONALES = {
    'q01': '중복 경고의 발생 조건, 기존 Account·Lead 값과 매핑·중복 규칙을 읽기 전용으로 확인하는 근거다. 문서의 전환·필드 수정 예시는 고객 데이터 변경 권한을 뜻하지 않는다.',
    'q02': 'UI 및 Apex의 실제 Account 병합 절차는 직접 답변이므로 함께 유지한다.',
    'q03': 'Case 자동 생성에 필요한 Email-to-Case 활성화와 주소 검증·forwarding 설정을 유지한다. 제한 사항 위주의 소개와 발신 주소 설정은 보조 자료다.',
    'q04': '사용자의 Send Apex Warning Emails 설정, 권한과 적용 임계치를 직접 설명한다.',
    'q05': '기능 활성화, 관계 생성과 AccountContactRelation의 실제 사용을 유지한다. 지원 호출 목록이나 필드 목록만 있는 청크는 제외한다.',
    'q06': '한 Opportunity에 여러 Quote를 만들고 상품·가격 조합을 비교하는 절차가 핵심이다. Quote 활성화와 개별 API 필드 명세는 보조 자료다.',
    'q07': 'Apex 없이 before-save Flow를 선택하고 $Record 값을 갱신하는 핵심 구현을 유지한다.',
    'q08': '승인 템플릿 개인화와 Journey Builder 전송 설정이 핵심이다. OAuth와 전송 이벤트는 별도 개발 참고이며 정답으로 채점하지 않는다.',
    'q09': 'Apex DML 미지원 목록의 Profile이 직접 답변이다. 일반 Metadata API 배포 방법은 이 질문의 정답이 아니다.',
    'q10': '가용성 확인, queue 선택, Decision과 Route Work 분기를 직접 설명하는 부분을 유지한다. migration 및 skills 전용 설정은 제외한다.',
    'q11': '기사·보존 버전·번역 수로 용량을 추정하는 계산이 핵심이다. 실제 사용량 모니터링 절차만으로는 이 질문에 직접 답하지 않는다.',
    'q12': 'after trigger/after-save Flow 선택과 관련 record를 찾아 갱신하는 Update Records 구현은 핵심이다. 실행 순서는 보조 근거다. 정확한 Case→Account 완성 예제라는 주장은 하지 않는다.',
    'q13': 'CRM 데이터 동기화와 생성되는 DE 및 사용 제약을 설명하는 Synchronized Data Sources 설정을 유지한다. 일반 SQL 설정과 동기화 관계 관리 세부 사항은 제외한다.',
    'q14': '조건으로 새 filtered DE를 만드는 절차가 핵심이다. refresh 절차와 일반 SQL Query Activity 설정은 정답에서 제외한다.',
    'q15': 'FLS, 실제 field visibility, hidden field sections 및 page assignment처럼 필드가 보이지 않는 원인을 직접 설명하는 부분을 유지한다. custom Apex라는 추가 가정이 필요한 보안 문서는 보조 자료다.',
    'q16': 'Engagement Split 설정과 NOT open AND NOT click을 명시한 SQL은 직접 답변이다. 일반 활동 목록과 SQL 대상 DE 소개만 있는 청크는 제외한다.',
    'q17': '입력·실행 경로 확인과 rollback을 설명하는 Flow Builder Debug 및 screen flow 예시를 유지한다. 일반 sandbox 통합 테스트 주의 사항은 보조 자료다.',
    'q18': '대량 처리·update·export 요구를 충족하는 도구 비교와 Data Loader 기능이 핵심이다. import 권한은 도구 선택에 대한 직접 답변이 아니다.',
    'q19': '질문이 조사와 재설계를 함께 요구하므로 bulk SOQL/DML·Flow 처리와 실제 trace 설정·limit 로그 해석을 유지한다. 일반 실행 순서와 원인 연결이 없는 한도 표는 제외한다.',
    'q20': 'object Edit와 record sharing, read/write grant, approval lock, 실제 record action 표시 위치처럼 증상의 원인을 직접 설명하는 부분을 유지한다. Apex 실행 모드와 일반 역할 생성 절차는 제외한다.',
}

ANSWER_OVERRIDES = {
    'q01': '기존 Account와 중복 후보 Account, Lead의 현재 필드값 및 Lead→Account 매핑·matching/duplicate rules를 읽기 전용으로 확인한다. 특히 기존 Account의 매핑 필드가 비어 있고, 그 필드에 들어갈 Lead 값이 다른 Account와 일치하는지 확인해 경고 원인을 설명한다. Account의 빈 필드를 채우거나 Lead 값을 비우지 않는다. 레코드 수정·병합, 새 Account 생성이나 전환 재시도도 실행하지 않는다.',
    'q14': 'Email Studio에서 source DE로 Filtered Data Extension을 만들고 Country equals UK 조건을 지정해 Save & Build한다.',
    'q15': '해당 사용자의 FLS Read/Visible, Dynamic Forms의 field/section visibility 및 실제 App·Record Type·Profile별 Lightning page assignment를 확인한다.',
    'q20': 'Account object의 Edit와 record별 write access를 확인하고 OWD·sharing grants를 조사한다. 승인 record lock과 page layout의 실제 Edit action 표시도 원인 후보로 확인한다.',
}


def main():
    baseline = ROOT / 'results/before_core_labels'
    old = read_jsonl(baseline / 'queries.jsonl')
    docs = {d['doc_id']: d for d in read_jsonl(ROOT / 'data/processed/documents.jsonl')}
    plan = json.loads((ROOT / 'data/raw/core_labels.json').read_text(encoding='utf-8'))
    by_plan = {item['query_id']: item for item in plan['queries']}
    if len(by_plan) != len(plan['queries']) or set(by_plan) != {q['query_id'] for q in old}:
        raise ValueError('Core review must cover every query exactly once')
    queries, changes = [], []
    for prior in old:
        q = {key: value for key, value in prior.items()
             if key not in {'user_role', 'agent_role', 'answer_constraints', 'expected_source'}}
        qid = q['query_id']
        item = by_plan[qid]
        if hashlib.sha256(q['query'].encode()).hexdigest() != item['query_sha256']:
            raise ValueError(f'Question changed; review the core labels again: {qid}')
        labels = []
        for reference in item['core_labels']:
            d = docs[reference['doc_id']]
            if hashlib.sha256(d['text'].encode()).hexdigest() != reference['text_sha256']:
                raise ValueError(f'Source changed; review the core label again: {d["doc_id"]}')
            labels.append(d['doc_id'])
        removed = [i for i in prior['relevant_doc_ids'] if i not in labels]
        noise = [i for i in removed if docs[i]['text'].lstrip().startswith('You are here:') or docs[i].get('section', '').endswith('See Also')]
        q['relevant_doc_ids'] = labels
        q['core_label_text_sha256'] = {r['doc_id']: r['text_sha256'] for r in item['core_labels']}
        q['supplementary_doc_ids'] = [i for i in removed if i not in noise]
        q['excluded_doc_ids'] = noise
        # Broad admin evidence groups are archived in the baseline, not evaluated as gold.
        q.pop('answer_aspects', None)
        q['benchmark_scope'] = plan['scope']
        q['relevance_policy'] = 'core_direct_answer_only'
        q['notes'] = RATIONALES[qid]
        changes.append({'query_id': qid, 'rationale': RATIONALES[qid], 'old_labels': prior['relevant_doc_ids'], 'core_labels': labels, 'removed_labels': removed, 'supplementary_doc_ids': q['supplementary_doc_ids'], 'excluded_doc_ids': noise})
        queries.append(q)
    validate_inputs(list(docs.values()), queries)
    write_jsonl(ROOT / 'data/processed/queries.jsonl', queries)
    (ROOT / 'results/core_label_review.json').write_text(json.dumps({'scope': plan['scope'], 'policy': plan['policy'], 'baseline': 'results/before_core_labels', 'changes': changes}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with (ROOT / 'data/processed/label_candidates.csv').open(encoding='utf-8', newline='') as file:
        reader = csv.DictReader(file)
        fields, candidates = reader.fieldnames, list(reader)
    by_query = {q['query_id']: q for q in queries}
    for row in candidates:
        row['is_labeled_relevant'] = str(row['doc_id'] in by_query[row['query_id']]['relevant_doc_ids'])
    with (ROOT / 'data/processed/label_candidates.csv').open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(candidates)

    prior_guide = (baseline / 'query_answers.md').read_text(encoding='utf-8')
    sections = {m.group(1): m.group(0).split('**현재 admin/개발 답변 항목')[0].strip() for m in re.finditer(r'^## (q\d{2}) .*?(?=^## q\d{2} |\Z)', prior_guide, re.M | re.S)}
    guide = ['# 핵심 정답과 직접 근거', '', '모든 문제는 admin/developer agent의 관점으로 검토한다. 그러나 정답은 질문의 핵심 해결 방법·구현 단계·증상 원인을 직접 설명하는 청크만 포함한다. 개발 대안도 직접 답하면 유지한다.', '', '질문과 코퍼스는 변경하지 않았다. 일반 인증·배포·실행 순서·migration·참고 링크는 필요에 따라 설명에 활용할 수 있지만 관련 있다는 이유만으로 정답으로 채점하지 않는다. 모든 핵심 단계를 단일 청크가 완결한다는 의미는 아니며, 여러 직접 근거를 조합해야 하는 질문도 있다.', '', '현재 20개 질문, 핵심 라벨 60개다. 보조 문서는 supplementary_doc_ids, 탐색/참고 링크 블록은 excluded_doc_ids로 분리했다. 두 필드는 Recall/MRR 계산에 사용하지 않는다. 광범위한 answer_aspects 지표는 현재 평가에서 제거하고 이전 버전에 보존했다.', '']
    urls = ['# Core answer source URLs', '', 'Only relevant_doc_ids below count as gold. Supplementary context remains in the corpus.', '']
    for q in queries:
        qid = q['query_id']
        section = sections[qid]
        # Retain the question and existing answer, replacing stale broad relevance commentary.
        section = section.split('**근거와 한계:**')[0].strip().replace('**기본 해결 경로:**', '**핵심 정답:**')
        if qid in ANSWER_OVERRIDES:
            section = re.sub(r'\*\*핵심 정답:\*\*.*', '**핵심 정답:** ' + ANSWER_OVERRIDES[qid], section)
        guide.extend([section, '', '**핵심 판정 근거:** ' + RATIONALES[qid], '', '정답 문서:', ''])
        urls.extend([f'## {qid}', '', q['query'], ''])
        for i in q['relevant_doc_ids']:
            d = docs[i]
            context = d.get('section') or f"PDF p{d['page_start']}–{d['page_end']}"
            line = f"- `{i}` — {context}: {d['url']}"
            guide.append(line)
            urls.append(line)
        guide.extend(['', f"보조 참고: {len(q['supplementary_doc_ids'])}개. 탐색/See Also 블록 제외: {len(q['excluded_doc_ids'])}개. 전체 변경 내역은 `results/core_label_review.json`을 참고한다.", ''])
        urls.append('')
    (ROOT / 'docs/query_answers.md').write_text('\n'.join(guide), encoding='utf-8')
    (ROOT / 'data/processed/query_label_urls.md').write_text('\n'.join(urls), encoding='utf-8')
    lines = ['# Core-answer Query Set', '', 'All 20 queries retain the CRM admin/developer perspective and their original wording, requester roles, category and difficulty. Only direct core-answer passages are gold. Useful prerequisites and implementation context are stored separately and receive no Recall/MRR credit.', '', '`relevant_doc_ids`: scored core answers. `supplementary_doc_ids`: non-gold context. `excluded_doc_ids`: navigation or See Also blocks formerly labelled relevant. Broad `answer_aspects` are archived in the previous version; current evaluation reports document recall@5 and MRR@5 only.', '', 'Selection is independent of retrieval rank and has no artificial five-document cap. q19 and q20 can have more than five valid core passages; recall@5 still has a ceiling. See [answers](query_answers.md) and [the explicit review](../data/raw/core_labels.json).', '', '| id | requester | category | difficulty | core labels | non-gold context |', '| --- | --- | --- | --- | ---: | ---: |']
    lines += [f"| {q['query_id']} | {q['requester_role']} | {q['category']} | {q['difficulty']} | {len(q['relevant_doc_ids'])} | {len(q['supplementary_doc_ids'])} |" for q in queries]
    (ROOT / 'docs/query_set.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f"Core labels: {sum(len(q['relevant_doc_ids']) for q in queries)}; supplementary: {sum(len(q['supplementary_doc_ids']) for q in queries)}; excluded navigation: {sum(len(q['excluded_doc_ids']) for q in queries)}")


if __name__ == '__main__':
    main()
