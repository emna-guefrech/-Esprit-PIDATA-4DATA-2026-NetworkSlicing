# Deployment Guide - Anomaly Detection Service MS-2

## Overview

This guide covers deployment options for the Anomaly Detection Service:
1. **Local Development** - Single machine
2. **Docker Compose** - Local containers
3. **Docker** - Production container
4. **Kubernetes** - Scalable deployment
5. **Cloud Services** - AWS, Azure, GCP

---

## Deployment Option 1: Local Development

### Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure .env
# DATABASE_URL=mysql+pymysql://root:@localhost:3306/network_slicing

# 3. Initialize database
python init_db.py

# 4. Run application
python run.py
```

**Access**: http://localhost:5000

---

## Deployment Option 2: Docker Compose (Recommended for Development)

### Quick Start

```bash
# 1. Build and run all services
docker-compose up -d

# 2. Check status
docker-compose ps

# 3. View logs
docker-compose logs -f anomaly-service

# 4. Access
# Dashboard: http://localhost:5000
# Database: localhost:3306 (root/rootpassword)
```

### What's Included

- **MySQL Database**: Port 3306
- **Flask App**: Port 5000
- **Nginx Proxy**: Port 80, 443 (optional)
- **Persistent Volumes**: Database data

### Configuration

Edit `docker-compose.yml`:

```yaml
services:
  mysql:
    environment:
      MYSQL_ROOT_PASSWORD: your_password
      MYSQL_DATABASE: network_slicing
  
  anomaly-service:
    environment:
      FLASK_ENV: production
      DATABASE_URL: mysql+pymysql://user:password@mysql:3306/network_slicing
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data!)
docker-compose down -v
```

### View Database

```bash
# Connect to MySQL
docker-compose exec mysql mysql -u root -p

# Or from host (if port 3306 exposed)
mysql -h localhost -u root -p network_slicing
```

---

## Deployment Option 3: Docker (Production)

### Build Image

```bash
# Build with tag
docker build -t anomaly-detection-service:latest .

# Or specific version
docker build -t anomaly-detection-service:1.0.0 .
```

### Run Container

```bash
# Basic run
docker run -p 5000:5000 \
  -e DATABASE_URL="mysql+pymysql://user:password@mysql:3306/network_slicing" \
  -e FLASK_ENV="production" \
  anomaly-detection-service:latest

# With volume for models persistence
docker run -p 5000:5000 \
  -v models:/app/models \
  -v logs:/app/logs \
  -e DATABASE_URL="mysql+pymysql://user:password@mysql:3306/network_slicing" \
  anomaly-detection-service:latest

# With network connection to MySQL container
docker run -p 5000:5000 \
  --network my_network \
  --link mysql:db \
  -e DATABASE_URL="mysql+pymysql://user:password@db:3306/network_slicing" \
  anomaly-detection-service:latest
```

### Docker Registry

```bash
# Tag for registry
docker tag anomaly-detection-service:latest myregistry.azurecr.io/anomaly-service:latest

# Push to registry
docker push myregistry.azurecr.io/anomaly-service:latest

# Pull from registry
docker pull myregistry.azurecr.io/anomaly-service:latest
```

---

## Deployment Option 4: Production WSGI Server

### Using Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn -w 4 -b 0.0.0.0:5000 run:app

# With logging
gunicorn -w 4 -b 0.0.0.0:5000 \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  run:app

# With configuration file
gunicorn --config gunicorn_config.py run:app
```

### Gunicorn Configuration

Create `gunicorn_config.py`:

```python
import multiprocessing

bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Reload on code changes
reload = False  # Set to True for development

# SSL/TLS (if needed)
# keyfile = "/path/to/key.pem"
# certfile = "/path/to/cert.pem"
```

### Using uWSGI

```bash
# Install uWSGI
pip install uwsgi

# Run application
uwsgi --http :5000 --wsgi-file run.py --callable app --processes 4 --threads 2

# With configuration file
uwsgi --ini uwsgi.ini
```

### uWSGI Configuration

Create `uwsgi.ini`:

```ini
[uwsgi]
http = :5000
wsgi-file = run.py
callable = app
processes = 4
threads = 2
master = true

# Logging
daemonize = /var/log/uwsgi/anomaly.log
log-maxsize = 104857600

# Socket for reverse proxy
# socket = /tmp/anomaly.sock
# chmod-socket = 666
```

---

## Deployment Option 5: Kubernetes

### Create Deployment

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: anomaly-detection-service
  labels:
    app: anomaly-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: anomaly-service
  template:
    metadata:
      labels:
        app: anomaly-service
    spec:
      containers:
      - name: anomaly-service
        image: myregistry.azurecr.io/anomaly-service:1.0.0
        imagePullPolicy: Always
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: anomaly-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: anomaly-secrets
              key: secret-key
        livenessProbe:
          httpGet:
            path: /api/anomaly/stats
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/anomaly/stats
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        volumeMounts:
        - name: models
          mountPath: /app/models
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: anomaly-models-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: anomaly-service
spec:
  selector:
    app: anomaly-service
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5000
  type: LoadBalancer

---
apiVersion: v1
kind: Secret
metadata:
  name: anomaly-secrets
type: Opaque
stringData:
  database-url: mysql+pymysql://user:password@mysql.default:3306/network_slicing
  secret-key: your-secret-key-here

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: anomaly-models-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

### Deploy to Kubernetes

```bash
# Apply configuration
kubectl apply -f k8s-deployment.yaml

# Check deployment status
kubectl get deployments
kubectl get pods
kubectl get svc

# View logs
kubectl logs -f deployment/anomaly-detection-service

# Access service
kubectl port-forward svc/anomaly-service 5000:80
# Visit: http://localhost:5000
```

---

## Deployment Option 6: Cloud Services

### AWS EC2

```bash
# 1. Launch EC2 instance (Ubuntu 20.04 LTS)
# 2. SSH into instance
ssh -i key.pem ubuntu@instance-ip

# 3. Install dependencies
sudo apt update && sudo apt install python3-pip python3-venv mysql-client

# 4. Clone repository
git clone https://github.com/repo/anomaly-service.git
cd anomaly-service

# 5. Setup and run
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

### AWS Lambda (Serverless)

For serverless detection, use AWS Lambda with Flask-AWS:

```python
from flask_aws import FlaskAWS

app = FlaskAWS(__name__)

# Or use Zappa for automatic Lambda deployment:
# pip install zappa
# zappa init
# zappa deploy production
```

### Azure App Service

```bash
# 1. Create resource group
az group create -n mygroup -l eastus

# 2. Create App Service Plan
az appservice plan create -n myplan -g mygroup --sku FREE

# 3. Deploy from Git
az webapp create -n myapp -g mygroup --plan myplan \
  --runtime "PYTHON|3.10" \
  --runtime-version 3.10

# 4. Configure environment
az webapp config appsettings set -n myapp -g mygroup \
  --settings DATABASE_URL="mysql+pymysql://..." FLASK_ENV="production"

# 5. Deploy code
git push azure master
```

### Google Cloud Run

```bash
# 1. Create requirements.txt with gunicorn
# 2. Create .gcloudignore
# 3. Deploy
gcloud run deploy anomaly-service \
  --source . \
  --platform managed \
  --region us-central1 \
  --set-env-vars DATABASE_URL="mysql+pymysql://..." \
  --allow-unauthenticated
```

---

## Monitoring & Logging

### Logging Setup

Edit `config.py`:

```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    if not app.debug:
        file_handler = RotatingFileHandler(
            'logs/anomaly.log',
            maxBytes=10240000,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Anomaly Detection Service startup')
```

### Health Checks

```bash
# Check service health
curl http://localhost:5000/api/anomaly/stats

# Monitor logs
docker-compose logs -f anomaly-service
```

### Monitoring Tools

- **Prometheus**: Collect metrics
- **Grafana**: Visualize metrics
- **ELK Stack**: Log aggregation

---

## Backup & Disaster Recovery

### Database Backup

```bash
# Backup
mysqldump -u root -p network_slicing > backup_$(date +%Y%m%d).sql

# Restore
mysql -u root -p network_slicing < backup_20260425.sql

# Automated daily backup
0 2 * * * mysqldump -u root -p network_slicing > /backups/db_$(date +\%Y\%m\%d).sql
```

### Docker Volume Backup

```bash
# Backup models volume
docker run --rm -v anomaly_models:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/models.tar.gz -C /data .

# Restore models volume
docker run --rm -v anomaly_models:/data -v $(pwd):/backup \
  ubuntu tar xzf /backup/models.tar.gz -C /data
```

---

## Security Checklist

- [ ] Set strong `SECRET_KEY`
- [ ] Use HTTPS/SSL certificates
- [ ] Restrict database access
- [ ] Enable authentication on API
- [ ] Use environment variables for secrets
- [ ] Implement rate limiting
- [ ] Add CORS restrictions if needed
- [ ] Keep dependencies updated
- [ ] Enable audit logging
- [ ] Regular security scans

---

## Performance Tuning

### Database Optimization

```sql
-- Add indexes
CREATE INDEX idx_slice_id ON anomalies(slice_id);
CREATE INDEX idx_created_at ON anomalies(created_at);

-- Enable query cache
SET GLOBAL query_cache_size = 268435456;
SET GLOBAL query_cache_type = ON;
```

### Application Optimization

```python
# Enable caching
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@app.route('/api/anomaly/stats')
@cache.cached(timeout=300)
def get_stats():
    ...
```

### Load Balancing

```bash
# Nginx upstream
upstream anomaly_backend {
    server app1:5000;
    server app2:5000;
    server app3:5000;
    least_conn;
}
```

---

## Troubleshooting

### Service won't start

```bash
# Check logs
docker-compose logs anomaly-service

# Check port availability
netstat -tulpn | grep 5000

# Test database connection
python -c "from app import create_app; app = create_app()"
```

### High Memory Usage

```bash
# Monitor memory
docker stats

# Optimize gunicorn workers
# workers = (2 × CPUs) + 1
```

### Database Connection Issues

```bash
# Test connection
mysql -h localhost -u user -p -e "SELECT 1"

# Check connection pool
# max_pool_size = 10
# pool_pre_ping = True
```

---

**Deployment Guide - MS-2 Anomaly Detection Service**
