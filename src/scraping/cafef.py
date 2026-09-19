"""Scraper cho cafef.vn.

QUAN TRỌNG: các CSS selector dưới đây dựa trên cấu trúc HTML điển hình của
cafef.vn quan sát được, nhưng CẦN xác nhận lại bằng cách chạy pilot thật và
in thử `html` để đối chiếu — trang có thể đổi cấu trúc theo thời gian.

Cách kiểm tra nhanh (chạy trong Python REPL):
    from src.scraping.cafef import CafeFScraper
    s = CafeFScraper()
    html = s.fetch(s.listing_url(1))
    print(html[:3000])   # xem cấu trúc thật, chỉnh lại selector nếu cần

Định dạng URL bài viết cafef.vn thường có dạng:
    https://cafef.vn/<slug>-<id>.chn
trong đó <id> có thể chứa timestamp encode dạng YYMMDDHHMMSS ở giữa —
hàm `try_decode_timestamp_from_url()` thử giải mã phần này làm nguồn
đối chiếu (cross-check) với timestamp hiển thị trên trang.
"""

from __future__ import annotations

import re
from datetime import datetime

from bs4 import BeautifulSoup

from src.scraping.base import BaseScraper

# Regex bắt định dạng "DD/MM/YYYY HH:MM" xuất hiện trong text quanh mỗi bài
DATETIME_PATTERN = re.compile(r"(\d{2})/(\d{2})/(\d{4})\s+(\d{2}):(\d{2})")

# Regex thử bắt cụm số dài trong URL bài viết, vd: ...-188260909093332991.chn
URL_ID_PATTERN = re.compile(r"-(\d{15,20})\.chn")

# Danh sách 30 mã VN30 để nhận diện ticker được nhắc tới trong tiêu đề/nội dung
# (load từ configs/vn30_tickers.yaml trong production — hardcode tạm ở đây cho pilot)
VN30_TICKERS = [
    "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG",
    "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB",
    "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE",
]


def try_decode_timestamp_from_url(url: str) -> datetime | None:
    """Thử giải mã timestamp nhúng trong URL bài viết cafef.

    Ví dụ quan sát: .../loat-rui-ro...-188260909093332991.chn
    được đăng lúc hiển thị 09/09/2026 09:35.
    Giả thuyết: cụm "260909093332" (bỏ 3 số đầu "188" là site id, bỏ đuôi) mã hoá
    YYMMDDHHMMSS = 26-09-09 09:33:32 → khớp gần đúng với thời gian hiển thị.

    Hàm này CHƯA ĐƯỢC XÁC NHẬN CHẮC CHẮN — dùng để cross-check, không thay thế
    timestamp lấy từ trang HTML. Trả None nếu không decode được hợp lệ.
    """
    m = URL_ID_PATTERN.search(url)
    if not m:
        return None
    digits = m.group(1)
    # Thử bỏ 3 ký tự đầu (site/category id) rồi lấy 12 số tiếp theo làm YYMMDDHHMMSS
    for offset in (3, 2, 4):
        candidate = digits[offset : offset + 12]
        if len(candidate) < 12:
            continue
        try:
            yy, mm, dd, hh, mi, ss = (
                int(candidate[0:2]),
                int(candidate[2:4]),
                int(candidate[4:6]),
                int(candidate[6:8]),
                int(candidate[8:10]),
                int(candidate[10:12]),
            )
            year = 2000 + yy
            dt = datetime(year, mm, dd, hh, mi, ss)
            # Sanity check: năm phải hợp lý (2020-2030), không thì loại
            if 2020 <= year <= 2030:
                return dt
        except (ValueError, IndexError):
            continue
    return None


def extract_tickers(text: str) -> list[str]:
    """Tìm các mã VN30 xuất hiện trong text (so khớp từ nguyên, phân biệt hoa/thường)."""
    found = []
    text_upper = text.upper()
    for ticker in VN30_TICKERS:
        # \b để tránh match nhầm substring, vd "SSI" trong "SSIT"
        if re.search(rf"\b{ticker}\b", text_upper):
            found.append(ticker)
    return found


class CafeFScraper(BaseScraper):
    source_name = "cafef"
    base_url = "https://cafef.vn"
    listing_path = "chung-khoan"  # trang danh mục Chứng khoán

    def listing_url(self, page: int) -> str:
        if page == 1:
            return f"{self.base_url}/{self.listing_path}.html"
        return f"{self.base_url}/{self.listing_path}/trang-{page}.html"

    def parse_listing_page(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        items = []

        # Cafef thường bọc mỗi tin trong thẻ có class chứa "tlitem" hoặc "item"
        # kèm 1 thẻ <a> (link+title) và 1 span/div chứa timestamp.
        # THỬ NHIỀU SELECTOR — giữ cái nào match được nhiều nhất.
        candidates = soup.select("h3 a[href*='.chn'], h2 a[href*='.chn']")

        seen_urls = set()
        for a_tag in candidates:
            href = a_tag.get("href", "")
            title = a_tag.get_text(strip=True)
            if not href or not title or href in seen_urls:
                continue
            if not href.startswith("http"):
                href = self.base_url + href
            seen_urls.add(href)

            # Tìm timestamp: quét text trong vùng lân cận thẻ cha
            parent = a_tag.find_parent(["div", "li", "article"])
            time_text = ""
            if parent:
                # Tìm trong 200 ký tự text kế tiếp sau title trong cùng khối cha
                sibling_text = parent.get_text(" ", strip=True)
                time_text = sibling_text

            dt, raw, precision = self._parse_timestamp(time_text)

            items.append(
                {
                    "url": href,
                    "title": title,
                    "published_at": dt,
                    "published_at_raw": raw,
                    "timestamp_precision": precision,
                }
            )

        return items

    def parse_article_page(self, html: str, url: str) -> dict:
        soup = BeautifulSoup(html, "lxml")

        # Timestamp trên trang chi tiết: cafef thường có span class "pdate" hoặc tương tự
        # Fallback: quét toàn bộ text đầu trang tìm pattern DD/MM/YYYY HH:MM
        full_text = soup.get_text(" ", strip=True)[:2000]
        dt, raw, precision = self._parse_timestamp(full_text)

        # Cross-check với timestamp decode từ URL
        url_dt = try_decode_timestamp_from_url(url)
        if url_dt is not None:
            if dt is not None:
                diff_sec = abs((url_dt - dt).total_seconds())
                if diff_sec > 300:  # lệch >5 phút → nghi ngờ decode URL sai, bỏ qua
                    url_dt = None
            else:
                # Không có timestamp trang chi tiết, dùng URL decode + hạ precision
                dt = url_dt
                precision = "second_from_url_unverified"

        # Nội dung bài viết: thử selector phổ biến cho khung nội dung chính
        content_div = soup.select_one("div.detail-content, div#mainContent, div.contentdetail, article")
        content = content_div.get_text(" ", strip=True) if content_div else ""
        if not content:
            # Fallback: lấy toàn bộ <p> trong body
            paragraphs = soup.find_all("p")
            content = " ".join(p.get_text(strip=True) for p in paragraphs)

        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else ""

        tickers = extract_tickers(title + " " + content[:1000])

        return {
            "title": title,
            "published_at": dt,
            "published_at_raw": raw,
            "timestamp_precision": precision,
            "content": content,
            "tickers_mentioned": tickers,
            "_url_decoded_timestamp": url_dt.isoformat() if url_dt else None,
        }

    @staticmethod
    def _parse_timestamp(text: str) -> tuple[datetime | None, str, str]:
        """Parse 'DD/MM/YYYY HH:MM' từ text tự do. Trả (datetime|None, raw_match, precision)."""
        m = DATETIME_PATTERN.search(text)
        if not m:
            return None, "", "unknown"
        dd, mm, yyyy, hh, minute = m.groups()
        raw = m.group(0)
        try:
            dt = datetime(int(yyyy), int(mm), int(dd), int(hh), int(minute))
            return dt, raw, "minute"
        except ValueError:
            return None, raw, "unknown"
