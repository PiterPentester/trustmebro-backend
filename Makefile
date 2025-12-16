.PHONY: help format lint scan-security build scan-image push run-compose stop-compose clean all

# Variables
IMAGE_NAME := trustmebro-backend
IMAGE_TAG := latest
REGISTRY ?= docker.io
FULL_IMAGE_NAME := $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)

# Default target
help:
	@echo "Available targets:"
	@echo "  format         - Format code using ruff"
	@echo "  lint           - Lint code using ruff"
	@echo "  scan-security  - Scan code for security issues using bandit"
	@echo "  build          - Build Docker image"
	@echo "  scan-image     - Scan Docker image for vulnerabilities using grype"
	@echo "  push           - Push Docker image to registry"
	@echo "  run-compose    - Run application using docker-compose"
	@echo "  stop-compose   - Stop docker-compose services"
	@echo "  clean          - Clean up generated files and containers"
	@echo "  all            - Run format, lint, scan-security, build, and scan-image"

# Format code using ruff
format:
	@echo "Formatting code with ruff..."
	@uvx ruff format .
	@echo "✓ Code formatted successfully"

# Lint code using ruff
lint:
	@echo "Linting code with ruff..."
	@uvx ruff check . --fix
	@echo "✓ Linting completed"

# Scan code for security issues using bandit
scan-security:
	@echo "Scanning code for security issues with bandit..."
	@uvx bandit -c pyproject.toml -r .
	@echo "✓ Security scan completed"

# Run tests using pytest
test:
	@echo "Running tests..."
	@uv run pytest
	@echo "✓ Tests completed"

# Build Docker image
build:
	@echo "Building Docker image: $(IMAGE_NAME):$(IMAGE_TAG)..."
	@docker buildx build --platform linux/amd64,linux/arm64 -t $(IMAGE_NAME):$(IMAGE_TAG) --load .
	@echo "✓ Docker image built successfully"

# Scan Docker image for vulnerabilities using grype
scan-image:
	@echo "Scanning Docker image for vulnerabilities with grype..."
	@grype $(IMAGE_NAME):$(IMAGE_TAG)
	@echo "✓ Image scan completed"

# Push Docker image to registry
push:
	@echo "Tagging image for registry..."
	@docker tag $(IMAGE_NAME):$(IMAGE_TAG) $(FULL_IMAGE_NAME)
	@echo "Pushing image to $(FULL_IMAGE_NAME)..."
	@docker push $(FULL_IMAGE_NAME)
	@echo "✓ Image pushed successfully"

# Run application using docker-compose
run-compose:
	@echo "Starting services with docker-compose..."
	@docker-compose -f dockercompose.yaml up -d --build
	@echo "✓ Services started successfully"
	@echo "Backend available at: http://localhost:8080"

# Stop docker-compose services
stop-compose:
	@echo "Stopping docker-compose services..."
	@docker-compose -f dockercompose.yaml down
	@echo "✓ Services stopped"

# Clean up generated files and containers
clean:
	@echo "Cleaning up..."
	@rm -f bandit-report.json grype-report.json
	@docker-compose -f dockercompose.yaml down -v 2>/dev/null || true
	@echo "✓ Cleanup completed"

# Deploy to Kubernetes
deploy:
	@echo "Deploying to Kubernetes..."
	@kubectl apply -f k8s/
	@echo "✓ Deployed to Kubernetes"

# Undeploy from Kubernetes
undeploy:
	@echo "Undeploying from Kubernetes..."
	@kubectl delete -f k8s/
	@echo "✓ Undeployed from Kubernetes"

# Run all quality checks and build
all: format lint scan-security test build scan-image deploy
	@echo "✓ All checks and build completed successfully"
