"""Baseline lexicon cho phân loại cảm xúc tin tài chính tiếng Việt.

Cung cấp HAI từ điển để so sánh trực tiếp (theo tinh thần Loughran & McDonald 2011):
  1. GENERAL  — từ cảm xúc chung tiếng Việt (tốt/xấu/vui/buồn...)
  2. FINANCE  — từ chuyên ngành tài chính có trọng số (lãi/lỗ/cổ tức/xử phạt...)

Luận điểm khoa học: từ điển chung áp vào miền tài chính kém hiệu quả hơn từ điển
chuyên ngành — vì nhiều từ "xấu" trong đời thường lại trung tính trong tài chính
(vd "nợ" là bình thường), và ngược lại.

Cách chạy:
    python3 -m src.models.lexicon --test data/processed/test.csv --lexicon finance
    python3 -m src.models.lexicon --test data/processed/test.csv --lexicon general
    python3 -m src.models.lexicon --test data/processed/test.csv --lexicon both  # so sánh

Cách hoạt động: đếm điểm cảm xúc trong (tiêu đề + nội dung), có xử lý phủ định
("không tăng" → đảo dấu). Điểm > ngưỡng → tich_cuc; < -ngưỡng → tieu_cuc; giữa → trung_tinh.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

# ============================================================
# TỪ ĐIỂN 1 — CẢM XÚC CHUNG (mô phỏng VietSentiWordNet)
# Từ cảm xúc đời thường, không chuyên ngành tài chính.
# ============================================================
GENERAL_LEXICON = {
    # tích cực chung
    "tốt": 1, "tuyệt": 1, "xuất sắc": 1, "vui": 1, "mừng": 1, "hạnh phúc": 1,
    "thành công": 1, "tích cực": 1, "lạc quan": 1, "ấn tượng": 1, "hài lòng": 1,
    "tuyệt vời": 1, "đỉnh": 1, "bứt phá": 1, "kỷ lục": 1, "dẫn đầu": 1,
    "vượt trội": 1, "mạnh": 1, "khởi sắc": 1, "hồi phục": 1, "thăng hoa": 1,
    "hứng khởi": 1, "phấn khởi": 1, "khả quan": 1, "sáng": 1, "bùng nổ": 1,
    # tiêu cực chung
    "xấu": -1, "tệ": -1, "kém": -1, "buồn": -1, "lo": -1, "lo ngại": -1,
    "thất bại": -1, "tiêu cực": -1, "bi quan": -1, "thất vọng": -1, "khó khăn": -1,
    "yếu": -1, "giảm sút": -1, "suy giảm": -1, "khủng hoảng": -1, "rủi ro": -1,
    "nguy cơ": -1, "sụt": -1, "lao dốc": -1, "ảm đạm": -1, "u ám": -1,
    "căng thẳng": -1, "bất ổn": -1, "tồi tệ": -1, "sa sút": -1, "đáng ngại": -1,
}

# ============================================================
# TỪ ĐIỂN 2 — TÀI CHÍNH CHUYÊN NGÀNH (có trọng số)
# Từ có tác động tài chính thực, trọng số theo mức độ.
# ============================================================
FINANCE_LEXICON = {
    # ---- tích cực tài chính ----
    "lãi": 1.0, "lợi nhuận": 1.0, "lãi ròng": 1.5, "lãi sau thuế": 1.5,
    "tăng trưởng": 1.0, "doanh thu tăng": 1.5, "vượt kế hoạch": 2.0,
    "trúng thầu": 2.0, "trúng gói thầu": 2.0, "ký hợp đồng": 1.5,
    "cổ tức tiền mặt": 2.0, "chia cổ tức": 1.5, "mua cổ phiếu quỹ": 2.0,
    "mua lại cổ phiếu": 1.5, "đăng ký mua": 1.5, "khối ngoại mua": 1.0,
    "nâng hạng": 2.0, "vào rổ": 1.5, "biên lợi nhuận": 0.5, "cải thiện": 1.0,
    "vượt dự báo": 2.0, "kỷ lục lợi nhuận": 2.0, "thắng kiện": 1.5,
    "tất toán nợ": 1.5, "thoái vốn": 0.5, "hoàn thành vượt mức": 2.0,
    "khả quan": 1.0, "hồi phục": 1.0, "phục hồi": 1.0,
    # ---- tiêu cực tài chính ----
    "lỗ": -1.5, "thua lỗ": -2.0, "lỗ ròng": -2.0, "lỗ lũy kế": -1.5,
    "lãi giảm": -1.5, "doanh thu giảm": -1.5, "sụt giảm lợi nhuận": -2.0,
    "không đạt kế hoạch": -1.5, "bị xử phạt": -2.0, "xử phạt": -1.5,
    "thanh tra": -1.0, "khởi tố": -2.5, "điều tra": -1.5, "thua kiện": -1.5,
    "nợ xấu": -2.0, "chậm trả": -2.0, "vỡ nợ": -2.5, "mất thanh khoản": -2.5,
    "hủy niêm yết": -2.5, "cảnh báo": -1.5, "kiểm soát": -1.0, "đình chỉ": -2.0,
    "từ chức": -1.5, "bị bắt": -2.5, "từ chối ý kiến": -2.0, "đăng ký bán": -1.5,
    "khối ngoại bán": -1.0, "bán ròng": -1.0, "phát hành thêm": -1.0,
    "pha loãng": -1.5, "thu hồi": -1.5, "mất hợp đồng": -2.0, "sự cố": -1.5,
    "vi phạm": -1.5, "gian lận": -2.5, "phá sản": -2.5,
}

# Từ phủ định — đảo dấu điểm của từ theo sau (trong cửa sổ 3 từ)
NEGATION_WORDS = {"không", "chưa", "chẳng", "khỏi", "đâu", "phi", "bất"}

# Ngưỡng quyết định nhãn (điều chỉnh được)
DEFAULT_THRESHOLD = 1.0

LABELS = ["tieu_cuc", "trung_tinh", "tich_cuc"]


def normalize_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"\s+", " ", text)
    return text


def score_text(text: str, lexicon: dict[str, float]) -> float:
    """Tính tổng điểm cảm xúc, có xử lý phủ định đơn giản.

    Quét từng cụm từ trong lexicon; nếu 1-3 từ trước đó là phủ định, đảo dấu.
    """
    text = normalize_text(text)
    tokens = text.split()
    total = 0.0

    # sắp cụm từ dài trước (ưu tiên khớp cụm dài như "cổ tức tiền mặt")
    phrases = sorted(lexicon.keys(), key=lambda p: -len(p.split()))

    # đánh dấu vị trí đã dùng để tránh đếm trùng cụm lồng nhau
    consumed = [False] * len(tokens)

    for phrase in phrases:
        p_tokens = phrase.split()
        plen = len(p_tokens)
        for i in range(len(tokens) - plen + 1):
            if any(consumed[i : i + plen]):
                continue
            if tokens[i : i + plen] == p_tokens:
                weight = lexicon[phrase]
                # kiểm tra phủ định trong 3 từ trước
                window = tokens[max(0, i - 3) : i]
                if any(w in NEGATION_WORDS for w in window):
                    weight = -weight
                total += weight
                for j in range(i, i + plen):
                    consumed[j] = True
    return total


def classify(score: float, threshold: float = DEFAULT_THRESHOLD) -> str:
    if score >= threshold:
        return "tich_cuc"
    if score <= -threshold:
        return "tieu_cuc"
    return "trung_tinh"


def predict_dataframe(
    df: pd.DataFrame, lexicon: dict[str, float], threshold: float = DEFAULT_THRESHOLD
) -> pd.Series:
    """Dự đoán nhãn cho mỗi tin. Dùng tiêu đề (trọng số x2) + nội dung."""
    preds = []
    for _, row in df.iterrows():
        title = str(row.get("tieu_de", ""))
        content = str(row.get("noi_dung", ""))
        # tiêu đề quan trọng hơn → nhân đôi ảnh hưởng
        s = 2 * score_text(title, lexicon) + score_text(content[:1500], lexicon)
        preds.append(classify(s, threshold))
    return pd.Series(preds, index=df.index)


def run_and_evaluate(test_path: str, lexicon_name: str, threshold: float):
    """Chạy 1 lexicon, đánh giá qua module evaluate."""
    from src.benchmark.evaluate import evaluate_predictions

    df = pd.read_csv(test_path, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]
    y_true = df["nhan_final"]

    lex = FINANCE_LEXICON if lexicon_name == "finance" else GENERAL_LEXICON
    y_pred = predict_dataframe(df, lex, threshold)

    result = evaluate_predictions(
        y_true, y_pred, model_name=f"Lexicon-{lexicon_name}",
        extra={"lexicon_size": len(lex), "threshold": threshold},
    )
    return result, y_pred


def main():
    parser = argparse.ArgumentParser(description="Baseline lexicon classifier")
    parser.add_argument("--test", default="data/processed/test.csv")
    parser.add_argument("--lexicon", choices=["general", "finance", "both"], default="both")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--out", default="results/tables")
    args = parser.parse_args()

    Path(args.out).mkdir(parents=True, exist_ok=True)
    names = ["general", "finance"] if args.lexicon == "both" else [args.lexicon]

    rows = []
    for name in names:
        result, y_pred = run_and_evaluate(args.test, name, args.threshold)
        print(result.summary())
        print()
        rows.append(result.to_row())
        pd.DataFrame({"y_pred": y_pred}).to_csv(
            Path(args.out) / f"pred_lexicon_{name}.csv", index=False, encoding="utf-8-sig"
        )

    comp = pd.DataFrame(rows)
    comp_path = Path(args.out) / "lexicon_comparison.csv"
    comp.to_csv(comp_path, index=False, encoding="utf-8-sig")
    print("=" * 55)
    print("SO SÁNH 2 LEXICON")
    print("=" * 55)
    print(comp[["model", "accuracy", "macro_f1", "f1_tieu_cuc", "f1_trung_tinh", "f1_tich_cuc"]].to_string(index=False))
    print(f"\n✅ Đã lưu bảng so sánh: {comp_path}")

    if args.lexicon == "both" and len(rows) == 2:
        gen_f1 = rows[0]["macro_f1"]
        fin_f1 = rows[1]["macro_f1"]
        print(f"\n→ Lexicon tài chính {'TỐT HƠN' if fin_f1 > gen_f1 else 'KHÔNG hơn'} "
              f"lexicon chung: macro-F1 {fin_f1:.3f} vs {gen_f1:.3f}")
        print("  (kỳ vọng theo Loughran & McDonald 2011: từ điển chuyên ngành > từ điển chung)")


if __name__ == "__main__":
    main()
