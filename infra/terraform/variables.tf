variable "aws_region" {
  type        = string
  description = "AWS region for deployment"
  default     = "us-east-1"
}

variable "environment" {
  type        = string
  description = "Deployment environment (e.g., staging, prod)"
  default     = "staging"
}

variable "budget_limit_usd" {
  type        = number
  description = "Monthly budget limit in USD to prevent unexpected cloud costs"
  default     = 25
}

variable "budget_notification_email" {
  type        = string
  description = "Email address for AWS budget threshold alert notifications"
  default     = "alerts@example.com"
}

variable "eks_cluster_version" {
  type        = string
  description = "Currently supported Kubernetes version on EKS to avoid extended support charges"
  default     = "1.30"
}

variable "db_name" {
  type        = string
  description = "PostgreSQL database name"
  default     = "convo_glasses"
}

variable "db_username" {
  type        = string
  description = "PostgreSQL administrator username"
  default     = "convouser"
}

variable "s3_bucket_prefix" {
  type        = string
  description = "Prefix for private S3 storage bucket"
  default     = "convo-glasses-documents"
}
