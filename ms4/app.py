"""
app.py
======
MS-4 Auth & Admin Service

Routes:
  POST /auth/login              → login
  POST /auth/logout             → logout
  GET  /                        → login page / redirect to dashboard
  GET  /admin                   → admin dashboard
  GET  /admin/users             → list users
  POST /admin/users             → create/disable user
  GET  /admin/health            → status of all 4 MS
  GET  /admin/logs              → integration logs
"""

import os
import time
import requests
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import (Flask, request, jsonify, render_template,
                   redirect, url_for, session, flash)
from flask_login import (LoginManager, login_user, logout_user,
                          login_required, current_user)
from models import db, User, IntegrationLog

# ── App setup ──────────────────────────────────────────────────────
app = Flask(__name__)

DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "root")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "network_slicing")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "ms4_auth_super_secret_key_2026"

db.init_app(app)

# ── Flask-Login setup ──────────────────────────────────────────────
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ── MS URLs ───────────────────────────────────────────────────────
# URLs pour appels internes (health check depuis le container)
MS_URLS_INTERNAL = {
    "MS-1 Prediction":  os.environ.get("MS1_URL", "http://ms1:5001"),
    "MS-2 Anomaly":     os.environ.get("MS2_URL", "http://ms2:5002"),
    "MS-3 Dashboard":   os.environ.get("MS3_URL", "http://ms3:5003"),
    "MS-5 Model Mgmt":  os.environ.get("MS5_URL", "http://ms5:5005"),
}

# URLs pour le navigateur (depuis Windows)
MS_URLS = {
    "MS-1 Prediction":  "http://localhost:5001",
    "MS-2 Anomaly":     "http://localhost:5002",
    "MS-3 Dashboard":   "http://localhost:5003",
    "MS-5 Model Mgmt":  "http://localhost:5005",
}

ROLE_REDIRECTS = {
    "system_admin":      "/admin",
    "noc_operator":      "http://localhost:5003",
    "data_scientist":    "http://localhost:5005",
    "network_engineer":  "http://localhost:5001",
}

ROLE_LABELS = {
    "system_admin":     "⚙️ System Admin",
    "noc_operator":     "🖥️ NOC Operator",
    "data_scientist":   "🧪 Data Scientist",
    "network_engineer": "📡 Network Engineer",
}


# ── Helper: call MS and log ────────────────────────────────────────
def call_ms(service: str, url: str, endpoint: str = "/health") -> dict:
    """Call a microservice health endpoint and log the result."""
    start = time.time()
    try:
        r          = requests.get(f"{url}{endpoint}", timeout=3)
        latency_ms = int((time.time() - start) * 1000)
        status     = r.status_code
        up         = status == 200
        data       = r.json() if up else {}
    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        status     = 0
        up         = False
        data       = {"error": str(e)}

    # Log to DB
    log = IntegrationLog(
        service     = service,
        endpoint    = endpoint,
        status_code = status,
        latency_ms  = latency_ms,
    )
    db.session.add(log)
    db.session.commit()

    return {
        "service":    service,
        "url":        url,
        "up":         up,
        "status":     status,
        "latency_ms": latency_ms,
        "data":       data,
    }


# ══════════════════════════════════════════════════════════════════
# FRONTEND ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.role == "system_admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("portal"))
    return redirect(url_for("login_page"))


@app.route("/login", methods=["GET"])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/portal")
@login_required
def portal():
    """User portal — shows links to the right MS based on role."""
    return render_template(
        "portal.html",
        user=current_user,
        role_label=ROLE_LABELS.get(current_user.role, current_user.role),
        ms_urls=MS_URLS,
    )


@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != "system_admin":
        flash("Access denied — System Admin only", "error")
        return redirect(url_for("portal"))

    users      = User.query.order_by(User.created_at.desc()).all()
    logs       = IntegrationLog.query.order_by(
        IntegrationLog.created_at.desc()).limit(20).all()
    total_users  = len(users)
    active_users = sum(1 for u in users if u.is_active)

    return render_template(
        "admin.html",
        users=users,
        logs=logs,
        total_users=total_users,
        active_users=active_users,
        ms_urls=MS_URLS,
        role_labels=ROLE_LABELS,
    )


# ══════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route("/auth/login", methods=["POST"])
def login():
    """Login endpoint — accepts JSON or form data."""
    if request.is_json:
        data     = request.get_json()
        username = data.get("username")
        password = data.get("password")
    else:
        username = request.form.get("username")
        password = request.form.get("password")

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password_hash, password):
        if request.is_json:
            return jsonify({"error": "Invalid credentials"}), 401
        flash("Invalid username or password", "error")
        return redirect(url_for("login_page"))

    if not user.is_active:
        if request.is_json:
            return jsonify({"error": "Account disabled"}), 403
        flash("Your account has been disabled", "error")
        return redirect(url_for("login_page"))

    login_user(user)
    user.last_login = datetime.now()
    db.session.commit()

    # Log the login
    log = IntegrationLog(
        service     = "MS-4 Auth",
        endpoint    = "/auth/login",
        status_code = 200,
        latency_ms  = 0,
    )
    db.session.add(log)
    db.session.commit()

    if request.is_json:
        return jsonify({
            "status":   "success",
            "username": user.username,
            "role":     user.role,
            "redirect": ROLE_REDIRECTS.get(user.role, "/portal"),
        })

    if user.role == "system_admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("portal"))


@app.route("/auth/logout", methods=["POST", "GET"])
@login_required
def logout():
    """Logout endpoint."""
    logout_user()
    if request.is_json:
        return jsonify({"status": "logged out"})
    flash("Logged out successfully", "success")
    return redirect(url_for("login_page"))


# ══════════════════════════════════════════════════════════════════
# ADMIN API ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route("/admin/users", methods=["GET"])
@login_required
def get_users():
    """Return list of all users."""
    if current_user.role != "system_admin":
        return jsonify({"error": "Unauthorized"}), 403

    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({
        "total":  len(users),
        "active": sum(1 for u in users if u.is_active),
        "users":  [u.to_dict() for u in users],
    })


@app.route("/admin/users", methods=["POST"])
@login_required
def manage_user():
    """
    Create a new user or toggle active status.
    Input: {action: 'create'|'toggle', ...}
    """
    if current_user.role != "system_admin":
        return jsonify({"error": "Unauthorized"}), 403

    data   = request.get_json()
    action = data.get("action", "create")

    if action == "create":
        username = data.get("username")
        password = data.get("password")
        role     = data.get("role", "noc_operator")

        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already exists"}), 400

        user = User(
            username      = username,
            password_hash = generate_password_hash(password),
            role          = role,
            is_active     = True,
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({
            "status":   "created",
            "user":     user.to_dict(),
        })

    elif action == "toggle":
        user_id = data.get("user_id")
        user    = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        if user.id == current_user.id:
            return jsonify({"error": "Cannot disable yourself"}), 400
        user.is_active = not user.is_active
        db.session.commit()
        return jsonify({
            "status":    "toggled",
            "user_id":   user_id,
            "is_active": user.is_active,
        })

    elif action == "delete":
        user_id = data.get("user_id")
        user    = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        if user.id == current_user.id:
            return jsonify({"error": "Cannot delete yourself"}), 400
        db.session.delete(user)
        db.session.commit()
        return jsonify({"status": "deleted", "user_id": user_id})

    return jsonify({"error": "Unknown action"}), 400


@app.route("/admin/health", methods=["GET"])
@login_required
def admin_health():
    """Check health of all microservices."""
    results = []
    for service, url in MS_URLS_INTERNAL.items():
        result = call_ms(service, url, "/health")
        results.append(result)

    return jsonify({
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "services":   results,
        "summary": {
            "up":   sum(1 for r in results if r["up"]),
            "down": sum(1 for r in results if not r["up"]),
        }
    })


@app.route("/admin/logs", methods=["GET"])
@login_required
def admin_logs():
    """Return integration logs."""
    if current_user.role != "system_admin":
        return jsonify({"error": "Unauthorized"}), 403

    limit   = request.args.get("limit", 50, type=int)
    service = request.args.get("service", None)
    query   = IntegrationLog.query
    if service:
        query = query.filter_by(service=service)
    logs    = query.order_by(
        IntegrationLog.created_at.desc()).limit(limit).all()

    return jsonify({
        "total": IntegrationLog.query.count(),
        "logs":  [l.to_dict() for l in logs],
    })


@app.route("/health")
def health():
    return jsonify({
        "status":  "running",
        "service": "MS-4 Auth & Admin Service",
    })


# ── Init DB ────────────────────────────────────────────────────────
with app.app_context():
    try:
        db.create_all()
        # Seed default users if empty
        if User.query.count() == 0:
            defaults = [
                ("admin",    "admin123",   "system_admin"),
                ("engineer", "eng123",     "network_engineer"),
                ("scientist","sci123",     "data_scientist"),
                ("operator", "ops123",     "noc_operator"),
            ]
            for username, password, role in defaults:
                db.session.add(User(
                    username      = username,
                    password_hash = generate_password_hash(password),
                    role          = role,
                    is_active     = True,
                ))
            db.session.commit()
            print("[DB] ✅ Default users seeded")
            print("[DB]    admin/admin123       → system_admin")
            print("[DB]    engineer/eng123      → network_engineer")
            print("[DB]    scientist/sci123     → data_scientist")
            print("[DB]    operator/ops123      → noc_operator")
        print("[DB] ✅ Tables ready")
    except Exception as e:
        print(f"[DB] ⚠️ {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)
