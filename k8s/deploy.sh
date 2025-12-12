#!/bin/bash

# Exit on error
set -e

# Configuration
REGISTRY="${DOCKER_REGISTRY:-localhost:5000}"
BACKEND_IMAGE="${REGISTRY}/trustmebro-backend:latest"
FRONTEND_IMAGE="${REGISTRY}/trustmebro-frontend:latest"
NAMESPACE="trustmebro"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
log_info "Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { log_error "Docker is not installed"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { log_error "kubectl is not installed"; exit 1; }

# Create namespace if it doesn't exist
log_info "Creating namespace..."
kubectl apply -f k8s/namespace.yaml

# Build backend Docker image
log_info "Building backend Docker image..."
docker build -t "${BACKEND_IMAGE}" -f trustmebro-backend/Dockerfile trustmebro-backend/

# Build frontend Docker image
log_info "Building frontend Docker image..."
docker build -t "${FRONTEND_IMAGE}" -f trustmebro-frontend/Dockerfile trustmebro-frontend/

# Push images to registry (if not localhost)
if [[ "${REGISTRY}" != "localhost:5000" ]]; then
  log_info "Pushing backend image to registry..."
  docker push "${BACKEND_IMAGE}"
  
  log_info "Pushing frontend image to registry..."
  docker push "${FRONTEND_IMAGE}"
else
  log_warn "Using local Docker images. Make sure your cluster can access them."
fi

# Apply Kubernetes manifests
log_info "Applying Kubernetes manifests..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/ingress.yaml

# Wait for deployments to be ready
log_info "Waiting for deployments to be ready..."
kubectl rollout status deployment/backend -n ${NAMESPACE} --timeout=5m || log_warn "Backend deployment status check timed out"
kubectl rollout status deployment/frontend -n ${NAMESPACE} --timeout=5m || log_warn "Frontend deployment status check timed out"

# Get service information
log_info "Deployment complete! Service information:"
echo ""
kubectl get svc -n ${NAMESPACE}
echo ""
kubectl get ingress -n ${NAMESPACE}
echo ""

# Get pod status
log_info "Pod status:"
kubectl get pods -n ${NAMESPACE}
echo ""

# Provide access information
log_info "Access information:"
FRONTEND_SERVICE=$(kubectl get svc frontend -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
if [ "${FRONTEND_SERVICE}" == "pending" ] || [ -z "${FRONTEND_SERVICE}" ]; then
  log_warn "Frontend LoadBalancer IP is pending. If using Ingress, configure your domain to point to the Ingress IP."
  INGRESS_IP=$(kubectl get ingress trustmebro-http -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
  echo "Ingress IP: ${INGRESS_IP}"
else
  echo "Frontend URL: http://${FRONTEND_SERVICE}"
fi

log_info "To view logs: kubectl logs -f deployment/backend -n ${NAMESPACE}"
log_info "To port-forward: kubectl port-forward svc/frontend 8080:80 -n ${NAMESPACE}"
