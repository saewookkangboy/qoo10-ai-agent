"""
데이터 파이프라인 전체 테스트 스크립트
- 크롤링 → 분석 → 체크리스트 → 검증/동기화 → 리포트 생성 → 오류 신고
"""
import asyncio
import json
import httpx
from datetime import datetime

TEST_URL = "https://www.qoo10.jp/g/1093098159"
API_BASE = "http://localhost:8000"

async def test_complete_pipeline():
    """전체 파이프라인 테스트"""
    print("=" * 80)
    print("데이터 파이프라인 전체 테스트")
    print("=" * 80)
    print(f"테스트 URL: {TEST_URL}\n")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # 1. 분석 시작
        print("[1단계] 분석 시작...")
        try:
            response = await client.post(
                f"{API_BASE}/api/v1/analyze",
                json={"url": TEST_URL}
            )
            response.raise_for_status()
            result = response.json()
            analysis_id = result.get("analysis_id")
            print(f"  ✓ 분석 ID: {analysis_id}")
        except Exception as e:
            print(f"  ✗ 분석 시작 실패: {e}")
            return
        
        # 2. 분석 결과 대기
        print("\n[2단계] 분석 결과 대기 중...")
        max_wait = 300  # 5분
        wait_time = 0
        while wait_time < max_wait:
            try:
                response = await client.get(f"{API_BASE}/api/v1/analyze/{analysis_id}")
                response.raise_for_status()
                result = response.json()
                status = result.get("status")
                progress = result.get("progress", {})
                
                if status == "completed":
                    print(f"  ✓ 분석 완료!")
                    print(f"    - 진행률: {progress.get('percentage', 0)}%")
                    print(f"    - 단계: {progress.get('stage', 'N/A')}")
                    break
                elif status == "failed":
                    print(f"  ✗ 분석 실패: {result.get('error', 'Unknown error')}")
                    return
                else:
                    percentage = progress.get('percentage', 0)
                    stage = progress.get('stage', 'N/A')
                    print(f"    진행 중... {percentage}% ({stage})")
                
                await asyncio.sleep(5)
                wait_time += 5
            except Exception as e:
                print(f"  ✗ 결과 조회 실패: {e}")
                return
        
        if wait_time >= max_wait:
            print("  ✗ 타임아웃: 분석이 완료되지 않았습니다")
            return
        
        # 3. 분석 결과 확인
        print("\n[3단계] 분석 결과 확인...")
        try:
            response = await client.get(f"{API_BASE}/api/v1/analyze/{analysis_id}")
            response.raise_for_status()
            result = response.json()
            
            if result.get("status") != "completed":
                print(f"  ✗ 분석이 완료되지 않았습니다: {result.get('status')}")
                return
            
            analysis_result = result.get("result", {})
            product_data = analysis_result.get("product_data", {})
            checklist = analysis_result.get("checklist", {})
            validation = analysis_result.get("validation")
            
            print(f"  ✓ 분석 결과 확인 완료")
            print(f"    - 상품명: {product_data.get('product_name', 'N/A')}")
            print(f"    - 판매가: {product_data.get('price', {}).get('sale_price', 'N/A')}")
            print(f"    - 체크리스트 완성도: {checklist.get('overall_completion', 0)}%")
            if validation:
                print(f"    - 검증 점수: {validation.get('validation_score', 0)}%")
                print(f"    - 검증 상태: {'✓ 유효' if validation.get('is_valid') else '✗ 무효'}")
                corrected = validation.get('corrected_fields', [])
                if corrected:
                    print(f"    - 보정된 필드: {', '.join(corrected)}")
        except Exception as e:
            print(f"  ✗ 결과 확인 실패: {e}")
            return
        
        # 4. 오류 신고 테스트
        print("\n[4단계] 오류 신고 기능 테스트...")
        try:
            error_report_data = {
                "analysis_id": analysis_id,
                "field_name": "product_name",
                "issue_type": "mismatch",
                "severity": "medium",
                "user_description": "테스트용 오류 신고",
                "crawler_value": product_data.get('product_name'),
                "report_value": "테스트 리포트 값"
            }
            
            response = await client.post(
                f"{API_BASE}/api/v1/error/report",
                json=error_report_data
            )
            response.raise_for_status()
            report_result = response.json()
            error_report_id = report_result.get("error_report_id")
            print(f"  ✓ 오류 신고 성공: {error_report_id}")
            
            # 오류 신고 조회 테스트
            response = await client.get(
                f"{API_BASE}/api/v1/error/reports",
                params={"field_name": "product_name", "status": "pending", "limit": 10}
            )
            response.raise_for_status()
            reports = response.json()
            print(f"  ✓ 오류 신고 조회 성공: {len(reports.get('reports', []))}개")
            
        except Exception as e:
            print(f"  ✗ 오류 신고 테스트 실패: {e}")
            import traceback
            traceback.print_exc()
        
        # 5. 리포트 생성 테스트
        print("\n[5단계] 리포트 생성 테스트...")
        try:
            response = await client.get(
                f"{API_BASE}/api/v1/analyze/{analysis_id}/download",
                params={"format": "markdown"}
            )
            response.raise_for_status()
            report_content = response.text
            print(f"  ✓ 리포트 생성 성공: {len(report_content)} bytes")
            
            # 리포트에 크롤러 데이터가 포함되어 있는지 확인
            if product_data.get('product_name') and product_data.get('product_name') in report_content:
                print(f"  ✓ 리포트에 크롤러 데이터 반영 확인")
            else:
                print(f"  ⚠ 리포트에 크롤러 데이터 미반영 가능성")
                
        except Exception as e:
            print(f"  ✗ 리포트 생성 실패: {e}")
        print("\n" + "=" * 80)
        print("테스트 완료")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_complete_pipeline())
