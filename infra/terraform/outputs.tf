output "cognito_user_pool_id" {
  value       = module.cognito.user_pool_id
  description = "Cognito User Pool ID"
}

output "cognito_client_id" {
  value       = module.cognito.client_id
  description = "Cognito App Client ID for Mobile"
}

output "s3_bucket_name" {
  value       = module.storage.bucket_name
  description = "S3 documents bucket"
}

output "sqs_queue_url" {
  value       = module.queue.queue_url
  description = "SQS job queue URL"
}

output "database_endpoint" {
  value       = module.database.endpoint
  description = "RDS PostgreSQL endpoint"
}

output "database_secret_arn" {
  value       = module.database.db_credentials_secret_arn
  description = "Secrets Manager secret ARN containing DB credentials"
}

output "api_ecr_repository" {
  value       = module.ecr.api_repository_url
  description = "ECR repository for API"
}

output "worker_ecr_repository" {
  value       = module.ecr.worker_repository_url
  description = "ECR repository for Worker"
}

output "eks_cluster_name" {
  value       = module.eks.cluster_name
  description = "EKS cluster name"
}

output "eks_cluster_endpoint" {
  value       = module.eks.cluster_endpoint
  description = "EKS cluster API endpoint"
}
