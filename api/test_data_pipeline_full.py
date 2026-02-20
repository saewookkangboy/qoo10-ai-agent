"""
전체 에이전트 데이터 파이프라인 테스트 (상품 + Shop 지원)
- Crawl → Analysis → Recommendation → Checklist → Validation → Report
- URL 타입 자동 감지 (product / shop)
- 누락 데이터 정밀 분석용 결과 저장
"""
import asyncio
import json
import re
import sys
import os
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.crawler import Qoo10Crawler
from services.analyzer import ProductAnalyzer
from services.shop_analyzer import ShopAnalyzer
from services.recommender import SalesEnhancementRecommender
from services.checklist_evaluator import ChecklistEvaluator
from services.report_generator import ReportGenerator
from services.data_validator import DataValidator
from services.error_reporting_service import ErrorReportingService


def detect_url_type(url: str) -> str:
    """URL 타입 감지"""
    url_lower = url.lower()
    if any(p in url_lower for p in ["/shop/", "shopid=", "shop_id="]):
        return "shop"
    if any(p in url_lower for p in ["/goods/", "/g/", "goodscode=", "/item/"]):
        return "product"
    if re.search(r"/shop/[^/]+", url_lower):
        return "shop"
    return "product"


async def run_product_pipeline(
    url: str,
    crawler: Qoo10Crawler,
    analyzer: ProductAnalyzer,
    recommender: SalesEnhancementRecommender,
    checklist_evaluator: ChecklistEvaluator,
    data_validator: DataValidator,
    report_generator: ReportGenerator,
) -> Dict[str, Any]:
    """상품 URL 전체 파이프라인"""
    print("[1] 크롤링 (상품)...")
    product_data = await crawler.crawl_product(url, use_playwright=True)
    if not product_data:
        raise ValueError("크롤링 결과가 없습니다.")
    print(f"    ✓ product_data 필드 수: {len(product_data)}")

    print("[2] 분석 (ProductAnalyzer)...")
    analysis_result = await analyzer.analyze(product_data)
    analysis_result = {"product_analysis": analysis_result} if "product_analysis" not in analysis_result else analysis_result
    score = analysis_result.get("product_analysis", {}).get("overall_score", analysis_result.get("overall_score", 0))
    print(f"    ✓ overall_score: {score}")

    print("[3] 추천 생성...")
    try:
        recommendations = await asyncio.wait_for(
            recommender.generate_recommendations(product_data, analysis_result),
            timeout=30.0,
        )
    except asyncio.TimeoutError:
        recommendations = []
    print(f"    ✓ recommendations: {len(recommendations)}개")

    print("[4] 체크리스트 평가...")
    try:
        checklist_result = await asyncio.wait_for(
            checklist_evaluator.evaluate_checklist(
                product_data=product_data,
                analysis_result=analysis_result,
            ),
            timeout=10.0,
        )
    except (asyncio.TimeoutError, Exception) as e:
        checklist_result = None
        print(f"    ⚠ 체크리스트 스킵: {e}")
    else:
        print(f"    ✓ overall_completion: {checklist_result.get('overall_completion', 0)}%")

    print("[5] 데이터 검증...")
    validation_result = data_validator.validate_crawler_vs_report(
        product_data=product_data,
        analysis_result=analysis_result,
        checklist_result=checklist_result or {},
    )
    print(f"    ✓ validation_score: {validation_result.get('validation_score', 0)}%, is_valid: {validation_result.get('is_valid')}")

    print("[6] 리포트 생성 (Markdown)...")
    report_content = report_generator.generate_markdown_report(
        analysis_result,
        product_data,
        validation_result=validation_result,
    )
    print(f"    ✓ 리포트 길이: {len(report_content)}자")

    return {
        "url": url,
        "url_type": "product",
        "product_data": product_data,
        "shop_data": None,
        "analysis_result": analysis_result,
        "recommendations": recommendations,
        "checklist_result": checklist_result,
        "validation_result": validation_result,
        "report_preview": report_content[:2000] if report_content else "",
    }


async def run_shop_pipeline(
    url: str,
    crawler: Qoo10Crawler,
    shop_analyzer: ShopAnalyzer,
    recommender: SalesEnhancementRecommender,
    checklist_evaluator: ChecklistEvaluator,
    data_validator: DataValidator,
    report_generator: ReportGenerator,
) -> Dict[str, Any]:
    """Shop URL 전체 파이프라인"""
    print("[1] 크롤링 (Shop)...")
    shop_data = await crawler.crawl_shop(url, use_playwright=True)
    if not shop_data:
        raise ValueError("Shop 크롤링 결과가 없습니다.")
    print(f"    ✓ shop_data 필드 수: {len(shop_data)}")
    print(f"    - shop_name: {shop_data.get('shop_name', 'N/A')}")
    print(f"    - shop_level: {shop_data.get('shop_level', 'N/A')}")
    print(f"    - follower_count: {shop_data.get('follower_count', 'N/A')}")
    print(f"    - product_count: {shop_data.get('product_count', 'N/A')}")
    print(f"    - products: {len(shop_data.get('products', []))}개")
    print(f"    - coupons: {len(shop_data.get('coupons', []))}개")
    print(f"    - categories: {len(shop_data.get('categories', {}))}개")

    print("[2] 분석 (ShopAnalyzer)...")
    raw_analysis = await shop_analyzer.analyze(shop_data, checklist_result=None)
    analysis_result = {"shop_analysis": raw_analysis}
    score = raw_analysis.get("overall_score", 0)
    print(f"    ✓ overall_score: {score}")

    print("[3] 추천 생성 (Shop)...")
    try:
        recommendations = await asyncio.wait_for(
            recommender.generate_shop_recommendations(shop_data, analysis_result),
            timeout=30.0,
        )
    except asyncio.TimeoutError:
        recommendations = []
    print(f"    ✓ recommendations: {len(recommendations)}개")

    print("[4] 체크리스트 평가 (Shop)...")
    page_structure = shop_data.get("page_structure")
    try:
        checklist_result = await asyncio.wait_for(
            checklist_evaluator.evaluate_checklist(
                shop_data=shop_data,
                analysis_result=analysis_result,
                page_structure=page_structure,
            ),
            timeout=10.0,
        )
    except (asyncio.TimeoutError, Exception) as e:
        checklist_result = None
        print(f"    ⚠ 체크리스트 스킵: {e}")
    else:
        print(f"    ✓ overall_completion: {checklist_result.get('overall_completion', 0)}%")

    print("[5] 데이터 검증 (Shop)...")
    try:
        validation_result = data_validator.validate_crawler_vs_report(
            shop_data=shop_data,
            analysis_result=analysis_result,
            checklist_result=checklist_result or {},
        )
    except Exception as e:
        validation_result = {
            "is_valid": False,
            "validation_score": 0,
            "mismatches": [],
            "missing_items": [],
            "message": str(e),
        }
        print(f"    ⚠ 검증 예외: {e}")
    else:
        print(f"    ✓ validation_score: {validation_result.get('validation_score', 0)}%, is_valid: {validation_result.get('is_valid')}")

    print("[6] 리포트 생성 (Markdown, Shop)...")
    try:
        report_content = report_generator.generate_markdown_report(
            analysis_result,
            product_data=None,
            shop_data=shop_data,
            validation_result=validation_result,
        )
    except Exception as e:
        report_content = f"(리포트 생성 실패: {e})"
        print(f"    ⚠ {e}")
    else:
        print(f"    ✓ 리포트 길이: {len(report_content)}자")

    return {
        "url": url,
        "url_type": "shop",
        "product_data": None,
        "shop_data": shop_data,
        "analysis_result": analysis_result,
        "recommendations": recommendations,
        "checklist_result": checklist_result,
        "validation_result": validation_result,
        "report_preview": report_content[:2000] if report_content else "",
    }


def analyze_missing_data(
    result: Dict[str, Any],
    expected_shop: Optional[Dict[str, Any]] = None,
    expected_product: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    누락 데이터 정밀 분석.
    expected_shop: Shop 페이지 기준 기대값
    expected_product: 상품 페이지 기준 기대값 (product_code, review_count, sale_price 등)
    """
    url_type = result.get("url_type", "product")
    missing = {"fields_empty": [], "expected_vs_actual": [], "suggestions": []}

    if url_type == "product" and result.get("product_data"):
        product_data = result["product_data"]
        analysis = result.get("analysis_result", {}).get("product_analysis", {})
        # 빈 필드
        key_fields = [
            "product_name", "product_code", "url", "price", "reviews", "description",
            "images", "page_structure", "crawled_with",
        ]
        for k in key_fields:
            v = product_data.get(k)
            if v is None or (isinstance(v, (list, dict)) and len(v) == 0):
                if k != "description":  # description 빈 값 허용
                    missing["fields_empty"].append(k)
        review_count = (product_data.get("reviews") or {}).get("review_count")
        if review_count is None or (isinstance(review_count, int) and review_count == 0 and expected_product and expected_product.get("review_count")):
            missing["fields_empty"].append("reviews.review_count")
        # 기대값 vs 실제 (상품 1093098159 기준)
        if expected_product:
            for field, expected_val in expected_product.items():
                if field == "review_count":
                    actual = (product_data.get("reviews") or {}).get("review_count")
                elif field == "sale_price":
                    actual = (product_data.get("price") or {}).get("sale_price")
                elif field == "original_price":
                    actual = (product_data.get("price") or {}).get("original_price")
                elif field == "rating":
                    actual = (product_data.get("reviews") or {}).get("rating")
                elif field == "has_thumbnail":
                    actual = bool((product_data.get("images") or {}).get("thumbnail"))
                elif field == "detail_images_min":
                    actual = len((product_data.get("images") or {}).get("detail_images", []))
                    # expected_val 이상이면 OK
                    if isinstance(expected_val, int) and actual >= expected_val:
                        continue
                    if actual != expected_val:
                        missing["expected_vs_actual"].append({
                            "field": "detail_images_count",
                            "expected": f">= {expected_val}",
                            "actual": actual,
                        })
                    continue
                else:
                    actual = product_data.get(field)
                if actual != expected_val:
                    missing["expected_vs_actual"].append({
                        "field": field,
                        "expected": expected_val,
                        "actual": actual,
                    })
        # 이미지 빈 필드
        imgs = product_data.get("images") or {}
        if not imgs.get("thumbnail") and not imgs.get("detail_images"):
            missing["fields_empty"].append("images.thumbnail or images.detail_images")
        # 제안
        if "reviews.review_count" in missing["fields_empty"] or any("review_count" in str(x) for x in missing["expected_vs_actual"]):
            missing["suggestions"].append("상품 페이지에서 'レビュー (N)' 또는 '4.8 (N)' 패턴으로 총 리뷰 수 추출 (쉼표 허용), crawler._extract_reviews / Playwright JS")
        if "images.thumbnail or images.detail_images" in missing["fields_empty"] or any("detail_images" in str(x) for x in missing["expected_vs_actual"]):
            missing["suggestions"].append("썸네일/상세 이미지: crawler._extract_images(썸네일·itemGoods·detail 선택자, img alt 수집), Playwright JS로 #itemGoods img 보강")
        return missing

    if url_type == "shop":
        shop_data = result.get("shop_data") or {}
        # 빈 필드 수집
        key_fields = [
            "shop_name", "shop_id", "shop_level", "follower_count", "product_count",
            "categories", "products", "coupons", "page_structure", "url", "crawled_with",
        ]
        for k in key_fields:
            v = shop_data.get(k)
            if v is None or (isinstance(v, (list, dict)) and len(v) == 0):
                missing["fields_empty"].append(k)
            elif k == "follower_count" and v == 0:
                missing["fields_empty"].append(f"{k}(0)")
            elif k == "product_count" and v == 0:
                missing["fields_empty"].append(f"{k}(0)")

        # 기대값 vs 실제 (whippedofficial 기준)
        if expected_shop:
            for field, expected_val in expected_shop.items():
                actual = shop_data.get(field)
                if actual != expected_val:
                    missing["expected_vs_actual"].append({
                        "field": field,
                        "expected": expected_val,
                        "actual": actual,
                    })

        # 제안
        if "follower_count" in missing["fields_empty"] or any("follower" in str(x) for x in missing["fields_empty"]):
            missing["suggestions"].append("Shop 페이지에서 'フォロワー' 텍스트 정규식 추출 강화 (crawler_shop._extract_follower_count)")
        if "product_count" in missing["fields_empty"] or any("product_count" in str(x) for x in missing["fields_empty"]):
            missing["suggestions"].append("'全ての商品 (N)' 패턴 추출 강화 (crawler_shop._extract_product_count)")
        if "coupons" in missing["fields_empty"] or (shop_data.get("coupons") in ([], None)):
            missing["suggestions"].append("Shop 쿠폰 영역 셀렉터/정규식 점검 (crawler_shop._extract_shop_coupons)")

    return missing


async def run_manual_pipeline_step() -> Optional[Dict[str, Any]]:
    """메뉴얼 파이프라인 실행 (수집 → 검증 → 누락 분석). 전체 에이전트 활용 시 선택 호출."""
    try:
        from run_manual_pipeline import run_manual_pipeline as _run
        return await _run(manual_path=None)
    except Exception as e:
        print(f"    ⚠ 메뉴얼 파이프라인 스킵: {e}")
        return None


async def main():
    test_url = "https://www.qoo10.jp/shop/whippedofficial"
    run_manual = False
    argv = [a for a in sys.argv[1:] if a != "--manual"]
    if "--manual" in sys.argv:
        run_manual = True
    if argv:
        test_url = argv[0].strip()

    url_type = detect_url_type(test_url)
    print("=" * 80)
    print("전체 에이전트 데이터 파이프라인 테스트")
    print("=" * 80)
    print(f"URL: {test_url}")
    print(f"URL 타입: {url_type}")
    if run_manual:
        print("메뉴얼 파이프라인: 실행함 (수집 → 검증 → 누락 분석)\n")
    else:
        print("메뉴얼 파이프라인: 생략 (--manual 옵션으로 실행)\n")

    error_reporting_service = ErrorReportingService()
    crawler = Qoo10Crawler(error_reporting_service=error_reporting_service)
    analyzer = ProductAnalyzer()
    shop_analyzer = ShopAnalyzer()
    recommender = SalesEnhancementRecommender()
    checklist_evaluator = ChecklistEvaluator()
    data_validator = DataValidator()
    report_generator = ReportGenerator()

    try:
        if url_type == "shop":
            result = await run_shop_pipeline(
                test_url,
                crawler,
                shop_analyzer,
                recommender,
                checklist_evaluator,
                data_validator,
                report_generator,
            )
        else:
            result = await run_product_pipeline(
                test_url,
                crawler,
                analyzer,
                recommender,
                checklist_evaluator,
                data_validator,
                report_generator,
            )

        # 누락 데이터 정밀 분석
        expected_shop = None
        expected_product = None
        if url_type == "shop" and "whippedofficial" in test_url:
            expected_shop = {
                "shop_name": "ホイップド公式",
                "follower_count": 51981,
                "product_count": 18,
            }
        if url_type == "product" and "1093098159" in test_url:
            # g/1093098159: 販売価格 2,990円, 参考 3,300円, レビュー (1,063), 4.8, 썸네일+상세 이미지
            expected_product = {
                "product_code": "1093098159",
                "sale_price": 2990,
                "original_price": 3300,
                "review_count": 1063,
                "rating": 4.8,
                "has_thumbnail": True,
                "detail_images_min": 1,  # 상세/제품 소개 이미지 최소 1개 이상
            }
        missing_analysis = analyze_missing_data(result, expected_shop=expected_shop, expected_product=expected_product)

        # (선택) 메뉴얼 파이프라인: 큐텐 대학 한국어 메뉴얼 수집·검증·누락 분석
        manual_result = None
        if run_manual:
            print("\n[메뉴얼] 수집·검증·누락 분석...")
            manual_result = await run_manual_pipeline_step()
            if manual_result:
                ma = manual_result.get("missing_analysis", {})
                print(f"    ✓ coverage_score: {ma.get('coverage_score', 0)}%, 누락 링크: {len(ma.get('missing_links') or [])}건")

        # JSON 저장 시 바이트/중첩 객체 제한
        def _serializable(obj: Any, depth: int = 0):
            if depth > 5:
                return "<<max depth>>"
            if obj is None or isinstance(obj, (bool, int, float, str)):
                return obj
            if isinstance(obj, (list, tuple)):
                return [_serializable(x, depth + 1) for x in obj[:50]]
            if isinstance(obj, dict):
                return {k: _serializable(v, depth + 1) for k, v in list(obj.items())[:100]}
            return str(type(obj))

        result_export = {
            "url": result["url"],
            "url_type": result["url_type"],
            "analysis_result": result["analysis_result"],
            "recommendations_count": len(result.get("recommendations", [])),
            "checklist_overall_completion": (result.get("checklist_result") or {}).get("overall_completion"),
            "validation_result": result.get("validation_result"),
            "missing_analysis": missing_analysis,
            "manual_missing_analysis": (
                manual_result.get("missing_analysis") if manual_result else None
            ),
            "shop_data_summary": None,
            "product_data_summary": None,
        }
        if result.get("shop_data"):
            sd = result["shop_data"]
            result_export["shop_data_summary"] = {
                "shop_name": sd.get("shop_name"),
                "shop_id": sd.get("shop_id"),
                "shop_level": sd.get("shop_level"),
                "follower_count": sd.get("follower_count"),
                "product_count": sd.get("product_count"),
                "products_len": len(sd.get("products", [])),
                "coupons_len": len(sd.get("coupons", [])),
                "categories_len": len(sd.get("categories", {})),
                "has_page_structure": bool(sd.get("page_structure")),
            }
        if result.get("product_data"):
            pd = result["product_data"]
            result_export["product_data_summary"] = {
                "product_name": pd.get("product_name"),
                "product_code": pd.get("product_code"),
                "has_price": bool(pd.get("price")),
                "images_count": len((pd.get("images") or {}).get("detail_images", [])),
            }

        out_path = "test_data_pipeline_full_result.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result_export, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 80)
        print("누락 데이터 정밀 분석")
        print("=" * 80)
        print("빈 필드:", missing_analysis.get("fields_empty", []))
        print("기대 vs 실제:", json.dumps(missing_analysis.get("expected_vs_actual", []), ensure_ascii=False, indent=2))
        print("제안:", missing_analysis.get("suggestions", []))

        print("\n" + "=" * 80)
        print("테스트 완료")
        print("=" * 80)
        print(f"결과 요약: {out_path}")

    except Exception as e:
        print(f"\n오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
