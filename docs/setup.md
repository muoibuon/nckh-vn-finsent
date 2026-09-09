# Hướng dẫn cài đặt & tái lập

## 1. Yêu cầu

- Python 3.10+ (dùng `pyenv` hoặc `conda` để quản lý)
- Git 2.30+
- (Cho LoRA fine-tune) GPU NVIDIA ≥16GB VRAM, CUDA 11.8+
- (Tuỳ chọn) Docker 24+ với nvidia-container-toolkit

## 2. Clone và cài đặt

```bash
git clone https://github.com/muoibuon121-commits/nckh-vn-finsent.git
cd nckh-vn-finsent

# Tạo venv
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
# .venv\Scripts\activate       # Windows

# Cài deps
pip install --upgrade pip
pip install -r requirements.txt

# Cài git hooks
pre-commit install
```

## 3. Cấu hình biến môi trường

```bash
cp .env.example .env
# Mở .env và điền HF_TOKEN, ANTHROPIC_API_KEY (nếu dùng), v.v.
```

Lấy HuggingFace token: https://huggingface.co/settings/tokens

## 4. Kiểm tra cài đặt

```bash
pytest tests/ -v
make lint
```

## 5. Chạy pipeline

### Chạy từng bước

```bash
# Bước 1: thu thập tin
make scrape

# Bước 2: clean + dedup
make clean-data

# Bước 3: tính IAA sau khi đã gán nhãn thủ công
make iaa

# Bước 4: benchmark các model
make benchmark-lexicon
make benchmark-phobert
make benchmark-llm

# Bước 5: LoRA fine-tune (cần GPU)
make lora-train

# Bước 6: event study + hồi quy
make event-study
make regression

# Bước 7: backtest minh hoạ
make backtest
```

### Chạy toàn bộ

```bash
make reproduce
```

## 6. Docker (cho reproducibility tuyệt đối)

```bash
make docker-build
make docker-run
```

Trong container:
```bash
make reproduce
```

## 7. Xử lý sự cố

**Lỗi CUDA out of memory khi fine-tune Qwen-7B:**
- Giảm `batch_size` trong `configs/models/lora_qwen.yaml`
- Bật gradient checkpointing
- Đổi sang QLoRA 4-bit (đã cài `bitsandbytes`)

**Lỗi khi scrape (bị chặn IP):**
- Giảm nhịp request trong `src/scraping/base.py`
- Đổi User-Agent
- Dùng proxy hoặc Selenium

**PhoBERT tokenizer báo lỗi:**
- Kiểm tra `sentencepiece` đã cài
- Chạy `python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('vinai/phobert-base')"`

## 8. Cấu trúc log

Mọi script ghi log vào `logs/<timestamp>_<module>.log`. Kiểm tra ở đây nếu có lỗi.
