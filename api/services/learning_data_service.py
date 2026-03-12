"""
AI 강화학습용 학습 데이터 서비스 (dev-agent-kit / Agent Lightning 연동)

분석 결과를 state/action/reward 형태로 저장하여,
Microsoft Agent Lightning 등 RL 프레임워크에서 활용할 수 있도록 합니다.
- state: 크롤링·분석 입력 요약
- actions: AI가 수행한 판단·추천 요약
- reward: overall_score 또는 사용자 피드백
"""
from typing import Dict, Any, Optional
import json
import os
import logging
from services.database import CrawlerDatabase

logger = logging.getLogger(__name__)

# 강화학습 trajectory 수집 활성화 (환경 변수)
ENABLE_LEARNING_TRAJECTORY = os.getenv("ENABLE_LEARNING_TRAJECTORY", "1").lower() in ("1", "true", "yes")


def _safe_json(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        return "{}"


class LearningDataService:
    """분석 trajectory를 DB에 저장하여 RL/Agent Lightning 학습 데이터로 활용"""

    def __init__(self, db: Optional[CrawlerDatabase] = None):
        self.db = db or CrawlerDatabase()
        self._enabled = ENABLE_LEARNING_TRAJECTORY

    def save_trajectory(
        self,
        analysis_id: str,
        url: str,
        url_type: str,
        analysis_result: Dict[str, Any],
        reward: Optional[float] = None,
    ) -> bool:
        """
        한 번의 분석 실행을 MDP-style trajectory로 저장합니다.

        Args:
            analysis_id: 분석 ID
            url: 분석 URL
            url_type: product | shop
            analysis_result: 최종 분석 결과 (product_analysis, recommendations 등)
            reward: 보상 값. None이면 overall_score로 설정

        Returns:
            저장 성공 여부
        """
        if not self._enabled:
            return False
        try:
            # reward: 분석 점수 또는 명시적 보상
            if reward is None:
                pa = analysis_result.get("product_analysis") or {}
                sa = analysis_result.get("shop_analysis") or {}
                reward = float(pa.get("overall_score") or sa.get("overall_score") or 0)

            # state: 입력/컨텍스트 요약 (크롤링·검증 결과 요약)
            state_snapshot = _build_state_snapshot(analysis_result)
            # actions: AI가 한 판단·추천 요약
            actions_snapshot = _build_actions_snapshot(analysis_result)

            metadata = {
                "url_type": url_type,
                "has_product_analysis": "product_analysis" in analysis_result,
                "has_shop_analysis": "shop_analysis" in analysis_result,
                "recommendations_count": len(analysis_result.get("recommendations") or []),
            }

            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                if self.db.use_postgres:
                    cursor.execute("""
                        INSERT INTO learning_trajectory (
                            analysis_id, url, url_type, state_snapshot, actions_snapshot,
                            reward, metadata_json
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (analysis_id) DO UPDATE SET
                            url = EXCLUDED.url,
                            url_type = EXCLUDED.url_type,
                            state_snapshot = EXCLUDED.state_snapshot,
                            actions_snapshot = EXCLUDED.actions_snapshot,
                            reward = EXCLUDED.reward,
                            metadata_json = EXCLUDED.metadata_json
                    """, (
                        analysis_id,
                        url,
                        url_type,
                        _safe_json(state_snapshot),
                        _safe_json(actions_snapshot),
                        reward,
                        _safe_json(metadata),
                    ))
                else:
                    cursor.execute("""
                        INSERT OR REPLACE INTO learning_trajectory (
                            analysis_id, url, url_type, state_snapshot, actions_snapshot,
                            reward, metadata_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        analysis_id,
                        url,
                        url_type,
                        _safe_json(state_snapshot),
                        _safe_json(actions_snapshot),
                        reward,
                        _safe_json(metadata),
                    ))
                conn.commit()
            logger.debug("Learning trajectory saved: analysis_id=%s reward=%s", analysis_id, reward)
            return True
        except Exception as e:
            logger.warning("Failed to save learning trajectory: %s", e)
            return False


def _build_state_snapshot(result: Dict[str, Any]) -> Dict[str, Any]:
    """분석 입력/컨텍스트를 state 요약으로 만듭니다."""
    state = {}
    if result.get("product_data"):
        pd = result["product_data"]
        state["product"] = {
            "product_code": pd.get("product_code"),
            "product_name": (pd.get("product_name") or "")[:200],
            "has_description": bool(pd.get("description")),
            "has_images": bool(pd.get("images")),
        }
    if result.get("shop_data"):
        sd = result["shop_data"]
        state["shop"] = {
            "shop_name": (sd.get("shop_name") or "")[:200],
            "has_intro": bool(sd.get("shop_intro") or sd.get("intro")),
        }
    if result.get("validation"):
        v = result["validation"]
        state["validation_summary"] = {
            "passed": v.get("passed"),
            "total_checks": v.get("total_checks"),
        }
    return state


def _build_actions_snapshot(result: Dict[str, Any]) -> Dict[str, Any]:
    """AI가 수행한 판단·추천을 actions 요약으로 만듭니다."""
    actions = {}
    if result.get("product_analysis"):
        pa = result["product_analysis"]
        actions["product_analysis"] = {
            "overall_score": pa.get("overall_score"),
            "category_scores": pa.get("category_scores"),
        }
    if result.get("recommendations"):
        recs = result["recommendations"]
        actions["recommendations"] = [
            {"priority": r.get("priority"), "title": (r.get("title") or "")[:100]}
            for r in recs[:20]
        ]
    if result.get("checklist"):
        actions["checklist_summary"] = {
            k: v.get("status") if isinstance(v, dict) else v
            for k, v in list(result.get("checklist", {}).items())[:30]
        }
    return actions
