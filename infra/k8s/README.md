# Kubernetes Infrastructure (k3d & EKS)

This directory contains the production-grade Kubernetes manifests and Kustomize overlays for Convo Glasses.

## Architecture

- **Base (`infra/k8s/base/`)**:
  - `api-deployment.yaml`: FastAPI deployment (2 replicas, zero-downtime `RollingUpdate` with `maxSurge: 1, maxUnavailable: 0`, non-root security context `UID: 1001`, liveness `/healthz`, readiness `/readyz`, CPU/memory limits).
  - `api-service.yaml`: ClusterIP service exposing the API on port 8000.
  - `worker-deployment.yaml`: Background SQS consumer deployment with liveness checking.
  - `postgres.yaml`: StatefulSet and Service for local PostgreSQL.
  - `minio.yaml`: Deployment and Service for local MinIO S3 object storage.
  - `elasticmq.yaml`: Deployment and Service for local ElasticMQ SQS message queue.
  - `hpa.yaml`: HorizontalPodAutoscaler scaling API pods from 2 to 5 based on 70% CPU target utilization.
  - `configmap.yaml` & `secrets.yaml`: Declarative environment variables and credentials.

- **Overlays (`infra/k8s/overlays/`)**:
  - `local/`: Local k3d cluster deployment running the full stack including local DB/S3/SQS.
  - `aws/`: Production AWS EKS deployment targeting managed RDS, S3, and SQS.

## Running Locally on k3d

Prerequisites:
- [Docker](https://docs.docker.com/get-docker/)
- [k3d](https://k3d.io)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)

### Commands

1. **Spin up local cluster and deploy full stack**:
   ```bash
   make k8s-up
   ```
   Creates the `convo-glasses-cluster` k3d cluster, builds production multi-stage Docker images, imports them into the cluster, applies the Kustomize manifests, and waits for rollout.

2. **Trigger and verify zero-downtime rolling update**:
   ```bash
   make k8s-rollout
   ```
   Triggers `kubectl rollout restart deployment/convo-glasses-api` and verifies that service remains responsive without dropped requests.

3. **Tear down cluster**:
   ```bash
   make k8s-down
   ```
