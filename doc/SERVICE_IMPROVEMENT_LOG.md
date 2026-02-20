# 서비스 개선 로그 (Service Improvement Log)

Qoo10 AI Agent 파이프라인 및 에이전트별 기능·성능 고도화 내역을 기록합니다.  
QC/QA 리포트와 연동하여 누락·보완·오류 데이터 개선을 반영합니다.

---

## 2026-02-20

### QC/QA 대상
- **페이지**: https://www.qoo10.jp/g/1093098159 (ホイップド ヴィーガンパックスクラブ)
- **리포트**: [doc/QC_QA_REPORT_1093098159.md](QC_QA_REPORT_1093098159.md)

### 적용된 개선

| 구분 | 내용 | 파일/위치 |
|------|------|------------|
| **기능** | Playwright 상품 크롤 시 정규화 URL(`gmkt.inc/Goods/Goods.aspx?goodscode=...`) 접속 실패(ERR_CONNECTION_RESET 등) 시 **원본 URL**(`/g/1093098159`)로 재시도 | `api/services/crawler.py` — `crawl_product_with_playwright()` |
| **동작** | `effective_url` 도입: 실제 로드에 성공한 URL을 이후 추출·저장에 사용 | 동일 |

### 적용된 개선 (추가)
| 구분 | 내용 | 파일/위치 |
|------|------|------------|
| **기능** | `elements_detail` 없을 때 `elements_validation` 빈 배열만 반환하지 않고, `elements_validation_note`에 "요소 미수집" 안내 메시지 설정 | `api/services/data_validator.py` |

### 권장 후속 작업 (미적용)
- Crawl: 상품 옵션·재고·Q&A 건수·배송국/배송지역 스키마 및 추출 로직 추가
- Manual: `test_data_pipeline_full.py --manual` 정기 실행 또는 CI 메뉴얼 검증 단계

---

## 이전 개선 (참고)

- **데이터 파이프라인 테스트 요약**: [DATA_PIPELINE_TEST_SUMMARY.md](DATA_PIPELINE_TEST_SUMMARY.md) — review_count 쉼표 처리, 이미지 정밀 크롤링, Shop product_count/shop_level 등
- **크롤러 개선**: [CRAWLER_IMPROVEMENTS.md](CRAWLER_IMPROVEMENTS.md), [SHOP_CRAWLER_IMPROVEMENTS.md](SHOP_CRAWLER_IMPROVEMENTS.md)

---

**최종 수정**: 2026-02-20
