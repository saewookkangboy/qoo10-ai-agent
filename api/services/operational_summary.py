"""
운영 포인트·의사결정 요약 서비스 (Report & Output Agent 연동)
상품 상세 페이지 분석 결과를 Qoo10 판매자 관점에서 운영 포인트와 핵심 의사결정으로 정리합니다.
"""
from typing import Dict, Any, List, Optional

# 분석 영역 라벨 (한국어)
SECTION_LABELS = {
    "image_analysis": "이미지",
    "description_analysis": "상품 설명",
    "price_analysis": "가격",
    "review_analysis": "리뷰",
    "seo_analysis": "SEO",
    "page_structure_analysis": "페이지 구조",
}


def build_operational_summary(
    product_analysis: Optional[Dict[str, Any]] = None,
    recommendations: Optional[List[Dict[str, Any]]] = None,
    checklist: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    product_analysis, recommendations, checklist로부터 운영 포인트와 핵심 의사결정을 생성합니다.

    Returns:
        - summary_text: 한 줄 요약 (UI용)
        - operational_points: [{ area, point, impact, source }]
        - key_decisions: [{ decision, reason, priority, action }]
    """
    operational_points: List[Dict[str, Any]] = []
    key_decisions: List[Dict[str, Any]] = []
    seen_point_keys: set = set()

    # 1) 분석 결과에서 저득점 영역 → 운영 포인트
    if product_analysis:
        overall = product_analysis.get("overall_score", 0)
        for section_key, label in SECTION_LABELS.items():
            section = product_analysis.get(section_key)
            if not section or not isinstance(section, dict):
                continue
            score = section.get("score", 0)
            if not isinstance(score, (int, float)):
                score = 0
            if score < 70:
                recs = section.get("recommendations") or []
                point = recs[0] if recs else f"{label} 영역 점수가 낮습니다({score}/100). 개선이 필요합니다."
                key = (label, point[:80])
                if key not in seen_point_keys:
                    seen_point_keys.add(key)
                    operational_points.append({
                        "area": label,
                        "point": point,
                        "impact": "매출·전환율에 직결",
                        "source": "analysis",
                    })
        if overall < 60 and not operational_points:
            operational_points.append({
                "area": "종합",
                "point": f"종합 점수가 {overall}점으로 개선이 필요합니다. 이미지·설명·가격·리뷰·SEO를 점검하세요.",
                "impact": "전체 상품 경쟁력",
                "source": "analysis",
            })

    # 2) High/Medium 추천 → 핵심 의사결정 (중복 제목 제거)
    recs = recommendations or []
    seen_titles: set = set()
    for rec in recs:
        priority = (rec.get("priority") or "medium").lower()
        if priority not in ("high", "medium"):
            continue
        title = (rec.get("title") or "").strip()
        if not title or title in seen_titles:
            continue
        seen_titles.add(title)
        action = ""
        action_items = rec.get("action_items")
        if isinstance(action_items, list) and len(action_items) > 0:
            first = action_items[0]
            if first is not None:
                action = first if isinstance(first, str) else str(first)
        elif isinstance(action_items, str) and action_items.strip():
            action = action_items.strip()
        key_decisions.append({
            "decision": title,
            "reason": rec.get("description") or "",
            "priority": priority,
            "action": action,
        })
        if len(key_decisions) >= 5:
            break

    # 3) 체크리스트 미완료 비율 → 운영 포인트 1건
    if checklist and isinstance(checklist, dict):
        completion = checklist.get("overall_completion", 0)
        if not isinstance(completion, (int, float)):
            completion = 0
        if completion < 80:
            point = f"메뉴얼 체크리스트 완성도 {completion}%입니다. Qoo10 판매 가이드 기준으로 누락 항목을 보완하세요."
            key = ("체크리스트", point[:80])
            if key not in seen_point_keys:
                seen_point_keys.add(key)
                operational_points.append({
                    "area": "체크리스트",
                    "point": point,
                    "impact": "정산·페널티 방지",
                    "source": "checklist",
                })

    # 4) 한 줄 요약
    if key_decisions:
        summary_text = f"상품 상세 페이지 분석 완료. {len(operational_points)}개 운영 포인트, {len(key_decisions)}개 핵심 의사결정을 확인하세요."
    elif operational_points:
        summary_text = f"상품 상세 페이지 분석 완료. {len(operational_points)}개 개선 포인트를 확인하세요."
    else:
        summary_text = "상품 상세 페이지 분석 완료. 전반적으로 양호합니다."

    return {
        "summary_text": summary_text,
        "operational_points": operational_points,
        "key_decisions": key_decisions,
    }
