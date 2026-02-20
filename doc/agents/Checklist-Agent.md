# Checklist Agent (체크리스트 평가 에이전트)

**역할**: 상품/Shop 데이터와 분석 결과를 기준으로 판매 준비·판매 개선·광고 등 체크리스트 항목을 평가하고, 완료율(overall_completion) 및 항목별 체크 상태를 반환한다. 큐텐 대학 메뉴얼 기반 체크리스트 정의를 사용한다. Orchestration Agent의 4단계로 호출된다.

**코드 위치**: `api/services/checklist_evaluator.py` (ChecklistEvaluator), `api/main.py` 내 `perform_analysis` 4단계.

---

## 1. 책임

- **상품 체크리스트**: `ChecklistEvaluator.evaluate_checklist(product_data=..., analysis_result=...)`.
- **Shop 체크리스트**: `evaluate_checklist(shop_data=..., analysis_result=..., page_structure=...)` — Shop 페이지 구조 전달.
- **메뉴얼 기반 항목**: `_load_checklist_definitions()` — 판매 준비·매출 증대·광고·고객 관리 등 카테고리별 항목 정의. `manual_check` 플래그로 수동 확인 항목 구분.
- **점수 반영(Shop)**: 체크리스트 결과를 반영해 `ShopAnalyzer.analyze(shop_data, checklist_result=...)` 재호출하여 overall_score 갱신 가능.
- **타임아웃**: Orchestrator에서 최대 10초(테스트)/5초; 초과 시 `checklist_result=None`, 파이프라인 계속.
- **실패 허용**: 예외 시 `checklist_result=None`, `PipelineMonitor.record_stage(..., stage="evaluating_checklist", status="failure")` 기록.

---

## 2. 입출력

| 구분 | 내용 |
|------|------|
| **입력** | `product_data` 또는 `shop_data`, `analysis_result`, (Shop 시) `page_structure` |
| **출력** | `checklist_result`: `overall_completion`, 카테고리별 항목·체크 상태, `element_id`·`element_status` 매핑 등. |
| **실패 시** | `None`, `PipelineMonitor.record_stage(..., stage="evaluating_checklist", status="failure")` |

---

## 3. 데이터 흐름 (Orchestrator 관점)

```
Orchestrator: product_data | shop_data, analysis_result 확정 후
    → ChecklistEvaluator.evaluate_checklist(...)
    → checklist_result 반환
    → Validation Agent 입력, final_result.checklist 에 포함 (Report & Output 단계)
```

---

## 4. 파이프라인 위치

- **이전 단계**: Analysis Agent.
- **다음 단계**: Validation Agent가 `checklist_result`를 참고; Report & Output이 `final_result.checklist`에 포함.
- **PipelineMonitor stage**: `evaluating_checklist`.

---

## 5. 동시 실행

- Recommendation Agent와 동일 입력(`product_data`/`shop_data`, `analysis_result`)으로 병렬 실행 가능.

---

## 6. 의존성

- ChecklistEvaluator (체크리스트 정의: `.project-data/checklists.json` 또는 코드 내 정의)
- product_data / shop_data 의 page_structure (요소 단위 매핑 시)

---

**문서 버전**: 1.1  
**최종 수정**: 2026-02-28
