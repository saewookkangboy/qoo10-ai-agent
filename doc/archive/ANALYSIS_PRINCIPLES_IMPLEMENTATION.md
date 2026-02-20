# 분석 원칙 적용 가이드

## 📋 개요

이 문서는 `CRAWLING_ANALYSIS_PRINCIPLES.md`에 정의된 원칙을 실제 코드에 적용하는 방법을 설명합니다.

---

## ✅ 적용 완료 사항

### 1. 크롤링 서비스 (crawler.py)

**적용 내용**:
- ✅ Playwright 크롤링 구현 완료
- ✅ HTTP 크롤링과 Playwright 크롤링 선택 가능
- ✅ 모든 크롤링 결과에 `crawled_with` 필드 포함
- ✅ 데이터 검증 및 정규화 규칙 적용

**사용 방법**:
```python
# Playwright 크롤링 (권장)
product_data = await crawler.crawl_product(url, use_playwright=True)
shop_data = await crawler.crawl_shop(url, use_playwright=True)

# HTTP 크롤링 (Fallback)
product_data = await crawler.crawl_product(url, use_playwright=False)
shop_data = await crawler.crawl_shop(url, use_playwright=False)
```

### 2. 분석 서비스 (analyzer.py, shop_analyzer.py)

**적용 내용**:
- ✅ 분석 원칙 문서 참조 주석 추가
- ✅ 점수 계산 기준 통일
- ✅ 분석 결과 구조 표준화

**점수 계산 기준**:
- **상세한 점수 계산 기준은 `ENHANCED_ANALYSIS_METRICS.md` 참조**
- 이미지 점수: 0-100점 (썸네일 25% + 상세 이미지 35% + 다양성 20% + 품질 20%)
- 설명 점수: 0-100점 (길이 35% + 구조화 25% + SEO 키워드 20% + 일본어 품질 20%)
- 가격 점수: 0-100점 (경쟁사 대비 40% + 할인율 25% + 가격 심리학 20% + 일관성 15%)
- 리뷰 점수: 0-100점 (평점 45% + 리뷰 수 30% + 부정 리뷰 비율 15% + 리뷰 품질 10%)
- 등급 시스템: Excellent (90-100), Good (70-89), Fair (50-69), Poor (0-49)

### 3. 리포트 생성 서비스 (report_generator.py)

**적용 내용**:
- ✅ 리포트 생성 원칙 문서 참조 주석 추가
- ✅ 리포트 구조 표준화
- ✅ 크롤링 방법 명시

**리포트 구조**:
```json
{
  "crawled_data": {
    "crawled_with": "playwright" | "httpx",
    // ... 크롤링 데이터
  },
  "analysis": {
    // ... 분석 결과
  },
  "recommendations": [
    // ... 개선 제안
  ]
}
```

---

## 🔧 적용 필요 사항

### 1. 분석 서비스 점수 계산 기준 통일

**현재 상태**:
- `analyzer.py`의 점수 계산 기준이 원칙 문서와 부분적으로 일치
- 일부 서비스에서 점수 계산 방식이 다를 수 있음

**적용 방법**:
1. `CRAWLING_ANALYSIS_PRINCIPLES.md`의 점수 계산 기준 확인
2. 모든 분석 서비스에서 동일한 기준 사용
3. 점수 계산 로직을 함수로 추출하여 재사용

### 2. 리포트 생성 시 크롤링 방법 명시

**현재 상태**:
- 리포트 생성 시 `crawled_with` 필드 포함 필요
- 리포트 헤더에 크롤링 방법 표시

**적용 방법**:
1. 리포트 생성 시 `product_data` 또는 `shop_data`에서 `crawled_with` 추출
2. 리포트 헤더에 크롤링 방법 명시
3. 크롤링 방법에 따른 데이터 품질 정보 포함

### 3. 데이터 검증 규칙 적용

**현재 상태**:
- 일부 데이터 검증 규칙이 적용됨
- 모든 필드에 대한 검증 규칙이 완전히 적용되지 않을 수 있음

**적용 방법**:
1. `CRAWLING_ANALYSIS_PRINCIPLES.md`의 데이터 검증 원칙 확인
2. 크롤링 후 데이터 검증 함수 추가
3. 검증 실패 시 경고 또는 오류 처리

---

## 📝 체크리스트

코드 수정 시 다음 사항을 확인하세요:

- [ ] 크롤링 방법(`crawled_with`) 필드 포함
- [ ] 데이터 검증 규칙 적용
- [ ] 점수 계산 기준 통일
- [ ] 리포트 구조 표준화
- [ ] 분석 원칙 문서 참조 주석 추가
- [ ] 일관성 검증

---

## 📚 관련 문서

- **CRAWLING_ANALYSIS_PRINCIPLES.md**: 크롤링 및 분석 원칙 문서
- **ENHANCED_ANALYSIS_METRICS.md**: 고도화된 분석 지표 체계

## 🔄 업데이트 이력

- **2026-01-14**: 초기 문서 작성 (Playwright 크롤링 반영)
- **2026-01-14**: 고도화된 지표 체계 반영

---

**참고**: 이 문서는 지속적으로 업데이트되며, 새로운 원칙이나 변경 사항이 있을 때마다 갱신됩니다. 상세한 지표 기준은 `ENHANCED_ANALYSIS_METRICS.md`를 참조하세요.
