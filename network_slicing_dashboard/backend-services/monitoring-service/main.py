"""
Monitoring Service - Backend Microservice
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime
import random
from pydantic import BaseModel
from typing import Dict, Any

# Configuration
from config import LOG_LEVEL

# Setup logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Monitoring Service",
    description="System monitoring and health check service",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class MonitoringRequest(BaseModel):
    """Request for monitoring metrics"""
    service_name: str
    time_range: str = "1h"

# Health check
@app.get("/health")
async def health_check():
    """Check if monitoring service is healthy"""
    return {
        "service": "Monitoring Service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Monitoring Service",
        "version": "1.0.0",
        "endpoints": [
            "/health",
            "/metrics",
            "/monitoring/metrics"
        ]
    }

# Metrics endpoint
@app.post("/monitoring/metrics")
async def get_monitoring_metrics(request: MonitoringRequest):
    """Get monitoring metrics for a service"""
    try:
        # Mock monitoring metrics
        metrics = {
            "service_name": request.service_name,
            "time_range": request.time_range,
            "metrics": {
                "request_count": random.randint(100, 10000),
                "success_rate": random.uniform(0.95, 0.999),
                "avg_response_time": random.uniform(50, 500),
                "error_rate": random.uniform(0.001, 0.05),
                "cpu_usage": random.uniform(20, 80),
                "memory_usage": random.uniform(30, 70),
                "active_connections": random.randint(10, 1000)
            },
            "alerts": [],
            "health_status": "Healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return {
            "service": "Monitoring Service",
            "monitoring_data": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Monitoring metrics error: {e}")
        raise HTTPException(status_code=500, detail=f"Monitoring failed: {str(e)}")

@app.get("/metrics")
async def get_system_metrics():
    """Get overall system metrics"""
    try:
        metrics = {
            "total_requests": random.randint(1000, 50000),
            "total_services": 5,
            "healthy_services": random.randint(4, 5),
            "system_uptime": "24h 15m",
            "avg_cpu_usage": random.uniform(30, 70),
            "avg_memory_usage": random.uniform(40, 60),
            "network_latency": random.uniform(10, 100),
            "disk_usage": random.uniform(20, 80)
        }
        
        return {
            "service": "Monitoring Service",
            "system_metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"System metrics error: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
