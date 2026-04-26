# MS-3: Dashboard & Alerts Service

**Network Slicing Microservice - Dashboard & Alerts (MS-3)**

A dedicated Flask microservice that provides real-time dashboard and alerts functionality for network slicing monitoring. This service aggregates data from MS-1 (Slice Management) and MS-2 (QoS Monitoring) to provide a comprehensive NOC operator interface.

## 🚀 Service Information

- **Service Name**: MS-3 Dashboard & Alerts Service
- **Version**: 1.0.0
- **Port**: 5003
- **Main File**: `ms3_dashboard_service.py`
- **Launcher**: `run_ms3_dashboard.py`

## 📋 Features

### API Endpoints (MS-3)

- **GET /ms3/health** - Health check for MS-3 service
- **GET /dashboard/slices** - Get status of all active network slices
- **GET /dashboard/alerts** - Get all active WARN/CRITICAL alerts
- **POST /dashboard/threshold** - Configure monitoring thresholds
- **POST /dashboard/alert/ack** - Acknowledge an alert
- **GET /dashboard/thresholds** - Get all configured thresholds
- **GET /api/qos-history** - Get historical QoS data for charts

### Dashboard Interface

- **Real-time Monitoring**: 30-second polling for live slice status and alerts
- **Alert Management**: Visual alerts with WARN/CRITICAL badges and acknowledge functionality
- **QoS Historical Charts**: Interactive charts showing bandwidth, latency, and packet loss trends
- **Threshold Configuration**: Dynamic threshold management for different metrics
- **Responsive Design**: Modern UI built with Tailwind CSS

## 🗄️ Database Schema

### Alerts Table
```sql
CREATE TABLE IF NOT EXISTS `alerts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `slice_id` varchar(50) DEFAULT NULL,
  `level` enum('WARN','CRITICAL') DEFAULT NULL,
  `message` text,
  `acknowledged` tinyint(1) DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

### Thresholds Table
```sql
CREATE TABLE IF NOT EXISTS `thresholds` (
  `id` int NOT NULL AUTO_INCREMENT,
  `metric` varchar(50) DEFAULT NULL,
  `warn_value` float DEFAULT NULL,
  `critical_value` float DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

## 🛠️ Installation & Setup

### 1. Install Dependencies
```bash
pip install -r ms3_requirements.txt
```

### 2. Setup MySQL Database
```sql
CREATE DATABASE network_slicing;
-- Import the schema files for alerts and thresholds tables
```

### 3. Configure Database Connection
Update the database URI in `ms3_dashboard_service.py`:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/network_slicing'
```

## 🚀 Running MS-3 Service

### Method 1: Using the Launcher (Recommended)
```bash
python run_ms3_dashboard.py
```

### Method 2: Direct Execution
```bash
python ms3_dashboard_service.py
```

### Service URLs
- **Dashboard UI**: http://localhost:5003/
- **Health Check**: http://localhost:5003/ms3/health
- **API Documentation**: See endpoints below

## 📡 API Usage Examples

### Health Check
```bash
curl http://localhost:5003/ms3/health
```

### Get All Active Slices
```bash
curl http://localhost:5003/dashboard/slices
```

### Get Active Alerts
```bash
curl http://localhost:5003/dashboard/alerts
```

### Configure Threshold
```bash
curl -X POST http://localhost:5003/dashboard/threshold \
  -H "Content-Type: application/json" \
  -d '{
    "metric": "bandwidth",
    "warn_value": 70.0,
    "critical_value": 50.0
  }'
```

### Acknowledge Alert
```bash
curl -X POST http://localhost:5003/dashboard/alert/ack \
  -H "Content-Type: application/json" \
  -d '{
    "alert_id": 1
  }'
```

## 🏗️ Architecture

### MS-3 Components

1. **Flask Application**: Main web server and API endpoints
2. **SQLAlchemy Models**: Database ORM for alerts and thresholds
3. **Dashboard UI**: Real-time web interface for NOC operators
4. **Chart.js**: Interactive QoS trend visualization
5. **Tailwind CSS**: Modern responsive styling

### MS-3 Data Flow

1. **MS-1 Integration**: Mock data for slice status and QoS metrics
   - Real implementation: `http://localhost:5001/slices`
2. **MS-2 Integration**: Historical QoS data aggregation
   - Real implementation: `http://localhost:5002/qos/history`
3. **Real-time Updates**: 30-second polling for live monitoring
4. **Alert Generation**: Threshold-based alert creation
5. **User Interaction**: Alert acknowledgment and threshold configuration

## ⚙️ Default Configuration

### Default Thresholds
- **Bandwidth**: Warn at 70 Mbps, Critical at 50 Mbps
- **Latency**: Warn at 20 ms, Critical at 50 ms
- **Packet Loss**: Warn at 2%, Critical at 5%
- **Jitter**: Warn at 3 ms, Critical at 5 ms

### Service Configuration
- **Port**: 5003
- **Debug Mode**: Enabled in development
- **Database**: MySQL (network_slicing)
- **Polling Interval**: 30 seconds

## 🔧 Development Notes

- MS-3 uses mock data for MS-1 and MS-2 integration
- In production, replace mock data with actual API calls to other microservices
- Database tables are created automatically on first run
- The dashboard supports real-time updates without page refresh
- All API responses include service identification for microservice architecture

## 🔒 Security Considerations

- Database credentials should be stored in environment variables
- API endpoints should be secured with authentication in production
- CORS policies should be configured for cross-origin requests
- Rate limiting should be implemented for public endpoints

## 📊 Monitoring Features

MS-3 Dashboard provides:

- **Connection Status**: Real-time connection indicator
- **Last Update Timestamp**: Shows when data was last refreshed
- **Alert Count Badge**: Visual indicator of active alerts
- **Slice Status Indicators**: Color-coded status for each slice
- **QoS Trend Visualization**: Historical performance charts

## 🚀 Future Enhancements

- WebSocket support for real-time updates
- Integration with actual MS-1 and MS-2 APIs
- User authentication and role-based access
- Historical alert logging and reporting
- Email/SMS alert notifications
- Advanced filtering and search capabilities
- Multi-tenant support
- API rate limiting and security

## 📝 Service Logs

MS-3 provides comprehensive logging:
- Service startup/shutdown events
- API request/response logging
- Database operation logging
- Error tracking and debugging
- Integration call logging (MS-1, MS-2)

## 🌐 Microservice Integration

MS-3 is designed to work with:
- **MS-1**: Slice Management Service (Port 5001)
- **MS-2**: QoS Monitoring Service (Port 5002)
- **MS-4**: (Future) Analytics Service
- **MS-5**: (Future) Notification Service

---

**MS-3 Dashboard & Alerts Service - Your Network Slicing Monitoring Hub** 🚀
