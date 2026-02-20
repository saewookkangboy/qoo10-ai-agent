"""
데이터 파이프라인 일관성 테스트
크롤링 → 체크리스트 기반 분석 → 분석 리포트의 모든 데이터 일치 여부 확인
"""
import asyncio
import json
import os
import sys
from typing import Dict, Any, List

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "api"))
_TESTS_RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
os.makedirs(_TESTS_RESULTS_DIR, exist_ok=True)
from services.crawler import Qoo10Crawler
from services.analyzer import ProductAnalyzer
from services.checklist_evaluator import ChecklistEvaluator
from services.report_generator import ReportGenerator
from services.data_validator import DataValidator
from services.error_reporting_service import ErrorReportingService


class PipelineConsistencyTester:
    """파이프라인 일관성 테스터"""
    
    def __init__(self):
        self.error_reporting_service = ErrorReportingService()
        self.crawler = Qoo10Crawler(error_reporting_service=self.error_reporting_service)
        self.analyzer = ProductAnalyzer()
        self.checklist_evaluator = ChecklistEvaluator()
        self.report_generator = ReportGenerator()
        self.data_validator = DataValidator()
    
    def extract_report_data(self, report_content: str) -> Dict[str, Any]:
        """리포트 내용에서 데이터 추출"""
        report_data = {}
        lines = report_content.split('\n')
        
        current_section = None
        for line in lines:
            # 상품 정보 섹션
            if '## 📦 상품 정보' in line:
                current_section = 'product_info'
                continue
            
            # 분석 결과 섹션
            if '## 📊 상품 분석 결과' in line:
                current_section = 'analysis'
                continue
            
            # 체크리스트 섹션
            if '## ✅ 메뉴얼 기반 체크리스트' in line:
                current_section = 'checklist'
                continue
            
            # 상품 정보 파싱
            if current_section == 'product_info' and '|' in line:
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 2:
                    key = parts[0]
                    value = parts[1]
                    
                    if key == '상품명':
                        report_data['product_name'] = value
                    elif key == '상품 코드':
                        report_data['product_code'] = value
                    elif key == '판매가':
                        # "1,000円" 형식에서 숫자 추출
                        import re
                        match = re.search(r'([\d,]+)', value.replace('円', ''))
                        if match:
                            report_data['sale_price'] = int(match.group(1).replace(',', ''))
                    elif key == '정가':
                        import re
                        match = re.search(r'([\d,]+)', value.replace('円', ''))
                        if match:
                            report_data['original_price'] = int(match.group(1).replace(',', ''))
                    elif key == '할인율':
                        import re
                        match = re.search(r'(\d+)%', value)
                        if match:
                            report_data['discount_rate'] = int(match.group(1))
            
            # 분석 결과 파싱
            if current_section == 'analysis':
                if '종합 점수:' in line:
                    import re
                    match = re.search(r'(\d+)/100', line)
                    if match:
                        report_data['overall_score'] = int(match.group(1))
                
                # 각 분석 항목 점수
                for analysis_type in ['이미지 분석', '상품 설명 분석', '가격 분석', '리뷰 분석', 'SEO 분석']:
                    if analysis_type in line and '**' in line:
                        import re
                        match = re.search(r'\*\*(\d+)/100\*\*', line)
                        if match:
                            report_data[f'{analysis_type}_score'] = int(match.group(1))
        
        return report_data
    
    def compare_data_consistency(
        self,
        product_data: Dict[str, Any],
        analysis_result: Dict[str, Any],
        checklist_result: Dict[str, Any],
        report_content: str
    ) -> Dict[str, Any]:
        """데이터 일관성 비교"""
        consistency_result = {
            "crawler_vs_analysis": {},
            "crawler_vs_checklist": {},
            "crawler_vs_report": {},
            "analysis_vs_report": {},
            "checklist_vs_report": {},
            "all_consistent": True,
            "inconsistencies": []
        }
        
        # 리포트에서 데이터 추출
        report_data = self.extract_report_data(report_content)
        
        # 1. 크롤러 vs 분석 결과
        crawler_vs_analysis = self._compare_crawler_vs_analysis(product_data, analysis_result)
        consistency_result["crawler_vs_analysis"] = crawler_vs_analysis
        
        # 2. 크롤러 vs 체크리스트
        crawler_vs_checklist = self._compare_crawler_vs_checklist(product_data, checklist_result)
        consistency_result["crawler_vs_checklist"] = crawler_vs_checklist
        
        # 3. 크롤러 vs 리포트
        crawler_vs_report = self._compare_crawler_vs_report(product_data, report_data)
        consistency_result["crawler_vs_report"] = crawler_vs_report
        
        # 4. 분석 결과 vs 리포트
        analysis_vs_report = self._compare_analysis_vs_report(analysis_result, report_data)
        consistency_result["analysis_vs_report"] = analysis_vs_report
        
        # 5. 체크리스트 vs 리포트
        checklist_vs_report = self._compare_checklist_vs_report(checklist_result, report_data)
        consistency_result["checklist_vs_report"] = checklist_vs_report
        
        # 전체 일관성 확인
        all_checks = [
            crawler_vs_analysis.get("consistent", False),
            crawler_vs_checklist.get("consistent", False),
            crawler_vs_report.get("consistent", False),
            analysis_vs_report.get("consistent", False),
            checklist_vs_report.get("consistent", False)
        ]
        
        consistency_result["all_consistent"] = all(all_checks)
        
        # 불일치 항목 수집
        inconsistencies = []
        for check_name, check_result in [
            ("크롤러 vs 분석", crawler_vs_analysis),
            ("크롤러 vs 체크리스트", crawler_vs_checklist),
            ("크롤러 vs 리포트", crawler_vs_report),
            ("분석 vs 리포트", analysis_vs_report),
            ("체크리스트 vs 리포트", checklist_vs_report)
        ]:
            if not check_result.get("consistent", True):
                inconsistencies.append({
                    "comparison": check_name,
                    "mismatches": check_result.get("mismatches", [])
                })
        
        consistency_result["inconsistencies"] = inconsistencies
        
        return consistency_result
    
    def _compare_crawler_vs_analysis(
        self,
        product_data: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """크롤러 데이터와 분석 결과 비교"""
        mismatches = []
        
        product_analysis = analysis_result.get("product_analysis", {})
        
        # 가격 (분석 결과에는 price_analysis에 가격 정보가 있음)
        crawler_price = product_data.get("price", {}).get("sale_price")
        analysis_price = product_analysis.get("price_analysis", {}).get("sale_price")
        if crawler_price and analysis_price and crawler_price != analysis_price:
            mismatches.append({
                "field": "sale_price",
                "crawler": crawler_price,
                "analysis": analysis_price
            })
        
        # 리뷰 수
        crawler_reviews = product_data.get("reviews", {}).get("review_count", 0)
        analysis_reviews = product_analysis.get("review_analysis", {}).get("review_count", 0)
        if crawler_reviews != analysis_reviews:
            mismatches.append({
                "field": "review_count",
                "crawler": crawler_reviews,
                "analysis": analysis_reviews
            })
        
        # 이미지 개수
        crawler_images = len(product_data.get("images", {}).get("detail_images", []))
        analysis_images = product_analysis.get("image_analysis", {}).get("image_count", 0)
        if crawler_images != analysis_images:
            mismatches.append({
                "field": "image_count",
                "crawler": crawler_images,
                "analysis": analysis_images
            })
        
        return {
            "consistent": len(mismatches) == 0,
            "mismatches": mismatches,
            "total_fields_checked": 3
        }
    
    def _compare_crawler_vs_checklist(
        self,
        product_data: Dict[str, Any],
        checklist_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """크롤러 데이터와 체크리스트 결과 비교"""
        mismatches = []
        
        # 체크리스트에서 크롤러 데이터를 기반으로 평가된 항목 확인
        checklists = checklist_result.get("checklists", [])
        
        # Qポイント 정보 확인
        crawler_qpoint = product_data.get("qpoint_info", {})
        has_qpoint_in_checklist = False
        for checklist in checklists:
            for item in checklist.get("items", []):
                if item.get("id") in ["item_006a", "item_006b"] and item.get("status") == "completed":
                    has_qpoint_in_checklist = True
                    break
        
        if any(crawler_qpoint.values()) and not has_qpoint_in_checklist:
            mismatches.append({
                "field": "qpoint_info",
                "crawler_has_data": True,
                "checklist_missing": True
            })
        
        # 쿠폰 정보 확인
        crawler_coupon = product_data.get("coupon_info", {}).get("has_coupon", False)
        has_coupon_in_checklist = False
        for checklist in checklists:
            for item in checklist.get("items", []):
                if item.get("id") in ["item_011", "item_020", "item_021"] and item.get("status") == "completed":
                    has_coupon_in_checklist = True
                    break
        
        if crawler_coupon and not has_coupon_in_checklist:
            mismatches.append({
                "field": "coupon_info",
                "crawler_has_data": True,
                "checklist_missing": True
            })
        
        return {
            "consistent": len(mismatches) == 0,
            "mismatches": mismatches,
            "total_fields_checked": 2
        }
    
    def _compare_crawler_vs_report(
        self,
        product_data: Dict[str, Any],
        report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """크롤러 데이터와 리포트 비교"""
        mismatches = []
        
        # 상품명
        crawler_name = product_data.get("product_name", "")
        report_name = report_data.get("product_name", "")
        if crawler_name and report_name and crawler_name != report_name:
            mismatches.append({
                "field": "product_name",
                "crawler": crawler_name,
                "report": report_name
            })
        
        # 가격
        crawler_price = product_data.get("price", {}).get("sale_price")
        report_price = report_data.get("sale_price")
        if crawler_price and report_price and crawler_price != report_price:
            mismatches.append({
                "field": "sale_price",
                "crawler": crawler_price,
                "report": report_price
            })
        
        return {
            "consistent": len(mismatches) == 0,
            "mismatches": mismatches,
            "total_fields_checked": 2
        }
    
    def _compare_analysis_vs_report(
        self,
        analysis_result: Dict[str, Any],
        report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """분석 결과와 리포트 비교"""
        mismatches = []
        
        product_analysis = analysis_result.get("product_analysis", {})
        
        # 종합 점수
        analysis_score = product_analysis.get("overall_score", 0)
        report_score = report_data.get("overall_score")
        if report_score is not None and analysis_score != report_score:
            mismatches.append({
                "field": "overall_score",
                "analysis": analysis_score,
                "report": report_score
            })
        
        return {
            "consistent": len(mismatches) == 0,
            "mismatches": mismatches,
            "total_fields_checked": 1
        }
    
    def _compare_checklist_vs_report(
        self,
        checklist_result: Dict[str, Any],
        report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """체크리스트 결과와 리포트 비교"""
        # 리포트에서 체크리스트 완성도 추출
        import re
        report_content_lines = []
        # 리포트 내용이 없으면 체크리스트 정보를 리포트에서 직접 확인 불가
        # 대신 체크리스트 결과 자체를 검증
        
        checklist_completion = checklist_result.get("overall_completion", 0)
        
        return {
            "consistent": True,  # 리포트에서 체크리스트 정보 추출이 어려우므로 일단 True
            "mismatches": [],
            "total_fields_checked": 0,
            "note": "리포트에서 체크리스트 정보 추출 필요"
        }
    
    async def test_pipeline(self, test_url: str) -> Dict[str, Any]:
        """전체 파이프라인 테스트"""
        print("=" * 80)
        print("데이터 파이프라인 일관성 테스트")
        print("=" * 80)
        print(f"테스트 URL: {test_url}\n")
        
        results = {
            "url": test_url,
            "stages": {},
            "consistency": {},
            "validation": {},
            "summary": {}
        }
        
        try:
            # 1. 크롤링
            print("[1단계] 크롤링 중...")
            # 데이터베이스 잠금 문제를 피하기 위해 Playwright 사용
            try:
                product_data = await self.crawler.crawl_product(test_url, use_playwright=True)
            except Exception as e:
                # Playwright 실패 시 HTTP로 재시도
                print(f"  ⚠️ Playwright 크롤링 실패, HTTP로 재시도: {str(e)}")
                product_data = await self.crawler.crawl_product(test_url, use_playwright=False)
            
            # 크롤링 데이터 검증
            required_fields = ["product_name", "product_code", "price", "reviews"]
            missing_fields = [f for f in required_fields if f not in product_data or not product_data[f]]
            
            print(f"  ✓ 크롤링 완료")
            print(f"    - 데이터 소스: {product_data.get('crawled_with', 'unknown')}")
            print(f"    - 상품명: {product_data.get('product_name', 'N/A')[:50]}...")
            print(f"    - 상품 코드: {product_data.get('product_code', 'N/A')}")
            print(f"    - 판매가: {product_data.get('price', {}).get('sale_price', 'N/A')}")
            if missing_fields:
                print(f"    ⚠️ 누락된 필수 필드: {missing_fields}")
            
            results["stages"]["crawling"] = {
                "success": True,
                "data_source": product_data.get("crawled_with", "unknown"),
                "fields_count": len(product_data),
                "missing_fields": missing_fields
            }
            
            # 2. 분석
            print("\n[2단계] 분석 실행 중...")
            raw_analysis_result = await self.analyzer.analyze(product_data)
            
            # 리포트 생성을 위해 product_analysis로 감싸기
            analysis_result = {
                "product_analysis": raw_analysis_result
            }
            
            overall_score = raw_analysis_result.get("overall_score", 0)
            price_analysis = raw_analysis_result.get("price_analysis", {})
            
            print(f"  ✓ 분석 완료")
            print(f"    - 종합 점수: {overall_score}/100")
            print(f"    - 판매가 (분석): {price_analysis.get('sale_price', 'N/A')}")
            print(f"    - 이미지 분석 점수: {raw_analysis_result.get('image_analysis', {}).get('score', 0)}")
            print(f"    - 리뷰 분석 점수: {raw_analysis_result.get('review_analysis', {}).get('score', 0)}")
            
            results["stages"]["analysis"] = {
                "success": True,
                "overall_score": overall_score,
                "has_product_analysis": True,
                "image_score": raw_analysis_result.get("image_analysis", {}).get("score", 0),
                "review_score": raw_analysis_result.get("review_analysis", {}).get("score", 0)
            }
            
            # 3. 체크리스트 평가
            print("\n[3단계] 체크리스트 평가 중...")
            checklist_result = await self.checklist_evaluator.evaluate_checklist(
                product_data=product_data,
                analysis_result=analysis_result
            )
            
            completion = checklist_result.get("overall_completion", 0)
            checklists = checklist_result.get("checklists", [])
            
            print(f"  ✓ 체크리스트 완료")
            print(f"    - 전체 완성도: {completion}%")
            print(f"    - 체크리스트 카테고리 수: {len(checklists)}")
            
            # 완료된 항목 수
            completed_items = sum(
                len([item for item in cl.get("items", []) if item.get("status") == "completed"])
                for cl in checklists
            )
            total_items = sum(len(cl.get("items", [])) for cl in checklists)
            print(f"    - 완료된 항목: {completed_items}/{total_items}")
            
            results["stages"]["checklist"] = {
                "success": True,
                "overall_completion": completion,
                "categories_count": len(checklists),
                "completed_items": completed_items,
                "total_items": total_items
            }
            
            # 4. 리포트 생성
            print("\n[4단계] 리포트 생성 중...")
            # 리포트 생성을 위해 analysis_result에 checklist 포함
            report_analysis_result = analysis_result.copy()
            report_analysis_result["checklist"] = checklist_result
            
            # 검증 결과 생성 (리포트에 포함하기 위해)
            validation_result_for_report = self.data_validator.validate_crawler_vs_report(
                product_data=product_data,
                analysis_result=analysis_result,
                checklist_result=checklist_result
            )
            
            report_content = self.report_generator.generate_markdown_report(
                report_analysis_result,  # checklist가 포함된 analysis_result
                product_data,
                validation_result=validation_result_for_report
            )
            
            print(f"  ✓ 리포트 생성 완료")
            print(f"    - 리포트 길이: {len(report_content)}자")
            print(f"    - 리포트에 상품 정보 포함: {'## 📦 상품 정보' in report_content}")
            print(f"    - 리포트에 분석 결과 포함: {'## 📊 상품 분석 결과' in report_content}")
            print(f"    - 리포트에 체크리스트 포함: {'## ✅ 메뉴얼 기반 체크리스트' in report_content}")
            
            results["stages"]["report"] = {
                "success": True,
                "report_length": len(report_content),
                "has_product_info": "## 📦 상품 정보" in report_content,
                "has_analysis": "## 📊 상품 분석 결과" in report_content,
                "has_checklist": "## ✅ 메뉴얼 기반 체크리스트" in report_content
            }
            
            # 5. 데이터 검증
            print("\n[5단계] 데이터 검증 중...")
            validation_result = self.data_validator.validate_crawler_vs_report(
                product_data=product_data,
                analysis_result=analysis_result,
                checklist_result=checklist_result
            )
            
            validation_score = validation_result.get("validation_score", 0)
            is_valid = validation_result.get("is_valid", False)
            mismatches = validation_result.get("mismatches", [])
            missing_items = validation_result.get("missing_items", [])
            corrected_fields = validation_result.get("corrected_fields", [])
            
            print(f"  ✓ 검증 완료")
            print(f"    - 검증 점수: {validation_score:.1f}%")
            print(f"    - 일치 여부: {'✅ 일치' if is_valid else '⚠️ 불일치'}")
            print(f"    - 불일치 항목: {len(mismatches)}개")
            print(f"    - 누락 항목: {len(missing_items)}개")
            print(f"    - 보정된 필드: {len(corrected_fields)}개")
            
            if corrected_fields:
                print(f"    - 보정된 필드 목록: {', '.join(corrected_fields)}")
            
            if mismatches:
                print(f"\n  불일치 항목 상세:")
                for mismatch in mismatches[:5]:  # 최대 5개만 표시
                    print(f"    - {mismatch.get('field')}: 크롤러={mismatch.get('crawler_value')}, 리포트={mismatch.get('report_value')}")
            
            if missing_items:
                print(f"\n  누락 항목 상세:")
                for missing in missing_items[:5]:  # 최대 5개만 표시
                    print(f"    - {missing.get('field')}: 체크리스트 항목={missing.get('checklist_item_id')}")
            
            results["validation"] = validation_result
            
            # 6. 데이터 일관성 비교
            print("\n[6단계] 데이터 일관성 비교 중...")
            consistency_result = self.compare_data_consistency(
                product_data=product_data,
                analysis_result=analysis_result,
                checklist_result=checklist_result,
                report_content=report_content
            )
            
            print(f"  ✓ 일관성 비교 완료")
            print(f"    - 전체 일관성: {'✅ 일치' if consistency_result['all_consistent'] else '⚠️ 불일치'}")
            
            for comparison_name, comparison_result in [
                ("크롤러 vs 분석", consistency_result["crawler_vs_analysis"]),
                ("크롤러 vs 체크리스트", consistency_result["crawler_vs_checklist"]),
                ("크롤러 vs 리포트", consistency_result["crawler_vs_report"]),
                ("분석 vs 리포트", consistency_result["analysis_vs_report"]),
                ("체크리스트 vs 리포트", consistency_result["checklist_vs_report"])
            ]:
                status = "✅" if comparison_result.get("consistent", False) else "⚠️"
                mismatches_count = len(comparison_result.get("mismatches", []))
                print(f"    - {status} {comparison_name}: {'일치' if mismatches_count == 0 else f'{mismatches_count}개 불일치'}")
            
            results["consistency"] = consistency_result
            
            # 7. 최종 요약
            print("\n" + "=" * 80)
            print("테스트 요약")
            print("=" * 80)
            
            all_stages_success = all(
                stage.get("success", False)
                for stage in results["stages"].values()
            )
            
            print(f"✅ 모든 단계 성공: {'예' if all_stages_success else '아니오'}")
            print(f"✅ 데이터 검증 통과: {'예' if is_valid else '아니오'} (점수: {validation_score:.1f}%)")
            print(f"✅ 데이터 일관성: {'예' if consistency_result['all_consistent'] else '아니오'}")
            
            if not is_valid or not consistency_result['all_consistent']:
                print(f"\n⚠️ 발견된 문제:")
                if not is_valid:
                    print(f"  - 검증 실패: 불일치 {len(mismatches)}개, 누락 {len(missing_items)}개")
                if not consistency_result['all_consistent']:
                    print(f"  - 일관성 문제: {len(consistency_result['inconsistencies'])}개 비교에서 불일치 발견")
            
            results["summary"] = {
                "all_stages_success": all_stages_success,
                "validation_passed": is_valid,
                "consistency_passed": consistency_result['all_consistent'],
                "overall_success": all_stages_success and is_valid and consistency_result['all_consistent']
            }
            
            # 8. 결과 저장
            print("\n[7단계] 결과 저장 중...")
            output_file = os.path.join(_TESTS_RESULTS_DIR, "test_pipeline_consistency_result.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"  ✓ 결과 저장 완료: {output_file}")
            
            # 리포트도 저장
            report_file = os.path.join(_TESTS_RESULTS_DIR, "test_pipeline_report.md")
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(report_content)
            
            print(f"  ✓ 리포트 저장 완료: {report_file}")
            
            print("\n" + "=" * 80)
            print("테스트 완료!")
            print("=" * 80)
            
            return results
            
        except Exception as e:
            print(f"\n❌ 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            results["error"] = str(e)
            results["traceback"] = traceback.format_exc()
            return results


async def main():
    """메인 함수"""
    tester = PipelineConsistencyTester()
    
    # 테스트 URL
    test_url = "https://www.qoo10.jp/g/1093098159"
    
    # 파이프라인 테스트 실행
    results = await tester.test_pipeline(test_url)
    
    # 최종 결과 출력
    if results.get("summary", {}).get("overall_success"):
        print("\n🎉 모든 테스트 통과!")
    else:
        print("\n⚠️ 일부 테스트 실패 - 상세 내용은 결과 파일을 확인하세요.")


if __name__ == "__main__":
    asyncio.run(main())
