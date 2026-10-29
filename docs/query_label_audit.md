# Query 정답 라벨 재검토

> 수정 전 라벨 43개에 대한 검토 기록이다. 이후 사용자 요청에 따라 라벨을 50개로 수정했다. 현재 정답·근거는 [query_answers.md](query_answers.md), 변경 내역은 [label_review_changes.json](../results/label_review_changes.json), 수정 전 데이터는 [before_label_review](../results/before_label_review/)를 참고한다. 아래의 “변경하지 않았다”는 최초 검토 시점의 상태를 뜻한다.

검토일: 2026-10-22. 대상: `data/processed/queries.jsonl`의 20개 질문과 43개 정답 라벨.

## 검토 범위와 기준

- 현재 벤치마크의 고정 코퍼스 `documents.jsonl`을 기준으로 모든 정답 청크의 전체 텍스트를 읽었다.
- 정답 텍스트 43개 모두를 `data/raw/pdf_text/*.jsonl`의 해당 PDF 페이지 범위와 토큰 단위로 대조했다. 43/43 일치했다. PDF를 새로 다운로드하거나 최신 Salesforce 동작을 확인한 검토는 아니다.
- 문서 ID 중복, 질문 ID 중복, 질문 내 정답 ID 중복, 존재하지 않는 정답 ID는 모두 0개였다.
- 질문의 핵심을 설명하는 직접 근거와 구현에 도움이 되는 보조 근거를 구분했다. 같은 섹션에 있다는 이유만으로 직접 정답이라고 판단하지 않았다.
- 누락 후보는 코퍼스의 제목·본문 검색과 관련 문서 전체 텍스트 확인으로 조사했다. 모든 비정답 청크에 대해 별도 판정한 전수 qrels는 아니므로 후보 목록의 완전성을 보장하지 않는다.
- 기존 `queries.jsonl`, 평가 결과, README 수치는 변경하지 않았다. 아래 변경안은 검토 제안이다.

## 결론

정답의 큰 주제는 대체로 맞지만, 현재 라벨을 그대로 완전한 정답 집합으로 보기는 어렵다. **빠진 정답 때문에 발생하는 오답 판정**과 **주변 청크까지 정답으로 세는 문제**가 함께 있다. 특히 q02, q05, q12, q13, q16, q17, q19, q20은 정답 집합이나 질문 범위를 다듬어야 한다. q01도 질문은 일반적인 중복 경고인데 라벨은 특정 전환 오류에 집중되어 있다.

## 질문별 판정

| 질문 | 의도에 맞는 답 | 현재 라벨 판정 및 조치 |
| --- | --- | --- |
| q01 | 중복 후보·중복 규칙을 확인하고 기존 Account를 선택한다. 무시할 수 없는 경고라면 매핑된 빈 Account 필드 또는 Lead 값을 조정한다. | `sales_core_p0096_002`는 맞지만 특정 오류 조건을 설명한다. 현재 넓은 질문에는 `sales_core_p0095_001`, `sales_core_p0103_004`도 관련 있다. 질문에 경고를 무시할 수 없다는 조건을 넣거나 정답을 넓힌다. |
| q02 | Account 중복 병합. 권한과 소유권/역할 계층 조건을 확인한다. | Lightning 라벨은 맞다. 질문은 UI를 지정하지 않으므로 Classic 문서 `sales_core_p0220_023`도 정답이다. `marketing_user`라는 직무만으로 병합 권한이 생기는 것은 아니다. |
| q03 | Email-to-Case와 On-Demand Service를 켜고 routing address를 검증한 뒤 생성된 email services address로 전달한다. | 4개 라벨 모두 관련 있다. p575는 대부분 제한 사항이고 끝에 기능 소개가 있다. p576·577·584가 설정의 핵심이다. p575를 필수 정답으로 셀지는 직접/보조 근거 기준에 달렸다. |
| q04 | 사용자 설정의 Send Apex Warning Emails. | 맞다. 라벨에는 50% 초과 시 알림, Author Apex 권한, per-request 한정이라는 조건이 있다. 모든 한도에 대한 임의 임계치 경고 기능으로 설명하면 안 된다. |
| q05 | Contacts to Multiple Accounts와 Account Contact Relationship, Related Accounts/Contacts에서 Add Relationship. | 현재 2개 라벨은 맞다. 실제 관계 생성 절차인 `sales_core_p0287_029`가 빠져 있다. |
| q06 | Opportunity의 Quotes 관련 목록에서 여러 Quote를 생성한다. 동기화는 한 번에 하나만 가능하다. | 맞다. `sales_core_p0166_020`에 생성 절차와 여러 Quote 사용 설명이 함께 있다. |
| q07 | before-save record-triggered Flow에서 triggering record의 값을 변경한다. | 맞다. p36은 기능 선택, p37은 `$Record` 값 변경과 별도 Update Records 불필요 설명이다. |
| q08 | 승인된 WhatsApp 템플릿을 Content Builder에서 개인화하고 Journey Builder WhatsApp Message activity로 전송한다. | 맞다. 다만 문서 p322는 WhatsApp 메시지에 Journey Builder Campaigns와 Engagement Splits를 사용할 수 없다고 명시한다. 질문의 campaign은 일반적인 마케팅 활동으로 해석해야 하며 해당 Salesforce 기능 사용으로 해석하면 충돌한다. |
| q09 | Profile은 일반 sObject DML update를 지원하지 않는다. | 맞다. `salesforce_apex_developer_guide_p0169_008`의 DML 미지원 목록에 Profile이 있다. Profile 메타데이터 변경의 모든 API 경로까지 불가능하다는 뜻으로 확장하면 안 된다. |
| q10 | Omni-Channel Flow의 Check Availability for Routing과 Decision으로 경로를 분기한다. | p39·40은 관련 있다. p40의 정확한 예시는 특정 agent가 오프라인이면 queue로 보내는 경우다. 질문의 queue 간 대체 라우팅에 대한 완전한 설정 예시는 아니다. Messaging 범위 및 agent→queue fallback으로 질문을 구체화하면 더 정확하다. |
| q11 | articles × retained versions × translations를 고려하고 edition 할당과 실제 Storage Usage를 확인한다. | 맞다. p11은 계산과 할당, p12는 할당 및 Knowledge/Knowledge Versions 모니터링을 설명한다. |
| q12 | Case insert/update 후 관련 Account를 갱신하는 Apex trigger 또는 after-save record-triggered Flow. | 방향은 맞지만 5개 라벨의 직접성이 다르다. after-save Flow를 명시한 `extend_click_automate_p0031_004`가 누락되어 있다. 아래 상세 검토 참조. |
| q13 | Marketing Cloud Connect와 Contact Builder Synchronized Data Sources로 CRM 데이터를 동기화하고, Data Filters/Query Activities 등을 활용한다. | `_p0139_007`이 핵심이다. `_008`은 관계·동기화 설정의 보조 근거, `_009`는 주로 동기화 상태/진행률 설명이라 직접성이 낮다. 동기화된 DE를 primary sendable DE로 직접 사용할 수 없다는 제약을 답에 포함해야 한다. |
| q14 | Email Studio의 filtered data extension 생성 시 Country equals UK 조건을 지정한다. | 맞다. p129에 생성 절차가 있다. p130은 필터 기능 소개와 refresh에 대한 보조 근거다. |
| q15 | permission set/profile의 field-level security와 해당 사용자의 실제 page layout을 확인한다. | 맞다. `_p0048_020`은 FLS와 layout 관계, `_021`은 권한 설정 절차다. `_022`는 절차의 마지막 부분 뒤에 암호화 필드 설명이 이어져 보조성이 크다. 배포 성공만으로 특정 사용자의 FLS나 올바른 layout 할당까지 확인되지는 않는다. |
| q16 | 이메일 후 Wait와 Engagement Split을 사용해 미반응 경로를 구성하고 후속 mobile activity를 연결한다. | 핵심 `_p0351_041`은 맞다. `_p0300_029`는 LINE 관계/활동 설정 조각이며 미오픈·미클릭 선별을 설명하지 않는다. `_p0350_040`의 Engagement Split 소개가 누락되어 있다. 아래 상세 검토 참조. |
| q17 | Flow Builder Debug, 입력 변경·실행 경로 확인, rollback mode. | `_p0238_012`는 직접 근거, `_013`은 screen flow 예시로 적절하다. `_014`의 실제 예시는 template-triggered prompt flow이므로 guided screen flow에 대한 직접 예시로 취급하면 안 된다. |
| q18 | Data Loader 등 import/export 도구의 규모·기능을 비교한다. | 맞다. `setup_p0411_003`은 Data Loader의 insert/update/delete/export 및 대량 처리 범위를 제시한다. 질문이 비교를 요청하므로 Data Loader만 유일한 가능한 제품이라고 단정할 필요는 없다. |
| q19 | Apex인 경우 SOQL/DML 루프, collection 처리, trigger bulkification과 transaction governor limits를 조사한다. | 현재 2개는 맞지만 질문은 automation 전반인데 정답은 Apex로 한정되어 있다. Apex 가정을 명시하거나 Flow 관련 정답 범위를 정해야 한다. Apex로 한정해도 bulk DML 문서와 limit 예외 설명이 누락되어 있다. |
| q20 | object Edit 권한과 OWD·소유권·sharing/역할 계층으로 결정되는 record별 write access를 확인한다. | 현재 2개는 맞다. `salesforce_security_impl_guide_p0017_002`와 Account sharing 예시 `salesforce_record_access_under_the_hood_p0010_006`도 관련 있다. 질문이 원인을 제한하지 않아 record locking 등 다른 조사 경로도 가능하다. |

## 우선 수정할 정답 집합

### q02 — 명확한 누락 정답

현재 정답 `sales_core_p0218_022`는 Lightning용이다. `sales_core_p0220_023`는 Salesforce Classic에서 Accounts 탭의 Merge Accounts를 사용하라고 설명하며 권한 조건도 제시한다. 질문에 Lightning 조건이 없으므로 이를 비정답으로 처리할 근거가 없다.

제안: Classic 라벨을 추가하거나 질문에 “in Lightning Experience”를 명시한다. 질문에 없는 UI 제한을 출처 설명만으로 강제해서는 안 된다.

### q05 — 실제 사용자 작업 절차 누락

`sales_core_p0287_029`는 “Create and Edit Relationships Between Contacts and Accounts”이며 Related Contacts의 Add Relationship, Related Accounts 사용, 관계 저장 절차를 설명한다. 현재 라벨은 기능 활성화와 관계 필드 설명에 집중되어 있다. 이 문서를 추가하는 것이 타당하다.

### q12 — after-save 근거 누락과 라벨 직접성 혼합

| 현재/누락 라벨 | 판정 |
| --- | --- |
| `salesforce_apex_developer_guide_p0271_014` | 유지. after trigger가 다른 record를 변경하는 용도임을 설명한다. |
| `salesforce_apex_developer_guide_p0271_015` | 보조. trigger event/syntax와 bulk 처리를 설명하지만 Case→Account 구현 자체는 없다. |
| `salesforce_apex_developer_guide_p0271_016` | 보조 또는 제외 검토. 대부분 Trigger context variables이며 관련 Account 갱신 방법은 설명하지 않는다. |
| `extend_click_automate_p0036_005` | 보조. before-save는 관련 record 갱신에 적합하지 않음을 설명하는 선택 근거이지 after-save 구현 절차는 아니다. |
| `extend_click_automate_p0100_008` | 유지. Update Records로 기존 record를 찾고 필드를 갱신하는 방법이다. 단독으로 Case trigger 조건까지 설명하지는 않는다. |
| `extend_click_automate_p0031_004` | 추가 후보. Record-Triggered After Save Flow와 related record 변경을 명시한다. |

정답은 여러 문서를 조합하는 방식이다. 현재 코퍼스에 정확히 Case→Account 예제를 완결해서 보여 주는 것으로 확인된 라벨은 없다. 직접 답변 청크를 요구한다면 코퍼스 보완도 필요하다.

### q13 — 동기화 상태 페이지를 직접 답으로 세는 문제

`engagement_audience_builder_and_contact_builder_5_30_2026_p0139_007`은 Connect 통합, sync object/field 선택, Poll Schedule, 생성된 DE와 sendability 제약까지 설명한다. `_008`은 관계와 sync 설정 보조 근거로 둘 수 있다. `_009`의 대부분은 Populating/Field Updating/Refreshing 상태이며 CRM 데이터로 고객 메시징을 구현하는 방법을 설명하지 않는다. 직접 정답 기준에서는 `_009` 제외를 권고한다.

### q16 — 미반응 고객 선별과 무관한 청크

- `mc_journeys_and_automations_p0351_041`: 유지. tracking 활성화, 최소 1시간 Wait, email 선택, opens/clicks 기준과 Yes/No 경로 설정을 설명한다.
- `mc_journeys_and_automations_p0300_028`: mobile 후속 활동에 대한 보조 근거다. 선별 기능의 정답과 구분해야 한다.
- `mc_journeys_and_automations_p0300_029`: 제외 권고. LINE contact key/address 연결 조건 및 activity 이름 설정만 남은 짧은 조각이다. 질문이 LINE을 요구하지 않는다.
- `mc_journeys_and_automations_p0350_040`: 추가 후보. open/click/bounce에 따라 Yes/No로 분기하는 Engagement Split을 소개한다.
- `mc_journeys_and_automations_p0293_027`: mobile 후속 활동도 정답 범위에 넣는다면 추가 후보다. SMS/LINE/Push/In-App/Inbox 활동을 소개한다.

“neither opened nor clicked”는 `NOT open AND NOT click`이다. 두 지표를 각각 판정하는 경우 두 split의 No 경로를 순차 연결하는 식의 조건 구성이 필요하다. 현재 라벨이 하나의 split으로 이 논리식 전체를 구현한다고 명시하지는 않는다. 또한 라벨의 open 설명에는 이미지 차단과 click 집계 조건이 있으므로 실제 열람 여부를 완벽하게 식별한다는 답도 피해야 한다.

### q17 — prompt flow 예시와 screen flow 예시 구분

`extend_click_automate_p0238_014`는 PDF 실제 p242~244의 template-triggered prompt flow 예시다. rollback checkbox를 명시한다는 점에서는 관련 있지만 질문의 guided screen flow와 유형이 다르다. 따라서 명백한 무관 문서로 단정하기보다는 **유형이 다른 보조 근거**로 분류한다. `_012`에 일반 Debug 및 rollback 경고가 있고 `_013`에 screen flow 실행·입력 변경·Debug Details 예시가 있으므로 이 둘이 더 직접적이다.

현재 ID와 URL의 p238은 병합 범위 시작이다. `_014`가 실제로 PDF p238 한 장의 내용이라는 뜻은 아니다. 이는 정답 ID 오류는 아니지만 검토할 때 혼동하기 쉽다.

### q19 — Apex로 질문 범위를 맞추고 누락 근거 보완

유지할 현재 라벨은 `salesforce_apex_developer_guide_p0290_017`(bulk trigger 패턴)과 `salesforce_apex_developer_guide_p0354_027`(transaction limits)이다. 다음 후보도 본문에 직접 관련 설명이 있다.

- `salesforce_apex_developer_guide_p0141_003`: list DML을 권장하고 statement 한도를 설명한다.
- `salesforce_apex_developer_guide_p0142_004`: 루프 안 update로 실패하는 코드와 collection을 한 번에 update하도록 고친 예시다.
- `salesforce_apex_developer_guide_p0353_026`: governor limit 초과 시 runtime exception과 transaction별 한도를 설명한다.
- `salesforce_apex_developer_guide_p0271_015`: trigger가 여러 record를 처리한다는 보조 근거다.

질문을 유지한다면 Flow 실패의 validation/rollback 등 다른 가능성도 검토 대상이다. 다만 `extend_click_automate_p0277_016`의 앞부분은 schedule-triggered flow에 관한 내용이므로 Case update 시나리오의 직접 정답으로 바로 추가해서는 안 된다.

### q20 — read/write 차이를 설명하는 근거 누락

`salesforce_security_impl_guide_p0017_002`는 object Read/Edit가 있어도 OWD가 Read-Only면 소유권이나 추가 grant 없이는 편집할 수 없다고 설명한다. `salesforce_record_access_under_the_hood_p0010_006`은 실제 Account의 read-only/read-write grant와 가장 허용적인 grant 적용을 설명한다. 두 문서는 현재 정답과 같은 수준으로 질문에 관련된다.

`extend_click_automate_p0886_022`에는 record locking이 sharing/FLS와 무관하게 편집을 막는다고 나온다. 질문이 access settings에 초점을 두므로 우선 별도 원인 후보로 기록한다. 모든 경우를 sharing 문제로 확정하지 않는다.

## 기존 평가 해석에 미치는 영향

아래는 새 모델 실행 결과가 아니라 저장된 `results/per_query_results.csv`의 순위를 대조한 결과다.

| 사례 | 기존 결과에서 확인된 영향 |
| --- | --- |
| q02 | BM25 4위가 Classic 병합 문서인데 현재 비정답이다. 이를 정답에 추가하면 이 질문의 RR은 0에서 1/4로 바뀐다. Hybrid 두 설정도 Classic 문서가 1위이므로 RR이 1/2에서 1로 바뀐다. |
| q05 | dense 4위와 hybrid_rerank 3위가 빠진 관계 생성 절차 문서다. 정답 집합 변경 시 recall 분자와 분모를 함께 다시 계산해야 한다. |
| q16 | dense 5위가 제외 권고한 LINE 조각이다. 현재 recall 2/3 중 한 건은 이 조각에 의존한다. 첫 정답은 Engagement Split이므로 RR은 이 조각 때문은 아니다. |
| q19 | BM25 2위가 bulk DML의 필요성을 설명하는 `salesforce_apex_developer_guide_p0141_003`다. 이를 정답으로 채택하면 BM25의 해당 질문 RR은 0에서 1/2이므로 README의 “every configuration missed”는 그대로 유지할 수 없다. |
| q20 | BM25 5위가 누락 후보 `salesforce_security_impl_guide_p0017_002`다. 채택하면 해당 질문 RR은 0에서 1/5로 바뀐다. |

`src/evaluate.py`는 라벨별 부분 점수나 직접/보조 등급 없이 동일한 binary relevance를 적용한다. 따라서 정답에 주변 청크를 많이 넣으면 핵심 답을 찾아도 recall이 낮아지고, 정답 누락이 있으면 타당한 검색 결과가 오답 처리된다. 라벨 기준을 먼저 통일하고 수정한 뒤 전체 metric과 README의 성능 해석을 다시 계산해야 한다. 현재 자료만으로 어떤 설정이 최종 1위가 될지 새로 단정하지 않는다.
