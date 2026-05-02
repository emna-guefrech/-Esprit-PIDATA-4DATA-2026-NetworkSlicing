"""
app.py
======
MS-5 Model Management Service
Specific to Data Scientists.

Routes:
  GET  /                         → main dashboard
  GET  /versions                 → versions history page
  GET  /model/metrics            → R², RMSE, accuracy per model
  POST /model/retrain            → trigger retraining
  GET  /model/versions           → version history (JSON)
  GET  /model/shap/<slice_id>    → top 5 SHAP features
  GET  /model/drift              → model drift score
  GET  /model/compare            → before/after tuning comparison
"""

import os
import json
import time
import numpy as np
import pandas as pd
import joblib
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
from models import db, ModelVersion, ShapLog, DriftLog

# ── App setup ──────────────────────────────────────────────────────
app = Flask(__name__)

DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "root")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "network_slicing_")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "bb3cef985bd3e65b14bf0372223983dd6c4f31503f787f02"

db.init_app(app)

# ── Load ML models ─────────────────────────────────────────────────
ML_DIR = os.path.join(os.path.dirname(__file__), "ml")

print("[ML] Loading models...")
try:
    model_6g_qos     = joblib.load(os.path.join(ML_DIR, "model_6g_qos.joblib"))
    model_6g_xai     = joblib.load(os.path.join(ML_DIR, "model_6g_xai.joblib"))
    shap_explainer   = joblib.load(os.path.join(ML_DIR, "shap_explainer_6g.joblib"))
    features_6g      = joblib.load(os.path.join(ML_DIR, "features_6g.joblib"))
    model_5g_rf      = joblib.load(os.path.join(ML_DIR, "model_5g_rf.pkl"))
    scaler_5g        = joblib.load(os.path.join(ML_DIR, "scaler_5g.pkl"))
    print("[ML] ✅ All models loaded")
except Exception as e:
    print(f"[ML] ❌ {e}")
    model_6g_qos = model_6g_xai = shap_explainer = None
    features_6g  = model_5g_rf = scaler_5g = None

FEATURE_NAMES_6G = [
    "Latency_Gap", "Packet_Loss_Gap", "Jitter_Gap", "Rate_Gap"
]
FEATURE_NAMES_5G = [
    "time_sin", "time_cos", "is_peak", "log_plr",
    "log_delay", "plr_x_delay", "lte5g_cat",
    "high_delay", "high_plr"
]


# ── Helpers ────────────────────────────────────────────────────────
def build_6g_features(data: dict) -> pd.DataFrame:
    return pd.DataFrame([{
        "Latency_Gap":     data.get("latency_budget", 200) - data.get("slice_latency", 150),
        "Packet_Loss_Gap": data.get("packet_loss_budget", 0.01) - data.get("slice_packet_loss", 0.005),
        "Jitter_Gap":      data.get("jitter_budget", 50) - data.get("slice_jitter", 30),
        "Rate_Gap":        data.get("slice_transfer_rate", 6.0) - data.get("data_rate_budget", 5.0),
    }])


def compute_drift_score(model_name: str) -> dict:
    """
    Compute a simple drift score based on recent prediction
    variance compared to training distribution.
    Uses statistical simulation for demo purposes.
    """
    np.random.seed(int(time.time()) % 1000)

    # Simulate reference distribution (training)
    ref_mean = 0.75 if "6G" in model_name else 0.85
    ref_std  = 0.12

    # Simulate current distribution (recent predictions)
    curr_mean = ref_mean - np.random.uniform(0, 0.20)
    curr_std  = ref_std + np.random.uniform(0, 0.08)

    # KL divergence approximation
    drift_score = abs(curr_mean - ref_mean) / ref_std + \
                  abs(curr_std - ref_std) / ref_std
    drift_score = round(min(drift_score, 1.0), 4)

    if drift_score < 0.2:
        status = "Stable"
    elif drift_score < 0.5:
        status = "Warning"
    else:
        status = "Drift Detected"

    return {
        "drift_score":    drift_score,
        "drift_status":   status,
        "ref_mean":       round(ref_mean, 4),
        "curr_mean":      round(curr_mean, 4),
        "ref_std":        round(ref_std, 4),
        "curr_std":       round(curr_std, 4),
        "recommendation": (
            "Model is stable. No action needed." if drift_score < 0.2
            else "Monitor closely. Consider retraining soon." if drift_score < 0.5
            else "Retraining recommended immediately!"
        )
    }


# ══════════════════════════════════════════════════════════════════
# FRONTEND ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    """Main Data Scientist dashboard."""
    versions     = ModelVersion.query.order_by(
        ModelVersion.trained_at.desc()).limit(10).all()
    shap_logs    = ShapLog.query.order_by(
        ShapLog.created_at.desc()).limit(5).all()
    drift_logs   = DriftLog.query.order_by(
        DriftLog.checked_at.desc()).limit(6).all()
    total_versions = ModelVersion.query.count()
    total_retrains = ModelVersion.query.filter(
        ModelVersion.version != "1.0").count()

    return render_template(
        "index.html",
        versions=versions,
        shap_logs=shap_logs,
        drift_logs=drift_logs,
        total_versions=total_versions,
        total_retrains=total_retrains,
    )


@app.route("/versions")
def versions_page():
    """Full model versions history page."""
    model_filter = request.args.get("model", "all")
    query        = ModelVersion.query
    if model_filter != "all":
        query    = query.filter_by(model_name=model_filter)
    versions     = query.order_by(ModelVersion.trained_at.desc()).all()
    models_list  = db.session.query(
        ModelVersion.model_name).distinct().all()
    models_list  = [m[0] for m in models_list]
    return render_template(
        "versions.html",
        versions=versions,
        models_list=models_list,
        model_filter=model_filter,
    )


# ══════════════════════════════════════════════════════════════════
# API ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route("/model/metrics", methods=["GET"])
def get_metrics():
    """Return R², RMSE, accuracy per model."""
    versions = ModelVersion.query.order_by(
        ModelVersion.trained_at.desc()).all()

    # Group by model name, take latest version
    latest = {}
    for v in versions:
        if v.model_name not in latest:
            latest[v.model_name] = v.to_dict()

    return jsonify({
        "models": list(latest.values()),
        "total_models": len(latest),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })


@app.route("/model/retrain", methods=["POST"])
def retrain_model():
    """
    Trigger model retraining.
    Input: {model_name, hyperparams (optional)}
    Simulates retraining with improved metrics.
    """
    data       = request.get_json()
    model_name = data.get("model_name", "XGBoost_QoS_6G")
    hyperparams = data.get("hyperparams", {})

    print(f"[Retrain] Starting retraining for {model_name}...")
    start_time = time.time()

    # Get last version
    last = ModelVersion.query.filter_by(
        model_name=model_name
    ).order_by(ModelVersion.trained_at.desc()).first()

    # Simulate improved metrics after retraining
    np.random.seed(int(time.time()) % 1000)
    improvement = np.random.uniform(0.001, 0.015)

    if last:
        new_r2       = min((last.r2_score or 0.95) + improvement, 0.999)
        new_rmse     = max((last.rmse or 0.02) - improvement * 0.5, 0.001)
        new_accuracy = min((last.accuracy or 0.90) + improvement * 0.5, 0.999)
        new_version  = f"{float(last.version) + 0.1:.1f}"
    else:
        new_r2       = 0.95 + improvement
        new_rmse     = 0.02
        new_accuracy = 0.90
        new_version  = "1.0"

    # Save new version
    new_ver = ModelVersion(
        model_name = model_name,
        version    = new_version,
        r2_score   = round(new_r2,       4),
        rmse       = round(new_rmse,      4),
        accuracy   = round(new_accuracy,  4),
    )
    db.session.add(new_ver)
    db.session.commit()

    duration = round(time.time() - start_time, 2)
    print(f"[Retrain] ✅ Done in {duration}s — v{new_version}")

    return jsonify({
        "status":      "success",
        "model_name":  model_name,
        "new_version": new_version,
        "duration_s":  duration,
        "metrics": {
            "r2_score":   round(new_r2,      4),
            "rmse":       round(new_rmse,     4),
            "accuracy":   round(new_accuracy, 4),
        },
        "improvement": round(improvement, 4),
        "hyperparams": hyperparams,
    })


@app.route("/model/versions", methods=["GET"])
def get_versions():
    """Return model version history as JSON."""
    model_name = request.args.get("model", None)
    query      = ModelVersion.query
    if model_name:
        query  = query.filter_by(model_name=model_name)
    versions   = query.order_by(ModelVersion.trained_at.desc()).all()
    return jsonify({
        "total":    len(versions),
        "versions": [v.to_dict() for v in versions],
    })


@app.route("/model/shap/<slice_id>", methods=["GET"])
def get_shap(slice_id: str):
    """
    Compute and return top 5 SHAP features for a given slice.
    Uses the 6G XAI XGBoost model.
    """
    if model_6g_xai is None or shap_explainer is None:
        return jsonify({"error": "XAI model not loaded"}), 503

    try:
        # Build feature vector from query params or defaults
        data = {
            "latency_budget":      float(request.args.get("latency_budget",      200)),
            "slice_latency":       float(request.args.get("slice_latency",       150)),
            "packet_loss_budget":  float(request.args.get("packet_loss_budget",  0.01)),
            "slice_packet_loss":   float(request.args.get("slice_packet_loss",   0.005)),
            "jitter_budget":       float(request.args.get("jitter_budget",       50)),
            "slice_jitter":        float(request.args.get("slice_jitter",        30)),
            "data_rate_budget":    float(request.args.get("data_rate_budget",    5.0)),
            "slice_transfer_rate": float(request.args.get("slice_transfer_rate", 6.0)),
        }

        X           = build_6g_features(data)
        qos_pred    = float(np.clip(model_6g_xai.predict(X)[0], 0, 1))
        shap_values = shap_explainer.shap_values(X)

        # Build SHAP contributions
        contributions = {
            FEATURE_NAMES_6G[i]: round(float(shap_values[0][i]), 6)
            for i in range(len(FEATURE_NAMES_6G))
        }

        # Top 5 by absolute value
        top5 = sorted(
            contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:5]

        top_factor = top5[0][0] if top5 else "N/A"
        direction  = "improves" if top5[0][1] > 0 else "degrades"

        # Save to DB
        shap_log = ShapLog(
            slice_id      = slice_id,
            model_version = "latest",
            features_json = json.dumps({
                "contributions": contributions,
                "top5":          top5,
                "qos_pred":      qos_pred,
            }),
        )
        db.session.add(shap_log)
        db.session.commit()

        return jsonify({
            "slice_id":       slice_id,
            "qos_prediction": round(qos_pred, 4),
            "top5_features":  [
                {
                    "feature":     f,
                    "shap_value":  v,
                    "direction":   "positive" if v > 0 else "negative",
                    "importance":  round(abs(v), 6),
                }
                for f, v in top5
            ],
            "all_contributions": contributions,
            "top_factor":     top_factor,
            "explanation": (
                f"QoS={qos_pred:.2%}. "
                f"'{top_factor}' is the most influential feature "
                f"(SHAP={top5[0][1]:+.4f}), which {direction} QoS."
            ),
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/model/drift", methods=["GET"])
def get_drift():
    """Return drift scores for all models."""
    models_to_check = [
        "XGBoost_QoS_6G",
        "XGBoost_QoS_5G",
        "RandomForest_5G",
        "SGD_Congestion_6G",
        "IsolationForest_5G",
    ]

    results = []
    for model_name in models_to_check:
        drift   = compute_drift_score(model_name)
        # Save to DB
        log = DriftLog(
            model_name   = model_name,
            drift_score  = drift["drift_score"],
            drift_status = drift["drift_status"],
            details_json = json.dumps(drift),
        )
        db.session.add(log)
        results.append({
            "model_name": model_name,
            **drift,
        })

    db.session.commit()

    return jsonify({
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "models":     results,
        "summary": {
            "stable":         sum(1 for r in results if r["drift_status"] == "Stable"),
            "warning":        sum(1 for r in results if r["drift_status"] == "Warning"),
            "drift_detected": sum(1 for r in results if r["drift_status"] == "Drift Detected"),
        }
    })


@app.route("/model/compare", methods=["GET"])
def compare_versions():
    """
    Compare before/after tuning for a specific model.
    Returns last 2 versions side by side.
    """
    model_name = request.args.get("model", "XGBoost_QoS_6G")
    versions   = ModelVersion.query.filter_by(
        model_name=model_name
    ).order_by(ModelVersion.trained_at.desc()).limit(2).all()

    if len(versions) < 2:
        return jsonify({
            "message":  "Need at least 2 versions to compare",
            "versions": [v.to_dict() for v in versions],
        })

    before = versions[1].to_dict()
    after  = versions[0].to_dict()

    return jsonify({
        "model_name": model_name,
        "before":     before,
        "after":      after,
        "improvement": {
            "r2_score": round(
                (after.get("r2_score") or 0) -
                (before.get("r2_score") or 0), 4),
            "rmse": round(
                (before.get("rmse") or 0) -
                (after.get("rmse") or 0), 4),
            "accuracy": round(
                (after.get("accuracy") or 0) -
                (before.get("accuracy") or 0), 4),
        }
    })


@app.route("/health")
def health():
    return jsonify({
        "status":  "running",
        "service": "MS-5 Model Management Service",
        "models": {
            "6g_qos":       model_6g_qos is not None,
            "6g_xai":       model_6g_xai is not None,
            "shap":         shap_explainer is not None,
            "5g_rf":        model_5g_rf is not None,
        }
    })


# ── Init DB ────────────────────────────────────────────────────────
with app.app_context():
    try:
        db.create_all()
        # Seed initial model versions if empty
        if ModelVersion.query.count() == 0:
            seeds = [
                ModelVersion(model_name="XGBoost_QoS_6G",    version="1.0",
                             r2_score=0.9950, rmse=0.0092,   accuracy=None),
                ModelVersion(model_name="XGBoost_QoS_5G",    version="1.0",
                             r2_score=None,   rmse=None,      accuracy=0.9051),
                ModelVersion(model_name="RandomForest_5G",   version="1.0",
                             r2_score=None,   rmse=None,      accuracy=0.9051),
                ModelVersion(model_name="SGD_Congestion_6G", version="1.0",
                             r2_score=None,   rmse=None,      accuracy=0.8950),
                ModelVersion(model_name="IsolationForest_5G",version="1.0",
                             r2_score=None,   rmse=None,      accuracy=None),
            ]
            for s in seeds:
                db.session.add(s)
            db.session.commit()
            print("[DB] ✅ Model versions seeded")
        print("[DB] ✅ Tables ready")
    except Exception as e:
        print(f"[DB] ⚠️ {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
