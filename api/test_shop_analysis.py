#!/usr/bin/env python3
"""Shop 페이지 분석 테스트 스크립트"""
import requests
import json
import time
import sys

def test_shop_analysis():
    url = "https://www.qoo10.jp/shop/whippedofficial"
    
    print("=" * 60)
    print("Shop 페이지 분석 테스트")
    print("=" * 60)
    print(f"URL: {url}\n")
    
    # 1. 분석 시작
    print("1. 분석 시작...")
    try:
        response = requests.post(
            "http://localhost:8080/api/v1/analyze",
            json={"url": url},
            timeout=15
        )
        response.raise_for_status()
        result = response.json()
        analysis_id = result.get("analysis_id")
        print(f"   ✅ 분석 시작 성공")
        print(f"   Analysis ID: {analysis_id}")
        print(f"   Status: {result.get('status')}")
        print(f"   URL Type: {result.get('url_type')}\n")
    except Exception as e:
        print(f"   ❌ 분석 시작 실패: {e}")
        return
    
    # 2. 분석 결과 대기 및 조회
    print("2. 분석 결과 대기 중...")
    max_attempts = 60
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(
                f"http://localhost:8080/api/v1/analyze/{analysis_id}",
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            status = result.get("status")
            
            progress = result.get("progress", {})
            stage = progress.get("stage", "unknown")
            percentage = progress.get("percentage", 0)
            
            print(f"   시도 {attempt}/{max_attempts}: Status={status}, Stage={stage}, Progress={percentage}%")
            
            if status == "completed":
                print(f"\n   ✅ 분석 완료!\n")
                break
            elif status == "failed":
                error = result.get("error", "Unknown error")
                print(f"\n   ❌ 분석 실패: {error}\n")
                return
            
            time.sleep(2)
        except Exception as e:
            print(f"   ⚠️ 조회 중 오류: {e}")
            time.sleep(2)
    
    # 3. 최종 결과 확인
    print("3. 최종 결과 확인...")
    try:
        response = requests.get(
            f"http://localhost:8080/api/v1/analyze/{analysis_id}",
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get("status") != "completed":
            print(f"   ⚠️ 분석이 아직 완료되지 않았습니다. Status: {result.get('status')}")
            return
        
        final_result = result.get("result", {})
        shop_analysis = final_result.get("shop_analysis", {})
        shop_data = final_result.get("shop_data", {})
        checklist = final_result.get("checklist", {})
        
        print(f"   ✅ 분석 결과:")
        print(f"   - Overall Score: {shop_analysis.get('overall_score', 'N/A')}")
        print(f"   - Shop Name: {shop_data.get('shop_name', 'N/A')}")
        print(f"   - Shop Level: {shop_data.get('shop_level', 'N/A')}")
        print(f"   - Product Count: {shop_data.get('product_count', 'N/A')}")
        print(f"   - Follower Count: {shop_data.get('follower_count', 'N/A')}")
        print(f"   - Page Structure: {'✅ 있음' if shop_data.get('page_structure') else '❌ 없음'}")
        print(f"   - Checklist Completion: {checklist.get('overall_completion', 'N/A')}%")
        
        # 페이지 구조 상세 정보
        page_structure = shop_data.get("page_structure", {})
        if page_structure:
            print(f"\n   📊 페이지 구조 정보:")
            print(f"   - 총 div 클래스 수: {len(page_structure.get('all_div_classes', []))}")
            print(f"   - 주요 요소 카테고리: {len(page_structure.get('key_elements', {}))}")
            print(f"   - 의미 구조 요소: {len(page_structure.get('semantic_structure', {}))}")
            
            shop_specific = page_structure.get("shop_specific_elements", {})
            if shop_specific:
                print(f"   - Shop 특화 요소:")
                print(f"     * POWER 레벨: {shop_specific.get('power_level', 'N/A')}")
                print(f"     * 팔로워 수: {shop_specific.get('follower_count', 'N/A')}")
                print(f"     * 상품 수: {shop_specific.get('product_count', 'N/A')}")
                print(f"     * 쿠폰 개수: {shop_specific.get('coupon_count', 'N/A')}")
                print(f"     * 카테고리 개수: {shop_specific.get('category_count', 'N/A')}")
        
        # 체크리스트 상세 정보
        if checklist:
            print(f"\n   ✅ 체크리스트 결과:")
            print(f"   - 전체 완성도: {checklist.get('overall_completion', 0)}%")
            print(f"   - 통과 항목: {checklist.get('passed_items', 0)}")
            print(f"   - 실패 항목: {checklist.get('failed_items', 0)}")
            
            items = checklist.get("items", [])
            if items:
                print(f"   - 상세 항목:")
                for item in items[:5]:  # 상위 5개만 표시
                    status = "✅" if item.get("passed") else "❌"
                    print(f"     {status} {item.get('title', 'N/A')}: {item.get('recommendation', 'N/A')}")
        
        # 체크리스트 점수 반영 확인
        checklist_score = shop_analysis.get("checklist_score")
        checklist_contribution = shop_analysis.get("checklist_contribution")
        if checklist_score is not None:
            print(f"\n   📈 체크리스트 점수 반영:")
            print(f"   - Checklist Score: {checklist_score}%")
            print(f"   - Checklist Contribution: {checklist_contribution}")
            print(f"   - Final Overall Score: {shop_analysis.get('overall_score', 'N/A')}")
        
        print("\n" + "=" * 60)
        print("✅ 테스트 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"   ❌ 결과 조회 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_shop_analysis()
