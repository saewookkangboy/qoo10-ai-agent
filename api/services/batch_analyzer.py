"""
배치 분석 서비스
여러 URL을 한 번에 분석하고 결과를 관리합니다.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
from services.crawler import Qoo10Crawler
from services.analyzer import ProductAnalyzer
from services.shop_analyzer import ShopAnalyzer
from services.recommender import SalesEnhancementRecommender
from services.checklist_evaluator import ChecklistEvaluator
from services.competitor_analyzer import CompetitorAnalyzer
from services.database import CrawlerDatabase
import json


class BatchAnalyzer:
    """배치 분석기"""
    
    def __init__(self, db: Optional[CrawlerDatabase] = None):
        """
        배치 분석기 초기화
        
        Args:
            db: 데이터베이스 인스턴스 (없으면 자동 생성)
        """
        self.db = db or CrawlerDatabase()
        self.crawler = Qoo10Crawler(db)
        self._init_batch_tables()
    
    def _init_batch_tables(self):
        """배치 분석 테이블 초기화"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db.use_postgres:
                # PostgreSQL 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS batch_analyses (
                        id SERIAL PRIMARY KEY,
                        batch_id TEXT NOT NULL UNIQUE,
                        name TEXT,
                        urls TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending',
                        total_count INTEGER DEFAULT 0,
                        completed_count INTEGER DEFAULT 0,
                        failed_count INTEGER DEFAULT 0,
                        results TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS batch_analysis_items (
                        id SERIAL PRIMARY KEY,
                        batch_id TEXT NOT NULL,
                        url TEXT NOT NULL,
                        url_type TEXT,
                        analysis_id TEXT,
                        status TEXT NOT NULL DEFAULT 'pending',
                        result TEXT,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            else:
                # SQLite 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS batch_analyses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        batch_id TEXT NOT NULL UNIQUE,
                        name TEXT,
                        urls TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending',
                        total_count INTEGER DEFAULT 0,
                        completed_count INTEGER DEFAULT 0,
                        failed_count INTEGER DEFAULT 0,
                        results TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS batch_analysis_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        batch_id TEXT NOT NULL,
                        url TEXT NOT NULL,
                        url_type TEXT,
                        analysis_id TEXT,
                        status TEXT NOT NULL DEFAULT 'pending',
                        result TEXT,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            
            conn.commit()
    
    async def create_batch_analysis(
        self,
        urls: List[str],
        name: Optional[str] = None
    ) -> str:
        """
        배치 분석 생성
        
        Args:
            urls: 분석할 URL 리스트
            name: 배치 분석 이름 (선택사항)
            
        Returns:
            배치 ID
        """
        import uuid
        batch_id = str(uuid.uuid4())
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db.use_postgres:
                cursor.execute("""
                    INSERT INTO batch_analyses (
                        batch_id, name, urls, total_count, status
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (
                    batch_id,
                    name or f"배치 분석 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    json.dumps(urls, ensure_ascii=False),
                    len(urls),
                    "pending"
                ))
            else:
                cursor.execute("""
                    INSERT INTO batch_analyses (
                        batch_id, name, urls, total_count, status
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    batch_id,
                    name or f"배치 분석 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    json.dumps(urls, ensure_ascii=False),
                    len(urls),
                    "pending"
                ))
            
            # 배치 아이템 생성
            for url in urls:
                if self.db.use_postgres:
                    cursor.execute("""
                        INSERT INTO batch_analysis_items (
                            batch_id, url, status
                        ) VALUES (%s, %s, %s)
                    """, (batch_id, url, "pending"))
                else:
                    cursor.execute("""
                        INSERT INTO batch_analysis_items (
                            batch_id, url, status
                        ) VALUES (?, ?, ?)
                    """, (batch_id, url, "pending"))
            
            conn.commit()
        
        # 백그라운드에서 분석 시작
        asyncio.create_task(self._process_batch_analysis(batch_id, urls))
        
        return batch_id
    
    async def _process_batch_analysis(self, batch_id: str, urls: List[str]):
        """배치 분석 처리 (백그라운드)"""
        try:
            # 상태를 processing으로 변경
            self._update_batch_status(batch_id, "processing")
            
            completed_count = 0
            failed_count = 0
            results = []
            
            # 각 URL 분석
            for url in urls:
                try:
                    # URL 타입 감지
                    def detect_url_type(url: str) -> str:
                        """URL 타입 자동 감지"""
                        if "/Goods/Goods.aspx" in url or "/goods/" in url.lower():
                            return "product"
                        elif "/shop/" in url.lower():
                            return "shop"
                        else:
                            return "unknown"
                    
                    url_type = detect_url_type(url)
                    
                    # 크롤링
                    if url_type == "product":
                        data = await self.crawler.crawl_product(url)
                        
                        # 분석
                        analyzer = ProductAnalyzer()
                        analysis_result = await analyzer.analyze(data)
                        
                        # 추천
                        recommender = SalesEnhancementRecommender()
                        recommendations = await recommender.generate_recommendations(
                            data,
                            analysis_result
                        )
                        
                        # 체크리스트
                        checklist_evaluator = ChecklistEvaluator()
                        checklist_result = await checklist_evaluator.evaluate_checklist(
                            product_data=data,
                            analysis_result=analysis_result
                        )
                        
                        # 경쟁사 분석
                        competitor_analyzer = CompetitorAnalyzer()
                        competitor_result = await competitor_analyzer.analyze_competitors(data)
                        
                        result = {
                            "product_analysis": analysis_result,
                            "recommendations": recommendations,
                            "checklist": checklist_result,
                            "competitor_analysis": competitor_result,
                            "product_data": data
                        }
                    
                    elif url_type == "shop":
                        data = await self.crawler.crawl_shop(url)
                        
                        # Shop 분석
                        shop_analyzer = ShopAnalyzer()
                        analysis_result = await shop_analyzer.analyze(data)
                        
                        # 추천
                        recommender = SalesEnhancementRecommender()
                        recommendations = await recommender.generate_shop_recommendations(
                            data,
                            analysis_result
                        )
                        
                        # 체크리스트
                        checklist_evaluator = ChecklistEvaluator()
                        checklist_result = await checklist_evaluator.evaluate_checklist(
                            shop_data=data,
                            analysis_result=analysis_result
                        )
                        
                        result = {
                            "shop_analysis": analysis_result,
                            "recommendations": recommendations,
                            "checklist": checklist_result,
                            "shop_data": data
                        }
                    else:
                        raise ValueError(f"Unknown URL type: {url_type}")
                    
                    # 결과 저장
                    import uuid
                    analysis_id = str(uuid.uuid4())
                    
                    self._update_batch_item(
                        batch_id,
                        url,
                        analysis_id,
                        url_type,
                        "completed",
                        result
                    )
                    
                    results.append({
                        "url": url,
                        "analysis_id": analysis_id,
                        "status": "completed",
                        "result": result
                    })
                    
                    completed_count += 1
                    
                except Exception as e:
                    self._update_batch_item(
                        batch_id,
                        url,
                        None,
                        None,
                        "failed",
                        None,
                        str(e)
                    )
                    
                    results.append({
                        "url": url,
                        "status": "failed",
                        "error": str(e)
                    })
                    
                    failed_count += 1
                
                # 진행 상황 업데이트
                self._update_batch_progress(batch_id, completed_count, failed_count)
            
            # 배치 완료
            self._update_batch_status(batch_id, "completed", results)
            
        except Exception as e:
            self._update_batch_status(batch_id, "failed", None, str(e))
    
    def _update_batch_status(
        self,
        batch_id: str,
        status: str,
        results: Optional[List[Dict[str, Any]]] = None,
        error: Optional[str] = None
    ):
        """배치 상태 업데이트"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db.use_postgres:
                if results is not None:
                    cursor.execute("""
                        UPDATE batch_analyses 
                        SET status = %s, results = %s, updated_at = %s
                        WHERE batch_id = %s
                    """, (
                        status,
                        json.dumps(results, ensure_ascii=False),
                        datetime.now().isoformat(),
                        batch_id
                    ))
                elif error:
                    cursor.execute("""
                        UPDATE batch_analyses 
                        SET status = %s, updated_at = %s
                        WHERE batch_id = %s
                    """, (status, datetime.now().isoformat(), batch_id))
                else:
                    cursor.execute("""
                        UPDATE batch_analyses 
                        SET status = %s, updated_at = %s
                        WHERE batch_id = %s
                    """, (status, datetime.now().isoformat(), batch_id))
            else:
                if results is not None:
                    cursor.execute("""
                        UPDATE batch_analyses 
                        SET status = ?, results = ?, updated_at = ?
                        WHERE batch_id = ?
                    """, (
                        status,
                        json.dumps(results, ensure_ascii=False),
                        datetime.now().isoformat(),
                        batch_id
                    ))
                else:
                    cursor.execute("""
                        UPDATE batch_analyses 
                        SET status = ?, updated_at = ?
                        WHERE batch_id = ?
                    """, (status, datetime.now().isoformat(), batch_id))
            
            conn.commit()
    
    def _update_batch_item(
        self,
        batch_id: str,
        url: str,
        analysis_id: Optional[str],
        url_type: Optional[str],
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ):
        """배치 아이템 업데이트"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db.use_postgres:
                cursor.execute("""
                    UPDATE batch_analysis_items 
                    SET analysis_id = %s, url_type = %s, status = %s, 
                        result = %s, error_message = %s, updated_at = %s
                    WHERE batch_id = %s AND url = %s
                """, (
                    analysis_id,
                    url_type,
                    status,
                    json.dumps(result, ensure_ascii=False) if result else None,
                    error_message,
                    datetime.now().isoformat(),
                    batch_id,
                    url
                ))
            else:
                cursor.execute("""
                    UPDATE batch_analysis_items 
                    SET analysis_id = ?, url_type = ?, status = ?, 
                        result = ?, error_message = ?, updated_at = ?
                    WHERE batch_id = ? AND url = ?
                """, (
                    analysis_id,
                    url_type,
                    status,
                    json.dumps(result, ensure_ascii=False) if result else None,
                    error_message,
                    datetime.now().isoformat(),
                    batch_id,
                    url
                ))
            
            conn.commit()
    
    def _update_batch_progress(
        self,
        batch_id: str,
        completed_count: int,
        failed_count: int
    ):
        """배치 진행 상황 업데이트"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db.use_postgres:
                cursor.execute("""
                    UPDATE batch_analyses 
                    SET completed_count = %s, failed_count = %s, updated_at = %s
                    WHERE batch_id = %s
                """, (
                    completed_count,
                    failed_count,
                    datetime.now().isoformat(),
                    batch_id
                ))
            else:
                cursor.execute("""
                    UPDATE batch_analyses 
                    SET completed_count = ?, failed_count = ?, updated_at = ?
                    WHERE batch_id = ?
                """, (
                    completed_count,
                    failed_count,
                    datetime.now().isoformat(),
                    batch_id
                ))
            
            conn.commit()
    
    def get_batch_analysis(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """배치 분석 조회"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db.use_postgres:
                cursor.execute("""
                    SELECT * FROM batch_analyses WHERE batch_id = %s
                """, (batch_id,))
            else:
                cursor.execute("""
                    SELECT * FROM batch_analyses WHERE batch_id = ?
                """, (batch_id,))
            
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
            if result.get("urls"):
                result["urls"] = json.loads(result["urls"])
            if result.get("results"):
                result["results"] = json.loads(result["results"])
            
            return result
    
    def get_batch_items(self, batch_id: str) -> List[Dict[str, Any]]:
        """배치 아이템 조회"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db.use_postgres:
                cursor.execute("""
                    SELECT * FROM batch_analysis_items 
                    WHERE batch_id = %s 
                    ORDER BY created_at ASC
                """, (batch_id,))
            else:
                cursor.execute("""
                    SELECT * FROM batch_analysis_items 
                    WHERE batch_id = ? 
                    ORDER BY created_at ASC
                """, (batch_id,))
            
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
                if result.get("result"):
                    result["result"] = json.loads(result["result"])
            
            return results
