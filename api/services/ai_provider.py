"""
AI 제공자 선택 (Gemini 우선, OpenAI 폴백 또는 환경 변수 지정)
분석 강화, 채팅, 추천에서 단일 진입점으로 사용.
"""
import os
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

# 환경 변수: AI_PROVIDER=gemini | openai (기본: gemini)
_PROVIDER = (os.getenv("AI_PROVIDER") or "gemini").strip().lower()
if _PROVIDER not in ("gemini", "openai"):
    _PROVIDER = "gemini"


def get_ai_service():
    """
    설정에 따라 사용 가능한 AI 서비스 인스턴스 반환.
    - AI_PROVIDER=openai: OpenAI만 사용 (OPENAI_API_KEY 필요)
    - AI_PROVIDER=gemini (기본): Gemini 우선, 없으면 OpenAI 폴백

    Returns:
        GeminiService 또는 OpenAIService 인스턴스 (사용 가능한 것).
        둘 다 없으면 None.
    """
    if _PROVIDER == "openai":
        from .openai_service import OpenAIService
        svc = OpenAIService()
        if svc.available:
            return svc
        return None

    # gemini 우선
    try:
        from .gemini_service import GeminiService
        gemini = GeminiService()
        if gemini.model:
            return gemini
    except Exception as e:
        logger.debug("Gemini 서비스 사용 불가: %s", str(e))

    try:
        from .openai_service import OpenAIService
        openai_svc = OpenAIService()
        if openai_svc.available:
            logger.info("Gemini 미사용, OpenAI로 폴백합니다.")
            return openai_svc
    except Exception as e:
        logger.debug("OpenAI 서비스 사용 불가: %s", str(e))

    return None


def get_ai_service_for_chat():
    """채팅용 AI 서비스 (generate_text 호환)."""
    return get_ai_service()


def get_ai_service_for_analysis():
    """분석 강화용 AI 서비스 (enhance_analysis_with_ai 호환)."""
    return get_ai_service()


def get_ai_service_for_recommendations():
    """추천 생성용 AI 서비스 (generate_recommendations_with_ai 호환)."""
    return get_ai_service()
