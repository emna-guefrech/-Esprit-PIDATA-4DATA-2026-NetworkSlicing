"""
config.py
=========
Alerting configuration.
Set your email/Slack credentials here.
"""

# ── Email config (Gmail) ──────────────────────────────────────────
EMAIL_CONFIG = {
    "enabled":       True,
    "smtp_host":     "smtp.gmail.com",
    "smtp_port":     587,
    "sender_email":  "emnaguefrech9@gmail.com",
    "sender_password": "fsmj gsnf rjon wyqr",
    "receiver_email": "emnaguefrech9@gmail.com",
}

# ── Slack config ──────────────────────────────────────────────────
SLACK_CONFIG = {
    "enabled":     False,
    "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
}

# ── Alert thresholds ──────────────────────────────────────────────
THRESHOLDS = {
    "sla_risk_score":    0.5,   # XGBoost risk score > 0.5 → alert
    "qos_probability":   0.4,   # QoS prob < 0.4 → alert
    "anomaly_score":     0.6,   # Anomaly score > 0.6 → alert
    "congestion_class": ["1", "2", "3"],
}
