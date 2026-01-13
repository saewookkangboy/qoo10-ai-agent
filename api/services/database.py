"""
데이터베이스 모델 및 연결 관리
크롤링 데이터 저장 및 성능 추적
PostgreSQL 및 SQLite 지원
"""
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import contextmanager
import os
from pathlib import Path
from urllib.parse import urlparse

# PostgreSQL 또는 SQLite 선택
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres"):
    # PostgreSQL 사용
    import psycopg2
    from psycopg2.extras import RealDictCursor
    USE_POSTGRES = True
else:
    # SQLite 사용 (로컬 개발용)
    import sqlite3
    USE_POSTGRES = False


class CrawlerDatabase:
    """크롤러 데이터베이스 관리 클래스"""
    
    def __init__(self, db_path: str = "crawler_data.db"):
        """데이터베이스 초기화"""
        self.db_path = db_path
        self.use_postgres = USE_POSTGRES
        self._init_database()
    
    def _get_connection_string(self):
        """PostgreSQL 연결 문자열 반환"""
        if not self.use_postgres:
            return None
        return DATABASE_URL
    
    def _get_db_path(self) -> str:
        """SQLite 데이터베이스 경로 반환"""
        if self.use_postgres:
            return None
        api_dir = Path(__file__).parent.parent
        return str(api_dir / self.db_path)
    
    def _init_database(self):
        """데이터베이스 테이블 초기화"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.use_postgres:
                # PostgreSQL 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS crawled_products (
                        id SERIAL PRIMARY KEY,
                        product_code TEXT UNIQUE,
                        url TEXT NOT NULL,
                        product_name TEXT,
                        category TEXT,
                        brand TEXT,
                        price_data TEXT,
                        images TEXT,
                        description TEXT,
                        search_keywords TEXT,
                        reviews_data TEXT,
                        seller_info TEXT,
                        shipping_info TEXT,
                        crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        success_rate REAL DEFAULT 1.0,
                        data_quality_score REAL DEFAULT 0.0
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS crawling_performance (
                        id SERIAL PRIMARY KEY,
                        url TEXT NOT NULL,
                        success BOOLEAN NOT NULL,
                        response_time REAL,
                        status_code INTEGER,
                        error_message TEXT,
                        user_agent TEXT,
                        proxy_used TEXT,
                        retry_count INTEGER DEFAULT 0,
                        crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        data_quality_score REAL DEFAULT 0.0
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS selector_performance (
                        id SERIAL PRIMARY KEY,
                        selector_type TEXT NOT NULL,
                        selector TEXT NOT NULL,
                        success_count INTEGER DEFAULT 0,
                        failure_count INTEGER DEFAULT 0,
                        avg_data_quality REAL DEFAULT 0.0,
                        last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS proxy_performance (
                        id SERIAL PRIMARY KEY,
                        proxy_url TEXT NOT NULL,
                        success_count INTEGER DEFAULT 0,
                        failure_count INTEGER DEFAULT 0,
                        avg_response_time REAL DEFAULT 0.0,
                        last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_agent_performance (
                        id SERIAL PRIMARY KEY,
                        user_agent TEXT NOT NULL UNIQUE,
                        success_count INTEGER DEFAULT 0,
                        failure_count INTEGER DEFAULT 0,
                        avg_response_time REAL DEFAULT 0.0,
                        last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """)
            else:
                # SQLite 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS crawled_products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_code TEXT UNIQUE,
                        url TEXT NOT NULL,
                        product_name TEXT,
                        category TEXT,
                        brand TEXT,
                        price_data TEXT,
                        images TEXT,
                        description TEXT,
                        search_keywords TEXT,
                        reviews_data TEXT,
                        seller_info TEXT,
                        shipping_info TEXT,
                        crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        success_rate REAL DEFAULT 1.0,
                        data_quality_score REAL DEFAULT 0.0
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS crawling_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url TEXT NOT NULL,
                        success BOOLEAN NOT NULL,
                        response_time REAL,
                        status_code INTEGER,
                        error_message TEXT,
                        user_agent TEXT,
                        proxy_used TEXT,
                        retry_count INTEGER DEFAULT 0,
                        crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        data_quality_score REAL DEFAULT 0.0
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS selector_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        selector_type TEXT NOT NULL,
                        selector TEXT NOT NULL,
                        success_count INTEGER DEFAULT 0,
                        failure_count INTEGER DEFAULT 0,
                        avg_data_quality REAL DEFAULT 0.0,
                        last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS proxy_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        proxy_url TEXT NOT NULL,
                        success_count INTEGER DEFAULT 0,
                        failure_count INTEGER DEFAULT 0,
                        avg_response_time REAL DEFAULT 0.0,
                        last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_agent_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_agent TEXT NOT NULL UNIQUE,
                        success_count INTEGER DEFAULT 0,
                        failure_count INTEGER DEFAULT 0,
                        avg_response_time REAL DEFAULT 0.0,
                        last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1
                    )
                """)
            
            # 인덱스 생성
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_code ON crawled_products(product_code)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_crawled_at ON crawled_products(crawled_at)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_url ON crawling_performance(url)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_success ON crawling_performance(success)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_selector_type ON selector_performance(selector_type)")
            except Exception:
                # 인덱스가 이미 존재하는 경우 무시
                pass
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """데이터베이스 연결 컨텍스트 매니저"""
        if self.use_postgres:
            conn = psycopg2.connect(self._get_connection_string())
            conn.cursor_factory = RealDictCursor
        else:
            db_path = self._get_db_path()
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
    
    def save_crawled_product(self, product_data: Dict[str, Any]) -> int:
        """크롤링된 상품 데이터 저장"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 데이터 품질 점수 계산
            quality_score = self._calculate_data_quality(product_data)
            
            if self.use_postgres:
                cursor.execute("""
                    INSERT INTO crawled_products (
                        product_code, url, product_name, category, brand,
                        price_data, images, description, search_keywords,
                        reviews_data, seller_info, shipping_info,
                        success_rate, data_quality_score, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (product_code) DO UPDATE SET
                        url = EXCLUDED.url,
                        product_name = EXCLUDED.product_name,
                        category = EXCLUDED.category,
                        brand = EXCLUDED.brand,
                        price_data = EXCLUDED.price_data,
                        images = EXCLUDED.images,
                        description = EXCLUDED.description,
                        search_keywords = EXCLUDED.search_keywords,
                        reviews_data = EXCLUDED.reviews_data,
                        seller_info = EXCLUDED.seller_info,
                        shipping_info = EXCLUDED.shipping_info,
                        success_rate = EXCLUDED.success_rate,
                        data_quality_score = EXCLUDED.data_quality_score,
                        updated_at = EXCLUDED.updated_at
                """, (
                    product_data.get("product_code"),
                    product_data.get("url"),
                    product_data.get("product_name"),
                    product_data.get("category"),
                    product_data.get("brand"),
                    json.dumps(product_data.get("price", {})),
                    json.dumps(product_data.get("images", {})),
                    product_data.get("description", ""),
                    json.dumps(product_data.get("search_keywords", [])),
                    json.dumps(product_data.get("reviews", {})),
                    json.dumps(product_data.get("seller_info", {})),
                    json.dumps(product_data.get("shipping_info", {})),
                    1.0,
                    quality_score,
                    datetime.now().isoformat()
                ))
            else:
                cursor.execute("""
                    INSERT OR REPLACE INTO crawled_products (
                        product_code, url, product_name, category, brand,
                        price_data, images, description, search_keywords,
                        reviews_data, seller_info, shipping_info,
                        success_rate, data_quality_score, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product_data.get("product_code"),
                    product_data.get("url"),
                    product_data.get("product_name"),
                    product_data.get("category"),
                    product_data.get("brand"),
                    json.dumps(product_data.get("price", {})),
                    json.dumps(product_data.get("images", {})),
                    product_data.get("description", ""),
                    json.dumps(product_data.get("search_keywords", [])),
                    json.dumps(product_data.get("reviews", {})),
                    json.dumps(product_data.get("seller_info", {})),
                    json.dumps(product_data.get("shipping_info", {})),
                    1.0,
                    quality_score,
                    datetime.now().isoformat()
                ))
            
            if self.use_postgres:
                cursor.execute("SELECT LASTVAL()")
                return cursor.fetchone()["lastval"]
            else:
                return cursor.lastrowid
    
    def record_crawling_performance(
        self,
        url: str,
        success: bool,
        response_time: Optional[float] = None,
        status_code: Optional[int] = None,
        error_message: Optional[str] = None,
        user_agent: Optional[str] = None,
        proxy_used: Optional[str] = None,
        retry_count: int = 0,
        data_quality_score: float = 0.0
    ):
        """크롤링 성능 기록"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.use_postgres:
                cursor.execute("""
                    INSERT INTO crawling_performance (
                        url, success, response_time, status_code, error_message,
                        user_agent, proxy_used, retry_count, data_quality_score
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    url, success, response_time, status_code, error_message,
                    user_agent, proxy_used, retry_count, data_quality_score
                ))
            else:
                cursor.execute("""
                    INSERT INTO crawling_performance (
                        url, success, response_time, status_code, error_message,
                        user_agent, proxy_used, retry_count, data_quality_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    url, success, response_time, status_code, error_message,
                    user_agent, proxy_used, retry_count, data_quality_score
                ))
            
            # User-Agent 성능 업데이트
            if user_agent:
                self._update_user_agent_performance(
                    conn, user_agent, success, response_time
                )
            
            # 프록시 성능 업데이트
            if proxy_used:
                self._update_proxy_performance(
                    conn, proxy_used, success, response_time
                )
    
    def record_selector_performance(
        self,
        selector_type: str,
        selector: str,
        success: bool,
        data_quality: float = 0.0
    ):
        """선택자 성능 기록"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.use_postgres:
                cursor.execute("""
                    SELECT success_count, failure_count, avg_data_quality
                    FROM selector_performance
                    WHERE selector_type = %s AND selector = %s
                """, (selector_type, selector))
            else:
                cursor.execute("""
                    SELECT success_count, failure_count, avg_data_quality
                    FROM selector_performance
                    WHERE selector_type = ? AND selector = ?
                """, (selector_type, selector))
            
            row = cursor.fetchone()
            
            if row:
                success_count = row["success_count"] + (1 if success else 0)
                failure_count = row["failure_count"] + (0 if success else 1)
                
                # 평균 데이터 품질 업데이트
                if success:
                    current_avg = row["avg_data_quality"] or 0.0
                    total = success_count + failure_count - 1
                    new_avg = ((current_avg * total) + data_quality) / (total + 1)
                else:
                    new_avg = row["avg_data_quality"] or 0.0
                
                if self.use_postgres:
                    cursor.execute("""
                        UPDATE selector_performance
                        SET success_count = %s, failure_count = %s,
                            avg_data_quality = %s, last_used_at = %s
                        WHERE selector_type = %s AND selector = %s
                    """, (
                        success_count, failure_count, new_avg,
                        datetime.now().isoformat(), selector_type, selector
                    ))
                else:
                    cursor.execute("""
                        UPDATE selector_performance
                        SET success_count = ?, failure_count = ?,
                            avg_data_quality = ?, last_used_at = ?
                        WHERE selector_type = ? AND selector = ?
                    """, (
                        success_count, failure_count, new_avg,
                        datetime.now().isoformat(), selector_type, selector
                    ))
            else:
                if self.use_postgres:
                    cursor.execute("""
                        INSERT INTO selector_performance (
                            selector_type, selector, success_count, failure_count,
                            avg_data_quality
                        ) VALUES (%s, %s, %s, %s, %s)
                    """, (
                        selector_type, selector,
                        1 if success else 0,
                        0 if success else 1,
                        data_quality if success else 0.0
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO selector_performance (
                            selector_type, selector, success_count, failure_count,
                            avg_data_quality
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        selector_type, selector,
                        1 if success else 0,
                        0 if success else 1,
                        data_quality if success else 0.0
                    ))
    
    def get_best_selectors(self, selector_type: str, limit: int = 5) -> List[Dict[str, Any]]:
        """가장 성공률이 높은 선택자 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.use_postgres:
                cursor.execute("""
                    SELECT selector, success_count, failure_count,
                           (CAST(success_count AS REAL) / (success_count + failure_count + 1)) as success_rate,
                           avg_data_quality
                    FROM selector_performance
                    WHERE selector_type = %s AND (success_count + failure_count) > 0
                    ORDER BY success_rate DESC, avg_data_quality DESC
                    LIMIT %s
                """, (selector_type, limit))
            else:
                cursor.execute("""
                    SELECT selector, success_count, failure_count,
                           (CAST(success_count AS REAL) / (success_count + failure_count + 1)) as success_rate,
                           avg_data_quality
                    FROM selector_performance
                    WHERE selector_type = ? AND (success_count + failure_count) > 0
                    ORDER BY success_rate DESC, avg_data_quality DESC
                    LIMIT ?
                """, (selector_type, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_best_user_agent(self) -> Optional[str]:
        """가장 성공률이 높은 User-Agent 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.use_postgres:
                cursor.execute("""
                    SELECT user_agent,
                           (CAST(success_count AS REAL) / (success_count + failure_count + 1)) as success_rate
                    FROM user_agent_performance
                    WHERE is_active = TRUE
                    ORDER BY success_rate DESC, avg_response_time ASC
                    LIMIT 1
                """)
            else:
                cursor.execute("""
                    SELECT user_agent,
                           (CAST(success_count AS REAL) / (success_count + failure_count + 1)) as success_rate
                    FROM user_agent_performance
                    WHERE is_active = 1
                    ORDER BY success_rate DESC, avg_response_time ASC
                    LIMIT 1
                """)
            
            row = cursor.fetchone()
            return row["user_agent"] if row else None
    
    def get_best_proxy(self) -> Optional[str]:
        """가장 성공률이 높은 프록시 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.use_postgres:
                cursor.execute("""
                    SELECT proxy_url,
                           (CAST(success_count AS REAL) / (success_count + failure_count + 1)) as success_rate
                    FROM proxy_performance
                    WHERE is_active = TRUE
                    ORDER BY success_rate DESC, avg_response_time ASC
                    LIMIT 1
                """)
            else:
                cursor.execute("""
                    SELECT proxy_url,
                           (CAST(success_count AS REAL) / (success_count + failure_count + 1)) as success_rate
                    FROM proxy_performance
                    WHERE is_active = 1
                    ORDER BY success_rate DESC, avg_response_time ASC
                    LIMIT 1
                """)
            
            row = cursor.fetchone()
            return row["proxy_url"] if row else None
    
    def get_crawling_statistics(self) -> Dict[str, Any]:
        """크롤링 통계 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 전체 성공률
            if self.use_postgres:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN success = TRUE THEN 1 ELSE 0 END) as successful,
                        AVG(response_time) as avg_response_time
                    FROM crawling_performance
                """)
                
                cursor.execute("""
                    SELECT 
                        COUNT(*) as recent_total,
                        SUM(CASE WHEN success = TRUE THEN 1 ELSE 0 END) as recent_successful
                    FROM crawling_performance
                    WHERE crawled_at > NOW() - INTERVAL '1 day'
                """)
            else:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                        AVG(response_time) as avg_response_time
                    FROM crawling_performance
                """)
                
                cursor.execute("""
                    SELECT 
                        COUNT(*) as recent_total,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as recent_successful
                    FROM crawling_performance
                    WHERE crawled_at > datetime('now', '-1 day')
                """)
            
            stats = dict(cursor.fetchone())
            recent_stats = dict(cursor.fetchone())
            
            return {
                "total_crawls": stats["total"] or 0,
                "successful_crawls": stats["successful"] or 0,
                "success_rate": (stats["successful"] / stats["total"] * 100) if stats["total"] else 0,
                "avg_response_time": stats["avg_response_time"] or 0.0,
                "recent_24h": {
                    "total": recent_stats["recent_total"] or 0,
                    "successful": recent_stats["recent_successful"] or 0
                }
            }
    
    def _update_user_agent_performance(
        self,
        conn,
        user_agent: str,
        success: bool,
        response_time: Optional[float]
    ):
        """User-Agent 성능 업데이트"""
        cursor = conn.cursor()
        
        if self.use_postgres:
            cursor.execute("""
                SELECT success_count, failure_count, avg_response_time
                FROM user_agent_performance
                WHERE user_agent = %s
            """, (user_agent,))
        else:
            cursor.execute("""
                SELECT success_count, failure_count, avg_response_time
                FROM user_agent_performance
                WHERE user_agent = ?
            """, (user_agent,))
        
        row = cursor.fetchone()
        
        if row:
            success_count = row["success_count"] + (1 if success else 0)
            failure_count = row["failure_count"] + (0 if success else 1)
            
            # 평균 응답 시간 업데이트
            if response_time:
                current_avg = row["avg_response_time"] or 0.0
                total = success_count + failure_count - 1
                new_avg = ((current_avg * total) + response_time) / (total + 1)
            else:
                new_avg = row["avg_response_time"] or 0.0
            
            if self.use_postgres:
                cursor.execute("""
                    UPDATE user_agent_performance
                    SET success_count = %s, failure_count = %s,
                        avg_response_time = %s, last_used_at = %s
                    WHERE user_agent = %s
                """, (
                    success_count, failure_count, new_avg,
                    datetime.now().isoformat(), user_agent
                ))
            else:
                cursor.execute("""
                    UPDATE user_agent_performance
                    SET success_count = ?, failure_count = ?,
                        avg_response_time = ?, last_used_at = ?
                    WHERE user_agent = ?
                """, (
                    success_count, failure_count, new_avg,
                    datetime.now().isoformat(), user_agent
                ))
        else:
            if self.use_postgres:
                cursor.execute("""
                    INSERT INTO user_agent_performance (
                        user_agent, success_count, failure_count, avg_response_time
                    ) VALUES (%s, %s, %s, %s)
                """, (
                    user_agent,
                    1 if success else 0,
                    0 if success else 1,
                    response_time or 0.0
                ))
            else:
                cursor.execute("""
                    INSERT INTO user_agent_performance (
                        user_agent, success_count, failure_count, avg_response_time
                    ) VALUES (?, ?, ?, ?)
                """, (
                    user_agent,
                    1 if success else 0,
                    0 if success else 1,
                    response_time or 0.0
                ))
    
    def _update_proxy_performance(
        self,
        conn,
        proxy_url: str,
        success: bool,
        response_time: Optional[float]
    ):
        """프록시 성능 업데이트"""
        cursor = conn.cursor()
        
        if self.use_postgres:
            cursor.execute("""
                SELECT success_count, failure_count, avg_response_time
                FROM proxy_performance
                WHERE proxy_url = %s
            """, (proxy_url,))
        else:
            cursor.execute("""
                SELECT success_count, failure_count, avg_response_time
                FROM proxy_performance
                WHERE proxy_url = ?
            """, (proxy_url,))
        
        row = cursor.fetchone()
        
        if row:
            success_count = row["success_count"] + (1 if success else 0)
            failure_count = row["failure_count"] + (0 if success else 1)
            
            if response_time:
                current_avg = row["avg_response_time"] or 0.0
                total = success_count + failure_count - 1
                new_avg = ((current_avg * total) + response_time) / (total + 1)
            else:
                new_avg = row["avg_response_time"] or 0.0
            
            if self.use_postgres:
                cursor.execute("""
                    UPDATE proxy_performance
                    SET success_count = %s, failure_count = %s,
                        avg_response_time = %s, last_used_at = %s
                    WHERE proxy_url = %s
                """, (
                    success_count, failure_count, new_avg,
                    datetime.now().isoformat(), proxy_url
                ))
            else:
                cursor.execute("""
                    UPDATE proxy_performance
                    SET success_count = ?, failure_count = ?,
                        avg_response_time = ?, last_used_at = ?
                    WHERE proxy_url = ?
                """, (
                    success_count, failure_count, new_avg,
                    datetime.now().isoformat(), proxy_url
                ))
        else:
            if self.use_postgres:
                cursor.execute("""
                    INSERT INTO proxy_performance (
                        proxy_url, success_count, failure_count, avg_response_time
                    ) VALUES (%s, %s, %s, %s)
                """, (
                    proxy_url,
                    1 if success else 0,
                    0 if success else 1,
                    response_time or 0.0
                ))
            else:
                cursor.execute("""
                    INSERT INTO proxy_performance (
                        proxy_url, success_count, failure_count, avg_response_time
                    ) VALUES (?, ?, ?, ?)
                """, (
                    proxy_url,
                    1 if success else 0,
                    0 if success else 1,
                    response_time or 0.0
                ))
    
    def _calculate_data_quality(self, product_data: Dict[str, Any]) -> float:
        """데이터 품질 점수 계산 (0.0 ~ 1.0)"""
        score = 0.0
        max_score = 0.0
        
        # 필수 필드 체크
        fields = {
            "product_name": 0.2,
            "price": 0.2,
            "category": 0.15,
            "description": 0.15,
            "images": 0.1,
            "seller_info": 0.1,
            "reviews": 0.1
        }
        
        for field, weight in fields.items():
            max_score += weight
            value = product_data.get(field)
            
            if value:
                if isinstance(value, dict):
                    if value:  # 비어있지 않은 딕셔너리
                        score += weight
                elif isinstance(value, list):
                    if value:  # 비어있지 않은 리스트
                        score += weight
                elif isinstance(value, str):
                    if value.strip() and value != "상품명 없음":
                        score += weight
                else:
                    score += weight
        
        return score / max_score if max_score > 0 else 0.0
