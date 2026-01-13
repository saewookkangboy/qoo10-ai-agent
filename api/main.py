"""
Qoo10 Sales Intelligence Agent - FastAPI Main Application
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
import os
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
from services.seo_optimizer import SEOOptimizer
from services.ai_seo_optimizer import AISEOOptimizer
from services.geo_optimizer import GEOOptimizer
from services.aio_optimizer import AIOOptimizer

load_dotenv()

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
        
        # 분석 ID 생성
        analysis_id = str(uuid.uuid4())
        
        # 분석 작업 시작 (백그라운드)
        background_tasks.add_task(
            perform_analysis,
            analysis_id,
            url_str,
            url_type
        )
        
        # 초기 상태 저장
        analysis_store[analysis_id] = {
            "analysis_id": analysis_id,
            "url": url_str,
            "url_type": url_type,
            "status": "processing",
            "created_at": datetime.now().isoformat(),
            "result": None
        }
        
        return AnalyzeResponse(
            analysis_id=analysis_id,
            status="processing",
            url_type=url_type,
            estimated_time=30
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed to start: {str(e)}"
        )


@app.get("/api/v1/analyze/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    """
    분석 결과 조회
    
    - analysis_id로 분석 결과를 조회합니다
    - status가 "completed"일 때만 결과를 반환합니다
    """
    if analysis_id not in analysis_store:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found"
        )
    
    analysis = analysis_store[analysis_id]
    
    if analysis["status"] == "processing":
        return {
            "analysis_id": analysis_id,
            "status": "processing",
            "message": "Analysis is still in progress"
        }
    
    if analysis["status"] == "failed":
        return {
            "analysis_id": analysis_id,
            "status": "failed",
            "error": analysis.get("error")
        }
    
    return {
        "analysis_id": analysis_id,
        "status": "completed",
        "result": analysis["result"]
    }


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


def detect_url_type(url: str) -> str:
    """URL 타입 자동 감지"""
    if "/Goods/Goods.aspx" in url or "/goods/" in url.lower():
        return "product"
    elif "/shop/" in url.lower():
        return "shop"
    else:
        return "unknown"


async def perform_analysis(analysis_id: str, url: str, url_type: str):
    """분석 수행 (백그라운드 작업)"""
    try:
        # 크롤러 초기화
        crawler = Qoo10Crawler()
        
        # 데이터 수집
        if url_type == "product":
            product_data = await crawler.crawl_product(url)
            
            # 분석기 초기화
            analyzer = ProductAnalyzer()
            analysis_result = await analyzer.analyze(product_data)
            
            # 추천 시스템 초기화
            recommender = SalesEnhancementRecommender()
            recommendations = await recommender.generate_recommendations(
                product_data,
                analysis_result
            )
            
            # 체크리스트 평가 (Phase 2)
            checklist_evaluator = ChecklistEvaluator()
            checklist_result = await checklist_evaluator.evaluate_checklist(
                product_data=product_data,
                analysis_result=analysis_result
            )
            
            # 경쟁사 분석 (Phase 2)
            competitor_analyzer = CompetitorAnalyzer()
            competitor_result = await competitor_analyzer.analyze_competitors(
                product_data
            )
            
            # 결과 저장
            final_result = {
                "product_analysis": analysis_result,
                "recommendations": recommendations,
                "checklist": checklist_result,
                "competitor_analysis": competitor_result,
                "product_data": product_data
            }
            analysis_store[analysis_id]["result"] = final_result
            analysis_store[analysis_id]["status"] = "completed"
            
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
                analysis_result.get("overall_score", 0)
            )
            
            # 임계값 알림
            notification_service.notify_threshold_alert(
                analysis_id,
                url,
                analysis_result.get("overall_score", 0)
            )
        
        elif url_type == "shop":
            shop_data = await crawler.crawl_shop(url)
            
            # Shop 분석기 초기화
            shop_analyzer = ShopAnalyzer()
            analysis_result = await shop_analyzer.analyze(shop_data)
            
            # 추천 시스템 초기화 (Shop용)
            recommender = SalesEnhancementRecommender()
            recommendations = await recommender.generate_shop_recommendations(
                shop_data,
                analysis_result
            )
            
            # 체크리스트 평가 (Phase 2)
            checklist_evaluator = ChecklistEvaluator()
            checklist_result = await checklist_evaluator.evaluate_checklist(
                shop_data=shop_data,
                analysis_result=analysis_result
            )
            
            # 결과 저장
            final_result = {
                "shop_analysis": analysis_result,
                "recommendations": recommendations,
                "checklist": checklist_result,
                "shop_data": shop_data
            }
            analysis_store[analysis_id]["result"] = final_result
            analysis_store[analysis_id]["status"] = "completed"
            
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
                analysis_result.get("overall_score", 0)
            )
            
            # 임계값 알림
            notification_service.notify_threshold_alert(
                analysis_id,
                url,
                analysis_result.get("overall_score", 0)
            )
        
        else:
            analysis_store[analysis_id]["status"] = "failed"
            analysis_store[analysis_id]["error"] = "Unknown URL type"
    
    except Exception as e:
        analysis_store[analysis_id]["status"] = "failed"
        analysis_store[analysis_id]["error"] = str(e)


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


@app.get("/api/v1/history/url/{url}/trend")
async def get_score_trend(url: str, days: int = 30):
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
    items = batch_analyzer.get_batch_items(batch_id)
    return {"items": items}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
