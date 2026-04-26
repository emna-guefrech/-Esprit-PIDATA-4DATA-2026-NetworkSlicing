# 🔄 Flux de Données - MS-2 Anomaly Detection Service

## 1️⃣ Flux de Détection d'Anomalies (POST /api/anomaly/detect)

```
CLIENT (e.g., Network Monitoring System)
  │
  ├─ Sends JSON with metrics
  │  {
  │    "slice_id": "slice_001",
  │    "features": {
  │      "bandwidth": 85.5,
  │      "latency": 12.3,
  │      "jitter": 2.1,
  │      "packet_loss": 1.0
  │    }
  │  }
  │
  ▼
FLASK API (routes/api.py)
  └─ @api_bp.route('/anomaly/detect', methods=['POST'])
     └─ detect_anomaly() function
        │
        ├─ Validate input
        │  └─ Check required fields
        │
        ├─ Call ConsensusService.detect()
        │  │
        │  ├─ IsolationForestService.predict_single()
        │  │  │
        │  │  └─ Loaded model (models/isolation_forest_model.pkl)
        │  │     ├─ Standardize features
        │  │     ├─ Compute anomaly score
        │  │     └─ Return: is_anomaly=False, score=0.34
        │  │
        │  ├─ AutoencoderService.predict_single()
        │  │  │
        │  │  └─ Loaded model (models/autoencoder_model.h5)
        │  │     ├─ Encode/Decode features
        │  │     ├─ Calculate reconstruction error
        │  │     └─ Return: is_anomaly=False, score=0.35
        │  │
        │  └─ Consensus Logic
        │     ├─ is_anomaly = IF AND AE (both must agree)
        │     ├─ score = (IF_score + AE_score) / 2
        │     ├─ confidence = score if anomaly else 1 - score
        │     └─ Return: {is_anomaly, score, confidence, methods{...}}
        │
        ├─ Save to Database
        │  │
        │  └─ Create Anomaly object
        │     ├── slice_id = "slice_001"
        │     ├── score = 0.3425
        │     ├── is_anomaly = False
        │     ├── method = "isolation_forest"
        │     ├── isolation_forest_score = 0.34
        │     ├── autoencoder_score = 0.35
        │     ├── features_json = "{...}"
        │     └── created_at = NOW()
        │
        └─ SQLAlchemy ORM
           └─ INSERT INTO anomalies (...)
              └─ MySQL Database
                 └─ Table: anomalies
                    ├─ id (AUTO_INCREMENT)
                    ├─ slice_id (INDEX)
                    ├─ score
                    ├─ is_anomaly
                    ├─ method
                    ├─ isolation_forest_score
                    ├─ autoencoder_score
                    ├─ features_json
                    └─ created_at (INDEX)
  │
  ▼
RESPONSE (JSON)
  {
    "success": true,
    "data": {
      "is_anomaly": false,
      "score": 0.3425,
      "confidence": 0.6575,
      "method": "isolation_forest",
      "anomaly_id": 123,
      "methods": {
        "isolation_forest": {"is_anomaly": false, "score": 0.34},
        "autoencoder": {"is_anomaly": false, "score": 0.35}
      }
    }
  }
```

---

## 2️⃣ Flux d'Historique (GET /api/anomaly/history)

```
CLIENT (Browser or API Consumer)
  │
  ├─ Request with filters
  │  GET /api/anomaly/history?slice_id=slice_001&is_anomaly=true&limit=20&offset=0
  │
  ▼
FLASK API (routes/api.py)
  └─ @api_bp.route('/anomaly/history', methods=['GET'])
     └─ get_anomaly_history() function
        │
        ├─ Parse Query Parameters
        │  ├─ slice_id = "slice_001"
        │  ├─ is_anomaly = True
        │  ├─ limit = 20
        │  └─ offset = 0
        │
        └─ Build Database Query
           └─ SQLAlchemy Query Builder
              │
              ├─ Base Query: SELECT * FROM anomalies
              │
              ├─ Filter 1: WHERE slice_id = 'slice_001'
              │  └─ Use INDEX on slice_id ✓
              │
              ├─ Filter 2: WHERE is_anomaly = True
              │
              ├─ Order: ORDER BY created_at DESC
              │  └─ Use INDEX on created_at ✓
              │
              ├─ Pagination: LIMIT 20 OFFSET 0
              │
              └─ Execute Query
                 └─ MySQL Database
                    └─ Return 20 records
  │
  ├─ Format Response
  │  └─ Loop through records
  │     ├─ Convert each Anomaly to dict
  │     ├─ Add confidence_level (HIGH/MEDIUM/LOW)
  │     ├─ Round scores to 4 decimals
  │     └─ Format dates to ISO 8601
  │
  ▼
RESPONSE (JSON)
  {
    "success": true,
    "data": {
      "total": 150,          # Total matching in DB
      "count": 20,           # Records returned
      "anomalies": [
        {
          "id": 42,
          "slice_id": "slice_001",
          "score": 0.8234,
          "is_anomaly": true,
          "method": "isolation_forest",
          "confidence_level": "HIGH",
          "isolation_forest_score": 0.8243,
          "autoencoder_score": 0.8225,
          "features": {...},
          "created_at": "2026-04-25T10:30:45"
        },
        ... 19 more records
      ]
    }
  }
```

---

## 3️⃣ Flux de Statistiques (GET /api/anomaly/stats)

```
CLIENT (Dashboard or Analytics)
  │
  ├─ Request stats
  │  GET /api/anomaly/stats?days=7
  │
  ▼
FLASK API (routes/api.py)
  └─ @api_bp.route('/anomaly/stats', methods=['GET'])
     └─ get_anomaly_stats() function
        │
        ├─ Calculate Time Window
        │  └─ start_date = NOW() - 7 days
        │
        └─ Query Database
           └─ Multiple aggregations
              │
              ├─ Query 1: All detections in range
              │  └─ SELECT * FROM anomalies WHERE created_at >= start_date
              │     └─ Return: [Anomaly1, Anomaly2, ...]
              │
              ├─ Query 2: By Slice
              │  └─ GROUP BY slice_id
              │     └─ Calculate: total, anomalies count, rate %
              │     └─ Result: {"slice_001": {total: 100, anomalies: 15, rate: 15%}}
              │
              ├─ Query 3: By Method
              │  └─ GROUP BY method WHERE is_anomaly=True
              │     └─ COUNT(*)
              │     └─ Result: {"isolation_forest": 10, "autoencoder": 5}
              │
              └─ Query 4: By Period (Daily)
                 └─ GROUP BY DATE(created_at)
                    └─ Calculate daily totals & anomalies
                    └─ Result: [
                         {date: "2026-04-24", total: 80, anomalies: 7, rate: 8.75%},
                         {date: "2026-04-25", total: 85, anomalies: 9, rate: 10.59%}
                       ]
  │
  ├─ Format Response
  │  ├─ Calculate rates: anomalies / total * 100
  │  ├─ Round percentages
  │  └─ Add metadata
  │
  ▼
RESPONSE (JSON)
  {
    "success": true,
    "data": {
      "total_detections": 500,
      "total_anomalies": 45,
      "anomaly_rate": 9.0,
      "days": 7,
      "by_slice": {
        "slice_001": {"total": 200, "anomalies": 15, "rate": 7.5},
        "slice_002": {"total": 180, "anomalies": 20, "rate": 11.11},
        "slice_003": {"total": 120, "anomalies": 10, "rate": 8.33}
      },
      "by_method": {
        "isolation_forest": 30,
        "autoencoder": 15
      },
      "by_period": [
        {"date": "2026-04-24", "total": 80, "anomalies": 7, "rate": 8.75},
        {"date": "2026-04-25", "total": 85, "anomalies": 9, "rate": 10.59}
      ]
    }
  }
```

---

## 4️⃣ Flux Dashboard Frontend (GET /)

```
USER (Open http://localhost:5000/)
  │
  ▼
BROWSER
  └─ Request GET /
     │
     ▼
FLASK (routes/web.py)
  └─ @web_bp.route('/')
     └─ index()
        └─ return render_template('index.html')
           │
           ▼
JINJA2 Template Engine
  └─ Render templates/index.html
     ├─ Extend base.html
     ├─ Include CSS: static/css/style.css
     ├─ Include JS: static/js/dashboard.js
     └─ Output: HTML
        │
        ▼
HTML Sent to Browser
  │
  ▼
BROWSER JavaScript Execution
  └─ dashboard.js loaded
     │
     ├─ addEventListener('DOMContentLoaded', loadDashboardData)
     │  │
     │  ├─ Fetch: GET /api/dashboard-data
     │  │  │
     │  │  └─ FLASK API (routes/web.py)
     │  │     └─ get_dashboard_data()
     │  │        └─ Query recent anomalies from DB
     │  │           └─ Return: slices, alerts, stats
     │  │
     │  └─ JavaScript processes response
     │     │
     │     ├─ displaySlices(data.slices)
     │     │  └─ Generate HTML for each slice
     │     │     ├─ <div class="slice-card">
     │     │     ├─ Status badge (ACTIVE/DEGRADED)
     │     │     ├─ Metrics (bandwidth, latency, etc.)
     │     │     └─ Insert into DOM
     │     │
     │     └─ displayAlerts(data.alerts)
     │        └─ Generate HTML for alerts
     │           └─ Show or hide "No alerts"
     │
     └─ setInterval(loadDashboardData, 10000)
        └─ Auto-refresh every 10 seconds
```

---

## 5️⃣ Flux de Démarrage Complet

```
USER STARTS APPLICATION
  │
  ├─ python init_db.py
  │  │
  │  ├─ create_app()
  │  │  │
  │  │  ├─ Load config from config.py
  │  │  ├─ Initialize SQLAlchemy
  │  │  ├─ Connect to MySQL
  │  │  └─ Create tables via db.create_all()
  │  │
  │  └─ add_test_data()
  │     └─ Generate 20 test records
  │        └─ INSERT INTO anomalies VALUES (...)
  │
  ├─ python run.py
  │  │
  │  ├─ Load .env variables
  │  ├─ create_app('development')
  │  ├─ Initialize db, CORS
  │  ├── Register blueprints
  │  │   ├─ api_bp (routes/api.py)
  │  │   └─ web_bp (routes/web.py)
  │  └─ app.run()
  │     └─ Listen on 0.0.0.0:5000
  │
  └─ FLASK APP RUNNING ✓
     │
     └─ Open http://localhost:5000 in browser
        │
        └─ Dashboard loads and shows data ✓
```

---

## 6️⃣ Architecture Globale

```
┌────────────────────────────────────────────────────────────────┐
│ USER/CLIENT LAYER                                              │
├────────────────────────────────────────────────────────────────┤
│ Browser (HTTP)          │  Network System (API)               │
│ ├─ Dashboard            │  ├─ Monitoring Tools               │
│ ├─ History              │  ├─ Network Slicing Manager        │
│ └─ Stats                │  └─ Other Microservices            │
└────────────────────────────────────────────────────────────────┘
              │                           │
              └───────────────────────────┘
                          │
           ┌──────────────▼───────────────┐
           │   FLASK APPLICATION          │
           │   (run.py, config.py)        │
           ├──────────────────────────────┤
           │   ROUTING LAYER              │
           │ ├─ routes/api.py (3 routes)  │
           │ └─ routes/web.py (4 routes)  │
           ├──────────────────────────────┤
           │   ML SERVICES LAYER          │
           │ ├─ Isolation Forest          │
           │ ├─ Autoencoder (TensorFlow)  │
           │ └─ Consensus Logic           │
           ├──────────────────────────────┤
           │   DATA LAYER                 │
           │ ├─ models/anomaly.py (ORM)   │
           │ └─ SQLAlchemy                │
           └───────────────┬──────────────┘
                           │
           ┌───────────────▼──────────────┐
           │   MYSQL DATABASE             │
           │ ├─ anomalies table           │
           │ ├─ alerts table              │
           │ ├─ predictions table         │
           │ ├─ thresholds table          │
           │ ├─ users table               │
           │ ├─ model_versions table      │
           │ ├─ integration_logs table    │
           │ └─ shap_logs table           │
           └──────────────────────────────┘
```

---

## 🎬 Scénario Complet: Détection & Visualisation

```
INSTANT T0: Network Monitoring System détecte une anomalie
│
├─ Envoie: POST /api/anomaly/detect
│  {
│    "slice_id": "slice_001",
│    "features": {"bandwidth": 15, "latency": 50, "jitter": 8, "packet_loss": 5}
│  }
│
▼
T0+50ms: ConsensusService traite
│
├─ Isolation Forest: ✓ Anomaly detected (score: 0.82)
├─ Autoencoder: ✓ Anomaly detected (score: 0.81)
├─ Consensus: ✓ BOTH agree → is_anomaly = TRUE
└─ DB Save: INSERT INTO anomalies (id=999, ...)

▼
T0+100ms: Response sent back
│
└─ {"success": true, "data": {"is_anomaly": true, "score": 0.815, ...}}

▼
T0+1s: User opens Dashboard (http://localhost:5000)
│
├─ Browser loads index.html
├─ dashboard.js calls GET /api/dashboard-data
├─ Flask queries: SELECT * FROM anomalies WHERE created_at > (NOW - 24h)
│  └─ Finds new record (id=999)
├─ JavaScript renders slices with updated status
│  └─ slice_001 shows: DEGRADED badge (orange)
│  └─ Metrics display: bandwidth=15 (red), latency=50 (red)
└─ Alerts box shows: "Anomalies detected for slice_001"

▼
T0+10s: Dashboard auto-refreshes
│
├─ Call GET /api/dashboard-data again
├─ If more anomalies: update display
└─ If status changed: update badge color

▼
User clicks "Historique" → /history page
│
├─ Page loads history.html
├─ User filters: slice_id=slice_001, is_anomaly=true
├─ history.js builds query: GET /api/anomaly/history?slice_id=slice_001&is_anomaly=true
├─ Flask returns anomalies matching filters (including id=999)
└─ Table displays with pagination

▼
User clicks "Statistiques" → /stats page
│
├─ Page loads stats.html
├─ stats.js calls GET /api/anomaly/stats?days=7
├─ Flask aggregates all detections last 7 days
│  ├─ total_anomalies: +1 (now includes id=999)
│  ├─ by_slice[slice_001]: +1 anomaly
│  └─ by_method[isolation_forest]: +1
├─ Chart updates showing new anomaly count
└─ Rates recalculated with new data
```

---

**Tous les flux fonctionnent en harmonie pour une détection et monitoring en temps réel ! 🚀**
