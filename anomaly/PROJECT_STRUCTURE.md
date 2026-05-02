# Project Structure & File Overview

## Complete Project Structure

```
anomalies/
│
├── 📄 Core Application Files
│   ├── run.py                          # Application entry point
│   ├── config.py                       # Flask configuration
│   ├── init_db.py                      # Database initialization script
│   ├── requirements.txt                # Python dependencies
│   └── .env                            # Environment variables
│
├── 📁 app/                             # Main Flask application package
│   ├── __init__.py                     # Application factory
│   │
│   ├── 📁 models/                      # Database models
│   │   ├── __init__.py
│   │   └── anomaly.py                  # Anomaly ORM model (SQLAlchemy)
│   │
│   ├── 📁 routes/                      # API & Web routes
│   │   ├── __init__.py
│   │   ├── api.py                      # 3 API endpoints
│   │   │   ├── POST /anomaly/detect
│   │   │   ├── GET /anomaly/history
│   │   │   └── GET /anomaly/stats
│   │   └── web.py                      # Frontend routes
│   │       ├── GET /                   # Dashboard
│   │       ├── GET /history            # History page
│   │       └── GET /stats              # Statistics page
│   │
│   ├── 📁 services/                    # ML services & business logic
│   │   ├── __init__.py
│   │   ├── isolation_forest_service.py # Isolation Forest detection
│   │   ├── autoencoder_service.py      # Autoencoder detection
│   │   └── consensus_service.py        # Consensus (IF + AE)
│   │
│   ├── 📁 templates/                   # Jinja2 HTML templates
│   │   ├── base.html                   # Base template with navbar
│   │   ├── index.html                  # Dashboard page
│   │   ├── history.html                # History & filtering
│   │   └── stats.html                  # Statistics & analytics
│   │
│   └── 📁 static/                      # Static assets
│       ├── 📁 css/
│       │   └── style.css               # Responsive dashboard styling
│       └── 📁 js/
│           ├── utils.js                # Shared utilities
│           ├── dashboard.js            # Dashboard interactivity
│           ├── history.js              # History page logic
│           └── stats.js                # Statistics & charts
│
├── 📄 Documentation & Configuration
│   ├── README.md                       # Main project documentation
│   ├── INSTALLATION.md                 # Step-by-step installation guide
│   ├── API_DOCUMENTATION.md            # Complete API reference
│   ├── DEPLOYMENT.md                   # Deployment options & guide
│   ├── .gitignore                      # Git ignore patterns
│   ├── Dockerfile                      # Docker image definition
│   ├── docker-compose.yml              # Multi-container setup
│   └── nginx.conf                      # Nginx reverse proxy config
│
├── 📄 Testing & Utilities
│   ├── test_api.py                     # API endpoint testing script
│   └── (models/)                       # ML model storage (created at runtime)
│
└── 📄 Network Slicing Database
    └── network_slicing.sql             # Complete DB schema (from attachments)
```

---

## File Descriptions

### Entry Points

| File | Purpose | Command |
|------|---------|---------|
| `run.py` | Start Flask application | `python run.py` |
| `init_db.py` | Initialize database with test data | `python init_db.py` |
| `test_api.py` | Test all API endpoints | `python test_api.py` |

### Configuration

| File | Purpose |
|------|---------|
| `config.py` | Flask configuration classes (Dev/Prod/Test) |
| `.env` | Environment variables (DATABASE_URL, SECRET_KEY, etc) |
| `requirements.txt` | Python package dependencies |
| `.gitignore` | Git exclusion patterns |

### Application Core

| Module | Classes/Functions | Purpose |
|--------|------------------|---------|
| `app/__init__.py` | `create_app()`, `db` | Flask app factory, SQLAlchemy init |
| `config.py` | `Config`, `DevelopmentConfig` | Configuration management |

### Data Models

| File | Class | Fields |
|------|-------|--------|
| `models/anomaly.py` | `Anomaly` | id, slice_id, score, is_anomaly, method, isolation_forest_score, autoencoder_score, features_json, created_at |

### API Endpoints

| File | Route | Method | Purpose |
|------|-------|--------|---------|
| `routes/api.py` | `/anomaly/detect` | POST | Detect anomaly from features |
| `routes/api.py` | `/anomaly/history` | GET | Query anomaly history with filters |
| `routes/api.py` | `/anomaly/stats` | GET | Get statistics by period/slice/method |
| `routes/web.py` | `/` | GET | Dashboard page |
| `routes/web.py` | `/history` | GET | History page |
| `routes/web.py` | `/stats` | GET | Statistics page |

### ML Services

| File | Class | Methods |
|------|-------|---------|
| `services/isolation_forest_service.py` | `IsolationForestService` | `train()`, `predict()`, `predict_single()` |
| `services/autoencoder_service.py` | `AutoencoderService` | `build()`, `train()`, `predict()`, `predict_single()` |
| `services/consensus_service.py` | `ConsensusAnomalyDetectionService` | `detect()`, `detect_batch()` |

### Frontend Assets

| File | Type | Content |
|------|------|---------|
| `static/css/style.css` | CSS | Responsive dashboard styling (blue/green/orange theme) |
| `static/js/utils.js` | JS | API utilities, formatting functions |
| `static/js/dashboard.js` | JS | Dashboard data loading & display |
| `static/js/history.js` | JS | History filtering & pagination |
| `static/js/stats.js` | JS | Statistics loading & chart rendering |

### Templates

| File | Purpose | Extends |
|------|---------|---------|
| `templates/base.html` | Base layout with navbar | - |
| `templates/index.html` | Dashboard with slices/alerts | base.html |
| `templates/history.html` | Anomaly history table | base.html |
| `templates/stats.html` | Statistics & charts | base.html |

### Deployment

| File | Purpose |
|------|---------|
| `Dockerfile` | Build Docker image for production |
| `docker-compose.yml` | Multi-container local development |
| `nginx.conf` | Nginx reverse proxy configuration |

### Documentation

| File | Audience | Content |
|------|----------|---------|
| `README.md` | Developers | Overview, architecture, usage |
| `INSTALLATION.md` | DevOps/Installers | Step-by-step setup instructions |
| `API_DOCUMENTATION.md` | API Consumers | Complete endpoint reference |
| `DEPLOYMENT.md` | DevOps/Cloud | Deployment on various platforms |

---

## Technology Stack

### Backend
- **Flask 2.3**: Web framework
- **SQLAlchemy 3.0**: ORM for database
- **scikit-learn 1.2**: Isolation Forest algorithm
- **TensorFlow 2.12**: Autoencoder neural network
- **mysql-connector-python 8.0**: MySQL driver

### Frontend
- **Jinja2**: Template engine
- **HTML5**: Markup
- **CSS3**: Styling (responsive, grid, flexbox)
- **JavaScript (Vanilla)**: Interactivity, API calls

### Database
- **MySQL 8.0**: Data persistence

### DevOps
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Reverse proxy & web server
- **Gunicorn**: WSGI application server

---

## Key Features by File

### Detection System (`services/`)
```
IsolationForest Model
├── Contamination: 5%
├── Score: 0-1 range
└── File: isolation_forest_service.py

Autoencoder Model
├── Layers: Dense(64→32→8→32→64)
├── Threshold: 95th percentile of reconstruction error
└── File: autoencoder_service.py

Consensus
├── Logic: Both models must agree (AND logic)
├── Score: Average of IF + AE scores
└── File: consensus_service.py
```

### API System (`routes/api.py`)
```
POST /anomaly/detect
├── Input: JSON with features
├── ML Processing: Consensus detection
├── DB Storage: Save to anomalies table
└── Response: Detection result + confidence

GET /anomaly/history
├── Filters: slice_id, is_anomaly, method, date range
├── Pagination: limit, offset
├── DB Query: SQLAlchemy with filters
└── Response: Anomaly records with metadata

GET /anomaly/stats
├── Aggregation: By slice, method, period
├── Time Range: Configurable (default 7 days)
├── Calculations: Counts, percentages, rates
└── Response: Statistical summaries
```

### Dashboard System (`templates/`, `static/`)
```
Frontend Architecture
├── Base Layout: Navbar, navigation, footer
├── Dashboard (index.html): Real-time slices & alerts
├── History (history.html): Searchable table with filters
├── Statistics (stats.html): Charts & aggregated data
└── Styling: Theme matching Network Slicing Dashboard
```

---

## Database Schema

### Main Table: anomalies
```sql
┌─────────────────────────────────────────┐
│ anomalies                               │
├─────────────────────────────────────────┤
│ id INT PRIMARY KEY AUTO_INCREMENT       │
│ slice_id VARCHAR(50) INDEX              │
│ score FLOAT                             │
│ is_anomaly BOOLEAN                      │
│ method VARCHAR(30)                      │
│ isolation_forest_score FLOAT            │
│ autoencoder_score FLOAT                 │
│ features_json TEXT                      │
│ created_at DATETIME INDEX               │
└─────────────────────────────────────────┘
```

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `FLASK_ENV` | development | Environment mode |
| `FLASK_DEBUG` | True | Debug mode |
| `FLASK_HOST` | 0.0.0.0 | Server host |
| `FLASK_PORT` | 5000 | Server port |
| `DATABASE_URL` | localhost | MySQL connection string |
| `SECRET_KEY` | dev-key | Flask session secret |
| `CONTAMINATION_RATE` | 0.05 | Isolation Forest contamination |
| `AUTOENCODER_ENCODING_DIM` | 8 | AE bottleneck dimension |

---

## Workflow Examples

### Normal Operation
```
1. Client POST /api/anomaly/detect with features
2. ConsensusService.detect() runs
3. IsolationForest + Autoencoder predict
4. Consensus logic combines results
5. Result saved to DB
6. Response returned to client
```

### Dashboard Usage
```
1. User opens http://localhost:5000
2. Dashboard.js calls /api/dashboard-data
3. Flask fetches recent anomalies from DB
4. HTML renders with live metrics
5. Auto-refresh every 10 seconds
```

### Historical Analysis
```
1. User filters history page (slice_id=slice_001)
2. History.js builds query with filters
3. Flask processes GET /api/anomaly/history?filters
4. SQLAlchemy applies filters to query
5. Results paginated and displayed
```

---

## Dependencies Installation

```bash
# All dependencies from requirements.txt
pip install -r requirements.txt

# Individual key packages
pip install Flask==2.3.2              # Web framework
pip install Flask-SQLAlchemy==3.0.5   # ORM
pip install scikit-learn==1.2.2       # ML
pip install tensorflow==2.12.0        # Deep learning
pip install mysql-connector-python    # DB driver
pip install gunicorn                  # Production server
pip install docker docker-compose     # Containerization
```

---

## File Size Overview

```
Models/                          ~10 MB (created at runtime)
├── isolation_forest_model.pkl   ~5 MB
└── autoencoder_model.h5         ~5 MB

Source Code                      ~200 KB
├── app/                         ~120 KB
├── templates/                   ~30 KB
└── static/                      ~50 KB

Documentation                    ~300 KB
├── README.md                    ~50 KB
├── INSTALLATION.md              ~100 KB
├── API_DOCUMENTATION.md         ~120 KB
└── DEPLOYMENT.md                ~50 KB
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-04-25 | Initial release with Isolation Forest + Autoencoder |
| - | - | Features: Dashboard, API, Consensus detection, History, Stats |

---

## Next Steps

1. **Install**: Follow `INSTALLATION.md`
2. **Test**: Run `python test_api.py`
3. **Deploy**: Choose option from `DEPLOYMENT.md`
4. **Monitor**: Check logs and dashboards
5. **Optimize**: Train models with production data

---

**Project Structure Documentation - MS-2 Anomaly Detection Service**
