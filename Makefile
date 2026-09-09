# Makefile — tái lập pipeline bằng 1 lệnh
# Cách dùng: `make <target>`. Xem `make help` để liệt kê target.

.PHONY: help setup install lint format test \
        scrape clean-data annotate iaa \
        benchmark-lexicon benchmark-phobert benchmark-llm \
        lora-train event-study regression backtest \
        reproduce clean docker-build docker-run

PYTHON := python
PIP    := pip
SEED   := 42

help:
	@echo "Targets chính:"
	@echo "  setup           - Tạo venv và cài dependencies"
	@echo "  install         - Cài dependencies vào venv hiện tại"
	@echo "  lint            - Chạy ruff + black --check"
	@echo "  format          - Format code (black + ruff --fix)"
	@echo "  test            - Chạy pytest"
	@echo ""
	@echo "Data pipeline:"
	@echo "  scrape          - Thu thập tin từ 3 nguồn"
	@echo "  clean-data      - Clean + dedup + gán ngày sự kiện"
	@echo "  iaa             - Tính Cohen κ + Krippendorff α"
	@echo ""
	@echo "Modeling:"
	@echo "  benchmark-lexicon    - Chạy baseline lexicon"
	@echo "  benchmark-phobert    - Fine-tune + eval PhoBERT"
	@echo "  benchmark-llm        - Zero/few-shot LLM (Qwen, Llama, ...)"
	@echo "  lora-train           - QLoRA fine-tune Qwen2.5-7B"
	@echo ""
	@echo "Finance:"
	@echo "  event-study     - Ước lượng CAPM + tính CAR"
	@echo "  regression      - Hồi quy chéo CAR ~ sentiment + controls"
	@echo "  backtest        - Backtest chiến lược minh hoạ"
	@echo ""
	@echo "  reproduce       - Chạy TOÀN BỘ pipeline"
	@echo "  clean           - Xoá cache, logs, tmp files"
	@echo "  docker-build    - Build Docker image"
	@echo "  docker-run      - Chạy container với GPU"

# ==== Env ====
setup:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && $(PIP) install --upgrade pip && $(PIP) install -r requirements.txt
	. .venv/bin/activate && pre-commit install

install:
	$(PIP) install -r requirements.txt

# ==== Code quality ====
lint:
	ruff check src/ tests/
	black --check src/ tests/

format:
	black src/ tests/
	ruff check --fix src/ tests/

test:
	pytest tests/ -v --cov=src

# ==== Data pipeline ====
scrape:
	$(PYTHON) -m src.scraping.run --output data/raw/news.parquet --seed $(SEED)

clean-data:
	$(PYTHON) -m src.preprocessing.pipeline --input data/raw/news.parquet --output data/processed/news_clean.parquet

iaa:
	$(PYTHON) -m src.annotation.iaa --input data/gold/annotations.csv --output results/tables/iaa_report.txt

# ==== Benchmark ====
benchmark-lexicon:
	$(PYTHON) -m src.models.lexicon --gold data/gold/labels.csv --output results/tables/lexicon_pred.csv

benchmark-phobert:
	$(PYTHON) -m src.models.phobert_finetune --config configs/models/phobert.yaml --seed $(SEED)

benchmark-llm:
	$(PYTHON) -m src.models.llm_zeroshot --config configs/models/qwen25_7b.yaml
	$(PYTHON) -m src.models.llm_zeroshot --config configs/models/llama31_8b.yaml

lora-train:
	$(PYTHON) -m src.models.llm_lora --config configs/models/lora_qwen.yaml --seed $(SEED)

# ==== Finance ====
event-study:
	$(PYTHON) -m src.event_study.run --config configs/event_study/capm.yaml

regression:
	$(PYTHON) -m src.regression.cross_sectional --input results/tables/car_by_event.parquet

backtest:
	$(PYTHON) -m src.backtest.strategy --input results/tables/predictions.parquet

# ==== Full pipeline ====
reproduce: scrape clean-data iaa benchmark-lexicon benchmark-phobert benchmark-llm lora-train event-study regression backtest
	@echo ""
	@echo "==== Pipeline hoàn tất. Xem kết quả trong results/ ===="

# ==== Cleanup ====
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ipynb_checkpoints -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache .mypy_cache
	rm -rf results/tmp results/debug logs/

# ==== Docker ====
docker-build:
	docker build -t nckh-finsent:latest .

docker-run:
	docker run --gpus all -it --rm \
		-v $(PWD):/workspace \
		-v $(HOME)/.cache/huggingface:/workspace/.cache/huggingface \
		nckh-finsent:latest
