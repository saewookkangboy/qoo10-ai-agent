# Validation Agent (검증·동기화 에이전트)

**역할**: 크롤링 결과(product_data/shop_data)와 분석·리포트 내용(analysis_result, checklist_result) 간 일치 여부를 검증하고, 불일치·누락을 보정하여 검증 점수 및 보정 필드 목록을 반환한다. API 데이터가 있으면 우선 사용하여 검증한다. Orchestration Agent의 5단계로 호출된다.

**코드 위치**: `api/services/data_validator.py` (DataValidator), `api/main.py` 내 `perform_analysis` 5단계.

---

## 1. 책임

- **검증**: `DataValidator.validate_crawler_vs_report(product_data=..., analysis_result=..., checklist_result=..., api_data=...)`. `shop_data`만으로도 호출 가능.
- **보정**: 크롤러(또는 API 정규화 결과) 기준으로 분석 결과 동기화; `corrected_fields` 목록 반환.
- **API 연동**: `api_data` 제공 시 우선 참조 데이터로 사용; 없으면 product_data/shop_data 사용. `Qoo10APISchema.normalize_crawler_data_to_api_structure` 로 정규화 후 비교 가능.
- **요소 단위 검증**: `elements_validation` — 크롤러의 `page_structure.elements_detail`과 분석의 `page_structure_analysis.elements` 비교.
- **실패 허용**: 예외 시 `validation_result=None`, 파이프라인은 계속; Report에는 validation 누락. `PipelineMonitor.record_stage(..., stage="validating", status="failure")` 기록.

---

## 2. 입출력

| 구분 | 내용 |
|------|------|
| **입력** | `product_data` 또는 `shop_data`, `analysis_result`, `checklist_result` (또는 {}), (선택) `api_data` |
| **출력** | `validation_result`: `is_valid`, `validation_score`, `mismatches`, `missing_items`, `corrected_fields`, `data_source`, `elements_validation` 등. |
| **실패 시** | `None`, `PipelineMonitor.record_stage(..., stage="validating", status="failure")` |

---

## 3. 데이터 흐름 (Orchestrator 관점)

```
Orchestrator: product_data | shop_data, analysis_result, checklist_result 확정 후
    → DataValidator.validate_crawler_vs_report(...)
    → (선택) Qoo10APISchema 정규화·구조 비교
    → validation_result 반환 (보정 시 analysis_result 내부 갱신)
    → final_result.validation 에 포함 (Report & Output 단계)
```

---

## 4. 파이프라인 위치

- **이전 단계**: Crawl, Analysis, Recommendation, Checklist 완료 후.
- **다음 단계**: Report & Output Agent가 `final_result.validation`에 포함; 프론트엔드 오류 신고 UI 연동.
- **PipelineMonitor stage**: `validating`.

---

## 5. 요소(Element) 단위 검증

- **`elements_validation`**: 크롤러의 `page_structure.elements_detail`과 분석의 `page_structure_analysis.elements`를 비교하여, 요소별 존재 여부 일치를 검증.
- 각 항목: `element_id`, `name_ko`, `crawl_present`, `analysis_present`, `consistent`, `note`.
- Report & Output 시 마크다운 리포트에 "요소별 검증 (크롤러 vs 분석)" 요약 포함 가능.

---

## 6. 확장 포인트

- **메뉴얼 검증**: 상품/Shop 파이프라인과 별도로 `manual_validator`가 큐텐 대학 메뉴얼 MD vs 크롤 결과를 비교하여 누락 링크·섹션을 분석(Manual Agent 참조).

---

## 7. 의존성

- DataValidator
- (선택) Qoo10APISchema, Qoo10APIService

---

**문서 버전**: 1.1  
**최종 수정**: 2026-02-28
