"""
오류 신고 서비스
사용자가 크롤링 결과와 리포트 내용의 불일치를 신고하고,
신고된 항목을 우선적으로 크롤링하도록 관리합니다.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json

from services.database import CrawlerDatabase

logger = logging.getLogger(__name__)


class ErrorReportingService:
    """오류 신고 서비스"""
    
    def __init__(self, db: Optional[CrawlerDatabase] = None):
        self.db = db or CrawlerDatabase()
    
    def report_error(
        self,
        analysis_id: str,
        url: str,
        field_name: str,
        issue_type: str,
        severity: str,
        user_description: Optional[str] = None,
        crawler_value: Optional[Any] = None,
        report_value: Optional[Any] = None,
        page_structure_chunk: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        오류 신고
        
        Args:
            analysis_id: 분석 ID
            url: 분석된 URL
            field_name: 문제가 있는 필드명
            issue_type: 문제 유형 (mismatch, missing, incorrect)
            severity: 심각도 (high, medium, low)
            user_description: 사용자 설명
            crawler_value: 크롤러가 수집한 값
            report_value: 리포트에 표시된 값
            page_structure_chunk: 페이지 구조 Chunk
            
        Returns:
            저장된 오류 신고 정보
        """
        # 크롤러 값과 리포트 값을 문자열로 변환
        crawler_value_str = json.dumps(crawler_value) if crawler_value is not None else None
        report_value_str = json.dumps(report_value) if report_value is not None else None
        
        error_report_id = self.db.save_error_report(
            analysis_id=analysis_id,
            url=url,
            field_name=field_name,
            issue_type=issue_type,
            severity=severity,
            user_description=user_description,
            crawler_value=crawler_value_str,
            report_value=report_value_str,
            page_structure_chunk=page_structure_chunk
        )
        
        # Chunk 분석 및 저장
        if page_structure_chunk:
            self._analyze_and_save_chunks(
                error_report_id=error_report_id,
                field_name=field_name,
                page_structure_chunk=page_structure_chunk
            )
        
        return {
            "error_report_id": error_report_id,
            "status": "reported",
            "message": "오류 신고가 저장되었습니다."
        }
    
    def _analyze_and_save_chunks(
        self,
        error_report_id: int,
        field_name: str,
        page_structure_chunk: Dict[str, Any]
    ):
        """페이지 구조 Chunk를 분석하여 저장"""
        # 관련된 DOM 요소들 추출
        related_classes = page_structure_chunk.get("related_classes", [])
        element_present = page_structure_chunk.get("element_present", False)
        class_frequency = page_structure_chunk.get("class_frequency", {})
        
        # Chunk 데이터 구성
        chunk_data = {
            "field_name": field_name,
            "related_classes": related_classes,
            "element_present": element_present,
            "class_frequency": class_frequency,
            "timestamp": datetime.now().isoformat()
        }
        
        # 가장 빈번한 클래스 패턴 추출
        selector_pattern = None
        if class_frequency:
            # 빈도가 높은 클래스들을 조합하여 선택자 패턴 생성
            top_classes = sorted(
                class_frequency.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            selector_pattern = " > ".join([f".{cls}" for cls, _ in top_classes])
        
        # Chunk 저장
        self.db.save_error_report_chunk(
            error_report_id=error_report_id,
            chunk_type="page_structure",
            chunk_data=chunk_data,
            selector_pattern=selector_pattern,
            extraction_method="dom_analysis"
        )
    
    def get_priority_fields_for_crawling(self) -> List[str]:
        """
        우선 크롤링해야 할 필드 목록 조회
        오류 신고가 많은 필드들을 우선순위로 반환
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db.use_postgres:
                cursor.execute("""
                    SELECT field_name, COUNT(*) as error_count
                    FROM error_reports
                    WHERE status = 'pending'
                    GROUP BY field_name
                    ORDER BY error_count DESC, field_name
                    LIMIT 10
                """)
            else:
                cursor.execute("""
                    SELECT field_name, COUNT(*) as error_count
                    FROM error_reports
                    WHERE status = 'pending'
                    GROUP BY field_name
                    ORDER BY error_count DESC, field_name
                    LIMIT 10
                """)
            
            rows = cursor.fetchall()
            return [row["field_name"] for row in rows]
    
    def get_chunks_for_field(
        self,
        field_name: str
    ) -> List[Dict[str, Any]]:
        """
        특정 필드에 대한 Chunk 목록 조회
        유사한 사이트 구조 크롤링 시 참고용
        """
        error_reports = self.db.get_error_reports_by_field(field_name, status="pending")
        
        all_chunks = []
        for report in error_reports:
            chunks = self.db.get_error_report_chunks(report["id"])
            for chunk in chunks:
                chunk_data = json.loads(chunk["chunk_data"]) if isinstance(chunk["chunk_data"], str) else chunk["chunk_data"]
                all_chunks.append({
                    "error_report_id": report["id"],
                    "chunk_id": chunk["id"],
                    "chunk_type": chunk["chunk_type"],
                    "chunk_data": chunk_data,
                    "selector_pattern": chunk["selector_pattern"],
                    "extraction_method": chunk["extraction_method"],
                    "url": report["url"]
                })
        
        return all_chunks
    
    def should_prioritize_field(
        self,
        field_name: str
    ) -> bool:
        """
        특정 필드가 우선 크롤링 대상인지 확인
        """
        priority_fields = self.get_priority_fields_for_crawling()
        return field_name in priority_fields
    
    def mark_error_resolved(
        self,
        error_report_id: int
    ) -> bool:
        """오류 신고를 해결됨으로 표시"""
        return self.db.update_error_report_status(error_report_id, "resolved")
