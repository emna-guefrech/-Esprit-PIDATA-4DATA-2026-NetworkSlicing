"""
app.py
======
MS-2 Anomaly Detection Service
Flask backend serving:
  POST /anomaly/detect    → is_anomaly + score (IF + Autoencoder consensus)
  GET  /anomaly/history   → logs of detected anomalies
  GET  /anomaly/stats     → anomaly rates by period
  GET  /                  → main dashboard
  GET  /history           → history page
"""

import os
import json
import numpy as np
import pandas as pd
import joblib
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
from models import db, Anomaly
from sqlalchemy import func

# ── App setup ─────────────────────────────────────────────────────
app = Flask(__name__)

DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "root")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "network_slicing")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "ms2_anomaly_secret"

db.init_app(app)

# ── Alert service ─────────────────────────────────────────────────
try:
    from alert_service import send_alert
    ALERTS_ENABLED = True
    print("[Alert] ✅ Alert service loaded")
except Exception as e:
    ALERTS_ENABLED = False
    print(f"[Alert] ⚠️ {e}")

# ── Load ML models ────────────────────────────────────────────────
ML_DIR = os.path.join(os.path.dirname(__file__), "ml")

print("[ML] Loading anomaly models...")
try:
    # 5G ensemble (IF + SVM + PCA autoencoder)
    anomaly_models_5g  = joblib.load(os.path.join(ML_DIR, "anomaly_models.pkl"))
    anomaly_scaler_5g  = joblib.load(os.path.join(ML_DIR, "anomaly_scaler.pkl"))
    anomaly_thresh_5g  = joblib.load(os.path.join(ML_DIR, "anomaly_threshold.pkl"))

    # 6G Isolation Forest
    isoforest_6g       = joblib.load(os.path.join(ML_DIR, "model_6g_isoforest.joblib"))
    scaler_6g          = joblib.load(os.path.join(ML_DIR, "scaler_6g.joblib"))
    features_6g        = joblib.load(os.path.join(ML_DIR, "features_6g.joblib"))

    print("[ML] ✅ All anomaly models loaded")
except Exception as e:
    print(f"[ML] ❌ {e}")
    anomaly_models_5g = anomaly_scaler_5g = anomaly_thresh_5g = None
    isoforest_6g = scaler_6g = features_6g = None


# ── Feature builders ──────────────────────────────────────────────

def build_5g_anomaly_features(data: dict) -> np.ndarray:
    """Build 23 features for 5G anomaly ensemble."""
    time  = data.get("time", 14)
    plr   = data.get("plr", 0.001)
    delay = data.get("delay", 100)
    cat   = data.get("lte5g_cat", 14)

    time_sin    = np.sin(2 * np.pi * time / 24)
    time_cos    = np.cos(2 * np.pi * time / 24)
    is_peak     = 1 if (8 <= time <= 10 or 18 <= time <= 21) else 0
    log_plr     = np.log10(max(plr, 1e-9))
    log_delay   = np.log10(delay)
    strictness  = (1 / (delay + 1e-9)) * 0.4 + (plr / 0.01) * 0.6
    gbr         = data.get("gbr", 1)
    iot         = data.get("iot", 0)
    gbr_strict  = gbr * strictness
    peak_strict = is_peak * strictness
    n_use       = 1
    is_mc       = 0
    is_cons     = 1
    is_ind      = 0

    row = pd.DataFrame([{
        "LTE/5g Category": cat,
        "time_sin":        time_sin,
        "time_cos":        time_cos,
        "is_peak":         is_peak,
        "log_plr":         log_plr,
        "log_delay":       log_delay,
        "qos_strictness":  strictness,
        "IoT":             iot,
        "GBR":             gbr,
        "gbr_x_strict":    gbr_strict,
        "peak_x_strict":   peak_strict,
        "n_use_cases":     n_use,
        "is_mc":           is_mc,
        "is_consumer":     is_cons,
        "is_industrial":   is_ind,
        "AR/VR/Gaming":    0,
        "Healthcare":      0,
        "Industry 4.0":    0,
        "IoT Devices":     iot,
        "Public Safety":   0,
        "Smart City & Home":    0,
        "Smart Transportation": 0,
        "Smartphone":      1,
    }])
    return anomaly_scaler_5g.transform(row)


def build_6g_anomaly_features(data: dict) -> np.ndarray:
    """Build features for 6G Isolation Forest."""
    lat_budget  = data.get("latency_budget", 200)
    lat_slice   = data.get("slice_latency", 150)
    plr_budget  = data.get("packet_loss_budget", 0.01)
    plr_slice   = data.get("slice_packet_loss", 0.005)
    jit_budget  = data.get("jitter_budget", 50)
    jit_slice   = data.get("slice_jitter", 30)
    rate_budget = data.get("data_rate_budget", 5.0)
    rate_slice  = data.get("slice_transfer_rate", 6.0)

    gaps = {
        "Latency_Gap":     lat_budget  - lat_slice,
        "Packet_Loss_Gap": plr_budget  - plr_slice,
        "Jitter_Gap":      jit_budget  - jit_slice,
        "Rate_Gap":        rate_slice  - rate_budget,
    }

    row = pd.DataFrame([gaps])
    valid_features = [f for f in features_6g if f in row.columns]
    for f in features_6g:
        if f not in row.columns:
            row[f] = 0
    return scaler_6g.transform(row[features_6g])


# ══════════════════════════════════════════════════════════════════
# FRONTEND ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    """Main anomaly detection dashboard."""
    recent      = Anomaly.query.order_by(
        Anomaly.created_at.desc()).limit(5).all()
    total       = Anomaly.query.count()
    total_anom  = Anomaly.query.filter_by(is_anomaly=True).count()
    rate        = round(total_anom / max(total, 1) * 100, 1)
    return render_template(
        "index.html",
        recent=recent,
        total=total,
        total_anom=total_anom,
        rate=rate,
    )


@app.route("/history")
def history():
    """Full anomaly history page."""
    method  = request.args.get("method", "all")
    only_an = request.args.get("only_anomalies", "false") == "true"

    query = Anomaly.query
    if method != "all":
        query = query.filter_by(method=method)
    if only_an:
        query = query.filter_by(is_anomaly=True)

    anomalies = query.order_by(Anomaly.created_at.desc()).limit(100).all()
    return render_template(
        "history.html",
        anomalies=anomalies,
        method=method,
        only_anomalies=only_an,
    )


# ══════════════════════════════════════════════════════════════════
# API ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route("/anomaly/detect", methods=["POST"])
def detect_anomaly():
    """
    Detect anomaly using consensus of:
      - 5G: Isolation Forest + One-Class SVM + PCA Autoencoder
      - 6G: Isolation Forest
    Returns: is_anomaly, score, confidence, method
    """
    data     = request.get_json()
    slice_id = data.get("slice_id", f"slice_{datetime.now().strftime('%H%M%S')}")
    pipeline = data.get("pipeline", "5g").lower()

    results = {}

    # ── 5G Ensemble ───────────────────────────────────────────────
    if pipeline == "5g" and anomaly_models_5g is not None:
        try:
            X_s     = build_5g_anomaly_features(data)
            models  = anomaly_models_5g

            sIF = float(-models["if"].score_samples(X_s)[0])
            sOC = float(-models["svm"].decision_function(X_s)[0])
            sAE = float(np.mean(
                (X_s - models["ae"].inverse_transform(
                    models["ae"].transform(X_s))) ** 2
            ))

            scores  = np.array([sIF, sOC, sAE])
            scores  = (scores - scores.min()) / (scores.max() - scores.min() + 1e-9)
            ens     = float(scores.mean())
            is_anom = bool(ens >= anomaly_thresh_5g)

            results = {
                "if_score":  round(sIF, 4),
                "svm_score": round(sOC, 4),
                "ae_score":  round(sAE, 4),
                "ensemble":  round(ens, 4),
                "method":    "IF+SVM+AE_ensemble",
            }

        except Exception as e:
            return jsonify({"error": f"5G detection failed: {e}"}), 500

    # ── 6G Isolation Forest ───────────────────────────────────────
    elif pipeline == "6g" and isoforest_6g is not None:
        try:
            X_s     = build_6g_anomaly_features(data)
            pred    = int(isoforest_6g.predict(X_s)[0])
            score   = float(-isoforest_6g.score_samples(X_s)[0])
            ens     = float(np.clip(score, 0, 1))
            is_anom = pred == -1

            results = {
                "if_score": round(score, 4),
                "ensemble": round(ens, 4),
                "method":   "IsolationForest_6G",
            }

        except Exception as e:
            return jsonify({"error": f"6G detection failed: {e}"}), 500

    else:
        return jsonify({"error": f"Pipeline '{pipeline}' not available"}), 503

    # ── Confidence & risk tier ────────────────────────────────────
    ens_score  = results["ensemble"]
    confidence = round(abs(ens_score - 0.5) * 2, 4)
    if ens_score < 0.35:
        risk_tier = "Low"
    elif ens_score < 0.65:
        risk_tier = "Medium"
    else:
        risk_tier = "High"

    # ── Save to DB ────────────────────────────────────────────────
    record = Anomaly(
        slice_id   = slice_id,
        score      = round(ens_score, 4),
        is_anomaly = is_anom,
        method     = results["method"],
    )
    db.session.add(record)
    db.session.commit()
    # Notify MS3
    MS3_URL = os.environ.get("MS3_URL", "http://ms3:5003")
    try:
        import requests as req
        req.post(f"{MS3_URL}/dashboard/notify", json={
            "slice_id":     slice_id,
            "is_anomaly":   is_anom,
            "anomaly_score": round(ens_score, 4),
            "source":       "ms2"
        }, timeout=2)
    except Exception:
        pass

    # ── Alert if anomaly ──────────────────────────────────────────
    if is_anom and ALERTS_ENABLED:
        send_alert(
            subject=f"🚨 Anomaly Detected — Slice {slice_id} ({pipeline.upper()})",
            body=(
                f"Pipeline      : {pipeline.upper()}\n"
                f"Slice ID      : {slice_id}\n"
                f"Anomaly Score : {ens_score:.4f}\n"
                f"Risk Tier     : {risk_tier}\n"
                f"Method        : {results['method']}\n\n"
                f"🔍 Investigate network slice immediately."
            ),
            level="CRITICAL" if risk_tier == "High" else "WARNING"
        )

    return jsonify({
        "slice_id":   slice_id,
        "is_anomaly": is_anom,
        "score":      round(ens_score, 4),
        "confidence": confidence,
        "risk_tier":  risk_tier,
        "pipeline":   pipeline.upper(),
        "details":    results,
    })


@app.route("/anomaly/history", methods=["GET"])
def anomaly_history():
    """Return anomaly detection history as JSON."""
    limit    = request.args.get("limit", 50, type=int)
    only_an  = request.args.get("only_anomalies", "false") == "true"
    query    = Anomaly.query
    if only_an:
        query = query.filter_by(is_anomaly=True)
    records  = query.order_by(Anomaly.created_at.desc()).limit(limit).all()
    return jsonify({
        "total":     Anomaly.query.count(),
        "anomalies": [r.to_dict() for r in records],
    })


@app.route("/anomaly/stats", methods=["GET"])
def anomaly_stats():
    """Return anomaly statistics by period."""
    total      = Anomaly.query.count()
    total_anom = Anomaly.query.filter_by(is_anomaly=True).count()
    rate       = round(total_anom / max(total, 1) * 100, 1)

    # Last 24 hours
    since_24h  = datetime.now() - timedelta(hours=24)
    last_24h   = Anomaly.query.filter(
        Anomaly.created_at >= since_24h).count()
    anom_24h   = Anomaly.query.filter(
        Anomaly.created_at >= since_24h,
        Anomaly.is_anomaly == True).count()

    # By method
    by_method  = db.session.query(
        Anomaly.method,
        func.count(Anomaly.id),
        func.sum(Anomaly.is_anomaly.cast(db.Integer))
    ).group_by(Anomaly.method).all()

    # Average score
    avg_score  = db.session.query(
        func.avg(Anomaly.score)).scalar()

    return jsonify({
        "total_detections":    total,
        "total_anomalies":     total_anom,
        "anomaly_rate_pct":    rate,
        "last_24h": {
            "detections": last_24h,
            "anomalies":  anom_24h,
            "rate_pct":   round(anom_24h / max(last_24h, 1) * 100, 1),
        },
        "by_method": [
            {
                "method":        m,
                "detections":    d,
                "anomalies":     int(a or 0),
                "anomaly_rate":  round(int(a or 0) / max(d, 1) * 100, 1),
            }
            for m, d, a in by_method
        ],
        "average_score": round(float(avg_score), 4) if avg_score else 0,
    })


@app.route("/health")
def health():
    return jsonify({
        "status":  "running",
        "service": "MS-2 Anomaly Detection Service",
        "models": {
            "5g_ensemble":    anomaly_models_5g is not None,
            "6g_isoforest":   isoforest_6g is not None,
        }
    })


# ── Init DB ───────────────────────────────────────────────────────
with app.app_context():
    try:
        db.create_all()
        print("[DB] ✅ Tables ready")
    except Exception as e:
        print(f"[DB] ⚠️ {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
