"""
AI SEO 최적화 서비스
AI 검색 엔진을 위한 SEO 최적화를 수행합니다.
"""
from typing import Dict, List, Any, Optional
import re
from collections import Counter


class AISEOOptimizer:
    """AI SEO 최적화 클래스"""
    
    def __init__(self):
        self.min_keyword_density = 0.01  # 1%
        self.max_keyword_density = 0.03  # 3%
    
    async def analyze(self, url: str, product_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        AI SEO 분석 수행
        
        Args:
            url: 분석할 URL
            product_data: 상품 데이터 (선택사항)
            
        Returns:
            AI SEO 분석 결과
        """
        analysis = {
            "url": url,
            "score": 0,
            "keyword_research": await self._research_keywords(product_data) if product_data else {},
            "content_optimization": self._analyze_content(product_data) if product_data else {},
            "semantic_keywords": self._extract_semantic_keywords(product_data) if product_data else [],
            "ai_readability": self._analyze_ai_readability(product_data) if product_data else {},
            "recommendations": []
        }
        
        # 점수 계산
        analysis["score"] = self._calculate_ai_seo_score(analysis)
        
        return analysis
    
    async def _research_keywords(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """키워드 리서치"""
        product_name = product_data.get("product_name", "")
        description = product_data.get("description", "")
        category = product_data.get("category", "")
        existing_keywords = product_data.get("search_keywords", [])
        
        # 기본 키워드 추출
        suggested_keywords = []
        
        # 상품명에서 키워드 추출
        if product_name:
            words = re.findall(r'\w+', product_name.lower())
            suggested_keywords.extend([w for w in words if len(w) > 2])
        
        # 카테고리 키워드 추가
        if category:
            suggested_keywords.append(category.lower())
        
        # 기존 키워드와 결합
        all_keywords = list(set(existing_keywords + suggested_keywords))
        
        return {
            "primary_keywords": existing_keywords[:3] if existing_keywords else suggested_keywords[:3],
            "secondary_keywords": suggested_keywords[3:10],
            "long_tail_keywords": self._generate_long_tail_keywords(product_name, category),
            "keyword_volume": len(all_keywords),
            "recommendations": [
                "주요 키워드를 상품명 앞부분에 배치하세요",
                "긴 꼬리 키워드를 상품 설명에 포함하세요"
            ]
        }
    
    def _generate_long_tail_keywords(self, product_name: str, category: str) -> List[str]:
        """긴 꼬리 키워드 생성"""
        long_tail = []
        
        if product_name and category:
            modifiers = ["구매", "추천", "리뷰", "가격", "할인", "배송"]
            for modifier in modifiers:
                long_tail.append(f"{product_name} {modifier}")
                long_tail.append(f"{category} {product_name}")
        
        return long_tail[:5]
    
    def _analyze_content(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """콘텐츠 최적화 분석"""
        description = product_data.get("description", "")
        keywords = product_data.get("search_keywords", [])
        
        content_analysis = {
            "word_count": len(description.split()),
            "keyword_density": {},
            "keyword_placement": {},
            "content_structure": self._analyze_structure(description),
            "recommendations": []
        }
        
        # 키워드 밀도 계산
        if keywords and description:
            for keyword in keywords[:5]:  # 상위 5개 키워드만
                keyword_lower = keyword.lower()
                text_lower = description.lower()
                count = text_lower.count(keyword_lower)
                total_words = len(text_lower.split())
                density = count / total_words if total_words > 0 else 0
                
                content_analysis["keyword_density"][keyword] = {
                    "count": count,
                    "density": round(density, 4),
                    "optimal": self.min_keyword_density <= density <= self.max_keyword_density
                }
                
                if density < self.min_keyword_density:
                    content_analysis["recommendations"].append(
                        f"'{keyword}' 키워드 밀도를 높이세요 (현재: {density:.2%})"
                    )
                elif density > self.max_keyword_density:
                    content_analysis["recommendations"].append(
                        f"'{keyword}' 키워드 밀도를 낮추세요 (현재: {density:.2%}, 키워드 스터핑 의심)"
                    )
        
        # 키워드 배치 분석
        if keywords and description:
            for keyword in keywords[:3]:
                keyword_lower = keyword.lower()
                text_lower = description.lower()
                first_occurrence = text_lower.find(keyword_lower)
                
                content_analysis["keyword_placement"][keyword] = {
                    "in_first_100_chars": first_occurrence < 100 if first_occurrence >= 0 else False,
                    "in_first_paragraph": first_occurrence < len(description.split('\n')[0]) if description else False
                }
        
        return content_analysis
    
    def _analyze_structure(self, description: str) -> Dict[str, Any]:
        """콘텐츠 구조 분석"""
        has_paragraphs = '\n' in description or '<p>' in description
        has_lists = '<li>' in description or '- ' in description or '* ' in description
        has_headings = bool(re.search(r'<h[1-6]>', description))
        
        return {
            "has_paragraphs": has_paragraphs,
            "has_lists": has_lists,
            "has_headings": has_headings,
            "structure_score": sum([has_paragraphs, has_lists, has_headings])
        }
    
    def _extract_semantic_keywords(self, product_data: Dict[str, Any]) -> List[str]:
        """의미론적 키워드 추출"""
        description = product_data.get("description", "")
        product_name = product_data.get("product_name", "")
        category = product_data.get("category", "")
        
        # 간단한 의미론적 키워드 추출 (실제로는 NLP 모델 사용)
        semantic_keywords = []
        
        # 관련 단어 매핑 (예시)
        related_words = {
            "가격": ["비용", "요금", "금액", "할인"],
            "품질": ["재질", "소재", "내구성", "견고"],
            "배송": ["택배", "배달", "발송", "무료배송"]
        }
        
        text = (product_name + " " + description + " " + category).lower()
        
        for main_word, related in related_words.items():
            if main_word in text:
                semantic_keywords.extend(related)
        
        return list(set(semantic_keywords))[:10]
    
    def _analyze_ai_readability(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """AI 가독성 분석"""
        description = product_data.get("description", "")
        
        readability = {
            "sentence_length_avg": 0,
            "paragraph_count": len(description.split('\n')),
            "has_bullet_points": bool(re.search(r'[-*•]', description)),
            "has_numbers": bool(re.search(r'\d+', description)),
            "readability_score": 0
        }
        
        if description:
            sentences = re.split(r'[.!?。！？]', description)
            sentences = [s.strip() for s in sentences if s.strip()]
            if sentences:
                readability["sentence_length_avg"] = sum(len(s.split()) for s in sentences) / len(sentences)
        
        # 가독성 점수 계산
        score = 0
        if readability["sentence_length_avg"] < 20:
            score += 25
        if readability["paragraph_count"] > 2:
            score += 25
        if readability["has_bullet_points"]:
            score += 25
        if readability["has_numbers"]:
            score += 25
        
        readability["readability_score"] = score
        
        return readability
    
    def _calculate_ai_seo_score(self, analysis: Dict[str, Any]) -> int:
        """AI SEO 점수 계산"""
        score = 0
        
        # 키워드 리서치 점수
        if analysis["keyword_research"].get("primary_keywords"):
            score += 20
        
        # 콘텐츠 최적화 점수
        content_score = analysis["content_optimization"].get("content_structure", {}).get("structure_score", 0)
        score += content_score * 10
        
        # AI 가독성 점수
        readability_score = analysis["ai_readability"].get("readability_score", 0)
        score += readability_score * 0.3
        
        return min(100, int(score))
    
    async def optimize_content(self, content: str, keywords: List[str]) -> Dict[str, Any]:
        """
        콘텐츠 최적화 제안
        
        Args:
            content: 최적화할 콘텐츠
            keywords: 타겟 키워드 목록
            
        Returns:
            최적화 제안
        """
        optimized = {
            "original_content": content,
            "optimized_suggestions": [],
            "keyword_insertion_points": [],
            "structure_improvements": []
        }
        
        # 키워드 삽입 지점 제안
        for keyword in keywords[:3]:
            if keyword.lower() not in content.lower():
                optimized["keyword_insertion_points"].append({
                    "keyword": keyword,
                    "suggested_position": "첫 번째 문단",
                    "suggestion": f"'{keyword}' 키워드를 첫 번째 문단에 추가하세요"
                })
        
        # 구조 개선 제안
        if not re.search(r'[-*•]', content):
            optimized["structure_improvements"].append("불릿 포인트를 사용하여 가독성을 높이세요")
        
        if len(content.split('\n')) < 3:
            optimized["structure_improvements"].append("문단을 나누어 구조화하세요")
        
        return optimized
