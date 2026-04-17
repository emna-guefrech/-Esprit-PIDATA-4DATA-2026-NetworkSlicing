"""
Configuration for Monitoring Service
"""

import os

# Service configuration
SERVICE_NAME = "monitoring-service"
SERVICE_VERSION = "1.0.0"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8004))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Monitoring configuration
METRICS_RETENTION_HOURS = int(os.getenv("METRICS_RETENTION_HOURS", 24))
ALERT_THRESHOLD_CPU = float(os.getenv("ALERT_THRESHOLD_CPU", 80.0))
ALERT_THRESHOLD_MEMORY = float(os.getenv("ALERT_THRESHOLD_MEMORY", 80.0))
ALERT_THRESHOLD_ERROR_RATE = float(os.getenv("ALERT_THRESHOLD_ERROR_RATE", 0.05))
