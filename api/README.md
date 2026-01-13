# Qoo10 AI Agent - FastAPI Backend

## 설치

```bash
cd api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 실행

```bash
# 개발 모드
uvicorn main:app --reload --host 0.0.0.0 --port 8080

# 또는
python main.py
```

## API 문서

서버 실행 후 다음 URL에서 API 문서 확인:
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## 주요 기능

### 1. AI 강화 학습 시스템
크롤러는 모든 크롤링 데이터를 자동으로 학습하여 성능을 지속적으로 개선합니다:
- **선택자 최적화**: CSS 선택자의 성공률을 추적하고 가장 효과적인 선택자를 우선 사용
- **데이터 품질 평가**: 추출된 데이터의 완전성을 평가하고 개선
- **성능 추적**: 크롤링 성공률, 응답 시간 등을 기록하고 분석

### 2. 방화벽 우회 기능
Qoo10 사이트의 제한을 우회하기 위한 다양한 기능:
- **User-Agent 로테이션**: 여러 User-Agent를 자동으로 로테이션하며 가장 성공률이 높은 것을 학습
- **프록시 지원**: 프록시 서버를 통한 요청 (환경 변수로 설정)
- **지능형 재시도**: 실패 시 다른 User-Agent와 프록시로 자동 재시도
- **랜덤 지연**: 요청 간 랜덤 지연으로 자연스러운 트래픽 패턴 생성
- **세션 관리**: 쿠키를 유지하여 세션 기반 제한 우회

### 3. 데이터베이스 저장
모든 크롤링 데이터는 SQLite 데이터베이스에 자동 저장됩니다:
- 크롤링된 상품 데이터 저장
- 크롤링 성능 통계 기록
- 선택자 성능 추적
- User-Agent 및 프록시 성능 추적

## 주요 엔드포인트

### 분석 시작
```
POST /api/v1/analyze
Body: {
  "url": "https://www.qoo10.jp/gmkt.inc/Goods/Goods.aspx?goodscode=..."
}
```

### 분석 결과 조회
```
GET /api/v1/analyze/{analysis_id}
```

### 크롤러 통계 조회
```
GET /api/v1/crawler/statistics
```
크롤링 성공률, 평균 응답 시간, 최근 24시간 통계 등을 반환합니다.

## 환경 변수

`.env` 파일을 생성하여 다음 변수를 설정하세요:

```bash
# 프록시 설정 (선택사항, 쉼표로 구분)
PROXY_LIST=http://proxy1.example.com:8080,http://proxy2.example.com:8080

# 기타 환경 변수
# ...
```

## 데이터베이스

크롤링 데이터는 `api/crawler_data.db` SQLite 데이터베이스에 저장됩니다.

### 데이터베이스 구조
- `crawled_products`: 크롤링된 상품 데이터
- `crawling_performance`: 크롤링 성능 추적
- `selector_performance`: CSS 선택자 성능 추적
- `proxy_performance`: 프록시 성능 추적
- `user_agent_performance`: User-Agent 성능 추적

## 성능 최적화

크롤러는 자동으로 학습하여 성능을 개선합니다:
1. **선택자 학습**: 가장 성공률이 높은 CSS 선택자를 우선 사용
2. **User-Agent 최적화**: 가장 성공률이 높은 User-Agent를 우선 사용
3. **프록시 최적화**: 가장 성공률이 높은 프록시를 우선 사용
4. **데이터 품질 개선**: 데이터 품질 점수를 기반으로 추출 방법 개선
