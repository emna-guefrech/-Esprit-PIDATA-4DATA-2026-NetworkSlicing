# Installation Guide - Anomaly Detection Service MS-2

## Quick Start (5 minutes)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Database

Make sure MySQL is running, then:

```bash
# Create the database
mysql -u root < path/to/network_slicing.sql

# Or create manually:
mysql -u root
mysql> CREATE DATABASE network_slicing;
mysql> USE network_slicing;
mysql> SOURCE network_slicing.sql;
```

### 3. Configure Environment

Edit `.env` file:

```bash
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/network_slicing
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_PORT=5000
```

### 4. Initialize Database

```bash
python init_db.py
```

### 5. Run the Application

```bash
python run.py
```

Visit: **http://localhost:5000**

---

## Detailed Installation

### Prerequisites

- **Python**: 3.8 or higher
  ```bash
  python --version
  ```

- **MySQL**: 8.0 or higher
  ```bash
  mysql --version
  ```

- **pip**: Package manager for Python
  ```bash
  pip --version
  ```

### Step 1: Clone/Create Project

```bash
cd c:\Users\MSI\Desktop\4eme Data\PI data\anomalies
```

### Step 2: Create Virtual Environment

#### Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

#### Linux/Mac:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Python Packages

```bash
pip install -r requirements.txt
```

This will install:
- Flask 2.3.2
- Flask-SQLAlchemy 3.0.5
- scikit-learn 1.2.2 (Isolation Forest)
- TensorFlow 2.12.0 (Autoencoder)
- mysql-connector-python 8.0.33
- And other dependencies

### Step 4: Setup MySQL Database

#### Option A: Using SQL Dump File

```bash
mysql -u root -p < network_slicing.sql
```

Enter your MySQL password when prompted.

#### Option B: Manual Setup

```bash
# Connect to MySQL
mysql -u root -p

# In MySQL CLI:
CREATE DATABASE IF NOT EXISTS network_slicing;
USE network_slicing;

-- Create tables (copy contents from network_slicing.sql)
```

#### Option C: Verify Database Created

```bash
mysql -u root -p -e "SHOW DATABASES;"
```

You should see `network_slicing` in the list.

### Step 5: Configure Environment Variables

Create/Edit `.env` file in the project root:

```bash
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Database Configuration
DATABASE_URL=mysql+pymysql://root:@localhost:3306/network_slicing
# Format: mysql+pymysql://username:password@host:port/database

# For authentication:
# DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/network_slicing

# Flask Settings
SECRET_KEY=dev-secret-key-change-in-production

# ML Configuration
CONTAMINATION_RATE=0.05
AUTOENCODER_ENCODING_DIM=8
AUTOENCODER_THRESHOLD=0.5
```

### Step 6: Initialize Database Schema

```bash
python init_db.py
```

This script will:
- Create all database tables
- Add sample test data (20 records)
- Display progress

Expected output:
```
Creating database tables...
✓ Tables created successfully

Adding test data...
  ✓ Added: slice_001 - Anomaly: False (score: 0.324)
  ✓ Added: slice_002 - Anomaly: True (score: 0.823)
  ... (18 more records)

Database initialization completed!
```

### Step 7: Run the Application

```bash
python run.py
```

Expected output:
```
╔════════════════════════════════════════════════════════════════╗
║  Anomaly Detection Service - MS-2                             ║
║  Flask Application Starting...                                ║
╠════════════════════════════════════════════════════════════════╣
║  Host: 0.0.0.0                                                 ║
║  Port: 5000                                                    ║
║  Debug: True                                                   ║
║  Environment: development                                      ║
╠════════════════════════════════════════════════════════════════╣
║  Dashboard:     http://0.0.0.0:5000                            ║
║  API Docs:      http://0.0.0.0:5000/api/anomaly/detect       ║
╚════════════════════════════════════════════════════════════════╝
```

Open your browser: **http://localhost:5000**

---

## Verification & Testing

### Test 1: Check Dashboard

1. Open browser: http://localhost:5000
2. You should see:
   - Network Slicing Dashboard
   - Active slices with metrics
   - Recent anomalies

### Test 2: Test API Endpoints

```bash
python test_api.py
```

This will:
- Send test data to `/api/anomaly/detect`
- Query `/api/anomaly/history`
- Get stats from `/api/anomaly/stats`

Expected output:
```
======================================================================
Anomaly Detection Service - API Testing
======================================================================

[TEST 1] POST /api/anomaly/detect
----------------------------------------------------------------------
✓ Test case 1: SUCCESS
  Slice ID: slice_001
  Is Anomaly: False
  Score: 0.3421
  Confidence: 0.6579
  Method: isolation_forest

... (more tests)
```

### Test 3: Manual API Test (cURL)

```bash
# Detect an anomaly
curl -X POST http://localhost:5000/api/anomaly/detect \
  -H "Content-Type: application/json" \
  -d '{
    "slice_id": "slice_001",
    "features": {
      "bandwidth": 85.5,
      "latency": 12.3,
      "jitter": 2.1,
      "packet_loss": 1.0
    }
  }'

# Get history
curl http://localhost:5000/api/anomaly/history?limit=10

# Get statistics
curl http://localhost:5000/api/anomaly/stats?days=7
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'flask'"

**Solution**: Activate virtual environment and install dependencies
```bash
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Issue: "No module named 'mysql'"

**Solution**: Install MySQL connector
```bash
pip install mysql-connector-python==8.0.33
```

### Issue: "Can't connect to MySQL server"

**Solutions**:
1. Check MySQL is running:
   ```bash
   mysql --version
   mysql -u root -p -e "SELECT 1"
   ```

2. Verify DATABASE_URL in `.env`:
   ```bash
   DATABASE_URL=mysql+pymysql://root:password@localhost:3306/network_slicing
   ```

3. Ensure database exists:
   ```bash
   mysql -u root -p -e "SHOW DATABASES;"
   ```

### Issue: "Database 'network_slicing' doesn't exist"

**Solution**: Create the database
```bash
mysql -u root -p < network_slicing.sql
# Or manually:
mysql -u root -p -e "CREATE DATABASE network_slicing;"
```

### Issue: Port 5000 already in use

**Solution**: Change port in `.env`
```bash
FLASK_PORT=5001
```

Then access: http://localhost:5001

### Issue: "ModuleNotFoundError: No module named 'tensorflow'"

**Solution**: Install TensorFlow (may take a while)
```bash
pip install tensorflow==2.12.0
```

### Issue: Dashboard shows "Loading..." forever

**Solution**: Check browser console (F12)
1. Make sure API is responding
2. Check CORS is enabled (it is by default)
3. Check Flask is running without errors

---

## Project Structure Verification

After installation, verify the structure:

```
anomalies/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── templates/
│   └── static/
├── config.py
├── run.py
├── init_db.py
├── test_api.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

---

## Configuration Options

### Development Mode

Edit `.env`:
```bash
FLASK_ENV=development
FLASK_DEBUG=True
```

Features:
- Auto-reload on code changes
- Detailed error messages
- SQL queries logged

### Production Mode

Edit `.env`:
```bash
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

Recommendations:
- Use a production WSGI server (Gunicorn, uWSGI)
- Set strong SECRET_KEY
- Use SSL/HTTPS
- Hide sensitive configuration

### Production Deployment with Gunicorn

```bash
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app

# Or with multiple workers
gunicorn -w 4 -b 127.0.0.1:5000 --access-logfile - --error-logfile - run:app
```

---

## Data Management

### Backup Database

```bash
mysqldump -u root -p network_slicing > backup.sql
```

### Restore Database

```bash
mysql -u root -p network_slicing < backup.sql
```

### Clear Test Data

```bash
mysql -u root -p
USE network_slicing;
TRUNCATE TABLE anomalies;
```

---

## Performance Tuning

### Database Optimization

```sql
-- Create indexes for better performance
CREATE INDEX idx_slice_id ON anomalies(slice_id);
CREATE INDEX idx_created_at ON anomalies(created_at);
CREATE INDEX idx_is_anomaly ON anomalies(is_anomaly);
```

### ML Model Optimization

For better anomaly detection:

1. **Train models with historical data**:
   ```python
   from app.services import ConsensusAnomalyDetectionService
   service = ConsensusAnomalyDetectionService()
   # Load your training data
   service.isolation_forest.train(X_train)
   service.autoencoder.train(X_train)
   ```

2. **Adjust contamination rate** in `.env`:
   ```bash
   CONTAMINATION_RATE=0.1  # For 10% anomalies
   ```

---

## Next Steps

1. ✅ **Explore Dashboard**: http://localhost:5000
2. ✅ **Check API**: Test endpoints with `test_api.py`
3. ✅ **Review Logs**: Monitor Flask output for errors
4. ✅ **Train Models**: With your own data for better results
5. ✅ **Deploy**: Use Gunicorn for production

---

## Support & Debugging

### Enable Detailed Logging

Edit `app/__init__.py` and set:
```python
app.logger.setLevel(logging.DEBUG)
```

### Monitor Database

```bash
# Connect to MySQL and monitor queries
GENERAL_LOG=1;
SELECT * FROM mysql.general_log;
```

### Check API Health

```bash
curl -s http://localhost:5000/api/anomaly/stats | jq .
```

---

## Additional Resources

- **Flask Documentation**: https://flask.palletsprojects.com/
- **SQLAlchemy ORM**: https://docs.sqlalchemy.org/
- **scikit-learn**: https://scikit-learn.org/
- **TensorFlow**: https://www.tensorflow.org/
- **MySQL**: https://dev.mysql.com/

---

**Installation Guide - MS-2 Anomaly Detection Service**
