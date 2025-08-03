#!/bin/bash
# Computer Vision CNC Manufacturing Platform - Production Deployment Script
# This script deploys the platform to production environments with full monitoring

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOY_ENV="${1:-production}"
NAMESPACE="${2:-cv-cnc-manufacturing}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Deployment functions
check_prerequisites() {
    log_info "Checking deployment prerequisites..."
    
    # Check if required tools are installed
    local required_tools=("docker" "kubectl" "helm")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is not installed or not in PATH"
            exit 1
        fi
    done
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        log_error "Docker is not running"
        exit 1
    fi
    
    # Check if kubectl can connect to cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "All prerequisites check passed"
}

load_environment() {
    log_info "Loading environment configuration for $DEPLOY_ENV..."
    
    local env_file="$PROJECT_ROOT/.env.$DEPLOY_ENV"
    if [[ -f "$env_file" ]]; then
        set -a  # automatically export all variables
        source "$env_file"
        set +a
        log_success "Environment configuration loaded from $env_file"
    else
        log_warning "Environment file $env_file not found, using defaults"
    fi
    
    # Set default values if not provided
    export CV_CNC_VERSION="${CV_CNC_VERSION:-latest}"
    export CV_CNC_REGISTRY="${CV_CNC_REGISTRY:-cv-cnc-manufacturing}"
    export CV_CNC_NAMESPACE="${CV_CNC_NAMESPACE:-$NAMESPACE}"
}

build_images() {
    log_info "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    # Build main application image
    log_info "Building main application image..."
    docker build -t "$CV_CNC_REGISTRY/cv-cnc-api:$CV_CNC_VERSION" \
        --target production \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse HEAD)" \
        .
    
    # Build GPU-enabled image for computer vision
    log_info "Building GPU-enabled computer vision image..."
    docker build -t "$CV_CNC_REGISTRY/cv-cnc-vision:$CV_CNC_VERSION" \
        --target gpu-production \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse HEAD)" \
        .
    
    log_success "Docker images built successfully"
}

push_images() {
    log_info "Pushing Docker images to registry..."
    
    # Push main application image
    docker push "$CV_CNC_REGISTRY/cv-cnc-api:$CV_CNC_VERSION"
    
    # Push GPU-enabled image
    docker push "$CV_CNC_REGISTRY/cv-cnc-vision:$CV_CNC_VERSION"
    
    log_success "Docker images pushed successfully"
}

create_namespace() {
    log_info "Creating Kubernetes namespace: $CV_CNC_NAMESPACE"
    
    kubectl create namespace "$CV_CNC_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Label namespace for monitoring and security
    kubectl label namespace "$CV_CNC_NAMESPACE" \
        app.kubernetes.io/name=cv-cnc-manufacturing \
        app.kubernetes.io/version="$CV_CNC_VERSION" \
        environment="$DEPLOY_ENV" \
        --overwrite
    
    log_success "Namespace $CV_CNC_NAMESPACE ready"
}

deploy_secrets() {
    log_info "Deploying secrets and configuration..."
    
    # Create TLS certificates secret
    if [[ -f "$PROJECT_ROOT/certs/tls.crt" && -f "$PROJECT_ROOT/certs/tls.key" ]]; then
        kubectl create secret tls cv-cnc-tls-secret \
            --cert="$PROJECT_ROOT/certs/tls.crt" \
            --key="$PROJECT_ROOT/certs/tls.key" \
            --namespace="$CV_CNC_NAMESPACE" \
            --dry-run=client -o yaml | kubectl apply -f -
    fi
    
    # Create application secrets
    kubectl create secret generic cv-cnc-app-secrets \
        --from-literal=secret-key="${CV_CNC_SECRET_KEY:-$(openssl rand -base64 32)}" \
        --from-literal=database-password="${POSTGRES_PASSWORD:-$(openssl rand -base64 16)}" \
        --from-literal=redis-password="${REDIS_PASSWORD:-$(openssl rand -base64 16)}" \
        --namespace="$CV_CNC_NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    log_success "Secrets deployed successfully"
}

deploy_infrastructure() {
    log_info "Deploying infrastructure components..."
    
    # Deploy PostgreSQL
    helm repo add bitnami https://charts.bitnami.com/bitnami
    helm repo update
    
    helm upgrade --install cv-cnc-postgres bitnami/postgresql \
        --namespace "$CV_CNC_NAMESPACE" \
        --set auth.database=cv_cnc_manufacturing \
        --set auth.username=cvuser \
        --set auth.existingSecret=cv-cnc-app-secrets \
        --set auth.secretKeys.adminPasswordKey=database-password \
        --set primary.persistence.enabled=true \
        --set primary.persistence.size=20Gi \
        --set metrics.enabled=true
    
    # Deploy Redis
    helm upgrade --install cv-cnc-redis bitnami/redis \
        --namespace "$CV_CNC_NAMESPACE" \
        --set auth.existingSecret=cv-cnc-app-secrets \
        --set auth.existingSecretPasswordKey=redis-password \
        --set master.persistence.enabled=true \
        --set master.persistence.size=8Gi \
        --set metrics.enabled=true
    
    # Deploy Prometheus monitoring
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm upgrade --install cv-cnc-monitoring prometheus-community/kube-prometheus-stack \
        --namespace "$CV_CNC_NAMESPACE" \
        --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
        --set grafana.adminPassword="${GRAFANA_PASSWORD:-admin123}"
    
    log_success "Infrastructure components deployed"
}

deploy_application() {
    log_info "Deploying application components..."
    
    # Apply Kubernetes manifests
    kubectl apply -f "$PROJECT_ROOT/kubernetes/" --namespace="$CV_CNC_NAMESPACE"
    
    # Wait for deployments to be ready
    kubectl wait --for=condition=available --timeout=300s \
        deployment/cv-cnc-api deployment/cv-cnc-vision deployment/cv-cnc-controller \
        --namespace="$CV_CNC_NAMESPACE"
    
    log_success "Application components deployed successfully"
}

run_health_checks() {
    log_info "Running health checks..."
    
    # Wait for all pods to be ready
    kubectl wait --for=condition=ready --timeout=300s \
        pod -l app.kubernetes.io/name=cv-cnc-manufacturing \
        --namespace="$CV_CNC_NAMESPACE"
    
    # Check API health endpoint
    local api_url
    api_url=$(kubectl get service cv-cnc-api-service \
        --namespace="$CV_CNC_NAMESPACE" \
        -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    
    if [[ -n "$api_url" ]]; then
        if curl -f "http://$api_url/health" &> /dev/null; then
            log_success "API health check passed"
        else
            log_warning "API health check failed"
        fi
    fi
    
    log_success "Health checks completed"
}

show_deployment_info() {
    log_info "Deployment Information:"
    echo ""
    echo "Namespace: $CV_CNC_NAMESPACE"
    echo "Environment: $DEPLOY_ENV"
    echo "Version: $CV_CNC_VERSION"
    echo ""
    
    log_info "Services:"
    kubectl get services --namespace="$CV_CNC_NAMESPACE"
    echo ""
    
    log_info "Pods:"
    kubectl get pods --namespace="$CV_CNC_NAMESPACE"
    echo ""
    
    log_info "Ingress:"
    kubectl get ingress --namespace="$CV_CNC_NAMESPACE"
    echo ""
    
    log_success "Deployment completed successfully!"
    echo ""
    echo "🎉 Computer Vision CNC Manufacturing Platform is now running!"
    echo ""
    echo "Access URLs:"
    echo "- API Documentation: https://your-domain/docs"
    echo "- Grafana Dashboard: https://your-domain/grafana"
    echo "- Prometheus: https://your-domain/prometheus"
    echo ""
    echo "Next steps:"
    echo "1. Configure DNS to point to the load balancer IP"
    echo "2. Update SSL certificates if needed"
    echo "3. Configure CNC machine connections"
    echo "4. Set up monitoring alerts"
}

# Main deployment flow
main() {
    log_info "Starting deployment of Computer Vision CNC Manufacturing Platform"
    log_info "Environment: $DEPLOY_ENV"
    log_info "Namespace: $NAMESPACE"
    echo ""
    
    check_prerequisites
    load_environment
    build_images
    
    if [[ "$DEPLOY_ENV" == "production" ]]; then
        push_images
    fi
    
    create_namespace
    deploy_secrets
    deploy_infrastructure
    deploy_application
    run_health_checks
    show_deployment_info
}

# Handle script interruption
trap 'log_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"
