"""
데이터 파이프라인 테스트
- 크롤링 → 분석 → 리포트 생성 → 데이터 검증 → 오류 신고
"""
import asyncio
import json
from services.crawler import Qoo10Crawler
from services.analyzer import ProductAnalyzer
from services.checklist_evaluator import ChecklistEvaluator
from services.report_generator import ReportGenerator
from services.data_validator import DataValidator
from services.error_reporting_service import ErrorReportingService

async def main():
    test_url = "https://www.qoo10.jp/g/1093098159"
    
    print("=" * 80)
    print("데이터 파이프라인 테스트")
    print("=" * 80)
    print(f"테스트 URL: {test_url}\n")
    
    try:
        # 서비스 초기화
        error_reporting_service = ErrorReportingService()
        crawler = Qoo10Crawler(error_reporting_service=error_reporting_service)
        analyzer = ProductAnalyzer()
        checklist_evaluator = ChecklistEvaluator()
        report_generator = ReportGenerator()
        data_validator = DataValidator()
        
        # 1. 크롤링
        print("[1단계] 크롤링 중...")
        product_data = await crawler.crawl_product(test_url, use_playwright=True)
        print(f"  ✓ 크롤링 완료: {len(product_data)}개 필드")
        
        # 2. 분석
        print("\n[2단계] 분석 실행 중...")
        analysis_result = await analyzer.analyze(product_data)
        print(f"  ✓ 분석 완료: 점수 {analysis_result.get('overall_score', 0)}")
        
        # 3. 체크리스트 평가
        print("\n[3단계] 체크리스트 평가 중...")
        checklist_result = await checklist_evaluator.evaluate_checklist(
            product_data=product_data,
            analysis_result=analysis_result
        )
        completion = checklist_result.get("overall_completion", 0)
        print(f"  ✓ 체크리스트 완료: {completion}%")
        
        # 4. 리포트 생성
        print("\n[4단계] 리포트 생성 중...")
        report_content = report_generator.generate_markdown_report(
            analysis_result,
            product_data
        )
        print(f"  ✓ 리포트 생성 완료: {len(report_content)}자")
        
        # 5. 데이터 검증
        print("\n[5단계] 데이터 검증 중...")
        validation_result = data_validator.validate_crawler_vs_report(
            product_data=product_data,
            analysis_result=analysis_result,
            checklist_result=checklist_result
        )
        validation_score = validation_result.get("validation_score", 0)
        is_valid = validation_result.get("is_valid", False)
        mismatches = validation_result.get("mismatches", [])
        missing_items = validation_result.get("missing_items", [])
        
        print(f"  ✓ 검증 완료:")
        print(f"    - 검증 점수: {validation_score}%")
        print(f"    - 일치 여부: {'일치' if is_valid else '불일치'}")
        print(f"    - 불일치 항목: {len(mismatches)}개")
        print(f"    - 누락 항목: {len(missing_items)}개")
        
        if mismatches:
            print("\n  불일치 항목:")
            for mismatch in mismatches:
                print(f"    - {mismatch['field']}: 크롤러={mismatch['crawler_value']}, 리포트={mismatch['report_value']}")
        
        if missing_items:
            print("\n  누락 항목:")
            for missing in missing_items:
                print(f"    - {missing['field']}: 체크리스트 항목={missing['checklist_item_id']}")
        
        # 6. 우선 크롤링 필드 확인
        print("\n[6단계] 우선 크롤링 필드 확인 중...")
        priority_fields = error_reporting_service.get_priority_fields_for_crawling()
        print(f"  ✓ 우선 크롤링 필드: {priority_fields}")
        
        # 7. 결과 저장
        result = {
            "url": test_url,
            "product_data": product_data,
            "analysis_result": analysis_result,
            "checklist_result": checklist_result,
            "validation_result": validation_result,
            "priority_fields": priority_fields
        }
        
        with open("test_data_pipeline_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print("\n" + "=" * 80)
        print("테스트 완료!")
        print("=" * 80)
        print("\n결과 파일: test_data_pipeline_result.json")
        
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
