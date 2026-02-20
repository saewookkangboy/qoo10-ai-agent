"""
Qoo10 큐텐 대학 한국어 메뉴얼 수집 서비스
article-university.qoo10.jp 페이지에서 유형별 판매 노하우 및 단계별 교육(초급) 목록·링크를 수집합니다.
데이터 파이프라인에서 메뉴얼 최신화 및 누락 데이터 분석에 사용됩니다.
"""
import re
import asyncio
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# 큐텐 대학 한국어 메인 페이지
QOO10_UNIVERSITY_KR_TOPIC = "https://article-university.qoo10.jp/qoo10-selling-tips_kor"
# 단계별 교육 (초급) 카테고리
QOO10_UNIVERSITY_KR_BEGINNER = "https://article-university.qoo10.jp/archive/category/%EB%8B%A8%EA%B3%84%EB%B3%84%20%EA%B5%90%EC%9C%A1%20(%EC%B4%88%EA%B8%89)"


class Qoo10ManualCrawler:
    """Qoo10 큐텐 대학 한국어 메뉴얼 전용 크롤러"""

    def __init__(self, timeout: float = 25.0):
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
                },
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def fetch_html(self, url: str) -> str:
        """URL에서 HTML 텍스트 조회"""
        client = await self._get_client()
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text
        except httpx.HTTPError as e:
            logger.warning("manual_crawler fetch %s: %s", url, e)
            return ""

    def _parse_topic_page(self, html: str, base_url: str) -> Dict[str, Any]:
        """
        유형별 판매 노하우 메인 페이지 파싱.
        섹션(제목), 항목(제목+링크), 더보기 링크를 추출합니다.
        """
        soup = BeautifulSoup(html, "html.parser")
        sections: List[Dict[str, Any]] = []
        all_links: List[Dict[str, str]] = []

        # 목차에 해당하는 섹션: listitem / heading + list
        for block in soup.find_all(["section", "li", "div"], recursive=True):
            heading = block.find(["h2", "h3", "h4"])
            if not heading:
                continue
            title = (heading.get_text() or "").strip()
            if not title or title in ("日本語", "한국어", "Qoo10大学"):
                continue

            links_in_block: List[Dict[str, str]] = []
            for a in block.find_all("a", href=True):
                href = a.get("href", "")
                text = (a.get_text() or "").strip()
                if not href or href.startswith("#"):
                    continue
                full_url = urljoin(base_url, href)
                if "article-university.qoo10.jp" not in full_url:
                    continue
                links_in_block.append({"title": text or full_url, "url": full_url})
                all_links.append({"title": text or full_url, "url": full_url})

            if title and (links_in_block or "더보기" in block.get_text()):
                # 더보기 링크만 있는 경우도 수집
                for a in block.find_all("a", href=True):
                    if (a.get_text() or "").strip() == "더보기":
                        href = a.get("href", "")
                        if href and "article-university" in urljoin(base_url, href):
                            full_url = urljoin(base_url, href)
                            if not any(l["url"] == full_url for l in links_in_block):
                                links_in_block.append({"title": "더보기", "url": full_url})
                                all_links.append({"title": "더보기", "url": full_url})
                sections.append({
                    "section_title": title,
                    "links": links_in_block,
                })

        # 링크만 있고 섹션으로 묶이지 않은 경우: a[href*="article-university"] 전부 수집
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if "article-university.qoo10.jp" not in urljoin(base_url, href):
                continue
            full_url = urljoin(base_url, href)
            text = (a.get_text() or "").strip()
            if full_url not in [x["url"] for x in all_links]:
                all_links.append({"title": text or full_url, "url": full_url})

        return {
            "source_url": base_url,
            "sections": sections,
            "all_links": all_links,
            "crawled_with": "httpx",
        }

    def _parse_beginner_category_page(self, html: str, base_url: str) -> Dict[str, Any]:
        """단계별 교육 (초급) 카테고리 페이지 파싱. 글 제목 + 링크 수집."""
        soup = BeautifulSoup(html, "html.parser")
        articles: List[Dict[str, str]] = []
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if "article-university.qoo10.jp" not in urljoin(base_url, href):
                continue
            full_url = urljoin(base_url, href)
            text = (a.get_text() or "").strip()
            # 긴 제목(교육 제목)만 수집. 날짜 패턴(2025-11-27 등) 옆 제목
            if len(text) > 5 and "단계별" in text or "초보" in text or "교육" in text or "탄!" in text:
                articles.append({"title": text, "url": full_url})
            elif re.match(r"^\d{4}\s*-\s*\d{2}\s*-\s*\d{2}", text):
                # 날짜만 있는 링크는 다음 형제에서 제목 찾기
                parent = a.parent
                if parent:
                    next_heading = parent.find(["h2", "h3", "h4"])
                    if next_heading:
                        t = (next_heading.get_text() or "").strip()
                        if t and t not in [x["title"] for x in articles]:
                            articles.append({"title": t, "url": full_url})

        # heading 링크 조합: section > a + heading
        for section in soup.find_all(["section", "article", "div"], class_=re.compile(r"entry|article|card")):
            link = section.find("a", href=True)
            heading = section.find(["h1", "h2", "h3", "h4"])
            if link and heading:
                href = link.get("href", "")
                if "article-university.qoo10.jp" not in urljoin(base_url, href):
                    continue
                full_url = urljoin(base_url, href)
                title = (heading.get_text() or "").strip()
                if title and not any(x["url"] == full_url for x in articles):
                    articles.append({"title": title, "url": full_url})

        return {
            "source_url": base_url,
            "category": "단계별 교육 (초급)",
            "articles": articles,
            "crawled_with": "httpx",
        }

    async def crawl_topic_page(self) -> Dict[str, Any]:
        """유형별 판매 노하우 메인 페이지 수집"""
        html = await self.fetch_html(QOO10_UNIVERSITY_KR_TOPIC)
        if not html:
            return {"source_url": QOO10_UNIVERSITY_KR_TOPIC, "sections": [], "all_links": [], "crawled_with": "httpx", "error": "empty_html"}
        return self._parse_topic_page(html, QOO10_UNIVERSITY_KR_TOPIC)

    async def crawl_beginner_category(self) -> Dict[str, Any]:
        """단계별 교육 (초급) 카테고리 페이지 수집"""
        html = await self.fetch_html(QOO10_UNIVERSITY_KR_BEGINNER)
        if not html:
            return {"source_url": QOO10_UNIVERSITY_KR_BEGINNER, "category": "단계별 교육 (초급)", "articles": [], "crawled_with": "httpx", "error": "empty_html"}
        return self._parse_beginner_category_page(html, QOO10_UNIVERSITY_KR_BEGINNER)

    async def crawl_all(self) -> Dict[str, Any]:
        """메인 토픽 + 단계별 교육 카테고리 모두 수집"""
        topic = await self.crawl_topic_page()
        beginner = await self.crawl_beginner_category()
        return {
            "topic": topic,
            "beginner_category": beginner,
            "expected_section_titles": [
                "입점 검토하기",
                "판매 준비하기",
                "주문・배송・고객 관리하기",
                "판매 데이터 관리・분석하기",
                "매출 증대시키기",
                "광고・프로모션 활용하기",
                "메가할인・메가포 대비하기",
                "세미나 다시보기",
                "트렌드 인사이트",
                "단계별 교육 (초급)",
            ],
        }
