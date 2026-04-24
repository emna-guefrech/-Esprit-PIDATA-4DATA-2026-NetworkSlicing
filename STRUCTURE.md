# Project Architecture & Structure

## Overview

The Network Slicing Dashboard User Management module follows a **modular Flask application factory pattern** with clear separation of concerns.

## Directory Tree

```
flask/
│
├── app/                          # Main application package
│   ├── __init__.py              # App factory: create_app()
│   ├── extensions.py            # Extension initialization (db, login_manager, mail)
│   ├── security.py              # RBAC decorators (@role_required, @admin_required)
│   │
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── __init__.py          # Model registry
│   │   ├── user.py              # User model + UserRole enum + password hashing
│   │   ├── monitoring.py        # Alert, Threshold, Prediction, Anomaly, ModelVersion
│   │   └── logs.py              # IntegrationLog, ShapLog
│   │
│   ├── blueprints/              # Flask blueprints (modular routes)
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication routes (login, logout, profile)
│   │   ├── dashboard.py         # Dashboard & metrics API
│   │   └── admin.py             # User CRUD + MS-4 API endpoints
│   │
│   ├── templates/               # Jinja2 HTML templates
│   │   ├── base.html            # Master layout (sidebar, topbar, flash messages)
│   │   ├── auth/
│   │   │   ├── login.html       # Login form
│   │   │   └── profile.html     # User profile & password change
│   │   ├── dashboard/
│   │   │   └── index.html       # Main dashboard with metric cards
│   │   └── admin/
│   │       ├── users.html       # User list with pagination
│   │       ├── create_user.html # Create user form
│   │       └── edit_user.html   # Edit user (role, status)
│   │
│   └── static/                  # Static assets
│       ├── css/
│       │   └── dashboard.css    # Dashboard styling (sidebar, cards, responsive)
│       └── js/
│           └── dashboard.js     # Dashboard interactions & AJAX
│
├── config.py                    # Configuration classes (dev/prod/testing)
├── run.py                       # Development server entry point
├── wsgi.py                      # Production WSGI entry (Gunicorn)
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules (includes .env)
├── README.md                    # Installation & usage guide
└── STRUCTURE.md                # This file
```

---

## Application Factory Pattern

### Initialization Flow

```
run.py (entry point)
  ↓
create_app('development')
  ↓
config.py (load DevelopmentConfig)
  ↓
extensions.py (init db, login_manager, mail)
  ↓
blueprints (auth, dashboard, admin)
  ↓
Flask app ready at :5000
```

### Key Files

#### `app/__init__.py` (App Factory)
```python
def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    return app
```

#### `config.py` (Configuration Management)
Three config classes:
- **DevelopmentConfig**: `DEBUG=True`, local SQLite/MySQL
- **ProductionConfig**: `DEBUG=False`, secured cookies, production DB
- **TestingConfig**: In-memory SQLite, CSRF disabled

---

## Models & Database Schema

### User Model (`app/models/user.py`)
```
users table
├── id (PK)
├── username (unique)
├── password_hash (Werkzeug PBKDF2)
├── role (enum: system_admin, network_engineer, data_scientist, noc_operator)
├── is_active (soft delete flag)
├── created_at (auto-set timestamp)
└── updated_at (auto-update timestamp)

Methods:
├── set_password(password) → hash with Werkzeug
├── check_password(password) → verify hash
├── has_role(*roles) → check if user has role
├── is_admin() → convenience check
└── get_role_label() → human-readable role
```

### Monitoring Models (`app/models/monitoring.py`)
- **Alert**: Network slice alerts (level, message, acknowledged)
- **Threshold**: Metric thresholds (warn_value, critical_value)
- **Prediction**: ML model predictions (congestion_level, qos_score)
- **Anomaly**: Anomaly detection results
- **ModelVersion**: ML model performance tracking

### Log Models (`app/models/logs.py`)
- **IntegrationLog**: Microservice integration audit trail
- **ShapLog**: SHAP feature importance logs

---

## Routes & API Endpoints

### Authentication Blueprint (`/auth/*`)
| Route | Method | Auth | Purpose |
|-------|--------|------|---------|
| `/auth/login` | GET, POST | No | Login form & processing |
| `/auth/logout` | POST | Yes | Logout & session clear |
| `/auth/profile` | GET, POST | Yes | View/edit profile & password |

### Dashboard Blueprint (`//*`)
| Route | Method | Auth | Purpose |
|-------|--------|------|---------|
| `/` | GET | Yes | Main dashboard |
| `/api/dashboard/metrics` | GET | Yes | JSON metrics for AJAX |

### Admin Blueprint (`/admin/*`)
**MS-4 API Endpoints:**
| Route | Method | Auth | Purpose |
|-------|--------|------|---------|
| `/admin/users` | GET | Yes (admin) | List users (JSON) |
| `/admin/users` | POST | Yes (admin) | Create user (JSON) |
| `/admin/health` | GET | No | System health check |
| `/admin/logs` | GET | Yes (admin) | Integration logs (JSON) |

**Web Interface Routes:**
| Route | Method | Auth | Purpose |
|-------|--------|------|---------|
| `/admin/users/web` | GET | Yes (admin) | List users (HTML paginated) |
| `/admin/users/web/create` | GET, POST | Yes (admin) | Create user form |
| `/admin/users/web/<id>/edit` | GET, POST | Yes (admin) | Edit user (role, status) |
| `/admin/users/web/<id>/deactivate` | POST | Yes (admin) | Deactivate user |

---

## Role-Based Access Control (RBAC)

### Role Hierarchy & Permissions

**system_admin**
- Full system access
- Manage all users
- View all dashboards
- Access all APIs

**network_engineer**
- View dashboard
- View alerts
- View predictions
- Cannot manage users

**data_scientist**
- View dashboard
- View predictions
- Cannot view alerts
- Cannot manage users

**noc_operator**
- View dashboard
- View alerts
- Cannot view predictions
- Cannot manage users

### Implementation

**Decorator Pattern:**
```python
@admin_required  # Shorthand for system_admin only
def admin_route():
    pass

@role_required('network_engineer', 'noc_operator')
def alerts_route():
    pass
```

**Sidebar Conditional Rendering:**
```html
{% if current_user.has_role('network_engineer', 'noc_operator') %}
    <li><a href="/alerts">Alertes</a></li>
{% endif %}
```

---

## Templates & UI Components

### Base Layout (`base.html`)
- Master template with DOCTYPE, head, body structure
- Responsive sidebar (hidden on mobile)
- Top bar with user dropdown and status indicator
- Flash messages container
- Bootstrap 5 + Font Awesome icons

### Authentication Templates
- **login.html**: Gradient login form with remember-me checkbox
- **profile.html**: User info display + password change form

### Dashboard Templates
- **dashboard/index.html**: 4 metric cards + Active Slices section + Alerts/Thresholds sidebar

### Admin Templates
- **users.html**: Paginated user table with edit/deactivate actions
- **create_user.html**: Create user form with role selection
- **edit_user.html**: Edit role and active status

### Styling
- **dashboard.css**: 
  - Sidebar navigation styling (gradient background)
  - Responsive grid layout
  - Metric cards with hover effects
  - Modern form styling
  - Badge and button variants
  - Mobile-first responsive design (768px, 992px breakpoints)

### JavaScript
- **dashboard.js**:
  - Auto-dismiss alerts after 5 seconds
  - Sidebar mobile toggle
  - AJAX metrics refresh (every 30 seconds)
  - Date formatting utility
  - Clipboard copy helper

---

## Security Architecture

### Password Security
- **Werkzeug PBKDF2**: Industry-standard password hashing
- **Minimum 12 characters**: Enforced in validation
- **Salted hashing**: Automatic per Werkzeug

### Session Management
- **Flask-Login**: User session tracking
- **HTTPOnly cookies**: Prevent XSS attacks
- **SameSite=Lax**: CSRF protection
- **Secure flag**: HTTPS only in production

### Data Protection
- **SQLAlchemy ORM**: Prevents SQL injection via parameterized queries
- **Input validation**: Server-side validation on all forms
- **Output escaping**: Jinja2 auto-escapes template variables
- **Logical deletion**: Users marked inactive instead of deleted

### Access Control
- **@login_required**: Protects authenticated routes
- **@role_required**: Role-based route access
- **403 Forbidden**: Proper error response for unauthorized access
- **Session checks**: Role validated on each request

---

## Configuration & Environment

### Environment Variables (`.env`)

```bash
# Flask
FLASK_APP=wsgi.py
FLASK_ENV=development
SECRET_KEY=<random-key>

# Database
DEV_DATABASE_URL=mysql+pymysql://user:pass@host:3306/db
DATABASE_URL=<production-db-url>

# Email (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=<email>
MAIL_PASSWORD=<app-password>
```

### Configuration Classes

**BaseConfig**: Shared settings across all environments
- `SQLALCHEMY_TRACK_MODIFICATIONS = False`
- `SESSION_COOKIE_SAMESITE = 'Lax'`
- `SESSION_COOKIE_HTTPONLY = True`

**DevelopmentConfig**: Local development
- `DEBUG = True`
- `SQLALCHEMY_ECHO = True` (log SQL)
- Local MySQL connection

**ProductionConfig**: Production deployment
- `DEBUG = False`
- `SESSION_COOKIE_SECURE = True` (HTTPS)
- Production database connection

---

## Data Flow Diagram

```
User
  ↓
Login Page
  ├→ POST /auth/login
  ├→ Verify username
  ├→ Check password hash
  ├→ Set Flask-Login session
  └→ Redirect to dashboard
  
Dashboard
  ├→ Load current_user from session
  ├→ Query alerts, thresholds, predictions
  ├→ Render base.html + dashboard/index.html
  └→ AJAX /api/dashboard/metrics (every 30s)

Admin Panel
  ├→ Verify is_admin() via @admin_required
  ├→ GET /admin/users/web → Paginate users
  ├→ POST /admin/users/web/create → Validate + Create
  ├→ POST /admin/users/<id>/edit → Update role/status
  └→ POST /admin/users/<id>/deactivate → Logical delete

API (MS-4)
  ├→ POST /auth/login → Return session
  ├→ GET /admin/users → JSON user list
  ├→ POST /admin/users → Create user (JSON)
  ├→ GET /admin/health → System status
  └→ GET /admin/logs → Integration logs
```

---

## Dependencies & Technology Stack

### Backend
- **Flask 2.3.3**: Micro web framework
- **Flask-SQLAlchemy 3.0.5**: ORM integration
- **Flask-Login 0.6.2**: Session management
- **Flask-Mail 0.9.1**: Email support (optional)
- **Flask-WTF 1.1.1**: Form CSRF protection
- **Werkzeug 2.3.7**: Password hashing & utilities
- **PyMySQL 1.1.0**: MySQL connector
- **python-dotenv 1.0.0**: Environment variable loader

### Frontend
- **Bootstrap 5.1.3**: Responsive CSS framework
- **Font Awesome 6.0.0**: Icon library
- **Vanilla JavaScript**: AJAX & interactions

---

## Development Workflow

### Adding New Features

1. **Create Model** (`app/models/`)
2. **Create Blueprint** (`app/blueprints/`)
3. **Add Routes** with proper decorators
4. **Create Templates** in `app/templates/`
5. **Style & Test**

### Example: Adding New Alerts Feature

```python
# 1. Model exists: Alert in app/models/monitoring.py

# 2. Create blueprint: app/blueprints/alerts.py
@alerts_bp.route('/alerts', methods=['GET'])
@role_required('network_engineer', 'noc_operator', 'system_admin')
def list_alerts():
    alerts = Alert.query.order_by(Alert.created_at.desc()).all()
    return render_template('alerts.html', alerts=alerts)

# 3. Register in app/__init__.py
from app.blueprints.alerts import alerts_bp
app.register_blueprint(alerts_bp, url_prefix='/alerts')

# 4. Create template: app/templates/alerts.html
```

---

## Performance Considerations

- **Database Connection Pooling**: Configured in config.py (pool_size=10)
- **Query Optimization**: Use `.limit()` and `.paginate()` for large result sets
- **Caching**: AJAX metrics refresh every 30s (not real-time)
- **Static File Serving**: CSS/JS cached by browser

---

## Monitoring & Logging

### Health Check Endpoint
`GET /admin/health` - Returns database and service status

### Integration Logs
All microservice calls logged to `integration_logs` table

### Application Logs
- Development: Console output with SQL echo
- Production: File logging (to be configured)

---

## Future Enhancements

- [ ] Email-based password reset with token expiration
- [ ] Two-factor authentication (2FA)
- [ ] Audit trail for all user actions
- [ ] User groups/teams for role management
- [ ] Real-time WebSocket updates for dashboard
- [ ] Export functionality (CSV, PDF)
- [ ] Advanced search and filtering
- [ ] API rate limiting
- [ ] OAuth2/LDAP integration

---

**Document Version:** 1.0.0  
**Last Updated:** April 2026
