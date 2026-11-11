variable "budget_limit_usd" {
  type        = number
  description = "Budget limit in USD"
}

variable "notification_email" {
  type        = string
  description = "Email recipient for budget alerts"
}
