"""Base scraper: rate limiting, retry, logging chung cho cafef/vietstock/vneconomy.

Thiết kế để dễ mở rộng sang nguồn khác — mỗi nguồn chỉ cần kế thừa BaseScraper
và implement 2 hàm: parse_listing_page() và parse_article_page().
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36",
]


@dataclass
class Article:
    """Một tin tức đã parse, chuẩn hoá schema chung cho mọi nguồn."""

    source: str  # "cafef" | "vietstock" | "vneconomy"
    url: str
    title: str
    published_at: datetime | None  # None nếu không parse được — PHẢI ghi log cảnh báo
    published_at_raw: str  # chuỗi gốc trước khi parse, để debug
    timestamp_precision: str  # "second" | "minute" | "day" | "unknown"
    content: str = ""
    tickers_mentioned: list[str] = field(default_factory=list)
    scraped_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "url": self.url,
            "title": self.title,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "published_at_raw": self.published_at_raw,
            "timestamp_precision": self.timestamp_precision,
            "content": self.content,
            "tickers_mentioned": ",".join(self.tickers_mentioned),
            "scraped_at": self.scraped_at.isoformat(),
        }


class BaseScraper:
    """Lớp cơ sở: quản lý session, rate limit, retry, và ghi log tiến độ.

    Subclass PHẢI implement:
        - listing_url(page: int) -> str
        - parse_listing_page(html: str) -> list[dict]  (mỗi dict có ít nhất 'url', 'title', 'published_at_raw')
        - parse_article_page(html: str, url: str) -> dict  (content, published_at_raw chi tiết)
    """

    source_name: str = "base"
    min_delay_sec: float = 1.5
    max_delay_sec: float = 3.5
    max_retries: int = 3
    timeout_sec: int = 15

    def __init__(self, output_dir: str | Path = "data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self._configure_logging()

    def _configure_logging(self) -> None:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"{ts}_{self.source_name}_scrape.log"
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler()],
        )
        logger.info("Bắt đầu scrape nguồn: %s. Log: %s", self.source_name, log_file)

    def _headers(self) -> dict:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    def _sleep(self) -> None:
        """Nhịp nghỉ ngẫu nhiên giữa các request — tránh bị chặn bot."""
        time.sleep(random.uniform(self.min_delay_sec, self.max_delay_sec))

    def fetch(self, url: str) -> str | None:
        """GET một URL với retry + backoff. Trả None nếu thất bại sau max_retries."""
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(url, headers=self._headers(), timeout=self.timeout_sec)
                if resp.status_code == 200:
                    return resp.text
                if resp.status_code == 429:
                    wait = 10 * attempt
                    logger.warning("429 Too Many Requests tại %s — nghỉ %ds", url, wait)
                    time.sleep(wait)
                    continue
                logger.warning("Status %d tại %s (lần %d/%d)", resp.status_code, url, attempt, self.max_retries)
            except requests.RequestException as e:
                logger.warning("Lỗi request tại %s (lần %d/%d): %s", url, attempt, self.max_retries, e)
            time.sleep(2 * attempt)
        logger.error("Thất bại sau %d lần thử: %s", self.max_retries, url)
        return None

    def run_pilot(self, target_count: int = 250) -> list[Article]:
        """Chạy pilot: thu thập tối thiểu target_count bài, dừng khi đủ hoặc hết trang.

        Đây là hàm chính để xác thực tính khả thi trước khi scrape quy mô lớn.
        """
        articles: list[Article] = []
        page = 1
        empty_pages = 0

        while len(articles) < target_count and empty_pages < 3:
            url = self.listing_url(page)
            logger.info("Đang lấy trang %d: %s (đã có %d/%d bài)", page, url, len(articles), target_count)
            html = self.fetch(url)
            self._sleep()

            if html is None:
                empty_pages += 1
                page += 1
                continue

            items = self.parse_listing_page(html)
            if not items:
                empty_pages += 1
                logger.warning("Trang %d không có bài nào — thử %d/3 trước khi dừng", page, empty_pages)
            else:
                empty_pages = 0

            for item in items:
                if len(articles) >= target_count:
                    break
                article = self._build_article(item)
                if article is not None:
                    articles.append(article)

            page += 1

        logger.info("Hoàn tất pilot: thu được %d bài từ %s", len(articles), self.source_name)
        return articles

    def _build_article(self, listing_item: dict) -> Article | None:
        """Từ 1 item trong trang danh sách, fetch trang chi tiết và build Article."""
        url = listing_item.get("url")
        if not url:
            return None

        detail_html = self.fetch(url)
        self._sleep()
        if detail_html is None:
            logger.warning("Không fetch được trang chi tiết: %s", url)
            return None

        detail = self.parse_article_page(detail_html, url)

        published_at = detail.get("published_at") or listing_item.get("published_at")
        precision = detail.get("timestamp_precision") or listing_item.get("timestamp_precision", "unknown")

        return Article(
            source=self.source_name,
            url=url,
            title=listing_item.get("title", detail.get("title", "")),
            published_at=published_at,
            published_at_raw=listing_item.get("published_at_raw", "") or detail.get("published_at_raw", ""),
            timestamp_precision=precision,
            content=detail.get("content", ""),
            tickers_mentioned=detail.get("tickers_mentioned", []),
        )

    # ==== Phải override ở subclass ====
    def listing_url(self, page: int) -> str:
        raise NotImplementedError

    def parse_listing_page(self, html: str) -> list[dict]:
        raise NotImplementedError

    def parse_article_page(self, html: str, url: str) -> dict:
        raise NotImplementedError
