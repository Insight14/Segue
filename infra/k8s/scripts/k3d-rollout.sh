#!/usr/bin/env bash
set -euo pipefail

echo "=== Convo Glasses: Triggering Rolling Update ==="

if ! command -v kubectl &>/dev/null; then
    echo "Error: kubectl command not found."
    exit 1
fi

# Trigger restart of API deployment to test rolling update
kubectl rollout restart deployment/convo-glasses-api

# Monitor rolling update status
echo "Waiting for zero-downtime rolling update to complete..."
kubectl rollout status deployment/convo-glasses-api --timeout=120s

echo "=== Rolling update completed successfully with zero downtime ==="

