"""
shared_api/app.py
=================
Unified FastAPI REST service for both 5G and 6G Network Slicing pipelines.

Endpoints
---------
GET  /                          Health check
GET  /models                    Status of all loaded models

-- 5G endpoints --
POST /5g/predict/slice          Predict slice type (Random Forest)
POST /5g/predict/sla_risk       Predict SLA risk score (XGBoost)
POST /5g/predict/anomaly        Detect anomaly (Ensemble)
POST /5g/predict/online         Predict via online HAT model
POST /5g/retrain/rf             Retrain Random Forest
POST /5g/retrain/xgb            Retrain XGBoost

-- 6G endpoints --
POST /6g/predict/qos            Predict QoS probability (DSO1 - XGBoost regression)
POST /6g/predict/anomaly        Detect anomaly (DSO5.2 - Isolation Forest)
POST /6g/predict/congestion     Predict congestion class (DSO5.3 - SGD online)
POST /6g/retrain/dso1           Retrain DSO1 regression model
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

# ── Path setup: allow importing from both pipelines ───────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DIR_5G     = os.path.join(BASE_DIR, "..", "5g_pipeline")
DIR_6G     = os.path.join(BASE_DIR, "..", "6g_pipeline")
MODELS_5G  = os.path.join(DIR_5G, "models")
MODELS_6G  = os.path.join(DIR_6G, "models")

# ── Import 5G helpers explicitly using importlib ──────────────────────────────
import importlib.util

def _load_module(name, path):
    """Load a Python module from an explicit file path."""
    spec   = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

mp5g = _load_module("model_pipeline_5g",
                    os.path.join(DIR_5G, "model_pipeline.py"))
mp6g = _load_module("model_pipeline_6g",
                    os.path.join(DIR_6G, "model_pipeline.py"))

eng_rf_5g       = mp5g._engineer_features_rf
online_feat_5g  = mp5g._make_online_features
SLICE_NAMES     = mp5g.SLICE_NAMES
safe_sigmoid_6g = mp6g.safe_sigmoid

# ── App instance ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Network Slicing Unified API",
    description="""
## 5G + 6G Network Slicing — Unified REST API

This single API serves all ML models from both pipelines:

### 5G Models
- **Random Forest** → Slice type classification (eMBB / URLLC / mIoT)
- **XGBoost** → SLA risk scoring
- **Anomaly Ensemble** → Isolation Forest + One-Class SVM + PCA
- **Online HAT** → Stream-based anomaly detection
- **SHAP + LIME** → XAI explainability for Random Forest

### 6G Models
- **DSO1 XGBoost Regressor** → QoS probability prediction
- **DSO5.2 Isolation Forest** → Network anomaly detection
- **DSO5.3 SGDClassifier** → Online congestion classification
- **DSO5.4 XGBoost + SHAP** → XAI explainable QoS prediction
### Input format
All endpoints accept raw network QoS measurements.
Visit each endpoint's schema for the exact fields required.
""",
    version="1.0.0",
)

# ── Model registry ────────────────────────────────────────────────────────────
MODELS = {}


def _load(name: str, path: str):
    """Load a model file if it exists, otherwise mark as unavailable."""
    if os.path.exists(path):
        MODELS[name] = joblib.load(path)
        print(f"[startup] ✅ Loaded {name}")
    else:
        MODELS[name] = None
        print(f"[startup] ⚠️  Not found: {path}")


# Load all 5G models
_load("5g_rf_model",           os.path.join(MODELS_5G, "rf_model.pkl"))
_load("5g_rf_scaler",          os.path.join(MODELS_5G, "rf_scaler.pkl"))
_load("5g_xgb_model",          os.path.join(MODELS_5G, "xgb_model.pkl"))
_load("5g_anomaly_models",     os.path.join(MODELS_5G, "anomaly_models.pkl"))
_load("5g_anomaly_scaler",     os.path.join(MODELS_5G, "anomaly_scaler.pkl"))
_load("5g_anomaly_threshold",  os.path.join(MODELS_5G, "anomaly_threshold.pkl"))
_load("5g_online_model",       os.path.join(MODELS_5G, "online_model.pkl"))
_load("5g_online_scaler",      os.path.join(MODELS_5G, "online_scaler.pkl"))

# Load all 6G models
_load("6g_dso1_model",         os.path.join(MODELS_6G, "model_dso1_regression.joblib"))
_load("6g_dso52_model",        os.path.join(MODELS_6G, "model_dso52_isoforest.joblib"))
_load("6g_dso52_scaler",       os.path.join(MODELS_6G, "scaler_dso52.joblib"))
_load("6g_dso52_features",     os.path.join(MODELS_6G, "features_dso52.joblib"))
_load("6g_dso53_model",        os.path.join(MODELS_6G, "model_dso53_sgd.joblib"))
_load("6g_dso53_scaler",       os.path.join(MODELS_6G, "scaler_dso53.joblib"))
_load("6g_dso53_encoder",      os.path.join(MODELS_6G, "encoder_dso53.joblib"))
_load("6g_dso54_model",        os.path.join(MODELS_6G, "model_dso54_xgboost_xai.joblib"))
_load("6g_dso54_explainer",    os.path.join(MODELS_6G, "..", "xai_artifacts", "shap_explainer_dso54.joblib"))

# ═══════════════════════════════════════════════════════════════════════════════
# INPUT / OUTPUT SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

# ── 5G schemas ────────────────────────────────────────────────────────────────

class Input5G(BaseModel):
    """Raw QoS features for 5G predictions."""
    time: float = Field(..., ge=0, le=23, description="Hour of day (0-23)", example=14)
    plr: float = Field(..., gt=0, le=1, description="Packet Loss Rate (e.g. 1e-3)", example=0.001)
    delay: float = Field(..., gt=0, description="Packet delay in ms", example=100)
    lte5g_cat: float = Field(..., description="LTE/5G Category", example=14)


class SliceOutput(BaseModel):
    slice_type: int
    slice_name: str
    confidence: float
    probabilities: dict


class SLARiskOutput(BaseModel):
    p_sla_met: float
    qos_risk_score: float
    sla_prediction: int
    risk_tier: str


class AnomalyOutput5G(BaseModel):
    anomaly_score: float
    is_anomaly: int
    risk_tier: str


class OnlineOutput5G(BaseModel):
    anomaly_probability: float
    is_anomaly: int


class RetrainRFInput(BaseModel):
    n_estimators: int = Field(200, ge=10, le=1000, description="Number of trees")
    max_depth: Optional[int] = Field(None, ge=1, le=50, description="Max depth (None=unlimited)")


class RetrainXGBInput(BaseModel):
    n_estimators: int = Field(300, ge=10, le=1000)
    learning_rate: float = Field(0.05, gt=0, le=1.0)
    max_depth: int = Field(5, ge=1, le=15)


class RetrainOutput(BaseModel):
    status: str
    message: str
    metrics: dict


# ── 6G schemas ────────────────────────────────────────────────────────────────

class Input6G(BaseModel):
    """SLA gap features for 6G predictions."""
    latency_budget_us: float = Field(..., description="Latency budget in microseconds", example=200.0)
    slice_latency_us: float = Field(..., description="Actual slice latency in microseconds", example=150.0)
    packet_loss_budget: float = Field(..., description="Packet loss budget", example=0.01)
    slice_packet_loss: float = Field(..., description="Actual slice packet loss", example=0.005)
    jitter_budget_us: float = Field(..., description="Jitter budget in microseconds", example=50.0)
    slice_jitter_us: float = Field(..., description="Actual slice jitter in microseconds", example=30.0)
    data_rate_budget_gbps: float = Field(..., description="Data rate budget in Gbps", example=5.0)
    slice_transfer_rate_gbps: float = Field(..., description="Actual available transfer rate in Gbps", example=6.0)


class QoSOutput6G(BaseModel):
    qos_probability: float
    sla_respected: bool
    risk_level: str


class AnomalyOutput6G(BaseModel):
    is_anomaly: int
    anomaly_label: str


class CongestionOutput6G(BaseModel):
    congestion_class: str
    congestion_probability: float

class XAIOutput6G(BaseModel):
    qos_probability: float
    sla_respected: bool
    risk_level: str
    shap_contributions: dict
    top_factor: str
    explanation: str

class RetrainDSO1Input(BaseModel):
    n_estimators: int = Field(300, ge=10, le=1000)
    max_depth: int = Field(5, ge=1, le=15)
    learning_rate: float = Field(0.1, gt=0, le=1.0)


# ═══════════════════════════════════════════════════════════════════════════════
# SHARED ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "running",
        "message": "5G + 6G Network Slicing Unified API ✅",
        "docs": "Visit /docs for interactive API documentation",
        "pipelines": ["5G (slice classification)", "6G (QoS + anomaly + congestion)"],
    }


@app.get("/models", tags=["Health"])
def list_models():
    """Show which models are loaded and available."""
    return {
        name: ("✅ loaded" if model is not None else "⚠️ not available")
        for name, model in MODELS.items()
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 5G ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

def _build_5g_features(inp: Input5G) -> np.ndarray:
    """Build scaled feature array from 5G input."""
    if MODELS["5g_rf_scaler"] is None:
        raise HTTPException(status_code=503, detail="5G RF scaler not loaded.")
    row = pd.DataFrame([{
        "Time": inp.time,
        "Packet Loss Rate": inp.plr,
        "Packet delay": inp.delay,
        "LTE/5g Category": inp.lte5g_cat,
    }])
    features = eng_rf_5g(row)
    return MODELS["5g_rf_scaler"].transform(features)


@app.post("/5g/predict/slice", response_model=SliceOutput, tags=["5G Predictions"])
def predict_5g_slice(inp: Input5G):
    """Predict 5G network slice type (eMBB / URLLC / mIoT) using Random Forest."""
    if MODELS["5g_rf_model"] is None:
        raise HTTPException(status_code=503, detail="5G RF model not loaded.")
    try:
        X = _build_5g_features(inp)
        pred = int(MODELS["5g_rf_model"].predict(X)[0])
        proba = MODELS["5g_rf_model"].predict_proba(X)[0]
        conf = float(proba[pred - 1])
        return SliceOutput(
            slice_type=pred,
            slice_name=SLICE_NAMES[pred],
            confidence=round(conf, 4),
            probabilities={
                SLICE_NAMES[i + 1]: round(float(p), 4)
                for i, p in enumerate(proba)
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/5g/predict/anomaly", response_model=AnomalyOutput5G, tags=["5G Predictions"])
def predict_5g_anomaly(inp: Input5G):
    """Detect anomalies in 5G traffic using Isolation Forest + SVM + PCA ensemble."""
    if MODELS["5g_anomaly_models"] is None:
        raise HTTPException(status_code=503, detail="5G anomaly models not loaded.")
    try:
        X = _build_5g_features(inp)
        models = MODELS["5g_anomaly_models"]
        threshold = MODELS["5g_anomaly_threshold"]

        sIF = float(-models["if"].score_samples(X)[0])
        sOC = float(-models["svm"].decision_function(X)[0])
        sAE = float(np.mean((X - models["ae"].inverse_transform(
            models["ae"].transform(X))) ** 2))

        scores = np.array([sIF, sOC, sAE])
        scores = (scores - scores.min()) / (scores.max() - scores.min() + 1e-9)
        ens = float(scores.mean())

        tier = "Low" if ens < 0.35 else ("Medium" if ens < 0.65 else "High")
        return AnomalyOutput5G(
            anomaly_score=round(ens, 4),
            is_anomaly=int(ens >= threshold),
            risk_tier=tier,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/5g/predict/online", response_model=OnlineOutput5G, tags=["5G Predictions"])
def predict_5g_online(inp: Input5G):
    """Predict using the 5G online Hoeffding Adaptive Tree model."""
    if MODELS["5g_online_model"] is None:
        raise HTTPException(status_code=503, detail="5G online model not loaded.")
    try:
        x = online_feat_5g((inp.time, inp.plr, inp.delay, inp.lte5g_cat))
        xs = MODELS["5g_online_scaler"].transform_one(x)
        p1 = MODELS["5g_online_model"].predict_proba_one(xs).get(1, 0.0)
        return OnlineOutput5G(
            anomaly_probability=round(float(p1), 4),
            is_anomaly=int(p1 >= 0.5),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/5g/retrain/rf", response_model=RetrainOutput, tags=["5G Retrain"])
def retrain_5g_rf(params: RetrainRFInput):
    """Retrain the 5G Random Forest model with new hyperparameters."""
    try:
        os.chdir(DIR_5G)
        prepare_data  = mp5g.prepare_data
        train_model   = mp5g.train_model
        evaluate_model = mp5g.evaluate_model
        data = prepare_data("train_dataset.csv", "test_dataset.csv")
        model = train_model(data["X_tr"], data["y_tr"],
                            n_estimators=params.n_estimators,
                            max_depth=params.max_depth)
        metrics = evaluate_model(model, data["X_val"], data["y_val"])
        joblib.dump(model, os.path.join(MODELS_5G, "rf_model.pkl"))
        joblib.dump(data["scaler"], os.path.join(MODELS_5G, "rf_scaler.pkl"))
        MODELS["5g_rf_model"] = model
        MODELS["5g_rf_scaler"] = data["scaler"]
        os.chdir(os.path.join(BASE_DIR))
        return RetrainOutput(
            status="success",
            message=f"5G RF retrained — n_estimators={params.n_estimators}, max_depth={params.max_depth}",
            metrics={"accuracy": round(metrics["accuracy"], 4), "f1_macro": round(metrics["f1_macro"], 4)},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/5g/predict/sla_risk", response_model=SLARiskOutput, tags=["5G Predictions"])
def predict_5g_sla_risk(inp: Input5G):
    """Predict SLA risk score using the calibrated XGBoost model."""
    if MODELS["5g_xgb_model"] is None:
        raise HTTPException(status_code=503, detail="5G XGBoost model not loaded.")
    try:
        X = _build_5g_features(inp)
        p_met = float(MODELS["5g_xgb_model"].predict_proba(X)[0][1])
        risk  = round(1 - p_met, 4)
        if risk < 0.10:
            tier = "Low"
        elif risk < 0.25:
            tier = "Medium"
        elif risk < 0.50:
            tier = "High"
        else:
            tier = "Critical"
        return SLARiskOutput(
            p_sla_met=round(p_met, 4),
            qos_risk_score=risk,
            sla_prediction=int(p_met >= 0.5),
            risk_tier=tier,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/5g/retrain/xgb", response_model=RetrainOutput, tags=["5G Retrain"])
def retrain_5g_xgb(params: RetrainXGBInput):
    """Retrain the 5G XGBoost SLA risk model with new hyperparameters."""
    try:
        os.chdir(DIR_5G)
        data       = mp5g.prepare_data("train_dataset.csv", "test_dataset.csv")
        xgb_res    = mp5g.train_xgboost(data["train_raw"], data["test_raw"])
        joblib.dump(xgb_res["model"], os.path.join(MODELS_5G, "xgb_model.pkl"))
        MODELS["5g_xgb_model"] = xgb_res["model"]
        os.chdir(BASE_DIR)
        return RetrainOutput(
            status="success",
            message=f"5G XGBoost retrained",
            metrics={
                "auc":     round(xgb_res["results"]["auc"],    4),
                "brier":   round(xgb_res["results"]["brier"],  4),
                "logloss": round(xgb_res["results"]["logloss"], 4),
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/5g/predict/xai", tags=["5G Predictions"])
def predict_5g_xai(inp: Input5G):
    """
    Predict 5G slice type AND explain the decision using SHAP.
    Returns slice prediction + SHAP contribution per feature.
    """
    if MODELS["5g_rf_model"] is None:
        raise HTTPException(status_code=503, detail="5G RF model not loaded.")
    try:
        import shap
        X = _build_5g_features(inp)
        pred  = int(MODELS["5g_rf_model"].predict(X)[0])
        proba = MODELS["5g_rf_model"].predict_proba(X)[0]
        conf  = float(proba[pred - 1])

        # SHAP explanation
        explainer   = shap.TreeExplainer(MODELS["5g_rf_model"])
        shap_values = explainer.shap_values(X)

        # Mean SHAP across all classes for this sample
        mean_shap = {
            FEAT_NAMES[i]: round(float(
                sum(abs(shap_values[c][0][i])
                for c in range(len(shap_values))) / len(shap_values)
            ), 6)
            for i in range(len(FEAT_NAMES))
        }
        top_feature = max(mean_shap, key=mean_shap.get)

        return {
            "slice_type":        pred,
            "slice_name":        SLICE_NAMES[pred],
            "confidence":        round(conf, 4),
            "shap_contributions": mean_shap,
            "top_feature":       top_feature,
            "explanation": (
                f"Predicted slice: {SLICE_NAMES[pred]} "
                f"(confidence: {conf:.2%}). "
                f"Most influential feature: '{top_feature}' "
                f"(SHAP={mean_shap[top_feature]:.4f})."
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════════════════════════
# 6G ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

def _build_6g_gaps(inp: Input6G) -> dict:
    """Compute the 4 SLA gap features from raw 6G input."""
    return {
        "Latency_Gap":     inp.latency_budget_us - inp.slice_latency_us,
        "Packet_Loss_Gap": inp.packet_loss_budget - inp.slice_packet_loss,
        "Jitter_Gap":      inp.jitter_budget_us - inp.slice_jitter_us,
        "Rate_Gap":        inp.slice_transfer_rate_gbps - inp.data_rate_budget_gbps,
    }


@app.post("/6g/predict/qos", response_model=QoSOutput6G, tags=["6G Predictions"])
def predict_6g_qos(inp: Input6G):
    """
    Predict QoS probability for a 6G network slice (DSO1 - XGBoost Regressor).
    Returns a probability score between 0 and 1 indicating SLA compliance likelihood.
    """
    if MODELS["6g_dso1_model"] is None:
        raise HTTPException(status_code=503, detail="6G DSO1 model not loaded.")
    try:
        gaps = _build_6g_gaps(inp)
        X = pd.DataFrame([gaps])
        qos_prob = float(MODELS["6g_dso1_model"].predict(X)[0])
        qos_prob = float(np.clip(qos_prob, 0, 1))

        if qos_prob >= 0.7:
            risk = "Low"
        elif qos_prob >= 0.5:
            risk = "Medium"
        elif qos_prob >= 0.3:
            risk = "High"
        else:
            risk = "Critical"

        return QoSOutput6G(
            qos_probability=round(qos_prob, 4),
            sla_respected=qos_prob >= 0.5,
            risk_level=risk,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/6g/predict/anomaly", response_model=AnomalyOutput6G, tags=["6G Predictions"])
def predict_6g_anomaly(inp: Input6G):
    """
    Detect anomalies in 6G network traffic (DSO5.2 - Isolation Forest).
    Returns binary anomaly flag.
    """
    if MODELS["6g_dso52_model"] is None:
        raise HTTPException(status_code=503, detail="6G DSO5.2 model not loaded.")
    try:
        gaps = _build_6g_gaps(inp)
        features = MODELS["6g_dso52_features"]

        row = {}
        for f in features:
            row[f] = gaps.get(f, 0.0)

        X_raw = pd.DataFrame([row])[features]
        X_scaled = MODELS["6g_dso52_scaler"].transform(X_raw)
        pred = int(MODELS["6g_dso52_model"].predict(X_scaled)[0])
        label = "Anomaly" if pred == -1 else "Normal"

        return AnomalyOutput6G(
            is_anomaly=int(pred == -1),
            anomaly_label=label,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/6g/predict/congestion", response_model=CongestionOutput6G, tags=["6G Predictions"])
def predict_6g_congestion(inp: Input6G):
    """
    Predict congestion class for a 6G slice (DSO5.3 - SGDClassifier online model).
    Returns congestion class label and probability.
    """
    if MODELS["6g_dso53_model"] is None:
        raise HTTPException(status_code=503, detail="6G DSO5.3 model not loaded.")
    try:
        gaps = _build_6g_gaps(inp)
        row = pd.DataFrame([gaps])

        X_scaled = MODELS["6g_dso53_scaler"].transform(row)
        pred_enc = int(MODELS["6g_dso53_model"].predict(X_scaled)[0])
        proba = MODELS["6g_dso53_model"].predict_proba(X_scaled)[0]
        conf = float(proba[pred_enc])

        le = MODELS["6g_dso53_encoder"]
        pred_label = str(le.inverse_transform([pred_enc])[0])

        return CongestionOutput6G(
            congestion_class=pred_label,
            congestion_probability=round(conf, 4),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/6g/predict/xai", response_model=XAIOutput6G, tags=["6G Predictions"])
def predict_6g_xai(inp: Input6G):
    """
    Predict QoS probability for a 6G slice using the XAI-enabled XGBoost model
    (DSO 5.4). Returns the prediction AND a SHAP-based explanation showing
    exactly which SLA gap contributed most to the decision.

    This is the most interpretable endpoint — designed for network operators
    who need to understand WHY a slice is at risk.
    """
    if MODELS["6g_dso54_model"] is None:
        raise HTTPException(
            status_code=503,
            detail="6G DSO5.4 XAI model not loaded. Run 'python3 main.py --step dso54' first."
        )
    try:
        import shap

        gaps = _build_6g_gaps(inp)
        feature_names = ["Latency_Gap", "Packet_Loss_Gap", "Jitter_Gap", "Rate_Gap"]
        X = pd.DataFrame([gaps])[feature_names]

        # Prediction
        qos_prob = float(np.clip(MODELS["6g_dso54_model"].predict(X)[0], 0, 1))

        # SHAP explanation
        if MODELS["6g_dso54_explainer"] is not None:
            explainer = MODELS["6g_dso54_explainer"]
        else:
            explainer = shap.TreeExplainer(MODELS["6g_dso54_model"])

        shap_vals = explainer.shap_values(X)

        # Build contribution dict
        contributions = {
            feat: round(float(shap_vals[0][i]), 6)
            for i, feat in enumerate(feature_names)
        }

        # Find top contributing factor
        top_factor = max(contributions, key=lambda k: abs(contributions[k]))
        top_val    = contributions[top_factor]

        # Risk level
        if qos_prob >= 0.7:
            risk = "Low"
        elif qos_prob >= 0.5:
            risk = "Medium"
        elif qos_prob >= 0.3:
            risk = "High"
        else:
            risk = "Critical"

        # Human-readable explanation
        direction = "improves" if top_val > 0 else "degrades"
        explanation = (
            f"QoS probability is {qos_prob:.2%}. "
            f"The most influential factor is '{top_factor}' "
            f"(SHAP={top_val:+.4f}), which {direction} SLA compliance. "
            f"Risk level: {risk}."
        )

        return XAIOutput6G(
            qos_probability=round(qos_prob, 4),
            sla_respected=qos_prob >= 0.5,
            risk_level=risk,
            shap_contributions=contributions,
            top_factor=top_factor,
            explanation=explanation,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/6g/retrain/dso1", response_model=RetrainOutput, tags=["6G Retrain"])
def retrain_6g_dso1(params: RetrainDSO1Input):
    """Retrain the 6G DSO1 QoS regression model (XGBoost) with new hyperparameters."""
    try:
        os.chdir(DIR_6G)
        mp_main = _load_module("main_6g", os.path.join(DIR_6G, "main.py"))
        mp_main.run_dso1()
        new_model = joblib.load(os.path.join(MODELS_6G, "model_dso1_regression.joblib"))
        MODELS["6g_dso1_model"] = new_model
        os.chdir(BASE_DIR)
        return RetrainOutput(
            status="success",
            message=f"6G DSO1 retrained with n_estimators={params.n_estimators}",
            metrics={"note": "Check 6G pipeline logs for detailed metrics"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
