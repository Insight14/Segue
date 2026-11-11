import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TERRAFORM_DIR = REPO_ROOT / "infra" / "terraform"


def test_terraform_structure_and_modules() -> None:
    """Ensure all required Terraform files, modules, and scripts exist."""
    assert (TERRAFORM_DIR / "versions.tf").exists()
    assert (TERRAFORM_DIR / "variables.tf").exists()
    assert (TERRAFORM_DIR / "main.tf").exists()
    assert (TERRAFORM_DIR / "outputs.tf").exists()

    required_modules = [
        "budgets",
        "network",
        "cognito",
        "storage",
        "queue",
        "database",
        "ecr",
        "eks",
    ]
    for mod in required_modules:
        mod_dir = TERRAFORM_DIR / "modules" / mod
        assert mod_dir.is_dir(), f"Missing module: {mod}"
        assert (mod_dir / "main.tf").exists(), f"Missing main.tf in module: {mod}"


def test_aws_budgets_configured() -> None:
    """Rule: Add AWS Budgets alerts in the Terraform before anything expensive."""
    budgets_file = TERRAFORM_DIR / "modules" / "budgets" / "main.tf"
    content = budgets_file.read_text()
    assert "aws_budgets_budget" in content
    assert "COST" in content
    assert "notification" in content


def test_eks_version_supported() -> None:
    """Rule: Use a currently supported Kubernetes version on EKS to avoid 6x hourly penalty."""
    vars_file = TERRAFORM_DIR / "variables.tf"
    content = vars_file.read_text()
    assert "eks_cluster_version" in content
    assert "1.30" in content


def test_single_command_scripts_exist_and_executable() -> None:
    """Rule: A single command to deploy and a single command to destroy."""
    deploy_script = TERRAFORM_DIR / "scripts" / "deploy.sh"
    destroy_script = TERRAFORM_DIR / "scripts" / "destroy.sh"

    assert deploy_script.exists()
    assert destroy_script.exists()
    assert os.access(deploy_script, os.X_OK), "deploy.sh must be executable"
    assert os.access(destroy_script, os.X_OK), "destroy.sh must be executable"


def test_github_actions_oidc_deploy_workflow() -> None:
    """Verify GitHub Actions deployment workflow uses OIDC without static AWS credentials."""
    workflow_file = REPO_ROOT / ".github" / "workflows" / "deploy.yml"
    assert workflow_file.exists()
    content = workflow_file.read_text()

    assert "id-token: write" in content
    assert "aws-actions/configure-aws-credentials" in content
    assert "role-to-assume" in content
