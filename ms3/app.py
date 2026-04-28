"""
app.py
======
MS-3 Dashboard & Alerts Service
Aggregates MS-1 (QoS) + MS-2 (Anomaly) in real time.

Routes:
  GET  /                          → main NOC dashboard
  GET  /alerts                    → alerts page
  GET  /dashboard/slices          → all active slices (JSON)
  GET  /dashboard/alerts          → active alerts WARN/CRITICAL (JSON)
  POST /dashboard/threshold       → configure thresholds
  POST /dashboard/alert/ack       → acknowledge an alert
  POST /dashboard/simulate        → simulate slice data (demo)
"""

import os
import json
import requests
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from models import db, Alert, Threshold, SliceState

# ── App setup ──────────────────────────────────────────────────────
app = Flask(__name__)

DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "root")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "network_slicing")

# MS-1 and MS-2 URLs
MS1_URL = os.environ.get("MS1_URL", "http://localhost:5001")
MS2_URL = os.environ.get("MS2_URL", "http://localhost:5002")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "ms3_dashboard_secret"

db.init_app(app)

# ── Alert service ──────────────────────────────────────────────────
try:
    from alert_service import send_alert
    ALERTS_ENABLED = True
    print("[Alert] ✅ Alert service loaded")
except Exception as e:
    ALERTS_ENABLED = False
    print(f"[Alert] ⚠️ {e}")


# ── Helper: check thresholds and create alert ─────────────────────
def check_and_alert(slice_id: str, qos_score: float,
                    congestion: str, is_anomaly: bool):
    """Compare metrics against thresholds and create alerts."""
    thresholds = {t.metric: t for t in Threshold.query.all()}

    qos_warn     = thresholds.get("qos_score")
    cong_warn    = thresholds.get("congestion_level")

    alerts_created = []

    # QoS threshold check
    if qos_warn and qos_score is not None:
        if qos_score <= qos_warn.critical_value:
            level   = "CRITICAL"
            message = (f"QoS score {qos_score:.3f} below critical "
                       f"threshold {qos_warn.critical_value}")
        elif qos_score <= qos_warn.warn_value:
            level   = "WARN"
            message = (f"QoS score {qos_score:.3f} below warning "
                       f"threshold {qos_warn.warn_value}")
        else:
            level = None

        if level:
            alert = Alert(
                slice_id = slice_id,
                level    = level,
                message  = message,
            )
            db.session.add(alert)
            alerts_created.append(alert)

            if ALERTS_ENABLED:
                send_alert(
                    subject=f"[{level}] QoS Alert — Slice {slice_id}",
                    body=message,
                    level=level,
                )

    # Anomaly alert
    if is_anomaly:
        alert = Alert(
            slice_id = slice_id,
            level    = "CRITICAL",
            message  = f"Anomaly detected on slice {slice_id}",
        )
        db.session.add(alert)
        alerts_created.append(alert)

        if ALERTS_ENABLED:
            send_alert(
                subject=f"🚨 Anomaly Alert — Slice {slice_id}",
                body=f"Anomaly detected on slice {slice_id} "
                     f"(QoS={qos_score:.3f})",
                level="CRITICAL",
            )

    # Congestion alert
    if congestion == "Critical":
        alert = Alert(
            slice_id = slice_id,
            level    = "CRITICAL",
            message  = f"Critical congestion on slice {slice_id}",
        )
        db.session.add(alert)
        alerts_created.append(alert)

    db.session.commit()
    return alerts_created


# ══════════════════════════════════════════════════════════════════
# FRONTEND ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    """Main NOC dashboard."""
    slices        = SliceState.query.order_by(
        SliceState.last_updated.desc()).all()
    active_alerts = Alert.query.filter_by(
        acknowledged=False).order_by(
        Alert.created_at.desc()).limit(10).all()
    total_slices  = len(slices)
    critical_cnt  = sum(1 for s in slices if s.congestion_level == "Critical"
                        or s.is_anomaly)
    warn_cnt      = sum(1 for s in slices if s.congestion_level == "Light")
    normal_cnt    = sum(1 for s in slices if s.congestion_level == "Normal"
                        and not s.is_anomaly)
    thresholds    = Threshold.query.all()

    return render_template(
        "index.html",
        slices=slices,
        active_alerts=active_alerts,
        total_slices=total_slices,
        critical_cnt=critical_cnt,
        warn_cnt=warn_cnt,
        normal_cnt=normal_cnt,
        thresholds=thresholds,
        ms1_url=MS1_URL,
        ms2_url=MS2_URL,
    )


@app.route("/alerts")
def alerts_page():
    """Full alerts history page."""
    level      = request.args.get("level", "all")
    unacked    = request.args.get("unacked", "false") == "true"
    query      = Alert.query
    if level != "all":
        query  = query.filter_by(level=level.upper())
    if unacked:
        query  = query.filter_by(acknowledged=False)
    alerts     = query.order_by(Alert.created_at.desc()).limit(100).all()
    return render_template(
        "alerts.html",
        alerts=alerts,
        level=level,
        unacked=unacked,
    )


# ══════════════════════════════════════════════════════════════════
# API ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route("/dashboard/slices", methods=["GET"])
def get_slices():
    """Return all active slices with their current state."""
    slices = SliceState.query.order_by(
        SliceState.last_updated.desc()).all()
    return jsonify({
        "total":   len(slices),
        "slices":  [s.to_dict() for s in slices],
        "summary": {
            "critical": sum(1 for s in slices
                            if s.congestion_level == "Critical"
                            or s.is_anomaly),
            "warning":  sum(1 for s in slices
                            if s.congestion_level == "Light"),
            "normal":   sum(1 for s in slices
                            if s.congestion_level == "Normal"
                            and not s.is_anomaly),
        }
    })


@app.route("/dashboard/alerts", methods=["GET"])
def get_alerts():
    """Return active (unacknowledged) alerts."""
    level  = request.args.get("level", None)
    query  = Alert.query.filter_by(acknowledged=False)
    if level:
        query = query.filter_by(level=level.upper())
    alerts = query.order_by(Alert.created_at.desc()).all()
    return jsonify({
        "total":    Alert.query.filter_by(acknowledged=False).count(),
        "critical": Alert.query.filter_by(
            acknowledged=False, level="CRITICAL").count(),
        "warn":     Alert.query.filter_by(
            acknowledged=False, level="WARN").count(),
        "alerts":   [a.to_dict() for a in alerts],
    })


@app.route("/dashboard/threshold", methods=["POST"])
def set_threshold():
    """
    Configure alert thresholds.
    Input: {metric, warn_value, critical_value}
    """
    data     = request.get_json()
    metric   = data.get("metric")
    warn     = data.get("warn_value")
    critical = data.get("critical_value")

    if not all([metric, warn is not None, critical is not None]):
        return jsonify({"error": "metric, warn_value and critical_value required"}), 400

    existing = Threshold.query.filter_by(metric=metric).first()
    if existing:
        existing.warn_value     = warn
        existing.critical_value = critical
    else:
        db.session.add(Threshold(
            metric         = metric,
            warn_value     = warn,
            critical_value = critical,
        ))
    db.session.commit()

    return jsonify({
        "status":  "updated",
        "metric":  metric,
        "warn":    warn,
        "critical": critical,
    })


@app.route("/dashboard/alert/ack", methods=["POST"])
def acknowledge_alert():
    """
    Acknowledge an alert.
    Input: {alert_id} or {slice_id} to ack all for a slice
    """
    data     = request.get_json()
    alert_id = data.get("alert_id")
    slice_id = data.get("slice_id")

    if alert_id:
        alert = Alert.query.get(alert_id)
        if not alert:
            return jsonify({"error": "Alert not found"}), 404
        alert.acknowledged = True
        db.session.commit()
        return jsonify({"status": "acknowledged", "alert_id": alert_id})

    elif slice_id:
        count = Alert.query.filter_by(
            slice_id=slice_id, acknowledged=False).update(
            {"acknowledged": True})
        db.session.commit()
        return jsonify({
            "status":       "acknowledged",
            "slice_id":     slice_id,
            "count":        count,
        })

    return jsonify({"error": "alert_id or slice_id required"}), 400


@app.route("/dashboard/simulate", methods=["POST"])
def simulate_slice():
    """
    Simulate a slice update by calling MS-1 and MS-2.
    Used for demo purposes.
    Input: slice metrics
    """
    data     = request.get_json()
    slice_id = data.get("slice_id", f"slice_{datetime.now().strftime('%H%M%S')}")
    pipeline = data.get("pipeline", "6g").lower()

    qos_score    = None
    congestion   = "Normal"
    is_anomaly   = False
    anomaly_score = 0.0

    # ── Call MS-1 for QoS ──────────────────────────────────────────
    try:
        endpoint = f"{MS1_URL}/predict/qos"
        r        = requests.post(endpoint, json=data, timeout=5)
        if r.status_code == 200:
            ms1_data   = r.json()
            qos_score  = ms1_data.get("qos_score")
            congestion = ms1_data.get("congestion_level", "Normal")
    except Exception as e:
        print(f"[MS1] ⚠️ {e}")

    # ── Call MS-2 for anomaly ──────────────────────────────────────
    try:
        anomaly_payload = {**data, "pipeline": pipeline}
        r = requests.post(
            f"{MS2_URL}/anomaly/detect",
            json=anomaly_payload, timeout=5
        )
        if r.status_code == 200:
            ms2_data      = r.json()
            is_anomaly    = ms2_data.get("is_anomaly", False)
            anomaly_score = ms2_data.get("score", 0.0)
    except Exception as e:
        print(f"[MS2] ⚠️ {e}")

    # ── Update slice state ─────────────────────────────────────────
    existing = SliceState.query.filter_by(slice_id=slice_id).first()
    if existing:
        existing.qos_score        = qos_score
        existing.congestion_level = congestion
        existing.is_anomaly       = is_anomaly
        existing.anomaly_score    = anomaly_score
        existing.pipeline         = pipeline.upper()
        existing.last_updated     = datetime.now()
    else:
        db.session.add(SliceState(
            slice_id         = slice_id,
            pipeline         = pipeline.upper(),
            qos_score        = qos_score,
            congestion_level = congestion,
            is_anomaly       = is_anomaly,
            anomaly_score    = anomaly_score,
        ))
    db.session.commit()

    # ── Check thresholds and create alerts ─────────────────────────
    alerts = check_and_alert(slice_id, qos_score, congestion, is_anomaly)

    return jsonify({
        "slice_id":     slice_id,
        "qos_score":    qos_score,
        "congestion":   congestion,
        "is_anomaly":   is_anomaly,
        "anomaly_score": anomaly_score,
        "alerts_created": len(alerts),
        "ms1_reachable": qos_score is not None,
        "ms2_reachable": anomaly_score > 0,
    })
@app.route("/dashboard/notify", methods=["POST"])
def notify_from_ms():
    """
    Receive real-time updates from MS1 and MS2.
    Updates slice state without calling back to MS1/MS2.
    """
    data      = request.get_json()
    slice_id  = data.get("slice_id")
    source    = data.get("source", "unknown")

    if not slice_id:
        return jsonify({"error": "slice_id required"}), 400

    existing = SliceState.query.filter_by(slice_id=slice_id).first()
    if existing:
        if "qos_score" in data:
            existing.qos_score        = data.get("qos_score")
            existing.congestion_level = data.get("congestion", existing.congestion_level)
        if "is_anomaly" in data:
            existing.is_anomaly    = data.get("is_anomaly")
            existing.anomaly_score = data.get("anomaly_score", 0)
        existing.last_updated = datetime.now()
    else:
        db.session.add(SliceState(
            slice_id         = slice_id,
            pipeline         = data.get("pipeline", "6G").upper(),
            qos_score        = data.get("qos_score"),
            congestion_level = data.get("congestion", "Normal"),
            is_anomaly       = data.get("is_anomaly", False),
            anomaly_score    = data.get("anomaly_score", 0),
        ))

    # Check thresholds
    if data.get("qos_score") is not None:
        check_and_alert(
            slice_id,
            data.get("qos_score"),
            data.get("congestion", "Normal"),
            data.get("is_anomaly", False)
        )

    db.session.commit()
    return jsonify({"status": "updated", "slice_id": slice_id})

@app.route("/health")
def health():
    ms1_ok = ms2_ok = False
    try:
        ms1_ok = requests.get(
            f"{MS1_URL}/health", timeout=3).status_code == 200
    except Exception:
        pass
    try:
        ms2_ok = requests.get(
            f"{MS2_URL}/health", timeout=3).status_code == 200
    except Exception:
        pass
    return jsonify({
        "status":  "running",
        "service": "MS-3 Dashboard & Alerts Service",
        "dependencies": {
            "ms1_prediction": "✅ up" if ms1_ok else "⚠️ down",
            "ms2_anomaly":    "✅ up" if ms2_ok else "⚠️ down",
        }
    })


# ── Init DB ────────────────────────────────────────────────────────
with app.app_context():
    try:
        db.create_all()
        # Seed default thresholds if empty
        if Threshold.query.count() == 0:
            defaults = [
                Threshold(metric="qos_score",
                          warn_value=0.5, critical_value=0.3),
                Threshold(metric="anomaly_score",
                          warn_value=0.4, critical_value=0.65),
                Threshold(metric="congestion_level",
                          warn_value=1.0, critical_value=2.0),
            ]
            for t in defaults:
                db.session.add(t)
            db.session.commit()
            print("[DB] ✅ Default thresholds seeded")
        print("[DB] ✅ Tables ready")
    except Exception as e:
        print(f"[DB] ⚠️ {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
