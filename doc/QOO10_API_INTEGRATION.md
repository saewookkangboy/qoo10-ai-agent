# Qoo10 API 통합 완료 보고서

**완료 일시**: 2024년 (현재)
**통합 범위**: Qoo10 공식 API를 데이터 파이프라인에 통합

---

## 📋 개요

Qoo10 공식 API를 데이터 파이프라인에 통합하여 크롤링보다 더 정확한 데이터를 얻을 수 있도록 개선했습니다.

### 주요 개선 사항

1. **Qoo10 API 서비스 구현**: 공식 API를 사용한 상품 정보 조회
2. **크롤러 통합**: API 우선 사용, 실패 시 크롤링으로 전환
3. **데이터 검증 강화**: API 데이터와 크롤링 데이터 비교 검증
4. **리포트 개선**: 데이터 소스 표시 (API 또는 크롤링)

---

## 🔧 구현 내용

### 1. Qoo10 API 서비스 (`api/services/qoo10_api_service.py`)

**주요 기능**:
- `GetGoodsInfo` API를 사용한 상품 정보 조회
- API 응답을 크롤러 형식으로 정규화
- HMAC-SHA256 서명 생성

**주요 메서드**:
```python
class Qoo10APIService:
    async def get_goods_info(goods_code: str) -> Dict[str, Any]
    def normalize_api_data_to_crawler_format(api_data: Dict[str, Any]) -> Dict[str, Any]
    async def fetch_product_data(product_code: str) -> Optional[Dict[str, Any]]
```

**API 파라미터**:
- `key`: Certification Key (인증 키)
- `method`: `GetGoodsInfo`
- `goodsCode`: 상품 코드
- `responseType`: `JSON` 또는 `XML`
- `signature`: HMAC-SHA256 서명

### 2. 크롤러 통합 (`api/services/crawler.py`)

**변경 사항**:
- Qoo10 API 서비스 초기화
- 크롤링 전에 API로 데이터 조회 시도
- API 성공 시 즉시 반환, 실패 시 크롤링으로 전환

**데이터 흐름**:
```
1. 상품 코드 추출
2. Qoo10 API로 데이터 조회 시도
   ├─ 성공 → API 데이터 반환
   └─ 실패 → 크롤링으로 전환
3. 크롤링 데이터 반환
```

### 3. 데이터 검증 강화 (`api/services/data_validator.py`)

**변경 사항**:
- `validate_crawler_vs_report`에 `api_data` 파라미터 추가
- API 데이터가 있으면 우선적으로 사용하여 검증
- 검증 결과에 데이터 소스 정보 포함

**검증 우선순위**:
1. API 데이터 (가장 신뢰)
2. 크롤링 데이터

### 4. 리포트 개선 (`api/services/report_generator.py`)

**변경 사항**:
- 데이터 소스 표시 (Qoo10 API 또는 크롤링 방법)
- 검증 결과에 데이터 소스 정보 포함

---

## 🔑 환경 변수 설정

`.env` 파일에 다음 환경 변수를 추가하세요:

```bash
# Qoo10 API 인증 키
QOO10_API_KEY=your_certification_key_here
```

**인증 키 발급 방법**:
1. [Qoo10 Developer's Guide](https://api.qoo10.jp/GMKT.INC.Front.QAPIService/Document/QAPIGuideIndex.aspx) 접속
2. API 신청 및 인증 키 발급
3. `.env` 파일에 `QOO10_API_KEY` 설정

---

## 📊 데이터 파이프라인 흐름

### 개선 전
```
크롤링 → 분석 → 검증 → 리포트 생성
```

### 개선 후
```
API 조회 시도
  ├─ 성공 → API 데이터 사용
  └─ 실패 → 크롤링
      ↓
분석 → 검증 (API 데이터 우선) → 리포트 생성 (데이터 소스 표시)
```

---

## 🎯 주요 효과

### 1. 데이터 정확도 향상
- **API 데이터 우선 사용**: 공식 API로 더 정확한 데이터 확보
- **자동 폴백**: API 실패 시 크롤링으로 자동 전환

### 2. 데이터 소스 추적
- **리포트에 표시**: 사용자가 데이터 소스를 확인 가능
- **검증 결과에 포함**: 데이터 소스 정보가 검증 결과에 포함

### 3. 유연성 향상
- **API 키 없어도 동작**: API 키가 없으면 크롤링으로 자동 전환
- **점진적 개선**: API 키 설정 시 자동으로 API 사용

---

## 🔍 사용 예시

### API 키 설정 시
```python
# .env 파일에 QOO10_API_KEY 설정
# 자동으로 API를 우선 사용
crawler = Qoo10Crawler()
product_data = await crawler.crawl_product(url)
# product_data["crawled_with"] == "qoo10_api"
```

### API 키 미설정 시
```python
# API 키가 없으면 크롤링으로 자동 전환
crawler = Qoo10Crawler()
product_data = await crawler.crawl_product(url)
# product_data["crawled_with"] == "http" or "playwright"
```

---

## 📝 API 응답 형식

### 정규화된 데이터 구조
```python
{
    "product_name": "상품명",
    "product_code": "123456",
    "category": "카테고리",
    "brand": "브랜드",
    "price": {
        "sale_price": 1000,
        "original_price": 1500,
        "discount_rate": 33
    },
    "reviews": {
        "review_count": 100,
        "rating": 4.5
    },
    "images": {
        "thumbnail": "https://...",
        "detail_images": ["https://...", ...]
    },
    "description": "상품 설명",
    "qpoint_info": {...},
    "coupon_info": {...},
    "shipping_info": {...},
    "crawled_with": "qoo10_api",
    "api_timestamp": "2024-01-15T..."
}
```

---

## ⚠️ 주의사항

1. **API 키 보안**: `.env` 파일에 API 키를 저장하고 Git에 커밋하지 마세요
2. **API 제한**: Qoo10 API는 요청 제한이 있을 수 있으므로 주의하세요
3. **에러 처리**: API 실패 시 자동으로 크롤링으로 전환되므로 안전합니다

---

## 🔄 향후 개선 사항

1. **API 캐싱**: 동일 상품의 반복 조회 시 캐싱
2. **배치 API**: 여러 상품을 한 번에 조회
3. **API 모니터링**: API 성공률 및 응답 시간 모니터링
4. **다른 API 메서드**: Shop 정보, 리뷰 등 추가 API 통합

---

## 📚 참고 자료

- [Qoo10 Developer's Guide](https://api.qoo10.jp/GMKT.INC.Front.QAPIService/Document/QAPIGuideIndex.aspx)
- Qoo10 API 문서: API 파라미터 및 응답 형식 참조

---

## 결론

Qoo10 공식 API를 데이터 파이프라인에 성공적으로 통합했습니다. API를 우선적으로 사용하되, 실패 시 크롤링으로 자동 전환하는 유연한 구조로 구현되어 있어 안정성과 정확성을 모두 확보했습니다.

**주요 성과**:
- ✅ API 우선 사용으로 데이터 정확도 향상
- ✅ 자동 폴백으로 안정성 확보
- ✅ 데이터 소스 추적으로 투명성 향상
- ✅ 점진적 개선으로 유연성 확보

---

**완료 일시**: 2024년 (현재)
**작성자**: AI Assistant
