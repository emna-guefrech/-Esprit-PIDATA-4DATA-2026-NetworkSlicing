"""
API Gateway for 6G Network Slicing Microservices
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import asyncio
from typing import Dict, Any
import logging
from datetime import datetime, timedelta
import jwt

# Configuration
from config import SERVICE_URLS, JWT_SECRET, JWT_ALGORITHM

app = FastAPI(
    title="6G Network Slicing API Gateway",
    description="Gateway for 6G Network Slicing microservices",
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

# Security
security = HTTPBearer()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service clients
prediction_client = httpx.AsyncClient(base_url=SERVICE_URLS["prediction"])
model_client = httpx.AsyncClient(base_url=SERVICE_URLS["model"])
trustworthy_client = httpx.AsyncClient(base_url=SERVICE_URLS["trustworthy"])
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

def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Health Check
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
        check_service("prediction", prediction_client),
        check_service("model", model_client),
        check_service("trustworthy", trustworthy_client),
        check_service("monitoring", monitoring_client)
    )
    
    return {
        "gateway": "healthy",
        "services": services_status,
        "timestamp": datetime.utcnow().isoformat()
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

# Prediction Routes
@app.post("/predict/classification")
async def predict_classification(
    features: Dict[str, Any],
    current_user: dict = Depends(verify_jwt_token)
):
    """Route to prediction service for classification"""
    try:
        response = await prediction_client.post("/predict/classification", json=features)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Prediction service error: {e}")
        raise HTTPException(status_code=503, detail="Prediction service unavailable")

@app.post("/predict/regression")
async def predict_regression(
    features: Dict[str, Any],
    current_user: dict = Depends(verify_jwt_token)
):
    """Route to prediction service for regression"""
    try:
        response = await prediction_client.post("/predict/regression", json=features)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Prediction service error: {e}")
        raise HTTPException(status_code=503, detail="Prediction service unavailable")

@app.post("/predict/anomaly")
async def predict_anomaly(
    features: Dict[str, Any],
    current_user: dict = Depends(verify_jwt_token)
):
    """Route to prediction service for anomaly detection"""
    try:
        response = await prediction_client.post("/predict/anomaly", json=features)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Prediction service error: {e}")
        raise HTTPException(status_code=503, detail="Prediction service unavailable")

# Model Management Routes
@app.get("/models")
async def list_models(current_user: dict = Depends(verify_jwt_token)):
    """List available models"""
    try:
        response = await model_client.get("/models")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Model service error: {e}")
        raise HTTPException(status_code=503, detail="Model service unavailable")

@app.post("/models/{model_id}/load")
async def load_model(
    model_id: str,
    current_user: dict = Depends(verify_jwt_token)
):
    """Load specific model"""
    try:
        response = await model_client.post(f"/models/{model_id}/load")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Model service error: {e}")
        raise HTTPException(status_code=503, detail="Model service unavailable")

# Trustworthy AI Routes
@app.post("/explain/shap")
async def explain_shap(
    features: Dict[str, Any],
    current_user: dict = Depends(verify_jwt_token)
):
    """SHAP explanation route"""
    try:
        response = await trustworthy_client.post("/explain/shap", json=features)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Trustworthy service error: {e}")
        raise HTTPException(status_code=503, detail="Trustworthy service unavailable")

@app.post("/fairness/analyze")
async def analyze_fairness(
    features: Dict[str, Any],
    current_user: dict = Depends(verify_jwt_token)
):
    """Fairness analysis route"""
    try:
        response = await trustworthy_client.post("/fairness/analyze", json=features)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Trustworthy service error: {e}")
        raise HTTPException(status_code=503, detail="Trustworthy service unavailable")

@app.post("/drift/detect")
async def detect_drift(
    features: Dict[str, Any],
    current_user: dict = Depends(verify_jwt_token)
):
    """Drift detection route"""
    try:
        response = await trustworthy_client.post("/drift/detect", json=features)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Trustworthy service error: {e}")
        raise HTTPException(status_code=503, detail="Trustworthy service unavailable")

# Monitoring Routes
@app.get("/monitoring/metrics")
async def get_metrics(current_user: dict = Depends(verify_jwt_token)):
    """Get system metrics"""
    try:
        response = await monitoring_client.get("/metrics")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Monitoring service error: {e}")
        raise HTTPException(status_code=503, detail="Monitoring service unavailable")

@app.get("/monitoring/health")
async def get_health(current_user: dict = Depends(verify_jwt_token)):
    """Get system health"""
    try:
        response = await monitoring_client.get("/health")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Monitoring service error: {e}")
        raise HTTPException(status_code=503, detail="Monitoring service unavailable")

# Shutdown
@app.on_event("shutdown")
async def shutdown():
    """Close HTTP clients"""
    await prediction_client.aclose()
    await model_client.aclose()
    await trustworthy_client.aclose()
    await monitoring_client.aclose()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
