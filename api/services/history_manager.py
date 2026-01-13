"""
히스토리 관리 서비스
분석 이력을 저장하고 조회하며, 시간에 따른 변화를 추적합니다.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from services.database import CrawlerDatabase
import json


class HistoryManager:
    """히스토리 관리자"""
    
    def __init__(self, db: Optional[CrawlerDatabase] = None):
        """
        히스토리 관리자 초기화
        
        Args:
            db: 데이터베이스 인스턴스 (없으면 자동 생성)
        """
        self.db = db or CrawlerDatabase()
        self._init_history_tables()
    
    def _init_history_tables(self):
        """히스토리 테이블 초기화"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db.use_postgres:
                # PostgreSQL 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_history (
                        id SERIAL PRIMARY KEY,
                        analysis_id TEXT NOT NULL UNIQUE,
                        url TEXT NOT NULL,
                        url_type TEXT NOT NULL,
                        analysis_result TEXT NOT NULL,
                        overall_score INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_analysis_history_url 
                    ON analysis_history(url)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_analysis_history_created_at 
                    ON analysis_history(created_at)
                """)
            else:
                # SQLite 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        analysis_id TEXT NOT NULL UNIQUE,
                        url TEXT NOT NULL,
                        url_type TEXT NOT NULL,
                        analysis_result TEXT NOT NULL,
                        overall_score INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_analysis_history_url 
                    ON analysis_history(url)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_analysis_history_created_at 
                    ON analysis_history(created_at)
                """)
            
            conn.commit()
    
    def save_analysis_history(
        self,
        analysis_id: str,
        url: str,
        url_type: str,
        analysis_result: Dict[str, Any]
    ) -> int:
        """
        분석 이력 저장
        
        Args:
            analysis_id: 분석 ID
            url: 분석한 URL
            url_type: URL 타입 (product/shop)
            analysis_result: 분석 결과
            
        Returns:
            저장된 레코드 ID
        """
        # 종합 점수 추출
        overall_score = 0
        if "product_analysis" in analysis_result:
            overall_score = analysis_result["product_analysis"].get("overall_score", 0)
        elif "shop_analysis" in analysis_result:
            overall_score = analysis_result["shop_analysis"].get("overall_score", 0)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db.use_postgres:
                cursor.execute("""
                    INSERT INTO analysis_history (
                        analysis_id, url, url_type, analysis_result, overall_score, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (analysis_id) DO UPDATE SET
                        url = EXCLUDED.url,
                        url_type = EXCLUDED.url_type,
                        analysis_result = EXCLUDED.analysis_result,
                        overall_score = EXCLUDED.overall_score,
                        updated_at = EXCLUDED.updated_at
                """, (
                    analysis_id,
                    url,
                    url_type,
                    json.dumps(analysis_result, ensure_ascii=False),
                    overall_score,
                    datetime.now().isoformat()
                ))
            else:
                cursor.execute("""
                    INSERT OR REPLACE INTO analysis_history (
                        analysis_id, url, url_type, analysis_result, overall_score, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    analysis_id,
                    url,
                    url_type,
                    json.dumps(analysis_result, ensure_ascii=False),
                    overall_score,
                    datetime.now().isoformat()
                ))
            
            record_id = cursor.lastrowid if not self.db.use_postgres else cursor.fetchone()[0] if cursor.rowcount > 0 else None
            conn.commit()
            
            return record_id
    
    def get_analysis_history(
        self,
        url: Optional[str] = None,
        url_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        분석 이력 조회
        
        Args:
            url: URL 필터 (선택사항)
            url_type: URL 타입 필터 (선택사항)
            limit: 조회 개수 제한
            offset: 오프셋
            
        Returns:
            분석 이력 리스트
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM analysis_history WHERE 1=1"
            params = []
            
            if url:
                query += " AND url = ?" if not self.db.use_postgres else " AND url = %s"
                params.append(url)
            
            if url_type:
                query += " AND url_type = ?" if not self.db.use_postgres else " AND url_type = %s"
                params.append(url_type)
            
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
                if result.get("analysis_result"):
                    result["analysis_result"] = json.loads(result["analysis_result"])
            
            return results
    
    def get_analysis_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        분석 ID로 이력 조회
        
        Args:
            analysis_id: 분석 ID
            
        Returns:
            분석 이력 또는 None
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db.use_postgres:
                cursor.execute("""
                    SELECT * FROM analysis_history WHERE analysis_id = %s
                """, (analysis_id,))
            else:
                cursor.execute("""
                    SELECT * FROM analysis_history WHERE analysis_id = ?
                """, (analysis_id,))
            
            if self.db.use_postgres:
                columns = [desc[0] for desc in cursor.description]
                row = cursor.fetchone()
                if row:
                    result = dict(zip(columns, row))
                else:
                    return None
            else:
                columns = [description[0] for description in cursor.description]
                row = cursor.fetchone()
                if row:
                    result = dict(zip(columns, row))
                else:
                    return None
            
            # JSON 파싱
            if result.get("analysis_result"):
                result["analysis_result"] = json.loads(result["analysis_result"])
            
            return result
    
    def get_score_trend(
        self,
        url: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        점수 추이 조회
        
        Args:
            url: URL
            days: 조회 기간 (일)
            
        Returns:
            점수 추이 리스트
        """
        start_date = datetime.now() - timedelta(days=days)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db.use_postgres:
                cursor.execute("""
                    SELECT 
                        DATE(created_at) as date,
                        AVG(overall_score) as avg_score,
                        MAX(overall_score) as max_score,
                        MIN(overall_score) as min_score,
                        COUNT(*) as count
                    FROM analysis_history
                    WHERE url = %s AND created_at >= %s
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """, (url, start_date.isoformat()))
            else:
                cursor.execute("""
                    SELECT 
                        DATE(created_at) as date,
                        AVG(overall_score) as avg_score,
                        MAX(overall_score) as max_score,
                        MIN(overall_score) as min_score,
                        COUNT(*) as count
                    FROM analysis_history
                    WHERE url = ? AND created_at >= ?
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """, (url, start_date.isoformat()))
            
            if self.db.use_postgres:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                results = [dict(zip(columns, row)) for row in rows]
            else:
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                results = [dict(zip(columns, row)) for row in rows]
            
            return results
    
    def delete_analysis_history(self, analysis_id: str) -> bool:
        """
        분석 이력 삭제
        
        Args:
            analysis_id: 분석 ID
            
        Returns:
            삭제 성공 여부
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db.use_postgres:
                cursor.execute("""
                    DELETE FROM analysis_history WHERE analysis_id = %s
                """, (analysis_id,))
            else:
                cursor.execute("""
                    DELETE FROM analysis_history WHERE analysis_id = ?
                """, (analysis_id,))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def get_recent_analyses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        최근 분석 이력 조회
        
        Args:
            limit: 조회 개수
            
        Returns:
            최근 분석 이력 리스트
        """
        return self.get_analysis_history(limit=limit, offset=0)
