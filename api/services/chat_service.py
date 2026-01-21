"""
챗봇 서비스
분석 리포트에 대한 질문에 답변하는 AI 챗봇
"""
from typing import Dict, Any, Optional
import os
import json
import logging

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not available. Chat service will use fallback responses.")

# Gemini 서비스 임포트
try:
    from .gemini_service import GeminiService
    GEMINI_SERVICE_AVAILABLE = True
except ImportError:
    GEMINI_SERVICE_AVAILABLE = False
    GeminiService = None


class ChatService:
    """챗봇 서비스 클래스"""
    
    def __init__(self):
        self.openai_client = None
        self.gemini_service = None
        
        # OpenAI 초기화
        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
            else:
                logger.warning("OPENAI_API_KEY not set. Chat service will use fallback responses.")
        
        # Gemini 초기화
        if GEMINI_SERVICE_AVAILABLE and GeminiService:
            try:
                self.gemini_service = GeminiService()
                if self.gemini_service.model:
                    logger.info("Gemini 서비스가 활성화되었습니다.")
            except Exception as e:
                logger.warning(f"Gemini 서비스 초기화 실패: {str(e)}")
    
    async def generate_response(
        self,
        message: str,
        analysis_result: Optional[Dict[str, Any]] = None,
        analysis_id: Optional[str] = None
    ) -> str:
        """
        사용자 메시지에 대한 응답 생성
        
        Args:
            message: 사용자 메시지
            analysis_result: 분석 결과 데이터
            analysis_id: 분석 ID
            
        Returns:
            AI 응답 메시지
        """
        # 우선순위: Gemini > OpenAI > Fallback
        if self.gemini_service and self.gemini_service.model and analysis_result:
            return await self._generate_gemini_response(message, analysis_result)
        elif self.openai_client and analysis_result:
            return await self._generate_openai_response(message, analysis_result)
        else:
            return self._generate_fallback_response(message, analysis_result)
    
    async def _generate_openai_response(
        self,
        message: str,
        analysis_result: Dict[str, Any]
    ) -> str:
        """OpenAI를 사용한 응답 생성"""
        try:
            # 분석 결과를 요약하여 컨텍스트로 사용
            context = self._build_context(analysis_result)
            
            system_prompt = """당신은 Qoo10 상품 분석 리포트 전문가입니다. 
사용자가 리포트에 대해 질문하면, 리포트 내용을 바탕으로 명확하고 실용적인 답변을 제공하세요.

답변 시 다음을 고려하세요:
1. 리포트의 구체적인 데이터와 점수를 참고하여 답변
2. 실제로 적용 가능한 구체적인 액션 아이템 제시
3. 우선순위가 높은 개선 사항부터 설명
4. 한국어로 친절하고 전문적으로 답변
5. 필요시 리포트의 특정 섹션을 언급

답변은 대화 형식으로 자연스럽게 작성하세요."""

            user_prompt = f"""다음은 분석 리포트의 요약입니다:

{context}

사용자 질문: {message}

위 리포트 내용을 바탕으로 질문에 답변해주세요."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # 또는 "gpt-3.5-turbo"로 변경 가능
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {str(e)}")
            return self._generate_fallback_response(message, analysis_result)
    
    async def _generate_gemini_response(
        self,
        message: str,
        analysis_result: Dict[str, Any]
    ) -> str:
        """Gemini를 사용한 응답 생성"""
        try:
            context = self._build_context(analysis_result)
            
            system_prompt = """당신은 Qoo10 상품 분석 리포트 전문가입니다. 
사용자가 리포트에 대해 질문하면, 리포트 내용을 바탕으로 명확하고 실용적인 답변을 제공하세요.

답변 시 다음을 고려하세요:
1. 리포트의 구체적인 데이터와 점수를 참고하여 답변
2. 실제로 적용 가능한 구체적인 액션 아이템 제시
3. 우선순위가 높은 개선 사항부터 설명
4. 한국어로 친절하고 전문적으로 답변
5. 필요시 리포트의 특정 섹션을 언급

답변은 대화 형식으로 자연스럽게 작성하세요."""
            
            user_prompt = f"""다음은 분석 리포트의 요약입니다:

{context}

사용자 질문: {message}

위 리포트 내용을 바탕으로 질문에 답변해주세요."""
            
            response = await self.gemini_service.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=1000
            )
            
            if response:
                return response.strip()
            else:
                # Gemini 실패 시 OpenAI로 폴백
                if self.openai_client:
                    return await self._generate_openai_response(message, analysis_result)
                return self._generate_fallback_response(message, analysis_result)
            
        except Exception as e:
            logger.error(f"Error generating Gemini response: {str(e)}")
            # Gemini 실패 시 OpenAI로 폴백
            if self.openai_client:
                return await self._generate_openai_response(message, analysis_result)
            return self._generate_fallback_response(message, analysis_result)
    
    def _build_context(self, analysis_result: Dict[str, Any]) -> str:
        """분석 결과를 컨텍스트 문자열로 변환"""
        context_parts = []
        
        # 종합 점수
        product_analysis = analysis_result.get("product_analysis", {})
        shop_analysis = analysis_result.get("shop_analysis", {})
        overall_score = product_analysis.get("overall_score") or shop_analysis.get("overall_score", 0)
        context_parts.append(f"종합 점수: {overall_score}/100")
        
        # 상품 분석 세부 점수
        if product_analysis:
            image_score = product_analysis.get("image_analysis", {}).get("score", 0)
            desc_score = product_analysis.get("description_analysis", {}).get("score", 0)
            price_score = product_analysis.get("price_analysis", {}).get("score", 0)
            review_score = product_analysis.get("review_analysis", {}).get("score", 0)
            context_parts.append(f"세부 점수 - 이미지: {image_score}, 설명: {desc_score}, 가격: {price_score}, 리뷰: {review_score}")
        
        # 추천 사항
        recommendations = analysis_result.get("recommendations", [])
        if recommendations:
            high_priority = [r for r in recommendations if r.get("priority") == "high"]
            medium_priority = [r for r in recommendations if r.get("priority") == "medium"]
            low_priority = [r for r in recommendations if r.get("priority") == "low"]
            
            context_parts.append(f"\n우선순위별 추천 사항:")
            if high_priority:
                context_parts.append(f"- High Priority ({len(high_priority)}개):")
                for rec in high_priority[:3]:  # 상위 3개만
                    context_parts.append(f"  • {rec.get('title', '')}: {rec.get('description', '')}")
            if medium_priority:
                context_parts.append(f"- Medium Priority ({len(medium_priority)}개)")
            if low_priority:
                context_parts.append(f"- Low Priority ({len(low_priority)}개)")
        
        # 체크리스트
        checklist = analysis_result.get("checklist", {})
        if checklist:
            completion = checklist.get("overall_completion", 0)
            context_parts.append(f"\n체크리스트 완성도: {completion}%")
        
        # 경쟁사 분석
        competitor_analysis = analysis_result.get("competitor_analysis")
        if competitor_analysis:
            target = competitor_analysis.get("target_product", {})
            comparison = competitor_analysis.get("comparison", {})
            context_parts.append(f"\n경쟁사 분석:")
            context_parts.append(f"- 가격 포지션: {comparison.get('price_position', 'N/A')}")
            context_parts.append(f"- 평점 포지션: {comparison.get('rating_position', 'N/A')}")
        
        return "\n".join(context_parts)
    
    def _generate_fallback_response(
        self,
        message: str,
        analysis_result: Optional[Dict[str, Any]] = None
    ) -> str:
        """OpenAI를 사용할 수 없을 때의 대체 응답"""
        message_lower = message.lower()
        
        # 키워드 기반 응답
        if any(keyword in message_lower for keyword in ["점수", "점수가", "점수는"]):
            if analysis_result:
                product_analysis = analysis_result.get("product_analysis", {})
                shop_analysis = analysis_result.get("shop_analysis", {})
                overall_score = product_analysis.get("overall_score") or shop_analysis.get("overall_score", 0)
                return f"현재 종합 점수는 {overall_score}점입니다. 리포트의 각 영역별 점수를 확인하시고, 개선이 필요한 영역부터 우선적으로 작업하시는 것을 권장합니다."
            return "점수 정보를 확인할 수 없습니다. 리포트를 다시 로드해주세요."
        
        elif any(keyword in message_lower for keyword in ["개선", "개선사항", "개선할", "어떻게"]):
            if analysis_result:
                recommendations = analysis_result.get("recommendations", [])
                high_priority = [r for r in recommendations if r.get("priority") == "high"]
                if high_priority:
                    return f"긴급 개선이 필요한 항목이 {len(high_priority)}개 있습니다. 리포트의 '매출 강화 아이디어' 탭에서 High Priority 항목을 확인하시고, 각 항목의 액션 아이템을 단계적으로 실행하시면 됩니다."
            return "개선 사항은 리포트의 '매출 강화 아이디어' 탭에서 확인하실 수 있습니다."
        
        elif any(keyword in message_lower for keyword in ["우선순위", "우선", "먼저", "빠르게"]):
            if analysis_result:
                recommendations = analysis_result.get("recommendations", [])
                high_priority = [r for r in recommendations if r.get("priority") == "high"]
                if high_priority:
                    first_rec = high_priority[0]
                    return f"가장 우선적으로 개선하실 항목은 '{first_rec.get('title', '')}'입니다. {first_rec.get('description', '')} 이 항목을 개선하시면 {first_rec.get('expected_impact', '긍정적인 효과')}를 기대할 수 있습니다."
            return "우선순위가 높은 개선 사항은 리포트의 High Priority 섹션에서 확인하실 수 있습니다."
        
        elif any(keyword in message_lower for keyword in ["경쟁사", "경쟁", "비교"]):
            if analysis_result and analysis_result.get("competitor_analysis"):
                comp = analysis_result.get("competitor_analysis", {})
                comparison = comp.get("comparison", {})
                return f"경쟁사 분석 결과, 가격 포지션은 {comparison.get('price_position', 'N/A')}이며, 평점 포지션은 {comparison.get('rating_position', 'N/A')}입니다. 자세한 내용은 리포트의 경쟁사 비교 섹션에서 확인하실 수 있습니다."
            return "경쟁사 분석 정보는 리포트의 경쟁사 비교 섹션에서 확인하실 수 있습니다."
        
        else:
            return "죄송합니다. 더 정확한 답변을 위해 OpenAI API 키가 필요합니다. 현재는 기본 응답만 제공됩니다. 리포트의 각 섹션을 직접 확인하시거나, 구체적인 질문을 해주시면 더 도움을 드릴 수 있습니다."
