# EventBridge configuration for routing incidents to Lambda

# EventBridge Rule for K8s Pod Failures
resource "aws_cloudwatch_event_rule" "incident_events" {
  name        = "${var.environment}-k8s-incident-events"
  description = "Captures Kubernetes and infrastructure incidents"

  event_pattern = jsonencode({
    source = [
      "k8s.cluster",
      "k8s.production",
      "k8s.test",
      "aws.cloudwatch",
      "aws.rds",
      "aws.ec2"
    ]
    detail-type = [
      "K8s Pod Failure",
      "K8s Pod Event",
      "CloudWatch Alarm State Change",
      "RDS DB Instance Event",
      "EC2 Instance State-change Notification"
    ]
  })

  tags = {
    Name = "${var.environment}-incident-events"
  }
}

# EventBridge Target - Lambda
resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.incident_events.name
  target_id = "IncidentDetectorLambda"
  arn       = aws_lambda_function.incident_detector.arn
}

# Additional EventBridge Rule for CloudWatch Alarms
resource "aws_cloudwatch_event_rule" "cloudwatch_alarms" {
  name        = "${var.environment}-cloudwatch-alarm-events"
  description = "Captures CloudWatch alarm state changes"

  event_pattern = jsonencode({
    source      = ["aws.cloudwatch"]
    detail-type = ["CloudWatch Alarm State Change"]
    detail = {
      state = {
        value = ["ALARM"]
      }
    }
  })

  tags = {
    Name = "${var.environment}-cloudwatch-alarms"
  }
}

# CloudWatch Alarms Target
resource "aws_cloudwatch_event_target" "cloudwatch_alarms_target" {
  rule      = aws_cloudwatch_event_rule.cloudwatch_alarms.name
  target_id = "CloudWatchAlarmsToLambda"
  arn       = aws_lambda_function.incident_detector.arn
}

# Lambda Permission for CloudWatch Alarms
resource "aws_lambda_permission" "cloudwatch_alarms" {
  statement_id  = "AllowCloudWatchAlarmsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.incident_detector.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.cloudwatch_alarms.arn
}

# Outputs
output "eventbridge_rule_name" {
  description = "Name of the EventBridge rule"
  value       = aws_cloudwatch_event_rule.incident_events.name
}

output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule"
  value       = aws_cloudwatch_event_rule.incident_events.arn
}