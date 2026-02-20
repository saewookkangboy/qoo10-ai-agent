"""
OpenAI API 서비스 (Chat Completions)
분석 강화, 채팅, 추천 생성에 사용. 환경 변수 OPENAI_API_KEY 사용.
"""
from typing import Dict, Any, List, Optional
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None
    logger.warning(
        "OpenAI library not available. Install with: pip install openai"
    )


class OpenAIService:
    """OpenAI Chat Completions API 서비스"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Args:
            api_key: OpenAI API 키 (미지정 시 환경 변수 OPENAI_API_KEY 사용)
            model: 모델명 (미지정 시 환경 변수 AI_MODEL_OPENAI, 기본 gpt-4o-mini)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = (model or os.getenv("AI_MODEL_OPENAI") or "gpt-4o-mini").strip()
        self._client: Optional[Any] = None

        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI library not available. OpenAI service disabled.")
            return

        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set. OpenAI service will not be available.")
            return

        try:
            self._client = AsyncOpenAI(api_key=self.api_key)
            logger.info("OpenAI API 서비스가 활성화되었습니다. (모델: %s)", self.model)
        except Exception as e:
            logger.error("OpenAI API 초기화 실패: %s", str(e))
            self._client = None

    def _max_tokens(self, override: Optional[int] = None) -> Optional[int]:
        """환경 변수 AI_MAX_TOKENS 또는 인자 값 반환"""
        if override is not None:
            return override
        val = os.getenv("AI_MAX_TOKENS", "").strip()
        if not val:
            return None
        try:
            return int(val)
        except ValueError:
            return None

    @property
    def available(self) -> bool:
        """서비스 사용 가능 여부"""
        return bool(OPENAI_AVAILABLE and self._client and self.api_key)

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Optional[str]:
        """
        텍스트 생성 (Chat Completions)

        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트 (선택)
            temperature: 0.0 ~ 1.0
            max_tokens: 최대 출력 토큰 (None이면 환경 변수 또는 미지정)

        Returns:
            생성된 텍스트 또는 None
        """
        if not self._client:
            return None

        max_tok = max_tokens if max_tokens is not None else self._max_tokens()
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            kwargs: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }
            if max_tok is not None:
                kwargs["max_tokens"] = max_tok

            response = await self._client.chat.completions.create(**kwargs)
            choice = response.choices[0] if response.choices else None
            if choice and getattr(choice, "message", None):
                text = choice.message.content
                return text.strip() if text else None
            return None
        except Exception as e:
            logger.error("OpenAI 텍스트 생성 오류: %s", str(e), exc_info=True)
            return None

    def _build_analysis_context(
        self,
        product_data: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> str:
        """분석 컨텍스트 문자열 구성 (Gemini 서비스와 동일 구조)"""
        context_parts = []

        context_parts.append("=== 상품 기본 정보 ===")
        context_parts.append(f"상품명: {product_data.get('product_name', 'N/A')}")
        context_parts.append(f"상품 코드: {product_data.get('product_code', 'N/A')}")
        context_parts.append(f"카테고리: {product_data.get('category', 'N/A')}")
        context_parts.append(f"브랜드: {product_data.get('brand', 'N/A')}")

        price = product_data.get("price", {})
        context_parts.append("\n=== 가격 정보 ===")
        context_parts.append(f"판매가: {price.get('sale_price', 'N/A')}円")
        context_parts.append(f"정가: {price.get('original_price', 'N/A')}円")
        context_parts.append(f"할인율: {price.get('discount_rate', 0)}%")

        reviews = product_data.get("reviews", {})
        context_parts.append("\n=== 리뷰 정보 ===")
        context_parts.append(f"리뷰 수: {reviews.get('review_count', 0)}개")
        context_parts.append(f"평점: {reviews.get('rating', 0.0)}/5.0")

        images = product_data.get("images", {})
        context_parts.append("\n=== 이미지 정보 ===")
        context_parts.append(f"상세 이미지 개수: {len(images.get('detail_images', []))}개")

        product_analysis = analysis_result.get("product_analysis") or analysis_result.get("shop_analysis") or {}
        context_parts.append("\n=== 분석 결과 ===")
        context_parts.append(f"종합 점수: {product_analysis.get('overall_score', 0)}/100")
        context_parts.append(f"이미지 분석 점수: {product_analysis.get('image_analysis', {}).get('score', 0)}/100")
        context_parts.append(f"설명 분석 점수: {product_analysis.get('description_analysis', {}).get('score', 0)}/100")
        context_parts.append(f"가격 분석 점수: {product_analysis.get('price_analysis', {}).get('score', 0)}/100")
        context_parts.append(f"리뷰 분석 점수: {product_analysis.get('review_analysis', {}).get('score', 0)}/100")
        context_parts.append(f"SEO 분석 점수: {product_analysis.get('seo_analysis', {}).get('score', 0)}/100")

        checklist = analysis_result.get("checklist", {})
        if checklist:
            context_parts.append("\n=== 체크리스트 ===")
            context_parts.append(f"전체 완성도: {checklist.get('overall_completion', 0)}%")

        return "\n".join(context_parts)

    async def analyze_product_with_ai(
        self,
        product_data: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """OpenAI를 사용한 상품 분석 강화 (Gemini와 동일 JSON 스키마)"""
        if not self._client:
            return {}

        try:
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
                response_text = response_text.strip()
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                return json.loads(response_text)
            return {}
        except json.JSONDecodeError as e:
            logger.warning("OpenAI 분석 응답 JSON 파싱 실패: %s", str(e))
            return {}
        except Exception as e:
            logger.error("OpenAI 상품 분석 오류: %s", str(e), exc_info=True)
            return {}

    async def generate_recommendations_with_ai(
        self,
        product_data: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """OpenAI를 사용한 추천 생성 (Gemini와 동일 JSON 스키마)"""
        if not self._client:
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
                response_text = response_text.strip()
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                result = json.loads(response_text)
                return result.get("recommendations", [])
            return []
        except json.JSONDecodeError:
            logger.warning("OpenAI 추천 생성 JSON 파싱 실패")
            return []
        except Exception as e:
            logger.error("OpenAI 추천 생성 오류: %s", str(e), exc_info=True)
            return []

    async def enhance_analysis_with_ai(
        self,
        product_data: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """기존 분석 결과를 AI로 강화 (product_analysis 또는 shop_analysis 구조 유지)"""
        if not self._client:
            return analysis_result

        try:
            ai_analysis = await self.analyze_product_with_ai(product_data, analysis_result)
            enhanced_result = dict(analysis_result)

            if "product_analysis" in enhanced_result:
                if not isinstance(enhanced_result["product_analysis"], dict):
                    enhanced_result["product_analysis"] = {}
                enhanced_result["product_analysis"]["ai_insights"] = {
                    "strengths": ai_analysis.get("strengths", []),
                    "weaknesses": ai_analysis.get("weaknesses", []),
                    "action_items": ai_analysis.get("action_items", []),
                    "insights": ai_analysis.get("insights", ""),
                    "generated_by": "openai"
                }
            if "shop_analysis" in enhanced_result:
                if not isinstance(enhanced_result["shop_analysis"], dict):
                    enhanced_result["shop_analysis"] = {}
                enhanced_result["shop_analysis"]["ai_insights"] = {
                    "strengths": ai_analysis.get("strengths", []),
                    "weaknesses": ai_analysis.get("weaknesses", []),
                    "action_items": ai_analysis.get("action_items", []),
                    "insights": ai_analysis.get("insights", ""),
                    "generated_by": "openai"
                }

            return enhanced_result
        except Exception as e:
            logger.error("OpenAI 분석 강화 오류: %s", str(e), exc_info=True)
            return analysis_result
