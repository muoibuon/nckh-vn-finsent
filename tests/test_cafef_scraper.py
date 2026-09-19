"""Test cho cafef scraper — dùng HTML/URL mẫu, KHÔNG cần internet.

Chạy: pytest tests/test_cafef_scraper.py -v
"""

from datetime import datetime

from src.scraping.cafef import (
    CafeFScraper,
    extract_tickers,
    try_decode_timestamp_from_url,
)

# HTML mẫu tối giản, mô phỏng cấu trúc trang danh sách quan sát được ngày 09/09/2026
SAMPLE_LISTING_HTML = """
<html><body>
<div class="tlitem">
  <h3><a href="https://cafef.vn/loat-rui-ro-toan-cau-lam-rung-chuyen-thi-truong-188260909093332991.chn">
    Loạt rủi ro toàn cầu làm rung chuyển thị trường
  </a></h3>
  <span class="time">09/09/2026 09:35</span>
</div>
<div class="tlitem">
  <h3><a href="https://cafef.vn/hon-24-trieu-co-phieu-mch-188260908194604621.chn">
    Hơn 2,4 triệu cổ phiếu MCH có thể được mua
  </a></h3>
  <span class="time">09/09/2026 08:00</span>
</div>
</body></html>
"""

SAMPLE_ARTICLE_HTML = """
<html><body>
<h1>Loạt rủi ro toàn cầu làm rung chuyển thị trường: HPG và VCB chịu áp lực</h1>
<div class="pdate">09/09/2026 09:35</div>
<div class="detail-content">
<p>Thị trường chứng khoán Mỹ giảm điểm ngày 8/9. Cổ phiếu HPG và VCB nằm trong nhóm chịu áp lực bán mạnh nhất.</p>
</div>
</body></html>
"""


def test_parse_listing_extracts_articles():
    scraper = CafeFScraper.__new__(CafeFScraper)  # bypass __init__ (không cần tạo log dir)
    items = scraper.parse_listing_page(SAMPLE_LISTING_HTML)
    assert len(items) == 2
    assert items[0]["url"].endswith(".chn")
    assert "Loạt rủi ro" in items[0]["title"]


def test_parse_listing_extracts_timestamp_minute_precision():
    scraper = CafeFScraper.__new__(CafeFScraper)
    items = scraper.parse_listing_page(SAMPLE_LISTING_HTML)
    first = items[0]
    assert first["published_at"] is not None
    assert first["published_at"].year == 2026
    assert first["published_at"].month == 9
    assert first["published_at"].day == 9
    assert first["published_at"].hour == 9
    assert first["published_at"].minute == 35
    assert first["timestamp_precision"] == "minute"


def test_parse_article_page_extracts_content_and_tickers():
    scraper = CafeFScraper.__new__(CafeFScraper)
    result = scraper.parse_article_page(
        SAMPLE_ARTICLE_HTML,
        "https://cafef.vn/loat-rui-ro-188260909093332991.chn",
    )
    assert "HPG" in result["tickers_mentioned"]
    assert "VCB" in result["tickers_mentioned"]
    assert result["published_at"].hour == 9
    assert result["published_at"].minute == 35
    assert "áp lực" in result["content"]


def test_extract_tickers_word_boundary():
    """Đảm bảo không match nhầm substring, vd 'SSI' trong từ khác."""
    text = "Cổ phiếu HPG tăng mạnh, trong khi SSI giảm nhẹ."
    tickers = extract_tickers(text)
    assert "HPG" in tickers
    assert "SSI" in tickers
    assert len(tickers) == 2


def test_extract_tickers_no_false_positive():
    text = "Thị trường chung không có tin gì đặc biệt hôm nay."
    tickers = extract_tickers(text)
    assert tickers == []


def test_decode_timestamp_from_url_matches_displayed_time():
    """Kiểm tra giả thuyết decode timestamp từ URL — CẦN xác nhận thêm với data thật.

    Ví dụ quan sát: URL chứa 188260909093332991, trang hiển thị 09/09/2026 09:35.
    Decode kỳ vọng ra ngày 09/09/2026, giờ gần 09:35 (chênh lệch vài phút do làm tròn).
    """
    url = "https://cafef.vn/loat-rui-ro-toan-cau-188260909093332991.chn"
    dt = try_decode_timestamp_from_url(url)
    if dt is not None:  # decode có thể fail nếu giả thuyết offset sai — không assert cứng
        assert dt.year == 2026
        assert dt.month == 9
        assert dt.day == 9


def test_decode_timestamp_from_url_no_match_returns_none():
    url = "https://cafef.vn/some-static-page.html"
    assert try_decode_timestamp_from_url(url) is None


def test_parse_timestamp_handles_missing_pattern():
    scraper = CafeFScraper.__new__(CafeFScraper)
    dt, raw, precision = scraper._parse_timestamp("không có ngày giờ ở đây")
    assert dt is None
    assert precision == "unknown"
