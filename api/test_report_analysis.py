"""
실제 리포트 생성 및 체크리스트 완성도 분석
"""
import asyncio
import json
from services.crawler import Qoo10Crawler
from services.analyzer import ProductAnalyzer
from services.checklist_evaluator import ChecklistEvaluator
from services.report_generator import ReportGenerator

async def main():
    test_url = "https://www.qoo10.jp/g/1093098159"
    
    print("=" * 80)
    print("실제 리포트 생성 및 체크리스트 완성도 분석")
    print("=" * 80)
    print(f"테스트 URL: {test_url}\n")
    
    try:
        # 1. 크롤링
        print("[1단계] 크롤링 중...")
        crawler = Qoo10Crawler()
        product_data = await crawler.crawl_product(test_url, use_playwright=True)
        print(f"  ✓ 크롤링 완료: {len(product_data)}개 필드")
        
        # 2. 분석
        print("\n[2단계] 분석 실행 중...")
        analyzer = ProductAnalyzer()
        analysis_result = await analyzer.analyze(product_data)
        print(f"  ✓ 분석 완료: 종합 점수 {analysis_result.get('overall_score', 0)}점")
        
        # 3. 체크리스트 평가
        print("\n[3단계] 체크리스트 평가 중...")
        checklist_evaluator = ChecklistEvaluator()
        checklist_result = await checklist_evaluator.evaluate_checklist(
            product_data=product_data,
            shop_data=None,
            analysis_result=analysis_result,
            page_structure=product_data.get("page_structure")
        )
        
        print(f"  ✓ 체크리스트 평가 완료")
        print(f"    - 전체 완성도: {checklist_result.get('overall_completion', 0)}%")
        print(f"    - 카테고리 수: {len(checklist_result.get('checklists', []))}")
        
        # 체크리스트 상세 분석
        print("\n[체크리스트 상세 분석]")
        for checklist in checklist_result.get("checklists", []):
            category = checklist.get("category", "")
            completion_rate = checklist.get("completion_rate", 0)
            items = checklist.get("items", [])
            completed_count = len([item for item in items if item.get("status") == "completed"])
            total_count = len(items)
            
            print(f"\n  카테고리: {category}")
            print(f"    - 완성도: {completion_rate}%")
            print(f"    - 완료 항목: {completed_count}/{total_count}")
            
            # 완료된 항목
            completed_items = [item for item in items if item.get("status") == "completed"]
            if completed_items:
                print(f"    - 완료된 항목:")
                for item in completed_items[:5]:  # 최대 5개만 표시
                    print(f"      ✓ {item.get('title', 'N/A')}")
                if len(completed_items) > 5:
                    print(f"      ... 외 {len(completed_items) - 5}개")
            
            # 미완료 항목
            pending_items = [item for item in items if item.get("status") == "pending"]
            if pending_items:
                print(f"    - 미완료 항목:")
                for item in pending_items[:5]:  # 최대 5개만 표시
                    auto_checked = item.get("auto_checked", False)
                    auto_status = "(자동 체크 가능)" if auto_checked else "(수동 확인 필요)"
                    print(f"      ⬜ {item.get('title', 'N/A')} {auto_status}")
                if len(pending_items) > 5:
                    print(f"      ... 외 {len(pending_items) - 5}개")
        
        # 4. 리포트 생성
        print("\n[4단계] 리포트 생성 중...")
        report_generator = ReportGenerator()
        
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
        
        # 리포트 저장
        report_file = "test_report_analysis.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(markdown_report)
        
        print(f"  ✓ 리포트 생성 완료: {report_file}")
        
        # 리포트에서 체크리스트 섹션 추출
        print("\n[리포트 체크리스트 섹션 확인]")
        if "메뉴얼 기반 체크리스트" in markdown_report:
            checklist_section_start = markdown_report.find("## ✅ 메뉴얼 기반 체크리스트")
            checklist_section_end = markdown_report.find("##", checklist_section_start + 1)
            if checklist_section_end == -1:
                checklist_section = markdown_report[checklist_section_start:]
            else:
                checklist_section = markdown_report[checklist_section_start:checklist_section_end]
            
            print("\n체크리스트 섹션 내용:")
            print("-" * 80)
            print(checklist_section[:2000])  # 처음 2000자만 표시
            if len(checklist_section) > 2000:
                print(f"\n... (총 {len(checklist_section)}자, 나머지 생략)")
            print("-" * 80)
        else:
            print("  ⚠ 체크리스트 섹션이 리포트에 없습니다!")
        
        # 통계 요약
        print("\n[통계 요약]")
        total_items = sum(len(cl.get("items", [])) for cl in checklist_result.get("checklists", []))
        completed_items = sum(
            len([item for item in cl.get("items", []) if item.get("status") == "completed"])
            for cl in checklist_result.get("checklists", [])
        )
        auto_checkable_items = sum(
            len([item for item in cl.get("items", []) if item.get("auto_checked", False)])
            for cl in checklist_result.get("checklists", [])
        )
        
        print(f"  - 전체 항목 수: {total_items}")
        print(f"  - 완료 항목 수: {completed_items}")
        print(f"  - 미완료 항목 수: {total_items - completed_items}")
        print(f"  - 자동 체크 가능 항목: {auto_checkable_items}")
        print(f"  - 전체 완성도: {checklist_result.get('overall_completion', 0)}%")
        print(f"  - 계산된 완성도: {int((completed_items / total_items) * 100) if total_items > 0 else 0}%")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
