"""
app.py
======
MS-1 Prediction & QoS Service
Flask backend serving:
  POST /predict/congestion  → Normal / Light / Critical
  POST /predict/qos         → Score [0,1]
  GET  /predict/history     → prediction history
  GET  /                    → main dashboard
  GET  /history             → history page
"""

import os
import json
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for
from models import db, Prediction, ModelVersion
try:
    from alert_service import send_alert
    ALERTS_ENABLED = True
    print("[Alert] ✅ Alert service loaded")
except Exception as e:
    ALERTS_ENABLED = False
    print(f"[Alert] ⚠️ Alert service not available: {e}")

# ── App setup ─────────────────────────────────────────────────────
app = Flask(__name__)

# ── Database config ───────────────────────────────────────────────
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "root")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "network_slicing")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "ms1_network_slicing_secret"

db.init_app(app)

# ── Load ML models ────────────────────────────────────────────────
ML_DIR = os.path.join(os.path.dirname(__file__), "ml")

print("[ML] Loading models...")
try:
    # 6G QoS regression model (DSO1 XGBoost)
    model_qos_6g       = joblib.load(os.path.join(ML_DIR, "model_6G.joblib"))
    # 5G SLA risk model (XGBoost calibrated)
    model_qos_5g       = joblib.load(os.path.join(ML_DIR, "model_5G.joblib"))
    scaler_5g          = joblib.load(os.path.join(ML_DIR, "scaler_5G.joblib"))
    # Congestion classifier (SGD)
    model_congestion   = joblib.load(os.path.join(ML_DIR, "model_congestion.joblib"))
    scaler_congestion  = joblib.load(os.path.join(ML_DIR, "scaler_congestion.joblib"))
    encoder_congestion = joblib.load(os.path.join(ML_DIR, "encoder_congestion.joblib"))
    print("[ML] ✅ All models loaded (5G + 6G)")
except Exception as e:
    print(f"[ML] ❌ Error loading models: {e}")
    model_qos_6g       = None
    model_qos_5g       = None
    scaler_5g          = None
    model_congestion   = None
    scaler_congestion  = None
    encoder_congestion = None

# ── Helper: build QoS features ───────────────────────────────────
def build_qos_features(data: dict) -> pd.DataFrame:
    """Build the 4 gap features for the QoS regression model."""
    latency_gap     = data["latency_budget"] - data["slice_latency"]
    packet_loss_gap = data["packet_loss_budget"] - data["slice_packet_loss"]
    jitter_gap      = data["jitter_budget"] - data["slice_jitter"]
    rate_gap        = data["slice_transfer_rate"] - data["data_rate_budget"]

    return pd.DataFrame([{
        "Latency_Gap":     latency_gap,
        "Packet_Loss_Gap": packet_loss_gap,
        "Jitter_Gap":      jitter_gap,
        "Rate_Gap":        rate_gap,
    }])

def build_5g_features(data: dict) -> pd.DataFrame:
    plr   = data.get("plr", 0.001)
    delay = data.get("delay", 100)
    time  = data.get("time", 14)
    cat   = data.get("lte5g_cat", 14)

    # More realistic network load calculation
    is_peak             = 1 if (8 <= time <= 10 or 18 <= time <= 21) else 0
    network_load_factor = min(
        0.15 + is_peak * 0.25 + (plr / 0.01) * 0.08 + (delay / 300) * 0.12,
        1.0
    )
    packet_delay_noisy       = delay * (1 + network_load_factor * 0.12)
    packet_loss_noisy        = plr   * (1 + network_load_factor * 0.10)
    qos_strictness           = (1 / (delay + 1e-9)) + plr * 10
    load_induced_delay       = network_load_factor * 100
    delay_margin             = 500 - delay
    delay_margin_pct         = delay_margin / 500 if delay < 500 else 0
    effective_loss_rate      = packet_loss_noisy * (1 + network_load_factor)
    loss_margin              = 0.05 - plr
    violation_risk_composite = (plr / 0.01) * 0.5 + (delay / 300) * 0.5
    delay_margin_ok          = 1 if delay_margin > 0 else 0
    loss_margin_ok           = 1 if loss_margin > 0 else 0
    n_margins_ok             = delay_margin_ok + loss_margin_ok

    return pd.DataFrame([{
        "LTE/5g Category":          cat,
        "Time":                     time,
        "Packet Loss Rate":         plr,
        "Packet delay":             delay,
        "IoT":                      0,
        "LTE/5G":                   1,
        "GBR":                      1,
        "Non-GBR":                  0,
        "AR/VR/Gaming":             0,
        "Healthcare":               0,
        "Industry 4.0":             0,
        "IoT Devices":              0,
        "Public Safety":            0,
        "Smart City & Home":        0,
        "Smart Transportation":     0,
        "Smartphone":               1,
        "network_load_factor":      round(network_load_factor, 4),
        "packet_delay_noisy":       round(packet_delay_noisy, 4),
        "packet_loss_noisy":        round(packet_loss_noisy, 6),
        "qos_strictness":           round(qos_strictness, 6),
        "load_induced_delay":       round(load_induced_delay, 4),
        "delay_margin":             round(delay_margin, 4),
        "delay_margin_pct":         round(delay_margin_pct, 4),
        "effective_loss_rate":      round(effective_loss_rate, 6),
        "loss_margin":              round(loss_margin, 6),
        "violation_risk_composite": round(violation_risk_composite, 4),
        "delay_margin_ok":          delay_margin_ok,
        "loss_margin_ok":           loss_margin_ok,
        "n_margins_ok":             n_margins_ok,
    }])

   
def build_congestion_features(data: dict) -> pd.DataFrame:
    """Build the 15 features for the congestion classifier."""
    latency_stress  = data["slice_latency"] / (data["latency_budget"] + 1e-9)
    bandwidth_usage = data["data_rate_budget"] / (data["slice_transfer_rate"] + 1e-9)
    mobility_jitter = data["slice_jitter"] / (data["jitter_budget"] + 1e-9)

    return pd.DataFrame([{
        "Packet Loss Budget":                   data["packet_loss_budget"],
        "Latency Budget (μs)":                  data["latency_budget"],
        "Jitter Budget (μs)":                   data["jitter_budget"],
        "Data Rate Budget (Gbps)":              data["data_rate_budget"],
        "Required Mobility":                    data.get("required_mobility", 0),
        "Required Connectivity":                data.get("required_connectivity", 1),
        "Slice Available Transfer Rate (Gbps)": data["slice_transfer_rate"],
        "Slice Latency (μs)":                   data["slice_latency"],
        "Slice Packet Loss":                    data["slice_packet_loss"],
        "Slice Jitter (μs)":                    data["slice_jitter"],
        "Slice Type":                           data.get("slice_type", 0),
        "Slice Handover":                       data.get("slice_handover", 0),
        "Latency_Stress_Ratio":                 round(latency_stress, 4),
        "Mobility_Jitter_Impact":               round(mobility_jitter, 4),
        "Bandwidth_Usage_Ratio":                round(bandwidth_usage, 4),
    }])


def qos_to_congestion_level(qos_score: float) -> str:
    """Map QoS score to congestion level."""
    if qos_score >= 0.7:
        return "Normal"
    elif qos_score >= 0.4:
        return "Light"
    else:
        return "Critical"


# ══════════════════════════════════════════════════════════════════
# FRONTEND ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    """Main dashboard page."""
    recent = Prediction.query.order_by(
        Prediction.created_at.desc()
    ).limit(5).all()
    total       = Prediction.query.count()
    critical    = Prediction.query.filter_by(congestion_level="Critical").count()
    normal      = Prediction.query.filter_by(congestion_level="Normal").count()
    return render_template(
        "index.html",
        recent=recent,
        total=total,
        critical=critical,
        normal=normal,
    )


@app.route("/history")
def history():
    """Full prediction history page."""
    predictions = Prediction.query.order_by(
        Prediction.created_at.desc()
    ).limit(100).all()
    return render_template("history.html", predictions=predictions)


# ══════════════════════════════════════════════════════════════════
# API ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route("/predict/qos", methods=["POST"])
def predict_qos():
    """
    Predict QoS probability score [0, 1].
    Input: JSON with slice metrics
    Output: {qos_score, congestion_level, slice_id}
    """
    data     = request.get_json()
    slice_id = data.get("slice_id", f"slice_{datetime.now().strftime('%H%M%S')}")

    if model_qos_6g is None:
        return jsonify({"error": "QoS model not loaded"}), 503

    try:
        X        = build_qos_features(data)
        qos_raw  = float(model_qos_6g.predict(X)[0])
        qos_score = float(np.clip(qos_raw, 0, 1))
        congestion = qos_to_congestion_level(qos_score)

        # Save to DB
        pred = Prediction(
            slice_id         = slice_id,
            congestion_level = congestion,
            qos_score        = round(qos_score, 4),
            features_json    = json.dumps(data),
        )
        db.session.add(pred)
        db.session.commit()
        # Trigger alert if Critical
        if ALERTS_ENABLED and congestion == "Critical":
            send_alert(
                subject=f"🚨 Critical QoS Alert — Slice {slice_id}",
                body=(
                    f"Slice ID      : {slice_id}\n"
                    f"QoS Score     : {qos_score:.1%}\n"
                    f"SLA Respected : {'✅ Yes' if qos_score >= 0.5 else '❌ No'}\n"
                    f"Risk Level    : Critical\n\n"
                    f"Latency Budget : {data.get('latency_budget')} μs\n"
                    f"Slice Latency  : {data.get('slice_latency')} μs\n\n"
                    f"⚠️ Immediate action required!"
                ),
                level="CRITICAL"
            )

        return jsonify({
            "slice_id":         slice_id,
            "qos_score":        round(qos_score, 4),
            "congestion_level": congestion,
            "sla_respected":    qos_score >= 0.5,
            "risk_level":       "Low" if qos_score >= 0.7
                                else "Medium" if qos_score >= 0.4
                                else "Critical",
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/predict/qos/5g", methods=["POST"])
def predict_qos_5g():
    """
    Predict 5G SLA risk / QoS score using XGBoost.
    Input: JSON with time, plr, delay, lte5g_cat
    Output: {qos_score, congestion_level, p_sla_met, risk_tier}
    """
    data     = request.get_json()
    slice_id = data.get("slice_id", f"5g_{datetime.now().strftime('%H%M%S')}")

    if model_qos_5g is None:
        return jsonify({"error": "5G model not loaded"}), 503

    try:
        X = build_5g_features(data)
        if X is None:
            return jsonify({"error": "Could not build 5G features"}), 500

        cc        = model_qos_5g.calibrated_classifiers_[0]
        raw       = float(cc.estimator.predict(X.values)[0])
        qos_score = float(np.clip(raw, 0, 1))
        qos_score = round(qos_score, 4)
        risk      = round(1 - qos_score, 4)

        if risk >= 0.35:
            tier = "Critical"
        elif risk >= 0.20:
            tier = "High"
        elif risk >= 0.10:
            tier = "Medium"
        else:
            tier = "Low"

        congestion = qos_to_congestion_level(qos_score)

        # Save to DB
        pred = Prediction(
            slice_id         = slice_id,
            congestion_level = congestion,
            qos_score        = qos_score,
            features_json    = json.dumps(data),
        )
        db.session.add(pred)
        db.session.commit()
        # Trigger alert if Critical
        if ALERTS_ENABLED and congestion == "Critical":
            send_alert(
                subject=f"🚨 5G Critical QoS Alert — Slice {slice_id}",
                body=(
                    f"Pipeline      : 5G\n"
                    f"Slice ID      : {slice_id}\n"
                    f"QoS Score     : {qos_score:.1%}\n"
                    f"P(SLA Met)    : {qos_score:.1%}\n"
                    f"Risk Score    : {risk:.1%}\n"
                    f"Risk Tier     : {tier}\n"
                    f"SLA Respected : {'✅ Yes' if qos_score >= 0.5 else '❌ No'}\n\n"
                    f"Input — Time  : {data.get('time')}h\n"
                    f"Input — PLR   : {data.get('plr')}\n"
                    f"Input — Delay : {data.get('delay')} ms\n\n"
                    f"⚠️ 5G SLA violation detected — immediate action required!"
                ),
                level="CRITICAL" if tier == "Critical" else "WARNING"
            )

        return jsonify({
            "slice_id":         slice_id,
            "qos_score":        qos_score,
            "p_sla_met":        qos_score,
            "qos_risk_score":   risk,
            "risk_tier":        tier,
            "congestion_level": congestion,
            "sla_respected":    qos_score >= 0.5,
            "pipeline":         "5G",
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/predict/congestion", methods=["POST"])
def predict_congestion():
    """
    Predict congestion level: Normal / Light / Critical.
    Input: JSON with slice metrics
    Output: {congestion_level, confidence, slice_id}
    """
    data     = request.get_json()
    slice_id = data.get("slice_id", f"slice_{datetime.now().strftime('%H%M%S')}")

    if model_congestion is None:
        return jsonify({"error": "Congestion model not loaded"}), 503

    try:
        X         = build_congestion_features(data)
        X_scaled  = scaler_congestion.transform(X)
        pred_enc  = int(model_congestion.predict(X_scaled)[0])
        proba     = model_congestion.predict_proba(X_scaled)[0]

        model_classes = model_congestion.classes_
        class_idx     = list(model_classes).index(pred_enc)
        confidence    = float(proba[class_idx])

        raw_label = str(encoder_congestion.inverse_transform([pred_enc])[0])

        # Map to human-readable level
        level_map = {"0": "Normal", "1": "Light", "2": "Light", "3": "Critical"}
        congestion = level_map.get(raw_label, "Normal")

        # Save to DB
        pred = Prediction(
            slice_id         = slice_id,
            congestion_level = congestion,
            qos_score        = round(1 - confidence if congestion == "Critical"
                                     else confidence, 4),
            features_json    = json.dumps(data),
        )
        db.session.add(pred)
        db.session.commit()
        # Alert if Critical
        if ALERTS_ENABLED and congestion == "Critical":
            send_alert(
                subject=f"🚨 Congestion Critical — Slice {slice_id}",
                body=(
                    f"Slice ID         : {slice_id}\n"
                    f"Congestion Level : Critical\n"
                    f"Confidence       : {confidence:.1%}\n"
                    f"Raw Class        : {raw_label}\n\n"
                    f"🔴 Network congestion requires immediate attention!"
                ),
                level="CRITICAL"
            )

        return jsonify({
            "slice_id":         slice_id,
            "congestion_level": congestion,
            "confidence":       round(confidence, 4),
            "raw_class":        raw_label,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/predict/batch", methods=["POST"])
def predict_batch():
    """
    Predict QoS for multiple slices at once.
    Input: {"slices": [...list of slice metrics...]}
    Output: list of predictions
    """
    data   = request.get_json()
    slices = data.get("slices", [])

    if not slices:
        return jsonify({"error": "No slices provided"}), 400

    results = []
    for item in slices:
        try:
            X          = build_qos_features(item)
            qos_raw    = float(model_qos_6g.predict(X)[0])
            qos_score  = float(np.clip(qos_raw, 0, 1))
            congestion = qos_to_congestion_level(qos_score)

            pred = Prediction(
                slice_id         = item.get("slice_id", "batch"),
                congestion_level = congestion,
                qos_score        = round(qos_score, 4),
                features_json    = json.dumps(item),
            )
            db.session.add(pred)
            db.session.add(pred)

            # Alert if Critical
            if ALERTS_ENABLED and congestion == "Critical":
                send_alert(
                    subject=f"🚨 Batch Critical Alert — Slice {item.get('slice_id')}",
                    body=(
                        f"Slice ID      : {item.get('slice_id')}\n"
                        f"QoS Score     : {qos_score:.1%}\n"
                        f"Congestion    : Critical\n"
                        f"SLA Respected : ❌ No\n\n"
                        f"Detected in batch prediction of {len(slices)} slices."
                    ),
                    level="CRITICAL"
                )

            results.append({
                "slice_id":         item.get("slice_id"),
                "qos_score":        round(qos_score, 4),
                "congestion_level": congestion,
                "sla_respected":    qos_score >= 0.5,
            })
        except Exception as e:
            results.append({"slice_id": item.get("slice_id"), "error": str(e)})

    db.session.commit()
    return jsonify({
        "total":    len(results),
        "results":  results,
        "critical": sum(1 for r in results if r.get("congestion_level") == "Critical"),
        "normal":   sum(1 for r in results if r.get("congestion_level") == "Normal"),
    })

@app.route("/predict/stats")
def predict_stats():
    """Return prediction statistics."""
    from sqlalchemy import func

    total    = Prediction.query.count()
    by_level = db.session.query(
        Prediction.congestion_level,
        func.count(Prediction.id)
    ).group_by(Prediction.congestion_level).all()

    avg_qos  = db.session.query(func.avg(Prediction.qos_score)).scalar()
    min_qos  = db.session.query(func.min(Prediction.qos_score)).scalar()
    max_qos  = db.session.query(func.max(Prediction.qos_score)).scalar()

    return jsonify({
        "total_predictions": total,
        "by_congestion_level": {
            level: count for level, count in by_level
        },
        "qos_stats": {
            "average": round(float(avg_qos), 4) if avg_qos else 0,
            "min":     round(float(min_qos), 4) if min_qos else 0,
            "max":     round(float(max_qos), 4) if max_qos else 0,
        },
        "sla_compliance_rate": round(
            Prediction.query.filter(Prediction.qos_score >= 0.5).count()
            / max(total, 1) * 100, 1
        ),
    })

import csv
import io
from flask import Response

@app.route("/predict/export")
def export_csv():
    """Export all predictions as CSV."""
    predictions = Prediction.query.order_by(
        Prediction.created_at.desc()
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "slice_id", "congestion_level",
                     "qos_score", "created_at"])
    for p in predictions:
        writer.writerow([p.id, p.slice_id, p.congestion_level,
                         p.qos_score,
                         p.created_at.strftime("%Y-%m-%d %H:%M:%S")])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition":
                 "attachment; filename=predictions.csv"}
    )

@app.route("/predict/history", methods=["GET"])
def predict_history():
    """Return prediction history as JSON."""
    limit       = request.args.get("limit", 50, type=int)
    predictions = Prediction.query.order_by(
        Prediction.created_at.desc()
    ).limit(limit).all()
    return jsonify({
        "total":       Prediction.query.count(),
        "predictions": [p.to_dict() for p in predictions],
    })


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({
        "status":  "running",
        "service": "MS-1 Prediction & QoS Service",
        "models": {
            "qos_6g":      model_qos_6g is not None,
            "qos_5g":      model_qos_5g is not None,
            "congestion":  model_congestion is not None,
        
        }
    })


# ══════════════════════════════════════════════════════════════════
# INIT DB
# ══════════════════════════════════════════════════════════════════

with app.app_context():
    try:
        db.create_all()
        print("[DB] ✅ Tables created")
    except Exception as e:
        print(f"[DB] ⚠️ {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
