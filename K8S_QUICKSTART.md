# Kubernetes Quick Start Guide

## 🚀 Quick Deployment (5 minutes)

### Prerequisites Check
```bash
# Verify you have a running Kubernetes cluster
kubectl cluster-info
kubectl get nodes

# Check if metrics-server is running (required for HPA)
kubectl get deployment metrics-server -n kube-system
```

### Option 1: Using the Deployment Script (Recommended)

```bash
# Make script executable
chmod +x deploy.sh

# Deploy to Kubernetes
./deploy.sh k8s deploy wine-quality

# Check status
./deploy.sh k8s status

# View logs
./deploy.sh k8s logs <pod-name>

# Access application
./deploy.sh k8s portforward 8080 8080
```

### Option 2: Manual Deployment with kubectl

```bash
# Step 1: Update secrets with your credentials
# Edit k8s/secret.yaml and replace with your actual MLflow credentials
# IMPORTANT: Use base64 encoding for production:
# echo -n "your_password" | base64

# Step 2: Deploy
kubectl apply -k k8s/

# Step 3: Verify deployment
kubectl get pods -n wine-quality
kubectl get svc -n wine-quality

# Step 4: Access the app
kubectl port-forward svc/wine-quality-service 8080:8080 -n wine-quality
# Visit: http://localhost:8080
```

## 📊 Monitoring & Management

### Check Deployment Status
```bash
./deploy.sh k8s status

# Or manually:
kubectl get all -n wine-quality
```

### View Application Logs
```bash
# View logs from a specific pod
./deploy.sh k8s logs wine-quality-app-<pod-id>

# Stream logs from all pods
kubectl logs -f -l app=wine-quality-prediction -n wine-quality
```

### Access the Application

#### Method 1: Port Forward (Development)
```bash
./deploy.sh k8s portforward 8080 8080
# Visit: http://localhost:8080
```

#### Method 2: Service IP (if accessible)
```bash
kubectl get svc wine-quality-service -n wine-quality
# Note the EXTERNAL-IP and visit: http://<EXTERNAL-IP>
```

#### Method 3: Ingress (Production)
- Update the hostname in `k8s/ingress.yaml`
- Configure your DNS to point to the ingress controller
- Visit: http://wine-quality.example.com

## 🔧 Common Operations

### Scale Up/Down
```bash
./deploy.sh k8s scale 5  # Scale to 5 replicas

# Or manually:
kubectl scale deployment wine-quality-app --replicas=5 -n wine-quality
```

### Update Application
```bash
# Build and push new image
./deploy.sh docker build v1.1.0
./deploy.sh docker push v1.1.0

# Update deployment with new image
kubectl set image deployment/wine-quality-app \
  wine-quality-app=kishorkumarparoi/wine-quality-prediction:v1.1.0 \
  -n wine-quality

# Check rollout status
kubectl rollout status deployment/wine-quality-app -n wine-quality
```

### Rollback Failed Deployment
```bash
./deploy.sh k8s rollback

# Or manually:
kubectl rollout undo deployment/wine-quality-app -n wine-quality
```

### Update Configuration
```bash
# Edit CloudConfig
kubectl edit configmap wine-quality-config -n wine-quality

# Edit Secrets
kubectl edit secret mlflow-credentials -n wine-quality

# Restart pods to apply changes
kubectl rollout restart deployment/wine-quality-app -n wine-quality
```

## 🐛 Troubleshooting

### Pods Not Running
```bash
# Check pod status
kubectl describe pod <pod-name> -n wine-quality

# View logs
kubectl logs <pod-name> -n wine-quality --previous

# Common issues:
# 1. Image pull error - check Docker credentials
# 2. CrashLoopBackOff - check logs and MLflow credentials
# 3. Pending - check available resources: kubectl describe node
```

### Health Check Failing
```bash
# Test health endpoint manually
kubectl exec <pod-name> -n wine-quality -- curl http://localhost:8080/health

# Check HTTP response
kubectl logs <pod-name> -n wine-quality | grep -i health
```

### Storage Issues
```bash
# Check PVC status
kubectl get pvc -n wine-quality

# Check available storage
kubectl get pv

# Check node storage
kubectl top nodes

# Describe PVC for details
kubectl describe pvc wine-quality-artifacts-pvc -n wine-quality
```

### Network Issues
```bash
# Check services and endpoints
kubectl get svc -n wine-quality
kubectl get endpoints -n wine-quality

# Test DNS resolution from pod
kubectl exec <pod-name> -n wine-quality -- nslookup wine-quality-service.wine-quality.svc.cluster.local

# Check network policies
kubectl get networkpolicy -n wine-quality
```

## 📈 Auto-scaling

The Horizontal Pod Autoscaler is already configured to:
- **Scale up** when CPU > 70% or Memory > 80%
- **Min replicas**: 2
- **Max replicas**: 10

### Monitor HPA
```bash
# Check HPA status
kubectl get hpa -n wine-quality

# Watch HPA in action
kubectl get hpa wine-quality-hpa -n wine-quality --watch

# Get detailed HPA info
kubectl describe hpa wine-quality-hpa -n wine-quality
```

### Adjust HPA Settings
```bash
# Edit HPA configuration
kubectl edit hpa wine-quality-hpa -n wine-quality

# Or update via patch
kubectl patch hpa wine-quality-hpa -p \
  '{"spec":{"maxReplicas":20}}' \
  -n wine-quality
```

## 🔒 Security

### Check Security Policies
```bash
# Check network policies
kubectl get networkpolicy -n wine-quality

# Check RBAC
kubectl get role,rolebinding -n wine-quality

# Check pod security
kubectl get pods -n wine-quality -o jsonpath='{.items[*].spec.securityContext}'
```

### View Credentials (Never in Production!)
```bash
# Decode secret (development only)
kubectl get secret mlflow-credentials -n wine-quality -o jsonpath='{.data.MLFLOW_TRACKING_PASSWORD}' | base64 -d
```

## 📚 Testing API Endpoints

### Health Check
```bash
kubectl run -it --rm alpine --image=alpine --restart=Never -- sh
# Inside pod:
wget -O- http://wine-quality-service.wine-quality.svc.cluster.local:8080/health
```

### Make Prediction
```bash
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{
    "fixed_acidity": 7.4,
    "volatile_acidity": 0.7,
    "citric_acid": 0.0,
    "residual_sugar": 1.9,
    "chlorides": 0.076,
    "free_sulfur_dioxide": 11.0,
    "total_sulfur_dioxide": 34.0,
    "density": 0.9978,
    "pH": 3.51,
    "sulphates": 0.56,
    "alcohol": 9.4
  }'
```

### Trigger Training
```bash
curl http://localhost:8080/train
```

## 🧹 Cleanup

### Delete Entire Deployment
```bash
./deploy.sh k8s delete

# Or manually:
kubectl delete -k k8s/
kubectl delete namespace wine-quality
```

### Delete Specific Resources
```bash
# Delete deployment but keep PVC data
kubectl delete deployment wine-quality-app -n wine-quality

# Delete specific service
kubectl delete svc wine-quality-service -n wine-quality
```

## 🆘 Getting Help

### View Events
```bash
# Recent cluster events
kubectl get events -n wine-quality --sort-by='.lastTimestamp'

# Specific pod events
kubectl describe pod <pod-name> -n wine-quality
```

### Debug Mode
```bash
# Get detailed pod information
kubectl describe pod <pod-name> -n wine-quality

# Execute bash in pod
kubectl exec -it <pod-name> -n wine-quality -- /bin/sh

# Check system resources
kubectl top pods -n wine-quality
kubectl top nodes
```

### Resource Usage
```bash
# Pod resource usage
kubectl top pods -n wine-quality

# Node resource usage
kubectl top nodes

# View resource requests/limits
kubectl get pods -n wine-quality -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].resources}{"\n"}{end}'
```

## 📖 Additional Resources

- **Full Documentation**: See `DEPLOYMENT.md`
- **Kubernetes Docs**: https://kubernetes.io/docs/
- **kubectl Cheatsheet**: https://kubernetes.io/docs/reference/kubectl/cheatsheet/
- **Troubleshooting Guide**: https://kubernetes.io/docs/tasks/debug-application-cluster/

---

Happy deploying! 🎉
