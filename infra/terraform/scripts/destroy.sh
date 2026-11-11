#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Convo Glasses: Terraform Teardown ==="

if ! command -v terraform &>/dev/null; then
    echo "Error: terraform CLI is not installed."
    exit 1
fi

cd "$ROOT_DIR"

read -p "CAUTION: This will destroy ALL cloud resources (EKS, RDS, S3, SQS). Type 'destroy' to proceed: " confirm
if [[ "$confirm" == "destroy" ]]; then
    echo "Destroying Terraform resources..."
    terraform destroy -auto-approve
    echo "=== All cloud resources destroyed. Charges stopped. ==="
else
    echo "Teardown aborted."
    exit 0
fi
