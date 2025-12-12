# Kubernetes Quick Reference

## Deploy

```bash
# Local deployment (minikube/docker-desktop)
chmod +x k8s/deploy.sh
./k8s/deploy.sh

# With custom registry
DOCKER_REGISTRY=your-registry.com:5000 ./k8s/deploy.sh
```

## Access Application

```bash
# Port forward (development)
kubectl port-forward svc/frontend 8080:80 -n trustmebro
# Access: http://localhost:8080

# Minikube service
minikube service frontend -n trustmebro

# Ingress (production)
kubectl get ingress -n trustmebro
# Access: http://<INGRESS-IP>
```

## View Status

```bash
# Pods
kubectl get pods -n trustmebro
kubectl get pods -n trustmebro -o wide

# Services
kubectl get svc -n trustmebro

# Deployments
kubectl get deployments -n trustmebro

# All resources
kubectl get all -n trustmebro
```

## View Logs

```bash
# Backend logs
kubectl logs -f deployment/backend -n trustmebro

# Frontend logs
kubectl logs -f deployment/frontend -n trustmebro

# Redis logs
kubectl logs -f statefulset/redis -n trustmebro

# Specific pod
kubectl logs -f <pod-name> -n trustmebro

# Previous logs (crashed pod)
kubectl logs <pod-name> -n trustmebro --previous
```

## Debug

```bash
# Pod details
kubectl describe pod <pod-name> -n trustmebro

# Pod events
kubectl get events -n trustmebro --sort-by='.lastTimestamp'

# Execute command in pod
kubectl exec -it <pod-name> -n trustmebro -- /bin/sh

# Port forward to service
kubectl port-forward svc/redis 6379:6379 -n trustmebro

# Check resource usage
kubectl top pods -n trustmebro
kubectl top nodes
```

## Scale

```bash
# Scale deployment
kubectl scale deployment backend --replicas=5 -n trustmebro

# Autoscale (requires metrics-server)
kubectl autoscale deployment backend --min=2 --max=10 -n trustmebro
```

## Update

```bash
# Update image
kubectl set image deployment/backend \
  backend=your-registry/trustmebro-backend:v1.1.0 \
  -n trustmebro

# Check rollout status
kubectl rollout status deployment/backend -n trustmebro

# Rollback
kubectl rollout undo deployment/backend -n trustmebro

# View rollout history
kubectl rollout history deployment/backend -n trustmebro
```

## Manage

```bash
# Apply manifests
kubectl apply -f k8s/

# Delete namespace (all resources)
kubectl delete namespace trustmebro

# Delete specific resource
kubectl delete deployment backend -n trustmebro

# Restart deployment
kubectl rollout restart deployment/backend -n trustmebro
```

## Redis

```bash
# Connect to Redis
kubectl exec -it redis-0 -n trustmebro -- redis-cli

# Backup
kubectl exec -it redis-0 -n trustmebro -- redis-cli BGSAVE
kubectl cp trustmebro/redis-0:/data/dump.rdb ./redis-backup.rdb

# Restore
kubectl cp ./redis-backup.rdb trustmebro/redis-0:/data/dump.rdb
kubectl exec -it redis-0 -n trustmebro -- redis-cli shutdown
kubectl delete pod redis-0 -n trustmebro
```

## Ingress

```bash
# View ingress
kubectl get ingress -n trustmebro

# Describe ingress
kubectl describe ingress trustmebro -n trustmebro

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

## Useful Aliases

```bash
# Add to ~/.zshrc or ~/.bashrc
alias k='kubectl'
alias kn='kubectl config set-context --current --namespace'
alias kgp='kubectl get pods -n trustmebro'
alias kgs='kubectl get svc -n trustmebro'
alias kl='kubectl logs -f'
alias kd='kubectl describe'
alias ke='kubectl exec -it'

# Usage
k get pods -n trustmebro
kn trustmebro  # Set default namespace
kgp            # Get pods in trustmebro
kl deployment/backend -n trustmebro
```

## Common Issues

### Pods not starting
```bash
kubectl describe pod <pod-name> -n trustmebro
kubectl logs <pod-name> -n trustmebro
```

### Backend can't reach Redis
```bash
kubectl exec -it <backend-pod> -n trustmebro -- nslookup redis
kubectl exec -it redis-0 -n trustmebro -- redis-cli ping
```

### Frontend can't reach backend
```bash
kubectl exec -it <frontend-pod> -n trustmebro -- wget -O- http://backend:8080/health
```

### Ingress not working
```bash
kubectl get ingress -n trustmebro
kubectl describe ingress trustmebro -n trustmebro
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

## Resources

- [Kubernetes Docs](https://kubernetes.io/docs/)
- [kubectl Cheatsheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Minikube Docs](https://minikube.sigs.k8s.io/)
