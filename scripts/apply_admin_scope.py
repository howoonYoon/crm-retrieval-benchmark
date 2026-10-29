"""Curate the admin-agent benchmark from a preserved label-review baseline."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from build_corpus import admin_supplement_documents, DEFAULT_SOURCE_URLS, DEFAULT_TEXT_CACHE_DIR


def load(path):
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write(path, rows):
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def main():
    current = ROOT / 'data/processed/queries.jsonl'
    if current.exists() and any(q.get('benchmark_scope') in {'admin_agent_html_v1', 'admin_agent_core_v1'} for q in load(current)):
        raise SystemExit('A newer scope is active; use its applicator (apply_html_labels.py or apply_core_labels.py).')
    baseline = ROOT / "results/before_admin_scope"
    queries = load(baseline / "queries.jsonl")
    original = {q["query_id"]: q for q in load(baseline / "queries.jsonl")}
    documents = load(baseline / "documents.jsonl") + admin_supplement_documents(DEFAULT_SOURCE_URLS, DEFAULT_TEXT_CACHE_DIR)
    docs = {d["doc_id"]: d for d in documents}
    supplements = {}
    for d in documents:
        if d.get("curation_key"):
            supplements.setdefault(d["curation_key"], []).append(d["doc_id"])

    def passage(key):
        return supplements[key]

    def ids(qid, *indexes):
        values = original[qid]["relevant_doc_ids"]
        return [values[i] for i in indexes] if indexes else values

    # Each aspect measures retrieval evidence for an answer component or implementation route.
    # It does not prescribe executing every alternative or claim end-to-end answer correctness.
    specs = {
        "q01": [("admin_resolution", "전환 UI·duplicate rules·빈 매핑 필드의 원인을 확인한다.", ids("q01")), ("apex_conversion", "개발 경로에서는 기존 Account ID와 Database.convertLead 및 LeadConvertResult를 조사한다. 일반 Account insert의 allowSave 예시를 전환 우회책으로 단정하지 않는다.", passage("lead_conversion"))],
        "q02": [("admin_merge", "UI 병합의 권한·소유권·보존 필드를 확인한다.", ids("q02")), ("apex_merge", "개발 경로에서는 merge/Database.merge, 관련 record 재연결, 결과 오류와 보존 필드를 확인한다.", passage("account_merge"))],
        "q03": [("feature_setup", "Email-to-Case와 On-Demand Service를 활성화한다.", ids("q03", 0, 1, 2)), ("routing_integration", "routing address 검증, mail forwarding 및 실제 이메일 테스트를 확인한다. 표준 기능으로 해결할 수 있으며 custom Apex email handler가 필수인 것은 아니다.", ids("q03", 3) + ["agentforce_contact_center_5_30_2026_p0585_011"])],
        "q04": [("apex_warning_configuration", "사용자별 Send Apex Warning Emails, Author Apex 권한, 50%와 per-request 적용 범위를 함께 설명한다. 임의 임계치 또는 전체 org 한도 알림으로 확장하지 않는다.", ids("q04"))],
        "q05": [("admin_relationship_setup", "기능 활성화, 관련 목록과 Add Relationship 절차를 확인한다.", ids("q05", 0, 3)), ("relationship_model", "Account Contact Relationship 객체와 direct/indirect 관계를 이해한다. 구체적인 DML/API payload는 현재 문서 근거가 부족해 생성하지 않는다.", ids("q05", 1, 2))],
        "q06": [("quote_workflow", "여러 Quote를 만들되 Opportunity와의 sync는 한 번에 하나라는 제약을 설명한다.", ids("q06")), ("admin_quote_setup", "Quote Settings 활성화, Customize Application 권한과 Opportunity 관련 목록을 확인한다. Quote/QuoteLineItem API 구현은 현재 코퍼스의 미충족 항목이다.", passage("quote_setup"))],
        "q07": [("flow_selection", "질문의 without Apex 조건을 지켜 before-save record-triggered Flow를 선택한다.", ids("q07", 0)), ("flow_implementation", "$Record 값을 변경하고 지원 요소와 별도 Update Records 불필요 조건을 설명한다. 관련 record 갱신에는 이 방식을 적용하지 않는다.", ids("q07", 1))],
        "q08": [("template_lifecycle", "승인·active 상태·개인화 변수 제약을 확인한다.", ids("q08", 0)), ("journey_execution", "WhatsApp activity와 App Channel을 설정한다. Journey Builder Campaigns 및 WhatsApp engagement split 제약을 설명하며 근거 없는 Apex 전송 방법은 제시하지 않는다.", ids("q08", 1))],
        "q09": [("apex_dml_support", "Profile은 일반 sObject DML update 미지원임을 확인한다. Profile 메타데이터 변경은 별도 문서 검증이 필요한 경로이며 DML 우회 코드를 만들지 않는다.", ids("q09"))],
        "q10": [("omni_channel_setup", "Messaging service channel·presence·fallback queue 선행 설정을 확인한다.", ids("q10", 0)), ("availability_flow", "Check Availability for Routing과 Decision으로 분기한다. 문서 예시는 agent→queue fallback이며 queue 간 전환 전체 구현은 아니다.", ids("q10", 1))],
        "q11": [("capacity_model", "article × retained versions × translations와 edition 할당을 계산한다.", ids("q11", 0)), ("capacity_monitoring", "Storage Usage의 Knowledge/Knowledge Versions를 모니터링한다. 단순 article record 수만으로 판단하지 않는다.", ids("q11", 1))],
        "q12": [("flow_implementation", "after-save Flow에서 관련 Account를 식별하고 Update Records를 사용한다.", ids("q12", 1, 2)), ("apex_implementation", "Case after insert/update trigger에서 관련 record를 갱신한다. 정확한 Case→Account 완성 예제는 아니며 별도 bulk·recursion·권한 검증이 필요하다.", ids("q12", 0))],
        "q13": [("crm_sync_setup", "Marketing Cloud Connect와 Synchronized Data Sources의 object·field·filter·poll schedule을 설정한다.", ids("q13", 0)), ("data_pipeline", "관계·contact keys와 Query Activity의 별도 target DE를 검토한다. synchronized source를 primary sendable DE로 직접 사용하지 않는다. 실제 schema와 sendable 관계는 org별 검증 사항이다.", ids("q13", 1) + passage("sql_query_setup"))],
        "q14": [("filtered_de", "Country equals UK 조건으로 filtered DE를 만들고 refresh 동작을 설명한다.", ids("q14")), ("sql_alternative", "개발 대안은 별도 target DE에 SELECT ... FROM [source] WHERE Country = 'UK' 결과를 쓰는 SQL Query Activity다. 쿼리는 문서의 일반 절차를 적용한 예시이며 실제 필드·키·overwrite 영향을 검증해야 한다.", passage("sql_query_setup"))],
        "q15": [("ui_field_access", "해당 사용자의 FLS와 실제 layout을 확인한다.", ids("q15")), ("apex_field_access", "custom UI/Apex 경로가 있다면 object/FLS describe checks와 user/system mode를 함께 확인한다. API 67.0 전후 기본 실행 모드 차이를 문서 버전에 맞춰 해석하며 UI 원인으로 바로 확정하지 않는다.", passage("apex_permissions"))],
        "q16": [("journey_branching", "Wait와 Engagement Split을 사용하고 NOT open AND NOT click의 두 조건을 검증한다.", ids("q16")), ("sql_audience", "개발 대안으로 _Sent/_Open/_Click을 job/list/batch/subscriber 기준으로 연결해 두 미반응 조건을 검사하고 target DE를 만든다. Job 필터·규모·추적 한계를 확인한다.", ["mc_journeys_and_automations_p0102_002", "mc_journeys_and_automations_p0103_003"] + passage("sql_nonengagement"))],
        "q17": [("debug_workflow", "Flow Builder Debug에서 입력·실행 경로·rollback mode를 확인한다.", ids("q17")), ("execution_context_testing", "다른 사용자/system context 차이, delete·Wait 동작, Debug와 실제 transaction 차이를 점검하고 sandbox에서 통합 검증한다. rollback이 외부 부작용까지 모두 취소한다고 주장하지 않는다.", passage("flow_debug_limits"))],
        "q18": [("tool_selection", "import/update/export와 규모를 기준으로 Data Loader 등을 비교한다.", ids("q18")), ("automated_loading", "CSV/field mapping·성공 및 오류 로그·CLI 자동 처리 경로를 검토한다.", ["setup_p0439_013"]), ("api_permissions", "Data Loader의 object 권한·API Enabled와 hard-delete 사용 시 별도 권한을 확인한다.", ["setup_p0444_017"])],
        "q19": [("apex_bulk_path", "Apex trigger/SOQL/DML의 bulkification과 transaction limits를 확인한다.", ids("q19")), ("flow_bulk_path", "Flow interviews의 같은 요소 단위 bulkification과 transaction 실패·rollback을 확인한다. Apex만 원인으로 가정하지 않는다.", passage("flow_bulk"))],
        "q20": [("record_permissions", "object Edit와 OWD·소유권·role·sharing grants를 함께 조사한다.", ids("q20")), ("apex_execution_context", "custom Apex 접근은 sharing과 object/FLS 및 user/system mode를 구분한다. API 버전 영향을 확인하며 without sharing을 일반 권한 해결책으로 제시하지 않는다.", passage("apex_sharing") + passage("apex_permissions"))],
    }
    changes = []
    for q in queries:
        qid = q["query_id"]
        q["requester_role"] = q["user_role"]
        for key in ('user_role', 'agent_role', 'answer_constraints', 'expected_source'):
            q.pop(key, None)
        q["benchmark_scope"] = "admin_agent_v1"
        q["answer_aspects"] = [{"aspect_id": name, "description": text, "relevant_doc_ids": references} for name, text, references in specs[qid]]
        old_ids = q["relevant_doc_ids"]
        q["relevant_doc_ids"] = list(dict.fromkeys(i for a in q["answer_aspects"] for i in a["relevant_doc_ids"]))
        assert set(q["relevant_doc_ids"]) <= docs.keys(), qid
        assert set(old_ids) <= set(q["relevant_doc_ids"]), qid
        q["notes"] = "Admin-agent scope: include relevant configuration, data-model, developer and integration reasoning. " + " ".join(a["description"] for a in q["answer_aspects"])
        changes.append({"query_id": qid, "added": [i for i in q["relevant_doc_ids"] if i not in old_ids], "removed": [], "aspect_ids": [a["aspect_id"] for a in q["answer_aspects"]]})
    write(ROOT / "data/processed/documents.jsonl", documents)
    write(ROOT / "data/processed/queries.jsonl", queries)
    (ROOT / "results/admin_scope_changes.json").write_text(json.dumps({"date": "2026-10-23", "baseline": "results/before_admin_scope", "query_strings_changed": False, "added_documents": [d['doc_id'] for d in documents if d.get('curation_key')], "changes": changes}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Keep the previously reviewed answer text, then explain the widened admin scope.
    old_answers = (baseline / "query_answers.md").read_text(encoding="utf-8")
    import re
    sections = {m.group(1): m.group(0).rstrip() for m in re.finditer(r"^## (q\d{2}) .*?(?=^## q\d{2} |\Z)", old_answers, re.M | re.S)}
    ceiling = sum(min(5, len(q['relevant_doc_ids'])) / len(q['relevant_doc_ids']) for q in queries) / len(queries)
    guide = ["# Admin agent용 문제별 정답과 근거", "", "2026-10-23: 모든 질문의 답변 대상을 CRM admin/developer로 통일했다. 질문 표현과 최초 요청자 역할은 유지하며, 설정·권한·데이터 모델·관련 코드/SQL·실행 조건을 함께 검토한다. 모든 질문에 Apex가 필요한 것은 아니다.", "", "기존 답변은 아래 ‘기본 해결 경로’에 보존했다. 기존 추가/제외 판단은 2026-10-22 검토 기록이며, 현재 라벨은 각 문제 끝의 목록을 기준으로 한다. 버전이 고정된 PDF의 증거이며 최신 제품 동작 검증은 아니다.", "", f"총 {len(documents)}개 문서, {sum(len(q['relevant_doc_ids']) for q in queries)}개 라벨. 문서 recall@5 이론 상한은 {ceiling:.6f}. 보조 지표 aspect_recall@5는 답변 항목/구현 경로별 근거 검색률이며 생성 답변의 정확도나 완성도를 의미하지 않는다.", "", "미충족 근거: AccountContactRelation의 API/DML 명세, Quote/QuoteLineItem API 구현, Profile 메타데이터 수정 경로, WhatsApp REST 전송 API 등은 현재 PDF만으로 검증하지 못했다. 이 경로를 구현하는 코드는 별도 공식 레퍼런스를 확보한 후 검증해야 한다.", ""]
    url_lines = ["# Admin-agent Query Label URLs", "", "2026-10-23. Merged passage URLs open the first PDF page in the declared range.", ""]
    for q in queries:
        qid = q["query_id"]
        section = sections[qid]
        main_text = section.split("정답 문서:")[0].replace("**정답:**", "**기본 해결 경로:**")
        guide.extend([main_text, "", "**Admin/개발 관점에서 추가로 확인할 항목:**", ""])
        for aspect in q["answer_aspects"]:
            guide.append(f"- **{aspect['aspect_id']}**: {aspect['description']}")
            guide.append("  - 근거: " + ", ".join(f"`{i}`" for i in aspect['relevant_doc_ids']))
        guide.extend(["", "현재 정답 문서:", ""])
        url_lines.extend([f"## {qid}", "", q['query'], ""])
        for i in q['relevant_doc_ids']:
            d = docs[i]
            line = f"- `{i}` — {d['source_file']} PDF p{d['page_start']}–{d['page_end']}: {d['url']}"
            guide.append(line)
            url_lines.append(line)
        guide.append("")
        url_lines.append("")
    (ROOT / "docs/query_answers.md").write_text("\n".join(guide), encoding="utf-8")
    (ROOT / "data/processed/query_label_urls.md").write_text("\n".join(url_lines), encoding="utf-8")
    # Rebuild the human candidate inventory; scores are intentionally absent after re-curation.
    with (ROOT / "data/processed/label_candidates.csv").open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fields, candidates = reader.fieldnames, list(reader)
    candidates = [row for row in candidates if row['doc_id'] in docs]
    by_qid = {q['query_id']: q for q in queries}
    for row in candidates:
        row['is_labeled_relevant'] = str(row['doc_id'] in by_qid[row['query_id']]['relevant_doc_ids'])
        row['snippet'] = row['snippet'].rstrip()
    present = {(r['query_id'], r['doc_id']) for r in candidates}
    for q in queries:
        rank = max(int(r['rank']) for r in candidates if r['query_id'] == q['query_id'])
        for i in q['relevant_doc_ids']:
            if (q['query_id'], i) not in present:
                rank += 1
                d = docs[i]
                candidates.append(dict(query_id=q['query_id'], rank=rank, doc_id=i, is_labeled_relevant='True', source_file=d['source_file'], page=d['page_start'], page_end=d['page_end'], score='', matched_terms='', title=d['title'], snippet=' '.join(d['text'].split())[:220].rstrip()))
    candidates.sort(key=lambda r: (r['query_id'], int(r['rank'])))
    with (ROOT / "data/processed/label_candidates.csv").open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(candidates)
    set_lines = ["# Admin-agent Query Set", "", "All 20 queries target a CRM admin/developer agent. `requester_role` preserves the original source of the question. Query strings, categories and difficulty are unchanged.", "", "Technical evidence includes Apex when relevant, Flow configuration/runtime behavior, SQL and data-extension pipelines, permissions, limits and integration prerequisites. A developer perspective does not require Apex for every task. Known unsupported API paths are recorded in the [answer guide](query_answers.md).", "", "Each query defines `answer_aspects` with evidence IDs. aspect_recall@5 is the fraction of these evidence groups hit by top-5 retrieval, macro-averaged over queries. Groups can represent alternative implementation routes; this is evidence coverage, not answer accuracy.", "", "| id | original requester | category | difficulty | labels | evidence aspects |", "| --- | --- | --- | --- | ---: | ---: |"]
    set_lines += [f"| {q['query_id']} | {q['requester_role']} | {q['category']} | {q['difficulty']} | {len(q['relevant_doc_ids'])} | {len(q['answer_aspects'])} |" for q in queries]
    (ROOT / "docs/query_set.md").write_text("\n".join(set_lines) + "\n", encoding="utf-8")
    print(f"Admin scope: {len(documents)} documents; {sum(len(q['relevant_doc_ids']) for q in queries)} labels; {sum(len(q['answer_aspects']) for q in queries)} aspects")


if __name__ == '__main__':
    main()
