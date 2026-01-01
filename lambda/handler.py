"""
AI-Driven Incident Detection Lambda Handler
Analyzes CloudWatch events using Claude AI via AWS Bedrock
"""
import json
import os
import boto3
from datetime import datetime
from claude_agent import ClaudeIncidentAgent
from slack_notifier import SlackNotifier

# Make PagerDuty optional
try:
    from pagerduty_notifier import PagerDutyNotifier
    PAGERDUTY_AVAILABLE = True
except (ImportError, AttributeError):
    PAGERDUTY_AVAILABLE = False
    print("PagerDuty notifier not available - will skip PagerDuty notifications")

def lambda_handler(event, context):
    """
    Main Lambda handler for incident detection and analysis
    """
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # Check if using Bedrock or Anthropic API
        use_bedrock = os.environ.get('USE_BEDROCK', '1') == '1'
        aws_region = os.environ.get('AWS_REGION', 'us-east-1')
        
        # Initialize AI agent
        if use_bedrock:
            # Using AWS Bedrock - no API key needed
            agent = ClaudeIncidentAgent(use_bedrock=True, region=aws_region)
            print("Using AWS Bedrock for Claude AI")
        else:
            # Using Anthropic API directly
            claude_api_key = os.environ['CLAUDE_API_KEY']
            agent = ClaudeIncidentAgent(api_key=claude_api_key, use_bedrock=False)
            print("Using Anthropic API for Claude AI")
        
        # Parse the incoming event
        incident_data = parse_event(event)
        
        # Use Claude to analyze the incident
        analysis = agent.analyze_incident(incident_data)
        
        # Determine severity and actions
        severity = analysis['severity']
        
        # Send notifications based on severity (pass incident_data for K8s context)
        send_notifications(analysis, severity, incident_data)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Incident analyzed successfully',
                'severity': severity,
                'incident_id': analysis['incident_id']
            })
        }
        
    except Exception as e:
        print(f"Error processing incident: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def parse_event(event):
    """Parse CloudWatch/EventBridge event into structured incident data"""
    
    # Handle CloudWatch Alarm events
    if 'detail-type' in event and 'CloudWatch Alarm' in event['detail-type']:
        alarm = event['detail']
        return {
            'source': 'cloudwatch_alarm',
            'type': 'infrastructure',
            'timestamp': event['time'],
            'alarm_name': alarm.get('alarmName', 'Unknown'),
            'state': alarm.get('state', {}).get('value', 'UNKNOWN'),
            'reason': alarm.get('state', {}).get('reason', ''),
            'metrics': alarm.get('configuration', {}).get('metrics', []),
            'namespace': alarm.get('configuration', {}).get('namespace', ''),
            'raw_event': event
        }
    
    # Handle custom K8s events from watcher
    elif 'detail-type' in event and 'K8s Pod' in event['detail-type']:
        detail = event['detail']
        return {
            'source': 'kubernetes',
            'type': 'pod_failure',
            'timestamp': event.get('time', datetime.utcnow().isoformat()),
            'pod_name': detail.get('pod_name', detail.get('podName', 'Unknown')),
            'namespace': detail.get('namespace', 'default'),
            'status': detail.get('status', 'Unknown'),
            'reason': detail.get('reason', ''),
            'message': detail.get('message', ''),
            'cluster_name': detail.get('cluster_name', 'Unknown'),
            'node_name': detail.get('node_name', ''),
            'restart_count': detail.get('restart_count', 0),
            'raw_event': event
        }
    
    # Handle RDS events
    elif 'detail-type' in event and 'RDS' in event['detail-type']:
        detail = event['detail']
        return {
            'source': 'rds',
            'type': 'database_issue',
            'timestamp': event['time'],
            'db_instance': detail.get('SourceIdentifier', 'Unknown'),
            'event_category': detail.get('EventCategories', []),
            'message': detail.get('Message', ''),
            'raw_event': event
        }
    
    # Handle events from EventBridge (our K8s watcher)
    elif 'Source' in event:
        # Direct EventBridge event format
        detail = json.loads(event.get('Detail', '{}')) if isinstance(event.get('Detail'), str) else event.get('Detail', {})
        return {
            'source': detail.get('source', 'kubernetes'),
            'type': detail.get('type', 'pod_failure'),
            'timestamp': detail.get('timestamp', event.get('Time', datetime.utcnow().isoformat())),
            'pod_name': detail.get('pod_name', 'Unknown'),
            'namespace': detail.get('namespace', 'default'),
            'status': detail.get('status', 'Unknown'),
            'reason': detail.get('reason', ''),
            'message': detail.get('message', ''),
            'cluster_name': detail.get('cluster_name', 'Unknown'),
            'node_name': detail.get('node_name', ''),
            'restart_count': detail.get('restart_count', 0),
            'raw_event': event
        }
    
    # Generic fallback
    else:
        return {
            'source': 'unknown',
            'type': 'generic',
            'timestamp': datetime.utcnow().isoformat(),
            'raw_event': event
        }


def send_notifications(analysis, severity, incident_data):
    """Send notifications to Slack and/or PagerDuty based on severity"""
    slack_webhook = os.environ.get('SLACK_WEBHOOK_URL')
    pagerduty_key = os.environ.get('PAGERDUTY_INTEGRATION_KEY')
    
    # Merge incident data into analysis for Slack (add K8s context)
    analysis_with_context = {
        **analysis,
        'pod_name': incident_data.get('pod_name', ''),
        'namespace': incident_data.get('namespace', ''),
        'reason': incident_data.get('reason', ''),
        'cluster_name': incident_data.get('cluster_name', ''),
        'node_name': incident_data.get('node_name', ''),
        'restart_count': incident_data.get('restart_count', 0)
    }
    
    # Always send to Slack
    if slack_webhook:
        try:
            slack = SlackNotifier(slack_webhook)
            slack.send_incident_alert(analysis_with_context)
            print("Slack notification sent successfully")
        except Exception as e:
            print(f"Error sending Slack notification: {str(e)}")
    else:
        print("Slack webhook not configured")
    
    # Send to PagerDuty for high severity incidents (if available)
    if PAGERDUTY_AVAILABLE and pagerduty_key and pagerduty_key != "" and severity in ['critical', 'high']:
        try:
            pd = PagerDutyNotifier(pagerduty_key)
            pd.create_incident(analysis)
            print("PagerDuty notification sent successfully")
        except Exception as e:
            print(f"Error sending PagerDuty notification: {str(e)}")
    elif not PAGERDUTY_AVAILABLE:
        print("PagerDuty integration not available, skipping")
    elif not pagerduty_key or pagerduty_key == "":
        print("PagerDuty not configured, skipping")