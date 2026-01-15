# 한국어-일본어 임베딩 솔루션 가이드

## 개요

Qoo10 사이트의 일본어 데이터와 한국어 리포트 간의 데이터 정확성을 향상시키기 위한 임베딩 기반 솔루션입니다.

## 추천 모델 (앙상블 모드) ⭐

### 1. BGE-M3 + Multilingual-E5-Base (기본 추천) ⭐⭐⭐

**구성**:
- **기본 모델**: `BAAI/bge-m3` (가중치: 0.7)
- **보완 모델**: `intfloat/multilingual-e5-base` (가중치: 0.3)

**장점**:
- 두 모델의 장점을 결합하여 최고의 정확도 제공
- BGE-M3의 정확도 + E5-Base의 균형잡힌 성능
- 앙상블 효과로 단일 모델보다 더 안정적인 결과
- 한국어-일본어 매칭 정확도 향상

**작동 방식**:
- 두 모델의 임베딩을 가중 평균으로 결합
- BGE-M3 결과에 더 높은 가중치 부여 (0.7)
- Multilingual-E5-Base로 보완하여 정확도 향상 (0.3)

**사용 시나리오**:
- 최고 정확도가 필요한 프로덕션 환경
- 한국어-일본어 매칭이 중요한 경우
- 충분한 리소스가 있는 환경

### 2. BGE-M3 단독 사용

**모델명**: `BAAI/bge-m3`

**장점**:
- 가장 정확한 다국어 임베딩 성능
- 100개 이상의 언어 지원 (한국어, 일본어 포함)
- 긴 컨텍스트 지원 (최대 8192 토큰)
- Dense + Sparse + Multi-vector 검색 모드 지원

**단점**:
- 모델 크기가 큼 (약 2.2GB)
- 메모리 사용량이 많음
- 긴 텍스트 처리 시 속도가 느릴 수 있음

**사용 시나리오**:
- 앙상블 모드 비활성화 시
- 리소스가 제한적인 경우

### 3. Multilingual-E5-Base 단독 사용

**모델명**: `intfloat/multilingual-e5-base`

**장점**:
- 균형잡힌 성능과 속도
- 상대적으로 작은 모델 크기
- 빠른 추론 속도

**단점**:
- 컨텍스트 윈도우가 작음 (512 토큰)
- BGE-M3보다 정확도가 약간 낮음

**사용 시나리오**:
- 앙상블 모드 비활성화 시
- 리소스가 제한적인 환경
- 빠른 응답이 필요한 경우
- 짧은 텍스트 처리

### 4. Multilingual-E5-Small (경량 추천)

**모델명**: `intfloat/multilingual-e5-small`

**장점**:
- 매우 빠른 속도
- 작은 메모리 사용량
- 경량 모델

**단점**:
- 정확도가 상대적으로 낮음
- 임베딩 차원이 작음 (384)

**사용 시나리오**:
- 개발/테스트 환경
- 매우 빠른 응답이 필요한 경우
- 리소스가 매우 제한적인 환경

## 설치 방법

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

주요 패키지:
- `sentence-transformers>=2.2.2`: 임베딩 모델 사용
- `torch>=2.0.0`: 딥러닝 프레임워크
- `langdetect>=1.0.9`: 언어 감지

### 2. 환경 변수 설정

`.env` 파일에 다음 변수를 추가:

```env
# 임베딩 모델 선택 (bge-m3, multilingual-e5-base, multilingual-e5-small, paraphrase-multilingual)
EMBEDDING_MODEL=bge-m3

# 앙상블 모드 활성화 (1: 활성화, 0: 비활성화)
# BGE-M3를 기본으로 사용할 때 Multilingual-E5-Base를 보완 모델로 사용
EMBEDDING_ENSEMBLE=1

# 자동 학습 활성화 (1: 활성화, 0: 비활성화)
EMBEDDING_AUTO_LEARN=1
```

## 사용 방법

### 1. 기본 사용

```python
from services.embedding_service import EmbeddingService
from services.database import CrawlerDatabase

# 데이터베이스 초기화
db = CrawlerDatabase()

# 임베딩 서비스 초기화
embedding_service = EmbeddingService(db=db)

# 텍스트 임베딩 생성
texts = ["商品価格", "상품가격"]
embeddings = embedding_service.encode(texts)

# 유사도 계산
similarity = embedding_service.compute_similarity("商品価格", "상품가격")
print(f"유사도: {similarity:.3f}")
```

### 2. 크롤러 통합 (자동 학습)

크롤러는 자동으로 크롤링한 텍스트를 임베딩하여 저장합니다:

```python
from services.crawler import Qoo10Crawler

crawler = Qoo10Crawler()
product_data = await crawler.crawl_product_with_playwright(url)

# 자동으로 다음 필드들이 임베딩되어 저장됩니다:
# - product_name (상품명)
# - description (상품 설명)
# - search_keywords (검색 키워드)
# - category (카테고리)
# - brand (브랜드)
```

### 3. 일본어-한국어 매칭

```python
from services.embedding_integration import EmbeddingIntegration

integration = EmbeddingIntegration(db=db)

# 일본어 텍스트와 가장 유사한 한국어 텍스트 찾기
japanese_text = "商品価格"
match = integration.match_japanese_to_korean(
    japanese_text,
    text_type="product_name",
    threshold=0.7
)

if match:
    print(f"매칭된 한국어: {match['text']}")
    print(f"유사도: {match['similarity']:.3f}")
```

### 4. 번역 검증

```python
# 일본어 원문과 한국어 번역문의 정확도 검증
validation = integration.validate_translation(
    japanese_text="商品価格",
    korean_text="상품가격",
    threshold=0.7
)

print(validation)
# {
#     "is_valid": True,
#     "similarity": 0.95,
#     "message": "유사도: 0.950 (통과)"
# }
```

### 5. 번역 제안

```python
# 일본어 텍스트에 대한 한국어 번역 제안
suggestions = integration.suggest_korean_translation(
    japanese_text="商品価格",
    text_type="product_name",
    top_k=3
)

for suggestion in suggestions:
    print(f"제안: {suggestion['korean_text']}")
    print(f"유사도: {suggestion['similarity']:.3f}")
```

### 6. 데이터 정확도 개선

```python
# 크롤링 데이터와 리포트 데이터 간의 정확도 검증 및 개선
improvements = integration.improve_data_accuracy(
    crawled_data={
        "product_name": "商品価格",
        "description": "商品説明"
    },
    report_data={
        "product_name": "상품가격",
        "description": "상품설명"
    }
)

for field, result in improvements.items():
    if result["needs_improvement"]:
        print(f"{field} 필드 개선 필요")
        print(f"검증 결과: {result['validation']}")
        print(f"제안: {result['suggestions']}")
```

## 데이터베이스 스키마

### text_embeddings 테이블

```sql
CREATE TABLE text_embeddings (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL,                    -- 원본 텍스트
    text_type TEXT NOT NULL,                -- 텍스트 타입 (product_name, description, etc.)
    source_lang TEXT,                        -- 원본 언어 (ja, ko)
    lang_confidence REAL DEFAULT 0.0,        -- 언어 감지 신뢰도
    embedding JSONB NOT NULL,                -- 임베딩 벡터 (JSON 배열)
    embedding_dimension INTEGER NOT NULL,    -- 임베딩 차원
    model_name TEXT NOT NULL,                -- 사용된 모델 이름
    metadata JSONB,                          -- 추가 메타데이터
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_text_embeddings_text_type ON text_embeddings(text_type);
CREATE INDEX idx_text_embeddings_source_lang ON text_embeddings(source_lang);
CREATE INDEX idx_text_embeddings_model_name ON text_embeddings(model_name);
```

## 자동 학습 기능

### 작동 방식

1. **크롤링 시 자동 저장**: 크롤러가 일본어 텍스트를 추출하면 자동으로 임베딩하여 DB에 저장
2. **언어 자동 감지**: 텍스트의 언어를 자동으로 감지하여 `source_lang` 필드에 저장
3. **메타데이터 저장**: URL, 상품 코드 등 추가 정보를 메타데이터로 저장
4. **유사도 기반 검색**: 저장된 임베딩을 활용하여 유사한 텍스트를 빠르게 검색

### 학습 데이터 축적

- 크롤링할 때마다 자동으로 학습 데이터가 축적됩니다
- 시간이 지날수록 더 정확한 매칭이 가능해집니다
- 같은 상품을 여러 번 크롤링해도 중복 저장되지 않습니다 (UNIQUE 제약 조건)

## 성능 최적화

### 1. 모델 선택

- **정확도 우선**: BGE-M3 사용
- **속도 우선**: Multilingual-E5-Small 사용
- **균형**: Multilingual-E5-Base 사용

### 2. 배치 처리

```python
# 여러 텍스트를 한 번에 임베딩 (더 빠름)
texts = ["텍스트1", "텍스트2", "텍스트3", ...]
embeddings = embedding_service.encode(texts, normalize=True)
```

### 3. 캐싱

임베딩은 DB에 저장되므로 동일한 텍스트는 재계산하지 않습니다.

## 추가 언어 API 제안

### 1. Google Cloud Translation API

**용도**: 고품질 번역이 필요한 경우

**장점**:
- 매우 정확한 번역
- 한국어-일본어 양방향 번역 지원
- API 기반으로 빠른 응답

**단점**:
- 유료 (사용량 기반)
- API 키 필요

**사용 예시**:
```python
from google.cloud import translate_v2 as translate

client = translate.Client()
result = client.translate("商品価格", target_language="ko")
print(result['translatedText'])  # "상품가격"
```

### 2. DeepL API

**용도**: 자연스러운 번역이 필요한 경우

**장점**:
- 매우 자연스러운 번역 품질
- 한국어-일본어 지원

**단점**:
- 유료
- API 키 필요

### 3. Papago API (네이버)

**용도**: 한국어 중심 번역

**장점**:
- 한국어 번역 품질이 우수
- 무료 티어 제공

**단점**:
- API 키 필요
- 일본어 번역 품질이 Google/DeepL보다 약간 낮을 수 있음

## 추천 아키텍처

### 하이브리드 접근법

1. **임베딩 기반 매칭** (기본)
   - 빠른 속도
   - 비용 효율적
   - 자동 학습 가능

2. **번역 API** (필요시)
   - 임베딩 매칭 실패 시 사용
   - 고품질 번역이 필요한 경우
   - 리포트 생성 시 사용

### 워크플로우

```
크롤링 (일본어)
    ↓
임베딩 생성 및 저장
    ↓
리포트 생성 시:
    1. 임베딩 기반 매칭 시도
    2. 매칭 실패 시 번역 API 사용
    3. 번역 결과도 임베딩하여 저장 (학습)
```

## 문제 해결

### 1. 모델 로딩 실패

**증상**: `ImportError: sentence-transformers 패키지가 필요합니다`

**해결**:
```bash
pip install sentence-transformers torch
```

### 2. 메모리 부족

**증상**: OOM (Out of Memory) 에러

**해결**:
- 더 작은 모델 사용 (`multilingual-e5-small`)
- 배치 크기 줄이기
- GPU 사용 (가능한 경우)

### 3. 느린 속도

**해결**:
- 더 작은 모델 사용
- 배치 처리 활용
- GPU 사용 (가능한 경우)

## 모니터링

### 로그 확인

임베딩 관련 로그는 다음과 같이 확인할 수 있습니다:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

로그 예시:
```
INFO: 임베딩 모델 로딩 중: BAAI/bge-m3
INFO: 임베딩 모델 로딩 완료: bge-m3
INFO: 임베딩 저장 완료: 5개 필드, URL=https://...
```

## 결론

**가장 효과적이며 일치 여부가 명확한 솔루션**:

1. **앙상블 모드 (기본 추천)**: BGE-M3 + Multilingual-E5-Base
   - 두 모델을 결합하여 최고의 정확도 제공
   - 가중치: BGE-M3 0.7, E5-Base 0.3
   - 한국어-일본어 매칭에 최적화

2. **단독 모델 옵션**:
   - BGE-M3 (최고 정확도, 단독 사용)
   - Multilingual-E5-Base (균형, 단독 사용)
   - Multilingual-E5-Small (빠른 속도, 경량)

**추가 언어 API**:
- Google Cloud Translation API (고품질 번역)
- DeepL API (자연스러운 번역)
- Papago API (한국어 중심, 무료 티어)

이 솔루션을 통해 Qoo10 사이트의 일본어 데이터와 한국어 리포트 간의 데이터 정확성을 크게 향상시킬 수 있습니다.
