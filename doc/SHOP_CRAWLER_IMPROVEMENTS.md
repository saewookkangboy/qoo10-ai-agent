# Shop 페이지 크롤러 개선 사항

## 개요
실제 Qoo10 Shop 페이지 구조에 맞게 Shop 크롤러의 데이터 추출 로직을 개선했습니다.

## 주요 개선 사항

### 1. Shop 이름 추출 개선 (`_extract_shop_name`)
- **기존 문제**: 기본 선택자만 사용하여 Shop 이름을 찾지 못하는 경우가 많음
- **개선 내용**:
  - `title` 태그에서 Shop 이름 추출 (Qoo10 형식: "Shop 이름 | Qoo10")
  - 의미있는 텍스트인지 확인 (너무 짧거나 일반적인 텍스트 제외)
  - 다양한 선택자 추가

### 2. Shop 레벨 추출 개선 (`_extract_shop_level`)
- **기존 문제**: "POWER 95%" 같은 형식을 정확히 추출하지 못함
- **개선 내용**:
  - "POWER 95%" 패턴에서 퍼센트 추출
  - 퍼센트에 따라 레벨 판단 (90% 이상: power, 70% 이상: excellent)
  - "byPower grade" 같은 패턴도 확인

### 3. 팔로워 수 추출 개선 (`_extract_follower_count`)
- **기존 문제**: "フォロワー_50,357_" 같은 형식을 정확히 추출하지 못함
- **개선 내용**:
  - "フォロワー_50,357_" 패턴에서 숫자 추출
  - 쉼표와 언더스코어 제거 후 숫자 변환
  - 다양한 팔로워 패턴 지원

### 4. 상품 수 추출 개선 (`_extract_product_count`)
- **기존 문제**: "全ての商品 (16)" 같은 형식을 정확히 추출하지 못함
- **개선 내용**:
  - "全ての商品 (16)" 패턴에서 숫자 추출
  - 상품 리스트에서 실제 상품인지 확인 (상품명이나 가격이 있는지)
  - 중복 제거

### 5. Shop 쿠폰 정보 추출 개선 (`_extract_shop_coupons`)
- **기존 문제**: 쿠폰 정보를 정확히 추출하지 못함
- **개선 내용**:
  - "5,000円以上のご購入で10%off" 같은 형식에서 할인율과 최소 금액 추출
  - 유효 기간 추출 ("2026.01.08 00:00~2026.01.31 23:59")
  - 중복 쿠폰 제거
  - 다양한 쿠폰 패턴 지원

### 6. Shop 상품 목록 추출 개선 (`_extract_shop_products`)
- **기존 문제**: 가격과 리뷰 수를 정확히 추출하지 못함
- **개선 내용**:
  - "~~6,500円~~**4,500円**" 형식에서 정가와 판매가 추출
  - "レビュー (**565**)" 형식에서 리뷰 수 추출
  - 상품명 추출 로직 개선
  - 상품 종류 파악 (크림, 클렌저, 마스크팩 등)

## 실제 페이지 예시

### Shop 정보
- Shop 이름: "ホイップド公式"
- POWER: 95%
- 팔로워: 50,357명
- 상품 수: 16개

### 쿠폰 정보
- 5,000円 이상 10% off
- 2,000円 이상 5% off

### 상품 정보
- 상품명: "ホイップド パッククレンザー+ミスト2点セット"
- 가격: ~~6,500円~~**4,500円**
- 리뷰: レビュー (**565**)

## 테스트 방법

### 1. 실제 Shop 페이지로 테스트
```python
from services.crawler import Qoo10Crawler
from services.shop_analyzer import ShopAnalyzer

# 크롤러 초기화
crawler = Qoo10Crawler()

# Shop 페이지 크롤링
url = "https://www.qoo10.jp/shop/whippedofficial"
shop_data = await crawler.crawl_shop(url)

# 분석 수행
analyzer = ShopAnalyzer()
analysis_result = await analyzer.analyze(shop_data)

# 결과 확인
print("Shop 이름:", shop_data.get("shop_name"))
print("Shop 레벨:", shop_data.get("shop_level"))
print("팔로워 수:", shop_data.get("follower_count"))
print("상품 수:", shop_data.get("product_count"))
print("쿠폰 수:", len(shop_data.get("coupons", [])))
```

### 2. API 엔드포인트로 테스트
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.qoo10.jp/shop/whippedofficial"
  }'
```

## 예상 개선 효과

1. **데이터 추출 정확도 향상**: 실제 Qoo10 Shop 페이지 구조에 맞게 다양한 패턴을 사용하여 데이터 추출 성공률 향상
2. **Shop 분석 정확도 향상**: 추출된 데이터를 기반으로 Shop 분석 결과의 정확도 향상
3. **상세한 Shop 정보 제공**: Shop 레벨, 팔로워 수, 쿠폰 정보 등을 정확히 추출하여 상세한 분석 가능

## 주의 사항

1. **페이지 구조 변경**: Qoo10 Shop 페이지 구조가 변경되면 패턴을 업데이트해야 할 수 있습니다.
2. **동적 콘텐츠**: JavaScript로 동적 로드되는 콘텐츠는 추출하지 못할 수 있습니다.
3. **상품 목록**: Shop 페이지의 상품 목록은 페이지네이션이 있을 수 있으므로, 첫 페이지의 상품만 추출됩니다.

## 다음 단계

1. 실제 Shop 페이지로 테스트하여 추출 정확도 확인
2. 추출되지 않는 데이터가 있으면 추가 패턴 추가
3. Shop 분석 결과와 실제 페이지를 비교하여 오차 확인 및 수정
