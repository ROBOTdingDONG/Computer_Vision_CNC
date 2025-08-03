# Computer Vision CNC Manufacturing Platform - Deployment Guide

## 🚀 Production Deployment Guide

This guide provides comprehensive instructions for deploying the Computer Vision CNC Manufacturing Platform in production environments with enterprise-grade reliability, security, and monitoring.

## 📋 Prerequisites

### Infrastructure Requirements

#### Minimum Hardware Specifications
- **Control Plane**: 3 nodes with 4 vCPU, 8GB RAM, 100GB SSD
- **Worker Nodes**: 4+ nodes with 8 vCPU, 16GB RAM, 200GB SSD
- **GPU Nodes**: 2+ nodes with NVIDIA GPU (Tesla T4 or better)
- **Storage**: Network-attached storage (NFS/Ceph) with 500GB+ capacity

#### Software Requirements
- Kubernetes 1.24+
- Docker 20.10+
- Helm 3.8+
- kubectl configured with cluster access
- NGINX Ingress Controller
- Cert-Manager for SSL certificates

#### Network Requirements
- Load balancer with public IP
- Internal network access to CNC machines
- Firewall rules for industrial protocols (MTConnect, OPC-UA)

### Security Prerequisites
- SSL/TLS certificates for production domains
- Secrets management solution (Kubernetes secrets or external)
- Network security policies configured
- Industrial network segmentation

## 🔧 Deployment Methods

### Method 1: Automated Deployment (Recommended)

Use the provided deployment script for automated setup:

```bash
# Make the script executable
chmod +x scripts/deploy.sh

# Deploy to production
./scripts/deploy.sh production cv-cnc-manufacturing
```

The script will:
1. Check prerequisites
2. Build and push Docker images
3. Create Kubernetes namespace
4. Deploy infrastructure components
5. Deploy application services
6. Run health checks
7. Display access information

### Method 2: Manual Deployment

#### Step 1: Prepare Environment

```bash
# Clone the repository
git clone https://github.com/ROBOTdingDONG/Computer_Vision_CNC.git
cd Computer_Vision_CNC

# Create environment file
cp .env.example .env.production

# Edit environment variables
nano .env.production
```

#### Step 2: Build Docker Images

```bash
# Build main API image
docker build -t cv-cnc-manufacturing/cv-cnc-api:latest \
    --target production .

# Build GPU-enabled vision image
docker build -t cv-cnc-manufacturing/cv-cnc-vision:latest \
    --target gpu-production .

# Push to registry
docker push cv-cnc-manufacturing/cv-cnc-api:latest
docker push cv-cnc-manufacturing/cv-cnc-vision:latest
```

#### Step 3: Create Kubernetes Namespace

```bash
kubectl create namespace cv-cnc-manufacturing
kubectl label namespace cv-cnc-manufacturing \
    app.kubernetes.io/name=cv-cnc-manufacturing
```

#### Step 4: Deploy Secrets and Configuration

```bash
# Create TLS secret
kubectl create secret tls cv-cnc-tls-secret \
    --cert=certs/tls.crt \
    --key=certs/tls.key \
    --namespace=cv-cnc-manufacturing

# Create application secrets
kubectl create secret generic cv-cnc-app-secrets \
    --from-literal=secret-key="your-secret-key" \
    --from-literal=database-password="your-db-password" \
    --from-literal=redis-password="your-redis-password" \
    --namespace=cv-cnc-manufacturing

# Apply configuration
kubectl apply -f kubernetes/storage-config.yaml
```

#### Step 5: Deploy Infrastructure

```bash
# Add Helm repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Deploy PostgreSQL
helm install cv-cnc-postgres bitnami/postgresql \
    --namespace cv-cnc-manufacturing \
    --set auth.database=cv_cnc_manufacturing \
    --set auth.username=cvuser \
    --set auth.existingSecret=cv-cnc-app-secrets

# Deploy Redis
helm install cv-cnc-redis bitnami/redis \
    --namespace cv-cnc-manufacturing \
    --set auth.existingSecret=cv-cnc-app-secrets

# Deploy monitoring
helm install cv-cnc-monitoring prometheus-community/kube-prometheus-stack \
    --namespace cv-cnc-manufacturing
```

#### Step 6: Deploy Applications

```bash
# Deploy all application components
kubectl apply -f kubernetes/ --namespace=cv-cnc-manufacturing

# Wait for deployments
kubectl wait --for=condition=available --timeout=300s \
    deployment/cv-cnc-api deployment/cv-cnc-vision deployment/cv-cnc-controller \
    --namespace=cv-cnc-manufacturing
```

### Method 3: Docker Compose (Development/Testing)

For development or testing environments:

```bash
# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

## 🔐 Security Configuration

### SSL/TLS Setup

1. **Generate or obtain SSL certificates**:
```bash
# Using Let's Encrypt with cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.12.0/cert-manager.yaml

# Create cluster issuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@your-domain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

2. **Configure authentication**:
```bash
# Update JWT secret key
kubectl patch secret cv-cnc-app-secrets \
    --namespace=cv-cnc-manufacturing \
    --patch='{"data":{"secret-key":"'$(openssl rand -base64 32 | base64 -w 0)'"}}'
```

### Network Security

1. **Apply network policies**:
```bash
kubectl apply -f kubernetes/ingress-network.yaml
```

2. **Configure firewall rules** for industrial protocols:
- MTConnect: TCP 5000
- OPC-UA: TCP 4840
- Modbus TCP: TCP 502

## 📊 Monitoring and Observability

### Access Monitoring Dashboards

After deployment, access the monitoring interfaces:

- **Grafana**: https://your-domain/grafana
  - Username: admin
  - Password: (from GRAFANA_PASSWORD env var)

- **Prometheus**: https://your-domain/prometheus

- **API Documentation**: https://your-domain/docs

### Key Metrics to Monitor

1. **Manufacturing Metrics**:
   - Defect detection rate
   - Quality scores
   - Production throughput
   - Machine utilization

2. **System Metrics**:
   - API response times
   - Computer vision processing latency
   - Resource utilization (CPU, memory, GPU)
   - Error rates

3. **Business Metrics**:
   - Overall equipment effectiveness (OEE)
   - First-pass yield
   - Mean time between failures (MTBF)

## 🔧 Post-Deployment Configuration

### 1. Configure CNC Machine Connections

Update the configuration for your specific CNC machines:

```bash
kubectl edit configmap cv-cnc-config --namespace=cv-cnc-manufacturing
```

Update these values:
- `mtconnect-host`: Your MTConnect server address
- `opcua-endpoint`: Your OPC-UA server endpoint

### 2. Upload Computer Vision Models

```bash
# Copy trained models to persistent volume
kubectl cp models/ cv-cnc-manufacturing/cv-cnc-vision-xxx:/app/models/
```

### 3. Configure Quality Thresholds

Adjust quality control parameters in the ConfigMap:
- `defect-threshold`: Minimum confidence for defect detection
- `quality-threshold`: Minimum quality score for acceptance

### 4. Set Up Alerts

Configure alert destinations in Prometheus:

```bash
kubectl edit configmap prometheus-config --namespace=cv-cnc-manufacturing
```

Add your alerting endpoints (email, Slack, PagerDuty).

## 🚨 Troubleshooting

### Common Issues

1. **Pods not starting**:
```bash
kubectl describe pod <pod-name> --namespace=cv-cnc-manufacturing
kubectl logs <pod-name> --namespace=cv-cnc-manufacturing
```

2. **Database connection issues**:
```bash
kubectl exec -it cv-cnc-postgres-0 --namespace=cv-cnc-manufacturing -- psql -U cvuser -d cv_cnc_manufacturing
```

3. **GPU not available**:
```bash
kubectl describe node <gpu-node>
nvidia-smi  # Run on GPU node
```

4. **Network connectivity**:
```bash
kubectl exec -it <pod-name> --namespace=cv-cnc-manufacturing -- nslookup cv-cnc-postgres
```

### Health Checks

```bash
# Check all pods
kubectl get pods --namespace=cv-cnc-manufacturing

# Check services
kubectl get services --namespace=cv-cnc-manufacturing

# Check ingress
kubectl get ingress --namespace=cv-cnc-manufacturing

# Check persistent volumes
kubectl get pv,pvc --namespace=cv-cnc-manufacturing
```

## 📈 Scaling

### Horizontal Pod Autoscaler

```bash
# Enable autoscaling for API pods
kubectl autoscale deployment cv-cnc-api \
    --namespace=cv-cnc-manufacturing \
    --cpu-percent=70 \
    --min=3 \
    --max=10

# Enable autoscaling for vision processing
kubectl autoscale deployment cv-cnc-vision \
    --namespace=cv-cnc-manufacturing \
    --cpu-percent=80 \
    --min=2 \
    --max=6
```

### Vertical Pod Autoscaler

```bash
# Install VPA
kubectl apply -f https://github.com/kubernetes/autoscaler/releases/latest/download/vpa-release.yaml

# Create VPA for API
kubectl apply -f - <<EOF
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: cv-cnc-api-vpa
  namespace: cv-cnc-manufacturing
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cv-cnc-api
  updatePolicy:
    updateMode: "Auto"
EOF
```

## 🔄 Updates and Maintenance

### Rolling Updates

```bash
# Update API image
kubectl set image deployment/cv-cnc-api \
    cv-cnc-api=cv-cnc-manufacturing/cv-cnc-api:v1.1.0 \
    --namespace=cv-cnc-manufacturing

# Check rollout status
kubectl rollout status deployment/cv-cnc-api \
    --namespace=cv-cnc-manufacturing

# Rollback if needed
kubectl rollout undo deployment/cv-cnc-api \
    --namespace=cv-cnc-manufacturing
```

### Backup and Recovery

```bash
# Backup PostgreSQL
kubectl exec cv-cnc-postgres-0 --namespace=cv-cnc-manufacturing -- \
    pg_dump -U cvuser cv_cnc_manufacturing > backup-$(date +%Y%m%d).sql

# Backup persistent volumes
kubectl get pv --namespace=cv-cnc-manufacturing -o yaml > pv-backup.yaml
```

## 📞 Support and Maintenance

### Log Collection

```bash
# Collect logs from all pods
kubectl logs -l app.kubernetes.io/name=cv-cnc-manufacturing \
    --namespace=cv-cnc-manufacturing \
    --since=1h > logs-$(date +%Y%m%d-%H%M).txt
```

### Performance Monitoring

Regular monitoring checklist:
- [ ] Check resource utilization
- [ ] Monitor defect detection accuracy
- [ ] Verify CNC machine connectivity
- [ ] Review alert history
- [ ] Validate backup procedures

---

## 🎯 Success Criteria

Your deployment is successful when:

✅ All pods are running and healthy  
✅ API endpoints respond correctly  
✅ Computer vision processing works  
✅ CNC machines are connected  
✅ Monitoring dashboards show data  
✅ SSL certificates are valid  
✅ Alerts are configured  
✅ Quality control is operational  

## 📧 Getting Help

For deployment issues:
1. Check the troubleshooting section
2. Review logs and metrics
3. Consult the API documentation
4. Contact the development team

**Production Support**: production-support@cv-cnc-platform.com  
**Emergency Contact**: +1-XXX-XXX-XXXX
