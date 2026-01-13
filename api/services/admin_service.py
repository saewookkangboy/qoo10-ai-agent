"""
Admin 서비스
관리자용 통계, 로그, 리포트 기능을 제공합니다.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from services.database import CrawlerDatabase
import json


class AdminService:
    """Admin 서비스"""
    
    def __init__(self, db: Optional[CrawlerDatabase] = None):
        """
        Admin 서비스 초기화
        
        Args:
            db: 데이터베이스 인스턴스 (없으면 자동 생성)
        """
        self.db = db or CrawlerDatabase()
    
    def get_analysis_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        분석 로그 조회
        
        Args:
            limit: 조회 개수 제한
            offset: 오프셋
            status: 상태 필터 (completed, failed, processing)
            start_date: 시작 날짜 (ISO 형식)
            end_date: 종료 날짜 (ISO 형식)
            
        Returns:
            분석 로그 리스트 및 통계
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 기본 쿼리
            query = """
                SELECT 
                    analysis_id,
                    url,
                    url_type,
                    overall_score,
                    created_at,
                    updated_at
                FROM analysis_history
                WHERE 1=1
            """
            params = []
            
            # 필터 추가
            if status:
                # status는 analysis_history에 없으므로 overall_score로 추정
                # completed는 overall_score가 있음, failed는 NULL
                if status == "completed":
                    query += " AND overall_score IS NOT NULL"
                elif status == "failed":
                    query += " AND overall_score IS NULL"
            
            if start_date:
                query += " AND created_at >= ?" if not self.db.use_postgres else " AND created_at >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND created_at <= ?" if not self.db.use_postgres else " AND created_at <= %s"
                params.append(end_date)
            
            query += " ORDER BY created_at DESC"
            
            # 카운트 쿼리
            count_query = query.replace(
                "SELECT analysis_id, url, url_type, overall_score, created_at, updated_at",
                "SELECT COUNT(*)"
            )
            
            if self.db.use_postgres:
                cursor.execute(count_query, params)
                total = cursor.fetchone()[0]
                
                query += " LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                cursor.execute(query, params)
            else:
                cursor.execute(count_query, params)
                total = cursor.fetchone()[0]
                
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                cursor.execute(query, params)
            
            # 결과 파싱
            if self.db.use_postgres:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                logs = [dict(zip(columns, row)) for row in rows]
            else:
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                logs = [dict(zip(columns, row)) for row in rows]
            
            return {
                "logs": logs,
                "total": total,
                "limit": limit,
                "offset": offset
            }
    
    def get_error_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        에러 로그 조회
        
        Args:
            limit: 조회 개수 제한
            offset: 오프셋
            start_date: 시작 날짜
            end_date: 종료 날짜
            
        Returns:
            에러 로그 리스트
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    id,
                    url,
                    success,
                    error_message,
                    status_code,
                    response_time,
                    crawled_at
                FROM crawling_performance
                WHERE success = 0
            """
            params = []
            
            if start_date:
                query += " AND crawled_at >= ?" if not self.db.use_postgres else " AND crawled_at >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND crawled_at <= ?" if not self.db.use_postgres else " AND crawled_at <= %s"
                params.append(end_date)
            
            query += " ORDER BY crawled_at DESC"
            
            # 카운트
            count_query = query.replace(
                "SELECT id, url, success, error_message, status_code, response_time, crawled_at",
                "SELECT COUNT(*)"
            )
            
            if self.db.use_postgres:
                cursor.execute(count_query, params)
                total = cursor.fetchone()[0]
                
                query += " LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                cursor.execute(query, params)
            else:
                cursor.execute(count_query, params)
                total = cursor.fetchone()[0]
                
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                cursor.execute(query, params)
            
            if self.db.use_postgres:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                logs = [dict(zip(columns, row)) for row in rows]
            else:
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                logs = [dict(zip(columns, row)) for row in rows]
            
            return {
                "logs": logs,
                "total": total,
                "limit": limit,
                "offset": offset
            }
    
    def get_score_statistics(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        점수 통계 조회
        
        Args:
            days: 조회 기간 (일)
            
        Returns:
            점수 통계
        """
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db.use_postgres:
                cursor.execute("""
                    SELECT 
                        AVG(overall_score) as avg_score,
                        MAX(overall_score) as max_score,
                        MIN(overall_score) as min_score,
                        COUNT(*) as total_count,
                        COUNT(CASE WHEN overall_score >= 80 THEN 1 END) as excellent_count,
                        COUNT(CASE WHEN overall_score >= 60 AND overall_score < 80 THEN 1 END) as good_count,
                        COUNT(CASE WHEN overall_score < 60 THEN 1 END) as poor_count
                    FROM analysis_history
                    WHERE overall_score IS NOT NULL 
                    AND created_at >= %s
                """, (start_date,))
            else:
                cursor.execute("""
                    SELECT 
                        AVG(overall_score) as avg_score,
                        MAX(overall_score) as max_score,
                        MIN(overall_score) as min_score,
                        COUNT(*) as total_count,
                        COUNT(CASE WHEN overall_score >= 80 THEN 1 END) as excellent_count,
                        COUNT(CASE WHEN overall_score >= 60 AND overall_score < 80 THEN 1 END) as good_count,
                        COUNT(CASE WHEN overall_score < 60 THEN 1 END) as poor_count
                    FROM analysis_history
                    WHERE overall_score IS NOT NULL 
                    AND created_at >= ?
                """, (start_date,))
            
            if self.db.use_postgres:
                columns = [desc[0] for desc in cursor.description]
                row = cursor.fetchone()
                stats = dict(zip(columns, row)) if row else {}
            else:
                columns = [description[0] for description in cursor.description]
                row = cursor.fetchone()
                stats = dict(zip(columns, row)) if row else {}
            
            # 일별 통계
            if self.db.use_postgres:
                cursor.execute("""
                    SELECT 
                        DATE(created_at) as date,
                        AVG(overall_score) as avg_score,
                        COUNT(*) as count
                    FROM analysis_history
                    WHERE overall_score IS NOT NULL 
                    AND created_at >= %s
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """, (start_date,))
            else:
                cursor.execute("""
                    SELECT 
                        DATE(created_at) as date,
                        AVG(overall_score) as avg_score,
                        COUNT(*) as count
                    FROM analysis_history
                    WHERE overall_score IS NOT NULL 
                    AND created_at >= ?
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """, (start_date,))
            
            if self.db.use_postgres:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                daily_stats = [dict(zip(columns, row)) for row in rows]
            else:
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                daily_stats = [dict(zip(columns, row)) for row in rows]
            
            return {
                "overall": stats,
                "daily": daily_stats
            }
    
    def get_analysis_statistics(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        분석 통계 조회
        
        Args:
            days: 조회 기간 (일)
            
        Returns:
            분석 통계
        """
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db.use_postgres:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_analyses,
                        COUNT(DISTINCT url) as unique_urls,
                        COUNT(CASE WHEN url_type = 'product' THEN 1 END) as product_count,
                        COUNT(CASE WHEN url_type = 'shop' THEN 1 END) as shop_count
                    FROM analysis_history
                    WHERE created_at >= %s
                """, (start_date,))
            else:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_analyses,
                        COUNT(DISTINCT url) as unique_urls,
                        COUNT(CASE WHEN url_type = 'product' THEN 1 END) as product_count,
                        COUNT(CASE WHEN url_type = 'shop' THEN 1 END) as shop_count
                    FROM analysis_history
                    WHERE created_at >= ?
                """, (start_date,))
            
            if self.db.use_postgres:
                columns = [desc[0] for desc in cursor.description]
                row = cursor.fetchone()
                stats = dict(zip(columns, row)) if row else {}
            else:
                columns = [description[0] for description in cursor.description]
                row = cursor.fetchone()
                stats = dict(zip(columns, row)) if row else {}
            
            return stats
    
    def get_user_analysis_logs(
        self,
        url: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        사용자별 분석 로그 조회 (URL별)
        
        Args:
            url: URL 필터
            limit: 조회 개수 제한
            offset: 오프셋
            
        Returns:
            사용자 분석 로그
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    url,
                    COUNT(*) as analysis_count,
                    MAX(created_at) as last_analyzed,
                    AVG(overall_score) as avg_score
                FROM analysis_history
                WHERE 1=1
            """
            params = []
            
            if url:
                query += " AND url = ?" if not self.db.use_postgres else " AND url = %s"
                params.append(url)
            
            query += " GROUP BY url ORDER BY last_analyzed DESC"
            
            # 카운트
            count_query = query.replace(
                "SELECT url, COUNT(*) as analysis_count, MAX(created_at) as last_analyzed, AVG(overall_score) as avg_score",
                "SELECT COUNT(DISTINCT url)"
            )
            
            if self.db.use_postgres:
                cursor.execute(count_query, params)
                total = cursor.fetchone()[0]
                
                query += " LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                cursor.execute(query, params)
            else:
                cursor.execute(count_query, params)
                total = cursor.fetchone()[0]
                
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                cursor.execute(query, params)
            
            if self.db.use_postgres:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                logs = [dict(zip(columns, row)) for row in rows]
            else:
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                logs = [dict(zip(columns, row)) for row in rows]
            
            return {
                "logs": logs,
                "total": total,
                "limit": limit,
                "offset": offset
            }
    
    def get_analysis_results_list(
        self,
        limit: int = 50,
        offset: int = 0,
        min_score: Optional[int] = None,
        max_score: Optional[int] = None,
        url_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        분석 결과 리스트 조회
        
        Args:
            limit: 조회 개수 제한
            offset: 오프셋
            min_score: 최소 점수 필터
            max_score: 최대 점수 필터
            url_type: URL 타입 필터
            
        Returns:
            분석 결과 리스트
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    analysis_id,
                    url,
                    url_type,
                    overall_score,
                    created_at
                FROM analysis_history
                WHERE overall_score IS NOT NULL
            """
            params = []
            
            if min_score is not None:
                query += " AND overall_score >= ?" if not self.db.use_postgres else " AND overall_score >= %s"
                params.append(min_score)
            
            if max_score is not None:
                query += " AND overall_score <= ?" if not self.db.use_postgres else " AND overall_score <= %s"
                params.append(max_score)
            
            if url_type:
                query += " AND url_type = ?" if not self.db.use_postgres else " AND url_type = %s"
                params.append(url_type)
            
            query += " ORDER BY created_at DESC"
            
            # 카운트
            count_query = query.replace(
                "SELECT analysis_id, url, url_type, overall_score, created_at",
                "SELECT COUNT(*)"
            )
            
            if self.db.use_postgres:
                cursor.execute(count_query, params)
                total = cursor.fetchone()[0]
                
                query += " LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                cursor.execute(query, params)
            else:
                cursor.execute(count_query, params)
                total = cursor.fetchone()[0]
                
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
            
            return {
                "results": results,
                "total": total,
                "limit": limit,
                "offset": offset
            }
    
    def generate_ai_insight_report(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        AI 분석 리포트 생성
        
        Args:
            days: 분석 기간 (일)
            
        Returns:
            AI 인사이트 리포트
        """
        # 통계 수집
        score_stats = self.get_score_statistics(days)
        analysis_stats = self.get_analysis_statistics(days)
        
        # AI 인사이트 생성 (간단한 버전)
        insights = []
        
        overall = score_stats.get("overall", {})
        avg_score = overall.get("avg_score", 0) or 0
        
        if avg_score < 60:
            insights.append({
                "type": "warning",
                "title": "평균 점수가 낮습니다",
                "description": f"최근 {days}일간 평균 점수가 {avg_score:.1f}점으로 개선이 필요합니다.",
                "recommendation": "상품 페이지 최적화 및 SEO 개선을 권장합니다."
            })
        elif avg_score >= 80:
            insights.append({
                "type": "success",
                "title": "우수한 평균 점수",
                "description": f"최근 {days}일간 평균 점수가 {avg_score:.1f}점으로 양호한 수준입니다.",
                "recommendation": "현재 수준을 유지하면서 지속적인 모니터링을 권장합니다."
            })
        
        excellent_count = overall.get("excellent_count", 0) or 0
        total_count = overall.get("total_count", 0) or 0
        
        if total_count > 0:
            excellent_ratio = (excellent_count / total_count) * 100
            if excellent_ratio < 20:
                insights.append({
                    "type": "info",
                    "title": "우수 상품 비율 개선 필요",
                    "description": f"우수 상품(80점 이상) 비율이 {excellent_ratio:.1f}%입니다.",
                    "recommendation": "상품 페이지 품질 향상을 위한 체계적인 개선이 필요합니다."
                })
        
        return {
            "period_days": days,
            "statistics": {
                "score": score_stats,
                "analysis": analysis_stats
            },
            "insights": insights,
            "generated_at": datetime.now().isoformat()
        }
