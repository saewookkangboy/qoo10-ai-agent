#!/usr/bin/env python3
"""최종 결과 확인 스크립트"""
import requests
import json

analysis_id = "90586a1b-f838-4de9-8fe7-8f2eb0786a4f"

try:
    r = requests.get(f'http://localhost:8080/api/v1/analyze/{analysis_id}', timeout=15)
    result = r.json()
    
    print("=" * 70)
    print("최종 분석 결과 확인")
    print("=" * 70)
    print(f"Status: {result.get('status')}")
    
    shop_analysis = result.get('result', {}).get('shop_analysis', {})
    shop_data = result.get('result', {}).get('shop_data', {})
    checklist = result.get('result', {}).get('checklist', {})
    
    print(f"\n📊 분석 결과:")
    print(f"  - Overall Score: {shop_analysis.get('overall_score', 'N/A')}")
    print(f"  - Checklist Score: {shop_analysis.get('checklist_score', 'N/A')}")
    print(f"  - Checklist Contribution: {shop_analysis.get('checklist_contribution', 'N/A')}")
    
    print(f"\n🏪 Shop 정보:")
    print(f"  - Shop Name: {shop_data.get('shop_name', 'N/A')}")
    print(f"  - Shop Level: {shop_data.get('shop_level', 'N/A')}")
    print(f"  - Product Count: {shop_data.get('product_count', 'N/A')}")
    print(f"  - Follower Count: {shop_data.get('follower_count', 'N/A')}")
    
    page_structure = shop_data.get('page_structure', {})
    print(f"\n📋 페이지 구조:")
    print(f"  - Page Structure: {'✅ 있음' if page_structure else '❌ 없음'}")
    if page_structure:
        print(f"  - 총 div 클래스 수: {len(page_structure.get('all_div_classes', []))}")
        print(f"  - 주요 요소 카테고리: {len(page_structure.get('key_elements', {}))}")
        shop_specific = page_structure.get('shop_specific_elements', {})
        if shop_specific:
            print(f"  - POWER 레벨: {shop_specific.get('power_level', 'N/A')}")
            print(f"  - 팔로워 수: {shop_specific.get('follower_count', 'N/A')}")
            print(f"  - 상품 수: {shop_specific.get('product_count', 'N/A')}")
    
    if checklist:
        print(f"\n✅ 체크리스트:")
        print(f"  - 완성도: {checklist.get('overall_completion', 'N/A')}%")
        print(f"  - 통과 항목: {checklist.get('passed_items', 'N/A')}")
        print(f"  - 실패 항목: {checklist.get('failed_items', 'N/A')}")
    
    print("\n" + "=" * 70)
    
except Exception as e:
    print(f"오류: {e}")
    import traceback
    traceback.print_exc()
