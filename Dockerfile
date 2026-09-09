# CUDA 12.1 + Ubuntu 22.04 — tương thích PyTorch 2.4
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/workspace/.cache/huggingface

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3.10-venv python3-pip \
    git curl wget ca-certificates \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3.10 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

WORKDIR /workspace

# Cài dependencies trước (tận dụng Docker layer cache)
COPY requirements.txt /workspace/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy code (khi build cuối)
COPY . /workspace

# Seed toàn cục
ENV PYTHONHASHSEED=42

CMD ["/bin/bash"]
