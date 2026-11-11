resource "aws_sqs_queue" "dlq" {
  name                      = "convo-glasses-jobs-dlq-${var.environment}"
  message_retention_seconds = 1209600 # 14 days
}

resource "aws_sqs_queue" "jobs" {
  name                      = "convo-glasses-jobs-${var.environment}"
  visibility_timeout_seconds = 300
  message_retention_seconds = 86400 # 1 day

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })
}
