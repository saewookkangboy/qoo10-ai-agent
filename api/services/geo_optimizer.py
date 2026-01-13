"""
GEO (Generative Engine Optimization) 최적화 서비스
생성형 AI 검색 엔진을 위한 최적화를 수행합니다.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class GEOOptimizer:
    """GEO 최적화 클래스"""
    
    def __init__(self):
        self.supported_engines = ["chatgpt", "claude", "perplexity", "gemini"]
    
    async def analyze(self, url: str, product_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        GEO 분석 수행
        
        Args:
            url: 분석할 URL
            product_data: 상품 데이터 (선택사항)
            
        Returns:
            GEO 분석 결과
        """
        analysis = {
            "url": url,
            "score": 0,
            "schema_markup": self._analyze_schema_markup(product_data) if product_data else {},
            "faq_schema": self._check_faq_schema(product_data) if product_data else {},
            "howto_schema": self._check_howto_schema(product_data) if product_data else {},
            "article_schema": self._check_article_schema(product_data) if product_data else {},
            "citation_readiness": self._analyze_citation_readiness(product_data) if product_data else {},
            "ai_engine_compatibility": self._analyze_engine_compatibility(product_data) if product_data else {},
            "recommendations": []
        }
        
        # 점수 계산
        analysis["score"] = self._calculate_geo_score(analysis)
        
        return analysis
    
    def _analyze_schema_markup(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """스키마 마크업 분석"""
        return {
            "has_product_schema": True,  # Qoo10은 기본적으로 제품 스키마 사용
            "has_review_schema": bool(product_data.get("reviews", {}).get("review_count", 0) > 0),
            "has_organization_schema": bool(product_data.get("seller_info", {}).get("shop_name")),
            "recommendations": [
                "FAQ 스키마를 추가하여 AI 검색 엔진에서 더 잘 인식되도록 하세요",
                "HowTo 스키마를 추가하여 사용 가이드를 제공하세요"
            ]
        }
    
    def _check_faq_schema(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """FAQ 스키마 확인"""
        return {
            "has_faq_schema": False,
            "suggested_questions": self._generate_faq_questions(product_data),
            "recommendations": ["FAQ 스키마를 추가하여 AI 검색 엔진에서 질문에 답변할 수 있도록 하세요"]
        }
    
    def _check_howto_schema(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """HowTo 스키마 확인"""
        return {
            "has_howto_schema": False,
            "suggested_steps": self._generate_howto_steps(product_data),
            "recommendations": ["HowTo 스키마를 추가하여 사용 방법을 명확히 하세요"]
        }
    
    def _check_article_schema(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Article 스키마 확인"""
        return {
            "has_article_schema": False,
            "has_author": False,
            "has_publish_date": False,
            "recommendations": ["Article 스키마를 추가하여 콘텐츠의 신뢰도를 높이세요"]
        }
    
    def _analyze_citation_readiness(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """인용 가능성 분석"""
        description = product_data.get("description", "")
        product_name = product_data.get("product_name", "")
        
        return {
            "has_clear_title": bool(product_name),
            "has_structured_content": bool(description),
            "has_authority_signals": bool(product_data.get("brand")),
            "citation_score": self._calculate_citation_score(product_data),
            "recommendations": [
                "명확한 제목과 구조화된 콘텐츠로 인용 가능성을 높이세요",
                "권위 있는 소스 링크를 추가하세요"
            ]
        }
    
    def _analyze_engine_compatibility(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """AI 엔진 호환성 분석"""
        compatibility = {}
        
        for engine in self.supported_engines:
            compatibility[engine] = {
                "compatible": True,
                "score": 70,  # 기본 점수
                "notes": f"{engine}에서 인식 가능한 구조입니다"
            }
        
        return compatibility
    
    def _calculate_citation_score(self, product_data: Dict[str, Any]) -> int:
        """인용 점수 계산"""
        score = 0
        
        if product_data.get("product_name"):
            score += 25
        if product_data.get("description"):
            score += 25
        if product_data.get("brand"):
            score += 25
        if product_data.get("reviews", {}).get("review_count", 0) > 0:
            score += 25
        
        return score
    
    def _generate_faq_questions(self, product_data: Dict[str, Any]) -> List[str]:
        """FAQ 질문 생성"""
        product_name = product_data.get("product_name", "이 상품")
        questions = [
            f"{product_name}의 가격은 얼마인가요?",
            f"{product_name}의 배송 기간은 얼마나 걸리나요?",
            f"{product_name}의 반품 정책은 무엇인가요?",
            f"{product_name}의 사용 방법은 무엇인가요?",
            f"{product_name}의 재질은 무엇인가요?"
        ]
        return questions[:5]
    
    def _generate_howto_steps(self, product_data: Dict[str, Any]) -> List[str]:
        """HowTo 단계 생성"""
        return [
            "상품을 장바구니에 추가합니다",
            "결제 정보를 입력합니다",
            "주문을 확인합니다",
            "배송을 기다립니다",
            "상품을 수령하고 리뷰를 작성합니다"
        ]
    
    def _calculate_geo_score(self, analysis: Dict[str, Any]) -> int:
        """GEO 점수 계산"""
        score = 0
        
        # 스키마 마크업 점수
        if analysis["schema_markup"].get("has_product_schema"):
            score += 20
        if analysis["schema_markup"].get("has_review_schema"):
            score += 15
        if analysis["schema_markup"].get("has_organization_schema"):
            score += 10
        
        # 인용 가능성 점수
        citation_score = analysis["citation_readiness"].get("citation_score", 0)
        score += citation_score * 0.3
        
        # AI 엔진 호환성 점수
        engine_scores = [v.get("score", 0) for v in analysis["ai_engine_compatibility"].values()]
        if engine_scores:
            score += sum(engine_scores) / len(engine_scores) * 0.2
        
        return min(100, int(score))
    
    def generate_faq_schema(self, questions: List[str], answers: List[str]) -> Dict[str, Any]:
        """
        FAQ 스키마 생성
        
        Args:
            questions: 질문 목록
            answers: 답변 목록
            
        Returns:
            FAQ 스키마 JSON-LD
        """
        faq_items = []
        for q, a in zip(questions, answers):
            faq_items.append({
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": a
                }
            })
        
        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": faq_items
        }
        
        return schema
    
    def generate_howto_schema(self, name: str, steps: List[str], description: Optional[str] = None) -> Dict[str, Any]:
        """
        HowTo 스키마 생성
        
        Args:
            name: 가이드 이름
            steps: 단계 목록
            description: 설명 (선택사항)
            
        Returns:
            HowTo 스키마 JSON-LD
        """
        howto_steps = []
        for i, step in enumerate(steps, 1):
            howto_steps.append({
                "@type": "HowToStep",
                "position": i,
                "name": step,
                "text": step
            })
        
        schema = {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": name,
            "description": description or f"{name} 가이드",
            "step": howto_steps
        }
        
        return schema
    
    def generate_article_schema(self, 
                               headline: str,
                               author: str,
                               url: str,
                               publish_date: Optional[str] = None,
                               image: Optional[str] = None) -> Dict[str, Any]:
        """
        Article 스키마 생성
        
        Args:
            headline: 제목
            author: 작성자
            url: URL
            publish_date: 발행일 (선택사항)
            image: 이미지 URL (선택사항)
            
        Returns:
            Article 스키마 JSON-LD
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": headline,
            "author": {
                "@type": "Person",
                "name": author
            },
            "url": url
        }
        
        if publish_date:
            schema["datePublished"] = publish_date
        else:
            schema["datePublished"] = datetime.now().isoformat()
        
        if image:
            schema["image"] = image
        
        return schema
    
    def generate_llms_txt(self, base_url: str, sitemap_url: Optional[str] = None) -> str:
        """
        llms.txt 파일 생성
        
        Args:
            base_url: 기본 URL
            sitemap_url: sitemap URL (선택사항)
            
        Returns:
            llms.txt 내용
        """
        llms_txt = f"# llms.txt\n"
        llms_txt += f"# AI 검색 엔진을 위한 사이트 정보\n\n"
        llms_txt += f"Base URL: {base_url}\n"
        
        if sitemap_url:
            llms_txt += f"Sitemap: {sitemap_url}\n"
        
        llms_txt += "\n# 허용된 크롤러\n"
        llms_txt += "User-agent: GPTBot\n"
        llms_txt += "User-agent: ChatGPT-User\n"
        llms_txt += "User-agent: anthropic-ai\n"
        llms_txt += "User-agent: Claude-Web\n"
        
        return llms_txt
