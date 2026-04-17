"""
Configuration for Trustworthy AI Service
"""

import os

# Service configuration
SERVICE_NAME = "trustworthy-ai-service"
SERVICE_VERSION = "1.0.0"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8003))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Trustworthy AI configuration
SUPPORTED_MODEL_TYPES = ["classification", "regression", "anomaly"]
EXPLAINABILITY_METHODS = ["shap", "lime", "permutation"]
FAIRNESS_METRICS = ["statistical_parity", "equal_opportunity", "equalized_odds", "demographic_parity"]
DRIFT_DETECTION_METHODS = ["ks_test", "psi", "kl_divergence"]
MONITORING_TIME_RANGES = ["1h", "6h", "24h", "7d"]

# Thresholds
FAIRNESS_THRESHOLD = float(os.getenv("FAIRNESS_THRESHOLD", 0.8))
DRIFT_THRESHOLD = float(os.getenv("DRIFT_THRESHOLD", 0.5))
ALERT_THRESHOLD = float(os.getenv("ALERT_THRESHOLD", 0.7))
