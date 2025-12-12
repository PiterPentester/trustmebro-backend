# TrustMeBro Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the TrustMeBro application (frontend + backend + Redis) to a Kubernetes cluster.

## Prerequisites

- Kubernetes cluster (v1.20+)
- Docker (for building images)
- kubectl configured to access your cluster
- (Optional) Docker registry for storing images

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Ingress (nginx)                      │
│  trustmebro.example.com → /api → backend:8080          │
│  trustmebro.example.com → /    → frontend:80           │
└─────────────────────────────────────────────────────────┘
                    ↓                    ↓
        ┌──────────────────┐  ┌──────────────────┐
        │   Frontend (2)   │  │   Backend (2)    │
        │  nginx:alpine    │  │  Python/FastAPI  │
        │   Port 80        │  │   Port 8080      │
        └──────────────────┘  └──────────────────┘
                                       ↓
                            ┌──────────────────┐
                            │   Redis (1)      │
                            │  redis:7-alpine  │
                            │   Port 6379      │
                            └──────────────────┘
```

## Files Overview

- **namespace.yaml** - Creates the `trustmebro` namespace
- **redis-deployment.yaml** - Redis StatefulSet with persistent storage
- **backend-deployment.yaml** - FastAPI backend with 2 replicas, health checks, and security context
- **frontend-deployment.yaml** - Nginx frontend with 2 replicas, caching, and security headers
- **ingress.yaml** - Ingress configuration for routing traffic
- **network-policy.yaml** - Network policies for security
- **resource-quota.yaml** - Resource quotas and limits
- **deploy.sh** - Deployment script

## Quick Start

### 1. Build and Deploy

```bash
# Make the script executable
chmod +x k8s/deploy.sh

# Run the deployment script
./k8s/deploy.sh

# Or with a custom registry
DOCKER_REGISTRY=your-registry.com:5000 ./k8s/deploy.sh
```

### 2. Verify Deployment

```bash
# Check pods
kubectl get pods -n trustmebro

# Check services
kubectl get svc -n trustmebro

# Check ingress
kubectl get ingress -n trustmebro

# View logs
kubectl logs -f deployment/backend -n trustmebro
kubectl logs -f deployment/frontend -n trustmebro
```

### 3. Access the Application

#### Option A: Port Forwarding (Development)
```bash
kubectl port-forward svc/frontend 8080:80 -n trustmebro
# Access at http://localhost:8080
```

#### Option B: Ingress (Production)
Configure your DNS to point to the Ingress IP:
```bash
kubectl get ingress -n trustmebro -o wide
```

#### Option C: LoadBalancer Service
```bash
kubectl get svc frontend -n trustmebro
# Use the EXTERNAL-IP
```

## Configuration

### Environment Variables

**Backend** (in `backend-deployment.yaml`):
- `REDIS_URL` - Redis connection string (default: `redis:6379`)
- `APP_URL` - Backend URL for QR codes (default: `http://backend:8080`)
- `FRONTEND_URL` - Frontend URL for CORS (default: `http://frontend`)
- `ENVIRONMENT` - Set to `production` for strict CORS

**Frontend** (in `index.html`):
- Auto-detects API URL based on hostname
- Development: `http://localhost:8080`
- Production: `{protocol}://{host}/api`

### Scaling

To scale deployments:
```bash
# Scale backend to 3 replicas
kubectl scale deployment backend --replicas=3 -n trustmebro

# Scale frontend to 3 replicas
kubectl scale deployment frontend --replicas=3 -n trustmebro
```

### Resource Limits

Adjust resource requests/limits in the deployment manifests:
- **Backend**: 100m CPU / 128Mi memory (requests), 500m CPU / 256Mi memory (limits)
- **Frontend**: 50m CPU / 64Mi memory (requests), 200m CPU / 128Mi memory (limits)
- **Redis**: 100m CPU / 128Mi memory (requests), 200m CPU / 256Mi memory (limits)

## Production Considerations

### 1. Image Registry
- Push images to a private registry (ECR, GCR, Docker Hub, etc.)
- Update image references in deployment manifests
- Use image pull secrets for private registries

### 2. TLS/SSL
- Install cert-manager: `kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml`
- Create a ClusterIssuer for Let's Encrypt
- Update Ingress annotations with certificate issuer

### 3. Database Persistence
- Redis uses StatefulSet with PersistentVolumeClaim (1Gi)
- For production, increase storage and enable backups
- Consider using managed Redis (AWS ElastiCache, Google Cloud Memorystore, etc.)

### 4. Monitoring & Logging
- Install Prometheus for metrics: `helm install prometheus prometheus-community/kube-prometheus-stack`
- Install ELK or Loki for logging
- Configure alerts for pod failures and resource usage

### 5. Security
- Network policies restrict traffic between pods
- Containers run as non-root users
- Read-only root filesystems where possible
- Resource quotas prevent resource exhaustion

### 6. High Availability
- Multiple replicas for frontend and backend
- Pod anti-affinity spreads pods across nodes
- Rolling update strategy for zero-downtime deployments

## Troubleshooting

### Pods not starting
```bash
# Check pod status
kubectl describe pod <pod-name> -n trustmebro

# View logs
kubectl logs <pod-name> -n trustmebro
```

### Backend can't connect to Redis
```bash
# Test Redis connectivity
kubectl exec -it redis-0 -n trustmebro -- redis-cli ping

# Check service DNS
kubectl exec -it <backend-pod> -n trustmebro -- nslookup redis
```

### Frontend can't reach backend
```bash
# Check if backend service is accessible
kubectl exec -it <frontend-pod> -n trustmebro -- wget -O- http://backend:8080/health

# Check CORS headers
curl -H "Origin: http://localhost:3000" http://<backend-ip>:8080/health -v
```

### Ingress not working
```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress status
kubectl describe ingress trustmebro -n trustmebro

# Test with port-forward
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80
```

## Cleanup

```bash
# Delete all resources in the namespace
kubectl delete namespace trustmebro

# Or delete specific resources
kubectl delete -f k8s/ -n trustmebro
```

## Advanced Deployment

### Using Helm
Create a `values.yaml` and `Chart.yaml` for Helm deployment:
```bash
helm install trustmebro ./helm-chart -f values.yaml
```

### GitOps with ArgoCD
```bash
kubectl apply -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
# Create an ArgoCD Application pointing to your git repo
```

### CI/CD Integration
Update your CI/CD pipeline to:
1. Build Docker images
2. Push to registry
3. Update image tags in manifests
4. Apply manifests with `kubectl apply -f k8s/`

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Kubernetes logs: `kubectl logs -f <pod-name> -n trustmebro`
3. Check events: `kubectl get events -n trustmebro`
