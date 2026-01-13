"""
AIO (All-In-One) 종합 최적화 서비스
SEO, AI SEO, GEO를 종합적으로 분석하고 최적화합니다.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

from .seo_optimizer import SEOOptimizer
from .ai_seo_optimizer import AISEOOptimizer
from .geo_optimizer import GEOOptimizer


class AIOOptimizer:
    """AIO 종합 최적화 클래스"""
    
    def __init__(self):
        self.seo_optimizer = SEOOptimizer()
        self.ai_seo_optimizer = AISEOOptimizer()
        self.geo_optimizer = GEOOptimizer()
    
    async def analyze(self, url: str, product_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        종합 분석 수행
        
        Args:
            url: 분석할 URL
            product_data: 상품 데이터 (선택사항)
            
        Returns:
            종합 분석 결과
        """
        # 병렬로 모든 분석 수행
        seo_result, ai_seo_result, geo_result = await asyncio.gather(
            self.seo_optimizer.analyze(url, product_data),
            self.ai_seo_optimizer.analyze(url, product_data),
            self.geo_optimizer.analyze(url, product_data)
        )
        
        # 종합 결과 구성
        analysis = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "overall_score": 0,
            "seo": seo_result,
            "ai_seo": ai_seo_result,
            "geo": geo_result,
            "performance": await self._analyze_performance(url, product_data),
            "accessibility": self._analyze_accessibility(product_data) if product_data else {},
            "security": self._analyze_security(url),
            "social_optimization": self._analyze_social(product_data) if product_data else {},
            "recommendations": [],
            "priority_actions": []
        }
        
        # 종합 점수 계산
        analysis["overall_score"] = self._calculate_overall_score(analysis)
        
        # 우선순위 액션 생성
        analysis["priority_actions"] = self._generate_priority_actions(analysis)
        
        # 종합 추천사항 생성
        analysis["recommendations"] = self._generate_recommendations(analysis)
        
        return analysis
    
    async def _analyze_performance(self, url: str, product_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """성능 분석"""
        return {
            "page_load_time": "N/A",  # 실제로는 측정 필요
            "image_optimization": "good" if product_data and product_data.get("images") else "needs_improvement",
            "recommendations": [
                "이미지를 WebP 형식으로 최적화하세요",
                "이미지 lazy loading을 구현하세요"
            ]
        }
    
    def _analyze_accessibility(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """접근성 분석"""
        return {
            "has_alt_text": False,  # 실제로는 확인 필요
            "has_aria_labels": False,
            "color_contrast": "unknown",
            "keyboard_navigation": "unknown",
            "recommendations": [
                "모든 이미지에 alt 텍스트를 추가하세요",
                "ARIA 레이블을 추가하여 스크린 리더 지원을 개선하세요"
            ]
        }
    
    def _analyze_security(self, url: str) -> Dict[str, Any]:
        """보안 분석"""
        is_https = url.startswith("https://")
        return {
            "is_https": is_https,
            "has_ssl": is_https,
            "recommendations": [] if is_https else ["HTTPS를 사용하세요"]
        }
    
    def _analyze_social(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """소셜 미디어 최적화 분석"""
        has_og_tags = bool(product_data.get("product_name"))
        has_twitter_tags = has_og_tags
        
        return {
            "has_og_tags": has_og_tags,
            "has_twitter_tags": has_twitter_tags,
            "social_score": 50 if has_og_tags else 0,
            "recommendations": [] if has_og_tags else [
                "Open Graph 태그를 추가하세요",
                "Twitter Card 태그를 추가하세요"
            ]
        }
    
    def _calculate_overall_score(self, analysis: Dict[str, Any]) -> int:
        """종합 점수 계산"""
        weights = {
            "seo": 0.3,
            "ai_seo": 0.3,
            "geo": 0.2,
            "performance": 0.1,
            "accessibility": 0.05,
            "security": 0.05
        }
        
        overall = 0
        
        # SEO 점수
        seo_score = analysis["seo"].get("score", 0)
        overall += seo_score * weights["seo"]
        
        # AI SEO 점수
        ai_seo_score = analysis["ai_seo"].get("score", 0)
        overall += ai_seo_score * weights["ai_seo"]
        
        # GEO 점수
        geo_score = analysis["geo"].get("score", 0)
        overall += geo_score * weights["geo"]
        
        # 성능 점수 (간단한 휴리스틱)
        performance_score = 70  # 기본값
        overall += performance_score * weights["performance"]
        
        # 접근성 점수 (간단한 휴리스틱)
        accessibility_score = 60  # 기본값
        overall += accessibility_score * weights["accessibility"]
        
        # 보안 점수
        security_score = 100 if analysis["security"].get("is_https") else 0
        overall += security_score * weights["security"]
        
        return min(100, int(overall))
    
    def _generate_priority_actions(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """우선순위 액션 생성"""
        actions = []
        
        # SEO 액션
        seo_recommendations = analysis["seo"].get("recommendations", [])
        for rec in seo_recommendations[:2]:
            actions.append({
                "category": "SEO",
                "priority": "high",
                "action": rec,
                "impact": "high"
            })
        
        # AI SEO 액션
        ai_seo_recommendations = analysis["ai_seo"].get("recommendations", [])
        for rec in ai_seo_recommendations[:2]:
            actions.append({
                "category": "AI SEO",
                "priority": "medium",
                "action": rec,
                "impact": "medium"
            })
        
        # GEO 액션
        geo_recommendations = analysis["geo"].get("recommendations", [])
        for rec in geo_recommendations[:2]:
            actions.append({
                "category": "GEO",
                "priority": "medium",
                "action": rec,
                "impact": "medium"
            })
        
        return actions[:5]  # 상위 5개만 반환
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """종합 추천사항 생성"""
        recommendations = []
        
        # 각 분석의 추천사항 수집
        all_recommendations = []
        all_recommendations.extend(analysis["seo"].get("recommendations", []))
        all_recommendations.extend(analysis["ai_seo"].get("recommendations", []))
        all_recommendations.extend(analysis["geo"].get("recommendations", []))
        all_recommendations.extend(analysis["performance"].get("recommendations", []))
        all_recommendations.extend(analysis["accessibility"].get("recommendations", []))
        all_recommendations.extend(analysis["security"].get("recommendations", []))
        all_recommendations.extend(analysis["social_optimization"].get("recommendations", []))
        
        # 중복 제거 및 정리
        seen = set()
        for rec in all_recommendations:
            if rec and rec not in seen:
                recommendations.append(rec)
                seen.add(rec)
        
        return recommendations[:10]  # 상위 10개만 반환
    
    async def optimize(self, url: str, product_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        자동 최적화 수행
        
        Args:
            url: 최적화할 URL
            product_data: 상품 데이터 (선택사항)
            
        Returns:
            최적화 결과
        """
        # 분석 수행
        analysis = await self.analyze(url, product_data)
        
        # 최적화 제안 생성
        optimizations = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "optimizations_applied": [],
            "optimizations_suggested": [],
            "before_score": analysis["overall_score"],
            "estimated_after_score": min(100, analysis["overall_score"] + 10)  # 추정치
        }
        
        # SEO 최적화 제안
        if analysis["seo"]["score"] < 70:
            optimizations["optimizations_suggested"].append({
                "type": "SEO",
                "action": "메타 태그 최적화",
                "impact": "high"
            })
        
        # AI SEO 최적화 제안
        if analysis["ai_seo"]["score"] < 70:
            optimizations["optimizations_suggested"].append({
                "type": "AI SEO",
                "action": "키워드 밀도 최적화",
                "impact": "medium"
            })
        
        # GEO 최적화 제안
        if analysis["geo"]["score"] < 70:
            optimizations["optimizations_suggested"].append({
                "type": "GEO",
                "action": "스키마 마크업 추가",
                "impact": "high"
            })
        
        return optimizations
    
    def generate_report(self, analysis: Dict[str, Any], format: str = "json") -> str:
        """
        리포트 생성
        
        Args:
            analysis: 분석 결과
            format: 리포트 형식 (json, markdown)
            
        Returns:
            리포트 문자열
        """
        if format == "markdown":
            return self._generate_markdown_report(analysis)
        else:
            import json
            return json.dumps(analysis, indent=2, ensure_ascii=False)
    
    def _generate_markdown_report(self, analysis: Dict[str, Any]) -> str:
        """Markdown 리포트 생성"""
        report = f"# AIO 최적화 리포트\n\n"
        report += f"**URL**: {analysis['url']}\n\n"
        report += f"**분석 일시**: {analysis['timestamp']}\n\n"
        report += f"**종합 점수**: {analysis['overall_score']}/100\n\n"
        
        report += "## SEO 분석\n\n"
        report += f"- 점수: {analysis['seo']['score']}/100\n"
        report += f"- 추천사항: {len(analysis['seo'].get('recommendations', []))}개\n\n"
        
        report += "## AI SEO 분석\n\n"
        report += f"- 점수: {analysis['ai_seo']['score']}/100\n"
        report += f"- 추천사항: {len(analysis['ai_seo'].get('recommendations', []))}개\n\n"
        
        report += "## GEO 분석\n\n"
        report += f"- 점수: {analysis['geo']['score']}/100\n"
        report += f"- 추천사항: {len(analysis['geo'].get('recommendations', []))}개\n\n"
        
        report += "## 우선순위 액션\n\n"
        for i, action in enumerate(analysis.get('priority_actions', [])[:5], 1):
            report += f"{i}. **{action['category']}** ({action['priority']}): {action['action']}\n"
        
        report += "\n## 종합 추천사항\n\n"
        for i, rec in enumerate(analysis.get('recommendations', [])[:10], 1):
            report += f"{i}. {rec}\n"
        
        return report
