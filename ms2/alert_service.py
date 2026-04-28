"""
alert_service.py
================
Alerting service for the 5G+6G Network Slicing pipeline.

Sends email/Slack alerts when:
  - Anomaly detected (5G or 6G)
  - SLA violated (XGBoost risk > threshold)
  - QoS probability drops below threshold
  - Congestion detected (6G)

Can be used:
  1. Standalone: python3 alert_service.py --test
  2. Integrated into the FastAPI app
  3. Called from model_pipeline.py after predictions
"""

import smtplib
import json
import urllib.request
import urllib.error
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from config import EMAIL_CONFIG, SLACK_CONFIG, THRESHOLDS


# ── Core alert sender ─────────────────────────────────────────────

def send_email_alert(subject: str, body: str) -> bool:
    """Send an email alert via Gmail SMTP."""
    if not EMAIL_CONFIG["enabled"]:
        print("[Alert] Email disabled in config")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = EMAIL_CONFIG["sender_email"]
        msg["To"]      = EMAIL_CONFIG["receiver_email"]

        # Plain text version
        text_part = MIMEText(body, "plain")

        # HTML version
        html_body = f"""
        <html><body>
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #1e40af, #3b82f6);
                        padding: 20px; border-radius: 8px 8px 0 0;">
                <h1 style="color: white; margin: 0;">
                    🚨 Network Slicing Alert
                </h1>
                <p style="color: #bfdbfe; margin: 5px 0 0 0;">
                    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </div>
            <div style="background: #f8fafc; padding: 20px;
                        border: 1px solid #e2e8f0; border-radius: 0 0 8px 8px;">
                <pre style="background: white; padding: 15px; border-radius: 6px;
                            border-left: 4px solid #ef4444; font-size: 14px;
                            white-space: pre-wrap;">{body}</pre>
            </div>
        </div>
        </body></html>
        """
        html_part = MIMEText(html_body, "html")

        msg.attach(text_part)
        msg.attach(html_part)

        with smtplib.SMTP(EMAIL_CONFIG["smtp_host"],
                          EMAIL_CONFIG["smtp_port"]) as server:
            server.starttls()
            server.login(EMAIL_CONFIG["sender_email"],
                         EMAIL_CONFIG["sender_password"])
            server.sendmail(
                EMAIL_CONFIG["sender_email"],
                EMAIL_CONFIG["receiver_email"],
                msg.as_string()
            )

        print(f"[Alert] ✅ Email sent: {subject}")
        return True

    except Exception as e:
        print(f"[Alert] ❌ Email failed: {e}")
        return False


def send_slack_alert(message: str) -> bool:
    """Send a Slack alert via webhook."""
    if not SLACK_CONFIG["enabled"]:
        print("[Alert] Slack disabled in config")
        return False

    try:
        payload = json.dumps({
            "text": message,
            "username": "Network Slicing Bot",
            "icon_emoji": ":warning:"
        }).encode("utf-8")

        req = urllib.request.Request(
            SLACK_CONFIG["webhook_url"],
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=10)
        print(f"[Alert] ✅ Slack message sent")
        return True

    except Exception as e:
        print(f"[Alert] ❌ Slack failed: {e}")
        return False


def send_alert(subject: str, body: str, level: str = "WARNING") -> dict:
    """
    Send alert via all configured channels.

    Parameters
    ----------
    subject : alert subject/title
    body    : alert message body
    level   : WARNING, CRITICAL, INFO

    Returns
    -------
    dict with channel results
    """
    emoji = {"CRITICAL": "🚨", "WARNING": "⚠️", "INFO": "ℹ️"}.get(level, "⚠️")
    full_subject = f"{emoji} [{level}] {subject}"

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    full_body  = f"[{timestamp}] {level}\n\n{body}"

    print(f"\n{'='*50}")
    print(f"{emoji} ALERT: {subject}")
    print(f"Level  : {level}")
    print(f"Body   : {body}")
    print(f"{'='*50}\n")

    results = {
        "email": send_email_alert(full_subject, full_body),
        "slack": send_slack_alert(f"{full_subject}\n{full_body}"),
    }
    return results


# ── Alert checkers ────────────────────────────────────────────────

def check_5g_slice_prediction(prediction: dict, input_data: dict) -> None:
    """Check 5G slice prediction and alert if needed."""
    confidence = prediction.get("confidence", 1.0)
    slice_name = prediction.get("slice_name", "Unknown")

    if confidence < 0.6:
        send_alert(
            subject=f"Low confidence 5G slice prediction: {slice_name}",
            body=(
                f"Slice Type    : {slice_name} (Type {prediction.get('slice_type')})\n"
                f"Confidence    : {confidence:.1%}\n"
                f"Input — Time  : {input_data.get('time')}h\n"
                f"Input — PLR   : {input_data.get('plr')}\n"
                f"Input — Delay : {input_data.get('delay')} ms\n\n"
                f"⚠️ Model is uncertain about this prediction.\n"
                f"Manual review recommended."
            ),
            level="WARNING"
        )


def check_5g_sla_risk(prediction: dict, input_data: dict) -> None:
    """Check 5G SLA risk and alert if violated."""
    risk_score = prediction.get("qos_risk_score", 0)
    risk_tier  = prediction.get("risk_tier", "Low")
    sla_pred   = prediction.get("sla_prediction", 1)

    if risk_score > THRESHOLDS["sla_risk_score"] or sla_pred == 0:
        level = "CRITICAL" if risk_tier == "Critical" else "WARNING"
        send_alert(
            subject=f"5G SLA Risk Alert — {risk_tier} Risk Detected",
            body=(
                f"Risk Tier     : {risk_tier}\n"
                f"Risk Score    : {risk_score:.1%}\n"
                f"P(SLA Met)    : {prediction.get('p_sla_met', 0):.1%}\n"
                f"SLA Status    : {'✅ Met' if sla_pred == 1 else '❌ VIOLATED'}\n\n"
                f"Input — Time  : {input_data.get('time')}h\n"
                f"Input — PLR   : {input_data.get('plr')}\n"
                f"Input — Delay : {input_data.get('delay')} ms\n\n"
                f"🚨 Immediate action required to restore SLA compliance."
            ),
            level=level
        )


def check_5g_anomaly(prediction: dict, input_data: dict) -> None:
    """Check 5G anomaly detection and alert if anomaly found."""
    is_anomaly    = prediction.get("is_anomaly", 0)
    anomaly_score = prediction.get("anomaly_score", 0)
    risk_tier     = prediction.get("risk_tier", "Low")

    if is_anomaly == 1 or anomaly_score > THRESHOLDS["anomaly_score"]:
        level = "CRITICAL" if risk_tier == "High" else "WARNING"
        send_alert(
            subject=f"5G Anomaly Detected — {risk_tier} Risk",
            body=(
                f"Anomaly Score : {anomaly_score:.4f}\n"
                f"Risk Tier     : {risk_tier}\n"
                f"Status        : {'🚨 ANOMALY' if is_anomaly else '⚠️ Suspicious'}\n\n"
                f"Input — Time  : {input_data.get('time')}h\n"
                f"Input — PLR   : {input_data.get('plr')}\n"
                f"Input — Delay : {input_data.get('delay')} ms\n\n"
                f"🔍 Investigate network slice for unusual behavior."
            ),
            level=level
        )


def check_6g_qos(prediction: dict, input_data: dict) -> None:
    """Check 6G QoS probability and alert if too low."""
    qos_prob   = prediction.get("qos_probability", 1.0)
    sla_resp   = prediction.get("sla_respected", True)
    risk_level = prediction.get("risk_level", "Low")

    if qos_prob < THRESHOLDS["qos_probability"] or not sla_resp:
        level = "CRITICAL" if risk_level == "Critical" else "WARNING"
        send_alert(
            subject=f"6G QoS Alert — {risk_level} Risk (QoS={qos_prob:.1%})",
            body=(
                f"QoS Probability : {qos_prob:.1%}\n"
                f"SLA Respected   : {'✅ Yes' if sla_resp else '❌ No'}\n"
                f"Risk Level      : {risk_level}\n\n"
                f"Latency Budget  : {input_data.get('latency_budget_us')} μs\n"
                f"Slice Latency   : {input_data.get('slice_latency_us')} μs\n"
                f"PLR Budget      : {input_data.get('packet_loss_budget')}\n"
                f"Slice PLR       : {input_data.get('slice_packet_loss')}\n\n"
                f"📉 QoS degradation detected. Check network slice configuration."
            ),
            level=level
        )


def check_6g_anomaly(prediction: dict, input_data: dict) -> None:
    """Check 6G anomaly detection and alert if anomaly found."""
    is_anomaly = prediction.get("is_anomaly", 0)

    if is_anomaly == 1:
        send_alert(
            subject="6G Network Anomaly Detected",
            body=(
                f"Status          : 🚨 ANOMALY DETECTED\n"
                f"Label           : {prediction.get('anomaly_label')}\n\n"
                f"Latency Budget  : {input_data.get('latency_budget_us')} μs\n"
                f"Slice Latency   : {input_data.get('slice_latency_us')} μs\n\n"
                f"🔍 Unusual network behavior detected in 6G slice."
            ),
            level="CRITICAL"
        )


def check_6g_congestion(prediction: dict, input_data: dict) -> None:
    """Check 6G congestion and alert if detected."""
    congestion_class = prediction.get("congestion_class", "0")
    confidence       = prediction.get("congestion_probability", 0)

    if congestion_class in THRESHOLDS["congestion_class"]:
        send_alert(
            subject=f"6G Congestion Alert (confidence: {confidence:.1%})",
            body=(
                f"Congestion Class : {congestion_class}\n"
                f"Confidence       : {confidence:.1%}\n\n"
                f"Rate Budget      : {input_data.get('data_rate_budget_gbps')} Gbps\n"
                f"Transfer Rate    : {input_data.get('slice_transfer_rate_gbps')} Gbps\n\n"
                f"🔴 Network congestion detected. Consider load balancing."
            ),
            level="WARNING"
        )


# ── Test function ─────────────────────────────────────────────────

def test_alerts():
    """Test all alert types with mock data."""
    print("\n" + "="*55)
    print("🧪 TESTING ALERT SERVICE")
    print("="*55)

    mock_input_5g = {
        "time": 20, "plr": 0.01,
        "delay": 300, "lte5g_cat": 14
    }
    mock_input_6g = {
        "latency_budget_us": 100,
        "slice_latency_us": 280,
        "packet_loss_budget": 0.001,
        "slice_packet_loss": 0.009,
        "jitter_budget_us": 20,
        "slice_jitter_us": 45,
        "data_rate_budget_gbps": 10.0,
        "slice_transfer_rate_gbps": 3.0
    }

    print("\n--- Test 1: 5G SLA Risk Alert ---")
    check_5g_sla_risk(
        {"qos_risk_score": 0.75, "risk_tier": "Critical",
         "sla_prediction": 0, "p_sla_met": 0.25},
        mock_input_5g
    )

    print("\n--- Test 2: 5G Anomaly Alert ---")
    check_5g_anomaly(
        {"is_anomaly": 1, "anomaly_score": 0.82, "risk_tier": "High"},
        mock_input_5g
    )

    print("\n--- Test 3: 6G QoS Alert ---")
    check_6g_qos(
        {"qos_probability": 0.25, "sla_respected": False,
         "risk_level": "Critical"},
        mock_input_6g
    )

    print("\n--- Test 4: 6G Anomaly Alert ---")
    check_6g_anomaly(
        {"is_anomaly": 1, "anomaly_label": "Anomaly"},
        mock_input_6g
    )

    print("\n--- Test 5: 6G Congestion Alert ---")
    check_6g_congestion(
        {"congestion_class": "1", "congestion_probability": 0.87},
        mock_input_6g
    )

    print("\n✅ All alert tests completed!")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_alerts()
    else:
        print("Usage: python3 alert_service.py --test")
