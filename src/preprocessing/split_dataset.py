"""Chia dataset thành train/val/test theo cách STRATIFIED (giữ tỉ lệ 3 lớp ở mọi tập)
và tính class weights để xử lý mất cân bằng khi train PhoBERT.

Vì sao stratified: dữ liệu chỉ có 55 tin tiêu_cực (3.7%). Nếu chia ngẫu nhiên thường,
test set có thể chỉ dính vài tin tiêu_cực → F1 lớp đó vô nghĩa. Stratified đảm bảo
mỗi tập giữ đúng tỉ lệ 3 lớp.

Cách dùng:
    python3 -m src.preprocessing.split_dataset \
        --input data/gold/mau_gan_nhan_final.csv \
        --label-col nhan_final \
        --out-dir data/processed \
        --seed 42
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

LABELS = ["tieu_cuc", "trung_tinh", "tich_cuc"]


def compute_class_weights(y: pd.Series) -> dict[str, float]:
    """Trọng số nghịch đảo tần suất, chuẩn hoá để trung bình = 1.

    Dùng cho CrossEntropyLoss(weight=...) khi train PhoBERT — phạt nặng hơn khi
    model sai ở lớp hiếm.
    """
    counts = y.value_counts()
    n = len(y)
    k = len(counts)
    # weight_c = n / (k * count_c)  — công thức sklearn 'balanced'
    weights = {label: n / (k * counts[label]) for label in counts.index}
    return weights


def main():
    parser = argparse.ArgumentParser(description="Chia train/val/test stratified + class weights")
    parser.add_argument("--input", required=True)
    parser.add_argument("--label-col", default="nhan_final")
    parser.add_argument("--out-dir", default="data/processed")
    parser.add_argument("--test-size", type=float, default=0.15)
    parser.add_argument("--val-size", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--drop-empty", action="store_true", default=True,
                       help="Loại tin chưa gán nhãn (mặc định có)")
    args = parser.parse_args()

    df = pd.read_csv(args.input, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]

    if args.label_col not in df.columns:
        raise ValueError(f"Thiếu cột nhãn '{args.label_col}'. Cột có: {list(df.columns)}")

    # loại tin trống nhãn
    before = len(df)
    df = df[df[args.label_col].isin(LABELS)].copy()
    dropped = before - len(df)
    if dropped:
        print(f"Loại {dropped} tin không có nhãn hợp lệ. Còn {len(df)} tin.")

    y = df[args.label_col]

    # ==== Chia stratified: trước tách test, rồi tách val từ phần còn lại ====
    df_trainval, df_test = train_test_split(
        df, test_size=args.test_size, stratify=y, random_state=args.seed
    )
    val_ratio = args.val_size / (1 - args.test_size)  # điều chỉnh tỉ lệ val trên phần còn lại
    df_train, df_val = train_test_split(
        df_trainval,
        test_size=val_ratio,
        stratify=df_trainval[args.label_col],
        random_state=args.seed,
    )

    # ==== Class weights (tính TRÊN TRAIN, không dùng val/test để tránh leakage) ====
    class_weights = compute_class_weights(df_train[args.label_col])

    # ==== Lưu ====
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    df_train.to_csv(out / "train.csv", index=False, encoding="utf-8-sig")
    df_val.to_csv(out / "val.csv", index=False, encoding="utf-8-sig")
    df_test.to_csv(out / "test.csv", index=False, encoding="utf-8-sig")

    meta = {
        "seed": args.seed,
        "total": len(df),
        "train": len(df_train),
        "val": len(df_val),
        "test": len(df_test),
        "class_weights": class_weights,
        "label_order": LABELS,
        "distribution": {
            "train": df_train[args.label_col].value_counts().to_dict(),
            "val": df_val[args.label_col].value_counts().to_dict(),
            "test": df_test[args.label_col].value_counts().to_dict(),
        },
    }
    (out / "split_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # ==== In tóm tắt ====
    print("=" * 55)
    print("CHIA DATASET STRATIFIED")
    print("=" * 55)
    print(f"Seed: {args.seed} (tái lập được)")
    print(f"Train: {len(df_train)} | Val: {len(df_val)} | Test: {len(df_test)}")
    print()
    print("Phân bố 3 lớp mỗi tập (giữ tỉ lệ nhờ stratify):")
    print(f"{'lớp':12s} {'train':>10s} {'val':>10s} {'test':>10s}")
    for lb in LABELS:
        tr = (df_train[args.label_col] == lb).sum()
        va = (df_val[args.label_col] == lb).sum()
        te = (df_test[args.label_col] == lb).sum()
        print(f"{lb:12s} {tr:>10d} {va:>10d} {te:>10d}")
    print()
    print("Class weights (dùng cho CrossEntropyLoss khi train PhoBERT):")
    for lb in LABELS:
        w = class_weights.get(lb, 0)
        print(f"  {lb:12s}: {w:.3f}")
    print()
    print(f"✅ Đã lưu train/val/test + split_meta.json vào {out}/")


if __name__ == "__main__":
    main()
