# Kubernetes & Docker Deployment Guide

## Table of Contents
1. [Docker Setup](#docker-setup)
2. [Local Testing with Docker Compose](#local-testing)
3. [Kubernetes Architecture](#kubernetes-architecture)
4. [Prerequisites](#prerequisites)
5. [Deployment Instructions](#deployment-instructions)
6. [Management Operations](#management-operations)
7. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
8. [Production Scaling](#production-scaling)

---

## Docker Setup

### Building the Docker Image

```bash
# Build the image
docker build -t kishorkumarparoi/wine-quality-prediction:latest .

# Tag for registry
docker tag kishorkumarparoi/wine-quality-prediction:latest \
  <docker-registry>/wine-quality-prediction:latest

# Push to registry
docker push <docker-registry>/wine-quality-prediction:latest
```

### Image Details

- **Base Image**: `python:3.11-slim`
- **Multi-stage Build**: Reduces final image size
- **Non-root User**: Runs as `appuser` (UID 1000) for security
- **Health Check**: HTTP GET to `/health` endpoint
- **Port**: 8080

---

## Local Testing

### Using Docker Compose

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f wine-quality-app

# Stop the application
docker-compose down

# Rebuild image
docker-compose build --no-cache
```

**Environment Variables** (set in `.env` or `docker-compose.yml`):
```
MLFLOW_TRACKING_USERNAME=KishorKumarParoi
MLFLOW_TRACKING_PASSWORD=<your_token>
```

### Testing Endpoints

```bash
# Health check
curl http://localhost:8080/health

# Prediction
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{"fixed_acidity": 7.4, "volatile_acidity": 0.7, ...}'

# Train model
curl http://localhost:8080/train
```

---

## Kubernetes Architecture

### Components

```
┌─────────────────────────────────────────────────────┐
│         Kubernetes Cluster (wine-quality)           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │         Ingress (nginx)                      │  │
│  │  Route: wine-quality.example.com             │  │
│  └───────────────────┬──────────────────────────┘  │
│                      │                             │
│  ┌───────────────────▼──────────────────────────┐  │
│  │  LoadBalancer Service (port 80)              │  │
│  └───────────────────┬──────────────────────────┘  │
│                      │                             │
│  ┌───────────────────▼──────────────────────────┐  │
│  │  ClusterIP Service (port 8080)               │  │
│  └───────────────────┬──────────────────────────┘  │
│                      │                             │
│  ┌───────────────────▼──────────────────────────┐  │
│  │  Deployment (3 replicas)                     │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐   │  │
│  │  │  Pod 1   │  │  Pod 2   │  │  Pod 3   │   │  │
│  │  │  8080    │  │  8080    │  │  8080    │   │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘   │  │
│  └───────┼─────────────┼─────────────┼─────────┘  │
│          │             │             │            │
│  ┌───────▼─────────────▼─────────────▼─────────┐  │
│  │  Persistent Volumes                         │  │
│  │  ├─ artifacts (10Gi)                        │  │
│  │  └─ logs (5Gi)                              │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  HPA: Auto-scale 2-10 replicas               │  │
│  │  Triggers: CPU >70%, Memory >80%             │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Files Structure

```
k8s/
├── namespace.yaml          # wine-quality namespace
├── configmap.yaml          # Non-sensitive config (MLFLOW_TRACKING_URI, etc)
├── secret.yaml             # Sensitive credentials (MLflow username/password)
├── rbac.yaml               # ServiceAccount, Role, RoleBinding
├── pvc.yaml                # PersistentVolumeClaims (artifacts, logs)
├── deployment.yaml         # Main app deployment (3 replicas, health checks)
├── service.yaml            # LoadBalancer and ClusterIP services
├── hpa.yaml                # Horizontal Pod Autoscaler (2-10 replicas)
├── ingress.yaml            # Ingress for HTTP routing
├── network-policy.yaml     # Network policies for security
├── kustomization.yaml      # Kustomize manifest
└── README.md               # This file
```

---

## Prerequisites

### Required Tools

```bash
# Check kubectl version
kubectl version --client

# Check cluster connectivity
kubectl cluster-info

# List available contexts
kubectl config get-contexts

# Switch context (if needed)
kubectl config use-context <context-name>
```

### Cluster Requirements

- **Kubernetes Version**: 1.20+
- **Metrics Server**: Required for HPA (auto-scaling)
- **Storage Class**: Default storage class for PVCs
- **Ingress Controller**: NGINX or similar (for Ingress)

### Check Cluster Status

```bash
# Check nodes
kubectl get nodes

# Check metrics server
kubectl get deployment metrics-server -n kube-system

# Check available storage classes
kubectl get storageclass
```

---

## Deployment Instructions

### Step 1: Update Configuration

Edit sensitive data in manifests:

```bash
# Update Docker registry credentials
kubectl create secret docker-registry docker-registry-secret \
  --docker-server=<your-registry> \
  --docker-username=<username> \
  --docker-password=<password> \
  --docker-email=<email> \
  -n wine-quality \
  --dry-run=client -o yaml > k8s/docker-registry-secret.yaml

# Update MLflow credentials (edit k8s/secret.yaml)
# Replace base64-encoded values with actual credentials
```

### Step 2: Deploy Using Kubectl

#### Option A: Manual Deployment (Recommended for getting started)

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create secrets (IMPORTANT: Update with real credentials first!)
kubectl apply -f k8s/secret.yaml

# Create ConfigMap
kubectl apply -f k8s/configmap.yaml

# Create RBAC
kubectl apply -f k8s/rbac.yaml

# Create PVCs
kubectl apply -f k8s/pvc.yaml

# Create Deployment
kubectl apply -f k8s/deployment.yaml

# Create Services
kubectl apply -f k8s/service.yaml

# Create HPA
kubectl apply -f k8s/hpa.yaml

# Create NetworkPolicy
kubectl apply -f k8s/network-policy.yaml

# Create Ingress
kubectl apply -f k8s/ingress.yaml

# Verify deployment
kubectl rollout status deployment/wine-quality-app -n wine-quality
```

#### Option B: Using Kustomize

```bash
# Deploy all manifests
kubectl apply -k k8s/

# Verify
kubectl rollout status deployment/wine-quality-app -n wine-quality
```

### Step 3: Verify Deployment

```bash
# Check pods status
kubectl get pods -n wine-quality

# Check services
kubectl get svc -n wine-quality

# Describe deployment
kubectl describe deployment wine-quality-app -n wine-quality

# Check events
kubectl get events -n wine-quality
```

### Step 4: Access the Application

```bash
# Port forward (for local testing)
kubectl port-forward svc/wine-quality-service 8080:8080 -n wine-quality

# Visit: http://localhost:8080/

# Via LoadBalancer (if available)
kubectl get svc wine-quality-service -n wine-quality
# Note the EXTERNAL-IP and visit: http://<EXTERNAL-IP>:80/
```

---

## Management Operations

### Scaling

```bash
# Manual scaling
kubectl scale deployment wine-quality-app --replicas=5 -n wine-quality

# Check HPA status
kubectl get hpa -n wine-quality
kubectl describe hpa wine-quality-hpa -n wine-quality

# Watch HPA scaling in action
kubectl get hpa wine-quality-hpa -n wine-quality --watch
```

### Updating the Image

```bash
# Set new image
kubectl set image deployment/wine-quality-app \
  wine-quality-app=kishorkumarparoi/wine-quality-prediction:v2.0.0 \
  -n wine-quality

# Check rollout status
kubectl rollout status deployment/wine-quality-app -n wine-quality

# View rollout history
kubectl rollout history deployment/wine-quality-app -n wine-quality

# Rollback if needed
kubectl rollout undo deployment/wine-quality-app -n wine-quality
```

### Updating ConfigMap/Secrets

```bash
# Update ConfigMap
kubectl edit configmap wine-quality-config -n wine-quality

# Restart pods to apply changes (ConfigMap changes aren't auto-applied)
kubectl rollout restart deployment/wine-quality-app -n wine-quality

# Update Secret
kubectl edit secret mlflow-credentials -n wine-quality

# Restart pods
kubectl rollout restart deployment/wine-quality-app -n wine-quality
```

### Logs

```bash
# View logs from single pod
kubectl logs <pod-name> -n wine-quality

# Stream logs
kubectl logs -f <pod-name> -n wine-quality

# View logs from all pods
kubectl logs -l app=wine-quality-prediction -n wine-quality --all-containers=true

# View previous logs (if pod crashed)
kubectl logs <pod-name> -n wine-quality --previous
```

### Executing Commands in Pod

```bash
# Interactive shell
kubectl exec -it <pod-name> -n wine-quality -- /bin/sh

# Run command
kubectl exec <pod-name> -n wine-quality -- python -c "print('test')"

# Run health check
kubectl exec <pod-name> -n wine-quality -- curl http://localhost:8080/health
```

### Debugging Issues

```bash
# Get detailed pod info
kubectl describe pod <pod-name> -n wine-quality

# Get recent events
kubectl get events -n wine-quality --sort-by='.lastTimestamp'

# Check resource usage
kubectl top pods -n wine-quality
kubectl top nodes

# Check persistent volume status
kubectl get pvc -n wine-quality
kubectl get pv

# Inspect container logs
kubectl logs <pod-name> -n wine-quality --tail=100
```

---

## Monitoring & Troubleshooting

### Common Issues

#### 1. Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n wine-quality

# Common causes:
# - Image pull errors: check image exists and credentials
# - Resource limits: insufficient cluster resources
# - Health check failures: app not responding on port 8080
```

#### 2. CrashLoopBackOff

```bash
# Check logs
kubectl logs <pod-name> -n wine-quality --previous

# Common causes:
# - MLflow credentials incorrect
# - Missing environment variables
# - Port already in use
```

#### 3. Pending PVC

```bash
# Check PVC status
kubectl describe pvc wine-quality-artifacts-pvc -n wine-quality

# Common causes:
# - No storage class available
# - Storage quota exceeded
# - Node storage full
```

#### 4. Service Not Accessible

```bash
# Check service endpoints
kubectl get endpoints wine-quality-service -n wine-quality

# Check network policies
kubectl get networkpolicy -n wine-quality

# Test DNS resolution
kubectl exec <pod-name> -n wine-quality -- nslookup wine-quality-service.wine-quality.svc.cluster.local
```

### Monitoring Setup

#### Prometheus (Optional)

```yaml
# Add ServiceMonitor for Prometheus if installed
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: wine-quality-monitor
  namespace: wine-quality
spec:
  selector:
    matchLabels:
      app: wine-quality-prediction
  endpoints:
  - port: http
    interval: 30s
    path: /health
```

#### Alerts (Optional)

```bash
# Monitor pod restarts
kubectl get pods -n wine-quality -w

# Check resource usage trends
kubectl top pods -n wine-quality --containers
```

---

## Production Scaling

### Best Practices

1. **Resource Limits**: Set appropriate CPU/memory limits (already in deployment.yaml)
2. **Health Checks**: Liveness and readiness probes configured
3. **Auto-scaling**: HPA configured for CPU (70%) and memory (80%)
4. **Rolling Updates**: Zero-downtime deployments via RollingUpdate strategy
5. **Security**: Network policies, RBAC, and non-root user
6. **Persistence**: PVCs for artifacts and logs

### High Availability Configuration

```bash
# Ensure multiple replicas (3 recommended)
kubectl get deployment wine-quality-app -n wine-quality

# Verify pod distribution across nodes
kubectl get pods -n wine-quality -o wide

# Check disruption budgets
kubectl get pdb -n wine-quality
```

### Performance Optimization

```bash
# Monitor HPA metrics
kubectl get hpa wine-quality-hpa -n wine-quality --watch

# Adjust HPA thresholds if needed
kubectl edit hpa wine-quality-hpa -n wine-quality

# Monitor actual resource usage
kubectl top pods -n wine-quality --containers

# Adjust resource requests/limits if needed
kubectl patch deployment wine-quality-app -p \
  '{"spec":{"template":{"spec":{"containers":[{"name":"wine-quality-app","resources":{"limits":{"cpu":"1","memory":"2Gi"}}}]}}}}' \
  -n wine-quality
```

### Backup & Recovery

```bash
# Backup PVC data
kubectl get pvc -n wine-quality
# Configure backup policy in your storage system

# Export deployment config
kubectl get deployment wine-quality-app -n wine-quality -o yaml > backup-deployment.yaml

# Export all namespace resources
kubectl get all -n wine-quality -o yaml > backup-all.yaml
```

---

## Environment-Specific Overrides

### Development Environment

```bash
# Fewer replicas, lower resources
kubectl apply -f k8s/ -k k8s/overlays/dev/
```

### Production Environment

```bash
# More replicas, higher resources, ingress TLS
kubectl apply -f k8s/ -k k8s/overlays/prod/
```

Create overlay directories:
```
k8s/
├── base/              # All manifests here
└── overlays/
    ├── dev/
    │   ├── kustomization.yaml
    │   └── patches/
    └── prod/
        ├── kustomization.yaml
        └── patches/
```

---

## Quick Reference Commands

```bash
# Deploy
kubectl apply -k k8s/

# Check status
kubectl get all -n wine-quality

# View logs
kubectl logs -f -l app=wine-quality-prediction -n wine-quality

# Scale
kubectl scale deployment wine-quality-app --replicas=5 -n wine-quality

# Update image
kubectl set image deployment/wine-quality-app \
  wine-quality-app=<image:tag> -n wine-quality

# Restart
kubectl rollout restart deployment/wine-quality-app -n wine-quality

# Delete
kubectl delete -k k8s/

# Get endpoint
kubectl get svc wine-quality-service -n wine-quality

# SSH into pod
kubectl exec -it -n wine-quality <pod-name> -- /bin/sh

# Check resource usage
kubectl top pods -n wine-quality
```

---

## Support & Additional Resources

- **Kubernetes Documentation**: https://kubernetes.io/docs/
- **Docker Documentation**: https://docs.docker.com/
- **Flask Documentation**: https://flask.palletsprojects.com/
- **MLflow Documentation**: https://mlflow.org/docs/

## Author
Created by: Kishor Kumar Paroi
