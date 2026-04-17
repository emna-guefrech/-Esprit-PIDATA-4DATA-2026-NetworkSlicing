"""
API Gateway - Backend Microservice
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
from typing import Dict, Any
import logging
from datetime import datetime, timedelta
import jwt
import os

# Configuration
from config import SERVICE_URLS, JWT_SECRET, JWT_ALGORITHM

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="6G/5G Network Slicing API Gateway",
    description="Gateway for 6G/5G network slicing microservices",
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

# Service clients
sixg_client = httpx.AsyncClient(base_url=SERVICE_URLS["sixg_prediction"])
fiveg_client = httpx.AsyncClient(base_url=SERVICE_URLS["fiveg_prediction"])
trustworthy_client = httpx.AsyncClient(base_url=SERVICE_URLS["trustworthy_ai"])
monitoring_client = httpx.AsyncClient(base_url=SERVICE_URLS["monitoring"])

# JWT Functions
def create_jwt_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=1)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Health check
@app.get("/health")
async def health_check():
    """Check if gateway and all services are healthy"""
    services_status = {}
    
    async def check_service(name: str, client: httpx.AsyncClient):
        try:
            response = await client.get("/health")
            services_status[name] = response.status_code == 200
        except Exception:
            services_status[name] = False
    
    await asyncio.gather(
        check_service("6G Prediction", sixg_client),
        check_service("5G Prediction", fiveg_client),
        check_service("Trustworthy AI", trustworthy_client),
        check_service("Monitoring", monitoring_client)
    )
    
    return {
        "gateway": "healthy",
        "services": services_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "6G/5G Network Slicing API Gateway",
        "version": "1.0.0",
        "backend_services": {
            "6G Prediction": "http://6g-prediction-service:8001",
            "5G Prediction": "http://5g-prediction-service:8002",
            "Trustworthy AI": "http://trustworthy-ai-service:8003",
            "Monitoring": "http://monitoring-service:8004"
        },
        "endpoints": [
            "/auth/login",
            "/predict/6g/*",
            "/predict/5g/*",
            "/explain/*",
            "/fairness/*",
            "/drift/*",
            "/monitoring/*",
            "/health"
        ]
    }

# Authentication
@app.post("/auth/login")
async def login(username: str, password: str):
    """Authenticate user and return JWT token"""
    # Simple authentication (in production, use database)
    if username == "admin" and password == "admin123":
        token = create_jwt_token({"sub": username, "role": "admin"})
        return {"access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# 6G Prediction Routes
@app.post("/predict/6g/classification")
async def predict_6g_classification(
    features: Dict[str, Any],
    authorization: str = None
):
    """Route to 6G prediction service for classification"""
    try:
        headers = {}
        if authorization:
            headers["Authorization"] = authorization
            
        response = await sixg_client.post("/predict/6g/classification", json=features, headers=headers)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"6G prediction service error: {e}")
        raise HTTPException(status_code=503, detail="6G prediction service unavailable")

@app.post("/predict/6g/regression")
async def predict_6g_regression(
    features: Dict[str, Any],
    authorization: str = None
):
    """Route to 6G prediction service for regression"""
    try:
        headers = {}
        if authorization:
            headers["Authorization"] = authorization
            
        response = await sixg_client.post("/predict/6g/regression", json=features, headers=headers)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"6G prediction service error: {e}")
        raise HTTPException(status_code=503, detail="6G prediction service unavailable")

@app.post("/predict/6g/anomaly")
async def predict_6g_anomaly(
    features: Dict[str, Any],
    authorization: str = None
):
    """Route to 6G prediction service for anomaly detection"""
    try:
        headers = {}
        if authorization:
            headers["Authorization"] = authorization
            
        response = await sixg_client.post("/predict/6g/anomaly", json=features, headers=headers)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"6G prediction service error: {e}")
        raise HTTPException(status_code=503, detail="6G prediction service unavailable")

# 5G Prediction Routes
@app.post("/predict/5g/objective-a")
async def predict_5g_objective_a(
    features: Dict[str, Any],
    authorization: str = None
):
    """Route to 5G prediction service for objective A"""
    try:
        headers = {}
        if authorization:
            headers["Authorization"] = authorization
            
        response = await fiveg_client.post("/predict/5g/objective-a", json=features, headers=headers)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"5G prediction service error: {e}")
        raise HTTPException(status_code=503, detail="5G prediction service unavailable")

@app.post("/predict/5g/objective-b")
async def predict_5g_objective_b(
    features: Dict[str, Any],
    authorization: str = None
):
    """Route to 5G prediction service for objective B"""
    try:
        headers = {}
        if authorization:
            headers["Authorization"] = authorization
            
        response = await fiveg_client.post("/predict/5g/objective-b", json=features, headers=headers)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"5G prediction service error: {e}")
        raise HTTPException(status_code=503, detail="5G prediction service unavailable")

@app.post("/predict/5g/objective-c")
async def predict_5g_objective_c(
    features: Dict[str, Any],
    authorization: str = None
):
    """Route to 5G prediction service for objective C"""
    try:
        headers = {}
        if authorization:
            headers["Authorization"] = authorization
            
        response = await fiveg_client.post("/predict/5g/objective-c", json=features, headers=headers)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"5G prediction service error: {e}")
        raise HTTPException(status_code=503, detail="5G prediction service unavailable")

# Trustworthy AI Routes
@app.post("/explain/shap")
async def explain_shap(
    request_data: Dict[str, Any],
    authorization: str = None
):
    """Route to trustworthy AI service for SHAP explanation"""
    try:
        headers = {}
        if authorization:
            headers["Authorization"] = authorization
            
        response = await trustworthy_client.post("/explain/shap", json=request_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Trustworthy AI service error: {e}")
        raise HTTPException(status_code=503, detail="Trustworthy AI service unavailable")

@app.post("/fairness/analyze")
async def analyze_fairness(
    request_data: Dict[str, Any],
    authorization: str = None
):
    """Route to trustworthy AI service for fairness analysis"""
    try:
        headers = {}
        if authorization:
            headers["Authorization"] = authorization
            
        response = await trustworthy_client.post("/fairness/analyze", json=request_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Trustworthy AI service error: {e}")
        raise HTTPException(status_code=503, detail="Trustworthy AI service unavailable")

@app.post("/drift/detect")
async def detect_drift(
    request_data: Dict[str, Any],
    authorization: str = None
):
    """Route to trustworthy AI service for drift detection"""
    try:
        headers = {}
        if authorization:
            headers["Authorization"] = authorization
            
        response = await trustworthy_client.post("/drift/detect", json=request_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Trustworthy AI service error: {e}")
        raise HTTPException(status_code=503, detail="Trustworthy AI service unavailable")

# Monitoring Routes
@app.post("/monitoring/metrics")
async def get_monitoring_metrics(
    request_data: Dict[str, Any],
    authorization: str = None
):
    """Route to monitoring service for metrics"""
    try:
        headers = {}
        if authorization:
            headers["Authorization"] = authorization
            
        response = await monitoring_client.post("/monitoring/metrics", json=request_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Monitoring service error: {e}")
        raise HTTPException(status_code=503, detail="Monitoring service unavailable")

# Batch predictions
@app.post("/predict/batch/all")
async def predict_batch_all(
    sixg_features: Dict[str, Any],
    fiveg_features: Dict[str, Any],
    authorization: str = None
):
    """Batch prediction for all services"""
    try:
        headers = {}
        if authorization:
            headers["Authorization"] = authorization
        
        # Get 6G predictions
        sixg_response = await sixg_client.post("/predict/6g/batch", json=sixg_features, headers=headers)
        
        # Get 5G predictions
        fiveg_response = await fiveg_client.post("/predict/5g/batch", json=fiveg_features, headers=headers)
        
        return {
            "batch_results": {
                "6G": sixg_response.json(),
                "5G": fiveg_response.json()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except httpx.HTTPError as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=503, detail="Batch prediction failed")

# Service status
@app.get("/services/status")
async def get_services_status():
    """Get status of all backend services"""
    services_status = {}
    
    async def check_service(name: str, client: httpx.AsyncClient):
        try:
            response = await client.get("/health")
            services_status[name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds(),
                "last_check": datetime.utcnow().isoformat()
            }
        except Exception as e:
            services_status[name] = {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    await asyncio.gather(
        check_service("6G Prediction", sixg_client),
        check_service("5G Prediction", fiveg_client),
        check_service("Trustworthy AI", trustworthy_client),
        check_service("Monitoring", monitoring_client)
    )
    
    return {
        "gateway_services": services_status,
        "total_services": len(services_status),
        "healthy_services": sum(1 for s in services_status.values() if s["status"] == "healthy"),
        "timestamp": datetime.utcnow().isoformat()
    }

# Shutdown
@app.on_event("shutdown")
async def shutdown():
    """Close HTTP clients"""
    await sixg_client.aclose()
    await fiveg_client.aclose()
    await trustworthy_client.aclose()
    await monitoring_client.aclose()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
