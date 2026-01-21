"""
Qoo10 크롤링 서비스 (AI 강화 학습 및 방화벽 우회 기능 포함)
Qoo10 상품 및 Shop 페이지에서 데이터를 수집하며, 학습을 통해 성능을 지속적으로 개선합니다.

크롤링 원칙:
- CRAWLING_ANALYSIS_PRINCIPLES.md 참조
- Playwright 크롤링을 기본 권장 (동적 콘텐츠 추출)
- 모든 크롤링 결과에 crawled_with 필드 포함
- 데이터 검증 및 정규화 규칙 준수
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
import logging
from pathlib import Path
from dotenv import load_dotenv
import json

from services.database import CrawlerDatabase
from .crawler_shop import ShopCrawlerMixin

load_dotenv()

_logger = logging.getLogger(__name__)

from services.logging_utils import log_debug as _log_debug

# Qoo10 API 서비스 임포트 (선택적)
try:
    from .qoo10_api_service import Qoo10APIService
    QOO10_API_AVAILABLE = True
except ImportError:
    QOO10_API_AVAILABLE = False
    Qoo10APIService = None

# Qoo10 API 스키마 임포트 (API 구조 참고)
try:
    from .qoo10_api_schema import Qoo10APISchema
    API_SCHEMA_AVAILABLE = True
except ImportError:
    API_SCHEMA_AVAILABLE = False
    Qoo10APISchema = None

# Playwright 임포트 (선택적)
try:
    from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


# httpx 버전별 proxies 지원 여부 (모듈 로드 시 1회 판별)
try:
    import inspect as _inspect

    _HTTPX_SUPPORTS_PROXIES_PARAM = "proxies" in _inspect.signature(httpx.AsyncClient.__init__).parameters
except Exception:
    _HTTPX_SUPPORTS_PROXIES_PARAM = True  # 보수적으로 기본값 True


class Qoo10Crawler(ShopCrawlerMixin):
    """Qoo10 페이지 크롤러 (AI 강화 학습 및 방화벽 우회 기능 포함)

    주의: 인스턴스는 **단일 작업/단일 코루틴**에서 사용하는 것을 전제로 설계되었습니다.
    동일한 인스턴스를 여러 코루틴에서 동시에 사용하면 User-Agent, 프록시, 세션 쿠키
    상태가 공유되어 예기치 않은 동작이 발생할 수 있습니다. 동시에 여러 URL을
    크롤링해야 한다면 `Qoo10Crawler` 인스턴스를 URL/작업별로 분리해서 생성하세요.
    """
    
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
    
    def __init__(self, db: Optional[CrawlerDatabase] = None, error_reporting_service=None):
        """
        크롤러 초기화
        
        Args:
            db: 데이터베이스 인스턴스 (없으면 자동 생성)
            error_reporting_service: 오류 신고 서비스 (우선 크롤링용)
        """
        self.base_url = "https://www.qoo10.jp"
        self.timeout = 15.0  # 타임아웃 단축: 30초 -> 15초
        self.max_retries = 2  # 재시도 횟수 감소: 3 -> 2
        self.retry_delay_base = 1.0  # 재시도 지연 시간 단축: 2초 -> 1초
        
        # 데이터베이스 초기화
        self.db = db or CrawlerDatabase()
        
        # 오류 신고 서비스 (우선 크롤링용)
        self.error_reporting_service = error_reporting_service
        
        # 프록시 설정 (환경 변수에서 읽기)
        self.proxies = self._load_proxies()
        
        # 일본어-한국어 패턴 생성
        self._init_jp_kr_patterns()
        
        # 현재 사용 중인 User-Agent 및 프록시
        self.current_user_agent = None
        self.current_proxy = None
        
        # 세션 관리
        self.session_cookies = {}
        
        # Playwright 브라우저 인스턴스 (필요시 초기화)
        self._playwright_browser = None
        self._playwright_context = None
        
        # 우선 크롤링 필드 목록 (오류 신고된 필드)
        self._priority_fields = None
        self._priority_chunks = {}  # 필드별 Chunk 정보
        
        # Qoo10 API 서비스 (선택적)
        self.api_service = None
        if QOO10_API_AVAILABLE:
            try:
                self.api_service = Qoo10APIService()
                if self.api_service.certification_key:
                    _logger.info("Qoo10 API 서비스가 활성화되었습니다.")
            except Exception as e:
                _logger.warning(f"Qoo10 API 서비스 초기화 실패: {e!s}")
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
                # httpx 버전에 따라 proxies 지원 여부 확인 (모듈 로드 시 1회 판별)
                if _HTTPX_SUPPORTS_PROXIES_PARAM:
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
    
    
    async def crawl_product_with_playwright(self, url: str) -> Dict[str, Any]:
        """
        Playwright를 사용한 상품 페이지 크롤링 (JavaScript 실행 환경)
        
        Args:
            url: Qoo10 상품 URL
            
        Returns:
            상품 데이터 딕셔너리
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if not PLAYWRIGHT_AVAILABLE:
            raise Exception("Playwright is not available. Please install it: pip install playwright && playwright install")
        
        browser = None
        page = None
        playwright = None
        
        try:
            # URL 정규화
            normalized_url = self._normalize_product_url(url)
            logger.info(f"Playwright crawling product - URL: {normalized_url}")
            
            # Playwright 브라우저 초기화
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled']
            )
            
            # 새 컨텍스트 생성
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=self._get_user_agent(),
                locale='ja-JP',
                timezone_id='Asia/Tokyo'
            )
            
            page = await context.new_page()
            
            # 페이지 로드
            logger.debug(f"Loading page: {normalized_url}")
            # networkidle 대신 load 사용 (더 안정적이고 빠름)
            # load: 모든 리소스 로드 완료, domcontentloaded보다 안정적
            try:
                await page.goto(normalized_url, wait_until='load', timeout=60000)
            except PlaywrightTimeoutError:
                # load 타임아웃 시 domcontentloaded로 재시도 (더 빠름)
                logger.warning(f"Page load timeout, trying domcontentloaded...")
                await page.goto(normalized_url, wait_until='domcontentloaded', timeout=30000)
            
            # 추가 대기 (동적 콘텐츠 로딩)
            await asyncio.sleep(2)
            
            # 스크롤하여 지연 로딩된 콘텐츠 로드 (타임아웃 보호)
            try:
                await asyncio.wait_for(
                    page.evaluate("""
                        async () => {
                            await new Promise((resolve) => {
                                let totalHeight = 0;
                                const distance = 100;
                                const maxHeight = 5000;
                                const timer = setInterval(() => {
                                    const scrollHeight = document.body.scrollHeight;
                                    window.scrollBy(0, distance);
                                    totalHeight += distance;
                                    
                                    if(totalHeight >= scrollHeight || totalHeight > maxHeight){
                                        clearInterval(timer);
                                        resolve();
                                    }
                                }, 100);
                            });
                        }
                    """),
                    timeout=10.0  # 스크롤 최대 10초
                )
            except asyncio.TimeoutError:
                logger.warning("Scroll timeout, continuing with current content...")
            
            # 추가 대기
            await asyncio.sleep(1)
            
            # HTML 가져오기
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'lxml')
            
            # 상품 데이터 추출 (기존 메서드 재사용)
            product_code = self._extract_product_code(normalized_url, soup)
            product_name = self._extract_product_name(soup)
            
            product_data = {
                "url": normalized_url,
                "product_code": product_code,
                "product_name": product_name,
                "crawled_with": "playwright"  # 크롤링 방법 표시
            }
            
            # 각 필드 추출
            try:
                product_data["category"] = self._extract_category(soup)
            except Exception as e:
                logger.warning(f"Failed to extract category: {str(e)}")
                product_data["category"] = None
            
            try:
                product_data["brand"] = self._extract_brand(soup)
            except Exception as e:
                logger.warning(f"Failed to extract brand: {str(e)}")
                product_data["brand"] = None
            
            try:
                product_data["price"] = self._extract_price(soup)
            except Exception as e:
                logger.warning(f"Failed to extract price: {str(e)}")
                product_data["price"] = {}
            
            try:
                product_data["images"] = self._extract_images(soup)
            except Exception as e:
                logger.warning(f"Failed to extract images: {str(e)}")
                product_data["images"] = {}
            
            try:
                product_data["description"] = self._extract_description(soup)
            except Exception as e:
                logger.warning(f"Failed to extract description: {str(e)}")
                product_data["description"] = ""
            
            try:
                product_data["search_keywords"] = self._extract_search_keywords(soup)
            except Exception as e:
                logger.warning(f"Failed to extract search keywords: {str(e)}")
                product_data["search_keywords"] = []
            
            try:
                product_data["reviews"] = self._extract_reviews(soup)
            except Exception as e:
                logger.warning(f"Failed to extract reviews: {str(e)}")
                product_data["reviews"] = {}
            
            try:
                product_data["qna"] = self._extract_qna(soup)
            except Exception as e:
                logger.warning(f"Failed to extract Q&A: {str(e)}")
                product_data["qna"] = {}
            
            try:
                product_data["goods_info"] = self._extract_goods_info(soup)
            except Exception as e:
                logger.warning(f"Failed to extract goods info: {str(e)}")
                product_data["goods_info"] = {}
            
            try:
                product_data["seller_info"] = self._extract_seller_info(soup)
            except Exception as e:
                logger.warning(f"Failed to extract seller info: {str(e)}")
                product_data["seller_info"] = {}
            
            try:
                product_data["shipping_info"] = self._extract_shipping_info(soup)
            except Exception as e:
                logger.warning(f"Failed to extract shipping info: {str(e)}")
                product_data["shipping_info"] = {}
            
            try:
                product_data["is_move_product"] = self._extract_move_product(soup)
            except Exception as e:
                logger.warning(f"Failed to extract MOVE product flag: {str(e)}")
                product_data["is_move_product"] = False
            
            try:
                product_data["qpoint_info"] = self._extract_qpoint_info(soup)
            except Exception as e:
                logger.warning(f"Failed to extract Qpoint info: {str(e)}")
                product_data["qpoint_info"] = {}
            
            try:
                product_data["coupon_info"] = self._extract_coupon_info(soup)
            except Exception as e:
                logger.warning(f"Failed to extract coupon info: {str(e)}")
                product_data["coupon_info"] = {}
            
            try:
                product_data["page_structure"] = self._extract_page_structure(soup)
            except Exception as e:
                logger.warning(f"Failed to extract page structure: {str(e)}")
                product_data["page_structure"] = {}
            
            # 추가: JavaScript로 동적 로드된 데이터 직접 추출 시도
            try:
                # 페이지에서 직접 데이터 추출
                js_data = await page.evaluate("""
                    () => {
                        const data = {};
                        
                        // 상품명 (가격 안내 텍스트 제외)
                        const excludePatterns = ['全割引適用後の価格案内', '価格案内', '割引.*適用', 'クーポン.*割引'];
                        const h1Elements = document.querySelectorAll('h1');
                        for (let h1 of h1Elements) {
                            const text = h1.textContent.trim();
                            let excluded = false;
                            for (let pattern of excludePatterns) {
                                if (new RegExp(pattern).test(text)) {
                                    excluded = true;
                                    break;
                                }
                            }
                            if (!excluded && text.length > 10 && text !== 'Qoo10' && text !== 'ホーム') {
                                // 대괄호 제거
                                text = text.replace(/^\[.*?\]\s*/, '').replace(/\s*\[.*?\]$/, '').replace(/\[.*?\]/g, '').trim();
                                if (text.length > 10) {
                                    data.product_name = text;
                                    break;
                                }
                            }
                        }
                        
                        // title 태그에서 상품명 추출 (fallback)
                        if (!data.product_name) {
                            const title = document.querySelector('title');
                            if (title) {
                                let titleText = title.textContent.trim();
                                if (titleText.includes('|')) {
                                    titleText = titleText.split('|')[0].trim();
                                }
                                titleText = titleText.replace(/Qoo10/g, '').trim();
                                // 대괄호 제거
                                titleText = titleText.replace(/^\[.*?\]\s*/, '').replace(/\s*\[.*?\]$/, '').replace(/\[.*?\]/g, '').trim();
                                if (titleText.length > 3) {
                                    data.product_name = titleText;
                                }
                            }
                        }
                        
                        // 가격 정보 (유효성 검증 포함)
                        const priceElements = document.querySelectorAll('[class*="price"], [class*="prc"]');
                        const prices = [];
                        priceElements.forEach(el => {
                            const text = el.textContent.trim();
                            const match = text.match(/(\\d{1,3}(?:,\\d{3})*)円/);
                            if (match) {
                                const price = parseInt(match[1].replace(/,/g, ''));
                                // 합리적인 가격 범위 (100~1,000,000엔)
                                if (price >= 100 && price <= 1000000) {
                                    prices.push(price);
                                }
                            }
                        });
                        data.prices = prices;
                        
                        // 리뷰 수 (다양한 패턴 시도)
                        const reviewPatterns = [
                            /レビュー\\s*\\((\\d+)\\)/,
                            /評価\\s*\\((\\d+)\\)/,
                            /(\\d+)\\s*レビュー/,
                            /(\\d+)\\s*評価/
                        ];
                        for (let pattern of reviewPatterns) {
                            const match = document.body.textContent.match(pattern);
                            if (match) {
                                data.review_count = parseInt(match[1]);
                                break;
                            }
                        }
                        
                        // 평점
                        const ratingMatch = document.body.textContent.match(/(\\d+\\.?\\d*)\\s*\\((\\d+)\\)/);
                        if (ratingMatch) {
                            data.rating = parseFloat(ratingMatch[1]);
                            if (!data.review_count) {
                            data.review_count = parseInt(ratingMatch[2]);
                            }
                        }
                        
                        // Qポイント 정보 추출
                        const qpointText = document.body.textContent;
                        const receiveMatch = qpointText.match(/受取確認[：:\\s]*最大?\\s*(\\d+)P/i);
                        if (receiveMatch) data.receive_confirmation_points = parseInt(receiveMatch[1]);
                        
                        const reviewPointMatch = qpointText.match(/レビュー作成[：:\\s]*最大?\\s*(\\d+)P/i);
                        if (reviewPointMatch) data.review_points = parseInt(reviewPointMatch[1]);
                        
                        const maxPointMatch = qpointText.match(/最大\\s*(\\d+)P/i);
                        if (maxPointMatch) data.max_points = parseInt(maxPointMatch[1]);
                        
                        return data;
                    }
                """)
                
                # JavaScript에서 추출한 데이터 병합
                if js_data.get('product_name') and (not product_data.get('product_name') or product_data.get('product_name') == '상품명 없음'):
                    # 가격 안내 텍스트가 아닌지 확인
                    exclude_patterns = ['全割引適用後の価格案内', '価格案内']
                    product_name = js_data['product_name']
                    excluded = False
                    for pattern in exclude_patterns:
                        if pattern in product_name:
                            excluded = True
                            break
                    if not excluded:
                        # 상품명 정제: 대괄호 제거
                        product_name = re.sub(r'^\[.*?\]\s*', '', product_name)  # 앞쪽 대괄호 제거
                        product_name = re.sub(r'\s*\[.*?\]$', '', product_name)  # 뒤쪽 대괄호 제거
                        product_name = re.sub(r'\[.*?\]', '', product_name)  # 중간 대괄호 제거
                        product_name = ' '.join(product_name.split())  # 불필요한 공백 제거
                        product_data['product_name'] = product_name
                
                if js_data.get('prices'):
                    if not product_data.get('price', {}).get('sale_price'):
                        # 유효한 가격만 사용 (이미 JavaScript에서 필터링됨)
                        prices = js_data['prices']
                        if prices:
                            # 여러 가격 중 최소값을 판매가로 추정
                            product_data.setdefault('price', {})['sale_price'] = min(prices)
                
                if js_data.get('review_count') and not product_data.get('reviews', {}).get('review_count'):
                    product_data.setdefault('reviews', {})['review_count'] = js_data['review_count']
                
                if js_data.get('rating') and not product_data.get('reviews', {}).get('rating'):
                    product_data.setdefault('reviews', {})['rating'] = js_data['rating']
                
                # Qポイント 정보 병합
                if js_data.get('receive_confirmation_points'):
                    product_data.setdefault('qpoint_info', {})['receive_confirmation_points'] = js_data['receive_confirmation_points']
                if js_data.get('review_points'):
                    product_data.setdefault('qpoint_info', {})['review_points'] = js_data['review_points']
                if js_data.get('max_points'):
                    product_data.setdefault('qpoint_info', {})['max_points'] = js_data['max_points']
                
                # Shop 정보 추출 (상품 페이지에서 가능한 정보만)
                shop_js_data = await page.evaluate("""
                    () => {
                        const data = {};
                        
                        // 팔로워 수
                        const followerMatch = document.body.textContent.match(/フォロワー[_\s]*(\d{1,3}(?:,\d{3})*)/);
                        if (followerMatch) {
                            data.follower_count = parseInt(followerMatch[1].replace(/,/g, ''));
                        }
                        
                        return data;
                    }
                """)
                
                if shop_js_data.get('follower_count'):
                    if not product_data.get("seller_info"):
                        product_data["seller_info"] = {}
                    product_data["seller_info"]["follower_count"] = shop_js_data['follower_count']
                    
            except Exception as e:
                logger.warning(f"Failed to extract JS data: {str(e)}")
            
            # API 구조 기반 데이터 정규화 (API Key 없이도 구조 참고)
            if API_SCHEMA_AVAILABLE and Qoo10APISchema:
                try:
                    # 크롤러 데이터를 API 구조에 맞게 정규화
                    normalized_data = Qoo10APISchema.normalize_crawler_data_to_api_structure(product_data)
                    
                    # 정규화된 데이터의 유효한 필드만 크롤러 데이터에 반영
                    # (누락된 필드 보완, 타입 변환, 검증 통과한 값만 사용)
                    product_data = self._apply_api_schema_normalization(product_data, normalized_data)
                    
                    logger.info("API 구조 기반 데이터 정규화 완료 (Playwright)")
                except Exception as e:
                    logger.warning(f"API 구조 기반 정규화 실패 (계속 진행): {str(e)}")
            
            logger.info(f"Playwright crawling completed - Product: {product_name or 'Unknown'}, Code: {product_code or 'N/A'}")
            
            # 데이터베이스 저장
            try:
                self.db.save_crawled_product(product_data)
            except Exception as e:
                logger.warning(f"Failed to save to database: {str(e)}")
            
            # 임베딩 저장 (자동 학습)
            try:
                auto_learn = os.getenv("EMBEDDING_AUTO_LEARN", "1").lower() in {"1", "true", "yes"}
                if auto_learn:
                    from .embedding_integration import EmbeddingIntegration
                    embedding_integration = EmbeddingIntegration(db=self.db)
                    embedding_integration.save_crawled_texts(product_data, normalized_url, auto_learn=True)
            except Exception as e:
                logger.warning(f"Failed to save embeddings: {str(e)}")
            
            return product_data
        
        except PlaywrightTimeoutError as e:
            error_msg = f"Playwright timeout error: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error in Playwright crawling: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)
        finally:
            # 리소스 정리
            if page:
                try:
                    await page.close()
                except:
                    pass
            if browser:
                try:
                    await browser.close()
                except:
                    pass
            if playwright:
                try:
                    await playwright.stop()
                except:
                    pass
    
    async def crawl_product(self, url: str, use_playwright: bool = False) -> Dict[str, Any]:
        """
        상품 페이지 크롤링 (다양한 URL 형식 지원)
        
        Args:
            url: Qoo10 상품 URL (다양한 형식 지원: /g/XXXXX, /item/.../XXXXX, ?goodscode=XXXXX 등)
            use_playwright: True이면 Playwright 사용, False이면 기본 HTTP 크롤링 (기본값: False)
            
        Returns:
            상품 데이터 딕셔너리
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 우선 크롤링 필드 로드 (오류 신고된 필드)
        if self.error_reporting_service:
            try:
                self._priority_fields = self.error_reporting_service.get_priority_fields_for_crawling()
                # 각 우선 필드에 대한 Chunk 정보 로드
                for field_name in self._priority_fields:
                    chunks = self.error_reporting_service.get_chunks_for_field(field_name)
                    if chunks:
                        self._priority_chunks[field_name] = chunks
                logger.info(f"Priority fields loaded: {self._priority_fields}")
            except Exception as e:
                logger.warning(f"Failed to load priority fields: {str(e)}")
                self._priority_fields = []
        
        # Playwright 사용 요청 시
        if use_playwright:
            if PLAYWRIGHT_AVAILABLE:
                return await self.crawl_product_with_playwright(url)
            else:
                logger.warning("Playwright not available, falling back to HTTP crawling")
        
        # 상품 코드 추출 (API 사용을 위해)
        product_code = self._extract_product_code_from_url(url)
        api_data = None
        
        # Qoo10 API를 사용하여 데이터 조회 시도 (우선순위)
        if self.api_service and product_code:
            try:
                logger.info(f"Qoo10 API를 사용하여 상품 정보 조회 시도: {product_code}")
                api_data = await self.api_service.fetch_product_data(product_code, use_api=True)
                if api_data:
                    logger.info(f"Qoo10 API로 상품 정보 조회 성공: {product_code}")
                    # API 데이터에 URL 추가
                    api_data["url"] = url
                    api_data["product_code"] = product_code
                    return api_data
                else:
                    logger.info(f"Qoo10 API로 상품 정보 조회 실패, 크롤링으로 전환: {product_code}")
            except Exception as e:
                logger.warning(f"Qoo10 API 호출 중 오류 발생, 크롤링으로 전환: {str(e)}")
        
        try:
            # URL 정규화 (다양한 형식을 표준 형식으로 변환 시도)
            normalized_url = self._normalize_product_url(url)
            logger.info(f"Crawling product - Original URL: {url}, Normalized URL: {normalized_url}")
            
            # HTTP 요청 (정규화된 URL 사용)
            logger.debug(f"Making HTTP request to: {normalized_url}")
            response = await self._make_request(normalized_url)
            response.raise_for_status()
            logger.debug(f"HTTP response status: {response.status_code}, Content length: {len(response.text)}")
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 상품 기본 정보 추출 (AI 학습 기반 선택자 사용)
            # 페이지 구조 추출은 선택적으로 수행 (성능 최적화)
            # 에러 페이지 감지를 위해 먼저 페이지 구조 추출
            page_structure = None
            is_error_page = False
            error_indicators = []
            try:
                page_structure = self._extract_page_structure(soup)
                # 에러 페이지 감지 확인
                if page_structure and page_structure.get("is_error_page", False):
                    is_error_page = True
                    error_indicators = page_structure.get("error_indicators", [])
                    logger.warning(f"⚠️ 에러 페이지 감지됨 (HTTP 크롤링) - 지표: {error_indicators}")
            except Exception as e:
                logger.warning(f"Failed to extract page structure: {str(e)}")
                # 페이지 구조 추출 실패해도 계속 진행
                pass
            
            # 에러 페이지가 감지되고 Playwright가 사용 가능하면 자동 재시도
            if is_error_page:
                logger.warning(f"⚠️ 에러 페이지 감지됨 (HTTP 크롤링) - 지표: {error_indicators}")
                logger.warning(f"⚠️ HTML 길이: {len(response.text)} bytes, Playwright 사용 가능: {PLAYWRIGHT_AVAILABLE}, use_playwright: {use_playwright}")
                
                if PLAYWRIGHT_AVAILABLE and not use_playwright:
                    logger.info("🔄 Playwright가 사용 가능합니다. Playwright로 자동 재시도합니다...")
                    try:
                        playwright_result = await self.crawl_product_with_playwright(url)
                        # Playwright 결과에 재시도 정보 추가
                        playwright_result["_retry_info"] = {
                            "original_method": "httpx",
                            "retry_method": "playwright",
                            "retry_reason": "error_page_detected",
                            "error_indicators": error_indicators
                        }
                        # Playwright로 성공적으로 크롤링한 경우, 에러 페이지 정보 제거
                        if playwright_result.get("page_structure"):
                            playwright_result["page_structure"].pop("is_error_page", None)
                            playwright_result["page_structure"].pop("error_indicators", None)
                        extracted_name = playwright_result.get('product_name', 'Unknown')
                        logger.info(f"✅ Playwright 재시도 성공 - 상품명: {extracted_name}")
                        if extracted_name and extracted_name != "상품명 없음" and extracted_name != "Unknown":
                            logger.info(f"✅ 상품명 추출 성공: {extracted_name}")
                        return playwright_result
                    except Exception as e:
                        logger.error(f"❌ Playwright 재시도 실패: {str(e)}", exc_info=True)
                        logger.warning("HTTP 크롤링 결과를 사용하지만, 에러 페이지이므로 데이터가 불완전할 수 있습니다.")
                        # Playwright 재시도 실패 시 HTTP 크롤링 결과 계속 사용 (에러 페이지 정보 포함)
                else:
                    if not PLAYWRIGHT_AVAILABLE:
                        logger.warning("⚠️ Playwright가 설치되지 않아 재시도할 수 없습니다. pip install playwright && playwright install 실행 필요")
                    elif use_playwright:
                        logger.info("이미 Playwright를 사용 중이므로 재시도하지 않습니다.")
            
            # 각 필드 추출 시도 (실패해도 기본값 사용)
            product_code = None
            try:
                product_code = self._extract_product_code(normalized_url, soup)
            except Exception as e:
                logger.warning(f"Failed to extract product code: {str(e)}")
            
            product_name = None
            try:
                product_name = self._extract_product_name(soup)
            except Exception as e:
                logger.warning(f"Failed to extract product name: {str(e)}")
            
            # 나머지 필드들도 안전하게 추출
            product_data = {
                "url": normalized_url,  # 정규화된 URL 사용
                "product_code": product_code,
                "product_name": product_name,
                "crawled_with": "httpx"  # 크롤링 방법 표시
            }
            
            # 각 필드를 안전하게 추출
            try:
                product_data["category"] = self._extract_category(soup)
            except Exception as e:
                logger.warning(f"Failed to extract category: {str(e)}")
                product_data["category"] = None
            
            try:
                product_data["brand"] = self._extract_brand(soup)
            except Exception as e:
                logger.warning(f"Failed to extract brand: {str(e)}")
                product_data["brand"] = None
            
            try:
                product_data["price"] = self._extract_price(soup)
            except Exception as e:
                logger.warning(f"Failed to extract price: {str(e)}")
                product_data["price"] = {}
            
            try:
                product_data["images"] = self._extract_images(soup)
            except Exception as e:
                logger.warning(f"Failed to extract images: {str(e)}")
                product_data["images"] = {}
            
            try:
                product_data["description"] = self._extract_description(soup)
            except Exception as e:
                logger.warning(f"Failed to extract description: {str(e)}")
                product_data["description"] = ""
            
            try:
                product_data["search_keywords"] = self._extract_search_keywords(soup)
            except Exception as e:
                logger.warning(f"Failed to extract search keywords: {str(e)}")
                product_data["search_keywords"] = []
            
            try:
                product_data["reviews"] = self._extract_reviews(soup)
            except Exception as e:
                logger.warning(f"Failed to extract reviews: {str(e)}")
                product_data["reviews"] = {}
            
            try:
                product_data["qna"] = self._extract_qna(soup)
            except Exception as e:
                logger.warning(f"Failed to extract Q&A: {str(e)}")
                product_data["qna"] = {}
            
            try:
                product_data["goods_info"] = self._extract_goods_info(soup)
            except Exception as e:
                logger.warning(f"Failed to extract goods info: {str(e)}")
                product_data["goods_info"] = {}
            
            try:
                product_data["seller_info"] = self._extract_seller_info(soup)
            except Exception as e:
                logger.warning(f"Failed to extract seller info: {str(e)}")
                product_data["seller_info"] = {}
            
            try:
                product_data["shipping_info"] = self._extract_shipping_info(soup)
            except Exception as e:
                logger.warning(f"Failed to extract shipping info: {str(e)}")
                product_data["shipping_info"] = {}
            
            try:
                product_data["is_move_product"] = self._extract_move_product(soup)
            except Exception as e:
                logger.warning(f"Failed to extract MOVE product flag: {str(e)}")
                product_data["is_move_product"] = False
            
            try:
                product_data["qpoint_info"] = self._extract_qpoint_info(soup)
            except Exception as e:
                logger.warning(f"Failed to extract Qpoint info: {str(e)}")
                product_data["qpoint_info"] = {}
            
            try:
                product_data["coupon_info"] = self._extract_coupon_info(soup)
            except Exception as e:
                logger.warning(f"Failed to extract coupon info: {str(e)}")
                product_data["coupon_info"] = {}
            
            product_data["page_structure"] = page_structure  # 페이지 구조 및 모든 div class 정보 추가
            
            # API 구조 기반 데이터 정규화 (API Key 없이도 구조 참고)
            if API_SCHEMA_AVAILABLE and Qoo10APISchema:
                try:
                    # 크롤러 데이터를 API 구조에 맞게 정규화
                    normalized_data = Qoo10APISchema.normalize_crawler_data_to_api_structure(product_data)
                    
                    # 정규화된 데이터의 유효한 필드만 크롤러 데이터에 반영
                    # (누락된 필드 보완, 타입 변환, 검증 통과한 값만 사용)
                    product_data = self._apply_api_schema_normalization(product_data, normalized_data)
                    
                    logger.info("API 구조 기반 데이터 정규화 완료")
                except Exception as e:
                    logger.warning(f"API 구조 기반 정규화 실패 (계속 진행): {str(e)}")
            
            logger.info(f"Crawling completed - Product: {product_name or 'Unknown'}, Code: {product_code or 'N/A'}")
            
            # 데이터베이스 저장은 비동기로 처리 (성능 최적화)
            # 저장 실패해도 분석은 계속 진행
            try:
                self.db.save_crawled_product(product_data)
            except Exception as e:
                logger.warning(f"Failed to save to database: {str(e)}")
                pass  # 저장 실패해도 무시
            
            # 임베딩 저장 (자동 학습)
            try:
                auto_learn = os.getenv("EMBEDDING_AUTO_LEARN", "1").lower() in {"1", "true", "yes"}
                if auto_learn:
                    from .embedding_integration import EmbeddingIntegration
                    embedding_integration = EmbeddingIntegration(db=self.db)
                    embedding_integration.save_crawled_texts(product_data, url, auto_learn=True)
            except Exception as e:
                logger.warning(f"Failed to save embeddings: {str(e)}")
            
            return product_data
        
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code} error while crawling: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except httpx.HTTPError as e:
            error_msg = f"HTTP error while crawling: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error crawling product: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)
    
    
    def _extract_with_learning(
        self,
        selector_type: str,
        soup: BeautifulSoup,
        default_selectors: List[str],
        extract_func
    ) -> Any:
        """
        AI 학습 기반 데이터 추출 - 최적화: DB 조회 최소화, 우선 크롤링 Chunk 활용
        
        Args:
            selector_type: 선택자 타입 ('product_name', 'price', etc.)
            soup: BeautifulSoup 객체
            default_selectors: 기본 선택자 목록
            extract_func: 추출 함수
            
        Returns:
            추출된 데이터
        """
        # 우선 크롤링 필드인 경우 Chunk 정보의 선택자를 최우선으로 시도
        field_name = selector_type  # selector_type이 필드명과 일치하는 경우
        if self._priority_fields and field_name in self._priority_fields:
            if field_name in self._priority_chunks:
                chunks = self._priority_chunks[field_name]
                logger = logging.getLogger(__name__)
                logger.info(f"Using priority chunks for field: {field_name}, chunks count: {len(chunks)}")
                
                # Chunk 정보에서 선택자 패턴 추출하여 우선 시도
                for chunk in chunks:
                    chunk_data = chunk.get("chunk_data", {})
                    selector_pattern = chunk.get("selector_pattern")
                    
                    # selector_pattern이 있으면 우선 시도
                    if selector_pattern:
                        try:
                            result = extract_func(soup, selector_pattern)
                            if result and result != "상품명 없음" and result != "":
                                logger.info(f"Successfully extracted {field_name} using priority chunk selector: {selector_pattern}")
                                return result
                        except Exception as e:
                            logger.debug(f"Failed to extract using chunk selector {selector_pattern}: {str(e)}")
                            continue
                    
                    # chunk_data에서 관련 클래스 정보 활용
                    related_classes = chunk_data.get("related_classes", [])
                    if related_classes:
                        # 가장 빈번한 클래스를 선택자로 사용
                        for class_name in related_classes[:3]:  # 상위 3개만 시도
                            selector = f".{class_name}"
                            try:
                                result = extract_func(soup, selector)
                                if result and result != "상품명 없음" and result != "":
                                    logger.info(f"Successfully extracted {field_name} using priority chunk class: {class_name}")
                                    return result
                            except Exception:
                                continue
        
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
        import logging
        logger = logging.getLogger(__name__)
        
        # URL에서 상품 코드 추출
        product_code = None
        original_url = url
        
        # 다양한 패턴에서 상품 코드 추출
        patterns = [
            (r'goodscode=(\d+)', 1),  # ?goodscode=123456
            (r'/g/(\d+)', 1),  # /g/123456
            (r'/item/[^/]+/(\d+)', 1),  # /item/.../123456
            (r'/item/[^/]+/(\d+)\?', 1),  # /item/.../123456?
            (r'#(\d+)$', 1),  # #123456 (끝에 있는 경우)
        ]
        
        for pattern, group in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                product_code = match.group(group)
                logger.debug(f"Extracted product code '{product_code}' from URL using pattern: {pattern}")
                break
        
        # 상품 코드가 있으면 표준 형식으로 변환
        if product_code:
            # 표준 형식: https://www.qoo10.jp/gmkt.inc/Goods/Goods.aspx?goodscode=XXXXX
            normalized = f"https://www.qoo10.jp/gmkt.inc/Goods/Goods.aspx?goodscode={product_code}"
            logger.info(f"Normalized URL: {original_url} -> {normalized}")
            return normalized
        
        # 변환할 수 없으면 원본 반환 (로그 남기기)
        logger.warning(f"Could not extract product code from URL: {url}, using original URL")
        return url
    
    def _extract_product_code_from_url(self, url: str) -> Optional[str]:
        """URL에서 상품 코드 추출 (API 사용을 위해)"""
        # 다양한 패턴에서 상품 코드 추출
        patterns = [
            r'goodscode=(\d+)',  # ?goodscode=123456
            r'/g/(\d+)',  # /g/123456
            r'/item/[^/]+/(\d+)',  # /item/.../123456
            r'/item/[^/]+/(\d+)\?',  # /item/.../123456?
            r'#(\d+)$',  # #123456 (끝에 있는 경우)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def _apply_api_schema_normalization(
        crawler_data: Dict[str, Any],
        normalized_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        API 스키마로 정규화된 데이터를 크롤러 데이터에 반영
        
        Args:
            crawler_data: 원본 크롤러 데이터
            normalized_data: API 구조로 정규화된 데이터
            
        Returns:
            정규화가 적용된 크롤러 데이터
        """
        # 정규화된 데이터를 크롤러 형식으로 변환
        from services.data_validator import DataValidator
        normalized_crawler_format = DataValidator._convert_api_structure_to_crawler_format(normalized_data)
        
        # 크롤러 데이터에 정규화된 값 반영 (크롤러 데이터가 없거나 유효하지 않은 경우만)
        result = crawler_data.copy()
        
        # 기본 정보
        if not result.get("product_name") or result.get("product_name") == "상품명 없음":
            if normalized_crawler_format.get("product_name"):
                result["product_name"] = normalized_crawler_format["product_name"]
        
        if not result.get("product_code"):
            if normalized_crawler_format.get("product_code"):
                result["product_code"] = normalized_crawler_format["product_code"]
        
        if not result.get("category"):
            if normalized_crawler_format.get("category"):
                result["category"] = normalized_crawler_format["category"]
        
        if not result.get("brand"):
            if normalized_crawler_format.get("brand"):
                result["brand"] = normalized_crawler_format["brand"]
        
        # 가격 정보 (크롤러 데이터가 유효하지 않은 경우만)
        if not result.get("price", {}).get("sale_price") or not (100 <= result.get("price", {}).get("sale_price", 0) <= 1000000):
            if normalized_crawler_format.get("price", {}).get("sale_price"):
                if "price" not in result:
                    result["price"] = {}
                result["price"]["sale_price"] = normalized_crawler_format["price"]["sale_price"]
        
        if not result.get("price", {}).get("original_price"):
            if normalized_crawler_format.get("price", {}).get("original_price"):
                if "price" not in result:
                    result["price"] = {}
                result["price"]["original_price"] = normalized_crawler_format["price"]["original_price"]
        
        # 리뷰 정보
        if not result.get("reviews", {}).get("review_count"):
            if normalized_crawler_format.get("reviews", {}).get("review_count"):
                if "reviews" not in result:
                    result["reviews"] = {}
                result["reviews"]["review_count"] = normalized_crawler_format["reviews"]["review_count"]
        
        if not result.get("reviews", {}).get("rating"):
            if normalized_crawler_format.get("reviews", {}).get("rating"):
                if "reviews" not in result:
                    result["reviews"] = {}
                result["reviews"]["rating"] = normalized_crawler_format["reviews"]["rating"]
        
        # 이미지 정보 (크롤러 데이터가 없는 경우만)
        if not result.get("images", {}).get("detail_images"):
            if normalized_crawler_format.get("images", {}).get("detail_images"):
                if "images" not in result:
                    result["images"] = {}
                result["images"]["detail_images"] = normalized_crawler_format["images"]["detail_images"]
        
        # Qポイント 정보 (크롤러 데이터가 없는 경우만)
        if not result.get("qpoint_info") or not any(result.get("qpoint_info", {}).values()):
            if normalized_crawler_format.get("qpoint_info") and any(normalized_crawler_format["qpoint_info"].values()):
                result["qpoint_info"] = normalized_crawler_format["qpoint_info"]
        
        # 쿠폰 정보 (크롤러 데이터가 없는 경우만)
        if not result.get("coupon_info", {}).get("has_coupon"):
            if normalized_crawler_format.get("coupon_info", {}).get("has_coupon"):
                result["coupon_info"] = normalized_crawler_format["coupon_info"]
        
        # 배송 정보 (크롤러 데이터가 없는 경우만)
        if not result.get("shipping_info"):
            if normalized_crawler_format.get("shipping_info"):
                result["shipping_info"] = normalized_crawler_format["shipping_info"]
        
        return result
    
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
        # #region agent log
        _log_debug("debug-session", "run1", "A", "crawler.py:_extract_product_name", "상품명 추출 시작", {})
        # #endregion

        # 제외할 텍스트 패턴 (가격 안내, 일반적인 텍스트 등)
        exclude_patterns = [
            r'全割引適用後の価格案内',  # 가격 안내 텍스트
            r'価格案内',  # 가격 안내
            r'割引.*適用',  # 할인 적용 관련
            r'クーポン.*割引',  # 쿠폰 할인
            r'Qポイント',  # Q포인트 관련
            r'返品.*案内',  # 반품 안내
            r'配送.*案内',  # 배송 안내
            r'Qoo10',  # 사이트명
            r'ホーム',  # 홈
            r'Home',
            r'トップ',  # 탑
            r'Top',
            r'商品名',  # 상품명 (레이블)
            r'商品詳細',  # 상품 상세
        ]

        default_selectors = [
            'h1.product-name',
            'h1[itemprop="name"]',
            '.product_name',
            '#goods_name',
            '.goods_name',
            '[data-product-name]',  # data 속성에서 추출
            '.goods_title',  # Qoo10 특정 클래스
            'h1',  # h1 태그 (하지만 제외 패턴 확인)
            'title',  # fallback으로 title 태그도 확인
        ]

        def extract_func(soup_obj: BeautifulSoup, selector: Optional[str]) -> str:
            # selector가 있는 경우 우선 시도
            if selector:
                if selector == 'title':
                    # title 태그에서 상품명 추출 (Qoo10 형식: "상품명 | Qoo10")
                    title_elem = soup_obj.find('title')
                    if title_elem:
                        title_text = title_elem.get_text(strip=True)
                        # "|" 또는 "｜"로 분리하여 첫 번째 부분 추출
                        if '|' in title_text:
                            name = title_text.split('|')[0].strip()
                        elif '｜' in title_text:
                            name = title_text.split('｜')[0].strip()
                        else:
                            name = title_text

                        # "Qoo10" 제거
                        name = name.replace('Qoo10', '').replace('[Qoo10]', '').strip()

                        # 제외 패턴 확인
                        if name and len(name) > 3:
                            excluded = False
                            for pattern in exclude_patterns:
                                if re.search(pattern, name):
                                    excluded = True
                                    break
                            if not excluded:
                                return name

                elif selector == '[data-product-name]':
                    # data 속성에서 추출
                    elem = soup_obj.select_one(selector)
                    if elem:
                        name = elem.get('data-product-name') or elem.get_text(strip=True)
                        if name and len(name) > 3:
                            excluded = False
                            for pattern in exclude_patterns:
                                if re.search(pattern, name):
                                    excluded = True
                                    break
                            if not excluded:
                                return name

                else:
                    elem = soup_obj.select_one(selector)
                    if elem:
                        text = elem.get_text(strip=True)
                        # 의미있는 텍스트인지 확인 (너무 짧거나 일반적인 텍스트 제외)
                        if text and len(text) > 3:
                            excluded = False
                            for pattern in exclude_patterns:
                                if re.search(pattern, text):
                                    excluded = True
                                    break
                            if not excluded and text not in ['Qoo10', 'ホーム', 'Home', 'トップ', 'Top', '商品名']:
                                return text

            # selector 기반으로 찾지 못한 경우: 페이지 내 h1 태그에서 추출
            h1_tags = soup_obj.find_all('h1')
            for h1 in h1_tags:
                text = h1.get_text(strip=True)
                if text and len(text) > 10:
                    excluded = False
                    for pattern in exclude_patterns:
                        if re.search(pattern, text):
                            excluded = True
                            break
                    if not excluded and text not in ['Qoo10', 'ホーム', 'Home', 'トップ', 'Top', '商品名', '商品詳細']:
                        return text

            return "상품명 없음"

        result = self._extract_with_learning(
            "product_name",
            soup,
            default_selectors,
            extract_func,
        )

        # 결과 검증 및 정제
        if result and result != "상품명 없음":
            # 불필요한 공백 제거
            result = ' '.join(result.split())
            # 특수 문자 정제: 대괄호 제거
            result = re.sub(r'^\[.*?\]\s*', '', result)  # 앞쪽 대괄호 제거
            result = re.sub(r'\s*\[.*?\]$', '', result)  # 뒤쪽 대괄호 제거
            result = re.sub(r'\[.*?\]', '', result)  # 중간 대괄호 제거
            # 특수 문자 정제 (필요시)
            result = result.strip()

        # #region agent log
        _log_debug("debug-session", "run1", "A", "crawler.py:_extract_product_name", "상품명 추출 완료", {
            "result": result[:100] if result else "",
            "is_empty": result == "상품명 없음" or not result,
        })
        # #endregion

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
        # #region agent log
        _log_debug("debug-session", "run1", "B", "crawler.py:_extract_price", "가격 정보 추출 시작", {})
        # #endregion
        
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
                        # None 체크를 먼저 수행하여 타입 오류 방지
                        sale_price = price_data.get("sale_price")
                        if sale_price is None or original_price > sale_price:
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
        original_price = price_data.get("original_price")
        sale_price = price_data.get("sale_price")
        if original_price and sale_price and original_price > sale_price:
            discount = original_price - sale_price
            price_data["discount_rate"] = int((discount / original_price) * 100)
        elif original_price and sale_price:
            # 정가가 판매가보다 낮으면 잘못된 데이터
            price_data["original_price"] = None
        
        # 가격 유효성 검증 및 필터링 (비정상적인 값 제거)
        sale_price = price_data.get("sale_price")
        if sale_price is not None:
            # 합리적인 가격 범위 확인 (100엔 ~ 1,000,000엔)
            if not (100 <= sale_price <= 1000000):
                # 비정상적인 값이면 null로 설정
                price_data["sale_price"] = None
        
        original_price = price_data.get("original_price")
        if original_price is not None:
            # 합리적인 가격 범위 확인 (100엔 ~ 1,000,000엔)
            if not (100 <= original_price <= 1000000):
                # 비정상적인 값이면 null로 설정
                price_data["original_price"] = None
            else:
                # 정가가 판매가보다 낮으면 잘못된 데이터
                sale_price = price_data.get("sale_price")
                if sale_price is not None and original_price < sale_price:
                    price_data["original_price"] = None
        
        # 데이터 검증: 판매가가 없으면 오류
        if not price_data["sale_price"]:
            # 최후의 시도: 페이지 전체에서 가격 패턴 찾기
            all_text = soup.get_text()
            price_patterns = [
                r'商品価格[：:]\s*(\d{1,3}(?:,\d{3})*)円',  # 상품가격 패턴 (우선순위 높음)
                r'価格[：:]\s*(\d{1,3}(?:,\d{3})*)円',
                r'(\d{1,3}(?:,\d{3})*)円',  # 일반적인 가격 패턴
                r'¥\s*(\d{1,3}(?:,\d{3})*)'
            ]
            for pattern in price_patterns:
                matches = re.findall(pattern, all_text)
                if matches:
                    prices = [self._parse_price(m) for m in matches if self._parse_price(m)]
                    if prices:
                        # 합리적인 가격 범위 (100엔 ~ 1,000,000엔) - 여러 가격 중 최소값 선택
                        valid_prices = [p for p in prices if 100 <= p <= 1000000]
                        if valid_prices:
                            # 여러 가격이 있으면 최소값을 판매가로 추정 (일반적으로 표시되는 가격)
                            price_data["sale_price"] = min(valid_prices)
                            break
        
        # #region agent log
        _log_debug("debug-session", "run1", "B", "crawler.py:_extract_price", "가격 정보 추출 완료", {
            "sale_price": price_data.get("sale_price"),
            "original_price": price_data.get("original_price"),
            "discount_rate": price_data.get("discount_rate"),
            "has_coupon": bool(price_data.get("coupon_discount")),
            "is_empty": not price_data.get("sale_price")
        })
        # #endregion
        
        return price_data
    
    def _parse_price(self, price_text: Optional[str]) -> Optional[int]:
        """가격 텍스트를 숫자로 변환"""
        if not price_text:
            return None
        # 숫자와 쉼표만 추출
        numbers = re.sub(r'[^\d,]', '', str(price_text).replace(',', ''))
        try:
            return int(numbers) if numbers else None
        except:
            return None
    
    def _extract_images(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """이미지 정보 추출 - 실제 Qoo10 페이지 구조에 맞게 개선 (itemGoods 영역 포함)"""
        images = {
            "thumbnail": None,
            "detail_images": [],
            "item_goods_images": []  # itemGoods 영역의 모든 이미지
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
        
        # itemGoods 영역의 모든 이미지 추출 (상세 페이지 이미지 영역)
        item_goods_div = soup.find('div', {'id': 'itemGoods'})
        if item_goods_div:
            seen_item_images = set()
            # itemGoods 내의 모든 img 태그 찾기
            item_imgs = item_goods_div.find_all('img')
            for img in item_imgs:
                src = img.get('src') or img.get('data-src') or img.get('data-original')
                if src:
                    # 상대 경로를 절대 경로로 변환
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = 'https://www.qoo10.jp' + src
                    
                    # 중복 제거 및 유효한 이미지 URL인지 확인
                    if src not in seen_item_images and ('http' in src or src.startswith('//')):
                        # 작은 아이콘이나 배너 이미지 제외
                        if not any(exclude in src.lower() for exclude in ['icon', 'logo', 'banner', 'button']):
                            images["item_goods_images"].append(src)
                            seen_item_images.add(src)
        
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
        # item_goods_images도 중복 체크에 추가
        for img_url in images["item_goods_images"]:
            seen_images.add(img_url)
        
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
        
        # #region agent log
        _log_debug("debug-session", "run1", "E", "crawler.py:_extract_images", "이미지 추출 완료", {
            "has_thumbnail": bool(images.get("thumbnail")),
            "detail_images_count": len(images.get("detail_images", [])),
            "item_goods_images_count": len(images.get("item_goods_images", [])),
            "total_images": len(images.get("detail_images", [])) + len(images.get("item_goods_images", [])) + (1 if images.get("thumbnail") else 0),
            "is_empty": not images.get("thumbnail") and len(images.get("detail_images", [])) == 0 and len(images.get("item_goods_images", [])) == 0
        })
        # #endregion
        
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
        
        # #region agent log
        _log_debug("debug-session", "run1", "D", "crawler.py:_extract_description", "상품 설명 추출 완료", {
            "description_length": len(result) if result else 0,
            "is_empty": not result or len(result) < 50
        })
        # #endregion
        
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
        # #region agent log
        _log_debug("debug-session", "run1", "C", "crawler.py:_extract_reviews", "리뷰 정보 추출 시작", {})
        # #endregion
        
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
        
        # CustomerReview 영역의 상세 리뷰 추출
        customer_review_div = soup.find('div', {'id': 'CustomerReview'}) or soup.find('div', {'class': 'sec_review'})
        if customer_review_div:
            # review_list 내의 각 리뷰 항목 추출
            review_list = customer_review_div.find('ul', {'class': 'review_list'}) or customer_review_div.find('ul', {'id': 'reviews_wrapper'})
            if review_list:
                review_items = review_list.find_all('li', recursive=False)
                for review_item in review_items[:50]:  # 최대 50개 리뷰
                    review_detail = {}
                    
                    # 평점 추출
                    review_star_area = review_item.find('div', {'class': 'review_star_area'})
                    if review_star_area:
                        score_elem = review_star_area.find('span', {'class': 'score'})
                        total_elem = review_star_area.find('span', {'class': 'total'})
                        if score_elem and total_elem:
                            try:
                                review_detail["rating"] = float(score_elem.get_text(strip=True))
                                review_detail["max_rating"] = float(total_elem.get_text(strip=True))
                            except (ValueError, AttributeError):
                                pass
                    
                    # 사용자 정보 추출
                    review_user_info = review_item.find('div', {'class': 'review_user_info'})
                    if review_user_info:
                        spans = review_user_info.find_all('span')
                        if len(spans) > 0:
                            review_detail["user_name"] = spans[0].get_text(strip=True)
                        if len(spans) > 1:
                            review_detail["date"] = spans[1].get_text(strip=True)
                        # 옵션 정보 추출
                        option_texts = []
                        for span in spans[2:]:
                            text = span.get_text(strip=True)
                            if text and text not in option_texts:
                                option_texts.append(text)
                        if option_texts:
                            review_detail["options"] = option_texts
                    
                    # 옵션 상세 정보
                    review_user_type = review_item.find('div', {'class': 'review_user_type'})
                    if review_user_type:
                        option_span = review_user_type.find('span')
                        if option_span:
                            review_detail["option_detail"] = option_span.get_text(strip=True)
                    
                    # 리뷰 텍스트 추출
                    review_txt = review_item.find('p', {'class': 'review_txt'})
                    if review_txt:
                        review_detail["text"] = review_txt.get_text(strip=True)
                    
                    # 리뷰 이미지 추출
                    review_photo = review_item.find('ul', {'class': 'review_photo'})
                    if review_photo:
                        review_images = []
                        for img_li in review_photo.find_all('li'):
                            img = img_li.find('img')
                            if img:
                                img_src = img.get('src') or img.get('data-src')
                                if img_src:
                                    # 상대 경로를 절대 경로로 변환
                                    if img_src.startswith('//'):
                                        img_src = 'https:' + img_src
                                    elif img_src.startswith('/'):
                                        img_src = 'https://www.qoo10.jp' + img_src
                                    review_images.append(img_src)
                        if review_images:
                            review_detail["images"] = review_images
                    
                    # 좋아요 수 추출
                    review_button = review_item.find('div', {'class': 'review_button'})
                    if review_button:
                        count_elem = review_button.find('span', {'class': 'count'})
                        if count_elem:
                            try:
                                review_detail["like_count"] = int(count_elem.get_text(strip=True))
                            except (ValueError, AttributeError):
                                pass
                    
                    # 리뷰가 유효한 경우에만 추가
                    if review_detail.get("text") or review_detail.get("rating"):
                        reviews_data["reviews"].append(review_detail)
        
        # 기존 방식으로도 리뷰 텍스트 추출 (fallback)
        if len(reviews_data["reviews"]) == 0:
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
                            reviews_data["reviews"].append({"text": review_text})
                            seen_reviews.add(review_text)
                            if len(reviews_data["reviews"]) >= 10:  # 최대 10개
                                break
                if len(reviews_data["reviews"]) >= 10:
                    break
        
        # review_count가 0이지만 reviews 배열에 리뷰가 있으면 fallback
        if reviews_data["review_count"] == 0 and len(reviews_data["reviews"]) > 0:
            reviews_data["review_count"] = len(reviews_data["reviews"])
        
        # #region agent log
        _log_debug("debug-session", "run1", "C", "crawler.py:_extract_reviews", "리뷰 정보 추출 완료", {
            "rating": reviews_data.get("rating"),
            "review_count": reviews_data.get("review_count"),
            "reviews_count": len(reviews_data.get("reviews", [])),
            "is_empty": not reviews_data.get("rating") and not reviews_data.get("review_count")
        })
        # #endregion
        
        return reviews_data
    
    def _extract_qna(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Q&A 정보 추출 - Question_Answer 영역의 상세 Q&A 정보 추출"""
        qna_data = {
            "total_count": 0,
            "qna_list": []
        }
        
        # Question_Answer 영역 찾기
        qna_div = soup.find('div', {'id': 'Question_Answer'})
        if not qna_div:
            return qna_data
        
        # Q&A 총 개수 추출
        qna_count_elem = qna_div.find('span', {'id': 'qnaList_count_1'})
        if qna_count_elem:
            try:
                qna_data["total_count"] = int(qna_count_elem.get_text(strip=True))
            except (ValueError, AttributeError):
                pass
        
        # Q&A 목록 추출
        qna_board = qna_div.find('div', {'class': 'qna_board'})
        if qna_board:
            qna_list_div = qna_board.find('div', {'id': 'dv_lst'})
            if qna_list_div:
                # 각 Q&A 항목 추출
                qna_rows = qna_list_div.find_all('div', {'class': 'row'}, recursive=False)
                for row in qna_rows[:50]:  # 최대 50개 Q&A
                    qna_item = {}
                    
                    # 상태 추출 (回答完了, 未回答, 処理中 등)
                    col1 = row.find('div', {'class': 'col1'})
                    if col1:
                        status_tag = col1.find('span', {'class': re.compile(r'tag')})
                        if status_tag:
                            qna_item["status"] = status_tag.get_text(strip=True)
                    
                    # 질문 제목 추출
                    col2 = row.find('div', {'class': 'col2'})
                    if col2:
                        title_link = col2.find('a')
                        if title_link:
                            qna_item["question_title"] = title_link.get_text(strip=True)
                    
                    # 날짜 추출
                    col3 = row.find('div', {'class': 'col3'})
                    if col3:
                        qna_item["date"] = col3.get_text(strip=True)
                    
                    # 작성자 추출
                    col4 = row.find('div', {'class': 'col4'})
                    if col4:
                        qna_item["author"] = col4.get_text(strip=True)
                    
                    # 질문 내용 추출
                    mode_user = row.find('div', {'class': 'mode_user'})
                    if mode_user:
                        user_col2 = mode_user.find('div', {'class': 'col2'})
                        if user_col2:
                            cont = user_col2.find('div', {'class': 'cont'})
                            if cont:
                                qna_item["question"] = cont.get_text(strip=True)
                    
                    # 답변 내용 추출
                    mode_sllr = row.find('div', {'class': 'mode_sllr'})
                    if mode_sllr:
                        seller_col2 = mode_sllr.find('div', {'class': 'col2'})
                        if seller_col2:
                            cont = seller_col2.find('div', {'class': 'cont'})
                            if cont:
                                qna_item["answer"] = cont.get_text(strip=True)
                    
                    # Q&A가 유효한 경우에만 추가
                    if qna_item.get("question") or qna_item.get("question_title"):
                        qna_data["qna_list"].append(qna_item)
        
        # total_count가 0이지만 qna_list에 Q&A가 있으면 fallback
        if qna_data["total_count"] == 0 and len(qna_data["qna_list"]) > 0:
            qna_data["total_count"] = len(qna_data["qna_list"])
        
        # #region agent log
        _log_debug("debug-session", "run1", "C", "crawler.py:_extract_qna", "Q&A 정보 추출 완료", {
            "total_count": qna_data.get("total_count"),
            "qna_list_count": len(qna_data.get("qna_list", [])),
            "is_empty": qna_data.get("total_count") == 0 and len(qna_data.get("qna_list", [])) == 0
        })
        # #endregion
        
        return qna_data
    
    def _extract_goods_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """상품 정보 영역 추출 - goods_info div 내의 모든 상세 정보 추출"""
        goods_info = {
            "product_images": [],
            "brand": None,
            "product_title": None,
            "promotion_text": None,
            "price_info": {},
            "benefits": {},
            "shipping_info": {},
            "return_info": {},
            "options": [],
            "custom_name_field": None
        }
        
        # goods_info 영역 찾기
        goods_info_div = soup.find('div', {'class': 'goods_info'})
        if not goods_info_div:
            return goods_info
        
        # 상품 이미지 영역 (goods_img)
        goods_img_div = goods_info_div.find('div', {'class': 'goods_img'})
        if goods_img_div:
            # div_Default_Image 내의 이미지 목록 추출
            default_image_div = goods_img_div.find('div', {'id': 'div_Default_Image'})
            if default_image_div:
                # 기본 이미지
                basic_image_input = default_image_div.find('input', {'id': 'basic_image'})
                if basic_image_input:
                    basic_image_url = basic_image_input.get('value', '')
                    if basic_image_url:
                        goods_info["product_images"].append(basic_image_url)
                
                # 썸네일 목록 (ulIndicate)
                thumb_list = default_image_div.find('ul', {'id': 'ulIndicate'})
                if thumb_list:
                    thumb_items = thumb_list.find_all('li', {'name': 'liIndicateID'})
                    for item in thumb_items:
                        img = item.find('img')
                        if img:
                            img_src = img.get('src') or img.get('data-src')
                            if img_src:
                                # 상대 경로를 절대 경로로 변환
                                if img_src.startswith('//'):
                                    img_src = 'https:' + img_src
                                elif img_src.startswith('/'):
                                    img_src = 'https://www.qoo10.jp' + img_src
                                if img_src not in goods_info["product_images"]:
                                    goods_info["product_images"].append(img_src)
                
                # 확대 이미지 레이어 (gei_layer_enlarge) 내의 이미지 목록
                enlarge_layer = goods_img_div.find('div', {'id': 'gei_layer_enlarge'})
                if enlarge_layer:
                    thumb_list_enlarge = enlarge_layer.find('ul', {'id': re.compile(r'gei_goodsimg')})
                    if thumb_list_enlarge:
                        enlarge_items = thumb_list_enlarge.find_all('li')
                        for item in enlarge_items:
                            large_img = item.get('large_img')
                            if large_img:
                                if large_img.startswith('//'):
                                    large_img = 'https:' + large_img
                                elif large_img.startswith('/'):
                                    large_img = 'https://www.qoo10.jp' + large_img
                                if large_img not in goods_info["product_images"]:
                                    goods_info["product_images"].append(large_img)
        
        # 상품 상세 정보 영역 (goods_detail)
        goods_detail_div = goods_info_div.find('div', {'class': 'goods_detail'})
        if goods_detail_div:
            # 브랜드 및 상품명
            detail_title = goods_detail_div.find('div', {'class': 'detail_title'})
            if detail_title:
                brand_link = detail_title.find('a', {'class': 'title_brand'})
                if brand_link:
                    goods_info["brand"] = brand_link.get_text(strip=True)
                
                text_title = detail_title.find('div', {'class': 'text_title'})
                if text_title:
                    # 브랜드 링크를 제외한 텍스트가 상품명
                    brand_link_clone = text_title.find('a', {'class': 'title_brand'})
                    if brand_link_clone:
                        brand_link_clone.decompose()
                    goods_info["product_title"] = text_title.get_text(strip=True)
                
                promotion_p = detail_title.find('p', {'class': 'text_promotion'})
                if promotion_p:
                    goods_info["promotion_text"] = promotion_p.get_text(strip=True)
            
            # 가격 정보
            info_area = goods_detail_div.find('ul', {'class': 'infoArea'})
            if info_area:
                # 판매 가격
                sell_price_dl = info_area.find('dl', {'id': 'dl_sell_price'})
                if sell_price_dl:
                    price_dd = sell_price_dl.find('dd')
                    if price_dd:
                        price_strong = price_dd.find('strong')
                        if price_strong:
                            price_text = price_strong.get_text(strip=True)
                            # 숫자 추출
                            price_match = re.search(r'([\d,]+)', price_text.replace(',', ''))
                            if price_match:
                                try:
                                    goods_info["price_info"]["selling_price"] = int(price_match.group(1).replace(',', ''))
                                except ValueError:
                                    pass
                
                # 타임세일 가격
                discount_info = info_area.find('span', {'id': re.compile(r'discount_info')})
                if discount_info:
                    dcprice_dl = discount_info.find('dl', {'class': 'q_dcprice'})
                    if dcprice_dl:
                        dcprice_dd = dcprice_dl.find('dd')
                        if dcprice_dd:
                            dcprice_strong = dcprice_dd.find('strong')
                            if dcprice_strong:
                                dcprice_text = dcprice_strong.get_text(strip=True)
                                dcprice_match = re.search(r'([\d,]+)', dcprice_text.replace(',', ''))
                                if dcprice_match:
                                    try:
                                        goods_info["price_info"]["timesale_price"] = int(dcprice_match.group(1).replace(',', ''))
                                    except ValueError:
                                        pass
                    
                    # 세일 시간 정보
                    dsc_txt_dl = discount_info.find('dl', {'class': 'dsc_txt'})
                    if dsc_txt_dl:
                        dsc_dd = dsc_txt_dl.find('dd')
                        if dsc_dd:
                            sale_time_p = dsc_dd.find('p', {'class': 'fs_11'})
                            if sale_time_p:
                                goods_info["price_info"]["sale_time"] = sale_time_p.get_text(strip=True)
                
                # 추가 혜택 (Q포인트)
                benefit_li = info_area.find('li', {'id': re.compile(r'li_BenefitInfo')})
                if benefit_li:
                    super_point = benefit_li.find('span', {'class': 'super_point'})
                    if super_point:
                        point_strong = super_point.find('strong')
                        if point_strong:
                            goods_info["benefits"]["qpoint"] = point_strong.get_text(strip=True)
                
                # 배송 정보 - infoData 클래스를 가진 모든 li 중에서 배송 관련 찾기
                all_info_data = info_area.find_all('li', {'class': 'infoData'})
                shipping_li = None
                for li in all_info_data:
                    text = li.get_text()
                    if '발송국' in text or '送料' in text or '配送' in text or '배송' in text:
                        shipping_li = li
                        break
                
                if shipping_li:
                    # 발송국
                    shipping_dl = shipping_li.find('dl', {'name': 'shipping_panel_area'})
                    if shipping_dl:
                        shipping_dt = shipping_dl.find('dt')
                        shipping_dd = shipping_dl.find('dd')
                        if shipping_dt and shipping_dd:
                            key = shipping_dt.get_text(strip=True)
                            value = shipping_dd.get_text(strip=True)
                            goods_info["shipping_info"][key] = value
                    
                    # 배송비
                    shipping_fee_dl = shipping_li.find('dl', {'class': 'detailsArea'})
                    if shipping_fee_dl:
                        shipping_fee_dt = shipping_fee_dl.find('dt')
                        shipping_fee_dd = shipping_fee_dl.find('dd')
                        if shipping_fee_dt and shipping_fee_dd:
                            fee_text = shipping_fee_dd.get_text(strip=True)
                            if '무료' in fee_text or '無料' in fee_text or 'FREE' in fee_text.upper():
                                goods_info["shipping_info"]["shipping_fee"] = 0
                                goods_info["shipping_info"]["free_shipping"] = True
                            else:
                                fee_match = re.search(r'(\d+)', fee_text)
                                if fee_match:
                                    try:
                                        goods_info["shipping_info"]["shipping_fee"] = int(fee_match.group(1))
                                    except ValueError:
                                        pass
                    
                    # 배송일
                    delivery_date_panel = shipping_li.find('div', {'id': re.compile(r'availabledatePanel')})
                    if delivery_date_panel:
                        delivery_dl = delivery_date_panel.find('dl', {'class': 'detailsArea'})
                        if delivery_dl:
                            delivery_dd = delivery_dl.find('dd')
                            if delivery_dd:
                                goods_info["shipping_info"]["delivery_date"] = delivery_dd.get_text(strip=True)
                
                # 반품 정보
                return_panel = info_area.find('div', {'id': re.compile(r'deliveryRuleExplain')})
                if return_panel:
                    return_li = return_panel.find('li', {'class': 'infoData'})
                    if return_li:
                        return_dl = return_li.find('dl', {'class': 'detailsArea'})
                        if return_dl:
                            return_dt = return_dl.find('dt')
                            return_dd = return_dl.find('dd')
                            if return_dt and return_dd:
                                goods_info["return_info"]["title"] = return_dt.get_text(strip=True)
                                goods_info["return_info"]["description"] = return_dd.get_text(strip=True)
                
                # 상품 옵션 추출
                option_info = info_area.find('div', {'id': re.compile(r'OptionInfo')})
                if option_info:
                    # 본체 컬러 (inventory) - stock 클래스가 있는 dl 찾기
                    all_dls = option_info.find_all('dl', {'class': 'detailsArea'})
                    inventory_dl = None
                    for dl in all_dls:
                        if 'stock' in dl.get('class', []):
                            inventory_dl = dl
                            break
                    if not inventory_dl:
                        # stock 클래스가 없으면 첫 번째 detailsArea dl 사용
                        inventory_dl = option_info.find('dl', {'class': 'detailsArea'})
                    if inventory_dl:
                        inventory_dt = inventory_dl.find('dt')
                        if inventory_dt:
                            option_name = inventory_dt.get_text(strip=True)
                            inventory_outer = inventory_dl.find('div', {'id': re.compile(r'inventory_outer')})
                            if inventory_outer:
                                content_inventory = inventory_outer.find('ul', {'id': re.compile(r'content_inventory')})
                                if content_inventory:
                                    option_items = content_inventory.find_all('li')
                                    option_values = []
                                    for item in option_items:
                                        span = item.find('span')
                                        if span:
                                            option_text = span.get_text(strip=True)
                                            if option_text and option_text != '-----------------------------------------------------------':
                                                option_values.append(option_text)
                                    if option_values:
                                        goods_info["options"].append({
                                            "name": option_name,
                                            "type": "inventory",
                                            "values": option_values
                                        })
                    
                    # 이라스트 (opt)
                    opt_dls = option_info.find_all('dl', {'class': 'detailsArea'})
                    for opt_dl in opt_dls:
                        opt_dt = opt_dl.find('dt')
                        if opt_dt:
                            opt_name = opt_dt.get_text(strip=True)
                            # inventory가 아닌 경우만 (이미 처리했으므로)
                            if '본체 컬러' not in opt_name and '∙' not in opt_name:
                                opt_outer = opt_dl.find('div', {'id': re.compile(r'opt_outer')})
                                if opt_outer:
                                    content_opt = opt_outer.find('ul', {'id': re.compile(r'content_opt')})
                                    if content_opt:
                                        opt_items = content_opt.find_all('li')
                                        opt_values = []
                                        for item in opt_items:
                                            span = item.find('span')
                                            if span:
                                                opt_text = span.get_text(strip=True)
                                                if opt_text and opt_text != '-----------------------------------------------------------':
                                                    opt_values.append(opt_text)
                                        if opt_values:
                                            goods_info["options"].append({
                                                "name": opt_name,
                                                "type": "option",
                                                "values": opt_values
                                            })
                    
                    # 작성 이름 필드
                    request_info = option_info.find('span', {'id': re.compile(r'RequestInfo')})
                    if request_info:
                        request_dl = request_info.find('dl', {'class': 'detailsArea'})
                        if request_dl:
                            request_dt = request_dl.find('dt')
                            request_dd = request_dl.find('dd')
                            if request_dt and request_dd:
                                field_name = request_dt.get_text(strip=True)
                                input_field = request_dd.find('input')
                                if input_field:
                                    maxlength = input_field.get('maxlength', '')
                                    goods_info["custom_name_field"] = {
                                        "name": field_name,
                                        "maxlength": maxlength
                                    }
        
        # #region agent log
        _log_debug("debug-session", "run1", "D", "crawler.py:_extract_goods_info", "상품 정보 영역 추출 완료", {
            "has_images": len(goods_info.get("product_images", [])) > 0,
            "has_brand": bool(goods_info.get("brand")),
            "has_title": bool(goods_info.get("product_title")),
            "has_price": bool(goods_info.get("price_info")),
            "options_count": len(goods_info.get("options", [])),
            "is_empty": not goods_info.get("product_title") and not goods_info.get("price_info")
        })
        # #endregion
        
        return goods_info
    
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
        # #region agent log
        _log_debug("debug-session", "run1", "F", "crawler.py:_extract_shipping_info", "배송 정보 추출 시작", {})
        # #endregion

        shipping_info: Dict[str, Any] = {
            "shipping_fee": None,
            "shipping_method": None,
            "estimated_delivery": None,
            "free_shipping": False,  # 무료배송 여부
            "return_policy": None,  # 반품 정책 정보
        }

        # 배송비 정보 찾기 (다양한 패턴 시도)
        shipping_patterns = [
            r'送料[：:]\s*(\d+)円',
            r'送料[：:]\s*無料',
            r'送料[：:]\s*FREE',
            r'配送料[：:]\s*(\d+)円',
            r'배송비[：:]\s*(\d+)円',
            r'Shipping[：:]\s*(\d+)円',
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
                if (
                    re.search(free_shipping_pattern, shipping_text)
                    or 'FREE' in shipping_text.upper()
                    or '無料' in shipping_text
                    or '무료' in shipping_text
                ):
                    shipping_info["free_shipping"] = True
                    shipping_info["shipping_fee"] = 0
                else:
                    # 숫자 추출
                    for pattern in shipping_patterns:
                        m = re.search(pattern, shipping_text)
                        if m and m.group(1):
                            shipping_info["shipping_fee"] = int(m.group(1))
                            break

                    # 패턴 매칭 실패 시 숫자만 추출
                    if shipping_info["shipping_fee"] is None:
                        numbers = re.findall(r'\d+', shipping_text)
                        if numbers:
                            shipping_info["shipping_fee"] = int(numbers[0])

        # 반품 정책 정보 추출 (일본어-한국어 모두 지원) - 강화된 추출
        return_pattern = self._create_jp_kr_regex("返品", "반품")
        return_elem = soup.find(string=re.compile(f'{return_pattern}|返却|Return', re.I))

        # 반품 정보가 있는 섹션 찾기 (더 넓은 범위)
        return_section = None
        if return_elem:
            return_section = return_elem.find_parent()
            if return_section:
                parent = return_section.find_parent()
                if parent is not None:
                    return_section = parent

        # 반품 관련 선택자로도 시도
        if return_section is None:
            return_selectors = [
                'div[class*="返品"]',
                'div[class*="반품"]',
                'div[class*="return"]',
                '[id*="返品"]',
                '[id*="반품"]',
                '[id*="return"]',
            ]
            for selector in return_selectors:
                return_section = soup.select_one(selector)
                if return_section:
                    break

        if return_section is not None:
            return_text = return_section.get_text()
            # "返品無料" 또는 "무료반품" 또는 "返品無料サービス" 확인
            free_return_pattern = self._create_jp_kr_regex("返品無料", "무료반품")
            if (
                re.search(free_return_pattern, return_text)
                or '無料返品' in return_text
                or '返品無料サービス' in return_text
            ):
                shipping_info["return_policy"] = "free_return"
            elif re.search(return_pattern, return_text):
                shipping_info["return_policy"] = "return_available"

        # 추가 시도: 페이지 전체 텍스트에서 반품 정보 찾기
        if not shipping_info["return_policy"]:
            all_text = soup.get_text()
            free_return_pattern = self._create_jp_kr_regex("返品無料", "무료반품")
            if (
                re.search(free_return_pattern, all_text)
                or '無料返品' in all_text
                or '返品無料サービス' in all_text
            ):
                shipping_info["return_policy"] = "free_return"
            elif re.search(return_pattern, all_text):
                shipping_info["return_policy"] = "return_available"

        # #region agent log
        _log_debug("debug-session", "run1", "F", "crawler.py:_extract_shipping_info", "배송 정보 추출 완료", {
            "shipping_fee": shipping_info.get("shipping_fee"),
            "free_shipping": shipping_info.get("free_shipping"),
            "shipping_method": shipping_info.get("shipping_method"),
            "estimated_delivery": shipping_info.get("estimated_delivery"),
            "is_empty": not shipping_info.get("shipping_fee") and not shipping_info.get("free_shipping"),
        })
        # #endregion

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
        # #region agent log
        _log_debug("debug-session", "run1", "I", "crawler.py:_extract_qpoint_info", "Qポイント 정보 추출 시작", {})
        # #endregion

        qpoint_info: Dict[str, Any] = {
            "max_points": None,
            "receive_confirmation_points": None,
            "review_points": None,
            "auto_points": None,
        }

        # Qポイント 섹션 찾기 (다양한 선택자 시도)
        qpoint_selectors = [
            'div[class*="qpoint"]',
            'div[class*="ポイント"]',
            'table[class*="qpoint"]',
            'table[class*="ポイント"]',
            '.qpoint-info',
            '#qpoint-info',
            '[id*="qpoint"]',
            '[id*="ポイント"]',
        ]

        qpoint_section = None
        for selector in qpoint_selectors:
            qpoint_section = soup.select_one(selector)
            if qpoint_section:
                break

        # 텍스트 기반 검색 (일본어-한국어 모두 지원)
        if qpoint_section is None:
            qpoint_method_pattern = self._create_jp_kr_regex("Qポイント獲得方法", "Q포인트획득방법")
            qpoint_get_pattern = self._create_jp_kr_regex("Qポイント獲得", "Q포인트획득")
            qpoint_pattern = self._create_jp_kr_regex("Qポイント", "Q포인트")
            qpoint_text_elem = soup.find(
                string=re.compile(f'{qpoint_method_pattern}|{qpoint_get_pattern}|{qpoint_pattern}', re.I)
            )
            if qpoint_text_elem:
                qpoint_section = qpoint_text_elem.find_parent()
                if qpoint_section:
                    parent = qpoint_section.find_parent()
                    if parent is not None:
                        qpoint_section = parent

        if qpoint_section is not None:
            # 섹션의 모든 텍스트 추출
            qpoint_text = qpoint_section.get_text()

            # "受取確認: 最大1P" 또는 "수령확인: 최대1P" 패턴 찾기 (더 유연한 패턴)
            receive_pattern = self._create_jp_kr_regex("受取確認", "수령확인")
            max_pattern = self._create_jp_kr_regex("最大", "최대")

            # 패턴 1: "受取確認: 最大1P"
            receive_match = re.search(
                f'{receive_pattern}[：:\s]*{max_pattern}?\s*(\d+)P', qpoint_text, re.I
            )
            if receive_match:
                try:
                    points = int(receive_match.group(1))
                    qpoint_info["receive_confirmation_points"] = points
                except (ValueError, AttributeError):
                    pass  # 숫자 변환 실패 시 무시

            # 패턴 2: "受取確認.*(\d+)P" (더 유연한 패턴, 숫자만 매칭)
            if not qpoint_info["receive_confirmation_points"]:
                receive_match2 = re.search(
                    f'{receive_pattern}[：:\s]*.*?(\d+)\s*P', qpoint_text, re.I
                )
                if receive_match2:
                    try:
                        points = int(receive_match2.group(1))
                        qpoint_info["receive_confirmation_points"] = points
                    except (ValueError, AttributeError):
                        pass  # 숫자 변환 실패 시 무시

            # "レビュー作成: 最大20P" 또는 "리뷰작성: 최대20P" 패턴 찾기
            review_create_pattern = self._create_jp_kr_regex("レビュー作成", "리뷰작성")

            # 패턴 1: "レビュー作成: 最大20P"
            review_match = re.search(
                f'{review_create_pattern}[：:\s]*{max_pattern}?\s*(\d+)P',
                qpoint_text,
                re.I,
            )
            if review_match:
                try:
                    points = int(review_match.group(1))
                    qpoint_info["review_points"] = points
                except (ValueError, AttributeError):
                    pass  # 숫자 변환 실패 시 무시

            # 패턴 2: "レビュー作成.*(\d+)P" (더 유연한 패턴, 숫자만 매칭)
            if not qpoint_info["review_points"]:
                review_match2 = re.search(
                    f'{review_create_pattern}[：:\s]*.*?(\d+)\s*P', qpoint_text, re.I
                )
                if review_match2:
                    try:
                        points = int(review_match2.group(1))
                        qpoint_info["review_points"] = points
                    except (ValueError, AttributeError):
                        pass  # 숫자 변환 실패 시 무시

            # "最大(\d+)P" 또는 "최대(\d+)P" 패턴 찾기 (전체 최대 포인트)
            max_match = re.search(f'{max_pattern}\s*(\d+)\s*P', qpoint_text, re.I)
            if max_match:
                try:
                    points = int(max_match.group(1))
                    qpoint_info["max_points"] = points
                except (ValueError, AttributeError):
                    pass  # 숫자 변환 실패 시 무시

            # "配送完了.*自動.*(\d+)P" 또는 "배송완료.*자동.*(\d+)P" 패턴 찾기 (자동 포인트)
            delivery_complete_pattern = self._create_jp_kr_regex("配送完了", "배송완료")
            auto_pattern = self._create_jp_kr_regex("自動", "자동")
            auto_match = re.search(
                f'{delivery_complete_pattern}.*?{auto_pattern}.*?(\d+)\s*P',
                qpoint_text,
                re.I | re.DOTALL,
            )
            if auto_match:
                try:
                    points = int(auto_match.group(1))
                    qpoint_info["auto_points"] = points
                except (ValueError, AttributeError):
                    pass  # 숫자 변환 실패 시 무시

        # 추가 시도: 페이지 전체 텍스트에서 Qポイント 정보 찾기
        if not any(qpoint_info.values()):
            all_text = soup.get_text()
            receive_pattern = self._create_jp_kr_regex("受取確認", "수령확인")
            review_create_pattern = self._create_jp_kr_regex("レビュー作成", "리뷰작성")
            max_pattern = self._create_jp_kr_regex("最大", "최대")

            receive_match = re.search(
                f'{receive_pattern}[：:\s]*.*?(\d+)\s*P', all_text, re.I
            )
            if receive_match:
                try:
                    points = int(receive_match.group(1))
                    qpoint_info["receive_confirmation_points"] = points
                except (ValueError, AttributeError):
                    pass  # 숫자 변환 실패 시 무시

            review_match = re.search(
                f'{review_create_pattern}[：:\s]*.*?(\d+)\s*P', all_text, re.I
            )
            if review_match:
                try:
                    points = int(review_match.group(1))
                    qpoint_info["review_points"] = points
                except (ValueError, AttributeError):
                    pass  # 숫자 변환 실패 시 무시

            max_match = re.search(f'{max_pattern}\s*(\d+)\s*P', all_text, re.I)
            if max_match:
                try:
                    points = int(max_match.group(1))
                    qpoint_info["max_points"] = points
                except (ValueError, AttributeError):
                    pass  # 숫자 변환 실패 시 무시

        # #region agent log
        _log_debug("debug-session", "run1", "I", "crawler.py:_extract_qpoint_info", "Qポイント 정보 추출 완료", {
            "max_points": qpoint_info.get("max_points"),
            "receive_confirmation_points": qpoint_info.get("receive_confirmation_points"),
            "review_points": qpoint_info.get("review_points"),
            "auto_points": qpoint_info.get("auto_points"),
            "is_empty": not any(qpoint_info.values()),
        })
        # #endregion

        return qpoint_info
    
    def _extract_coupon_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """쿠폰 상세 정보 추출 - 실제 Qoo10 페이지 구조에 맞게 개선"""
        # #region agent log
        _log_debug("debug-session", "run1", "G", "crawler.py:_extract_coupon_info", "쿠폰 정보 추출 시작", {})
        # #endregion
        
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
        
        # #region agent log
        _log_debug("debug-session", "run1", "G", "crawler.py:_extract_coupon_info", "쿠폰 정보 추출 완료", {
            "has_coupon": coupon_info.get("has_coupon"),
            "coupon_type": coupon_info.get("coupon_type"),
            "max_discount": coupon_info.get("max_discount"),
            "is_empty": not coupon_info.get("has_coupon")
        })
        # #endregion
        
        return coupon_info
    
    def _extract_page_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        페이지 구조 및 모든 div class 추출 (최적화 버전)
        Qoo10 페이지의 모든 div class를 분석하여 각 요소의 의미를 파악
        """
        # 에러 페이지 감지 (로깅 전에 수행)
        is_error_page = False
        error_indicators = []
        if soup:
            # 에러 페이지 클래스 확인
            error_classes = soup.find_all(class_=re.compile(r'error|Error|ERROR|section_error'))
            if error_classes:
                is_error_page = True
                error_indicators.append("error_class_found")
            
            # 에러 메시지 텍스트 확인
            page_text = soup.get_text().lower() if soup else ""
            error_keywords = ["エラー", "error", "ページが見つかりません", "not found", "404", "500", "アクセスできません"]
            if any(keyword in page_text for keyword in error_keywords):
                is_error_page = True
                error_indicators.append("error_text_found")
            
            # HTML 길이 확인 (너무 짧으면 에러 페이지일 가능성)
            html_str = str(soup)
            if len(html_str) < 5000:  # 5KB 미만이면 의심
                is_error_page = True
                error_indicators.append("html_too_short")
        
        # #region agent log - H1, H3, H4 가설 검증
        import json
        from datetime import datetime
        log_path = "/Users/chunghyo/qoo10-ai-agent/.cursor/debug.log"
        try:
            # 디렉토리가 없으면 생성
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "id": f"log_{int(datetime.now().timestamp() * 1000)}_extract_start",
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "location": "crawler.py:_extract_page_structure",
                    "message": "페이지 구조 추출 시작",
                    "data": {
                        "soup_exists": soup is not None,
                        "is_error_page": is_error_page,
                        "error_indicators": error_indicators,
                        "html_length": len(str(soup)) if soup else 0
                    },
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H1,H3,H4"
                }, ensure_ascii=False) + "\n")
        except: pass
        # #endregion
        
        # 에러 페이지인 경우 빈 구조 반환
        if is_error_page:
            return {
                "all_div_classes": [],
                "class_frequency": {},
                "key_elements": {},
                "semantic_structure": {},
                "is_error_page": True,
                "error_indicators": error_indicators
            }
        
        structure = {
            "all_div_classes": [],
            "class_frequency": {},
            "key_elements": {},
            "semantic_structure": {}
        }
        
        # 최적화: 한 번의 순회로 모든 정보 수집
        all_divs = soup.find_all('div', limit=1000)  # 최대 1000개로 제한
        
        # #region agent log - H1 가설 검증
        try:
            # 페이지 전체 구조 확인
            all_elements = soup.find_all()
            body_elements = soup.find_all('body')
            html_length = len(str(soup)) if soup else 0
            
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "id": f"log_{int(datetime.now().timestamp() * 1000)}_divs_found",
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "location": "crawler.py:_extract_page_structure",
                    "message": "div 요소 개수 확인",
                    "data": {
                        "div_count": len(all_divs),
                        "total_elements": len(all_elements),
                        "body_elements": len(body_elements),
                        "html_length": html_length,
                        "sample_div_classes": [div.get('class', [])[:3] for div in all_divs[:5]] if all_divs else []
                    },
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H1"
                }, ensure_ascii=False) + "\n")
        except Exception as e:
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "id": f"log_{int(datetime.now().timestamp() * 1000)}_divs_found_error",
                        "timestamp": int(datetime.now().timestamp() * 1000),
                        "location": "crawler.py:_extract_page_structure",
                        "message": "div 요소 개수 확인 중 오류",
                        "data": {"error": str(e)},
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "H1"
                    }, ensure_ascii=False) + "\n")
            except: pass
        # #endregion
        
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
        
        # #region agent log - H1, H3, H4 가설 검증
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "id": f"log_{int(datetime.now().timestamp() * 1000)}_extract_end",
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "location": "crawler.py:_extract_page_structure",
                    "message": "페이지 구조 추출 완료",
                    "data": {
                        "total_classes": len(structure["all_div_classes"]),
                        "key_elements_count": len(structure["key_elements"]),
                        "semantic_structure_keys": list(structure["semantic_structure"].keys()),
                        "key_elements_keys": list(structure["key_elements"].keys()),
                        "semantic_structure_sample": {k: len(v) for k, v in structure["semantic_structure"].items()}
                    },
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H1,H3,H4"
                }, ensure_ascii=False) + "\n")
        except: pass
        # #endregion
        
        return structure
    
    def _extract_product_keywords(self, product_name: str) -> List[str]:
        """상품명에서 키워드 추출 (간단 버전)

        - 대소문자/한글/일본어 단어를 모두 포함하는 토큰을 기준으로 추출
        - 향후 형태소 분석 라이브러리를 붙일 수 있도록 최소한의 구현만 유지
        """
        keywords = []
        
        # 상품명에서 의미있는 단어 추출 (2자 이상 토큰)
        words = re.findall(r"\b\w+\b", product_name, re.UNICODE)
        for word in words:
            if len(word) >= 2:
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
                if not elem:
                    continue
                    
                coupon = {
                    "discount_rate": 0,
                    "min_amount": 0,
                    "valid_until": None,
                    "description": ""
                }
                
                # 쿠폰 텍스트 추출 - 안전하게 처리
                discount_text = ""
                try:
                    discount_text = elem.get_text(strip=True)
                    if not discount_text:
                        continue
                except (AttributeError, TypeError):
                    continue
                
                # discount_text가 여전히 비어있으면 건너뛰기
                if not discount_text:
                    continue
                
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
                
                # 쿠폰 설명 - 안전하게 처리
                coupon["description"] = discount_text[:100] if discount_text else ""  # 최대 100자
                
                # 중복 제거 (할인율과 최소 금액이 같은 쿠폰)
                coupon_key = f"{coupon['discount_rate']}_{coupon['min_amount']}"
                if coupon_key not in seen_coupons and coupon["discount_rate"] > 0:
                    coupons.append(coupon)
                    seen_coupons.add(coupon_key)
        
        return coupons
    
    def get_statistics(self) -> Dict[str, Any]:
        """크롤링 통계 조회"""
        return self.db.get_crawling_statistics()