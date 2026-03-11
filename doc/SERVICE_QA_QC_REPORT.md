# 서비스 전체 진단 및 QA/QC 리포트

**진행 일자**: 2026-03-11  
**대상**: 전체 에이전트 파이프라인 (Orchestration, Crawl, Analysis, Recommendation, Checklist, Validation, Report-Output)  
**참조**: [agents/README.md](agents/README.md), [DATA_PIPELINE_TEST_SUMMARY.md](DATA_PIPELINE_TEST_SUMMARY.md)

---

## 1. 진단 요약

| 구분 | 결과 | 비고 |
|------|------|------|
| **API·핵심 서비스 로드** | ✓ 통과 | main, Crawler, ProductAnalyzer, Recommender, DataValidator, ReportGenerator import 정상 |
| **프론트엔드 빌드** | ✓ 통과 | `tsc && vite build` 성공 (110 modules) |
| **린트** | ✓ 이슈 없음 | 대상 파일 기준 |
| **상품 파이프라인** | ✓ 통과 | g/1093098159 기준 Crawl→Analysis→Recommendation→Checklist→Validation→Report 정상 (이미지·리뷰 수 반영) |
| **Shop 파이프라인** | ✓ 통과 | whippedofficial 기준 전체 단계 완료 (coupons 빈 필드·기대값 차이는 데이터 변동/선택자 이슈) |

---

## 2. 에이전트별 점검

| Agent | 담당 코드 | 점검 항목 | 상태 |
|-------|-----------|-----------|------|
| **Orchestration** | main.py | URL 검증, analysis_id, 단계 조율 | ✓ |
| **Crawl** | crawler.py, crawler_shop.py | product/shop 크롤, 이미지(썸네일·상세·alt), 리뷰 수(쉼표), Shop product_count/shop_level | ✓ |
| **Analysis** | analyzer.py, shop_analyzer.py | overall_score, image_count(detail+item_goods) | ✓ |
| **Recommendation** | recommender.py | priority 정렬(medium-low 등 복합값 처리) | ✓ 수정 반영 |
| **Checklist** | checklist_evaluator.py | product/shop 체크리스트, overall_completion | ✓ |
| **Validation** | data_validator.py | product_data/shop_data 검증, validation_score | ✓ |
| **Report-Output** | report_generator.py | Markdown/PDF/Excel, 저장·다운로드 | ✓ |

---

## 3. 알려진 이슈 및 제한

- **Shop 기대값 변동**: follower_count, product_count는 페이지/시간에 따라 달라질 수 있음. 테스트 기대값은 참고용.
- **coupons 빈 필드**: Shop 쿠폰 영역 선택자/정규식 점검 권장 (`crawler_shop._extract_shop_coupons`).
- **상품 파이프라인 실행 시간**: Playwright 사용 시 상품 1건 기준 약 2분 내외 소요 가능.
- **QC 상세**: 상품 페이지(g/1093098159) 요소 단위 QC는 [tests/docs/QC_QA_REPORT_1093098159.md](../tests/docs/QC_QA_REPORT_1093098159.md) 참고.

---

## 4. 실행 방법 (재현)

```bash
# 상품 파이프라인
python tests/scripts/test_data_pipeline_full.py "https://www.qoo10.jp/g/1093098159"

# Shop 파이프라인
python tests/scripts/test_data_pipeline_full.py "https://www.qoo10.jp/shop/whippedofficial"

# 프론트엔드 빌드
cd frontend && npm run build

# API 서버 (선택)
cd api && uvicorn main:app --reload
```

---

**문서 버전**: 1.0  
**최종 수정**: 2026-03-11
