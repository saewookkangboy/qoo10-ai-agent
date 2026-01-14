"""
상품 분석 서비스
수집된 상품 데이터를 분석하여 점수와 인사이트를 제공합니다.
"""
from typing import Dict, Any, List
import re
from PIL import Image
import httpx
import asyncio


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
        """가격 분석"""
        analysis = {
            "score": 70,  # 기본 점수
            "sale_price": price_data.get("sale_price"),
            "original_price": price_data.get("original_price"),
            "discount_rate": price_data.get("discount_rate", 0),
            "positioning": "unknown",
            "recommendations": []
        }
        
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
        sale_price = analysis["sale_price"]
        if sale_price:
            last_digits = sale_price % 1000
            if last_digits < 100:  # 예: 9,800엔
                analysis["score"] += 10
        
        analysis["score"] = min(100, analysis["score"])
        
        return analysis
    
    def _analyze_reviews(self, reviews_data: Dict[str, Any]) -> Dict[str, Any]:
        """리뷰 분석"""
        rating = reviews_data.get("rating", 0.0)
        review_count = reviews_data.get("review_count", 0)
        review_texts = reviews_data.get("reviews", [])
        
        analysis = {
            "score": 0,
            "rating": rating,
            "review_count": review_count,
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
        else:
            analysis["score"] += 10
            analysis["recommendations"].append("상품 품질 및 서비스를 개선하여 평점을 높이세요")
        
        # 리뷰 수 평가
        if review_count >= 50:
            analysis["score"] += 30
        elif review_count >= 20:
            analysis["score"] += 25
        elif review_count >= 10:
            analysis["score"] += 20
            analysis["recommendations"].append("리뷰를 더 많이 받기 위해 샘플마켓 참가를 고려하세요")
        else:
            analysis["score"] += 10
            analysis["recommendations"].append("리뷰가 부족합니다. 최소 10개 이상의 리뷰를 확보하세요")
        
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
        analysis = {
            "score": 0,
            "total_classes": 0,
            "key_elements_present": {},
            "structure_completeness": {},
            "recommendations": []
        }
        
        if not page_structure:
            analysis["recommendations"].append("페이지 구조 정보를 추출할 수 없습니다")
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
        
        # 필수 요소 체크
        essential_elements = {
            "product_info": "상품 정보",
            "price_info": "가격 정보",
            "image_info": "이미지 정보",
            "description_elements": "상품 설명"
        }
        
        for element_key, element_name in essential_elements.items():
            # key_elements에서 확인
            if element_key in key_elements and key_elements[element_key]:
                analysis["key_elements_present"][element_key] = True
                analysis["score"] += 15
            # semantic_structure에서 확인
            elif element_key in semantic_structure and semantic_structure[element_key]:
                analysis["key_elements_present"][element_key] = True
                analysis["score"] += 15
            else:
                analysis["key_elements_present"][element_key] = False
                analysis["recommendations"].append(f"{element_name} 요소가 페이지에서 확인되지 않습니다")
        
        # 선택적 요소 체크
        optional_elements = {
            "review_info": "리뷰 정보",
            "seller_info": "판매자 정보",
            "shipping_info": "배송 정보",
            "coupon_info": "쿠폰 정보",
            "qpoint_info": "Qポイント 정보"
        }
        
        optional_count = 0
        for element_key, element_name in optional_elements.items():
            # key_elements에서 확인
            if element_key in key_elements and key_elements[element_key]:
                analysis["key_elements_present"][element_key] = True
                optional_count += 1
            # semantic_structure에서 확인
            elif element_key in semantic_structure and semantic_structure[element_key]:
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
        if class_frequency:
            # 가장 많이 사용되는 class 상위 10개
            top_classes = sorted(class_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
            analysis["top_classes"] = [{"class": cls, "frequency": freq} for cls, freq in top_classes]
            
            # 중요한 요소가 자주 사용되는지 확인
            important_keywords = ["product", "goods", "price", "image", "detail", "description"]
            important_class_count = sum(1 for cls, _ in top_classes if any(kw in cls.lower() for kw in important_keywords))
            
            if important_class_count >= 5:
                analysis["score"] += 10
            elif important_class_count >= 3:
                analysis["score"] += 5
        
        # 점수 정규화 (0-100)
        analysis["score"] = min(100, max(0, analysis["score"]))
        
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
