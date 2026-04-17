"""
Configuration for 5G Prediction Service
"""

import os

# Service configuration
SERVICE_NAME = "5g-prediction-service"
SERVICE_VERSION = "1.0.0"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8002))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 5G specific configuration
SUPPORTED_OBJECTIVES = ["A", "B", "C"]
MODEL_TYPE = "mock"  # Change to "real" when using real models
PERFORMANCE_LEVELS = ["Excellent", "Good", "Fair", "Poor"]
OPTIMIZATION_LEVELS = ["Highly Optimized", "Well Optimized", "Moderately Optimized", "Poorly Optimized"]
ALLOCATION_EFFICIENCY_LEVELS = ["Highly Efficient", "Efficient", "Moderately Efficient", "Inefficient"]
