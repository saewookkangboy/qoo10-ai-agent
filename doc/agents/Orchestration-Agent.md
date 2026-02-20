# Orchestration Agent (조율 에이전트)

**역할**: 전체 분석 파이프라인의 단일 진입점을 담당하고, 단계별 에이전트 호출 순서·진행률·실패 처리·최종 결과 저장을 조율한다.

**코드 위치**: `api/main.py` — `POST /api/v1/analyze`, `perform_analysis()`, `_update_progress()`, `analysis_store` 관리.

---

## 1. 책임

- **진입 처리**: URL 검증(`is_valid_qoo10_url`), URL 타입 결정(`detect_url_type`), `analysis_id` 발급, `analysis_store` 초기 상태 등록.
- **백그라운드 실행**: `BackgroundTasks.add_task(perform_analysis, ...)` 로 실제 파이프라인을 비동기 실행.
- **단계 제어**: `_update_progress(analysis_id, stage, percentage, message)` 로 단계별 진행률/메시지 갱신.
- **에이전트 호출 순서**  
  1. Crawl Agent → product_data / shop_data  
  2. Analysis Agent → analysis_result  
  3. Recommendation Agent → recommendations (실패 시 빈 리스트로 계속)  
  4. Checklist Agent → checklist_result (실패 시 None으로 계속)  
  5. Validation Agent → validation_result (실패 시 None으로 계속)  
  6. Report & Output Agent → final_result 조립, store 저장, 히스토리·알림
- **실패 정책**:  
  - Crawl / Analysis 실패 → 해당 분석 `status: "failed"`, progress 0, 에러 메시지 저장 후 종료.  
  - Recommendation / Checklist / Validation 실패 → 로그·파이프라인 모니터 기록 후 기본값으로 계속 진행.
- **모니터링**: 각 단계 성공/실패·소요 시간을 `PipelineMonitor.record_stage()` 로 기록.

---

## 2. 입출력

| 구분 | 내용 |
|------|------|
| **입력** | `AnalyzeRequest`: `url` (HttpUrl), `url_type` (optional, 자동 감지) |
| **즉시 출력** | `AnalyzeResponse`: `analysis_id`, `status: "processing"`, `url_type`, `estimated_time` |
| **비동기 최종 출력** | `analysis_store[analysis_id]`: `status` (completed/failed), `progress`, `result` (완료 시) |

---

## 3. 데이터 흐름 (Orchestrator 관점)

```
request.url, request.url_type(optional)
    → analysis_id 생성, analysis_store 초기화
    → perform_analysis(analysis_id, url, url_type) [백그라운드]

perform_analysis 내부:
    product_data | shop_data  = Crawl Agent(url, url_type)
    analysis_result           = Analysis Agent(product_data | shop_data)
    recommendations           = Recommendation Agent(product_data, analysis_result)
    checklist_result          = Checklist Agent(product_data, analysis_result [, page_structure])
    validation_result         = Validation Agent(product_data, analysis_result, checklist_result)
    final_result              = { product_analysis|shop_analysis, recommendations, checklist, product_data|shop_data, validation }
    → analysis_store[analysis_id].result = final_result, status = "completed"
    → HistoryManager, NotificationService (비동기)
```

---

## 4. 확장 포인트

- **병렬화**: Recommendation Agent와 Checklist Agent는 `analysis_result` 확정 후 동시 실행 가능. `asyncio.gather(recommendations_task, checklist_task)` 로 전환 가능.
- **SEO/AIO/GEO**: 동일 URL에 대해 “일반 분석” 대신 “SEO 전용” 등 라우트가 들어오면, Orchestrator가 Crawl만 공유하고 이후 Analysis를 SEO/AIO/GEO 전용 서비스로 분기하도록 확장 가능.
- **배치 분석**: `BatchAnalyzer`는 여러 URL에 대해 Orchestration Agent를 N회 호출하는 상위 조율자로 볼 수 있음.
- **메뉴얼 파이프라인**: 상품/Shop 분석과 독립적으로, 큐텐 대학 한국어 메뉴얼 수집·검증·누락 분석을 수행하는 Manual Agent(`run_manual_pipeline.py`, `test_data_pipeline_full.py --manual`)가 있으며, 동일 조율 패턴(수집 → 검증 → 결과 저장)으로 확장되어 있다.

---

## 5. 의존성

- Crawl Agent (Qoo10Crawler, error_reporting_service)
- Analysis Agent (ProductAnalyzer, ShopAnalyzer, ai_provider)
- Recommendation Agent (SalesEnhancementRecommender)
- Checklist Agent (ChecklistEvaluator)
- Validation Agent (DataValidator)
- Report & Output (ReportGenerator, HistoryManager, NotificationService, PipelineMonitor)
- (선택·독립) Manual Agent (Qoo10ManualCrawler, manual_validator) — `run_manual_pipeline.py` / `--manual` 호출 시

---

## 6. 문서 간 참조

| 단계 | 상세 문서 |
|------|-----------|
| 1단계 수집 | [Crawl-Agent.md](./Crawl-Agent.md) |
| 2단계 분석 | [Analysis-Agent.md](./Analysis-Agent.md) |
| 3·4단계 추천·체크리스트 | [Recommendation-Agent.md](./Recommendation-Agent.md), [Checklist-Agent.md](./Checklist-Agent.md) |
| 5단계 검증 | [Validation-Agent.md](./Validation-Agent.md) |
| 6단계 출력 | [Report-Output-Agent.md](./Report-Output-Agent.md) |
| 메뉴얼(선택) | [Manual-Agent.md](./Manual-Agent.md) |

---

**문서 버전**: 1.1  
**최종 수정**: 2026-02-28
