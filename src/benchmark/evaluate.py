"""Module đánh giá chuẩn cho bài toán phân loại cảm xúc 3 lớp mất cân bằng.

Dùng chung cho MỌI model (lexicon, PhoBERT, Qwen, Llama, Claude...) để so sánh công bằng.
Chỉ số chính là MACRO-F1 (không phải accuracy) vì dữ liệu mất cân bằng nặng.

Cách dùng:
    from src.benchmark.evaluate import evaluate_predictions
    result = evaluate_predictions(y_true, y_pred, model_name="PhoBERT")
    print(result.summary())
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)

LABELS = ["tieu_cuc", "trung_tinh", "tich_cuc"]


@dataclass
class EvalResult:
    model_name: str
    accuracy: float
    macro_f1: float
    macro_f1_ci: tuple[float, float]  # bootstrap 95% CI
    per_class_f1: dict[str, float]
    per_class_precision: dict[str, float]
    per_class_recall: dict[str, float]
    per_class_support: dict[str, int]
    confusion: np.ndarray
    n_samples: int
    extra: dict = field(default_factory=dict)  # cost, latency...

    def summary(self) -> str:
        lines = []
        lines.append(f"=== {self.model_name} (n={self.n_samples}) ===")
        lines.append(f"Accuracy : {self.accuracy:.3f}  (⚠️ không dùng làm chỉ số chính — dữ liệu lệch)")
        lines.append(
            f"Macro-F1 : {self.macro_f1:.3f}  "
            f"[95% CI: {self.macro_f1_ci[0]:.3f}–{self.macro_f1_ci[1]:.3f}]  ← CHỈ SỐ CHÍNH"
        )
        lines.append("")
        lines.append("F1 / Precision / Recall / Support từng lớp:")
        for lb in LABELS:
            lines.append(
                f"  {lb:12s}: F1={self.per_class_f1[lb]:.3f}  "
                f"P={self.per_class_precision[lb]:.3f}  "
                f"R={self.per_class_recall[lb]:.3f}  "
                f"(n={self.per_class_support[lb]})"
            )
        lines.append("")
        lines.append("Confusion matrix (hàng=thật, cột=dự đoán):")
        header = "           " + "  ".join(f"{lb:>10s}" for lb in LABELS)
        lines.append(header)
        for i, lb in enumerate(LABELS):
            row = f"{lb:>10s} " + "  ".join(f"{self.confusion[i][j]:>10d}" for j in range(len(LABELS)))
            lines.append(row)
        if self.extra:
            lines.append("")
            lines.append("Chi phí / độ trễ:")
            for k, v in self.extra.items():
                lines.append(f"  {k}: {v}")
        return "\n".join(lines)

    def to_row(self) -> dict:
        """1 dòng cho bảng benchmark tổng hợp."""
        row = {
            "model": self.model_name,
            "accuracy": round(self.accuracy, 4),
            "macro_f1": round(self.macro_f1, 4),
            "macro_f1_ci_low": round(self.macro_f1_ci[0], 4),
            "macro_f1_ci_high": round(self.macro_f1_ci[1], 4),
            "f1_tieu_cuc": round(self.per_class_f1["tieu_cuc"], 4),
            "f1_trung_tinh": round(self.per_class_f1["trung_tinh"], 4),
            "f1_tich_cuc": round(self.per_class_f1["tich_cuc"], 4),
        }
        row.update(self.extra)
        return row


def bootstrap_macro_f1_ci(
    y_true: np.ndarray, y_pred: np.ndarray, n_boot: int = 2000, seed: int = 42
) -> tuple[float, float]:
    """Bootstrap 95% CI cho macro-F1. Quan trọng vì lớp hiếm khiến F1 dao động mạnh."""
    rng = np.random.default_rng(seed)
    n = len(y_true)
    scores = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)  # resample có hoàn lại
        yt, yp = y_true[idx], y_pred[idx]
        # bỏ mẫu bootstrap nếu thiếu lớp (hiếm) — tính F1 với labels cố định
        f1 = f1_score(yt, yp, labels=LABELS, average="macro", zero_division=0)
        scores.append(f1)
    lo, hi = np.percentile(scores, [2.5, 97.5])
    return float(lo), float(hi)


def evaluate_predictions(
    y_true, y_pred, model_name: str = "model", extra: dict | None = None, seed: int = 42
) -> EvalResult:
    """Đánh giá đầy đủ 1 model. y_true/y_pred là list/array nhãn dạng chữ (LABELS)."""
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    acc = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0)
    ci = bootstrap_macro_f1_ci(y_true, y_pred, seed=seed)

    prec, rec, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=LABELS, zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred, labels=LABELS)

    return EvalResult(
        model_name=model_name,
        accuracy=float(acc),
        macro_f1=float(macro_f1),
        macro_f1_ci=ci,
        per_class_f1={lb: float(f1[i]) for i, lb in enumerate(LABELS)},
        per_class_precision={lb: float(prec[i]) for i, lb in enumerate(LABELS)},
        per_class_recall={lb: float(rec[i]) for i, lb in enumerate(LABELS)},
        per_class_support={lb: int(support[i]) for i, lb in enumerate(LABELS)},
        confusion=cm,
        n_samples=len(y_true),
        extra=extra or {},
    )


def mcnemar_test(y_true, y_pred_a, y_pred_b) -> dict:
    """Kiểm định McNemar so sánh 2 model trên cùng test set.

    Trả p-value: nếu p < 0.05, chênh lệch giữa 2 model có ý nghĩa thống kê.
    Đây là điểm mấu chốt để kết luận 'model A tốt hơn B' — không chỉ nhìn F1.
    """
    from statsmodels.stats.contingency_tables import mcnemar

    y_true = np.asarray(y_true)
    a_correct = np.asarray(y_pred_a) == y_true
    b_correct = np.asarray(y_pred_b) == y_true

    # bảng 2x2: (A đúng/sai) x (B đúng/sai)
    n00 = int(np.sum(~a_correct & ~b_correct))  # cả 2 sai
    n01 = int(np.sum(~a_correct & b_correct))   # A sai, B đúng
    n10 = int(np.sum(a_correct & ~b_correct))   # A đúng, B sai
    n11 = int(np.sum(a_correct & b_correct))    # cả 2 đúng

    table = [[n11, n10], [n01, n00]]
    result = mcnemar(table, exact=(n01 + n10 < 25))  # exact khi mẫu bất đồng nhỏ
    return {
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "significant_at_0.05": bool(result.pvalue < 0.05),
        "a_only_correct": n10,
        "b_only_correct": n01,
    }
