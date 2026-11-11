from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
K8S_BASE = REPO_ROOT / "infra" / "k8s" / "base"
K8S_OVERLAYS = REPO_ROOT / "infra" / "k8s" / "overlays"


def test_all_k8s_manifests_valid_yaml() -> None:
    """Ensure all base and overlay manifests parse cleanly as valid Kubernetes YAML."""
    manifest_files = list(K8S_BASE.glob("*.yaml")) + list(K8S_OVERLAYS.rglob("*.yaml"))
    assert len(manifest_files) >= 10

    for f in manifest_files:
        content = f.read_text()
        docs = list(yaml.safe_load_all(content))
        assert len(docs) >= 1, f"Empty manifest file: {f.name}"
        for doc in docs:
            if doc is not None:
                assert "apiVersion" in doc, f"Missing apiVersion in {f.name}"
                assert "kind" in doc, f"Missing kind in {f.name}"
                if doc.get("kind") != "Kustomization":
                    assert "metadata" in doc, f"Missing metadata in {f.name}"


def test_api_deployment_spec() -> None:
    """Verify production API deployment satisfies zero-downtime rolling update,
    probes, and non-root security.
    """
    api_deploy_file = K8S_BASE / "api-deployment.yaml"
    doc = yaml.safe_load(api_deploy_file.read_text())

    assert doc["kind"] == "Deployment"
    assert doc["metadata"]["name"] == "convo-glasses-api"

    # 1. Rolling update strategy
    strategy = doc["spec"]["strategy"]
    assert strategy["type"] == "RollingUpdate"
    assert strategy["rollingUpdate"]["maxSurge"] == 1
    assert strategy["rollingUpdate"]["maxUnavailable"] == 0

    # 2. Pod security context
    pod_sec = doc["spec"]["template"]["spec"]["securityContext"]
    assert pod_sec["runAsNonRoot"] is True
    assert pod_sec["runAsUser"] == 1001

    # 3. Container probes & security
    container = doc["spec"]["template"]["spec"]["containers"][0]
    assert container["name"] == "api"

    # Liveness & Readiness probes
    assert container["livenessProbe"]["httpGet"]["path"] == "/healthz"
    assert container["readinessProbe"]["httpGet"]["path"] == "/readyz"

    # Drop capabilities & non-root container
    assert "ALL" in container["securityContext"]["capabilities"]["drop"]
    assert container["securityContext"]["allowPrivilegeEscalation"] is False

    # Resources
    assert "cpu" in container["resources"]["requests"]
    assert "memory" in container["resources"]["requests"]
    assert "cpu" in container["resources"]["limits"]
    assert "memory" in container["resources"]["limits"]


def test_worker_deployment_spec() -> None:
    """Verify worker deployment runs non-root and has health probing."""
    worker_deploy_file = K8S_BASE / "worker-deployment.yaml"
    doc = yaml.safe_load(worker_deploy_file.read_text())

    assert doc["kind"] == "Deployment"
    assert doc["metadata"]["name"] == "convo-glasses-worker"

    pod_sec = doc["spec"]["template"]["spec"]["securityContext"]
    assert pod_sec["runAsNonRoot"] is True
    assert pod_sec["runAsUser"] == 1001

    container = doc["spec"]["template"]["spec"]["containers"][0]
    assert "livenessProbe" in container


def test_hpa_spec() -> None:
    """Verify Horizontal Pod Autoscaler targets API deployment with scaling limits."""
    hpa_file = K8S_BASE / "hpa.yaml"
    doc = yaml.safe_load(hpa_file.read_text())

    assert doc["kind"] == "HorizontalPodAutoscaler"
    assert doc["spec"]["scaleTargetRef"]["name"] == "convo-glasses-api"
    assert doc["spec"]["minReplicas"] == 2
    assert doc["spec"]["maxReplicas"] == 5
    assert doc["spec"]["metrics"][0]["resource"]["name"] == "cpu"


def test_production_dockerfiles_structure() -> None:
    """Verify production Dockerfiles are multi-stage, non-root, and include healthchecks."""
    api_dockerfile = (REPO_ROOT / "services" / "api" / "Dockerfile").read_text()
    worker_dockerfile = (REPO_ROOT / "services" / "worker" / "Dockerfile").read_text()

    # Multi-stage check
    assert "AS builder" in api_dockerfile
    assert "AS runner" in api_dockerfile
    assert "AS builder" in worker_dockerfile
    assert "AS runner" in worker_dockerfile

    # Non-root user check
    assert "USER appuser" in api_dockerfile
    assert "USER appuser" in worker_dockerfile
    assert "1001" in api_dockerfile
    assert "1001" in worker_dockerfile

    # Healthcheck check
    assert "HEALTHCHECK" in api_dockerfile
    assert "/healthz" in api_dockerfile
    assert "HEALTHCHECK" in worker_dockerfile
