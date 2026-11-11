variable "cluster_version" {
  type        = string
  description = "Kubernetes version"
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "Public subnet IDs"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs"
}

variable "s3_bucket_arn" {
  type        = string
  description = "ARN of S3 storage bucket"
}

variable "sqs_queue_arn" {
  type        = string
  description = "ARN of SQS queue"
}

variable "environment" {
  type        = string
  description = "Deployment environment"
}
