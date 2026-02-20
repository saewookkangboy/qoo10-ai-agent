"""
분석 리포트와 실제 페이지 내용 비교 테스트
"""
import asyncio
import json
import os
import sys
from typing import Dict, Any, List
from datetime import datetime

_API_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "api")
sys.path.insert(0, _API_DIR)
_TESTS_RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
os.makedirs(_TESTS_RESULTS_DIR, exist_ok=True)

# 로깅 설정
LOG_PATH = "/Users/chunghyo/qoo10-ai-agent/.cursor/debug.log"

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
    
    print(f"테스트 URL: {test_url}")
    print("=" * 80)
    
    # 가설 정의
    hypotheses = {
        "A": "상품 제목이 누락되거나 잘못 추출됨",
        "B": "가격 정보(정가, 할인가, 쿠폰가)가 누락되거나 잘못 추출됨",
        "C": "리뷰/평점 정보가 누락되거나 잘못 추출됨",
        "D": "상품 설명이 누락되거나 일부만 추출됨",
        "E": "이미지가 누락되거나 일부만 추출됨",
        "F": "배송 정보가 누락됨",
        "G": "쿠폰/할인 정보가 누락됨",
        "H": "상품 옵션(사이즈, 색상 등)이 누락됨",
        "I": "Qポイント 정보가 누락됨",
        "J": "반품/교환 정보가 누락됨"
    }
    
    log_debug(session_id, run_id, "INIT", "test_analysis_comparison.py:main", "테스트 시작", {
        "url": test_url,
        "hypotheses": hypotheses
    })
    
    try:
        # 크롤러 및 분석기 import
        from services.crawler import Qoo10Crawler
        from services.analyzer import ProductAnalyzer
        
        # 크롤러 초기화
        crawler = Qoo10Crawler()
        log_debug(session_id, run_id, "INIT", "test_analysis_comparison.py:main", "크롤러 초기화 완료")
        
        # 페이지 크롤링 (Playwright 사용)
        print("\n[1단계] 페이지 크롤링 중 (Playwright 사용)...")
        log_debug(session_id, run_id, "A", "test_analysis_comparison.py:main", "크롤링 시작 전", {"url": test_url})
        
        # Playwright를 사용하여 크롤링 (동적 콘텐츠 로딩)
        try:
            product_data = await crawler.crawl_product_with_playwright(test_url)
        except Exception as e:
            print(f"Playwright 크롤링 실패, 일반 크롤링 시도: {e}")
            product_data = await crawler.crawl_product(test_url, use_playwright=False)
        
        log_debug(session_id, run_id, "A", "test_analysis_comparison.py:main", "크롤링 완료", {
            "product_name": product_data.get("product_name", ""),
            "has_price": bool(product_data.get("price")),
            "has_reviews": bool(product_data.get("reviews")),
            "has_description": bool(product_data.get("description")),
            "has_images": bool(product_data.get("images")),
            "image_count": len(product_data.get("images", {}).get("product_images", [])) if product_data.get("images") else 0
        })
        
        print(f"크롤링된 데이터:")
        print(f"  - 상품명: {product_data.get('product_name', 'N/A')[:50]}...")
        print(f"  - 가격: {product_data.get('price', {})}")
        print(f"  - 리뷰: {product_data.get('reviews', {})}")
        print(f"  - 이미지 수: {len(product_data.get('images', {}).get('product_images', [])) if product_data.get('images') else 0}")
        
        # 분석기 초기화 및 분석 실행
        print("\n[2단계] 분석 실행 중...")
        try:
            analyzer = ProductAnalyzer()
            log_debug(session_id, run_id, "B", "test_analysis_comparison.py:main", "분석 시작 전", {
                "product_name": product_data.get("product_name", "")[:50]
            })
            
            analysis_result = await analyzer.analyze(product_data)
            
            log_debug(session_id, run_id, "B", "test_analysis_comparison.py:main", "분석 완료", {
                "has_price_analysis": bool(analysis_result.get("price_analysis")),
                "has_review_analysis": bool(analysis_result.get("review_analysis")),
                "has_description_analysis": bool(analysis_result.get("description_analysis")),
                "has_image_analysis": bool(analysis_result.get("image_analysis")),
                "has_seo_analysis": bool(analysis_result.get("seo_analysis"))
            })
        except Exception as e:
            print(f"분석 단계에서 에러 발생 (계속 진행): {e}")
            analysis_result = {}
        
        # 리포트는 생략하고 크롤링 데이터만 확인
        print("\n[3단계] 데이터 검증 중...")
        report = {}
        
        # 실제 페이지에서 확인해야 할 항목들 (웹 검색 결과 기반)
        expected_items = {
            "product_name": "3箱セット【剥離あり】ダーマスキンピーリング",
            "price": "2,990円",
            "original_price": "29,400円",
            "sale_price": "24,700円",
            "review_rating": "4.6",
            "review_count": "184",
            "coupon_info": "쿠폰 정보 존재",
            "qpoint_info": "Qポイント 정보 존재",
            "return_info": "返品 정보 존재",
            "delivery_info": "배송 정보 존재"
        }
        
        print("\n[4단계] 리포트와 실제 페이지 비교...")
        print("=" * 80)
        
        missing_items = []
        mismatched_items = []
        
        # 리포트에서 추출된 데이터
        report_product_name = product_data.get("product_name", "")
        report_price = product_data.get("price", {})
        report_reviews = product_data.get("reviews", {})
        
        log_debug(session_id, run_id, "D", "test_analysis_comparison.py:main", "비교 시작", {
            "expected_items": expected_items,
            "report_product_name": report_product_name[:100] if report_product_name else "",
            "report_price": report_price,
            "report_reviews": report_reviews
        })
        
        # 1. 상품명 확인
        if not report_product_name:
            missing_items.append("상품명")
            log_debug(session_id, run_id, "A", "test_analysis_comparison.py:main", "상품명 누락 확인", {})
        elif expected_items["product_name"] not in report_product_name and report_product_name not in expected_items["product_name"]:
            mismatched_items.append(f"상품명: 예상 '{expected_items['product_name'][:30]}...', 실제 '{report_product_name[:50]}...'")
            log_debug(session_id, run_id, "A", "test_analysis_comparison.py:main", "상품명 불일치", {
                "expected": expected_items["product_name"][:50],
                "actual": report_product_name[:50]
            })
        else:
            log_debug(session_id, run_id, "A", "test_analysis_comparison.py:main", "상품명 일치", {})
        
        # 2. 가격 정보 확인
        sale_price = report_price.get("sale_price") or report_price.get("current_price") or report_price.get("price")
        original_price = report_price.get("original_price") or report_price.get("list_price")
        
        if not sale_price and not original_price:
            missing_items.append("가격 정보")
            log_debug(session_id, run_id, "B", "test_analysis_comparison.py:main", "가격 정보 누락", {})
        else:
            log_debug(session_id, run_id, "B", "test_analysis_comparison.py:main", "가격 정보 존재", {
                "sale_price": sale_price,
                "original_price": original_price
            })
        
        # 3. 리뷰 정보 확인
        review_count = report_reviews.get("review_count") or report_reviews.get("count")
        review_rating = report_reviews.get("rating") or report_reviews.get("average_rating")
        
        if not review_count and not review_rating:
            missing_items.append("리뷰/평점 정보")
            log_debug(session_id, run_id, "C", "test_analysis_comparison.py:main", "리뷰 정보 누락", {})
        else:
            log_debug(session_id, run_id, "C", "test_analysis_comparison.py:main", "리뷰 정보 존재", {
                "review_count": review_count,
                "review_rating": review_rating
            })
        
        # 4. 상품 설명 확인
        description = product_data.get("description", "")
        if not description or len(description) < 50:
            missing_items.append("상품 설명 (충분한 길이)")
            log_debug(session_id, run_id, "D", "test_analysis_comparison.py:main", "상품 설명 부족", {
                "description_length": len(description)
            })
        else:
            log_debug(session_id, run_id, "D", "test_analysis_comparison.py:main", "상품 설명 존재", {
                "description_length": len(description)
            })
        
        # 5. 이미지 확인
        images = product_data.get("images", {}).get("product_images", [])
        if not images or len(images) == 0:
            missing_items.append("상품 이미지")
            log_debug(session_id, run_id, "E", "test_analysis_comparison.py:main", "이미지 누락", {})
        else:
            log_debug(session_id, run_id, "E", "test_analysis_comparison.py:main", "이미지 존재", {
                "image_count": len(images)
            })
        
        # 6. 쿠폰 정보 확인
        coupon_info = product_data.get("coupons") or product_data.get("discount_info")
        if not coupon_info:
            missing_items.append("쿠폰/할인 정보")
            log_debug(session_id, run_id, "G", "test_analysis_comparison.py:main", "쿠폰 정보 누락", {})
        else:
            log_debug(session_id, run_id, "G", "test_analysis_comparison.py:main", "쿠폰 정보 존재", {})
        
        # 7. 배송 정보 확인
        delivery_info = product_data.get("delivery") or product_data.get("shipping")
        if not delivery_info:
            missing_items.append("배송 정보")
            log_debug(session_id, run_id, "F", "test_analysis_comparison.py:main", "배송 정보 누락", {})
        else:
            log_debug(session_id, run_id, "F", "test_analysis_comparison.py:main", "배송 정보 존재", {})
        
        # 8. Qポイント 정보 확인
        qpoint_info = product_data.get("qpoint") or product_data.get("points")
        if not qpoint_info:
            missing_items.append("Qポイント 정보")
            log_debug(session_id, run_id, "I", "test_analysis_comparison.py:main", "Qポイント 정보 누락", {})
        else:
            log_debug(session_id, run_id, "I", "test_analysis_comparison.py:main", "Qポイント 정보 존재", {})
        
        # 9. 반품 정보 확인
        return_info = product_data.get("return") or product_data.get("return_policy")
        if not return_info:
            missing_items.append("반품/교환 정보")
            log_debug(session_id, run_id, "J", "test_analysis_comparison.py:main", "반품 정보 누락", {})
        else:
            log_debug(session_id, run_id, "J", "test_analysis_comparison.py:main", "반품 정보 존재", {})
        
        # 결과 출력
        print("\n[비교 결과]")
        print("=" * 80)
        print(f"\n✅ 추출된 데이터:")
        print(f"  - 상품명: {report_product_name[:80] if report_product_name else 'N/A'}")
        print(f"  - 가격: {report_price}")
        print(f"  - 리뷰: {report_reviews}")
        print(f"  - 이미지 수: {len(images)}")
        print(f"  - 설명 길이: {len(description)} 문자")
        
        print(f"\n❌ 누락된 항목 ({len(missing_items)}개):")
        for item in missing_items:
            print(f"  - {item}")
        
        if mismatched_items:
            print(f"\n⚠️ 불일치 항목 ({len(mismatched_items)}개):")
            for item in mismatched_items:
                print(f"  - {item}")
        
        # 전체 데이터 구조 확인
        print(f"\n📊 추출된 전체 데이터 키:")
        print(f"  {list(product_data.keys())}")
        
        log_debug(session_id, run_id, "RESULT", "test_analysis_comparison.py:main", "테스트 완료", {
            "missing_items": missing_items,
            "mismatched_items": mismatched_items,
            "extracted_keys": list(product_data.keys())
        })
        
        # 리포트를 파일로 저장
        result_path = os.path.join(_TESTS_RESULTS_DIR, "test_analysis_result.json")
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump({
                "product_data": product_data,
                "analysis_result": analysis_result,
                "report": report,
                "missing_items": missing_items,
                "mismatched_items": mismatched_items
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 결과가 '{result_path}'에 저장되었습니다.")
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        log_debug(session_id, run_id, "ERROR", "test_analysis_comparison.py:main", "에러 발생", {
            "error": error_msg,
            "traceback": traceback_str
        })
        print(f"\n❌ 에러 발생: {error_msg}")
        print(traceback_str)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
