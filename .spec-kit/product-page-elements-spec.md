# 제품 페이지 요소 분석 스펙 (Product Page Elements Spec)

**프로젝트**: qoo10-ai-agent  
**목적**: dev-agent-kit 원칙에 따른 제품 페이지 요소의 정교·정밀 분석 기준 정의  
**참조**: `doc/ENHANCED_ANALYSIS_METRICS.md`, `api/services/crawler.py`, `api/services/analyzer.py`

---

## 1. 개요

- **제품 페이지 요소 분석**은 크롤러가 추출한 `page_structure`(all_div_classes, key_elements, semantic_structure 등)를 기준으로, 필수/선택 요소 존재 여부, 구조 완성도, 요소 품질, 요소 간 관계, 시맨틱 깊이, 접근성·SEO 관점을 정밀 평가한다.
- 분석 결과는 `page_structure_analysis`로 통합되며, 점수(0–100)와 등급(Excellent/Good/Fair/Poor), 세부 지표·추천사항을 포함한다.

---

## 2. 필수 요소 (Essential Elements)

| 요소 ID | 한글명 | key_elements 키 | semantic_structure 키 | 검색 키워드 (class/선택자) | 가중치 |
|--------|--------|-----------------|------------------------|----------------------------|--------|
| product_info | 상품 정보 | product_info | product_name_elements | product, goods, item, detail, info, name, title, goods_name, product_name | 25% |
| price_info | 가격 정보 | price_info | price_elements | price, cost, discount, sale, original, prc | 25% |
| image_info | 이미지 정보 | image_info | image_elements | image, img, photo, thumbnail, thmb, picture | 25% |
| description_info | 상품 설명 | description_info | description_elements | description, detail, content | 25% |

- **필수 4요소**가 모두 존재해야 기본 점수 40점 만점. 개별 누락 시 해당 비중만큼 감점 및 추천사항 추가.

---

## 3. 선택 요소 (Optional Elements)

| 요소 ID | 한글명 | key_elements 키 | semantic_structure 키 | 검색 키워드 | 비고 |
|--------|--------|-----------------|------------------------|------------|------|
| review_info | 리뷰 정보 | review_info | review_elements | review, rating, star, comment, evaluation | 신뢰도 |
| seller_info | 판매자 정보 | seller_info | seller_elements | shop, seller, store, vendor, merchant | 신뢰도 |
| shipping_info | 배송 정보 | shipping_info | shipping_elements | shipping, delivery, ship, 配送, 送料 | 구매 결정 |
| coupon_info | 쿠폰 정보 | coupon_info | coupon_elements | coupon, discount, 割引, クーポン | 전환 |
| qpoint_info | Qポイント | qpoint_info | qpoint_elements | qpoint, point, ポイント, Qポイント | 전환 |

- 선택 요소는 최대 30점 분배(요소당 비중 균등 또는 그룹별 가중치). 존재할수록 점수 가산.

---

## 4. Qoo10 전용 보강 패턴

크롤러의 `_extract_page_structure`에서 아래 패턴을 추가로 인식할 수 있도록 권장한다.

- **상품명**: `goods_name`, `product_name`, `item_title`, `gd_name`, `prod_name`
- **가격**: `prc`, `sale_prc`, `original_prc`, `price_area`, `total_price`
- **이미지**: `thumb`, `gds_img`, `product_img`, `detail_img`, `pd_img`
- **설명**: `gds_detail`, `product_detail`, `desc_area`, `detail_content`
- **리뷰**: `review_list`, `rating_area`, `review_count`
- **판매자**: `shop_info`, `seller_area`, `store_name`

---

## 5. 구조 완성도 (Structure Completeness)

- **항목**: has_product_name, has_price, has_images, has_description, has_reviews, has_seller, has_shipping, has_coupon, has_qpoint  
- **점수**: 9항목 중 존재하는 항목 비율로 0–20점. 7개 이상이면 20점, 5–6개 15점, 3–4개 10점, 그 미만 0점 및 추천사항.

---

## 6. 요소 품질 (Element Quality)

- **빈도 분석**: 각 카테고리별 요소 개수·평균 빈도 → 품질 점수 기여.
- **다양성**: 필수 4카테고리 + 선택 5카테고리 존재 비율.
- **일관성**: 동일 카테고리 내 class 빈도 편차(표준편차/평균)가 작을수록 가산.
- **가중치**: 전체 품질 점수는 페이지 구조 총점의 최대 15% 반영 권장.

---

## 7. 요소 간 관계 (Element Relationships)

- **필수 쌍 연결성**: (product_info, price_info), (product_info, image_info), (price_info, image_info), (product_info, description_info)  
  → 4쌍 중 만족 비율로 관계 점수.
- **그룹 완성도**:  
  - 구매 정보 그룹: price, coupon, qpoint  
  - 상품 정보 그룹: product, image, description  
  - 신뢰 정보 그룹: review, seller, shipping  
- 그룹별 70% 이상 존재 시 가산. 관계 점수는 총점의 최대 10% 반영 권장.

---

## 8. 시맨틱 깊이·상관관계·접근성·SEO

- **시맨틱 깊이**: 카테고리별 요소 개수·가중 빈도로 깊이 점수. 총점의 최대 5% 반영 권장.
- **상관관계**: 가격-이미지, 설명-리뷰, 상품-판매자, 이미지-설명 쌍 존재 여부. 총점의 최대 5% 반영 권장.
- **접근성·SEO**: 시맨틱 요소 수, 필수 SEO 요소 4종 존재, 구조화 class 수. 총점의 최대 5% 반영 권장.

---

## 9. 등급 기준 (Page Structure Grade)

| 등급 | 점수 구간 | 설명 |
|------|-----------|------|
| Excellent | 90–100 | 필수 4요소 모두 존재, 선택 요소 4개 이상, 구조 완성도·품질·관계·접근성 우수 |
| Good | 70–89 | 필수 4요소 모두 존재, 선택 요소 2개 이상, 구조 완성도·품질 양호 |
| Fair | 50–69 | 필수 3요소 이상, 선택 요소 1개 이상, 구조 완성도 보통 |
| Poor | 0–49 | 필수 요소 2개 이하 또는 에러 페이지, 구조 단순·불완전 |

---

## 10. 체크리스트 (dev-agent-kit 정합성)

- [ ] 필수 4요소(product, price, image, description) 매핑이 analyzer와 crawler에서 일치하는가?
- [ ] 선택 요소 5종이 key_elements 및 semantic_structure 양쪽으로 평가되는가?
- [ ] 구조 완성도 9항목이 structure_completeness에 반영되는가?
- [ ] element_quality, element_relationships, semantic_depth, correlation_analysis, accessibility_seo_score가 리포트에 노출되는가?
- [ ] 등급(grade)이 page_structure_analysis에 포함되어 다른 섹션과 동일하게 표시되는가?

---

**업데이트 이력**

- **2026-02-20**: 초안 (제품 페이지 요소 분석 고도화 — dev-agent-kit 연동)
