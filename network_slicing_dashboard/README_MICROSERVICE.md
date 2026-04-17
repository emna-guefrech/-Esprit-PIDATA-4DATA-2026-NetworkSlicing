# 6G Network Slicing - Microservice Architecture

## Overview

This is a complete microservice architecture for 6G Network Slicing with Trustworthy AI features. The system provides real-time network congestion prediction, QoS probability estimation, and anomaly detection with explainability, fairness, and drift detection capabilities.

## Architecture

### Microservice Components

1. **API Gateway** (Port 8000) - Single entry point, authentication, routing
2. **Prediction Service** (Port 8001) - ML predictions (classification, regression, anomaly)
3. **Model Service** (Port 8002) - Model management, versioning, loading
4. **Trustworthy AI Service** (Port 8003) - Explainability, fairness, drift detection
5. **Monitoring Service** (Port 8004) - System metrics, health checks, alerts
6. **Frontend Service** (Port 8500) - Streamlit dashboard interface

### Supporting Infrastructure

- **Redis** - Caching and message queue
- **Prometheus** - Metrics collection
- **Grafana** - Visualization dashboards
- **Docker** - Containerization
- **Kubernetes** - Orchestration

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.10+
- Make (optional, for convenience)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd network-slicing-microservice
```

2. **Copy models**
```bash
mkdir -p shared/models
cp ../models/*.joblib shared/models/
```

3. **Build and run**
```bash
make quick-start
```

### Manual Setup

```bash
# Build all services
docker-compose build

# Run all services
docker-compose up -d

# Check service health
curl http://localhost:8000/health
```

## Services

### API Gateway

**URL:** `http://localhost:8000`

**Endpoints:**
- `POST /auth/login` - Authentication
- `POST /predict/classification` - Congestion classification
- `POST /predict/regression` - QoS probability prediction
- `POST /predict/anomaly` - Anomaly detection
- `GET /models` - List available models
- `POST /explain/shap` - SHAP explanations
- `GET /monitoring/metrics` - System metrics

### Prediction Service

**URL:** `http://localhost:8001`

**Features:**
- XGBoost classification (Normal/Light/Critical congestion)
- QoS probability regression (0-100% SLA compliance)
- Isolation Forest anomaly detection

### Model Service

**URL:** `http://localhost:8002`

**Features:**
- Model versioning and loading
- Model metadata management
- Model performance tracking

### Trustworthy AI Service

**URL:** `http://localhost:8003`

**Features:**
- SHAP explainability
- Bias and fairness detection
- Concept drift detection
- Real-time monitoring

### Monitoring Service

**URL:** `http://localhost:8004`

**Features:**
- System health checks
- Performance metrics
- Alert management
- Service discovery

### Frontend Dashboard

**URL:** `http://localhost:8500`

**Features:**
- Streamlit interface
- Real-time predictions
- Interactive visualizations
- Trustworthy AI insights

## API Usage

### Authentication

```bash
# Get JWT token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Classification Prediction

```bash
curl -X POST http://localhost:8000/predict/classification \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "packet_loss_budget": 0.001,
    "latency_budget": 1000,
    "jitter_budget": 500,
    "data_rate_budget": 5.0,
    "slice_available_transfer_rate": 4.8,
    "slice_latency": 800,
    "slice_packet_loss": 0.0005,
    "slice_jitter": 200,
    "slice_handover": 0.5
  }'
```

### QoS Probability Prediction

```bash
curl -X POST http://localhost:8000/predict/regression \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "latency_gap": 200,
    "packet_loss_gap": 0.0005,
    "jitter_gap": 300,
    "rate_gap": -0.2
  }'
```

## Development

### Local Development

```bash
# Setup development environment
make dev-setup

# Run tests
make test

# Check logs
make logs

# Health check
make health
```

### Building Images

```bash
# Build all services
make build

# Build for production
make prod-build
```

### Monitoring

```bash
# Open monitoring dashboards
make monitor

# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

## Deployment

### Docker Compose

```bash
# Development deployment
make run

# Production deployment
make deploy
```

### Kubernetes

```bash
# Deploy to Kubernetes
make k8s-deploy

# Check status
kubectl get pods -n network-slicing

# Clean up
make k8s-clean
```

## Performance

### Benchmarks

- **Classification**: < 100ms prediction time
- **Regression**: < 50ms prediction time
- **Anomaly Detection**: < 75ms prediction time
- **API Gateway**: < 10ms routing time

### Scalability

- **Horizontal scaling**: Auto-scaling based on CPU/memory
- **Load balancing**: Round-robin distribution
- **Caching**: Redis for frequent predictions
- **Batch processing**: Up to 100 predictions per request

## Security

### Authentication

- JWT tokens with expiration
- Role-based access control (RBAC)
- API key authentication for services

### Data Protection

- Input validation and sanitization
- Rate limiting (100 requests/minute)
- HTTPS encryption in production
- Secure secret management

## Monitoring

### Metrics

- Request latency and throughput
- Error rates and status codes
- Resource utilization (CPU, memory)
- Model performance metrics

### Alerting

- Service health failures
- High error rates
- Resource exhaustion
- Model drift detection

## Troubleshooting

### Common Issues

1. **Service not responding**
   ```bash
   docker-compose logs <service-name>
   ```

2. **Model loading errors**
   ```bash
   ls -la shared/models/
   ```

3. **Authentication failures**
   ```bash
   curl -X POST http://localhost:8000/auth/login
   ```

### Health Checks

```bash
# All services
make health

# Individual service
curl http://localhost:8001/health
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the troubleshooting section

## Roadmap

- [ ] Additional ML models (Neural Networks, Ensemble)
- [ ] Real-time streaming predictions
- [ ] Advanced monitoring and alerting
- [ ] Multi-cloud deployment
- [ ] Edge computing integration
