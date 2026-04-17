# Architecture Microservice - 6G Network Slicing Dashboard

## Structure des Services

```
network-slicing-microservice/
|
|-- api-gateway/
|   |-- Dockerfile
|   |-- requirements.txt
|   |-- main.py
|   |-- config.py
|
|-- prediction-service/
|   |-- Dockerfile
|   |-- requirements.txt
|   |-- main.py
|   |-- models/
|   |-- utils/
|
|-- model-service/
|   |-- Dockerfile
|   |-- requirements.txt
|   |-- main.py
|   |-- models/
|
|-- trustworthy-ai-service/
|   |-- Dockerfile
|   |-- requirements.txt
|   |-- main.py
|   |-- explainability/
|   |-- fairness/
|   |-- drift/
|   |-- monitoring/
|
|-- monitoring-service/
|   |-- Dockerfile
|   |-- requirements.txt
|   |-- main.py
|   |-- metrics.py
|
|-- frontend-service/
|   |-- Dockerfile
|   |-- requirements.txt
|   |-- app.py
|   |-- pages/
|
|-- shared/
|   |-- models/
|   |-- utils/
|   |-- config.py
|
|-- docker-compose.yml
|-- docker-compose.prod.yml
|-- kubernetes/
|   |-- namespace.yaml
|   |-- api-gateway.yaml
|   |-- prediction-service.yaml
|   |-- model-service.yaml
|   |-- trustworthy-ai-service.yaml
|   |-- monitoring-service.yaml
|   |-- frontend-service.yaml
|
|-- Makefile
|-- README.md
```

## Services et Responsabilités

### 1. API Gateway (Port: 8000)
- **Rôle** : Point d'entrée unique, authentification, routing
- **Technologies** : FastAPI, JWT, Nginx
- **Endpoints** : `/predict/*`, `/explain/*`, `/fairness/*`, `/drift/*`, `/monitor/*`

### 2. Prediction Service (Port: 8001)
- **Rôle** : Prédictions ML (classification, régression, anomalies)
- **Technologies** : FastAPI, XGBoost, scikit-learn
- **Endpoints** : `/predict/classification`, `/predict/regression`, `/predict/anomaly`

### 3. Model Service (Port: 8002)
- **Rôle** : Gestion des modèles ML, versioning, loading
- **Technologies** : FastAPI, MLflow, joblib
- **Endpoints** : `/models/list`, `/models/load/{model_id}`, `/models/update`

### 4. Trustworthy AI Service (Port: 8003)
- **Rôle** : Explainability, fairness, drift detection, monitoring
- **Technologies** : FastAPI, SHAP, pandas, numpy
- **Endpoints** : `/explain/*`, `/fairness/*`, `/drift/*`, `/monitor/*`

### 5. Monitoring Service (Port: 8004)
- **Rôle** : Métriques, alertes, santé des services
- **Technologies** : FastAPI, Prometheus, Grafana
- **Endpoints** : `/health`, `/metrics`, `/alerts`

### 6. Frontend Service (Port: 8500)
- **Rôle** : Interface utilisateur Streamlit
- **Technologies** : Streamlit, React, WebSocket
- **Pages** : Dashboard, prediction, explainability, monitoring

## Communication Entre Services

### API REST
- **Synchrone** : Prédictions, chargement de modèles
- **Format** : JSON
- **Authentification** : JWT tokens

### Message Queue (Redis/RabbitMQ)
- **Asynchrone** : Monitoring, alertes, logging
- **Événements** : model_updates, predictions, anomalies

### WebSocket
- **Temps réel** : Dashboard updates, monitoring live
- **Connexions** : Frontend vers services

## Déploiement

### Docker
- **Images** : Multi-stage builds optimisées
- **Volumes** : Partage des modèles, données
- **Networks** : Isolation des services

### Kubernetes
- **Pods** : Auto-scaling horizontal
- **Services** : Load balancing
- **ConfigMaps** : Configuration centralisée
- **Secrets** : Clés API, tokens

## Scalabilité

### Horizontal Scaling
- **Prediction Service** : Scale basé sur la charge
- **Frontend Service** : Scale basé sur les utilisateurs
- **Monitoring Service** : Scale basé sur les métriques

### Vertical Scaling
- **Model Service** : Plus de RAM pour gros modèles
- **Trustworthy AI Service** : Plus de CPU pour calculs intensifs

## Résilience

### Circuit Breaker
- **Timeouts** : 30s pour predictions, 5s pour health checks
- **Retry** : 3 tentatives avec backoff exponentiel
- **Fallback** : Mode demo si service indisponible

### Health Checks
- **Liveness** : Service en vie
- **Readiness** : Service prêt à recevoir des requêtes
- **Startup** : Service démarré

## Sécurité

### Authentification
- **JWT** : Tokens avec expiration
- **OAuth2** : Intégration possible
- **API Keys** : Pour les services internes

### Autorisation
- **RBAC** : Rôles par service
- **Rate Limiting** : Protection contre abus
- **Input Validation** : Validation des entrées

## Monitoring

### Métriques
- **Prometheus** : Collecte des métriques
- **Grafana** : Dashboards visuels
- **AlertManager** : Alertes automatiques

### Logging
- **ELK Stack** : Elasticsearch, Logstash, Kibana
- **Structured Logging** : JSON format
- **Correlation IDs** : Suivi des requêtes

## Performance

### Caching
- **Redis** : Cache des prédictions fréquentes
- **Model Loading** : Cache des modèles en mémoire
- **API Responses** : Cache des réponses statiques

### Optimisation
- **Async Processing** : Prédictions en arrière-plan
- **Batch Processing** : Traitement par lots
- **Connection Pooling** : Réutilisation des connexions
