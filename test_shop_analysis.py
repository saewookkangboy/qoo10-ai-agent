#!/usr/bin/env python3
"""
Shop 분석 테스트 스크립트
"""
import asyncio
import sys
import os

# API 디렉토리를 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

from services.crawler import Qoo10Crawler
from services.shop_analyzer import ShopAnalyzer
from services.recommender import SalesEnhancementRecommender


async def test_shop_analysis(url: str):
    """Shop 분석 테스트"""
    print(f"🔍 Shop 분석 시작: {url}\n")
    
    try:
        # 크롤러 초기화
        print("1. 크롤러 초기화...")
        crawler = Qoo10Crawler()
        
        # Shop 데이터 수집
        print("2. Shop 데이터 수집 중...")
        shop_data = await crawler.crawl_shop(url)
        print(f"   ✅ Shop 이름: {shop_data.get('shop_name', 'N/A')}")
        print(f"   ✅ Shop ID: {shop_data.get('shop_id', 'N/A')}")
        print(f"   ✅ Shop 레벨: {shop_data.get('shop_level', 'N/A')}")
        print(f"   ✅ 팔로워 수: {shop_data.get('follower_count', 0):,}")
        print(f"   ✅ 상품 수: {shop_data.get('product_count', 0)}")
        
        # Shop 분석
        print("\n3. Shop 분석 중...")
        shop_analyzer = ShopAnalyzer()
        analysis_result = await shop_analyzer.analyze(shop_data)
        
        print(f"   ✅ 종합 점수: {analysis_result.get('overall_score', 0)}/100")
        print(f"   ✅ Shop 정보 점수: {analysis_result.get('shop_info', {}).get('score', 0)}/100")
        print(f"   ✅ 상품 분석 점수: {analysis_result.get('product_analysis', {}).get('score', 0)}/100")
        
        # 추천 생성
        print("\n4. 매출 강화 아이디어 생성 중...")
        recommender = SalesEnhancementRecommender()
        recommendations = await recommender.generate_shop_recommendations(
            shop_data,
            analysis_result
        )
        
        print(f"   ✅ 추천 아이디어: {len(recommendations)}개\n")
        
        # 결과 출력
        print("=" * 60)
        print("📊 분석 결과 요약")
        print("=" * 60)
        print(f"\n종합 점수: {analysis_result.get('overall_score', 0)}/100")
        
        level_analysis = analysis_result.get('level_analysis', {})
        print(f"\nShop 레벨:")
        print(f"  - 현재 레벨: {level_analysis.get('current_level', 'N/A')}")
        print(f"  - 정산 리드타임: {level_analysis.get('settlement_leadtime', 15)}일")
        print(f"  - 목표 레벨: {level_analysis.get('target_level', 'N/A')}")
        
        if recommendations:
            print(f"\n💡 매출 강화 아이디어 ({len(recommendations)}개):")
            for i, rec in enumerate(recommendations, 1):
                print(f"\n  {i}. [{rec.get('priority', 'N/A').upper()}] {rec.get('title', 'N/A')}")
                print(f"     {rec.get('description', 'N/A')}")
                if rec.get('action_items'):
                    print(f"     실행 방법:")
                    for item in rec['action_items']:
                        print(f"       - {item}")
        
        print("\n" + "=" * 60)
        print("✅ 분석 완료!")
        print("=" * 60)
        
        return {
            "shop_data": shop_data,
            "analysis_result": analysis_result,
            "recommendations": recommendations
        }
    
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    url = "https://www.qoo10.jp/shop/whippedofficial"
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    
    result = asyncio.run(test_shop_analysis(url))
    
    if result:
        print("\n✅ 테스트 성공!")
    else:
        print("\n❌ 테스트 실패!")
        sys.exit(1)
