# 1. Cost & Budget Safety Alerts (Rule: Add AWS Budgets before anything expensive)
module "budgets" {
  source             = "./modules/budgets"
  budget_limit_usd   = var.budget_limit_usd
  notification_email = var.budget_notification_email
}

# 2. Networking (VPC, Subnets, NAT Gateway)
module "network" {
  source = "./modules/network"
}

# 3. Authentication (Cognito User Pool + Public Mobile Client)
module "cognito" {
  source      = "./modules/cognito"
  environment = var.environment
}

# 4. Object Storage (Private encrypted S3 Bucket)
module "storage" {
  source        = "./modules/storage"
  bucket_prefix = var.s3_bucket_prefix
  environment   = var.environment
}

# 5. Message Queue (SQS Jobs Queue + DLQ)
module "queue" {
  source      = "./modules/queue"
  environment = var.environment
}

# 6. Database (Private RDS PostgreSQL 16)
module "database" {
  source             = "./modules/database"
  vpc_id             = module.network.vpc_id
  private_subnet_ids = module.network.private_subnet_ids
  db_name            = var.db_name
  db_username        = var.db_username
  environment        = var.environment
}

# 7. Container Registries (ECR for API & Worker)
module "ecr" {
  source = "./modules/ecr"
}

# 8. Kubernetes Cluster (EKS + Node Group + IRSA)
module "eks" {
  source             = "./modules/eks"
  cluster_version    = var.eks_cluster_version
  public_subnet_ids  = module.network.public_subnet_ids
  private_subnet_ids = module.network.private_subnet_ids
  s3_bucket_arn      = module.storage.bucket_arn
  sqs_queue_arn      = module.queue.queue_arn
  environment        = var.environment
}
