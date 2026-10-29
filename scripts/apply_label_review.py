"""Apply the documented relevance review without changing query wording.

Run after preserving the pre-review queries in results/before_label_review/.
This script updates labels and review documentation, not retrieval results.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from textwrap import shorten

ROOT = Path(__file__).resolve().parents[1]

REVISED_LABELS = {
    "q01": ["sales_core_p0096_002", "sales_core_p0095_001", "sales_core_p0103_004"],
    "q02": ["sales_core_p0218_022", "sales_core_p0220_023"],
    "q05": ["sales_core_p0280_027", "sales_core_p0280_028", "sales_core_p0277_026", "sales_core_p0287_029"],
    "q12": ["salesforce_apex_developer_guide_p0271_014", "extend_click_automate_p0031_004", "extend_click_automate_p0100_008"],
    "q13": ["engagement_audience_builder_and_contact_builder_5_30_2026_p0139_007", "engagement_audience_builder_and_contact_builder_5_30_2026_p0139_008"],
    "q15": ["salesforce_security_impl_guide_p0048_020", "salesforce_security_impl_guide_p0048_021"],
    "q16": ["mc_journeys_and_automations_p0351_041", "mc_journeys_and_automations_p0350_040"],
    "q17": ["extend_click_automate_p0238_012", "extend_click_automate_p0238_013"],
    "q19": ["salesforce_apex_developer_guide_p0290_017", "salesforce_apex_developer_guide_p0354_027", "salesforce_apex_developer_guide_p0141_003", "salesforce_apex_developer_guide_p0142_004", "salesforce_apex_developer_guide_p0353_026"],
    "q20": ["salesforce_record_access_under_the_hood_p0006_002", "salesforce_record_access_under_the_hood_p0007_003", "salesforce_security_impl_guide_p0017_002", "salesforce_record_access_under_the_hood_p0010_006", "salesforce_security_impl_guide_p0046_018", "salesforce_security_impl_guide_p0047_019", "salesforce_security_impl_guide_p0059_023"],
}

# Answer and reasoning describe the checked-in corpus, not current product advice.
ANSWERS = {
    "q01": ("Lead 전환 중 Account 중복 경고가 나면 어떻게 처리하는가?", "중복 후보와 duplicate rules를 확인하고 기존 Account를 선택한다. 경고를 무시할 수 없는 특정 오류라면 기존 Account의 빈 매핑 필드를 먼저 채우거나 해당 Lead 값을 비운 뒤 다시 전환한다.", "p95·103은 일반 중복 처리와 기존 Account 선택을, p96은 빈 매핑 필드 때문에 발생하는 특정 경고의 해결책을 설명한다. 질문이 일반 경고이므로 특정 오류 문서만 정답으로 제한하지 않았다."),
    "q02": ("중복 Account를 어떻게 병합하는가?", "Lightning에서는 View Duplicates에서 최대 세 Account와 보존할 principal/필드 값을 선택한다. Classic에서는 Accounts 탭의 Merge Accounts를 사용한다. Delete 권한, 관련 객체 Edit 권한, 관리자·소유자·상위 역할 조건을 확인한다.", "p218은 Lightning 병합 절차와 권한, p220은 Classic 절차와 권한을 설명한다. 질문에는 Lightning 제한이 없으므로 두 UI 모두 정답이다. marketing user라는 직무는 권한을 보장하지 않는다."),
    "q03": ("지원 주소로 들어온 이메일이 자동으로 Case를 생성하게 하려면?", "Email-to-Case와 On-Demand Service를 활성화하고 routing address를 등록·검증한다. 지원 메일 시스템에서 Salesforce가 생성한 email services address로 전달하도록 설정한다.", "p575는 기능 소개, p576은 설정 단계, p577은 활성화, p584는 routing address와 forwarding 절차다. 기능을 식별하는 소개와 실제 설정 절차를 모두 유효한 답변 근거로 유지했다."),
    "q04": ("Apex governor limit 사용량에 대한 경고 이메일을 설정하려면?", "관리자가 Setup → Users에서 대상 사용자를 편집하고 Send Apex Warning Emails를 켠다. Author Apex 권한이 필요하다.", "p364는 설정 절차와 함께 할당량의 50%를 넘을 때 검사 대상 per-request limits에 대해 경고한다고 설명한다. 임의 임계치나 모든 org 한도에 대한 알림으로 해석하면 안 된다."),
    "q05": ("한 Contact를 여러 Account에 연결하려면?", "Contacts to Multiple Accounts를 활성화하고 Related Contacts/Related Accounts에서 Add Relationship을 사용한다. 기본 Account는 direct, 추가 관계는 indirect로 관리한다.", "p277은 기능과 direct/indirect 관계, p280~284는 활성화·관련 목록·관계 필드, p287은 실제 관계 생성·수정 절차다. 관리자의 설정뿐 아니라 사용자의 관계 생성 방법도 정답에 추가했다."),
    "q06": ("한 Opportunity에 여러 Quote를 만들어 상품·가격 조합을 비교하려면?", "Opportunity의 Quotes 관련 목록에서 New Quote로 여러 Quote를 만들고 각 Quote의 상품·수량·할인을 조정한다. Opportunity와 동기화할 수 있는 Quote는 한 번에 하나다.", "p166은 서로 다른 조합의 Quote 생성, New Quote 절차, 여러 Quote와 단일 sync 관계를 직접 설명한다."),
    "q07": ("Apex 없이 Opportunity가 저장되기 전에 필드를 갱신하려면?", "before-save record-triggered Flow를 사용해 triggering record의 $Record 필드 값을 변경한다. 해당 변경을 저장하려고 별도 Update Records를 둘 필요는 없다.", "p36은 before-save Flow의 용도와 실행 시점, p37은 $Record와 지원 요소를 설명한다. 관련 Account 같은 다른 record를 갱신하는 용도와는 구분해야 한다."),
    "q08": ("승인된 WhatsApp 템플릿 메시지를 고객에게 보내려면?", "승인된 템플릿을 Content Builder에서 개인화한 뒤 Journey Builder에 WhatsApp Message activity를 추가하고 메시지·App Channel을 선택하여 journey를 활성화한다.", "p321은 승인 상태·개인화, p322는 전송 설정을 설명한다. p322는 WhatsApp 메시지에 Journey Builder Campaigns와 Engagement Splits를 사용할 수 없다고 한다. 질문의 campaign은 일반 마케팅 활동으로 해석한다."),
    "q09": ("Apex에서 Profile 객체를 update할 수 있는가?", "일반 sObject DML update로는 할 수 없다. Profile은 query할 수 있지만 DML 미지원 객체 목록에 포함된다.", "p169의 sObjects That Don't Support DML Operations에 Profile이 명시되어 있다. 이 근거는 DML에 관한 것이며 모든 메타데이터 변경 경로가 불가능하다는 의미는 아니다."),
    "q10": ("상담원 가용성에 따라 라우팅 경로를 바꾸려면?", "Omni-Channel Flow에서 Check Availability for Routing과 Decision으로 경로를 분기하고 대체 queue로 라우팅한다.", "p39는 Messaging용 Omni-Channel Flow 설정, p40은 특정 agent가 available이면 agent에게 보내고 offline이면 queue로 보내는 예시다. 질문의 queue 간 전환 전체를 구현하는 예시는 아니므로 기능 선택 근거로 해석한다."),
    "q11": ("Knowledge의 버전·번역을 고려해 용량을 산정하려면?", "기사 수 × 보존 버전 수 × 버전별 번역 수를 기준으로 총 article versions를 계산하고 edition별 할당과 org 전체 제한을 확인한다. Storage Usage의 Knowledge와 Knowledge Versions로 실제 사용량을 본다.", "p11은 100,000 × 5 × 5 = 2,500,000 예시와 edition별 할당을, p12는 실제 기사/버전 수 모니터링을 설명한다. 현재 제품 한도를 새로 검증한 수치는 아니다."),
    "q12": ("Case 생성·수정 시 관련 Account의 필드를 자동으로 갱신하려면?", "Case의 after insert/after update Apex trigger 또는 after-save record-triggered Flow를 사용한다. 관련 Account를 식별하고 필요한 필드 값을 설정한 뒤 갱신한다.", "Apex p271은 after trigger가 다른 record를 변경하는 용도라고 설명한다. Flow p31은 after-save Flow, p100은 Update Records를 설명한다. context variables·일반 trigger syntax와 before-save 제한 설명은 직접 구현 근거에서 제외했다. Case→Account 완성 예제 자체가 있는 것은 아니다."),
    "q13": ("Salesforce CRM 데이터를 Marketing Cloud DE와 고객 메시징에 사용하려면?", "Marketing Cloud Connect로 연결한 뒤 Contact Builder의 Synchronized Data Sources에서 object·field·filter·Poll Schedule을 설정한다. 동기화 데이터를 Data Filters/Query Activities 등으로 활용한다.", "p139~142의 _007은 동기화 설정과 생성된 DE, _008은 관계와 설정 변경을 설명한다. synchronized source를 primary sendable DE로 직접 사용할 수 없다는 제약도 있다. 주로 진행률/상태를 설명하는 _009는 제외했다."),
    "q14": ("Country가 UK인 고객만 새 Data Extension에 넣으려면?", "Email Studio에서 source DE로 Filtered Data Extension을 만들고 Country equals UK 조건을 지정해 Save & Build한다. 원본 데이터 변경 후에는 refresh가 필요하다.", "p129는 필터 생성 절차와 operator 선택, p130은 필터 기능과 refresh 절차를 설명한다. 구체적인 Country 필드 값은 질문의 예시이고 문서의 일반 필터 절차를 적용한다."),
    "q15": ("배포와 layout 추가를 마친 custom field가 Account 페이지에 안 보이면?", "해당 사용자의 permission set/profile에서 field-level security의 Read/Visible을 확인하고 실제 적용된 page layout도 확인한다.", "p48~50의 _020은 FLS와 layout 중 더 제한적인 설정이 적용됨을, _021은 field permission 설정 절차를 설명한다. _022는 앞 청크의 절차 끝부분과 암호화 필드 설명이 중심이라 제외했다. FLS가 가능한 원인이며 유일한 원인으로 확정하는 질문은 아니다."),
    "q16": ("Journey Builder에서 쿠폰 이메일을 열지도 클릭하지도 않은 고객을 선별하려면?", "이메일 tracking을 활성화하고 Wait 후 Engagement Split의 No 경로를 사용한다. open과 click을 별도로 확인한다면 두 조건을 순차 확인하여 NOT open AND NOT click을 구성한 뒤 후속 mobile activity로 연결한다.", "p350은 Engagement Split 기능, p351은 최소 1시간 Wait와 open/click 기준 및 Yes/No 경로 설정을 설명한다. 질문의 핵심은 선별이므로 일반 mobile/LINE 활동 목록과 LINE 설정 조각은 제외했다. 한 split이 두 조건을 동시에 검사한다고 문서가 명시하지 않으므로 두 조건 구성은 문서에 기초한 구현 추론이다. open 추적의 이미지 차단 등 제약도 고려한다."),
    "q17": ("입력을 바꿔 guided process를 테스트하고 실행 경로를 보되 test record를 남기지 않으려면?", "Flow Builder Debug에서 입력을 바꿔 실행하고 Debug Details로 경로를 확인한다. DB 변경을 남기지 않도록 Run flow in rollback mode를 사용한다.", "p238~244의 _012는 일반 Debug·입력·rollback 경고, _013은 screen flow 실행·Debug Details·재실행 예시다. _014의 명시적 rollback checkbox 예시는 template-triggered prompt flow이므로 screen flow의 직접 정답에서 제외했다. 화면을 닫거나 재시작하는 것만으로 기존 변경이 rollback되지는 않는다."),
    "q18": ("대량 import·기존 record update·export를 지원하는 도구를 고르려면?", "Data Loader가 요구를 충족한다. Data Import Wizard, Data Loader, dataloader.io를 규모·지원 객체·실행 방식·export 지원으로 비교한다.", "p411 비교표는 Data Loader의 insert/update/delete/export와 5,000~5,000,000 record 범위를 제시한다. Data Import Wizard에는 export가 없다. 이는 고정 문서의 비교이며 현재 모든 도구의 최신 한도를 뜻하지 않는다."),
    "q19": ("소량 Case에서는 되지만 대량 update 때 실패하는 automation을 조사·개선하려면?", "오류와 실행 경로를 먼저 확인한다. Apex 경로라면 SOQL/DML을 record 루프 안에서 반복하는지와 transaction limits를 확인하고, 전체 trigger record를 collection/set으로 처리하여 SOQL·DML 호출을 묶는다.", "p290은 잘못된 bulk trigger 패턴과 set/IN query 해법, p141~142는 bulk DML과 루프 update의 개선 예시, p353~354는 limit 초과 예외와 한도다. 질문만으로 원인이 Apex라고 확정할 수는 없다. Flow 검증 실패 등도 가능하며 현재 정답은 Apex 원인 경로를 다룬다. schedule-triggered Flow rollback 설명은 Case update의 직접 근거로 채택하지 않았다."),
    "q20": ("Account는 열리지만 일부 record에서 Edit가 없으면 어떤 접근 설정을 보는가?", "Account object의 Edit 권한과 record별 write access를 함께 확인한다. OWD, 소유권, role hierarchy, sharing rules, team/manual/programmatic grants를 조사한다.", "Record Access p6~7은 object/record 접근과 grants, p10은 Account의 read-only/read-write 예시다. Security p17은 object Edit가 있어도 OWD 때문에 편집이 제한될 수 있음을, p46~47은 역할·공유 설정, p59는 Account sharing rule과 access level을 설명한다. 유효한 설정 설명을 포함하여 라벨이 7개가 됐다. record lock이나 UI 구성 등 다른 원인을 이 질문만으로 배제할 수는 없다."),
}


def load(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> None:
    query_path = ROOT / "data/processed/queries.jsonl"
    queries = load(query_path)
    if any(q.get("benchmark_scope", "").startswith("admin_agent") for q in queries):
        raise SystemExit("Historical review script: admin_agent_v1 is active. Use scripts/apply_admin_scope.py instead.")
    original = {q["query_id"]: q for q in load(ROOT / "results/before_label_review/queries.jsonl")}
    documents = {d["doc_id"]: d for d in load(ROOT / "data/processed/documents.jsonl")}
    changes = []
    for q in queries:
        for key in ('user_role', 'agent_role', 'answer_constraints', 'expected_source'):
            q.pop(key, None)
        qid = q["query_id"]
        assert q["query"] == original[qid]["query"], qid
        if qid in REVISED_LABELS:
            q["relevant_doc_ids"] = REVISED_LABELS[qid]
        ids = q["relevant_doc_ids"]
        assert ids and len(ids) == len(set(ids)) and set(ids) <= documents.keys(), qid
        old = original[qid]["relevant_doc_ids"]
        changes.append({"query_id": qid, "added": [i for i in ids if i not in old], "removed": [i for i in old if i not in ids]})
    by_id = {q["query_id"]: q for q in queries}
    by_id["q12"]["notes"] = "Hard natural-language task. Relevant passages explain after triggers, after-save record-triggered Flow, and record updates; general trigger context and before-save limitations are not labelled as direct answers."
    by_id["q16"]["notes"] = "Hard feature discovery. Labels target identifying email non-engagement; generic mobile activity lists and LINE setup fragments are excluded. Neither opened nor clicked requires both negative conditions; tracking has limitations."
    by_id["q19"]["notes"] = "Hard bulk-failure symptom. Labels cover the Apex bulkification/governor-limit investigation path; the wording alone does not establish Apex as the only possible cause."
    by_id["q20"]["notes"] = "Hard access symptom. Labels cover object permissions and record-level sharing/write access. Other causes such as locking remain possible. Seven relevant documents make the maximum document recall@5 equal to 5/7."
    query_path.write_text("".join(json.dumps(q, ensure_ascii=False) + "\n" for q in queries), encoding="utf-8")
    (ROOT / "results/label_review_changes.json").write_text(json.dumps({"review_date": "2026-10-22", "policy": "Include passages that explain a core answer, configuration step, or diagnostic setting. Exclude generic context, unrelated workflow steps and fragments whose useful content is already in the preceding chunk. Query wording, corpus, categories and difficulty are unchanged. Relevance is not exhaustive; see per-query scope limitations.", "changes": changes}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    explanation = ["# 문제별 정답과 근거", "", "검토일: 2026-10-22. 고정 코퍼스의 근거를 기준으로 정답 라벨을 수정했다. 최신 Salesforce 문서를 새로 확인한 결과는 아니다.", "", "기준: 핵심 기능, 실제 설정 절차 또는 진단할 접근 설정을 설명하는 청크를 포함했다. 단순 주변 맥락·다른 유형의 예시·무관한 설정 조각은 제외했다. 여러 청크는 대체 근거 또는 답의 일부이며, 모든 청크를 읽어야만 답할 수 있다는 뜻은 아니다.", "", "질문 원문은 변경하지 않았다. q10의 라우팅 범위, q16의 복합 조건, q19의 Apex 가정 등은 아래 설명의 적용 한계를 참고한다. 정답 후보에 대한 검토는 완전한 전수 relevance annotation을 보장하지 않는다.", "", "q20은 정답 7개이므로 document-level recall@5의 최대가 5/7이다. 전체 20문항의 이론적 평균 recall@5 상한은 0.985714이며, MRR 상한은 1이다.", ""]
    urls = ["# Query Label URLs", "", "Labels reviewed on 2026-10-22. Page ranges are PDF pages; a merged chunk URL opens the range start.", ""]
    for q, change in zip(queries, changes):
        qid = q["query_id"]
        question, answer, reason = ANSWERS[qid]
        explanation.extend([f"## {qid} — {question}", "", f"**원문:** {q['query']}", "", f"**정답:** {answer}", "", f"**근거와 한계:** {reason}", "", "정답 문서:", ""])
        urls.extend([f"## {qid} - {q['category']}", "", f"Query: {q['query']}", ""])
        for doc_id in q["relevant_doc_ids"]:
            d = documents[doc_id]
            pages = str(d["page_start"]) if d["page_start"] == d["page_end"] else f"{d['page_start']}–{d['page_end']}"
            line = f"- `{doc_id}` — {d['source_file']} PDF p{pages}: {d['url']}"
            explanation.append(line)
            urls.append(line)
        explanation.extend(["", "추가: " + (", ".join(f"`{x}`" for x in change["added"]) or "없음"), "", "제외: " + (", ".join(f"`{x}`" for x in change["removed"]) or "없음"), ""])
        urls.append("")
    (ROOT / "docs/query_answers.md").write_text("\n".join(explanation), encoding="utf-8")
    (ROOT / "data/processed/query_label_urls.md").write_text("\n".join(urls), encoding="utf-8")
    candidates_path = ROOT / "data/processed/label_candidates.csv"
    with candidates_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        candidates = list(reader)
    for row in candidates:
        row["is_labeled_relevant"] = str(row["doc_id"] in by_id[row["query_id"]]["relevant_doc_ids"])
    present = {(row["query_id"], row["doc_id"]) for row in candidates}
    for q in queries:
        qid = q["query_id"]
        rank = max(int(row["rank"]) for row in candidates if row["query_id"] == qid)
        for doc_id in q["relevant_doc_ids"]:
            if (qid, doc_id) in present:
                continue
            rank += 1
            d = documents[doc_id]
            # Blank score: manually reviewed addition, not a new lexical scoring run.
            candidates.append({"query_id": qid, "rank": rank, "doc_id": doc_id, "is_labeled_relevant": "True", "source_file": d["source_file"], "page": d["page_start"], "page_end": d["page_end"], "score": "", "matched_terms": "", "title": d["title"], "snippet": shorten(d["text"], width=220, placeholder="...")})
    candidates.sort(key=lambda row: (row["query_id"], int(row["rank"])))
    with candidates_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(candidates)
    query_set = ROOT / "docs/query_set.md"
    lines = query_set.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.startswith("| q"):
            cells = line.split("|")
            qid = cells[1].strip()
            cells[3] = f" {len(by_id[qid]['relevant_doc_ids'])} "
            if qid == "q16":
                cells[4] = " Identify email non-engagement before a mobile follow-up. "
            lines[index] = "|".join(cells)
    note = "Labels were reviewed on 2026-10-22; see [answers and evidence](query_answers.md). q20 has seven relevant documents, so its maximum document-level recall@5 is 5/7. Query wording is unchanged."
    if note not in lines:
        lines.extend(["", note])
    query_set.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Updated {len(queries)} queries; {sum(len(q['relevant_doc_ids']) for q in queries)} labels")
    print(f"Added {sum(len(c['added']) for c in changes)}; removed {sum(len(c['removed']) for c in changes)}")


if __name__ == "__main__":
    main()
