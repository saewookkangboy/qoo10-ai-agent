"""
SEO 최적화 서비스
웹사이트 및 상품 페이지의 SEO를 최적화합니다.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from urllib.parse import urlparse, urljoin


class SEOOptimizer:
    """SEO 최적화 클래스"""
    
    def __init__(self):
        self.default_user_agent = "*"
        self.default_crawl_delay = 1
    
    async def analyze(self, url: str, product_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        SEO 분석 수행
        
        Args:
            url: 분석할 URL
            product_data: 상품 데이터 (선택사항)
            
        Returns:
            SEO 분석 결과
        """
        analysis = {
            "url": url,
            "score": 0,
            "meta_tags": self._analyze_meta_tags(product_data) if product_data else {},
            "title_optimization": self._analyze_title(product_data) if product_data else {},
            "description_optimization": self._analyze_description(product_data) if product_data else {},
            "heading_structure": self._analyze_headings(product_data) if product_data else {},
            "image_optimization": self._analyze_images(product_data) if product_data else {},
            "internal_links": [],
            "external_links": [],
            "recommendations": []
        }
        
        # 점수 계산
        analysis["score"] = self._calculate_seo_score(analysis)
        
        return analysis
    
    def _analyze_meta_tags(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """메타 태그 분석"""
        meta_analysis = {
            "has_title": bool(product_data.get("product_name")),
            "has_description": bool(product_data.get("description")),
            "has_keywords": bool(product_data.get("search_keywords")),
            "has_og_tags": False,
            "has_twitter_tags": False,
            "recommendations": []
        }
        
        if not meta_analysis["has_title"]:
            meta_analysis["recommendations"].append("제목 메타 태그를 추가하세요")
        
        if not meta_analysis["has_description"]:
            meta_analysis["recommendations"].append("설명 메타 태그를 추가하세요 (150-160자 권장)")
        
        return meta_analysis
    
    def _analyze_title(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """제목 최적화 분석"""
        title = product_data.get("product_name", "")
        title_analysis = {
            "title": title,
            "length": len(title),
            "optimal_length": 50 <= len(title) <= 60,
            "has_keywords": bool(product_data.get("search_keywords")),
            "recommendations": []
        }
        
        if title_analysis["length"] < 50:
            title_analysis["recommendations"].append("제목을 50자 이상으로 늘리세요")
        elif title_analysis["length"] > 60:
            title_analysis["recommendations"].append("제목을 60자 이하로 줄이세요")
        
        return title_analysis
    
    def _analyze_description(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """설명 최적화 분석"""
        description = product_data.get("description", "")
        desc_analysis = {
            "description": description[:160] + "..." if len(description) > 160 else description,
            "length": len(description),
            "optimal_length": 150 <= len(description) <= 160,
            "has_keywords": bool(product_data.get("search_keywords")),
            "recommendations": []
        }
        
        if desc_analysis["length"] < 150:
            desc_analysis["recommendations"].append("메타 설명을 150자 이상으로 늘리세요")
        elif desc_analysis["length"] > 160:
            desc_analysis["recommendations"].append("메타 설명을 160자 이하로 줄이세요")
        
        return desc_analysis
    
    def _analyze_headings(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """헤딩 구조 분석"""
        return {
            "has_h1": True,  # 상품명이 H1으로 사용됨
            "has_h2": False,
            "has_h3": False,
            "recommendations": ["H2, H3 태그를 사용하여 콘텐츠를 구조화하세요"]
        }
    
    def _analyze_images(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """이미지 최적화 분석"""
        images = product_data.get("images", {})
        image_analysis = {
            "total_images": len(images.get("detail_images", [])),
            "has_alt_text": False,
            "image_sizes": [],
            "recommendations": []
        }
        
        if image_analysis["total_images"] == 0:
            image_analysis["recommendations"].append("최소 3개 이상의 이미지를 추가하세요")
        
        image_analysis["recommendations"].append("모든 이미지에 alt 텍스트를 추가하세요")
        
        return image_analysis
    
    def _calculate_seo_score(self, analysis: Dict[str, Any]) -> int:
        """SEO 점수 계산"""
        score = 0
        
        # 메타 태그 점수
        if analysis["meta_tags"].get("has_title"):
            score += 20
        if analysis["meta_tags"].get("has_description"):
            score += 20
        if analysis["meta_tags"].get("has_keywords"):
            score += 10
        
        # 제목 최적화
        if analysis["title_optimization"].get("optimal_length"):
            score += 15
        if analysis["title_optimization"].get("has_keywords"):
            score += 10
        
        # 설명 최적화
        if analysis["description_optimization"].get("optimal_length"):
            score += 15
        if analysis["description_optimization"].get("has_keywords"):
            score += 10
        
        return min(100, score)
    
    def generate_sitemap(self, urls: List[str], base_url: str) -> str:
        """
        XML Sitemap 생성
        
        Args:
            urls: 포함할 URL 목록
            base_url: 기본 URL
            
        Returns:
            XML 형식의 sitemap 문자열
        """
        sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
        sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        
        for url in urls:
            sitemap += '  <url>\n'
            sitemap += f'    <loc>{url}</loc>\n'
            sitemap += f'    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>\n'
            sitemap += '    <changefreq>weekly</changefreq>\n'
            sitemap += '    <priority>0.8</priority>\n'
            sitemap += '  </url>\n'
        
        sitemap += '</urlset>'
        
        return sitemap
    
    def generate_robots_txt(self, 
                           allowed_paths: Optional[List[str]] = None,
                           disallowed_paths: Optional[List[str]] = None,
                           sitemap_url: Optional[str] = None) -> str:
        """
        robots.txt 생성
        
        Args:
            allowed_paths: 허용할 경로 목록
            disallowed_paths: 차단할 경로 목록
            sitemap_url: sitemap.xml URL
            
        Returns:
            robots.txt 내용
        """
        robots = f"User-agent: {self.default_user_agent}\n"
        
        if allowed_paths:
            for path in allowed_paths:
                robots += f"Allow: {path}\n"
        
        if disallowed_paths:
            for path in disallowed_paths:
                robots += f"Disallow: {path}\n"
        
        robots += f"Crawl-delay: {self.default_crawl_delay}\n"
        
        if sitemap_url:
            robots += f"\nSitemap: {sitemap_url}\n"
        
        return robots
    
    def generate_meta_tags(self, product_data: Dict[str, Any], base_url: str) -> Dict[str, str]:
        """
        메타 태그 생성
        
        Args:
            product_data: 상품 데이터
            base_url: 기본 URL
            
        Returns:
            메타 태그 딕셔너리
        """
        product_name = product_data.get("product_name", "")
        description = product_data.get("description", "")[:160]
        keywords = ", ".join(product_data.get("search_keywords", []))
        thumbnail = product_data.get("images", {}).get("thumbnail", "")
        
        meta_tags = {
            "title": product_name,
            "description": description,
            "keywords": keywords,
            "og:title": product_name,
            "og:description": description,
            "og:type": "product",
            "og:url": base_url,
            "og:image": thumbnail,
            "twitter:card": "summary_large_image",
            "twitter:title": product_name,
            "twitter:description": description,
            "twitter:image": thumbnail
        }
        
        return meta_tags
