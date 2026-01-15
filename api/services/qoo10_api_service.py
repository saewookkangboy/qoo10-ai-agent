"""
Qoo10 API 서비스
Qoo10 공식 API를 사용하여 상품 정보를 조회합니다.
크롤링 데이터와 비교하여 데이터 정확도를 향상시킵니다.
"""
import httpx
from typing import Dict, Any, Optional, List
import logging
import hashlib
import hmac
import time
from urllib.parse import urlencode, quote
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Qoo10APIService:
    """Qoo10 API 서비스"""
    
    API_BASE_URL = "https://api.qoo10.jp/GMKT.INC.Front.QAPIService/qaapi.aspx"
    
    def __init__(self, certification_key: Optional[str] = None):
        """
        Qoo10 API 서비스 초기화
        
        Args:
            certification_key: Qoo10 API 인증 키 (환경 변수 QOO10_API_KEY에서도 로드 가능)
        """
        self.certification_key = certification_key or os.getenv("QOO10_API_KEY")
        if not self.certification_key:
            logger.warning("Qoo10 API Key가 설정되지 않았습니다. API 기능을 사용할 수 없습니다.")
    
    def _generate_signature(self, parameters: Dict[str, Any]) -> str:
        """
        API 요청 서명 생성
        
        Args:
            parameters: API 파라미터 딕셔너리
            
        Returns:
            서명 문자열
        """
        if not self.certification_key:
            return ""
        
        # 파라미터를 정렬하여 문자열 생성
        sorted_params = sorted(parameters.items())
        param_string = "&".join([f"{k}={v}" for k, v in sorted_params if v])
        
        # 서명 생성 (HMAC-SHA256)
        signature = hmac.new(
            self.certification_key.encode('utf-8'),
            param_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    async def get_goods_info(
        self,
        goods_code: str,
        response_type: str = "JSON"
    ) -> Optional[Dict[str, Any]]:
        """
        상품 정보 조회 (GetGoodsInfo API)
        
        Args:
            goods_code: 상품 코드
            response_type: 응답 형식 (JSON 또는 XML)
            
        Returns:
            상품 정보 딕셔너리 또는 None
        """
        if not self.certification_key:
            logger.warning("Qoo10 API Key가 없어 API 호출을 건너뜁니다.")
            return None
        
        try:
            # API 파라미터 구성
            parameters = {
                "key": self.certification_key,
                "method": "GetGoodsInfo",
                "goodsCode": goods_code,
                "responseType": response_type
            }
            
            # 서명 생성
            signature = self._generate_signature(parameters)
            parameters["signature"] = signature
            
            # API 요청
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.API_BASE_URL,
                    params=parameters
                )
                response.raise_for_status()
                
                if response_type.upper() == "JSON":
                    data = response.json()
                else:
                    # XML 파싱 (필요시)
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(response.text)
                    data = self._parse_xml_response(root)
                
                # API 응답 검증
                if data.get("ResultCode") == "0":
                    return data.get("ResultObject", {})
                else:
                    error_msg = data.get("ResultMessage", "Unknown error")
                    logger.error(f"Qoo10 API 오류: {error_msg}")
                    return None
                    
        except httpx.HTTPError as e:
            logger.error(f"Qoo10 API HTTP 오류: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Qoo10 API 오류: {str(e)}", exc_info=True)
            return None
    
    def _parse_xml_response(self, root) -> Dict[str, Any]:
        """XML 응답을 딕셔너리로 변환"""
        result = {}
        for child in root:
            if len(child) == 0:
                result[child.tag] = child.text
            else:
                result[child.tag] = self._parse_xml_response(child)
        return result
    
    def normalize_api_data_to_crawler_format(
        self,
        api_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        API 데이터를 크롤러 형식으로 정규화
        
        Args:
            api_data: Qoo10 API 응답 데이터
            
        Returns:
            크롤러 형식의 상품 데이터
        """
        normalized = {
            "product_name": api_data.get("GoodsName", ""),
            "product_code": api_data.get("GoodsCode", ""),
            "category": api_data.get("CategoryName", ""),
            "brand": api_data.get("BrandName", ""),
            "price": {
                "sale_price": self._parse_price_value(api_data.get("SalePrice", 0)),
                "original_price": self._parse_price_value(api_data.get("OriginalPrice", 0)),
                "discount_rate": self._calculate_discount_rate(
                    api_data.get("OriginalPrice", 0),
                    api_data.get("SalePrice", 0)
                )
            },
            "reviews": {
                "review_count": api_data.get("ReviewCount", 0),
                "rating": api_data.get("Rating", 0.0)
            },
            "images": {
                "thumbnail": api_data.get("ImageUrl", ""),
                "detail_images": self._extract_detail_images(api_data)
            },
            "description": api_data.get("Description", ""),
            "qpoint_info": self._extract_qpoint_info(api_data),
            "coupon_info": self._extract_coupon_info(api_data),
            "shipping_info": self._extract_shipping_info(api_data),
            "crawled_with": "qoo10_api",  # 데이터 소스 표시
            "api_timestamp": datetime.now().isoformat()
        }
        
        return normalized
    
    def _parse_price_value(self, value: Any) -> Optional[int]:
        """가격 값을 정수로 변환"""
        if value is None:
            return None
        try:
            price = int(float(str(value).replace(",", "")))
            # 유효성 검증 (100~1,000,000엔)
            if 100 <= price <= 1000000:
                return price
            return None
        except (ValueError, TypeError):
            return None
    
    def _calculate_discount_rate(
        self,
        original_price: Any,
        sale_price: Any
    ) -> int:
        """할인율 계산"""
        try:
            original = float(str(original_price).replace(",", ""))
            sale = float(str(sale_price).replace(",", ""))
            if original > sale and original > 0:
                return int((original - sale) / original * 100)
            return 0
        except (ValueError, TypeError):
            return 0
    
    def _extract_detail_images(self, api_data: Dict[str, Any]) -> List[str]:
        """상세 이미지 목록 추출"""
        images = []
        
        # ImageUrlList 또는 DetailImages 필드 확인
        if "ImageUrlList" in api_data:
            if isinstance(api_data["ImageUrlList"], list):
                images = api_data["ImageUrlList"]
            elif isinstance(api_data["ImageUrlList"], str):
                images = [img.strip() for img in api_data["ImageUrlList"].split(",") if img.strip()]
        
        if "DetailImages" in api_data:
            if isinstance(api_data["DetailImages"], list):
                images.extend(api_data["DetailImages"])
            elif isinstance(api_data["DetailImages"], str):
                images.extend([img.strip() for img in api_data["DetailImages"].split(",") if img.strip()])
        
        # 중복 제거
        return list(dict.fromkeys(images))
    
    def _extract_qpoint_info(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Qポイント 정보 추출"""
        qpoint_info = {}
        
        if "QPointInfo" in api_data:
            qpoint_data = api_data["QPointInfo"]
            if isinstance(qpoint_data, dict):
                qpoint_info = {
                    "max_points": qpoint_data.get("MaxPoints", 0),
                    "receive_confirmation_points": qpoint_data.get("ReceiveConfirmationPoints", 0),
                    "review_points": qpoint_data.get("ReviewPoints", 0),
                    "auto_points": qpoint_data.get("AutoPoints", 0)
                }
        
        return qpoint_info if any(qpoint_info.values()) else {}
    
    def _extract_coupon_info(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """쿠폰 정보 추출"""
        coupon_info = {
            "has_coupon": False,
            "coupon_type": None,
            "max_discount": None
        }
        
        if "CouponInfo" in api_data:
            coupon_data = api_data["CouponInfo"]
            if isinstance(coupon_data, dict):
                coupon_info["has_coupon"] = coupon_data.get("HasCoupon", False)
                coupon_info["coupon_type"] = coupon_data.get("CouponType", "auto")
                coupon_info["max_discount"] = coupon_data.get("MaxDiscount", None)
        
        return coupon_info
    
    def _extract_shipping_info(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """배송 정보 추출"""
        shipping_info = {
            "free_shipping": False,
            "shipping_fee": None,
            "return_policy": None
        }
        
        if "ShippingInfo" in api_data:
            shipping_data = api_data["ShippingInfo"]
            if isinstance(shipping_data, dict):
                shipping_info["free_shipping"] = shipping_data.get("FreeShipping", False)
                shipping_info["shipping_fee"] = shipping_data.get("ShippingFee", None)
                shipping_info["return_policy"] = shipping_data.get("ReturnPolicy", None)
        
        return shipping_info
    
    async def fetch_product_data(
        self,
        product_code: str,
        use_api: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        상품 데이터 조회 (API 우선, 실패 시 None 반환)
        
        Args:
            product_code: 상품 코드
            use_api: API 사용 여부
            
        Returns:
            정규화된 상품 데이터 또는 None
        """
        if not use_api or not self.certification_key:
            return None
        
        api_data = await self.get_goods_info(product_code)
        if api_data:
            return self.normalize_api_data_to_crawler_format(api_data)
        
        return None
