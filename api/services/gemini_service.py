"""
Google Gemini API 서비스
Gemini API를 사용하여 AI 분석 및 추천을 제공합니다.
"""
from typing import Dict, Any, List, Optional
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Google Generative AI 임포트
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google Generative AI library not available. Please install: pip install google-generativeai")


class GeminiService:
    """Google Gemini API 서비스"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Gemini 서비스 초기화
        
        Args:
            api_key: Gemini API 키 (환경 변수 GEMINI_API_KEY에서도 로드 가능)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None
        
        if not GEMINI_AVAILABLE:
            logger.warning("Google Generative AI library not available.")
            return
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set. Gemini service will not be available.")
            return
        
        try:
            genai.configure(api_key=self.api_key)
            # 사용 가능한 모델 확인 및 선택
            # gemini-2.5-flash (빠르고 비용 효율적) 또는 gemini-2.5-pro (더 강력)
            try:
                # 먼저 gemini-2.5-flash 시도 (더 빠르고 비용 효율적)
                self.model = genai.GenerativeModel('gemini-2.5-flash')
                logger.info("Gemini API 서비스가 활성화되었습니다. (모델: gemini-2.5-flash)")
            except Exception:
                # gemini-2.5-flash 실패 시 gemini-2.5-pro 시도
                try:
                    self.model = genai.GenerativeModel('gemini-2.5-pro')
                    logger.info("Gemini API 서비스가 활성화되었습니다. (모델: gemini-2.5-pro)")
                except Exception as e2:
                    logger.error(f"Gemini 모델 초기화 실패: {str(e2)}")
                    self.model = None
        except Exception as e:
            logger.error(f"Gemini API 초기화 실패: {str(e)}")
            self.model = None
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Optional[str]:
        """
        텍스트 생성
        
        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트 (선택사항)
            temperature: 생성 온도 (0.0 ~ 1.0)
            max_tokens: 최대 토큰 수 (선택사항)
            
        Returns:
            생성된 텍스트 또는 None
        """
        if not self.model:
            return None
        
        try:
            # 시스템 프롬프트가 있으면 프롬프트에 포함
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # 생성 설정
            generation_config = {
                "temperature": temperature,
            }
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens
            
            # 텍스트 생성
            response = await self._generate_async(full_prompt, generation_config)
            return response.text if response else None
            
        except Exception as e:
            logger.error(f"Gemini API 텍스트 생성 오류: {str(e)}")
            return None
    
    async def _generate_async(self, prompt: str, config: Dict[str, Any]) -> Any:
        """비동기 텍스트 생성 (동기 함수를 비동기로 래핑)"""
        import asyncio
        
        def _sync_generate():
            try:
                # GenerationConfig 객체 생성
                gen_config_dict = {
                    "temperature": config.get("temperature", 0.7)
                }
                if "max_output_tokens" in config:
                    gen_config_dict["max_output_tokens"] = config["max_output_tokens"]
                
                generation_config = genai.types.GenerationConfig(**gen_config_dict)
                return self.model.generate_content(prompt, generation_config=generation_config)
            except Exception as e:
                logger.error(f"Gemini generate_content 오류: {str(e)}")
                raise
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_generate)
    
    async def analyze_product_with_ai(
        self,
        product_data: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Gemini를 사용한 상품 분석 강화
        
        Args:
            product_data: 크롤러 데이터
            analysis_result: 기존 분석 결과
            
        Returns:
            AI 강화 분석 결과
        """
        if not self.model:
            return {}
        
        try:
            # 분석 컨텍스트 구성
            context = self._build_analysis_context(product_data, analysis_result)
            
            system_prompt = """당신은 Qoo10 상품 분석 전문가입니다. 
제공된 상품 데이터와 분석 결과를 바탕으로 심층적인 인사이트와 개선 제안을 제공하세요.

분석 시 다음을 고려하세요:
1. 상품의 강점과 약점 파악
2. 경쟁력 있는 요소 식별
3. 구체적이고 실행 가능한 개선 제안
4. 우선순위가 높은 액션 아이템 제시
5. 한국어로 명확하고 전문적으로 작성"""
            
            user_prompt = f"""다음은 상품 데이터와 분석 결과입니다:

{context}

위 정보를 바탕으로 다음을 분석해주세요:
1. 상품의 주요 강점 3가지
2. 개선이 필요한 주요 약점 3가지
3. 즉시 실행 가능한 우선순위 액션 아이템 5가지
4. 예상 효과 및 기대 결과

JSON 형식으로 응답해주세요:
{{
    "strengths": ["강점1", "강점2", "강점3"],
    "weaknesses": ["약점1", "약점2", "약점3"],
    "action_items": [
        {{"title": "액션1", "priority": "high", "description": "설명", "expected_impact": "효과"}},
        ...
    ],
    "insights": "종합 인사이트"
}}"""
            
            response_text = await self.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7
            )
            
            if response_text:
                # JSON 응답 파싱 시도
                try:
                    # JSON 코드 블록 제거
                    response_text = response_text.strip()
                    if "```json" in response_text:
                        response_text = response_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in response_text:
                        response_text = response_text.split("```")[1].split("```")[0].strip()
                    
                    ai_analysis = json.loads(response_text)
                    return ai_analysis
                except json.JSONDecodeError:
                    # JSON 파싱 실패 시 텍스트로 반환
                    return {
                        "raw_response": response_text,
                        "parsed": False
                    }
            
            return {}
            
        except Exception as e:
            logger.error(f"Gemini 상품 분석 오류: {str(e)}")
            return {}
    
    async def generate_recommendations_with_ai(
        self,
        product_data: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Gemini를 사용한 추천 생성
        
        Args:
            product_data: 크롤러 데이터
            analysis_result: 분석 결과
            
        Returns:
            AI 생성 추천 리스트
        """
        if not self.model:
            return []
        
        try:
            context = self._build_analysis_context(product_data, analysis_result)
            
            system_prompt = """당신은 Qoo10 매출 강화 전문가입니다.
상품 데이터와 분석 결과를 바탕으로 실전적이고 실행 가능한 매출 강화 아이디어를 제안하세요."""
            
            user_prompt = f"""다음은 상품 데이터와 분석 결과입니다:

{context}

위 정보를 바탕으로 매출 강화를 위한 구체적인 추천 아이디어 5-10개를 제안해주세요.
각 추천은 다음 형식으로 작성해주세요:
- title: 추천 제목
- priority: high/medium/low
- description: 상세 설명
- action_items: 실행 방법 리스트
- expected_impact: 예상 효과

JSON 형식으로 응답해주세요:
{{
    "recommendations": [
        {{
            "title": "추천 제목",
            "priority": "high",
            "description": "상세 설명",
            "action_items": ["액션1", "액션2"],
            "expected_impact": "예상 효과"
        }},
        ...
    ]
}}"""
            
            response_text = await self.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.8
            )
            
            if response_text:
                try:
                    # JSON 파싱
                    response_text = response_text.strip()
                    if "```json" in response_text:
                        response_text = response_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in response_text:
                        response_text = response_text.split("```")[1].split("```")[0].strip()
                    
                    result = json.loads(response_text)
                    return result.get("recommendations", [])
                except json.JSONDecodeError:
                    logger.warning("Gemini 추천 생성 JSON 파싱 실패")
                    return []
            
            return []
            
        except Exception as e:
            logger.error(f"Gemini 추천 생성 오류: {str(e)}")
            return []
    
    def _build_analysis_context(
        self,
        product_data: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> str:
        """분석 컨텍스트 구성"""
        context_parts = []
        
        # 상품 기본 정보
        context_parts.append("=== 상품 기본 정보 ===")
        context_parts.append(f"상품명: {product_data.get('product_name', 'N/A')}")
        context_parts.append(f"상품 코드: {product_data.get('product_code', 'N/A')}")
        context_parts.append(f"카테고리: {product_data.get('category', 'N/A')}")
        context_parts.append(f"브랜드: {product_data.get('brand', 'N/A')}")
        
        # 가격 정보
        price = product_data.get("price", {})
        context_parts.append(f"\n=== 가격 정보 ===")
        context_parts.append(f"판매가: {price.get('sale_price', 'N/A')}円")
        context_parts.append(f"정가: {price.get('original_price', 'N/A')}円")
        context_parts.append(f"할인율: {price.get('discount_rate', 0)}%")
        
        # 리뷰 정보
        reviews = product_data.get("reviews", {})
        context_parts.append(f"\n=== 리뷰 정보 ===")
        context_parts.append(f"리뷰 수: {reviews.get('review_count', 0)}개")
        context_parts.append(f"평점: {reviews.get('rating', 0.0)}/5.0")
        
        # 이미지 정보
        images = product_data.get("images", {})
        context_parts.append(f"\n=== 이미지 정보 ===")
        context_parts.append(f"상세 이미지 개수: {len(images.get('detail_images', []))}개")
        
        # 분석 결과
        product_analysis = analysis_result.get("product_analysis", {})
        context_parts.append(f"\n=== 분석 결과 ===")
        context_parts.append(f"종합 점수: {product_analysis.get('overall_score', 0)}/100")
        context_parts.append(f"이미지 분석 점수: {product_analysis.get('image_analysis', {}).get('score', 0)}/100")
        context_parts.append(f"설명 분석 점수: {product_analysis.get('description_analysis', {}).get('score', 0)}/100")
        context_parts.append(f"가격 분석 점수: {product_analysis.get('price_analysis', {}).get('score', 0)}/100")
        context_parts.append(f"리뷰 분석 점수: {product_analysis.get('review_analysis', {}).get('score', 0)}/100")
        context_parts.append(f"SEO 분석 점수: {product_analysis.get('seo_analysis', {}).get('score', 0)}/100")
        
        # 체크리스트
        checklist = analysis_result.get("checklist", {})
        if checklist:
            context_parts.append(f"\n=== 체크리스트 ===")
            context_parts.append(f"전체 완성도: {checklist.get('overall_completion', 0)}%")
        
        return "\n".join(context_parts)
    
    async def enhance_analysis_with_ai(
        self,
        product_data: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        기존 분석 결과를 AI로 강화
        
        Args:
            product_data: 크롤러 데이터
            analysis_result: 기존 분석 결과
            
        Returns:
            AI 강화된 분석 결과
        """
        if not self.model:
            return analysis_result
        
        try:
            # AI 분석 수행
            ai_analysis = await self.analyze_product_with_ai(product_data, analysis_result)
            
            # 기존 분석 결과에 AI 인사이트 추가
            enhanced_result = analysis_result.copy()
            
            if "product_analysis" not in enhanced_result:
                enhanced_result["product_analysis"] = {}
            
            # AI 인사이트 추가
            enhanced_result["product_analysis"]["ai_insights"] = {
                "strengths": ai_analysis.get("strengths", []),
                "weaknesses": ai_analysis.get("weaknesses", []),
                "action_items": ai_analysis.get("action_items", []),
                "insights": ai_analysis.get("insights", ""),
                "generated_by": "gemini"
            }
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Gemini 분석 강화 오류: {str(e)}")
            return analysis_result
