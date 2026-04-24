# Network Slicing Dashboard - User Management Module

**Version:** 1.0.0  
**Technology Stack:** Flask + MySQL + Jinja2 + Bootstrap 5

---

## 📋 Overview

Complete user management module for a Network Slicing Dashboard monitoring system. Includes authentication, role-based access control (RBAC), admin user CRUD operations, and a modern dashboard interface.

**Key Features:**
- ✅ User authentication (login/logout)
- ✅ Role-based access control (4 roles: system_admin, network_engineer, data_scientist, noc_operator)
- ✅ User management (CRUD + logical deletion)
- ✅ Dashboard with real-time metrics
- ✅ MS-4 API endpoints for microservice integration
- ✅ Modern UI with Bootstrap 5 + Font Awesome icons
- ✅ Password security (Werkzeug hashing)
- ✅ Flash messages and error handling

---

## 🔧 Installation

### 1. Prerequisites

- **Python 3.8+**
- **MySQL 5.7+** (already running with existing schema)
- **pip** (Python package manager)

### 2. Clone/Setup Project

```bash
cd c:\Users\AymenJallouli\Desktop\flask
```

### 3. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Database Connection

Create a `.env` file in the project root (copy from `.env.example`):

```bash
# Flask
FLASK_APP=wsgi.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-in-production

# Database (Update with your MySQL credentials)
DEV_DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/network_slicing

# Email (Optional for V1 - leave as-is for local testing)
MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_USE_TLS=False
```

**Important:** Replace `root:password` with your actual MySQL credentials.

### 6. Database Setup

Before running the app, ensure your MySQL database exists with the `users` table:

```sql
CREATE DATABASE IF NOT EXISTS network_slicing;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('system_admin', 'network_engineer', 'data_scientist', 'noc_operator') DEFAULT 'network_engineer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username)
);

-- Optional: Create other monitoring tables if needed
CREATE TABLE IF NOT EXISTS alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slice_id VARCHAR(50) NOT NULL,
    level VARCHAR(20),
    message TEXT,
    acknowledged BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_slice (slice_id)
);

CREATE TABLE IF NOT EXISTS thresholds (
    id INT AUTO_INCREMENT PRIMARY KEY,
    metric VARCHAR(100) UNIQUE NOT NULL,
    warn_value FLOAT,
    critical_value FLOAT,
    unit VARCHAR(50),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_metric (metric)
);

CREATE TABLE IF NOT EXISTS predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slice_id VARCHAR(50) NOT NULL,
    congestion_level VARCHAR(50),
    qos_score FLOAT,
    features_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_slice (slice_id)
);
```

### 7. Create Initial Admin User (Optional)

```bash
# From Python interactive shell
python
>>> from app import create_app, db
>>> from app.models.user import User
>>> app = create_app('development')
>>> with app.app_context():
...     admin = User(username='admin', role='system_admin')
...     admin.set_password('Admin@123456')  # Min 12 chars
...     db.session.add(admin)
...     db.session.commit()
...     print("Admin user created successfully")
```

---

## 🚀 Running the Application

### Development Server

```bash
# Make sure virtual environment is activated
python run.py
```

Server will start at: **http://127.0.0.1:5000**

### Production Server (using Gunicorn)

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn wsgi:app --bind 0.0.0.0:5000 --workers 4
```

---

## 📱 Accessing the Application

1. **Login Page:** http://127.0.0.1:5000/auth/login
2. **Dashboard:** http://127.0.0.1:5000/
3. **Admin Users:** http://127.0.0.1:5000/admin/users/web (admin only)
4. **Profile:** Click on username dropdown → Profil

**Test Credentials (after creating admin user):**
- Username: `admin`
- Password: `Admin@123456`

---

## 🔐 User Roles & Permissions

### Role Access Matrix

| Feature | system_admin | network_engineer | data_scientist | noc_operator |
|---------|:------------:|:----------------:|:---------------:|:------------:|
| Dashboard | ✅ | ✅ | ✅ | ✅ |
| View Alerts | ✅ | ✅ | ❌ | ✅ |
| Predictions | ✅ | ✅ | ✅ | ❌ |
| Admin Panel | ✅ | ❌ | ❌ | ❌ |
| User Management | ✅ | ❌ | ❌ | ❌ |
| Change Password | ✅ | ✅ | ✅ | ✅ |

---

## 📡 API Endpoints (MS-4)

### Authentication

**POST /auth/login**
```bash
curl -X POST http://127.0.0.1:5000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=Admin@123456"
```

**POST /auth/logout**
```bash
curl -X POST http://127.0.0.1:5000/auth/logout \
  -H "Cookie: session=<session_cookie>"
```

### Admin APIs

**GET /admin/users**
```bash
curl -X GET http://127.0.0.1:5000/admin/users \
  -H "Cookie: session=<session_cookie>"
```

**POST /admin/users**
```bash
curl -X POST http://127.0.0.1:5000/admin/users \
  -H "Content-Type: application/json" \
  -H "Cookie: session=<session_cookie>" \
  -d '{
    "username": "john_doe",
    "password": "SecurePassword123",
    "role": "network_engineer"
  }'
```

**GET /admin/health**
```bash
curl -X GET http://127.0.0.1:5000/admin/health
```

**GET /admin/logs**
```bash
curl -X GET "http://127.0.0.1:5000/admin/logs?limit=50" \
  -H "Cookie: session=<session_cookie>"
```

---

## 📂 Project Structure

```
flask/
├── app/
│   ├── __init__.py                 # App factory
│   ├── extensions.py               # SQLAlchemy, LoginManager, Mail
│   ├── security.py                 # RBAC decorators
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                 # User model with password hashing
│   │   ├── monitoring.py           # Alert, Threshold, Prediction models
│   │   └── logs.py                 # IntegrationLog, ShapLog models
│   │
│   ├── blueprints/
│   │   ├── __init__.py
│   │   ├── auth.py                 # Login, logout, profile
│   │   ├── dashboard.py            # Main dashboard
│   │   └── admin.py                # User CRUD + MS-4 APIs
│   │
│   ├── templates/
│   │   ├── base.html               # Layout with sidebar/topbar
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   └── profile.html
│   │   ├── dashboard/
│   │   │   └── index.html
│   │   └── admin/
│   │       ├── users.html
│   │       ├── create_user.html
│   │       └── edit_user.html
│   │
│   └── static/
│       ├── css/
│       │   └── dashboard.css
│       └── js/
│           └── dashboard.js
│
├── config.py                       # Configuration (dev/prod/test)
├── run.py                          # Development server entry
├── wsgi.py                         # Production entry (Gunicorn)
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
└── README.md                       # This file
```

---

## 🔑 Security Features

- ✅ **Password Hashing:** Werkzeug PBKDF2 (industry standard)
- ✅ **Session Management:** Secure cookies with HTTPOnly flag
- ✅ **CSRF Protection:** Flask-WTF enabled on all forms
- ✅ **SQL Injection Prevention:** SQLAlchemy ORM parameterized queries
- ✅ **Role-Based Access Control:** Decorator-based route protection
- ✅ **Input Validation:** Server-side validation on all inputs
- ✅ **Error Handling:** No stack traces in production
- ✅ **Logical Deletion:** Users marked inactive instead of deleted

---

## 🧪 Testing the Application

### Test Scenarios

1. **Login Flow**
   - Navigate to `/auth/login`
   - Enter credentials
   - Verify redirect to dashboard
   - Check session cookie is set

2. **RBAC Test**
   - Login as non-admin user
   - Try to access `/admin/users/web`
   - Expect 403 Forbidden error

3. **User Management (Admin)**
   - Login as system_admin
   - Navigate to Admin → Utilisateurs
   - Create a new user
   - Edit user role
   - Verify user cannot login while inactive

4. **Dashboard**
   - View metric cards
   - Check alert and prediction display
   - Verify pagination on user list

5. **API Testing**
   - Use Postman or curl to test MS-4 endpoints
   - Verify authentication tokens
   - Check role-based access enforcement

---

## 🛠️ Troubleshooting

### Issue: "No module named 'app'"

**Solution:** Ensure you're in the project root directory and virtual environment is activated.

```bash
cd c:\Users\AymenJallouli\Desktop\flask
venv\Scripts\activate
```

### Issue: "MySQL connection failed"

**Solution:** Verify MySQL is running and credentials in `.env` are correct.

```bash
# Check MySQL connection
mysql -u root -p -e "SELECT 1"

# Update .env with correct credentials
DEV_DATABASE_URL=mysql+pymysql://root:your_password@127.0.0.1:3306/network_slicing
```

### Issue: "user table doesn't exist"

**Solution:** Run the SQL schema above to create required tables.

### Issue: "500 Error on login"

**Solution:** Check app logs for detailed error. Often due to missing `.env` configuration.

```bash
# Verify .env exists and has SECRET_KEY set
cat .env
```

---

## 📝 Environment Variables

| Variable | Required | Description |
|----------|:--------:|-------------|
| `FLASK_APP` | Yes | Entry point (should be `wsgi.py`) |
| `FLASK_ENV` | No | `development` or `production` |
| `SECRET_KEY` | Yes | Random key for session encryption |
| `DEV_DATABASE_URL` | Yes | MySQL connection string |
| `DATABASE_URL` | No | Production database URL |
| `MAIL_SERVER` | No | SMTP server for email (optional) |
| `MAIL_PORT` | No | SMTP port |
| `MAIL_USERNAME` | No | SMTP user |
| `MAIL_PASSWORD` | No | SMTP password |

---

## 🚀 Deployment Checklist

- [ ] Set `FLASK_ENV=production` in `.env`
- [ ] Generate strong `SECRET_KEY`: `python -c "import os; print(os.urandom(24).hex())"`
- [ ] Update database credentials for production
- [ ] Enable HTTPS/SSL in production
- [ ] Set `SESSION_COOKIE_SECURE=True`
- [ ] Configure email (SMTP) if needed
- [ ] Set up logging and monitoring
- [ ] Perform security audit
- [ ] Test all API endpoints
- [ ] Backup database before deployment

---

## 📞 Support

For issues or questions:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review Flask documentation: https://flask.palletsprojects.com
3. Check SQLAlchemy docs: https://docs.sqlalchemy.org

---

## 📄 License

Internal project for Network Slicing Dashboard system.

---

**Last Updated:** April 2026  
**Maintained by:** Development Team
