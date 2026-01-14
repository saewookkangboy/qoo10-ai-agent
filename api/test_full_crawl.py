"""
Qoo10 상품 페이지 전체 크롤링 테스트
"""
import asyncio
import json
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.crawler import Qoo10Crawler

async def main():
    # 크롤링할 URL
    url = "https://www.qoo10.jp/item/%e3%83%9b%e3%82%a4%e3%83%83%e3%83%97%e3%83%89-%e4%bd%8e%e5%88%ba%e6%bf%80%e3%82%b9%e3%82%af%e3%83%a9%e3%83%96-%e3%83%b4%e3%82%a3%e3%83%bc%e3%82%ac%e3%83%b3%e3%83%91%e3%83%83%e3%82%af%e3%82%b9%e3%82%af%e3%83%a9%e3%83%96-210G%ef%bc%883%e7%a8%ae%e9%a1%9e%ef%bc%89-%e9%a1%94%e3%81%ab%e3%82%82%e4%bd%bf%e3%81%88%e3%82%8b%e3%82%b9%e3%82%af%e3%83%a9%e3%83%96-%e3%83%87%e3%82%a4%e3%83%aa%e3%83%bc%e3%83%9c%e3%83%87%e3%82%a3%e3%82%bd%e3%83%bc%e3%83%97-%e3%83%8a%e3%82%a4%e3%82%a2%e3%82%b7%e3%83%b3%e3%82%a4%e3%83%9f%e3%83%89%ef%bc%86%e3%82%bb%e3%83%a9%e3%83%9f%e3%83%89/1093098159?&sellerview=on&ga_priority=-1&ga_prdlist=remarkables&ga_tid=&ga_idx=5"
    
    print("=" * 80)
    print("Qoo10 상품 페이지 전체 크롤링 시작")
    print("=" * 80)
    print(f"URL: {url}")
    print()
    
    # 크롤러 초기화
    crawler = Qoo10Crawler()
    
    try:
        # Playwright를 사용한 크롤링 실행
        print("Playwright를 사용한 크롤링 중...")
        print("(JavaScript 실행 환경에서 동적 콘텐츠를 로드합니다)")
        print()
        product_data = await crawler.crawl_product(url, use_playwright=True)
        
        # 결과를 JSON으로 저장 (보기 좋게 포맷팅)
        output_file = "crawl_result.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(product_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n크롤링 완료! 결과를 {output_file}에 저장했습니다.\n")
        
        # 결과 요약 출력
        print("=" * 80)
        print("크롤링 결과 요약")
        print("=" * 80)
        
        # 0. 크롤링 방법
        print("\n[0] 크롤링 방법")
        print(f"  - 사용된 방법: {product_data.get('crawled_with', 'N/A')}")
        
        # 1. 기본 정보
        print("\n[1] 기본 정보")
        print(f"  - 상품명: {product_data.get('product_name', 'N/A')}")
        print(f"  - 상품코드: {product_data.get('product_code', 'N/A')}")
        print(f"  - URL: {product_data.get('url', 'N/A')}")
        print(f"  - 카테고리: {product_data.get('category', 'N/A')}")
        print(f"  - 브랜드: {product_data.get('brand', 'N/A')}")
        
        # 2. 가격 정보
        print("\n[2] 가격 정보")
        price = product_data.get('price', {})
        print(f"  - 정가: {price.get('original_price', 'N/A')}円")
        print(f"  - 판매가: {price.get('sale_price', 'N/A')}円")
        print(f"  - 할인율: {price.get('discount_rate', 0)}%")
        print(f"  - 쿠폰할인: {price.get('coupon_discount', 'N/A')}")
        print(f"  - Q포인트 정보: {price.get('qpoint_info', 'N/A')}")
        
        # 3. 이미지 정보
        print("\n[3] 이미지 정보")
        images = product_data.get('images', {})
        print(f"  - 썸네일: {images.get('thumbnail', 'N/A')}")
        detail_images = images.get('detail_images', [])
        print(f"  - 상세이미지 개수: {len(detail_images)}")
        if detail_images:
            print("  - 상세이미지 목록:")
            for i, img in enumerate(detail_images[:5], 1):  # 최대 5개만 출력
                print(f"    {i}. {img}")
            if len(detail_images) > 5:
                print(f"    ... 외 {len(detail_images) - 5}개")
        
        # 4. 설명
        print("\n[4] 상품 설명")
        description = product_data.get('description', '')
        if description:
            desc_preview = description[:200] + "..." if len(description) > 200 else description
            print(f"  - 설명 길이: {len(description)}자")
            print(f"  - 설명 미리보기: {desc_preview}")
        else:
            print("  - 설명 없음")
        
        # 5. 리뷰 정보
        print("\n[5] 리뷰 정보")
        reviews = product_data.get('reviews', {})
        print(f"  - 평점: {reviews.get('rating', 0.0)}")
        print(f"  - 리뷰 수: {reviews.get('review_count', 0)}")
        review_list = reviews.get('reviews', [])
        if review_list:
            print(f"  - 추출된 리뷰 텍스트: {len(review_list)}개")
            for i, review in enumerate(review_list[:3], 1):  # 최대 3개만 출력
                review_preview = review[:100] + "..." if len(review) > 100 else review
                print(f"    {i}. {review_preview}")
        
        # 6. 판매자 정보
        print("\n[6] 판매자 정보")
        seller = product_data.get('seller_info', {})
        print(f"  - 샵 ID: {seller.get('shop_id', 'N/A')}")
        print(f"  - 샵명: {seller.get('shop_name', 'N/A')}")
        print(f"  - 샵 레벨: {seller.get('shop_level', 'N/A')}")
        
        # 7. 배송 정보
        print("\n[7] 배송 정보")
        shipping = product_data.get('shipping_info', {})
        print(f"  - 배송비: {shipping.get('shipping_fee', 'N/A')}円")
        print(f"  - 무료배송: {'예' if shipping.get('free_shipping', False) else '아니오'}")
        print(f"  - 배송 방법: {shipping.get('shipping_method', 'N/A')}")
        print(f"  - 예상 배송일: {shipping.get('estimated_delivery', 'N/A')}")
        print(f"  - 반품 정책: {shipping.get('return_policy', 'N/A')}")
        
        # 8. 쿠폰 정보
        print("\n[8] 쿠폰 정보")
        coupon = product_data.get('coupon_info', {})
        print(f"  - 쿠폰 있음: {'예' if coupon.get('has_coupon', False) else '아니오'}")
        print(f"  - 쿠폰 타입: {coupon.get('coupon_type', 'N/A')}")
        print(f"  - 최대 할인: {coupon.get('max_discount', 'N/A')}")
        print(f"  - 쿠폰 텍스트: {coupon.get('coupon_text', 'N/A')}")
        
        # 9. Q포인트 정보
        print("\n[9] Q포인트 정보")
        qpoint = product_data.get('qpoint_info', {})
        print(f"  - 최대 포인트: {qpoint.get('max_points', 'N/A')}P")
        print(f"  - 수령확인 포인트: {qpoint.get('receive_confirmation_points', 'N/A')}P")
        print(f"  - 리뷰 작성 포인트: {qpoint.get('review_points', 'N/A')}P")
        print(f"  - 자동 포인트: {qpoint.get('auto_points', 'N/A')}P")
        
        # 10. MOVE 상품 여부
        print("\n[10] MOVE 상품 여부")
        is_move = product_data.get('is_move_product', False)
        print(f"  - MOVE 상품: {'예' if is_move else '아니오'}")
        
        # 11. 검색 키워드
        print("\n[11] 검색 키워드")
        keywords = product_data.get('search_keywords', [])
        if keywords:
            print(f"  - 키워드: {', '.join(keywords)}")
        else:
            print("  - 키워드 없음")
        
        # 12. 페이지 구조 분석
        print("\n[12] 페이지 구조 분석")
        page_structure = product_data.get('page_structure', {})
        if page_structure:
            all_classes = page_structure.get('all_div_classes', [])
            print(f"  - 총 div 클래스 수: {len(all_classes)}")
            
            key_elements = page_structure.get('key_elements', {})
            if key_elements:
                print("  - 주요 요소:")
                for category, elements in key_elements.items():
                    print(f"    - {category}: {len(elements)}개")
                    if elements:
                        top_classes = [e.get('class', '') for e in elements[:3]]
                        print(f"      예시: {', '.join(top_classes)}")
            
            semantic_structure = page_structure.get('semantic_structure', {})
            if semantic_structure:
                print("  - 의미 구조:")
                for semantic_key, classes in semantic_structure.items():
                    if classes:
                        print(f"    - {semantic_key}: {len(classes)}개 클래스")
                        top_semantic = [c.get('class', '') if isinstance(c, dict) else c for c in classes[:2]]
                        print(f"      예시: {', '.join(str(c) for c in top_semantic)}")
        else:
            print("  - 페이지 구조 정보 없음")
        
        print("\n" + "=" * 80)
        print("크롤링 완료!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
