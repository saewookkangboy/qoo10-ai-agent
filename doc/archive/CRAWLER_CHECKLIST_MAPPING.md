# 크롤러 수집 항목 ↔ 체크리스트 항목 매핑표

## 개요
이 문서는 새롭게 업데이트된 크롤러가 수집하는 데이터 항목과 분석 리포트에 반영되는 체크리스트 항목 간의 매핑 관계를 정리한 것입니다.

---

## 📦 크롤러 수집 항목 목록

### 상품 기본 정보
| 항목명 | 필드 경로 | 데이터 타입 | 설명 |
|--------|----------|------------|------|
| 상품명 | `product_name` | string | 개선: 제외 패턴 적용 (가격 안내 텍스트 제외) |
| 상품 코드 | `product_code` | string | URL 또는 메타데이터에서 추출 |
| 카테고리 | `category` | string | 메타데이터 또는 페이지에서 추출 |
| 브랜드 | `brand` | string | 메타데이터에서 추출 |

### 가격 정보
| 항목명 | 필드 경로 | 데이터 타입 | 설명 |
|--------|----------|------------|------|
| 판매가 | `price.sale_price` | number | 개선: 유효성 검증 (100~1,000,000엔) |
| 정가 | `price.original_price` | number | 개선: 유효성 검증 (100~1,000,000엔) |
| 할인율 | `price.discount_rate` | number | 계산 또는 추출 |

### 이미지 정보
| 항목명 | 필드 경로 | 데이터 타입 | 설명 |
|--------|----------|------------|------|
| 썸네일 | `images.thumbnail` | string (URL) | 상품 대표 이미지 |
| 상세 이미지 | `images.detail_images` | array[string] | 상품 상세 이미지 목록 |

### 상품 설명
| 항목명 | 필드 경로 | 데이터 타입 | 설명 |
|--------|----------|------------|------|
| 상품 설명 | `description` | string | HTML 태그 포함 가능, 개선: 더 긴 설명 추출 |

### 검색 키워드
| 항목명 | 필드 경로 | 데이터 타입 | 설명 |
|--------|----------|------------|------|
| 검색어 | `search_keywords` | array[string] | 검색어 필드에서 추출 |

### 리뷰 정보
| 항목명 | 필드 경로 | 데이터 타입 | 설명 |
|--------|----------|------------|------|
| 평점 | `reviews.rating` | number | 0.0 ~ 5.0 |
| 리뷰 개수 | `reviews.review_count` | number | 개선: fallback 로직 (reviews 배열 길이 사용) |
| 리뷰 텍스트 | `reviews.reviews` | array[string] | 리뷰 본문 목록 |

### 배송 정보
| 항목명 | 필드 경로 | 데이터 타입 | 설명 |
|--------|----------|------------|------|
| 배송비 | `shipping_info.shipping_fee` | number | 배송비 금액 |
| 무료배송 | `shipping_info.free_shipping` | boolean | 무료배송 여부 |
| 반품 정책 | `shipping_info.return_policy` | string | 개선: "free_return", "return_available" 등 |

### Qポイント 정보
| 항목명 | 필드 경로 | 데이터 타입 | 설명 |
|--------|----------|------------|------|
| 최대 포인트 | `qpoint_info.max_points` | number | 개선: 다양한 소스에서 추출 |
| 수령확인 포인트 | `qpoint_info.receive_confirmation_points` | number | 개선: 추가 추출 |
| 리뷰작성 포인트 | `qpoint_info.review_points` | number | 개선: 추가 추출 |
| 자동 포인트 | `qpoint_info.auto_points` | number | 개선: 추가 추출 |

### 쿠폰 정보
| 항목명 | 필드 경로 | 데이터 타입 | 설명 |
|--------|----------|------------|------|
| 쿠폰 존재 여부 | `coupon_info.has_coupon` | boolean | 쿠폰 존재 여부 |
| 쿠폰 타입 | `coupon_info.coupon_type` | string | "auto", "manual" 등 |
| 최대 할인액 | `coupon_info.max_discount` | number | 최대 할인 금액 |

### MOVE 상품
| 항목명 | 필드 경로 | 데이터 타입 | 설명 |
|--------|----------|------------|------|
| MOVE 상품 여부 | `is_move_product` | boolean | MOVE 상품 등록 여부 |

### 판매자 정보
| 항목명 | 필드 경로 | 데이터 타입 | 설명 |
|--------|----------|------------|------|
| Shop ID | `seller_info.shop_id` | string | Shop 식별자 |
| Shop 이름 | `seller_info.shop_name` | string | Shop 이름 |
| Shop 레벨 | `seller_info.shop_level` | string | "power", "excellent", "normal" 등 |

### 페이지 구조
| 항목명 | 필드 경로 | 데이터 타입 | 설명 |
|--------|----------|------------|------|
| 페이지 구조 | `page_structure` | object | div class 정보, semantic structure 등 |

---

## ✅ 체크리스트 항목 ↔ 크롤러 데이터 매핑

### 판매 준비 카테고리

| 체크리스트 ID | 체크리스트 항목 | 사용하는 크롤러 데이터 | 체크 함수 | 자동 체크 |
|--------------|----------------|---------------------|----------|----------|
| item_001 | 상품 등록 완료 | `product_name`<br>`description`<br>`images.thumbnail`<br>`images.detail_images` | `check_product_registered` | ✅ |
| item_002 | 검색어 설정 완료 | `search_keywords` | `check_search_keywords` | ✅ |
| item_003 | 카테고리 및 브랜드 등록 완료 | `category`<br>`brand` | `check_category_brand` | ✅ |
| item_004 | 가격 설정 완료 | `price.sale_price`<br>`price.original_price`<br>`price.discount_rate` | `check_price_set` | ✅ |
| item_005 | 배송 정보 설정 완료 | `shipping_info.shipping_fee`<br>`shipping_info.free_shipping` | `check_shipping_info` | ✅ |
| item_006 | 재고 관리 설정 완료 | - | - | ❌ (수동 확인) |
| item_006b | Qポイント 정보 설정 | `qpoint_info.max_points`<br>`qpoint_info.receive_confirmation_points`<br>`qpoint_info.review_points`<br>`qpoint_info.auto_points` | `check_qpoint_info` | ✅ |
| item_006c | 반품 정책 명시 | `shipping_info.return_policy` | `check_return_policy` | ✅ |
| item_006d | MOVE 상품 등록 (해당 시) | `is_move_product` | `check_move_product` | ✅ |

### 매출 증대 카테고리

| 체크리스트 ID | 체크리스트 항목 | 사용하는 크롤러 데이터 | 체크 함수 | 자동 체크 |
|--------------|----------------|---------------------|----------|----------|
| item_007 | 상품 페이지 최적화 | `analysis_result.overall_score`<br>`analysis_result.image_analysis`<br>`analysis_result.description_analysis`<br>`analysis_result.price_analysis`<br>`analysis_result.review_analysis` | `check_page_optimization` | ✅ |
| item_008 | 검색 키워드 최적화 | `product_name`<br>`search_keywords`<br>`analysis_result.seo_analysis` | `check_keyword_optimization` | ✅ |
| item_009 | 가격 전략 수립 | `price.sale_price`<br>`price.discount_rate`<br>`analysis_result.price_analysis` | `check_price_strategy` | ✅ |
| item_010 | 고객 리뷰 관리 | - | - | ❌ (수동 확인) |
| item_011 | 프로모션 활용 | `coupon_info`<br>`price.discount_rate`<br>`shop_data.coupons` | `check_promotion` | ✅ |
| item_011b | 쿠폰 상세 정보 제공 | `coupon_info.has_coupon`<br>`coupon_info.max_discount`<br>`price.coupon_discount` | `check_coupon_detail` | ✅ |
| item_012 | 광고 전략 수립 | - | - | ❌ (수동 확인) |
| item_013 | 배송 옵션 다양화 | - | - | ❌ (수동 확인) |
| item_014 | 고객 서비스 개선 | - | - | ❌ (수동 확인) |
| item_015 | 데이터 분석 기반 의사결정 | - | - | ❌ (수동 확인) |
| item_016 | 지속적인 개선 및 테스트 | - | - | ❌ (수동 확인) |

### Shop 운영 카테고리

| 체크리스트 ID | 체크리스트 항목 | 사용하는 크롤러 데이터 | 체크 함수 | 자동 체크 |
|--------------|----------------|---------------------|----------|----------|
| item_016b | Shop 레벨 최적화 | `seller_info.shop_level`<br>`seller_info.shop_name`<br>`shop_data.shop_level` | `check_shop_level` | ✅ |
| item_016c | Shop 팔로워 수 관리 | `seller_info.follower_count`<br>`shop_data.follower_count` | `check_shop_followers` | ✅ |
| item_016d | Shop 상품 다양성 | `shop_data.product_count`<br>`shop_data.categories` | `check_shop_product_diversity` | ✅ |

### 광고/프로모션 카테고리

| 체크리스트 ID | 체크리스트 항목 | 사용하는 크롤러 데이터 | 체크 함수 | 자동 체크 |
|--------------|----------------|---------------------|----------|----------|
| item_017 | 파워랭크업 광고 활용 | - | - | ❌ (수동 확인) |
| item_018 | 스마트세일즈 광고 활용 | - | - | ❌ (수동 확인) |
| item_019 | 플러스 전시 광고 활용 | - | - | ❌ (수동 확인) |
| item_020 | 키워드 플러스 광고 활용 | - | - | ❌ (수동 확인) |
| item_021 | 샵 쿠폰 설정 | `shop_data.coupons` | `check_shop_coupon` | ✅ |
| item_022 | 상품 할인 설정 | `price.discount_rate` | `check_product_discount` | ✅ |
| item_023 | 샘플마켓 참가 (가능한 경우) | `product_data` (기본 확인) | `check_sample_market` | ✅ |
| item_024 | 메가할인/메가포 대비 준비 | - | - | ❌ (수동 확인) |

---

## 🔄 개선 사항 요약

### 크롤러 개선 사항
1. **상품명 추출**: 가격 안내 텍스트 제외 패턴 적용
2. **가격 정보**: 유효성 검증 범위 (100~1,000,000엔) 적용
3. **Qポイント 정보**: 다양한 소스에서 포인트 정보 추출 (max_points, receive_confirmation_points, review_points, auto_points)
4. **반품 정보**: 반품 정책 추출 로직 개선
5. **리뷰 개수**: fallback 로직 적용 (review_count가 0이지만 reviews 배열에 리뷰가 있으면 배열 길이 사용)

### 체크리스트 평가 개선 사항
1. **상품명 체크**: 크롤러의 제외 패턴 반영
2. **가격 체크**: 크롤러와 동일한 유효성 검증 범위 사용
3. **Qポイント 체크**: 개선된 크롤러의 다양한 Qポイント 정보 확인
4. **반품 정책 체크**: 개선된 크롤러의 반품 정책 값 확인
5. **데이터 검증**: 개선된 크롤러의 유효성 검증 로직 반영

---

## 📊 통계

- **총 체크리스트 항목**: 24개
- **자동 체크 가능 항목**: 16개 (66.7%)
- **수동 확인 필요 항목**: 8개 (33.3%)
- **크롤러 수집 항목**: 15개 주요 카테고리

---

## 🔍 참고사항

1. **분석 결과 데이터**: 일부 체크리스트 항목은 크롤러 데이터뿐만 아니라 `analysis_result` (분석 결과)도 사용합니다.
2. **Shop 데이터**: Shop 관련 체크리스트 항목은 `shop_data` 또는 `seller_info`를 사용합니다.
3. **페이지 구조**: `page_structure`는 체크리스트 평가 시 참고 정보로 사용됩니다.
4. **자동 체크 불가 항목**: 광고 설정, 고객 서비스, 데이터 분석 등은 크롤링으로 확인할 수 없어 수동 확인이 필요합니다.
