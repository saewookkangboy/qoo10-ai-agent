# Qoo10 AI Agent - 에이전트 오케스트레이션 설계

**목적**: 전체 서비스를 Orchestration 중심으로 구조화하여, 분석(크롤링·영역 추출)·리포트·개선 제안·점수 출력이 **동시에 분석 → 관리 → 출력**되며 **데이터 파이프라인이 명확히 흐르도록** 설계합니다.

**참조**: dev-agent-kit 역할 체계(PM, Backend, Frontend, Server/DB, AI Marketing Researcher 등), `.cursor/agents/dev-agent-kit.md`, `api/main.py`의 `perform_analysis` 플로우.

---

## 1. 데이터 파이프라인 개요

```
[사용자 요청: URL]
        │
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Orchestration Agent (조율)                                          │
│  - URL 검증, url_type 결정, analysis_id 발급                          │
│  - 단계별 진행률·상태 업데이트 (_update_progress)                     │
│  - 단계 실패 시 보상 경로·재시도 정책 결정                             │
└─────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Stage 1: 수집 (Crawl Agent)                                         │
│  - product: Qoo10Crawler.crawl_product()                             │
│  - shop: Qoo10Crawler.crawl_shop()                                   │
│  - 출력: product_data | shop_data                                     │
└─────────────────────────────────────────────────────────────────────┘
        │ product_data / shop_data
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Stage 2: 분석 (Analysis Agent)                                      │
│  - product: ProductAnalyzer.analyze() + AI enhance                   │
│  - shop: ShopAnalyzer.analyze() + AI enhance                         │
│  - 출력: analysis_result (overall_score, 섹션별 점수·인사이트)        │
└─────────────────────────────────────────────────────────────────────┘
        │ analysis_result
        ├──────────────────────────────────┬──────────────────────────┐
        ▼                                  ▼                          ▼
┌─────────────────────┐    ┌─────────────────────────────┐   ┌─────────────────────┐
│ Recommendation      │    │ Checklist Agent             │   │ (선택) Competitor   │
│ Agent               │    │ - ChecklistEvaluator        │   │ Agent               │
│ - Recommender       │    │ - product/shop 체크리스트   │   │ - CompetitorAnalyzer│
│ - recommendations[] │    │ - checklist_result          │   │ - competitor_analysis│
└─────────────────────┘    └─────────────────────────────┘   └─────────────────────┘
        │                                  │                          │
        └──────────────────────────────────┴──────────────────────────┘
        │ recommendations, checklist_result
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Stage 3: 검증 (Validation Agent)                                    │
│  - DataValidator.validate_crawler_vs_report()                       │
│  - 크롤링 vs 리포트 일치·보정, validation_result                      │
└─────────────────────────────────────────────────────────────────────┘
        │ validation_result
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Stage 4: 출력·관리 (Report & Output Agent)                          │
│  - final_result 조립 (product_analysis, recommendations, checklist, │
│    validation, product_data/shop_data)                               │
│  - analysis_store 저장, PipelineMonitor 기록                          │
│  - HistoryManager 저장, NotificationService 알림                      │
│  - ReportGenerator (PDF/Excel/Markdown) - 다운로드 시                 │
└─────────────────────────────────────────────────────────────────────┘
        │
        ▼
[API 응답: GET /api/v1/analyze/{id}]  [다운로드: /api/v1/analyze/{id}/download]
```

**동시 실행 가능 구간**  
- **Stage 2 직후**: Recommendation Agent, Checklist Agent(및 선택적 Competitor Agent)는 `product_data` + `analysis_result`만 있으면 동시에 실행 가능.  
- 현재 구현은 순차(추천 → 체크리스트)이지만, 오케스트레이터에서 `asyncio.gather` 등으로 병렬화 가능.

---

## 2. 에이전트 역할 매핑 (코드 ↔ 문서)

| Agent | 담당 서비스/클래스 | 입력 | 출력 | PipelineMonitor stage |
|-------|-------------------|------|------|------------------------|
| **Orchestration** | `main.py` (라우트, `perform_analysis` 조율) | URL, url_type | analysis_id, progress, 최종 result | 전체 단계 |
| **Crawl** | `Qoo10Crawler`, `crawler_shop` | url, url_type | product_data / shop_data | crawling |
| **Analysis** | `ProductAnalyzer`, `ShopAnalyzer`, `ai_provider` | product_data / shop_data | analysis_result | analyzing |
| **Recommendation** | `SalesEnhancementRecommender` | product_data, analysis_result | recommendations | generating_recommendations |
| **Checklist** | `ChecklistEvaluator` | product_data, analysis_result(, page_structure) | checklist_result | evaluating_checklist |
| **Validation** | `DataValidator` | product_data, analysis_result, checklist_result | validation_result | validating |
| **Report & Output** | `ReportGenerator`, `HistoryManager`, `NotificationService`, `PipelineMonitor` | final_result | 저장·알림·다운로드 | finalizing |
| **Manual (메뉴얼)** | `Qoo10ManualCrawler`, `manual_validator` | — | 큐텐 대학 한국어 메뉴얼 수집·검증·누락 분석 | `run_manual_pipeline.py`, `--manual` 옵션 |

---

## 3. 문서 목록

- **[Orchestration-Agent.md](./Orchestration-Agent.md)** – 조율 에이전트: 진입·단계 제어·실패 정책·데이터 흐름·확장 포인트·문서 간 참조.
- **[Crawl-Agent.md](./Crawl-Agent.md)** – 크롤링·영역 추출, product/shop/메뉴얼, PipelineMonitor stage, 확장 포인트.
- **[Analysis-Agent.md](./Analysis-Agent.md)** – 상품/Shop 분석, 점수·섹션별 인사이트, AI 강화, 데이터 흐름·스키마.
- **[Recommendation-Agent.md](./Recommendation-Agent.md)** – 매출 강화 제안, 메뉴얼 연동, 동시 실행(Checklist와 병렬).
- **[Checklist-Agent.md](./Checklist-Agent.md)** – 체크리스트 평가, 메뉴얼 기반 항목, 동시 실행(Recommendation과 병렬).
- **[Validation-Agent.md](./Validation-Agent.md)** – 크롤러 vs 리포트 검증·보정, 요소 단위 검증, API 연동, 메뉴얼 검증 확장.
- **[Report-Output-Agent.md](./Report-Output-Agent.md)** – 결과 조립, 저장, 히스토리, 알림, 리포트 다운로드, 데이터 흐름.
- **[Manual-Agent.md](./Manual-Agent.md)** – 큐텐 대학 한국어 메뉴얼 수집·검증·누락 분석(독립 파이프라인).

**관련**: [../QC_QA_REPORT_1093098159.md](../QC_QA_REPORT_1093098159.md) (상품 페이지 QC/QA), [../SERVICE_IMPROVEMENT_LOG.md](../SERVICE_IMPROVEMENT_LOG.md) (서비스 개선 로그).

---

## 4. 상세 페이지 요소(Element) 단위 분석 흐름

상세 페이지는 **요소(element) 단위**로 추출·분석·추천·체크리스트·리포트에 일관되게 반영된다.

| 단계 | 데이터 | 설명 |
|------|--------|------|
| **Crawl** | `page_structure.elements_detail` | 요소별 `element_id`, `name_ko`, `present`, `classes`, `source` (product_info, price_info, image_info 등) |
| **Analysis** | `page_structure_analysis.elements` | 요소별 `score`, `present`, `quality`, `recommendation`, `kind`(essential/optional) |
| **Recommendation** | `recommendations[].element_id` | 추천 항목이 연관된 요소(예: product_info, price_info, image_info) |
| **Checklist** | `checklists[].items[].element_id`, `element_status` | 체크 항목과 요소 매핑, 요소별 present/score/quality |
| **Validation** | `validation_result.elements_validation` | 크롤러 vs 분석 요소 존재 여부 일치 검증(`crawl_present`, `analysis_present`, `consistent`) |
| **Report & Output** | PDF/MD/Excel 내 "요소별 분석" | 요소별 존재 여부, 점수, 품질, 권장 사항; 검증 시 요소 일치 요약 포함 가능 |

요소 ID는 `.spec-kit/product-page-elements-spec.md` 및 본 디렉터리 에이전트 문서와 동일한 규칙을 사용한다.

---

## 5. dev-agent-kit과의 정합성

- **Spec-kit**: 본 설계는 `.spec-kit/` 및 `doc/`의 분석·파이프라인 스펙과 맞춰 관리한다.
- **To-do / Role**: 에이전트별 작업은 `.project-data/todos.json`, `role-config.json`의 역할(Backend, Server/DB, PM 등)과 연결해 할당할 수 있다.
- **요소 단위 분석**: Crawl → Analysis → Recommendation → Checklist → Report 전 구간에서 동일한 `element_id` 체계로 상세 페이지 요소가 반영된다.
- **SEO/AIO/GEO**: 별도 엔드포인트(`/api/v1/seo/analyze`, `/api/v1/aio/analyze` 등)는 Orchestration Agent가 “특수 분석 요청”으로 라우팅하는 확장 노드로 볼 수 있다.

---

## 6. 문서 고도화 (Orchestration-Agent 기준)

모든 에이전트 문서는 **Orchestration-Agent.md**를 기준으로 아래 구조로 통일·고도화되어 있다.

| 섹션 | 설명 |
|------|------|
| 역할·코드 위치 | 한 줄 역할 요약 + 구현 위치 |
| 1. 책임 | 단계별 책임, 실패 시 Orchestrator/PipelineMonitor 동작 |
| 2. 입출력 | 입력/출력/실패 시 |
| 3. 데이터 흐름 (Orchestrator 관점) | 호출 순서·데이터 전달 요약 |
| 4. 데이터 스키마 / 파이프라인 위치 | 스키마 요약 또는 이전·다음 단계, PipelineMonitor stage |
| 5. 확장 포인트 | 병렬화, SEO/AIO/GEO, 메뉴얼 등 |
| 6. 의존성 | 사용 서비스·모듈 |

- **문서 버전**: 에이전트별 1.0/1.1, **최종 수정**: 2026-02-28

---

**최종 수정**: 2026-02-28
