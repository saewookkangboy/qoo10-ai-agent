# Manual Agent (메뉴얼 수집·검증 에이전트)

**역할**: Qoo10 큐텐 대학 한국어 메뉴얼을 최신 사이트 기준으로 수집하고, 현재 메뉴얼 마크다운 파일과 비교하여 누락·추가·오래된 항목을 정밀 분석한다. 상품/Shop 분석 파이프라인과 독립적으로 실행되며, 동일한 조율 패턴(수집 → 검증 → 결과 저장)을 따른다.

**코드 위치**: `api/services/manual_crawler.py` (Qoo10ManualCrawler), `api/services/manual_validator.py` (load_and_validate, validate_manual_vs_crawled), `api/run_manual_pipeline.py`, `api/test_data_pipeline_full.py` (--manual 옵션).

---

## 1. 책임

- **수집 (Crawl)**: `Qoo10ManualCrawler.crawl_all()` — `article-university.qoo10.jp/qoo10-selling-tips_kor`(유형별 판매 노하우) 및 `archive/category/단계별 교육 (초급)` 페이지에서 섹션·링크·글 목록 수집. httpx + BeautifulSoup 사용.
- **검증 (Validation)**: `manual_validator.load_and_validate(crawled, manual_path)` — `doc/Qoo10_큐텐대학_한국어_메뉴얼.md` 파싱 후 크롤 결과와 비교.
- **누락 분석**: `validate_manual_vs_crawled(manual_content, crawled)` — missing_sections, missing_links, missing_in_manual_items, extra_in_manual, coverage_score, suggestions 산출.
- **실행 진입점**: `run_manual_pipeline.py` (메뉴얼 전용), `test_data_pipeline_full.py --manual` (상품/Shop 파이프라인과 함께 실행 시 결과에 `manual_missing_analysis` 포함).

---

## 2. 입출력

| 구분 | 내용 |
|------|------|
| **입력** | (수집) 고정 URL: qoo10-selling-tips_kor, 단계별 교육 초급 카테고리. (검증) 크롤 결과 + 메뉴얼 MD 파일 경로. |
| **출력** | `crawled`: topic(sections, all_links), beginner_category(articles). `validation`: manual_parsed, missing_sections, missing_links, missing_in_manual_items, extra_in_manual, coverage_score, suggestions, summary. |
| **산출물** | `manual_pipeline_result.json` (run_manual_pipeline.py), `test_data_pipeline_full_result.manual_missing_analysis` (--manual 시). |

---

## 3. 데이터 흐름

```
run_manual_pipeline() | test_data_pipeline_full --manual
    → Qoo10ManualCrawler.crawl_all()
        → crawl_topic_page() → topic (sections, all_links)
        → crawl_beginner_category() → beginner_category (articles)
    → load_and_validate(crawled, manual_path)
        → parse_manual_markdown(content) → sections, all_더보기_urls, toc_titles
        → validate_manual_vs_crawled(manual_content, crawled)
    → validation (missing_sections, missing_links, missing_in_manual_items, ...), coverage_score, suggestions
    → JSON 저장 / result.validation; --manual 시 result.manual_missing_analysis = validation
```

---

## 4. 파이프라인 위치

- **Orchestration과의 관계**: 상품/Shop 파이프라인의 일부가 아님. 별도 스크립트(`run_manual_pipeline.py`) 또는 테스트 옵션(`--manual`)으로 호출.
- **다음 단계**: 없음(독립 파이프라인). 사용자가 suggestions에 따라 `doc/Qoo10_큐텐대학_한국어_메뉴얼.md`를 수동 보완하거나, 크롤러/검증기 규칙을 조정.

---

## 5. 확장 포인트

- **Playwright**: 동적 로딩 페이지 대응 시 `manual_crawler`에 Playwright 폴백 추가 가능.
- **자동 반영**: missing_links·missing_in_manual_items를 기반으로 메뉴얼 MD에 **[더보기](url)** 자동 삽입 스크립트 확장 가능.
- **Recommender 연동**: `doc/Qoo10_큐텐대학_한국어_메뉴얼.md`는 Recommendation Agent의 `_load_manual_knowledge()`에서 로드되어 `manual_reference`에 반영됨.

---

## 6. 의존성

- Qoo10ManualCrawler (httpx, BeautifulSoup)
- manual_validator (Path, re; 메뉴얼 파일 경로: doc/Qoo10_큐텐대학_한국어_메뉴얼.md)

---

**문서 버전**: 1.0  
**최종 수정**: 2026-02-28
