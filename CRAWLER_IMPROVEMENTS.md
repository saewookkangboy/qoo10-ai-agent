# 크롤러 및 체크리스트 평가 개선 사항

## 개요
실제 Qoo10 상품 페이지 구조에 맞게 크롤러의 데이터 추출 로직과 체크리스트 평가 로직을 개선했습니다.

## 주요 개선 사항

### 1. 상품명 추출 개선 (`_extract_product_name`)
- **기존 문제**: 기본 선택자만 사용하여 상품명을 찾지 못하는 경우가 많음
- **개선 내용**:
  - `title` 태그에서 상품명 추출 (Qoo10 형식: "상품명 | Qoo10")
  - 페이지 내 모든 `h1` 태그를 확인하여 가장 긴 텍스트를 상품명으로 사용
  - 의미있는 텍스트인지 확인 (최소 길이 체크)

### 2. 가격 정보 추출 개선 (`_extract_price`)
- **기존 문제**: 쿠폰 할인, Qポイント 정보를 추출하지 못함
- **개선 내용**:
  - "商品価格" 섹션에서 가격 추출
  - 쿠폰 할인 정보 추출 ("プラス0割引", "最大0円" 패턴)
  - Qポイント 정보 추출 ("最大0P" 패턴)
  - 취소선이 있는 정가 추출 (`<del>`, `<s>` 태그)
  - 다양한 가격 선택자 추가

### 3. 배송 정보 추출 개선 (`_extract_shipping_info`)
- **기존 문제**: 무료배송, 반품 정책 정보를 추출하지 못함
- **개선 내용**:
  - 무료배송 여부 확인 ("無料", "FREE" 패턴)
  - 반품 정책 정보 추출 ("返品無料", "無料返品" 패턴)
  - 다양한 배송비 패턴 지원

### 4. 상품 설명 추출 개선 (`_extract_description`)
- **기존 문제**: 설명을 찾지 못하거나 너무 짧은 텍스트를 추출
- **개선 내용**:
  - 메타 `description` 태그 확인
  - JSON-LD 스키마에서 설명 추출
  - 의미있는 설명인지 확인 (최소 50자 이상)
  - 다양한 설명 선택자 추가

### 5. 카테고리 추출 개선 (`_extract_category`)
- **기존 문제**: 카테고리를 찾지 못하는 경우가 많음
- **개선 내용**:
  - URL에서 카테고리 추출 (`/category/`, `/cat/` 패턴)
  - 브레드크럼에서 마지막 링크를 카테고리로 사용
  - 다양한 카테고리 선택자 추가

### 6. 이미지 추출 개선 (`_extract_images`)
- **기존 문제**: 이미지 URL을 찾지 못하거나 상대 경로를 절대 경로로 변환하지 못함
- **개선 내용**:
  - 상대 경로를 절대 경로로 변환 (`//`, `/` 시작하는 URL 처리)
  - `data-src`, `data-original` 속성 확인
  - 아이콘, 로고, 배너 이미지 제외
  - 중복 이미지 제거

### 7. 리뷰 정보 추출 개선 (`_extract_reviews`)
- **기존 문제**: "4.8(150)" 같은 형식에서 평점과 리뷰 수를 정확히 추출하지 못함
- **개선 내용**:
  - "4.8(150)" 형식에서 평점과 리뷰 수 추출
  - 다양한 평점/리뷰 수 패턴 지원
  - 중복 리뷰 제거
  - 의미있는 리뷰인지 확인 (최소 10자 이상)

### 8. 체크리스트 평가 로직 개선

#### `_check_product_registered`
- 상품명이 "상품명 없음"이 아닌지 확인
- 설명이 최소 50자 이상인지 확인
- 썸네일 또는 상세 이미지가 있는지 확인

#### `_check_price_set`
- 판매가가 설정되어 있는지 확인
- 정가와 할인율이 설정되어 있으면 추가 점수 부여
- 상세한 권장 사항 제공

#### `_check_shipping_info`
- 무료배송 여부 확인
- 배송비 정보가 설정되어 있는지 확인 (무료배송 포함)

#### `_check_promotion`
- 쿠폰 할인 정보 확인
- 상품 할인 정보 확인
- Qポイント 정보 확인

## 테스트 방법

### 1. 실제 페이지로 테스트
```python
from services.crawler import Qoo10Crawler
from services.checklist_evaluator import ChecklistEvaluator
from services.analyzer import ProductAnalyzer

# 크롤러 초기화
crawler = Qoo10Crawler()

# 상품 페이지 크롤링
url = "https://www.qoo10.jp/item/..."
product_data = await crawler.crawl_product(url)

# 분석 수행
analyzer = ProductAnalyzer()
analysis_result = await analyzer.analyze(product_data)

# 체크리스트 평가
evaluator = ChecklistEvaluator()
checklist_result = await evaluator.evaluate_checklist(
    product_data=product_data,
    analysis_result=analysis_result
)

# 결과 확인
print("상품명:", product_data.get("product_name"))
print("가격:", product_data.get("price"))
print("배송 정보:", product_data.get("shipping_info"))
print("체크리스트 완성도:", checklist_result.get("overall_completion"))
```

### 2. API 엔드포인트로 테스트
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.qoo10.jp/item/..."
  }'
```

## 예상 개선 효과

1. **데이터 추출 정확도 향상**: 실제 Qoo10 페이지 구조에 맞게 다양한 선택자와 패턴을 사용하여 데이터 추출 성공률 향상
2. **체크리스트 평가 정확도 향상**: 실제 추출된 데이터 구조에 맞게 평가 로직을 조정하여 오차 감소
3. **상세한 권장 사항 제공**: 각 체크리스트 항목에 대해 구체적인 권장 사항 제공

## 주의 사항

1. **페이지 구조 변경**: Qoo10 페이지 구조가 변경되면 선택자를 업데이트해야 할 수 있습니다.
2. **동적 콘텐츠**: JavaScript로 동적 로드되는 콘텐츠는 추출하지 못할 수 있습니다.
3. **방화벽/차단**: 과도한 요청 시 IP 차단될 수 있으므로 적절한 지연 시간을 유지해야 합니다.

## 다음 단계

1. 실제 페이지로 테스트하여 추출 정확도 확인
2. 추출되지 않는 데이터가 있으면 추가 선택자/패턴 추가
3. 체크리스트 평가 결과와 실제 페이지를 비교하여 오차 확인 및 수정
