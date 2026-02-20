# SEO/AIO/GEO 최적화 통합 가이드

## 개요

이 프로젝트는 [ai-visibility-optimizer](https://github.com/saewookkangboy/ai-visibility-optimizer)의 기능을 통합하여 Qoo10 상품 및 Shop 페이지에 대한 SEO, AI SEO, GEO 최적화 기능을 제공합니다.

## 통합된 기능

### 1. SEO 최적화 (Search Engine Optimization)

- **메타 태그 분석 및 최적화**
- **제목 및 설명 최적화**
- **헤딩 구조 분석**
- **이미지 최적화 분석**
- **Sitemap 생성**
- **robots.txt 생성**

### 2. AI SEO 최적화 (AI Search Engine Optimization)

- **AI 키워드 리서치**
- **콘텐츠 최적화 분석**
- **키워드 밀도 분석**
- **의미론적 키워드 추출**
- **AI 가독성 분석**

### 3. GEO 최적화 (Generative Engine Optimization)

- **스키마 마크업 분석**
- **FAQ 스키마 생성**
- **HowTo 스키마 생성**
- **Article 스키마 생성**
- **인용 가능성 분석**
- **AI 엔진 호환성 분석 (ChatGPT, Claude, Perplexity, Gemini)**
- **llms.txt 생성**

### 4. AIO 종합 최적화 (All-In-One)

- **SEO, AI SEO, GEO 종합 분석**
- **성능 분석**
- **접근성 분석**
- **보안 분석**
- **소셜 미디어 최적화**
- **자동 최적화 제안**
- **종합 리포트 생성**

## API 엔드포인트

### SEO 분석

```http
POST /api/v1/seo/analyze
Content-Type: application/json

{
  "url": "https://www.qoo10.jp/gmkt.inc/Goods/Goods.aspx?goodscode=..."
}
```

**응답:**
```json
{
  "status": "success",
  "url": "https://www.qoo10.jp/...",
  "seo_analysis": {
    "score": 75,
    "meta_tags": {...},
    "title_optimization": {...},
    "description_optimization": {...},
    "recommendations": [...]
  }
}
```

### AI SEO 분석

```http
POST /api/v1/ai-seo/analyze
Content-Type: application/json

{
  "url": "https://www.qoo10.jp/gmkt.inc/Goods/Goods.aspx?goodscode=..."
}
```

**응답:**
```json
{
  "status": "success",
  "url": "https://www.qoo10.jp/...",
  "ai_seo_analysis": {
    "score": 70,
    "keyword_research": {...},
    "content_optimization": {...},
    "semantic_keywords": [...],
    "recommendations": [...]
  }
}
```

### GEO 분석

```http
POST /api/v1/geo/analyze
Content-Type: application/json

{
  "url": "https://www.qoo10.jp/gmkt.inc/Goods/Goods.aspx?goodscode=..."
}
```

**응답:**
```json
{
  "status": "success",
  "url": "https://www.qoo10.jp/...",
  "geo_analysis": {
    "score": 65,
    "schema_markup": {...},
    "faq_schema": {...},
    "citation_readiness": {...},
    "ai_engine_compatibility": {...},
    "recommendations": [...]
  }
}
```

### AIO 종합 분석

```http
POST /api/v1/aio/analyze
Content-Type: application/json

{
  "url": "https://www.qoo10.jp/gmkt.inc/Goods/Goods.aspx?goodscode=..."
}
```

**응답:**
```json
{
  "status": "success",
  "url": "https://www.qoo10.jp/...",
  "aio_analysis": {
    "overall_score": 70,
    "seo": {...},
    "ai_seo": {...},
    "geo": {...},
    "performance": {...},
    "accessibility": {...},
    "security": {...},
    "priority_actions": [...],
    "recommendations": [...]
  }
}
```

### AIO 자동 최적화

```http
POST /api/v1/aio/optimize
Content-Type: application/json

{
  "url": "https://www.qoo10.jp/gmkt.inc/Goods/Goods.aspx?goodscode=..."
}
```

### Sitemap 생성

```http
GET /api/v1/seo/sitemap?urls=https://example.com,https://example.com/about
```

**응답:** XML 형식의 sitemap 파일

### robots.txt 생성

```http
GET /api/v1/seo/robots?allowed_paths=/api,/public&disallowed_paths=/admin&sitemap_url=https://example.com/sitemap.xml
```

**응답:** robots.txt 파일

### FAQ 스키마 생성

```http
POST /api/v1/geo/faq-schema
Content-Type: application/json

{
  "questions": ["질문1", "질문2"],
  "answers": ["답변1", "답변2"]
}
```

### HowTo 스키마 생성

```http
POST /api/v1/geo/howto-schema
Content-Type: application/json

{
  "name": "상품 사용 가이드",
  "steps": ["단계1", "단계2", "단계3"],
  "description": "가이드 설명"
}
```

### AIO 리포트 생성

```http
POST /api/v1/aio/report?format=markdown
Content-Type: application/json

{
  "url": "https://www.qoo10.jp/gmkt.inc/Goods/Goods.aspx?goodscode=..."
}
```

**응답:** Markdown 또는 JSON 형식의 리포트

## 사용 예시

### Python 클라이언트 예시

```python
import httpx

async def analyze_product_seo(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8080/api/v1/aio/analyze",
            json={"url": url}
        )
        return response.json()

# 사용
result = await analyze_product_seo("https://www.qoo10.jp/...")
print(f"종합 점수: {result['aio_analysis']['overall_score']}/100")
```

### cURL 예시

```bash
# AIO 종합 분석
curl -X POST "http://localhost:8080/api/v1/aio/analyze" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.qoo10.jp/gmkt.inc/Goods/Goods.aspx?goodscode=..."}'

# Sitemap 생성
curl "http://localhost:8080/api/v1/seo/sitemap?urls=https://example.com,https://example.com/about" \
  -o sitemap.xml

# 리포트 생성 (Markdown)
curl -X POST "http://localhost:8080/api/v1/aio/report?format=markdown" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.qoo10.jp/..."}' \
  -o report.md
```

## 모듈 구조

```
api/services/
├── seo_optimizer.py          # SEO 최적화 모듈
├── ai_seo_optimizer.py        # AI SEO 최적화 모듈
├── geo_optimizer.py           # GEO 최적화 모듈
└── aio_optimizer.py           # AIO 종합 최적화 모듈
```

## 주요 클래스

### SEOOptimizer
- `analyze()`: SEO 분석 수행
- `generate_sitemap()`: XML sitemap 생성
- `generate_robots_txt()`: robots.txt 생성
- `generate_meta_tags()`: 메타 태그 생성

### AISEOOptimizer
- `analyze()`: AI SEO 분석 수행
- `optimize_content()`: 콘텐츠 최적화 제안
- `_research_keywords()`: 키워드 리서치
- `_analyze_content()`: 콘텐츠 분석

### GEOOptimizer
- `analyze()`: GEO 분석 수행
- `generate_faq_schema()`: FAQ 스키마 생성
- `generate_howto_schema()`: HowTo 스키마 생성
- `generate_article_schema()`: Article 스키마 생성
- `generate_llms_txt()`: llms.txt 생성

### AIOOptimizer
- `analyze()`: 종합 분석 수행
- `optimize()`: 자동 최적화 수행
- `generate_report()`: 리포트 생성

## 점수 체계

### SEO 점수 (0-100)
- 메타 태그: 50점
- 제목 최적화: 25점
- 설명 최적화: 25점

### AI SEO 점수 (0-100)
- 키워드 리서치: 20점
- 콘텐츠 구조: 30점
- AI 가독성: 50점

### GEO 점수 (0-100)
- 스키마 마크업: 45점
- 인용 가능성: 30점
- AI 엔진 호환성: 25점

### AIO 종합 점수 (0-100)
- SEO: 30%
- AI SEO: 30%
- GEO: 20%
- 성능: 10%
- 접근성: 5%
- 보안: 5%

## 추천사항 우선순위

AIO 분석 결과는 다음 우선순위로 액션을 제안합니다:

1. **High Priority**: SEO 점수 개선 (즉시 영향)
2. **Medium Priority**: AI SEO 및 GEO 개선 (중기 영향)
3. **Low Priority**: 성능 및 접근성 개선 (장기 영향)

## 통합 워크플로우

1. **상품 URL 입력** → 크롤링 → 상품 데이터 수집
2. **SEO/AIO/GEO 분석** → 종합 점수 계산
3. **최적화 제안 생성** → 우선순위별 액션 아이템
4. **리포트 생성** → Markdown 또는 JSON 형식
5. **스키마 생성** → FAQ, HowTo, Article 스키마
6. **Sitemap/Robots.txt 생성** → 검색 엔진 최적화

## 참고 자료

- [ai-visibility-optimizer GitHub](https://github.com/saewookkangboy/ai-visibility-optimizer)
- [Schema.org 문서](https://schema.org/)
- [Google Search Central](https://developers.google.com/search)
- [OpenAI GPTBot 문서](https://openai.com/gptbot)

## 향후 개선 사항

- [ ] 실시간 성능 측정 (PageSpeed Insights API 통합)
- [ ] 이미지 최적화 자동화
- [ ] 다국어 지원 (일본어, 영어)
- [ ] 배치 분석 기능
- [ ] AI 가시성 모니터링 대시보드
- [ ] 자동 반영 시스템 (Auto Injector)
