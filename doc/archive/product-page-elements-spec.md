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

| 요소 ID | 한글명 | key_elements 키 | semantic_structure 키 | 검색 키워드 (class/선택자) | 요소당 비중 |
|--------|--------|-----------------|------------------------|----------------------------|--------|
| product_info | 상품 정보 | product_info | product_name_elements | product, goods, item, detail, info, name, title, goods_name, product_name | 25% |
| price_info | 가격 정보 | price_info | price_elements | price, cost, discount, sale, original, prc | 25% |
| image_info | 이미지 정보 | image_info | image_elements | image, img, photo, thumbnail, thmb, picture | 25% |
| description_info | 상품 설명 | description_info | description_elements | description, detail, content | 25% |

- **정규화**: 존재하는 필수 요소 비율로 **essential_score** = (존재 개수 / 4) × 100 (0–100).
- **가중치**: 최종 합산 시 essential_score에 **25%** 적용. (아래 §9 점수 산식 참조)
- 개별 누락 시 추천사항 추가.

---

## 3. 선택 요소 (Optional Elements)

| 요소 ID | 한글명 | key_elements 키 | semantic_structure 키 | 검색 키워드 | 비고 |
|--------|--------|-----------------|------------------------|------------|------|
| review_info | 리뷰 정보 | review_info | review_elements | review, rating, star, comment, evaluation | 신뢰도 |
| seller_info | 판매자 정보 | seller_info | seller_elements | shop, seller, store, vendor, merchant | 신뢰도 |
| shipping_info | 배송 정보 | shipping_info | shipping_elements | shipping, delivery, ship, 配送, 送料 | 구매 결정 |
| coupon_info | 쿠폰 정보 | coupon_info | coupon_elements | coupon, discount, 割引, クーポン | 전환 |
| qpoint_info | Qポイント | qpoint_info | qpoint_elements | qpoint, point, ポイント, Qポイント | 전환 |

- **정규화**: 존재하는 선택 요소 비율로 **optional_score** = (존재 개수 / 5) × 100 (0–100).
- **가중치**: 최종 합산 시 optional_score에 **15%** 적용. (아래 §9 점수 산식 참조)

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
- **정규화**: 9항목 중 존재 비율로 **completeness_score** = (존재 개수 / 9) × 100 (0–100). 구현: `api/services/analyzer.py`의 structure_completeness 카운트 기준.
- **가중치**: 최종 합산 시 completeness_score에 **15%** 적용. (아래 §9 점수 산식 참조)

---

## 6. 요소 품질 (Element Quality)

- **빈도 분석**: 각 카테고리별 요소 개수·평균 빈도 → 품질 점수 기여.
- **다양성**: 필수 4카테고리 + 선택 5카테고리 존재 비율.
- **일관성**: 동일 카테고리 내 class 빈도 편차(표준편차/평균)가 작을수록 가산.
- **정규화**: 위 지표를 종합한 **quality_score** = element_quality.overall_quality_score (0–100). 구현: `analyzer.py`의 `_analyze_element_quality`.
- **가중치**: 최종 합산 시 quality_score에 **10%** 적용. (아래 §9 점수 산식 참조)

### 6.5. class_freq_score (중요 class 빈도 점수)

- **목적**: 페이지 내에서 “의미적으로 중요한” CSS class가 실제로 자주 쓰이는지 빈도로 평가한다. 자주 반복되는 class 중 중요 키워드가 포함된 비율이 높을수록 점수가 올라간다.
- **중요 class의 정의**  
  - **선정 기준**: CSS class 이름(대소문자 무시)에 아래 **important_keywords** 중 하나라도 포함되면 “중요 class”로 간주한다.  
  - **키워드 목록** (구현: `api/services/analyzer.py` `_analyze_page_structure` 내 660행):  
    `product`, `goods`, `price`, `image`, `detail`, `description`  
  - 시맨틱 역할·상품 페이지 핵심 요소를 나타내는 이름 패턴을 기준으로 하며, 별도 시맨틱 구조(예: key_elements)가 아닌 **class 이름 문자열**만 사용한다.
- **빈도 측정 방법**  
  - **데이터 소스**: 크롤러가 단일 페이지를 파싱할 때 만든 `page_structure["class_frequency"]` (`Dict[str, int]`)를 사용한다.  
  - **의미**: 각 class가 **해당 페이지 내에서** 등장한 횟수(페이지 내 반복 횟수)이다.  
  - **전체 페이지 집합 대비 출현 비율**은 사용하지 않으며, **페이지 내 반복 횟수**만 사용한다.  
  - 상위 N개: 해당 페이지의 `class_frequency`를 빈도 값 내림차순으로 정렬한 뒤 **상위 10개** class만 사용한다.
- **가중치 적용 및 계산식**  
  - **1단계**: `class_frequency = page_structure.get("class_frequency", {})`  
  - **2단계**: `top_classes = sorted(class_frequency.items(), key=빈도, reverse=True)[:10]`  
  - **3단계**: `important_class_count = top_classes` 중에서 class 이름에 `important_keywords` 중 하나라도 포함된 개수 (0~10)  
  - **4단계**: `class_frequency_score = min(100, important_class_count * 20)` → 0, 20, 40, …, 100 (0–100 캡)  
  - 최종 합산 시 **가중치 10%** 적용. (§9 점수 산식 참조)
- **구현 위치 및 입·출력**  
  - **함수**: 별도 함수 없음. `api/services/analyzer.py`의 **`_analyze_page_structure`** 내부에서 인라인으로 계산된다.  
  - **입력**: `page_structure` (dict). 그중 `page_structure["class_frequency"]`가 `Dict[str, int]` (class 이름 → 페이지 내 출현 횟수).  
  - **출력**: `analysis["class_frequency_score"]` (int, 0–100), `analysis["top_classes"]` (list of `{"class": str, "frequency": int}`, 상위 10개).  
  - 합산 시에는 `class_freq_score = analysis.get("class_frequency_score", 0)`으로 읽어 §9의 가중치 합산에 사용한다.
- **예시**  
  - `class_frequency = {"product_name": 3, "goods_detail": 2, "price_area": 4, "image_thumb": 5, "detail_content": 1, "other_class": 10}`  
  - 상위 10개: `other_class`, `image_thumb`, `price_area`, `product_name`, `goods_detail`, `detail_content` 등.  
  - 이 중 important_keywords 포함: `product_name`, `goods_detail`, `price_area`, `image_thumb`, `detail_content` → `important_class_count = 5`  
  - `class_frequency_score = min(100, 5 * 20) = 100`.

---

## 7. 요소 간 관계 (Element Relationships)

- **필수 쌍 연결성**: (product_info, price_info), (product_info, image_info), (price_info, image_info), (product_info, description_info)  
  → 4쌍 중 만족 비율로 관계 점수.
- **그룹 완성도**:  
  - 구매 정보 그룹: price, coupon, qpoint  
  - 상품 정보 그룹: product, image, description  
  - 신뢰 정보 그룹: review, seller, shipping  
- 그룹별 70% 이상 존재 시 가산.
- **정규화**: **relationship_score** = element_relationships.relationship_score (0–100). 구현: `analyzer.py`의 `_analyze_element_relationships`.
- **가중치**: 최종 합산 시 relationship_score에 **10%** 적용. (아래 §9 점수 산식 참조)

---

## 8. 시맨틱 깊이·상관관계·접근성·SEO

- **시맨틱 깊이**: 카테고리별 요소 개수·가중 빈도로 **depth_score** (0–100). 구현: `analyzer.py`의 `_analyze_semantic_depth`. 가중치 **5%**.
- **상관관계**: 가격-이미지, 설명-리뷰, 상품-판매자, 이미지-설명 쌍 존재 여부 → **correlation_score** (0–100). 구현: `analyzer.py`의 correlation_analysis. 가중치 **5%**.
- **접근성·SEO**: 시맨틱 요소 수, 필수 SEO 요소 4종 존재, 구조화 class 수 → **accessibility_score** (0–100). 구현: `analyzer.py`의 `_analyze_accessibility_seo`. 가중치 **5%**.

---

## 9. Scoring Formula (점수 산식)

**참조**: `api/services/analyzer.py` — `_analyze_page_structure` 내 가중치 합산부.

- **정규화 규칙**: 아래 모든 서브점수는 **0–100** 범위로 산출·캡핑한 뒤 가중치를 적용한다. (구현에서 이미 0–100으로 계산되는 항목은 그대로 사용.)

| 서브점수 | 설명 | 가중치 |
|----------|------|--------|
| essential_score | 필수 4요소 존재 비율 (존재 개수/4)×100 | 25% |
| optional_score | 선택 5요소 존재 비율 (존재 개수/5)×100 | 15% |
| completeness_score | 구조 완성도 9항목 존재 비율 (존재 개수/9)×100 | 15% |
| class_freq_score | 중요 class 빈도 기반 점수 (정의·계산식·구현: §6.5 참조, `_analyze_page_structure` 내 인라인) | 10% |
| quality_score | element_quality.overall_quality_score | 10% |
| relationship_score | element_relationships.relationship_score | 10% |
| depth_score | semantic_depth.depth_score (최대 100 캡) | 5% |
| correlation_score | correlation_analysis.correlation_score | 5% |
| accessibility_score | accessibility_seo_score (최대 100 캡) | 5% |

- **합산 공식**:  
  `page_structure_score = ⌊ Σ (sub_score_i × weight_i) ⌋`  
  이때 `sub_score_i`는 위 항목을 0–100으로 정규화한 값, `weight_i`는 위 표의 비율(합 100%).  
  최종 `score = clamp(page_structure_score, 0, 100)`.

- **예시 계산**:  
  essential_score=100, optional_score=60, completeness_score=100, class_freq_score=80, quality_score=70, relationship_score=100, depth_score=50, correlation_score=75, accessibility_score=40 이면  
  `100×0.25 + 60×0.15 + 100×0.15 + 80×0.10 + 70×0.10 + 100×0.10 + 50×0.05 + 75×0.05 + 40×0.05 = 25 + 9 + 15 + 8 + 7 + 10 + 2.5 + 3.75 + 2 = 82.25` → **82점**.

---

## 10. 등급 기준 (Page Structure Grade)

| 등급 | 점수 구간 | 설명 |
|------|-----------|------|
| Excellent | 90–100 | 필수 4요소 모두 존재, 선택 요소 4개 이상, 구조 완성도·품질·관계·접근성 우수 |
| Good | 70–89 | 필수 4요소 모두 존재, 선택 요소 2개 이상, 구조 완성도·품질 양호 |
| Fair | 50–69 | 필수 3요소 이상, 선택 요소 1개 이상, 구조 완성도 보통 |
| Poor | 0–49 | 필수 요소 2개 이하 또는 에러 페이지, 구조 단순·불완전 |

---

## 11. 체크리스트 (dev-agent-kit 정합성)

- [ ] 필수 4요소(product, price, image, description) 매핑이 analyzer와 crawler에서 일치하는가?
- [ ] 선택 요소 5종이 key_elements 및 semantic_structure 양쪽으로 평가되는가?
- [ ] 구조 완성도 9항목이 structure_completeness에 반영되는가?
- [ ] element_quality, element_relationships, semantic_depth, correlation_analysis, accessibility_seo_score가 리포트에 노출되는가?
- [ ] 등급(grade)이 page_structure_analysis에 포함되어 다른 섹션과 동일하게 표시되는가? (점수는 §9 점수 산식과 일치)

---

**업데이트 이력**

- **2026-02-20**: 초안 (제품 페이지 요소 분석 고도화 — dev-agent-kit 연동)
