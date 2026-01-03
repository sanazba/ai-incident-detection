# AI-Powered Kubernetes Incident Detection System

<div align="center">

![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=for-the-badge&logo=kubernetes&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white)
![Terraform](https://img.shields.io/badge/terraform-%235835CC.svg?style=for-the-badge&logo=terraform&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Anthropic](https://img.shields.io/badge/Claude%20AI-191919?style=for-the-badge&logo=anthropic&logoColor=white)
![Slack](https://img.shields.io/badge/Slack-4A154B?style=for-the-badge&logo=slack&logoColor=white)

**Intelligent Kubernetes monitoring with AI-powered incident analysis and automated remediation recommendations**

[Features](#features) • [Architecture](#architecture) • [Quick Start](#quick-start) • [Screenshots](#slack-alerts) • [Documentation](#documentation)

</div>

---

## 🌟 Overview

An intelligent incident detection and response system that monitors Kubernetes clusters 24/7, automatically analyzes failures using Claude AI (via AWS Bedrock), and sends actionable remediation recommendations to Slack within seconds.

### Why This Exists

Traditional monitoring tells you *what* broke. This system tells you *why* it broke and *how* to fix it—powered by AI.

## ✨ Features

- 🤖 **AI-Powered Analysis** - Claude 3 Sonnet analyzes incidents and provides intelligent remediation steps
- ⚡ **Real-Time Detection** - Watches all Kubernetes pods across namespaces with <6 second response time
- 🎯 **Smart Severity Classification** - Automatically categorizes incidents as LOW, MEDIUM, HIGH, or CRITICAL
- 📊 **Beautiful Slack Alerts** - Rich, formatted notifications with pod details and AI recommendations
- 🔄 **Auto-Deduplication** - Prevents alert fatigue with intelligent duplicate detection
- 🏗️ **Infrastructure as Code** - Complete Terraform deployment with best practices
- 🔒 **Secure** - Least-privilege IAM roles, encrypted credentials, VPC support

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  K8s Incident Watcher Pod (Python)                       │   │
│  │  • Monitors all namespaces                               │   │
│  │  • Detects pod failures, crashes, OOM kills              │   │
│  │  • Deduplicates alerts                                   │   │
│  └────────────────────┬─────────────────────────────────────┘   │
└─────────────────────┬─┴─────────────────────────────────────────┘
                      │
                      │ EventBridge PutEvents
                      ▼
          ┌───────────────────────────┐
          │   AWS EventBridge         │
          │   (Event Router)          │
          └───────────┬───────────────┘
                      │
                      │ Triggers Lambda
                      ▼
          ┌───────────────────────────┐
          │   AWS Lambda              │
          │   • Python 3.11           │
          │   • 512MB Memory          │
          │   • 60s Timeout           │
          └───────────┬───────────────┘
                      │
                      │ InvokeModel
                      ▼
          ┌───────────────────────────┐
          │   AWS Bedrock             │
          │   Claude 3 Sonnet         │
          │   • Analyzes incident     │
          │   • Generates remediation │
          └───────────┬───────────────┘
                      │
                      │ Webhook POST
                      ▼
          ┌───────────────────────────┐
          │   Slack Channel           │
          │   • Formatted alerts      │
          │   • AI recommendations    │
          │   • Incident tracking     │
          └───────────────────────────┘
```

## 📸 Slack Alerts

### High Severity Alert - CrashLoopBackOff
```
🔴 Incident Alert - HIGH

Incident ID: INC-69BA7B7BB4E2
Source: kubernetes
Pod Name: crash-loop-test
Namespace: default
Reason: CrashLoopBackOff
Severity: HIGH
Time: 2025-12-31 19:30:02 UTC

Summary:
Kubernetes pod crashing in a loop

AI Recommendations:
• Check application logs for errors that may indicate the root cause
• Temporarily scale down or remove the affected pod to stop the crashing loop

Incident INC-69BA7B7BB4E2 detected and analyzed by AI
AI Incident Detection System | Today at 8:30 PM
```

### Medium Severity Alert - Pod Failure
```
🟡 Incident Alert - MEDIUM

Incident ID: INC-C27C6B875A29
Source: kubernetes
Pod Name: show-details-1767209132
Namespace: default
Reason: Error
Severity: MEDIUM
Time: 2025-12-31 19:30:02 UTC

Summary:
Kubernetes pod failure in default namespace

AI Recommendations:
• Check recent logs from the failed pod for error messages that could indicate the root cause
• Check node ip-10-59-21-12.eu-west-1.compute.internal for resource constraints or other issues
• Verify pod's resource requests/limits are properly configured

Incident INC-C27C6B875A29 detected and analyzed by AI
AI Incident Detection System | Today at 8:30 PM
```

### Medium Severity Alert - Monitoring Pod Issues
```
🟡 Incident Alert - MEDIUM

Incident ID: INC-A69C7C15928D
Source: kubernetes
Pod Name: grafana-k8s-monitoring-alloy-logs-87bng
Namespace: monitoring
Reason: Unknown
Severity: MEDIUM
Time: 2025-12-31 19:30:03 UTC

Summary:
Kubernetes Pod Failure - Grafana Monitoring Pod Restarting

AI Recommendations:
• Check the pod logs for errors or failures
• Ensure the pod has sufficient resources (CPU/memory) allocated
• Verify all required ConfigMaps and Secrets are present

Incident INC-A69C7C15928D detected and analyzed by AI
AI Incident Detection System | Today at 8:30 PM
```

## 🚀 Quick Start

### Prerequisites

- AWS Account with admin access
- Kubernetes cluster (EKS, self-hosted, etc.)
- Terraform >= 1.0
- kubectl configured
- Slack workspace with admin permissions

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/k8s-ai-incident-detection.git
cd k8s-ai-incident-detection
```

### 2. Create Slack Webhook

1. Go to https://api.slack.com/apps
2. Create new app → From scratch
3. Enable "Incoming Webhooks"
4. Add webhook to workspace
5. Copy webhook URL (looks like `https://hooks.slack.com/services/...`)

### 3. Enable AWS Bedrock Model

**Important:** You must enable the Claude 3 Sonnet model in AWS Bedrock before deployment.

#### Why is this needed?

AWS Bedrock models are now auto-enabled on first invocation. However, the first invocation requires AWS Marketplace permissions (`aws-marketplace:Subscribe` and `aws-marketplace:ViewSubscriptions`). 

By manually invoking the model once as an admin user, you **activate it for the entire AWS account**, allowing the Lambda function to use it without needing marketplace permissions.

#### How to Enable:

```bash
# Create test request
cat > /tmp/bedrock-request.json <<EOF
{
  "anthropic_version": "bedrock-2023-05-31",
  "max_tokens": 100,
  "messages": [{"role": "user", "content": "test"}]
}
EOF

# Invoke model to activate it (run this with admin credentials)
aws bedrock-runtime invoke-model \
  --region eu-west-1 \
  --model-id anthropic.claude-3-sonnet-20240229-v1:0 \
  --body fileb:///tmp/bedrock-request.json \
  /tmp/response.json

# Verify activation
cat /tmp/response.json
```

**Success looks like:**
```json
{
  "id": "msg_...",
  "type": "message",
  "role": "assistant",
  "content": [{"type": "text", "text": "..."}]
}
```

The model is now activated! Your Lambda function can use it without marketplace permissions.

### 4. Configure Terraform

```bash
cd terraform

# Create configuration file
cat > dev.tfvars <<EOF
aws_region                = "eu-west-1"
environment               = "dev"
use_bedrock               = true
claude_api_key            = "not-needed-for-bedrock"
slack_webhook_url         = "YOUR_SLACK_WEBHOOK_URL_HERE"
pagerduty_integration_key = ""
k8s_cluster_name          = "your-cluster-name"
rds_instance_ids          = []
lambda_timeout            = 60
lambda_memory             = 512
log_retention_days        = 7
EOF
```

### 5. Build Lambda Layer

```bash
cd ../lambda
mkdir -p layer/python
pip install -r requirements.txt -t layer/python/ --index-url https://pypi.org/simple
cd layer
zip -r ../lambda_layer.zip python/
cd ..
mv lambda_layer.zip ../terraform/
```

### 6. Deploy Infrastructure

```bash
cd ../terraform
terraform init
terraform plan -var-file=dev.tfvars
terraform apply -var-file=dev.tfvars
```

### 7. Deploy Kubernetes Watcher

```bash
cd ../k8s
kubectl apply -f watcher-deployment.yaml

# Verify deployment
kubectl get pods -n incident-detection
kubectl logs -n incident-detection -l app=k8s-incident-watcher -f
```

### 8. Test the System

```bash
# Create a crashing pod
kubectl run test-crash --image=busybox --restart=Never -- /bin/sh -c "exit 1"

# Watch Lambda logs
aws logs tail /aws/lambda/dev-ai-incident-detector --follow

# Check Slack for alert!
```

## 📊 System Components

### AWS Lambda Function
- **Runtime:** Python 3.11
- **Memory:** 512 MB
- **Timeout:** 60 seconds
- **Trigger:** EventBridge
- **Dependencies:** boto3, anthropic SDK, slack-sdk

### Kubernetes Watcher
- **Image:** python:3.11-slim
- **Resources:** 128Mi memory, 100m CPU
- **Permissions:** Read-only cluster access
- **Detects:** Pod failures, crashes, OOM kills, ImagePullBackOff

### EventBridge Rules
- K8s pod failures
- CloudWatch alarms
- RDS events
- Custom sources

### IAM Roles
- Lambda execution role (Bedrock, CloudWatch, EventBridge)
- K8s watcher IAM user (EventBridge PutEvents - optional, uses node role)
- EKS node role (EventBridge PutEvents access)

## 🔧 Configuration

### Environment Variables

Lambda function environment variables (set in `dev.tfvars`):

```hcl
SLACK_WEBHOOK_URL         = "https://hooks.slack.com/services/..."
PAGERDUTY_INTEGRATION_KEY = "" # Optional
ENVIRONMENT               = "dev"
USE_BEDROCK               = "1"
K8S_CLUSTER_NAME          = "service-runner"
```

### Customization

**Adjust detection rules** (`k8s/watcher-deployment.yaml`):
```yaml
pod_failure_states:
  - "Failed"
  - "CrashLoopBackOff"
  - "Error"
  - "ImagePullBackOff"
  - "OOMKilled"
```

**Change check interval:**
```yaml
check_interval: 60  # seconds
```

**Modify deduplication window:**
```yaml
debounce_seconds: 300  # 5 minutes
```

**Adjust severity thresholds** (`lambda/claude_agent.py`):
```python
# Modify the AI prompt to change severity classification logic
```

## 📖 How It Works

### 1. Detection
The Kubernetes watcher monitors all pods across namespaces using the Kubernetes watch API. When a pod enters a failure state (Error, CrashLoopBackOff, OOMKilled, etc.), it immediately captures:
- Pod name and namespace
- Failure reason and message
- Container status
- Restart count
- Node information

### 2. Routing
The watcher sends structured event data to AWS EventBridge via the PutEvents API. EventBridge routes events to the Lambda function based on configurable rules (source: `k8s.cluster`).

### 3. AI Analysis
Lambda invokes Claude 3 Sonnet via AWS Bedrock with a specialized prompt containing:
- Incident context (pod, namespace, cluster)
- Current status and error messages
- Historical context (restart count, node info)

Claude analyzes the incident and returns:
- Severity classification (LOW/MEDIUM/HIGH/CRITICAL)
- Root cause analysis summary
- Step-by-step remediation recommendations
- Prevention strategies

### 4. Notification
The system formats the AI analysis into a rich Slack message with:
- Color-coded severity indicators (🟢🟡🔴🚨)
- Structured incident details
- Pod name, namespace, reason
- Actionable AI recommendations
- Unique incident ID for tracking

### 5. Deduplication
To prevent alert fatigue, the system maintains a 5-minute cache of recent alerts using a combination of pod name and failure reason as the key. This prevents duplicate alerts when pods transition through multiple failure states.

## 🛠️ Troubleshooting

### Lambda can't access Bedrock model

**Error:** `Model access is denied due to IAM user or service role is not authorized`

**Solution:** Manually activate the Bedrock model (see [step 3](#3-enable-aws-bedrock-model) in Quick Start)

### No Slack notifications

**Check webhook configuration:**
```bash
aws lambda get-function-configuration \
  --function-name dev-ai-incident-detector \
  --query 'Environment.Variables.SLACK_WEBHOOK_URL'
```

**Check Lambda logs:**
```bash
aws logs tail /aws/lambda/dev-ai-incident-detector --follow
```

### Watcher not detecting pods

**View watcher logs:**
```bash
kubectl logs -n incident-detection -l app=k8s-incident-watcher -f
```

**Verify RBAC permissions:**
```bash
kubectl auth can-i list pods \
  --as=system:serviceaccount:incident-detection:k8s-incident-watcher
```

**Check if watcher is running:**
```bash
kubectl get pods -n incident-detection
```

### EventBridge permissions error

**Error:** `User is not authorized to perform: events:PutEvents`

**Solution:** The EKS node role needs EventBridge permissions (already included in Terraform):
```bash
# Verify policy is attached
aws iam list-attached-role-policies \
  --role-name YOUR-NODE-ROLE-NAME
```

## 📚 Documentation

### File Structure

```
.
├── lambda/
│   ├── handler.py              # Main Lambda handler
│   ├── claude_agent.py         # AI analysis logic
│   ├── slack_notifier.py       # Slack integration
│   ├── pagerduty_notifier.py   # PagerDuty integration (optional)
│   └── requirements.txt        # Python dependencies
├── terraform/
│   ├── main.tf                 # Provider configuration
│   ├── lambda.tf               # Lambda function resources
│   ├── eventbridge.tf          # EventBridge rules
│   ├── iam.tf                  # IAM roles and policies
│   ├── kubernetes.tf           # K8s namespace and secrets (managed by Terraform)
│   ├── cloudwatch.tf           # Monitoring and alarms
│   ├── outputs.tf              # Terraform outputs
│   └── variables.tf            # Input variables
├── k8s/
│   └── watcher-deployment.yaml # Kubernetes watcher deployment
├── test_events/
│   ├── test-pod-failure.json   # Sample test events
│   └── test-oom-kill.json
└── README.md
```

### EventBridge Event Schema

```json
{
  "Source": "k8s.cluster",
  "DetailType": "K8s Pod Failure",
  "Detail": {
    "source": "kubernetes",
    "type": "pod_failure",
    "timestamp": "2025-12-31T19:30:02.123456",
    "cluster_name": "service-runner",
    "pod_name": "crash-loop-test",
    "namespace": "default",
    "status": "Failed",
    "reason": "CrashLoopBackOff",
    "message": "Back-off restarting failed container",
    "status_type": "Waiting",
    "restart_count": 8,
    "node_name": "ip-10-59-21-12.eu-west-1.compute.internal",
    "labels": {"app": "web", "env": "production"}
  }
}
```

## 🔐 Security Best Practices

- ✅ Least-privilege IAM roles (Lambda can only invoke Bedrock and write logs)
- ✅ Secrets managed by Terraform (AWS credentials in K8s secret)
- ✅ Read-only Kubernetes RBAC for watcher
- ✅ Encrypted CloudWatch logs (optional)
- ✅ VPC endpoint support for private EKS clusters
- ✅ No hardcoded credentials in code
- ✅ Slack webhook URL in environment variable (not committed)

## 🚦 Monitoring

### CloudWatch Alarms (Included)

- Lambda error rate > 5%
- Lambda duration > 30 seconds
- Lambda concurrent executions > 80% of limit

### Metrics to Watch

```bash
# Lambda invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=dev-ai-incident-detector \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Bedrock invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock \
  --metric-name Invocations \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Anthropic](https://www.anthropic.com/) for Claude AI
- [AWS Bedrock](https://aws.amazon.com/bedrock/) for managed AI infrastructure  
- [Kubernetes](https://kubernetes.io/) for container orchestration
- [Terraform](https://www.terraform.io/) for infrastructure as code

## 📧 Support

For issues and questions:
- 🐛 Open an issue on GitHub
- 📖 Check the [documentation](#documentation)
- 🔍 Review CloudWatch logs for debugging
- 💬 Discussion forum (coming soon)

## 🗺️ Roadmap

- [ ] Support for multiple Slack channels
- [ ] PagerDuty integration improvements
- [ ] Historical incident analytics dashboard
- [ ] Auto-remediation for common issues
- [ ] Support for more Claude models (Opus, Haiku)
- [ ] Prometheus metrics export
- [ ] Multi-cluster support

---

<div align="center">

**Built with ❤️ using Terraform, AWS, and Claude AI**

⭐ Star this repo if you find it useful!

[![GitHub stars](https://img.shields.io/github/stars/yourusername/k8s-ai-incident-detection?style=social)](https://github.com/yourusername/k8s-ai-incident-detection)
[![GitHub forks](https://img.shields.io/github/forks/yourusername/k8s-ai-incident-detection?style=social)](https://github.com/yourusername/k8s-ai-incident-detection/fork)

</div>
