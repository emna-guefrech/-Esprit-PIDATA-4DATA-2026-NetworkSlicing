# ══════════════════════════════════════════════════════════════════
# Dockerfile — 5G + 6G Network Slicing Unified API
# ══════════════════════════════════════════════════════════════════

# Base image: slim Python 3.11
FROM python:3.11-slim

# Metadata
LABEL maintainer="emna"
LABEL description="5G + 6G Network Slicing Unified FastAPI Service"
LABEL version="1.0.0"

# Set working directory inside the container
WORKDIR /app

# ── Install system dependencies ───────────────────────────────────
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# ── Copy requirements first (for Docker layer caching) ───────────
COPY shared_api/requirements.txt /app/requirements.txt

# ── Install Python dependencies in stages ────────────────────────
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir numpy pandas joblib seaborn matplotlib
RUN pip install --no-cache-dir scikit-learn
RUN pip install --no-cache-dir xgboost
RUN pip install --no-cache-dir fastapi uvicorn python-multipart
RUN pip install --no-cache-dir river
RUN pip install --no-cache-dir shap
RUN pip install --no-cache-dir mlflow

# ── Copy both pipelines and the shared API ────────────────────────
COPY 5g_pipeline/model_pipeline.py          /app/5g_pipeline/model_pipeline.py
COPY 5g_pipeline/models/                    /app/5g_pipeline/models/
COPY 6g_pipeline/model_pipeline.py          /app/6g_pipeline/model_pipeline.py
COPY 6g_pipeline/models/                    /app/6g_pipeline/models/
COPY 6g_pipeline/xai_artifacts/             /app/6g_pipeline/xai_artifacts/
COPY shared_api/app.py                      /app/shared_api/app.py

# ── Set working directory to shared_api ───────────────────────────
WORKDIR /app/shared_api

# ── Expose port 8000 ──────────────────────────────────────────────
EXPOSE 8000

# ── Health check ──────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# ── Start the FastAPI server ──────────────────────────────────────
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
