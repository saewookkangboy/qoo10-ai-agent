"""
Qoo10 큐텐 대학 한국어 메뉴얼 검증 서비스
현재 메뉴얼 마크다운 파일과 크롤링 결과를 비교하여 누락·추가·오래된 항목을 정밀 분석합니다.
데이터 파이프라인에서 누락 데이터 반영 및 메뉴얼 최신화에 사용됩니다.
"""
import re
import os
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path
from urllib.parse import urlparse, urlunparse, quote, unquote

logger = logging.getLogger(__name__)

# Known item titles → correct section (overrides crawler section when building missing_in_manual_items)
ITEM_TITLE_SECTION_OVERRIDES: List[Tuple[str, str]] = [
    ("JQSM(판매 관리 툴) 용어 모음", "판매 준비하기"),
    ("고객 클레임을 최소화하는 취소 처리 대응 방법", "주문・배송・고객 관리하기"),
    ("메가할인 기간 매출 극대화 전략", "광고・프로모션 활용하기"),
]


def _section_for_missing_item(section_from_crawler: str, item_title: str) -> str:
    """Apply explicit overrides for known titles; otherwise use crawler section."""
    for key, section in ITEM_TITLE_SECTION_OVERRIDES:
        if key in (item_title or "") or (item_title or "").startswith(key):
            return section
    return section_from_crawler


def normalize_url_for_comparison(u: Optional[str]) -> str:
    """
    URL을 비교/병합 시 일관되게 쓰기 위해 정규화합니다.
    - 앞뒤 공백 제거, trailing slash 제거
    - path: percent-encoding 정규화 (unquote 후 UTF-8 quote로 통일, raw 한글과 %EB%8B... 등 동일하게 비교)
    - scheme/host 소문자, 기본 포트(80/443) 제거
    - fragment(#), query(?) 제거
    """
    if u is None or not isinstance(u, str):
        return ""
    u = u.strip()
    if not u:
        return ""
    try:
        p = urlparse(u)
        scheme = (p.scheme or "https").lower()
        hostname = (p.hostname or p.netloc or "").lower()
        port = p.port
        if port is not None and (scheme, port) in (("http", 80), ("https", 443)):
            port = None
        netloc = f"{hostname}:{port}" if port is not None else hostname
        path = (p.path or "/").strip()
        path = path.rstrip("/") or "/"
        path = quote(unquote(path), safe="/", encoding="utf-8")
        return urlunparse((scheme, netloc, path, "", "", ""))
    except Exception:
        return (u or "").strip().rstrip("/") or ""

# 프로젝트 루트 기준 메뉴얼 파일 경로
DEFAULT_MANUAL_PATH = "doc/Qoo10_큐텐대학_한국어_메뉴얼.md"


def find_manual_path(manual_path: Optional[str] = None) -> Optional[Path]:
    """메뉴얼 파일 절대 경로 반환. api/에서 실행 시 상위 doc/ 검색."""
    if manual_path and os.path.isfile(manual_path):
        return Path(manual_path).resolve()
    # api/services 등에서 실행 시 프로젝트 루트 기준
    for base in (Path(__file__).resolve().parent.parent.parent, Path.cwd(), Path.cwd().parent):
        p = base / "doc" / "Qoo10_큐텐대학_한국어_메뉴얼.md"
        if p.is_file():
            return p
        p = base / "Qoo10_큐텐대학_한국어_메뉴얼.md"
        if p.is_file():
            return p
    return None


def parse_manual_markdown(content: str) -> Dict[str, Any]:
    """
    메뉴얼 마크다운에서 구조 추출.
    - sections: [ { "title": "1. 입점 검토하기", "anchor": "입점-검토하기", "items": [ {"title": "...", "더보기_url": "..." } ] } ]
    - all_더보기_urls: [...]
    - toc_titles: 목차에 나온 제목 목록
    """
    sections: List[Dict[str, Any]] = []
    all_더보기_urls: List[str] = []
    toc_titles: List[str] = []

    # 목차: 1. [입점 검토하기](#...) 형태
    for m in re.finditer(r"^\d+\.\s*\[([^\]]+)\]\(#([^)]+)\)", content, re.MULTILINE):
        toc_titles.append(m.group(1).strip())

    # ## 1. 입점 검토하기
    section_pattern = re.compile(r"^##\s+(.+?)(?=\n|$)", re.MULTILINE)
    # #### 제목 ... **[더보기](url)**
    item_pattern = re.compile(r"^####\s+(.+?)(?=\n|$)", re.MULTILINE)
    더보기_pattern = re.compile(r"\*\*\[더보기\]\((https?://[^)]+)\)\*\*")

    current_section: Optional[Dict[str, Any]] = None
    for line in content.split("\n"):
        sec_m = section_pattern.match(line.strip())
        if sec_m:
            title = sec_m.group(1).strip()
            anchor = re.sub(r"[^\w\s-]", "", title).strip()
            anchor = re.sub(r"\s+", "-", anchor)
            current_section = {
                "title": title,
                "anchor": anchor,
                "items": [],
            }
            sections.append(current_section)
            continue

        item_m = item_pattern.match(line.strip())
        if item_m and current_section:
            item_title = item_m.group(1).strip()
            current_section["items"].append({"title": item_title, "더보기_url": None})

        # 같은 블록 내 **[더보기](url)** 찾기 (이전 항목에 붙임)
        for url_m in 더보기_pattern.finditer(line):
            url = url_m.group(1)
            all_더보기_urls.append(url)
            if current_section and current_section["items"]:
                current_section["items"][-1]["더보기_url"] = url

    return {
        "sections": sections,
        "all_더보기_urls": list(dict.fromkeys(all_더보기_urls)),
        "toc_titles": toc_titles,
    }


def validate_manual_vs_crawled(
    manual_content: str,
    crawled: Dict[str, Any],
    manual_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    메뉴얼 내용과 크롤링 결과를 비교하여 누락·추가 항목을 분석합니다.

    Returns:
        - manual_parsed: 파싱된 메뉴얼 구조
        - missing_sections: 크롤러에는 있으나 메뉴얼에 없는 섹션
        - missing_links: 크롤러에 있으나 메뉴얼 더보기에 없는 URL
        - missing_in_manual_items: 섹션별로 메뉴얼에 없는 항목 제목
        - extra_in_manual: 메뉴얼에만 있는 더보기 URL (삭제된 페이지일 수 있음)
        - coverage_score: 0~100
        - suggestions: 개선 제안
    """
    manual_parsed = parse_manual_markdown(manual_content)
    topic = crawled.get("topic") or {}
    beginner = crawled.get("beginner_category") or {}
    expected_titles = crawled.get("expected_section_titles") or []

    missing_sections: List[str] = []
    missing_links: List[Dict[str, str]] = []
    missing_in_manual_items: List[Dict[str, Any]] = []
    extra_in_manual: List[str] = []
    suggestions: List[str] = []

    # 정규화된 URL로 비교하여 trailing slash / encoding / fragment 차이로 인한 오매칭 방지
    _all_더보기 = manual_parsed.get("all_더보기_urls") or []
    manual_urls_normalized: Set[str] = {normalize_url_for_comparison(u) for u in _all_더보기}
    manual_entry_ids: Set[str] = set()
    for u in _all_더보기:
        m = re.search(r"/entry/(\d+)", u)
        if m:
            manual_entry_ids.add(m.group(1))
    manual_section_titles = {s["title"] for s in manual_parsed.get("sections") or []}
    # 목차/헤딩에서 숫자 제거 후 비교용
    manual_section_titles_normalized = set()
    for t in manual_section_titles:
        normalized = re.sub(r"^\d+\.\s*", "", t).strip()
        manual_section_titles_normalized.add(normalized)

    # 1) 기대 섹션 중 메뉴얼에 없는 것
    for exp in expected_titles:
        if not any(exp in t or t.endswith(exp) for t in manual_section_titles_normalized):
            if not any(exp in t for t in manual_section_titles):
                missing_sections.append(exp)

    # 2) 크롤링된 링크 중 메뉴얼 더보기에 없는 URL (정규화된 URL로 비교)
    crawled_url_list: List[str] = []
    for link in topic.get("all_links") or []:
        url = link.get("url") or ""
        if url and "article-university.qoo10.jp" in url:
            crawled_url_list.append(url)
    for art in beginner.get("articles") or []:
        url = art.get("url") or ""
        if url:
            crawled_url_list.append(url)
    crawled_urls_normalized: Set[str] = {normalize_url_for_comparison(u) for u in crawled_url_list}

    for url in crawled_url_list:
        u_norm = normalize_url_for_comparison(url)
        if u_norm in manual_urls_normalized:
            continue
        if "entry/" in url:
            entry_id = re.search(r"/entry/(\d+)", url)
            if entry_id and entry_id.group(1) in manual_entry_ids:
                continue
            missing_links.append({"url": url, "source": "crawled"})
        else:
            missing_links.append({"url": url, "source": "crawled"})

    # 3) 메뉴얼에만 있는 URL (크롤러에 없음) → 삭제/이동된 페이지 가능 (정규화된 URL로 비교)
    for url in _all_더보기:
        u_norm = normalize_url_for_comparison(url)
        if u_norm in crawled_urls_normalized:
            continue
        if "article-university.qoo10.jp" not in url:
            continue
        if "#" in url and normalize_url_for_comparison(url.split("#")[0]) in crawled_urls_normalized:
            continue
        extra_in_manual.append(url)

    # 4) 크롤링된 섹션별 항목 제목이 메뉴얼에 없는 경우 (section, item_title, url) 기준 중복 제거)
    # section_index로 동일 section_title이 반복될 때 구분 가능 (고유 식별자)
    seen_missing_key: set = set()  # (section, item_title, url) tuple
    for sec in topic.get("sections") or []:
        section_title = sec.get("section_title") or ""
        section_index = sec.get("section_index")
        for link in sec.get("links") or []:
            title = (link.get("title") or "").strip()
            if not title or title == "더보기":
                continue
            found = False
            for ms in manual_parsed.get("sections") or []:
                if section_title not in ms.get("title", "") and ms.get("title") not in section_title:
                    continue
                for it in ms.get("items") or []:
                    if title in (it.get("title") or "") or (it.get("title") or "") in title:
                        found = True
                        break
                if found:
                    break
            if not found:
                url_val = link.get("url") or ""
                key = (section_title, title, url_val)
                if key not in seen_missing_key:
                    seen_missing_key.add(key)
                    section_assigned = _section_for_missing_item(section_title, title)
                    item = {
                        "section": section_assigned,
                        "item_title": title,
                        "url": link.get("url"),
                    }
                    if section_index is not None:
                        item["section_index"] = section_index
                    missing_in_manual_items.append(item)

    # Dedupe missing_in_manual_items by normalized URL (first occurrence wins, order preserved)
    seen_url: Set[str] = set()
    deduped: List[Dict[str, Any]] = []
    for it in missing_in_manual_items:
        u = it.get("url") or ""
        u_norm = normalize_url_for_comparison(u)
        if u_norm not in seen_url:
            seen_url.add(u_norm)
            deduped.append(it)
    missing_in_manual_items = deduped

    # 5) coverage_score
    total_expected = len(crawled_url_list) + len(expected_titles)
    if total_expected == 0:
        coverage_score = 100.0
    else:
        missing_count = len(missing_links) + len(missing_sections) + len(missing_in_manual_items)
        coverage_score = max(0.0, 100.0 - (missing_count / max(1, total_expected) * 50))

    if missing_sections:
        suggestions.append("메뉴얼에 다음 섹션을 추가하세요: " + ", ".join(missing_sections))
    if missing_links:
        suggestions.append("크롤링된 링크 중 메뉴얼에 반영되지 않은 URL이 %d건 있습니다. 해당 항목에 **[더보기](url)** 를 추가하세요." % len(missing_links))
    if missing_in_manual_items:
        suggestions.append("섹션별 항목 제목이 메뉴얼에 없습니다. 항목 및 더보기 링크를 추가하세요.")
    if extra_in_manual:
        suggestions.append("메뉴얼에만 있는 URL이 %d건 있습니다. 삭제/이동된 페이지면 정리하세요." % len(extra_in_manual))

    return {
        "manual_parsed": manual_parsed,
        "missing_sections": missing_sections,
        "missing_links": missing_links,
        "missing_in_manual_items": missing_in_manual_items,
        "extra_in_manual": extra_in_manual,
        "coverage_score": round(coverage_score, 1),
        "suggestions": suggestions,
        "summary": {
            "crawled_links_count": len(crawled_url_list),
            "manual_더보기_count": len(_all_더보기),
            "missing_links_count": len(missing_links),
            "missing_sections_count": len(missing_sections),
        },
    }


def load_and_validate(
    crawled: Dict[str, Any],
    manual_path: Optional[str] = None,
) -> Dict[str, Any]:
    """메뉴얼 파일을 읽어서 검증 결과 반환. 파일이 없으면 오류 포함."""
    path = find_manual_path(manual_path)
    if not path or not path.is_file():
        return {
            "manual_parsed": None,
            "missing_sections": [],
            "missing_links": [],
            "missing_in_manual_items": [],
            "extra_in_manual": [],
            "coverage_score": 0.0,
            "suggestions": ["메뉴얼 파일을 찾을 수 없습니다: doc/Qoo10_큐텐대학_한국어_메뉴얼.md"],
            "summary": {},
            "error": "manual_file_not_found",
            "manual_path": str(manual_path or DEFAULT_MANUAL_PATH),
        }
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "manual_parsed": None,
            "missing_sections": [],
            "missing_links": [],
            "missing_in_manual_items": [],
            "extra_in_manual": [],
            "coverage_score": 0.0,
            "suggestions": [f"메뉴얼 파일 읽기 실패: {e}"],
            "summary": {},
            "error": str(e),
            "manual_path": str(path),
        }
    result = validate_manual_vs_crawled(content, crawled, manual_path)
    result["manual_path"] = str(path)
    return result
