"""
Qoo10 큐텐 대학 한국어 메뉴얼 데이터 파이프라인
전체 에이전트 설계에 맞춰: 수집(Crawl) → 검증(Validation) → 누락 데이터 정밀 분석 → 결과 저장

실행:
  cd api
  python run_manual_pipeline.py
  python run_manual_pipeline.py --output results/manual_pipeline_result.json
"""
import asyncio
import json
import sys
import os
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.manual_crawler import Qoo10ManualCrawler
from services.manual_validator import load_and_validate, find_manual_path, parse_manual_markdown
from services.manual_pipeline_cleaner import clean_manual_pipeline_result


async def run_manual_pipeline(
    manual_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    1) 수집: 큐텐 대학 한국어 메인 + 단계별 교육(초급) 카테고리
    2) 검증: 현재 메뉴얼 마크다운 vs 크롤링 결과
    3) 누락 데이터 정밀 분석 결과 반환
    """
    crawler = Qoo10ManualCrawler()
    try:
        # Stage 1: 수집 (Crawl Agent)
        crawled = await crawler.crawl_all()
        # Stage 2: 검증 (Validation Agent) + 누락 분석
        validation = load_and_validate(crawled, manual_path=manual_path)
        result = {
            "pipeline": "manual",
            "crawled": crawled,
            "validation": validation,
        }
        # Post-crawl clean: placeholders, dedupe, normalize, schema validation
        result = clean_manual_pipeline_result(result, mark_placeholders=False)
        return result
    finally:
        await crawler.close()


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Qoo10 큐텐 대학 한국어 메뉴얼 파이프라인")
    parser.add_argument("--output", "-o", default="manual_pipeline_result.json", help="결과 JSON 저장 경로")
    parser.add_argument("--manual-path", default=None, help="메뉴얼 마크다운 파일 경로 (기본: doc/Qoo10_큐텐대학_한국어_메뉴얼.md)")
    parser.add_argument("--clean-file", default=None, help="기존 JSON 파일 경로; 지정 시 크롤 없이 클린만 수행 후 저장")
    args = parser.parse_args()

    print("=" * 80)
    print("Qoo10 큐텐 대학 한국어 메뉴얼 데이터 파이프라인")
    print("=" * 80)

    if args.clean_file:
        clean_path = args.clean_file if os.path.isabs(args.clean_file) else os.path.join(os.path.dirname(__file__), args.clean_file)
        if not os.path.isfile(clean_path):
            print(f"오류: 파일을 찾을 수 없습니다: {clean_path}")
            sys.exit(1)
        with open(clean_path, "r", encoding="utf-8") as f:
            result = json.load(f)
        from services.manual_pipeline_cleaner import clean_manual_pipeline_result
        result = clean_manual_pipeline_result(result, mark_placeholders=False)
        out_path = args.output if os.path.isabs(args.output) else os.path.join(os.path.dirname(__file__), args.output)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"클린 완료. 저장: {out_path}")
        print("=" * 80)
        return

    result = asyncio.run(run_manual_pipeline(manual_path=args.manual_path))

    # 콘솔 요약
    crawled = result.get("crawled", {})
    topic = crawled.get("topic", {})
    beginner = crawled.get("beginner_category", {})
    val = result.get("validation", {})

    print("\n[1] 수집 (Crawl)")
    print(f"    - 메인 토픽 섹션 수: {len(topic.get('sections') or [])}")
    print(f"    - 메인 토픽 링크 수: {len(topic.get('all_links') or [])}")
    print(f"    - 단계별 교육(초급) 글 수: {len(beginner.get('articles') or [])}")

    print("\n[2] 검증 (Validation) & 누락 데이터 정밀 분석")
    print(f"    - coverage_score: {val.get('coverage_score', 0)}%")
    print(f"    - 누락 섹션: {len(val.get('missing_sections') or [])}건")
    print(f"    - 누락 링크: {len(val.get('missing_links') or [])}건")
    print(f"    - 메뉴얼에 없는 항목: {len(val.get('missing_in_manual_items') or [])}건")
    print(f"    - 메뉴얼에만 있는 URL: {len(val.get('extra_in_manual') or [])}건")
    for s in (val.get("suggestions") or [])[:5]:
        print(f"    - 제안: {s}")

    # JSON 저장 (직렬화 가능한 것만; depth/limit 완화로 placeholder 재발 방지)
    def _serializable(obj: Any, depth: int = 0):
        if depth > 18:
            return "<<max depth>>"
        if obj is None or isinstance(obj, (bool, int, float, str)):
            return obj
        if isinstance(obj, (list, tuple)):
            return [_serializable(x, depth + 1) for x in obj[:400]]
        if isinstance(obj, dict):
            return {k: _serializable(v, depth + 1) for k, v in list(obj.items())[:150]}
        return str(obj)

    out_path = args.output
    if not os.path.isabs(out_path):
        out_path = os.path.join(os.path.dirname(__file__), out_path)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(_serializable(result), f, ensure_ascii=False, indent=2)

    print(f"\n결과 저장: {out_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
