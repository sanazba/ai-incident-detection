variable "aws_region" {
  description = "AWS region for deployment (us-east-1, us-west-2, or eu-west-1 recommended for Bedrock)"
  type        = string
  default     = "eu-west-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "claude_api_key" {
  description = "Anthropic Claude API key"
  type        = string
  sensitive   = true
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for notifications"
  type        = string
  sensitive   = true
}

variable "pagerduty_integration_key" {
  description = "PagerDuty integration key (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "k8s_cluster_name" {
  description = "Name of the Kubernetes cluster to monitor"
  type        = string
  default     = "service-runner"
}

variable "rds_instance_ids" {
  description = "List of RDS instance IDs to monitor"
  type        = list(string)
  default     = []
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 60
}

variable "lambda_memory" {
  description = "Lambda function memory in MB"
  type        = number
  default     = 512
}

variable "use_bedrock" {
  description = "Use AWS Bedrock for Claude (true) or Anthropic API (false)"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 7
}