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
        Shop 데이터 종합 분석
        
        Args:
            shop_data: 크롤러에서 수집한 Shop 데이터
            
        Returns:
            분석 결과 딕셔너리
        """
        analysis_result = {
            "overall_score": 0,
            "shop_info": self._analyze_shop_info(shop_data),
            "product_analysis": self._analyze_products(shop_data),
            "category_analysis": self._analyze_categories(shop_data),
            "competitor_analysis": self._analyze_competitors(shop_data),
            "level_analysis": self._analyze_shop_level(shop_data)
        }
        
        # 종합 점수 계산
        analysis_result["overall_score"] = self._calculate_overall_score(analysis_result)
        
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
    
    def _calculate_overall_score(self, analysis_result: Dict[str, Any]) -> int:
        """종합 점수 계산"""
        weights = {
            "shop_info": 0.30,
            "product_analysis": 0.30,
            "category_analysis": 0.15,
            "competitor_analysis": 0.15,
            "level_analysis": 0.10
        }
        
        overall = 0
        for key, weight in weights.items():
            if key in analysis_result:
                score = analysis_result[key].get("score", 0)
                overall += score * weight
        
        return int(overall)
