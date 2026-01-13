"""
Shop 분석 서비스
Qoo10 Shop 페이지를 분석하여 Shop 레벨, 카테고리, 경쟁사 정보 등을 제공합니다.
"""
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
import re


class ShopAnalyzer:
    """Shop 분석기"""
    
    def __init__(self):
        pass
    
    async def analyze(self, shop_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Shop 데이터 종합 분석 (Shop 특수성 고려)
        
        Args:
            shop_data: 크롤러에서 수집한 Shop 데이터
            
        Returns:
            분석 결과 딕셔너리
        """
        # Shop 특수성 분석 (우선 수행)
        shop_specialty = self._analyze_shop_specialty(shop_data)
        
        analysis_result = {
            "overall_score": 0,
            "shop_info": self._analyze_shop_info(shop_data),
            "product_analysis": self._analyze_products(shop_data),
            "category_analysis": self._analyze_categories(shop_data),
            "competitor_analysis": self._analyze_competitors(shop_data),
            "level_analysis": self._analyze_shop_level(shop_data),
            "shop_specialty": shop_specialty,  # Shop 특수성 분석 추가
            "product_type_analysis": self._analyze_product_types(shop_data),  # 상품 종류 분석 추가
            "customized_insights": self._generate_customized_insights(shop_data, shop_specialty)  # 독자적 인사이트
        }
        
        # Shop 특수성을 반영한 종합 점수 계산
        analysis_result["overall_score"] = self._calculate_overall_score(analysis_result, shop_specialty)
        
        return analysis_result
    
    def _analyze_shop_info(self, shop_data: Dict[str, Any]) -> Dict[str, Any]:
        """Shop 기본 정보 분석"""
        analysis = {
            "shop_name": shop_data.get("shop_name", ""),
            "shop_id": shop_data.get("shop_id", ""),
            "shop_level": shop_data.get("shop_level", "unknown"),
            "follower_count": shop_data.get("follower_count", 0),
            "product_count": shop_data.get("product_count", 0),
            "score": 0
        }
        
        # Shop 레벨 평가
        level_scores = {
            "power": 100,
            "excellent": 70,
            "normal": 40,
            "unknown": 0
        }
        analysis["score"] = level_scores.get(analysis["shop_level"].lower(), 0)
        
        # 팔로워 수 평가
        if analysis["follower_count"] >= 50000:
            analysis["score"] += 30
        elif analysis["follower_count"] >= 10000:
            analysis["score"] += 20
        elif analysis["follower_count"] >= 1000:
            analysis["score"] += 10
        
        # 상품 수 평가
        if analysis["product_count"] >= 100:
            analysis["score"] += 20
        elif analysis["product_count"] >= 50:
            analysis["score"] += 15
        elif analysis["product_count"] >= 20:
            analysis["score"] += 10
        
        analysis["score"] = min(100, analysis["score"])
        
        return analysis
    
    def _analyze_products(self, shop_data: Dict[str, Any]) -> Dict[str, Any]:
        """Shop 상품 분석"""
        products = shop_data.get("products", [])
        
        analysis = {
            "total_products": len(products),
            "average_rating": 0.0,
            "total_reviews": 0,
            "price_range": {"min": None, "max": None},
            "score": 0
        }
        
        if not products:
            return analysis
        
        # 평균 평점 계산
        ratings = [p.get("rating", 0) for p in products if p.get("rating")]
        if ratings:
            analysis["average_rating"] = sum(ratings) / len(ratings)
        
        # 총 리뷰 수
        analysis["total_reviews"] = sum(p.get("review_count", 0) for p in products)
        
        # 가격 범위
        prices = [p.get("price", {}).get("sale_price") for p in products if p.get("price", {}).get("sale_price")]
        if prices:
            analysis["price_range"]["min"] = min(prices)
            analysis["price_range"]["max"] = max(prices)
        
        # 점수 계산
        if analysis["average_rating"] >= 4.5:
            analysis["score"] += 40
        elif analysis["average_rating"] >= 4.0:
            analysis["score"] += 30
        elif analysis["average_rating"] >= 3.5:
            analysis["score"] += 20
        
        if analysis["total_reviews"] >= 1000:
            analysis["score"] += 30
        elif analysis["total_reviews"] >= 500:
            analysis["score"] += 20
        elif analysis["total_reviews"] >= 100:
            analysis["score"] += 10
        
        if analysis["total_products"] >= 50:
            analysis["score"] += 30
        elif analysis["total_products"] >= 20:
            analysis["score"] += 20
        
        analysis["score"] = min(100, analysis["score"])
        
        return analysis
    
    def _analyze_categories(self, shop_data: Dict[str, Any]) -> Dict[str, Any]:
        """카테고리 분석"""
        categories = shop_data.get("categories", {})
        
        analysis = {
            "main_category": None,
            "category_distribution": categories,
            "category_count": len(categories),
            "score": 0
        }
        
        if categories:
            # 가장 많은 상품이 있는 카테고리 찾기
            main_category = max(categories.items(), key=lambda x: x[1])
            analysis["main_category"] = main_category[0]
            analysis["score"] = min(100, len(categories) * 10)
        
        return analysis
    
    def _analyze_competitors(self, shop_data: Dict[str, Any]) -> Dict[str, Any]:
        """경쟁사 분석 (강화 버전)"""
        analysis = {
            "score": 70,  # 기본 점수
            "main_category": None,
            "category_competition": {},
            "recommendations": []
        }
        
        # 주요 카테고리 확인
        categories = shop_data.get("categories", {})
        products = shop_data.get("products", [])
        
        if categories:
            main_category = max(categories.items(), key=lambda x: x[1])
            analysis["main_category"] = main_category[0]
            
            # 카테고리별 경쟁 강도 분석
            # 전체 상품 데이터를 기반으로 카테고리별 경쟁 지표 계산
            analysis["category_competition"] = self._calculate_category_competition(
                categories, products
            )
            
            # 카테고리별 경쟁 점수 기반으로 전체 점수 조정
            if analysis["category_competition"]:
                avg_competition_score = sum(
                    cat_data.get("competition_score", 0)
                    for cat_data in analysis["category_competition"].values()
                ) / len(analysis["category_competition"])
                
                if avg_competition_score >= 70:
                    analysis["score"] += 20
                    analysis["recommendations"].append("카테고리별 경쟁력이 우수합니다")
                elif avg_competition_score >= 50:
                    analysis["score"] += 10
                    analysis["recommendations"].append("카테고리별 경쟁력 향상 여지가 있습니다")
                else:
                    analysis["recommendations"].append("카테고리별 경쟁력 강화가 필요합니다")
            
            # 상품 수 기반 추천
            product_count = shop_data.get("product_count", 0)
            if product_count >= 50:
                analysis["score"] += 20
                analysis["recommendations"].append("상품 라인업이 충분합니다")
            elif product_count >= 20:
                analysis["score"] += 10
                analysis["recommendations"].append("상품 수를 더 늘리면 경쟁력이 향상됩니다")
            else:
                analysis["recommendations"].append("상품 라인업 확대가 필요합니다")
        
        analysis["score"] = min(100, analysis["score"])
        
        return analysis
    
    def _calculate_category_competition(
        self, 
        categories: Dict[str, int], 
        products: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        카테고리별 경쟁 지표 계산
        
        Args:
            categories: 카테고리 이름 -> 상품 수 매핑
            products: 상품 리스트
            
        Returns:
            카테고리별 경쟁 지표 딕셔너리
        """
        category_competition = {}
        
        if not categories or not products:
            return category_competition
        
        # 전체 상품 통계 계산
        all_prices = [
            p.get("price", {}).get("sale_price") 
            for p in products 
            if p.get("price", {}).get("sale_price")
        ]
        all_ratings = [p.get("rating", 0) for p in products if p.get("rating", 0) > 0]
        all_reviews = [p.get("review_count", 0) for p in products]
        
        avg_price = sum(all_prices) / len(all_prices) if all_prices else 0
        avg_rating = sum(all_ratings) / len(all_ratings) if all_ratings else 0
        avg_reviews = sum(all_reviews) / len(all_reviews) if all_reviews else 0
        
        # 각 카테고리에 대해 경쟁 지표 계산
        total_products = len(products)
        
        for category_name, category_product_count in categories.items():
            # 카테고리별 상품 수 비율
            category_ratio = category_product_count / total_products if total_products > 0 else 0
            
            # 카테고리별 경쟁 지표 계산
            # 실제로는 각 상품의 카테고리를 알 수 없으므로,
            # 전체 상품 통계를 기반으로 추정하고 카테고리별 상품 수를 반영
            num_products = category_product_count
            num_unique_sellers = 1  # 현재 Shop의 상품이므로 1
            avg_price_category = avg_price  # 전체 평균 가격 사용
            avg_rating_category = avg_rating  # 전체 평균 평점 사용
            avg_reviews_category = avg_reviews  # 전체 평균 리뷰 수 사용
            
            # 경쟁 점수 계산 (0-100)
            competition_score = 0
            
            # 상품 수 기반 점수 (최대 30점)
            if num_products >= 20:
                competition_score += 30
            elif num_products >= 10:
                competition_score += 20
            elif num_products >= 5:
                competition_score += 10
            
            # 평점 기반 점수 (최대 30점)
            if avg_rating_category >= 4.5:
                competition_score += 30
            elif avg_rating_category >= 4.0:
                competition_score += 20
            elif avg_rating_category >= 3.5:
                competition_score += 10
            
            # 리뷰 수 기반 점수 (최대 20점)
            if avg_reviews_category >= 100:
                competition_score += 20
            elif avg_reviews_category >= 50:
                competition_score += 15
            elif avg_reviews_category >= 20:
                competition_score += 10
            
            # 카테고리 비율 기반 점수 (최대 20점)
            if category_ratio >= 0.5:
                competition_score += 20  # 주요 카테고리
            elif category_ratio >= 0.3:
                competition_score += 15
            elif category_ratio >= 0.1:
                competition_score += 10
            
            competition_score = min(100, competition_score)
            
            category_competition[category_name] = {
                "num_products": num_products,
                "num_unique_sellers": num_unique_sellers,
                "avg_price": round(avg_price_category, 2) if avg_price_category else None,
                "avg_rating": round(avg_rating_category, 2) if avg_rating_category else 0.0,
                "avg_reviews": round(avg_reviews_category, 2) if avg_reviews_category else 0.0,
                "competition_score": competition_score,
                "category_ratio": round(category_ratio, 3)
            }
        
        return category_competition
    
    def _analyze_shop_level(self, shop_data: Dict[str, Any]) -> Dict[str, Any]:
        """Shop 레벨 분석"""
        current_level = shop_data.get("shop_level", "normal").lower()
        analysis = {
            "current_level": current_level,
            "settlement_leadtime": self._get_settlement_leadtime(current_level),
            "target_level": self._get_target_level(current_level),
            "requirements": [],
            "recommendations": []
        }
        
        # 레벨별 정산 리드타임
        if current_level == "power":
            analysis["recommendations"].append("파워 셀러 레벨 유지")
        elif current_level == "excellent":
            analysis["requirements"] = ["월 매출 500만엔 이상", "평점 4.7 이상"]
            analysis["recommendations"].append("파워 셀러 레벨 달성을 위해 매출 및 평점 향상 필요")
        else:
            analysis["requirements"] = ["월 매출 100만엔 이상", "평점 4.5 이상"]
            analysis["recommendations"].append("우수 셀러 레벨 달성을 위해 매출 및 평점 향상 필요")
        
        return analysis
    
    def _get_settlement_leadtime(self, level: str) -> int:
        """레벨별 정산 리드타임 (일)"""
        leadtimes = {
            "power": 5,
            "excellent": 10,
            "normal": 15
        }
        return leadtimes.get(level, 15)
    
    def _get_target_level(self, current_level: str) -> str:
        """다음 목표 레벨"""
        if current_level == "normal":
            return "excellent"
        elif current_level == "excellent":
            return "power"
        else:
            return "maintain"
    
    def _analyze_shop_specialty(self, shop_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Shop 특수성 분석
        - 브랜드 샵 여부
        - 제품 라인업 특성
        - 타겟 고객층
        - Shop의 독특한 특징
        """
        shop_name = shop_data.get("shop_name", "").lower()
        shop_id = shop_data.get("shop_id", "").lower()
        products = shop_data.get("products", [])
        
        specialty = {
            "is_brand_shop": False,
            "brand_name": None,
            "product_lineup_type": "mixed",  # specialized, mixed, diverse
            "target_customer": "general",
            "unique_features": [],
            "specialty_score": 0
        }
        
        # 브랜드 샵 여부 판단
        # "公式", "official", "공식" 등의 키워드 확인
        official_keywords = ["公式", "official", "공식", "オフィシャル"]
        if any(keyword in shop_name or keyword in shop_id for keyword in official_keywords):
            specialty["is_brand_shop"] = True
            # 브랜드명 추출
            if "公式" in shop_name or "official" in shop_name:
                brand_name = shop_name.replace("公式", "").replace("official", "").strip()
                specialty["brand_name"] = brand_name if brand_name else shop_id
        
        # 제품 라인업 특성 분석
        product_types = {}
        for product in products:
            product_type = product.get("product_type")
            if product_type:
                product_types[product_type] = product_types.get(product_type, 0) + 1
        
        if product_types:
            total_products = len(products)
            max_type_count = max(product_types.values())
            max_type_ratio = max_type_count / total_products if total_products > 0 else 0
            
            if max_type_ratio >= 0.6:
                specialty["product_lineup_type"] = "specialized"  # 특화된 제품 라인업
                specialty["main_product_type"] = max(product_types.items(), key=lambda x: x[1])[0]
            elif max_type_ratio >= 0.3:
                specialty["product_lineup_type"] = "mixed"  # 혼합형
            else:
                specialty["product_lineup_type"] = "diverse"  # 다양형
            
            specialty["product_type_distribution"] = product_types
        
        # 타겟 고객층 분석
        # 상품명과 키워드를 기반으로 타겟 고객층 추정
        all_keywords = []
        for product in products:
            keywords = product.get("keywords", [])
            all_keywords.extend(keywords)
        
        keyword_text = " ".join(all_keywords).lower()
        
        if any(kw in keyword_text for kw in ["敏感", "敏感肌", "sensitive", "乾燥", "dry"]):
            specialty["target_customer"] = "sensitive_skin"
        elif any(kw in keyword_text for kw in ["毛穴", "pore", "ニキビ", "acne"]):
            specialty["target_customer"] = "problem_skin"
        elif any(kw in keyword_text for kw in ["アンチエイジング", "anti-aging", "抗老化"]):
            specialty["target_customer"] = "anti_aging"
        elif any(kw in keyword_text for kw in ["保湿", "moisture", "hydrating"]):
            specialty["target_customer"] = "dry_skin"
        
        # 독특한 특징 추출
        unique_features = []
        
        # POWER 레벨이 높은 경우
        if shop_data.get("shop_level", "").lower() == "power":
            unique_features.append("POWER 셀러 레벨")
        
        # 팔로워가 많은 경우
        if shop_data.get("follower_count", 0) >= 50000:
            unique_features.append("대규모 팔로워 보유")
        
        # 쿠폰 제공 여부
        coupons = shop_data.get("coupons", [])
        if coupons:
            unique_features.append(f"{len(coupons)}종의 쿠폰 제공")
        
        # 특화된 제품 라인업
        if specialty["product_lineup_type"] == "specialized":
            unique_features.append(f"{specialty.get('main_product_type', '특화')} 제품 특화")
        
        specialty["unique_features"] = unique_features
        
        # 특수성 점수 계산
        score = 0
        if specialty["is_brand_shop"]:
            score += 30
        if specialty["product_lineup_type"] == "specialized":
            score += 25
        elif specialty["product_lineup_type"] == "mixed":
            score += 15
        if len(unique_features) >= 3:
            score += 25
        elif len(unique_features) >= 2:
            score += 15
        elif len(unique_features) >= 1:
            score += 10
        
        specialty["specialty_score"] = min(100, score)
        
        return specialty
    
    def _analyze_product_types(self, shop_data: Dict[str, Any]) -> Dict[str, Any]:
        """상품 종류별 상세 분석"""
        products = shop_data.get("products", [])
        
        analysis = {
            "product_type_distribution": {},
            "type_performance": {},
            "recommended_types": [],
            "underrepresented_types": [],
            "score": 0
        }
        
        if not products:
            return analysis
        
        # 상품 종류별 통계
        type_stats = {}
        for product in products:
            product_type = product.get("product_type", "기타")
            
            if product_type not in type_stats:
                type_stats[product_type] = {
                    "count": 0,
                    "total_rating": 0.0,
                    "rating_count": 0,
                    "total_reviews": 0,
                    "avg_price": 0.0,
                    "price_count": 0
                }
            
            stats = type_stats[product_type]
            stats["count"] += 1
            
            # 평점 집계
            rating = product.get("rating", 0)
            if rating > 0:
                stats["total_rating"] += rating
                stats["rating_count"] += 1
            
            # 리뷰 수 집계
            review_count = product.get("review_count", 0)
            stats["total_reviews"] += review_count
            
            # 가격 집계
            price = product.get("price", {}).get("sale_price")
            if price:
                stats["avg_price"] += price
                stats["price_count"] += 1
        
        # 상품 종류별 성과 계산
        for product_type, stats in type_stats.items():
            avg_rating = stats["total_rating"] / stats["rating_count"] if stats["rating_count"] > 0 else 0
            avg_price = stats["avg_price"] / stats["price_count"] if stats["price_count"] > 0 else 0
            
            # 성과 점수 계산
            performance_score = 0
            if avg_rating >= 4.5:
                performance_score += 40
            elif avg_rating >= 4.0:
                performance_score += 30
            elif avg_rating >= 3.5:
                performance_score += 20
            
            if stats["total_reviews"] >= 100:
                performance_score += 30
            elif stats["total_reviews"] >= 50:
                performance_score += 20
            elif stats["total_reviews"] >= 20:
                performance_score += 10
            
            if stats["count"] >= 5:
                performance_score += 30
            elif stats["count"] >= 3:
                performance_score += 20
            
            analysis["product_type_distribution"][product_type] = stats["count"]
            analysis["type_performance"][product_type] = {
                "count": stats["count"],
                "avg_rating": round(avg_rating, 2),
                "total_reviews": stats["total_reviews"],
                "avg_price": round(avg_price, 0) if avg_price > 0 else None,
                "performance_score": min(100, performance_score)
            }
        
        # 추천 상품 종류 (성과가 좋은 종류)
        sorted_types = sorted(
            analysis["type_performance"].items(),
            key=lambda x: x[1]["performance_score"],
            reverse=True
        )
        analysis["recommended_types"] = [t[0] for t in sorted_types[:3]]
        
        # 부족한 상품 종류 (다양성 확보 필요)
        total_products = len(products)
        for product_type, count in analysis["product_type_distribution"].items():
            ratio = count / total_products if total_products > 0 else 0
            if ratio < 0.1 and count < 2:  # 전체의 10% 미만이고 2개 미만
                analysis["underrepresented_types"].append(product_type)
        
        # 종합 점수
        if analysis["type_performance"]:
            avg_performance = sum(
                perf["performance_score"] 
                for perf in analysis["type_performance"].values()
            ) / len(analysis["type_performance"])
            analysis["score"] = int(avg_performance)
        
        return analysis
    
    def _generate_customized_insights(self, shop_data: Dict[str, Any], shop_specialty: Dict[str, Any]) -> Dict[str, Any]:
        """
        Shop 특수성을 고려한 독자적인 인사이트 생성
        """
        insights = {
            "shop_positioning": "",
            "strengths": [],
            "opportunities": [],
            "recommendations": [],
            "competitive_advantages": [],
            "score": 0
        }
        
        shop_name = shop_data.get("shop_name", "")
        shop_level = shop_data.get("shop_level", "").lower()
        follower_count = shop_data.get("follower_count", 0)
        product_count = shop_data.get("product_count", 0)
        products = shop_data.get("products", [])
        
        # Shop 포지셔닝
        if shop_specialty.get("is_brand_shop"):
            brand_name = shop_specialty.get("brand_name", shop_name)
            insights["shop_positioning"] = f"{brand_name} 공식 브랜드 샵"
        else:
            insights["shop_positioning"] = "일반 판매자 샵"
        
        # 강점 분석
        if shop_level == "power":
            insights["strengths"].append("POWER 셀러 레벨로 높은 신뢰도 보유")
        
        if follower_count >= 50000:
            insights["strengths"].append(f"대규모 팔로워({follower_count:,}명) 보유로 높은 브랜드 인지도")
        elif follower_count >= 10000:
            insights["strengths"].append(f"안정적인 팔로워 기반({follower_count:,}명)")
        
        if shop_specialty.get("product_lineup_type") == "specialized":
            main_type = shop_specialty.get("main_product_type", "")
            insights["strengths"].append(f"{main_type} 제품 특화로 전문성 확보")
        
        # 기회 분석
        if product_count < 20:
            insights["opportunities"].append(f"상품 라인업 확대 (현재 {product_count}개)로 매출 증대 가능")
        
        coupons = shop_data.get("coupons", [])
        if not coupons or len(coupons) < 2:
            insights["opportunities"].append("다양한 쿠폰 제공으로 고객 유치 강화 가능")
        
        # 추천 사항
        if shop_specialty.get("product_lineup_type") == "specialized":
            insights["recommendations"].append("특화된 제품 라인업을 활용한 타겟 마케팅 강화")
        
        if shop_specialty.get("target_customer") != "general":
            target = shop_specialty.get("target_customer", "").replace("_", " ")
            insights["recommendations"].append(f"{target} 타겟 고객층을 위한 맞춤형 마케팅 전략 수립")
        
        # 경쟁 우위
        if shop_specialty.get("is_brand_shop"):
            insights["competitive_advantages"].append("공식 브랜드 샵으로 제품 신뢰도 및 품질 보장")
        
        if shop_level == "power":
            insights["competitive_advantages"].append("POWER 셀러 레벨로 빠른 정산 및 우수한 서비스 제공")
        
        # 인사이트 점수
        score = 0
        score += len(insights["strengths"]) * 20
        score += len(insights["opportunities"]) * 15
        score += len(insights["recommendations"]) * 10
        score += len(insights["competitive_advantages"]) * 15
        
        insights["score"] = min(100, score)
        
        return insights
    
    def _calculate_overall_score(self, analysis_result: Dict[str, Any], shop_specialty: Dict[str, Any]) -> int:
        """종합 점수 계산 (Shop 특수성 반영)"""
        weights = {
            "shop_info": 0.25,
            "product_analysis": 0.25,
            "category_analysis": 0.10,
            "competitor_analysis": 0.10,
            "level_analysis": 0.10,
            "shop_specialty": 0.10,  # Shop 특수성 가중치 추가
            "product_type_analysis": 0.05,  # 상품 종류 분석 가중치 추가
            "customized_insights": 0.05  # 독자적 인사이트 가중치 추가
        }
        
        overall = 0
        for key, weight in weights.items():
            if key in analysis_result:
                score = analysis_result[key].get("score", 0)
                overall += score * weight
        
        # Shop 특수성 보너스
        if shop_specialty.get("is_brand_shop"):
            overall += 5  # 브랜드 샵 보너스
        if shop_specialty.get("product_lineup_type") == "specialized":
            overall += 5  # 특화 제품 라인업 보너스
        
        return min(100, int(overall))
