"""
경쟁사 비교 분석 서비스
동일 카테고리 Top 10 상품과의 상세 비교 분석을 제공합니다.
"""
from typing import Dict, Any, List, Optional
import asyncio
from services.crawler import Qoo10Crawler


class CompetitorAnalyzer:
    """경쟁사 분석기"""
    
    def __init__(self):
        self.crawler = Qoo10Crawler()
        self.top_n = 10  # Top N 상품 비교
    
    async def analyze_competitors(
        self,
        product_data: Dict[str, Any],
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        경쟁사 분석 수행
        
        Args:
            product_data: 분석 대상 상품 데이터
            category: 카테고리 (없으면 product_data에서 추출)
            
        Returns:
            경쟁사 분석 결과
        """
        target_category = category or product_data.get("category")
        
        if not target_category:
            return {
                "error": "카테고리를 확인할 수 없습니다",
                "competitors": []
            }
        
        # 동일 카테고리 Top 10 상품 수집
        competitors = await self._collect_competitors(target_category, product_data)
        
        # 비교 분석 수행
        comparison_result = self._compare_with_competitors(product_data, competitors)
        
        return {
            "target_product": {
                "product_name": product_data.get("product_name"),
                "price": product_data.get("price", {}).get("sale_price"),
                "rating": product_data.get("reviews", {}).get("rating", 0),
                "review_count": product_data.get("reviews", {}).get("review_count", 0)
            },
            "competitors": competitors,
            "comparison": comparison_result,
            "differentiation_points": self._find_differentiation_points(product_data, competitors),
            "recommendations": self._generate_competitor_recommendations(product_data, competitors, comparison_result)
        }
    
    async def _collect_competitors(
        self,
        category: str,
        target_product: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        경쟁사 상품 수집
        
        Note: 실제로는 Qoo10 카테고리 페이지에서 Top 10 상품을 크롤링해야 하지만,
        여기서는 시뮬레이션 데이터를 반환합니다.
        실제 구현 시 카테고리 페이지 크롤링 로직이 필요합니다.
        """
        competitors = []
        
        # 실제 구현 시:
        # 1. 카테고리 페이지 URL 구성
        # 2. 카테고리 페이지 크롤링
        # 3. Top 10 상품 URL 추출
        # 4. 각 상품 크롤링
        
        # 여기서는 시뮬레이션
        target_price = target_product.get("price", {}).get("sale_price", 0)
        target_rating = target_product.get("reviews", {}).get("rating", 0)
        
        # 가격대별 경쟁사 시뮬레이션
        for i in range(min(10, self.top_n)):
            price_variation = target_price * (0.8 + (i * 0.04))  # ±20% 범위
            competitors.append({
                "rank": i + 1,
                "product_name": f"경쟁 상품 {i+1}",
                "price": int(price_variation),
                "rating": max(3.5, min(5.0, target_rating + (i - 5) * 0.1)),
                "review_count": (i + 1) * 10,
                "discount_rate": i * 5 if i < 5 else 0,
                "has_coupon": i % 2 == 0,
                "advertising": ["파워랭크업"] if i < 3 else []
            })
        
        return competitors
    
    def _compare_with_competitors(
        self,
        target_product: Dict[str, Any],
        competitors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """경쟁사와 비교 분석"""
        target_price = target_product.get("price", {}).get("sale_price", 0)
        target_rating = target_product.get("reviews", {}).get("rating", 0)
        target_reviews = target_product.get("reviews", {}).get("review_count", 0)
        
        if not competitors:
            return {
                "price_position": "unknown",
                "rating_position": "unknown",
                "review_position": "unknown"
            }
        
        # 가격 비교
        competitor_prices = [c.get("price", 0) for c in competitors if c.get("price")]
        if competitor_prices:
            avg_price = sum(competitor_prices) / len(competitor_prices)
            min_price = min(competitor_prices)
            max_price = max(competitor_prices)
            
            if target_price < min_price:
                price_position = "lowest"
            elif target_price < avg_price:
                price_position = "below_average"
            elif target_price == avg_price:
                price_position = "average"
            elif target_price < max_price:
                price_position = "above_average"
            else:
                price_position = "highest"
        else:
            price_position = "unknown"
        
        # 평점 비교
        competitor_ratings = [c.get("rating", 0) for c in competitors if c.get("rating")]
        if competitor_ratings:
            avg_rating = sum(competitor_ratings) / len(competitor_ratings)
            if target_rating >= avg_rating + 0.3:
                rating_position = "excellent"
            elif target_rating >= avg_rating:
                rating_position = "above_average"
            elif target_rating >= avg_rating - 0.3:
                rating_position = "below_average"
            else:
                rating_position = "poor"
        else:
            rating_position = "unknown"
        
        # 리뷰 수 비교
        competitor_reviews = [c.get("review_count", 0) for c in competitors if c.get("review_count")]
        if competitor_reviews:
            avg_reviews = sum(competitor_reviews) / len(competitor_reviews)
            if target_reviews >= avg_reviews * 1.5:
                review_position = "excellent"
            elif target_reviews >= avg_reviews:
                review_position = "above_average"
            elif target_reviews >= avg_reviews * 0.5:
                review_position = "below_average"
            else:
                review_position = "poor"
        else:
            review_position = "unknown"
        
        return {
            "price_position": price_position,
            "price_stats": {
                "target": target_price,
                "average": avg_price if competitor_prices else 0,
                "min": min_price if competitor_prices else 0,
                "max": max_price if competitor_prices else 0
            },
            "rating_position": rating_position,
            "rating_stats": {
                "target": target_rating,
                "average": avg_rating if competitor_ratings else 0
            },
            "review_position": review_position,
            "review_stats": {
                "target": target_reviews,
                "average": avg_reviews if competitor_reviews else 0
            }
        }
    
    def _find_differentiation_points(
        self,
        target_product: Dict[str, Any],
        competitors: List[Dict[str, Any]]
    ) -> List[str]:
        """차별화 포인트 도출"""
        points = []
        
        target_price = target_product.get("price", {}).get("sale_price", 0)
        target_rating = target_product.get("reviews", {}).get("rating", 0)
        target_images = len(target_product.get("images", {}).get("detail_images", []))
        
        # 가격 차별화
        competitor_prices = [c.get("price", 0) for c in competitors if c.get("price")]
        if competitor_prices:
            avg_price = sum(competitor_prices) / len(competitor_prices)
            if target_price < avg_price * 0.9:
                points.append("경쟁사 대비 저렴한 가격")
            elif target_price > avg_price * 1.1:
                points.append("프리미엄 가격 포지셔닝")
        
        # 평점 차별화
        competitor_ratings = [c.get("rating", 0) for c in competitors if c.get("rating")]
        if competitor_ratings:
            avg_rating = sum(competitor_ratings) / len(competitor_ratings)
            if target_rating >= avg_rating + 0.3:
                points.append("높은 고객 만족도 (평점 우수)")
        
        # 이미지 차별화
        if target_images >= 5:
            points.append("풍부한 상품 이미지")
        
        # 설명 차별화
        description_length = len(target_product.get("description", ""))
        if description_length >= 500:
            points.append("상세한 상품 설명")
        
        if not points:
            points.append("경쟁사와 유사한 수준")
        
        return points
    
    def _generate_competitor_recommendations(
        self,
        target_product: Dict[str, Any],
        competitors: List[Dict[str, Any]],
        comparison: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """경쟁사 분석 기반 추천 생성"""
        recommendations = []
        
        # 가격 전략 추천
        price_position = comparison.get("price_position", "unknown")
        price_stats = comparison.get("price_stats", {})
        
        if price_position == "highest":
            recommendations.append({
                "category": "가격 전략",
                "priority": "high",
                "title": "가격 경쟁력 강화",
                "description": f"현재 가격({price_stats.get('target', 0):,}엔)이 경쟁사 평균({price_stats.get('average', 0):,}엔)보다 높습니다.",
                "action_items": [
                    "경쟁사 평균 가격 수준으로 조정 검토",
                    "또는 프리미엄 포지셔닝 강화 (고품질 강조)"
                ]
            })
        elif price_position == "lowest":
            recommendations.append({
                "category": "가격 전략",
                "priority": "low",
                "title": "가격 상향 조정 검토",
                "description": "현재 가격이 경쟁사보다 낮습니다. 수익성 개선을 위해 가격 상향 조정을 검토하세요.",
                "action_items": [
                    "경쟁사 평균 가격 수준으로 조정 검토",
                    "가격 상향 시 상품 품질 강조"
                ]
            })
        
        # 평점 개선 추천
        rating_position = comparison.get("rating_position", "unknown")
        if rating_position in ["below_average", "poor"]:
            recommendations.append({
                "category": "상품 품질",
                "priority": "high",
                "title": "평점 향상 필요",
                "description": "경쟁사 대비 평점이 낮습니다. 상품 품질 및 서비스 개선이 필요합니다.",
                "action_items": [
                    "부정 리뷰 분석 및 개선",
                    "상품 품질 향상",
                    "배송 서비스 개선"
                ]
            })
        
        # 리뷰 수 확보 추천
        review_position = comparison.get("review_position", "unknown")
        if review_position in ["below_average", "poor"]:
            recommendations.append({
                "category": "마케팅",
                "priority": "medium",
                "title": "리뷰 수 확보",
                "description": "경쟁사 대비 리뷰 수가 부족합니다. 리뷰 확보를 위한 전략이 필요합니다.",
                "action_items": [
                    "샘플마켓 참가 검토",
                    "구매 후 리뷰 작성 유도",
                    "리뷰 작성 시 혜택 제공"
                ]
            })
        
        # 광고 활용도 비교
        target_advertising = []  # 실제로는 상품 데이터에서 확인
        competitor_advertising = [c.get("advertising", []) for c in competitors]
        active_advertisers = sum(1 for ads in competitor_advertising if ads)
        
        if active_advertisers >= 5:
            recommendations.append({
                "category": "광고",
                "priority": "medium",
                "title": "광고 활용 검토",
                "description": f"경쟁사 중 {active_advertisers}개가 광고를 활용하고 있습니다.",
                "action_items": [
                    "파워랭크업 광고 시작 검토",
                    "스마트세일즈 광고 활용 검토"
                ]
            })
        
        return recommendations
