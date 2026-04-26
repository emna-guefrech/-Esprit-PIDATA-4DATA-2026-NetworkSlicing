# API Documentation - Anomaly Detection Service MS-2

## Overview

The Anomaly Detection Service provides 3 RESTful endpoints for:
1. **Detecting anomalies** in network metrics
2. **Retrieving anomaly history** with advanced filtering
3. **Getting statistics** on anomalies per period

All endpoints return JSON responses with standardized success/error format.

---

## Base URL

```
http://localhost:5000/api
```

## Response Format

All API responses follow this format:

### Success Response
```json
{
  "success": true,
  "data": {
    ...
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message"
}
```

---

## Endpoint 1: Detect Anomaly

### POST /anomaly/detect

Detect if provided network metrics contain an anomaly using consensus between Isolation Forest and Autoencoder models.

#### Request

**Method**: `POST`

**Headers**:
```
Content-Type: application/json
```

**Body**:
```json
{
  "slice_id": "slice_001",
  "features": {
    "bandwidth": 85.5,
    "latency": 12.3,
    "jitter": 2.1,
    "packet_loss": 1.0
  }
}
```

**Parameters**:
- `slice_id` (string, required): Network slice identifier
- `features` (object, required): Network metrics object
  - `bandwidth` (number): Bandwidth in Mbps
  - `latency` (number): Latency in milliseconds
  - `jitter` (number): Jitter in milliseconds
  - `packet_loss` (number): Packet loss percentage

#### Response

**Status**: `201 Created` (success) or `400/500` (error)

**Body**:
```json
{
  "success": true,
  "data": {
    "is_anomaly": false,
    "score": 0.3421,
    "confidence": 0.6579,
    "method": "isolation_forest",
    "anomaly_id": 123,
    "methods": {
      "isolation_forest": {
        "is_anomaly": false,
        "score": 0.3412
      },
      "autoencoder": {
        "is_anomaly": false,
        "score": 0.3430
      }
    }
  }
}
```

**Response Fields**:
- `is_anomaly` (boolean): True if anomaly detected
- `score` (float): Consensus score (0.0 to 1.0)
- `confidence` (float): Confidence level (0.0 to 1.0)
- `method` (string): Primary detection method
- `anomaly_id` (integer): Database record ID
- `methods.isolation_forest.is_anomaly` (boolean): IF detection result
- `methods.isolation_forest.score` (float): IF score
- `methods.autoencoder.is_anomaly` (boolean): AE detection result
- `methods.autoencoder.score` (float): AE score

#### Examples

##### Normal Metrics
```bash
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
```

Response:
```json
{
  "success": true,
  "data": {
    "is_anomaly": false,
    "score": 0.3421,
    "confidence": 0.6579,
    "method": "isolation_forest",
    "anomaly_id": 1,
    "methods": {
      "isolation_forest": {"is_anomaly": false, "score": 0.3412},
      "autoencoder": {"is_anomaly": false, "score": 0.3430}
    }
  }
}
```

##### Anomalous Metrics
```bash
curl -X POST http://localhost:5000/api/anomaly/detect \
  -H "Content-Type: application/json" \
  -d '{
    "slice_id": "slice_003",
    "features": {
      "bandwidth": 15.0,
      "latency": 50.0,
      "jitter": 8.0,
      "packet_loss": 5.0
    }
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "is_anomaly": true,
    "score": 0.8234,
    "confidence": 0.8234,
    "method": "isolation_forest",
    "anomaly_id": 4,
    "methods": {
      "isolation_forest": {"is_anomaly": true, "score": 0.8243},
      "autoencoder": {"is_anomaly": true, "score": 0.8225}
    }
  }
}
```

#### Error Cases

**Missing features**:
```bash
curl -X POST http://localhost:5000/api/anomaly/detect \
  -H "Content-Type: application/json" \
  -d '{"slice_id": "slice_001"}'
```

Response (400 Bad Request):
```json
{
  "success": false,
  "error": "Manquant: \"features\" requis"
}
```

---

## Endpoint 2: Get Anomaly History

### GET /anomaly/history

Retrieve historical anomaly detections with advanced filtering and pagination.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `slice_id` | string | No | - | Filter by network slice |
| `is_anomaly` | boolean | No | - | Filter by anomaly status (true/false) |
| `method` | string | No | - | Filter by detection method |
| `start_date` | datetime | No | - | Start date (ISO format: YYYY-MM-DD HH:MM:SS) |
| `end_date` | datetime | No | - | End date (ISO format: YYYY-MM-DD HH:MM:SS) |
| `limit` | integer | No | 100 | Max records (1-500) |
| `offset` | integer | No | 0 | Pagination offset |

#### Request Examples

**Get all anomalies (paginated)**:
```bash
GET /api/anomaly/history?limit=50&offset=0
```

**Get anomalies for specific slice**:
```bash
GET /api/anomaly/history?slice_id=slice_001
```

**Get detected anomalies only**:
```bash
GET /api/anomaly/history?is_anomaly=true&limit=100
```

**Get anomalies for date range**:
```bash
GET /api/anomaly/history?start_date=2026-04-20%2008:00:00&end_date=2026-04-25%2010:00:00
```

**Get anomalies detected by Isolation Forest**:
```bash
GET /api/anomaly/history?method=isolation_forest&limit=25
```

**Complex filter**:
```bash
GET /api/anomaly/history?slice_id=slice_002&is_anomaly=true&method=autoencoder&limit=50
```

#### Response

**Status**: `200 OK`

**Body**:
```json
{
  "success": true,
  "data": {
    "total": 150,
    "count": 10,
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
        "features": {
          "bandwidth": 15.0,
          "latency": 50.0,
          "jitter": 8.0,
          "packet_loss": 5.0
        },
        "created_at": "2026-04-25T10:30:45.123456"
      },
      ...
    ]
  }
}
```

**Response Fields**:
- `total` (integer): Total matching records in database
- `count` (integer): Count of returned records
- `anomalies` (array): Array of anomaly records
  - `id`: Database record ID
  - `slice_id`: Network slice identifier
  - `score`: Consensus score
  - `is_anomaly`: Anomaly flag
  - `method`: Detection method used
  - `confidence_level`: HIGH / MEDIUM / LOW
  - `isolation_forest_score`: IF specific score
  - `autoencoder_score`: AE specific score
  - `features`: Original network metrics
  - `created_at`: Detection timestamp

#### Examples

```bash
# Get last 20 anomalies
curl "http://localhost:5000/api/anomaly/history?limit=20&offset=0"

# Get anomalies for slice_001 in the last 7 days
curl "http://localhost:5000/api/anomaly/history?slice_id=slice_001&limit=100"

# Get all detected anomalies (is_anomaly=true)
curl "http://localhost:5000/api/anomaly/history?is_anomaly=true&limit=50"

# With URL encoding for dates
curl "http://localhost:5000/api/anomaly/history?start_date=2026-04-20%2000%3A00%3A00&end_date=2026-04-25%2023%3A59%3A59"
```

---

## Endpoint 3: Get Anomaly Statistics

### GET /anomaly/stats

Get aggregated statistics on anomalies by period, slice, and detection method.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `slice_id` | string | No | - | Filter by slice |
| `period` | string | No | jour | Time period (jour/semaine/mois) |
| `days` | integer | No | 7 | Number of days to analyze |

#### Request Examples

**Get last 7 days stats**:
```bash
GET /api/anomaly/stats?days=7
```

**Get stats for specific slice (14 days)**:
```bash
GET /api/anomaly/stats?slice_id=slice_001&days=14
```

**Get monthly stats**:
```bash
GET /api/anomaly/stats?period=mois&days=30
```

#### Response

**Status**: `200 OK`

**Body**:
```json
{
  "success": true,
  "data": {
    "total_detections": 500,
    "total_anomalies": 45,
    "anomaly_rate": 9.0,
    "period": "jour",
    "days": 7,
    "by_slice": {
      "slice_001": {
        "total": 200,
        "anomalies": 15,
        "rate": 7.5
      },
      "slice_002": {
        "total": 180,
        "anomalies": 20,
        "rate": 11.11
      },
      "slice_003": {
        "total": 120,
        "anomalies": 10,
        "rate": 8.33
      }
    },
    "by_method": {
      "isolation_forest": 30,
      "autoencoder": 15
    },
    "by_period": [
      {
        "date": "2026-04-24",
        "total": 80,
        "anomalies": 7,
        "rate": 8.75
      },
      {
        "date": "2026-04-25",
        "total": 85,
        "anomalies": 9,
        "rate": 10.59
      }
    ]
  }
}
```

**Response Fields**:
- `total_detections`: Total number of detections in period
- `total_anomalies`: Number of detected anomalies
- `anomaly_rate`: Percentage of anomalies
- `period`: Requested period
- `days`: Number of days analyzed
- `by_slice`: Stats grouped by slice_id
  - `total`: Total detections for this slice
  - `anomalies`: Number of anomalies for this slice
  - `rate`: Percentage of anomalies
- `by_method`: Count of anomalies by detection method
- `by_period`: Daily/weekly breakdown
  - `date`: Date identifier
  - `total`: Detections on this date
  - `anomalies`: Anomalies on this date
  - `rate`: Anomaly percentage

#### Examples

```bash
# Last 7 days
curl "http://localhost:5000/api/anomaly/stats?days=7"

# Last 30 days for slice_001
curl "http://localhost:5000/api/anomaly/stats?slice_id=slice_001&days=30"

# Weekly stats
curl "http://localhost:5000/api/anomaly/stats?period=semaine&days=14"
```

---

## HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Successful GET request |
| 201 | Created | Successful POST request |
| 400 | Bad Request | Invalid parameters or missing required fields |
| 404 | Not Found | Resource not found |
| 500 | Server Error | Internal server error |

---

## Rate Limiting & Best Practices

### Recommendations

1. **Batch requests**: Send multiple metrics in one request when possible
2. **Use pagination**: Always specify `limit` and `offset` for large queries
3. **Add filters**: Use `slice_id`, date range to narrow results
4. **Cache results**: Store history queries for 5-10 minutes
5. **Monitor anomalies**: Use WebSocket for real-time updates (future)

### Performance Tips

- **Detect**: ~50-100ms per request
- **History**: ~200-500ms with filters
- **Stats**: ~500-1000ms depending on date range

---

## Error Handling

### Network Error
```json
{
  "success": false,
  "error": "Connection to database failed"
}
```

### Invalid Date Format
```json
{
  "success": false,
  "error": "Format de date invalide pour start_date: invalid"
}
```

### Database Error
```json
{
  "success": false,
  "error": "Database query error"
}
```

---

## Integration Examples

### Python (requests)
```python
import requests

# Detect anomaly
response = requests.post(
    'http://localhost:5000/api/anomaly/detect',
    json={
        'slice_id': 'slice_001',
        'features': {
            'bandwidth': 85.5,
            'latency': 12.3,
            'jitter': 2.1,
            'packet_loss': 1.0
        }
    }
)

data = response.json()
if data['success']:
    print(f"Anomaly: {data['data']['is_anomaly']}")
    print(f"Score: {data['data']['score']}")
```

### JavaScript (fetch)
```javascript
// Detect anomaly
const response = await fetch('/api/anomaly/detect', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    slice_id: 'slice_001',
    features: {
      bandwidth: 85.5,
      latency: 12.3,
      jitter: 2.1,
      packet_loss: 1.0
    }
  })
});

const data = await response.json();
if (data.success) {
  console.log(`Anomaly: ${data.data.is_anomaly}`);
  console.log(`Score: ${data.data.score}`);
}
```

### cURL
```bash
# Detect
curl -X POST http://localhost:5000/api/anomaly/detect \
  -H "Content-Type: application/json" \
  -d '{"slice_id":"slice_001","features":{"bandwidth":85.5,"latency":12.3,"jitter":2.1,"packet_loss":1.0}}'

# History
curl "http://localhost:5000/api/anomaly/history?limit=10&is_anomaly=true"

# Stats
curl "http://localhost:5000/api/anomaly/stats?days=7"
```

---

## API Versioning

Current version: **v1** (implicit in base URL)

Future versions will use: `/api/v2/anomaly/detect`

---

**API Documentation - MS-2 Anomaly Detection Service**
