# Analysis Agent (분석·점수 에이전트)

**역할**: 크롤링된 상품/Shop 데이터를 받아 이미지·설명·가격·리뷰·SEO·페이지 구조 등을 분석하고, 종합 점수(overall_score) 및 섹션별 점수·인사이트를 산출한다. 필요 시 AI(Gemini/OpenAI)로 분석을 강화한다. Orchestration Agent의 2단계로 호출된다.

**코드 위치**: `api/services/analyzer.py` (ProductAnalyzer), `api/services/shop_analyzer.py` (ShopAnalyzer), `api/services/ai_provider.py`, `api/main.py` 내 `perform_analysis` 2단계.

---

## 1. 책임

- **상품 분석**: `ProductAnalyzer.analyze(product_data)` → 이미지/설명/가격/리뷰/SEO/페이지 구조 분석, `overall_score` 및 섹션별 점수.
- **Shop 분석**: `ShopAnalyzer.analyze(shop_data, checklist_result=None)` → Shop 정보·카테고리·레벨·특화·체크리스트 기여도 등, `overall_score`.
- **AI 강화**: `get_ai_service_for_analysis().enhance_analysis_with_ai(product_data, analysis_result)` — Gemini 우선, 없으면 OpenAI 폴백.
- **결과 정규화**: `overall_score` 없으면 0으로 설정; 빈 결과 시 기본 구조 반환.
- **실패 시**: Orchestrator가 `status: "failed"`, `PipelineMonitor.record_stage(..., stage="analyzing", status="failure")` 기록.

---

## 2. 입출력

| 구분 | 내용 |
|------|------|
| **입력** | `product_data` 또는 `shop_data` (Crawl Agent 출력) |
| **출력** | `analysis_result`: 상품 시 `{"product_analysis": {...}, "overall_score": N}`, Shop 시 `{"shop_analysis": {...}, "overall_score": N}`. 내부에 섹션별 점수·인사이트·`page_structure_analysis.elements` 포함. |
| **실패 시** | 예외 발생 → Orchestrator가 `status: "failed"`, analyzing 단계 failure 기록. |

---

## 3. 데이터 흐름 (Orchestrator 관점)

```
Orchestrator: product_data | shop_data 수신
    → url_type 에 따라 ProductAnalyzer.analyze(...) | ShopAnalyzer.analyze(...) 호출
    → (선택) AI enhance
    → analysis_result 반환
    → 다음 단계: Recommendation Agent, Checklist Agent 입력으로 전달
```

---

## 4. 데이터 스키마 (요약)

- **product_analysis**: `overall_score`, `image_analysis`, `description_analysis`, `price_analysis`, `review_analysis`, `seo_analysis`, `page_structure_analysis`(요소별 score, present, quality, recommendation, kind) 등.
- **shop_analysis**: `overall_score`, `shop_info`, `category_analysis`, `level_analysis`, `shop_specialty`, `checklist_contribution` 등.

---

## 5. 파이프라인 위치

- **이전 단계**: Crawl Agent.
- **다음 단계**: Recommendation Agent, Checklist Agent(및 선택적 Competitor Agent)가 `analysis_result`를 사용.
- **PipelineMonitor stage**: `analyzing`.

---

## 6. 확장 포인트

- **SEO/AIO/GEO**: 별도 라우트에서 Crawl 공유 후 Analysis만 SEO/AIO/GEO 전용 서비스로 분기 가능.
- **요소 단위**: `page_structure_analysis.elements`는 Recommendation·Checklist·Validation·Report에서 동일 `element_id` 체계로 사용.

---

## 7. 의존성

- ProductAnalyzer, ShopAnalyzer
- ai_provider (Gemini/OpenAI), ENHANCED_ANALYSIS_METRICS·METRICS_CODE_MAPPING 등 문서 기준

---

**문서 버전**: 1.1  
**최종 수정**: 2026-02-28
