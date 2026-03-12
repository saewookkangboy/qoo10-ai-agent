"""
상세 이미지(긴 이미지) 내용 추출 서비스.

상품 상세 이미지 URL 목록을 받아 Vision API(OpenAI/Gemini)로 이미지 내 텍스트를 추출하고,
분석(설명 보강·점수)에 쓸 수 있도록 product_data["detail_image_contents"]에 담는다.

참고: doc/agents/Detail-Image-Content-Research.md
"""
from typing import Dict, Any, List, Optional
import os
import asyncio
import logging

logger = logging.getLogger(__name__)

# 환경 변수: 기능 on/off, 최대 처리 이미지 수
ENABLE_ENV = "ENABLE_DETAIL_IMAGE_EXTRACTION"
MAX_IMAGES_ENV = "DETAIL_IMAGE_MAX_COUNT"
DEFAULT_MAX_IMAGES = 5


def _is_enabled() -> bool:
    return os.getenv(ENABLE_ENV, "").strip().lower() in ("1", "true", "yes")


def _max_images() -> int:
    try:
        return max(0, int(os.getenv(MAX_IMAGES_ENV, str(DEFAULT_MAX_IMAGES))))
    except ValueError:
        return DEFAULT_MAX_IMAGES


async def extract_detail_image_contents(product_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    product_data["images"]["detail_images"] URL 목록에서 텍스트를 추출해
    [{ "url", "text", "error"? }, ...] 형태로 반환한다.
    product_data 자체는 수정하지 않는다.
    """
    if not _is_enabled():
        return []
    images = product_data.get("images") or {}
    urls = images.get("detail_images") or []
    if not urls or not isinstance(urls, list):
        return []
    max_n = _max_images()
    to_process = urls[:max_n]

    try:
        from services.ai_provider import get_ai_service
        svc = get_ai_service()
    except Exception as e:
        logger.debug("AI 서비스 로드 실패(상세 이미지 추출 스킵): %s", str(e))
        return []

    if not svc or not getattr(svc, "extract_text_from_image_url", None):
        return []

    results: List[Dict[str, Any]] = []
    for url in to_process:
        if not url or not isinstance(url, str):
            continue
        try:
            text = await svc.extract_text_from_image_url(url)
            results.append({
                "url": url,
                "text": text if text else "",
            })
            if text:
                logger.debug("상세 이미지 텍스트 추출 완료: url=%s, len=%s", url[:60], len(text))
        except Exception as e:
            results.append({
                "url": url,
                "text": "",
                "error": str(e),
            })
            logger.debug("상세 이미지 추출 실패 url=%s: %s", url[:50], str(e))
        await asyncio.sleep(0.3)

    return results


def merge_detail_contents_into_product(
    product_data: Dict[str, Any],
    detail_contents: List[Dict[str, Any]],
) -> None:
    """
    추출 결과를 product_data["detail_image_contents"]에 넣고,
    설명 분석용 보조 텍스트를 product_data["detail_image_text_merged"]에 합쳐 둔다.
    """
    if not detail_contents:
        return
    product_data["detail_image_contents"] = detail_contents
    merged = []
    for item in detail_contents:
        t = (item.get("text") or "").strip()
        if t:
            merged.append(t)
    if merged:
        product_data["detail_image_text_merged"] = "\n\n".join(merged)
