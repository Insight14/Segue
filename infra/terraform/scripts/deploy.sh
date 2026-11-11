#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Convo Glasses: Terraform Deploy ==="

if ! command -v terraform &>/dev/null; then
    echo "Error: terraform CLI is not installed."
    echo "Install terraform: https://developer.hashicorp.com/terraform/install"
    exit 1
fi

cd "$ROOT_DIR"

echo "Initializing Terraform..."
terraform init

echo "Generating execution plan..."
terraform plan -out=tfplan

read -p "Do you want to apply this plan to AWS? (yes/no): " choice
if [[ "$choice" == "yes" ]]; then
    echo "Applying Terraform plan..."
    terraform apply tfplan
    echo "=== Deployment Succeeded ==="
else
    echo "Deployment aborted."
    exit 0
fi
