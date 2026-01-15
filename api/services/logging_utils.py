"""
공유 디버그 로깅 유틸리티
모든 서비스에서 사용할 수 있는 중앙화된 디버그 로깅 기능을 제공합니다.
"""
from typing import Dict, Any
from datetime import datetime
import os
import json
from pathlib import Path

# 디버그 로깅 설정 (환경변수 기반, 기본 비활성화)
# - DEBUG_LOG: "1"/"true"/"True" 이면 파일 로깅 활성화
# - DEBUG_LOG_PATH: 파일 경로 지정 (기본: 프로젝트 루트/.cursor/debug.log)
_DEBUG_LOG_ENABLED = os.getenv("DEBUG_LOG", "0").lower() in {"1", "true", "yes"}
_default_log_path = Path(__file__).resolve().parents[1] / ".cursor" / "debug.log"
_LOG_PATH = Path(os.getenv("DEBUG_LOG_PATH", str(_default_log_path)))
_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def log_debug(
    session_id: str,
    run_id: str,
    hypothesis_id: str,
    location: str,
    message: str,
    data: Dict[str, Any] = None
):
    """
    디버그 로그 작성
    
    Args:
        session_id: 세션 ID
        run_id: 실행 ID
        hypothesis_id: 가설 ID
        location: 로그 위치 (예: "checklist_evaluator.py:evaluate_checklist")
        message: 로그 메시지
        data: 추가 데이터 (선택사항)
    
    환경 변수:
        - DEBUG_LOG: "1"/"true"/"True"로 설정하면 로깅 활성화
        - DEBUG_LOG_PATH: 로그 파일 경로 (기본: 프로젝트 루트/.cursor/debug.log)
    
    기본적으로 비활성화되어 있으며, 환경변수로만 활성화 가능합니다.
    JSON 라인 포맷을 유지해 디버깅/분석 도구와의 호환성을 보장합니다.
    """
    if not _DEBUG_LOG_ENABLED:
        return
    
    try:
        log_entry = {
            "sessionId": session_id,
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data or {},
            "timestamp": int(datetime.now().timestamp() * 1000)
        }
        with _LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # 로깅 실패해도 계속 진행
