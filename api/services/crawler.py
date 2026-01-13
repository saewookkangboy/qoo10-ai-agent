"""
Qoo10 크롤링 서비스 (AI 강화 학습 및 방화벽 우회 기능 포함)
Qoo10 상품 및 Shop 페이지에서 데이터를 수집하며, 학습을 통해 성능을 지속적으로 개선합니다.
"""
import httpx
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional, Any
import asyncio
from urllib.parse import urlparse
import random
import time
from datetime import datetime
import os
from dotenv import load_dotenv

from services.database import CrawlerDatabase

load_dotenv()


class Qoo10Crawler:
    """Qoo10 페이지 크롤러 (AI 강화 학습 및 방화벽 우회 기능 포함)"""
    
    # 다양한 User-Agent 목록
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    def __init__(self, db: Optional[CrawlerDatabase] = None):
        """
        크롤러 초기화
        
        Args:
            db: 데이터베이스 인스턴스 (없으면 자동 생성)
        """
        self.base_url = "https://www.qoo10.jp"
        self.timeout = 30.0
        self.max_retries = 3
        self.retry_delay_base = 2.0  # 기본 재시도 지연 시간 (초)
        
        # 데이터베이스 초기화
        self.db = db or CrawlerDatabase()
        
        # 프록시 설정 (환경 변수에서 읽기)
        self.proxies = self._load_proxies()
        
        # 현재 사용 중인 User-Agent 및 프록시
        self.current_user_agent = None
        self.current_proxy = None
        
        # 세션 관리
        self.session_cookies = {}
    
    def _load_proxies(self) -> List[str]:
        """환경 변수에서 프록시 목록 로드"""
        proxy_list = os.getenv("PROXY_LIST", "")
        if proxy_list:
            return [p.strip() for p in proxy_list.split(",") if p.strip()]
        return []
    
    def _get_user_agent(self) -> str:
        """최적의 User-Agent 선택 (학습 데이터 기반)"""
        # 데이터베이스에서 가장 성공률이 높은 User-Agent 조회
        best_ua = self.db.get_best_user_agent()
        
        if best_ua:
            self.current_user_agent = best_ua
            return best_ua
        
        # 없으면 랜덤 선택
        self.current_user_agent = random.choice(self.USER_AGENTS)
        return self.current_user_agent
    
    def _get_proxy(self) -> Optional[Dict[str, str]]:
        """최적의 프록시 선택 (학습 데이터 기반)"""
        if not self.proxies:
            return None
        
        # 데이터베이스에서 가장 성공률이 높은 프록시 조회
        best_proxy = self.db.get_best_proxy()
        
        if best_proxy:
            self.current_proxy = best_proxy
        else:
            # 없으면 랜덤 선택
            self.current_proxy = random.choice(self.proxies)
        
        # httpx 프록시 형식으로 변환
        return {"http://": self.current_proxy, "https://": self.current_proxy}
    
    def _get_headers(self) -> Dict[str, str]:
        """요청 헤더 생성"""
        headers = {
            "User-Agent": self._get_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }
        return headers
    
    async def _random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """랜덤 지연 시간 (인간처럼 보이게)"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def _make_request(
        self,
        url: str,
        retry_count: int = 0
    ) -> httpx.Response:
        """
        HTTP 요청 수행 (재시도 및 우회 기능 포함)
        
        Args:
            url: 요청할 URL
            retry_count: 현재 재시도 횟수
            
        Returns:
            HTTP 응답 객체
        """
        start_time = time.time()
        proxy_config = self._get_proxy()
        headers = self._get_headers()
        
        # 지연 시간 추가 (너무 빠른 요청 방지)
        if retry_count == 0:
            await self._random_delay(1.0, 3.0)
        else:
            # 재시도 시 더 긴 지연
            await asyncio.sleep(self.retry_delay_base * (2 ** retry_count))
        
        try:
            # httpx.AsyncClient 설정
            # httpx 0.25.2에서는 proxies를 지원하지만, None일 때는 전달하지 않음
            client_kwargs = {
                "timeout": self.timeout,
                "follow_redirects": True,
                "cookies": self.session_cookies
            }
            
            # 프록시가 있는 경우에만 추가 (None이 아닐 때만)
            if proxy_config is not None and proxy_config:
                # httpx 버전에 따라 proxies 지원 여부 확인
                import inspect
                sig = inspect.signature(httpx.AsyncClient.__init__)
                if 'proxies' in sig.parameters:
                    # httpx 0.25.2 이하: proxies 인자 지원
                    client_kwargs["proxies"] = proxy_config
                else:
                    # httpx 0.26.0 이상: transport 사용
                    from httpx import AsyncHTTPTransport
                    proxy_url = proxy_config.get("http://") or proxy_config.get("https://")
                    if proxy_url:
                        transport = AsyncHTTPTransport(proxy=proxy_url)
                        client_kwargs["transport"] = transport
            
            async with httpx.AsyncClient(**client_kwargs) as client:
                response = await client.get(url, headers=headers)
                response_time = time.time() - start_time
                
                # 성공 기록
                self.db.record_crawling_performance(
                    url=url,
                    success=True,
                    response_time=response_time,
                    status_code=response.status_code,
                    user_agent=self.current_user_agent,
                    proxy_used=self.current_proxy,
                    retry_count=retry_count
                )
                
                # 쿠키 업데이트
                self.session_cookies.update(response.cookies)
                
                return response
                
        except httpx.HTTPStatusError as e:
            response_time = time.time() - start_time
            status_code = e.response.status_code if e.response else None
            
            # 실패 기록
            self.db.record_crawling_performance(
                url=url,
                success=False,
                response_time=response_time,
                status_code=status_code,
                error_message=str(e),
                user_agent=self.current_user_agent,
                proxy_used=self.current_proxy,
                retry_count=retry_count
            )
            
            # 429 (Too Many Requests) 또는 403 (Forbidden)인 경우 재시도
            if status_code in [429, 403, 503] and retry_count < self.max_retries:
                # 다른 User-Agent와 프록시로 재시도
                self.current_user_agent = None
                self.current_proxy = None
                return await self._make_request(url, retry_count + 1)
            
            raise
            
        except (httpx.RequestError, httpx.TimeoutException) as e:
            response_time = time.time() - start_time
            
            # 실패 기록
            self.db.record_crawling_performance(
                url=url,
                success=False,
                response_time=response_time,
                error_message=str(e),
                user_agent=self.current_user_agent,
                proxy_used=self.current_proxy,
                retry_count=retry_count
            )
            
            # 네트워크 오류인 경우 재시도
            if retry_count < self.max_retries:
                # 다른 프록시로 재시도
                self.current_proxy = None
                return await self._make_request(url, retry_count + 1)
            
            raise
    
    async def crawl_product(self, url: str) -> Dict[str, Any]:
        """
        상품 페이지 크롤링 (다양한 URL 형식 지원)
        
        Args:
            url: Qoo10 상품 URL (다양한 형식 지원: /g/XXXXX, /item/.../XXXXX, ?goodscode=XXXXX 등)
            
        Returns:
            상품 데이터 딕셔너리
        """
        try:
            # URL 정규화 (다양한 형식을 표준 형식으로 변환 시도)
            normalized_url = self._normalize_product_url(url)
            
            # HTTP 요청 (정규화된 URL 사용)
            response = await self._make_request(normalized_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 상품 기본 정보 추출 (AI 학습 기반 선택자 사용)
            product_data = {
                "url": normalized_url,  # 정규화된 URL 사용
                "product_code": self._extract_product_code(normalized_url, soup),
                "product_name": self._extract_product_name(soup),
                "category": self._extract_category(soup),
                "brand": self._extract_brand(soup),
                "price": self._extract_price(soup),
                "images": self._extract_images(soup),
                "description": self._extract_description(soup),
                "search_keywords": self._extract_search_keywords(soup),
                "reviews": self._extract_reviews(soup),
                "seller_info": self._extract_seller_info(soup),
                "shipping_info": self._extract_shipping_info(soup)
            }
            
            # 데이터베이스에 저장
            self.db.save_crawled_product(product_data)
            
            return product_data
        
        except httpx.HTTPError as e:
            raise Exception(f"HTTP error while crawling: {str(e)}")
        except Exception as e:
            raise Exception(f"Error crawling product: {str(e)}")
    
    def _extract_with_learning(
        self,
        selector_type: str,
        soup: BeautifulSoup,
        default_selectors: List[str],
        extract_func
    ) -> Any:
        """
        AI 학습 기반 데이터 추출
        
        Args:
            selector_type: 선택자 타입 ('product_name', 'price', etc.)
            soup: BeautifulSoup 객체
            default_selectors: 기본 선택자 목록
            extract_func: 추출 함수
            
        Returns:
            추출된 데이터
        """
        # 데이터베이스에서 가장 성공률이 높은 선택자 조회
        best_selectors = self.db.get_best_selectors(selector_type, limit=10)
        
        # 학습된 선택자와 기본 선택자 결합 (학습된 것이 우선)
        all_selectors = []
        if best_selectors:
            all_selectors.extend([s["selector"] for s in best_selectors])
        all_selectors.extend(default_selectors)
        
        # 중복 제거 (순서 유지)
        seen = set()
        unique_selectors = []
        for selector in all_selectors:
            if selector not in seen:
                seen.add(selector)
                unique_selectors.append(selector)
        
        # 각 선택자 시도
        for selector in unique_selectors:
            try:
                result = extract_func(soup, selector)
                if result and result != "상품명 없음" and result != "":
                    # 성공 기록
                    self.db.record_selector_performance(
                        selector_type=selector_type,
                        selector=selector,
                        success=True,
                        data_quality=1.0 if result else 0.0
                    )
                    return result
            except Exception:
                # 실패 기록
                self.db.record_selector_performance(
                    selector_type=selector_type,
                    selector=selector,
                    success=False
                )
                continue
        
        # 모두 실패한 경우
        return extract_func(soup, None) if extract_func else None
    
    def _normalize_product_url(self, url: str) -> str:
        """Qoo10 상품 URL 정규화 (다양한 형식을 표준 형식으로 변환)"""
        # URL에서 상품 코드 추출
        product_code = None
        
        # 다양한 패턴에서 상품 코드 추출
        patterns = [
            (r'goodscode=(\d+)', 1),
            (r'/g/(\d+)', 1),
            (r'/item/[^/]+/(\d+)', 1),
            (r'/item/[^/]+/(\d+)\?', 1),
        ]
        
        for pattern, group in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                product_code = match.group(group)
                break
        
        # 상품 코드가 있으면 표준 형식으로 변환
        if product_code:
            # 표준 형식: https://www.qoo10.jp/gmkt.inc/Goods/Goods.aspx?goodscode=XXXXX
            return f"https://www.qoo10.jp/gmkt.inc/Goods/Goods.aspx?goodscode={product_code}"
        
        # 변환할 수 없으면 원본 반환
        return url
    
    def _extract_product_code(self, url: str, soup: BeautifulSoup) -> Optional[str]:
        """상품 코드 추출 (다양한 URL 형식 지원)"""
        # 1. URL에서 추출 시도 - 다양한 패턴 지원
        patterns = [
            r'goodscode=(\d+)',  # 기본 형식: ?goodscode=123456
            r'/g/(\d+)',  # 짧은 형식: /g/123456
            r'/item/[^/]+/(\d+)',  # 긴 형식: /item/.../123456
            r'/item/[^/]+/(\d+)\?',  # 쿼리 파라미터 포함
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # 2. 페이지에서 추출 시도
        code_elem = soup.find('input', {'name': 'goodscode'}) or soup.find('meta', {'property': 'product:retailer_item_id'})
        if code_elem:
            code = code_elem.get('value') or code_elem.get('content')
            if code:
                return code
        
        # 3. JSON-LD 스키마에서 추출 시도
        json_ld = soup.find('script', {'type': 'application/ld+json'})
        if json_ld:
            try:
                import json
                data = json.loads(json_ld.string)
                if isinstance(data, dict):
                    # product:retailer_item_id 또는 sku 찾기
                    if 'sku' in data:
                        return str(data['sku'])
                    if 'productID' in data:
                        return str(data['productID'])
            except (ValueError, json.JSONDecodeError, TypeError):
                pass
        
        # 4. 메타 태그에서 추출 시도
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            prop = meta.get('property') or meta.get('name')
            if prop and ('product' in prop.lower() or 'item' in prop.lower()):
                content = meta.get('content')
                if content and content.isdigit():
                    return content
        
        return None
    
    def _extract_product_name(self, soup: BeautifulSoup) -> str:
        """상품명 추출 (AI 학습 기반)"""
        default_selectors = [
            'h1.product-name',
            'h1[itemprop="name"]',
            '.product_name',
            'h1'
        ]
        
        def extract_func(soup_obj, selector):
            if selector:
                elem = soup_obj.select_one(selector)
                if elem:
                    return elem.get_text(strip=True)
            return "상품명 없음"
        
        return self._extract_with_learning(
            "product_name",
            soup,
            default_selectors,
            extract_func
        )
    
    def _extract_category(self, soup: BeautifulSoup) -> Optional[str]:
        """카테고리 추출 (AI 학습 기반)"""
        default_selectors = [
            'meta[property="product:category"]',
            'nav.breadcrumb a',
            'ol.breadcrumb a',
            '.category'
        ]
        
        def extract_func(soup_obj, selector):
            if selector:
                if selector.startswith('meta'):
                    elem = soup_obj.find('meta', {'property': 'product:category'})
                    if elem:
                        return elem.get('content')
                else:
                    elems = soup_obj.select(selector)
                    if elems and len(elems) > 1:
                        return elems[-1].get_text(strip=True)
            
            # 기본 방법
            category_elem = soup_obj.find('meta', {'property': 'product:category'})
            if category_elem:
                return category_elem.get('content')
            
            breadcrumb = soup_obj.find('nav', class_='breadcrumb') or soup_obj.find('ol', class_='breadcrumb')
            if breadcrumb:
                links = breadcrumb.find_all('a')
                if len(links) > 1:
                    return links[-1].get_text(strip=True)
            
            return None
        
        return self._extract_with_learning(
            "category",
            soup,
            default_selectors,
            extract_func
        )
    
    def _extract_brand(self, soup: BeautifulSoup) -> Optional[str]:
        """브랜드 추출"""
        brand_elem = soup.find('meta', {'property': 'product:brand'})
        if brand_elem:
            return brand_elem.get('content')
        
        # 페이지에서 브랜드 정보 찾기
        brand_text = soup.find(string=re.compile(r'ブランド|브랜드|Brand'))
        if brand_text:
            parent = brand_text.find_parent()
            if parent:
                return parent.get_text(strip=True).split(':')[-1].strip()
        
        return None
    
    def _extract_price(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """가격 정보 추출 (AI 학습 기반)"""
        price_data = {
            "original_price": None,
            "sale_price": None,
            "discount_rate": 0
        }
        
        default_selectors = [
            '.price',
            '.product-price',
            '[itemprop="price"]',
            '.sale_price'
        ]
        
        def extract_func(soup_obj, selector):
            if selector:
                price_elem = soup_obj.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price = self._parse_price(price_text)
                    if price:
                        return price
            return None
        
        sale_price = self._extract_with_learning(
            "price",
            soup,
            default_selectors,
            extract_func
        )
        
        if sale_price:
            price_data["sale_price"] = sale_price
        
        # 정가 찾기
        original_price_elem = soup.find(class_=re.compile(r'original|정가|定価'))
        if original_price_elem:
            original_text = original_price_elem.get_text(strip=True)
            price_data["original_price"] = self._parse_price(original_text)
        
        # 할인율 계산
        if price_data["original_price"] and price_data["sale_price"]:
            discount = price_data["original_price"] - price_data["sale_price"]
            price_data["discount_rate"] = int((discount / price_data["original_price"]) * 100)
        
        return price_data
    
    def _parse_price(self, price_text: str) -> Optional[int]:
        """가격 텍스트를 숫자로 변환"""
        # 숫자와 쉼표만 추출
        numbers = re.sub(r'[^\d,]', '', price_text.replace(',', ''))
        try:
            return int(numbers) if numbers else None
        except:
            return None
    
    def _extract_images(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """이미지 정보 추출"""
        images = {
            "thumbnail": None,
            "detail_images": []
        }
        
        # 썸네일 이미지
        thumbnail_selectors = [
            'img.product-thumbnail',
            'img[itemprop="image"]',
            '.product-image img',
            'img.main-image'
        ]
        
        for selector in thumbnail_selectors:
            img = soup.select_one(selector)
            if img:
                images["thumbnail"] = img.get('src') or img.get('data-src')
                break
        
        # 상세 이미지
        detail_img_selectors = [
            '.product-detail img',
            '.detail-images img',
            '.product-images img'
        ]
        
        for selector in detail_img_selectors:
            imgs = soup.select(selector)
            for img in imgs:
                src = img.get('src') or img.get('data-src')
                if src and src not in images["detail_images"]:
                    images["detail_images"].append(src)
        
        return images
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """상품 설명 추출 (AI 학습 기반)"""
        default_selectors = [
            '.product-description',
            '[itemprop="description"]',
            '.description',
            '.product-detail'
        ]
        
        def extract_func(soup_obj, selector):
            if selector:
                desc_elem = soup_obj.select_one(selector)
                if desc_elem:
                    return desc_elem.get_text(strip=True)
            return ""
        
        return self._extract_with_learning(
            "description",
            soup,
            default_selectors,
            extract_func
        )
    
    def _extract_search_keywords(self, soup: BeautifulSoup) -> List[str]:
        """검색어 추출"""
        keywords = []
        
        # 메타 키워드
        meta_keywords = soup.find('meta', {'name': 'keywords'})
        if meta_keywords:
            keywords.extend(meta_keywords.get('content', '').split(','))
        
        # 검색어 필드 (페이지 내)
        search_keyword_elem = soup.find('input', {'name': 'search_keyword'})
        if search_keyword_elem:
            keywords.append(search_keyword_elem.get('value', ''))
        
        return [k.strip() for k in keywords if k.strip()]
    
    def _extract_reviews(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """리뷰 정보 추출"""
        reviews_data = {
            "rating": 0.0,
            "review_count": 0,
            "reviews": []
        }
        
        # 평점 추출
        rating_elem = soup.find('meta', {'itemprop': 'ratingValue'}) or \
                     soup.find(class_=re.compile(r'rating|평점'))
        if rating_elem:
            rating_text = rating_elem.get('content') or rating_elem.get_text(strip=True)
            try:
                reviews_data["rating"] = float(re.findall(r'\d+\.?\d*', rating_text)[0])
            except:
                pass
        
        # 리뷰 수 추출
        review_count_elem = soup.find('meta', {'itemprop': 'reviewCount'}) or \
                           soup.find(string=re.compile(r'レビュー|리뷰'))
        if review_count_elem:
            count_text = review_count_elem.get('content') if hasattr(review_count_elem, 'get') else str(review_count_elem)
            numbers = re.findall(r'\d+', count_text)
            if numbers:
                reviews_data["review_count"] = int(numbers[0])
        
        # 리뷰 텍스트 (최근 리뷰)
        review_elements = soup.select('.review-item, .review-text, [itemprop="reviewBody"]')
        for elem in review_elements[:10]:  # 최근 10개만
            review_text = elem.get_text(strip=True)
            if review_text:
                reviews_data["reviews"].append(review_text)
        
        return reviews_data
    
    def _extract_seller_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """판매자 정보 추출"""
        seller_info = {
            "shop_id": None,
            "shop_name": None,
            "shop_level": None
        }
        
        # Shop 링크에서 추출
        shop_link = soup.find('a', href=re.compile(r'/shop/'))
        if shop_link:
            href = shop_link.get('href', '')
            match = re.search(r'/shop/([^/?]+)', href)
            if match:
                seller_info["shop_id"] = match.group(1)
            seller_info["shop_name"] = shop_link.get_text(strip=True)
        
        return seller_info
    
    def _extract_shipping_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """배송 정보 추출"""
        shipping_info = {
            "shipping_fee": None,
            "shipping_method": None,
            "estimated_delivery": None
        }
        
        # 배송비 정보 찾기
        shipping_elem = soup.find(string=re.compile(r'送料|배송비|Shipping'))
        if shipping_elem:
            parent = shipping_elem.find_parent()
            if parent:
                shipping_text = parent.get_text(strip=True)
                # 숫자 추출
                numbers = re.findall(r'\d+', shipping_text)
                if numbers:
                    shipping_info["shipping_fee"] = int(numbers[0])
        
        return shipping_info
    
    async def crawl_shop(self, url: str) -> Dict[str, Any]:
        """
        Shop 페이지 크롤링
        
        Args:
            url: Qoo10 Shop URL
            
        Returns:
            Shop 데이터 딕셔너리
        """
        try:
            # HTTP 요청
            response = await self._make_request(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Shop 기본 정보 추출
            shop_data = {
                "url": url,
                "shop_id": self._extract_shop_id(url),
                "shop_name": self._extract_shop_name(soup),
                "shop_level": self._extract_shop_level(soup),
                "follower_count": self._extract_follower_count(soup),
                "product_count": self._extract_product_count(soup),
                "categories": self._extract_shop_categories(soup),
                "products": self._extract_shop_products(soup),
                "coupons": self._extract_shop_coupons(soup)
            }
            
            # 데이터베이스에 저장 (메서드가 있는 경우만)
            if hasattr(self.db, 'save_crawled_shop'):
                try:
                    self.db.save_crawled_shop(shop_data)
                except:
                    pass  # 데이터베이스 저장 실패해도 계속 진행
            
            return shop_data
        
        except httpx.HTTPError as e:
            raise Exception(f"HTTP error while crawling shop: {str(e)}")
        except Exception as e:
            raise Exception(f"Error crawling shop: {str(e)}")
    
    def _extract_shop_id(self, url: str) -> Optional[str]:
        """Shop ID 추출"""
        match = re.search(r'/shop/([^/?]+)', url)
        if match:
            return match.group(1)
        return None
    
    def _extract_shop_name(self, soup: BeautifulSoup) -> str:
        """Shop 이름 추출"""
        # 여러 가능한 선택자 시도
        selectors = [
            'h1.shop-name',
            'h1',
            '.shop-title',
            '[itemprop="name"]'
        ]
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if text and len(text) > 0:
                    return text
        
        return "Shop 이름 없음"
    
    def _extract_shop_level(self, soup: BeautifulSoup) -> Optional[str]:
        """Shop 레벨 추출"""
        # POWER, 우수 셀러, 일반 셀러 등 텍스트 찾기
        level_text = soup.find(string=re.compile(r'POWER|パワー|우수|일반|excellent|normal|power', re.I))
        if level_text:
            text = level_text.lower()
            if 'power' in text or 'パワー' in text:
                return "power"
            elif 'excellent' in text or '우수' in text:
                return "excellent"
            elif 'normal' in text or '일반' in text:
                return "normal"
        
        # POWER 95% 같은 패턴 찾기
        power_elem = soup.find(string=re.compile(r'POWER\s*\d+%', re.I))
        if power_elem:
            return "power"
        
        return "unknown"
    
    def _extract_follower_count(self, soup: BeautifulSoup) -> int:
        """팔로워 수 추출"""
        # 팔로워 텍스트 찾기
        follower_text = soup.find(string=re.compile(r'フォロワー|팔로워|follower', re.I))
        if follower_text:
            parent = follower_text.find_parent()
            if parent:
                text = parent.get_text(strip=True)
                # 숫자 추출
                numbers = re.findall(r'[\d,]+', text.replace(',', ''))
                if numbers:
                    try:
                        return int(numbers[0])
                    except:
                        pass
        return 0
    
    def _extract_product_count(self, soup: BeautifulSoup) -> int:
        """상품 수 추출"""
        # "全ての商品 (16)" 같은 패턴 찾기
        product_text = soup.find(string=re.compile(r'全ての商品|전체 상품|商品.*\(\d+\)', re.I))
        if product_text:
            numbers = re.findall(r'\((\d+)\)', product_text)
            if numbers:
                try:
                    return int(numbers[0])
                except:
                    pass
        
        # 상품 리스트에서 개수 세기
        product_items = soup.select('.product-item, .goods-item, [data-goods-code]')
        return len(product_items)
    
    def _extract_shop_categories(self, soup: BeautifulSoup) -> Dict[str, int]:
        """Shop 카테고리 분포 추출 (개선 버전)"""
        categories = {}
        
        # 상품 카테고리 정보 추출
        category_links = soup.select('a[href*="/category/"], a[href*="/cat/"], .category-link, [class*="category"]')
        for link in category_links:
            category_name = link.get_text(strip=True)
            if category_name and len(category_name) > 0:
                categories[category_name] = categories.get(category_name, 0) + 1
        
        # 상품 목록에서 카테고리 추출
        products = self._extract_shop_products(soup)
        for product in products:
            if product.get("category"):
                categories[product["category"]] = categories.get(product["category"], 0) + 1
            if product.get("product_type"):
                categories[product["product_type"]] = categories.get(product["product_type"], 0) + 1
        
        return categories
    
    def _extract_shop_products(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Shop 상품 목록 추출 (상품 종류 파악 포함)"""
        products = []
        
        # 상품 아이템 찾기 (다양한 선택자 시도)
        product_items = soup.select(
            '.product-item, .goods-item, [data-goods-code], '
            '.item_list li, .goods_list li, .product-list-item, '
            '[class*="product"], [class*="goods"], [class*="item"]'
        )
        
        # 상품이 없는 경우 다른 패턴 시도
        if not product_items:
            # 리스트 형태의 상품 찾기
            product_items = soup.find_all('div', class_=re.compile(r'item|product|goods', re.I))
        
        for item in product_items[:50]:  # 최대 50개까지 확장
            product = {
                "product_name": "",
                "price": {"sale_price": None, "original_price": None},
                "rating": 0.0,
                "review_count": 0,
                "product_type": None,  # 상품 종류 (크림, 클렌저, 마스크팩 등)
                "category": None,  # 카테고리
                "keywords": []  # 상품명에서 추출한 키워드
            }
            
            # 상품명 추출 (다양한 선택자 시도)
            name_selectors = [
                '.product-name', '.goods-name', 'h3', 'h4', 
                '.item-name', '.title', 'a[title]', '[title]',
                '.name', '.product-title'
            ]
            for selector in name_selectors:
                name_elem = item.select_one(selector)
                if name_elem:
                    product["product_name"] = name_elem.get_text(strip=True) or name_elem.get('title', '')
                    if product["product_name"]:
                        break
            
            # 상품명이 없으면 텍스트에서 추출
            if not product["product_name"]:
                text = item.get_text(strip=True)
                # 첫 번째 의미있는 텍스트를 상품명으로 사용
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                if lines:
                    product["product_name"] = lines[0][:100]  # 최대 100자
            
            # 상품 종류 파악 (상품명 기반)
            if product["product_name"]:
                product["product_type"] = self._detect_product_type(product["product_name"])
                product["keywords"] = self._extract_product_keywords(product["product_name"])
            
            # 가격 추출
            price_selectors = [
                '.price', '.goods-price', '.sale-price', 
                '[class*="price"]', '.cost', '.amount'
            ]
            for selector in price_selectors:
                price_elem = item.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price = self._parse_price(price_text)
                    if price:
                        product["price"]["sale_price"] = price
                        break
            
            # 정가 추출
            original_price_elem = item.select_one('.original-price, .list-price, [class*="original"]')
            if original_price_elem:
                original_text = original_price_elem.get_text(strip=True)
                original_price = self._parse_price(original_text)
                if original_price:
                    product["price"]["original_price"] = original_price
            
            # 평점 추출
            rating_selectors = [
                '[itemprop="ratingValue"]', '.rating', '[class*="rating"]',
                '[class*="star"]', '.score'
            ]
            for selector in rating_selectors:
                rating_elem = item.select_one(selector)
                if rating_elem:
                    rating_text = rating_elem.get('content') or rating_elem.get_text(strip=True)
                    try:
                        rating_match = re.findall(r'\d+\.?\d*', rating_text)
                        if rating_match:
                            product["rating"] = float(rating_match[0])
                            break
                    except:
                        pass
            
            # 리뷰 수 추출
            review_patterns = [
                r'レビュー\s*\((\d+)\)',
                r'리뷰\s*\((\d+)\)',
                r'review\s*\((\d+)\)',
                r'\((\d+)\)'
            ]
            item_text = item.get_text()
            for pattern in review_patterns:
                match = re.search(pattern, item_text, re.I)
                if match:
                    try:
                        product["review_count"] = int(match.group(1))
                        break
                    except:
                        pass
            
            # 카테고리 추출 (상품명이나 링크에서)
            category_link = item.select_one('a[href*="/category/"], a[href*="/cat/"]')
            if category_link:
                href = category_link.get('href', '')
                category_match = re.search(r'/(?:category|cat)/([^/]+)', href)
                if category_match:
                    product["category"] = category_match.group(1)
            
            if product["product_name"]:
                products.append(product)
        
        return products
    
    def _detect_product_type(self, product_name: str) -> Optional[str]:
        """상품명에서 상품 종류 감지"""
        product_name_lower = product_name.lower()
        
        # 스킨케어 제품 타입 키워드
        product_types = {
            "크림": ["크림", "クリーム", "cream"],
            "클렌저": ["클렌저", "クレンザー", "cleanser", "クレンジング"],
            "마스크팩": ["마스크", "マスク", "mask", "パック"],
            "세럼": ["세럼", "セラム", "serum"],
            "로션": ["로션", "ローション", "lotion"],
            "토너": ["토너", "トナー", "toner"],
            "에센스": ["에센스", "エッセンス", "essence"],
            "스크럽": ["스크럽", "スクラブ", "scrub"],
            "보디케어": ["보디", "ボディ", "body"],
            "샴푸": ["샴푸", "シャンプー", "shampoo"],
            "트리트먼트": ["트리트먼트", "トリートメント", "treatment"],
            "선크림": ["선크림", "日焼け止め", "sunscreen", "spf"],
            "립밤": ["립밤", "リップ", "lip"],
            "아이크림": ["아이크림", "アイクリーム", "eye cream"],
            "미스트": ["미스트", "ミスト", "mist"],
            "오일": ["오일", "オイル", "oil"],
            "젤": ["젤", "ジェル", "gel"],
            "폼": ["폼", "フォーム", "foam"],
            "세트": ["세트", "セット", "set", "キット"],
            "기타": []
        }
        
        for product_type, keywords in product_types.items():
            if product_type == "기타":
                continue
            for keyword in keywords:
                if keyword in product_name_lower:
                    return product_type
        
        return "기타"
    
    def _extract_product_keywords(self, product_name: str) -> List[str]:
        """상품명에서 키워드 추출"""
        keywords = []
        
        # 주요 키워드 패턴
        keyword_patterns = [
            r'[A-Z][a-z]+',  # 대문자로 시작하는 단어 (브랜드명 등)
            r'[가-힣]+',  # 한글 단어
            r'[ひらがなカタカナ]+',  # 일본어
        ]
        
        # 상품명에서 의미있는 단어 추출
        words = re.findall(r'\b\w+\b', product_name, re.UNICODE)
        for word in words:
            if len(word) >= 2:  # 최소 2자 이상
                keywords.append(word)
        
        return keywords[:10]  # 최대 10개
    
    def _extract_shop_coupons(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Shop 쿠폰 정보 추출"""
        coupons = []
        
        # 쿠폰 요소 찾기
        coupon_elements = soup.select('.coupon-item, .discount-coupon')
        
        for elem in coupon_elements:
            coupon = {
                "discount_rate": 0,
                "min_amount": 0,
                "valid_until": None
            }
            
            # 할인율
            discount_text = elem.get_text()
            discount_match = re.search(r'(\d+)%', discount_text)
            if discount_match:
                coupon["discount_rate"] = int(discount_match.group(1))
            
            # 최소 금액
            amount_match = re.search(r'(\d+)[,円]以上', discount_text)
            if amount_match:
                coupon["min_amount"] = int(amount_match.group(1))
            
            if coupon["discount_rate"] > 0:
                coupons.append(coupon)
        
        return coupons
    
    def get_statistics(self) -> Dict[str, Any]:
        """크롤링 통계 조회"""
        return self.db.get_crawling_statistics()