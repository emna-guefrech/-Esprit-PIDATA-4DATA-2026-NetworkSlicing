# ══════════════════════════════════════════════════════════════════
# Makefile — 5G Network Slice Classification Pipeline
# ══════════════════════════════════════════════════════════════════

PYTHON     = python3
VENV       = venv
PIP        = $(VENV)/bin/pip
PYTEST     = $(VENV)/bin/pytest
FLAKE8     = $(VENV)/bin/flake8
BLACK      = $(VENV)/bin/black
BANDIT     = $(VENV)/bin/bandit
MAIN       = main.py
SRC        = model_pipeline.py main.py
TESTS      = tests/

.PHONY: all install format lint security test \
        prepare train_rf evaluate_rf \
        train_xgb evaluate_xgb \
        train_anomaly evaluate_anomaly \
        train_online evaluate_online \
        save load pipeline ci clean help \
        api api_docs \
        mlflow

# ── Default target ────────────────────────────────────────────────
all: ci pipeline

# ── Help ──────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  Available commands:"
	@echo ""
	@echo "  Setup"
	@echo "    make install          Install all dependencies"
	@echo ""
	@echo "  Code Quality (CI)"
	@echo "    make format           Auto-format code with black"
	@echo "    make lint             Check code quality with flake8"
	@echo "    make security         Check security with bandit"
	@echo "    make test             Run all tests with pytest"
	@echo "    make ci               Run all CI steps"
	@echo ""
	@echo "  ML Pipeline"
	@echo "    make prepare          Prepare and clean the data"
	@echo "    make train_rf         Train Random Forest"
	@echo "    make evaluate_rf      Evaluate Random Forest"
	@echo "    make train_xgb        Train XGBoost (SLA risk)"
	@echo "    make evaluate_xgb     Evaluate XGBoost"
	@echo "    make train_anomaly    Train anomaly detection ensemble"
	@echo "    make evaluate_anomaly Evaluate anomaly detection"
	@echo "    make train_online     Train online HAT model"
	@echo "    make evaluate_online  Evaluate online HAT model"
	@echo "    make save             Save models to disk"
	@echo "    make load             Load models from disk"
	@echo "    make pipeline         Run the full ML pipeline"
	@echo ""
	@echo "  API"
	@echo "    make api              Start FastAPI server"
	@echo "    make api_docs         Show API documentation link"
	@echo ""
	@echo "  Cleanup"
	@echo "    make clean            Remove generated files"
	@echo ""

# ── Setup ─────────────────────────────────────────────────────────
install:
	@echo ">>> Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	@echo ">>> Installing dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo ">>> Installation complete ✅"

# ── Code Quality (CI steps) ───────────────────────────────────────
format:
	@echo ">>> Auto-formatting code with black..."
	$(BLACK) $(SRC)
	@echo ">>> Formatting complete ✅"

lint:
	@echo ">>> Checking code quality with flake8..."
	$(FLAKE8) $(SRC) --max-line-length=120 --ignore=E501,W503
	@echo ">>> Linting complete ✅"

security:
	@echo ">>> Checking security with bandit..."
	$(BANDIT) -r $(SRC) -ll
	@echo ">>> Security check complete ✅"

test:
	@echo ">>> Running tests with pytest..."
	$(PYTEST) $(TESTS) -v --tb=short
	@echo ">>> Tests complete ✅"

ci: format lint security test
	@echo ""
	@echo ">>> All CI steps passed ✅"
	@echo ""

# ── ML Pipeline steps ─────────────────────────────────────────────
prepare:
	@echo ">>> Preparing data..."
	$(PYTHON) $(MAIN) --action prepare

train_rf:
	@echo ">>> Training Random Forest..."
	$(PYTHON) $(MAIN) --action train_rf

evaluate_rf:
	@echo ">>> Evaluating Random Forest..."
	$(PYTHON) $(MAIN) --action evaluate_rf

train_xgb:
	@echo ">>> Training XGBoost..."
	$(PYTHON) $(MAIN) --action train_xgb

evaluate_xgb:
	@echo ">>> Evaluating XGBoost..."
	$(PYTHON) $(MAIN) --action evaluate_xgb

train_anomaly:
	@echo ">>> Training Anomaly Detection..."
	$(PYTHON) $(MAIN) --action train_anomaly

evaluate_anomaly:
	@echo ">>> Evaluating Anomaly Detection..."
	$(PYTHON) $(MAIN) --action evaluate_anomaly

train_online:
	@echo ">>> Training Online HAT Model..."
	$(PYTHON) $(MAIN) --action train_online

evaluate_online:
	@echo ">>> Evaluating Online HAT Model..."
	$(PYTHON) $(MAIN) --action evaluate_online

save:
	@echo ">>> Saving models..."
	$(PYTHON) $(MAIN) --action save

load:
	@echo ">>> Loading models..."
	$(PYTHON) $(MAIN) --action load

pipeline: prepare train_rf evaluate_rf train_xgb evaluate_xgb \
          train_anomaly evaluate_anomaly \
          train_online evaluate_online \
          save load
	@echo ""
	@echo ">>> Full ML pipeline complete ✅"
	@echo ""

# ── API ───────────────────────────────────────────────────────────
api:
	@echo ">>> Starting FastAPI server..."
	$(VENV)/bin/uvicorn app:app --reload --host 0.0.0.0 --port 8000

api_docs:
	@echo ">>> Opening API docs..."
	@echo "Visit: http://127.0.0.1:8000/docs"

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


# ── Cleanup ───────────────────────────────────────────────────────
clean:
	@echo ">>> Cleaning up generated files..."
	rm -f *.pkl
	rm -f *.csv
	rm -rf __pycache__
	rm -rf tests/__pycache__
	rm -rf .pytest_cache
	@echo ">>> Cleanup complete ✅"
