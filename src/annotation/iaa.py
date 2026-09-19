"""Tính đồng thuận giữa 2 người gán (Inter-Annotator Agreement) và kiểm tra chất lượng nhãn.

Chức năng:
  1. Cohen's Kappa (2 người) + phần trăm nhất trí thô + Krippendorff's alpha
  2. Tách tin nhất trí (gold) và tin bất đồng (cần phân xử)
  3. Ma trận nhầm lẫn giữa 2 người — cho biết cặp nhãn nào hay lệch nhau nhất
  4. Kiểm tra chất lượng: phân bố lớp, tin bỏ trống, nhãn không hợp lệ

Cách chạy:
    python -m src.annotation.iaa --input data/gold/annotations.csv

Kỳ vọng file CSV có tối thiểu các cột:
    - stt (hoặc id): định danh tin
    - ma_ck: mã cổ phiếu
    - nhan_1: nhãn của người gán 1
    - nhan_2: nhãn của người gán 2
  (tên cột có thể chỉnh qua tham số --col1 / --col2)

Đầu ra:
    results/tables/iaa_report.txt   — báo cáo đầy đủ
    data/gold/gold_labels.csv       — tin 2 người nhất trí (dùng làm nhãn vàng)
    data/gold/bat_dong.csv          — tin bất đồng (cần chủ nhiệm phân xử)
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score, confusion_matrix

# Ba nhãn hợp lệ theo hướng dẫn gán nhãn v0.2
VALID_LABELS = {"tich_cuc", "trung_tinh", "tieu_cuc"}


def load_annotations(path: Path, col1: str, col2: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]
    missing = [c for c in (col1, col2) if c not in df.columns]
    if missing:
        raise ValueError(
            f"Không tìm thấy cột {missing} trong file.\n"
            f"Các cột hiện có: {list(df.columns)}\n"
            f"Dùng --col1 / --col2 để chỉ định đúng tên cột nhãn."
        )
    return df


def load_two_files(
    path1: Path, path2: Path, label_col1: str, label_col2: str, join_key: str
) -> pd.DataFrame:
    """Đọc 2 file nhãn riêng của 2 người, join theo join_key (thường là 'url').

    Trả DataFrame có cột: <join_key>, ma_ck, tieu_de, nhan_1, nhan_2, và (nếu có)
    ghi_chu_1, ghi_chu_2 để tiện phân xử.
    """
    df1 = pd.read_csv(path1, encoding="utf-8-sig")
    df2 = pd.read_csv(path2, encoding="utf-8-sig")
    df1.columns = [c.strip() for c in df1.columns]
    df2.columns = [c.strip() for c in df2.columns]

    for name, df, col in [("người 1", df1, label_col1), ("người 2", df2, label_col2)]:
        if col not in df.columns:
            raise ValueError(
                f"Không tìm thấy cột nhãn '{col}' trong file của {name}.\n"
                f"Các cột có: {list(df.columns)}"
            )
        if join_key not in df.columns:
            raise ValueError(
                f"Không tìm thấy cột khoá '{join_key}' trong file của {name}.\n"
                f"Các cột có: {list(df.columns)}"
            )

    # Chỉ giữ cột cần thiết, đổi tên để tránh trùng khi merge
    keep1 = [join_key, label_col1]
    keep2 = [join_key, label_col2]
    for extra in ("ma_ck", "tieu_de"):
        if extra in df1.columns and extra not in keep1:
            keep1.append(extra)
    if "ghi_chu" in df1.columns:
        keep1.append("ghi_chu")
    if "ghi_chu" in df2.columns:
        keep2.append("ghi_chu")

    d1 = df1[keep1].rename(columns={label_col1: "nhan_1", "ghi_chu": "ghi_chu_1"})
    d2 = df2[keep2].rename(columns={label_col2: "nhan_2", "ghi_chu": "ghi_chu_2"})

    merged = d1.merge(d2, on=join_key, how="inner", suffixes=("_1", "_2"))

    n1, n2, nm = len(df1), len(df2), len(merged)
    print(f"File người 1: {n1} tin | File người 2: {n2} tin | Khớp theo '{join_key}': {nm} tin")
    if nm < min(n1, n2):
        print(
            f"⚠️  Có {min(n1, n2) - nm} tin không khớp được giữa 2 file "
            f"(url khác nhau hoặc chỉ 1 người gán) — đã loại khỏi phép tính κ."
        )
    return merged


def normalize_labels(series: pd.Series) -> pd.Series:
    """Chuẩn hoá nhãn: bỏ khoảng trắng, đưa về lowercase, thống nhất dấu gạch dưới."""
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )


def check_quality(df: pd.DataFrame, col1: str, col2: str) -> list[str]:
    """Kiểm tra chất lượng nhãn thô. Trả list dòng cảnh báo."""
    lines = ["=== KIỂM TRA CHẤT LƯỢNG NHÃN ===\n"]
    n = len(df)
    lines.append(f"Tổng số tin đã gán (cả 2 người): {n}\n")

    for col, name in [(col1, "Người 1"), (col2, "Người 2")]:
        labels = df[col]
        empty = labels.isna().sum() + (labels == "nan").sum() + (labels == "").sum()
        invalid = labels[~labels.isin(VALID_LABELS) & (labels != "nan")].unique()
        dist = Counter(labels[labels.isin(VALID_LABELS)])

        lines.append(f"--- {name} (cột '{col}') ---")
        lines.append(f"  Tin bỏ trống / không hợp lệ: {empty}")
        if len(invalid) > 0:
            lines.append(f"  ⚠️  Nhãn KHÔNG hợp lệ tìm thấy: {list(invalid)}")
            lines.append(f"      (nhãn hợp lệ chỉ gồm: {sorted(VALID_LABELS)})")
        lines.append("  Phân bố lớp:")
        total_valid = sum(dist.values())
        for label in ["tich_cuc", "trung_tinh", "tieu_cuc"]:
            cnt = dist.get(label, 0)
            pct = 100 * cnt / total_valid if total_valid else 0
            lines.append(f"    {label:12s}: {cnt:4d} ({pct:.1f}%)")
        lines.append("")

    return lines


def compute_agreement(df: pd.DataFrame, col1: str, col2: str) -> tuple[list[str], pd.DataFrame]:
    """Tính Cohen κ, % nhất trí, ma trận nhầm lẫn. Chỉ dùng tin cả 2 người gán hợp lệ."""
    lines = ["=== ĐỒNG THUẬN GIỮA 2 NGƯỜI GÁN ===\n"]

    # Chỉ giữ dòng cả 2 nhãn đều hợp lệ
    valid_mask = df[col1].isin(VALID_LABELS) & df[col2].isin(VALID_LABELS)
    valid_df = df[valid_mask].copy()
    n_valid = len(valid_df)
    n_dropped = len(df) - n_valid

    lines.append(f"Số tin dùng để tính đồng thuận (cả 2 nhãn hợp lệ): {n_valid}")
    if n_dropped > 0:
        lines.append(f"  (bỏ qua {n_dropped} tin có ít nhất 1 nhãn trống/không hợp lệ)")
    lines.append("")

    if n_valid == 0:
        lines.append("❌ Không có tin nào hợp lệ để tính — kiểm tra lại tên cột và giá trị nhãn.")
        return lines, valid_df

    y1 = valid_df[col1]
    y2 = valid_df[col2]

    # % nhất trí thô
    agree = (y1.values == y2.values).sum()
    pct_agree = 100 * agree / n_valid
    lines.append(f"Nhất trí thô (raw agreement): {agree}/{n_valid} = {pct_agree:.1f}%")

    # Cohen's Kappa
    kappa = cohen_kappa_score(y1, y2, labels=sorted(VALID_LABELS))
    lines.append(f"Cohen's Kappa (κ): {kappa:.3f}")
    lines.append(f"  → Diễn giải: {interpret_kappa(kappa)}")
    lines.append("")

    # Krippendorff alpha (nếu có thư viện)
    try:
        import krippendorff

        label_to_int = {"tieu_cuc": 0, "trung_tinh": 1, "tich_cuc": 2}
        rel_data = [
            [label_to_int[v] for v in y1],
            [label_to_int[v] for v in y2],
        ]
        alpha = krippendorff.alpha(reliability_data=rel_data, level_of_measurement="nominal")
        lines.append(f"Krippendorff's alpha (α): {alpha:.3f}")
    except ImportError:
        lines.append("Krippendorff's alpha: (chưa cài thư viện 'krippendorff' — bỏ qua)")
    lines.append("")

    # Ma trận nhầm lẫn
    labels_sorted = ["tieu_cuc", "trung_tinh", "tich_cuc"]
    cm = confusion_matrix(y1, y2, labels=labels_sorted)
    lines.append("Ma trận nhầm lẫn (hàng = Người 1, cột = Người 2):")
    header = "           " + "  ".join(f"{lb:>10s}" for lb in labels_sorted)
    lines.append(header)
    for i, lb in enumerate(labels_sorted):
        row = f"{lb:>10s} " + "  ".join(f"{cm[i][j]:>10d}" for j in range(len(labels_sorted)))
        lines.append(row)
    lines.append("")

    # Cặp lệch nhiều nhất
    lines.append("Các ô bất đồng lớn nhất (ngoài đường chéo):")
    disagreements = []
    for i, lb1 in enumerate(labels_sorted):
        for j, lb2 in enumerate(labels_sorted):
            if i != j and cm[i][j] > 0:
                disagreements.append((cm[i][j], lb1, lb2))
    disagreements.sort(reverse=True)
    for cnt, lb1, lb2 in disagreements[:5]:
        lines.append(f"  {cnt:3d} tin: Người 1 gán '{lb1}' nhưng Người 2 gán '{lb2}'")
    lines.append("")

    return lines, valid_df


def interpret_kappa(kappa: float) -> str:
    """Thang Landis & Koch 1977."""
    if kappa < 0:
        return "tệ hơn ngẫu nhiên (poor)"
    if kappa < 0.20:
        return "rất thấp (slight)"
    if kappa < 0.40:
        return "thấp (fair) — CHƯA ĐẠT ngưỡng 0.6"
    if kappa < 0.60:
        return "trung bình (moderate) — CHƯA ĐẠT ngưỡng 0.6"
    if kappa < 0.80:
        return "tốt (substantial) — ✅ ĐẠT ngưỡng 0.6"
    return "rất tốt (almost perfect) — ✅ ĐẠT"


def split_gold_and_disagreement(
    df: pd.DataFrame, col1: str, col2: str, id_col: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tách tin nhất trí (gold) và bất đồng. Chỉ xét tin cả 2 nhãn hợp lệ."""
    valid_mask = df[col1].isin(VALID_LABELS) & df[col2].isin(VALID_LABELS)
    valid_df = df[valid_mask].copy()

    agree_mask = valid_df[col1] == valid_df[col2]
    gold = valid_df[agree_mask].copy()
    gold["gold_label"] = gold[col1]  # nhãn nhất trí

    disagree = valid_df[~agree_mask].copy()
    return gold, disagree


def main():
    parser = argparse.ArgumentParser(description="Tính IAA + kiểm tra chất lượng nhãn")
    # Chế độ 1: 1 file có 2 cột nhãn
    parser.add_argument("--input", help="1 file CSV chứa cả 2 cột nhãn")
    # Chế độ 2: 2 file riêng, join theo khoá
    parser.add_argument("--file1", help="File nhãn người 1 (chế độ 2 file)")
    parser.add_argument("--file2", help="File nhãn người 2 (chế độ 2 file)")
    parser.add_argument("--label-col1", default="nhan", help="Tên cột nhãn trong file người 1")
    parser.add_argument("--label-col2", default="nhan_chu", help="Tên cột nhãn trong file người 2")
    parser.add_argument("--join-key", default="url", help="Cột khoá để join 2 file")
    # Chung
    parser.add_argument("--col1", default="nhan_1", help="Tên cột nhãn người 1 (chế độ 1 file)")
    parser.add_argument("--col2", default="nhan_2", help="Tên cột nhãn người 2 (chế độ 1 file)")
    parser.add_argument("--id-col", default="url", help="Tên cột định danh tin")
    parser.add_argument("--report", default="results/tables/iaa_report.txt")
    parser.add_argument("--gold-out", default="data/gold/gold_labels.csv")
    parser.add_argument("--disagree-out", default="data/gold/bat_dong.csv")
    args = parser.parse_args()

    if args.file1 and args.file2:
        # Chế độ 2 file
        df = load_two_files(
            Path(args.file1), Path(args.file2),
            args.label_col1, args.label_col2, args.join_key,
        )
        args.col1, args.col2 = "nhan_1", "nhan_2"
    elif args.input:
        # Chế độ 1 file
        df = load_annotations(Path(args.input), args.col1, args.col2)
    else:
        parser.error("Cần --input (1 file) HOẶC cả --file1 và --file2 (2 file)")

    df[args.col1] = normalize_labels(df[args.col1])
    df[args.col2] = normalize_labels(df[args.col2])

    report_lines = []
    report_lines.append("#" * 60)
    report_lines.append("# BÁO CÁO IAA — Đề tài NCKH LLM-VN30")
    report_lines.append("#" * 60)
    report_lines.append("")

    report_lines += check_quality(df, args.col1, args.col2)
    agreement_lines, _ = compute_agreement(df, args.col1, args.col2)
    report_lines += agreement_lines

    gold, disagree = split_gold_and_disagreement(df, args.col1, args.col2, args.id_col)
    report_lines.append("=== TÁCH NHÃN VÀNG / BẤT ĐỒNG ===\n")
    report_lines.append(f"Tin NHẤT TRÍ (gold labels): {len(gold)}")
    report_lines.append(f"Tin BẤT ĐỒNG (cần phân xử): {len(disagree)}")
    report_lines.append("")

    # Ghi file
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.gold_out).parent.mkdir(parents=True, exist_ok=True)
    report_text = "\n".join(report_lines)
    Path(args.report).write_text(report_text, encoding="utf-8")
    gold.to_csv(args.gold_out, index=False, encoding="utf-8-sig")
    disagree.to_csv(args.disagree_out, index=False, encoding="utf-8-sig")

    print(report_text)
    print(f"\n✅ Báo cáo: {args.report}")
    print(f"✅ Nhãn vàng ({len(gold)} tin): {args.gold_out}")
    print(f"✅ Bất đồng ({len(disagree)} tin): {args.disagree_out}")


if __name__ == "__main__":
    main()
