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
        checklist_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        크롤링 결과와 리포트 내용 일치 여부 검증
        
        Args:
            product_data: 크롤러가 수집한 원본 데이터
            analysis_result: 분석 결과
            checklist_result: 체크리스트 평가 결과
            
        Returns:
            검증 결과 딕셔너리
        """
        validation_result = {
            "is_valid": True,
            "mismatches": [],
            "missing_items": [],
            "validation_score": 100.0,
            "timestamp": datetime.now().isoformat()
        }
        
        mismatches = []
        missing_items = []
        
        # 1. 상품명 검증
        crawler_name = product_data.get("product_name", "")
        report_name = analysis_result.get("product_analysis", {}).get("product_name", "")
        if crawler_name and report_name and crawler_name != report_name:
            mismatches.append({
                "field": "product_name",
                "crawler_value": crawler_name,
                "report_value": report_name,
                "severity": "high"
            })
        
        # 2. 가격 검증
        crawler_price = product_data.get("price", {}).get("sale_price")
        report_price = analysis_result.get("product_analysis", {}).get("price_analysis", {}).get("sale_price")
        if crawler_price and report_price and crawler_price != report_price:
            mismatches.append({
                "field": "price_sale",
                "crawler_value": crawler_price,
                "report_value": report_price,
                "severity": "high"
            })
        
        # 3. 리뷰 수 검증
        crawler_reviews = product_data.get("reviews", {}).get("review_count", 0)
        report_reviews = analysis_result.get("product_analysis", {}).get("review_analysis", {}).get("review_count", 0)
        if crawler_reviews != report_reviews:
            mismatches.append({
                "field": "review_count",
                "crawler_value": crawler_reviews,
                "report_value": report_reviews,
                "severity": "medium"
            })
        
        # 4. 이미지 개수 검증
        crawler_images = len(product_data.get("images", {}).get("detail_images", []))
        report_images = analysis_result.get("product_analysis", {}).get("image_analysis", {}).get("image_count", 0)
        if crawler_images != report_images:
            mismatches.append({
                "field": "image_count",
                "crawler_value": crawler_images,
                "report_value": report_images,
                "severity": "medium"
            })
        
        # 5. 체크리스트 항목 검증
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
        if product_data.get("qpoint_info") and not any(
            item["id"] in ["item_006b"] for item in checklist_items
        ):
            missing_items.append({
                "field": "qpoint_info",
                "crawler_has_data": True,
                "checklist_item_id": "item_006b",
                "severity": "high"
            })
        
        if product_data.get("coupon_info", {}).get("has_coupon") and not any(
            item["id"] in ["item_011", "item_021"] for item in checklist_items
        ):
            missing_items.append({
                "field": "coupon_info",
                "crawler_has_data": True,
                "checklist_item_id": "item_011",
                "severity": "high"
            })
        
        # 검증 점수 계산
        total_fields = 5
        error_count = len(mismatches) + len(missing_items)
        validation_score = max(0, 100 - (error_count / total_fields * 100))
        
        validation_result.update({
            "is_valid": len(mismatches) == 0 and len(missing_items) == 0,
            "mismatches": mismatches,
            "missing_items": missing_items,
            "validation_score": validation_score
        })
        
        return validation_result
    
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
