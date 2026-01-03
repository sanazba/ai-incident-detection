# CloudWatch alarms and metrics for monitoring

# SNS Topic for CloudWatch Alarms
resource "aws_sns_topic" "incident_alerts" {
  name = "${var.environment}-incident-alerts"
  
  tags = {
    Name = "${var.environment}-incident-alerts"
  }
}

# SNS Topic Subscription to Lambda
resource "aws_sns_topic_subscription" "lambda" {
  topic_arn = aws_sns_topic.incident_alerts.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.incident_detector.arn
}

# Lambda Permission for SNS
resource "aws_lambda_permission" "sns" {
  statement_id  = "AllowSNSInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.incident_detector.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.incident_alerts.arn
}

# CloudWatch Alarm for Lambda Errors
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.environment}-incident-detector-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "This metric monitors Lambda function errors"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.incident_detector.function_name
  }

  alarm_actions = [aws_sns_topic.incident_alerts.arn]
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "incident_detection" {
  dashboard_name = "${var.environment}-ai-incident-detection"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", { stat = "Sum", label = "Lambda Invocations" }],
            [".", "Errors", { stat = "Sum", label = "Errors" }],
            [".", "Duration", { stat = "Average", label = "Avg Duration (ms)" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Lambda Metrics"
        }
      }
    ]
  })
}

# Outputs
output "sns_topic_arn" {
  description = "ARN of the SNS topic for incident alerts"
  value       = aws_sns_topic.incident_alerts.arn
}