# Crawl Agent (크롤링·영역 추출 에이전트)

**역할**: Qoo10 상품 URL 또는 Shop URL에서 페이지를 수집하고, 영역별로 데이터를 추출하여 구조화된 `product_data` 또는 `shop_data`를 출력한다. Orchestration Agent의 1단계로 호출된다.

**코드 위치**: `api/services/crawler.py` (상품), `api/services/crawler_shop.py` (Shop), `api/services/manual_crawler.py` (메뉴얼), `api/main.py` 내 `perform_analysis` 1단계.

---

## 1. 책임

- **상품 페이지**: `Qoo10Crawler.crawl_product(url)` — 상품명, 가격, 이미지, 설명, 리뷰, 페이지 구조 등 추출. `use_playwright=True` 시 동적 콘텐츠 보강.
- **Shop 페이지**: `Qoo10Crawler.crawl_shop(url)` — Shop명, 레벨, 상품 수, 팔로워 수, 쿠폰·카테고리·페이지 구조 등 추출.
- **메뉴얼(선택)**: `Qoo10ManualCrawler.crawl_all()` — 큐텐 대학 한국어 메인·단계별 교육(초급) 페이지에서 섹션·링크 수집. `run_manual_pipeline.py` 및 `test_data_pipeline_full.py --manual`에서 사용.
- **URL 정규화**: 상품 URL은 `_normalize_product_url`로 표준 형식 통일.
- **오류 신고 연동**: `ErrorReportingService`를 주입받아 우선 크롤링 필드 목록·Chunk 정보를 반영한 추출 수행.
- **데이터 검증**: 크롤링 결과가 비어 있으면 예외 발생; Orchestrator가 실패로 처리하고 `PipelineMonitor.record_stage(..., stage="crawling", status="failure")` 기록.

---

## 2. 입출력

| 구분 | 내용 |
|------|------|
| **입력** | `url` (str), `url_type` ("product" \| "shop"), (선택) `error_reporting_service` |
| **출력** | `product_data` 또는 `shop_data` (dict). 필수 필드: 상품 시 product_name 또는 url 대체, shop 시 shop_name 등. 모든 출력에 `crawled_with` 포함. |
| **실패 시** | 예외 발생 → Orchestrator가 `status: "failed"`, `PipelineMonitor.record_stage(..., stage="crawling", status="failure")` |

---

## 3. 데이터 흐름 (Orchestrator 관점)

```
Orchestrator: perform_analysis(analysis_id, url, url_type)
    → url_type 에 따라 crawl_product(url) | crawl_shop(url) 호출
    → product_data | shop_data 반환
    → 다음 단계: Analysis Agent 입력으로 전달
```

---

## 4. 데이터 스키마 (요약)

- **product_data**: `product_name`, `product_code`, `url`, `price`, `images`, `description`, `reviews`, `page_structure`, `crawled_with`(playwright/qoo10_api 등) 등.
- **shop_data**: `shop_name`, `shop_id`, `shop_level`, `product_count`, `follower_count`, `page_structure`, `crawled_with` 등.
- **page_structure**: 요소 단위 분석용 `elements_detail` (element_id, name_ko, present, classes, source).

---

## 5. 파이프라인 위치

- **이전 단계**: 없음 (진입 단계).
- **다음 단계**: Analysis Agent가 `product_data` / `shop_data`를 입력으로 사용.
- **PipelineMonitor stage**: `crawling`.

---

## 6. 확장 포인트

- **Qoo10 API**: `Qoo10APIService` 연동 시 API 우선·크롤러 폴백으로 정규화된 데이터 반환.
- **메뉴얼 파이프라인**: 상품/Shop과 별도로 `Qoo10ManualCrawler`가 큐텐 대학 한국어 페이지를 수집하며, 동일 수집→검증 패턴으로 Manual Validator와 연결됨.

---

## 7. 의존성

- Playwright / httpx 등 HTTP·브라우저 도구
- `CrawlerDatabase` (캐시·통계)
- `ErrorReportingService` (우선 필드·Chunk)
- (선택) `Qoo10APIService`, `Qoo10APISchema`

---

**문서 버전**: 1.1  
**최종 수정**: 2026-02-28
