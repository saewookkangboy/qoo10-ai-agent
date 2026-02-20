# 데이터 측정 및 분석 고도화 스펙 (제안)

**프로젝트**: qoo10-ai-agent  
**관련 문서**: `doc/ENHANCED_ANALYSIS_METRICS.md`, `doc/METRICS_CODE_MAPPING.md`, `doc/CRAWLING_ANALYSIS_PRINCIPLES.md`  
**목적**: 분석 품질·비즈니스 가치 향상을 위한 신규/보강 지표 제안 및 파이프라인·운영 측정 강화 방안.

---

## 1. 측정 체계 정합성 (완료 반영)

- **정합성 검토**: `doc/METRICS_CODE_MAPPING.md`에 ENHANCED_ANALYSIS_METRICS vs analyzer/shop_analyzer 일치·갭 목록 정리됨.
- **코드 참조**: `api/services/analyzer.py`, `api/services/shop_analyzer.py` 상단 docstring에 지표 문서·매핑 문서 경로 명시.
- **후속**: 갭 정리는 문서 업데이트 또는 코드 단계적 반영으로 진행 (기존 API 동작 유지).

---

## 2. 신규/보강 측정 지표 제안

아래 항목은 측정 가능한 범위에서 제안하며, 구현 시 저장 스키마·집계 주기·API 노출 여부를 별도 정의하는 것을 권장한다.

### 2.1 시계열 비교


| 지표             | 설명                                  | 측정 방법 제안                                                    | 비고                                        |
| -------------- | ----------------------------------- | ----------------------------------------------------------- | ----------------------------------------- |
| **상품 점수 추이**   | 동일 상품의 overall_score / 섹션별 점수 시계열   | 분석 결과 저장 시 `product_code` + `analyzed_at` 기준 이력 저장 후 기간별 집계 | DB에 분석 이력 테이블 또는 기존 `crawled_products` 확장 |
| **Shop 점수 추이** | 동일 Shop의 overall_score / 섹션별 점수 시계열 | `shop_id` + `analyzed_at` 이력 저장                             | 상품과 동일 패턴                                 |
| **트렌드 요약**     | 전기 대비 점수 상승/하락 비율                   | (현재 점수 − 이전 점수) / 이전 점수, 기간별(주/월)                           | 리포트·대시보드용                                 |


### 2.2 A/B·효과 측정


| 지표            | 설명                                        | 측정 방법 제안                                   | 비고                    |
| ------------- | ----------------------------------------- | ------------------------------------------ | --------------------- |
| **개선 전후 비교**  | 특정 개선(이미지 추가, 설명 수정 등) 전후 점수 차이           | 동일 URL/product_code에 대해 이전 분석 vs 재분석 결과 비교 | 수동 “재분석” 플로우와 연동 시 유용 |
| **추천 적용률**    | 추천 항목 중 사용자가 적용했다고 표시한 비율                 | 프론트/백엔드에서 “적용함” 플래그 수집 후 집계                | UX 이벤트 수집 필요          |
| **섹션별 개선 효과** | 특정 섹션(이미지/설명/가격 등) 개선 시 overall_score 변화량 | 시계열 + 섹션별 점수로 회귀 또는 전후 비교                  | 선택 구현                 |


### 2.3 키워드·트렌드


| 지표               | 설명                                   | 측정 방법 제안                                  | 비고                    |
| ---------------- | ------------------------------------ | ----------------------------------------- | --------------------- |
| **키워드 노출률**      | 수집된 search_keywords 중 상품명/설명에 포함된 비율 | 기존 SEO 분석 확장 — 키워드별 포함 여부 집계              | analyzer 출력만으로도 집계 가능 |
| **카테고리별 평균 점수**  | 카테고리별 overall_score / 섹션별 평균         | 분석 결과 저장 시 category + score 저장 후 GROUP BY | 집계 API 또는 배치          |
| **인기 키워드 등장 빈도** | 동일 키워드가 여러 상품에서 사용된 빈도               | 크롤링·분석 결과에서 키워드 리스트 수집 후 count            | 트렌드 리포트용              |


### 2.4 리뷰 감성·추이


| 지표              | 설명                         | 측정 방법 제안                               | 비고                         |
| --------------- | -------------------------- | -------------------------------------- | -------------------------- |
| **부정 리뷰 비율 추이** | 동일 상품의 부정 리뷰 비율 시계열        | 분석 이력에 `negative_ratio` 저장 후 기간별 평균/최대 | 기존 negative_keywords 로직 활용 |
| **평점 추이**       | 동일 상품의 rating 시계열          | 분석 이력에 `rating` 저장                     | 리뷰 수와 함께 추이 대시보드           |
| **감성 점수 (확장)**  | 리뷰 텍스트에 대한 감성 점수 (예: -1~1) | 선택: 외부 API 또는 로컬 감성 모델 도입              | 현재 부정 키워드 비율을 보완           |


### 2.5 구현 우선순위 (제안)

1. **Phase 1 (저비용)**: 시계열 비교를 위한 분석 결과 이력 저장( product_code/shop_id, analyzed_at, overall_score, 섹션별 score), 키워드 노출률 집계.
2. **Phase 2**: 상품/Shop 점수 추이 API, 트렌드 요약(전기 대비), 카테고리별 평균 점수.
3. **Phase 3**: A/B 전후 비교, 리뷰 감성 추이, 추천 적용률(이벤트 수집 연동).

---

## 3. 파이프라인·운영 측정 강화 제안

기존 `pipeline_monitoring` / `pipeline_success_rates` / `get_crawling_statistics` 외에 아래 측정·집계를 추가하는 방안을 제안한다.

### 3.1 분석 결과 품질


| 항목                   | 설명                                       | 저장/집계 방안                                                            | 비고                                 |
| -------------------- | ---------------------------------------- | ------------------------------------------------------------------- | ---------------------------------- |
| **overall_score 분포** | 구간별(0–49, 50–69, 70–89, 90–100) 건수 또는 비율 | 분석 완료 시 `pipeline_monitoring.metadata` 또는 전용 테이블에 score 저장 후 기간별 집계 | Admin/대시보드용                        |
| **섹션별 점수 분포**        | 이미지/설명/가격/리뷰/SEO/페이지구조별 평균·분포            | 동일하게 metadata 또는 analysis_results 테이블에 저장 후 집계                      | 품질 모니터링                            |
| **등급별 비율**           | Excellent/Good/Fair/Poor 비율              | overall_score 구간 → 등급 매핑 후 집계                                       | ENHANCED_ANALYSIS_METRICS 등급 기준 사용 |


**구현 제안**  

- 분석 완료 시 `PipelineMonitor.record_stage(..., metadata={"overall_score": x, "section_scores": {...}})` 로 기록.  
- 별도 집계 테이블 `analysis_quality_aggregates` (period_type, period_start, score_bucket, count) 또는 기존 `pipeline_success_rates` 확장은 선택.  
- Admin API: `GET /admin/analysis-quality?period=day&days=7` 형태로 노출 검토.

### 3.2 크롤링 품질


| 항목              | 설명                    | 저장/집계 방안                                                                | 비고                               |
| --------------- | --------------------- | ----------------------------------------------------------------------- | -------------------------------- |
| **수집 필드 완성도**   | 필수/권장 필드별 채워진 비율      | 크롤링 성공 시 필드별 존재 여부(0/1) 저장, 기간별 평균                                      | `crawling_performance` 또는 전용 테이블 |
| **실패 사유 분류**    | 단계별 실패 시 원인 분류        | `pipeline_monitoring.error_message` 파싱 또는 코드에서 `failure_reason` enum 저장 | 타임아웃/셀렉터/네트워크/기타 등               |
| **URL 타입별 성공률** | product vs shop 별 성공률 | 기존 `url_type` 활용, `pipeline_success_rates`에 url_type 차원 추가 또는 별도 집계     | 현재 단계별만 집계됨                      |


**구현 제안**  

- 크롤링 단계 기록 시 metadata에 `fields_present: { product_name: true, price: true, ... }` 형태로 저장.  
- 실패 시 `error_message` + (선택) `failure_reason` 코드 저장.  
- 집계: 배치 또는 Admin API에서 기간별 필드 완성도·실패 사유별 건수 조회.

### 3.3 반영 여부

- **문서·스펙 반영**: 본 스펙(`.spec-kit/data-measurement-analysis-enhancement.md`)에 위 내용 반영 완료.
- **Todo 반영**: 아래 4.절에 따라 `.project-data/todos.json`에 항목 추가.
- **API 변경**: 기존 API 동작을 깨뜨리지 않는 범위에서, 새 엔드포인트(예: Admin 분석 품질/크롤링 품질 집계) 또는 기존 Admin API 확장으로 진행 권장.

---

## 4. Todo / Spec 반영 요약

- **정합성**: `doc/METRICS_CODE_MAPPING.md` 작성 및 analyzer/shop_analyzer docstring 참조 추가 완료.
- **신규 지표 제안**: 본 문서 2절에 정리, 경로 `.spec-kit/data-measurement-analysis-enhancement.md`.
- **파이프라인·운영 측정**: 본 문서 3절에 정리, 필요 시 todo로 “분석 품질 집계”, “크롤링 품질(필드 완성도·실패 사유) 집계” 추가.
- **역할별 category**: role-config.json 기준 backend / server_db / pm 등에 맞춰 todo category 배정.

---

**업데이트 이력**

- **2026-02-20**: 초안 (데이터 측정·분석 고도화 작업 반영)

