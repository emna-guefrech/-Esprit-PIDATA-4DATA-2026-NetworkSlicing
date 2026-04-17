"""
Configuration for API Gateway
"""

import os
from typing import Dict

# Service URLs
SERVICE_URLS: Dict[str, str] = {
    "prediction": os.getenv("PREDICTION_SERVICE_URL", "http://prediction-service:8001"),
    "model": os.getenv("MODEL_SERVICE_URL", "http://model-service:8002"),
    "trustworthy": os.getenv("TRUSTWORTHY_SERVICE_URL", "http://trustworthy-ai-service:8003"),
    "monitoring": os.getenv("MONITORING_SERVICE_URL", "http://monitoring-service:8004"),
    "frontend": os.getenv("FRONTEND_SERVICE_URL", "http://frontend-service:8500")
}

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Rate Limiting
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds

# Circuit Breaker
CIRCUIT_BREAKER_TIMEOUT = int(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "30"))
CIRCUIT_BREAKER_MAX_RETRIES = int(os.getenv("CIRCUIT_BREAKER_MAX_RETRIES", "3"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
