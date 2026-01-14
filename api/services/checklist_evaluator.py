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
                },
                {
                    "id": "item_006b",
                    "title": "Qポイント 정보 설정",
                    "description": "Qポイント獲得方法이 명시되어 있어 고객에게 혜택을 제공",
                    "auto_checkable": True,
                    "check_function": "check_qpoint_info"
                },
                {
                    "id": "item_006c",
                    "title": "반품 정책 명시",
                    "description": "返品無料 서비스 등 반품 정책이 명확히 표시되어 있음",
                    "auto_checkable": True,
                    "check_function": "check_return_policy"
                },
                {
                    "id": "item_006d",
                    "title": "MOVE 상품 등록 (해당 시)",
                    "description": "MOVE 상품으로 등록되어 있는 경우 추가 노출 기회 확보",
                    "auto_checkable": True,
                    "check_function": "check_move_product"
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
                    "id": "item_011b",
                    "title": "쿠폰 상세 정보 제공",
                    "description": "쿠폰 할인 정보가 명확히 표시되어 고객이 쉽게 확인 가능",
                    "auto_checkable": True,
                    "check_function": "check_coupon_detail"
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
            "Shop 운영": [
                {
                    "id": "item_016b",
                    "title": "Shop 레벨 최적화",
                    "description": "POWER 셀러 또는 우수 셀러 등급 유지로 정산 리드타임 단축",
                    "auto_checkable": True,
                    "check_function": "check_shop_level"
                },
                {
                    "id": "item_016c",
                    "title": "Shop 팔로워 수 관리",
                    "description": "Shop 팔로워 수가 충분하여 고객 기반 확보",
                    "auto_checkable": True,
                    "check_function": "check_shop_followers"
                },
                {
                    "id": "item_016d",
                    "title": "Shop 상품 다양성",
                    "description": "다양한 상품을 등록하여 고객 선택권 제공",
                    "auto_checkable": True,
                    "check_function": "check_shop_product_diversity"
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
        analysis_result: Optional[Dict[str, Any]] = None,
        page_structure: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        체크리스트 평가 (정확도 향상 및 데이터 일관성 검증 포함, 페이지 구조 기반)
        
        Args:
            product_data: 상품 데이터 (선택사항)
            shop_data: Shop 데이터 (선택사항)
            analysis_result: 분석 결과 (선택사항)
            page_structure: 페이지 구조 정보 (div class 정보 포함, 선택사항)
            
        Returns:
            체크리스트 평가 결과
        """
        # 데이터 검증 및 정제
        if product_data:
            product_data = self._validate_product_data(product_data)
        if shop_data:
            shop_data = self._validate_shop_data(shop_data)
        
        # 페이지 구조에서 체크리스트 항목과 관련된 div class 매핑
        checklist_class_mapping = self._map_checklist_to_page_structure(page_structure) if page_structure else {}
        
        evaluation_result = {
            "overall_completion": 0,
            "checklists": [],
            "data_quality": {
                "product_data_complete": self._check_data_completeness(product_data),
                "shop_data_complete": self._check_data_completeness(shop_data),
                "warnings": []
            }
        }
        
        # 데이터 일관성 검증
        consistency_issues = self._check_data_consistency(product_data, shop_data, analysis_result)
        if consistency_issues:
            evaluation_result["data_quality"]["warnings"].extend(consistency_issues)
        
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
                    "recommendation": None,
                    "confidence": "high"  # 신뢰도 추가
                }
                
                # 자동 체크 가능한 항목 평가 (페이지 구조 정보 활용)
                if item_def["auto_checkable"] and item_def["check_function"]:
                    check_result = await self._auto_check_item(
                        item_def["check_function"],
                        product_data,
                        shop_data,
                        analysis_result,
                        page_structure
                    )
                    item_result["status"] = "completed" if check_result["passed"] else "pending"
                    item_result["auto_checked"] = True
                    item_result["recommendation"] = check_result.get("recommendation")
                    
                    # 페이지 구조 매핑 정보 추가
                    if page_structure:
                        item_mapping = checklist_class_mapping.get(item_def["id"], {})
                        if item_mapping:
                            item_result["page_structure_mapping"] = {
                                "related_classes": item_mapping.get("classes", []),
                                "element_present": item_mapping.get("present", False),
                                "class_frequency": item_mapping.get("frequency", {})
                            }
                    
                    # 신뢰도 평가 (데이터 품질 및 페이지 구조에 따라)
                    if not product_data and not shop_data:
                        item_result["confidence"] = "low"
                    elif page_structure and not checklist_class_mapping.get(item_def["id"], {}).get("present", True):
                        item_result["confidence"] = "medium"  # 페이지 구조에서 요소를 찾지 못함
                    elif self._has_minimal_data(product_data, shop_data, item_def["check_function"]):
                        item_result["confidence"] = "medium"
                    
                    if check_result["passed"]:
                        category_completed += 1
                        completed_items += 1
                else:
                    # 수동 확인 필요 항목
                    item_result["status"] = "pending"
                    item_result["auto_checked"] = False
                    item_result["confidence"] = "unknown"  # 수동 확인 필요
                
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
    
    def _check_data_completeness(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """데이터 완성도 검사"""
        if not data:
            return {"complete": False, "missing_fields": [], "completeness_rate": 0}
        
        required_fields = {
            "product": ["product_name", "price", "description", "images"],
            "shop": ["shop_name", "shop_id"]
        }
        
        data_type = "product" if "product_name" in data else "shop"
        required = required_fields.get(data_type, [])
        
        missing = []
        for field in required:
            if field not in data or not data[field]:
                missing.append(field)
        
        completeness_rate = int(((len(required) - len(missing)) / len(required)) * 100) if required else 100
        
        return {
            "complete": len(missing) == 0,
            "missing_fields": missing,
            "completeness_rate": completeness_rate
        }
    
    def _check_data_consistency(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> List[str]:
        """데이터 일관성 검증"""
        issues = []
        
        if product_data:
            # 가격 일관성 검증
            price = product_data.get("price", {})
            if isinstance(price, dict):
                sale_price = price.get("sale_price")
                original_price = price.get("original_price")
                discount_rate = price.get("discount_rate", 0)
                
                if sale_price and original_price:
                    if original_price <= sale_price:
                        issues.append("정가가 판매가보다 낮거나 같습니다. 가격 정보를 확인하세요.")
                    else:
                        calculated_discount = int(((original_price - sale_price) / original_price) * 100)
                        if discount_rate > 0 and abs(calculated_discount - discount_rate) > 5:
                            issues.append(f"할인율 불일치: 설정된 할인율({discount_rate}%)과 계산된 할인율({calculated_discount}%)이 다릅니다.")
            
            # 이미지 일관성 검증
            images = product_data.get("images", {})
            if isinstance(images, dict):
                thumbnail = images.get("thumbnail")
                detail_images = images.get("detail_images", [])
                if not thumbnail and not detail_images:
                    issues.append("이미지 정보가 없습니다.")
        
        if shop_data:
            # Shop 데이터 일관성 검증
            shop_id = shop_data.get("shop_id")
            shop_name = shop_data.get("shop_name")
            if not shop_id and not shop_name:
                issues.append("Shop 정보가 부족합니다.")
        
        # 분석 결과와 크롤러 데이터 간 일관성 검증
        if analysis_result and product_data:
            analysis_score = analysis_result.get("overall_score", 0)
            # 점수가 너무 낮으면 데이터 추출에 문제가 있을 수 있음
            if analysis_score < 20:
                issues.append("분석 점수가 매우 낮습니다. 데이터 추출을 확인하세요.")
        
        return issues
    
    def _has_minimal_data(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        check_function: str
    ) -> bool:
        """체크 함수에 필요한 최소 데이터가 있는지 확인"""
        # 특정 체크 함수에 필요한 데이터 확인
        shop_checks = ["check_shop_level", "check_shop_followers", "check_shop_product_diversity"]
        if check_function in shop_checks:
            return bool(shop_data)
        
        product_checks = [
            "check_product_registered", "check_price_set", "check_shipping_info",
            "check_qpoint_info", "check_return_policy", "check_move_product", "check_coupon_detail"
        ]
        if check_function in product_checks:
            return bool(product_data)
        
        return bool(product_data or shop_data)
    
    async def _auto_check_item(
        self,
        check_function: str,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]],
        page_structure: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """자동 체크 항목 평가 (정확도 향상 및 오류 처리 강화, 페이지 구조 기반)"""
        
        # 데이터 검증
        if not product_data and not shop_data:
            return {"passed": False, "recommendation": "데이터가 없어 평가할 수 없습니다"}
        
        # 데이터 유효성 검증
        if product_data:
            product_data = self._validate_product_data(product_data)
        if shop_data:
            shop_data = self._validate_shop_data(shop_data)
        
        # 페이지 구조 정보를 product_data에 추가 (체크 함수에서 활용 가능하도록)
        if page_structure and product_data:
            product_data["_page_structure"] = page_structure
        if page_structure and shop_data:
            shop_data["_page_structure"] = page_structure
        
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
            "check_sample_market": self._check_sample_market,
            "check_qpoint_info": self._check_qpoint_info,
            "check_return_policy": self._check_return_policy,
            "check_move_product": self._check_move_product,
            "check_coupon_detail": self._check_coupon_detail,
            "check_shop_level": self._check_shop_level,
            "check_shop_followers": self._check_shop_followers,
            "check_shop_product_diversity": self._check_shop_product_diversity
        }
        
        func = check_functions.get(check_function)
        if func:
            try:
                result = await func(product_data, shop_data, analysis_result)
                # 결과 검증
                if not isinstance(result, dict):
                    return {"passed": False, "recommendation": "체크 함수가 올바른 형식의 결과를 반환하지 않았습니다"}
                if "passed" not in result:
                    return {"passed": False, "recommendation": "체크 함수 결과에 'passed' 필드가 없습니다"}
                return result
            except Exception as e:
                # 오류 발생 시 안전한 기본값 반환
                return {
                    "passed": False,
                    "recommendation": f"체크 중 오류가 발생했습니다: {str(e)}"
                }
        
        return {"passed": False, "recommendation": "체크 함수를 찾을 수 없습니다"}
    
    def _validate_product_data(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """상품 데이터 유효성 검증 및 정제 - 개선된 크롤러 데이터 반영"""
        validated = product_data.copy()
        
        # 상품명 검증 (개선된 크롤러의 제외 패턴 반영)
        product_name = validated.get("product_name", "")
        exclude_patterns = [
            "全割引適用後の価格案内", "価格案内", "割引", "クーポン", "Qポイント"
        ]
        if product_name in ["상품명 없음", "商品名なし", ""]:
            validated["product_name"] = ""
        else:
            # 제외 패턴 확인
            for pattern in exclude_patterns:
                if pattern in product_name:
                    validated["product_name"] = ""
                    break
        
        # 가격 데이터 검증 (개선된 크롤러의 유효성 검증 범위 반영)
        price = validated.get("price", {})
        if isinstance(price, dict):
            sale_price = price.get("sale_price")
            original_price = price.get("original_price")
            
            # 개선된 크롤러와 동일한 유효성 검증 범위 (100~1,000,000엔)
            if sale_price and (sale_price < 100 or sale_price > 1000000):
                validated["price"]["sale_price"] = None
            
            if original_price and (original_price < 100 or original_price > 1000000):
                validated["price"]["original_price"] = None
            
            # 판매가가 정가보다 높으면 잘못된 데이터
            if sale_price and original_price and sale_price > original_price:
                validated["price"]["original_price"] = None
                validated["price"]["discount_rate"] = 0
            
            # 음수 가격 제거
            if sale_price and sale_price < 0:
                validated["price"]["sale_price"] = None
            if original_price and original_price < 0:
                validated["price"]["original_price"] = None
        
        # 이미지 데이터 검증
        images = validated.get("images", {})
        if isinstance(images, dict):
            # 빈 리스트로 초기화
            if "detail_images" not in images:
                images["detail_images"] = []
            elif not isinstance(images["detail_images"], list):
                images["detail_images"] = []
        
        # 리뷰 데이터 검증 (fallback 로직 반영)
        reviews = validated.get("reviews", {})
        if isinstance(reviews, dict):
            review_count = reviews.get("review_count", 0)
            review_texts = reviews.get("reviews", [])
            # fallback: review_count가 0이지만 reviews 배열에 리뷰가 있으면 배열 길이로 설정
            if review_count == 0 and isinstance(review_texts, list) and len(review_texts) > 0:
                validated["reviews"]["review_count"] = len(review_texts)
        
        return validated
    
    def _map_checklist_to_page_structure(self, page_structure: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        체크리스트 항목과 페이지 구조(div class) 매핑
        
        Args:
            page_structure: 페이지 구조 정보
            
        Returns:
            체크리스트 ID별 페이지 구조 매핑 정보
        """
        mapping = {}
        
        if not page_structure:
            return mapping
        
        semantic_structure = page_structure.get("semantic_structure", {})
        key_elements = page_structure.get("key_elements", {})
        class_frequency = page_structure.get("class_frequency", {})
        
        # 체크리스트 항목별 관련 div class 매핑
        checklist_class_map = {
            # 판매 준비 카테고리
            "item_001": {  # 상품 등록 완료
                "classes": ["tt", "product-name", "goods_name", "product_name", "thmb", "thumbnail", "detail", "description"],
                "semantic_keys": ["product_name_elements", "image_elements", "description_elements"]
            },
            "item_002": {  # 검색어 설정 완료
                "classes": ["search", "keyword", "tag"],
                "semantic_keys": []
            },
            "item_003": {  # 카테고리 및 브랜드 등록 완료
                "classes": ["category", "breadcrumb", "brand", "brand_official"],
                "semantic_keys": ["navigation"]
            },
            "item_004": {  # 가격 설정 완료
                "classes": ["prc", "price", "cost", "del", "strong"],
                "semantic_keys": ["price_elements"]
            },
            "item_005": {  # 배송 정보 설정 완료
                "classes": ["ship", "ship_area", "shipping", "delivery", "配送", "送料"],
                "semantic_keys": ["shipping_elements"]
            },
            "item_006b": {  # Qポイント 정보 설정
                "classes": ["qpoint", "point", "ポイント", "Qポイント"],
                "semantic_keys": ["qpoint_elements"]
            },
            "item_006c": {  # 반품 정책 명시
                "classes": ["return", "返品", "返品無料"],
                "semantic_keys": []
            },
            "item_006d": {  # MOVE 상품 등록
                "classes": ["move", "MOVE"],
                "semantic_keys": []
            },
            # 매출 증대 카테고리
            "item_007": {  # 상품 페이지 최적화
                "classes": ["tt", "prc", "thmb", "detail", "description", "review"],
                "semantic_keys": ["product_name_elements", "price_elements", "image_elements", "description_elements", "review_elements"]
            },
            "item_008": {  # 검색 키워드 최적화
                "classes": ["tt", "product-name", "keyword", "tag"],
                "semantic_keys": ["product_name_elements"]
            },
            "item_009": {  # 가격 전략 수립
                "classes": ["prc", "price", "del", "strong"],
                "semantic_keys": ["price_elements"]
            },
            "item_011": {  # 프로모션 활용
                "classes": ["coupon", "discount", "割引", "クーポン"],
                "semantic_keys": ["coupon_elements"]
            },
            "item_011b": {  # 쿠폰 상세 정보 제공
                "classes": ["coupon", "discount", "割引", "クーポン", "ショップお気に入り"],
                "semantic_keys": ["coupon_elements"]
            },
            # Shop 운영 카테고리
            "item_016b": {  # Shop 레벨 최적화
                "classes": ["power", "POWER", "パワー", "grade"],
                "semantic_keys": []
            },
            "item_016c": {  # Shop 팔로워 수 관리
                "classes": ["follower", "フォロワー"],
                "semantic_keys": []
            },
            "item_016d": {  # Shop 상품 다양성
                "classes": ["item", "product", "goods"],
                "semantic_keys": []
            },
            # 광고/프로모션 카테고리
            "item_021": {  # 샵 쿠폰 설정
                "classes": ["coupon", "クーポン", "割引"],
                "semantic_keys": ["coupon_elements"]
            },
            "item_022": {  # 상품 할인 설정
                "classes": ["prc", "price", "del", "discount"],
                "semantic_keys": ["price_elements"]
            }
        }
        
        # 각 체크리스트 항목에 대해 페이지 구조 확인
        for item_id, class_info in checklist_class_map.items():
            related_classes = class_info.get("classes", [])
            semantic_keys = class_info.get("semantic_keys", [])
            
            found_classes = []
            element_present = False
            frequency_info = {}
            
            # 직접 class 확인
            for cls in related_classes:
                if cls in class_frequency:
                    found_classes.append(cls)
                    frequency_info[cls] = class_frequency[cls]
                    element_present = True
            
            # semantic structure 확인
            for semantic_key in semantic_keys:
                elements = semantic_structure.get(semantic_key, [])
                if elements:
                    element_present = True
                    for elem in elements[:3]:  # 상위 3개만
                        cls = elem.get("class")
                        if cls:
                            if cls not in found_classes:
                                found_classes.append(cls)
                            frequency_info[cls] = elem.get("frequency", 0)
            
            mapping[item_id] = {
                "classes": found_classes,
                "present": element_present,
                "frequency": frequency_info
            }
        
        return mapping
    
    def _validate_shop_data(self, shop_data: Dict[str, Any]) -> Dict[str, Any]:
        """Shop 데이터 유효성 검증 및 정제"""
        validated = shop_data.copy()
        
        # 팔로워 수 검증
        follower_count = validated.get("follower_count", 0)
        if not isinstance(follower_count, int) or follower_count < 0:
            validated["follower_count"] = 0
        
        # 상품 수 검증
        product_count = validated.get("product_count", 0)
        if not isinstance(product_count, int) or product_count < 0:
            validated["product_count"] = 0
        
        return validated
    
    async def _check_product_registered(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """상품 등록 완료 체크 - 개선된 크롤러 데이터 반영"""
        if not product_data:
            return {"passed": False, "recommendation": "상품 데이터가 없습니다"}
        
        product_name = product_data.get("product_name", "")
        description = product_data.get("description", "")
        images = product_data.get("images", {})
        thumbnail = images.get("thumbnail") if isinstance(images, dict) else None
        detail_images = images.get("detail_images", []) if isinstance(images, dict) else []
        
        # 상품명 확인 (개선된 크롤러의 제외 패턴 반영)
        # 크롤러에서 제외한 패턴: 가격 안내, 쿠폰 할인, Qポイント 관련 텍스트
        exclude_patterns = [
            "全割引適用後の価格案内", "価格案内", "割引", "クーポン", "Qポイント",
            "상품명 없음", "商品名なし", ""
        ]
        has_name = bool(product_name) and len(product_name.strip()) > 3
        if has_name:
            # 제외 패턴 확인
            for pattern in exclude_patterns:
                if pattern in product_name:
                    has_name = False
                    break
        
        # 상품 설명 확인 (최소 길이 확인, HTML 태그 제거 후 길이 확인)
        description_text = description.strip() if description else ""
        # HTML 태그 제거 (간단한 방법)
        import re
        description_text = re.sub(r'<[^>]+>', '', description_text)
        description_length = len(description_text)
        has_description = description_length >= 50
        
        # 이미지 확인 (썸네일 또는 상세 이미지)
        # 유효한 이미지 URL인지 확인
        has_thumbnail = bool(thumbnail) and isinstance(thumbnail, str) and ('http' in thumbnail or thumbnail.startswith('//'))
        has_detail_images = isinstance(detail_images, list) and len(detail_images) > 0
        has_images = has_thumbnail or has_detail_images
        image_count = len(detail_images) + (1 if has_thumbnail else 0)
        
        # 분석 결과에서 이미지 분석 점수 확인 (더 정확한 평가)
        image_score = 0
        if analysis_result:
            image_analysis = analysis_result.get("image_analysis", {})
            image_score = image_analysis.get("score", 0)
        
        # 점수 계산 (더 세밀한 평가)
        score = 0
        max_score = 3
        if has_name:
            score += 1
        if has_description:
            score += 1
        if has_images:
            score += 1
        
        if score == max_score:
            return {
                "passed": True,
                "recommendation": f"상품 등록 완료 (상품명: {product_name[:30]}{'...' if len(product_name) > 30 else ''}, 설명: {description_length}자, 이미지: {image_count}개)"
            }
        else:
            missing = []
            if not has_name:
                missing.append("상품명")
            if not has_description:
                missing.append(f"상품 설명 (현재: {description_length}자, 최소 50자 필요)")
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
        """카테고리 및 브랜드 등록 체크 - 실제 데이터 정확히 반영"""
        if not product_data:
            return {"passed": False, "recommendation": "상품 데이터가 없습니다"}
        
        category = product_data.get("category")
        brand = product_data.get("brand")
        
        has_category = bool(category) and category not in ["", "N/A", "카테고리 없음"]
        has_brand = bool(brand) and brand not in ["", "N/A", "브랜드 없음"]
        
        if has_category and has_brand:
            return {
                "passed": True,
                "recommendation": f"카테고리 및 브랜드 등록 완료 (카테고리: {category}, 브랜드: {brand})"
            }
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
        """가격 설정 체크 - 개선된 크롤러 데이터 반영 (유효성 검증 범위 일치)"""
        if not product_data:
            return {"passed": False, "recommendation": "상품 데이터가 없습니다"}
        
        price = product_data.get("price", {})
        if not isinstance(price, dict):
            return {"passed": False, "recommendation": "가격 정보가 올바른 형식이 아닙니다"}
        
        sale_price = price.get("sale_price")
        original_price = price.get("original_price")
        discount_rate = price.get("discount_rate", 0)
        
        # 판매가가 설정되어 있는지 확인 (유효한 범위 내)
        # 개선된 크롤러와 동일한 유효성 검증 범위 사용 (100~1,000,000엔)
        if not sale_price or sale_price <= 0:
            return {
                "passed": False,
                "recommendation": "판매가를 설정하세요"
            }
        
        # 개선된 크롤러와 동일한 유효성 검증 범위 (100엔 ~ 1,000,000엔)
        if sale_price < 100 or sale_price > 1000000:
            return {
                "passed": False,
                "recommendation": f"판매가가 합리적인 범위를 벗어났습니다 ({sale_price}円). 가격을 확인하세요 (100~1,000,000엔 범위)"
            }
        
        # 정가와 할인율이 설정되어 있는지 확인 (선택사항이지만 권장)
        if original_price and original_price > 0:
            # 개선된 크롤러와 동일한 유효성 검증 범위
            if original_price < 100 or original_price > 1000000:
                return {
                    "passed": True,
                    "recommendation": f"판매가 설정 완료 ({sale_price:,}円). 정가가 유효한 범위를 벗어났습니다 (100~1,000,000엔 범위)"
                }
            
            # 정가가 판매가보다 높아야 함
            if original_price <= sale_price:
                return {
                    "passed": False,
                    "recommendation": "정가가 판매가보다 낮거나 같습니다. 정가를 판매가보다 높게 설정하세요"
                }
            
            # 할인율 계산 검증
            calculated_discount = int(((original_price - sale_price) / original_price) * 100)
            if discount_rate > 0 and abs(calculated_discount - discount_rate) > 5:
                # 할인율이 계산된 값과 크게 다르면 경고
                return {
                    "passed": True,
                    "recommendation": f"가격 설정 완료 (판매가: {sale_price:,}円, 정가: {original_price:,}円). 할인율을 확인하세요 (계산된 할인율: {calculated_discount}%)"
                }
            
            return {
                "passed": True,
                "recommendation": f"가격 설정 완료 (판매가: {sale_price:,}円, 정가: {original_price:,}円, 할인율: {calculated_discount}%)"
            }
        elif sale_price:
            return {
                "passed": True,
                "recommendation": f"판매가 설정 완료 ({sale_price:,}円). 정가와 할인율 설정을 고려하세요 (구매 욕구 증대 효과)"
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
        """상품 페이지 최적화 체크 - 실제 분석 점수 정확히 반영"""
        if not analysis_result:
            return {"passed": False, "recommendation": "분석 결과가 없습니다"}
        
        overall_score = analysis_result.get("overall_score", 0)
        
        # 실제 분석 점수 확인 (정확도 향상)
        if overall_score >= 70:
            return {
                "passed": True,
                "recommendation": f"페이지 최적화 완료 (현재 점수: {overall_score}점)"
            }
        else:
            # 세부 점수 정보 추가
            detail_info = []
            image_analysis = analysis_result.get("image_analysis", {})
            description_analysis = analysis_result.get("description_analysis", {})
            price_analysis = analysis_result.get("price_analysis", {})
            review_analysis = analysis_result.get("review_analysis", {})
            
            if image_analysis:
                detail_info.append(f"이미지: {image_analysis.get('score', 0)}점")
            if description_analysis:
                detail_info.append(f"설명: {description_analysis.get('score', 0)}점")
            if price_analysis:
                detail_info.append(f"가격: {price_analysis.get('score', 0)}점")
            if review_analysis:
                detail_info.append(f"리뷰: {review_analysis.get('score', 0)}점")
            
            detail_str = f" ({', '.join(detail_info)})" if detail_info else ""
            
            return {
                "passed": False,
                "recommendation": f"현재 점수 {overall_score}점{detail_str}. 70점 이상을 목표로 개선하세요"
            }
    
    async def _check_keyword_optimization(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """검색 키워드 최적화 체크 - 실제 분석 결과 정확히 반영"""
        if not analysis_result:
            return {"passed": False, "recommendation": "분석 결과가 없습니다"}
        
        seo_analysis = analysis_result.get("seo_analysis", {})
        keywords_in_name = seo_analysis.get("keywords_in_name", False)
        keywords_in_description = seo_analysis.get("keywords_in_description", False)
        seo_score = seo_analysis.get("score", 0)
        
        # 실제 상품명과 검색어 확인
        product_name = ""
        search_keywords = []
        if product_data:
            product_name = product_data.get("product_name", "")
            search_keywords = product_data.get("search_keywords", [])
        
        if keywords_in_name or (search_keywords and len(search_keywords) > 0):
            keyword_info = []
            if search_keywords:
                keyword_info.append(f"검색어: {', '.join(search_keywords[:3])}{'...' if len(search_keywords) > 3 else ''}")
            if seo_score > 0:
                keyword_info.append(f"SEO 점수: {seo_score}점")
            return {
                "passed": True,
                "recommendation": f"검색 키워드 최적화 완료{(' (' + ', '.join(keyword_info) + ')' if keyword_info else '')}"
            }
        else:
            return {
                "passed": False,
                "recommendation": f"상품명에 인기 키워드를 포함하세요{' (현재 상품명: ' + product_name[:30] + '...)' if product_name and len(product_name) > 30 else (' (현재 상품명: ' + product_name + ')' if product_name else '')}"
            }
    
    async def _check_price_strategy(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """가격 전략 체크 - 실제 분석 결과 정확히 반영"""
        if not analysis_result:
            return {"passed": False, "recommendation": "분석 결과가 없습니다"}
        
        price_analysis = analysis_result.get("price_analysis", {})
        score = price_analysis.get("score", 0)
        positioning = price_analysis.get("positioning", "")
        sale_price = None
        discount_rate = 0
        
        if product_data:
            price = product_data.get("price", {})
            if isinstance(price, dict):
                sale_price = price.get("sale_price")
                discount_rate = price.get("discount_rate", 0)
        
        if score >= 60:
            price_info = []
            if sale_price:
                price_info.append(f"판매가: {sale_price:,}円")
            if discount_rate > 0:
                price_info.append(f"할인율: {discount_rate}%")
            if positioning:
                price_info.append(f"포지셔닝: {positioning}")
            
            return {
                "passed": True,
                "recommendation": f"가격 전략 수립 완료 (점수: {score}점{', ' + ', '.join(price_info) if price_info else ''})"
            }
        else:
            return {
                "passed": False,
                "recommendation": f"가격 전략을 재검토하세요 (현재 점수: {score}점)"
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
    
    async def _check_qpoint_info(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Qポイント 정보 체크 - 개선된 크롤러 데이터 반영"""
        if not product_data:
            return {"passed": False, "recommendation": "상품 데이터가 없습니다"}
        
        qpoint_info = product_data.get("qpoint_info", {})
        if isinstance(qpoint_info, dict):
            # 개선된 크롤러에서 추출하는 다양한 Qポイント 정보 확인
            max_points = qpoint_info.get("max_points")
            receive_confirmation_points = qpoint_info.get("receive_confirmation_points")
            review_points = qpoint_info.get("review_points")
            auto_points = qpoint_info.get("auto_points")
            
            # 하나라도 있으면 통과
            if max_points and max_points > 0:
                point_details = [f"최대 {max_points}P"]
                if receive_confirmation_points:
                    point_details.append(f"수령확인 {receive_confirmation_points}P")
                if review_points:
                    point_details.append(f"리뷰작성 {review_points}P")
                if auto_points:
                    point_details.append(f"자동 {auto_points}P")
                
                return {
                    "passed": True,
                    "recommendation": f"Qポイント 정보 설정 완료 ({', '.join(point_details)})"
                }
            elif receive_confirmation_points or review_points or auto_points:
                point_details = []
                if receive_confirmation_points:
                    point_details.append(f"수령확인 {receive_confirmation_points}P")
                if review_points:
                    point_details.append(f"리뷰작성 {review_points}P")
                if auto_points:
                    point_details.append(f"자동 {auto_points}P")
                
                return {
                    "passed": True,
                    "recommendation": f"Qポイント 정보 설정 완료 ({', '.join(point_details)})"
                }
        elif isinstance(qpoint_info, int) and qpoint_info > 0:
            return {
                "passed": True,
                "recommendation": f"Qポイント 정보 설정 완료 (최대 {qpoint_info}P)"
            }
        
        return {
            "passed": False,
            "recommendation": "Qポイント獲得方法을 명시하여 고객에게 혜택을 제공하세요"
        }
    
    async def _check_return_policy(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """반품 정책 체크 - 개선된 크롤러 데이터 반영"""
        if not product_data:
            return {"passed": False, "recommendation": "상품 데이터가 없습니다"}
        
        shipping_info = product_data.get("shipping_info", {})
        return_policy = shipping_info.get("return_policy")
        
        # 개선된 크롤러에서 추출하는 반품 정책 값 확인
        if return_policy == "free_return":
            return {
                "passed": True,
                "recommendation": "返品無料 서비스가 설정되어 있어 고객 신뢰도 향상"
            }
        elif return_policy == "return_available" or return_policy == "return":
            return {
                "passed": True,
                "recommendation": "반품 정책이 명시되어 있습니다. 返品無料 서비스 설정을 고려하세요"
            }
        elif return_policy:
            # 기타 반품 정책이 있는 경우
            return {
                "passed": True,
                "recommendation": f"반품 정책이 명시되어 있습니다 ({return_policy}). 返品無料 서비스 설정을 고려하세요"
            }
        else:
            return {
                "passed": False,
                "recommendation": "반품 정책을 명확히 표시하세요. 返品無料 서비스 설정 시 고객 신뢰도 향상"
            }
    
    async def _check_move_product(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """MOVE 상품 여부 체크"""
        if not product_data:
            return {"passed": False, "recommendation": "상품 데이터가 없습니다"}
        
        is_move = product_data.get("is_move_product", False)
        
        if is_move:
            return {
                "passed": True,
                "recommendation": "MOVE 상품으로 등록되어 있어 추가 노출 기회 확보"
            }
        else:
            return {
                "passed": True,  # MOVE는 선택사항이므로 통과로 처리
                "recommendation": "MOVE 상품 등록을 고려하세요. 추가 노출 기회를 확보할 수 있습니다"
            }
    
    async def _check_coupon_detail(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """쿠폰 상세 정보 체크"""
        if not product_data:
            return {"passed": False, "recommendation": "상품 데이터가 없습니다"}
        
        coupon_info = product_data.get("coupon_info", {})
        if isinstance(coupon_info, dict):
            has_coupon = coupon_info.get("has_coupon", False)
            max_discount = coupon_info.get("max_discount")
            
            if has_coupon:
                if max_discount and max_discount > 0:
                    return {
                        "passed": True,
                        "recommendation": f"쿠폰 정보가 명확히 표시되어 있습니다 (최대 {max_discount}円 할인)"
                    }
                else:
                    return {
                        "passed": True,
                        "recommendation": "쿠폰 정보가 표시되어 있습니다. 할인 금액을 명확히 표시하세요"
                    }
        
        # price에서 coupon_discount 확인
        price = product_data.get("price", {})
        coupon_discount = price.get("coupon_discount")
        if coupon_discount and coupon_discount > 0:
            return {
                "passed": True,
                "recommendation": f"쿠폰 할인 정보가 표시되어 있습니다 ({coupon_discount}円)"
            }
        
        return {
            "passed": False,
            "recommendation": "쿠폰 할인 정보를 명확히 표시하여 고객이 쉽게 확인할 수 있도록 하세요"
        }
    
    async def _check_shop_level(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Shop 레벨 체크 - 실제 데이터 정확히 반영"""
        # product_data에서 seller_info 확인 (shop_data가 없을 경우)
        if not shop_data and product_data:
            seller_info = product_data.get("seller_info", {})
            shop_level = seller_info.get("shop_level")
            shop_name = seller_info.get("shop_name")
            
            if shop_level:
                shop_data = {"shop_level": shop_level, "shop_name": shop_name}
        
        if not shop_data:
            # product_data에서도 확인 불가능한 경우
            return {
                "passed": False,
                "recommendation": "Shop 데이터가 없습니다. 상품 페이지에서 Shop 정보를 확인할 수 없습니다"
            }
        
        shop_level = shop_data.get("shop_level")
        shop_name = shop_data.get("shop_name", "")
        
        if shop_level == "power" or shop_level == "POWER":
            return {
                "passed": True,
                "recommendation": f"POWER 셀러 등급{' (' + shop_name + ')' if shop_name else ''}으로 정산 리드타임이 단축됩니다 (배송 완료 후 5일)"
            }
        elif shop_level == "excellent" or shop_level == "우수":
            return {
                "passed": True,
                "recommendation": f"우수 셀러 등급{' (' + shop_name + ')' if shop_name else ''}입니다. POWER 셀러 등급 달성을 목표로 하세요 (정산 리드타임: 배송 완료 후 10일)"
            }
        elif shop_level == "normal" or shop_level == "일반":
            return {
                "passed": True,
                "recommendation": f"일반 셀러 등급{' (' + shop_name + ')' if shop_name else ''}입니다. 우수 셀러 등급 달성을 목표로 하세요 (정산 리드타임: 배송 완료 후 15일)"
            }
        elif shop_level:
            return {
                "passed": True,
                "recommendation": f"Shop 레벨: {shop_level}{' (' + shop_name + ')' if shop_name else ''}. POWER 셀러 등급 달성을 목표로 하세요"
            }
        else:
            return {
                "passed": False,
                "recommendation": "Shop 레벨을 확인할 수 없습니다. 판매 실적을 향상시켜 등급을 올리세요"
            }
    
    async def _check_shop_followers(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Shop 팔로워 수 체크 - 실제 데이터 정확히 반영"""
        # product_data에서 seller_info 확인 (shop_data가 없을 경우)
        if not shop_data and product_data:
            seller_info = product_data.get("seller_info", {})
            if seller_info:
                shop_data = seller_info
        
        if not shop_data:
            return {
                "passed": False,
                "recommendation": "Shop 데이터가 없습니다. 상품 페이지에서 Shop 정보를 확인할 수 없습니다"
            }
        
        follower_count = shop_data.get("follower_count", 0)
        
        # 숫자 타입 확인 및 변환
        if isinstance(follower_count, str):
            try:
                follower_count = int(follower_count.replace(',', '').replace('명', '').strip())
            except:
                follower_count = 0
        
        if follower_count >= 1000:
            return {
                "passed": True,
                "recommendation": f"Shop 팔로워 수가 충분합니다 ({follower_count:,}명). 고객 기반이 잘 구축되어 있습니다"
            }
        elif follower_count >= 100:
            return {
                "passed": True,
                "recommendation": f"Shop 팔로워 수: {follower_count:,}명. 1,000명 이상을 목표로 하세요"
            }
        elif follower_count > 0:
            return {
                "passed": True,
                "recommendation": f"Shop 팔로워 수: {follower_count:,}명. 팔로워 수를 늘려 고객 기반을 확대하세요"
            }
        else:
            return {
                "passed": False,
                "recommendation": "Shop 팔로워 수를 늘려 고객 기반을 확대하세요. 샵 쿠폰, 이벤트 등을 활용하세요"
            }
    
    async def _check_shop_product_diversity(
        self,
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Shop 상품 다양성 체크 - 실제 데이터 정확히 반영"""
        # product_data에서 seller_info 확인 (shop_data가 없을 경우)
        if not shop_data and product_data:
            seller_info = product_data.get("seller_info", {})
            if seller_info:
                shop_data = seller_info
        
        if not shop_data:
            return {
                "passed": False,
                "recommendation": "Shop 데이터가 없습니다. 상품 페이지에서 Shop 정보를 확인할 수 없습니다"
            }
        
        product_count = shop_data.get("product_count", 0)
        categories = shop_data.get("categories", {})
        category_count = len(categories) if isinstance(categories, dict) else 0
        
        # 숫자 타입 확인 및 변환
        if isinstance(product_count, str):
            try:
                product_count = int(product_count.replace(',', '').replace('개', '').strip())
            except:
                product_count = 0
        
        if product_count >= 20 and category_count >= 3:
            return {
                "passed": True,
                "recommendation": f"다양한 상품이 등록되어 있습니다 (상품 수: {product_count}개, 카테고리: {category_count}개)"
            }
        elif product_count >= 10:
            return {
                "passed": True,
                "recommendation": f"상품 수: {product_count}개. 더 다양한 상품을 등록하여 고객 선택권을 넓히세요"
            }
        elif product_count > 0:
            return {
                "passed": True,
                "recommendation": f"상품 수: {product_count}개. 상품 다양성을 높여 고객 유입을 늘리세요"
            }
        else:
            return {
                "passed": False,
                "recommendation": "상품을 더 등록하여 Shop의 다양성을 높이세요"
            }