"""
Configuration for Prediction Service
"""

import os

# Model paths
MODEL_PATHS = {
    "classification": os.getenv("CLASSIFICATION_MODEL_PATH", "/app/shared/models/model_classification_eya.joblib"),
    "regression": os.getenv("REGRESSION_MODEL_PATH", "/app/shared/models/model_6G_5_2_xgboost.joblib"),
    "anomaly": os.getenv("ANOMALY_MODEL_PATH", "/app/shared/models/model_anomaly_eya.joblib"),
    "scaler_classification": os.getenv("SCALER_CLASSIFICATION_PATH", "/app/shared/models/scaler_classification_eya.joblib"),
    "scaler_regression": os.getenv("SCALER_REGRESSION_PATH", "/app/shared/models/scaler_6G_5_2_eya.joblib"),
    "scaler_anomaly": os.getenv("SCALER_ANOMALY_PATH", "/app/shared/models/scaler_anomaly_eya.joblib"),
    "target_encoder_classification": os.getenv("TARGET_ENCODER_CLASSIFICATION_PATH", "/app/shared/models/target_encoder_classification_eya.joblib")
}

# Service configuration
SERVICE_NAME = "prediction-service"
SERVICE_VERSION = "1.0.0"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8001))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Performance
MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", 100))
PREDICTION_TIMEOUT = int(os.getenv("PREDICTION_TIMEOUT", 30))

# Model caching
MODEL_CACHE_SIZE = int(os.getenv("MODEL_CACHE_SIZE", 10))
MODEL_CACHE_TTL = int(os.getenv("MODEL_CACHE_TTL", 3600))  # seconds
