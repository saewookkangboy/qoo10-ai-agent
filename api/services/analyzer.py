"""
상품 분석 서비스
수집된 상품 데이터를 분석하여 점수와 인사이트를 제공합니다.

분석 원칙:
- CRAWLING_ANALYSIS_PRINCIPLES.md 참조
- 모든 분석은 일관된 기준과 원칙을 따라야 함
- 크롤링 방법(crawled_with)에 따라 적절한 분석 수행

지표 정의 및 코드 정합성:
- doc/ENHANCED_ANALYSIS_METRICS.md — 세부 지표(가중치, 점수 범위, 등급)
- doc/METRICS_CODE_MAPPING.md — 문서 vs 구현 일치/갭 매핑
"""
from typing import Dict, Any, List, Optional
import re
from PIL import Image
import httpx
import asyncio
import json
import os
from datetime import datetime


class ProductAnalyzer:
    """상품 분석기"""
    
    def __init__(self):
        self.min_image_resolution = 800
        self.min_description_length = 500
        self.min_review_count = 10
        self.min_rating = 4.0
    
    async def analyze(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        상품 데이터 종합 분석
        
        Args:
            product_data: 크롤러에서 수집한 상품 데이터
            
        Returns:
            분석 결과 딕셔너리
        """
        analysis_result = {
            "overall_score": 0,
            "image_analysis": await self._analyze_images(product_data.get("images", {})),
            "description_analysis": self._analyze_description(product_data),
            "price_analysis": self._analyze_price(product_data.get("price", {})),
            "review_analysis": self._analyze_reviews(product_data.get("reviews", {})),
            "seo_analysis": self._analyze_seo(product_data),
            "page_structure_analysis": self._analyze_page_structure(product_data.get("page_structure", {}))
        }
        
        # 종합 점수 계산
        analysis_result["overall_score"] = self._calculate_overall_score(analysis_result)
        
        return analysis_result
    
    async def _analyze_images(self, images: Dict[str, Any]) -> Dict[str, Any]:
        """이미지 분석: 썸네일 + 상세/제품 소개 이미지 개수·품질·다양성(alt) 반영"""
        detail_list = images.get("detail_images") or []
        item_goods = images.get("item_goods_images") or []
        # 상세 이미지 = detail + item_goods (중복 제거)
        seen = set(detail_list)
        for u in item_goods:
            if u not in seen:
                seen.add(u)
                detail_list = list(detail_list) + [u]
        image_count = len(detail_list)

        analysis = {
            "score": 0,
            "thumbnail_quality": "unknown",
            "image_count": image_count,
            "recommendations": [],
        }

        # 썸네일 품질 확인 (최적화: HEAD 요청만 사용)
        thumbnail = images.get("thumbnail")
        if thumbnail:
            try:
                async with httpx.AsyncClient() as client:
                    # HEAD 요청으로 빠르게 확인 (이미지 다운로드 없이)
                    response = await client.head(thumbnail, timeout=5.0, follow_redirects=True)
                    if response.status_code == 200:
                        # Content-Length로 크기 추정
                        content_length = response.headers.get("content-length")
                        if content_length:
                            size_kb = int(content_length) / 1024
                            if size_kb > 10:  # 10KB 이상이면 좋은 품질로 간주
                                analysis["thumbnail_quality"] = "good"
                                analysis["score"] += 30
                            else:
                                analysis["thumbnail_quality"] = "small"
                                analysis["score"] += 20
                        else:
                            analysis["thumbnail_quality"] = "good"
                            analysis["score"] += 30
                    else:
                        analysis["thumbnail_quality"] = "poor"
                        analysis["recommendations"].append("썸네일 이미지를 확인할 수 없습니다")
            except:
                # 썸네일 URL이 있으면 기본 점수 부여
                analysis["thumbnail_quality"] = "unknown"
                analysis["score"] += 15
        
        # 상세 이미지 개수 평가
        detail_count = analysis["image_count"]
        if detail_count >= 5:
            analysis["score"] += 40
        elif detail_count >= 3:
            analysis["score"] += 25
            analysis["recommendations"].append("상세 이미지를 2개 이상 추가하세요")
        else:
            analysis["score"] += 10
            analysis["recommendations"].append("상세 이미지를 최소 5개 이상 추가하세요")
        
        # 이미지 다양성 평가 (간단한 휴리스틱)
        if detail_count > 0:
            analysis["score"] += 30
        
        # 점수 정규화 (0-100)
        analysis["score"] = min(100, analysis["score"])
        
        return analysis
    
    def _analyze_description(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """상품 설명 분석"""
        description = product_data.get("description", "")
        description_length = len(description)
        
        analysis = {
            "score": 0,
            "description_length": description_length,
            "seo_keywords": [],
            "structure_quality": "unknown",
            "recommendations": []
        }
        
        # 설명 길이 평가
        if description_length >= 500:
            analysis["score"] += 40
        elif description_length >= 300:
            analysis["score"] += 25
            analysis["recommendations"].append("상품 설명을 500자 이상으로 늘리세요")
        else:
            analysis["score"] += 10
            analysis["recommendations"].append("상품 설명을 최소 500자 이상 작성하세요")
        
        # 구조화 여부 평가
        if "\n" in description or "<br>" in description or "<li>" in description:
            analysis["structure_quality"] = "good"
            analysis["score"] += 20
        else:
            analysis["structure_quality"] = "poor"
            analysis["recommendations"].append("줄바꿈이나 리스트를 사용하여 설명을 구조화하세요")
        
        # 키워드 추출
        keywords = product_data.get("search_keywords", [])
        if keywords:
            analysis["seo_keywords"] = keywords
            analysis["score"] += 20
        
        # 일본어 품질 (간단한 휴리스틱)
        japanese_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', description))
        if japanese_chars > description_length * 0.5:
            analysis["score"] += 20
        else:
            analysis["recommendations"].append("일본어 설명의 비율을 높이세요")
        
        analysis["score"] = min(100, analysis["score"])
        
        return analysis
    
    def _analyze_price(self, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """가격 분석 (개선된 크롤러 데이터 반영)"""
        # 유효성 검증된 가격만 사용 (100~1,000,000엔 범위)
        sale_price = price_data.get("sale_price")
        original_price = price_data.get("original_price")
        
        # 유효성 검증
        if sale_price and not (100 <= sale_price <= 1000000):
            sale_price = None
        if original_price and not (100 <= original_price <= 1000000):
            original_price = None
        
        # 할인율 계산 (유효한 가격이 있을 때만)
        discount_rate = price_data.get("discount_rate", 0)
        if sale_price and original_price and original_price > sale_price:
            calculated_discount = int((original_price - sale_price) / original_price * 100)
            discount_rate = calculated_discount
        
        analysis = {
            "score": 70 if sale_price else 0,  # 가격이 없으면 기본 점수 0
            "sale_price": sale_price,
            "original_price": original_price,
            "discount_rate": discount_rate,
            "positioning": "unknown",
            "recommendations": []
        }
        
        # 가격이 없으면 추출 실패로 간주
        if not sale_price:
            analysis["recommendations"].append("가격 정보를 확인할 수 없습니다. 크롤링 로직을 확인하세요")
            return analysis
        
        # 할인율 평가
        discount = analysis["discount_rate"]
        if 10 <= discount <= 30:
            analysis["score"] += 20
        elif discount > 30:
            analysis["score"] -= 10
            analysis["recommendations"].append("할인율이 너무 높습니다. 신뢰도에 영향을 줄 수 있습니다")
        elif discount > 0:
            analysis["score"] += 10
        
        # 가격 심리학 (9,800엔 vs 10,000엔)
        if sale_price:
            last_digits = sale_price % 1000
            if last_digits < 100:  # 예: 9,800엔
                analysis["score"] += 10
        
        analysis["score"] = min(100, analysis["score"])
        
        return analysis
    
    def _analyze_reviews(self, reviews_data: Dict[str, Any]) -> Dict[str, Any]:
        """리뷰 분석 (개선된 크롤러 데이터 반영)"""
        rating = reviews_data.get("rating", 0.0)
        review_count = reviews_data.get("review_count", 0)
        review_texts = reviews_data.get("reviews", [])
        
        # fallback: review_count가 0이지만 reviews 배열에 리뷰가 있으면 배열 길이 사용
        if review_count == 0 and len(review_texts) > 0:
            review_count = len(review_texts)
        
        analysis = {
            "score": 0,
            "rating": rating,
            "review_count": review_count,
            "reviews": review_texts,  # 리포트에서 사용할 수 있도록 포함
            "negative_ratio": 0.0,
            "recommendations": []
        }
        
        # 평점 평가
        if rating >= 4.5:
            analysis["score"] += 40
        elif rating >= 4.0:
            analysis["score"] += 30
        elif rating >= 3.5:
            analysis["score"] += 20
            analysis["recommendations"].append("평점을 4.0 이상으로 향상시키세요")
        elif rating > 0:
            analysis["score"] += 10
            analysis["recommendations"].append("상품 품질 및 서비스를 개선하여 평점을 높이세요")
        else:
            analysis["recommendations"].append("평점 정보를 확인할 수 없습니다")
        
        # 리뷰 수 평가
        if review_count >= 50:
            analysis["score"] += 30
        elif review_count >= 20:
            analysis["score"] += 25
        elif review_count >= 10:
            analysis["score"] += 20
            analysis["recommendations"].append("리뷰를 더 많이 받기 위해 샘플마켓 참가를 고려하세요")
        elif review_count > 0:
            analysis["score"] += 10
            analysis["recommendations"].append("리뷰가 부족합니다. 최소 10개 이상의 리뷰를 확보하세요")
        else:
            analysis["recommendations"].append("리뷰 정보를 확인할 수 없습니다. 크롤링 로직을 확인하세요")
        
        # 부정 리뷰 패턴 감지
        negative_keywords = ["悪い", "最悪", "ダメ", "問題", "不満", "返品", "配送", "遅い"]
        negative_count = 0
        for review in review_texts:
            for keyword in negative_keywords:
                if keyword in review:
                    negative_count += 1
                    break
        
        if review_texts:
            analysis["negative_ratio"] = negative_count / len(review_texts)
            if analysis["negative_ratio"] > 0.2:
                analysis["score"] -= 20
                analysis["recommendations"].append("부정 리뷰 비율이 높습니다. 상품 품질 및 배송 서비스를 개선하세요")
        
        analysis["score"] = max(0, min(100, analysis["score"]))
        
        return analysis
    
    def _analyze_seo(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """SEO 분석"""
        analysis = {
            "score": 0,
            "keywords_in_name": False,
            "keywords_in_description": False,
            "category_set": False,
            "brand_set": False,
            "recommendations": []
        }
        
        product_name = product_data.get("product_name", "")
        description = product_data.get("description", "")
        keywords = product_data.get("search_keywords", [])
        category = product_data.get("category")
        brand = product_data.get("brand")
        
        # 키워드가 상품명에 포함되어 있는지
        if keywords:
            for keyword in keywords:
                if keyword.lower() in product_name.lower():
                    analysis["keywords_in_name"] = True
                    analysis["score"] += 25
                    break
        
        if not analysis["keywords_in_name"]:
            analysis["recommendations"].append("상품명에 인기 검색 키워드를 포함하세요")
        
        # 키워드가 설명에 포함되어 있는지
        if keywords:
            for keyword in keywords:
                if keyword.lower() in description.lower():
                    analysis["keywords_in_description"] = True
                    analysis["score"] += 25
                    break
        
        # 카테고리 설정 여부
        if category:
            analysis["category_set"] = True
            analysis["score"] += 25
        else:
            analysis["recommendations"].append("적절한 카테고리를 선택하세요")
        
        # 브랜드 설정 여부
        if brand:
            analysis["brand_set"] = True
            analysis["score"] += 25
        else:
            analysis["recommendations"].append("브랜드를 등록하세요")
        
        analysis["score"] = min(100, analysis["score"])
        
        return analysis
    
    def _analyze_page_structure(self, page_structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        페이지 구조 분석 (정밀 분석 버전)
        dev-agent-kit 서브에이전트 원칙에 따라 더욱 정밀한 분석 수행:
        - 요소 간 관계 분석
        - 요소 품질 평가 (빈도, 위치, 계층 구조)
        - 시맨틱 구조의 깊이 분석
        - 요소 간 상관관계 분석
        - 접근성 및 SEO 관점의 구조 분석
        """
        # #region agent log - H2, H4 가설 검증
        log_path = "/Users/chunghyo/qoo10-ai-agent/.cursor/debug.log"
        try:
            # 디렉토리가 없으면 생성
            import os
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "id": f"log_{int(datetime.now().timestamp() * 1000)}_analyze_start",
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "location": "analyzer.py:_analyze_page_structure",
                    "message": "페이지 구조 분석 시작 (정밀 분석)",
                    "data": {
                        "page_structure_is_none": page_structure is None,
                        "page_structure_keys": list(page_structure.keys()) if page_structure else []
                    },
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H2,H4"
                }, ensure_ascii=False) + "\n")
        except: pass
        # #endregion
        
        analysis = {
            "score": 0,
            "total_classes": 0,
            "key_elements_present": {},
            "structure_completeness": {},
            "element_quality": {},  # 요소 품질 평가 추가
            "element_relationships": {},  # 요소 간 관계 분석 추가
            "semantic_depth": {},  # 시맨틱 구조 깊이 분석 추가
            "correlation_analysis": {},  # 요소 간 상관관계 분석 추가
            "accessibility_seo_score": 0,  # 접근성 및 SEO 점수 추가
            "recommendations": []
        }
        
        if not page_structure:
            analysis["recommendations"].append("페이지 구조 정보를 추출할 수 없습니다")
            analysis["elements"] = []  # 요소 단위 분석 (Report 등에서 사용)
            # #region agent log - H4 가설 검증
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "id": f"log_{int(datetime.now().timestamp() * 1000)}_page_structure_none",
                        "timestamp": int(datetime.now().timestamp() * 1000),
                        "location": "analyzer.py:_analyze_page_structure",
                        "message": "페이지 구조 정보 없음",
                        "data": {},
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "H4"
                    }, ensure_ascii=False) + "\n")
            except: pass
            # #endregion
            return analysis
        
        # 에러 페이지인 경우 특별 처리
        if page_structure.get("is_error_page", False):
            analysis["recommendations"].append("에러 페이지가 감지되었습니다. 크롤러가 페이지를 제대로 로드하지 못했을 수 있습니다.")
            analysis["is_error_page"] = True
            analysis["error_indicators"] = page_structure.get("error_indicators", [])
            analysis["elements"] = []  # 요소 단위 분석 (Report 등에서 사용)
            # #region agent log - H1 가설 검증
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "id": f"log_{int(datetime.now().timestamp() * 1000)}_error_page_detected",
                        "timestamp": int(datetime.now().timestamp() * 1000),
                        "location": "analyzer.py:_analyze_page_structure",
                        "message": "에러 페이지 감지됨",
                        "data": {
                            "error_indicators": page_structure.get("error_indicators", [])
                        },
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "H1"
                    }, ensure_ascii=False) + "\n")
            except: pass
            # #endregion
            return analysis
        
        # 전체 class 수
        all_classes = page_structure.get("all_div_classes", [])
        analysis["total_classes"] = len(all_classes)
        if analysis["total_classes"] < 20:
            analysis["recommendations"].append("페이지 구조가 단순합니다. 더 많은 정보 요소를 추가하세요")
        
        # 주요 요소 존재 여부 확인
        key_elements = page_structure.get("key_elements", {})
        semantic_structure = page_structure.get("semantic_structure", {})
        
        # #region agent log - H2, H3 가설 검증
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "id": f"log_{int(datetime.now().timestamp() * 1000)}_before_essential_check",
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "location": "analyzer.py:_analyze_page_structure",
                    "message": "필수 요소 체크 전 상태",
                    "data": {
                        "key_elements_keys": list(key_elements.keys()),
                        "semantic_structure_keys": list(semantic_structure.keys()),
                        "score_before": analysis["score"]
                    },
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H2,H3"
                }, ensure_ascii=False) + "\n")
        except: pass
        # #endregion
        
        # 필수 요소 체크 (key_elements와 semantic_structure 모두 고려)
        # key_elements 매핑: product_info, price_info, image_info 등
        # semantic_structure 매핑: product_name_elements, price_elements, image_elements, description_elements 등
        essential_elements_mapping = {
            "product_info": {
                "key_elements_key": "product_info",
                "semantic_structure_key": "product_name_elements",
                "name": "상품 정보"
            },
            "price_info": {
                "key_elements_key": "price_info",
                "semantic_structure_key": "price_elements",
                "name": "가격 정보"
            },
            "image_info": {
                "key_elements_key": "image_info",
                "semantic_structure_key": "image_elements",
                "name": "이미지 정보"
            },
            "description_info": {
                "key_elements_key": "description_info",  # key_elements에는 없을 수 있음
                "semantic_structure_key": "description_elements",
                "name": "상품 설명"
            }
        }
        
        for element_key, mapping in essential_elements_mapping.items():
            element_name = mapping["name"]
            found = False
            
            # key_elements에서 확인
            key_elements_key = mapping["key_elements_key"]
            if key_elements_key in key_elements and key_elements[key_elements_key]:
                found = True
                # #region agent log - H2, H3 가설 검증
                try:
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps({
                            "id": f"log_{int(datetime.now().timestamp() * 1000)}_element_found_key",
                            "timestamp": int(datetime.now().timestamp() * 1000),
                            "location": "analyzer.py:_analyze_page_structure",
                            "message": f"요소 발견 (key_elements): {element_key}",
                            "data": {"element_key": element_key, "key_used": key_elements_key, "score_before": analysis["score"]},
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "H2,H3"
                        }, ensure_ascii=False) + "\n")
                except: pass
                # #endregion
            
            # semantic_structure에서 확인 (key_elements에서 찾지 못한 경우)
            if not found:
                semantic_key = mapping["semantic_structure_key"]
                semantic_value = semantic_structure.get(semantic_key, [])
                # 빈 배열이 아닌 경우에만 발견으로 간주
                if semantic_key in semantic_structure and semantic_value and len(semantic_value) > 0:
                    found = True
                    # #region agent log - H2, H3 가설 검증
                    try:
                        with open(log_path, "a", encoding="utf-8") as f:
                            f.write(json.dumps({
                                "id": f"log_{int(datetime.now().timestamp() * 1000)}_element_found_semantic",
                                "timestamp": int(datetime.now().timestamp() * 1000),
                                "location": "analyzer.py:_analyze_page_structure",
                                "message": f"요소 발견 (semantic_structure): {element_key}",
                                "data": {
                                    "element_key": element_key,
                                    "semantic_key_used": semantic_key,
                                    "semantic_value_length": len(semantic_value),
                                    "score_before": analysis["score"]
                                },
                                "sessionId": "debug-session",
                                "runId": "run1",
                                "hypothesisId": "H2,H3"
                            }, ensure_ascii=False) + "\n")
                    except: pass
                    # #endregion
            
            if found:
                analysis["key_elements_present"][element_key] = True
            else:
                analysis["key_elements_present"][element_key] = False
                analysis["recommendations"].append(f"{element_name} 요소가 페이지에서 확인되지 않습니다")
                # #region agent log - H2, H3 가설 검증
                try:
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps({
                            "id": f"log_{int(datetime.now().timestamp() * 1000)}_element_not_found",
                            "timestamp": int(datetime.now().timestamp() * 1000),
                            "location": "analyzer.py:_analyze_page_structure",
                            "message": f"요소 미발견: {element_key}",
                            "data": {
                                "element_key": element_key,
                                "key_elements_key": key_elements_key,
                                "semantic_structure_key": mapping["semantic_structure_key"],
                                "in_key_elements": key_elements_key in key_elements,
                                "in_semantic_structure": mapping["semantic_structure_key"] in semantic_structure,
                                "semantic_value_length": len(semantic_structure.get(mapping["semantic_structure_key"], []))
                            },
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "H2,H3"
                        }, ensure_ascii=False) + "\n")
                except: pass
                # #endregion
        
        # 선택적 요소 체크 (key_elements와 semantic_structure 모두 고려)
        optional_elements_mapping = {
            "review_info": {
                "key_elements_key": "review_info",
                "semantic_structure_key": "review_elements",
                "name": "리뷰 정보"
            },
            "seller_info": {
                "key_elements_key": "seller_info",
                "semantic_structure_key": "seller_elements",
                "name": "판매자 정보"
            },
            "shipping_info": {
                "key_elements_key": "shipping_info",
                "semantic_structure_key": "shipping_elements",
                "name": "배송 정보"
            },
            "coupon_info": {
                "key_elements_key": "coupon_info",
                "semantic_structure_key": "coupon_elements",
                "name": "쿠폰 정보"
            },
            "qpoint_info": {
                "key_elements_key": "qpoint_info",
                "semantic_structure_key": "qpoint_elements",
                "name": "Qポイント 정보"
            }
        }
        
        optional_count = 0
        for element_key, mapping in optional_elements_mapping.items():
            found = False
            
            # key_elements에서 확인
            key_elements_key = mapping["key_elements_key"]
            if key_elements_key in key_elements and key_elements[key_elements_key]:
                found = True
            
            # semantic_structure에서 확인 (key_elements에서 찾지 못한 경우)
            if not found:
                semantic_key = mapping["semantic_structure_key"]
                semantic_value = semantic_structure.get(semantic_key, [])
                if semantic_key in semantic_structure and semantic_value and len(semantic_value) > 0:
                    found = True
            
            if found:
                analysis["key_elements_present"][element_key] = True
                optional_count += 1
            else:
                analysis["key_elements_present"][element_key] = False
        if optional_count == 0:
            analysis["recommendations"].append("추가 정보 요소(리뷰, 판매자 정보, 배송 정보 등)를 추가하면 신뢰도가 향상됩니다")
        
        # 구조 완성도 평가
        structure_completeness = {
            "has_product_name": len(semantic_structure.get("product_name_elements", [])) > 0,
            "has_price": len(semantic_structure.get("price_elements", [])) > 0,
            "has_images": len(semantic_structure.get("image_elements", [])) > 0,
            "has_description": len(semantic_structure.get("description_elements", [])) > 0,
            "has_reviews": len(semantic_structure.get("review_elements", [])) > 0,
            "has_seller": len(semantic_structure.get("seller_elements", [])) > 0,
            "has_shipping": len(semantic_structure.get("shipping_elements", [])) > 0,
            "has_coupon": len(semantic_structure.get("coupon_elements", [])) > 0,
            "has_qpoint": len(semantic_structure.get("qpoint_elements", [])) > 0
        }
        
        analysis["structure_completeness"] = structure_completeness
        completeness_count = sum(1 for v in structure_completeness.values() if v)
        if completeness_count < 3:
            analysis["recommendations"].append("페이지 구조가 불완전합니다. 필수 요소들을 추가하세요")
        
        # class 빈도 분석 (자주 사용되는 class는 중요한 요소일 가능성이 높음)
        class_frequency = page_structure.get("class_frequency", {})
        # #region agent log - H5 가설 검증
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "id": f"log_{int(datetime.now().timestamp() * 1000)}_before_frequency",
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "location": "analyzer.py:_analyze_page_structure",
                    "message": "class 빈도 분석 전",
                    "data": {
                        "class_frequency_exists": bool(class_frequency),
                        "class_frequency_count": len(class_frequency) if class_frequency else 0,
                        "score_before": analysis["score"]
                    },
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H5"
                }, ensure_ascii=False) + "\n")
        except: pass
        # #endregion
        
        if class_frequency:
            # 가장 많이 사용되는 class 상위 10개
            top_classes = sorted(class_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
            analysis["top_classes"] = [{"class": cls, "frequency": freq} for cls, freq in top_classes]
            
            # 중요한 요소가 자주 사용되는지 확인
            important_keywords = ["product", "goods", "price", "image", "detail", "description"]
            important_class_count = sum(1 for cls, _ in top_classes if any(kw in cls.lower() for kw in important_keywords))
            
            # #region agent log - H5 가설 검증
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "id": f"log_{int(datetime.now().timestamp() * 1000)}_frequency_calc",
                        "timestamp": int(datetime.now().timestamp() * 1000),
                        "location": "analyzer.py:_analyze_page_structure",
                        "message": "class 빈도 계산 결과",
                        "data": {
                            "top_classes_count": len(top_classes),
                            "important_class_count": important_class_count,
                            "score_before_frequency": analysis["score"]
                        },
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "H5"
                    }, ensure_ascii=False) + "\n")
            except: pass
            # #endregion
            
            analysis["class_frequency_score"] = min(100, important_class_count * 20)  # 0-100
        else:
            analysis["class_frequency_score"] = 0
        
        # ===== 정밀 분석: 요소 품질 / 관계 / 시맨틱 깊이 / 상관관계 / 접근성·SEO =====
        analysis["element_quality"] = self._analyze_element_quality(
            key_elements, semantic_structure, class_frequency
        )
        analysis["element_relationships"] = self._analyze_element_relationships(
            key_elements, semantic_structure
        )
        analysis["semantic_depth"] = self._analyze_semantic_depth(semantic_structure)
        analysis["correlation_analysis"] = self._analyze_element_correlations(
            key_elements, semantic_structure, structure_completeness
        )
        analysis["accessibility_seo_score"] = self._analyze_accessibility_seo(
            semantic_structure, key_elements, class_frequency, page_structure
        )
        
        # 스펙 기반 가중치 합산 (.spec-kit/product-page-elements-spec.md)
        essential_count = sum(1 for k in ["product_info", "price_info", "image_info", "description_info"] if analysis["key_elements_present"].get(k))
        essential_score = (essential_count / 4) * 100 if essential_count <= 4 else 100
        optional_score = (optional_count / 5) * 100 if optional_count <= 5 else 100
        completeness_score = (completeness_count / 9) * 100 if completeness_count <= 9 else 100
        class_freq_score = analysis.get("class_frequency_score", 0)
        quality_score = analysis["element_quality"].get("overall_quality_score", 0)
        relationship_score = analysis["element_relationships"].get("relationship_score", 0)
        depth_score = min(100, analysis["semantic_depth"].get("depth_score", 0))
        correlation_score = analysis["correlation_analysis"].get("correlation_score", 0)
        accessibility_score = min(100, analysis["accessibility_seo_score"])
        
        weights = {
            "essential": 0.25,      # 필수 4요소 25%
            "optional": 0.15,      # 선택 5요소 15%
            "completeness": 0.15,  # 구조 완성도 15%
            "class_frequency": 0.10,  # 클래스 빈도 10%
            "quality": 0.10,       # 요소 품질 10%
            "relationship": 0.10, # 요소 관계 10%
            "depth": 0.05,         # 시맨틱 깊이 5%
            "correlation": 0.05,   # 상관관계 5%
            "accessibility": 0.05, # 접근성·SEO 5%
        }
        analysis["score"] = int(
            (
                essential_score * weights["essential"]
                + optional_score * weights["optional"]
                + completeness_score * weights["completeness"]
                + class_freq_score * weights["class_frequency"]
                + quality_score * weights["quality"]
                + relationship_score * weights["relationship"]
                + depth_score * weights["depth"]
                + correlation_score * weights["correlation"]
                + accessibility_score * weights["accessibility"]
            )
        )
        analysis["score"] = min(100, max(0, analysis["score"]))
        analysis["grade"] = self._get_page_structure_grade(analysis["score"])
        
        # 요소(element) 단위 분석 결과 (Analysis Agent → Recommendation/Checklist/Report 반영용)
        # doc/agents, .spec-kit/product-page-elements-spec.md 기준
        ELEMENT_SPEC = [
            ("product_info", "상품 정보", "essential"),
            ("price_info", "가격 정보", "essential"),
            ("image_info", "이미지 정보", "essential"),
            ("description_info", "상품 설명", "essential"),
            ("review_info", "리뷰 정보", "optional"),
            ("seller_info", "판매자 정보", "optional"),
            ("shipping_info", "배송 정보", "optional"),
            ("coupon_info", "쿠폰 정보", "optional"),
            ("qpoint_info", "Qポイント 정보", "optional"),
        ]
        key_present = analysis.get("key_elements_present", {})
        structure_completeness = analysis.get("structure_completeness", {})
        completeness_map = {
            "product_info": "has_product_name",
            "price_info": "has_price",
            "image_info": "has_images",
            "description_info": "has_description",
            "review_info": "has_reviews",
            "seller_info": "has_seller",
            "shipping_info": "has_shipping",
            "coupon_info": "has_coupon",
            "qpoint_info": "has_qpoint",
        }
        element_recommendations = {
            "product_info": "상품 정보 요소가 페이지에서 확인되지 않습니다",
            "price_info": "가격 정보 요소가 페이지에서 확인되지 않습니다",
            "image_info": "이미지 정보 요소가 페이지에서 확인되지 않습니다",
            "description_info": "상품 설명 요소가 페이지에서 확인되지 않습니다",
            "review_info": None,
            "seller_info": None,
            "shipping_info": None,
            "coupon_info": None,
            "qpoint_info": None,
        }
        elements_out = []
        for element_id, name_ko, kind in ELEMENT_SPEC:
            present = key_present.get(element_id, False)
            comp_key = completeness_map.get(element_id)
            complete = structure_completeness.get(comp_key, False) if comp_key else present
            score = 100 if (present or complete) else 0
            rec = None
            if not (present or complete) and element_recommendations.get(element_id):
                rec = element_recommendations[element_id]
            for r in analysis.get("recommendations", []):
                if r and name_ko in r and not rec:
                    rec = r
                    break
            quality = "good" if score >= 80 else ("fair" if score >= 50 else "poor")
            elements_out.append({
                "element_id": element_id,
                "name_ko": name_ko,
                "kind": kind,
                "score": score,
                "present": present or complete,
                "quality": quality,
                "recommendation": rec,
            })
        analysis["elements"] = elements_out
        
        # #region agent log - H2 가설 검증
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "id": f"log_{int(datetime.now().timestamp() * 1000)}_analyze_end",
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "location": "analyzer.py:_analyze_page_structure",
                    "message": "페이지 구조 분석 완료 (정밀 분석)",
                    "data": {
                        "final_score": analysis["score"],
                        "total_classes": analysis["total_classes"],
                        "key_elements_present": analysis["key_elements_present"],
                        "elements_count": len(analysis.get("elements", [])),
                        "element_quality_score": analysis["element_quality"].get("overall_quality_score", 0),
                        "relationship_score": analysis["element_relationships"].get("relationship_score", 0),
                        "semantic_depth_score": analysis["semantic_depth"].get("depth_score", 0),
                        "correlation_score": analysis["correlation_analysis"].get("correlation_score", 0),
                        "accessibility_seo_score": analysis["accessibility_seo_score"],
                        "recommendations_count": len(analysis["recommendations"])
                    },
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H2"
                }, ensure_ascii=False) + "\n")
        except: pass
        # #endregion
        
        return analysis
    
    def _analyze_element_quality(
        self, 
        key_elements: Dict[str, Any], 
        semantic_structure: Dict[str, Any],
        class_frequency: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        요소 품질 평가
        - 빈도 분석: 자주 사용되는 요소는 중요도가 높음
        - 다양성 분석: 다양한 요소가 존재하는지 확인
        - 일관성 분석: 유사한 패턴의 요소들이 일관되게 사용되는지
        """
        quality_analysis = {
            "overall_quality_score": 0,
            "frequency_analysis": {},
            "diversity_score": 0,
            "consistency_score": 0,
            "recommendations": []
        }
        
        # 빈도 분석: 각 요소 카테고리의 빈도 평가
        frequency_scores = {}
        for category, elements in key_elements.items():
            # 방어: 리스트가 아니면 단일 dict는 리스트로, 그 외는 빈 리스트
            if not isinstance(elements, list):
                if isinstance(elements, dict):
                    elements = [elements]
                else:
                    elements = []
            valid_elems = [e for e in elements if isinstance(e, dict)]
            valid_count = len(valid_elems)
            # 비 dict 항목은 제외하고 valid_elems만으로 빈도 계산
            total_frequency = sum(e.get("frequency", 1) for e in valid_elems)
            avg_frequency = (total_frequency / valid_count) if valid_count else 0
            frequency_scores[category] = {
                "element_count": valid_count,
                "avg_frequency": avg_frequency,
                "score": min(100, valid_count * 10 + int(avg_frequency * 5)) if valid_count else 0
            }
        
        quality_analysis["frequency_analysis"] = frequency_scores
        
        # 빈도 점수 계산 (평균)
        if frequency_scores:
            avg_frequency_score = sum(
                score["score"] for score in frequency_scores.values()
            ) / len(frequency_scores)
            quality_analysis["overall_quality_score"] += int(avg_frequency_score * 0.4)
        
        # 다양성 분석: 시맨틱 구조의 다양성 평가
        semantic_keys = list(semantic_structure.keys())
        diversity_score = 0
        
        # 필수 요소 카테고리 확인
        essential_categories = [
            "product_name_elements", "price_elements", 
            "image_elements", "description_elements"
        ]
        essential_found = sum(1 for key in essential_categories if key in semantic_keys)
        diversity_score += (essential_found / len(essential_categories)) * 50
        
        # 선택적 요소 카테고리 확인
        optional_categories = [
            "review_elements", "seller_elements", 
            "shipping_elements", "coupon_elements", "qpoint_elements"
        ]
        optional_found = sum(1 for key in optional_categories if key in semantic_keys)
        diversity_score += (optional_found / len(optional_categories)) * 50
        
        quality_analysis["diversity_score"] = int(diversity_score)
        quality_analysis["overall_quality_score"] += int(diversity_score * 0.3)
        
        # 일관성 분석: 유사한 패턴의 요소들이 일관되게 사용되는지
        consistency_score = 0
        
        # 각 카테고리 내에서 요소들의 빈도 일관성 확인
        for category, elements in key_elements.items():
            if len(elements) > 1:
                frequencies = [
                    elem.get("frequency", 1) 
                    for elem in elements 
                    if isinstance(elem, dict)
                ]
                if frequencies:
                    # 표준편차가 낮을수록 일관성이 높음
                    avg_freq = sum(frequencies) / len(frequencies)
                    variance = sum((f - avg_freq) ** 2 for f in frequencies) / len(frequencies)
                    std_dev = variance ** 0.5
                    
                    # 표준편차가 평균의 30% 이하면 일관성이 높음
                    if avg_freq > 0 and std_dev / avg_freq < 0.3:
                        consistency_score += 10
        
        quality_analysis["consistency_score"] = min(100, consistency_score)
        quality_analysis["overall_quality_score"] += int(quality_analysis["consistency_score"] * 0.3)
        
        # 품질 점수 정규화
        quality_analysis["overall_quality_score"] = min(100, quality_analysis["overall_quality_score"])
        
        # 추천사항
        if quality_analysis["diversity_score"] < 50:
            quality_analysis["recommendations"].append(
                "페이지 요소의 다양성이 부족합니다. 더 많은 정보 요소를 추가하세요"
            )
        
        if quality_analysis["consistency_score"] < 50:
            quality_analysis["recommendations"].append(
                "요소 사용의 일관성이 부족합니다. 유사한 패턴의 요소를 일관되게 사용하세요"
            )
        
        return quality_analysis
    
    def _analyze_element_relationships(
        self,
        key_elements: Dict[str, Any],
        semantic_structure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        요소 간 관계 분석
        - 필수 요소 간의 연결성 확인
        - 관련 요소들의 그룹화 확인
        - 요소 간 의존성 분석
        """
        relationship_analysis = {
            "relationship_score": 0,
            "essential_connections": {},
            "element_groups": {},
            "dependency_analysis": {},
            "recommendations": []
        }
        
        # 필수 요소 간 연결성 확인
        essential_pairs = [
            ("product_info", "price_info", "상품 정보와 가격 정보"),
            ("product_info", "image_info", "상품 정보와 이미지 정보"),
            ("price_info", "image_info", "가격 정보와 이미지 정보"),
            ("product_info", "description_info", "상품 정보와 설명 정보")
        ]
        
        connections_found = 0
        for elem1_key, elem2_key, pair_name in essential_pairs:
            elem1_found = (
                elem1_key in key_elements and key_elements[elem1_key]
            ) or (
                self._get_semantic_key(elem1_key) in semantic_structure 
                and semantic_structure[self._get_semantic_key(elem1_key)]
            )
            
            elem2_found = (
                elem2_key in key_elements and key_elements[elem2_key]
            ) or (
                self._get_semantic_key(elem2_key) in semantic_structure 
                and semantic_structure[self._get_semantic_key(elem2_key)]
            )
            
            if elem1_found and elem2_found:
                connections_found += 1
                relationship_analysis["essential_connections"][pair_name] = True
            else:
                relationship_analysis["essential_connections"][pair_name] = False
        
        # 연결성 점수 계산
        if essential_pairs:
            connection_score = (connections_found / len(essential_pairs)) * 100
            relationship_analysis["relationship_score"] += int(connection_score * 0.6)
        
        # 요소 그룹화 확인
        # 관련 요소들이 함께 존재하는지 확인
        related_groups = {
            "구매 정보 그룹": ["price_info", "coupon_info", "qpoint_info"],
            "상품 정보 그룹": ["product_info", "image_info", "description_info"],
            "신뢰 정보 그룹": ["review_info", "seller_info", "shipping_info"]
        }
        
        groups_complete = 0
        for group_name, group_elements in related_groups.items():
            found_count = 0
            for elem_key in group_elements:
                if (
                    elem_key in key_elements and key_elements[elem_key]
                ) or (
                    self._get_semantic_key(elem_key) in semantic_structure 
                    and semantic_structure[self._get_semantic_key(elem_key)]
                ):
                    found_count += 1
            
            completeness = found_count / len(group_elements)
            relationship_analysis["element_groups"][group_name] = {
                "completeness": completeness,
                "found_elements": found_count,
                "total_elements": len(group_elements)
            }
            
            if completeness >= 0.7:  # 70% 이상 완성도
                groups_complete += 1
        
        # 그룹화 점수 계산
        if related_groups:
            group_score = (groups_complete / len(related_groups)) * 100
            relationship_analysis["relationship_score"] += int(group_score * 0.4)
        
        relationship_analysis["relationship_score"] = min(100, relationship_analysis["relationship_score"])
        
        # 추천사항
        if relationship_analysis["relationship_score"] < 60:
            relationship_analysis["recommendations"].append(
                "필수 요소 간의 연결성이 부족합니다. 관련 정보를 함께 배치하세요"
            )
        
        return relationship_analysis
    
    def _analyze_semantic_depth(self, semantic_structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        시맨틱 구조 깊이 분석
        - 각 카테고리의 요소 깊이 확인
        - 중첩 레벨 분석
        - 요소 그룹화 깊이 확인
        """
        depth_analysis = {
            "depth_score": 0,
            "category_depths": {},
            "average_depth": 0,
            "max_depth": 0,
            "recommendations": []
        }
        
        total_depth = 0
        category_count = 0
        max_depth = 0
        
        for category, elements in semantic_structure.items():
            if elements:
                # 요소 개수로 깊이 측정
                element_count = len(elements) if isinstance(elements, list) else 1
                
                # 빈도 정보가 있으면 가중치 적용
                weighted_depth = element_count
                if isinstance(elements, list) and elements:
                    # 첫 번째 요소가 딕셔너리이고 frequency 정보가 있으면
                    if isinstance(elements[0], dict):
                        avg_frequency = sum(
                            e.get("frequency", 1) for e in elements if isinstance(e, dict)
                        ) / len(elements)
                        weighted_depth = element_count * (1 + avg_frequency / 10)
                
                depth_analysis["category_depths"][category] = {
                    "element_count": element_count,
                    "weighted_depth": weighted_depth
                }
                
                total_depth += weighted_depth
                category_count += 1
                max_depth = max(max_depth, weighted_depth)
        
        if category_count > 0:
            depth_analysis["average_depth"] = total_depth / category_count
            depth_analysis["max_depth"] = max_depth
            
            # 깊이 점수 계산 (평균 깊이와 최대 깊이를 고려)
            depth_score = min(100, int(depth_analysis["average_depth"] * 5) + int(max_depth * 2))
            depth_analysis["depth_score"] = depth_score
        
        # 추천사항
        if depth_analysis["average_depth"] < 2:
            depth_analysis["recommendations"].append(
                "시맨틱 구조의 깊이가 부족합니다. 더 상세한 요소 구조를 추가하세요"
            )
        
        return depth_analysis
    
    def _analyze_element_correlations(
        self,
        key_elements: Dict[str, Any],
        semantic_structure: Dict[str, Any],
        structure_completeness: Dict[str, bool]
    ) -> Dict[str, Any]:
        """
        요소 간 상관관계 분석
        - 가격-이미지 상관관계
        - 설명-리뷰 상관관계
        - 상품 정보-판매자 정보 상관관계
        """
        correlation_analysis = {
            "correlation_score": 0,
            "correlations": {},
            "recommendations": []
        }
        
        # 상관관계 쌍 정의
        correlation_pairs = [
            {
                "pair": ("price_info", "image_info"),
                "name": "가격-이미지",
                "description": "가격 정보와 이미지 정보는 함께 제공되어야 구매 결정에 도움이 됩니다"
            },
            {
                "pair": ("description_info", "review_info"),
                "name": "설명-리뷰",
                "description": "상품 설명과 리뷰 정보가 함께 있으면 신뢰도가 향상됩니다"
            },
            {
                "pair": ("product_info", "seller_info"),
                "name": "상품-판매자",
                "description": "상품 정보와 판매자 정보가 함께 있으면 신뢰도가 향상됩니다"
            },
            {
                "pair": ("image_info", "description_info"),
                "name": "이미지-설명",
                "description": "이미지와 설명이 함께 있으면 상품 이해도가 향상됩니다"
            }
        ]
        
        correlations_found = 0
        for pair_info in correlation_pairs:
            elem1_key, elem2_key = pair_info["pair"]
            pair_name = pair_info["name"]
            
            # 요소 존재 여부 확인
            elem1_found = (
                elem1_key in key_elements and key_elements[elem1_key]
            ) or (
                self._get_semantic_key(elem1_key) in semantic_structure 
                and semantic_structure[self._get_semantic_key(elem1_key)]
            )
            
            elem2_found = (
                elem2_key in key_elements and key_elements[elem2_key]
            ) or (
                self._get_semantic_key(elem2_key) in semantic_structure 
                and semantic_structure[self._get_semantic_key(elem2_key)]
            )
            
            # 둘 다 존재하면 상관관계가 좋음
            if elem1_found and elem2_found:
                correlations_found += 1
                correlation_analysis["correlations"][pair_name] = {
                    "exists": True,
                    "strength": "strong"
                }
            elif elem1_found or elem2_found:
                # 하나만 존재하면 약한 상관관계
                correlation_analysis["correlations"][pair_name] = {
                    "exists": False,
                    "strength": "weak",
                    "missing": elem2_key if elem1_found else elem1_key
                }
                correlation_analysis["recommendations"].append(
                    f"{pair_info['description']} ({pair_name} 상관관계)"
                )
            else:
                # 둘 다 없으면 상관관계 없음
                correlation_analysis["correlations"][pair_name] = {
                    "exists": False,
                    "strength": "none"
                }
        
        # 상관관계 점수 계산
        if correlation_pairs:
            correlation_score = (correlations_found / len(correlation_pairs)) * 100
            correlation_analysis["correlation_score"] = int(correlation_score)
        
        return correlation_analysis
    
    def _analyze_accessibility_seo(
        self,
        semantic_structure: Dict[str, Any],
        key_elements: Dict[str, Any],
        class_frequency: Dict[str, int],
        page_structure: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        접근성 및 SEO 관점의 구조 분석
        - 시맨틱 HTML 요소 사용 확인
        - 구조화된 데이터 확인
        - 접근성 요소(role, aria-label) 확인 — page_structure.accessibility_hints 사용
        """
        score = 0
        
        # 시맨틱 요소 확인
        semantic_elements_found = len([
            key for key in semantic_structure.keys() 
            if semantic_structure[key]
        ])
        if semantic_elements_found >= 7:
            score += 40
        elif semantic_elements_found >= 5:
            score += 30
        elif semantic_elements_found >= 3:
            score += 20
        else:
            score += 10
        
        # 필수 SEO 요소 확인
        seo_essential = [
            "product_name_elements", "price_elements", 
            "image_elements", "description_elements"
        ]
        seo_found = sum(1 for key in seo_essential if key in semantic_structure and semantic_structure[key])
        if seo_found == len(seo_essential):
            score += 30
        elif seo_found >= 3:
            score += 20
        elif seo_found >= 2:
            score += 10
        
        # 구조화된 데이터 확인 (class 빈도로 추정)
        if class_frequency:
            important_keywords = ["product", "goods", "item", "detail", "info"]
            important_classes = [
                cls for cls in class_frequency.keys()
                if any(kw in cls.lower() for kw in important_keywords)
            ]
            if len(important_classes) >= 10:
                score += 30
            elif len(important_classes) >= 5:
                score += 20
            elif len(important_classes) >= 3:
                score += 10
        
        # 접근성 힌트(role, aria-label) 반영 — 크롤러가 수집한 경우 가산
        if page_structure:
            hints = page_structure.get("accessibility_hints") or {}
            roles = hints.get("roles") or []
            aria_count = hints.get("aria_labels_count") or 0
            if roles or aria_count > 0:
                score = min(100, score + 10)
        
        return min(100, score)
    
    def _get_page_structure_grade(self, score: int) -> str:
        """페이지 구조 분석 등급 (.spec-kit/product-page-elements-spec.md 기준)"""
        if score >= 90:
            return "Excellent"
        if score >= 70:
            return "Good"
        if score >= 50:
            return "Fair"
        return "Poor"
    
    def _get_semantic_key(self, element_key: str) -> str:
        """요소 키를 시맨틱 키로 변환"""
        mapping = {
            "product_info": "product_name_elements",
            "price_info": "price_elements",
            "image_info": "image_elements",
            "description_info": "description_elements",
            "review_info": "review_elements",
            "seller_info": "seller_elements",
            "shipping_info": "shipping_elements",
            "coupon_info": "coupon_elements",
            "qpoint_info": "qpoint_elements"
        }
        return mapping.get(element_key, element_key)
    
    def _calculate_overall_score(self, analysis_result: Dict[str, Any]) -> int:
        """종합 점수 계산"""
        weights = {
            "image_analysis": 0.20,
            "description_analysis": 0.20,
            "price_analysis": 0.15,
            "review_analysis": 0.15,
            "seo_analysis": 0.15,
            "page_structure_analysis": 0.15
        }
        
        overall = 0
        for key, weight in weights.items():
            if key in analysis_result:
                score = analysis_result[key].get("score", 0)
                overall += score * weight
        
        return int(overall)
