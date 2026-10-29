# 핵심 정답과 직접 근거

모든 문제는 admin/developer agent의 관점으로 검토한다. 그러나 정답은 질문의 핵심 해결 방법·구현 단계·증상 원인을 직접 설명하는 청크만 포함한다. 개발 대안도 직접 답하면 유지한다.

질문과 코퍼스는 변경하지 않았다. 일반 인증·배포·실행 순서·migration·참고 링크는 필요에 따라 설명에 활용할 수 있지만 관련 있다는 이유만으로 정답으로 채점하지 않는다. 모든 핵심 단계를 단일 청크가 완결한다는 의미는 아니며, 여러 직접 근거를 조합해야 하는 질문도 있다.

현재 20개 질문, 핵심 라벨 60개다. 보조 문서는 supplementary_doc_ids, 탐색/참고 링크 블록은 excluded_doc_ids로 분리했다. 두 필드는 Recall/MRR 계산에 사용하지 않는다. 광범위한 answer_aspects 지표는 현재 평가에서 제거하고 이전 버전에 보존했다.

## q01 — Lead 전환 중 Account 중복 경고가 나면 어떻게 처리하는가?

**원문:** I am converting a Lead, but Salesforce shows a duplicate Account warning. How should I handle the duplicate record during lead conversion?

**핵심 정답:** 기존 Account와 중복 후보 Account, Lead의 현재 필드값 및 Lead→Account 매핑·matching/duplicate rules를 읽기 전용으로 확인한다. 특히 기존 Account의 매핑 필드가 비어 있고, 그 필드에 들어갈 Lead 값이 다른 Account와 일치하는지 확인해 경고 원인을 설명한다. Account의 빈 필드를 채우거나 Lead 값을 비우지 않는다. 레코드 수정·병합, 새 Account 생성이나 전환 재시도도 실행하지 않는다.

**핵심 판정 근거:** 중복 경고의 발생 조건, 기존 Account·Lead 값과 매핑·중복 규칙을 읽기 전용으로 확인하는 근거다. 문서의 전환·필드 수정 예시는 고객 데이터 변경 권한을 뜻하지 않는다.

정답 문서:

- `sales_core_p0096_002` — PDF p96–96: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sales_core.pdf#page=96
- `sales_core_p0095_001` — PDF p95–95: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sales_core.pdf#page=95
- `sales_core_p0103_004` — PDF p103–103: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sales_core.pdf#page=103
- `salesforce_apex_developer_guide_p0156_admin_lead_conversion_001` — PDF p156–157: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf#page=156

보조 참고: 0개. 탐색/See Also 블록 제외: 0개. 전체 변경 내역은 `results/core_label_review.json`을 참고한다.

## q02 — 중복 Account를 어떻게 병합하는가?

**원문:** I'm a marketing user and how do I merge duplicate Accounts in Salesforce?

**핵심 정답:** Lightning에서는 View Duplicates에서 최대 세 Account와 보존할 principal/필드 값을 선택한다. Classic에서는 Accounts 탭의 Merge Accounts를 사용한다. Delete 권한, 관련 객체 Edit 권한, 관리자·소유자·상위 역할 조건을 확인한다.

**핵심 판정 근거:** UI 및 Apex의 실제 Account 병합 절차는 직접 답변이므로 함께 유지한다.

정답 문서:

- `sales_core_p0218_022` — PDF p218–218: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sales_core.pdf#page=218
- `sales_core_p0220_023` — PDF p220–220: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sales_core.pdf#page=220
- `salesforce_apex_developer_guide_p0152_admin_account_merge_001` — PDF p152–155: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf#page=152
- `salesforce_apex_developer_guide_p0152_admin_account_merge_002` — PDF p152–155: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf#page=152

보조 참고: 0개. 탐색/See Also 블록 제외: 0개. 전체 변경 내역은 `results/core_label_review.json`을 참고한다.

## q03 — 지원 주소로 들어온 이메일이 자동으로 Case를 생성하게 하려면?

**원문:** How do I make emails sent to a support address automatically create Cases in Salesforce?

**핵심 정답:** Email-to-Case와 On-Demand Service를 활성화하고 routing address를 등록·검증한다. 지원 메일 시스템에서 Salesforce가 생성한 email services address로 전달하도록 설정한다.

**핵심 판정 근거:** Case 자동 생성에 필요한 Email-to-Case 활성화와 주소 검증·forwarding 설정을 유지한다. 제한 사항 위주의 소개와 발신 주소 설정은 보조 자료다.

정답 문서:

- `agentforce_contact_center_5_30_2026_p0576_002` — PDF p576–576: file:///C:/Users/hanna/Desktop/agentforce_contact_center_5-30-2026.pdf#page=576
- `agentforce_contact_center_5_30_2026_p0577_003` — PDF p577–577: file:///C:/Users/hanna/Desktop/agentforce_contact_center_5-30-2026.pdf#page=577
- `agentforce_contact_center_5_30_2026_p0584_010` — PDF p584–584: file:///C:/Users/hanna/Desktop/agentforce_contact_center_5-30-2026.pdf#page=584

보조 참고: 2개. 탐색/See Also 블록 제외: 0개. 전체 변경 내역은 `results/core_label_review.json`을 참고한다.

## q04 — Apex governor limit 사용량에 대한 경고 이메일을 설정하려면?

**원문:** How can I configure Salesforce to send email warnings when governor limits are close to being exceeded?

**핵심 정답:** 관리자가 Setup → Users에서 대상 사용자를 편집하고 Send Apex Warning Emails를 켠다. Author Apex 권한이 필요하다.

**핵심 판정 근거:** 사용자의 Send Apex Warning Emails 설정, 권한과 적용 임계치를 직접 설명한다.

정답 문서:

- `salesforce_apex_developer_guide_p0364_028` — PDF p364–364: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf#page=364

보조 참고: 0개. 탐색/See Also 블록 제외: 0개. 전체 변경 내역은 `results/core_label_review.json`을 참고한다.

## q05 — 한 Contact를 여러 Account에 연결하려면?

**원문:** How can one Contact be related to multiple Accounts when the same person works with more than one company?

**핵심 정답:** Contacts to Multiple Accounts를 활성화하고 Related Contacts/Related Accounts에서 Add Relationship을 사용한다. 기본 Account는 direct, 추가 관계는 indirect로 관리한다.

**핵심 판정 근거:** 기능 활성화, 관계 생성과 AccountContactRelation의 실제 사용을 유지한다. 지원 호출 목록이나 필드 목록만 있는 청크는 제외한다.

정답 문서:

- `sales_core_p0280_027` — PDF p280–284: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sales_core.pdf#page=280
- `sales_core_p0280_028` — PDF p280–284: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sales_core.pdf#page=280
- `sales_core_p0277_026` — PDF p277–277: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sales_core.pdf#page=277
- `sales_core_p0287_029` — PDF p287–287: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sales_core.pdf#page=287
- `sf_html_a32b6bcfc3358a0c_61b6181242_001` — AccountContactRelation > Usage: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_accountcontactrelation.htm

보조 참고: 4개. 탐색/See Also 블록 제외: 0개. 전체 변경 내역은 `results/core_label_review.json`을 참고한다.

## q06 — 한 Opportunity에 여러 Quote를 만들어 상품·가격 조합을 비교하려면?

**원문:** How can a sales rep create multiple Quotes for one Opportunity so the customer can compare different product combinations and prices?

**핵심 정답:** Opportunity의 Quotes 관련 목록에서 New Quote로 여러 Quote를 만들고 각 Quote의 상품·수량·할인을 조정한다. Opportunity와 동기화할 수 있는 Quote는 한 번에 하나다.

**핵심 판정 근거:** 한 Opportunity에 여러 Quote를 만들고 상품·가격 조합을 비교하는 절차가 핵심이다. Quote 활성화와 개별 API 필드 명세는 보조 자료다.

정답 문서:

- `sales_core_p0166_020` — PDF p166–166: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sales_core.pdf#page=166

보조 참고: 15개. 탐색/See Also 블록 제외: 0개. 전체 변경 내역은 `results/core_label_review.json`을 참고한다.

## q07 — Apex 없이 Opportunity가 저장되기 전에 필드를 갱신하려면?

**원문:** How can I update an Opportunity field before the record is saved without writing Apex?

**핵심 정답:** before-save record-triggered Flow를 사용해 triggering record의 $Record 필드 값을 변경한다. 해당 변경을 저장하려고 별도 Update Records를 둘 필요는 없다.

**핵심 판정 근거:** Apex 없이 before-save Flow를 선택하고 $Record 값을 갱신하는 핵심 구현을 유지한다.

정답 문서:

- `extend_click_automate_p0036_005` — PDF p36–36: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/extend_click_automate.pdf#page=36
- `extend_click_automate_p0037_006` — PDF p37–37: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/extend_click_automate.pdf#page=37

보조 참고: 0개. 탐색/See Also 블록 제외: 0개. 전체 변경 내역은 `results/core_label_review.json`을 참고한다.

## q08 — 승인된 WhatsApp 템플릿 메시지를 고객에게 보내려면?

**원문:** How can I send approved WhatsApp template messages to customers for a campaign?

**핵심 정답:** 승인된 템플릿을 Content Builder에서 개인화한 뒤 Journey Builder에 WhatsApp Message activity를 추가하고 메시지·App Channel을 선택하여 journey를 활성화한다.

**핵심 판정 근거:** 승인 템플릿 개인화와 Journey Builder 전송 설정이 핵심이다. OAuth와 전송 이벤트는 별도 개발 참고이며 정답으로 채점하지 않는다.

정답 문서:

- `mc_journeys_and_automations_p0321_034` — PDF p321–321: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/mc_journeys_and_automations.pdf#page=321
- `mc_journeys_and_automations_p0322_035` — PDF p322–322: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/mc_journeys_and_automations.pdf#page=322

보조 참고: 13개. 탐색/See Also 블록 제외: 0개. 전체 변경 내역은 `results/core_label_review.json`을 참고한다.

## q09 — Apex에서 Profile 객체를 update할 수 있는가?

**원문:** Can I update the Profile object in Apex?

**핵심 정답:** 일반 sObject DML update로는 할 수 없다. Profile은 query할 수 있지만 DML 미지원 객체 목록에 포함된다.

**핵심 판정 근거:** Apex DML 미지원 목록의 Profile이 직접 답변이다. 일반 Metadata API 배포 방법은 이 질문의 정답이 아니다.

정답 문서:

- `salesforce_apex_developer_guide_p0169_008` — PDF p169–169: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf#page=169

보조 참고: 6개. 탐색/See Also 블록 제외: 0개. 전체 변경 내역은 `results/core_label_review.json`을 참고한다.

## q10 — 상담원 가용성에 따라 라우팅 경로를 바꾸려면?

**원문:** How can I route work to a different queue based on agent availability?

**핵심 정답:** Omni-Channel Flow에서 Check Availability for Routing과 Decision으로 경로를 분기하고 대체 queue로 라우팅한다.

**핵심 판정 근거:** 가용성 확인, queue 선택, Decision과 Route Work 분기를 직접 설명하는 부분을 유지한다. migration 및 skills 전용 설정은 제외한다.

정답 문서:

- `messaging_admin_implementation_guide_p0040_011` — PDF p40–40: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/messaging_admin_implementation_guide.pdf#page=40
- `sf_html_a158f2754a62a0da_9cbf9b3ddb_001` — Make Smarter Routing Decisions by Checking Service Rep Availability: https://help.salesforce.com/s/articleView?id=sf.omnichannel_check_availability_for_routing.htm&language=en_US&type=5
- `sf_html_a158f2754a62a0da_9cbf9b3ddb_002` — Make Smarter Routing Decisions by Checking Service Rep Availability: https://help.salesforce.com/s/articleView?id=sf.omnichannel_check_availability_for_routing.htm&language=en_US&type=5
- `sf_html_a158f2754a62a0da_9cbf9b3ddb_005` — Make Smarter Routing Decisions by Checking Service Rep Availability: https://help.salesforce.com/s/articleView?id=sf.omnichannel_check_availability_for_routing.htm&language=en_US&type=5

보조 참고: 8개. 탐색/See Also 블록 제외: 3개. 전체 변경 내역은 `results/core_label_review.json`을 참고한다.

## q11 — Knowledge의 버전·번역을 고려해 용량을 산정하려면?

**원문:** How should an admin estimate Salesforce Knowledge capacity when articles have versions and translations?

**핵심 정답:** 기사 수 × 보존 버전 수 × 버전별 번역 수를 기준으로 총 article versions를 계산하고 edition별 할당과 org 전체 제한을 확인한다. Storage Usage의 Knowledge와 Knowledge Versions로 실제 사용량을 본다.

**핵심 판정 근거:** 기사·보존 버전·번역 수로 용량을 추정하는 계산이 핵심이다. 실제 사용량 모니터링 절차만으로는 이 질문에 직접 답하지 않는다.

정답 문서:

- `lightning_knowledge_guide_p0011_007` — PDF p11–11: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/lightning_knowledge_guide.pdf#page=11

보조 참고: 1개. 탐색/See Also 블록 제외: 0개. 전체 변경 내역은 `results/core_label_review.json`을 참고한다.

## q12 — Case 생성·수정 시 관련 Account의 필드를 자동으로 갱신하려면?

**원문:** How do I add logic so that when a Case is created or updated, a field on the related Account is also updated?

**핵심 정답:** Case의 after insert/after update Apex trigger 또는 after-save record-triggered Flow를 사용한다. 관련 Account를 식별하고 필요한 필드 값을 설정한 뒤 갱신한다.

**핵심 판정 근거:** after trigger/after-save Flow 선택과 관련 record를 찾아 갱신하는 Update Records 구현은 핵심이다. 실행 순서는 보조 근거다. 정확한 Case→Account 완성 예제라는 주장은 하지 않는다.

정답 문서:

- `salesforce_apex_developer_guide_p0271_014` — PDF p271–273: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf#page=271
- `extend_click_automate_p0031_004` — PDF p31–31: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/extend_click_automate.pdf#page=31
- `extend_click_automate_p0100_008` — PDF p100–100: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/extend_click_automate.pdf#page=100
- `sf_html_cba0a7e8ba972c9d_71ecfefff0_001` — Update Salesforce Records from a Flow > Required Editions: https://help.salesforce.com/s/articleView?id=flow_build_data_update.htm&language=en_US&type=0
- `sf_html_cba0a7e8ba972c9d_71ecfefff0_002` — Update Salesforce Records from a Flow > Required Editions: https://help.salesforce.com/s/articleView?id=flow_build_data_update.htm&language=en_US&type=0

보조 참고: 11개. 탐색/See Also 블록 제외: 1개. 전체 변경 내역은 `results/core_label_review.json`을 참고한다.

## q13 — Salesforce CRM 데이터를 Marketing Cloud DE와 고객 메시징에 사용하려면?

**원문:** How can I use Salesforce CRM data with Marketing Cloud data extensions for customer messaging?

**핵심 정답:** Marketing Cloud Connect로 연결한 뒤 Contact Builder의 Synchronized Data Sources에서 object·field·filter·Poll Schedule을 설정한다. 동기화 데이터를 Data Filters/Query Activities 등으로 활용한다.

**핵심 판정 근거:** CRM 데이터 동기화와 생성되는 DE 및 사용 제약을 설명하는 Synchronized Data Sources 설정을 유지한다. 일반 SQL 설정과 동기화 관계 관리 세부 사항은 제외한다.

정답 문서:

- `engagement_audience_builder_and_contact_builder_5_30_2026_p0139_007` — PDF p139–142: file:///C:/Users/hanna/Desktop/engagement_audience_builder_and_contact_builder_5-30-2026.pdf#page=139

보조 참고: 2개. 탐색/See Also 블록 제외: 0개. 전체 변경 내역은 `results/core_label_review.json`을 참고한다.

## q14 — Country가 UK인 고객만 새 Data Extension에 넣으려면?

**원문:** I have a customer Data Extension and need a new Data Extension containing only customers whose Country equals UK. How can I do this in Marketing Cloud?

**핵심 정답:** Email Studio에서 source DE로 Filtered Data Extension을 만들고 Country equals UK 조건을 지정해 Save & Build한다.

**핵심 판정 근거:** 조건으로 새 filtered DE를 만드는 절차가 핵심이다. refresh 절차와 일반 SQL Query Activity 설정은 정답에서 제외한다.

정답 문서:

- `mc_email_p0129_011` — PDF p129–129: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/mc_email.pdf#page=129

보조 참고: 2개. 탐색/See Also 블록 제외: 0개. 전체 변경 내역은 `results/core_label_review.json`을 참고한다.

## q15 — 배포와 layout 추가를 마친 custom field가 Account 페이지에 안 보이면?

**원문:** A custom field was added in the layout and deployed successfully, but it does not appear on the Account record page. What should I check?

**핵심 정답:** 해당 사용자의 FLS Read/Visible, Dynamic Forms의 field/section visibility 및 실제 App·Record Type·Profile별 Lightning page assignment를 확인한다.

**핵심 판정 근거:** FLS, 실제 field visibility, hidden field sections 및 page assignment처럼 필드가 보이지 않는 원인을 직접 설명하는 부분을 유지한다. custom Apex라는 추가 가정이 필요한 보안 문서는 보조 자료다.

정답 문서:

- `salesforce_security_impl_guide_p0048_020` — PDF p48–50: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf#page=48
- `salesforce_security_impl_guide_p0048_021` — PDF p48–50: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf#page=48
- `sf_html_7be2b814b39ccb02_62cad5e94b_001` — Visibility Rules on Lightning Pages > Visibility Rules on Dynamic Forms Fields and Field Sections: https://help.salesforce.com/s/articleView?id=sf.lightning_page_components_visibility.htm&language=en_US&type=5
- `sf_html_8ada3a8db77b5a87_54fe993072_002` — Dynamic Forms Tips and Considerations > Visibility Rules and Dynamic Forms: https://help.salesforce.com/s/articleView?id=sf.dynamic_forms_considerations.htm&language=en_US&type=5
- `sf_html_ac87ed5d4bc22bf8_aa7d572199_002` — Activate Lightning  Record or Home Pages > Required Editions: https://help.salesforce.com/s/articleView?id=sf.lightning_app_builder_customize_lex_pages_activate.htm&language=en_US&type=5

보조 참고: 12개. 탐색/See Also 블록 제외: 3개. 전체 변경 내역은 `results/core_label_review.json`을 참고한다.

## q16 — Journey Builder에서 쿠폰 이메일을 열지도 클릭하지도 않은 고객을 선별하려면?

**원문:** How can a marketer identify customers who neither opened nor clicked a voucher email in Journey Builder before sending a follow-up mobile message?

**핵심 정답:** 이메일 tracking을 활성화하고 Wait 후 Engagement Split의 No 경로를 사용한다. open과 click을 별도로 확인한다면 두 조건을 순차 확인하여 NOT open AND NOT click을 구성한 뒤 후속 mobile activity로 연결한다.

**핵심 판정 근거:** Engagement Split 설정과 NOT open AND NOT click을 명시한 SQL은 직접 답변이다. 일반 활동 목록과 SQL 대상 DE 소개만 있는 청크는 제외한다.

정답 문서:

- `mc_journeys_and_automations_p0351_041` — PDF p351–351: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/mc_journeys_and_automations.pdf#page=351
- `mc_journeys_and_automations_p0103_003` — PDF p103–103: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/mc_journeys_and_automations.pdf#page=103
- `mc_journeys_and_automations_p0102_admin_sql_nonengagement_001` — PDF p102–103: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/mc_journeys_and_automations.pdf#page=102

보조 참고: 2개. 탐색/See Also 블록 제외: 0개. 전체 변경 내역은 `results/core_label_review.json`을 참고한다.

## q17 — 입력을 바꿔 guided process를 테스트하고 실행 경로를 보되 test record를 남기지 않으려면?

**원문:** A sales team uses a guided process that collects deal information and creates an Opportunity with related records. The admin needs to test several user input combinations, observe the execution path taken by the automation, and prevent test records from being permanently saved. Which Salesforce feature would help with this investigation?

**핵심 정답:** Flow Builder Debug에서 입력을 바꿔 실행하고 Debug Details로 경로를 확인한다. DB 변경을 남기지 않도록 Run flow in rollback mode를 사용한다.

**핵심 판정 근거:** 입력·실행 경로 확인과 rollback을 설명하는 Flow Builder Debug 및 screen flow 예시를 유지한다. 일반 sandbox 통합 테스트 주의 사항은 보조 자료다.

정답 문서:

- `extend_click_automate_p0238_012` — PDF p238–244: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/extend_click_automate.pdf#page=238
- `extend_click_automate_p0238_013` — PDF p238–244: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/extend_click_automate.pdf#page=238

보조 참고: 1개. 탐색/See Also 블록 제외: 0개. 전체 변경 내역은 `results/core_label_review.json`을 참고한다.

## q18 — 대량 import·기존 record update·export를 지원하는 도구를 고르려면?

**원문:** A company is preparing a large customer migration and wants to compare Salesforce import options. The team needs a tool that supports high-volume data loads, updates to existing records, and export capability.

**핵심 정답:** Data Loader가 요구를 충족한다. Data Import Wizard, Data Loader, dataloader.io를 규모·지원 객체·실행 방식·export 지원으로 비교한다.

**핵심 판정 근거:** 대량 처리·update·export 요구를 충족하는 도구 비교와 Data Loader 기능이 핵심이다. import 권한은 도구 선택에 대한 직접 답변이 아니다.

정답 문서:

- `setup_p0411_003` — PDF p411–411: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/setup.pdf#page=411
- `setup_p0439_013` — PDF p439–439: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/setup.pdf#page=439

보조 참고: 1개. 탐색/See Also 블록 제외: 0개. 전체 변경 내역은 `results/core_label_review.json`을 참고한다.

## q19 — 소량 Case에서는 되지만 대량 update 때 실패하는 automation을 조사·개선하려면?

**원문:** A Case automation works for a few records but fails when many Cases are updated at once. How should I investigate and redesign the automation so it can handle large batches safely?

**핵심 정답:** 오류와 실행 경로를 먼저 확인한다. Apex 경로라면 SOQL/DML을 record 루프 안에서 반복하는지와 transaction limits를 확인하고, 전체 trigger record를 collection/set으로 처리하여 SOQL·DML 호출을 묶는다.

**핵심 판정 근거:** 질문이 조사와 재설계를 함께 요구하므로 bulk SOQL/DML·Flow 처리와 실제 trace 설정·limit 로그 해석을 유지한다. 일반 실행 순서와 원인 연결이 없는 한도 표는 제외한다.

정답 문서:

- `salesforce_apex_developer_guide_p0290_017` — PDF p290–290: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf#page=290
- `salesforce_apex_developer_guide_p0141_003` — PDF p141–141: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf#page=141
- `salesforce_apex_developer_guide_p0142_004` — PDF p142–142: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf#page=142
- `extend_click_automate_p0068_admin_flow_bulk_001` — PDF p68–69: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/extend_click_automate.pdf#page=68
- `sf_html_464fa8a2f5d3c3df_46f73113c5_001` — How to Capture and Read Salesforce Debug Logs for Troubleshooting Flows, Apex, and Automations: https://help.salesforce.com/s/articleView?id=000392579&language=en_US&type=1
- `sf_html_464fa8a2f5d3c3df_6be58da2dd_001` — How to Capture and Read Salesforce Debug Logs for Troubleshooting Flows, Apex, and Automations: https://help.salesforce.com/s/articleView?id=000392579&language=en_US&type=1
- `sf_html_464fa8a2f5d3c3df_fffc69cbd1_002` — How to Capture and Read Salesforce Debug Logs for Troubleshooting Flows, Apex, and Automations: https://help.salesforce.com/s/articleView?id=000392579&language=en_US&type=1

보조 참고: 7개. 탐색/See Also 블록 제외: 1개. 전체 변경 내역은 `results/core_label_review.json`을 참고한다.

## q20 — Account는 열리지만 일부 record에서 Edit가 없으면 어떤 접근 설정을 보는가?

**원문:** A user can open Account records but the Edit option is unavailable for some customer accounts. What access settings should I investigate?

**핵심 정답:** Account object의 Edit와 record별 write access를 확인하고 OWD·sharing grants를 조사한다. 승인 record lock과 page layout의 실제 Edit action 표시도 원인 후보로 확인한다.

**핵심 판정 근거:** object Edit와 record sharing, read/write grant, approval lock, 실제 record action 표시 위치처럼 증상의 원인을 직접 설명하는 부분을 유지한다. Apex 실행 모드와 일반 역할 생성 절차는 제외한다.

정답 문서:

- `salesforce_record_access_under_the_hood_p0006_002` — PDF p6–6: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_record_access_under_the_hood.pdf#page=6
- `salesforce_security_impl_guide_p0017_002` — PDF p17–17: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf#page=17
- `salesforce_record_access_under_the_hood_p0010_006` — PDF p10–10: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_record_access_under_the_hood.pdf#page=10
- `salesforce_security_impl_guide_p0059_023` — PDF p59–59: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf#page=59
- `sf_html_abd6d4a3ef832849_da0f42fbec_001` — Classic Approval Processes Terminology > Record Locking: https://help.salesforce.com/s/articleView?id=sf.approvals_terminology.htm&language=en_US&type=5
- `sf_html_363303a2e9de2b80_280d936586_001` — How Actions Are Ordered in Lightning Experience: https://help.salesforce.com/s/articleView?id=platform.actions_in_lex_ordering.htm&language=en_US&type=5

보조 참고: 12개. 탐색/See Also 블록 제외: 3개. 전체 변경 내역은 `results/core_label_review.json`을 참고한다.
