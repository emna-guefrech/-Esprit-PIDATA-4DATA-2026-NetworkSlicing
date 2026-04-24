# API Testing Guide - MS-4 Endpoints

This guide provides step-by-step instructions to test all MS-4 API endpoints for the Network Slicing Dashboard.

---

## Prerequisites

- Application running on `http://127.0.0.1:5000`
- **curl** installed (or Postman)
- MySQL database populated with test data
- Admin user created for testing

---

## Test 1: Health Check

**Endpoint:** `GET /admin/health`  
**Auth Required:** No  
**Purpose:** Verify system status

### Using curl

```bash
curl -i -X GET http://127.0.0.1:5000/admin/health
```

### Expected Response (200 OK)

```json
{
  "status": "success",
  "data": {
    "service": "Network Slicing Dashboard",
    "version": "1.0.0",
    "database": "healthy",
    "timestamp": "2026-04-24T14:30:45.123456"
  }
}
```

### Troubleshooting

- **database: "unhealthy"** → Check MySQL connection in `.env`
- **500 Error** → Check Flask logs for exceptions

---

## Test 2: Login

**Endpoint:** `POST /auth/login`  
**Auth Required:** No  
**Purpose:** Authenticate user and get session cookie

### Using curl

```bash
# Replace with your test credentials
curl -i -X POST http://127.0.0.1:5000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=Admin%40123456&remember=on" \
  -c cookies.txt
```

### Expected Response (302 Redirect)

```
HTTP/1.1 302 FOUND
Location: http://127.0.0.1:5000/
Set-Cookie: session=<session_token>; Path=/; HttpOnly
```

**Note:** The response code is 302 (redirect) because login succeeds and redirects to dashboard. The session cookie is automatically saved in `cookies.txt`.

### Using Postman

1. **New Request** → POST
2. **URL:** `http://127.0.0.1:5000/auth/login`
3. **Body** → form-data:
   - `username`: admin
   - `password`: Admin@123456
   - `remember`: on
4. **Settings** → Enable "Follow redirects"
5. **Send**

---

## Test 3: Get Users List (API)

**Endpoint:** `GET /admin/users`  
**Auth Required:** Yes (system_admin)  
**Purpose:** Retrieve all users in JSON format

### Using curl (with cookies)

```bash
curl -i -X GET http://127.0.0.1:5000/admin/users \
  -b cookies.txt
```

### Expected Response (200 OK)

```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "username": "admin",
      "role": "system_admin",
      "is_active": true,
      "created_at": "2026-04-24T10:00:00"
    },
    {
      "id": 2,
      "username": "john_doe",
      "role": "network_engineer",
      "is_active": true,
      "created_at": "2026-04-24T12:30:00"
    }
  ]
}
```

### Error Scenarios

**403 Forbidden** (non-admin user)
```json
{
  "error": "Insufficient permissions"
}
```

**401 Unauthorized** (not logged in)
```json
{
  "error": "Unauthorized"
}
```

---

## Test 4: Create User (API)

**Endpoint:** `POST /admin/users`  
**Auth Required:** Yes (system_admin)  
**Purpose:** Create new user via API

### Using curl

```bash
curl -i -X POST http://127.0.0.1:5000/admin/users \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "username": "jane_engineer",
    "password": "SecurePassword123456",
    "role": "network_engineer"
  }'
```

### Expected Response (201 Created)

```json
{
  "status": "success",
  "message": "User jane_engineer created successfully",
  "data": {
    "id": 3,
    "username": "jane_engineer",
    "role": "network_engineer"
  }
}
```

### Using Postman

1. **New Request** → POST
2. **URL:** `http://127.0.0.1:5000/admin/users`
3. **Headers:**
   - `Content-Type: application/json`
4. **Body** → raw (JSON):
   ```json
   {
     "username": "jane_engineer",
     "password": "SecurePassword123456",
     "role": "network_engineer"
   }
   ```
5. **Send**

### Error Scenarios

**400 Bad Request** (missing fields)
```json
{
  "status": "error",
  "message": "Missing required fields"
}
```

**409 Conflict** (user already exists)
```json
{
  "status": "error",
  "message": "User already exists"
}
```

**400 Bad Request** (invalid role)
```json
{
  "status": "error",
  "message": "Invalid role. Must be one of: system_admin, network_engineer, data_scientist, noc_operator"
}
```

---

## Test 5: Get Integration Logs (API)

**Endpoint:** `GET /admin/logs`  
**Auth Required:** Yes (system_admin)  
**Purpose:** Retrieve microservice integration logs

### Using curl

```bash
# Get last 50 logs (default)
curl -i -X GET "http://127.0.0.1:5000/admin/logs?limit=50" \
  -b cookies.txt

# Get last 20 logs
curl -i -X GET "http://127.0.0.1:5000/admin/logs?limit=20" \
  -b cookies.txt
```

### Expected Response (200 OK)

```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "service": "ML_Service",
      "endpoint": "/predict",
      "status_code": 200,
      "latency_ms": 245,
      "created_at": "2026-04-24T14:25:30"
    },
    {
      "id": 2,
      "service": "Alert_Service",
      "endpoint": "/alerts/acknowledge",
      "status_code": 201,
      "latency_ms": 120,
      "created_at": "2026-04-24T14:20:15"
    }
  ]
}
```

---

## Test 6: Logout

**Endpoint:** `POST /auth/logout`  
**Auth Required:** Yes  
**Purpose:** Clear session and logout user

### Using curl

```bash
curl -i -X POST http://127.0.0.1:5000/auth/logout \
  -b cookies.txt \
  -c cookies.txt
```

### Expected Response (302 Redirect)

```
HTTP/1.1 302 FOUND
Location: http://127.0.0.1:5000/auth/login
Set-Cookie: session=null; Expires=...
```

### Verify Logout

Try to access a protected route after logout:

```bash
curl -i -X GET http://127.0.0.1:5000/admin/users \
  -b cookies.txt
```

Should return **401 Unauthorized** or redirect to login.

---

## Complete Test Sequence (Bash Script)

Save as `test_api.sh`:

```bash
#!/bin/bash

BASE_URL="http://127.0.0.1:5000"
COOKIES_FILE="cookies.txt"
USERNAME="admin"
PASSWORD="Admin@123456"

echo "=== Network Slicing Dashboard - MS-4 API Tests ==="
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
echo "---"
curl -s -X GET "$BASE_URL/admin/health" | python -m json.tool
echo ""
echo ""

# Test 2: Login
echo "Test 2: Login"
echo "---"
curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$USERNAME&password=$PASSWORD&remember=on" \
  -c $COOKIES_FILE \
  -L | head -20
echo "Session saved in $COOKIES_FILE"
echo ""
echo ""

# Test 3: Get Users
echo "Test 3: Get Users List (API)"
echo "---"
curl -s -X GET "$BASE_URL/admin/users" \
  -b $COOKIES_FILE | python -m json.tool
echo ""
echo ""

# Test 4: Create User
echo "Test 4: Create New User (API)"
echo "---"
curl -s -X POST "$BASE_URL/admin/users" \
  -H "Content-Type: application/json" \
  -b $COOKIES_FILE \
  -d '{
    "username": "test_user_'$(date +%s)'",
    "password": "TestPassword123456",
    "role": "network_engineer"
  }' | python -m json.tool
echo ""
echo ""

# Test 5: Get Logs
echo "Test 5: Get Integration Logs (API)"
echo "---"
curl -s -X GET "$BASE_URL/admin/logs?limit=20" \
  -b $COOKIES_FILE | python -m json.tool
echo ""
echo ""

# Test 6: Logout
echo "Test 6: Logout"
echo "---"
curl -s -X POST "$BASE_URL/auth/logout" \
  -b $COOKIES_FILE | head -5
echo ""
echo "Tests completed!"

# Cleanup
rm -f $COOKIES_FILE
```

### Run Tests

```bash
chmod +x test_api.sh
./test_api.sh
```

---

## Test Access Control

### Test RBAC - Non-Admin Access

1. **Create non-admin user:**
   ```bash
   curl -X POST http://127.0.0.1:5000/admin/users \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{
       "username": "engineer1",
       "password": "EngPass123456",
       "role": "network_engineer"
     }'
   ```

2. **Login as non-admin:**
   ```bash
   curl -X POST http://127.0.0.1:5000/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=engineer1&password=EngPass123456" \
     -c engineer_cookies.txt
   ```

3. **Try to access admin endpoint (should fail):**
   ```bash
   curl -i -X GET http://127.0.0.1:5000/admin/users \
     -b engineer_cookies.txt
   ```
   
   Expected: **403 Forbidden**

---

## Postman Collection Import

### Create Collection from Scratch

1. **New Collection** → Name: "Network Slicing Dashboard"

2. **Add Requests:**

   **Health Check**
   - Method: GET
   - URL: `{{base_url}}/admin/health`
   
   **Login**
   - Method: POST
   - URL: `{{base_url}}/auth/login`
   - Body: form-data (username, password, remember)
   - Tests: Save session cookie
   
   **Get Users**
   - Method: GET
   - URL: `{{base_url}}/admin/users`
   - Auth: Inherit from collection
   
   **Create User**
   - Method: POST
   - URL: `{{base_url}}/admin/users`
   - Body: raw JSON
   
   **Get Logs**
   - Method: GET
   - URL: `{{base_url}}/admin/logs?limit=50`
   
   **Logout**
   - Method: POST
   - URL: `{{base_url}}/auth/logout`

3. **Environment Variables:**
   - `base_url`: http://127.0.0.1:5000
   - `username`: admin
   - `password`: Admin@123456

---

## Common Issues & Solutions

### Issue: "Method not allowed" (405)

**Cause:** Using wrong HTTP method  
**Solution:** Verify endpoint expects POST/GET

### Issue: "Unauthorized" (401)

**Cause:** Session expired or cookies not included  
**Solution:** 
```bash
# Re-login
curl -X POST http://127.0.0.1:5000/auth/login \
  -c cookies.txt \
  -d "username=admin&password=..."
```

### Issue: "Database connection failed"

**Cause:** MySQL not running or wrong connection string  
**Solution:**
```bash
# Verify MySQL is running
mysql -u root -p -e "SELECT 1"

# Update .env with correct credentials
DEV_DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/network_slicing
```

### Issue: JSON parsing error in curl response

**Solution:** Add JSON formatting:
```bash
curl -s -X GET http://127.0.0.1:5000/admin/users \
  -b cookies.txt | python -m json.tool
```

---

## Performance Testing

### Load Test Health Endpoint

```bash
# Apache Bench: 100 requests, 10 concurrent
ab -n 100 -c 10 http://127.0.0.1:5000/admin/health

# Results show: requests/sec, mean time per request, etc.
```

### Concurrent User Creation

```bash
for i in {1..10}; do
  curl -s -X POST http://127.0.0.1:5000/admin/users \
    -H "Content-Type: application/json" \
    -b cookies.txt \
    -d "{\"username\":\"user_$i\",\"password\":\"Pass123456\",\"role\":\"network_engineer\"}" &
done
wait
echo "10 users created"
```

---

## Documentation References

- **Flask-Login**: https://flask-login.readthedocs.io/
- **SQLAlchemy ORM**: https://docs.sqlalchemy.org/
- **HTTP Status Codes**: https://httpwg.org/specs/rfc7231.html#status.codes
- **curl Manual**: https://curl.se/docs/manual.html

---

**Last Updated:** April 2026  
**Test Environment:** Development (http://127.0.0.1:5000)
