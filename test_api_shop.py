#!/usr/bin/env python3
"""
API를 통한 Shop 분석 테스트
"""
import requests
import json
import time

API_URL = "http://localhost:8080"
SHOP_URL = "https://www.qoo10.jp/shop/whippedofficial"

def test_shop_analysis():
    """Shop 분석 API 테스트"""
    print(f"🔍 Shop 분석 테스트 시작\n")
    print(f"URL: {SHOP_URL}\n")
    
    # 1. 분석 시작
    print("1. 분석 시작 요청...")
    try:
        response = requests.post(
            f"{API_URL}/api/v1/analyze",
            json={"url": SHOP_URL},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        analysis_id = data.get("analysis_id")
        print(f"   ✅ 분석 ID: {analysis_id}")
        print(f"   ✅ 상태: {data.get('status')}")
        print(f"   ✅ URL 타입: {data.get('url_type')}")
    except requests.exceptions.ConnectionError:
        print("   ❌ API 서버에 연결할 수 없습니다.")
        print("   💡 API 서버를 먼저 실행하세요: cd api && uvicorn main:app --reload")
        return
    except Exception as e:
        print(f"   ❌ 오류: {str(e)}")
        return
    
    # 2. 분석 결과 대기
    print("\n2. 분석 결과 대기 중...")
    max_attempts = 30
    for i in range(max_attempts):
        try:
            response = requests.get(
                f"{API_URL}/api/v1/analyze/{analysis_id}",
                timeout=5
            )
            response.raise_for_status()
            result = response.json()
            
            status = result.get("status")
            print(f"   시도 {i+1}/{max_attempts}: {status}")
            
            if status == "completed":
                print("\n   ✅ 분석 완료!\n")
                print_result(result)
                return
            elif status == "failed":
                print(f"\n   ❌ 분석 실패: {result.get('error', 'Unknown error')}")
                return
            
            time.sleep(2)
        except Exception as e:
            print(f"   ⚠️  오류: {str(e)}")
            time.sleep(2)
    
    print("\n   ⏱️  타임아웃: 분석이 완료되지 않았습니다.")


def print_result(result):
    """분석 결과 출력"""
    analysis_data = result.get("result", {})
    
    if "shop_analysis" in analysis_data:
        shop_analysis = analysis_data["shop_analysis"]
        recommendations = analysis_data.get("recommendations", [])
        shop_data = analysis_data.get("shop_data", {})
        
        print("=" * 60)
        print("📊 Shop 분석 결과")
        print("=" * 60)
        
        print(f"\n🏪 Shop 정보:")
        print(f"  - Shop 이름: {shop_data.get('shop_name', 'N/A')}")
        print(f"  - Shop ID: {shop_data.get('shop_id', 'N/A')}")
        print(f"  - Shop 레벨: {shop_data.get('shop_level', 'N/A')}")
        print(f"  - 팔로워 수: {shop_data.get('follower_count', 0):,}")
        print(f"  - 상품 수: {shop_data.get('product_count', 0)}")
        
        print(f"\n📈 종합 점수: {shop_analysis.get('overall_score', 0)}/100")
        
        shop_info = shop_analysis.get("shop_info", {})
        print(f"\n  Shop 정보 점수: {shop_info.get('score', 0)}/100")
        
        product_analysis = shop_analysis.get("product_analysis", {})
        print(f"  상품 분석 점수: {product_analysis.get('score', 0)}/100")
        print(f"    - 총 상품: {product_analysis.get('total_products', 0)}개")
        print(f"    - 평균 평점: {product_analysis.get('average_rating', 0):.2f}")
        print(f"    - 총 리뷰: {product_analysis.get('total_reviews', 0):,}개")
        
        level_analysis = shop_analysis.get("level_analysis", {})
        print(f"\n  Shop 레벨 분석:")
        print(f"    - 현재 레벨: {level_analysis.get('current_level', 'N/A')}")
        print(f"    - 정산 리드타임: {level_analysis.get('settlement_leadtime', 15)}일")
        print(f"    - 목표 레벨: {level_analysis.get('target_level', 'N/A')}")
        
        if recommendations:
            print(f"\n💡 매출 강화 아이디어 ({len(recommendations)}개):")
            for i, rec in enumerate(recommendations, 1):
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(rec.get("priority"), "⚪")
                print(f"\n  {i}. {priority_emoji} [{rec.get('priority', 'N/A').upper()}] {rec.get('title', 'N/A')}")
                print(f"     {rec.get('description', 'N/A')}")
                if rec.get('action_items'):
                    print(f"     실행 방법:")
                    for item in rec['action_items']:
                        print(f"       ✓ {item}")
        
        print("\n" + "=" * 60)
    else:
        print("분석 결과 형식이 예상과 다릅니다.")
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    test_shop_analysis()
