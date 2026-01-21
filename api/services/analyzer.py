"""
상품 분석 서비스
수집된 상품 데이터를 분석하여 점수와 인사이트를 제공합니다.

분석 원칙:
- CRAWLING_ANALYSIS_PRINCIPLES.md 참조
- 모든 분석은 일관된 기준과 원칙을 따라야 함
- 크롤링 방법(crawled_with)에 따라 적절한 분석 수행
"""
from typing import Dict, Any, List
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
        """이미지 분석 (최적화 버전)"""
        analysis = {
            "score": 0,
            "thumbnail_quality": "unknown",
            "image_count": len(images.get("detail_images", [])),
            "recommendations": []
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
        페이지 구조 분석
        모든 div class를 분석하여 페이지의 구조적 완성도를 평가
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
                    "message": "페이지 구조 분석 시작",
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
            "recommendations": []
        }
        
        if not page_structure:
            analysis["recommendations"].append("페이지 구조 정보를 추출할 수 없습니다")
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
        
        # 기본 점수 (class가 많을수록 구조가 복잡하고 완성도가 높음)
        if analysis["total_classes"] >= 50:
            analysis["score"] += 20
        elif analysis["total_classes"] >= 30:
            analysis["score"] += 15
        elif analysis["total_classes"] >= 20:
            analysis["score"] += 10
        else:
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
                analysis["score"] += 15
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
        
        # 선택적 요소 점수 (최대 20점)
        if optional_count >= 4:
            analysis["score"] += 20
        elif optional_count >= 3:
            analysis["score"] += 15
        elif optional_count >= 2:
            analysis["score"] += 10
        elif optional_count >= 1:
            analysis["score"] += 5
        else:
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
        
        # 완성도 점수 계산
        completeness_score = sum(1 for v in structure_completeness.values() if v)
        if completeness_score >= 7:
            analysis["score"] += 20
        elif completeness_score >= 5:
            analysis["score"] += 15
        elif completeness_score >= 3:
            analysis["score"] += 10
        else:
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
            
            if important_class_count >= 5:
                analysis["score"] += 10
            elif important_class_count >= 3:
                analysis["score"] += 5
        
        # 점수 정규화 (0-100)
        analysis["score"] = min(100, max(0, analysis["score"]))
        
        # #region agent log - H2 가설 검증
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "id": f"log_{int(datetime.now().timestamp() * 1000)}_analyze_end",
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "location": "analyzer.py:_analyze_page_structure",
                    "message": "페이지 구조 분석 완료",
                    "data": {
                        "final_score": analysis["score"],
                        "total_classes": analysis["total_classes"],
                        "key_elements_present": analysis["key_elements_present"],
                        "recommendations_count": len(analysis["recommendations"])
                    },
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H2"
                }, ensure_ascii=False) + "\n")
        except: pass
        # #endregion
        
        return analysis
    
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
