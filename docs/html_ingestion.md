# 공식 HTML 문서 수집과 혼합 코퍼스

2026-10-23. 사용자가 제공한 공식 URL 25개 중 24개에서 본문을 확보했다. HTML 청크 240개와 기존 PDF 청크 354개를 합쳐 총 594개를 사용한다. 원본 URL 목록은 `data/raw/html_sources.json`에 있다.

## 수집 경로

1. URL에서 `utm_*`와 fragment를 제거하고 중복을 검사한다. Help의 article `id`, `type`, `language`는 문서 식별에 필요하므로 보존한다.
2. 일반 Developer 문서는 HTTP로 HTML을 내려받는다. Atlas 문서는 화면이 호출하는 공식 `get_document` / `get_document_content` 엔드포인트에서 article HTML과 문서 버전을 얻는다.
3. Help는 정적 HTML이 앱 껍데기인 경우 Edge/Chromium으로 렌더링한다. Salesforce의 component DOM을 통과하는 Playwright locator로 본문 준비를 기다린다.
4. `#content`, Knowledge article container, `article`, `main` 등에서 실제 본문을 선택한다. 메뉴·헤더·푸터·사이드바·script·style·cookie/feedback UI를 제외한다. 충분한 본문이나 제목이 없는 응답은 실패로 기록한다.
5. 제목 계층으로 section을 나누고 표는 Markdown 행으로, code/pre는 줄바꿈과 문장부호를 보존해 추출한다. 긴 표는 헤더를 반복한다.
6. 긴 section은 기본 220개 영숫자 토큰 이하로 나눈다. 큰 block 안에서는 32개 토큰을 겹치며, 일반 paragraph는 경계에서 묶는다. 이는 모델 tokenizer의 정확한 220개 subword 토큰을 뜻하지 않는다. 매우 긴 코드나 표의 한 행은 여러 chunk로 나뉠 수 있다.
7. PDF와 HTML 문서를 합친다. BM25와 dense는 같은 문서 목록을 사용하며 HTML의 title·section·본문을 검색 입력에 포함한다.

## metadata와 재현성

새 청크에는 `doc_id`, `parent_id`, `title`, `url`, `section`, `section_index`, `chunk_index`, `document_type`, `source_file`, `product_area`, `fetched_at`, `source_sha256`, `content_sha256`, `extraction_method`, `source_version`이 있다. `source_version`은 공식 API가 제공할 때만 기록하며 모르는 버전을 추정하지 않는다.

- raw HTTP HTML·렌더링 HTML·로컬 처리 cache: `data/raw/html/` (git 제외)
- 정제된 본문/section snapshot: `data/processed/html_pages.jsonl`
- HTML 검색 청크: `data/processed/html_documents.jsonl`
- 최종 PDF+HTML 검색 코퍼스: `data/processed/documents.jsonl`
- URL별 성공/실패·수집 경로·문서 버전·청크 수: `data/processed/html_ingestion_report.json`

동일한 URL·section 순서·본문은 같은 ID를 생성한다. 페이지 구조가 바뀌면 section ID가 바뀔 수 있으므로 `--refresh` 후에는 라벨을 재검토해야 한다. `--offline`은 저장된 정제 snapshot에서 동일 청크를 재생성한다. 본문 텍스트가 같아도 다른 객체의 Supported Calls 등 문맥이 다른 페이지는 별도 문서로 유지한다. 같은 canonical URL을 두 번 수집하지 않는다.

## 실패한 URL과 근거 범위

`Transactional Messaging — OTT API` root는 HTML 앱 껍데기였고, 해당 페이지 설정의 공식 OpenAPI JSON 및 AMF JSON 주소가 모두 404였다. 이 페이지는 검색에 넣지 않았다. 성공한 WhatsApp send/delivery 이벤트 문서와 OAuth 문서가 실제 전송 endpoint/payload 명세를 대신한다고 판단하지 않는다. 오류 내용과 원본 링크는 수집 보고서에 보존한다.

Case의 Contact 변경 시 Case.AccountId를 조정하는 Knowledge 예제는 수집했다. 그러나 q12는 **관련 Account record의 필드 갱신**을 묻기 때문에 이 예제를 q12 정답으로 지정하지 않았다.

## 정답과 평가

`query_hints`는 사용자가 제안한 문서 용도이며 자동 정답이 아니다. 최초의 넓은 근거 검토는 `data/raw/html_label_rules.json`과 `results/html_label_review.json`에 보존한다. 현재는 사용자 요청에 따라 **핵심 정답만** 채점한다. 현재 적용기는 `scripts/apply_core_labels.py`, 명시적 청크 ID·본문 hash·판정 이유는 `data/raw/core_labels.json`에 있다. 일반 인증·배포·실행 순서 등은 `supplementary_doc_ids`로 보존하고, 탐색/See Also 블록은 `excluded_doc_ids`로 분리한다. 이 두 필드는 점수를 받지 않는다.

본문이 충분히 수집되었다는 것과 질문에 직접 답한다는 것은 별도 판정이다. 현재 평가는 core Recall@5와 MRR@5를 사용하며, 넓은 근거 항목을 세던 Aspect recall은 이전 버전으로 보관했다. 핵심 구현 단계나 직접적인 대안은 여러 문서일 수 있으며 라벨 수를 5개 이하로 강제하지 않는다. 완전한 비정답 전수 annotation이나 생성 답변 정확도 검증을 보장하지는 않는다.

## 실행

처음 수집하거나 실패 페이지를 재시도한다.

```powershell
python src/build_html_corpus.py --render
```

Windows에서는 설치된 Edge를 사용한다. 다른 환경에서는 `python -m playwright install chromium`으로 browser를 준비한 뒤 실행한다. `--browser-channel`로 사용할 browser를 지정할 수 있다. `--refresh`는 성공 cache도 새로 수집한다.

저장된 snapshot으로 재현한다.

```powershell
python src/build_html_corpus.py --offline
python src/build_corpus.py
python scripts/apply_core_labels.py
python run_eval.py
python scripts/summarize_core_results.py
```

PDF 재빌드에는 기존 PDF cache 또는 `source_urls.txt`의 원본이 필요하다. 검색 평가만 재현할 때는 체크인된 `documents.jsonl`과 `queries.jsonl`을 이용해 `python run_eval.py`를 실행하면 된다. 혼합 코퍼스는 기존 과제의 200–500문서 범위를 넘어섰으며 현재 corpus builder의 기본 상한은 2,000이다.

핵심 라벨만 바뀌고 corpus와 query 문구가 동일한 경우에만 `python scripts/summarize_core_results.py --rescore-saved`로 저장된 순위를 재채점할 수 있다. 이 경우 latency는 이전 측정치를 재사용하며 새로 측정했다고 표기하지 않는다. 원문이 변경되면 core hash 검증이 실패하므로 의미적 라벨 검토가 선행되어야 한다.
