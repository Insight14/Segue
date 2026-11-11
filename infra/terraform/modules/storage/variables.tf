variable "bucket_prefix" {
  type        = string
  description = "Prefix for the S3 bucket name"
}

variable "environment" {
  type        = string
  description = "Deployment environment"
}
