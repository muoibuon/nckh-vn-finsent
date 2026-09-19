"""Chạy pilot scraper cho cafef.vn: thu ~250 tin, xuất CSV + báo cáo tính khả thi timestamp.

Cách chạy:
    python -m src.scraping.run_pilot --source cafef --target 250

Đầu ra:
    data/raw/pilot_cafef.csv          — dữ liệu thô
    results/tables/pilot_cafef_report.txt  — báo cáo tính khả thi timestamp (Đầu ra D1)
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from src.scraping.cafef import CafeFScraper


SCRAPERS = {
    "cafef": CafeFScraper,
    # "vietstock": VietstockScraper,   # TODO: implement sau khi cafef pilot pass
    # "vneconomy": VneconomyScraper,   # TODO
}


def run(source: str, target: int, output_dir: str) -> None:
    if source not in SCRAPERS:
        raise ValueError(f"Nguồn '{source}' chưa được implement. Chọn từ: {list(SCRAPERS)}")

    scraper_cls = SCRAPERS[source]
    scraper = scraper_cls(output_dir=output_dir)
    articles = scraper.run_pilot(target_count=target)

    out_csv = Path(output_dir) / f"pilot_{source}.csv"
    write_csv(articles, out_csv)

    report_path = Path("results/tables") / f"pilot_{source}_report.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    write_feasibility_report(articles, source, report_path)

    print(f"\n✅ Xong. Dữ liệu: {out_csv}")
    print(f"✅ Báo cáo tính khả thi: {report_path}")


def write_csv(articles, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not articles:
        print("⚠️  Không thu được bài nào — kiểm tra log trong logs/")
        return
    fieldnames = list(articles[0].to_dict().keys())
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for a in articles:
            writer.writerow(a.to_dict())


def write_feasibility_report(articles, source: str, path: Path) -> None:
    """Sinh báo cáo tính khả thi timestamp — đây là đầu ra chính của D1 (Duyên).

    Tiêu chí nghiệm thu D1: >= 200 tin có timestamp giờ/phút; kết luận rõ ràng.
    """
    total = len(articles)
    precision_counts: dict[str, int] = {}
    for a in articles:
        precision_counts[a.timestamp_precision] = precision_counts.get(a.timestamp_precision, 0) + 1

    minute_or_better = sum(
        v for k, v in precision_counts.items() if k in ("minute", "second", "second_from_url_unverified")
    )
    unknown_count = precision_counts.get("unknown", 0)

    lines = []
    lines.append(f"=== BÁO CÁO TÍNH KHẢ THI TIMESTAMP — nguồn: {source} ===\n")
    lines.append(f"Tổng số tin thu thập: {total}")
    lines.append("")
    lines.append("Phân bố độ chính xác timestamp:")
    for k, v in sorted(precision_counts.items(), key=lambda x: -x[1]):
        pct = 100 * v / total if total else 0
        lines.append(f"  - {k:30s}: {v:4d} tin ({pct:.1f}%)")
    lines.append("")
    lines.append(f"Số tin có timestamp >= độ chính xác PHÚT: {minute_or_better}/{total}")
    lines.append(f"Số tin KHÔNG parse được timestamp: {unknown_count}/{total}")
    lines.append("")

    lines.append("=== KẾT LUẬN (Tiêu chí nghiệm thu D1: >= 200 tin có timestamp giờ/phút) ===")
    if minute_or_better >= 200:
        lines.append(f"✅ ĐẠT. {minute_or_better} tin có timestamp đủ độ chính xác giờ/phút.")
        lines.append("   → Có thể tiến hành scrape quy mô lớn (D2) và dùng cho event study (Nội dung 4).")
    elif minute_or_better >= 100:
        lines.append(f"⚠️  CHƯA ĐẠT NGƯỠNG nhưng có tín hiệu tích cực ({minute_or_better}/200 tin).")
        lines.append("   → Kiểm tra lại selector parse (có thể trang đổi cấu trúc một phần).")
        lines.append("   → Thử tăng target_count hoặc kiểm tra log lỗi 429/timeout.")
    else:
        lines.append(f"❌ KHÔNG ĐẠT. Chỉ {minute_or_better}/200 tin có timestamp đủ chính xác.")
        lines.append("   → RỦI RO NGHIÊM TRỌNG cho Nội dung 4 (event study) — cần báo cáo ngay chủ nhiệm.")
        lines.append("   → Fallback: chuyển event study sang cửa sổ sự kiện theo NGÀY thay vì giờ/phút,")
        lines.append("     chấp nhận giảm độ chính xác nhân quả, và nêu rõ hạn chế này trong báo cáo.")

    lines.append("")
    lines.append("=== Mẫu 5 tin đầu tiên (kiểm tra thủ công) ===")
    for a in articles[:5]:
        lines.append(f"  [{a.timestamp_precision}] {a.published_at_raw or 'N/A'} | {a.title[:70]}")
        lines.append(f"    URL: {a.url}")

    report_text = "\n".join(lines)
    path.write_text(report_text, encoding="utf-8")
    print("\n" + report_text)


def main():
    parser = argparse.ArgumentParser(description="Chạy pilot scraper")
    parser.add_argument("--source", default="cafef", choices=list(SCRAPERS.keys()))
    parser.add_argument("--target", type=int, default=250, help="Số tin mục tiêu (mặc định 250)")
    parser.add_argument("--output-dir", default="data/raw")
    args = parser.parse_args()

    run(args.source, args.target, args.output_dir)


if __name__ == "__main__":
    main()
