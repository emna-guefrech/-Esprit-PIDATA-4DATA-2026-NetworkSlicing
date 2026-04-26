# ══════════════════════════════════════════════════════════════════
#  Makefile — 6G Network Slicing ML Pipeline
#  Usage: make <target>
# ══════════════════════════════════════════════════════════════════

PYTHON      = python3
PIP         = pip
VENV        = .venv
VENV_PYTHON = $(VENV)/bin/python
VENV_PIP    = $(VENV)/bin/pip
SRC         = model_pipeline.py main.py
TESTS       = tests/

.PHONY: all install venv prepare train evaluate test lint format security clean help cicd mlflow

# ── Default target ────────────────────────────────────────────────
all: install lint format security prepare train evaluate test
	@echo "✅ Full pipeline complete!"

# ── Help ──────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "Available targets:"
	@echo "  make install    — Create venv & install requirements.txt"
	@echo "  make prepare    — Run data preparation (DSO prepare step)"
	@echo "  make train      — Train all models (DSO1, 5.2, 5.3, 5.4)"
	@echo "  make evaluate   — Evaluate all models"
	@echo "  make test       — Run pytest test suite"
	@echo "  make lint       — Check code quality with flake8"
	@echo "  make format     — Auto-format code with black"
	@echo "  make security   — Scan for security issues with bandit"
	@echo "  make cicd       — Run full CI/CD pipeline (lint+format+security+prepare+train+test)"
	@echo "  make clean      — Remove generated files and venv"
	@echo ""

# ── Environment ───────────────────────────────────────────────────
venv:
	@echo "🐍 Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	@echo "✅ Virtual environment created at $(VENV)/"

install: venv
	@echo "📦 Installing dependencies..."
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements.txt
	@echo "✅ All dependencies installed."

# ── CI steps ─────────────────────────────────────────────────────
lint:
	@echo "🔍 Checking code quality with flake8..."
	$(VENV_PYTHON) -m flake8 $(SRC) --max-line-length=120 --ignore=E501,W503 || true
	@echo "✅ Lint done."

format:
	@echo "🎨 Auto-formatting code with black..."
	$(VENV_PYTHON) -m black $(SRC) --line-length=120
	@echo "✅ Format done."

security:
	@echo "🔒 Scanning for security issues with bandit..."
	$(VENV_PYTHON) -m bandit -r $(SRC) -ll || true
	@echo "✅ Security scan done."

# ── Pipeline steps ────────────────────────────────────────────────
prepare:
	@echo "📥 Preparing data..."
	$(VENV_PYTHON) main.py --step prepare
	@echo "✅ Data preparation done."

train:
	@echo "🚀 Training all models..."
	$(VENV_PYTHON) main.py --step dso1
	$(VENV_PYTHON) main.py --step dso52
	$(VENV_PYTHON) main.py --step dso53
	$(VENV_PYTHON) main.py --step dso54
	@echo "✅ All models trained."

evaluate:
	@echo "📊 Evaluation is included in each train step above."
	@echo "   PNG plots saved in current directory."
	@ls -lh *.png 2>/dev/null || echo "   No plots found yet — run make train first."

test:
	@echo "🧪 Running tests..."
	$(VENV_PYTHON) -m pytest $(TESTS) -v --tb=short
	@echo "✅ Tests done."

# ── Full CI/CD pipeline ───────────────────────────────────────────
cicd: lint format security prepare train test
	@echo ""
	@echo "🎉 CI/CD pipeline finished successfully!"

# ── MLflow ────────────────────────────────────────────────────────
mlflow:
	@echo ">>> Starting MLflow UI (shared backend)..."
	$(VENV)/bin/mlflow ui \
		--backend-store-uri sqlite:///../mlflow.db \
		--host 0.0.0.0 --port 5000 &
	@echo ">>> MLflow UI available at: http://127.0.0.1:5000"

# ── Monitoring ────────────────────────────────────────────────────
monitoring_up:
	@echo ">>> Starting Elasticsearch + Kibana..."
	cd ../monitoring && sudo docker-compose up -d
	@echo ">>> Elasticsearch: http://localhost:9200"
	@echo ">>> Kibana:        http://localhost:5601"

monitoring_down:
	@echo ">>> Stopping monitoring stack..."
	cd ../monitoring && sudo docker-compose down

mlflow:
	@echo ">>> Starting MLflow UI..."
	$(VENV)/bin/mlflow ui \
		--backend-store-uri sqlite:////home/emna/network_slicing_pipeline/mlflow.db \
		--host 0.0.0.0 --port 5000 &
	@echo ">>> MLflow UI: http://127.0.0.1:5000"


# ── Clean ─────────────────────────────────────────────────────────
clean:
	@echo "🧹 Cleaning up..."
	rm -rf $(VENV)
	rm -rf __pycache__ .pytest_cache
	rm -rf models/ xai_artifacts/
	rm -f *.png *.csv *.pkl
	find . -name "*.pyc" -delete
	@echo "✅ Clean done."
