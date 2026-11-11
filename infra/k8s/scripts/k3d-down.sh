#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="convo-glasses-cluster"

echo "=== Convo Glasses: Tearing Down Local Kubernetes (k3d) Cluster ==="

if ! command -v k3d &>/dev/null; then
    echo "k3d not found. Nothing to tear down."
    exit 0
fi

if k3d cluster list | grep -q "$CLUSTER_NAME"; then
    echo "Deleting cluster '$CLUSTER_NAME'..."
    k3d cluster delete "$CLUSTER_NAME"
    echo "Cluster deleted."
else
    echo "Cluster '$CLUSTER_NAME' does not exist."
fi

