"""
6G Prediction Service - Backend Microservice
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any
import logging
from datetime import datetime
from pydantic import BaseModel

# Configuration
from config import MODEL_PATHS, LOG_LEVEL

# Setup logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="6G Prediction Service",
    description="ML prediction service for 6G network slicing objectives",
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
    """Load all 6G ML models"""
    try:
        # 6G Objective 5.1 - Classification
        models['classification'] = joblib.load(MODEL_PATHS['classification'])
        scalers['classification'] = joblib.load(MODEL_PATHS['scaler_classification'])
        encoders['classification'] = joblib.load(MODEL_PATHS['target_encoder_classification'])
        
        # 6G Objective 5.2 - Regression
        models['regression'] = joblib.load(MODEL_PATHS['regression'])
        scalers['regression'] = joblib.load(MODEL_PATHS['scaler_regression'])
        
        # 6G Objective 5.3 - Anomaly Detection
        models['anomaly'] = joblib.load(MODEL_PATHS['anomaly'])
        scalers['anomaly'] = joblib.load(MODEL_PATHS['scaler_anomaly'])
        
        logger.info("6G models loaded successfully")
        return True
    except Exception as e:
        logger.error(f"Error loading 6G models: {e}")
        return False

# Pydantic models
class ClassificationFeatures(BaseModel):
    """Input features for 6G classification (Objective 5.1)"""
    packet_loss_budget: float
    latency_budget: float
    jitter_budget: float
    data_rate_budget: float
    slice_available_transfer_rate: float
    slice_latency: float
    slice_packet_loss: float
    slice_jitter: float
    slice_handover: float

class RegressionFeatures(BaseModel):
    """Input features for 6G regression (Objective 5.2)"""
    latency_gap: float
    packet_loss_gap: float
    jitter_gap: float
    rate_gap: float

class AnomalyFeatures(BaseModel):
    """Input features for 6G anomaly detection (Objective 5.3)"""
    packet_loss_budget: float
    latency_budget: float
    jitter_budget: float
    data_rate_budget: float
    slice_available_transfer_rate: float
    slice_latency: float
    slice_packet_loss: float
    slice_jitter: float
    slice_handover: float

# Load models on startup
@app.on_event("startup")
async def startup_event():
    """Initialize 6G prediction service"""
    success = load_models()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to load 6G models")

# Health check
@app.get("/health")
async def health_check():
    """Check if 6G service is healthy"""
    return {
        "service": "6G Prediction Service",
        "status": "healthy",
        "models_loaded": len(models),
        "objectives": ["5.1", "5.2", "5.3"],
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "6G Prediction Service",
        "version": "1.0.0",
        "objectives": {
            "5.1": "Congestion Classification",
            "5.2": "QoS Probability Regression",
            "5.3": "Anomaly Detection"
        },
        "endpoints": [
            "/predict/6g/classification",
            "/predict/6g/regression",
            "/predict/6g/anomaly",
            "/health"
        ]
    }

# 6G Objective 5.1 - Classification
@app.post("/predict/6g/classification")
async def predict_6g_classification(features: ClassificationFeatures):
    """Predict congestion classification for 6G Objective 5.1"""
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
            "objective": "6G Objective 5.1",
            "prediction_type": "Congestion Classification",
            "predicted_class": predicted_class,
            "confidence": confidence,
            "class_probabilities": probabilities,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"6G classification prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

# 6G Objective 5.2 - Regression
@app.post("/predict/6g/regression")
async def predict_6g_regression(features: RegressionFeatures):
    """Predict QoS probability for 6G Objective 5.2"""
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
            "objective": "6G Objective 5.2",
            "prediction_type": "QoS Probability Regression",
            "qos_probability": float(prediction),
            "risk_level": risk_level,
            "action_required": action,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"6G regression prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

# 6G Objective 5.3 - Anomaly Detection
@app.post("/predict/6g/anomaly")
async def predict_6g_anomaly(features: AnomalyFeatures):
    """Detect network anomalies for 6G Objective 5.3"""
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
            "objective": "6G Objective 5.3",
            "prediction_type": "Anomaly Detection",
            "anomaly_score": float(anomaly_score),
            "is_anomaly": bool(is_anomaly),
            "threshold": float(threshold),
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"6G anomaly detection error: {e}")
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")

# Batch predictions for all 6G objectives
@app.post("/predict/6g/batch")
async def predict_6g_batch(
    classification_features: ClassificationFeatures,
    regression_features: RegressionFeatures,
    anomaly_features: AnomalyFeatures
):
    """Batch prediction for all 6G objectives"""
    try:
        # Get predictions for all objectives
        classification_result = await predict_6g_classification(classification_features)
        regression_result = await predict_6g_regression(regression_features)
        anomaly_result = await predict_6g_anomaly(anomaly_features)
        
        return {
            "service": "6G Prediction Service",
            "batch_results": {
                "objective_5_1": classification_result,
                "objective_5_2": regression_result,
                "objective_5_3": anomaly_result
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"6G batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
