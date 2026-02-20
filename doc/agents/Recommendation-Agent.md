# Recommendation Agent (개선 제안 에이전트)

**역할**: 상품/Shop 데이터와 분석 결과를 바탕으로 매출 강화를 위한 개선 제안(recommendations) 리스트를 생성한다. 메뉴얼 지식(`doc/Qoo10_큐텐대학_한국어_메뉴얼.md`)을 우선 로드하여 `manual_reference`를 부여한다. Orchestration Agent의 3단계로 호출된다.

**코드 위치**: `api/services/recommender.py` (SalesEnhancementRecommender), `api/main.py` 내 `perform_analysis` 3단계.

---

## 1. 책임

- **상품 추천**: `SalesEnhancementRecommender.generate_recommendations(product_data, analysis_result, page_structure=None)`.
- **Shop 추천**: `SalesEnhancementRecommender.generate_shop_recommendations(shop_data, analysis_result)`.
- **메뉴얼 연동**: `_load_manual_knowledge()` — `doc/Qoo10_큐텐대학_한국어_메뉴얼.md` 존재 시 파싱하여 `manual_sections`·`manual_items` 반영; 없으면 기본 지식 사용.
- **AI 추천**: Gemini/OpenAI 사용 가능 시 `generate_recommendations_with_ai` 호출 후 기본(메뉴얼 기반) 추천과 병합.
- **타임아웃**: Orchestrator에서 최대 30초 제한; 초과 시 빈 리스트로 계속 진행.
- **실패 허용**: 예외 시 `recommendations=[]` 로 두고 파이프라인은 계속(추천만 누락). `PipelineMonitor.record_stage(..., stage="generating_recommendations", status="failure")` 기록.

---

## 2. 입출력

| 구분 | 내용 |
|------|------|
| **입력** | `product_data` 또는 `shop_data`, `analysis_result`, (선택) `page_structure` |
| **출력** | `recommendations` (list of dict). 항목별 `category`, `priority`, `title`, `description`, `action_items`, `manual_reference` 등. |
| **실패 시** | 빈 리스트 `[]`, `PipelineMonitor.record_stage(..., stage="generating_recommendations", status="failure")` |

---

## 3. 데이터 흐름 (Orchestrator 관점)

```
Orchestrator: product_data | shop_data, analysis_result 확정 후
    → SalesEnhancementRecommender.generate_recommendations(...) | generate_shop_recommendations(...)
    → recommendations 반환
    → final_result.recommendations 에 포함 (Report & Output 단계)
```

---

## 4. 파이프라인 위치

- **이전 단계**: Analysis Agent.
- **다음 단계**: Report & Output Agent가 `final_result.recommendations`에 포함; Validation Agent는 추천 결과를 직접 사용하지 않음.
- **PipelineMonitor stage**: `generating_recommendations`.

---

## 5. 동시 실행

- Checklist Agent와 독립: 같은 `product_data`, `analysis_result`만 있으면 동시 실행 가능. Orchestrator에서 `asyncio.gather`로 병렬화 권장.

---

## 6. 의존성

- SalesEnhancementRecommender (메뉴얼 파일 경로: `doc/Qoo10_큐텐대학_한국어_메뉴얼.md`)
- (선택) ai_provider (Gemini/OpenAI) — 추천 생성 강화

---

**문서 버전**: 1.1  
**최종 수정**: 2026-02-28
