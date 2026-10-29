# Admin agent용 문제별 정답과 근거

2026-10-23: 모든 질문의 답변 대상을 CRM admin/developer로 통일했다. 질문 표현과 최초 요청자 역할은 유지하며, 설정·권한·데이터 모델·관련 코드/SQL·실행 조건을 함께 검토한다. 모든 질문에 Apex가 필요한 것은 아니다.

기존 답변은 아래 ‘기본 해결 경로’에 보존했다. 기존 추가/제외 판단은 2026-10-22 검토 기록이며, 현재 라벨은 각 문제 끝의 목록을 기준으로 한다. 버전이 고정된 PDF의 증거이며 최신 제품 동작 검증은 아니다.

총 354개 문서, 67개 라벨. 문서 recall@5 이론 상한은 0.969444. 보조 지표 aspect_recall@5는 답변 항목/구현 경로별 근거 검색률이며 생성 답변의 정확도나 완성도를 의미하지 않는다.

미충족 근거: AccountContactRelation의 API/DML 명세, Quote/QuoteLineItem API 구현, Profile 메타데이터 수정 경로, WhatsApp REST 전송 API 등은 현재 PDF만으로 검증하지 못했다. 이 경로를 구현하는 코드는 별도 공식 레퍼런스를 확보한 후 검증해야 한다.

## q01 — Lead 전환 중 Account 중복 경고가 나면 어떻게 처리하는가?

**원문:** I am converting a Lead, but Salesforce shows a duplicate Account warning. How should I handle the duplicate record during lead conversion?

**기본 해결 경로:** 중복 후보와 duplicate rules를 확인하고 기존 Account를 선택한다. 경고를 무시할 수 없는 특정 오류라면 기존 Account의 빈 매핑 필드를 먼저 채우거나 해당 Lead 값을 비운 뒤 다시 전환한다.

**근거와 한계:** p95·103은 일반 중복 처리와 기존 Account 선택을, p96은 빈 매핑 필드 때문에 발생하는 특정 경고의 해결책을 설명한다. 질문이 일반 경고이므로 특정 오류 문서만 정답으로 제한하지 않았다.



**Admin/개발 관점에서 추가로 확인할 항목:**

- **admin_resolution**: 전환 UI·duplicate rules·빈 매핑 필드의 원인을 확인한다.
  - 근거: `sales_core_p0096_002`, `sales_core_p0095_001`, `sales_core_p0103_004`
- **apex_conversion**: 개발 경로에서는 기존 Account ID와 Database.convertLead 및 LeadConvertResult를 조사한다. 일반 Account insert의 allowSave 예시를 전환 우회책으로 단정하지 않는다.
  - 근거: `salesforce_apex_developer_guide_p0156_admin_lead_conversion_001`

현재 정답 문서:

- `sales_core_p0096_002` — sales_core.pdf PDF p96–96: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sales_core.pdf#page=96
- `sales_core_p0095_001` — sales_core.pdf PDF p95–95: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sales_core.pdf#page=95
- `sales_core_p0103_004` — sales_core.pdf PDF p103–103: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sales_core.pdf#page=103
- `salesforce_apex_developer_guide_p0156_admin_lead_conversion_001` — salesforce_apex_developer_guide.pdf PDF p156–157: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf#page=156

## q02 — 중복 Account를 어떻게 병합하는가?

**원문:** I'm a marketing user and how do I merge duplicate Accounts in Salesforce?

**기본 해결 경로:** Lightning에서는 View Duplicates에서 최대 세 Account와 보존할 principal/필드 값을 선택한다. Classic에서는 Accounts 탭의 Merge Accounts를 사용한다. Delete 권한, 관련 객체 Edit 권한, 관리자·소유자·상위 역할 조건을 확인한다.

**근거와 한계:** p218은 Lightning 병합 절차와 권한, p220은 Classic 절차와 권한을 설명한다. 질문에는 Lightning 제한이 없으므로 두 UI 모두 정답이다. marketing user라는 직무는 권한을 보장하지 않는다.



**Admin/개발 관점에서 추가로 확인할 항목:**

- **admin_merge**: UI 병합의 권한·소유권·보존 필드를 확인한다.
  - 근거: `sales_core_p0218_022`, `sales_core_p0220_023`
- **apex_merge**: 개발 경로에서는 merge/Database.merge, 관련 record 재연결, 결과 오류와 보존 필드를 확인한다.
  - 근거: `salesforce_apex_developer_guide_p0152_admin_account_merge_001`, `salesforce_apex_developer_guide_p0152_admin_account_merge_002`

현재 정답 문서:

- `sales_core_p0218_022` — sales_core.pdf PDF p218–218: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sales_core.pdf#page=218
- `sales_core_p0220_023` — sales_core.pdf PDF p220–220: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sales_core.pdf#page=220
- `salesforce_apex_developer_guide_p0152_admin_account_merge_001` — salesforce_apex_developer_guide.pdf PDF p152–155: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf#page=152
- `salesforce_apex_developer_guide_p0152_admin_account_merge_002` — salesforce_apex_developer_guide.pdf PDF p152–155: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf#page=152

## q03 — 지원 주소로 들어온 이메일이 자동으로 Case를 생성하게 하려면?

**원문:** How do I make emails sent to a support address automatically create Cases in Salesforce?

**기본 해결 경로:** Email-to-Case와 On-Demand Service를 활성화하고 routing address를 등록·검증한다. 지원 메일 시스템에서 Salesforce가 생성한 email services address로 전달하도록 설정한다.

**근거와 한계:** p575는 기능 소개, p576은 설정 단계, p577은 활성화, p584는 routing address와 forwarding 절차다. 기능을 식별하는 소개와 실제 설정 절차를 모두 유효한 답변 근거로 유지했다.



**Admin/개발 관점에서 추가로 확인할 항목:**

- **feature_setup**: Email-to-Case와 On-Demand Service를 활성화한다.
  - 근거: `agentforce_contact_center_5_30_2026_p0575_001`, `agentforce_contact_center_5_30_2026_p0576_002`, `agentforce_contact_center_5_30_2026_p0577_003`
- **routing_integration**: routing address 검증, mail forwarding 및 실제 이메일 테스트를 확인한다. 표준 기능으로 해결할 수 있으며 custom Apex email handler가 필수인 것은 아니다.
  - 근거: `agentforce_contact_center_5_30_2026_p0584_010`, `agentforce_contact_center_5_30_2026_p0585_011`

현재 정답 문서:

- `agentforce_contact_center_5_30_2026_p0575_001` — agentforce_contact_center_5-30-2026.pdf PDF p575–575: file:///C:/Users/hanna/Desktop/agentforce_contact_center_5-30-2026.pdf#page=575
- `agentforce_contact_center_5_30_2026_p0576_002` — agentforce_contact_center_5-30-2026.pdf PDF p576–576: file:///C:/Users/hanna/Desktop/agentforce_contact_center_5-30-2026.pdf#page=576
- `agentforce_contact_center_5_30_2026_p0577_003` — agentforce_contact_center_5-30-2026.pdf PDF p577–577: file:///C:/Users/hanna/Desktop/agentforce_contact_center_5-30-2026.pdf#page=577
- `agentforce_contact_center_5_30_2026_p0584_010` — agentforce_contact_center_5-30-2026.pdf PDF p584–584: file:///C:/Users/hanna/Desktop/agentforce_contact_center_5-30-2026.pdf#page=584
- `agentforce_contact_center_5_30_2026_p0585_011` — agentforce_contact_center_5-30-2026.pdf PDF p585–585: file:///C:/Users/hanna/Desktop/agentforce_contact_center_5-30-2026.pdf#page=585

## q04 — Apex governor limit 사용량에 대한 경고 이메일을 설정하려면?

**원문:** How can I configure Salesforce to send email warnings when governor limits are close to being exceeded?

**기본 해결 경로:** 관리자가 Setup → Users에서 대상 사용자를 편집하고 Send Apex Warning Emails를 켠다. Author Apex 권한이 필요하다.

**근거와 한계:** p364는 설정 절차와 함께 할당량의 50%를 넘을 때 검사 대상 per-request limits에 대해 경고한다고 설명한다. 임의 임계치나 모든 org 한도에 대한 알림으로 해석하면 안 된다.



**Admin/개발 관점에서 추가로 확인할 항목:**

- **apex_warning_configuration**: 사용자별 Send Apex Warning Emails, Author Apex 권한, 50%와 per-request 적용 범위를 함께 설명한다. 임의 임계치 또는 전체 org 한도 알림으로 확장하지 않는다.
  - 근거: `salesforce_apex_developer_guide_p0364_028`

현재 정답 문서:

- `salesforce_apex_developer_guide_p0364_028` — salesforce_apex_developer_guide.pdf PDF p364–364: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf#page=364

## q05 — 한 Contact를 여러 Account에 연결하려면?

**원문:** How can one Contact be related to multiple Accounts when the same person works with more than one company?

**기본 해결 경로:** Contacts to Multiple Accounts를 활성화하고 Related Contacts/Related Accounts에서 Add Relationship을 사용한다. 기본 Account는 direct, 추가 관계는 indirect로 관리한다.

**근거와 한계:** p277은 기능과 direct/indirect 관계, p280~284는 활성화·관련 목록·관계 필드, p287은 실제 관계 생성·수정 절차다. 관리자의 설정뿐 아니라 사용자의 관계 생성 방법도 정답에 추가했다.



**Admin/개발 관점에서 추가로 확인할 항목:**

- **admin_relationship_setup**: 기능 활성화, 관련 목록과 Add Relationship 절차를 확인한다.
  - 근거: `sales_core_p0280_027`, `sales_core_p0287_029`
- **relationship_model**: Account Contact Relationship 객체와 direct/indirect 관계를 이해한다. 구체적인 DML/API payload는 현재 문서 근거가 부족해 생성하지 않는다.
  - 근거: `sales_core_p0280_028`, `sales_core_p0277_026`

현재 정답 문서:

- `sales_core_p0280_027` — sales_core.pdf PDF p280–284: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sales_core.pdf#page=280
- `sales_core_p0287_029` — sales_core.pdf PDF p287–287: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sales_core.pdf#page=287
- `sales_core_p0280_028` — sales_core.pdf PDF p280–284: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sales_core.pdf#page=280
- `sales_core_p0277_026` — sales_core.pdf PDF p277–277: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sales_core.pdf#page=277

## q06 — 한 Opportunity에 여러 Quote를 만들어 상품·가격 조합을 비교하려면?

**원문:** How can a sales rep create multiple Quotes for one Opportunity so the customer can compare different product combinations and prices?

**기본 해결 경로:** Opportunity의 Quotes 관련 목록에서 New Quote로 여러 Quote를 만들고 각 Quote의 상품·수량·할인을 조정한다. Opportunity와 동기화할 수 있는 Quote는 한 번에 하나다.

**근거와 한계:** p166은 서로 다른 조합의 Quote 생성, New Quote 절차, 여러 Quote와 단일 sync 관계를 직접 설명한다.



**Admin/개발 관점에서 추가로 확인할 항목:**

- **quote_workflow**: 여러 Quote를 만들되 Opportunity와의 sync는 한 번에 하나라는 제약을 설명한다.
  - 근거: `sales_core_p0166_020`
- **admin_quote_setup**: Quote Settings 활성화, Customize Application 권한과 Opportunity 관련 목록을 확인한다. Quote/QuoteLineItem API 구현은 현재 코퍼스의 미충족 항목이다.
  - 근거: `sales_core_p0160_admin_quote_setup_001`

현재 정답 문서:

- `sales_core_p0166_020` — sales_core.pdf PDF p166–166: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sales_core.pdf#page=166
- `sales_core_p0160_admin_quote_setup_001` — sales_core.pdf PDF p160–160: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/sales_core.pdf#page=160

## q07 — Apex 없이 Opportunity가 저장되기 전에 필드를 갱신하려면?

**원문:** How can I update an Opportunity field before the record is saved without writing Apex?

**기본 해결 경로:** before-save record-triggered Flow를 사용해 triggering record의 $Record 필드 값을 변경한다. 해당 변경을 저장하려고 별도 Update Records를 둘 필요는 없다.

**근거와 한계:** p36은 before-save Flow의 용도와 실행 시점, p37은 $Record와 지원 요소를 설명한다. 관련 Account 같은 다른 record를 갱신하는 용도와는 구분해야 한다.



**Admin/개발 관점에서 추가로 확인할 항목:**

- **flow_selection**: 질문의 without Apex 조건을 지켜 before-save record-triggered Flow를 선택한다.
  - 근거: `extend_click_automate_p0036_005`
- **flow_implementation**: $Record 값을 변경하고 지원 요소와 별도 Update Records 불필요 조건을 설명한다. 관련 record 갱신에는 이 방식을 적용하지 않는다.
  - 근거: `extend_click_automate_p0037_006`

현재 정답 문서:

- `extend_click_automate_p0036_005` — extend_click_automate.pdf PDF p36–36: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/extend_click_automate.pdf#page=36
- `extend_click_automate_p0037_006` — extend_click_automate.pdf PDF p37–37: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/extend_click_automate.pdf#page=37

## q08 — 승인된 WhatsApp 템플릿 메시지를 고객에게 보내려면?

**원문:** How can I send approved WhatsApp template messages to customers for a campaign?

**기본 해결 경로:** 승인된 템플릿을 Content Builder에서 개인화한 뒤 Journey Builder에 WhatsApp Message activity를 추가하고 메시지·App Channel을 선택하여 journey를 활성화한다.

**근거와 한계:** p321은 승인 상태·개인화, p322는 전송 설정을 설명한다. p322는 WhatsApp 메시지에 Journey Builder Campaigns와 Engagement Splits를 사용할 수 없다고 한다. 질문의 campaign은 일반 마케팅 활동으로 해석한다.



**Admin/개발 관점에서 추가로 확인할 항목:**

- **template_lifecycle**: 승인·active 상태·개인화 변수 제약을 확인한다.
  - 근거: `mc_journeys_and_automations_p0321_034`
- **journey_execution**: WhatsApp activity와 App Channel을 설정한다. Journey Builder Campaigns 및 WhatsApp engagement split 제약을 설명하며 근거 없는 Apex 전송 방법은 제시하지 않는다.
  - 근거: `mc_journeys_and_automations_p0322_035`

현재 정답 문서:

- `mc_journeys_and_automations_p0321_034` — mc_journeys_and_automations.pdf PDF p321–321: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/mc_journeys_and_automations.pdf#page=321
- `mc_journeys_and_automations_p0322_035` — mc_journeys_and_automations.pdf PDF p322–322: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/mc_journeys_and_automations.pdf#page=322

## q09 — Apex에서 Profile 객체를 update할 수 있는가?

**원문:** Can I update the Profile object in Apex?

**기본 해결 경로:** 일반 sObject DML update로는 할 수 없다. Profile은 query할 수 있지만 DML 미지원 객체 목록에 포함된다.

**근거와 한계:** p169의 sObjects That Don't Support DML Operations에 Profile이 명시되어 있다. 이 근거는 DML에 관한 것이며 모든 메타데이터 변경 경로가 불가능하다는 의미는 아니다.



**Admin/개발 관점에서 추가로 확인할 항목:**

- **apex_dml_support**: Profile은 일반 sObject DML update 미지원임을 확인한다. Profile 메타데이터 변경은 별도 문서 검증이 필요한 경로이며 DML 우회 코드를 만들지 않는다.
  - 근거: `salesforce_apex_developer_guide_p0169_008`

현재 정답 문서:

- `salesforce_apex_developer_guide_p0169_008` — salesforce_apex_developer_guide.pdf PDF p169–169: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf#page=169

## q10 — 상담원 가용성에 따라 라우팅 경로를 바꾸려면?

**원문:** How can I route work to a different queue based on agent availability?

**기본 해결 경로:** Omni-Channel Flow에서 Check Availability for Routing과 Decision으로 경로를 분기하고 대체 queue로 라우팅한다.

**근거와 한계:** p39는 Messaging용 Omni-Channel Flow 설정, p40은 특정 agent가 available이면 agent에게 보내고 offline이면 queue로 보내는 예시다. 질문의 queue 간 전환 전체를 구현하는 예시는 아니므로 기능 선택 근거로 해석한다.



**Admin/개발 관점에서 추가로 확인할 항목:**

- **omni_channel_setup**: Messaging service channel·presence·fallback queue 선행 설정을 확인한다.
  - 근거: `messaging_admin_implementation_guide_p0039_010`
- **availability_flow**: Check Availability for Routing과 Decision으로 분기한다. 문서 예시는 agent→queue fallback이며 queue 간 전환 전체 구현은 아니다.
  - 근거: `messaging_admin_implementation_guide_p0040_011`

현재 정답 문서:

- `messaging_admin_implementation_guide_p0039_010` — messaging_admin_implementation_guide.pdf PDF p39–39: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/messaging_admin_implementation_guide.pdf#page=39
- `messaging_admin_implementation_guide_p0040_011` — messaging_admin_implementation_guide.pdf PDF p40–40: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/messaging_admin_implementation_guide.pdf#page=40

## q11 — Knowledge의 버전·번역을 고려해 용량을 산정하려면?

**원문:** How should an admin estimate Salesforce Knowledge capacity when articles have versions and translations?

**기본 해결 경로:** 기사 수 × 보존 버전 수 × 버전별 번역 수를 기준으로 총 article versions를 계산하고 edition별 할당과 org 전체 제한을 확인한다. Storage Usage의 Knowledge와 Knowledge Versions로 실제 사용량을 본다.

**근거와 한계:** p11은 100,000 × 5 × 5 = 2,500,000 예시와 edition별 할당을, p12는 실제 기사/버전 수 모니터링을 설명한다. 현재 제품 한도를 새로 검증한 수치는 아니다.



**Admin/개발 관점에서 추가로 확인할 항목:**

- **capacity_model**: article × retained versions × translations와 edition 할당을 계산한다.
  - 근거: `lightning_knowledge_guide_p0011_007`
- **capacity_monitoring**: Storage Usage의 Knowledge/Knowledge Versions를 모니터링한다. 단순 article record 수만으로 판단하지 않는다.
  - 근거: `lightning_knowledge_guide_p0012_008`

현재 정답 문서:

- `lightning_knowledge_guide_p0011_007` — lightning_knowledge_guide.pdf PDF p11–11: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/lightning_knowledge_guide.pdf#page=11
- `lightning_knowledge_guide_p0012_008` — lightning_knowledge_guide.pdf PDF p12–12: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/lightning_knowledge_guide.pdf#page=12

## q12 — Case 생성·수정 시 관련 Account의 필드를 자동으로 갱신하려면?

**원문:** How do I add logic so that when a Case is created or updated, a field on the related Account is also updated?

**기본 해결 경로:** Case의 after insert/after update Apex trigger 또는 after-save record-triggered Flow를 사용한다. 관련 Account를 식별하고 필요한 필드 값을 설정한 뒤 갱신한다.

**근거와 한계:** Apex p271은 after trigger가 다른 record를 변경하는 용도라고 설명한다. Flow p31은 after-save Flow, p100은 Update Records를 설명한다. context variables·일반 trigger syntax와 before-save 제한 설명은 직접 구현 근거에서 제외했다. Case→Account 완성 예제 자체가 있는 것은 아니다.



**Admin/개발 관점에서 추가로 확인할 항목:**

- **flow_implementation**: after-save Flow에서 관련 Account를 식별하고 Update Records를 사용한다.
  - 근거: `extend_click_automate_p0031_004`, `extend_click_automate_p0100_008`
- **apex_implementation**: Case after insert/update trigger에서 관련 record를 갱신한다. 정확한 Case→Account 완성 예제는 아니며 별도 bulk·recursion·권한 검증이 필요하다.
  - 근거: `salesforce_apex_developer_guide_p0271_014`

현재 정답 문서:

- `extend_click_automate_p0031_004` — extend_click_automate.pdf PDF p31–31: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/extend_click_automate.pdf#page=31
- `extend_click_automate_p0100_008` — extend_click_automate.pdf PDF p100–100: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/extend_click_automate.pdf#page=100
- `salesforce_apex_developer_guide_p0271_014` — salesforce_apex_developer_guide.pdf PDF p271–273: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf#page=271

## q13 — Salesforce CRM 데이터를 Marketing Cloud DE와 고객 메시징에 사용하려면?

**원문:** How can I use Salesforce CRM data with Marketing Cloud data extensions for customer messaging?

**기본 해결 경로:** Marketing Cloud Connect로 연결한 뒤 Contact Builder의 Synchronized Data Sources에서 object·field·filter·Poll Schedule을 설정한다. 동기화 데이터를 Data Filters/Query Activities 등으로 활용한다.

**근거와 한계:** p139~142의 _007은 동기화 설정과 생성된 DE, _008은 관계와 설정 변경을 설명한다. synchronized source를 primary sendable DE로 직접 사용할 수 없다는 제약도 있다. 주로 진행률/상태를 설명하는 _009는 제외했다.



**Admin/개발 관점에서 추가로 확인할 항목:**

- **crm_sync_setup**: Marketing Cloud Connect와 Synchronized Data Sources의 object·field·filter·poll schedule을 설정한다.
  - 근거: `engagement_audience_builder_and_contact_builder_5_30_2026_p0139_007`
- **data_pipeline**: 관계·contact keys와 Query Activity의 별도 target DE를 검토한다. synchronized source를 primary sendable DE로 직접 사용하지 않는다. 실제 schema와 sendable 관계는 org별 검증 사항이다.
  - 근거: `engagement_audience_builder_and_contact_builder_5_30_2026_p0139_008`, `mc_journeys_and_automations_p0029_admin_sql_query_setup_001`

현재 정답 문서:

- `engagement_audience_builder_and_contact_builder_5_30_2026_p0139_007` — engagement_audience_builder_and_contact_builder_5-30-2026.pdf PDF p139–142: file:///C:/Users/hanna/Desktop/engagement_audience_builder_and_contact_builder_5-30-2026.pdf#page=139
- `engagement_audience_builder_and_contact_builder_5_30_2026_p0139_008` — engagement_audience_builder_and_contact_builder_5-30-2026.pdf PDF p139–142: file:///C:/Users/hanna/Desktop/engagement_audience_builder_and_contact_builder_5-30-2026.pdf#page=139
- `mc_journeys_and_automations_p0029_admin_sql_query_setup_001` — mc_journeys_and_automations.pdf PDF p29–29: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/mc_journeys_and_automations.pdf#page=29

## q14 — Country가 UK인 고객만 새 Data Extension에 넣으려면?

**원문:** I have a customer Data Extension and need a new Data Extension containing only customers whose Country equals UK. How can I do this in Marketing Cloud?

**기본 해결 경로:** Email Studio에서 source DE로 Filtered Data Extension을 만들고 Country equals UK 조건을 지정해 Save & Build한다. 원본 데이터 변경 후에는 refresh가 필요하다.

**근거와 한계:** p129는 필터 생성 절차와 operator 선택, p130은 필터 기능과 refresh 절차를 설명한다. 구체적인 Country 필드 값은 질문의 예시이고 문서의 일반 필터 절차를 적용한다.



**Admin/개발 관점에서 추가로 확인할 항목:**

- **filtered_de**: Country equals UK 조건으로 filtered DE를 만들고 refresh 동작을 설명한다.
  - 근거: `mc_email_p0129_011`, `mc_email_p0130_012`
- **sql_alternative**: 개발 대안은 별도 target DE에 SELECT ... FROM [source] WHERE Country = 'UK' 결과를 쓰는 SQL Query Activity다. 쿼리는 문서의 일반 절차를 적용한 예시이며 실제 필드·키·overwrite 영향을 검증해야 한다.
  - 근거: `mc_journeys_and_automations_p0029_admin_sql_query_setup_001`

현재 정답 문서:

- `mc_email_p0129_011` — mc_email.pdf PDF p129–129: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/mc_email.pdf#page=129
- `mc_email_p0130_012` — mc_email.pdf PDF p130–130: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/mc_email.pdf#page=130
- `mc_journeys_and_automations_p0029_admin_sql_query_setup_001` — mc_journeys_and_automations.pdf PDF p29–29: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/mc_journeys_and_automations.pdf#page=29

## q15 — 배포와 layout 추가를 마친 custom field가 Account 페이지에 안 보이면?

**원문:** A custom field was added in the layout and deployed successfully, but it does not appear on the Account record page. What should I check?

**기본 해결 경로:** 해당 사용자의 permission set/profile에서 field-level security의 Read/Visible을 확인하고 실제 적용된 page layout도 확인한다.

**근거와 한계:** p48~50의 _020은 FLS와 layout 중 더 제한적인 설정이 적용됨을, _021은 field permission 설정 절차를 설명한다. _022는 앞 청크의 절차 끝부분과 암호화 필드 설명이 중심이라 제외했다. FLS가 가능한 원인이며 유일한 원인으로 확정하는 질문은 아니다.



**Admin/개발 관점에서 추가로 확인할 항목:**

- **ui_field_access**: 해당 사용자의 FLS와 실제 layout을 확인한다.
  - 근거: `salesforce_security_impl_guide_p0048_020`, `salesforce_security_impl_guide_p0048_021`
- **apex_field_access**: custom UI/Apex 경로가 있다면 object/FLS describe checks와 user/system mode를 함께 확인한다. API 67.0 전후 기본 실행 모드 차이를 문서 버전에 맞춰 해석하며 UI 원인으로 바로 확정하지 않는다.
  - 근거: `salesforce_apex_developer_guide_p0220_admin_apex_permissions_001`

현재 정답 문서:

- `salesforce_security_impl_guide_p0048_020` — salesforce_security_impl_guide.pdf PDF p48–50: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf#page=48
- `salesforce_security_impl_guide_p0048_021` — salesforce_security_impl_guide.pdf PDF p48–50: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf#page=48
- `salesforce_apex_developer_guide_p0220_admin_apex_permissions_001` — salesforce_apex_developer_guide.pdf PDF p220–220: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf#page=220

## q16 — Journey Builder에서 쿠폰 이메일을 열지도 클릭하지도 않은 고객을 선별하려면?

**원문:** How can a marketer identify customers who neither opened nor clicked a voucher email in Journey Builder before sending a follow-up mobile message?

**기본 해결 경로:** 이메일 tracking을 활성화하고 Wait 후 Engagement Split의 No 경로를 사용한다. open과 click을 별도로 확인한다면 두 조건을 순차 확인하여 NOT open AND NOT click을 구성한 뒤 후속 mobile activity로 연결한다.

**근거와 한계:** p350은 Engagement Split 기능, p351은 최소 1시간 Wait와 open/click 기준 및 Yes/No 경로 설정을 설명한다. 질문의 핵심은 선별이므로 일반 mobile/LINE 활동 목록과 LINE 설정 조각은 제외했다. 한 split이 두 조건을 동시에 검사한다고 문서가 명시하지 않으므로 두 조건 구성은 문서에 기초한 구현 추론이다. open 추적의 이미지 차단 등 제약도 고려한다.



**Admin/개발 관점에서 추가로 확인할 항목:**

- **journey_branching**: Wait와 Engagement Split을 사용하고 NOT open AND NOT click의 두 조건을 검증한다.
  - 근거: `mc_journeys_and_automations_p0351_041`, `mc_journeys_and_automations_p0350_040`
- **sql_audience**: 개발 대안으로 _Sent/_Open/_Click을 job/list/batch/subscriber 기준으로 연결해 두 미반응 조건을 검사하고 target DE를 만든다. Job 필터·규모·추적 한계를 확인한다.
  - 근거: `mc_journeys_and_automations_p0102_002`, `mc_journeys_and_automations_p0103_003`, `mc_journeys_and_automations_p0102_admin_sql_nonengagement_001`

현재 정답 문서:

- `mc_journeys_and_automations_p0351_041` — mc_journeys_and_automations.pdf PDF p351–351: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/mc_journeys_and_automations.pdf#page=351
- `mc_journeys_and_automations_p0350_040` — mc_journeys_and_automations.pdf PDF p350–350: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/mc_journeys_and_automations.pdf#page=350
- `mc_journeys_and_automations_p0102_002` — mc_journeys_and_automations.pdf PDF p102–102: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/mc_journeys_and_automations.pdf#page=102
- `mc_journeys_and_automations_p0103_003` — mc_journeys_and_automations.pdf PDF p103–103: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/mc_journeys_and_automations.pdf#page=103
- `mc_journeys_and_automations_p0102_admin_sql_nonengagement_001` — mc_journeys_and_automations.pdf PDF p102–103: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/mc_journeys_and_automations.pdf#page=102

## q17 — 입력을 바꿔 guided process를 테스트하고 실행 경로를 보되 test record를 남기지 않으려면?

**원문:** A sales team uses a guided process that collects deal information and creates an Opportunity with related records. The admin needs to test several user input combinations, observe the execution path taken by the automation, and prevent test records from being permanently saved. Which Salesforce feature would help with this investigation?

**기본 해결 경로:** Flow Builder Debug에서 입력을 바꿔 실행하고 Debug Details로 경로를 확인한다. DB 변경을 남기지 않도록 Run flow in rollback mode를 사용한다.

**근거와 한계:** p238~244의 _012는 일반 Debug·입력·rollback 경고, _013은 screen flow 실행·Debug Details·재실행 예시다. _014의 명시적 rollback checkbox 예시는 template-triggered prompt flow이므로 screen flow의 직접 정답에서 제외했다. 화면을 닫거나 재시작하는 것만으로 기존 변경이 rollback되지는 않는다.



**Admin/개발 관점에서 추가로 확인할 항목:**

- **debug_workflow**: Flow Builder Debug에서 입력·실행 경로·rollback mode를 확인한다.
  - 근거: `extend_click_automate_p0238_012`, `extend_click_automate_p0238_013`
- **execution_context_testing**: 다른 사용자/system context 차이, delete·Wait 동작, Debug와 실제 transaction 차이를 점검하고 sandbox에서 통합 검증한다. rollback이 외부 부작용까지 모두 취소한다고 주장하지 않는다.
  - 근거: `extend_click_automate_p0286_admin_flow_debug_limits_001`

현재 정답 문서:

- `extend_click_automate_p0238_012` — extend_click_automate.pdf PDF p238–244: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/extend_click_automate.pdf#page=238
- `extend_click_automate_p0238_013` — extend_click_automate.pdf PDF p238–244: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/extend_click_automate.pdf#page=238
- `extend_click_automate_p0286_admin_flow_debug_limits_001` — extend_click_automate.pdf PDF p286–286: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/extend_click_automate.pdf#page=286

## q18 — 대량 import·기존 record update·export를 지원하는 도구를 고르려면?

**원문:** A company is preparing a large customer migration and wants to compare Salesforce import options. The team needs a tool that supports high-volume data loads, updates to existing records, and export capability.

**기본 해결 경로:** Data Loader가 요구를 충족한다. Data Import Wizard, Data Loader, dataloader.io를 규모·지원 객체·실행 방식·export 지원으로 비교한다.

**근거와 한계:** p411 비교표는 Data Loader의 insert/update/delete/export와 5,000~5,000,000 record 범위를 제시한다. Data Import Wizard에는 export가 없다. 이는 고정 문서의 비교이며 현재 모든 도구의 최신 한도를 뜻하지 않는다.



**Admin/개발 관점에서 추가로 확인할 항목:**

- **tool_selection**: import/update/export와 규모를 기준으로 Data Loader 등을 비교한다.
  - 근거: `setup_p0411_003`
- **automated_loading**: CSV/field mapping·성공 및 오류 로그·CLI 자동 처리 경로를 검토한다.
  - 근거: `setup_p0439_013`
- **api_permissions**: Data Loader의 object 권한·API Enabled와 hard-delete 사용 시 별도 권한을 확인한다.
  - 근거: `setup_p0444_017`

현재 정답 문서:

- `setup_p0411_003` — setup.pdf PDF p411–411: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/setup.pdf#page=411
- `setup_p0439_013` — setup.pdf PDF p439–439: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/setup.pdf#page=439
- `setup_p0444_017` — setup.pdf PDF p444–444: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/setup.pdf#page=444

## q19 — 소량 Case에서는 되지만 대량 update 때 실패하는 automation을 조사·개선하려면?

**원문:** A Case automation works for a few records but fails when many Cases are updated at once. How should I investigate and redesign the automation so it can handle large batches safely?

**기본 해결 경로:** 오류와 실행 경로를 먼저 확인한다. Apex 경로라면 SOQL/DML을 record 루프 안에서 반복하는지와 transaction limits를 확인하고, 전체 trigger record를 collection/set으로 처리하여 SOQL·DML 호출을 묶는다.

**근거와 한계:** p290은 잘못된 bulk trigger 패턴과 set/IN query 해법, p141~142는 bulk DML과 루프 update의 개선 예시, p353~354는 limit 초과 예외와 한도다. 질문만으로 원인이 Apex라고 확정할 수는 없다. Flow 검증 실패 등도 가능하며 현재 정답은 Apex 원인 경로를 다룬다. schedule-triggered Flow rollback 설명은 Case update의 직접 근거로 채택하지 않았다.



**Admin/개발 관점에서 추가로 확인할 항목:**

- **apex_bulk_path**: Apex trigger/SOQL/DML의 bulkification과 transaction limits를 확인한다.
  - 근거: `salesforce_apex_developer_guide_p0290_017`, `salesforce_apex_developer_guide_p0354_027`, `salesforce_apex_developer_guide_p0141_003`, `salesforce_apex_developer_guide_p0142_004`, `salesforce_apex_developer_guide_p0353_026`
- **flow_bulk_path**: Flow interviews의 같은 요소 단위 bulkification과 transaction 실패·rollback을 확인한다. Apex만 원인으로 가정하지 않는다.
  - 근거: `extend_click_automate_p0068_admin_flow_bulk_001`

현재 정답 문서:

- `salesforce_apex_developer_guide_p0290_017` — salesforce_apex_developer_guide.pdf PDF p290–290: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf#page=290
- `salesforce_apex_developer_guide_p0354_027` — salesforce_apex_developer_guide.pdf PDF p354–354: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf#page=354
- `salesforce_apex_developer_guide_p0141_003` — salesforce_apex_developer_guide.pdf PDF p141–141: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf#page=141
- `salesforce_apex_developer_guide_p0142_004` — salesforce_apex_developer_guide.pdf PDF p142–142: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf#page=142
- `salesforce_apex_developer_guide_p0353_026` — salesforce_apex_developer_guide.pdf PDF p353–353: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf#page=353
- `extend_click_automate_p0068_admin_flow_bulk_001` — extend_click_automate.pdf PDF p68–69: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/extend_click_automate.pdf#page=68

## q20 — Account는 열리지만 일부 record에서 Edit가 없으면 어떤 접근 설정을 보는가?

**원문:** A user can open Account records but the Edit option is unavailable for some customer accounts. What access settings should I investigate?

**기본 해결 경로:** Account object의 Edit 권한과 record별 write access를 함께 확인한다. OWD, 소유권, role hierarchy, sharing rules, team/manual/programmatic grants를 조사한다.

**근거와 한계:** Record Access p6~7은 object/record 접근과 grants, p10은 Account의 read-only/read-write 예시다. Security p17은 object Edit가 있어도 OWD 때문에 편집이 제한될 수 있음을, p46~47은 역할·공유 설정, p59는 Account sharing rule과 access level을 설명한다. 유효한 설정 설명을 포함하여 라벨이 7개가 됐다. record lock이나 UI 구성 등 다른 원인을 이 질문만으로 배제할 수는 없다.



**Admin/개발 관점에서 추가로 확인할 항목:**

- **record_permissions**: object Edit와 OWD·소유권·role·sharing grants를 함께 조사한다.
  - 근거: `salesforce_record_access_under_the_hood_p0006_002`, `salesforce_record_access_under_the_hood_p0007_003`, `salesforce_security_impl_guide_p0017_002`, `salesforce_record_access_under_the_hood_p0010_006`, `salesforce_security_impl_guide_p0046_018`, `salesforce_security_impl_guide_p0047_019`, `salesforce_security_impl_guide_p0059_023`
- **apex_execution_context**: custom Apex 접근은 sharing과 object/FLS 및 user/system mode를 구분한다. API 버전 영향을 확인하며 without sharing을 일반 권한 해결책으로 제시하지 않는다.
  - 근거: `salesforce_apex_developer_guide_p0218_admin_apex_sharing_001`, `salesforce_apex_developer_guide_p0220_admin_apex_permissions_001`

현재 정답 문서:

- `salesforce_record_access_under_the_hood_p0006_002` — salesforce_record_access_under_the_hood.pdf PDF p6–6: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_record_access_under_the_hood.pdf#page=6
- `salesforce_record_access_under_the_hood_p0007_003` — salesforce_record_access_under_the_hood.pdf PDF p7–7: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_record_access_under_the_hood.pdf#page=7
- `salesforce_security_impl_guide_p0017_002` — salesforce_security_impl_guide.pdf PDF p17–17: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf#page=17
- `salesforce_record_access_under_the_hood_p0010_006` — salesforce_record_access_under_the_hood.pdf PDF p10–10: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_record_access_under_the_hood.pdf#page=10
- `salesforce_security_impl_guide_p0046_018` — salesforce_security_impl_guide.pdf PDF p46–46: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf#page=46
- `salesforce_security_impl_guide_p0047_019` — salesforce_security_impl_guide.pdf PDF p47–47: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf#page=47
- `salesforce_security_impl_guide_p0059_023` — salesforce_security_impl_guide.pdf PDF p59–59: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf#page=59
- `salesforce_apex_developer_guide_p0218_admin_apex_sharing_001` — salesforce_apex_developer_guide.pdf PDF p218–219: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf#page=218
- `salesforce_apex_developer_guide_p0220_admin_apex_permissions_001` — salesforce_apex_developer_guide.pdf PDF p220–220: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf#page=220
