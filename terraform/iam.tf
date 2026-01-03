# iam.tf
# IAM user and credentials for Kubernetes watcher

# IAM User for K8s Watcher
resource "aws_iam_user" "k8s_watcher" {
  name = "${var.environment}-k8s-incident-watcher"
  
  tags = {
    Name = "${var.environment}-k8s-incident-watcher"
  }
}

# IAM Policy for Lambda Invocation
resource "aws_iam_policy" "k8s_watcher_policy" {
  name        = "${var.environment}-k8s-watcher-lambda-invoke"
  description = "Allow K8s watcher to invoke Lambda function"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = aws_lambda_function.incident_detector.arn
      }
    ]
  })
}

# Attach Policy to User
resource "aws_iam_user_policy_attachment" "k8s_watcher_attachment" {
  user       = aws_iam_user.k8s_watcher.name
  policy_arn = aws_iam_policy.k8s_watcher_policy.arn
}

# Create Access Keys
resource "aws_iam_access_key" "k8s_watcher" {
  user = aws_iam_user.k8s_watcher.name
}

# IAM Policy for EventBridge PutEvents (for EKS node role)
resource "aws_iam_policy" "eventbridge_put_events" {
  name        = "${var.environment}-eventbridge-put-events"
  description = "Allow EKS nodes to send events to EventBridge"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "events:PutEvents"
        ]
        Resource = "arn:aws:events:${var.aws_region}:${data.aws_caller_identity.current.account_id}:event-bus/default"
      }
    ]
  })
}

# Attach EventBridge policy to EKS node role
resource "aws_iam_role_policy_attachment" "node_eventbridge" {
  role       = "service-runner-ng-2025032714382887"
  policy_arn = aws_iam_policy.eventbridge_put_events.arn
}

# Outputs
output "k8s_watcher_access_key_id" {
  description = "Access Key ID for K8s watcher"
  value       = aws_iam_access_key.k8s_watcher.id
}

output "k8s_watcher_secret_access_key" {
  description = "Secret Access Key for K8s watcher"
  value       = aws_iam_access_key.k8s_watcher.secret
  sensitive   = true
}

output "eventbridge_policy_arn" {
  description = "ARN of EventBridge PutEvents policy"
  value       = aws_iam_policy.eventbridge_put_events.arn
}

output "node_role_name" {
  description = "EKS node role that has EventBridge permissions"
  value       = "service-runner-ng-2025032714382887"
}