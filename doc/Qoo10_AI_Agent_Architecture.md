# Qoo10 Sales Intelligence Agent - 아키텍처 설계 문서

**문서 버전**: 1.0  
**작성일**: 2026-01-13  
**작성자**: Engineering Team  
**기반 문서**: Qoo10_AI_Agent_PRD.md

---

## 목차

1. [시스템 아키텍처 개요](#1-시스템-아키텍처-개요)
2. [Frontend 설계](#2-frontend-설계)
3. [Backend 설계](#3-backend-설계)
4. [데이터베이스 설계](#4-데이터베이스-설계)
5. [API 설계](#5-api-설계)
6. [인프라 및 배포](#6-인프라-및-배포)
7. [다국어 번역 시스템](#7-다국어-번역-시스템)

---

## 1. 시스템 아키텍처 개요

### 1.1 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Web App    │  │  Mobile Web  │  │   Admin UI   │     │
│  │  (Next.js)   │  │  (Responsive) │  │  (Optional)  │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                    ┌────────▼────────┐
                    │   API Gateway   │
                    │   (Nginx/Kong)  │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────▼─────┐    ┌──────▼──────┐    ┌─────▼─────┐    ┌─────▼─────┐
    │  Auth     │    │  Analysis   │    │  Crawler  │    │Translation│
    │ Service   │    │  Service    │    │  Service  │    │  Service  │
    └───────────┘    └──────┬───────┘    └──────┬────┘    └──────┬────┘
                            │                   │                │
                    ┌───────▼───────────────────▼────────────────▼───────┐
                    │      AI/ML Service                │                │
                    │  (LLM, Image Analysis, NLP)       │                │
                    └────────────────────────────────────┘                │
                                                                          │
                    ┌─────────────────────────────────────────────────────▼─────┐
                    │         Translation Service                               │
                    │  (한국어 ↔ 일본어 자동 번역, 번역 캐시)                  │
                    └──────────────────────────────────────────────────────────┘
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────▼─────┐    ┌──────▼──────┐    ┌─────▼─────┐
    │  MongoDB  │    │   Redis     │    │  S3/MinIO │
    │  (Primary)│    │  (Cache)    │    │  (Storage)│
    └───────────┘    └─────────────┘    └───────────┘
```

### 1.2 기술 스택

#### Frontend
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **UI Library**: React 18+
- **Styling**: Tailwind CSS
- **State Management**: Zustand / React Query
- **Chart Library**: Recharts / Chart.js
- **PDF Export**: jsPDF / react-pdf
- **i18n**: next-intl / react-i18next (다국어 지원)

#### Backend
- **Language**: Python 3.11+ (주요 서비스), Node.js (API Gateway)
- **Framework**: FastAPI (Python), Express.js (Node.js)
- **Web Scraping**: Playwright / Selenium
- **AI/ML**: OpenAI API / Anthropic Claude / Local LLM
- **Translation**: Google Translate API / DeepL API / OpenAI GPT-4
- **Image Processing**: Pillow, OpenCV
- **Task Queue**: Celery (Python) / Bull (Node.js)
- **Message Queue**: RabbitMQ / Redis

#### Database
- **Primary DB**: MongoDB 6.0+ (문서 기반, 확장성)
- **Cache**: Redis 7.0+
- **Object Storage**: AWS S3 / MinIO (이미지, 리포트 저장)

#### Infrastructure
- **Container**: Docker, Docker Compose
- **Orchestration**: Kubernetes (프로덕션)
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus, Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)

---

## 2. Frontend 설계

### 2.1 프로젝트 구조

```
frontend/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # 인증 관련 페이지
│   │   ├── login/
│   │   └── signup/
│   ├── (dashboard)/              # 대시보드 (인증 필요)
│   │   ├── analyze/              # 분석 페이지
│   │   │   ├── page.tsx
│   │   │   └── [id]/
│   │   ├── history/              # 히스토리 페이지
│   │   ├── settings/             # 설정 페이지
│   │   └── layout.tsx
│   ├── api/                      # API Routes (프록시)
│   ├── layout.tsx                # 루트 레이아웃
│   └── page.tsx                  # 랜딩 페이지
├── components/                    # 재사용 컴포넌트
│   ├── ui/                       # 기본 UI 컴포넌트
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Input.tsx
│   │   └── Modal.tsx
│   ├── analysis/                 # 분석 관련 컴포넌트
│   │   ├── UrlInputForm.tsx
│   │   ├── AnalysisProgress.tsx
│   │   ├── ReportCard.tsx
│   │   ├── ScoreCard.tsx
│   │   ├── ImprovementCard.tsx
│   │   └── CompetitorCard.tsx
│   ├── checklist/                # 체크리스트 컴포넌트
│   │   └── ChecklistCard.tsx
│   └── charts/                   # 차트 컴포넌트
│       ├── ScoreChart.tsx
│       └── ComparisonChart.tsx
├── lib/                          # 유틸리티 및 설정
│   ├── api/                      # API 클라이언트
│   │   ├── client.ts
│   │   ├── analysis.ts
│   │   ├── history.ts
│   │   └── translation.ts
│   ├── hooks/                    # Custom Hooks
│   │   ├── useAnalysis.ts
│   │   ├── useWebSocket.ts
│   │   └── useTranslation.ts
│   ├── utils/                    # 유틸리티 함수
│   │   ├── validation.ts
│   │   └── formatters.ts
│   ├── i18n/                     # 다국어 설정
│   │   ├── config.ts
│   │   ├── messages/
│   │   │   ├── ko.json
│   │   │   └── ja.json
│   │   └── locales.ts
│   └── constants/                # 상수
│       └── api.ts
├── store/                        # 상태 관리
│   ├── analysisStore.ts
│   ├── userStore.ts
│   └── localeStore.ts            # 언어 설정
├── types/                        # TypeScript 타입 정의
│   ├── analysis.ts
│   ├── api.ts
│   └── user.ts
├── styles/                       # 글로벌 스타일
│   └── globals.css
└── public/                       # 정적 파일
    ├── images/
    └── icons/
```

### 2.2 주요 페이지 및 컴포넌트

#### 2.2.1 분석 페이지 (`/analyze`)

**기능**:
- URL 입력 폼
- 분석 진행 상태 표시 (WebSocket 또는 Polling)
- 분석 결과 리포트 표시

**컴포넌트 구조**:
```typescript
// app/(dashboard)/analyze/page.tsx
<AnalyzePage>
  <UrlInputForm />
  <AnalysisProgress />
  <ReportDashboard>
    <ScoreCard />
    <AnalysisResultCard />
    <ImprovementCard />
    <CompetitorCard />
    <ChecklistCard />
  </ReportDashboard>
</AnalyzePage>
```

#### 2.2.2 리포트 카드 컴포넌트

**ScoreCard**: 종합 점수 및 개선 우선순위
```typescript
interface ScoreCardProps {
  overallScore: number;        // 0-100
  categoryScores: {
    image: number;
    seo: number;
    price: number;
    review: number;
  };
  priority: 'high' | 'medium' | 'low';
}
```

**AnalysisResultCard**: 상세 분석 결과
```typescript
interface AnalysisResultCardProps {
  type: 'image' | 'seo' | 'price' | 'review';
  score: number;
  details: AnalysisDetails;
  recommendations: string[];
}
```

**ImprovementCard**: 개선 제안
```typescript
interface ImprovementCardProps {
  category: 'seo' | 'advertising' | 'promotion' | 'page';
  priority: number;
  title: string;
  description: string;
  actionItems: ActionItem[];
}
```

### 2.3 상태 관리

#### Zustand Store 예시
```typescript
// store/analysisStore.ts
interface AnalysisState {
  currentAnalysis: Analysis | null;
  analysisHistory: Analysis[];
  isLoading: boolean;
  error: string | null;
  
  startAnalysis: (url: string) => Promise<void>;
  fetchAnalysis: (id: string) => Promise<void>;
  fetchHistory: () => Promise<void>;
}
```

### 2.4 API 통신

#### API Client 구조
```typescript
// lib/api/client.ts
class ApiClient {
  private baseURL: string;
  
  async post<T>(endpoint: string, data: any): Promise<T>;
  async get<T>(endpoint: string): Promise<T>;
  async delete<T>(endpoint: string): Promise<T>;
}

// lib/api/analysis.ts
export const analysisApi = {
  startAnalysis: (url: string) => 
    apiClient.post<AnalysisResponse>('/api/analysis/start', { url }),
  
  getAnalysis: (id: string) => 
    apiClient.get<Analysis>(`/api/analysis/${id}`),
  
  getProgress: (id: string) => 
    apiClient.get<ProgressResponse>(`/api/analysis/${id}/progress`),
};
```

### 2.5 반응형 디자인

**Breakpoints** (Tailwind CSS):
- Mobile: `< 640px`
- Tablet: `640px - 1024px`
- Desktop: `> 1024px`

**레이아웃 전략**:
- 모바일: 단일 컬럼, 카드 스택
- 태블릿: 2컬럼 그리드
- 데스크톱: 3-4컬럼 그리드

### 2.6 다국어 지원 (i18n)

#### 2.6.1 언어 설정

**지원 언어**:
- 한국어 (ko) - 기본
- 일본어 (ja)

**구현 방식**:
- next-intl 또는 react-i18next 사용
- 언어 선택 드롭다운 (헤더/설정)
- 브라우저 언어 자동 감지
- 사용자 언어 설정 저장 (DB)

**컴포넌트 예시**:
```typescript
// components/ui/LanguageSelector.tsx
interface LanguageSelectorProps {
  currentLocale: 'ko' | 'ja';
  onLocaleChange: (locale: 'ko' | 'ja') => void;
}

// lib/hooks/useTranslation.ts
export const useTranslation = () => {
  const { locale, setLocale, t } = useI18n();
  
  const translateAnalysis = async (text: string, targetLang: 'ko' | 'ja') => {
    // API를 통해 실시간 번역 또는 캐시된 번역 사용
    return await translationApi.translate(text, targetLang);
  };
  
  return { locale, setLocale, t, translateAnalysis };
};
```

#### 2.6.2 번역 전략

1. **정적 콘텐츠**: i18n JSON 파일에 저장
2. **동적 콘텐츠**: API를 통한 실시간 번역
3. **분석 결과**: 번역 캐시 활용 (성능 최적화)
4. **사용자 입력**: 원본 언어 유지, 필요시 번역

### 2.7 성능 최적화

- **코드 스플리팅**: Next.js Dynamic Import
- **이미지 최적화**: Next.js Image 컴포넌트
- **캐싱**: React Query 캐싱 전략
- **번들 최적화**: Tree shaking, Minification
- **번역 캐싱**: 번역 결과 Redis 캐시

---

## 3. Backend 설계

### 3.1 마이크로서비스 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    API Gateway                          │
│  - 라우팅, 인증, Rate Limiting, 로깅                    │
└──────────────┬──────────────────────────────────────────┘
               │
    ┌──────────┼──────────┬──────────────┬──────────────┐
    │          │          │              │              │
┌───▼───┐ ┌───▼───┐ ┌───▼───┐ ┌────────▼────┐ ┌─────▼─────┐
│ Auth  │ │Analysis│ │Crawler│ │ Notification│ │Translation│
│Service│ │Service │ │Service│ │  Service   │ │  Service  │
└───────┘ └───┬────┘ └───┬───┘ └────────────┘ └─────┬─────┘
              │          │                            │
        ┌─────▼──────────▼───────────────────────────▼─────┐
        │    AI/ML Service      │    Translation Service    │
        │  - LLM Analysis       │  - 한국어 ↔ 일본어 번역   │
        │  - Image Processing   │  - 번역 캐시 관리        │
        │  - NLP Processing     │  - 배치 번역 처리        │
        └───────────────────────┴───────────────────────────┘
```

### 3.2 서비스별 상세 설계

#### 3.2.1 API Gateway Service

**기술 스택**: Node.js + Express.js / Kong

**기능**:
- 요청 라우팅
- 인증/인가 (JWT)
- Rate Limiting
- 요청/응답 로깅
- CORS 처리

**구조**:
```
api-gateway/
├── src/
│   ├── routes/
│   │   ├── analysis.ts
│   │   ├── auth.ts
│   │   └── history.ts
│   ├── middleware/
│   │   ├── auth.ts
│   │   ├── rateLimit.ts
│   │   └── logger.ts
│   └── config/
│       └── services.ts
```

#### 3.2.2 Crawler Service

**기술 스택**: Python + FastAPI + Playwright

**기능**:
- Qoo10 상품 페이지 크롤링
- Shop 페이지 크롤링
- 이미지 다운로드
- robots.txt 준수

**구조**:
```
crawler-service/
├── src/
│   ├── crawlers/
│   │   ├── product_crawler.py
│   │   ├── shop_crawler.py
│   │   └── competitor_crawler.py
│   ├── parsers/
│   │   ├── product_parser.py
│   │   └── shop_parser.py
│   ├── validators/
│   │   └── url_validator.py
│   └── main.py
```

**주요 클래스**:
```python
class ProductCrawler:
    async def crawl(self, url: str) -> ProductData:
        """상품 페이지 크롤링"""
        pass
    
    async def extract_images(self, html: str) -> List[ImageData]:
        """이미지 추출"""
        pass
    
    async def extract_reviews(self, html: str) -> List[Review]:
        """리뷰 추출"""
        pass

class ShopCrawler:
    async def crawl(self, url: str) -> ShopData:
        """Shop 페이지 크롤링"""
        pass
    
    async def get_category_products(self, category: str) -> List[Product]:
        """카테고리별 상품 목록"""
        pass
```

#### 3.2.3 Analysis Service

**기술 스택**: Python + FastAPI + Celery

**기능**:
- 분석 작업 오케스트레이션
- 크롤링 결과 분석
- 리포트 생성
- 히스토리 관리

**구조**:
```
analysis-service/
├── src/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── analysis.py
│   │   │   └── history.py
│   │   └── main.py
│   ├── services/
│   │   ├── analysis_service.py
│   │   ├── report_service.py
│   │   └── history_service.py
│   ├── tasks/
│   │   └── analysis_tasks.py  # Celery tasks
│   └── models/
│       └── analysis.py
```

**주요 서비스**:
```python
class AnalysisService:
    async def start_analysis(self, url: str, user_id: str) -> str:
        """분석 작업 시작 (비동기)"""
        task = analyze_product.delay(url, user_id)
        return task.id
    
    async def get_analysis(self, analysis_id: str) -> Analysis:
        """분석 결과 조회"""
        pass

@celery_app.task
def analyze_product(url: str, user_id: str) -> Analysis:
    """상품 분석 작업 (Celery Task)"""
    # 1. 크롤링
    # 2. AI 분석
    # 3. 리포트 생성
    # 4. DB 저장
    pass
```

#### 3.2.4 AI/ML Service

**기술 스택**: Python + FastAPI + OpenAI/Claude API

**기능**:
- 이미지 품질 분석
- SEO 분석 (NLP)
- 가격 전략 분석
- 매출 강화 아이디어 생성
- 체크리스트 생성

**구조**:
```
ai-service/
├── src/
│   ├── services/
│   │   ├── image_analyzer.py
│   │   ├── seo_analyzer.py
│   │   ├── price_analyzer.py
│   │   ├── idea_generator.py
│   │   └── checklist_generator.py
│   ├── models/
│   │   └── manual_embedding.py  # 메뉴얼 임베딩
│   └── prompts/
│       ├── seo_prompt.txt
│       └── improvement_prompt.txt
```

**주요 서비스**:
```python
class ImageAnalyzer:
    def analyze_quality(self, images: List[Image]) -> ImageAnalysis:
        """이미지 품질 분석"""
        pass
    
    def count_images(self, images: List[Image]) -> ImageCount:
        """이미지 개수 및 구성 분석"""
        pass

class SEOAnalyzer:
    def analyze_keywords(self, description: str) -> SEOAnalysis:
        """키워드 분석"""
        pass
    
    def check_optimization(self, product_data: ProductData) -> SEOReport:
        """SEO 최적화 체크"""
        pass

class IdeaGenerator:
    def __init__(self, manual_embedding: ManualEmbedding):
        self.manual = manual_embedding
    
    def generate_ideas(self, analysis: Analysis) -> List[ImprovementIdea]:
        """메뉴얼 기반 개선 아이디어 생성"""
        # LLM + 메뉴얼 임베딩 검색
        pass
```

### 3.3 비동기 작업 처리

**Celery Task Queue 구조**:
```python
# tasks/analysis_tasks.py
from celery import Celery

celery_app = Celery('qoo10_agent')

@celery_app.task(bind=True)
def analyze_product(self, url: str, user_id: str):
    """상품 분석 전체 프로세스"""
    try:
        # 1. 크롤링 (20%)
        self.update_state(state='CRAWLING', meta={'progress': 20})
        product_data = crawler.crawl(url)
        
        # 2. 이미지 분석 (40%)
        self.update_state(state='ANALYZING_IMAGE', meta={'progress': 40})
        image_analysis = image_analyzer.analyze(product_data.images)
        
        # 3. SEO 분석 (60%)
        self.update_state(state='ANALYZING_SEO', meta={'progress': 60})
        seo_analysis = seo_analyzer.analyze(product_data.description)
        
        # 4. 아이디어 생성 (80%)
        self.update_state(state='GENERATING_IDEAS', meta={'progress': 80})
        ideas = idea_generator.generate(image_analysis, seo_analysis)
        
        # 5. 리포트 생성 (100%)
        self.update_state(state='GENERATING_REPORT', meta={'progress': 100})
        report = report_service.create(product_data, image_analysis, seo_analysis, ideas)
        
        return report
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise
```

#### 3.2.5 Translation Service

**기술 스택**: Python + FastAPI + Google Translate API / DeepL API / OpenAI GPT-4

**기능**:
- 한국어 ↔ 일본어 양방향 번역
- 번역 결과 캐싱 (성능 최적화)
- 배치 번역 처리
- 분석 결과 자동 번역
- 번역 품질 평가

**구조**:
```
translation-service/
├── src/
│   ├── api/
│   │   ├── routes/
│   │   │   └── translation.py
│   │   └── main.py
│   ├── services/
│   │   ├── translation_service.py
│   │   ├── cache_service.py
│   │   └── batch_translation_service.py
│   ├── providers/
│   │   ├── google_translate.py
│   │   ├── deepl_translate.py
│   │   └── openai_translate.py
│   └── models/
│       └── translation.py
```

**주요 서비스**:
```python
class TranslationService:
    def __init__(self):
        self.cache = RedisCache()
        self.provider = GoogleTranslateProvider()  # 또는 DeepL, OpenAI
    
    async def translate(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str,
        use_cache: bool = True
    ) -> TranslationResult:
        """텍스트 번역 (캐시 우선)"""
        # 1. 캐시 확인
        if use_cache:
            cached = await self.cache.get_translation(text, source_lang, target_lang)
            if cached:
                return cached
        
        # 2. 번역 실행
        result = await self.provider.translate(text, source_lang, target_lang)
        
        # 3. 캐시 저장
        await self.cache.save_translation(text, source_lang, target_lang, result)
        
        return result
    
    async def translate_analysis(
        self, 
        analysis: Analysis, 
        target_lang: str
    ) -> TranslatedAnalysis:
        """분석 결과 전체 번역"""
        # 분석 결과의 모든 텍스트 필드 번역
        translated = {
            'recommendations': await self.batch_translate(
                analysis.recommendations, 
                target_lang
            ),
            'improvement_ideas': await self.translate_ideas(
                analysis.improvement_ideas,
                target_lang
            ),
            # ... 기타 필드
        }
        return TranslatedAnalysis(**translated)
    
    async def batch_translate(
        self, 
        texts: List[str], 
        target_lang: str
    ) -> List[str]:
        """배치 번역 (성능 최적화)"""
        # 여러 텍스트를 한 번에 번역
        pass

class TranslationProvider:
    """번역 제공자 인터페이스"""
    async def translate(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str
    ) -> TranslationResult:
        pass

class GoogleTranslateProvider(TranslationProvider):
    """Google Translate API 구현"""
    async def translate(self, text: str, source_lang: str, target_lang: str):
        # Google Translate API 호출
        pass

class DeepLProvider(TranslationProvider):
    """DeepL API 구현 (고품질 번역)"""
    async def translate(self, text: str, source_lang: str, target_lang: str):
        # DeepL API 호출
        pass
```

**번역 캐시 전략**:
```python
class TranslationCache:
    """번역 결과 캐시 관리"""
    
    async def get_translation(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str
    ) -> Optional[TranslationResult]:
        """캐시에서 번역 결과 조회"""
        cache_key = f"translation:{hash(text)}:{source_lang}:{target_lang}"
        return await redis.get(cache_key)
    
    async def save_translation(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str, 
        result: TranslationResult
    ):
        """번역 결과 캐시 저장 (TTL: 30일)"""
        cache_key = f"translation:{hash(text)}:{source_lang}:{target_lang}"
        await redis.setex(cache_key, 2592000, result)  # 30일
```

### 3.4 에러 처리 및 재시도

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def crawl_with_retry(url: str) -> ProductData:
    """재시도 로직이 포함된 크롤링"""
    pass

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=5)
)
async def translate_with_retry(text: str, target_lang: str) -> str:
    """재시도 로직이 포함된 번역"""
    pass
```

---

## 4. 데이터베이스 설계

### 4.1 MongoDB 스키마 설계

#### 4.1.1 Users Collection

```javascript
{
  _id: ObjectId,
  email: String,              // 이메일 (unique)
  password_hash: String,       // 암호화된 비밀번호
  name: String,
  role: String,               // 'user' | 'admin'
  created_at: ISODate,
  updated_at: ISODate,
  last_login: ISODate,
  subscription: {
    plan: String,             // 'free' | 'premium'
    expires_at: ISODate
  }
}

// 인덱스
db.users.createIndex({ email: 1 }, { unique: true })
db.users.createIndex({ created_at: -1 })
```

#### 4.1.2 Analyses Collection

```javascript
{
  _id: ObjectId,
  user_id: ObjectId,          // Users 참조
  url: String,                // 분석 대상 URL
  url_type: String,           // 'product' | 'shop'
  status: String,             // 'pending' | 'processing' | 'completed' | 'failed'
  progress: Number,           // 0-100
  created_at: ISODate,
  completed_at: ISODate,
  
  // 분석 결과
  scores: {
    overall: Number,          // 0-100
    image: Number,
    seo: Number,
    price: Number,
    review: Number
  },
  
  // 상품 데이터 (크롤링 결과)
  product_data: {
    title: String,
    price: Number,
    original_price: Number,
    discount_rate: Number,
    category: String,
    shop_name: String,
    shop_level: String,
    images: [{
      url: String,
      type: String,           // 'thumbnail' | 'detail'
      quality_score: Number
    }],
    description: String,
    reviews: {
      average_rating: Number,
      total_count: Number,
      positive_count: Number,
      negative_count: Number
    }
  },
  
  // 분석 상세
  analysis_details: {
    image_analysis: {
      thumbnail_count: Number,
      detail_image_count: Number,
      quality_scores: [Number],
      recommendations: [String]
    },
    seo_analysis: {
      keyword_density: Map,
      description_length: Number,
      keyword_optimization: Boolean,
      recommendations: [String]
    },
    price_analysis: {
      competitor_avg_price: Number,
      price_position: String,  // 'high' | 'medium' | 'low'
      discount_strategy: String,
      recommendations: [String]
    },
    review_analysis: {
      sentiment_score: Number,
      common_issues: [String],
      recommendations: [String]
    }
  },
  
  // 개선 제안
  improvement_ideas: [{
    category: String,         // 'seo' | 'advertising' | 'promotion' | 'page'
    priority: Number,         // 1-10
    title: String,
    description: String,
    action_items: [String]
  }],
  
  // 체크리스트
  checklist: {
    sales_preparation: [{
      item: String,
      checked: Boolean,
      description: String
    }],
    sales_improvement: [{
      item: String,
      checked: Boolean,
      description: String
    }],
    advertising: [{
      item: String,
      checked: Boolean,
      description: String
    }]
  },
  
  // 경쟁사 비교
  competitor_analysis: {
    category: String,
    top_10_products: [{
      product_id: String,
      title: String,
      price: Number,
      rating: Number,
      review_count: Number,
      comparison_score: Number
    }]
  }
}

// 인덱스
db.analyses.createIndex({ user_id: 1, created_at: -1 })
db.analyses.createIndex({ url: 1 })
db.analyses.createIndex({ status: 1 })
db.analyses.createIndex({ created_at: -1 })
```

#### 4.1.3 Analysis History Collection

```javascript
{
  _id: ObjectId,
  analysis_id: ObjectId,      // Analyses 참조
  user_id: ObjectId,
  url: String,
  snapshot_date: ISODate,
  
  // 스냅샷 데이터 (분석 시점의 데이터)
  scores: {
    overall: Number,
    image: Number,
    seo: Number,
    price: Number,
    review: Number
  },
  product_data: { /* ... */ },
  improvement_ideas: [ /* ... */ ]
}

// 인덱스
db.analysis_history.createIndex({ analysis_id: 1, snapshot_date: -1 })
db.analysis_history.createIndex({ user_id: 1, snapshot_date: -1 })
```

#### 4.1.4 Manuals Collection (메뉴얼 저장)

```javascript
{
  _id: ObjectId,
  title: String,
  category: String,           // 'seo' | 'advertising' | 'promotion' | 'checklist'
  content: String,            // 메뉴얼 본문
  embedding: [Number],        // 벡터 임베딩 (AI 검색용)
  version: String,
  created_at: ISODate,
  updated_at: ISODate
}

// 인덱스
db.manuals.createIndex({ category: 1 })
db.manuals.createIndex({ embedding: "2dsphere" })  // 벡터 검색용
```

#### 4.1.5 Notifications Collection

```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  analysis_id: ObjectId,
  type: String,               // 'price_change' | 'new_review' | 'competitor_update'
  title: String,
  message: String,
  read: Boolean,
  created_at: ISODate
}

// 인덱스
db.notifications.createIndex({ user_id: 1, read: 1, created_at: -1 })
```

#### 4.1.6 Translations Collection (번역 캐시)

```javascript
{
  _id: ObjectId,
  text_hash: String,           // 원본 텍스트 해시
  source_text: String,        // 원본 텍스트
  source_lang: String,         // 'ko' | 'ja'
  target_lang: String,         // 'ko' | 'ja'
  translated_text: String,    // 번역된 텍스트
  provider: String,           // 'google' | 'deepl' | 'openai'
  quality_score: Number,      // 번역 품질 점수 (0-100)
  created_at: ISODate,
  updated_at: ISODate,
  access_count: Number,       // 접근 횟수
  last_accessed: ISODate
}

// 인덱스
db.translations.createIndex({ text_hash: 1, source_lang: 1, target_lang: 1 }, { unique: true })
db.translations.createIndex({ last_accessed: -1 })  // LRU 캐시 정리용
```

#### 4.1.7 User Preferences Collection (사용자 설정)

```javascript
{
  _id: ObjectId,
  user_id: ObjectId,          // Users 참조
  preferred_language: String,  // 'ko' | 'ja'
  auto_translate: Boolean,     // 자동 번역 활성화 여부
  translation_provider: String, // 'google' | 'deepl' | 'openai'
  created_at: ISODate,
  updated_at: ISODate
}

// 인덱스
db.user_preferences.createIndex({ user_id: 1 }, { unique: true })
```

### 4.2 Redis 캐시 구조

#### 4.2.1 캐시 키 전략

```
# 분석 진행 상태
analysis:progress:{analysis_id} -> { progress: 20, status: "CRAWLING" }

# 분석 결과 캐시 (TTL: 1시간)
analysis:result:{analysis_id} -> { ...analysis_data }

# 경쟁사 데이터 캐시 (TTL: 6시간)
competitor:category:{category} -> [ ...products ]

# 사용자 세션
session:{session_id} -> { user_id, expires_at }

# Rate Limiting
ratelimit:user:{user_id} -> { count, reset_at }

# 번역 캐시 (TTL: 30일)
translation:{text_hash}:{source_lang}:{target_lang} -> { translated_text, provider, quality_score }

# 사용자 언어 설정
user:locale:{user_id} -> { locale: 'ko' | 'ja', auto_translate: boolean }
```

### 4.3 Object Storage 구조 (S3/MinIO)

```
s3://qoo10-agent/
├── images/
│   ├── products/
│   │   └── {product_id}/
│   │       ├── thumbnail.jpg
│   │       └── detail_*.jpg
│   └── shops/
│       └── {shop_id}/
│           └── logo.jpg
├── reports/
│   └── {analysis_id}/
│       ├── report.pdf
│       └── report.xlsx
└── crawler-cache/
    └── {url_hash}/
        └── snapshot.html
```

---

## 5. API 설계

### 5.1 REST API 엔드포인트

#### 5.1.1 인증 API

```
POST   /api/auth/register          # 회원가입
POST   /api/auth/login             # 로그인
POST   /api/auth/logout            # 로그아웃
POST   /api/auth/refresh           # 토큰 갱신
GET    /api/auth/me                # 현재 사용자 정보
```

#### 5.1.2 분석 API

```
POST   /api/analysis/start         # 분석 시작
GET    /api/analysis/{id}          # 분석 결과 조회
GET    /api/analysis/{id}/progress # 분석 진행 상태
DELETE /api/analysis/{id}          # 분석 삭제
```

**요청/응답 예시**:

```typescript
// POST /api/analysis/start
Request:
{
  url: "https://www.qoo10.jp/gmkt.inc/Goods/Goods.aspx?goodscode=...",
  url_type: "product"  // optional, auto-detect
}

Response:
{
  analysis_id: "507f1f77bcf86cd799439011",
  status: "pending",
  estimated_time: 30  // seconds
}

// GET /api/analysis/{id}
Response:
{
  id: "507f1f77bcf86cd799439011",
  status: "completed",
  scores: {
    overall: 75,
    image: 80,
    seo: 70,
    price: 75,
    review: 80
  },
  product_data: { /* ... */ },
  analysis_details: { /* ... */ },
  improvement_ideas: [ /* ... */ ],
  checklist: { /* ... */ },
  competitor_analysis: { /* ... */ }
}

// GET /api/analysis/{id}/progress
Response:
{
  status: "processing",
  progress: 60,
  current_step: "ANALYZING_SEO",
  estimated_remaining: 12  // seconds
}
```

#### 5.1.3 히스토리 API

```
GET    /api/history                # 분석 히스토리 목록
GET    /api/history/{id}           # 특정 히스토리 조회
POST   /api/history/{id}/snapshot  # 스냅샷 생성
GET    /api/history/{id}/compare   # 시점별 비교
```

#### 5.1.4 리포트 API

```
GET    /api/reports/{id}/pdf       # PDF 다운로드
GET    /api/reports/{id}/excel     # Excel 다운로드
```

#### 5.1.5 번역 API

```
POST   /api/translation/translate        # 텍스트 번역
POST   /api/translation/batch            # 배치 번역
POST   /api/translation/analysis/{id}    # 분석 결과 번역
GET    /api/translation/cache/{hash}     # 번역 캐시 조회
```

**요청/응답 예시**:

```typescript
// POST /api/translation/translate
Request:
{
  text: "상품 이미지 품질을 개선하세요",
  source_lang: "ko",
  target_lang: "ja",
  use_cache: true
}

Response:
{
  translated_text: "商品画像の品質を改善してください",
  source_text: "상품 이미지 품질을 개선하세요",
  source_lang: "ko",
  target_lang: "ja",
  provider: "google",
  quality_score: 95,
  cached: true
}

// POST /api/translation/analysis/{id}
Request:
{
  analysis_id: "507f1f77bcf86cd799439011",
  target_lang: "ja",
  fields: ["recommendations", "improvement_ideas", "checklist"]  // optional
}

Response:
{
  analysis_id: "507f1f77bcf86cd799439011",
  translated_analysis: {
    recommendations: ["商品画像の品質を改善してください", ...],
    improvement_ideas: [{
      title: "SEO最適化の改善",
      description: "検索キーワードを最適化...",
      ...
    }],
    ...
  },
  translation_time: 1.2  // seconds
}
```

#### 5.1.6 사용자 설정 API

```
GET    /api/user/preferences        # 사용자 설정 조회
PUT    /api/user/preferences        # 사용자 설정 업데이트
GET    /api/user/locale            # 사용자 언어 설정 조회
PUT    /api/user/locale            # 사용자 언어 설정 업데이트
```

### 5.2 WebSocket API (실시간 진행 상태)

```
WS     /ws/analysis/{id}           # 분석 진행 상태 실시간 업데이트

Message Format:
{
  type: "progress",
  analysis_id: "507f1f77bcf86cd799439011",
  progress: 60,
  status: "ANALYZING_SEO",
  message: "SEO 분석 중..."
}
```

### 5.3 API 응답 표준

```typescript
// 성공 응답
{
  success: true,
  data: { /* ... */ },
  message?: string
}

// 에러 응답
{
  success: false,
  error: {
    code: "ANALYSIS_FAILED",
    message: "분석 중 오류가 발생했습니다.",
    details?: any
  }
}
```

### 5.4 Rate Limiting

- **무료 사용자**: 10회/일
- **프리미엄 사용자**: 100회/일
- **API 엔드포인트별**: 
  - `/api/analysis/start`: 1회/분
  - 기타: 100회/분

---

## 6. 인프라 및 배포

### 6.1 Docker Compose 설정 (개발 환경)

```yaml
version: '3.8'

services:
  # MongoDB
  mongodb:
    image: mongo:6.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password

  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # MinIO (Object Storage)
  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data

  # RabbitMQ
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: admin
      RABBITMQ_DEFAULT_PASS: admin

  # API Gateway
  api-gateway:
    build: ./api-gateway
    ports:
      - "3000:3000"
    depends_on:
      - mongodb
      - redis
    environment:
      MONGODB_URI: mongodb://admin:password@mongodb:27017
      REDIS_URI: redis://redis:6379

  # Analysis Service
  analysis-service:
    build: ./analysis-service
    depends_on:
      - mongodb
      - redis
      - rabbitmq
    environment:
      MONGODB_URI: mongodb://admin:password@mongodb:27017
      REDIS_URI: redis://redis:6379
      RABBITMQ_URI: amqp://admin:admin@rabbitmq:5672

  # Crawler Service
  crawler-service:
    build: ./crawler-service
    depends_on:
      - mongodb
      - redis
    environment:
      MONGODB_URI: mongodb://admin:password@mongodb:27017
      REDIS_URI: redis://redis:6379

  # Celery Worker
  celery-worker:
    build: ./analysis-service
    command: celery -A tasks.celery_app worker --loglevel=info
    depends_on:
      - mongodb
      - redis
      - rabbitmq
    environment:
      MONGODB_URI: mongodb://admin:password@mongodb:27017
      REDIS_URI: redis://redis:6379
      RABBITMQ_URI: amqp://admin:admin@rabbitmq:5672

  # Translation Service
  translation-service:
    build: ./translation-service
    ports:
      - "8003:8000"
    depends_on:
      - mongodb
      - redis
    environment:
      MONGODB_URI: mongodb://admin:password@mongodb:27017
      REDIS_URI: redis://redis:6379
      GOOGLE_TRANSLATE_API_KEY: ${GOOGLE_TRANSLATE_API_KEY}
      DEEPL_API_KEY: ${DEEPL_API_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      DEFAULT_PROVIDER: google

  # Frontend
  frontend:
    build: ./frontend
    ports:
      - "3001:3000"
    depends_on:
      - api-gateway
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:3000
      NEXT_PUBLIC_DEFAULT_LOCALE: ko

volumes:
  mongodb_data:
  minio_data:
```

### 6.2 프로덕션 배포 (Kubernetes)

**주요 리소스**:
- Deployment: 각 마이크로서비스
- Service: 서비스 간 통신
- Ingress: 외부 접근
- ConfigMap: 설정 관리
- Secret: 민감 정보 관리
- HorizontalPodAutoscaler: 자동 스케일링

### 6.3 모니터링 및 로깅

- **메트릭**: Prometheus + Grafana
- **로깅**: ELK Stack
- **트레이싱**: Jaeger (분산 추적)
- **알림**: AlertManager

### 6.4 보안

- **HTTPS**: TLS/SSL 인증서
- **인증**: JWT 토큰
- **암호화**: 민감 데이터 암호화 저장
- **방화벽**: 네트워크 보안 그룹
- **DDoS 방어**: Cloudflare / AWS Shield

---

## 7. 다국어 번역 시스템

### 7.1 번역 시스템 개요

**목적**: 한국어와 일본어 사용자 모두가 서비스를 원활하게 이용할 수 있도록 양방향 자동 번역 제공

**주요 기능**:
- 실시간 텍스트 번역 (한국어 ↔ 일본어)
- 분석 결과 자동 번역
- 번역 결과 캐싱 (성능 최적화)
- 배치 번역 처리
- 번역 품질 평가

### 7.2 번역 제공자 선택

#### 7.2.1 Google Translate API
- **장점**: 빠른 속도, 저렴한 비용, 안정성
- **단점**: 상대적으로 낮은 품질
- **용도**: 일반적인 텍스트 번역

#### 7.2.2 DeepL API
- **장점**: 매우 높은 번역 품질
- **단점**: 상대적으로 높은 비용
- **용도**: 중요한 분석 결과, 리포트 번역

#### 7.2.3 OpenAI GPT-4
- **장점**: 컨텍스트 이해, 자연스러운 번역
- **단점**: 높은 비용, 느린 속도
- **용도**: 복잡한 분석 설명, 개선 제안

**전략**: 
- 기본: Google Translate (빠르고 저렴)
- 중요 콘텐츠: DeepL (고품질)
- 복잡한 설명: OpenAI GPT-4 (컨텍스트 이해)

### 7.3 번역 캐싱 전략

#### 7.3.1 캐시 계층

1. **Redis 캐시** (1차 캐시)
   - TTL: 30일
   - 빠른 조회 (밀리초 단위)
   - 자주 사용되는 번역 결과

2. **MongoDB** (2차 캐시)
   - 영구 저장
   - 통계 및 분석용
   - LRU 기반 자동 정리

#### 7.3.2 캐시 키 구조

```
Redis:
translation:{text_hash}:{source_lang}:{target_lang}

예시:
translation:abc123def456:ko:ja -> "商品画像の品質を改善してください"
```

#### 7.3.3 캐시 히트율 최적화

- 텍스트 정규화 (공백, 대소문자 통일)
- 유사 텍스트 그룹핑
- 자주 번역되는 템플릿 미리 번역

### 7.4 번역 워크플로우

#### 7.4.1 실시간 번역 플로우

```
사용자 요청
    ↓
캐시 확인 (Redis)
    ↓ (Miss)
번역 API 호출 (Google/DeepL/OpenAI)
    ↓
결과 캐시 저장 (Redis + MongoDB)
    ↓
사용자에게 반환
```

#### 7.4.2 분석 결과 번역 플로우

```
분석 완료
    ↓
번역 대상 필드 추출
    ↓
배치 번역 요청
    ↓
병렬 번역 처리
    ↓
번역 결과 병합
    ↓
번역된 분석 결과 저장
    ↓
사용자에게 반환
```

### 7.5 번역 품질 관리

#### 7.5.1 품질 평가

```python
class TranslationQuality:
    def evaluate(self, source: str, translated: str) -> float:
        """번역 품질 평가 (0-100)"""
        # 1. 길이 비율 체크
        # 2. 특수 문자 보존 확인
        # 3. 의미 보존도 (선택적, LLM 사용)
        # 4. 문법 검사
        return quality_score
```

#### 7.5.2 번역 개선

- 사용자 피드백 수집
- 번역 오류 리포트
- 자동 재번역 (낮은 품질 점수 시)

### 7.6 Frontend 통합

#### 7.6.1 언어 선택 UI

```typescript
// components/ui/LanguageSelector.tsx
export const LanguageSelector = () => {
  const { locale, setLocale } = useTranslation();
  
  return (
    <Select value={locale} onChange={setLocale}>
      <Option value="ko">한국어</Option>
      <Option value="ja">日本語</Option>
    </Select>
  );
};
```

#### 7.6.2 자동 번역 토글

```typescript
// 사용자가 언어를 변경하면 자동으로 콘텐츠 번역
useEffect(() => {
  if (autoTranslate && analysis) {
    translateAnalysis(analysis, locale);
  }
}, [locale, autoTranslate]);
```

### 7.7 성능 최적화

- **병렬 번역**: 여러 텍스트 동시 번역
- **배치 처리**: 여러 요청을 묶어서 처리
- **캐시 우선**: 캐시 히트율 최대화
- **지연 로딩**: 필요할 때만 번역

### 7.8 비용 관리

- **캐시 활용**: 중복 번역 최소화
- **번역 제공자 선택**: 용도에 맞는 제공자 선택
- **사용량 모니터링**: API 사용량 추적
- **Rate Limiting**: 과도한 요청 방지

---

## 8. 개발 로드맵

### Phase 1 (MVP - 3개월)
- [ ] Frontend: URL 입력 및 리포트 표시
- [ ] Backend: 기본 크롤링 및 분석 서비스
- [ ] DB: 기본 스키마 설계 및 구현
- [ ] AI: 기본 이미지/SEO 분석
- [ ] Translation: 기본 번역 서비스 (한국어 ↔ 일본어)
- [ ] Frontend: i18n 설정 및 언어 선택 기능

### Phase 2 (4-6개월)
- [ ] Shop 카테고리 분석
- [ ] 체크리스트 기능
- [ ] 경쟁사 비교 분석
- [ ] 리포트 다운로드
- [ ] Translation: 분석 결과 자동 번역
- [ ] Translation: 번역 캐시 최적화
- [ ] Translation: 배치 번역 기능

### Phase 3 (7-9개월)
- [ ] 히스토리 관리
- [ ] 알림 기능
- [ ] 배치 분석
- [ ] 성능 최적화

---

**문서 승인**

- [ ] Engineering Lead
- [ ] Backend Lead
- [ ] Frontend Lead
- [ ] DevOps Lead
