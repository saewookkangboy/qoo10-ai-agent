"""
데이터 파이프라인 모니터링 서비스
각 단계별 성공률을 측정하고 DB에 기록합니다.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import logging
from contextlib import contextmanager

from services.database import CrawlerDatabase

logger = logging.getLogger(__name__)


class PipelineMonitor:
    """데이터 파이프라인 모니터링 서비스"""
    
    # 파이프라인 단계 정의
    STAGES = [
        "crawling",              # 크롤링
        "analyzing",             # 분석
        "generating_recommendations",  # 추천 생성
        "evaluating_checklist",  # 체크리스트 평가
        "validating",            # 데이터 검증
        "finalizing",            # 결과 저장
    ]
    
    def __init__(self, db: Optional[CrawlerDatabase] = None):
        self.db = db or CrawlerDatabase()
    
    def record_stage(
        self,
        analysis_id: str,
        url: str,
        url_type: str,
        stage: str,
        status: str,
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        파이프라인 단계 기록
        
        Args:
            analysis_id: 분석 ID
            url: 분석 URL
            url_type: URL 타입 (product/shop)
            stage: 파이프라인 단계
            status: 상태 (success/failure)
            duration_ms: 소요 시간 (밀리초)
            error_message: 오류 메시지 (실패 시)
            metadata: 추가 메타데이터
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                metadata_json = None
                if metadata:
                    if self.db.use_postgres:
                        metadata_json = json.dumps(metadata)
                    else:
                        metadata_json = json.dumps(metadata)
                
                if self.db.use_postgres:
                    cursor.execute("""
                        INSERT INTO pipeline_monitoring (
                            analysis_id, url, url_type, stage, status,
                            error_message, duration_ms, metadata
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        analysis_id, url, url_type, stage, status,
                        error_message, duration_ms, metadata_json
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO pipeline_monitoring (
                            analysis_id, url, url_type, stage, status,
                            error_message, duration_ms, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        analysis_id, url, url_type, stage, status,
                        error_message, duration_ms, metadata_json
                    ))
                
                # 성공률 집계 업데이트 (시간별, 일별)
                self._update_success_rates(stage, status, duration_ms)
                
        except Exception as e:
            logger.error(f"Failed to record pipeline stage: {str(e)}", exc_info=True)
    
    def _update_success_rates(
        self,
        stage: str,
        status: str,
        duration_ms: Optional[int]
    ):
        """성공률 집계 업데이트"""
        try:
            now = datetime.now()
            
            # 시간별 집계
            hour_start = now.replace(minute=0, second=0, microsecond=0)
            self._update_period_rate("hour", hour_start, stage, status, duration_ms)
            
            # 일별 집계
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            self._update_period_rate("day", day_start, stage, status, duration_ms)
            
            # 주별 집계 (월요일 시작)
            week_start = day_start - timedelta(days=day_start.weekday())
            self._update_period_rate("week", week_start, stage, status, duration_ms)
            
            # 월별 집계
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            self._update_period_rate("month", month_start, stage, status, duration_ms)
            
        except Exception as e:
            logger.error(f"Failed to update success rates: {str(e)}", exc_info=True)
    
    def _update_period_rate(
        self,
        period_type: str,
        period_start: datetime,
        stage: str,
        status: str,
        duration_ms: Optional[int]
    ):
        """특정 기간의 성공률 업데이트"""
        from contextlib import contextmanager
        
        @contextmanager
        def get_connection():
            if self.db.use_postgres:
                import psycopg2
                from psycopg2.extras import RealDictCursor
                conn = psycopg2.connect(self.db._get_connection_string())
                conn.cursor_factory = RealDictCursor
            else:
                import sqlite3
                db_path = self.db._get_db_path()
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
            
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        
        with get_connection() as conn:
            cursor = conn.cursor()
            
            period_start_str = period_start.isoformat()
            
            # 기존 레코드 조회
            if self.db.use_postgres:
                cursor.execute("""
                    SELECT total_count, success_count, failure_count, avg_duration_ms
                    FROM pipeline_success_rates
                    WHERE period_type = %s AND period_start = %s AND stage = %s
                """, (period_type, period_start_str, stage))
            else:
                cursor.execute("""
                    SELECT total_count, success_count, failure_count, avg_duration_ms
                    FROM pipeline_success_rates
                    WHERE period_type = ? AND period_start = ? AND stage = ?
                """, (period_type, period_start_str, stage))
            
            row = cursor.fetchone()
            
            if row:
                # 기존 레코드 업데이트
                total_count = row["total_count"] + 1
                success_count = row["success_count"] + (1 if status == "success" else 0)
                failure_count = row["failure_count"] + (1 if status == "failure" else 0)
                success_rate = (success_count / total_count * 100) if total_count > 0 else 0.0
                
                # 평균 소요 시간 업데이트
                current_avg = row["avg_duration_ms"] or 0.0
                if duration_ms:
                    new_avg = ((current_avg * (total_count - 1)) + duration_ms) / total_count
                else:
                    new_avg = current_avg
                
                if self.db.use_postgres:
                    cursor.execute("""
                        UPDATE pipeline_success_rates
                        SET total_count = %s, success_count = %s, failure_count = %s,
                            success_rate = %s, avg_duration_ms = %s, updated_at = %s
                        WHERE period_type = %s AND period_start = %s AND stage = %s
                    """, (
                        total_count, success_count, failure_count, success_rate,
                        new_avg, datetime.now().isoformat(),
                        period_type, period_start_str, stage
                    ))
                else:
                    cursor.execute("""
                        UPDATE pipeline_success_rates
                        SET total_count = ?, success_count = ?, failure_count = ?,
                            success_rate = ?, avg_duration_ms = ?, updated_at = ?
                        WHERE period_type = ? AND period_start = ? AND stage = ?
                    """, (
                        total_count, success_count, failure_count, success_rate,
                        new_avg, datetime.now().isoformat(),
                        period_type, period_start_str, stage
                    ))
            else:
                # 새 레코드 생성
                total_count = 1
                success_count = 1 if status == "success" else 0
                failure_count = 1 if status == "failure" else 0
                success_rate = 100.0 if status == "success" else 0.0
                avg_duration_ms = duration_ms if duration_ms else None
                
                if self.db.use_postgres:
                    cursor.execute("""
                        INSERT INTO pipeline_success_rates (
                            period_type, period_start, stage, total_count,
                            success_count, failure_count, success_rate, avg_duration_ms
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        period_type, period_start_str, stage, total_count,
                        success_count, failure_count, success_rate, avg_duration_ms
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO pipeline_success_rates (
                            period_type, period_start, stage, total_count,
                            success_count, failure_count, success_rate, avg_duration_ms
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        period_type, period_start_str, stage, total_count,
                        success_count, failure_count, success_rate, avg_duration_ms
                    ))
    
    def get_success_rates(
        self,
        period_type: str = "day",
        days: int = 7
    ) -> Dict[str, Any]:
        """
        성공률 조회
        
        Args:
            period_type: 집계 기간 타입 (hour/day/week/month)
            days: 조회할 일수 (day 타입일 때만 사용)
            
        Returns:
            성공률 통계 딕셔너리
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                if period_type == "day":
                    start_date = (datetime.now() - timedelta(days=days)).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    start_date_str = start_date.isoformat()
                    
                    if self.db.use_postgres:
                        cursor.execute("""
                            SELECT stage, period_start, total_count, success_count,
                                   failure_count, success_rate, avg_duration_ms
                            FROM pipeline_success_rates
                            WHERE period_type = %s AND period_start >= %s
                            ORDER BY period_start DESC, stage
                        """, (period_type, start_date_str))
                    else:
                        cursor.execute("""
                            SELECT stage, period_start, total_count, success_count,
                                   failure_count, success_rate, avg_duration_ms
                            FROM pipeline_success_rates
                            WHERE period_type = ? AND period_start >= ?
                            ORDER BY period_start DESC, stage
                        """, (period_type, start_date_str))
                else:
                    if self.db.use_postgres:
                        cursor.execute("""
                            SELECT stage, period_start, total_count, success_count,
                                   failure_count, success_rate, avg_duration_ms
                            FROM pipeline_success_rates
                            WHERE period_type = %s
                            ORDER BY period_start DESC, stage
                            LIMIT 100
                        """, (period_type,))
                    else:
                        cursor.execute("""
                            SELECT stage, period_start, total_count, success_count,
                                   failure_count, success_rate, avg_duration_ms
                            FROM pipeline_success_rates
                            WHERE period_type = ?
                            ORDER BY period_start DESC, stage
                            LIMIT 100
                        """, (period_type,))
                
                rows = cursor.fetchall()
                
                # 단계별로 그룹화
                stage_stats = {}
                for row in rows:
                    stage = row["stage"]
                    if stage not in stage_stats:
                        stage_stats[stage] = {
                            "total_count": 0,
                            "success_count": 0,
                            "failure_count": 0,
                            "periods": []
                        }
                    
                    stage_stats[stage]["total_count"] += row["total_count"]
                    stage_stats[stage]["success_count"] += row["success_count"]
                    stage_stats[stage]["failure_count"] += row["failure_count"]
                    stage_stats[stage]["periods"].append({
                        "period_start": row["period_start"],
                        "total_count": row["total_count"],
                        "success_count": row["success_count"],
                        "failure_count": row["failure_count"],
                        "success_rate": row["success_rate"],
                        "avg_duration_ms": row["avg_duration_ms"]
                    })
                
                # 전체 성공률 계산
                for stage, stats in stage_stats.items():
                    if stats["total_count"] > 0:
                        stats["success_rate"] = (stats["success_count"] / stats["total_count"]) * 100
                    else:
                        stats["success_rate"] = 0.0
                
                return {
                    "period_type": period_type,
                    "days": days if period_type == "day" else None,
                    "stages": stage_stats,
                    "overall": {
                        "total_count": sum(s["total_count"] for s in stage_stats.values()),
                        "success_count": sum(s["success_count"] for s in stage_stats.values()),
                        "failure_count": sum(s["failure_count"] for s in stage_stats.values()),
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get success rates: {str(e)}", exc_info=True)
            return {
                "period_type": period_type,
                "stages": {},
                "overall": {"total_count": 0, "success_count": 0, "failure_count": 0}
            }
    
    def get_stage_details(
        self,
        stage: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        특정 단계의 상세 기록 조회
        
        Args:
            stage: 파이프라인 단계
            limit: 조회할 레코드 수
            
        Returns:
            상세 기록 리스트
        """
        from contextlib import contextmanager
        
        @contextmanager
        def get_connection():
            if self.db.use_postgres:
                import psycopg2
                from psycopg2.extras import RealDictCursor
                conn = psycopg2.connect(self.db._get_connection_string())
                conn.cursor_factory = RealDictCursor
            else:
                import sqlite3
                db_path = self.db._get_db_path()
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
            
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                if self.db.use_postgres:
                    cursor.execute("""
                        SELECT * FROM pipeline_monitoring
                        WHERE stage = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (stage, limit))
                else:
                    cursor.execute("""
                        SELECT * FROM pipeline_monitoring
                        WHERE stage = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    """, (stage, limit))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get stage details: {str(e)}", exc_info=True)
            return []
