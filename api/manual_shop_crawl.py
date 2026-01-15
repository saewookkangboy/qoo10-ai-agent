"""
Qoo10 Shop 페이지 전체 크롤링 테스트 (Playwright 사용)
"""
import asyncio
import json
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.crawler import Qoo10Crawler

async def main():
    # 크롤링할 Shop URL
    url = "https://www.qoo10.jp/shop/whippedofficial"
    
    print("=" * 80)
    print("Qoo10 Shop 페이지 전체 크롤링 시작 (Playwright)")
    print("=" * 80)
    print(f"URL: {url}")
    print()
    
    # 크롤러 초기화
    crawler = Qoo10Crawler()
    
    try:
        # Playwright를 사용한 크롤링 실행
        print("Playwright를 사용한 Shop 크롤링 중...")
        print("(JavaScript 실행 환경에서 동적 콘텐츠를 로드합니다)")
        print()
        shop_data = await crawler.crawl_shop(url, use_playwright=True)
        
        # 결과를 JSON으로 저장 (보기 좋게 포맷팅)
        output_file = "shop_crawl_result.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(shop_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n크롤링 완료! 결과를 {output_file}에 저장했습니다.\n")
        
        # 결과 요약 출력
        print("=" * 80)
        print("Shop 크롤링 결과 요약")
        print("=" * 80)
        
        # 0. 크롤링 방법
        print("\n[0] 크롤링 방법")
        print(f"  - 사용된 방법: {shop_data.get('crawled_with', 'N/A')}")
        
        # 1. 기본 정보
        print("\n[1] Shop 기본 정보")
        print(f"  - Shop ID: {shop_data.get('shop_id', 'N/A')}")
        print(f"  - Shop명: {shop_data.get('shop_name', 'N/A')}")
        print(f"  - Shop 레벨: {shop_data.get('shop_level', 'N/A')}")
        print(f"  - URL: {shop_data.get('url', 'N/A')}")
        
        # 2. 팔로워 및 상품 정보
        print("\n[2] 팔로워 및 상품 정보")
        print(f"  - 팔로워 수: {shop_data.get('follower_count', 0):,}명")
        print(f"  - 상품 수: {shop_data.get('product_count', 0)}개")
        
        # 3. 카테고리 정보
        print("\n[3] 카테고리 정보")
        categories = shop_data.get('categories', {})
        if categories:
            print(f"  - 카테고리 개수: {len(categories)}개")
            print("  - 카테고리 목록:")
            for category, count in list(categories.items())[:10]:  # 최대 10개만 출력
                print(f"    - {category}: {count}개")
            if len(categories) > 10:
                print(f"    ... 외 {len(categories) - 10}개")
        else:
            print("  - 카테고리 정보 없음")
        
        # 4. 상품 목록
        print("\n[4] 상품 목록")
        products = shop_data.get('products', [])
        print(f"  - 추출된 상품 수: {len(products)}개")
        if products:
            print("  - 상품 목록 (최대 10개):")
            for i, product in enumerate(products[:10], 1):
                product_name = product.get('product_name', 'N/A')
                price = product.get('price', {})
                sale_price = price.get('sale_price', 'N/A')
                review_count = product.get('review_count', 0)
                print(f"    {i}. {product_name[:50]}...")
                print(f"       가격: {sale_price}円, 리뷰: {review_count}개")
            if len(products) > 10:
                print(f"    ... 외 {len(products) - 10}개")
        else:
            print("  - 상품 정보 없음")
        
        # 5. 쿠폰 정보
        print("\n[5] 쿠폰 정보")
        coupons = shop_data.get('coupons', [])
        print(f"  - 쿠폰 개수: {len(coupons)}개")
        if coupons:
            print("  - 쿠폰 목록:")
            for i, coupon in enumerate(coupons[:5], 1):  # 최대 5개만 출력
                discount_rate = coupon.get('discount_rate', 0)
                min_amount = coupon.get('min_amount', 0)
                description = coupon.get('description', '')[:50]
                print(f"    {i}. {discount_rate}% 할인 (최소 {min_amount:,}円 이상)")
                if description:
                    print(f"       설명: {description}...")
            if len(coupons) > 5:
                print(f"    ... 외 {len(coupons) - 5}개")
        else:
            print("  - 쿠폰 정보 없음")
        
        # 6. 상품 상세 정보 (첫 번째 상품)
        if products:
            print("\n[6] 첫 번째 상품 상세 정보")
            first_product = products[0]
            print(f"  - 상품명: {first_product.get('product_name', 'N/A')}")
            print(f"  - URL: {first_product.get('product_url', 'N/A')}")
            print(f"  - 썸네일: {first_product.get('thumbnail', 'N/A')}")
            
            price_info = first_product.get('price', {})
            print(f"  - 정가: {price_info.get('original_price', 'N/A')}円")
            print(f"  - 판매가: {price_info.get('sale_price', 'N/A')}円")
            print(f"  - 할인율: {price_info.get('discount_rate', 0)}%")
            
            shipping = first_product.get('shipping_info', {})
            print(f"  - 배송비: {shipping.get('shipping_fee', 'N/A')}円")
            print(f"  - 무료배송 조건: {shipping.get('free_shipping_threshold', 'N/A')}円 이상")
            
            print(f"  - 평점: {first_product.get('rating', 0.0)}")
            print(f"  - 리뷰 수: {first_product.get('review_count', 0)}개")
        
        print("\n" + "=" * 80)
        print("Shop 크롤링 완료!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
