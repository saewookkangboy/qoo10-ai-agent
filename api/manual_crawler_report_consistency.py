"""
크롤러 및 분석 결과 리포트 간의 데이터 일치 여부 테스트
"""
import asyncio
import json
import sys
from typing import Dict, Any
from datetime import datetime

# 로깅 설정 (crawler와 동일한 규칙 사용)
# - CRAWLER_DEBUG_LOG_PATH: 파일 경로 지정 (기본: 프로젝트 루트/.cursor/debug.log)
import os
from pathlib import Path

_default_log_path = Path(__file__).resolve().parents[1].parent / ".cursor" / "debug.log"
LOG_PATH = Path(os.getenv("CRAWLER_DEBUG_LOG_PATH", str(_default_log_path)))
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
def log_debug(session_id: str, run_id: str, hypothesis_id: str, location: str, message: str, data: Dict[str, Any] = None):
    """디버그 로그 작성"""
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
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Logging error: {e}")

async def main():
    test_url = "https://www.qoo10.jp/g/1093098159"
    session_id = "debug-session"
    run_id = "run1"
    
    print("=" * 80)
    print("크롤러 및 분석 결과 리포트 간의 데이터 일치 여부 테스트")
    print("=" * 80)
    print(f"테스트 URL: {test_url}\n")
    
    # 가설 정의
    hypotheses = {
        "H1": "크롤러가 수집한 데이터가 체크리스트 평가 과정에서 손실됨",
        "H2": "analysis_result 구조가 체크리스트 평가에 전달될 때 불일치 발생",
        "H3": "리포트 생성 시 크롤러 데이터와 체크리스트 결과가 매핑되지 않음",
        "H4": "데이터 검증 과정에서 유효한 데이터가 제거됨",
        "H5": "체크리스트 평가 결과가 리포트에 반영되지 않음"
    }
    
    log_debug(session_id, run_id, "INIT", "test_crawler_report_consistency.py:main", "테스트 시작", {
        "url": test_url,
        "hypotheses": hypotheses
    })
    
    try:
        from services.crawler import Qoo10Crawler
        from services.analyzer import ProductAnalyzer
        from services.checklist_evaluator import ChecklistEvaluator
        from services.report_generator import ReportGenerator
        
        # ========== 1단계: 크롤링 ==========
        print("[1단계] 크롤링 중...")
        crawler = Qoo10Crawler()
        log_debug(session_id, run_id, "H1", "test_crawler_report_consistency.py:main", "크롤링 시작", {"url": test_url})
        
        product_data = await crawler.crawl_product(test_url, use_playwright=True)
        
        # 크롤러 데이터 핵심 필드 로깅
        log_debug(session_id, run_id, "H1", "test_crawler_report_consistency.py:main", "크롤링 완료 - 원본 데이터", {
            "product_name": product_data.get("product_name", ""),
            "has_price": bool(product_data.get("price")),
            "price_sale": product_data.get("price", {}).get("sale_price"),
            "price_original": product_data.get("price", {}).get("original_price"),
            "has_reviews": bool(product_data.get("reviews")),
            "review_count": product_data.get("reviews", {}).get("review_count"),
            "review_rating": product_data.get("reviews", {}).get("rating"),
            "has_description": bool(product_data.get("description")),
            "description_length": len(product_data.get("description", "")),
            "has_images": bool(product_data.get("images")),
            "image_count": len(product_data.get("images", {}).get("detail_images", [])),
            "has_qpoint": bool(product_data.get("qpoint_info")),
            "qpoint_max": product_data.get("qpoint_info", {}).get("max_points"),
            "has_coupon": bool(product_data.get("coupon_info")),
            "has_shipping": bool(product_data.get("shipping_info")),
            "return_policy": product_data.get("shipping_info", {}).get("return_policy"),
            "has_category": bool(product_data.get("category")),
            "has_brand": bool(product_data.get("brand")),
            "has_search_keywords": bool(product_data.get("search_keywords")),
            "all_keys": list(product_data.keys())
        })
        
        print(f"  ✓ 크롤링 완료: {len(product_data)}개 필드")
        
        # ========== 2단계: 분석 ==========
        print("\n[2단계] 분석 실행 중...")
        analyzer = ProductAnalyzer()
        log_debug(session_id, run_id, "H2", "test_crawler_report_consistency.py:main", "분석 시작", {
            "product_name": product_data.get("product_name", "")[:50]
        })
        
        analysis_result = await analyzer.analyze(product_data)
        
        # analysis_result 구조 로깅
        log_debug(session_id, run_id, "H2", "test_crawler_report_consistency.py:main", "분석 완료 - analysis_result 구조", {
            "has_overall_score": bool(analysis_result.get("overall_score")),
            "overall_score": analysis_result.get("overall_score"),
            "has_image_analysis": bool(analysis_result.get("image_analysis")),
            "image_score": analysis_result.get("image_analysis", {}).get("score"),
            "has_price_analysis": bool(analysis_result.get("price_analysis")),
            "price_score": analysis_result.get("price_analysis", {}).get("score"),
            "price_sale": analysis_result.get("price_analysis", {}).get("sale_price"),
            "price_original": analysis_result.get("price_analysis", {}).get("original_price"),
            "has_review_analysis": bool(analysis_result.get("review_analysis")),
            "review_score": analysis_result.get("review_analysis", {}).get("score"),
            "review_count": analysis_result.get("review_analysis", {}).get("review_count"),
            "review_rating": analysis_result.get("review_analysis", {}).get("rating"),
            "has_description_analysis": bool(analysis_result.get("description_analysis")),
            "description_score": analysis_result.get("description_analysis", {}).get("score"),
            "has_seo_analysis": bool(analysis_result.get("seo_analysis")),
            "seo_score": analysis_result.get("seo_analysis", {}).get("score"),
            "all_keys": list(analysis_result.keys())
        })
        
        print(f"  ✓ 분석 완료: 종합 점수 {analysis_result.get('overall_score', 0)}점")
        
        # ========== 3단계: 체크리스트 평가 ==========
        print("\n[3단계] 체크리스트 평가 중...")
        checklist_evaluator = ChecklistEvaluator()
        log_debug(session_id, run_id, "H3", "test_crawler_report_consistency.py:main", "체크리스트 평가 시작", {
            "product_data_keys": list(product_data.keys()),
            "analysis_result_keys": list(analysis_result.keys())
        })
        
        # 체크리스트 평가 전 product_data 상태 확인
        log_debug(session_id, run_id, "H4", "test_crawler_report_consistency.py:main", "체크리스트 평가 전 - product_data 상태", {
            "product_name": product_data.get("product_name", ""),
            "price_sale": product_data.get("price", {}).get("sale_price"),
            "price_original": product_data.get("price", {}).get("original_price"),
            "has_qpoint": bool(product_data.get("qpoint_info")),
            "return_policy": product_data.get("shipping_info", {}).get("return_policy")
        })
        
        checklist_result = await checklist_evaluator.evaluate_checklist(
            product_data=product_data,
            shop_data=None,
            analysis_result=analysis_result,
            page_structure=product_data.get("page_structure")
        )
        
        # 체크리스트 결과 로깅
        log_debug(session_id, run_id, "H3", "test_crawler_report_consistency.py:main", "체크리스트 평가 완료", {
            "overall_completion": checklist_result.get("overall_completion", 0),
            "checklist_count": len(checklist_result.get("checklists", [])),
            "completed_items": sum(
                len([item for item in cl.get("items", []) if item.get("status") == "completed"])
                for cl in checklist_result.get("checklists", [])
            ),
            "total_items": sum(
                len(cl.get("items", []))
                for cl in checklist_result.get("checklists", [])
            ),
            "checklist_categories": [cl.get("category") for cl in checklist_result.get("checklists", [])]
        })
        
        # 각 체크리스트 항목별 상세 로깅
        for checklist in checklist_result.get("checklists", []):
            category = checklist.get("category", "")
            for item in checklist.get("items", []):
                item_id = item.get("id", "")
                status = item.get("status", "")
                auto_checked = item.get("auto_checked", False)
                log_debug(session_id, run_id, "H5", "test_crawler_report_consistency.py:main", f"체크리스트 항목: {item_id}", {
                    "category": category,
                    "title": item.get("title", ""),
                    "status": status,
                    "auto_checked": auto_checked,
                    "recommendation": item.get("recommendation", "")[:100] if item.get("recommendation") else ""
                })
        
        print(f"  ✓ 체크리스트 평가 완료: 전체 완성도 {checklist_result.get('overall_completion', 0)}%")
        
        # ========== 4단계: 리포트 생성 ==========
        print("\n[4단계] 리포트 생성 중...")
        report_generator = ReportGenerator()
        log_debug(session_id, run_id, "H3", "test_crawler_report_consistency.py:main", "리포트 생성 시작", {
            "has_product_data": bool(product_data),
            "has_analysis_result": bool(analysis_result),
            "has_checklist_result": bool(checklist_result)
        })
        
        # 리포트 생성 (Markdown 형식)
        final_result = {
            "product_analysis": analysis_result,
            "checklist": checklist_result,
            "product_data": product_data
        }
        
        markdown_report = report_generator.generate_markdown_report(
            analysis_result=final_result,
            product_data=product_data,
            shop_data=None
        )
        
        log_debug(session_id, run_id, "H3", "test_crawler_report_consistency.py:main", "리포트 생성 완료", {
            "report_length": len(markdown_report),
            "has_checklist_in_report": "체크리스트" in markdown_report or "checklist" in markdown_report.lower(),
            "has_product_info": "상품 정보" in markdown_report or "product" in markdown_report.lower()
        })
        
        print(f"  ✓ 리포트 생성 완료: {len(markdown_report)} 문자")
        
        # ========== 5단계: 데이터 일치 여부 검증 ==========
        print("\n[5단계] 데이터 일치 여부 검증 중...")
        
        # 검증 1: 크롤러 데이터 → 분석 결과 일치 여부
        inconsistencies = []
        
        # 가격 정보 일치 여부
        crawler_price_sale = product_data.get("price", {}).get("sale_price")
        analysis_price_sale = analysis_result.get("price_analysis", {}).get("sale_price")
        if crawler_price_sale != analysis_price_sale:
            inconsistencies.append({
                "field": "price.sale_price",
                "crawler": crawler_price_sale,
                "analysis": analysis_price_sale,
                "hypothesis": "H2"
            })
        
        crawler_price_original = product_data.get("price", {}).get("original_price")
        analysis_price_original = analysis_result.get("price_analysis", {}).get("original_price")
        if crawler_price_original != analysis_price_original:
            inconsistencies.append({
                "field": "price.original_price",
                "crawler": crawler_price_original,
                "analysis": analysis_price_original,
                "hypothesis": "H2"
            })
        
        # 리뷰 정보 일치 여부
        crawler_review_count = product_data.get("reviews", {}).get("review_count")
        analysis_review_count = analysis_result.get("review_analysis", {}).get("review_count")
        if crawler_review_count != analysis_review_count:
            inconsistencies.append({
                "field": "reviews.review_count",
                "crawler": crawler_review_count,
                "analysis": analysis_review_count,
                "hypothesis": "H2"
            })
        
        crawler_review_rating = product_data.get("reviews", {}).get("rating")
        analysis_review_rating = analysis_result.get("review_analysis", {}).get("rating")
        if crawler_review_rating != analysis_review_rating:
            inconsistencies.append({
                "field": "reviews.rating",
                "crawler": crawler_review_rating,
                "analysis": analysis_review_rating,
                "hypothesis": "H2"
            })
        
        # 검증 2: 체크리스트 평가에서 사용된 데이터 확인
        # item_001 (상품 등록 완료) 체크
        item_001 = None
        for checklist in checklist_result.get("checklists", []):
            for item in checklist.get("items", []):
                if item.get("id") == "item_001":
                    item_001 = item
                    break
            if item_001:
                break
        
        if item_001:
            item_001_status = item_001.get("status")
            has_product_name = bool(product_data.get("product_name"))
            has_description = bool(product_data.get("description"))
            has_images = bool(product_data.get("images", {}).get("thumbnail") or product_data.get("images", {}).get("detail_images"))
            
            if item_001_status == "pending" and (has_product_name and has_description and has_images):
                inconsistencies.append({
                    "field": "checklist.item_001",
                    "issue": "데이터가 있는데 체크리스트에서 pending으로 표시됨",
                    "crawler_has_name": has_product_name,
                    "crawler_has_description": has_description,
                    "crawler_has_images": has_images,
                    "checklist_status": item_001_status,
                    "hypothesis": "H1"
                })
        
        # item_004 (가격 설정 완료) 체크
        item_004 = None
        for checklist in checklist_result.get("checklists", []):
            for item in checklist.get("items", []):
                if item.get("id") == "item_004":
                    item_004 = item
                    break
            if item_004:
                break
        
        if item_004:
            item_004_status = item_004.get("status")
            has_price = bool(product_data.get("price", {}).get("sale_price"))
            
            if item_004_status == "pending" and has_price:
                inconsistencies.append({
                    "field": "checklist.item_004",
                    "issue": "가격 데이터가 있는데 체크리스트에서 pending으로 표시됨",
                    "crawler_has_price": has_price,
                    "checklist_status": item_004_status,
                    "hypothesis": "H1"
                })
        
        # 검증 3: 리포트에 체크리스트 반영 여부
        has_checklist_in_markdown = "체크리스트" in markdown_report or "checklist" in markdown_report.lower()
        if not has_checklist_in_markdown:
            inconsistencies.append({
                "field": "report.checklist",
                "issue": "리포트에 체크리스트 정보가 포함되지 않음",
                "hypothesis": "H5"
            })
        
        # 불일치 사항 로깅
        log_debug(session_id, run_id, "RESULT", "test_crawler_report_consistency.py:main", "데이터 일치 검증 완료", {
            "inconsistencies_count": len(inconsistencies),
            "inconsistencies": inconsistencies
        })
        
        # 결과 출력
        print("\n" + "=" * 80)
        print("검증 결과")
        print("=" * 80)
        
        if inconsistencies:
            print(f"\n❌ 발견된 불일치 사항: {len(inconsistencies)}개\n")
            for i, inc in enumerate(inconsistencies, 1):
                print(f"{i}. [{inc.get('hypothesis', 'N/A')}] {inc.get('field', 'N/A')}")
                if 'issue' in inc:
                    print(f"   문제: {inc['issue']}")
                if 'crawler' in inc:
                    print(f"   크롤러 값: {inc['crawler']}")
                if 'analysis' in inc:
                    print(f"   분석 값: {inc['analysis']}")
                print()
        else:
            print("\n✅ 모든 데이터가 일치합니다!")
        
        # 결과를 파일로 저장
        result_data = {
            "crawler_data": {
                "product_name": product_data.get("product_name"),
                "price": product_data.get("price"),
                "reviews": product_data.get("reviews"),
                "qpoint_info": product_data.get("qpoint_info"),
                "coupon_info": product_data.get("coupon_info"),
                "shipping_info": product_data.get("shipping_info")
            },
            "analysis_result": {
                "overall_score": analysis_result.get("overall_score"),
                "price_analysis": analysis_result.get("price_analysis"),
                "review_analysis": analysis_result.get("review_analysis")
            },
            "checklist_result": {
                "overall_completion": checklist_result.get("overall_completion"),
                "checklists": checklist_result.get("checklists")
            },
            "inconsistencies": inconsistencies
        }
        
        with open("test_consistency_result.json", "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 상세 결과가 'test_consistency_result.json'에 저장되었습니다.")
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        log_debug(session_id, run_id, "ERROR", "test_crawler_report_consistency.py:main", "에러 발생", {
            "error": error_msg,
            "traceback": traceback_str
        })
        print(f"\n❌ 에러 발생: {error_msg}")
        print(traceback_str)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
