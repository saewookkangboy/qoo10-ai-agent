"""
메뉴얼 기반 체크리스트 평가 서비스
큐텐 대학 메뉴얼을 기반으로 체크리스트를 평가하고 완성도를 계산합니다.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime


class ChecklistEvaluator:
    """체크리스트 평가기"""
    
    def __init__(self):
        # 메뉴얼 기반 체크리스트 항목 정의
        self.checklist_definitions = self._load_checklist_definitions()
    
    def _load_checklist_definitions(self) -> Dict[str, List[Dict[str, Any]]]:
        """체크리스트 정의 로드"""
        return {
            "판매 준비": [
                {
                    "id": "item_001",
                    "title": "상품 등록 완료",
                    "description": "상품명, 설명, 이미지 등 기본 정보 입력 완료",
                    "auto_checkable": True,
                    "check_function": "check_product_registered"
                },
                {
                    "id": "item_002",
                    "title": "검색어 설정 완료",
                    "description": "검색어 필드에 키워드 입력 완료",
                    "auto_checkable": True,
                    "check_function": "check_search_keywords"
                },
                {
                    "id": "item_003",
                    "title": "카테고리 및 브랜드 등록 완료",
                    "description": "적절한 카테고리 선택 및 브랜드 등록 완료",
                    "auto_checkable": True,
                    "check_function": "check_category_brand"
                },
                {
                    "id": "item_004",
                    "title": "가격 설정 완료",
                    "description": "정가, 판매가, 할인율 설정 완료",
                    "auto_checkable": True,
                    "check_function": "check_price_set"
                },
                {
                    "id": "item_005",
                    "title": "배송 정보 설정 완료",
                    "description": "배송 방법, 배송비, 배송 기간 설정 완료",
                    "auto_checkable": True,
                    "check_function": "check_shipping_info"
                },
                {
                    "id": "item_006",
                    "title": "재고 관리 설정 완료",
                    "description": "재고 수량 및 재고 관리 방법 설정 완료",
                    "auto_checkable": False,  # 수동 확인 필요
                    "check_function": None
                }
            ],
            "매출 증대": [
                {
                    "id": "item_007",
                    "title": "상품 페이지 최적화",
                    "description": "이미지 품질, 설명 완성도, 레이아웃 최적화",
                    "auto_checkable": True,
                    "check_function": "check_page_optimization"
                },
                {
                    "id": "item_008",
                    "title": "검색 키워드 최적화",
                    "description": "상품명, 검색어에 인기 키워드 포함",
                    "auto_checkable": True,
                    "check_function": "check_keyword_optimization"
                },
                {
                    "id": "item_009",
                    "title": "가격 전략 수립",
                    "description": "경쟁사 대비 적정 가격 설정, 가격 심리학 활용",
                    "auto_checkable": True,
                    "check_function": "check_price_strategy"
                },
                {
                    "id": "item_010",
                    "title": "고객 리뷰 관리",
                    "description": "리뷰 모니터링, 부정 리뷰 대응, 리뷰 활용",
                    "auto_checkable": False,
                    "check_function": None
                },
                {
                    "id": "item_011",
                    "title": "프로모션 활용",
                    "description": "샵 쿠폰, 상품 할인, 이벤트 참가",
                    "auto_checkable": True,
                    "check_function": "check_promotion"
                },
                {
                    "id": "item_012",
                    "title": "광고 전략 수립",
                    "description": "파워랭크업, 스마트세일즈, 플러스 전시 등 광고 활용",
                    "auto_checkable": False,  # 실제 광고 설정 여부는 확인 불가
                    "check_function": None
                },
                {
                    "id": "item_013",
                    "title": "배송 옵션 다양화",
                    "description": "다양한 배송 방법 제공, 배송비 최적화",
                    "auto_checkable": False,
                    "check_function": None
                },
                {
                    "id": "item_014",
                    "title": "고객 서비스 개선",
                    "description": "문의 대응 속도, 고객 만족도 향상",
                    "auto_checkable": False,
                    "check_function": None
                },
                {
                    "id": "item_015",
                    "title": "데이터 분석 기반 의사결정",
                    "description": "Qoo10 Analytics 활용, 데이터 기반 개선",
                    "auto_checkable": False,
                    "check_function": None
                },
                {
                    "id": "item_016",
                    "title": "지속적인 개선 및 테스트",
                    "description": "A/B 테스트, 지속적인 최적화",
                    "auto_checkable": False,
                    "check_function": None
                }
            ],
            "광고/프로모션": [
                {
                    "id": "item_017",
                    "title": "파워랭크업 광고 활용",
                    "description": "검색형 광고 설정 (200엔부터)",
                    "auto_checkable": False,
                    "check_function": None
                },
                {
                    "id": "item_018",
                    "title": "스마트세일즈 광고 활용",
                    "description": "알고리즘 기반 자동 노출 광고 설정",
                    "auto_checkable": False,
                    "check_function": None
                },
                {
                    "id": "item_019",
                    "title": "플러스 전시 광고 활용",
                    "description": "전시형 광고 설정",
                    "auto_checkable": False,
                    "check_function": None
                },
                {
                    "id": "item_020",
                    "title": "키워드 플러스 광고 활용",
                    "description": "특정 키워드 검색 시 노출 광고 설정",
                    "auto_checkable": False,
                    "check_function": None
                },
                {
                    "id": "item_021",
                    "title": "샵 쿠폰 설정",
                    "description": "할인 쿠폰 생성 및 설정",
                    "auto_checkable": True,
                    "check_function": "check_shop_coupon"
                },
                {
                    "id": "item_022",
                    "title": "상품 할인 설정",
                    "description": "상품별 할인율 설정",
                    "auto_checkable": True,
                    "check_function": "check_product_discount"
                },
                {
                    "id": "item_023",
                    "title": "샘플마켓 참가 (가능한 경우)",
                    "description": "상품 수량 10개 이상인 경우 샘플마켓 참가 신청",
                    "auto_checkable": True,
                    "check_function": "check_sample_market"
                },
                {
                    "id": "item_024",
                    "title": "메가할인/메가포 대비 준비",
                    "description": "이벤트 기간 대비 상품 준비, 가격 전략, 광고 예산 배분",
                    "auto_checkable": False,
                    "check_function": None
                }
            ]
        }
    
    async def evaluate_checklist(
        self,
        product_data: Optional[Dict[str, Any]] = None,
        shop_data: Optional[Dict[str, Any]] = None,
        analysis_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        체크리스트 평가
        
        Args:
            product_data: 상품 데이터 (선택사항)
            shop_data: Shop 데이터 (선택사항)
            analysis_result: 분석 결과 (선택사항)
            
        Returns:
            체크리스트 평가 결과
        """
        evaluation_result = {
            "overall_completion": 0,
            "checklists": []
        }
        
        total_items = 0
        completed_items = 0
        
        # 각 카테고리별 체크리스트 평가
        for category, items in self.checklist_definitions.items():
            checklist_result = {
                "category": category,
                "completion_rate": 0,
                "items": []
            }
            
            category_completed = 0
            category_total = len(items)
            
            for item_def in items:
                item_result = {
                    "id": item_def["id"],
                    "title": item_def["title"],
                    "description": item_def["description"],
                    "status": "pending",
                    "auto_checked": False,
                    "recommendation": None
                }
                
                # 자동 체크 가능한 항목 평가
                if item_def["auto_checkable"] and item_def["check_function"]:
                    check_result = await self._auto_check_item(
                        item_def["check_function"],
                        product_data,
                        shop_data,
                        analysis_result
                    )
                    item_result["status"] = "completed" if check_result["passed"] else "pending"
                    item_result["auto_checked"] = True
                    item_result["recommendation"] = check_result.get("recommendation")
                    
                    if check_result["passed"]:
                        category_completed += 1
                        completed_items += 1
                else:
                    # 수동 확인 필요 항목
                    item_result["status"] = "pending"
                    item_result["auto_checked"] = False
                
                checklist_result["items"].append(item_result)
                total_items += 1
            
            # 카테고리별 완성도 계산
            if category_total > 0:
                checklist_result["completion_rate"] = int((category_completed / category_total) * 100)
            
            evaluation_result["checklists"].append(checklist_result)
        
        # 전체 완성도 계산
        if total_items > 0:
            evaluation_result["overall_completion"] = int((completed_items / total_items) * 100)
        
        return evaluation_result
    
    async def _auto_check_item(
        self,
        check_function: str,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """자동 체크 항목 평가"""
        
        if not product_data and not shop_data:
            return {"passed": False, "recommendation": "데이터가 없어 평가할 수 없습니다"}
        
        # 체크 함수 매핑
        check_functions = {
            "check_product_registered": self._check_product_registered,
            "check_search_keywords": self._check_search_keywords,
            "check_category_brand": self._check_category_brand,
            "check_price_set": self._check_price_set,
            "check_shipping_info": self._check_shipping_info,
            "check_page_optimization": self._check_page_optimization,
            "check_keyword_optimization": self._check_keyword_optimization,
            "check_price_strategy": self._check_price_strategy,
            "check_promotion": self._check_promotion,
            "check_shop_coupon": self._check_shop_coupon,
            "check_product_discount": self._check_product_discount,
            "check_sample_market": self._check_sample_market
        }
        
        func = check_functions.get(check_function)
        if func:
            return await func(product_data, shop_data, analysis_result)
        
        return {"passed": False, "recommendation": "체크 함수를 찾을 수 없습니다"}
    
    async def _check_product_registered(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """상품 등록 완료 체크 - 실제 추출된 데이터 구조에 맞게 개선"""
        if not product_data:
            return {"passed": False, "recommendation": "상품 데이터가 없습니다"}
        
        product_name = product_data.get("product_name", "")
        description = product_data.get("description", "")
        images = product_data.get("images", {})
        thumbnail = images.get("thumbnail")
        detail_images = images.get("detail_images", [])
        
        # 상품명 확인 (빈 문자열이나 "상품명 없음"이 아닌지 확인)
        has_name = bool(product_name) and product_name != "상품명 없음" and len(product_name.strip()) > 0
        
        # 상품 설명 확인 (최소 길이 확인)
        has_description = bool(description) and len(description.strip()) > 50
        
        # 이미지 확인 (썸네일 또는 상세 이미지)
        has_images = bool(thumbnail) or len(detail_images) > 0
        
        if has_name and has_description and has_images:
            return {
                "passed": True,
                "recommendation": f"상품 등록 완료 (상품명: {product_name[:30]}..., 이미지: {len(detail_images) + (1 if thumbnail else 0)}개)"
            }
        else:
            missing = []
            if not has_name:
                missing.append("상품명")
            if not has_description:
                missing.append("상품 설명 (최소 50자 이상)")
            if not has_images:
                missing.append("이미지 (썸네일 또는 상세 이미지)")
            return {
                "passed": False,
                "recommendation": f"{', '.join(missing)}을(를) 등록하세요"
            }
    
    async def _check_search_keywords(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """검색어 설정 체크"""
        if not product_data:
            return {"passed": False, "recommendation": "상품 데이터가 없습니다"}
        
        keywords = product_data.get("search_keywords", [])
        if keywords and len(keywords) > 0:
            return {"passed": True}
        else:
            return {
                "passed": False,
                "recommendation": "검색어 필드에 키워드를 추가하세요"
            }
    
    async def _check_category_brand(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """카테고리 및 브랜드 등록 체크"""
        if not product_data:
            return {"passed": False, "recommendation": "상품 데이터가 없습니다"}
        
        has_category = bool(product_data.get("category"))
        has_brand = bool(product_data.get("brand"))
        
        if has_category and has_brand:
            return {"passed": True}
        else:
            missing = []
            if not has_category:
                missing.append("카테고리")
            if not has_brand:
                missing.append("브랜드")
            return {
                "passed": False,
                "recommendation": f"{', '.join(missing)}을(를) 등록하세요"
            }
    
    async def _check_price_set(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """가격 설정 체크 - 실제 추출된 데이터 구조에 맞게 개선"""
        if not product_data:
            return {"passed": False, "recommendation": "상품 데이터가 없습니다"}
        
        price = product_data.get("price", {})
        sale_price = price.get("sale_price")
        original_price = price.get("original_price")
        discount_rate = price.get("discount_rate", 0)
        
        # 판매가가 설정되어 있는지 확인
        if not sale_price or sale_price <= 0:
            return {
                "passed": False,
                "recommendation": "판매가를 설정하세요"
            }
        
        # 정가와 할인율이 설정되어 있는지 확인 (선택사항이지만 권장)
        if original_price and discount_rate > 0:
            return {
                "passed": True,
                "recommendation": f"가격 설정 완료 (판매가: {sale_price}円, 할인율: {discount_rate}%)"
            }
        elif sale_price:
            return {
                "passed": True,
                "recommendation": f"판매가 설정 완료 ({sale_price}円). 할인율 설정을 고려하세요"
            }
        
        return {"passed": True}
    
    async def _check_shipping_info(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """배송 정보 체크 - 실제 추출된 데이터 구조에 맞게 개선"""
        if not product_data:
            return {"passed": False, "recommendation": "상품 데이터가 없습니다"}
        
        shipping_info = product_data.get("shipping_info", {})
        shipping_fee = shipping_info.get("shipping_fee")
        free_shipping = shipping_info.get("free_shipping", False)
        
        # 배송비 정보가 설정되어 있는지 확인 (무료배송 포함)
        if free_shipping or (shipping_fee is not None and shipping_fee >= 0):
            if free_shipping:
                return {
                    "passed": True,
                    "recommendation": "무료배송이 설정되어 있습니다"
                }
            else:
                return {
                    "passed": True,
                    "recommendation": f"배송비 정보 설정 완료 ({shipping_fee}円)"
                }
        else:
            return {
                "passed": False,
                "recommendation": "배송비 정보를 설정하세요 (무료배송 포함)"
            }
    
    async def _check_page_optimization(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """상품 페이지 최적화 체크"""
        if not analysis_result:
            return {"passed": False, "recommendation": "분석 결과가 없습니다"}
        
        overall_score = analysis_result.get("overall_score", 0)
        
        if overall_score >= 70:
            return {"passed": True}
        else:
            return {
                "passed": False,
                "recommendation": f"현재 점수 {overall_score}점. 70점 이상을 목표로 개선하세요"
            }
    
    async def _check_keyword_optimization(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """검색 키워드 최적화 체크"""
        if not analysis_result:
            return {"passed": False, "recommendation": "분석 결과가 없습니다"}
        
        seo_analysis = analysis_result.get("seo_analysis", {})
        keywords_in_name = seo_analysis.get("keywords_in_name", False)
        
        if keywords_in_name:
            return {"passed": True}
        else:
            return {
                "passed": False,
                "recommendation": "상품명에 인기 키워드를 포함하세요"
            }
    
    async def _check_price_strategy(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """가격 전략 체크"""
        if not analysis_result:
            return {"passed": False, "recommendation": "분석 결과가 없습니다"}
        
        price_analysis = analysis_result.get("price_analysis", {})
        score = price_analysis.get("score", 0)
        
        if score >= 60:
            return {"passed": True}
        else:
            return {
                "passed": False,
                "recommendation": "가격 전략을 재검토하세요"
            }
    
    async def _check_promotion(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """프로모션 활용 체크 - 실제 추출된 데이터 구조에 맞게 개선"""
        promotion_items = []
        
        # Shop 쿠폰 확인
        if shop_data:
            coupons = shop_data.get("coupons", [])
            if coupons and len(coupons) > 0:
                promotion_items.append(f"샵 쿠폰 {len(coupons)}개")
        
        # 상품 할인 확인
        if product_data:
            price = product_data.get("price", {})
            discount_rate = price.get("discount_rate", 0)
            coupon_discount = price.get("coupon_discount")
            
            if discount_rate > 0:
                promotion_items.append(f"상품 할인 {discount_rate}%")
            
            if coupon_discount:
                promotion_items.append(f"쿠폰 할인 {coupon_discount}円")
        
        if promotion_items:
            return {
                "passed": True,
                "recommendation": f"프로모션 설정 완료: {', '.join(promotion_items)}"
            }
        
        return {
            "passed": False,
            "recommendation": "샵 쿠폰 또는 상품 할인을 설정하세요"
        }
    
    async def _check_shop_coupon(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """샵 쿠폰 체크"""
        if shop_data:
            coupons = shop_data.get("coupons", [])
            if coupons and len(coupons) > 0:
                return {"passed": True}
        
        return {
            "passed": False,
            "recommendation": "샵 쿠폰을 생성하세요"
        }
    
    async def _check_product_discount(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """상품 할인 체크"""
        if product_data:
            price = product_data.get("price", {})
            discount_rate = price.get("discount_rate", 0)
            if discount_rate > 0:
                return {"passed": True}
        
        return {
            "passed": False,
            "recommendation": "상품 할인율을 설정하세요"
        }
    
    async def _check_sample_market(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """샘플마켓 참가 가능 여부 체크"""
        # 상품 수량 정보는 크롤링으로 확인 불가
        # 여기서는 기본적인 체크만 수행
        if product_data:
            # 상품이 등록되어 있으면 참가 가능성 있음
            return {
                "passed": True,
                "recommendation": "상품 수량이 10개 이상인 경우 샘플마켓 참가 신청 가능"
            }
        
        return {
            "passed": False,
            "recommendation": "상품을 등록한 후 샘플마켓 참가를 검토하세요"
        }
