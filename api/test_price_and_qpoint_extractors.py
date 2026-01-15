"""Unit tests for Qoo10Crawler's price and Qpoint extractors.

These tests use 작은 HTML 조각으로 `_extract_price` 와 `_extract_qpoint_info`의
핵심 동작을 검증합니다. 실제 네트워크 요청은 사용하지 않습니다.
"""
from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from services.crawler import Qoo10Crawler


class _DummyDB:
    """Minimal stub DB so Qoo10Crawler can be instantiated without real DB access."""

    def __getattr__(self, name: str) -> Any:  # pragma: no cover - defensive fallback
        # 대부분의 테스트에서는 db 메서드를 사용하지 않지만,
        # 혹시 호출되더라도 NOP 형태로 동작하게 합니다.
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None

        return _noop


def _make_crawler() -> Qoo10Crawler:
    return Qoo10Crawler(db=_DummyDB())


def test_extract_price_basic_jp_text():
    """일본어 상품가격/정가/쿠폰/Q포인트 텍스트에서 가격 정보를 올바르게 추출한다."""
    html = """
    <html>
      <body>
        <div>
          商品価格: 4,562円
        </div>
        <div class="prc">
          <del>29,400円</del>
          <strong>4,562円</strong>
        </div>
        <div>
          クーポン割引 プラス500割引
        </div>
        <div>
          Qポイント獲得 最大21P
        </div>
      </body>
    </html>
    """
    soup = BeautifulSoup(html, "lxml")
    crawler = _make_crawler()

    price = crawler._extract_price(soup)  # type: ignore[attr-defined]

    assert price["sale_price"] == 4562
    assert price["original_price"] == 29400

    expected_discount = int((29400 - 4562) / 29400 * 100)
    assert price["discount_rate"] == expected_discount

    assert price["coupon_discount"] == 500
    # 간단한 Q포인트 최대값 추출 확인
    assert price["qpoint_info"] == 21


def test_extract_qpoint_info_section_and_page_fallback():
    """Qポイント 섹션 및 페이지 전체 텍스트에서 포인트 정보를 추출한다."""
    html = """
    <html>
      <body>
        <div class="qpoint-info">
          <p>Qポイント獲得方法</p>
          <p>受取確認: 最大1P</p>
          <p>レビュー作成: 最大20P</p>
          <p>最大21P 獲得可能</p>
          <p>配送完了 自動 1P</p>
        </div>
      </body>
    </html>
    """
    soup = BeautifulSoup(html, "lxml")
    crawler = _make_crawler()

    qpoint = crawler._extract_qpoint_info(soup)  # type: ignore[attr-defined]

    assert qpoint["receive_confirmation_points"] == 1
    assert qpoint["review_points"] == 20
    assert qpoint["max_points"] == 21
    assert qpoint["auto_points"] == 1
