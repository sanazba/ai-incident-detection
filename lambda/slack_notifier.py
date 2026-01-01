"""
Slack Notification Handler for AI Incident Detection System
Sends formatted incident alerts and analysis to Slack channels
"""
import os
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional


class SlackNotifier:
    """
    Handles Slack notifications for incident alerts
    Supports both webhook URLs and Slack Bot API
    """

    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize Slack notifier

        Args:
            webhook_url: Slack webhook URL (if None, gets from environment)
        """
        self.webhook_url = webhook_url or os.environ.get('SLACK_WEBHOOK_URL')
        if not self.webhook_url:
            raise ValueError("Slack webhook URL must be provided or set in SLACK_WEBHOOK_URL environment variable")

    def send_incident_alert(self, analysis: Dict[str, Any]) -> bool:
        """
        Send incident alert to Slack

        Args:
            analysis: Dict containing incident analysis from Claude AI
                     Expected keys: severity, incident_id, summary, recommendations, timestamp, source

        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        try:
            # Extract incident details
            severity = analysis.get('severity', 'UNKNOWN').upper()
            incident_id = analysis.get('incident_id', 'UNKNOWN')
            # Map different field names from Claude agent
            summary = analysis.get('summary') or analysis.get('title', 'No summary provided')
            recommendations = analysis.get('recommendations') or analysis.get('immediate_actions', [])
            timestamp = analysis.get('timestamp', datetime.utcnow().isoformat())
            source = analysis.get('source', 'Unknown')
            
            # Extract K8s specific fields
            pod_name = analysis.get('pod_name', '')
            namespace = analysis.get('namespace', '')
            reason = analysis.get('reason', '')

            # Create Slack message payload
            message_payload = self._build_message_payload(
                severity=severity,
                incident_id=incident_id,
                summary=summary,
                recommendations=recommendations,
                timestamp=timestamp,
                source=source,
                pod_name=pod_name,
                namespace=namespace,
                reason=reason
            )

            # Send to Slack
            response = requests.post(
                self.webhook_url,
                json=message_payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )

            if response.status_code == 200:
                print(f"✅ Slack notification sent successfully for incident {incident_id}")
                return True
            else:
                print(f"❌ Failed to send Slack notification. Status: {response.status_code}, Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error sending Slack notification: {str(e)}")
            return False

    def _build_message_payload(self, severity: str, incident_id: str, summary: str,
                              recommendations: list, timestamp: str, source: str,
                              pod_name: str = '', namespace: str = '', reason: str = '') -> Dict[str, Any]:
        """
        Build Slack message payload with rich formatting

        Returns:
            Dict: Slack message payload
        """
        # Determine color and emoji based on severity
        color, emoji = self._get_severity_formatting(severity)

        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
        except:
            formatted_time = timestamp

        # Build recommendations text
        recommendations_text = ""
        if recommendations:
            recommendations_text = "\n".join([f"• {rec}" for rec in recommendations[:5]])  # Limit to 5
            if len(recommendations) > 5:
                recommendations_text += f"\n• ... and {len(recommendations) - 5} more recommendations"
        else:
            recommendations_text = "No specific recommendations provided"

        # Build fields list dynamically
        fields = [
            {
                "type": "mrkdwn",
                "text": f"*Incident ID:*\n{incident_id}"
            },
            {
                "type": "mrkdwn",
                "text": f"*Source:*\n{source}"
            }
        ]
        
        # Add pod name if available
        if pod_name:
            fields.append({
                "type": "mrkdwn",
                "text": f"*Pod Name:*\n`{pod_name}`"
            })
        
        # Add namespace if available
        if namespace:
            fields.append({
                "type": "mrkdwn",
                "text": f"*Namespace:*\n`{namespace}`"
            })
        
        # Add reason if available
        if reason:
            fields.append({
                "type": "mrkdwn",
                "text": f"*Reason:*\n`{reason}`"
            })
        
        # Always add severity and time
        fields.extend([
            {
                "type": "mrkdwn",
                "text": f"*Severity:*\n{severity}"
            },
            {
                "type": "mrkdwn",
                "text": f"*Time:*\n{formatted_time}"
            }
        ])

        # Create main message block
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Incident Alert - {severity}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": fields
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:*\n{summary}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*AI Recommendations:*\n{recommendations_text}"
                }
            }
        ]

        # Add action buttons for high/critical incidents
        if severity in ['HIGH', 'CRITICAL']:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🚨 Acknowledge",
                            "emoji": True
                        },
                        "style": "danger",
                        "value": f"ack_{incident_id}",
                        "action_id": "acknowledge_incident"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📊 View Details",
                            "emoji": True
                        },
                        "value": f"details_{incident_id}",
                        "action_id": "view_incident_details"
                    }
                ]
            })

        # Add divider
        blocks.append({"type": "divider"})

        # Build final payload
        payload = {
            "text": f"{emoji} {severity} Incident Alert: {incident_id}",  # Fallback text
            "blocks": blocks,
            "attachments": [
                {
                    "color": color,
                    "text": f"Incident {incident_id} detected and analyzed by AI",
                    "footer": "AI Incident Detection System",
                    "footer_icon": "https://cdn-icons-png.flaticon.com/512/4712/4712139.png",
                    "ts": int(datetime.utcnow().timestamp())
                }
            ]
        }

        return payload

    def _get_severity_formatting(self, severity: str) -> tuple:
        """
        Get color and emoji for severity level

        Returns:
            tuple: (color, emoji)
        """
        severity_map = {
            'LOW': ('#36a64f', '🟢'),       # Green
            'MEDIUM': ('#ff9900', '🟡'),     # Orange
            'HIGH': ('#ff0000', '🔴'),       # Red
            'CRITICAL': ('#8B0000', '🚨'),   # Dark Red
            'UNKNOWN': ('#808080', '❓')     # Gray
        }

        return severity_map.get(severity.upper(), severity_map['UNKNOWN'])

    def send_test_message(self) -> bool:
        """
        Send a test message to verify Slack integration

        Returns:
            bool: True if test message sent successfully
        """
        test_analysis = {
            'severity': 'LOW',
            'incident_id': f'TEST-{int(datetime.utcnow().timestamp())}',
            'summary': 'This is a test message from the AI Incident Detection System',
            'recommendations': ['Verify Slack integration is working', 'Check webhook URL configuration'],
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'Test System'
        }

        return self.send_incident_alert(test_analysis)

    def send_system_notification(self, message: str, level: str = "INFO") -> bool:
        """
        Send a system notification (non-incident)

        Args:
            message: Message to send
            level: Notification level (INFO, WARNING, ERROR)

        Returns:
            bool: True if notification sent successfully
        """
        try:
            emoji_map = {
                'INFO': '💡',
                'WARNING': '⚠️',
                'ERROR': '❌'
            }

            emoji = emoji_map.get(level.upper(), '💡')

            payload = {
                "text": f"{emoji} System Notification",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"{emoji} *System Notification - {level}*\n\n{message}"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"AI Incident Detection System • {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                            }
                        ]
                    }
                ]
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )

            return response.status_code == 200

        except Exception as e:
            print(f"❌ Error sending system notification: {str(e)}")
            return False