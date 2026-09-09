# NCKH-VN-FinSent

**Đánh giá khả năng của các mô hình ngôn ngữ lớn open-source trong phân tích cảm xúc tin tức tài chính tiếng Việt và kiểm định khả năng dự báo trên thị trường chứng khoán Việt Nam.**

Đề tài Nghiên cứu Khoa học Sinh viên 2026 — Trường Đại học Việt Nhật (VJU) — ĐHQGHN.

## Nhóm nghiên cứu

| Vai trò | Thành viên | MSSV |
|---|---|---|
| Chủ nhiệm — LLM/Benchmark lead | Trần Ngô Tiến Đạt | 25112231 |
| Data Engineering + IAA coordinator | Phạm Hồng Duyên | 25112235 |
| Finance / Econometrics lead | Lê Văn Thái An | 25112001 |

Giảng viên hướng dẫn: TS. Bùi Huy Kiên.

## Đóng góp chính

1. **Bộ dữ liệu chuẩn so sánh (benchmark dataset)**: ~300 tin tài chính tiếng Việt về 30 mã VN30, gán nhãn 3 lớp cảm xúc (tích cực / trung tính / tiêu cực), Cohen κ ≥ 0.6. Công khai theo giấy phép CC-BY 4.0.
2. **Systematic benchmark**: so sánh 5 phương pháp trên cùng một tập gold — lexicon, PhoBERT fine-tuned, Qwen2.5-7B (zero-shot & few-shot), Llama-3.1-8B, và Claude Haiku (điểm neo thương mại).
3. **LoRA fine-tuning**: adapter weights cho Qwen2.5-7B trên tin tài chính tiếng Việt (`FinVN-Qwen-LoRA`), công khai trên HuggingFace Hub.
4. **Event study**: đo lợi suất bất thường (CAR) quanh các sự kiện tin tức, phân tách theo cảm xúc.
5. **Kết quả có ý nghĩa thống kê**: bootstrap CI, McNemar test giữa các model, kiểm định t + Wilcoxon cho CAR.

## Yêu cầu hệ thống

- Python 3.10+
- CUDA 11.8+ cho fine-tune LoRA (GPU ≥16GB VRAM cho Qwen2.5-7B)
- Docker (tuỳ chọn, cho reproducibility)
- ~20GB dung lượng cho model weights + data

## Cài đặt nhanh

```bash
git clone https://github.com/muoibuon121-commits/nckh-vn-finsent.git
cd nckh-vn-finsent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pre-commit install
```

Hoặc dùng Docker:
```bash
docker build -t nckh-finsent .
docker run --gpus all -it -v $(pwd):/workspace nckh-finsent
```

## Tái lập kết quả

```bash
make reproduce   # Chạy full pipeline từ raw data đến bảng kết quả
```

Chi tiết từng bước xem `docs/setup.md`.

## Cấu trúc thư mục

```
configs/          # YAML config cho model & event study
data/             # raw (gitignored), processed, gold (300 tin có nhãn)
src/              # code chính, chia theo module
notebooks/        # 5 notebooks demo end-to-end
scripts/          # bash scripts wrap pipeline
results/          # bảng + hình cho báo cáo
paper/            # LaTeX bản thảo
docs/             # annotation guideline, setup guide
```

## Giấy phép

- Code: MIT
- Dataset (300 tin có nhãn): CC-BY 4.0
- Model weights (LoRA adapters): Apache 2.0 (tuân theo giấy phép của Qwen)

## Trích dẫn

```bibtex
@misc{tran2026finvn,
  title  = {Evaluating Open-Source Large Language Models for Vietnamese
            Financial News Sentiment Analysis and VN30 Return Prediction},
  author = {Tran, Ngo Tien Dat and Pham, Hong Duyen and Le, Van Thai An},
  year   = {2026},
  note   = {Undergraduate research project, Vietnam-Japan University}
}
```
