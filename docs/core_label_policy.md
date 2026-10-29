# 핵심 정답만 채점하는 기준

현재 scope: `admin_agent_core_v1`. 20개 질문과 594개 코퍼스 문서는 그대로 두고, 넓은 관련 문서 170개 중 **핵심 정답 60개만** gold로 유지했다. 99개는 보조 참고, 11개는 탐색/See Also 블록으로 분리했다. 파일은 모두 코퍼스에 남아 있다.

## 포함 기준

- 질문에 명시된 목표를 해결하는 구체적인 방법 또는 설정 절차를 설명한다.
- 여러 청크를 조합해야 하는 경우, 목표 달성에 필요한 핵심 구현 단계를 직접 설명한다.
- troubleshooting 질문이면 제시된 증상의 원인이나 실제 조사 방법을 직접 설명한다.
- Apex·Flow·SQL 등 다른 구현 방식도 질문에 직접 답하면 유지한다. 사용자/admin/developer라는 직무만으로 모든 기술 문서가 정답이 되지는 않는다.

## 제외 기준

일반 인증, 일반 배포, migration, 관련 기능 목록, 질문이 요구하지 않는 권한·로그·실행 순서, 탐색 경로와 참고 링크는 gold가 아니다. 단, q19처럼 질문이 장애 **조사**를 직접 요구하면 실제 trace 설정과 limit 로그 해석은 핵심이다. 임의로 라벨을 다섯 개 이하로 줄이거나 검색 순위가 높은 문서만 선택하지 않았다.

| 예시 | 핵심 gold | 보조/제외 |
| --- | --- | --- |
| q02 Account 병합 | Lightning/Classic 병합 절차와 실제 Apex merge 구현 | 일반 object CRUD 명세 |
| q08 승인된 WhatsApp template 전송 | 개인화와 Journey Builder 전송 설정 | OAuth와 send/delivery 이벤트 |
| q09 Apex에서 Profile update 가능 여부 | Apex DML 미지원 객체 목록 | 일반 Metadata API 배포 |
| q12 관련 Account 갱신 | after trigger/after-save Flow와 Update Records 구현 | 일반 실행 순서, 반대로 Case.AccountId를 바꾸는 예제 |
| q16 미오픈·미클릭 고객 선별 | Engagement Split 설정과 두 부정 조건을 검사하는 실제 SQL | 일반 mobile activity 목록 |
| q18 대량 import/update/export 도구 선택 | 도구 비교와 Data Loader의 해당 기능 | import 권한 설정 |
| q19 소량 성공·대량 실패 조사와 개선 | bulk SOQL/DML/Flow 패턴, trace 설정·limit 로그 해석 | 일반 실행 순서·관련 없는 이벤트/참고 링크 |

## 데이터와 평가

q01의 정답 근거는 중복 경고의 발생 조건과 기존 Account·Lead 값, 필드 매핑 및 matching/duplicate rules의 관계를 설명한다. 공식 문서의 수정 절차는 실행 권한이 아니다. Recall/MRR는 검색 관련성 지표이며 답변의 행동 제약 준수 여부를 평가하지 않는다.

- `relevant_doc_ids`: core Recall/MRR에 사용하는 유일한 정답 목록.
- `supplementary_doc_ids`: 설명이나 추가 조사에 유용할 수 있는 non-gold 문서.
- `excluded_doc_ids`: 이전 라벨에 잘못 포함됐던 탐색/See Also 블록.
- `core_label_text_sha256`: 원문이 바뀌면 라벨 재검토를 요구하는 hash.

직접 핵심 근거가 여러 개일 수 있다. q19는 7개, q20은 6개라 document Recall@5에 상한이 남는다. 하나의 청크가 완전한 답변을 보장한다는 의미도 아니며, q12는 정확한 Case→Account 완성 코드 예제가 아직 없다. 검색 평가를 생성 답변 정확도와 동일시하지 않는다.

검토 ID와 이유는 `data/raw/core_labels.json`, 전후 변경은 `results/core_label_review.json`, 질문별 답변은 `docs/query_answers.md`에 있다. 이전 광범위 라벨과 결과는 `results/before_core_labels/`에 보존했다.
