"""
Qoo10 API 데이터 스키마 정의
API 문서의 데이터 인덱스를 기반으로 크롤러 데이터 구조를 정규화하고 검증합니다.
API Key 없이도 API 구조를 참고하여 데이터 일치 여부 정확성을 높입니다.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class FieldType(Enum):
    """필드 타입"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


@dataclass
class FieldDefinition:
    """필드 정의"""
    name: str
    api_field: str  # API 응답의 필드명
    crawler_field: str  # 크롤러에서 사용하는 필드명
    field_type: FieldType
    required: bool = False
    default_value: Any = None
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    nested_fields: List['FieldDefinition'] = field(default_factory=list)


class Qoo10APISchema:
    """Qoo10 API 데이터 스키마"""
    
    # API 응답 필드와 크롤러 필드 매핑
    FIELD_MAPPING = {
        # 기본 정보
        "GoodsName": "product_name",
        "GoodsCode": "product_code",
        "CategoryName": "category",
        "BrandName": "brand",
        
        # 가격 정보
        "SalePrice": "price.sale_price",
        "OriginalPrice": "price.original_price",
        "DiscountRate": "price.discount_rate",
        
        # 리뷰 정보
        "ReviewCount": "reviews.review_count",
        "Rating": "reviews.rating",
        
        # 이미지 정보
        "ImageUrl": "images.thumbnail",
        "ImageUrlList": "images.detail_images",
        "DetailImages": "images.detail_images",
        
        # 설명
        "Description": "description",
        
        # Qポイント 정보
        "QPointInfo.MaxPoints": "qpoint_info.max_points",
        "QPointInfo.ReceiveConfirmationPoints": "qpoint_info.receive_confirmation_points",
        "QPointInfo.ReviewPoints": "qpoint_info.review_points",
        "QPointInfo.AutoPoints": "qpoint_info.auto_points",
        
        # 쿠폰 정보
        "CouponInfo.HasCoupon": "coupon_info.has_coupon",
        "CouponInfo.CouponType": "coupon_info.coupon_type",
        "CouponInfo.MaxDiscount": "coupon_info.max_discount",
        
        # 배송 정보
        "ShippingInfo.FreeShipping": "shipping_info.free_shipping",
        "ShippingInfo.ShippingFee": "shipping_info.shipping_fee",
        "ShippingInfo.ReturnPolicy": "shipping_info.return_policy",
    }
    
    # 필드 정의 (API 구조 기반)
    FIELD_DEFINITIONS = [
        # 기본 정보
        FieldDefinition(
            name="product_name",
            api_field="GoodsName",
            crawler_field="product_name",
            field_type=FieldType.STRING,
            required=True,
            validation_rules={"min_length": 1, "max_length": 500}
        ),
        FieldDefinition(
            name="product_code",
            api_field="GoodsCode",
            crawler_field="product_code",
            field_type=FieldType.STRING,
            required=True,
            validation_rules={"pattern": r"^\d+$"}
        ),
        FieldDefinition(
            name="category",
            api_field="CategoryName",
            crawler_field="category",
            field_type=FieldType.STRING,
            required=False
        ),
        FieldDefinition(
            name="brand",
            api_field="BrandName",
            crawler_field="brand",
            field_type=FieldType.STRING,
            required=False
        ),
        
        # 가격 정보
        FieldDefinition(
            name="sale_price",
            api_field="SalePrice",
            crawler_field="price.sale_price",
            field_type=FieldType.INTEGER,
            required=True,
            validation_rules={"min": 100, "max": 1000000}
        ),
        FieldDefinition(
            name="original_price",
            api_field="OriginalPrice",
            crawler_field="price.original_price",
            field_type=FieldType.INTEGER,
            required=False,
            validation_rules={"min": 100, "max": 1000000}
        ),
        FieldDefinition(
            name="discount_rate",
            api_field="DiscountRate",
            crawler_field="price.discount_rate",
            field_type=FieldType.INTEGER,
            required=False,
            validation_rules={"min": 0, "max": 100}
        ),
        
        # 리뷰 정보
        FieldDefinition(
            name="review_count",
            api_field="ReviewCount",
            crawler_field="reviews.review_count",
            field_type=FieldType.INTEGER,
            required=False,
            validation_rules={"min": 0}
        ),
        FieldDefinition(
            name="rating",
            api_field="Rating",
            crawler_field="reviews.rating",
            field_type=FieldType.FLOAT,
            required=False,
            validation_rules={"min": 0.0, "max": 5.0}
        ),
        
        # 이미지 정보
        FieldDefinition(
            name="thumbnail",
            api_field="ImageUrl",
            crawler_field="images.thumbnail",
            field_type=FieldType.STRING,
            required=False,
            validation_rules={"pattern": r"^https?://"}
        ),
        FieldDefinition(
            name="detail_images",
            api_field="ImageUrlList",
            crawler_field="images.detail_images",
            field_type=FieldType.ARRAY,
            required=False
        ),
        
        # 설명
        FieldDefinition(
            name="description",
            api_field="Description",
            crawler_field="description",
            field_type=FieldType.STRING,
            required=False
        ),
        
        # Qポイント 정보
        FieldDefinition(
            name="qpoint_max_points",
            api_field="QPointInfo.MaxPoints",
            crawler_field="qpoint_info.max_points",
            field_type=FieldType.INTEGER,
            required=False,
            validation_rules={"min": 0}
        ),
        FieldDefinition(
            name="qpoint_receive_confirmation",
            api_field="QPointInfo.ReceiveConfirmationPoints",
            crawler_field="qpoint_info.receive_confirmation_points",
            field_type=FieldType.INTEGER,
            required=False,
            validation_rules={"min": 0}
        ),
        FieldDefinition(
            name="qpoint_review",
            api_field="QPointInfo.ReviewPoints",
            crawler_field="qpoint_info.review_points",
            field_type=FieldType.INTEGER,
            required=False,
            validation_rules={"min": 0}
        ),
        FieldDefinition(
            name="qpoint_auto",
            api_field="QPointInfo.AutoPoints",
            crawler_field="qpoint_info.auto_points",
            field_type=FieldType.INTEGER,
            required=False,
            validation_rules={"min": 0}
        ),
        
        # 쿠폰 정보
        FieldDefinition(
            name="coupon_has_coupon",
            api_field="CouponInfo.HasCoupon",
            crawler_field="coupon_info.has_coupon",
            field_type=FieldType.BOOLEAN,
            required=False
        ),
        FieldDefinition(
            name="coupon_type",
            api_field="CouponInfo.CouponType",
            crawler_field="coupon_info.coupon_type",
            field_type=FieldType.STRING,
            required=False
        ),
        FieldDefinition(
            name="coupon_max_discount",
            api_field="CouponInfo.MaxDiscount",
            crawler_field="coupon_info.max_discount",
            field_type=FieldType.INTEGER,
            required=False,
            validation_rules={"min": 0}
        ),
        
        # 배송 정보
        FieldDefinition(
            name="shipping_free_shipping",
            api_field="ShippingInfo.FreeShipping",
            crawler_field="shipping_info.free_shipping",
            field_type=FieldType.BOOLEAN,
            required=False
        ),
        FieldDefinition(
            name="shipping_fee",
            api_field="ShippingInfo.ShippingFee",
            crawler_field="shipping_info.shipping_fee",
            field_type=FieldType.INTEGER,
            required=False,
            validation_rules={"min": 0}
        ),
        FieldDefinition(
            name="shipping_return_policy",
            api_field="ShippingInfo.ReturnPolicy",
            crawler_field="shipping_info.return_policy",
            field_type=FieldType.STRING,
            required=False
        ),
    ]
    
    @classmethod
    def normalize_crawler_data_to_api_structure(
        cls,
        crawler_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        크롤러 데이터를 API 구조에 맞게 정규화
        
        Args:
            crawler_data: 크롤러가 추출한 데이터
            
        Returns:
            API 구조에 맞게 정규화된 데이터
        """
        normalized = {}
        
        for field_def in cls.FIELD_DEFINITIONS:
            # 크롤러 필드 경로 파싱 (예: "price.sale_price")
            crawler_path = field_def.crawler_field.split(".")
            value = crawler_data
            
            # 중첩된 필드 접근
            try:
                for key in crawler_path:
                    if isinstance(value, dict):
                        value = value.get(key)
                    else:
                        value = None
                        break
            except (TypeError, AttributeError):
                value = None
            
            # 값이 없으면 기본값 사용
            if value is None:
                value = field_def.default_value
            
            # 타입 변환
            value = cls._convert_type(value, field_def.field_type)
            
            # 검증
            if value is not None:
                validation_result = cls._validate_field(value, field_def)
                if not validation_result["valid"]:
                    # 검증 실패 시 None 또는 기본값 사용
                    value = field_def.default_value
            
            # API 필드 경로에 값 설정
            api_path = field_def.api_field.split(".")
            cls._set_nested_value(normalized, api_path, value)
        
        return normalized
    
    @classmethod
    def _convert_type(cls, value: Any, field_type: FieldType) -> Any:
        """값을 지정된 타입으로 변환"""
        if value is None:
            return None
        
        try:
            if field_type == FieldType.STRING:
                return str(value)
            elif field_type == FieldType.INTEGER:
                return int(float(str(value).replace(",", "")))
            elif field_type == FieldType.FLOAT:
                return float(str(value).replace(",", ""))
            elif field_type == FieldType.BOOLEAN:
                if isinstance(value, bool):
                    return value
                return str(value).lower() in ("true", "1", "yes", "on")
            elif field_type == FieldType.ARRAY:
                if isinstance(value, list):
                    return value
                elif isinstance(value, str):
                    return [item.strip() for item in value.split(",") if item.strip()]
                else:
                    return [value] if value else []
            else:
                return value
        except (ValueError, TypeError):
            return None
    
    @classmethod
    def _validate_field(cls, value: Any, field_def: FieldDefinition) -> Dict[str, Any]:
        """필드 값 검증"""
        rules = field_def.validation_rules
        errors = []
        
        if field_def.field_type == FieldType.STRING:
            if "min_length" in rules and len(str(value)) < rules["min_length"]:
                errors.append(f"최소 길이 {rules['min_length']} 미만")
            if "max_length" in rules and len(str(value)) > rules["max_length"]:
                errors.append(f"최대 길이 {rules['max_length']} 초과")
            if "pattern" in rules:
                import re
                if not re.match(rules["pattern"], str(value)):
                    errors.append(f"패턴 불일치: {rules['pattern']}")
        
        elif field_def.field_type == FieldType.INTEGER:
            if "min" in rules and value < rules["min"]:
                errors.append(f"최소값 {rules['min']} 미만")
            if "max" in rules and value > rules["max"]:
                errors.append(f"최대값 {rules['max']} 초과")
        
        elif field_def.field_type == FieldType.FLOAT:
            if "min" in rules and value < rules["min"]:
                errors.append(f"최소값 {rules['min']} 미만")
            if "max" in rules and value > rules["max"]:
                errors.append(f"최대값 {rules['max']} 초과")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    @classmethod
    def _set_nested_value(cls, data: Dict[str, Any], path: List[str], value: Any):
        """중첩된 딕셔너리에 값 설정"""
        current = data
        for i, key in enumerate(path[:-1]):
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    @classmethod
    def compare_structures(
        cls,
        crawler_data: Dict[str, Any],
        expected_structure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        크롤러 데이터와 예상 구조 비교
        
        Args:
            crawler_data: 크롤러 데이터
            expected_structure: 예상 구조 (API 구조 기반)
            
        Returns:
            비교 결과
        """
        normalized_crawler = cls.normalize_crawler_data_to_api_structure(crawler_data)
        
        comparison_result = {
            "missing_fields": [],
            "extra_fields": [],
            "type_mismatches": [],
            "value_mismatches": [],
            "structure_match": True
        }
        
        # 누락된 필드 확인
        def check_fields(expected: Dict, actual: Dict, path: str = ""):
            for key, expected_value in expected.items():
                current_path = f"{path}.{key}" if path else key
                
                if key not in actual:
                    comparison_result["missing_fields"].append(current_path)
                    comparison_result["structure_match"] = False
                elif isinstance(expected_value, dict) and isinstance(actual[key], dict):
                    check_fields(expected_value, actual[key], current_path)
                elif isinstance(expected_value, list) and isinstance(actual[key], list):
                    # 배열은 길이만 확인
                    if len(expected_value) != len(actual[key]):
                        comparison_result["value_mismatches"].append({
                            "field": current_path,
                            "expected": len(expected_value),
                            "actual": len(actual[key])
                        })
        
        check_fields(expected_structure, normalized_crawler)
        
        # 추가 필드 확인
        def check_extra_fields(expected: Dict, actual: Dict, path: str = ""):
            for key, actual_value in actual.items():
                current_path = f"{path}.{key}" if path else key
                
                if key not in expected:
                    comparison_result["extra_fields"].append(current_path)
                elif isinstance(actual_value, dict) and isinstance(expected.get(key), dict):
                    check_extra_fields(expected[key], actual_value, current_path)
        
        check_extra_fields(expected_structure, normalized_crawler)
        
        return comparison_result
    
    @classmethod
    def get_expected_structure(cls) -> Dict[str, Any]:
        """예상 데이터 구조 반환 (API 구조 기반)"""
        structure = {}
        
        for field_def in cls.FIELD_DEFINITIONS:
            api_path = field_def.api_field.split(".")
            default_value = field_def.default_value
            
            # 타입에 따른 기본값 설정
            if default_value is None:
                if field_def.field_type == FieldType.STRING:
                    default_value = ""
                elif field_def.field_type == FieldType.INTEGER:
                    default_value = 0
                elif field_def.field_type == FieldType.FLOAT:
                    default_value = 0.0
                elif field_def.field_type == FieldType.BOOLEAN:
                    default_value = False
                elif field_def.field_type == FieldType.ARRAY:
                    default_value = []
                elif field_def.field_type == FieldType.OBJECT:
                    default_value = {}
            
            cls._set_nested_value(structure, api_path, default_value)
        
        return structure
