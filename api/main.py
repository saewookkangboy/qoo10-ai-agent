"""
Qoo10 Sales Intelligence Agent - FastAPI Main Application
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
import os
import re
import logging
from dotenv import load_dotenv

from services.crawler import Qoo10Crawler
from services.analyzer import ProductAnalyzer
from services.recommender import SalesEnhancementRecommender
from services.shop_analyzer import ShopAnalyzer
from services.checklist_evaluator import ChecklistEvaluator
from services.competitor_analyzer import CompetitorAnalyzer
from services.report_generator import ReportGenerator
from services.history_manager import HistoryManager
from services.notification_service import NotificationService, NotificationType
from services.batch_analyzer import BatchAnalyzer
from services.admin_service import AdminService
from services.seo_optimizer import SEOOptimizer
from services.ai_seo_optimizer import AISEOOptimizer
from services.geo_optimizer import GEOOptimizer
from services.aio_optimizer import AIOOptimizer
from services.data_validator import DataValidator
from services.error_reporting_service import ErrorReportingService
from services.pipeline_monitor import PipelineMonitor

load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Qoo10 Sales Intelligence Agent API",
    description="Qoo10 Japan 입점 브랜드를 위한 AI 기반 커머스 분석 및 SEO/AIO/GEO 최적화 API",
    version="1.0.0"
)

# CORS 설정
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",") if os.getenv("ALLOWED_ORIGINS") else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # 환경 변수에서 설정 가능
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 분석 결과 저장소 (임시 - 프로덕션에서는 DB 사용)
analysis_store: Dict[str, Dict[str, Any]] = {}

# 히스토리 관리자 및 알림 서비스 초기화
history_manager = HistoryManager()
notification_service = NotificationService()
batch_analyzer = BatchAnalyzer()
admin_service = AdminService()
data_validator = DataValidator()
error_reporting_service = ErrorReportingService()
pipeline_monitor = PipelineMonitor()


class AnalyzeRequest(BaseModel):
    url: HttpUrl = Field(..., description="Qoo10 상품 또는 Shop URL")
    url_type: Optional[str] = Field(None, description="URL 타입 (product/shop, 자동 감지 가능)")


class AnalyzeResponse(BaseModel):
    analysis_id: str
    status: str
    url_type: str
    estimated_time: int = 30


@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "Qoo10 Sales Intelligence Agent API",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/api/v1/analyze",
            "result": "/api/v1/analyze/{analysis_id}",
            "seo": "/api/v1/seo/analyze",
            "ai_seo": "/api/v1/ai-seo/analyze",
            "geo": "/api/v1/geo/analyze",
            "aio": "/api/v1/aio/analyze",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/api/v1/crawler/statistics")
async def get_crawler_statistics():
    """
    크롤러 통계 조회
    
    - 크롤링 성공률, 평균 응답 시간 등 통계 정보를 반환합니다
    - AI 강화 학습 시스템의 성능 지표를 확인할 수 있습니다
    """
    try:
        from services.database import CrawlerDatabase
        db = CrawlerDatabase()
        stats = db.get_crawling_statistics()
        
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get crawler statistics: {str(e)}"
        )


@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
async def start_analysis(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks
):
    """
    URL 분석 시작
    
    - URL을 입력받아 분석을 시작합니다
    - 분석은 백그라운드에서 비동기로 진행됩니다
    - analysis_id를 반환하여 결과 조회에 사용합니다
    """
    try:
        url_str = str(request.url)
        
        # URL 검증
        if not is_valid_qoo10_url(url_str):
            raise HTTPException(
                status_code=400,
                detail="Invalid Qoo10 URL. Please provide a valid Qoo10 product or shop URL."
            )
        
        # URL 타입 결정
        url_type = request.url_type or detect_url_type(url_str)
        
        if url_type == "unknown":
            raise HTTPException(
                status_code=400,
                detail="Unable to detect URL type. Please specify product or shop URL."
            )
        
        # 분석 ID 생성
        analysis_id = str(uuid.uuid4())
        
        # 초기 상태 저장
        analysis_store[analysis_id] = {
            "analysis_id": analysis_id,
            "url": url_str,
            "url_type": url_type,
            "status": "processing",
            "created_at": datetime.now().isoformat(),
            "progress": {
                "stage": "initializing",
                "percentage": 0,
                "message": "분석을 초기화하는 중..."
            },
            "result": None
        }
        
        # 분석 작업 시작 (백그라운드)
        background_tasks.add_task(
            perform_analysis,
            analysis_id,
            url_str,
            url_type
        )
        
        logger.info(f"Analysis started: {analysis_id}, URL: {url_str}, Type: {url_type}")
        
        return AnalyzeResponse(
            analysis_id=analysis_id,
            status="processing",
            url_type=url_type,
            estimated_time=30
        )
    
    except HTTPException:
        raise
    except Exception as e:
        error_detail = str(e)
        logger.error(f"Failed to start analysis: {error_detail}", exc_info=True)
        
        # 사용자 친화적인 에러 메시지 생성
        if "URL" in error_detail or "url" in error_detail.lower():
            user_message = "URL 형식이 올바르지 않습니다. Qoo10 상품 또는 Shop URL을 입력해주세요."
        elif "detect" in error_detail.lower() or "type" in error_detail.lower():
            user_message = "URL 타입을 감지할 수 없습니다. 상품 URL 또는 Shop URL을 명확히 입력해주세요."
        else:
            user_message = f"분석 시작에 실패했습니다: {error_detail}"
        
        raise HTTPException(
            status_code=500,
            detail=user_message
        )


@app.get("/api/v1/analyze/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    """
    분석 결과 조회
    
    - analysis_id로 분석 결과를 조회합니다
    - status가 "completed"일 때만 결과를 반환합니다
    - 진행 상태(progress) 정보도 함께 반환합니다
    """
    if analysis_id not in analysis_store:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found"
        )
    
    analysis = analysis_store[analysis_id]
    
    # 기본 응답 구조
    response = {
        "analysis_id": analysis_id,
        "status": analysis["status"]
    }
    
    # 진행 상태 추가
    if "progress" in analysis:
        response["progress"] = analysis["progress"]
    
    if analysis["status"] == "processing":
        response["message"] = "Analysis is still in progress"
        return response
    
    if analysis["status"] == "failed":
        response["error"] = analysis.get("error", "Unknown error")
        return response
    
    # 완료된 경우 결과 반환
    if analysis["status"] == "completed":
        response["result"] = analysis.get("result")
        return response
    
    return response


@app.get("/api/v1/analyze/{analysis_id}/download")
async def download_report(
    analysis_id: str,
    format: str = "pdf"
):
    """
    리포트 다운로드
    
    - analysis_id로 분석 리포트를 다운로드합니다
    - format: pdf, excel, markdown
    """
    if analysis_id not in analysis_store:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found"
        )
    
    analysis = analysis_store[analysis_id]
    
    if analysis["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail="Analysis is not completed yet"
        )
    
    result = analysis["result"]
    product_data = result.get("product_data")
    shop_data = result.get("shop_data")
    
    # 리포트 생성기 초기화
    report_generator = ReportGenerator()
    
    try:
        if format.lower() == "pdf":
            report_bytes = report_generator.generate_pdf_report(
                result,
                product_data,
                shop_data
            )
            from fastapi.responses import Response
            return Response(
                content=report_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=analysis_report_{analysis_id}.pdf"}
            )
        
        elif format.lower() == "excel":
            report_bytes = report_generator.generate_excel_report(
                result,
                product_data,
                shop_data
            )
            from fastapi.responses import Response
            return Response(
                content=report_bytes,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=analysis_report_{analysis_id}.xlsx"}
            )
        
        elif format.lower() == "markdown":
            report_content = report_generator.generate_markdown_report(
                result,
                product_data,
                shop_data
            )
            from fastapi.responses import Response
            return Response(
                content=report_content.encode('utf-8'),
                media_type="text/markdown",
                headers={"Content-Disposition": f"attachment; filename=analysis_report_{analysis_id}.md"}
            )
        
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid format. Use 'pdf', 'excel', or 'markdown'"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )


def is_valid_qoo10_url(url: str) -> bool:
    """Qoo10 URL 유효성 검증"""
    valid_domains = ["qoo10.jp", "qoo10.com", "www.qoo10.jp", "www.qoo10.com"]
    return any(domain in url for domain in valid_domains)


def normalize_qoo10_url(url: str) -> str:
    """Qoo10 URL 정규화 (다양한 형식을 표준 형식으로 변환)"""
    # URL에서 상품 코드 추출
    product_code = None
    
    # 다양한 패턴에서 상품 코드 추출
    patterns = [
        (r'goodscode=(\d+)', 1),
        (r'/g/(\d+)', 1),
        (r'/item/[^/]+/(\d+)', 1),
        (r'/item/[^/]+/(\d+)\?', 1),
    ]
    
    for pattern, group in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            product_code = match.group(group)
            break
    
    # 상품 코드가 있으면 표준 형식으로 변환
    if product_code:
        # 표준 형식: https://www.qoo10.jp/gmkt.inc/Goods/Goods.aspx?goodscode=XXXXX
        return f"https://www.qoo10.jp/gmkt.inc/Goods/Goods.aspx?goodscode={product_code}"
    
    # 변환할 수 없으면 원본 반환
    return url


def detect_url_type(url: str) -> str:
    """URL 타입 자동 감지 (다양한 Qoo10 URL 패턴 지원)"""
    url_lower = url.lower()
    
    # 상품 URL 패턴들
    product_patterns = [
        "/goods/goods.aspx",  # 기본 형식
        "/goods/",  # 소문자 변형
        "/g/",  # 짧은 형식 (예: /g/1093098159)
        "/item/",  # 긴 형식 (예: /item/.../1093098159)
        "goodscode=",  # 쿼리 파라미터
        "gmkt.inc/goods",  # 구형 URL
    ]
    
    # Shop URL 패턴들
    shop_patterns = [
        "/shop/",
        "shopid=",
        "shop_id=",
    ]
    
    # 상품 URL 확인
    for pattern in product_patterns:
        if pattern in url_lower or pattern in url:
            return "product"
    
    # Shop URL 확인
    for pattern in shop_patterns:
        if pattern in url_lower:
            return "shop"
    
    # 숫자 ID가 있는 경우 상품으로 추정 (예: /g/1093098159)
    if re.search(r'/g/\d+', url) or re.search(r'/item/.*/\d+', url):
        return "product"
    
    return "unknown"


def _update_progress(analysis_id: str, stage: str, percentage: int, message: str):
    """진행 상태 업데이트 헬퍼 함수"""
    if analysis_id in analysis_store:
        analysis_store[analysis_id]["progress"] = {
            "stage": stage,
            "percentage": percentage,
            "message": message
        }


async def perform_analysis(analysis_id: str, url: str, url_type: str):
    """
    분석 수행 (백그라운드 작업) - 초기 개발 기준 단순화 버전
    
    핵심 플로우:
    1. 크롤링 (필수 데이터만 수집)
    2. 기본 분석 (이미지, 설명, 가격, 리뷰, SEO)
    3. 추천 생성 (매출 강화 아이디어)
    4. 결과 저장
    """
    import asyncio
    import time
    
    try:
        logger.info(f"[{analysis_id}] Analysis started - URL: {url}, Type: {url_type}")
        
        # ========== 1단계: 크롤링 (20%) ==========
        _update_progress(analysis_id, "crawling", 10, "상품 페이지를 수집하는 중...")
        # 오류 신고 서비스를 크롤러에 주입하여 우선 크롤링 지원
        crawler = Qoo10Crawler(error_reporting_service=error_reporting_service)
        
        if url_type == "product":
            crawl_start_time = time.time()
            try:
                _update_progress(analysis_id, "crawling", 20, "페이지 데이터를 추출하는 중...")
                logger.info(f"[{analysis_id}] Starting product crawl - URL: {url}")
                
                # URL 정규화 확인
                normalized_url = crawler._normalize_product_url(url)
                logger.info(f"[{analysis_id}] Normalized URL: {normalized_url}")
                
                product_data = await crawler.crawl_product(url)
                
                # 크롤링 데이터 검증 (더 유연하게)
                if not product_data:
                    raise Exception("크롤링된 데이터가 없습니다")
                
                # 상품명이 없어도 계속 진행 (다른 필드로 대체 가능)
                product_name = product_data.get("product_name") or product_data.get("url") or "Unknown Product"
                if not product_data.get("product_name"):
                    logger.warning(f"[{analysis_id}] Product name not found, using fallback: {product_name}")
                    product_data["product_name"] = product_name
                
                crawl_duration_ms = int((time.time() - crawl_start_time) * 1000)
                pipeline_monitor.record_stage(
                    analysis_id=analysis_id,
                    url=url,
                    url_type=url_type,
                    stage="crawling",
                    status="success",
                    duration_ms=crawl_duration_ms,
                    metadata={"product_name": product_name, "product_code": product_data.get("product_code")}
                )
                
                logger.info(f"[{analysis_id}] Crawling completed - Product: {product_name}, Code: {product_data.get('product_code', 'N/A')}")
                logger.debug(f"[{analysis_id}] Crawled data keys: {list(product_data.keys())}")
            except httpx.HTTPError as e:
                crawl_duration_ms = int((time.time() - crawl_start_time) * 1000)
                error_msg = f"HTTP 오류 발생: {str(e)}"
                logger.error(f"[{analysis_id}] {error_msg}", exc_info=True)
                pipeline_monitor.record_stage(
                    analysis_id=analysis_id,
                    url=url,
                    url_type=url_type,
                    stage="crawling",
                    status="failure",
                    duration_ms=crawl_duration_ms,
                    error_message=error_msg
                )
                analysis_store[analysis_id]["status"] = "failed"
                analysis_store[analysis_id]["error"] = error_msg
                _update_progress(analysis_id, "failed", 0, error_msg)
                return
            except Exception as e:
                crawl_duration_ms = int((time.time() - crawl_start_time) * 1000)
                error_msg = f"크롤링 실패: {str(e)}"
                logger.error(f"[{analysis_id}] {error_msg}", exc_info=True)
                pipeline_monitor.record_stage(
                    analysis_id=analysis_id,
                    url=url,
                    url_type=url_type,
                    stage="crawling",
                    status="failure",
                    duration_ms=crawl_duration_ms,
                    error_message=error_msg
                )
                analysis_store[analysis_id]["status"] = "failed"
                analysis_store[analysis_id]["error"] = error_msg
                _update_progress(analysis_id, "failed", 0, error_msg)
                return
            
            # ========== 2단계: 기본 분석 (50%) ==========
            analysis_start_time = time.time()
            try:
                _update_progress(analysis_id, "analyzing", 30, "상품 데이터를 분석하는 중...")
                logger.info(f"[{analysis_id}] Starting product analysis...")
                logger.debug(f"[{analysis_id}] Product data summary - Name: {product_data.get('product_name', 'N/A')}, Price: {product_data.get('price', {}).get('sale_price', 'N/A')}")
                
                analyzer = ProductAnalyzer()
                analysis_result = await analyzer.analyze(product_data)
                
                # 분석 결과 검증 (더 유연하게)
                if not analysis_result:
                    logger.warning(f"[{analysis_id}] Analysis result is empty, creating default result")
                    analysis_result = {
                        "overall_score": 0,
                        "image_analysis": {},
                        "description_analysis": {},
                        "price_analysis": {},
                        "review_analysis": {},
                        "seo_analysis": {},
                        "page_structure_analysis": {}
                    }
                
                # overall_score가 없으면 기본값 설정
                if "overall_score" not in analysis_result:
                    logger.warning(f"[{analysis_id}] Overall score not found, setting default to 0")
                    analysis_result["overall_score"] = 0
                
                analysis_duration_ms = int((time.time() - analysis_start_time) * 1000)
                pipeline_monitor.record_stage(
                    analysis_id=analysis_id,
                    url=url,
                    url_type=url_type,
                    stage="analyzing",
                    status="success",
                    duration_ms=analysis_duration_ms,
                    metadata={"overall_score": analysis_result.get("overall_score", 0)}
                )
                
                logger.info(f"[{analysis_id}] Analysis completed - Score: {analysis_result.get('overall_score', 0)}")
            except Exception as e:
                analysis_duration_ms = int((time.time() - analysis_start_time) * 1000)
                error_msg = f"분석 실패: {str(e)}"
                logger.error(f"[{analysis_id}] {error_msg}", exc_info=True)
                pipeline_monitor.record_stage(
                    analysis_id=analysis_id,
                    url=url,
                    url_type=url_type,
                    stage="analyzing",
                    status="failure",
                    duration_ms=analysis_duration_ms,
                    error_message=error_msg
                )
                analysis_store[analysis_id]["status"] = "failed"
                analysis_store[analysis_id]["error"] = error_msg
                _update_progress(analysis_id, "failed", 0, error_msg)
                return
            
            # ========== 3단계: 추천 생성 (80%) ==========
            recommendations_start_time = time.time()
            try:
                _update_progress(analysis_id, "generating_recommendations", 60, "개선 제안을 생성하는 중...")
                logger.info(f"[{analysis_id}] Generating recommendations...")
                
                recommender = SalesEnhancementRecommender()
                recommendations = await recommender.generate_recommendations(
                    product_data,
                    analysis_result
                )
                
                # 추천 검증
                if not isinstance(recommendations, list):
                    recommendations = []
                
                recommendations_duration_ms = int((time.time() - recommendations_start_time) * 1000)
                pipeline_monitor.record_stage(
                    analysis_id=analysis_id,
                    url=url,
                    url_type=url_type,
                    stage="generating_recommendations",
                    status="success",
                    duration_ms=recommendations_duration_ms,
                    metadata={"recommendations_count": len(recommendations)}
                )
                
                logger.info(f"[{analysis_id}] Recommendations generated - Count: {len(recommendations)}")
            except Exception as e:
                recommendations_duration_ms = int((time.time() - recommendations_start_time) * 1000)
                logger.warning(f"[{analysis_id}] Recommendations generation failed: {str(e)}")
                pipeline_monitor.record_stage(
                    analysis_id=analysis_id,
                    url=url,
                    url_type=url_type,
                    stage="generating_recommendations",
                    status="failure",
                    duration_ms=recommendations_duration_ms,
                    error_message=str(e)
                )
                recommendations = []  # 추천 실패해도 계속 진행
            
            # ========== 4단계: 체크리스트 평가 (선택적, 빠르게) ==========
            checklist_result = None
            checklist_start_time = time.time()
            try:
                _update_progress(analysis_id, "evaluating_checklist", 75, "체크리스트를 평가하는 중...")
                checklist_evaluator = ChecklistEvaluator()
                checklist_result = await asyncio.wait_for(
                    checklist_evaluator.evaluate_checklist(
                        product_data=product_data,
                        analysis_result=analysis_result
                    ),
                    timeout=5.0  # 최대 5초로 제한
                )
                checklist_duration_ms = int((time.time() - checklist_start_time) * 1000)
                pipeline_monitor.record_stage(
                    analysis_id=analysis_id,
                    url=url,
                    url_type=url_type,
                    stage="evaluating_checklist",
                    status="success",
                    duration_ms=checklist_duration_ms,
                    metadata={"completion_rate": checklist_result.get("overall_completion", 0) if checklist_result else 0}
                )
                logger.info(f"[{analysis_id}] Checklist evaluation completed")
            except (asyncio.TimeoutError, Exception) as e:
                checklist_duration_ms = int((time.time() - checklist_start_time) * 1000)
                logger.warning(f"[{analysis_id}] Checklist evaluation skipped: {str(e)}")
                pipeline_monitor.record_stage(
                    analysis_id=analysis_id,
                    url=url,
                    url_type=url_type,
                    stage="evaluating_checklist",
                    status="failure",
                    duration_ms=checklist_duration_ms,
                    error_message=str(e)
                )
                checklist_result = None
            
            # ========== 5단계: 데이터 검증 (85%) ==========
            validation_result = None
            validation_start_time = time.time()
            try:
                _update_progress(analysis_id, "validating", 85, "데이터 일치 여부를 검증하는 중...")
                logger.info(f"[{analysis_id}] Validating data consistency...")
                
                # 크롤링 결과와 리포트 내용 일치 여부 검증
                validation_result = data_validator.validate_crawler_vs_report(
                    product_data=product_data,
                    analysis_result=analysis_result,
                    checklist_result=checklist_result or {}
                )
                
                validation_duration_ms = int((time.time() - validation_start_time) * 1000)
                pipeline_monitor.record_stage(
                    analysis_id=analysis_id,
                    url=url,
                    url_type=url_type,
                    stage="validating",
                    status="success",
                    duration_ms=validation_duration_ms,
                    metadata={
                        "validation_score": validation_result.get("validation_score", 0),
                        "is_valid": validation_result.get("is_valid", False),
                        "mismatches_count": len(validation_result.get("mismatches", [])),
                        "missing_items_count": len(validation_result.get("missing_items", []))
                    }
                )
                
                logger.info(f"[{analysis_id}] Validation completed - Score: {validation_result.get('validation_score', 0)}%, Valid: {validation_result.get('is_valid', False)}")
                
                # 검증 실패 시 경고 로그
                if not validation_result.get("is_valid"):
                    mismatches = validation_result.get("mismatches", [])
                    missing_items = validation_result.get("missing_items", [])
                    logger.warning(f"[{analysis_id}] Data validation failed - Mismatches: {len(mismatches)}, Missing: {len(missing_items)}")
            except Exception as e:
                validation_duration_ms = int((time.time() - validation_start_time) * 1000)
                logger.warning(f"[{analysis_id}] Data validation failed: {str(e)}")
                pipeline_monitor.record_stage(
                    analysis_id=analysis_id,
                    url=url,
                    url_type=url_type,
                    stage="validating",
                    status="failure",
                    duration_ms=validation_duration_ms,
                    error_message=str(e)
                )
                validation_result = None
            
            # ========== 6단계: 결과 저장 (100%) ==========
            finalizing_start_time = time.time()
            try:
                _update_progress(analysis_id, "finalizing", 90, "결과를 정리하는 중...")
                logger.info(f"[{analysis_id}] Finalizing results...")
                
                # 최종 결과 구성
                final_result = {
                    "product_analysis": analysis_result,
                    "recommendations": recommendations,
                    "checklist": checklist_result,
                    "competitor_analysis": None,  # 선택적 기능은 나중에
                    "product_data": product_data,
                    "validation": validation_result  # 검증 결과 추가
                }
                
                # 결과 저장
                analysis_store[analysis_id]["result"] = final_result
                analysis_store[analysis_id]["status"] = "completed"
                _update_progress(analysis_id, "completed", 100, "분석이 완료되었습니다.")
                
                finalizing_duration_ms = int((time.time() - finalizing_start_time) * 1000)
                pipeline_monitor.record_stage(
                    analysis_id=analysis_id,
                    url=url,
                    url_type=url_type,
                    stage="finalizing",
                    status="success",
                    duration_ms=finalizing_duration_ms
                )
                
                logger.info(f"[{analysis_id}] Analysis completed successfully - Score: {analysis_result.get('overall_score', 0)}")
                
                # 히스토리 저장은 비동기로 (실패해도 무시)
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(_save_history_and_notify_async(
                        analysis_id,
                        url,
                        url_type,
                        final_result,
                        analysis_result.get("overall_score", 0)
                    ))
                except Exception as e:
                    logger.warning(f"[{analysis_id}] Failed to schedule history save: {str(e)}")
                
            except Exception as e:
                finalizing_duration_ms = int((time.time() - finalizing_start_time) * 1000)
                error_msg = f"결과 저장 실패: {str(e)}"
                logger.error(f"[{analysis_id}] {error_msg}", exc_info=True)
                pipeline_monitor.record_stage(
                    analysis_id=analysis_id,
                    url=url,
                    url_type=url_type,
                    stage="finalizing",
                    status="failure",
                    duration_ms=finalizing_duration_ms,
                    error_message=error_msg
                )
                analysis_store[analysis_id]["status"] = "failed"
                analysis_store[analysis_id]["error"] = error_msg
                _update_progress(analysis_id, "failed", 0, error_msg)
        
        elif url_type == "shop":
            # ========== 1단계: Shop 크롤링 (20%) ==========
            try:
                _update_progress(analysis_id, "crawling", 10, "Shop 페이지를 수집하는 중...")
                logger.info(f"[{analysis_id}] Starting shop crawl...")
                shop_data = await crawler.crawl_shop(url)
                
                if not shop_data or not shop_data.get("shop_name"):
                    raise Exception("Shop 데이터를 추출할 수 없습니다")
                
                logger.info(f"[{analysis_id}] Shop crawl completed - Shop: {shop_data.get('shop_name', 'Unknown')}")
            except Exception as e:
                error_msg = f"Shop 크롤링 실패: {str(e)}"
                logger.error(f"[{analysis_id}] {error_msg}", exc_info=True)
                analysis_store[analysis_id]["status"] = "failed"
                analysis_store[analysis_id]["error"] = error_msg
                _update_progress(analysis_id, "failed", 0, error_msg)
                return
            
            # ========== 2단계: Shop 분석 (50%) ==========
            try:
                _update_progress(analysis_id, "analyzing", 40, "Shop 데이터를 분석하는 중...")
                logger.info(f"[{analysis_id}] Starting shop analysis...")
                shop_analyzer = ShopAnalyzer()
                analysis_result = await shop_analyzer.analyze(shop_data)
                logger.info(f"[{analysis_id}] Shop analysis completed")
            except Exception as e:
                error_msg = f"Shop 분석 실패: {str(e)}"
                logger.error(f"[{analysis_id}] {error_msg}", exc_info=True)
                analysis_store[analysis_id]["status"] = "failed"
                analysis_store[analysis_id]["error"] = error_msg
                _update_progress(analysis_id, "failed", 0, error_msg)
                return
            
            # ========== 3단계: 추천 생성 (80%) ==========
            try:
                _update_progress(analysis_id, "generating_recommendations", 60, "개선 제안을 생성하는 중...")
                logger.info(f"[{analysis_id}] Generating shop recommendations...")
                recommender = SalesEnhancementRecommender()
                recommendations = await recommender.generate_shop_recommendations(
                    shop_data,
                    analysis_result
                )
                if not isinstance(recommendations, list):
                    recommendations = []
                logger.info(f"[{analysis_id}] Shop recommendations generated - Count: {len(recommendations)}")
            except Exception as e:
                logger.warning(f"[{analysis_id}] Shop recommendations generation failed: {str(e)}")
                recommendations = []
            
            # ========== 4단계: 체크리스트 평가 (선택적) ==========
            checklist_result = None
            try:
                _update_progress(analysis_id, "evaluating_checklist", 75, "체크리스트를 평가하는 중...")
                checklist_evaluator = ChecklistEvaluator()
                checklist_result = await asyncio.wait_for(
                    checklist_evaluator.evaluate_checklist(
                        shop_data=shop_data,
                        analysis_result=analysis_result
                    ),
                    timeout=5.0
                )
            except (asyncio.TimeoutError, Exception) as e:
                logger.warning(f"[{analysis_id}] Checklist evaluation skipped: {str(e)}")
                checklist_result = None
            
            # ========== 5단계: 결과 저장 (100%) ==========
            try:
                _update_progress(analysis_id, "finalizing", 90, "결과를 정리하는 중...")
                final_result = {
                    "shop_analysis": analysis_result,
                    "recommendations": recommendations,
                    "checklist": checklist_result,
                    "shop_data": shop_data
                }
                analysis_store[analysis_id]["result"] = final_result
                analysis_store[analysis_id]["status"] = "completed"
                _update_progress(analysis_id, "completed", 100, "분석이 완료되었습니다.")
                
                logger.info(f"[{analysis_id}] Shop analysis completed successfully")
                
                # 히스토리 저장은 비동기로
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(_save_history_and_notify_async(
                        analysis_id,
                        url,
                        url_type,
                        final_result,
                        analysis_result.get("overall_score", 0)
                    ))
                except Exception as e:
                    logger.warning(f"[{analysis_id}] Failed to schedule history save: {str(e)}")
            except Exception as e:
                error_msg = f"결과 저장 실패: {str(e)}"
                logger.error(f"[{analysis_id}] {error_msg}", exc_info=True)
                analysis_store[analysis_id]["status"] = "failed"
                analysis_store[analysis_id]["error"] = error_msg
                _update_progress(analysis_id, "failed", 0, error_msg)
        
        else:
            error_msg = f"알 수 없는 URL 타입: {url_type}"
            logger.error(f"[{analysis_id}] {error_msg}")
import re
import logging
from dotenv import load_dotenv
import httpx

from services.crawler import Qoo10Crawler
        if analysis_id in analysis_store:
            analysis_store[analysis_id]["status"] = "failed"
            analysis_store[analysis_id]["error"] = error_msg
            _update_progress(analysis_id, "failed", 0, error_msg)


async def _save_history_and_notify_async(
    analysis_id: str,
    url: str,
    url_type: str,
    final_result: Dict[str, Any],
    overall_score: int
):
    """히스토리 저장과 알림을 비동기로 처리"""
    try:
        # 히스토리 저장
        history_manager.save_analysis_history(
            analysis_id,
            url,
            url_type,
            final_result
        )
        
        # 알림 생성
        notification_service.notify_analysis_completed(
            analysis_id,
            url,
            overall_score
        )
        
        # 임계값 알림
        notification_service.notify_threshold_alert(
            analysis_id,
            url,
            overall_score
        )
    except Exception as e:
        logger.warning(f"[{analysis_id}] History save failed: {str(e)}")


# ==================== SEO/AIO/GEO 최적화 엔드포인트 ====================

@app.post("/api/v1/seo/analyze")
async def analyze_seo(request: AnalyzeRequest):
    """
    SEO 분석 수행
    
    - URL을 입력받아 SEO 분석을 수행합니다
    - 상품 데이터가 있으면 함께 분석합니다
    """
    try:
        url_str = str(request.url)
        
        # URL 검증
        if not is_valid_qoo10_url(url_str):
            raise HTTPException(
                status_code=400,
                detail="Invalid Qoo10 URL. Please provide a valid Qoo10 product or shop URL."
            )
        
        # 크롤러로 상품 데이터 수집 (선택사항)
        product_data = None
        try:
            crawler = Qoo10Crawler()
            url_type = detect_url_type(url_str)
            if url_type == "product":
                product_data = await crawler.crawl_product(url_str)
        except:
            pass  # 크롤링 실패해도 SEO 분석은 진행
        
        # SEO 분석 수행
        seo_optimizer = SEOOptimizer()
        seo_result = await seo_optimizer.analyze(url_str, product_data)
        
        return {
            "status": "success",
            "url": url_str,
            "seo_analysis": seo_result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"SEO analysis failed: {str(e)}"
        )


@app.post("/api/v1/ai-seo/analyze")
async def analyze_ai_seo(request: AnalyzeRequest):
    """
    AI SEO 분석 수행
    
    - URL을 입력받아 AI 검색 엔진을 위한 SEO 분석을 수행합니다
    """
    try:
        url_str = str(request.url)
        
        # URL 검증
        if not is_valid_qoo10_url(url_str):
            raise HTTPException(
                status_code=400,
                detail="Invalid Qoo10 URL. Please provide a valid Qoo10 product or shop URL."
            )
        
        # 크롤러로 상품 데이터 수집 (선택사항)
        product_data = None
        try:
            crawler = Qoo10Crawler()
            url_type = detect_url_type(url_str)
            if url_type == "product":
                product_data = await crawler.crawl_product(url_str)
        except:
            pass  # 크롤링 실패해도 AI SEO 분석은 진행
        
        # AI SEO 분석 수행
        ai_seo_optimizer = AISEOOptimizer()
        ai_seo_result = await ai_seo_optimizer.analyze(url_str, product_data)
        
        return {
            "status": "success",
            "url": url_str,
            "ai_seo_analysis": ai_seo_result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI SEO analysis failed: {str(e)}"
        )


@app.post("/api/v1/geo/analyze")
async def analyze_geo(request: AnalyzeRequest):
    """
    GEO (Generative Engine Optimization) 분석 수행
    
    - URL을 입력받아 생성형 AI 검색 엔진을 위한 최적화 분석을 수행합니다
    """
    try:
        url_str = str(request.url)
        
        # URL 검증
        if not is_valid_qoo10_url(url_str):
            raise HTTPException(
                status_code=400,
                detail="Invalid Qoo10 URL. Please provide a valid Qoo10 product or shop URL."
            )
        
        # 크롤러로 상품 데이터 수집 (선택사항)
        product_data = None
        try:
            crawler = Qoo10Crawler()
            url_type = detect_url_type(url_str)
            if url_type == "product":
                product_data = await crawler.crawl_product(url_str)
        except:
            pass  # 크롤링 실패해도 GEO 분석은 진행
        
        # GEO 분석 수행
        geo_optimizer = GEOOptimizer()
        geo_result = await geo_optimizer.analyze(url_str, product_data)
        
        return {
            "status": "success",
            "url": url_str,
            "geo_analysis": geo_result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"GEO analysis failed: {str(e)}"
        )


@app.post("/api/v1/aio/analyze")
async def analyze_aio(request: AnalyzeRequest):
    """
    AIO (All-In-One) 종합 분석 수행
    
    - URL을 입력받아 SEO, AI SEO, GEO를 종합적으로 분석합니다
    """
    try:
        url_str = str(request.url)
        
        # URL 검증
        if not is_valid_qoo10_url(url_str):
            raise HTTPException(
                status_code=400,
                detail="Invalid Qoo10 URL. Please provide a valid Qoo10 product or shop URL."
            )
        
        # 크롤러로 상품 데이터 수집 (선택사항)
        product_data = None
        try:
            crawler = Qoo10Crawler()
            url_type = detect_url_type(url_str)
            if url_type == "product":
                product_data = await crawler.crawl_product(url_str)
        except:
            pass  # 크롤링 실패해도 AIO 분석은 진행
        
        # AIO 종합 분석 수행
        aio_optimizer = AIOOptimizer()
        aio_result = await aio_optimizer.analyze(url_str, product_data)
        
        return {
            "status": "success",
            "url": url_str,
            "aio_analysis": aio_result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AIO analysis failed: {str(e)}"
        )


@app.post("/api/v1/aio/optimize")
async def optimize_aio(request: AnalyzeRequest):
    """
    AIO 자동 최적화 수행
    
    - URL을 입력받아 자동으로 최적화 제안을 생성합니다
    """
    try:
        url_str = str(request.url)
        
        # URL 검증
        if not is_valid_qoo10_url(url_str):
            raise HTTPException(
                status_code=400,
                detail="Invalid Qoo10 URL. Please provide a valid Qoo10 product or shop URL."
            )
        
        # 크롤러로 상품 데이터 수집 (선택사항)
        product_data = None
        try:
            crawler = Qoo10Crawler()
            url_type = detect_url_type(url_str)
            if url_type == "product":
                product_data = await crawler.crawl_product(url_str)
        except:
            pass
        
        # AIO 최적화 수행
        aio_optimizer = AIOOptimizer()
        optimization_result = await aio_optimizer.optimize(url_str, product_data)
        
        return {
            "status": "success",
            "url": url_str,
            "optimization": optimization_result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AIO optimization failed: {str(e)}"
        )


@app.get("/api/v1/seo/sitemap")
async def generate_sitemap(urls: str):
    """
    Sitemap 생성
    
    - URL 목록을 입력받아 XML sitemap을 생성합니다
    - 쿼리 파라미터: urls (쉼표로 구분된 URL 목록)
    """
    try:
        url_list = [url.strip() for url in urls.split(",") if url.strip()]
        
        if not url_list:
            raise HTTPException(
                status_code=400,
                detail="Please provide at least one URL"
            )
        
        seo_optimizer = SEOOptimizer()
        base_url = url_list[0] if url_list else ""
        sitemap_xml = seo_optimizer.generate_sitemap(url_list, base_url)
        
        from fastapi.responses import Response
        return Response(
            content=sitemap_xml,
            media_type="application/xml",
            headers={"Content-Disposition": "attachment; filename=sitemap.xml"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Sitemap generation failed: {str(e)}"
        )


@app.get("/api/v1/seo/robots")
async def generate_robots_txt(
    allowed_paths: Optional[str] = None,
    disallowed_paths: Optional[str] = None,
    sitemap_url: Optional[str] = None
):
    """
    robots.txt 생성
    
    - 쿼리 파라미터로 robots.txt를 생성합니다
    """
    try:
        seo_optimizer = SEOOptimizer()
        
        allowed = allowed_paths.split(",") if allowed_paths else None
        disallowed = disallowed_paths.split(",") if disallowed_paths else None
        
        robots_txt = seo_optimizer.generate_robots_txt(
            allowed_paths=allowed,
            disallowed_paths=disallowed,
            sitemap_url=sitemap_url
        )
        
        from fastapi.responses import Response
        return Response(
            content=robots_txt,
            media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=robots.txt"}
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Robots.txt generation failed: {str(e)}"
        )


@app.post("/api/v1/geo/faq-schema")
async def generate_faq_schema(questions: List[str], answers: List[str]):
    """
    FAQ 스키마 생성
    
    - 질문과 답변 목록을 입력받아 FAQ 스키마를 생성합니다
    """
    try:
        if len(questions) != len(answers):
            raise HTTPException(
                status_code=400,
                detail="Questions and answers must have the same length"
            )
        
        geo_optimizer = GEOOptimizer()
        faq_schema = geo_optimizer.generate_faq_schema(questions, answers)
        
        return {
            "status": "success",
            "schema": faq_schema
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"FAQ schema generation failed: {str(e)}"
        )


@app.post("/api/v1/geo/howto-schema")
async def generate_howto_schema(name: str, steps: List[str], description: Optional[str] = None):
    """
    HowTo 스키마 생성
    
    - 가이드 이름과 단계를 입력받아 HowTo 스키마를 생성합니다
    """
    try:
        geo_optimizer = GEOOptimizer()
        howto_schema = geo_optimizer.generate_howto_schema(name, steps, description)
        
        return {
            "status": "success",
            "schema": howto_schema
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"HowTo schema generation failed: {str(e)}"
        )


@app.post("/api/v1/aio/report")
async def generate_aio_report(request: AnalyzeRequest, format: str = "json"):
    """
    AIO 리포트 생성
    
    - URL을 입력받아 종합 분석 리포트를 생성합니다
    - format: json 또는 markdown
    """
    try:
        url_str = str(request.url)
        
        # URL 검증
        if not is_valid_qoo10_url(url_str):
            raise HTTPException(
                status_code=400,
                detail="Invalid Qoo10 URL. Please provide a valid Qoo10 product or shop URL."
            )
        
        # 크롤러로 상품 데이터 수집 (선택사항)
        product_data = None
        try:
            crawler = Qoo10Crawler()
            url_type = detect_url_type(url_str)
            if url_type == "product":
                product_data = await crawler.crawl_product(url_str)
        except:
            pass
        
        # AIO 분석 수행
        aio_optimizer = AIOOptimizer()
        aio_result = await aio_optimizer.analyze(url_str, product_data)
        
        # 리포트 생성
        report = aio_optimizer.generate_report(aio_result, format=format)
        
        if format == "markdown":
            from fastapi.responses import Response
            return Response(
                content=report,
                media_type="text/markdown",
                headers={"Content-Disposition": "attachment; filename=aio_report.md"}
            )
        else:
            return {
                "status": "success",
                "url": url_str,
                "report": aio_result
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )


# TODO: In @api/main.py arounIn @api/main.py around lines 1003 - 1085, Add an admin authentication dependency and apply it to all admin routes: implement a verify_admin_key dependency (using APIKeyHeader / Security or Depends) that checks the incoming key against the ADMIN_API_KEY env var and raises HTTPException(403) on mismatch, and then add that dependency parameter (e.g., _: None = Depends(verify_admin_key) or _: None = Security(verify_admin_key)) to each admin endpoint function (get_analysis_logs, get_error_logs, get_score_statistics, get_analysis_statistics, get_user_analysis_logs, get_analysis_results_list, get_ai_insight_report) so all /api/v1/admin/* routes perform the authorization check.ines 899 - 903, The route currently uses a path parameter for URLs which breaks on embedded slashes; change the endpoint to accept the target URL as a query parameter instead of a path segment: update the decorator on get_score_trend (remove "{url}" from the path), modify the function signature to take url: str as a query arg (keep days: int = 30), and keep the call to history_manager.get_score_trend(url, days=days); also update any callers/tests to pass the URL via the query string (e.g., ?url=...) so full URLs with slashes are handled correctly.
# 히스토리 관리 API (Phase 3)
@app.get("/api/v1/history")
async def get_history(
    url: Optional[str] = None,
    url_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    분석 이력 조회
    
    - url: URL 필터 (선택사항)
    - url_type: URL 타입 필터 (선택사항)
    - limit: 조회 개수 제한
    - offset: 오프셋
    """
    history = history_manager.get_analysis_history(
        url=url,
        url_type=url_type,
        limit=limit,
        offset=offset
    )
    return {"history": history}


@app.get("/api/v1/history/{analysis_id}")
async def get_history_by_id(analysis_id: str):
    """분석 ID로 이력 조회"""
    history_item = history_manager.get_analysis_by_id(analysis_id)
    if not history_item:
        raise HTTPException(status_code=404, detail="History not found")
    return history_item


@app.get("/api/v1/history/url/trend")
async def get_score_trend(url: str = Query(...), days: int = 30):
    """점수 추이 조회"""
    trend = history_manager.get_score_trend(url, days=days)
    return {"trend": trend}


# 알림 API (Phase 3)
@app.get("/api/v1/notifications")
async def get_notifications(
    is_read: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0
):
    """알림 조회"""
    notifications = notification_service.get_notifications(
        is_read=is_read,
        limit=limit,
        offset=offset
    )
    unread_count = notification_service.get_unread_count()
    return {
        "notifications": notifications,
        "unread_count": unread_count
    }


@app.get("/api/v1/notifications/unread-count")
async def get_unread_count():
    """미읽음 알림 개수 조회"""
    count = notification_service.get_unread_count()
    return {"unread_count": count}


@app.post("/api/v1/notifications/{notification_id}/read")
async def mark_notification_as_read(notification_id: int):
    """알림 읽음 처리"""
    success = notification_service.mark_as_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}


@app.post("/api/v1/notifications/read-all")
async def mark_all_notifications_as_read():
    """모든 알림 읽음 처리"""
    count = notification_service.mark_all_as_read()
    return {"updated_count": count}


@app.delete("/api/v1/notifications/{notification_id}")
async def delete_notification(notification_id: int):
    """알림 삭제"""
    success = notification_service.delete_notification(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}


# 배치 분석 API (Phase 3)
class BatchAnalysisRequest(BaseModel):
    urls: List[HttpUrl] = Field(..., description="분석할 URL 리스트")
    name: Optional[str] = Field(None, description="배치 분석 이름")


@app.post("/api/v1/batch/analyze")
async def create_batch_analysis(request: BatchAnalysisRequest):
    """
    배치 분석 생성
    
    - 여러 URL을 한 번에 분석합니다
    - 백그라운드에서 처리됩니다
    """
    urls = [str(url) for url in request.urls]
    
    # URL 검증
    invalid_urls = []
    for url in urls:
        if not is_valid_qoo10_url(url):
            invalid_urls.append(url)
    
    if invalid_urls:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid Qoo10 URLs detected: {', '.join(invalid_urls)}. Please provide valid Qoo10 product or shop URLs."
        )
    
    batch_id = await batch_analyzer.create_batch_analysis(
        urls=urls,
        name=request.name
    )
    return {
        "batch_id": batch_id,
        "status": "pending",
        "total_count": len(urls)
    }


@app.get("/api/v1/batch/{batch_id}")
async def get_batch_analysis(batch_id: str):
    """배치 분석 조회"""
    batch = batch_analyzer.get_batch_analysis(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch analysis not found")
    return batch


@app.get("/api/v1/batch/{batch_id}/items")
async def get_batch_items(batch_id: str):
    """배치 분석 아이템 조회"""
    # 배치 존재 여부 확인 (get_batch_analysis와 동일한 방식)
    batch = batch_analyzer.get_batch_analysis(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    items = batch_analyzer.get_batch_items(batch_id)
    return {"items": items}


# Admin API
@app.get("/api/v1/admin/analysis-logs")
async def get_analysis_logs(
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """분석 로그 조회"""
    return admin_service.get_analysis_logs(
        limit=limit,
        offset=offset,
        status=status,
        start_date=start_date,
        end_date=end_date
    )


@app.get("/api/v1/admin/error-logs")
async def get_error_logs(
    limit: int = 100,
    offset: int = 0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """에러 로그 조회"""
    return admin_service.get_error_logs(
        limit=limit,
        offset=offset,
        start_date=start_date,
        end_date=end_date
    )


# ========== 오류 신고 API ==========

class ErrorReportRequest(BaseModel):
    analysis_id: str = Field(..., description="분석 ID")
    field_name: str = Field(..., description="문제가 있는 필드명")
    issue_type: str = Field(..., description="문제 유형 (mismatch, missing, incorrect)")
    severity: str = Field(..., description="심각도 (high, medium, low)")
    user_description: Optional[str] = Field(None, description="사용자 설명")
    crawler_value: Optional[Any] = Field(None, description="크롤러가 수집한 값")
    report_value: Optional[Any] = Field(None, description="리포트에 표시된 값")


@app.post("/api/v1/error/report")
async def report_error(request: ErrorReportRequest):
    """
    오류 신고
    
    - 크롤링 결과와 리포트 내용의 불일치를 신고합니다
    - 신고된 항목은 우선적으로 크롤링됩니다
    """
    try:
        # 분석 결과 조회
        if request.analysis_id not in analysis_store:
            raise HTTPException(
                status_code=404,
                detail="Analysis not found"
            )
        
        analysis = analysis_store[request.analysis_id]
        if analysis["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail="Analysis is not completed yet"
            )
        
        result = analysis.get("result", {})
        product_data = result.get("product_data", {})
        page_structure = product_data.get("page_structure", {})
        
        # 페이지 구조 Chunk 추출
        page_structure_chunk = None
        if page_structure:
            field_structure = page_structure.get(request.field_name, {})
            if field_structure:
                page_structure_chunk = {
                    "related_classes": field_structure.get("related_classes", []),
                    "element_present": field_structure.get("element_present", False),
                    "class_frequency": field_structure.get("class_frequency", {})
                }
        
        # 오류 신고 저장
        report_result = error_reporting_service.report_error(
            analysis_id=request.analysis_id,
            url=analysis["url"],
            field_name=request.field_name,
            issue_type=request.issue_type,
            severity=request.severity,
            user_description=request.user_description,
            crawler_value=request.crawler_value,
            report_value=request.report_value,
            page_structure_chunk=page_structure_chunk
        )
        
        return {
            "status": "success",
            "message": "오류 신고가 저장되었습니다.",
            "error_report_id": report_result["error_report_id"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reporting failed: {str(e)}"
        )


@app.get("/api/v1/error/reports")
async def get_error_reports(
    field_name: Optional[str] = None,
    status: str = "pending",
    limit: int = 50
):
    """
    오류 신고 목록 조회
    
    - field_name: 특정 필드의 오류 신고만 조회 (선택사항)
    - status: 신고 상태 (pending, resolved)
    """
    try:
        if field_name:
            reports = error_reporting_service.db.get_error_reports_by_field(field_name, status)
        else:
            # 모든 오류 신고 조회
            from services.database import CrawlerDatabase
            db = CrawlerDatabase()
            with db.get_connection() as conn:
                cursor = conn.cursor()
                if db.use_postgres:
                    cursor.execute("""
                        SELECT * FROM error_reports
                        WHERE status = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (status, limit))
                else:
                    cursor.execute("""
                        SELECT * FROM error_reports
                        WHERE status = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    """, (status, limit))
                rows = cursor.fetchall()
                reports = [dict(row) for row in rows]
        
        return {
            "status": "success",
            "reports": reports,
            "count": len(reports)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get error reports: {str(e)}"
        )


@app.get("/api/v1/error/priority-fields")
async def get_priority_fields():
    """
    우선 크롤링해야 할 필드 목록 조회
    
    - 오류 신고가 많은 필드들을 우선순위로 반환
    """
    try:
        priority_fields = error_reporting_service.get_priority_fields_for_crawling()
        return {
            "status": "success",
            "priority_fields": priority_fields
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get priority fields: {str(e)}"
        )


@app.get("/api/v1/error/chunks/{field_name}")
async def get_chunks_for_field(field_name: str):
    """
    특정 필드에 대한 Chunk 목록 조회
    
    - 유사한 사이트 구조 크롤링 시 참고용
    """
    try:
        chunks = error_reporting_service.get_chunks_for_field(field_name)
        return {
            "status": "success",
            "field_name": field_name,
            "chunks": chunks,
            "count": len(chunks)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get chunks: {str(e)}"
        )


@app.post("/api/v1/error/resolve/{error_report_id}")
async def resolve_error(error_report_id: int):
    """
    오류 신고를 해결됨으로 표시
    """
    try:
        success = error_reporting_service.mark_error_resolved(error_report_id)
        if success:
            return {
                "status": "success",
                "message": "오류 신고가 해결됨으로 표시되었습니다."
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Error report not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resolve error: {str(e)}"
        )


@app.get("/api/v1/admin/statistics/score")
async def get_score_statistics(days: int = 30):
    """점수 통계 조회"""
    return admin_service.get_score_statistics(days=days)


# ========== 파이프라인 모니터링 API ==========

@app.get("/api/v1/admin/pipeline/success-rates")
async def get_pipeline_success_rates(
    period_type: str = "day",
    days: int = 7
):
    """
    파이프라인 성공률 조회
    
    - period_type: 집계 기간 타입 (hour/day/week/month)
    - days: 조회할 일수 (day 타입일 때만 사용)
    """
    try:
        if period_type not in ["hour", "day", "week", "month"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid period_type. Use 'hour', 'day', 'week', or 'month'"
            )
        
        stats = pipeline_monitor.get_success_rates(period_type=period_type, days=days)
        return {
            "status": "success",
            "data": stats
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get pipeline success rates: {str(e)}"
        )


@app.get("/api/v1/admin/pipeline/stage-details/{stage}")
async def get_pipeline_stage_details(
    stage: str,
    limit: int = 100
):
    """
    특정 파이프라인 단계의 상세 기록 조회
    
    - stage: 파이프라인 단계 (crawling, analyzing, generating_recommendations, evaluating_checklist, validating, finalizing)
    - limit: 조회할 레코드 수
    """
    try:
        if stage not in pipeline_monitor.STAGES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid stage. Use one of: {', '.join(pipeline_monitor.STAGES)}"
            )
        
        details = pipeline_monitor.get_stage_details(stage=stage, limit=limit)
        return {
            "status": "success",
            "stage": stage,
            "data": details,
            "count": len(details)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stage details: {str(e)}"
        )


@app.get("/api/v1/admin/statistics/analysis")
async def get_analysis_statistics(days: int = 30):
    """분석 통계 조회"""
    return admin_service.get_analysis_statistics(days=days)


@app.get("/api/v1/admin/user-logs")
async def get_user_analysis_logs(
    url: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """사용자 분석 로그 조회"""
    return admin_service.get_user_analysis_logs(
        url=url,
        limit=limit,
        offset=offset
    )


@app.get("/api/v1/admin/analysis-results")
async def get_analysis_results_list(
    limit: int = 50,
    offset: int = 0,
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    url_type: Optional[str] = None
):
    """분석 결과 리스트 조회"""
    return admin_service.get_analysis_results_list(
        limit=limit,
        offset=offset,
        min_score=min_score,
        max_score=max_score,
        url_type=url_type
    )


@app.get("/api/v1/admin/ai-insight-report")
async def get_ai_insight_report(days: int = 30):
    """AI 분석 리포트 생성"""
    return admin_service.generate_ai_insight_report(days=days)


# ========== 파이프라인 모니터링 API ==========

@app.get("/api/v1/admin/pipeline/success-rates")
async def get_pipeline_success_rates(
    period_type: str = "day",
    days: int = 7
):
    """
    파이프라인 성공률 조회
    
    - period_type: 집계 기간 타입 (hour/day/week/month)
    - days: 조회할 일수 (day 타입일 때만 사용)
    """
    try:
        if period_type not in ["hour", "day", "week", "month"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid period_type. Use 'hour', 'day', 'week', or 'month'"
            )
        
        stats = pipeline_monitor.get_success_rates(period_type=period_type, days=days)
        return {
            "status": "success",
            "data": stats
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get pipeline success rates: {str(e)}"
        )


@app.get("/api/v1/admin/pipeline/stage-details/{stage}")
async def get_pipeline_stage_details(
    stage: str,
    limit: int = 100
):
    """
    특정 파이프라인 단계의 상세 기록 조회
    
    - stage: 파이프라인 단계 (crawling, analyzing, generating_recommendations, evaluating_checklist, validating, finalizing)
    - limit: 조회할 레코드 수
    """
    try:
        if stage not in pipeline_monitor.STAGES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid stage. Use one of: {', '.join(pipeline_monitor.STAGES)}"
            )
        
        details = pipeline_monitor.get_stage_details(stage=stage, limit=limit)
        return {
            "status": "success",
            "stage": stage,
            "data": details,
            "count": len(details)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stage details: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
