"""
Prediction Service for 6G Network Slicing
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, List
import logging
from datetime import datetime
import os
from pydantic import BaseModel, Field

# Configuration
from config import MODEL_PATHS, LOG_LEVEL

# Setup logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="6G Network Slicing Prediction Service",
    description="ML prediction service for 6G network slicing",
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

# Load models
models = {}
scalers = {}
encoders = {}

def load_models():
    """Load all ML models and preprocessors"""
    try:
        # Classification model
        models['classification'] = joblib.load(MODEL_PATHS['classification'])
        scalers['classification'] = joblib.load(MODEL_PATHS['scaler_classification'])
        encoders['classification'] = joblib.load(MODEL_PATHS['target_encoder_classification'])
        
        # Regression model
        models['regression'] = joblib.load(MODEL_PATHS['regression'])
        scalers['regression'] = joblib.load(MODEL_PATHS['scaler_regression'])
        
        # Anomaly model
        models['anomaly'] = joblib.load(MODEL_PATHS['anomaly'])
        scalers['anomaly'] = joblib.load(MODEL_PATHS['scaler_anomaly'])
        
        logger.info("All models loaded successfully")
        return True
    except Exception as e:
        logger.error(f"Error loading models: {e}")
        return False

# Pydantic models for input validation
class ClassificationFeatures(BaseModel):
    """Input features for classification"""
    packet_loss_budget: float = Field(..., ge=0, le=1)
    latency_budget: float = Field(..., ge=0, le=10000)
    jitter_budget: float = Field(..., ge=0, le=10000)
    data_rate_budget: float = Field(..., ge=0, le=10)
    slice_available_transfer_rate: float = Field(..., ge=0, le=10)
    slice_latency: float = Field(..., ge=0, le=10000)
    slice_packet_loss: float = Field(..., ge=0, le=1)
    slice_jitter: float = Field(..., ge=0, le=10000)
    slice_handover: float = Field(..., ge=0, le=5)

class RegressionFeatures(BaseModel):
    """Input features for regression QoS"""
    latency_gap: float
    packet_loss_gap: float
    jitter_gap: float
    rate_gap: float

class AnomalyFeatures(BaseModel):
    """Input features for anomaly detection"""
    packet_loss_budget: float = Field(..., ge=0, le=1)
    latency_budget: float = Field(..., ge=0, le=10000)
    jitter_budget: float = Field(..., ge=0, le=10000)
    data_rate_budget: float = Field(..., ge=0, le=10)
    slice_available_transfer_rate: float = Field(..., ge=0, le=10)
    slice_latency: float = Field(..., ge=0, le=10000)
    slice_packet_loss: float = Field(..., ge=0, le=1)
    slice_jitter: float = Field(..., ge=0, le=10000)
    slice_handover: float = Field(..., ge=0, le=5)

# Load models on startup
@app.on_event("startup")
async def startup_event():
    """Initialize service"""
    success = load_models()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to load models")

# Health check
@app.get("/health")
async def health_check():
    """Check if service is healthy"""
    return {
        "status": "healthy",
        "models_loaded": len(models),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "6G Network Slicing Prediction Service",
        "version": "1.0.0",
        "endpoints": [
            "/predict/classification",
            "/predict/regression", 
            "/predict/anomaly",
            "/health"
        ]
    }

# Classification prediction
@app.post("/predict/classification")
async def predict_classification(features: ClassificationFeatures):
    """Predict congestion classification"""
    try:
        # Convert to DataFrame
        feature_dict = features.dict()
        feature_names = [
            'Packet Loss Budget', 'Latency Budget (µs)', 'Jitter Budget (µs)',
            'Data Rate Budget (Gbps)', 'Slice Available Transfer Rate (Gbps)',
            'Slice Latency (µs)', 'Slice Packet Loss', 'Slice Jitter (µs)', 'Slice Handover'
        ]
        
        X = pd.DataFrame([feature_dict], columns=feature_names)
        
        # Scale features
        X_scaled = scalers['classification'].transform(X)
        
        # Predict
        prediction_encoded = models['classification'].predict(X_scaled)[0]
        prediction_proba = models['classification'].predict_proba(X_scaled)[0]
        
        # Map back to class names
        class_names = encoders['classification'].classes_
        predicted_class = class_names[prediction_encoded]
        confidence = max(prediction_proba) * 100
        
        # Create probability dictionary
        probabilities = {
            class_names[i]: float(prediction_proba[i]) 
            for i in range(len(class_names))
        }
        
        return {
            "predicted_class": predicted_class,
            "confidence": confidence,
            "class_probabilities": probabilities,
            "timestamp": datetime.utcnow().isoformat(),
            "model_version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Classification prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

# Regression prediction
@app.post("/predict/regression")
async def predict_regression(features: RegressionFeatures):
    """Predict QoS probability"""
    try:
        # Convert to DataFrame
        feature_dict = features.dict()
        feature_names = ['Latency_Gap', 'Packet_Loss_Gap', 'Jitter_Gap', 'Rate_Gap']
        
        X = pd.DataFrame([feature_dict], columns=feature_names)
        
        # Scale features
        X_scaled = scalers['regression'].transform(X)
        
        # Predict
        prediction = models['regression'].predict(X_scaled)[0]
        
        # Ensure prediction is in [0, 1] range
        prediction = max(0, min(1, prediction))
        
        # Determine risk level
        if prediction >= 0.8:
            risk_level = "Low Risk"
            action = "Standard monitoring"
        elif prediction >= 0.6:
            risk_level = "Medium Risk"
            action = "Increased monitoring"
        elif prediction >= 0.4:
            risk_level = "Poor Performance"
            action = "Optimization required"
        else:
            risk_level = "Critical Risk"
            action = "Immediate action required"
        
        return {
            "qos_probability": float(prediction),
            "risk_level": risk_level,
            "action_required": action,
            "timestamp": datetime.utcnow().isoformat(),
            "model_version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Regression prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

# Anomaly detection
@app.post("/predict/anomaly")
async def predict_anomaly(features: AnomalyFeatures):
    """Detect network anomalies"""
    try:
        # Convert to DataFrame
        feature_dict = features.dict()
        feature_names = [
            'Packet Loss Budget', 'Latency Budget (µs)', 'Jitter Budget (µs)',
            'Data Rate Budget (Gbps)', 'Required Mobility', 'Required Connectivity',
            'Slice Available Transfer Rate (Gbps)', 'Slice Latency (µs)',
            'Slice Packet Loss', 'Slice Jitter (µs)', 'Slice Type', 'Slice Handover'
        ]
        
        # Add missing categorical features with defaults
        feature_dict.update({
            'Required Mobility': 1,  # medium
            'Required Connectivity': 1,  # medium
            'Slice Type': 4  # feMBB
        })
        
        X = pd.DataFrame([feature_dict], columns=feature_names)
        
        # Scale features
        X_scaled = scalers['anomaly'].transform(X)
        
        # Predict anomaly score
        anomaly_score = models['anomaly'].decision_function(X_scaled)[0]
        
        # Determine if anomaly
        threshold = models['anomaly'].threshold_
        is_anomaly = anomaly_score < threshold
        
        # Determine severity
        if anomaly_score > 0:
            severity = "Normal"
        elif anomaly_score > -0.1:
            severity = "Low"
        elif anomaly_score > -0.3:
            severity = "Medium"
        else:
            severity = "High"
        
        return {
            "anomaly_score": float(anomaly_score),
            "is_anomaly": bool(is_anomaly),
            "threshold": float(threshold),
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "model_version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Anomaly detection error: {e}")
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")

# Batch predictions
@app.post("/predict/batch")
async def predict_batch(
    requests: List[Dict[str, Any]],
    model_type: str = "classification"
):
    """Batch prediction for multiple requests"""
    try:
        results = []
        
        for request_data in requests:
            if model_type == "classification":
                features = ClassificationFeatures(**request_data)
                result = await predict_classification(features)
            elif model_type == "regression":
                features = RegressionFeatures(**request_data)
                result = await predict_regression(features)
            elif model_type == "anomaly":
                features = AnomalyFeatures(**request_data)
                result = await predict_anomaly(features)
            else:
                raise HTTPException(status_code=400, detail="Invalid model type")
            
            results.append(result)
        
        return {
            "results": results,
            "count": len(results),
            "model_type": model_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
