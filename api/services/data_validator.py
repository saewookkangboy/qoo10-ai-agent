"""
데이터 검증 서비스
크롤링 결과와 리포트 내용의 일치 여부를 검증합니다.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """데이터 검증기"""
    
    def __init__(self):
        pass
    
    def validate_crawler_vs_report(
        self,
        product_data: Dict[str, Any],
        analysis_result: Dict[str, Any],
        checklist_result: Dict[str, Any],
        api_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        크롤링 결과와 리포트 내용 일치 여부 검증 (강화된 버전)
        API 데이터가 있으면 우선적으로 사용하여 검증
        
        Args:
            product_data: 크롤러가 수집한 원본 데이터
            analysis_result: 분석 결과
            checklist_result: 체크리스트 평가 결과
            api_data: Qoo10 API로 조회한 데이터 (선택사항, 우선순위 높음)
            
        Returns:
            검증 결과 딕셔너리
        """
        # API 데이터가 있으면 우선적으로 사용
        reference_data = api_data if api_data else product_data
        data_source = "qoo10_api" if api_data else product_data.get("crawled_with", "crawler")
        
        validation_result = {
            "is_valid": True,
            "mismatches": [],
            "missing_items": [],
            "validation_score": 100.0,
            "timestamp": datetime.now().isoformat(),
            "corrected_fields": [],  # 자동 수정된 필드 목록
            "data_source": data_source,  # 데이터 소스 표시
            "has_api_data": bool(api_data)  # API 데이터 사용 여부
        }
        
        mismatches = []
        missing_items = []
        corrected_fields = []
        
        # 1. 상품명 검증 및 보정
        crawler_name = reference_data.get("product_name", "")
        if crawler_name and crawler_name != "상품명 없음":
            product_analysis = analysis_result.get("product_analysis", {})
            original_name = product_analysis.get("product_name", "")
            if not original_name or original_name != crawler_name:
                # Record mismatch BEFORE correction (only if there was an original value)
                if original_name and original_name != crawler_name:
                    mismatches.append({
                        "field": "product_name",
                        "crawler_value": crawler_name,
                        "report_value": original_name,
                        "severity": "high",
                        "corrected": True
                    })
                product_analysis["product_name"] = crawler_name
                corrected_fields.append("product_name")
        
        # 2. 가격 검증 및 보정
        crawler_price = reference_data.get("price", {}).get("sale_price")
        crawler_original_price = reference_data.get("price", {}).get("original_price")
        if crawler_price:
            price_analysis = analysis_result.get("product_analysis", {}).get("price_analysis", {})
            original_sale = price_analysis.get("sale_price")
            if not original_sale or original_sale != crawler_price:
                # 기존 값과 다를 경우 mismatch 기록
                if original_sale and original_sale != crawler_price:
                    mismatches.append({
                        "field": "price_sale",
                        "crawler_value": crawler_price,
                        "report_value": original_sale,
                        "severity": "high",
                        "corrected": True
                    })
                price_analysis["sale_price"] = crawler_price
                corrected_fields.append("price_sale")
            
            if crawler_original_price:
                original_original = price_analysis.get("original_price")
                if not original_original or original_original != crawler_original_price:
                    # 기존 값과 다를 경우 mismatch 기록
                    if original_original and original_original != crawler_original_price:
                        mismatches.append({
                            "field": "price_original",
                            "crawler_value": crawler_original_price,
                            "report_value": original_original,
                            "severity": "high",
                            "corrected": True
                        })
                    price_analysis["original_price"] = crawler_original_price
                    corrected_fields.append("price_original")
                
                # 할인율 재계산
                if crawler_price and crawler_original_price and crawler_original_price > crawler_price:
                    discount_rate = int((crawler_original_price - crawler_price) / crawler_original_price * 100)
                    price_analysis["discount_rate"] = discount_rate
        
        # 3. 리뷰 수 검증 및 보정
        crawler_reviews = reference_data.get("reviews", {}).get("review_count", 0)
        crawler_rating = reference_data.get("reviews", {}).get("rating", 0)
        review_analysis = analysis_result.get("product_analysis", {}).get("review_analysis", {})
        orig_report = review_analysis.get("review_count", 0)
        if orig_report != crawler_reviews:
            mismatches.append({
                "field": "review_count",
                "crawler_value": crawler_reviews,
                "report_value": orig_report,
                "severity": "medium",
                "corrected": True
            })
            review_analysis["review_count"] = crawler_reviews
            corrected_fields.append("review_count")
        
        if crawler_rating and review_analysis.get("rating", 0) != crawler_rating:
            review_analysis["rating"] = crawler_rating
            corrected_fields.append("rating")
        
        # 4. 이미지 개수 검증 및 보정
        crawler_images = len(reference_data.get("images", {}).get("detail_images", []))
        image_analysis = analysis_result.get("product_analysis", {}).get("image_analysis", {})
        original_image_count = image_analysis.get("image_count", 0)
        if original_image_count != crawler_images:
            mismatches.append({
                "field": "image_count",
                "crawler_value": crawler_images,
                "report_value": original_image_count,
                "severity": "medium",
                "corrected": True
            })
            image_analysis["image_count"] = crawler_images
            corrected_fields.append("image_count")
        
        # 5. 설명 길이 검증 및 보정
        crawler_description = reference_data.get("description", "")
        description_length = len(crawler_description)
        description_analysis = analysis_result.get("product_analysis", {}).get("description_analysis", {})
        if description_analysis.get("description_length", 0) != description_length:
            description_analysis["description_length"] = description_length
            corrected_fields.append("description_length")
        
        # 6. Qポイント 정보 검증 및 보정
        qpoint_info = reference_data.get("qpoint_info", {})
        if qpoint_info and any(qpoint_info.values()):
            # analysis_result에 Qポイント 정보가 없으면 추가
            if "qpoint_info" not in analysis_result.get("product_analysis", {}):
                analysis_result.setdefault("product_analysis", {})["qpoint_info"] = qpoint_info
                corrected_fields.append("qpoint_info")
        
        # 7. 쿠폰 정보 검증 및 보정
        coupon_info = reference_data.get("coupon_info", {})
        if coupon_info and coupon_info.get("has_coupon"):
            if "coupon_info" not in analysis_result.get("product_analysis", {}):
                analysis_result.setdefault("product_analysis", {})["coupon_info"] = coupon_info
                corrected_fields.append("coupon_info")
        
        # 8. 배송 정보 검증 및 보정
        shipping_info = reference_data.get("shipping_info", {})
        if shipping_info:
            if "shipping_info" not in analysis_result.get("product_analysis", {}):
                analysis_result.setdefault("product_analysis", {})["shipping_info"] = shipping_info
                corrected_fields.append("shipping_info")
        
        # 9. 체크리스트 항목 검증
        checklist_items = []
        for checklist in checklist_result.get("checklists", []):
            for item in checklist.get("items", []):
                checklist_items.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "status": item.get("status"),
                    "auto_checked": item.get("auto_checked", False)
                })
        
        # 크롤러 데이터가 있지만 체크리스트에서 누락된 항목 확인
        if reference_data.get("qpoint_info") and not any(
            item["id"] in ["item_006a", "item_006b"] for item in checklist_items
        ):
            missing_items.append({
                "field": "qpoint_info",
                "crawler_has_data": True,
                "checklist_item_id": "item_006b",
                "severity": "high"
            })
        
        if reference_data.get("coupon_info", {}).get("has_coupon") and not any(
            item["id"] in ["item_011", "item_020", "item_021"] for item in checklist_items
        ):
            missing_items.append({
                "field": "coupon_info",
                "crawler_has_data": True,
                "checklist_item_id": "item_011",
                "severity": "high"
            })
        
        # 검증 점수 계산
        # 검증 필드: product_name, price_sale, price_original, review_count, rating,
        #           image_count, description_length, qpoint_info, coupon_info, shipping_info
        total_fields = 10  # 실제 검증 필드 수 (discount_rate는 재계산만 수행)
        error_count = len([m for m in mismatches if not m.get("corrected", False)]) + len(missing_items)
        validation_score = max(0, 100 - (error_count / total_fields * 100))
        
        validation_result.update({
            "is_valid": len([m for m in mismatches if not m.get("corrected", False)]) == 0 and len(missing_items) == 0,
            "mismatches": mismatches,
            "missing_items": missing_items,
            "validation_score": validation_score,
            "corrected_fields": corrected_fields
        })
        
        return validation_result
    
    def sync_analysis_result_with_crawler_data(
        self,
        product_data: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        크롤러 데이터를 기반으로 analysis_result를 동기화
        
        주의: validate_crawler_vs_report에서 이미 보정을 수행하므로,
        이 함수는 validate_crawler_vs_report를 내부적으로 호출하여
        검증과 동기화를 함께 수행합니다.
        
        Args:
            product_data: 크롤러가 수집한 원본 데이터
            analysis_result: 분석 결과 (수정됨)
            
        Returns:
            동기화된 analysis_result
        """
        # validate_crawler_vs_report를 호출하여 검증 및 보정 수행
        # (checklist_result는 없어도 됨 - 동기화만 수행)
        validation_result = self.validate_crawler_vs_report(
            product_data=product_data,
            analysis_result=analysis_result,
            checklist_result={}  # 체크리스트 없이 동기화만 수행
        )
        
        # validate_crawler_vs_report에서 이미 보정이 수행되었으므로
        # analysis_result는 이미 동기화된 상태입니다.
        # 추가로 누락된 필드가 있으면 보완
        if "product_analysis" not in analysis_result:
            analysis_result["product_analysis"] = {}
        
        product_analysis = analysis_result["product_analysis"]
        
        # 누락된 필드 보완 (validate_crawler_vs_report에서 처리하지 않은 필드)
        # 이미 validate_crawler_vs_report에서 처리했으므로 여기서는 추가 보완만 수행
        
        return analysis_result
    
    def extract_validation_chunks(
        self,
        validation_result: Dict[str, Any],
        product_data: Dict[str, Any],
        page_structure: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        검증 결과를 Chunk로 분석하여 저장
        
        Args:
            validation_result: 검증 결과
            product_data: 크롤러 데이터
            page_structure: 페이지 구조 정보
            
        Returns:
            Chunk 분석 결과 리스트
        """
        chunks = []
        
        # 각 불일치 항목에 대해 Chunk 생성
        for mismatch in validation_result.get("mismatches", []):
            chunk = {
                "field": mismatch["field"],
                "issue_type": "mismatch",
                "crawler_value": mismatch["crawler_value"],
                "report_value": mismatch["report_value"],
                "severity": mismatch["severity"],
                "page_structure": page_structure.get(mismatch["field"], {}) if page_structure else {},
                "timestamp": datetime.now().isoformat(),
                "context": {
                    "product_code": product_data.get("product_code"),
                    "url": product_data.get("url"),
                    "crawled_with": product_data.get("crawled_with")
                }
            }
            chunks.append(chunk)
        
        # 각 누락 항목에 대해 Chunk 생성
        for missing in validation_result.get("missing_items", []):
            chunk = {
                "field": missing["field"],
                "issue_type": "missing",
                "crawler_has_data": missing["crawler_has_data"],
                "checklist_item_id": missing["checklist_item_id"],
                "severity": missing["severity"],
                "page_structure": page_structure.get(missing["field"], {}) if page_structure else {},
                "timestamp": datetime.now().isoformat(),
                "context": {
                    "product_code": product_data.get("product_code"),
                    "url": product_data.get("url"),
                    "crawled_with": product_data.get("crawled_with")
                }
            }
            chunks.append(chunk)
        
        return chunks
