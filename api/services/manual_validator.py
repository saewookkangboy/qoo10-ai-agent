"""
Qoo10 큐텐 대학 한국어 메뉴얼 검증 서비스
현재 메뉴얼 마크다운 파일과 크롤링 결과를 비교하여 누락·추가·오래된 항목을 정밀 분석합니다.
데이터 파이프라인에서 누락 데이터 반영 및 메뉴얼 최신화에 사용됩니다.
"""
import re
import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

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

    manual_urls = set(manual_parsed.get("all_더보기_urls") or [])
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

    # 2) 크롤링된 링크 중 메뉴얼 더보기에 없는 URL
    crawled_urls = set()
    for link in topic.get("all_links") or []:
        url = link.get("url") or ""
        if url and "article-university.qoo10.jp" in url:
            crawled_urls.add(url)
    for art in beginner.get("articles") or []:
        url = art.get("url") or ""
        if url:
            crawled_urls.add(url)

    for url in crawled_urls:
        if url not in manual_urls:
            # entry/130 등 상세 페이지는 메뉴얼에 있으면 동일 도메인으로만 체크
            if "entry/" in url:
                # 메뉴얼에 같은 entry가 있는지
                entry_id = re.search(r"/entry/(\d+)", url)
                if entry_id:
                    if not any(entry_id.group(1) in u for u in manual_urls):
                        missing_links.append({"url": url, "source": "crawled"})
            else:
                missing_links.append({"url": url, "source": "crawled"})

    # 3) 메뉴얼에만 있는 URL (크롤러에 없음) → 삭제/이동된 페이지 가능
    for url in manual_urls:
        if url not in crawled_urls and "article-university.qoo10.jp" in url:
            # 카테고리/해시 링크는 제외
            if "#" in url and url.split("#")[0] in crawled_urls:
                continue
            extra_in_manual.append(url)

    # 4) 크롤링된 섹션별 항목 제목이 메뉴얼에 없는 경우
    for sec in topic.get("sections") or []:
        section_title = sec.get("section_title") or ""
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
                missing_in_manual_items.append({
                    "section": section_title,
                    "item_title": title,
                    "url": link.get("url"),
                })

    # 5) coverage_score
    total_expected = len(crawled_urls) + len(expected_titles)
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
            "crawled_links_count": len(crawled_urls),
            "manual_더보기_count": len(manual_urls),
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
