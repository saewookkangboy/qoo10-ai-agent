# Shop 분석 테스트 가이드

## 구현 완료된 기능

✅ Shop 크롤링 기능 (`api/services/crawler.py`)
- Shop 기본 정보 추출 (이름, ID, 레벨)
- 팔로워 수, 상품 수 추출
- 카테고리 분포 추출
- 상품 목록 추출
- 쿠폰 정보 추출

✅ Shop 분석 기능 (`api/services/shop_analyzer.py`)
- Shop 정보 분석
- 상품 분석
- 카테고리 분석
- Shop 레벨 분석
- 경쟁사 분석 (기본)

✅ Shop 추천 시스템 (`api/services/recommender.py`)
- Shop 레벨 향상 제안
- 상품 라인업 확대 제안
- 카테고리 집중 전략 제안

✅ API 통합 (`api/main.py`)
- Shop URL 자동 감지
- Shop 분석 백그라운드 처리
- 분석 결과 반환

## 테스트 방법

### 방법 1: API 서버 실행 후 테스트

#### 1단계: API 서버 실행

```bash
cd api
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

#### 2단계: 다른 터미널에서 테스트 실행

```bash
cd /Users/chunghyo/qoo10-ai-agent
python3 test_api_shop.py
```

### 방법 2: 직접 Python 스크립트 실행

```bash
cd /Users/chunghyo/qoo10-ai-agent
PYTHONPATH=/Users/chunghyo/qoo10-ai-agent/api python3 test_shop_analysis.py
```

### 방법 3: Swagger UI에서 테스트

1. API 서버 실행 후 http://localhost:8080/docs 접속
2. `POST /api/v1/analyze` 엔드포인트 선택
3. Request body에 다음 입력:
```json
{
  "url": "https://www.qoo10.jp/shop/whippedofficial"
}
```
4. Execute 클릭
5. `analysis_id` 받기
6. `GET /api/v1/analyze/{analysis_id}` 엔드포인트로 결과 조회

### 방법 4: curl로 테스트

```bash
# 1. 분석 시작
curl -X POST "http://localhost:8080/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.qoo10.jp/shop/whippedofficial"}'

# 응답에서 analysis_id 확인 후:
# 2. 결과 조회 (analysis_id를 실제 ID로 변경)
curl "http://localhost:8080/api/v1/analyze/{analysis_id}"
```

## 예상 결과

### Shop 정보
- Shop 이름: "ホイップド公式" (Whipped Official)
- Shop ID: "whippedofficial"
- Shop 레벨: "power" (POWER 95% 표시)
- 팔로워 수: 50,354명
- 상품 수: 16개

### 분석 결과
- 종합 점수: 70-90점 (Shop 레벨과 상품 수에 따라)
- Shop 레벨: POWER 셀러
- 정산 리드타임: 5일

### 추천 아이디어
1. **상품 라인업 확대** (Medium Priority)
   - 현재 16개 상품 → 최소 20개 이상 권장
   
2. **카테고리 집중 전략** (Low Priority)
   - 주요 카테고리 2-3개에 집중

## 문제 해결

### API 서버 연결 오류
- API 서버가 실행 중인지 확인
- 포트 8080이 사용 중인지 확인

### 크롤링 실패
- Qoo10 사이트 접근 가능 여부 확인
- 네트워크 연결 확인
- User-Agent 로테이션 확인

### 데이터베이스 오류
- SQLite 데이터베이스 파일 권한 확인
- `api/crawler_data.db` 파일 생성 확인

## 다음 단계

Shop 분석 기능이 정상 작동하면:
1. 프론트엔드에 Shop 분석 결과 표시 기능 추가
2. Shop 분석 리포트 UI 컴포넌트 개발
3. 경쟁사 비교 분석 강화 (Phase 2)
