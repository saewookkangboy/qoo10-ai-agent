"""Shop 관련 크롤링 기능을 담당하는 믹스인.

Qoo10Crawler에서 Shop 페이지 크롤링/파싱 책임을 분리하기 위해 사용합니다.
"""
from __future__ import annotations

from typing import Dict, Any, Optional, List
import asyncio
import re

import httpx
from bs4 import BeautifulSoup

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:  # pragma: no cover - playwright 미설치 환경
    PLAYWRIGHT_AVAILABLE = False
    async_playwright = None  # type: ignore[assignment]
    PlaywrightTimeoutError = Exception  # type: ignore[assignment]


class ShopCrawlerMixin:
    async def crawl_shop_with_playwright(self, url: str) -> Dict[str, Any]:
        """Playwright를 사용한 Shop 페이지 크롤링 (JavaScript 실행 환경)."""
        import logging

        logger = logging.getLogger(__name__)

        if not PLAYWRIGHT_AVAILABLE or async_playwright is None:
            raise Exception(
                "Playwright is not available. Please install it: pip install playwright && playwright install"
            )

        browser = None
        page = None
        playwright = None

        try:
            logger.info(f"Playwright crawling shop - URL: {url}")

            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                ],
            )

            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=self._get_user_agent(),
                locale="ja-JP",
                timezone_id="Asia/Tokyo",
            )

            page = await context.new_page()

            logger.debug(f"Loading shop page: {url}")
            await page.goto(url, wait_until="networkidle", timeout=30000)

            await asyncio.sleep(2)

            # 지연 로딩된 콘텐츠까지 스크롤
            await page.evaluate(
                """
                async () => {
                    await new Promise((resolve) => {
                        let totalHeight = 0;
                        const distance = 100;
                        const timer = setInterval(() => {
                            const scrollHeight = document.body.scrollHeight;
                            window.scrollBy(0, distance);
                            totalHeight += distance;

                            if (totalHeight >= scrollHeight || totalHeight > 10000) {
                                clearInterval(timer);
                                resolve();
                            }
                        }, 100);
                    });
                }
                """
            )

            await asyncio.sleep(1)

            html_content = await page.content()
            soup = BeautifulSoup(html_content, "lxml")

            shop_data: Dict[str, Any] = {
                "url": url,
                "shop_id": self._extract_shop_id(url),
                "shop_name": self._extract_shop_name(soup),
                "shop_level": self._extract_shop_level(soup),
                "follower_count": self._extract_follower_count(soup),
                "product_count": self._extract_product_count(soup),
                "categories": self._extract_shop_categories(soup),
                "products": self._extract_shop_products(soup),
                "coupons": self._extract_shop_coupons(soup),
                "crawled_with": "playwright",
            }

            # JS에서 직접 추출 가능한 데이터 보완
            try:
                js_data = await page.evaluate(
                    """
                    () => {
                        const data = {};

                        const shopName = document.querySelector('h1') || document.querySelector('.shop-name');
                        if (shopName) data.shop_name = shopName.textContent.trim();

                        const followerMatch = document.body.textContent.match(/フォロワー[_\s]*(\d{1,3}(?:,\d{3})*)/);
                        if (followerMatch) {
                            data.follower_count = parseInt(followerMatch[1].replace(/,/g, ''));
                        }

                        const productMatch = document.body.textContent.match(/全ての商品[_\s]*\((\d+)\)/);
                        if (productMatch) {
                            data.product_count = parseInt(productMatch[1]);
                        }

                        const powerMatch = document.body.textContent.match(/POWER[_\s]*(\d+)%/);
                        if (powerMatch) {
                            data.power_level = parseInt(powerMatch[1]);
                        }

                        const productItems = document.querySelectorAll('.item, .product-item, div[class*="item"]');
                        data.product_items_count = productItems.length;

                        return data;
                    }
                    """
                )

                if js_data.get("shop_name") and not shop_data.get("shop_name"):
                    shop_data["shop_name"] = js_data["shop_name"]

                if js_data.get("follower_count") and not shop_data.get("follower_count"):
                    shop_data["follower_count"] = js_data["follower_count"]

                if js_data.get("product_count") and not shop_data.get("product_count"):
                    shop_data["product_count"] = js_data["product_count"]

                if js_data.get("power_level"):
                    power_level = js_data["power_level"]
                    if power_level >= 90:
                        shop_data["shop_level"] = "power"
                    elif power_level >= 70:
                        shop_data["shop_level"] = "excellent"

            except Exception as e:  # pragma: no cover - 디버그용 보완 로직
                logger.warning(f"Failed to extract JS data: {str(e)}")

            logger.info(
                "Playwright shop crawling completed - Shop: %s, ID: %s",
                shop_data.get("shop_name", "Unknown"),
                shop_data.get("shop_id", "N/A"),
            )

            if hasattr(self.db, "save_crawled_shop"):
                try:
                    self.db.save_crawled_shop(shop_data)
                except Exception as e:  # pragma: no cover - DB 오류는 크롤링에 치명적이지 않음
                    logger.warning(f"Failed to save to database: {str(e)}")

            return shop_data

        except PlaywrightTimeoutError as e:
            error_msg = f"Playwright timeout error: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error in Playwright shop crawling: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)
        finally:
            if page:
                try:
                    await page.close()
                except Exception:
                    pass
            if browser:
                try:
                    await browser.close()
                except Exception:
                    pass
            if playwright:
                try:
                    await playwright.stop()
                except Exception:
                    pass

    async def crawl_shop(self, url: str, use_playwright: bool = False) -> Dict[str, Any]:
        """Shop 페이지 크롤링 (HTTPx 또는 Playwright)."""
        import logging

        logger = logging.getLogger(__name__)

        if use_playwright and PLAYWRIGHT_AVAILABLE:
            return await self.crawl_shop_with_playwright(url)
        if use_playwright and not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not available, falling back to HTTP crawling")

        try:
            response = await self._make_request(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            shop_data: Dict[str, Any] = {
                "url": url,
                "shop_id": self._extract_shop_id(url),
                "shop_name": self._extract_shop_name(soup),
                "shop_level": self._extract_shop_level(soup),
                "follower_count": self._extract_follower_count(soup),
                "product_count": self._extract_product_count(soup),
                "categories": self._extract_shop_categories(soup),
                "products": self._extract_shop_products(soup),
                "coupons": self._extract_shop_coupons(soup),
                "crawled_with": "httpx",
            }

            if hasattr(self.db, "save_crawled_shop"):
                try:
                    self.db.save_crawled_shop(shop_data)
                except Exception:
                    pass

            return shop_data

        except httpx.HTTPError as e:
            raise Exception(f"HTTP error while crawling shop: {str(e)}")
        except Exception as e:
            raise Exception(f"Error crawling shop: {str(e)}")

    # ===================== Shop 파싱 유틸 =====================

    def _extract_shop_id(self, url: str) -> Optional[str]:
        match = re.search(r"/shop/([^/?]+)", url)
        if match:
            return match.group(1)
        return None

    def _extract_shop_name(self, soup: BeautifulSoup) -> str:
        selectors = [
            "h1.shop-name",
            "h1",
            ".shop-title",
            "[itemprop=\"name\"]",
            "#shop_name",
            ".shop_name",
            "title",
        ]

        for selector in selectors:
            if selector == "title":
                title_elem = soup.find("title")
                if not title_elem:
                    continue
                title_text = title_elem.get_text(strip=True)
                if "|" in title_text:
                    title_text = title_text.split("|")[0].strip()
                elif "｜" in title_text:
                    title_text = title_text.split("｜")[0].strip()
                if "Qoo10" in title_text:
                    title_text = title_text.replace("Qoo10", "").strip()
                if title_text:
                    return title_text
            else:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    if (
                        text
                        and len(text) > 2
                        and text not in {"홈", "Home", "トップ", "Top", "Qoo10"}
                    ):
                        return text

        return "Shop 이름 없음"

    def _extract_shop_level(self, soup: BeautifulSoup) -> Optional[str]:
        power_pattern = self._create_jp_kr_regex("POWER", "파워")
        power_jp_pattern = self._create_jp_kr_regex("パワー", "파워")
        power_patterns = [
            f"{power_pattern}\\s*(\\d+)%",
            f"{power_jp_pattern}\\s*(\\d+)%",
            f"{power_pattern}\\s*(\\d+)",
            f"{power_jp_pattern}\\s*(\\d+)",
        ]

        for pattern in power_patterns:
            power_elem = soup.find(string=re.compile(pattern, re.I))
            if not power_elem:
                continue
            match = re.search(pattern, str(power_elem), re.I)
            if not match:
                continue
            power_percent = int(match.group(1))
            if power_percent >= 90:
                return "power"
            if power_percent >= 70:
                return "excellent"

        excellent_pattern = self._create_jp_kr_regex("우수", "우수")
        normal_pattern = self._create_jp_kr_regex("일반", "일반")
        level_pattern = (
            f"{power_pattern}|{power_jp_pattern}|{excellent_pattern}|{normal_pattern}|"
            "excellent|normal|power"
        )
        level_text = soup.find(string=re.compile(level_pattern, re.I))
        if level_text:
            text = str(level_text).lower()
            power_kr = self._translate_jp_to_kr("パワー").lower()
            if "power" in text or "パワー" in text or power_kr in text:
                return "power"
            if "excellent" in text or "우수" in text:
                return "excellent"
            if "normal" in text or "일반" in text:
                return "normal"

        bypower_pattern = self._create_jp_kr_regex("byPower", "바이파워")
        power_grade = soup.find(
            string=re.compile(f"{bypower_pattern}\\s*grade|Power\\s*grade", re.I)
        )
        if power_grade:
            return "power"

        return "unknown"

    def _extract_follower_count(self, soup: BeautifulSoup) -> int:
        follower_pattern = self._create_jp_kr_regex("フォロワー", "팔로워")
        follower_patterns = [
            f"{follower_pattern}[_\\s]*(\\d{{1,3}}(?:,\\d{{3}})*)",
            f"{follower_pattern}[_\\s]*(\\d+)",
            r"follower[_\s]*(\d{1,3}(?:,\d{3})*)",
            r"follower[_\s]*(\d+)",
        ]

        for pattern in follower_patterns:
            follower_elem = soup.find(string=re.compile(pattern, re.I))
            if not follower_elem:
                continue
            match = re.search(pattern, str(follower_elem), re.I)
            if not match:
                continue
            try:
                count_str = match.group(1).replace(",", "").replace("_", "")
                return int(count_str)
            except Exception:
                continue

        follower_text = soup.find(string=re.compile(f"{follower_pattern}|follower", re.I))
        if follower_text:
            parent = follower_text.find_parent()
            if parent:
                text = parent.get_text(strip=True)
                numbers = re.findall(r"[\d,]+", text.replace(",", "").replace("_", ""))
                if numbers:
                    try:
                        return int(numbers[0])
                    except Exception:
                        pass

        return 0

    def _extract_product_count(self, soup: BeautifulSoup) -> int:
        all_product_pattern = self._create_jp_kr_regex("全ての商品", "전체상품")
        product_pattern = self._create_jp_kr_regex("商品", "상품")
        product_count_pattern = self._create_jp_kr_regex("商品数", "상품수")
        product_patterns = [
            f"{all_product_pattern}\\s*\\((\\d+)\\)",
            f"{product_pattern}.*\\((\\d+)\\)",
            f"{all_product_pattern}[：:]\\s*(\\d+)",
            f"{product_count_pattern}[：:]\\s*(\\d+)",
        ]

        for pattern in product_patterns:
            product_text = soup.find(string=re.compile(pattern, re.I))
            if not product_text:
                continue
            match = re.search(pattern, str(product_text), re.I)
            if match:
                try:
                    return int(match.group(1))
                except Exception:
                    continue

        product_selectors = [
            ".product-item",
            ".goods-item",
            "[data-goods-code]",
            "div[class*=\"product\"]",
            "div[class*=\"goods\"]",
            "div[class*=\"item\"]",
            "li[class*=\"product\"]",
            "li[class*=\"goods\"]",
        ]

        seen_products = set()
        for selector in product_selectors:
            for item in soup.select(selector):
                name = item.select_one(".product-name, .goods-name, h3, h4, [title]")
                price = item.select_one(".price, .goods-price, [class*=\"price\"]")
                if not (name or price):
                    continue
                item_id = item.get("data-goods-code") or item.get("id") or str(item)
                seen_products.add(item_id)

        return len(seen_products) if seen_products else 0

    def _extract_shop_categories(self, soup: BeautifulSoup) -> Dict[str, int]:
        categories: Dict[str, int] = {}

        category_links = soup.select(
            "a[href*=\"/category/\"], a[href*=\"/cat/\"], .category-link, [class*=\"category\"]"
        )
        for link in category_links:
            category_name = link.get_text(strip=True)
            if category_name:
                categories[category_name] = categories.get(category_name, 0) + 1

        products = self._extract_shop_products(soup)
        for product in products:
            if product.get("category"):
                categories[product["category"]] = categories.get(product["category"], 0) + 1
            if product.get("product_type"):
                categories[product["product_type"]] = categories.get(product["product_type"], 0) + 1

        return categories

    def _extract_shop_products(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        products: List[Dict[str, Any]] = []

        product_items = soup.select("div.item")
        if not product_items:
            product_items = soup.select(
                ".product-item, .goods-item, [data-goods-code], "
                ".item_list li, .goods_list li, .product-list-item, "
                "div[class*=\"item\"]",
            )
        if not product_items:
            product_items = soup.find_all("div", class_=re.compile(r"^item$|item\s", re.I))

        for item in product_items[:50]:
            product: Dict[str, Any] = {
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
                "keywords": [],
            }

            name_elem = item.select_one("a.tt")
            if name_elem:
                product["product_name"] = (
                    name_elem.get_text(strip=True) or name_elem.get("title", "")
                )
                product["product_url"] = name_elem.get("href", "")
                if product["product_url"] and product["product_url"].startswith("/"):
                    product["product_url"] = "https://www.qoo10.jp" + product["product_url"]

            if not product["product_name"]:
                name_selectors = [
                    ".product-name",
                    ".goods-name",
                    "h3",
                    "h4",
                    ".item-name",
                    ".title",
                    "a[title]",
                    "[title]",
                    ".name",
                    ".product-title",
                ]
                for selector in name_selectors:
                    name_elem = item.select_one(selector)
                    if not name_elem:
                        continue
                    product["product_name"] = (
                        name_elem.get_text(strip=True) or name_elem.get("title", "")
                    )
                    if product["product_name"]:
                        break

            thumb_elem = item.select_one("a.thmb img, .thmb img, a[class*=\"thmb\"] img")
            if thumb_elem:
                thumbnail = (
                    thumb_elem.get("src")
                    or thumb_elem.get("data-src")
                    or thumb_elem.get("data-original")
                )
                if thumbnail:
                    if thumbnail.startswith("//"):
                        thumbnail = "https:" + thumbnail
                    elif thumbnail.startswith("/"):
                        thumbnail = "https://www.qoo10.jp" + thumbnail
                    product["thumbnail"] = thumbnail

            brand_elem = item.select_one(
                ".brand_official, .brand_official button, .brand_official .txt_brand"
            )
            if brand_elem:
                brand_text = brand_elem.get_text(strip=True)
                if brand_text:
                    product["brand"] = self._translate_jp_to_kr(brand_text)

            prc_elem = item.select_one(".prc, div[class*=\"prc\"]")
            if prc_elem:
                del_elem = prc_elem.select_one("del")
                if del_elem:
                    original_text = del_elem.get_text(strip=True)
                    original_price = self._parse_price(original_text)
                    if original_price:
                        product["price"]["original_price"] = original_price

                strong_elem = prc_elem.select_one("strong")
                if strong_elem:
                    sale_text = strong_elem.get_text(strip=True)
                    sale_price = self._parse_price(sale_text)
                    if sale_price:
                        product["price"]["sale_price"] = sale_price

                if product["price"]["original_price"] and product["price"]["sale_price"]:
                    if product["price"]["original_price"] > product["price"]["sale_price"]:
                        discount = (
                            product["price"]["original_price"]
                            - product["price"]["sale_price"]
                        )
                        product["price"]["discount_rate"] = int(
                            (discount / product["price"]["original_price"]) * 100
                        )

            ship_elem = item.select_one(".ship_area .ship, .ship_area, span[class*=\"ship\"]")
            if ship_elem:
                ship_text = ship_elem.get_text()
                shipping_pattern = self._create_jp_kr_regex("送料", "배송비")
                shipping_match = re.search(
                    rf"Shipping\\s*rate[：:]\\s*(?P<fee1>\d{{1,3}}(?:,\d{{3}})*)円|"
                    rf"{shipping_pattern}[：:]\\s*(?P<fee2>\d{{1,3}}(?:,\d{{3}})*)円|"
                    r"(?P<fee3>\d{1,3}(?:,\d{3})*)円",
                    ship_text,
                )
                if shipping_match:
                    fee_str = (
                        shipping_match.group("fee1")
                        or shipping_match.group("fee2")
                        or shipping_match.group("fee3")
                    )
                    shipping_fee = self._parse_price(fee_str)
                    if shipping_fee:
                        product["shipping_info"]["shipping_fee"] = shipping_fee

                free_shipping_pattern = self._create_jp_kr_regex("送料無料", "무료배송")
                above_pattern = self._create_jp_kr_regex("以上購入", "이상구매")
                free_shipping_match = re.search(
                    rf"(?P<threshold1>\d{{1,3}}(?:,\d{{3}})*)円\\s*{above_pattern}.*{free_shipping_pattern}|"
                    rf"(?P<threshold2>\d{{1,3}}(?:,\d{{3}})*)円.*無料",
                    ship_text,
                )
                if free_shipping_match:
                    threshold_str = (
                        free_shipping_match.group("threshold1")
                        or free_shipping_match.group("threshold2")
                    )
                    threshold = self._parse_price(threshold_str)
                    if threshold:
                        product["shipping_info"]["free_shipping_threshold"] = threshold

            review_pattern = self._create_jp_kr_regex("レビュー", "리뷰")
            review_elem = item.find(
                string=re.compile(rf"{review_pattern}.*\((\d+)\)", re.I)
            )
            if review_elem:
                review_match = re.search(r"\((\d+)\)", str(review_elem))
                if review_match:
                    product["review_count"] = int(review_match.group(1))

            if not product["product_name"]:
                text = item.get_text(strip=True)
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                for line in lines:
                    if len(line) > 10 and line not in {"홈", "Home", "トップ", "Top"}:
                        product["product_name"] = line[:100]
                        break

            if product["product_name"]:
                product["product_type"] = self._detect_product_type(product["product_name"])
                product["keywords"] = self._extract_product_keywords(product["product_name"])

            if product["product_name"] and len(product["product_name"].strip()) > 3:
                products.append(product)

        return products

    def _detect_product_type(self, product_name: str) -> Optional[str]:
        product_name_lower = product_name.lower()

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
        }

        for product_type, keywords in product_types.items():
            for keyword in keywords:
                if keyword in product_name_lower:
                    return product_type

        return "기타"

    def _extract_product_keywords(self, product_name: str) -> List[str]:
        keywords: List[str] = []
        words = re.findall(r"\b\w+\b", product_name, re.UNICODE)
        for word in words:
            if len(word) >= 2:
                keywords.append(word)
        return keywords[:10]

    def _extract_shop_coupons(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        coupons: List[Dict[str, Any]] = []
        seen_coupons = set()

        page_text = soup.get_text()

        above_pattern = self._create_jp_kr_regex("以上", "이상")
        discount_pattern = self._create_jp_kr_regex("割引", "할인")

        coupon_patterns = [
            rf"(?P<amount>\d{{1,3}}(?:,\d{{3}})*)円{above_pattern}.*?(?P<rate>\d+)%off",
            rf"(?P<amount>\d{{1,3}}(?:,\d{{3}})*)円{above_pattern}.*?(?P<rate>\d+)%{discount_pattern}",
            rf"(?P<rate>\d+)%off.*?(?P<amount>\d{{1,3}}(?:,\d{{3}})*)円{above_pattern}",
            rf"(?P<rate>\d+)%{discount_pattern}.*?(?P<amount>\d{{1,3}}(?:,\d{{3}})*)円{above_pattern}",
        ]

        for pattern in coupon_patterns:
            for match in re.finditer(pattern, page_text, re.I):
                amount_str = match.group("amount")
                rate_str = match.group("rate")
                coupon_key = f"{amount_str}_{rate_str}"
                if coupon_key in seen_coupons:
                    continue
                seen_coupons.add(coupon_key)

                min_amount = self._parse_price(amount_str)
                discount_rate = int(rate_str) if rate_str.isdigit() else 0
                if discount_rate > 0 or (min_amount or 0) > 0:
                    coupons.append(
                        {
                            "discount_rate": discount_rate,
                            "min_amount": min_amount,
                            "valid_until": None,
                            "description": match.group(0),
                        }
                    )

        coupon_selectors = [
            ".coupon-item",
            ".discount-coupon",
            "div[class*=\"coupon\"]",
            "li[class*=\"coupon\"]",
            "[class*=\"クーポン\"]",
            "[class*=\"割引\"]",
            "div[class*=\"off\"]",
        ]

        for selector in coupon_selectors:
            for elem in soup.select(selector):
                discount_text = elem.get_text(strip=True) if elem else ""
                if not discount_text:
                    continue

                discount_pattern_local = self._create_jp_kr_regex("割引", "할인")
                discount_patterns = [
                    r"(?P<rate>\d+)%off",
                    r"(?P<rate>\d+)%OFF",
                    rf"(?P<rate>\d+)%{discount_pattern_local}",
                    r"(?P<rate>\d+)%",
                    r"off\s*(?P<rate>\d+)%",
                    rf"{discount_pattern_local}\s*(?P<rate>\d+)%",
                ]

                discount_rate = 0
                for pattern in discount_patterns:
                    m = re.search(pattern, discount_text, re.I)
                    if m:
                        rate_str = m.group("rate")
                        if rate_str.isdigit():
                            discount_rate = int(rate_str)
                            break

                above_purchase_pattern = self._create_jp_kr_regex("以上購入", "이상구매")
                amount_patterns = [
                    rf"(?P<amount>\d{{1,3}}(?:,\d{{3}})*)[,円]{above_pattern}",
                    rf"(?P<amount>\d+)[,円]{above_pattern}",
                    rf"(?P<amount>\d{{1,3}}(?:,\d{{3}})*)[,円]{above_pattern}の",
                    rf"(?P<amount>\d+)[,円]{above_pattern}の",
                    rf"(?P<amount>\d{{1,3}}(?:,\d{{3}})*)[,円]{above_purchase_pattern}",
                    rf"(?P<amount>\d+)[,円]{above_purchase_pattern}",
                ]

                min_amount = 0
                for pattern in amount_patterns:
                    m = re.search(pattern, discount_text)
                    if not m:
                        continue
                    amount_str = m.group("amount").replace(",", "")
                    if amount_str.isdigit():
                        min_amount = int(amount_str)
                        break

                valid_until = None
                date_patterns = [
                    r"(\d{4}\.\d{2}\.\d{2})\s*[~〜]\s*(\d{4}\.\d{2}\.\d{2})",
                    r"(\d{4}-\d{2}-\d{2})\s*[~〜]\s*(\d{4}-\d{2}-\d{2})",
                    r"(\d{4}/\d{2}/\d{2})\s*[~〜]\s*(\d{4}/\d{2}/\d{2})",
                ]
                for pattern in date_patterns:
                    m = re.search(pattern, discount_text)
                    if m:
                        valid_until = m.group(2)
                        break

                description = discount_text[:100]
                coupon_key = f"{discount_rate}_{min_amount}_{description}"
                if discount_rate > 0 and coupon_key not in seen_coupons:
                    seen_coupons.add(coupon_key)
                    coupons.append(
                        {
                            "discount_rate": discount_rate,
                            "min_amount": min_amount,
                            "valid_until": valid_until,
                            "description": description,
                        }
                    )

        return coupons
