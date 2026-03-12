# 데이터 파이프라인 테스트 요약

**실행 스크립트**: `api/test_data_pipeline_full.py`  
**에이전트 설계**: [doc/agents/README.md](agents/README.md)

---

## 1. 테스트 방법

```bash
cd api
# Shop URL
python test_data_pipeline_full.py "https://www.qoo10.jp/shop/whippedofficial"
# 상품 URL
python test_data_pipeline_full.py "https://www.qoo10.jp/g/1093098159"
```

- URL 타입 자동 감지 (product / shop)
- **상품**: Crawl → ProductAnalyzer → Recommendation → Checklist → Validation → Report
- **Shop**: Crawl → ShopAnalyzer → Recommendation → Checklist → Validation → Report
- 결과: `api/test_data_pipeline_full_result.json` + 콘솔 요약 + 누락 데이터 정밀 분석(기대값 vs 실제)

---

## 2. 적용한 파이프라인 수정 사항

### 2.1 DataValidator (Shop 검증)

- **파일**: `api/services/data_validator.py`
- **변경**: `product_data`가 없을 때(Shop 전용 검증) `normalize_crawler_data_to_api_structure(product_data)` 호출하지 않도록 조건 추가.
- **추가**: `page_structure` 참조 시 `(product_data or shop_data)` 사용해 Shop 페이지 구조 검증 지원.

### 2.2 Crawl Agent – 상품 수 / Shop 레벨 추출

- **파일**: `api/services/crawler_shop.py`

| 항목 | 수정 내용 |
|------|-----------|
| **product_count** | 페이지 전체 텍스트에서 `全ての商品（N）` / `全ての商品 (N)` 정규식 우선 추출. 반각/전각 괄호 모두 허용. DOM 개수 폴백은 그대로 유지. |
| **shop_level** | body 전체 텍스트에서 `POWER` 이후 80자 이내 `70–100` 범위의 `N%`/`N％`를 찾아 power/excellent 판정. 전각 `％` 허용. |
| **Playwright JS** | `product_count`: `全ての商品[（(]\s*(\d+)\s*[）)]` 패턴 사용. `power_level`: 첫 매칭 실패 시 `POWER` 이후 80자 구간에서 `\d{2,3}\s*[%％]` 검사 후 70–100만 반영. |

### 2.3 상품 리뷰 수(review_count) 추출

- **파일**: `api/services/crawler.py`
- **문제**: 페이지에는 "レビュー (1,063)"·"4.8 (1,063)"처럼 쉼표 포함 총 리뷰 수가 표시되나, 기존 정규식은 `\d+`만 사용해 매칭 실패 또는 평점 옆 소괄호만 추출해 10(표시된 리뷰 개수)만 반환됨.
- **수정**: Playwright JS에서 `[\d,]+` 패턴으로 쉼표 포함 숫자 매칭 후 `parseInt(match[1].replace(/,/g, ''))` 적용. Python `_extract_reviews`에서 페이지 전체 텍스트로 `レビュー\s*[（(]\s*([\d,]+)` 및 `(\d+\.?\d*)\s*[（(]\s*([\d,]+)` 패턴 추가, 총 리뷰 수 우선 추출 후 0일 때만 `len(reviews)` fallback.

### 2.4 이미지 정밀 크롤링·분석 (썸네일 / 상세·제품 소개 / alt)

- **파일**: `api/services/crawler.py`, `api/services/analyzer.py`
- **목적**: 분석 점수에 필요한 영역을 정밀 크롤링 — 제품 썸네일·상세(제품 소개) 이미지 및 `img` alt 수집.
- **crawler**  
  - `_extract_images`: `_normalize_img_src`, `_is_product_image_url` 헬퍼 추가.  
  - 썸네일: `.gds_img img`, `.pd_img img`, `#goods_img img`, `[class*="gallery"]`, `[class*="slideshow"]` 등 선택자 확장.  
  - **itemGoods**와 상세 선택자에서 `<img>`의 **src + alt** 수집 → **`detail_images_with_alt`** (`[{ "src", "alt" }]`).  
  - **`detail_images`**: 위 수집 결과의 URL 리스트(중복 제거). 썸네일 미발견 시 첫 상세 이미지를 썸네일로 사용.  
  - Playwright: `page.evaluate`로 썸네일 + 상세 이미지(src/alt) 추출 후 `product_data["images"]`에 병합.
- **analyzer**  
  - `_analyze_images`: **image_count**를 `detail_images`와 `item_goods_images`를 합쳐 중복 제거한 개수로 계산.

### 2.5 Recommender 우선순위 정렬

- **파일**: `api/services/recommender.py`
- **변경**: 체크리스트 등에서 오는 `priority` 값이 `medium-low` 등 복합값일 때 KeyError 방지. 정렬 시 `high`/`medium`/`low` 및 `medium-low`(앞부분 `medium`으로 매핑) 처리.

### 2.6 테스트 스크립트

- **파일**: `api/test_data_pipeline_full.py`
- **기능**: 상품/Shop 공통 파이프라인 테스트, 누락 데이터 정밀 분석(`analyze_missing_data`), Shop 시 `shop_data`만으로 검증·리포트 호출.
- **상품 기대값**: `1093098159` URL 기준 `product_code`, `sale_price` 2990, `original_price` 3300, `review_count` 1063, `rating` 4.8, **has_thumbnail** True, **detail_images_min** 1 이상. 이미지 빈 필드/기대 vs 실제/제안 출력.

---

## 3. 테스트 결과 요약

### 3.1 Shop (whippedofficial)

| 항목 | 기대 | 1차 결과 | 수정 후 |
|------|------|----------|---------|
| shop_name | ホイップド公式 | ✓ | ✓ |
| follower_count | 51,981 | ✓ | ✓ |
| product_count | 18 | 91 (DOM 개수) | **18** ✓ |
| shop_level | power | normal | normal* |

\* POWER 95%가 페이지에서 이미지/스타일 등으로만 표시되면 텍스트 추출 불가.

### 3.2 상품 (g/1093098159)

| 항목 | 기대 | 1차 결과 | 수정 후 |
|------|------|----------|---------|
| product_code | 1093098159 | ✓ | ✓ |
| sale_price | 2990 | ✓ | ✓ |
| original_price | 3300 | ✓ | ✓ |
| review_count | 1063 | 10 (표시 리뷰 개수) | **1063** ✓ |
| rating | 4.8 | ✓ | ✓ |
| has_thumbnail | True | — | **✓** |
| detail_images | ≥1 | — | **✓** (썸네일·상세/alt 정밀 크롤링 반영) |

- 파이프라인 테스트 통과: 빈 필드 0, 기대 vs 실제 0, 검증 100%, 리포트 생성 완료.

---

## 4. 실행 결과 예시

```
[1] 크롤링 (Shop)...     ✓ shop_name, product_count 18, coupons 4, categories 82
[2] 분석 (ShopAnalyzer)... ✓ overall_score
[3] 추천 생성 (Shop)...   ✓ recommendations
[4] 체크리스트 평가 (Shop)... ✓ overall_completion
[5] 데이터 검증 (Shop)... ✓ validation_score 100%, is_valid True
[6] 리포트 생성 (Markdown, Shop)... ✓
```

---

## 5. Qoo10 큐텐 대학 한국어 메뉴얼 파이프라인

**목적**: 메뉴얼을 최신 사이트 기준으로 수집·검증하고, **누락 데이터를 정밀 분석**하여 `doc/Qoo10_큐텐대학_한국어_메뉴얼.md` 반영 품질을 유지합니다.

### 5.1 실행 방법

```bash
cd api
# 메뉴얼 전용 파이프라인 (수집 → 검증 → 누락 분석)
python run_manual_pipeline.py
python run_manual_pipeline.py --output results/manual_pipeline_result.json --manual-path ../doc/Qoo10_큐텐대학_한국어_메뉴얼.md
```

### 5.2 단계

| 단계 | 담당 | 설명 |
|------|------|------|
| 수집 (Crawl) | `Qoo10ManualCrawler` | `article-university.qoo10.jp/qoo10-selling-tips_kor` 및 단계별 교육(초급) 카테고리에서 섹션·링크 수집 |
| 검증 (Validation) | `manual_validator.load_and_validate` | 메뉴얼 MD 파일과 크롤링 결과 비교 |
| 누락 분석 | `manual_validator.validate_manual_vs_crawled` | missing_sections, missing_links, missing_in_manual_items, extra_in_manual, coverage_score, suggestions |

### 5.3 산출물

- `manual_pipeline_result.json`: 크롤 결과 + 검증 결과 `validation` (누락 섹션/링크/항목, coverage_score, suggestions 등)
- 콘솔: coverage_score, 누락 링크 수, 제안 요약

### 5.4 전체 파이프라인과 연동

상품/Shop 파이프라인 테스트 시 메뉴얼 파이프라인을 함께 실행할 수 있습니다.

```bash
python test_data_pipeline_full.py "https://www.qoo10.jp/shop/whippedofficial" --manual
```

- `--manual` 사용 시 `run_manual_pipeline`이 호출되고, 결과의 `validation`이 `manual_missing_analysis` 키로 `test_data_pipeline_full_result.json`에 포함됩니다.
- 누락 데이터가 있을 경우 제안(suggestions)에 따라 메뉴얼을 수동 보완하거나, 크롤러/검증기 규칙을 조정할 수 있습니다.

### 5.5 관련 파일

- `api/services/manual_crawler.py`: 큐텐 대학 한국어 페이지 수집
- `api/services/manual_validator.py`: 메뉴얼 MD 파싱 및 누락 검증
- `api/run_manual_pipeline.py`: 메뉴얼 파이프라인 진입점
- `doc/Qoo10_큐텐대학_한국어_메뉴얼.md`: 반영 대상 메뉴얼

---

**최종 수정**: 2026-02-20
