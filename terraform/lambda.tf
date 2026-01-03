# Lambda function configuration for incident detection

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.environment}-ai-incident-detection-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# IAM Policy for Lambda
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.environment}-ai-incident-detection-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:DescribeAlarms",
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances",
          "rds:DescribeEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-*"
      },
      {
        Effect = "Allow"
        Action = [
          "aws-marketplace:ViewSubscriptions",
          "aws-marketplace:Subscribe"
        ]
        Resource = "*"
      }
    ]
  })
}

# Package Lambda function
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda"
  output_path = "${path.module}/lambda_function.zip"
  
  excludes = [
    "test_*.py",
    "test_*.json",
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    "venv",
    ".venv"
  ]
}

# Lambda Layer for dependencies
resource "aws_lambda_layer_version" "dependencies" {
  filename            = "${path.module}/lambda_layer.zip"
  layer_name          = "${var.environment}-ai-incident-detection-dependencies"
  compatible_runtimes = ["python3.11"]
  
  lifecycle {
    ignore_changes = [filename]
  }
}

# Lambda Function
resource "aws_lambda_function" "incident_detector" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${var.environment}-ai-incident-detector"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handler.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory

  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      CLAUDE_API_KEY            = var.claude_api_key
      SLACK_WEBHOOK_URL         = var.slack_webhook_url
      PAGERDUTY_INTEGRATION_KEY = var.pagerduty_integration_key
      ENVIRONMENT               = var.environment
      USE_BEDROCK               = var.use_bedrock ? "1" : "0"
      K8S_CLUSTER_NAME          = var.k8s_cluster_name
    }
  }

  tags = {
    Name = "${var.environment}-ai-incident-detector"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.incident_detector.function_name}"
  retention_in_days = var.log_retention_days
}

# Lambda Permission for EventBridge
resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.incident_detector.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.incident_events.arn
}

# Outputs
output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.incident_detector.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.incident_detector.arn
}

output "lambda_role_arn" {
  description = "ARN of the Lambda IAM role"
  value       = aws_iam_role.lambda_role.arn
}

resource "aws_iam_role_policy_attachment" "lambda_marketplace" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AWSMarketplaceRead-only"
}