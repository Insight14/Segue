#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="convo-glasses-cluster"

echo "=== Convo Glasses: Starting Local Kubernetes (k3d) Cluster ==="

# Check prerequisites
for cmd in docker k3d kubectl; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "Error: '$cmd' command not found."
        echo "Please install Docker, k3d (https://k3d.io), and kubectl to run local Kubernetes."
        exit 1
    fi
done

# Create cluster if it doesn't already exist
if ! k3d cluster list | grep -q "$CLUSTER_NAME"; then
    echo "Creating k3d cluster '$CLUSTER_NAME'..."
    k3d cluster create "$CLUSTER_NAME" \
        --port "8000:8000@loadbalancer" \
        --port "9000:9000@loadbalancer" \
        --port "9324:9324@loadbalancer" \
        --agents 1
else
    echo "k3d cluster '$CLUSTER_NAME' already exists."
fi

# Build Docker images
echo "Building API and Worker images..."
docker build -t convo-glasses-api:latest -f services/api/Dockerfile services/api
docker build -t convo-glasses-worker:latest -f services/worker/Dockerfile services/worker

# Import images into k3d
echo "Importing images into k3d cluster..."
k3d image import convo-glasses-api:latest convo-glasses-worker:latest -c "$CLUSTER_NAME"

# Apply manifests via Kustomize
echo "Applying Kubernetes manifests..."
kubectl apply -k infra/k8s/overlays/local

# Wait for deployments to be ready
echo "Waiting for deployments to roll out..."
kubectl rollout status deployment/convo-glasses-api --timeout=120s
kubectl rollout status deployment/convo-glasses-worker --timeout=120s

echo "=== Local Kubernetes stack is UP and HEALTHY ==="
echo "API endpoint: http://localhost:8000/healthz"

