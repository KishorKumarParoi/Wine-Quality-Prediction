#!/bin/bash

# Wine Quality Prediction - Docker & Kubernetes Deployment Script
# Usage: ./deploy.sh [docker|k8s] [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="wine-quality-prediction"
DOCKER_IMAGE="kishorkumarparoi/${PROJECT_NAME}"
NAMESPACE="wine-quality"
DEPLOYMENT_NAME="wine-quality-app"

# Functions
log_info() {
    echo -e "${BLUE}ℹ ${1}${NC}"
}

log_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

log_warn() {
    echo -e "${YELLOW}⚠ ${1}${NC}"
}

log_error() {
    echo -e "${RED}✗ ${1}${NC}"
}

# Usage
usage() {
    cat << EOF
Usage: ./deploy.sh [COMMAND] [OPTIONS]

Commands:
    docker          - Docker operations
    k8s             - Kubernetes operations
    help            - Show this help message

Docker Commands:
    ./deploy.sh docker build [TAG]          - Build Docker image
    ./deploy.sh docker run                  - Run container with docker-compose
    ./deploy.sh docker stop                 - Stop container
    ./deploy.sh docker push [TAG]           - Push to registry

Kubernetes Commands:
    ./deploy.sh k8s deploy [NAMESPACE]      - Deploy to Kubernetes
    ./deploy.sh k8s status                  - Check deployment status
    ./deploy.sh k8s logs [POD_NAME]         - View pod logs
    ./deploy.sh k8s scale [REPLICAS]        - Scale deployment
    ./deploy.sh k8s rollback                - Rollback deployment
    ./deploy.sh k8s delete                  - Delete deployment
    ./deploy.sh k8s portforward             - Port forward to local machine

Examples:
    ./deploy.sh docker build latest
    ./deploy.sh docker run
    ./deploy.sh k8s deploy wine-quality
    ./deploy.sh k8s status
    ./deploy.sh k8s logs wine-quality-app-xyz123

EOF
}

# Docker functions
docker_build() {
    local tag="${1:-latest}"
    log_info "Building Docker image: ${DOCKER_IMAGE}:${tag}"
    docker build -t "${DOCKER_IMAGE}:${tag}" .
    log_success "Docker image built successfully"
}

docker_run() {
    log_info "Starting application with Docker Compose"
    docker-compose up -d
    log_success "Application started"
    log_info "Access at: http://localhost:8080"
}

docker_stop() {
    log_info "Stopping application"
    docker-compose down
    log_success "Application stopped"
}

docker_push() {
    local tag="${1:-latest}"
    log_info "Pushing image: ${DOCKER_IMAGE}:${tag}"
    docker push "${DOCKER_IMAGE}:${tag}"
    log_success "Image pushed successfully"
}

# Kubernetes functions
k8s_deploy() {
    local namespace="${1:-wine-quality}"
    
    log_info "Checking kubectl connection"
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    log_success "Connected to cluster"
    
    log_info "Creating namespace: ${namespace}"
    kubectl create namespace "${namespace}" --dry-run=client -o yaml | kubectl apply -f -
    
    log_info "Deploying to Kubernetes (namespace: ${namespace})"
    kubectl apply -k k8s/ --namespace="${namespace}"
    
    log_info "Waiting for deployment to be ready"
    kubectl rollout status deployment/${DEPLOYMENT_NAME} -n "${namespace}" --timeout=5m
    
    log_success "Deployment completed successfully"
    log_info "Deployment status:"
    kubectl get all -n "${namespace}"
}

k8s_status() {
    log_info "Checking deployment status in namespace: ${NAMESPACE}"
    
    if ! kubectl get namespace "${NAMESPACE}" &> /dev/null; then
        log_error "Namespace ${NAMESPACE} not found"
        return 1
    fi
    
    echo ""
    log_info "Pods:"
    kubectl get pods -n "${NAMESPACE}"
    
    echo ""
    log_info "Services:"
    kubectl get svc -n "${NAMESPACE}"
    
    echo ""
    log_info "Deployments:"
    kubectl get deployment -n "${NAMESPACE}"
    
    echo ""
    log_info "HPA Status:"
    kubectl get hpa -n "${NAMESPACE}"
}

k8s_logs() {
    local pod_name="${1:-}"
    
    if [ -z "${pod_name}" ]; then
        log_info "Available pods:"
        kubectl get pods -n "${NAMESPACE}"
        log_warn "Please specify a pod name"
        exit 1
    fi
    
    log_info "Fetching logs for pod: ${pod_name}"
    kubectl logs -f "${pod_name}" -n "${NAMESPACE}"
}

k8s_scale() {
    local replicas="${1:-3}"
    
    if ! [[ "${replicas}" =~ ^[0-9]+$ ]]; then
        log_error "Invalid replica count: ${replicas}"
        exit 1
    fi
    
    log_info "Scaling deployment to ${replicas} replicas"
    kubectl scale deployment "${DEPLOYMENT_NAME}" --replicas="${replicas}" -n "${NAMESPACE}"
    log_success "Scaled successfully"
}

k8s_rollback() {
    log_info "Rolling back deployment"
    kubectl rollout undo deployment/"${DEPLOYMENT_NAME}" -n "${NAMESPACE}"
    kubectl rollout status deployment/"${DEPLOYMENT_NAME}" -n "${NAMESPACE}"
    log_success "Rollback completed"
}

k8s_delete() {
    log_warn "Are you sure you want to delete the deployment? This cannot be undone."
    read -p "Type 'yes' to confirm: " confirm
    
    if [ "${confirm}" != "yes" ]; then
        log_info "Deletion cancelled"
        return
    fi
    
    log_info "Deleting deployment from namespace: ${NAMESPACE}"
    kubectl delete -k k8s/ --namespace="${NAMESPACE}"
    log_success "Deployment deleted"
}

k8s_portforward() {
    local local_port="${1:-8080}"
    local remote_port="${2:-8080}"
    
    log_info "Setting up port forward: localhost:${local_port} -> pod:${remote_port}"
    log_info "Application will be available at: http://localhost:${local_port}"
    
    # Get first pod
    local pod=$(kubectl get pods -n "${NAMESPACE}" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -z "${pod}" ]; then
        log_error "No pods found in namespace ${NAMESPACE}"
        exit 1
    fi
    
    kubectl port-forward "pod/${pod}" "${local_port}:${remote_port}" -n "${NAMESPACE}"
}

# Main logic
main() {
    local command="${1:-}"
    
    if [ -z "${command}" ] || [ "${command}" = "help" ]; then
        usage
        exit 0
    fi
    
    case "${command}" in
        docker)
            local subcommand="${2:-}"
            case "${subcommand}" in
                build)
                    docker_build "${3:-latest}"
                    ;;
                run)
                    docker_run
                    ;;
                stop)
                    docker_stop
                    ;;
                push)
                    docker_push "${3:-latest}"
                    ;;
                *)
                    log_error "Unknown docker command: ${subcommand}"
                    usage
                    exit 1
                    ;;
            esac
            ;;
        k8s)
            local subcommand="${2:-}"
            case "${subcommand}" in
                deploy)
                    k8s_deploy "${3:-wine-quality}"
                    ;;
                status)
                    k8s_status
                    ;;
                logs)
                    k8s_logs "${3}"
                    ;;
                scale)
                    k8s_scale "${3:-3}"
                    ;;
                rollback)
                    k8s_rollback
                    ;;
                delete)
                    k8s_delete
                    ;;
                portforward)
                    k8s_portforward "${3:-8080}" "${4:-8080}"
                    ;;
                *)
                    log_error "Unknown k8s command: ${subcommand}"
                    usage
                    exit 1
                    ;;
            esac
            ;;
        *)
            log_error "Unknown command: ${command}"
            usage
            exit 1
            ;;
    esac
}

# Run main
main "$@"
