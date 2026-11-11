# AWS Terraform Infrastructure & Deployment

Terraform configurations for production AWS infrastructure (EKS, RDS, S3, SQS, Cognito, ECR, IAM, and AWS Budgets).

## Resources Provisioned

- **AWS Budgets**: Automated cost safety guardrails notifying if spend exceeds 50%, 80%, or 100% of the monthly threshold.
- **Networking**: VPC with 2 public subnets, 2 private subnets, Internet Gateway, and single NAT Gateway.
- **Cognito**: User Pool with email sign-in and public Mobile App Client (no client secret).
- **S3 Bucket**: Encrypted (AES256), private, public access blocked, CORS enabled for mobile presigned uploads.
- **SQS**: FIFO/Standard jobs queue with Dead-Letter Queue (DLQ) redrive policy.
- **RDS PostgreSQL 16**: Private subnet group, `db.t4g.micro` with gp3 storage, automated credentials generation in Secrets Manager.
- **ECR**: Registries for `convo-glasses-api` and `convo-glasses-worker` with lifecycle rules expiring images older than 14 days.
- **EKS**: Kubernetes 1.30 (standard support tier), managed node group (`t3.medium`), OpenID Connect provider for IAM Roles for Service Accounts (IRSA).

---

## Documented Monthly Cost Estimate

| Resource | Configuration | Estimated Monthly Cost |
|---|---|---|
| **EKS Control Plane** | Kubernetes 1.30 (standard support: $0.10/hr) | ~$73.00 |
| **EKS Worker Node** | 1x `t3.medium` on-demand instance | ~$30.36 |
| **NAT Gateway** | 1 gateway in public subnet ($0.045/hr + data) | ~$32.40 |
| **RDS PostgreSQL** | `db.t4g.micro` (Single-AZ, 20 GB gp3) | ~$15.00 *(Free Tier eligible)* |
| **S3 Storage** | Under 10 GB standard storage + PUT/GET | < $0.50 *(Free Tier eligible)* |
| **SQS** | Standard queue requests | < $0.10 *(1M requests free)* |
| **Cognito** | Up to 50,000 monthly active users | $0.00 *(Always free tier)* |
| **ECR** | Storage under 5 GB (with lifecycle policy) | < $0.50 |
| **Total (Continuous 24/7)** | | **~$151.00 / month** |
| **On-Demand Demo Run** | Active for ~2 hours then destroyed | **~$0.42 total** |

> [!IMPORTANT]
> To avoid unnecessary cloud charges, daily development should use Docker Compose or local k3d. Only deploy to AWS for live demos, and destroy resources immediately after demoing.

---

## Deployment & Teardown Commands

### 1. Deploy
```bash
./infra/terraform/scripts/deploy.sh
```

### 2. Teardown (Stop all cloud charges)
```bash
./infra/terraform/scripts/destroy.sh
```
