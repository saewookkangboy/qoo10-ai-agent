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
    
    # 일본어-한국어 텍스트 매핑 딕셔너리
    JP_KR_MAPPING = {
        # 가격 관련
        "商品価格": "상품가격",
        "価格": "가격",
        "定価": "정가",
        "元の価格": "원래가격",
        "元価格": "원가격",
        "販売価格": "판매가격",
        "セール価格": "세일가격",
        "割引価格": "할인가격",
        "円": "엔",
        
        # 배송 관련
        "送料": "배송비",
        "送料無料": "무료배송",
        "配送料": "배송료",
        "配送": "배송",
        "配送無料": "무료배송",
        "条件付無料": "조건부무료",
        "以上購入": "이상구매",
        "以上購入の際": "이상구매시",
        "購入": "구매",
        
        # 리뷰 관련
        "レビュー": "리뷰",
        "評価": "평가",
        "コメント": "코멘트",
        "口コミ": "구전",
        "星": "별",
        "評価数": "평가수",
        
        # 쿠폰/할인 관련
        "クーポン": "쿠폰",
        "割引": "할인",
        "クーポン割引": "쿠폰할인",
        "ショップお気に入り割引": "샵즐겨찾기할인",
        "お気に入り登録": "즐겨찾기등록",
        "プラス": "플러스",
        "最大": "최대",
        "off": "오프",
        "OFF": "오프",
        
        # Qポイント 관련
        "Qポイント": "Q포인트",
        "ポイント": "포인트",
        "Qポイント獲得": "Q포인트획득",
        "Qポイント獲得方法": "Q포인트획득방법",
        "受取確認": "수령확인",
        "レビュー作成": "리뷰작성",
        "配送完了": "배송완료",
        "自動": "자동",
        
        # 반품 관련
        "返品": "반품",
        "返品無料": "무료반품",
        "無料返品": "무료반품",
        "返品無料サービス": "무료반품서비스",
        "返却": "반환",
        "返品可能": "반품가능",
        
        # 상품 관련
        "商品": "상품",
        "商品名": "상품명",
        "商品説明": "상품설명",
        "商品詳細": "상품상세",
        "商品情報": "상품정보",
        "商品画像": "상품이미지",
        "商品番号": "상품번호",
        "商品コード": "상품코드",
        
        # Shop 관련
        "ショップ": "샵",
        "ショップ名": "샵명",
        "ショップ情報": "샵정보",
        "ショップページ": "샵페이지",
        "フォロワー": "팔로워",
        "フォロー": "팔로우",
        "フォロー中": "팔로우중",
        
        # 카테고리/브랜드 관련
        "カテゴリ": "카테고리",
        "カテゴリー": "카테고리",
        "ブランド": "브랜드",
        "メーカー": "메이커",
        
        # 기타
        "全ての商品": "전체상품",
        "全て": "전체",
        "検索": "검색",
        "検索結果": "검색결과",
        "人気": "인기",
        "新着": "신규",
        "ランキング": "랭킹",
        "タイムセール": "타임세일",
        "タイムセール中": "타임세일중",
        "MOVE": "무브",
        "POWER": "파워",
        "パワー": "파워",
        "グレード": "그레이드",
        "byPower": "바이파워",
        "by Power": "바이파워",
    }
    
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
        self.timeout = 15.0  # 타임아웃 단축: 30초 -> 15초
        self.max_retries = 2  # 재시도 횟수 감소: 3 -> 2
        self.retry_delay_base = 1.0  # 재시도 지연 시간 단축: 2초 -> 1초
        
        # 데이터베이스 초기화
        self.db = db or CrawlerDatabase()
        
        # 프록시 설정 (환경 변수에서 읽기)
        self.proxies = self._load_proxies()
        
        # 일본어-한국어 패턴 생성
        self._init_jp_kr_patterns()
        
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
    
    def _init_jp_kr_patterns(self):
        """일본어-한국어 패턴 초기화"""
        # 일본어와 한국어를 모두 포함하는 정규식 패턴 생성
        self.jp_kr_patterns = {}
        
        # 가격 관련 패턴
        self.jp_kr_patterns["price"] = r'(商品価格|상품가격|가격|価格)[：:]?\s*'
        self.jp_kr_patterns["original_price"] = r'(定価|정가|元の価格|원래가격|元価格|원가격)[：:]?\s*'
        self.jp_kr_patterns["sale_price"] = r'(販売価格|판매가격|セール価格|세일가격|割引価格|할인가격)[：:]?\s*'
        
        # 배송 관련 패턴
        self.jp_kr_patterns["shipping"] = r'(送料|배송비|配送料|배송료|配送|배송)[：:]?\s*'
        self.jp_kr_patterns["free_shipping"] = r'(送料無料|무료배송|配送無料|無料配送|条件付無料|조건부무료)'
        self.jp_kr_patterns["shipping_threshold"] = r'(\d{1,3}(?:,\d{3})*)円\s*(以上購入|이상구매|以上購入の際|이상구매시)'
        
        # 리뷰 관련 패턴
        self.jp_kr_patterns["review"] = r'(レビュー|리뷰|評価|평가|コメント|코멘트|口コミ|구전)'
        self.jp_kr_patterns["review_count"] = r'(レビュー|리뷰|評価|평가|評価数|평가수).*?\((\d+)\)'
        
        # 쿠폰 관련 패턴
        self.jp_kr_patterns["coupon"] = r'(クーポン|쿠폰|割引|할인|クーポン割引|쿠폰할인)'
        self.jp_kr_patterns["coupon_discount"] = r'(プラス|플러스|最大|최대)\s*(\d+)(割引|할인|円|엔)'
        self.jp_kr_patterns["shop_favorite_coupon"] = r'(ショップお気に入り割引|샵즐겨찾기할인|お気に入り登録|즐겨찾기등록)'
        
        # Qポイント 관련 패턴
        self.jp_kr_patterns["qpoint"] = r'(Qポイント|Q포인트|ポイント|포인트)'
        self.jp_kr_patterns["qpoint_method"] = r'(Qポイント獲得方法|Q포인트획득방법|Qポイント獲得|Q포인트획득)'
        self.jp_kr_patterns["qpoint_receive"] = r'(受取確認|수령확인)[：:]?\s*最大(\d+)P'
        self.jp_kr_patterns["qpoint_review"] = r'(レビュー作成|리뷰작성)[：:]?\s*最大(\d+)P'
        self.jp_kr_patterns["qpoint_auto"] = r'(配送完了|배송완료).*?(自動|자동).*?(\d+)P'
        
        # 반품 관련 패턴
        self.jp_kr_patterns["return"] = r'(返品|반품|返却|반환)'
        self.jp_kr_patterns["free_return"] = r'(返品無料|무료반품|無料返品|返品無料サービス|무료반품서비스)'
        
        # Shop 관련 패턴
        self.jp_kr_patterns["shop"] = r'(ショップ|샵|ショップ名|샵명)'
        self.jp_kr_patterns["follower"] = r'(フォロワー|팔로워|フォロー|팔로우)'
        self.jp_kr_patterns["power"] = r'(POWER|パワー|파워)'
        
        # 상품 관련 패턴
        self.jp_kr_patterns["product"] = r'(商品|상품|商品名|상품명)'
        self.jp_kr_patterns["product_count"] = r'(全ての商品|전체상품|商品数|상품수).*?\((\d+)\)'
        
        # 카테고리/브랜드 관련 패턴
        self.jp_kr_patterns["category"] = r'(カテゴリ|카테고리|カテゴリー)'
        self.jp_kr_patterns["brand"] = r'(ブランド|브랜드|メーカー|메이커)'
    
    def _translate_jp_to_kr(self, text: str) -> str:
        """일본어 텍스트를 한국어로 번역 (매핑 기반)"""
        if not text:
            return text
        
        translated = text
        for jp, kr in self.JP_KR_MAPPING.items():
            translated = translated.replace(jp, kr)
        
        return translated
    
    def _create_jp_kr_regex(self, jp_text: str, kr_text: str = None) -> str:
        """일본어와 한국어를 모두 포함하는 정규식 패턴 생성"""
        if kr_text is None:
            kr_text = self._translate_jp_to_kr(jp_text)
        
        # 특수 문자 이스케이프
        jp_escaped = re.escape(jp_text)
        kr_escaped = re.escape(kr_text)
        
        return f'({jp_escaped}|{kr_escaped})'
    
    def _get_user_agent(self) -> str:
        """최적의 User-Agent 선택 (학습 데이터 기반) - 최적화: 캐싱"""
        # 캐시된 User-Agent가 있으면 재사용
        if self.current_user_agent:
            return self.current_user_agent
        
        # 데이터베이스 조회는 최소화 (성능 최적화)
        try:
            best_ua = self.db.get_best_user_agent()
            if best_ua:
                self.current_user_agent = best_ua
                return best_ua
        except:
            # DB 조회 실패 시 무시하고 계속 진행
            pass
        
        # 없으면 랜덤 선택
        self.current_user_agent = random.choice(self.USER_AGENTS)
        return self.current_user_agent
    
    def _get_proxy(self) -> Optional[Dict[str, str]]:
        """최적의 프록시 선택 (학습 데이터 기반) - 최적화: 캐싱"""
        if not self.proxies:
            return None
        
        # 캐시된 프록시가 있으면 재사용
        if self.current_proxy:
            return {"http://": self.current_proxy, "https://": self.current_proxy}
        
        # 데이터베이스 조회는 최소화 (성능 최적화)
        try:
            best_proxy = self.db.get_best_proxy()
            if best_proxy:
                self.current_proxy = best_proxy
                return {"http://": self.current_proxy, "https://": self.current_proxy}
        except:
            # DB 조회 실패 시 무시하고 계속 진행
            pass
        
        # 없으면 랜덤 선택
        self.current_proxy = random.choice(self.proxies)
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
    
    async def _random_delay(self, min_seconds: float = 0.5, max_seconds: float = 1.5):
        """랜덤 지연 시간 (인간처럼 보이게) - 최적화: 지연 시간 단축"""
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
        
        # 지연 시간 추가 (너무 빠른 요청 방지) - 최적화: 지연 시간 단축
        if retry_count == 0:
            await self._random_delay(0.5, 1.5)  # 1-3초 -> 0.5-1.5초
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
            # 페이지 구조 추출은 선택적으로 수행 (성능 최적화)
            page_structure = None
            try:
                page_structure = self._extract_page_structure(soup)
            except Exception:
                # 페이지 구조 추출 실패해도 계속 진행
                pass
            
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
                "shipping_info": self._extract_shipping_info(soup),
                "is_move_product": self._extract_move_product(soup),  # MOVE 상품 여부 추가
                "qpoint_info": self._extract_qpoint_info(soup),  # Qポイント 정보 추가
                "coupon_info": self._extract_coupon_info(soup),  # 쿠폰 상세 정보 추가
                "page_structure": page_structure  # 페이지 구조 및 모든 div class 정보 추가
            }
            
            # 데이터베이스 저장은 비동기로 처리 (성능 최적화)
            # 저장 실패해도 분석은 계속 진행
            try:
                self.db.save_crawled_product(product_data)
            except:
                pass  # 저장 실패해도 무시
            
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
        AI 학습 기반 데이터 추출 - 최적화: DB 조회 최소화
        
        Args:
            selector_type: 선택자 타입 ('product_name', 'price', etc.)
            soup: BeautifulSoup 객체
            default_selectors: 기본 선택자 목록
            extract_func: 추출 함수
            
        Returns:
            추출된 데이터
        """
        # 성능 최적화: 기본 선택자를 먼저 시도 (DB 조회 없이)
        for selector in default_selectors[:5]:  # 상위 5개만 먼저 시도
            try:
                result = extract_func(soup, selector)
                if result and result != "상품명 없음" and result != "":
                    # 성공 기록은 비동기로 처리 (성능 최적화)
                    try:
                        self.db.record_selector_performance(
                            selector_type=selector_type,
                            selector=selector,
                            success=True,
                            data_quality=1.0 if result else 0.0
                        )
                    except:
                        pass  # DB 기록 실패해도 무시
                    return result
            except Exception:
                continue
        
        # 기본 선택자로 실패한 경우에만 DB 조회 (성능 최적화)
        try:
            best_selectors = self.db.get_best_selectors(selector_type, limit=5)  # limit 감소: 10 -> 5
            if best_selectors:
                for selector_info in best_selectors:
                    selector = selector_info.get("selector")
                    if selector and selector not in default_selectors:
                        try:
                            result = extract_func(soup, selector)
                            if result and result != "상품명 없음" and result != "":
                                return result
                        except:
                            continue
        except:
            # DB 조회 실패 시 무시하고 계속 진행
            pass
        
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
        """상품명 추출 (AI 학습 기반) - 실제 Qoo10 페이지 구조에 맞게 개선 및 정확도 향상"""
        default_selectors = [
            'h1.product-name',
            'h1[itemprop="name"]',
            '.product_name',
            'h1',
            '#goods_name',
            '.goods_name',
            '[data-product-name]',  # data 속성에서 추출
            '.goods_title',  # Qoo10 특정 클래스
            'title'  # fallback으로 title 태그도 확인
        ]
        
        def extract_func(soup_obj, selector):
            if selector:
                if selector == 'title':
                    # title 태그에서 상품명 추출 (Qoo10 형식: "상품명 | Qoo10")
                    title_elem = soup_obj.find('title')
                    if title_elem:
                        title_text = title_elem.get_text(strip=True)
                        # "|" 또는 "｜"로 분리하여 첫 번째 부분 추출
                        if '|' in title_text:
                            name = title_text.split('|')[0].strip()
                            # "Qoo10" 제거
                            name = name.replace('Qoo10', '').replace('[Qoo10]', '').strip()
                            if name and len(name) > 3:
                                return name
                        elif '｜' in title_text:
                            name = title_text.split('｜')[0].strip()
                            name = name.replace('Qoo10', '').replace('[Qoo10]', '').strip()
                            if name and len(name) > 3:
                                return name
                        # "Qoo10"이 포함된 경우 제거
                        name = title_text.replace('Qoo10', '').replace('[Qoo10]', '').strip()
                        if name and len(name) > 3:
                            return name
                elif selector == '[data-product-name]':
                    # data 속성에서 추출
                    elem = soup_obj.select_one(selector)
                    if elem:
                        name = elem.get('data-product-name') or elem.get_text(strip=True)
                        if name and len(name) > 3:
                            return name
                else:
                    elem = soup_obj.select_one(selector)
                    if elem:
                        text = elem.get_text(strip=True)
                        # 의미있는 텍스트인지 확인 (너무 짧거나 일반적인 텍스트 제외)
                        if text and text != "" and len(text) > 3:
                            # "Qoo10", "ホーム" 같은 일반적인 텍스트 제외
                            if text not in ['Qoo10', 'ホーム', 'Home', 'トップ', 'Top', '商品名']:
                                return text
            
            # 추가 시도: 페이지 내에서 가장 큰 h1 태그 찾기
            h1_tags = soup_obj.find_all('h1')
            for h1 in h1_tags:
                text = h1.get_text(strip=True)
                # 상품명은 보통 10자 이상이고, 일반적인 텍스트가 아님
                if text and len(text) > 10:
                    # 일반적인 텍스트 제외
                    if text not in ['Qoo10', 'ホーム', 'Home', 'トップ', 'Top', '商品名', '商品詳細']:
                        return text
            
            return "상품명 없음"
        
        result = self._extract_with_learning(
            "product_name",
            soup,
            default_selectors,
            extract_func
        )
        
        # 결과 검증 및 정제
        if result and result != "상품명 없음":
            # 불필요한 공백 제거
            result = ' '.join(result.split())
            # 특수 문자 정제 (필요시)
            result = result.strip()
        
        return result
    
    def _extract_category(self, soup: BeautifulSoup) -> Optional[str]:
        """카테고리 추출 (AI 학습 기반) - 실제 Qoo10 페이지 구조에 맞게 개선"""
        default_selectors = [
            'meta[property="product:category"]',
            'nav.breadcrumb a',
            'ol.breadcrumb a',
            '.category',
            'nav[class*="breadcrumb"] a',
            'ol[class*="breadcrumb"] a',
            'a[href*="/category/"]',
            'a[href*="/cat/"]'
        ]
        
        def extract_func(soup_obj, selector):
            if selector:
                if selector.startswith('meta'):
                    elem = soup_obj.find('meta', {'property': 'product:category'})
                    if elem:
                        return elem.get('content')
                else:
                    elems = soup_obj.select(selector)
                    if elems:
                        # 마지막 링크가 보통 카테고리
                        for elem in reversed(elems):
                            text = elem.get_text(strip=True)
                            href = elem.get('href', '')
                            # URL에서 카테고리 추출
                            if '/category/' in href or '/cat/' in href:
                                category_match = re.search(r'/(?:category|cat)/([^/]+)', href)
                                if category_match:
                                    return category_match.group(1)
                            # 텍스트가 의미있는 경우 (일본어 텍스트를 한국어로 번역)
                            if text and len(text) > 2 and text not in ['ホーム', 'Home', 'トップ', 'Top']:
                                # 일본어 텍스트를 한국어로 번역
                                translated_text = self._translate_jp_to_kr(text)
                                return translated_text
            
            # 기본 방법: 메타 태그
            category_elem = soup_obj.find('meta', {'property': 'product:category'})
            if category_elem:
                return category_elem.get('content')
            
            # 브레드크럼에서 추출
            breadcrumb = soup_obj.find('nav', class_=re.compile(r'breadcrumb', re.I)) or \
                        soup_obj.find('ol', class_=re.compile(r'breadcrumb', re.I))
            if breadcrumb:
                links = breadcrumb.find_all('a')
                if len(links) > 1:
                    # 마지막 링크가 카테고리일 가능성이 높음
                    last_link = links[-1]
                    text = last_link.get_text(strip=True)
                    if text and len(text) > 2:
                        return text
            
            # URL에서 카테고리 추출 시도
            category_links = soup_obj.find_all('a', href=re.compile(r'/category/|/cat/'))
            if category_links:
                for link in category_links:
                    href = link.get('href', '')
                    match = re.search(r'/(?:category|cat)/([^/]+)', href)
                    if match:
                        return match.group(1)
            
            return None
        
        return self._extract_with_learning(
            "category",
            soup,
            default_selectors,
            extract_func
        )
    
    def _extract_brand(self, soup: BeautifulSoup) -> Optional[str]:
        """브랜드 추출 (일본어-한국어 모두 지원)"""
        brand_elem = soup.find('meta', {'property': 'product:brand'})
        if brand_elem:
            return brand_elem.get('content')
        
        # 페이지에서 브랜드 정보 찾기 (일본어-한국어 모두 지원)
        brand_pattern = self._create_jp_kr_regex("ブランド", "브랜드")
        brand_text = soup.find(string=re.compile(f'{brand_pattern}|Brand', re.I))
        if brand_text:
            parent = brand_text.find_parent()
            if parent:
                brand_value = parent.get_text(strip=True).split(':')[-1].strip()
                # 일본어 텍스트를 한국어로 번역
                brand_value = self._translate_jp_to_kr(brand_value)
                return brand_value
        
        return None
    
    def _extract_price(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """가격 정보 추출 (AI 학습 기반) - 실제 Qoo10 페이지 구조에 맞게 개선 및 정확도 향상"""
        price_data = {
            "original_price": None,
            "sale_price": None,
            "discount_rate": 0,
            "coupon_discount": None,  # 쿠폰 할인 정보 추가
            "qpoint_info": None  # Qポイント 정보 추가
        }
        
        # 판매가 추출 (다양한 선택자 시도, 우선순위 순서)
        sale_price_selectors = [
            '.price',
            '.product-price',
            '[itemprop="price"]',
            '.sale_price',
            '#price',
            '.goods_price',
            'td.price',
            'span.price',
            'div.price',
            '[class*="price"]',  # price가 포함된 클래스
            '[data-price]'  # data 속성
        ]
        
        # "商品価格" 또는 "상품가격" 텍스트를 포함하는 요소 찾기 (일본어-한국어 모두 지원)
        price_pattern = self._create_jp_kr_regex("商品価格", "상품가격")
        price_section = soup.find(string=re.compile(f'{price_pattern}[：:]|가격[：:]|価格[：:]', re.I))
        if price_section:
            parent = price_section.find_parent()
            if parent:
                # 부모 요소에서 가격 숫자 찾기
                price_text = parent.get_text()
                # "商品価格: 4,562円" 또는 "상품가격: 4,562円" 같은 패턴에서 추출
                price_match = re.search(f'{price_pattern}[：:]\s*(\d{{1,3}}(?:,\d{{3}})*)円', price_text)
                if price_match:
                    price = self._parse_price(price_match.group(1))
                    if price:
                        price_data["sale_price"] = price
                else:
                    # 일반적인 숫자 추출
                    price = self._parse_price(price_text)
                    if price:
                        price_data["sale_price"] = price
        
        # 선택자를 통한 가격 추출
        for selector in sale_price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = self._parse_price(price_text)
                if price and not price_data["sale_price"]:
                    price_data["sale_price"] = price
                    break
        
        # 정가 찾기 (취소선이 있는 가격) - 더 정확한 패턴 매칭
        # "~~29,400円~~" 같은 패턴 찾기
        price_text_all = soup.get_text()
        
        # 패턴 1: ~~정가~~ 형식
        strikethrough_pattern = re.search(r'~~(\d{1,3}(?:,\d{3})*)円~~', price_text_all)
        if strikethrough_pattern:
            original_price = self._parse_price(strikethrough_pattern.group(1))
            if original_price:
                price_data["original_price"] = original_price
        
        # 패턴 2: HTML 태그에서 찾기
        if not price_data["original_price"]:
            original_price_patterns = [
                soup.find(class_=re.compile(r'original|정가|定価|元の価格|元価格', re.I)),
                soup.find('del'),
                soup.find('s'),
                soup.find(string=re.compile(r'~~\d+円|定価.*\d+円'))
            ]
            
            for pattern in original_price_patterns:
                if pattern:
                    if hasattr(pattern, 'get_text'):
                        original_text = pattern.get_text(strip=True)
                    else:
                        # string 객체인 경우
                        parent = pattern.find_parent()
                        if parent:
                            original_text = parent.get_text(strip=True)
                        else:
                            original_text = str(pattern)
                    
                    original_price = self._parse_price(original_text)
                    if original_price and original_price > 0:
                        # 판매가보다 높은지 확인 (정가는 보통 판매가보다 높음)
                        if not price_data["sale_price"] or original_price > price_data["sale_price"]:
                            price_data["original_price"] = original_price
                            break
        
        # 쿠폰 할인 정보 추출 - 더 정확한 패턴 매칭 (일본어-한국어 모두 지원)
        coupon_pattern = self._create_jp_kr_regex("クーポン割引", "쿠폰할인")
        discount_pattern = self._create_jp_kr_regex("割引", "할인")
        coupon_section = soup.find(string=re.compile(f'{coupon_pattern}|{discount_pattern}', re.I))
        if coupon_section:
            parent = coupon_section.find_parent()
            if parent:
                coupon_text = parent.get_text()
                # "プラス(\d+)割引" 또는 "플러스(\d+)할인" 또는 "最大(\d+)円" 또는 "최대(\d+)엔" 같은 패턴 찾기
                plus_pattern = self._create_jp_kr_regex("プラス", "플러스")
                max_pattern = self._create_jp_kr_regex("最大", "최대")
                coupon_match = re.search(f'{plus_pattern}(\d+){discount_pattern}|{max_pattern}(\d+)円|(\d+)円{discount_pattern}', coupon_text)
                if coupon_match:
                    discount = coupon_match.group(1) or coupon_match.group(2) or coupon_match.group(3)
                    if discount and discount.isdigit():
                        price_data["coupon_discount"] = int(discount)
        
        # 추가 시도: "クーポン割引_(0)_" 또는 "쿠폰할인_(0)_" 같은 패턴도 확인
        if not price_data["coupon_discount"]:
            coupon_text_all = soup.get_text()
            coupon_pattern = self._create_jp_kr_regex("クーポン割引", "쿠폰할인")
            coupon_match = re.search(f'{coupon_pattern}[_\s]*\((\d+)\)', coupon_text_all)
            if coupon_match:
                discount = coupon_match.group(1)
                if discount.isdigit():
                    price_data["coupon_discount"] = int(discount)
        
        # Qポイント 정보 추출 (간단한 버전, 상세 정보는 _extract_qpoint_info에서 추출)
        # 일본어-한국어 모두 지원
        qpoint_pattern = self._create_jp_kr_regex("Qポイント", "Q포인트")
        qpoint_get_pattern = self._create_jp_kr_regex("Qポイント獲得", "Q포인트획득")
        qpoint_section = soup.find(string=re.compile(f'{qpoint_pattern}|{qpoint_get_pattern}'))
        if qpoint_section:
            parent = qpoint_section.find_parent()
            if parent:
                qpoint_text = parent.get_text()
                max_pattern = self._create_jp_kr_regex("最大", "최대")
                qpoint_match = re.search(f'{max_pattern}(\d+)P', qpoint_text)
                if qpoint_match:
                    price_data["qpoint_info"] = int(qpoint_match.group(1))
        
        # 할인율 계산 (정확도 향상)
        if price_data["original_price"] and price_data["sale_price"]:
            if price_data["original_price"] > price_data["sale_price"]:
                discount = price_data["original_price"] - price_data["sale_price"]
                price_data["discount_rate"] = int((discount / price_data["original_price"]) * 100)
            else:
                # 정가가 판매가보다 낮으면 잘못된 데이터
                price_data["original_price"] = None
        
        # 데이터 검증: 판매가가 없으면 오류
        if not price_data["sale_price"]:
            # 최후의 시도: 페이지 전체에서 가격 패턴 찾기
            all_text = soup.get_text()
            price_patterns = [
                r'(\d{1,3}(?:,\d{3})*)円',  # 일반적인 가격 패턴
                r'価格[：:]\s*(\d{1,3}(?:,\d{3})*)円',
                r'¥\s*(\d{1,3}(?:,\d{3})*)'
            ]
            for pattern in price_patterns:
                matches = re.findall(pattern, all_text)
                if matches:
                    # 가장 큰 숫자를 판매가로 추정 (일반적으로 상품 가격은 큰 숫자)
                    prices = [self._parse_price(m) for m in matches if self._parse_price(m)]
                    if prices:
                        # 합리적인 가격 범위 (100엔 ~ 1,000,000엔)
                        valid_prices = [p for p in prices if 100 <= p <= 1000000]
                        if valid_prices:
                            price_data["sale_price"] = max(valid_prices)
                            break
        
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
        """이미지 정보 추출 - 실제 Qoo10 페이지 구조에 맞게 개선"""
        images = {
            "thumbnail": None,
            "detail_images": []
        }
        
        # 썸네일 이미지 (다양한 선택자 시도)
        thumbnail_selectors = [
            'img.product-thumbnail',
            'img[itemprop="image"]',
            '.product-image img',
            'img.main-image',
            '#goods_img img',
            '.goods_img img',
            '.thumbnail img',
            'img[class*="thumbnail"]',
            'img[class*="main"]',
            'img[class*="product"]'
        ]
        
        for selector in thumbnail_selectors:
            img = soup.select_one(selector)
            if img:
                src = img.get('src') or img.get('data-src') or img.get('data-original')
                if src:
                    # 상대 경로를 절대 경로로 변환
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = 'https://www.qoo10.jp' + src
                    images["thumbnail"] = src
                    break
        
        # 상세 이미지 (다양한 선택자 시도)
        detail_img_selectors = [
            '.product-detail img',
            '.detail-images img',
            '.product-images img',
            '#goods_detail img',
            '.goods_detail img',
            'div[class*="detail"] img',
            'div[class*="description"] img',
            'div[class*="content"] img'
        ]
        
        seen_images = set()
        if images["thumbnail"]:
            seen_images.add(images["thumbnail"])
        
        for selector in detail_img_selectors:
            imgs = soup.select(selector)
            for img in imgs:
                src = img.get('src') or img.get('data-src') or img.get('data-original')
                if src:
                    # 상대 경로를 절대 경로로 변환
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = 'https://www.qoo10.jp' + src
                    
                    # 중복 제거 및 유효한 이미지 URL인지 확인
                    if src not in seen_images and ('http' in src or src.startswith('//')):
                        # 작은 아이콘이나 배너 이미지 제외
                        if not any(exclude in src.lower() for exclude in ['icon', 'logo', 'banner', 'button']):
                            images["detail_images"].append(src)
                            seen_images.add(src)
        
        return images
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """상품 설명 추출 (AI 학습 기반) - 실제 Qoo10 페이지 구조에 맞게 개선 및 정확도 향상"""
        default_selectors = [
            '.product-description',
            '[itemprop="description"]',
            '.description',
            '.product-detail',
            '#goods_detail',
            '.goods_detail',
            '.detail_description',
            'div[class*="detail"]',
            'div[class*="description"]',
            '[id*="detail"]',  # id에 detail이 포함된 요소
            '[id*="description"]'  # id에 description이 포함된 요소
        ]
        
        def extract_func(soup_obj, selector):
            if selector:
                desc_elem = soup_obj.select_one(selector)
                if desc_elem:
                    # HTML 태그 제거하고 텍스트만 추출
                    text = desc_elem.get_text(separator='\n', strip=True)
                    # 의미있는 설명인지 확인 (너무 짧거나 일반적인 텍스트 제외)
                    if text and len(text) > 50:
                        # "상품 설명", "商品説明" 같은 제목 제거
                        text = re.sub(r'^(商品説明|상품\s*설명|Description)[：:]\s*', '', text, flags=re.I)
                        if len(text.strip()) > 50:
                            return text.strip()
            
            # 추가 시도: 메타 description 태그 확인
            meta_desc = soup_obj.find('meta', {'name': 'description'})
            if meta_desc:
                desc_content = meta_desc.get('content', '')
                if desc_content and len(desc_content) > 50:
                    return desc_content
            
            # JSON-LD 스키마에서 설명 추출
            json_ld_scripts = soup_obj.find_all('script', {'type': 'application/ld+json'})
            for script in json_ld_scripts:
                try:
                    import json
                    data = json.loads(script.string)
                    # 중첩된 구조 처리
                    if isinstance(data, dict):
                        if 'description' in data:
                            desc = data['description']
                            if isinstance(desc, str) and len(desc) > 50:
                                return desc
                        # @graph 구조 처리
                        if '@graph' in data:
                            for item in data['@graph']:
                                if isinstance(item, dict) and 'description' in item:
                                    desc = item['description']
                                    if isinstance(desc, str) and len(desc) > 50:
                                        return desc
                except (json.JSONDecodeError, TypeError, AttributeError):
                    continue
            
            # 최후의 시도: 페이지에서 긴 텍스트 블록 찾기
            # 상품명 다음에 오는 긴 텍스트가 설명일 가능성이 높음
            all_divs = soup_obj.find_all('div')
            for div in all_divs:
                text = div.get_text(separator=' ', strip=True)
                # 100자 이상이고, 상품명이나 일반적인 텍스트가 아닌 경우
                if len(text) >= 100:
                    # 일반적인 텍스트 제외
                    if not any(exclude in text[:50] for exclude in ['ホーム', 'Home', 'トップ', 'Top', 'メニュー', 'Menu']):
                        return text[:2000]  # 최대 2000자까지만
            
            return ""
        
        result = self._extract_with_learning(
            "description",
            soup,
            default_selectors,
            extract_func
        )
        
        # 결과 정제
        if result:
            # HTML 태그 제거 (혹시 남아있는 경우)
            result = re.sub(r'<[^>]+>', '', result)
            # 연속된 공백 정리
            result = ' '.join(result.split())
            # 최대 길이 제한
            if len(result) > 5000:
                result = result[:5000] + "..."
        
        return result
    
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
        """리뷰 정보 추출 - 실제 Qoo10 페이지 구조에 맞게 개선 및 정확도 향상"""
        reviews_data = {
            "rating": 0.0,
            "review_count": 0,
            "reviews": []
        }
        
        # 평점 추출 (다양한 패턴 시도, 우선순위 순서)
        rating_patterns = [
            ('meta', {'itemprop': 'ratingValue'}),
            ('meta', {'property': 'product:ratingValue'}),
            ('span', {'class': re.compile(r'rating|star|score', re.I)}),
            ('div', {'class': re.compile(r'rating|star|score', re.I)}),
        ]
        
        for tag, attrs in rating_patterns:
            rating_elem = soup.find(tag, attrs)
            if rating_elem:
                rating_text = rating_elem.get('content') or rating_elem.get_text(strip=True)
                try:
                    # "4.8(150)" 같은 형식에서 평점 추출
                    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                    if rating_match:
                        rating_value = float(rating_match.group(1))
                        # 합리적인 범위 확인 (0.0 ~ 5.0)
                        if 0.0 <= rating_value <= 5.0:
                            reviews_data["rating"] = rating_value
                            break
                except (ValueError, AttributeError):
                    pass
        
        # 텍스트에서 평점 패턴 찾기 (예: "4.6(184)")
        if reviews_data["rating"] == 0.0:
            rating_text_pattern = re.search(r'(\d+\.?\d*)\s*\((\d+)\)', soup.get_text())
            if rating_text_pattern:
                try:
                    rating_value = float(rating_text_pattern.group(1))
                    if 0.0 <= rating_value <= 5.0:
                        reviews_data["rating"] = rating_value
                        # 리뷰 수도 함께 추출
                        review_count = int(rating_text_pattern.group(2))
                        reviews_data["review_count"] = review_count
                except (ValueError, AttributeError):
                    pass
        
        # 리뷰 수 추출 (다양한 패턴 시도, 정확도 향상) - 일본어-한국어 모두 지원
        if reviews_data["review_count"] == 0:
            review_pattern = self._create_jp_kr_regex("レビュー", "리뷰")
            review_count_patterns = [
                ('meta', {'itemprop': 'reviewCount'}),
                ('meta', {'property': 'product:reviewCount'}),
                (None, {'string': re.compile(f'{review_pattern}.*\\((\\d+)\\)|review.*\\((\\d+)\\)', re.I)}),
            ]
            
            for tag, attrs in review_count_patterns:
                if tag:
                    review_count_elem = soup.find(tag, attrs)
                else:
                    # string 검색
                    review_count_elem = soup.find(string=attrs.get('string'))
                
                if review_count_elem:
                    if hasattr(review_count_elem, 'get'):
                        count_text = review_count_elem.get('content', '')
                    else:
                        # string 객체인 경우
                        count_text = str(review_count_elem)
                        # "4.8(150)" 같은 형식에서 리뷰 수 추출
                        count_match = re.search(r'\((\d+)\)', count_text)
                        if count_match:
                            count_value = int(count_match.group(1))
                            if count_value > 0:
                                reviews_data["review_count"] = count_value
                                break
                    
                    # 숫자 추출
                    numbers = re.findall(r'\d+', count_text)
                    if numbers:
                        count_value = int(numbers[0])
                        if count_value > 0:
                            reviews_data["review_count"] = count_value
                            break
        
        # 리뷰 텍스트 (최근 리뷰) - 다양한 선택자 시도
        review_selectors = [
            '.review-item',
            '.review-text',
            '[itemprop="reviewBody"]',
            '.review_content',
            '.review-body',
            'div[class*="review"]',
            'p[class*="review"]'
        ]
        
        seen_reviews = set()
        for selector in review_selectors:
            review_elements = soup.select(selector)
            for elem in review_elements[:20]:  # 최대 20개
                review_text = elem.get_text(strip=True)
                if review_text and len(review_text) > 10:  # 의미있는 리뷰인지 확인
                    # 중복 제거
                    if review_text not in seen_reviews:
                        reviews_data["reviews"].append(review_text)
                        seen_reviews.add(review_text)
                        if len(reviews_data["reviews"]) >= 10:  # 최대 10개
                            break
            if len(reviews_data["reviews"]) >= 10:
                break
        
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
        """배송 정보 추출 - 실제 Qoo10 페이지 구조에 맞게 개선"""
        shipping_info = {
            "shipping_fee": None,
            "shipping_method": None,
            "estimated_delivery": None,
            "free_shipping": False,  # 무료배송 여부
            "return_policy": None  # 반품 정책 정보
        }
        
        # 배송비 정보 찾기 (다양한 패턴 시도)
        shipping_patterns = [
            r'送料[：:]\s*(\d+)円',
            r'送料[：:]\s*無料',
            r'送料[：:]\s*FREE',
            r'配送料[：:]\s*(\d+)円',
            r'배송비[：:]\s*(\d+)円',
            r'Shipping[：:]\s*(\d+)円'
        ]
        
        # 배송 관련 텍스트 찾기 (일본어-한국어 모두 지원)
        shipping_pattern = self._create_jp_kr_regex("送料", "배송비")
        delivery_pattern = self._create_jp_kr_regex("配送", "배송")
        shipping_elem = soup.find(string=re.compile(f'{shipping_pattern}|{delivery_pattern}|Shipping', re.I))
        if shipping_elem:
            parent = shipping_elem.find_parent()
            if parent:
                shipping_text = parent.get_text(strip=True)
                
                # 무료배송 확인 (일본어-한국어 모두)
                free_shipping_pattern = self._create_jp_kr_regex("送料無料", "무료배송")
                if re.search(free_shipping_pattern, shipping_text) or 'FREE' in shipping_text.upper() or '無料' in shipping_text or '무료' in shipping_text:
                    shipping_info["free_shipping"] = True
                    shipping_info["shipping_fee"] = 0
                else:
                    # 숫자 추출
                    for pattern in shipping_patterns:
                        match = re.search(pattern, shipping_text)
                        if match:
                            if match.group(1):
                                shipping_info["shipping_fee"] = int(match.group(1))
                            break
                    
                    # 패턴 매칭 실패 시 숫자만 추출
                    if not shipping_info["shipping_fee"]:
                        numbers = re.findall(r'\d+', shipping_text)
                        if numbers:
                            shipping_info["shipping_fee"] = int(numbers[0])
        
        # 반품 정책 정보 추출 (일본어-한국어 모두 지원)
        return_pattern = self._create_jp_kr_regex("返品", "반품")
        return_elem = soup.find(string=re.compile(f'{return_pattern}|返却|Return', re.I))
        if return_elem:
            parent = return_elem.find_parent()
            if parent:
                return_text = parent.get_text(strip=True)
                # "返品無料" 또는 "무료반품" 또는 "返品無料サービス" 확인
                free_return_pattern = self._create_jp_kr_regex("返品無料", "무료반품")
                if re.search(free_return_pattern, return_text) or '無料返品' in return_text:
                    shipping_info["return_policy"] = "free_return"
                elif re.search(return_pattern, return_text):
                    shipping_info["return_policy"] = "return_available"
        
        return shipping_info
    
    def _extract_move_product(self, soup: BeautifulSoup) -> bool:
        """MOVE 상품 여부 추출 - 실제 Qoo10 페이지 구조에 맞게 개선"""
        # MOVE 관련 텍스트 찾기
        move_indicators = [
            soup.find(string=re.compile(r'MOVE|ムーブ', re.I)),
            soup.find('span', string=re.compile(r'MOVE|ムーブ', re.I)),
            soup.find('div', string=re.compile(r'MOVE|ムーブ', re.I)),
            soup.find('a', href=re.compile(r'/move/', re.I)),
        ]
        
        for indicator in move_indicators:
            if indicator:
                return True
        
        # URL에서 MOVE 확인
        move_link = soup.find('a', href=re.compile(r'/move/', re.I))
        if move_link:
            return True
        
        # 클래스명에서 MOVE 확인
        move_elem = soup.find(class_=re.compile(r'move', re.I))
        if move_elem:
            return True
        
        return False
    
    def _extract_qpoint_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Qポイント 정보 상세 추출 - 실제 Qoo10 페이지 구조에 맞게 개선"""
        qpoint_info = {
            "max_points": None,
            "receive_confirmation_points": None,
            "review_points": None,
            "auto_points": None
        }
        
        # Qポイント 섹션 찾기 (일본어-한국어 모두 지원)
        qpoint_method_pattern = self._create_jp_kr_regex("Qポイント獲得方法", "Q포인트획득방법")
        qpoint_get_pattern = self._create_jp_kr_regex("Qポイント獲得", "Q포인트획득")
        qpoint_pattern = self._create_jp_kr_regex("Qポイント", "Q포인트")
        qpoint_section = soup.find(string=re.compile(f'{qpoint_method_pattern}|{qpoint_get_pattern}|{qpoint_pattern}', re.I))
        if qpoint_section:
            parent = qpoint_section.find_parent()
            if parent:
                # 부모 요소의 모든 텍스트 추출
                qpoint_text = parent.get_text()
                
                # "受取確認: 最大1P" 또는 "수령확인: 최대1P" 패턴 찾기
                receive_pattern = self._create_jp_kr_regex("受取確認", "수령확인")
                max_pattern = self._create_jp_kr_regex("最大", "최대")
                receive_match = re.search(f'{receive_pattern}[：:]\s*{max_pattern}(\d+)P', qpoint_text)
                if receive_match:
                    qpoint_info["receive_confirmation_points"] = int(receive_match.group(1))
                
                # "レビュー作成: 最大20P" 또는 "리뷰작성: 최대20P" 패턴 찾기
                review_create_pattern = self._create_jp_kr_regex("レビュー作成", "리뷰작성")
                review_match = re.search(f'{review_create_pattern}[：:]\s*{max_pattern}(\d+)P', qpoint_text)
                if review_match:
                    qpoint_info["review_points"] = int(review_match.group(1))
                
                # "最大(\d+)P" 또는 "최대(\d+)P" 패턴 찾기 (전체 최대 포인트)
                max_pattern = self._create_jp_kr_regex("最大", "최대")
                max_match = re.search(f'{max_pattern}(\d+)P', qpoint_text)
                if max_match:
                    qpoint_info["max_points"] = int(max_match.group(1))
                
                # "配送完了.*自動.*(\d+)P" 또는 "배송완료.*자동.*(\d+)P" 패턴 찾기 (자동 포인트)
                delivery_complete_pattern = self._create_jp_kr_regex("配送完了", "배송완료")
                auto_pattern = self._create_jp_kr_regex("自動", "자동")
                auto_match = re.search(f'{delivery_complete_pattern}.*{auto_pattern}.*(\d+)P', qpoint_text)
                if auto_match:
                    qpoint_info["auto_points"] = int(auto_match.group(1))
        
        return qpoint_info
    
    def _extract_coupon_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """쿠폰 상세 정보 추출 - 실제 Qoo10 페이지 구조에 맞게 개선"""
        coupon_info = {
            "has_coupon": False,
            "coupon_discount": None,
            "coupon_type": None,  # "shop_favorite", "password", "auto" 등
            "max_discount": None,
            "coupon_text": None
        }
        
        # 쿠폰 섹션 찾기 (일본어-한국어 모두 지원)
        coupon_discount_pattern = self._create_jp_kr_regex("クーポン割引", "쿠폰할인")
        coupon_pattern = self._create_jp_kr_regex("クーポン", "쿠폰")
        discount_pattern = self._create_jp_kr_regex("割引", "할인")
        shop_favorite_pattern = self._create_jp_kr_regex("ショップお気に入り割引", "샵즐겨찾기할인")
        coupon_section = soup.find(string=re.compile(f'{coupon_discount_pattern}|{coupon_pattern}|{discount_pattern}|{shop_favorite_pattern}', re.I))
        if coupon_section:
            parent = coupon_section.find_parent()
            if parent:
                coupon_info["has_coupon"] = True
                coupon_text = parent.get_text()
                coupon_info["coupon_text"] = coupon_text
                
                # "プラス(\d+)割引" 또는 "플러스(\d+)할인" 또는 "最大(\d+)円" 또는 "최대(\d+)엔" 패턴 찾기
                plus_pattern = self._create_jp_kr_regex("プラス", "플러스")
                max_pattern = self._create_jp_kr_regex("最大", "최대")
                discount_match = re.search(f'{plus_pattern}(\d+){discount_pattern}|{max_pattern}(\d+)円', coupon_text)
                if discount_match:
                    discount = discount_match.group(1) or discount_match.group(2)
                    coupon_info["max_discount"] = int(discount) if discount.isdigit() else None
                
                # 쿠폰 타입 확인 (일본어-한국어 모두 지원)
                shop_favorite_pattern = self._create_jp_kr_regex("ショップお気に入り", "샵즐겨찾기")
                favorite_register_pattern = self._create_jp_kr_regex("お気に入り登録", "즐겨찾기등록")
                if re.search(shop_favorite_pattern, coupon_text) or re.search(favorite_register_pattern, coupon_text):
                    coupon_info["coupon_type"] = "shop_favorite"
                elif 'パスワード' in coupon_text or 'password' in coupon_text.lower() or '비밀번호' in coupon_text:
                    coupon_info["coupon_type"] = "password"
                else:
                    coupon_info["coupon_type"] = "auto"
        
        return coupon_info
    
    def _extract_page_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        페이지 구조 및 모든 div class 추출 (최적화 버전)
        Qoo10 페이지의 모든 div class를 분석하여 각 요소의 의미를 파악
        """
        structure = {
            "all_div_classes": [],
            "class_frequency": {},
            "key_elements": {},
            "semantic_structure": {}
        }
        
        # 최적화: 한 번의 순회로 모든 정보 수집
        all_divs = soup.find_all('div', limit=1000)  # 최대 1000개로 제한
        
        # 주요 요소별로 분류할 패턴 정의
        key_patterns = {
            "product_info": ["product", "goods", "item", "detail", "info", "name", "title"],
            "price_info": ["price", "cost", "discount", "sale", "original", "prc"],
            "image_info": ["image", "img", "photo", "thumbnail", "thmb", "picture"],
            "review_info": ["review", "rating", "star", "comment", "evaluation"],
            "seller_info": ["shop", "seller", "store", "vendor", "merchant"],
            "shipping_info": ["shipping", "delivery", "ship", "配送", "送料"],
            "coupon_info": ["coupon", "discount", "割引", "クーポン"],
            "qpoint_info": ["qpoint", "point", "ポイント", "Qポイント"],
        }
        
        # 의미 있는 구조 요소를 위한 태그 매핑
        semantic_mapping = {
            "product_name_elements": ["name", "title", "goods_name", "product_name"],
            "price_elements": ["price", "prc", "cost"],
            "image_elements": ["image", "img", "photo", "thmb", "thumbnail"],
            "description_elements": ["description", "detail", "content"],
            "review_elements": ["review", "rating", "star", "comment"],
            "seller_elements": ["shop", "seller", "store"],
            "shipping_elements": ["shipping", "ship", "delivery", "配送", "送料"],
            "coupon_elements": ["coupon", "割引", "クーポン", "discount"],
            "qpoint_elements": ["qpoint", "point", "ポイント"],
        }
        
        # 한 번의 순회로 모든 정보 수집
        semantic_elements = {key: [] for key in semantic_mapping.keys()}
        seen_classes = set()
        
        for div in all_divs:
            classes = div.get('class', [])
            if not isinstance(classes, list):
                continue
                
            for cls in classes:
                if not cls or cls in seen_classes:
                    continue
                    
                seen_classes.add(cls)
                structure["all_div_classes"].append(cls)
                structure["class_frequency"][cls] = structure["class_frequency"].get(cls, 0) + 1
                
                cls_lower = cls.lower()
                
                # 주요 요소 분류
                for category, patterns in key_patterns.items():
                    if any(pattern in cls_lower for pattern in patterns):
                        if category not in structure["key_elements"]:
                            structure["key_elements"][category] = []
                        structure["key_elements"][category].append({
                            "class": cls,
                            "frequency": structure["class_frequency"][cls]
                        })
                
                # 의미 있는 구조 요소 분류
                for semantic_key, keywords in semantic_mapping.items():
                    if any(keyword in cls_lower for keyword in keywords):
                        semantic_elements[semantic_key].append(cls)
        
        # 추가로 특정 태그에서도 수집 (최적화: 제한된 선택자만 사용)
        quick_selectors = {
            "product_name_elements": ['h1', 'h2[class*="name"]'],
            "price_elements": ['span[class*="price"]', 'strong[class*="price"]'],
            "image_elements": ['img[class*="thumbnail"]'],
        }
        
        for semantic_key, selectors in quick_selectors.items():
            for selector in selectors[:2]:  # 최대 2개 선택자만 시도
                try:
                    elems = soup.select(selector, limit=10)  # 최대 10개만
                    for elem in elems:
                        classes = elem.get('class', [])
                        if classes:
                            for cls in classes:
                                if cls and cls not in seen_classes:
                                    semantic_elements[semantic_key].append(cls)
                                    seen_classes.add(cls)
                except:
                    continue  # 선택자 오류 무시
        
        # 중복 제거 및 빈도 계산
        for key in semantic_elements:
            class_counts = {}
            for cls in semantic_elements[key]:
                class_counts[cls] = class_counts.get(cls, 0) + 1
            semantic_elements[key] = [
                {"class": cls, "frequency": count}
                for cls, count in sorted(class_counts.items(), key=lambda x: x[1], reverse=True)[:20]  # 상위 20개만
            ]
        
        structure["semantic_structure"] = semantic_elements
        
        # 고유한 class 목록 정리 (최대 500개로 제한)
        structure["all_div_classes"] = sorted(list(set(structure["all_div_classes"])))[:500]
        
        return structure
    
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
        """Shop 이름 추출 - 실제 Qoo10 Shop 페이지 구조에 맞게 개선"""
        # 여러 가능한 선택자 시도
        selectors = [
            'h1.shop-name',
            'h1',
            '.shop-title',
            '[itemprop="name"]',
            '#shop_name',
            '.shop_name',
            'title'  # fallback으로 title 태그도 확인
        ]
        
        for selector in selectors:
            if selector == 'title':
                # title 태그에서 Shop 이름 추출 (Qoo10 형식: "Shop 이름 | Qoo10")
                title_elem = soup.find('title')
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    # "|" 또는 "｜"로 분리하여 첫 번째 부분 추출
                    if '|' in title_text:
                        return title_text.split('|')[0].strip()
                    elif '｜' in title_text:
                        return title_text.split('｜')[0].strip()
                    # "Qoo10"이 포함된 경우 제거
                    if 'Qoo10' in title_text:
                        return title_text.replace('Qoo10', '').strip()
                    return title_text
            else:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    if text and len(text) > 0 and text != "Shop 이름 없음":
                        # 의미있는 텍스트인지 확인 (너무 짧거나 일반적인 텍스트 제외)
                        if len(text) > 2 and text not in ['ホーム', 'Home', 'トップ', 'Top', 'Qoo10']:
                            return text
        
        return "Shop 이름 없음"
    
    def _extract_shop_level(self, soup: BeautifulSoup) -> Optional[str]:
        """Shop 레벨 추출 - 실제 Qoo10 Shop 페이지 구조에 맞게 개선 (일본어-한국어 모두 지원)"""
        # POWER 95% 같은 패턴 찾기 (우선 확인)
        power_pattern = self._create_jp_kr_regex("POWER", "파워")
        power_jp_pattern = self._create_jp_kr_regex("パワー", "파워")
        power_patterns = [
            f'{power_pattern}\\s*(\\d+)%',
            f'{power_jp_pattern}\\s*(\\d+)%',
            f'{power_pattern}\\s*(\\d+)',
            f'{power_jp_pattern}\\s*(\\d+)'
        ]
        
        for pattern in power_patterns:
            power_elem = soup.find(string=re.compile(pattern, re.I))
            if power_elem:
                # POWER 퍼센트 추출
                match = re.search(pattern, str(power_elem), re.I)
                if match:
                    power_percent = int(match.group(1))
                    if power_percent >= 90:
                        return "power"
                    elif power_percent >= 70:
                        return "excellent"
        
        # POWER, 우수 셀러, 일반 셀러 등 텍스트 찾기 (일본어-한국어 모두 지원)
        excellent_pattern = self._create_jp_kr_regex("우수", "우수")
        normal_pattern = self._create_jp_kr_regex("일반", "일반")
        level_pattern = f'{power_pattern}|{power_jp_pattern}|{excellent_pattern}|{normal_pattern}|excellent|normal|power'
        level_text = soup.find(string=re.compile(level_pattern, re.I))
        if level_text:
            text = str(level_text).lower()
            power_kr = self._translate_jp_to_kr("パワー").lower()
            if 'power' in text or 'パワー' in text or power_kr in text:
                return "power"
            elif 'excellent' in text or '우수' in text:
                return "excellent"
            elif 'normal' in text or '일반' in text:
                return "normal"
        
        # "byPower grade" 같은 패턴 찾기
        bypower_pattern = self._create_jp_kr_regex("byPower", "바이파워")
        power_grade = soup.find(string=re.compile(f'{bypower_pattern}\\s*grade|Power\\s*grade', re.I))
        if power_grade:
            return "power"
        
        return "unknown"
    
    def _extract_follower_count(self, soup: BeautifulSoup) -> int:
        """팔로워 수 추출 - 실제 Qoo10 Shop 페이지 구조에 맞게 개선"""
        # 팔로워 텍스트 찾기 (다양한 패턴 시도) - 일본어-한국어 모두 지원
        follower_pattern = self._create_jp_kr_regex("フォロワー", "팔로워")
        follower_patterns = [
            f'{follower_pattern}[_\\s]*(\\d{{1,3}}(?:,\\d{{3}})*)',
            f'{follower_pattern}[_\\s]*(\\d+)',
            r'follower[_\s]*(\d{1,3}(?:,\d{3})*)',
            r'follower[_\s]*(\d+)'
        ]
        
        # 패턴 매칭 시도
        for pattern in follower_patterns:
            follower_elem = soup.find(string=re.compile(pattern, re.I))
            if follower_elem:
                match = re.search(pattern, str(follower_elem), re.I)
                if match:
                    try:
                        # 쉼표 제거 후 숫자 변환
                        count_str = match.group(1).replace(',', '').replace('_', '')
                        return int(count_str)
                    except:
                        pass
        
        # 기본 방법: 팔로워 텍스트 찾기 (일본어-한국어 모두 지원)
        follower_pattern = self._create_jp_kr_regex("フォロワー", "팔로워")
        follower_text = soup.find(string=re.compile(f'{follower_pattern}|follower', re.I))
        if follower_text:
            parent = follower_text.find_parent()
            if parent:
                text = parent.get_text(strip=True)
                # "フォロワー_50,357_" 같은 형식에서 숫자 추출
                numbers = re.findall(r'[\d,]+', text.replace(',', '').replace('_', ''))
                if numbers:
                    try:
                        return int(numbers[0])
                    except:
                        pass
        
        return 0
    
    def _extract_product_count(self, soup: BeautifulSoup) -> int:
        """상품 수 추출 - 실제 Qoo10 Shop 페이지 구조에 맞게 개선"""
        # "全ての商品 (16)" 또는 "전체상품 (16)" 같은 패턴 찾기 (일본어-한국어 모두 지원)
        all_product_pattern = self._create_jp_kr_regex("全ての商品", "전체상품")
        product_pattern = self._create_jp_kr_regex("商品", "상품")
        product_count_pattern = self._create_jp_kr_regex("商品数", "상품수")
        product_patterns = [
            f'{all_product_pattern}\\s*\\((\\d+)\\)',
            f'{product_pattern}.*\\((\\d+)\\)',
            f'{all_product_pattern}[：:]\\s*(\\d+)',
            f'{product_count_pattern}[：:]\\s*(\\d+)'
        ]
        
        for pattern in product_patterns:
            product_text = soup.find(string=re.compile(pattern, re.I))
            if product_text:
                match = re.search(pattern, str(product_text), re.I)
                if match:
                    try:
                        return int(match.group(1))
                    except:
                        pass
        
        # 상품 리스트에서 개수 세기 (다양한 선택자 시도)
        product_selectors = [
            '.product-item',
            '.goods-item',
            '[data-goods-code]',
            'div[class*="product"]',
            'div[class*="goods"]',
            'div[class*="item"]',
            'li[class*="product"]',
            'li[class*="goods"]'
        ]
        
        seen_products = set()
        for selector in product_selectors:
            product_items = soup.select(selector)
            for item in product_items:
                # 상품명이나 가격이 있는지 확인하여 실제 상품인지 판단
                name = item.select_one('.product-name, .goods-name, h3, h4, [title]')
                price = item.select_one('.price, .goods-price, [class*="price"]')
                if name or price:
                    # 중복 제거를 위한 식별자 생성
                    item_id = item.get('data-goods-code') or item.get('id') or str(item)
                    if item_id not in seen_products:
                        seen_products.add(item_id)
        
        return len(seen_products) if seen_products else 0
    
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
        """Shop 상품 목록 추출 (실제 Qoo10 Shop 페이지 구조에 맞게 개선)"""
        products = []
        
        # 실제 Qoo10 Shop 페이지 구조: <div class="item">
        # 우선순위 1: .item 클래스 (가장 정확한 선택자)
        product_items = soup.select('div.item')
        
        # 우선순위 2: 다른 패턴 시도
        if not product_items:
            product_items = soup.select(
                '.product-item, .goods-item, [data-goods-code], '
                '.item_list li, .goods_list li, .product-list-item, '
                'div[class*="item"]'
            )
        
        # 우선순위 3: 리스트 형태의 상품 찾기
        if not product_items:
            product_items = soup.find_all('div', class_=re.compile(r'^item$|item\s', re.I))
        
        for item in product_items[:50]:  # 최대 50개까지
            product = {
                "product_name": "",
                "product_url": None,
                "thumbnail": None,
                "brand": None,
                "price": {"sale_price": None, "original_price": None, "discount_rate": 0},
                "shipping_info": {"shipping_fee": None, "free_shipping_threshold": None},
                "rating": 0.0,
                "review_count": 0,
                "product_type": None,
                "category": None,
                "keywords": []
            }
            
            # 1. 상품명 추출 - <a class="tt"> (실제 Qoo10 구조)
            name_elem = item.select_one('a.tt')
            if name_elem:
                product["product_name"] = name_elem.get_text(strip=True) or name_elem.get('title', '')
                product["product_url"] = name_elem.get('href', '')
                # 상대 URL을 절대 URL로 변환
                if product["product_url"] and product["product_url"].startswith('/'):
                    product["product_url"] = 'https://www.qoo10.jp' + product["product_url"]
            
            # 2. 썸네일 이미지 추출 - <a class="thmb"> <img>
            if not product["product_name"]:
                # fallback: 다른 선택자 시도
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
            
            # 썸네일 이미지 추출
            thumb_elem = item.select_one('a.thmb img, .thmb img, a[class*="thmb"] img')
            if thumb_elem:
                thumbnail = thumb_elem.get('src') or thumb_elem.get('data-src') or thumb_elem.get('data-original')
                if thumbnail:
                    if thumbnail.startswith('//'):
                        thumbnail = 'https:' + thumbnail
                    elif thumbnail.startswith('/'):
                        thumbnail = 'https://www.qoo10.jp' + thumbnail
                    product["thumbnail"] = thumbnail
            
            # 3. 브랜드 정보 추출 - <div class="brand_official"> (일본어-한국어 번역 지원)
            brand_elem = item.select_one('.brand_official, .brand_official button, .brand_official .txt_brand')
            if brand_elem:
                brand_text = brand_elem.get_text(strip=True)
                if brand_text:
                    # 일본어 텍스트를 한국어로 번역
                    product["brand"] = self._translate_jp_to_kr(brand_text)
            
            # 4. 가격 정보 추출 - <div class="prc"> <del>정가</del> <strong>판매가</strong>
            prc_elem = item.select_one('.prc, div[class*="prc"]')
            if prc_elem:
                # 정가 추출 (<del> 태그)
                del_elem = prc_elem.select_one('del')
                if del_elem:
                    original_text = del_elem.get_text(strip=True)
                    original_price = self._parse_price(original_text)
                    if original_price:
                        product["price"]["original_price"] = original_price
                
                # 판매가 추출 (<strong> 태그)
                strong_elem = prc_elem.select_one('strong')
                if strong_elem:
                    sale_text = strong_elem.get_text(strip=True)
                    sale_price = self._parse_price(sale_text)
                    if sale_price:
                        product["price"]["sale_price"] = sale_price
                
                # 할인율 계산
                if product["price"]["original_price"] and product["price"]["sale_price"]:
                    if product["price"]["original_price"] > product["price"]["sale_price"]:
                        discount = product["price"]["original_price"] - product["price"]["sale_price"]
                        product["price"]["discount_rate"] = int((discount / product["price"]["original_price"]) * 100)
            
            # 5. 배송 정보 추출 - <span class="ship_area"> <span class="ship"> (일본어-한국어 모두 지원)
            ship_elem = item.select_one('.ship_area .ship, .ship_area, span[class*="ship"]')
            if ship_elem:
                ship_text = ship_elem.get_text()
                # "Shipping rate 400엔" 또는 "送料 400엔" 또는 "배송비 400엔" 패턴 찾기
                shipping_pattern = self._create_jp_kr_regex("送料", "배송비")
                shipping_match = re.search(f'Shipping\\s*rate[：:]\\s*(\\d{{1,3}}(?:,\\d{{3}})*)円|{shipping_pattern}[：:]\\s*(\\d{{1,3}}(?:,\\d{{3}})*)円|(\\d{{1,3}}(?:,\\d{{3}})*)円', ship_text)
                if shipping_match:
                    shipping_fee = self._parse_price(shipping_match.group(1) or shipping_match.group(2) or shipping_match.group(3))
                    if shipping_fee:
                        product["shipping_info"]["shipping_fee"] = shipping_fee
                
                # 무료배송 조건 추출 (예: "1,500円以上購入の際 送料無料" 또는 "1,500엔 이상구매시 무료배송")
                free_shipping_pattern = self._create_jp_kr_regex("送料無料", "무료배송")
                above_pattern = self._create_jp_kr_regex("以上購入", "이상구매")
                free_shipping_match = re.search(f'(\\d{{1,3}}(?:,\\d{{3}})*)円\\s*{above_pattern}.*{free_shipping_pattern}|(\\d{{1,3}}(?:,\\d{{3}})*)円.*無料', ship_text)
                if free_shipping_match:
                    threshold = self._parse_price(free_shipping_match.group(1) or free_shipping_match.group(2))
                    if threshold:
                        product["shipping_info"]["free_shipping_threshold"] = threshold
            
            # 6. 리뷰 정보 추출 (있는 경우) - 일본어-한국어 모두 지원
            review_pattern = self._create_jp_kr_regex("レビュー", "리뷰")
            review_elem = item.find(string=re.compile(f'{review_pattern}.*\\((\d+)\\)', re.I))
            if review_elem:
                review_match = re.search(r'\((\d+)\)', str(review_elem))
                if review_match:
                    product["review_count"] = int(review_match.group(1))
            
            # 상품명이 없으면 텍스트에서 추출 (최후의 수단)
            if not product["product_name"]:
                text = item.get_text(strip=True)
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                if lines:
                    # 첫 번째 의미있는 텍스트를 상품명으로 사용
                    for line in lines:
                        if len(line) > 10 and line not in ['ホーム', 'Home', 'トップ', 'Top']:
                            product["product_name"] = line[:100]
                            break
            
            # 상품 종류 파악 (상품명 기반)
            if product["product_name"]:
                product["product_type"] = self._detect_product_type(product["product_name"])
                product["keywords"] = self._extract_product_keywords(product["product_name"])
            
            # 상품명이 있는 경우에만 추가 (유효한 상품인지 확인)
            if product["product_name"] and len(product["product_name"].strip()) > 3:
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
        """Shop 쿠폰 정보 추출 - 실제 Qoo10 Shop 페이지 구조에 맞게 개선"""
        coupons = []
        
        # 실제 Qoo10 Shop 페이지 구조: 쿠폰 리스트
        # 우선순위 1: 쿠폰 리스트 요소 찾기
        coupon_list = soup.select('.coupon-list, [class*="coupon"], [class*="クーポン"]')
        
        # 우선순위 2: 개별 쿠폰 요소 찾기
        coupon_selectors = [
            '.coupon-item',
            '.discount-coupon',
            'div[class*="coupon"]',
            'li[class*="coupon"]',
            '[class*="クーポン"]',
            '[class*="割引"]',
            'div[class*="off"]'  # "5%off", "10%off" 같은 패턴
        ]
        
        seen_coupons = set()
        
        # 전체 페이지 텍스트에서 쿠폰 패턴 찾기
        page_text = soup.get_text()
        
        # 패턴 1: "5,000円以上のご購入で10%off" 또는 "5,000엔 이상구매시 10%off" 같은 형식 (일본어-한국어 모두 지원)
        above_pattern = self._create_jp_kr_regex("以上", "이상")
        discount_pattern = self._create_jp_kr_regex("割引", "할인")
        coupon_patterns = [
            f'(\\d{{1,3}}(?:,\\d{{3}})*)円{above_pattern}.*?(\\d+)%off',  # 금액 이상 구매 시 할인율
            f'(\\d{{1,3}}(?:,\\d{{3}})*)円{above_pattern}.*?(\\d+)%{discount_pattern}',  # 금액 이상 구매 시 할인율 (일본어-한국어)
            f'(\\d+)%off.*?(\\d{{1,3}}(?:,\\d{{3}})*)円{above_pattern}',  # 할인율 + 최소 금액
            f'(\\d+)%{discount_pattern}.*?(\\d{{1,3}}(?:,\\d{{3}})*)円{above_pattern}',  # 할인율 + 최소 금액 (일본어-한국어)
        ]
        
        for pattern in coupon_patterns:
            matches = re.finditer(pattern, page_text, re.I)
            for match in matches:
                # 중복 제거를 위한 키 생성
                coupon_key = f"{match.group(1)}_{match.group(2)}"
                if coupon_key not in seen_coupons:
                    seen_coupons.add(coupon_key)
                    
                    # 첫 번째 그룹이 금액인지 할인율인지 확인
                    try:
                        if '円' in match.group(1) or ',' in match.group(1):
                            # 첫 번째 그룹이 금액
                            min_amount = self._parse_price(match.group(1))
                            discount_rate = int(match.group(2)) if match.group(2).isdigit() else 0
                        else:
                            # 첫 번째 그룹이 할인율
                            discount_rate = int(match.group(1)) if match.group(1).isdigit() else 0
                            min_amount = self._parse_price(match.group(2))
                        
                        if discount_rate > 0 or min_amount > 0:
                            coupon = {
                                "discount_rate": discount_rate,
                                "min_amount": min_amount,
                                "valid_until": None,
                                "description": match.group(0)
                            }
                            coupons.append(coupon)
                    except (ValueError, AttributeError):
                        continue
        
        # 패턴 2: HTML 요소에서 쿠폰 정보 추출
        for selector in coupon_selectors:
            coupon_elements = soup.select(selector)
            for elem in coupon_elements:
                coupon = {
                    "discount_rate": 0,
                    "min_amount": 0,
                    "valid_until": None,
                    "description": ""
                }
                
                # 쿠폰 텍스트 추출
                discount_text = elem.get_text(strip=True)
                
                # 할인율 추출 (다양한 패턴) - 일본어-한국어 모두 지원
                discount_pattern = self._create_jp_kr_regex("割引", "할인")
                discount_patterns = [
                    r'(\d+)%off',
                    r'(\d+)%OFF',
                    f'(\\d+)%{discount_pattern}',
                    r'(\d+)%',
                    r'off\s*(\d+)%',
                    f'{discount_pattern}\\s*(\\d+)%'
                ]
                
                for pattern in discount_patterns:
                    discount_match = re.search(pattern, discount_text, re.I)
                    if discount_match:
                        coupon["discount_rate"] = int(discount_match.group(1))
                        break
                
        # 최소 금액 추출 (다양한 패턴) - 일본어-한국어 모두 지원
        above_pattern = self._create_jp_kr_regex("以上", "이상")
        above_purchase_pattern = self._create_jp_kr_regex("以上購入", "이상구매")
        amount_patterns = [
            f'(\\d{{1,3}}(?:,\\d{{3}})*)[,円]{above_pattern}',
            f'(\\d+)[,円]{above_pattern}',
            f'(\\d{{1,3}}(?:,\\d{{3}})*)[,円]{above_pattern}の',
            f'(\\d+)[,円]{above_pattern}の',
            f'(\\d{{1,3}}(?:,\\d{{3}})*)[,円]{above_purchase_pattern}',
            f'(\\d+)[,円]{above_purchase_pattern}'
        ]
                
                for pattern in amount_patterns:
                    amount_match = re.search(pattern, discount_text)
                    if amount_match:
                        amount_str = amount_match.group(1).replace(',', '')
                        coupon["min_amount"] = int(amount_str)
                        break
                
                # 유효 기간 추출
                date_patterns = [
                    r'(\d{4}\.\d{2}\.\d{2})\s*[~〜]\s*(\d{4}\.\d{2}\.\d{2})',
                    r'(\d{4}-\d{2}-\d{2})\s*[~〜]\s*(\d{4}-\d{2}-\d{2})',
                    r'(\d{4}/\d{2}/\d{2})\s*[~〜]\s*(\d{4}/\d{2}/\d{2})'
                ]
                
                for pattern in date_patterns:
                    date_match = re.search(pattern, discount_text)
                    if date_match:
                        coupon["valid_until"] = date_match.group(2)
                        break
                
                # 쿠폰 설명
                coupon["description"] = discount_text[:100]  # 최대 100자
                
                # 중복 제거 (할인율과 최소 금액이 같은 쿠폰)
                coupon_key = f"{coupon['discount_rate']}_{coupon['min_amount']}"
                if coupon_key not in seen_coupons and coupon["discount_rate"] > 0:
                    coupons.append(coupon)
                    seen_coupons.add(coupon_key)
        
        return coupons
    
    def get_statistics(self) -> Dict[str, Any]:
        """크롤링 통계 조회"""
        return self.db.get_crawling_statistics()