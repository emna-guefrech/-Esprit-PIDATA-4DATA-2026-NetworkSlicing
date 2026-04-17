# 6G Network Slicing Microservices Makefile

.PHONY: help build run stop clean deploy k8s-deploy k8s-clean test logs

# Default target
help:
	@echo "6G Network Slicing Microservices"
	@echo ""
	@echo "Available commands:"
	@echo "  build      - Build all Docker images"
	@echo "  run        - Run all services with docker-compose"
	@echo "  stop       - Stop all services"
	@echo "  clean      - Clean Docker images and containers"
	@echo "  deploy     - Deploy to production"
	@echo "  k8s-deploy - Deploy to Kubernetes"
	@echo "  k8s-clean  - Clean Kubernetes resources"
	@echo "  test       - Run tests"
	@echo "  logs       - Show logs for all services"

# Build all services
build:
	@echo "Building all Docker images..."
	docker build -t network-slicing/api-gateway:latest ./api-gateway
	docker build -t network-slicing/prediction-service:latest ./prediction-service
	docker build -t network-slicing/model-service:latest ./model-service
	docker build -t network-slicing/trustworthy-ai-service:latest ./trustworthy-ai-service
	docker build -t network-slicing/monitoring-service:latest ./monitoring-service
	docker build -t network-slicing/frontend-service:latest ./frontend-service
	@echo "All images built successfully!"

# Run with docker-compose
run:
	@echo "Starting all services..."
	docker-compose up -d
	@echo "Services started!"
	@echo "API Gateway: http://localhost:8000"
	@echo "Frontend: http://localhost:8500"
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3000"

# Stop services
stop:
	@echo "Stopping all services..."
	docker-compose down
	@echo "All services stopped!"

# Clean
clean:
	@echo "Cleaning Docker resources..."
	docker-compose down -v
	docker system prune -f
	docker volume prune -f
	@echo "Cleanup completed!"

# Deploy to production
deploy:
	@echo "Deploying to production..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "Production deployment completed!"

# Kubernetes deployment
k8s-deploy:
	@echo "Deploying to Kubernetes..."
	kubectl create namespace network-slicing --dry-run=client -o yaml | kubectl apply -f -
	kubectl apply -f kubernetes/
	@echo "Kubernetes deployment completed!"
	@echo "Check status with: kubectl get pods -n network-slicing"

# Kubernetes cleanup
k8s-clean:
	@echo "Cleaning Kubernetes resources..."
	kubectl delete namespace network-slicing
	@echo "Kubernetes cleanup completed!"

# Run tests
test:
	@echo "Running tests..."
	python -m pytest tests/ -v
	@echo "Tests completed!"

# Show logs
logs:
	@echo "Showing logs for all services..."
	docker-compose logs -f

# Development setup
dev-setup:
	@echo "Setting up development environment..."
	python -m venv venv
	./venv/Scripts/activate
	pip install -r requirements.txt
	@echo "Development environment ready!"

# Production build
prod-build:
	@echo "Building for production..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
	@echo "Production build completed!"

# Health check
health:
	@echo "Checking service health..."
	curl -f http://localhost:8000/health || echo "API Gateway: DOWN"
	curl -f http://localhost:8001/health || echo "Prediction Service: DOWN"
	curl -f http://localhost:8002/health || echo "Model Service: DOWN"
	curl -f http://localhost:8003/health || echo "Trustworthy AI Service: DOWN"
	curl -f http://localhost:8004/health || echo "Monitoring Service: DOWN"
	curl -f http://localhost:8500/_stcore/health || echo "Frontend Service: DOWN"

# Load testing
load-test:
	@echo "Running load tests..."
	# Install k6 if not present
	which k6 || (echo "Installing k6..." && go install go.k6.io/k6/v6@latest)
	k6 run tests/load-test.js
	@echo "Load tests completed!"

# Security scan
security-scan:
	@echo "Running security scan..."
	# Install trivy if not present
	which trivy || (echo "Installing trivy..." && brew install trivy || apt-get install trivy)
	trivy image network-slicing/api-gateway:latest
	trivy image network-slicing/prediction-service:latest
	trivy image network-slicing/model-service:latest
	trivy image network-slicing/trustworthy-ai-service:latest
	trivy image network-slicing/monitoring-service:latest
	trivy image network-slicing/frontend-service:latest
	@echo "Security scan completed!"

# Backup
backup:
	@echo "Backing up models and data..."
	mkdir -p backups
	cp -r shared/models backups/
	docker exec redis redis-cli BGSAVE
	@echo "Backup completed!"

# Restore
restore:
	@echo "Restoring from backup..."
	cp -r backups/models shared/models/
	@echo "Restore completed!"

# Monitor
monitor:
	@echo "Opening monitoring dashboards..."
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3000 (admin/admin)"
	@echo "API Gateway: http://localhost:8000/docs"

# Quick start
quick-start: build run
	@echo "Quick start completed!"
	@echo "Wait 30 seconds for services to initialize..."
	sleep 30
	$(MAKE) health
