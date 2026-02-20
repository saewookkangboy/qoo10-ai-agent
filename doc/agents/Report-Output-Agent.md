# Report & Output Agent (리포트·저장·출력 에이전트)

**역할**: 분석 파이프라인의 최종 결과를 조립하고, 저장·알림·다운로드 형식으로 출력한다. Orchestration Agent의 6단계(종단)를 담당한다.

**코드 위치**: `api/main.py` (final_result 조립, analysis_store 저장), `api/services/report_generator.py`, `api/services/history_manager.py`, `api/services/notification_service.py`, `api/services/pipeline_monitor.py`. 다운로드: `GET /api/v1/analyze/{id}/download`.

---

## 1. 책임

- **결과 조립**: `final_result` = product_analysis|shop_analysis + recommendations + checklist + product_data|shop_data + validation.
- **저장**: `analysis_store[analysis_id].result = final_result`, `status = "completed"`, `progress = 100`.
- **파이프라인 기록**: `PipelineMonitor.record_stage(..., stage="finalizing", status="success"|"failure")`.
- **히스토리**: `HistoryManager.save_analysis_history(analysis_id, url, url_type, final_result)`.
- **알림**: `NotificationService.notify_analysis_completed(...)`, `notify_threshold_alert(...)`.
- **다운로드**: `ReportGenerator.generate_pdf_report(...)`, `generate_excel_report(...)`, `generate_markdown_report(..., validation_result=...)` — format에 따라 PDF/Excel/Markdown 응답. 메뉴얼 기반 체크리스트 섹션 포함.
- **실패 시**: store 업데이트 재시도; 히스토리·알림 실패는 로그만 하고 사용자 결과는 우선 저장.

---

## 2. 입출력

| 구분 | 내용 |
|------|------|
| **입력** | `final_result` (위 조립 구조), (다운로드 시) `format`: pdf | excel | markdown |
| **출력** | analysis_store 갱신, DB(히스토리·파이프라인 모니터), 알림 생성; 다운로드 시 바이너리/텍스트 응답. |
| **실패 시** | store 업데이트 재시도; 히스토리·알림 실패는 로그만. |

---

## 3. 데이터 흐름 (Orchestrator 관점)

```
Orchestrator: validation_result 반환 후
    → final_result 조립 (product_analysis|shop_analysis, recommendations, checklist, product_data|shop_data, validation)
    → analysis_store[analysis_id].result = final_result, status = "completed"
    → PipelineMonitor.record_stage(finalizing), HistoryManager, NotificationService
    → 클라이언트: GET /api/v1/analyze/{id}, GET /api/v1/analyze/{id}/download?format=...
```

---

## 4. 파이프라인 위치

- **이전 단계**: Validation Agent 이후.
- **다음 단계**: 없음 (파이프라인 종단). 클라이언트는 `GET /api/v1/analyze/{id}` 로 결과 조회, `GET /api/v1/analyze/{id}/download?format=...` 로 다운로드.
- **PipelineMonitor stage**: `finalizing`.

---

## 5. 확장 포인트

- **프로덕션**: analysis_store를 메모리 대신 DB/캐시로 대체 권장.
- **요소 단위**: 리포트 내 "요소별 분석"·"요소별 검증" 요약은 Validation의 `elements_validation`과 연동.

---

## 6. 의존성

- ReportGenerator, HistoryManager, NotificationService, PipelineMonitor
- analysis_store (메모리; 프로덕션에서는 DB/캐시 대체 권장)

---

**문서 버전**: 1.1  
**최종 수정**: 2026-02-28
