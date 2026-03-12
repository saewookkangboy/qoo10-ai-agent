# 상세 이미지(긴 이미지) 내용 추출 리서치

**목적**: Qoo10 상품 상세 페이지의 긴 이미지(상세 이미지)를 판독하여 텍스트/구조를 추출하고, 실제 분석 결과(설명 분석·점수·권장 사항)에 반영할 수 있는 방법을 정리한다.

**관련 Agent**: Crawl Agent(이미지 URL 수집), Analysis Agent(분석 반영).  
**코드**: `api/services/crawler.py` (_extract_images → detail_images), `api/services/analyzer.py` (image_analysis, description_analysis).

---

## 1. 현황

| 항목 | 내용 |
|------|------|
| **수집 데이터** | `product_data["images"]["detail_images"]` (URL 목록), `detail_images_with_alt` (src, alt) |
| **현재 분석** | 이미지 **개수**, 썸네일 품질, alt 다양성만 사용. **이미지 내부 텍스트는 미사용** |
| **한계** | 상세 이미지에 스펙·사용법·보증 문구 등이 있어도 분석에 반영되지 않음 |

---

## 2. 추출 방식 옵션

### 2.1 Vision API (권장)

- **OpenAI GPT-4 Vision (gpt-4o / gpt-4o-mini)**
  - 이미지 URL 직접 전달 가능 (`image_url: { url }`). 공개 URL이면 다운로드 불필요.
  - 프롬프트로 "이 이미지에 보이는 모든 텍스트를 추출해 주세요" 요청.
  - **긴 이미지**: 한 장씩 전송. 해상도/비율 제한 있으나 대부분 상세 이미지는 처리 가능.
- **Google Gemini**
  - 이미지 URL 또는 base64 입력. 멀티모달 지원.
  - 프로젝트에서 이미 `GeminiService` 사용 중 → 동일 키로 Vision 확장 가능.

- **Operational considerations** (구현 시 참고: `detail_image_extractor.py`, OpenAI/Gemini 클라이언트)
  1. **Rate limiting**
     - **Throttling**: 상세 이미지 N장을 한 분석에서 처리할 때, 요청 간 최소 간격(예: 200–500ms) 두어 RPM 제한 회피.
     - **Queueing**: 동시 요청 수 상한(예: 2–3)으로 세마포어/큐 사용 시, 초과 요청은 순차 대기.
     - **Per-second/minute limits**: OpenAI/Gemini 각 문서의 RPM·TPM 제한 확인. 초과 시 429 응답 → 재시도 정책과 연동.
     - **Limit hit 시 동작**: 429 수신 시 백오프 후 재시도; 연속 실패 시 해당 이미지만 스킵하고 로그·메트릭 기록, 나머지 이미지는 계속 처리.
  2. **Retry policy**
     - **Max retries**: 요청당 최대 재시도 2–3회 권장.
     - **Exponential backoff + jitter**: 예: `delay = min(base * 2^attempt + random_jitter, max_delay)` (base 1–2초, max 30초).
     - **Retry 대상**: 429(Too Many Requests), 503(Service Unavailable), 500(Internal Server Error), 일시적 네트워크 오류. **Fail fast**: 400(Bad Request), 401/403(인증·권한), 413(Payload Too Large), 4xx(클라이언트 오류)는 재시도하지 않음.
  3. **Timeout**
     - **요청당 타임아웃**: Vision 호출 1건당 15_000–30_000ms 권장. 설정 위치: `httpx`/`aiohttp` 클라이언트 또는 `openai_service.py`/`gemini_service.py`의 Vision 호출부.
     - **전체 추출 타임아웃**: N장 합계 상한(예: 60_000–90_000ms)을 두어 한 분석이 무한 대기하지 않도록 함. `detail_image_extractor.py` 루프 내 누적 시간 체크.
  4. **Image pre-validation**
     - **포맷**: 허용 형식만 전달. OpenAI: PNG, JPEG, GIF, WEBP. Gemini: JPEG, PNG, WEBP, GIF 등. 지원 포맷 외는 스킵 또는 변환 후 전송.
     - **크기/해상도**: 파일 크기 상한(예: 4–20MB), 해상도 상한(API 문서 기준) 초과 시 리사이즈 또는 스킵. URL인 경우 HEAD/GET으로 Content-Length 확인 후 초과 시 스킵.
     - **URL**: 공개 접근 가능한지 HEAD 요청으로 확인(4xx/5xx 시 스킵). 리다이렉트 횟수·최종 URL 도메인 화이트리스트(필요 시) 적용.
     - **Base64**: 인코딩 길이 상한(API별 제한 있음). 디코딩 오류·잘못된 패딩 시 해당 이미지 스킵하고 로그.

**장점**: 레이아웃·언어 혼합·손글씨까지 유연하게 처리.  
**단점**: API 비용, 요청당 대기 시간.

### 2.2 OCR 전용 (Google Cloud Vision, Tesseract 등)

- **Google Cloud Vision API**
  - `TEXT_DETECTION` / `DOCUMENT_TEXT_DETECTION` (문서·밀집 텍스트에 유리).
  - Python: `google-cloud-vision`, 이미지 바이트 또는 GCS URI 전달.
- **Tesseract (오픈소스)**
  - 이미지 다운로드 후 로컬 OCR. 일본어/한국어 지원 가능.
  - 긴 이미지는 세로로 타일 분할 후 순서대로 OCR 병합하는 방식 필요.

**장점**: 텍스트만 필요할 때 비용·제어 용이.  
**단점**: 긴 이미지 분할·병합 로직 구현 필요, 레이아웃 보존은 Vision보다 약함.

### 2.3 긴 이미지 처리

- **한 장씩 전송**: 상세 이미지가 여러 장이면 각 URL을 별도 요청으로 처리. "긴" 한 장은 Vision/OCR이 대부분 한 번에 처리.
- **타일 분할**: 해상도가 매우 크면 일부 API 제한에 걸릴 수 있음. 필요 시 세로로 N등분해 순서대로 추출 후 텍스트 병합.
- **최대 개수 제한**: 비용·시간 제어를 위해 상세 이미지 중 **최대 N개**(예: 5개)만 추출하거나, 환경 변수로 기능 on/off.

---

## 3. 실제 분석에 반영하는 방법

### 3.1 설명(description) 분석 보강

- **방법**: 상세 이미지에서 추출한 텍스트를 `description`과 합쳐서(가상의 `effective_description`) 길이·구조·키워드 평가.
- **구현**: `product_data["detail_image_contents"]` = `[{ "url", "text" }, ...]` 를 Crawl 직후 또는 Analysis 직전에 채움.  
  `_analyze_description()`에서 `description + "\n".join(추출 텍스트)` 로 길이/구조 품질 계산.
- **효과**: 텍스트가 이미지에만 있는 상품도 설명 점수에 반영 가능.

### 3.2 별도 섹션: 상세 콘텐츠 분석(detail_content_analysis)

- **방법**: `analysis_result["detail_content_analysis"]` 추가.
  - `extracted_text_length`, `image_count_processed`, `has_specs`, `has_usage`, `recommendations` 등.
- **구현**: Analyzer에서 `detail_image_contents`가 있으면 위 지표 계산 후 리포트·체크리스트에 노출.
- **효과**: "상세 이미지에 스펙/사용법이 있는지"를 명시적으로 점수화·권장 가능.

### 3.3 AI 강화 입력으로 전달

- **방법**: `enhance_analysis_with_ai` 호출 시 `_build_analysis_context`에 "상세 이미지에서 추출한 텍스트" 요약을 추가.
- **구현**: `product_data["detail_image_contents"]` 요약 문자열을 context에 포함.
- **효과**: AI 인사이트·액션 아이템이 상세 이미지 내용을 반영.

---

## 4. 권장 구현 순서

1. **상세 이미지 내용 추출 서비스** (`api/services/detail_image_extractor.py`)
   - 입력: `detail_images` URL 리스트, 옵션(최대 개수, 타임아웃).
   - 출력: `[{ "url", "text", "error"? }, ...]`.
   - 내부: 현재 프로젝트 AI 제공자(OpenAI/Gemini) 중 Vision 지원하는 쪽 사용. 이미지 URL 직접 전달 우선.

2. **파이프라인 연동**
   - **Crawl 직후** (권장): `perform_analysis`에서 상품 크롤 완료 후 `extract_detail_image_contents(product_data)` 호출 → `product_data["detail_image_contents"]` 설정.
   - 환경 변수 예: `ENABLE_DETAIL_IMAGE_EXTRACTION=true`, `DETAIL_IMAGE_MAX_COUNT=5`.

3. **분석 반영**
   - `ProductAnalyzer._analyze_description()`: `detail_image_contents`가 있으면 추출 텍스트를 보조 설명으로 합산해 길이/구조 평가.
   - (선택) `detail_content_analysis` 섹션 추가 후 리포트·체크리스트에 반영.

4. **Agent 문서**
   - Crawl-Agent 확장 포인트: "상세 이미지 내용 추출(선택) 시 Crawl 직후 extractor 호출."
   - Analysis-Agent 확장 포인트: "detail_image_contents 기반 설명 보강 및 detail_content_analysis."

---

## 5. 참고

- OpenAI Vision: [Images](https://platform.openai.com/docs/guides/vision), `image_url` 지원.
- Google Cloud Vision OCR: [Text detection](https://cloud.google.com/vision/docs/ocr).
- 프로젝트: `api/services/openai_service.py`, `api/services/gemini_service.py`, `api/services/ai_provider.py`.

---

**문서 버전**: 1.0  
**최종 수정**: 2026-03-11
