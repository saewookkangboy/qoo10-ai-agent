"""
Manual pipeline result data cleaner.
Post-crawl step: remove placeholders, dedupe, normalize URLs/language, merge duplicate blocks, schema validation.
Prevents regrowth of "<<max depth>>", duplicated validation/missing_analysis, and mixed-language entries.
"""
import re
import logging
from typing import Dict, Any, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

PLACEHOLDER = "<<max depth>>"

# Canonical section titles (Korean) for normalization
EXPECTED_SECTION_TITLES = [
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
]

# Japanese → Korean section title mapping for normalization
SECTION_TITLE_NORMALIZE: Dict[str, str] = {
    "qoo10管理画面はこちら": "Qoo10 관리 화면",
    "ショップ運営ノウハウ": "쇼핑몰 운영 노하우",
}


def _norm_url(u: Optional[str]) -> str:
    if u is None or not isinstance(u, str):
        return ""
    return u.strip().rstrip("/") or ""


def _is_placeholder(v: Any) -> bool:
    return v == PLACEHOLDER or (isinstance(v, str) and v.strip() == PLACEHOLDER)


def remove_or_mark_placeholders_in_sections(sections: List[Dict[str, Any]], mark: bool = False) -> List[Dict[str, Any]]:
    """
    Remove link/item entries where title and url/더보기_url are placeholders.
    If mark=True, replace placeholder with a flag instead of removing.
    """
    out: List[Dict[str, Any]] = []
    for sec in sections:
        if not isinstance(sec, dict):
            out.append(sec)
            continue
        new_sec = dict(sec)
        links_key = "links" if "links" in new_sec else "items"
        key_url = "url" if links_key == "links" else "더보기_url"
        items = new_sec.get(links_key) or []
        if not isinstance(items, list):
            out.append(new_sec)
            continue
        cleaned: List[Dict[str, Any]] = []
        for it in items:
            if not isinstance(it, dict):
                continue
            title = it.get("title")
            url_val = it.get(key_url)
            if _is_placeholder(title) and _is_placeholder(url_val):
                if mark:
                    cleaned.append({"title": "__placeholder_removed__", key_url: ""})
                continue
            it = dict(it)
            if _is_placeholder(title):
                it["title"] = ""
            if _is_placeholder(url_val):
                it[key_url] = ""
            cleaned.append(it)
        new_sec[links_key] = cleaned
        out.append(new_sec)
    return out


def merge_validation_and_missing_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    If both 'validation' and 'missing_analysis' exist at top level, keep 'validation' and merge
    any keys from missing_analysis that are not already in validation; then remove 'missing_analysis'.
    """
    if "missing_analysis" not in data or "validation" not in data:
        return data
    val = data.get("validation") or {}
    ma = data.get("missing_analysis") or {}
    if not isinstance(val, dict) or not isinstance(ma, dict):
        return data
    for k, v in ma.items():
        if k not in val:
            val = dict(val)
            val[k] = v
    data = dict(data)
    data["validation"] = val
    del data["missing_analysis"]
    logger.info("Merged missing_analysis into validation and removed duplicate top-level block.")
    return data


def dedupe_by_url_title(
    items: List[Dict[str, Any]],
    url_key: str = "url",
    title_key: str = "title",
    extra_keys: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Deduplicate by normalized URL; if URL is same, by title. Preserves order (first occurrence wins)."""
    seen: Set[Tuple[str, str]] = set()
    out: List[Dict[str, Any]] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        u = _norm_url(it.get(url_key))
        t = (it.get(title_key) or "").strip()
        if extra_keys:
            key = (u, t, *(str(it.get(k) or "") for k in extra_keys))
        else:
            key = (u, t)
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def dedupe_missing_in_manual_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate by (section, item_title, url)."""
    seen: Set[Tuple[str, str, str]] = set()
    out: List[Dict[str, Any]] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        sec = (it.get("section") or "").strip()
        title = (it.get("item_title") or "").strip()
        u = _norm_url(it.get("url"))
        key = (sec, title, u)
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def dedupe_all_links(links: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate by normalized URL, then by title."""
    return dedupe_by_url_title(links, url_key="url", title_key="title")


def normalize_section_title(title: Optional[str]) -> str:
    """Normalize section title: strip, optional Japanese→Korean map."""
    if not title or not isinstance(title, str):
        return ""
    t = title.strip()
    # Remove leading "N. " for comparison
    t_lower = re.sub(r"^\d+\.\s*", "", t).strip().lower()
    for jp, ko in SECTION_TITLE_NORMALIZE.items():
        jp_lower = jp.lower()
        if t_lower == jp_lower or re.search(rf"\b{re.escape(jp)}\b", t_lower, re.IGNORECASE) is not None:
            return ko
    return t


def normalize_anchor(anchor: Optional[str]) -> str:
    """Normalize anchor: alphanumeric, spaces to hyphens."""
    if not anchor or not isinstance(anchor, str):
        return ""
    a = re.sub(r"[^\w\s\-]", "", anchor).strip()
    a = re.sub(r"\s+", "-", a)
    return a


def normalize_language_and_urls_in_links(links: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize URL (strip, rstrip /) and ensure title is string; prefer Korean '더보기' over mixed."""
    out: List[Dict[str, Any]] = []
    for it in links:
        if not isinstance(it, dict):
            continue
        it = dict(it)
        it["url"] = _norm_url(it.get("url"))
        title = it.get("title")
        if title is not None and not isinstance(title, str):
            it["title"] = str(title).strip()
        elif title == "More" or (isinstance(title, str) and title.strip().lower() == "more"):
            it["title"] = "더보기"
        out.append(it)
    return out


def normalize_manual_parsed_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize manual_parsed.sections[].items: title (More→더보기), 더보기_url normalized."""
    out: List[Dict[str, Any]] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        it = dict(it)
        url_val = it.get("더보기_url")
        it["더보기_url"] = _norm_url(url_val) or (url_val if isinstance(url_val, str) else "")
        title = it.get("title")
        if title is not None and not isinstance(title, str):
            it["title"] = str(title).strip()
        elif title == "More" or (isinstance(title, str) and title.strip().lower() == "more"):
            it["title"] = "더보기"
        out.append(it)
    return out


def normalize_manual_parsed_sections(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize manual_parsed.sections: anchors, item titles/URLs, language."""
    out: List[Dict[str, Any]] = []
    for sec in sections:
        if not isinstance(sec, dict):
            out.append(sec)
            continue
        sec = dict(sec)
        sec["anchor"] = normalize_anchor(sec.get("anchor"))
        items = sec.get("items") or []
        sec["items"] = normalize_manual_parsed_items(items if isinstance(items, list) else [])
        out.append(sec)
    return out


def schema_validate(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate expected schema; return a small report dict with errors/warnings.
    Expected: crawled.expected_section_titles, validation.coverage_score, validation.summary.manual_더보기_count (or len(all_더보기_urls)).
    """
    report: Dict[str, Any] = {"valid": True, "errors": [], "warnings": []}
    crawled = data.get("crawled") or {}
    validation = data.get("validation") or {}

    if not isinstance(crawled, dict):
        report["errors"].append("crawled is not an object")
        report["valid"] = False
    else:
        if "expected_section_titles" not in crawled:
            report["warnings"].append("crawled.expected_section_titles missing")
        elif not isinstance(crawled.get("expected_section_titles"), list):
            report["warnings"].append("crawled.expected_section_titles should be a list")

    if not isinstance(validation, dict):
        report["errors"].append("validation is not an object")
        report["valid"] = False
    else:
        if "coverage_score" not in validation:
            report["warnings"].append("validation.coverage_score missing")
        elif not isinstance(validation.get("coverage_score"), (int, float)):
            report["warnings"].append("validation.coverage_score should be number")
        manual_parsed = validation.get("manual_parsed") or {}
        urls = manual_parsed.get("all_더보기_urls") if isinstance(manual_parsed, dict) else []
        summary = validation.get("summary") or {}
        manual_count = summary.get("manual_더보기_count")
        if manual_count is None and urls is not None:
            report["warnings"].append("validation.summary.manual_더보기_count missing (can infer from all_더보기_urls)")

    return report


def clean_manual_pipeline_result(data: Dict[str, Any], mark_placeholders: bool = False) -> Dict[str, Any]:
    """
    Full clean: placeholders, merge validation/missing_analysis, dedupe, normalize, schema validate.
    Modifies a copy and returns it; use as post-crawl step before serialization.
    """
    data = merge_validation_and_missing_analysis(dict(data))

    # Crawled topic
    crawled = data.get("crawled") or {}
    if isinstance(crawled, dict):
        topic = crawled.get("topic") or {}
        if isinstance(topic, dict):
            sections = topic.get("sections") or []
            if isinstance(sections, list):
                sections = remove_or_mark_placeholders_in_sections(sections, mark=mark_placeholders)
                sections = [
                    dict(s, links=dedupe_all_links(normalize_language_and_urls_in_links(s.get("links") or [])))
                    if isinstance(s, dict) else s
                    for s in sections
                ]
                topic = dict(topic, sections=sections)
            all_links = topic.get("all_links") or []
            if isinstance(all_links, list):
                topic = dict(topic, all_links=dedupe_all_links(normalize_language_and_urls_in_links(all_links)))
            crawled = dict(crawled, topic=topic)
        if "expected_section_titles" not in crawled and EXPECTED_SECTION_TITLES:
            crawled = dict(crawled, expected_section_titles=EXPECTED_SECTION_TITLES)
        data["crawled"] = crawled

    # Validation
    validation = data.get("validation") or {}
    if isinstance(validation, dict):
        manual_parsed = validation.get("manual_parsed")
        if isinstance(manual_parsed, dict):
            sections = manual_parsed.get("sections") or []
            if isinstance(sections, list):
                sections = remove_or_mark_placeholders_in_sections(sections, mark=mark_placeholders)
                sections = normalize_manual_parsed_sections(sections)
                manual_parsed = dict(manual_parsed, sections=sections)
            urls = manual_parsed.get("all_더보기_urls") or []
            if isinstance(urls, list):
                manual_parsed = dict(manual_parsed, all_더보기_urls=list(dict.fromkeys(_norm_url(u) for u in urls if u)))
            validation = dict(validation, manual_parsed=manual_parsed)
        missing_in_manual_items = validation.get("missing_in_manual_items") or []
        if isinstance(missing_in_manual_items, list):
            validation = dict(validation, missing_in_manual_items=dedupe_missing_in_manual_items(missing_in_manual_items))
        summary = validation.get("summary") or {}
        manual_parsed_after = validation.get("manual_parsed")
        if isinstance(manual_parsed_after, dict):
            urls = manual_parsed_after.get("all_더보기_urls") or []
            if "manual_더보기_count" not in summary and isinstance(urls, list):
                summary = dict(summary, manual_더보기_count=len(urls))
                validation = dict(validation, summary=summary)
        data["validation"] = validation

    report = schema_validate(data)
    data["_schema_validation"] = report
    if report.get("errors"):
        logger.warning("Schema validation errors: %s", report["errors"])
    if report.get("warnings"):
        logger.info("Schema validation warnings: %s", report["warnings"])

    return data
