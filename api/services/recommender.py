"""
매출 강화 아이디어 제안 서비스
메뉴얼 기반의 실전적인 매출 강화 아이디어를 생성합니다.
페이지 구조(div class) 정보를 활용하여 더 정확한 추천을 제공합니다.
"""
from typing import Dict, Any, List, Optional
import json
import os
import re


class SalesEnhancementRecommender:
    """매출 강화 추천 시스템"""
    
    def __init__(self):
        # 메뉴얼 기반 지식 (큐텐 대학 메뉴얼에서 추출)
        self.manual_knowledge = self._load_manual_knowledge()
    
    def _load_manual_knowledge(self) -> Dict[str, Any]:
        """메뉴얼 지식 로드"""
        # 실제로는 메뉴얼 파일을 읽어서 로드
        # 여기서는 하드코딩된 지식 사용
        return {
            "seo_tips": [
                "상품명에 인기 키워드 포함",
                "검색어 필드 활용",
                "카테고리 및 브랜드 등록"
            ],
            "advertising_types": [
                {
                    "name": "파워랭크업",
                    "description": "검색형 광고 (200엔부터)",
                    "min_budget": 200
                },
                {
                    "name": "스마트세일즈",
                    "description": "알고리즘 기반 자동 노출",
                    "min_budget": 500
                },
                {
                    "name": "플러스 전시",
                    "description": "전시형 광고",
                    "min_budget": 300
                }
            ],
            "promotion_tips": [
                "샵 쿠폰 설정",
                "상품 할인 전략",
                "샘플마켓 참가 (상품 수량 10개 이상)"
            ]
        }
    
    async def generate_recommendations(
        self,
        product_data: Dict[str, Any],
        analysis_result: Dict[str, Any],
        page_structure: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        매출 강화 아이디어 생성 (페이지 구조 정보 활용)
        
        Args:
            product_data: 상품 데이터
            analysis_result: 분석 결과
            page_structure: 페이지 구조 정보 (div class 정보 포함)
            
        Returns:
            추천 아이디어 리스트
        """
        recommendations = []
        
        # SEO 최적화 제안 (페이지 구조 기반)
        recommendations.extend(
            self._generate_seo_recommendations(product_data, analysis_result, page_structure)
        )
        
        # 광고 전략 제안 (페이지 구조 기반)
        recommendations.extend(
            self._generate_advertising_recommendations(analysis_result, page_structure)
        )
        
        # 프로모션 제안 (페이지 구조 기반)
        recommendations.extend(
            self._generate_promotion_recommendations(product_data, analysis_result, page_structure)
        )
        
        # 상품 페이지 개선 제안 (페이지 구조 기반)
        recommendations.extend(
            self._generate_page_improvement_recommendations(analysis_result, page_structure)
        )
        
        # 우선순위 정렬
        recommendations = sorted(
            recommendations,
            key=lambda x: {"high": 3, "medium": 2, "low": 1}[x["priority"]],
            reverse=True
        )
        
        return recommendations
    
    def _generate_seo_recommendations(
        self,
        product_data: Dict[str, Any],
        analysis_result: Dict[str, Any],
        page_structure: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """SEO 최적화 제안 생성 (페이지 구조 기반)"""
        recommendations = []
        seo_analysis = analysis_result.get("seo_analysis", {})
        
        # 페이지 구조에서 상품명 관련 요소 확인
        has_product_name_element = False
        if page_structure:
            semantic_structure = page_structure.get("semantic_structure", {})
            product_name_elements = semantic_structure.get("product_name_elements", [])
            if product_name_elements:
                has_product_name_element = True
        
        # 검색어 최적화 (페이지 구조 확인)
        if not seo_analysis.get("keywords_in_name"):
            # 페이지에 상품명 요소가 있는지 확인
            page_structure_note = ""
            if page_structure and not has_product_name_element:
                page_structure_note = " (페이지 구조 분석: 상품명 요소가 명확하지 않습니다)"
            
            recommendations.append({
                "id": f"rec_seo_001",
                "category": "SEO",
                "priority": "high",
                "title": "상품명에 인기 키워드 추가",
                "description": f"상품명에 검색 키워드를 포함하면 검색 노출이 30% 증가할 수 있습니다.{page_structure_note}",
                "action_items": [
                    f"상품명 수정: '[인기] {product_data.get('product_name', '')}'",
                    "검색어 필드에 '인기' 키워드 추가",
                    "페이지 구조 확인: 상품명 요소(.tt, .product-name 등) 확인"
                ],
                "expected_impact": "high",
                "difficulty": "easy",
                "estimated_time": "5분",
                "manual_reference": "판매 데이터 관리・분석하기 - 검색 키워드 분석",
                "page_structure_mapping": {
                    "related_classes": ["tt", "product-name", "goods_name", "product_name"],
                    "element_present": has_product_name_element
                }
            })
        
        # 카테고리/브랜드 등록 (페이지 구조 확인)
        if not seo_analysis.get("category_set"):
            has_category_element = False
            if page_structure:
                semantic_structure = page_structure.get("semantic_structure", {})
                # 카테고리 관련 요소 확인은 navigation 카테고리에서
                key_elements = page_structure.get("key_elements", {})
                navigation_elements = key_elements.get("navigation", [])
                if navigation_elements:
                    has_category_element = True
            
            page_structure_note = ""
            if page_structure and not has_category_element:
                page_structure_note = " (페이지 구조 분석: 카테고리 요소가 명확하지 않습니다)"
            
            recommendations.append({
                "id": f"rec_seo_002",
                "category": "SEO",
                "priority": "high",
                "title": "적절한 카테고리 선택",
                "description": f"올바른 카테고리 선택은 검색 노출과 고객 유입에 중요합니다.{page_structure_note}",
                "action_items": [
                    "JQSM에서 상품 카테고리 확인",
                    "더 구체적인 하위 카테고리 선택 고려",
                    "페이지 구조 확인: 카테고리 요소(breadcrumb, category 등) 확인"
                ],
                "expected_impact": "high",
                "difficulty": "easy",
                "estimated_time": "10분",
                "manual_reference": "판매 데이터 관리・분석하기 - SEO 대책",
                "page_structure_mapping": {
                    "related_classes": ["breadcrumb", "category", "nav"],
                    "element_present": has_category_element
                }
            })
        
        return recommendations
    
    def _generate_advertising_recommendations(
        self,
        analysis_result: Dict[str, Any],
        page_structure: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """광고 전략 제안 생성 (페이지 구조 기반)"""
        recommendations = []
        
        overall_score = analysis_result.get("overall_score", 0)
        
        # 페이지 구조에서 광고 관련 요소 확인
        has_ad_element = False
        if page_structure:
            key_elements = page_structure.get("key_elements", {})
            # 광고 관련 요소는 직접 확인 불가하지만, 상품 페이지 완성도로 추정
            semantic_structure = page_structure.get("semantic_structure", {})
            if semantic_structure.get("product_name_elements") and semantic_structure.get("price_elements"):
                has_ad_element = True
        
        # 점수가 낮으면 광고 추천
        if overall_score < 70:
            page_structure_note = ""
            if page_structure and not has_ad_element:
                page_structure_note = " (페이지 구조 분석: 상품 페이지 기본 요소가 부족합니다)"
            
            recommendations.append({
                "id": "rec_adv_001",
                "category": "광고",
                "priority": "high",
                "title": "파워랭크업 광고 시작",
                "description": f"검색 노출을 높이기 위해 파워랭크업 광고를 시작하세요. 200엔부터 시작 가능합니다.{page_structure_note}",
                "action_items": [
                    "JQSM에서 파워랭크업 광고 설정",
                    "일 예산 1,000엔 권장",
                    "핵심 키워드 3-5개 선택",
                    "페이지 구조 확인: 상품명(.tt), 가격(.prc) 요소 확인"
                ],
                "expected_impact": "high",
                "difficulty": "medium",
                "estimated_time": "30분",
                "manual_reference": "광고・프로모션 활용하기 - 파워랭크업",
                "page_structure_mapping": {
                    "related_classes": ["tt", "prc", "price", "product-name"],
                    "element_present": has_ad_element
                }
            })
        
        # 이미지 점수가 낮으면 스마트세일즈 추천
        image_score = analysis_result.get("image_analysis", {}).get("score", 0)
        if image_score < 60:
            has_image_element = False
            if page_structure:
                semantic_structure = page_structure.get("semantic_structure", {})
                image_elements = semantic_structure.get("image_elements", [])
                if image_elements:
                    has_image_element = True
            
            page_structure_note = ""
            if page_structure and not has_image_element:
                page_structure_note = " (페이지 구조 분석: 이미지 요소가 부족합니다)"
            
            recommendations.append({
                "id": "rec_adv_002",
                "category": "광고",
                "priority": "medium",
                "title": "스마트세일즈 광고 활용",
                "description": f"이미지 품질을 개선한 후 스마트세일즈 광고를 활용하면 효과적입니다.{page_structure_note}",
                "action_items": [
                    "먼저 상품 이미지 개선",
                    "스마트세일즈 광고 설정",
                    "일 예산 2,000엔 권장",
                    "페이지 구조 확인: 이미지 요소(.thmb, .thumbnail 등) 확인"
                ],
                "expected_impact": "medium",
                "difficulty": "medium",
                "estimated_time": "1시간",
                "manual_reference": "광고・프로모션 활용하기 - 스마트세일즈",
                "page_structure_mapping": {
                    "related_classes": ["thmb", "thumbnail", "image", "img"],
                    "element_present": has_image_element
                }
            })
        
        return recommendations
    
    def _generate_promotion_recommendations(
        self,
        product_data: Dict[str, Any],
        analysis_result: Dict[str, Any],
        page_structure: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """프로모션 제안 생성 (페이지 구조 기반)"""
        recommendations = []
        
        # 페이지 구조에서 쿠폰 관련 요소 확인
        has_coupon_element = False
        coupon_classes = []
        if page_structure:
            semantic_structure = page_structure.get("semantic_structure", {})
            coupon_elements = semantic_structure.get("coupon_elements", [])
            if coupon_elements:
                has_coupon_element = True
                coupon_classes = [elem.get("class") for elem in coupon_elements[:5]]
        
        # 샘플마켓 참가 제안 (상품 수량 확인 필요 - 여기서는 가정)
        recommendations.append({
            "id": "rec_promo_001",
            "category": "프로모션",
            "priority": "medium",
            "title": "샘플마켓 참가 검토",
            "description": "상품 수량이 10개 이상인 경우 샘플마켓 참가를 통해 리뷰를 확보할 수 있습니다.",
            "action_items": [
                "상품 수량 확인 (10개 이상 필요)",
                "샘플마켓 신청서 작성",
                "참가 상품 및 일정 협의"
            ],
            "expected_impact": "high",
            "difficulty": "medium",
            "estimated_time": "2시간",
            "manual_reference": "매출 증대시키기 - 샘플마켓 참가 가이드",
            "page_structure_mapping": {
                "related_classes": ["item", "product", "goods"],
                "element_present": True  # 상품 목록은 항상 존재
            }
        })
        
        # 할인 전략 (페이지 구조에서 쿠폰 요소 확인)
        price_analysis = analysis_result.get("price_analysis", {})
        discount_rate = price_analysis.get("discount_rate", 0)
        
        if discount_rate == 0:
            page_structure_note = ""
            if page_structure and not has_coupon_element:
                page_structure_note = " (페이지 구조 분석: 쿠폰/할인 요소가 명확하지 않습니다)"
            
            recommendations.append({
                "id": "rec_promo_002",
                "category": "프로모션",
                "priority": "low",
                "title": "할인 프로모션 고려",
                "description": f"적절한 할인율(10-30%)을 설정하면 구매 전환율이 향상될 수 있습니다.{page_structure_note}",
                "action_items": [
                    "할인율 10-20% 설정 검토",
                    "할인 기간 설정",
                    "프로모션 페이지에 표시",
                    f"페이지 구조 확인: 쿠폰 요소({', '.join(coupon_classes) if coupon_classes else 'coupon, discount 등'}) 확인"
                ],
                "expected_impact": "medium",
                "difficulty": "easy",
                "estimated_time": "15분",
                "manual_reference": "광고・프로모션 활용하기 - 상품 할인",
                "page_structure_mapping": {
                    "related_classes": coupon_classes if coupon_classes else ["coupon", "discount", "割引", "クーポン"],
                    "element_present": has_coupon_element
                }
            })
        
        return recommendations
    
    def _generate_page_improvement_recommendations(
        self,
        analysis_result: Dict[str, Any],
        page_structure: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """상품 페이지 개선 제안 생성 (페이지 구조 기반)"""
        recommendations = []
        
        # 이미지 개선 (페이지 구조에서 이미지 요소 확인)
        image_analysis = analysis_result.get("image_analysis", {})
        image_count = image_analysis.get("image_count", 0)
        
        has_image_element = False
        image_classes = []
        if page_structure:
            semantic_structure = page_structure.get("semantic_structure", {})
            image_elements = semantic_structure.get("image_elements", [])
            if image_elements:
                has_image_element = True
                image_classes = [elem.get("class") for elem in image_elements[:5]]
        
        if image_count < 5:
            page_structure_note = ""
            if page_structure and not has_image_element:
                page_structure_note = " (페이지 구조 분석: 이미지 요소가 명확하지 않습니다)"
            
            recommendations.append({
                "id": "rec_page_001",
                "category": "상품 페이지",
                "priority": "high",
                "title": "상세 이미지 추가",
                "description": f"현재 {image_count}개의 이미지만 있습니다. 최소 5개 이상 권장합니다.{page_structure_note}",
                "action_items": [
                    "다각도 상품 사진 추가",
                    "사용 예시 이미지 추가",
                    "상세 설명 이미지 추가",
                    f"페이지 구조 확인: 이미지 요소({', '.join(image_classes) if image_classes else '.thmb, .thumbnail 등'}) 확인"
                ],
                "expected_impact": "high",
                "difficulty": "medium",
                "estimated_time": "1시간",
                "manual_reference": "판매 준비하기 - MOVE 상품 등록",
                "page_structure_mapping": {
                    "related_classes": image_classes if image_classes else ["thmb", "thumbnail", "image", "img"],
                    "element_present": has_image_element,
                    "current_count": image_count
                }
            })
        
        # 설명 개선 (페이지 구조에서 설명 요소 확인)
        description_analysis = analysis_result.get("description_analysis", {})
        description_length = description_analysis.get("description_length", 0)
        
        has_description_element = False
        description_classes = []
        if page_structure:
            semantic_structure = page_structure.get("semantic_structure", {})
            description_elements = semantic_structure.get("description_elements", [])
            if description_elements:
                has_description_element = True
                description_classes = [elem.get("class") for elem in description_elements[:5]]
        
        if description_length < 500:
            page_structure_note = ""
            if page_structure and not has_description_element:
                page_structure_note = " (페이지 구조 분석: 설명 요소가 명확하지 않습니다)"
            
            recommendations.append({
                "id": "rec_page_002",
                "category": "상품 페이지",
                "priority": "medium",
                "title": "상품 설명 보완",
                "description": f"현재 설명 길이가 {description_length}자입니다. 500자 이상 권장합니다.{page_structure_note}",
                "action_items": [
                    "상품 특징 상세 설명 추가",
                    "사용 방법 및 주의사항 추가",
                    "구조화된 리스트 형식 활용",
                    f"페이지 구조 확인: 설명 요소({', '.join(description_classes) if description_classes else '.detail, .description 등'}) 확인"
                ],
                "expected_impact": "medium",
                "difficulty": "easy",
                "estimated_time": "30분",
                "manual_reference": "판매 준비하기 - 잘 팔리는 상품 페이지 만들기",
                "page_structure_mapping": {
                    "related_classes": description_classes if description_classes else ["detail", "description", "content"],
                    "element_present": has_description_element,
                    "current_length": description_length
                }
            })
        
        return recommendations
    
    async def generate_shop_recommendations(
        self,
        shop_data: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Shop 매출 강화 아이디어 생성
        
        Args:
            shop_data: Shop 데이터
            analysis_result: Shop 분석 결과
            
        Returns:
            추천 아이디어 리스트
        """
        recommendations = []
        
        # Shop 레벨 향상 제안
        level_analysis = analysis_result.get("level_analysis", {})
        current_level = level_analysis.get("current_level", "normal")
        
        if current_level != "power":
            target_level = level_analysis.get("target_level", "excellent")
            recommendations.append({
                "id": "rec_shop_001",
                "category": "Shop 운영",
                "priority": "high",
                "title": f"{target_level.capitalize()} 셀러 레벨 달성",
                "description": f"현재 {current_level} 셀러입니다. {target_level} 셀러가 되면 정산 리드타임이 단축됩니다.",
                "action_items": level_analysis.get("requirements", []),
                "expected_impact": "high",
                "difficulty": "medium",
                "estimated_time": "지속적",
                "manual_reference": "입점 검토하기 - Shop 레벨"
            })
        
        # 상품 다양성 제안
        product_analysis = analysis_result.get("product_analysis", {})
        if product_analysis.get("total_products", 0) < 20:
            recommendations.append({
                "id": "rec_shop_002",
                "category": "상품 기획",
                "priority": "medium",
                "title": "상품 라인업 확대",
                "description": f"현재 {product_analysis.get('total_products', 0)}개의 상품만 있습니다. 최소 20개 이상 권장합니다.",
                "action_items": [
                    "신규 상품 등록",
                    "시즌 상품 추가",
                    "세트 상품 기획"
                ],
                "expected_impact": "medium",
                "difficulty": "medium",
                "estimated_time": "1-2주",
                "manual_reference": "매출 증대시키기 - 상품 기획"
            })
        
        # 카테고리 집중 제안
        category_analysis = analysis_result.get("category_analysis", {})
        if category_analysis.get("category_count", 0) > 5:
            recommendations.append({
                "id": "rec_shop_003",
                "category": "카테고리 전략",
                "priority": "low",
                "title": "카테고리 집중 전략",
                "description": "너무 많은 카테고리에 분산되어 있습니다. 주요 카테고리에 집중하는 것이 효과적입니다.",
                "action_items": [
                    "주요 카테고리 2-3개 선정",
                    "해당 카테고리 상품 확대",
                    "카테고리별 브랜딩 강화"
                ],
                "expected_impact": "medium",
                "difficulty": "medium",
                "estimated_time": "2-4주",
                "manual_reference": "판매 데이터 관리・분석하기 - 카테고리 분석"
            })
        
        return recommendations
