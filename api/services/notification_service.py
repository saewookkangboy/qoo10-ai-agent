"""
알림 서비스
분석 완료, 점수 변화, 추천 아이디어 등에 대한 알림을 관리합니다.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from services.database import CrawlerDatabase
import json


class NotificationType(str, Enum):
    """알림 타입"""
    ANALYSIS_COMPLETED = "analysis_completed"
    SCORE_CHANGED = "score_changed"
    NEW_RECOMMENDATION = "new_recommendation"
    THRESHOLD_ALERT = "threshold_alert"
    COMPETITOR_ALERT = "competitor_alert"


class NotificationService:
    """알림 서비스"""
    
    def __init__(self, db: Optional[CrawlerDatabase] = None):
        """
        알림 서비스 초기화
        
        Args:
            db: 데이터베이스 인스턴스 (없으면 자동 생성)
        """
        self.db = db or CrawlerDatabase()
        self._init_notification_tables()
    
    def _init_notification_tables(self):
        """알림 테이블 초기화"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db.use_postgres:
                # PostgreSQL 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS notifications (
                        id SERIAL PRIMARY KEY,
                        notification_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        message TEXT NOT NULL,
                        analysis_id TEXT,
                        url TEXT,
                        metadata TEXT,
                        is_read BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_notifications_created_at 
                    ON notifications(created_at)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_notifications_is_read 
                    ON notifications(is_read)
                """)
            else:
                # SQLite 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS notifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        notification_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        message TEXT NOT NULL,
                        analysis_id TEXT,
                        url TEXT,
                        metadata TEXT,
                        is_read BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_notifications_created_at 
                    ON notifications(created_at)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_notifications_is_read 
                    ON notifications(is_read)
                """)
            
            conn.commit()
    
    def create_notification(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        analysis_id: Optional[str] = None,
        url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        알림 생성
        
        Args:
            notification_type: 알림 타입
            title: 알림 제목
            message: 알림 메시지
            analysis_id: 분석 ID (선택사항)
            url: URL (선택사항)
            metadata: 추가 메타데이터 (선택사항)
            
        Returns:
            생성된 알림 ID
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None
            
            if self.db.use_postgres:
                cursor.execute("""
                    INSERT INTO notifications (
                        notification_type, title, message, analysis_id, url, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    notification_type.value,
                    title,
                    message,
                    analysis_id,
                    url,
                    metadata_json
                ))
                notification_id = cursor.fetchone()[0]
            else:
                cursor.execute("""
                    INSERT INTO notifications (
                        notification_type, title, message, analysis_id, url, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    notification_type.value,
                    title,
                    message,
                    analysis_id,
                    url,
                    metadata_json
                ))
                notification_id = cursor.lastrowid
            
            conn.commit()
            return notification_id
    
    def notify_analysis_completed(
        self,
        analysis_id: str,
        url: str,
        overall_score: int
    ):
        """분석 완료 알림"""
        self.create_notification(
            NotificationType.ANALYSIS_COMPLETED,
            "분석 완료",
            f"분석이 완료되었습니다. 종합 점수: {overall_score}/100",
            analysis_id=analysis_id,
            url=url,
            metadata={"overall_score": overall_score}
        )
    
    def notify_score_changed(
        self,
        analysis_id: str,
        url: str,
        old_score: int,
        new_score: int
    ):
        """점수 변화 알림"""
        score_diff = new_score - old_score
        if abs(score_diff) >= 5:  # 5점 이상 변화 시 알림
            direction = "상승" if score_diff > 0 else "하락"
            self.create_notification(
                NotificationType.SCORE_CHANGED,
                f"점수 {direction}",
                f"종합 점수가 {old_score}점에서 {new_score}점으로 {direction}했습니다. (변화: {abs(score_diff)}점)",
                analysis_id=analysis_id,
                url=url,
                metadata={
                    "old_score": old_score,
                    "new_score": new_score,
                    "score_diff": score_diff
                }
            )
    
    def notify_threshold_alert(
        self,
        analysis_id: str,
        url: str,
        score: int,
        threshold: int = 60
    ):
        """임계값 알림 (점수가 임계값 이하일 때)"""
        if score < threshold:
            self.create_notification(
                NotificationType.THRESHOLD_ALERT,
                "점수 경고",
                f"종합 점수가 {score}점으로 임계값({threshold}점) 이하입니다. 개선이 필요합니다.",
                analysis_id=analysis_id,
                url=url,
                metadata={"score": score, "threshold": threshold}
            )
    
    def get_notifications(
        self,
        is_read: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        알림 조회
        
        Args:
            is_read: 읽음 여부 필터 (None이면 전체)
            limit: 조회 개수 제한
            offset: 오프셋
            
        Returns:
            알림 리스트
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM notifications WHERE 1=1"
            params = []
            
            if is_read is not None:
                query += " AND is_read = ?" if not self.db.use_postgres else " AND is_read = %s"
                params.append(is_read)
            
            query += " ORDER BY created_at DESC"
            
            if self.db.use_postgres:
                query += " LIMIT %s OFFSET %s"
            else:
                query += " LIMIT ? OFFSET ?"
            
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            
            if self.db.use_postgres:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                results = [dict(zip(columns, row)) for row in rows]
            else:
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                results = [dict(zip(columns, row)) for row in rows]
            
            # JSON 파싱
            for result in results:
                if result.get("metadata"):
                    result["metadata"] = json.loads(result["metadata"])
            
            return results
    
    def get_unread_count(self) -> int:
        """미읽음 알림 개수 조회"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db.use_postgres:
                cursor.execute("""
                    SELECT COUNT(*) FROM notifications WHERE is_read = FALSE
                """)
            else:
                cursor.execute("""
                    SELECT COUNT(*) FROM notifications WHERE is_read = 0
                """)
            
            return cursor.fetchone()[0]
    
    def mark_as_read(self, notification_id: int) -> bool:
        """
        알림 읽음 처리
        
        Args:
            notification_id: 알림 ID
            
        Returns:
            업데이트 성공 여부
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db.use_postgres:
                cursor.execute("""
                    UPDATE notifications SET is_read = TRUE WHERE id = %s
                """, (notification_id,))
            else:
                cursor.execute("""
                    UPDATE notifications SET is_read = 1 WHERE id = ?
                """, (notification_id,))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def mark_all_as_read(self) -> int:
        """
        모든 알림 읽음 처리
        
        Returns:
            업데이트된 알림 개수
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db.use_postgres:
                cursor.execute("""
                    UPDATE notifications SET is_read = TRUE WHERE is_read = FALSE
                """)
            else:
                cursor.execute("""
                    UPDATE notifications SET is_read = 1 WHERE is_read = 0
                """)
            
            conn.commit()
            return cursor.rowcount
    
    def delete_notification(self, notification_id: int) -> bool:
        """
        알림 삭제
        
        Args:
            notification_id: 알림 ID
            
        Returns:
            삭제 성공 여부
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db.use_postgres:
                cursor.execute("""
                    DELETE FROM notifications WHERE id = %s
                """, (notification_id,))
            else:
                cursor.execute("""
                    DELETE FROM notifications WHERE id = ?
                """, (notification_id,))
            
            conn.commit()
            return cursor.rowcount > 0
