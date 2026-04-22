# ══════════════════════════════════════════════════════════════════
# Makefile — Shared API (5G + 6G Network Slicing)
# ══════════════════════════════════════════════════════════════════

VENV          = venv
PYTHON        = $(VENV)/bin/python
PIP           = $(VENV)/bin/pip

# ── Update these with your details ───────────────────────────────
IMAGE_NAME     = emna_guefrech_4data_mlops3
DOCKERHUB_USER = emna239
FULL_IMAGE     = $(DOCKERHUB_USER)/$(IMAGE_NAME):latest
CONTAINER      = network_slicing_api
PORT           = 8000

.PHONY: install api api_docs \
        docker_build docker_run docker_stop \
        docker_push docker_logs docker_clean help

help:
	@echo ""
	@echo "  Local API"
	@echo "    make install         Install dependencies"
	@echo "    make api             Start FastAPI server locally"
	@echo "    make api_docs        Print docs URL"
	@echo ""
	@echo "  Docker"
	@echo "    make docker_build    Build Docker image"
	@echo "    make docker_run      Run container locally"
	@echo "    make docker_stop     Stop and remove container"
	@echo "    make docker_push     Push image to Docker Hub"
	@echo "    make docker_logs     Show container logs"
	@echo "    make docker_clean    Remove image and container"
	@echo ""

# ── Local ─────────────────────────────────────────────────────────
install:
	@echo ">>> Installing dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo ">>> Done ✅"

api:
	@echo ">>> Starting unified 5G+6G API on port $(PORT)..."
	@echo ">>> Docs: http://127.0.0.1:$(PORT)/docs"
	$(VENV)/bin/uvicorn app:app --reload --host 0.0.0.0 --port $(PORT)

api_docs:
	@echo ">>> API docs: http://127.0.0.1:$(PORT)/docs"

# ── Docker ────────────────────────────────────────────────────────
docker_build:
	@echo ">>> Building Docker image: $(IMAGE_NAME)..."
	cd .. && docker build -t $(IMAGE_NAME) -f shared_api/Dockerfile .
	@echo ">>> Image built ✅"
	docker images | grep $(IMAGE_NAME)

docker_run:
	@echo ">>> Running container: $(CONTAINER) on port $(PORT)..."
	docker run -d --name $(CONTAINER) -p $(PORT):$(PORT) $(IMAGE_NAME)
	@echo ">>> Container started ✅"
	@echo ">>> API available at: http://127.0.0.1:$(PORT)/docs"

docker_stop:
	@echo ">>> Stopping container..."
	docker stop $(CONTAINER) || true
	docker rm   $(CONTAINER) || true
	@echo ">>> Container stopped ✅"

docker_logs:
	@echo ">>> Container logs:"
	docker logs $(CONTAINER)

docker_push:
	@echo ">>> Tagging image for Docker Hub..."
	docker tag $(IMAGE_NAME) $(FULL_IMAGE)
	@echo ">>> Pushing to Docker Hub..."
	docker push $(FULL_IMAGE)
	@echo ">>> Pushed ✅"
	@echo ">>> https://hub.docker.com/r/$(DOCKERHUB_USER)/$(IMAGE_NAME)"

docker_clean: docker_stop
	@echo ">>> Removing Docker image..."
	docker rmi $(IMAGE_NAME) || true
	docker rmi $(FULL_IMAGE) || true
	@echo ">>> Cleanup done ✅"
