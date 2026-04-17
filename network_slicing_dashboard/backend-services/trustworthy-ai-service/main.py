"""
Trustworthy AI Service - Backend Microservice
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
import logging
from pydantic import BaseModel
from typing import Dict, Any, List

# Configuration
from config import LOG_LEVEL

# Setup logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Trustworthy AI Service",
    description="Explainability, fairness, drift detection, and monitoring service",
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
class ExplainabilityRequest(BaseModel):
    """Request for model explainability"""
    model_type: str = Field(..., regex="^(classification|regression|anomaly)$")
    features: Dict[str, Any]
    prediction_result: Dict[str, Any]

class FairnessRequest(BaseModel):
    """Request for fairness analysis"""
    model_type: str = Field(..., regex="^(classification|regression|anomaly)$")
    dataset_path: str
    sensitive_features: List[str]

class DriftRequest(BaseModel):
    """Request for drift detection"""
    model_type: str = Field(..., regex="^(classification|regression|anomaly)$")
    reference_data: List[Dict[str, Any]]
    current_data: List[Dict[str, Any]]

class MonitoringRequest(BaseModel):
    """Request for system monitoring"""
    service_name: str
    time_range: str = Field(..., regex="^(1h|6h|24h|7d)$")

# Mock explainability functions
def generate_shap_explanation(features: Dict[str, Any], prediction_result: Dict[str, Any]):
    """Generate SHAP-like explanation"""
    # Create mock SHAP values
    feature_names = list(features.keys())
    shap_values = np.random.uniform(-0.5, 0.5, len(feature_names))
    
    # Create explanation
    explanation = {
        "feature_importance": {
            feature_names[i]: float(shap_values[i]) 
            for i in range(len(feature_names))
        },
        "base_value": float(np.random.uniform(0, 1)),
        "prediction": prediction_result.get("predicted_class", "Unknown"),
        "explanation_text": f"Model prediction {prediction_result.get('predicted_class', 'Unknown')} is primarily influenced by {feature_names[np.argmax(np.abs(shap_values))]}"
    }
    
    return explanation

def analyze_fairness(sensitive_features: List[str], dataset_path: str):
    """Analyze model fairness"""
    # Mock fairness analysis
    fairness_metrics = {
        "statistical_parity": np.random.uniform(0.8, 0.95),
        "equal_opportunity": np.random.uniform(0.85, 0.92),
        "equalized_odds": np.random.uniform(0.82, 0.90),
        "demographic_parity": np.random.uniform(0.78, 0.93)
    }
    
    # Determine fairness verdict
    avg_fairness = np.mean(list(fairness_metrics.values()))
    if avg_fairness >= 0.9:
        verdict = "Excellent"
    elif avg_fairness >= 0.8:
        verdict = "Good"
    elif avg_fairness >= 0.7:
        verdict = "Fair"
    else:
        verdict = "Poor"
    
    recommendations = []
    if fairness_metrics["statistical_parity"] < 0.85:
        recommendations.append("Consider re-weighting training data")
    if fairness_metrics["equal_opportunity"] < 0.85:
        recommendations.append("Adjust decision thresholds")
    if fairness_metrics["equalized_odds"] < 0.85:
        recommendations.append("Implement fairness constraints")
    
    return {
        "fairness_metrics": fairness_metrics,
        "verdict": verdict,
        "recommendations": recommendations,
        "sensitive_features_analyzed": sensitive_features
    }

def detect_concept_drift(reference_data: List[Dict[str, Any]], current_data: List[Dict[str, Any]]):
    """Detect concept drift"""
    # Mock drift detection
    drift_scores = {
        "feature_drift": np.random.uniform(0.1, 0.8),
        "label_drift": np.random.uniform(0.05, 0.6),
        "concept_drift": np.random.uniform(0.0, 0.7)
    }
    
    # Determine drift severity
    max_drift = max(drift_scores.values())
    if max_drift >= 0.7:
        severity = "High"
    elif max_drift >= 0.4:
        severity = "Medium"
    else:
        severity = "Low"
    
    recommendations = []
    if drift_scores["feature_drift"] > 0.5:
        recommendations.append("Retrain model with new feature distributions")
    if drift_scores["label_drift"] > 0.4:
        recommendations.append("Update label encoding")
    if drift_scores["concept_drift"] > 0.5:
        recommendations.append("Consider model architecture changes")
    
    return {
        "drift_scores": drift_scores,
        "severity": severity,
        "recommendations": recommendations,
        "data_points_analyzed": len(reference_data) + len(current_data)
    }

def generate_monitoring_metrics(service_name: str, time_range: str):
    """Generate monitoring metrics"""
    # Mock monitoring metrics
    metrics = {
        "request_count": np.random.randint(100, 10000),
        "success_rate": np.random.uniform(0.95, 0.999),
        "avg_response_time": np.random.uniform(50, 500),
        "error_rate": np.random.uniform(0.001, 0.05),
        "cpu_usage": np.random.uniform(20, 80),
        "memory_usage": np.random.uniform(30, 70),
        "active_connections": np.random.randint(10, 1000)
    }
    
    # Generate alerts
    alerts = []
    if metrics["success_rate"] < 0.98:
        alerts.append("Low success rate detected")
    if metrics["avg_response_time"] > 300:
        alerts.append("High response time detected")
    if metrics["cpu_usage"] > 80:
        alerts.append("High CPU usage")
    if metrics["memory_usage"] > 80:
        alerts.append("High memory usage")
    
    return {
        "service_name": service_name,
        "time_range": time_range,
        "metrics": metrics,
        "alerts": alerts,
        "health_status": "Healthy" if len(alerts) == 0 else "Warning"
    }

# Health check
@app.get("/health")
async def health_check():
    """Check if Trustworthy AI service is healthy"""
    return {
        "service": "Trustworthy AI Service",
        "status": "healthy",
        "capabilities": ["explainability", "fairness", "drift_detection", "monitoring"],
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Trustworthy AI Service",
        "version": "1.0.0",
        "capabilities": {
            "explainability": "SHAP-like explanations for ML models",
            "fairness": "Bias detection and fairness analysis",
            "drift_detection": "Concept drift detection and monitoring",
            "monitoring": "System health and performance monitoring"
        },
        "endpoints": [
            "/explain/shap",
            "/fairness/analyze",
            "/drift/detect",
            "/monitoring/metrics",
            "/health"
        ]
    }

# Explainability endpoints
@app.post("/explain/shap")
async def explain_shap(request: ExplainabilityRequest):
    """Generate SHAP-like explanation for model prediction"""
    try:
        explanation = generate_shap_explanation(request.features, request.prediction_result)
        
        return {
            "service": "Trustworthy AI - Explainability",
            "model_type": request.model_type,
            "explanation": explanation,
            "method": "SHAP-like",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"SHAP explanation error: {e}")
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")

@app.post("/explain/feature-importance")
async def get_feature_importance(model_type: str, features: List[str]):
    """Get feature importance for a model"""
    try:
        # Mock feature importance
        importance_scores = np.random.uniform(0.1, 1.0, len(features))
        
        feature_importance = {
            features[i]: float(importance_scores[i]) 
            for i in range(len(features))
        }
        
        # Sort by importance
        sorted_features = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
        
        return {
            "service": "Trustworthy AI - Explainability",
            "model_type": model_type,
            "feature_importance": sorted_features,
            "top_features": list(sorted_features.keys())[:5],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Feature importance error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# Fairness endpoints
@app.post("/fairness/analyze")
async def analyze_fairness_endpoint(request: FairnessRequest):
    """Analyze model fairness"""
    try:
        fairness_result = analyze_fairness(request.sensitive_features, request.dataset_path)
        
        return {
            "service": "Trustworthy AI - Fairness",
            "model_type": request.model_type,
            "fairness_analysis": fairness_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Fairness analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/fairness/metrics")
async def get_fairness_metrics(model_type: str):
    """Get fairness metrics for a model"""
    try:
        # Mock metrics
        metrics = {
            "demographic_parity_difference": np.random.uniform(0.0, 0.2),
            "equal_opportunity_difference": np.random.uniform(0.0, 0.15),
            "average_odds_difference": np.random.uniform(0.0, 0.18),
            "theil_index": np.random.uniform(0.1, 0.3)
        }
        
        return {
            "service": "Trustworthy AI - Fairness",
            "model_type": model_type,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Fairness metrics error: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics failed: {str(e)}")

# Drift detection endpoints
@app.post("/drift/detect")
async def detect_drift_endpoint(request: DriftRequest):
    """Detect concept drift"""
    try:
        drift_result = detect_concept_drift(request.reference_data, request.current_data)
        
        return {
            "service": "Trustworthy AI - Drift Detection",
            "model_type": request.model_type,
            "drift_analysis": drift_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Drift detection error: {e}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

@app.get("/drift/status")
async def get_drift_status(model_type: str):
    """Get current drift status"""
    try:
        # Mock drift status
        status = {
            "current_drift_score": np.random.uniform(0.0, 0.6),
            "last_check": datetime.utcnow().isoformat(),
            "drift_detected": np.random.choice([True, False]),
            "severity": np.random.choice(["Low", "Medium", "High"])
        }
        
        return {
            "service": "Trustworthy AI - Drift Detection",
            "model_type": model_type,
            "drift_status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Drift status error: {e}")
        raise HTTPException(status_code=500, detail=f"Status failed: {str(e)}")

# Monitoring endpoints
@app.post("/monitoring/metrics")
async def get_monitoring_metrics(request: MonitoringRequest):
    """Get monitoring metrics for a service"""
    try:
        metrics_result = generate_monitoring_metrics(request.service_name, request.time_range)
        
        return {
            "service": "Trustworthy AI - Monitoring",
            "monitoring_data": metrics_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Monitoring metrics error: {e}")
        raise HTTPException(status_code=500, detail=f"Monitoring failed: {str(e)}")

@app.get("/monitoring/health")
async def get_system_health():
    """Get overall system health"""
    try:
        # Mock system health
        services = ["6G Prediction", "5G Prediction", "Model Management", "API Gateway"]
        health_status = {}
        
        for service in services:
            health_status[service] = {
                "status": np.random.choice(["Healthy", "Warning", "Error"]),
                "uptime": np.random.uniform(0.95, 1.0),
                "last_check": datetime.utcnow().isoformat()
            }
        
        overall_health = "Healthy" if all(s["status"] == "Healthy" for s in health_status.values()) else "Warning"
        
        return {
            "service": "Trustworthy AI - Monitoring",
            "overall_health": overall_health,
            "services": health_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"System health error: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
