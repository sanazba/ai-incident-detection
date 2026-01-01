"""
Claude AI Agent for Incident Analysis
Uses AWS Bedrock to access Claude for analyzing and diagnosing incidents
"""
import json
import boto3
import os
from datetime import datetime
import hashlib


class ClaudeIncidentAgent:
    """AI agent powered by Claude via AWS Bedrock for intelligent incident analysis"""
    
    def __init__(self, api_key=None, use_bedrock=True, region=None):
        """
        Initialize the Claude agent
        
        Args:
            api_key: Anthropic API key (not used if use_bedrock=True)
            use_bedrock: Whether to use AWS Bedrock (default: True)
            region: AWS region for Bedrock (default: from environment or eu-west-1)
        """
        self.use_bedrock = use_bedrock
        
        # Get region from environment or use default
        if region is None:
            region = os.environ.get('AWS_REGION', 'eu-west-1')
        
        if self.use_bedrock:
            # Use AWS Bedrock
            self.bedrock_runtime = boto3.client(
                service_name='bedrock-runtime',
                region_name=region
            )
            
            # Use Claude 3.5 Sonnet (more stable, doesn't require inference profile)
            self.model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
            
            print(f"Initialized Claude agent with Bedrock in region {region}")
            print(f"Using model: {self.model_id}")
        else:
            # Use Anthropic API directly
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=api_key)
                self.model = "claude-3-5-sonnet-20241022"
                print("Initialized Claude agent with Anthropic API")
            except ImportError:
                print("Warning: anthropic package not installed, falling back to Bedrock")
                self.use_bedrock = True
                self.bedrock_runtime = boto3.client(
                    service_name='bedrock-runtime',
                    region_name=region
                )
                self.model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    def analyze_incident(self, incident_data):
        """
        Analyze an incident using Claude AI
        Returns structured analysis with severity, root cause, and recommendations
        """
        print(f"Analyzing incident from source: {incident_data.get('source', 'unknown')}")
        
        context = self._build_context(incident_data)
        prompt = self._build_analysis_prompt(incident_data, context)
        
        if self.use_bedrock:
            analysis_text = self._call_bedrock(prompt)
        else:
            analysis_text = self._call_anthropic(prompt)
        
        structured_analysis = self._parse_analysis(analysis_text, incident_data)
        
        print(f"Analysis complete: Severity={structured_analysis.get('severity', 'unknown')}, ID={structured_analysis.get('incident_id', 'unknown')}")
        
        return structured_analysis
    
    def _call_bedrock(self, prompt):
        """Call Claude via AWS Bedrock"""
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "temperature": 0.3,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            print(f"Calling Bedrock model: {self.model_id}")
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            
            if 'content' in response_body and len(response_body['content']) > 0:
                print("Bedrock response received successfully")
                return response_body['content'][0]['text']
            else:
                print("Error: No content in Bedrock response")
                return "Error: No content in Bedrock response"
                
        except Exception as e:
            print(f"Bedrock API error: {str(e)}")
            return f"Error calling Bedrock: {str(e)}"
    
    def _call_anthropic(self, prompt):
        """Call Claude via Anthropic API directly"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"Anthropic API error: {str(e)}")
            return f"Error calling Anthropic: {str(e)}"
    
    def _build_context(self, incident_data):
        """Build context about the incident"""
        context = {
            'source': incident_data.get('source', 'unknown'),
            'type': incident_data.get('type', 'unknown'),
            'timestamp': incident_data.get('timestamp', datetime.utcnow().isoformat())
        }
        
        if incident_data.get('source') == 'kubernetes':
            context['pod'] = incident_data.get('pod_name', 'unknown')
            context['namespace'] = incident_data.get('namespace', 'default')
            context['status'] = incident_data.get('status', 'unknown')
        elif incident_data.get('source') == 'rds':
            context['database'] = incident_data.get('db_instance', 'unknown')
            context['category'] = incident_data.get('event_category', [])
        
        return context
    
    def _build_analysis_prompt(self, incident_data, context):
        """Build the analysis prompt for Claude"""
        prompt = f"""You are an expert DevOps and SRE incident response AI. Analyze this incident and provide a structured response.

**Incident Details:**
Source: {context['source']}
Type: {context['type']}
Timestamp: {context['timestamp']}

**Incident Data:**
{json.dumps(incident_data, indent=2)}

**Your Task:**
Analyze this incident and provide:
1. Severity Level (critical/high/medium/low)
2. Root Cause Analysis - What likely caused this issue?
3. Impact Assessment - What systems/users are affected?
4. Immediate Actions - What should be done RIGHT NOW?
5. Recommended Fix - Step-by-step resolution
6. Prevention - How to prevent this in the future?

**Response Format (JSON):**
```json
{{
  "severity": "critical|high|medium|low",
  "title": "Brief incident description",
  "root_cause": "Likely root cause",
  "impact": "Impact description",
  "immediate_actions": ["action 1", "action 2"],
  "resolution_steps": ["step 1", "step 2"],
  "prevention": ["prevention 1", "prevention 2"]
}}
```

Provide ONLY the JSON response."""
        return prompt
    
    def _parse_analysis(self, analysis_text, incident_data):
        """Parse Claude's analysis into structured format"""
        try:
            if "```json" in analysis_text:
                json_start = analysis_text.find("```json") + 7
                json_end = analysis_text.find("```", json_start)
                analysis_text = analysis_text[json_start:json_end].strip()
            elif "```" in analysis_text:
                json_start = analysis_text.find("```") + 3
                json_end = analysis_text.find("```", json_start)
                analysis_text = analysis_text[json_start:json_end].strip()
            
            analysis = json.loads(analysis_text)
            print("Successfully parsed Claude's JSON response")
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            analysis = {
                "severity": "medium",
                "title": "Incident requires investigation",
                "root_cause": "Analysis in progress",
                "impact": "Unknown",
                "immediate_actions": ["Investigate the incident"],
                "resolution_steps": ["Manual investigation required"],
                "prevention": ["Review after resolution"]
            }
        
        analysis['incident_id'] = self._generate_incident_id(incident_data)
        analysis['timestamp'] = incident_data.get('timestamp', datetime.utcnow().isoformat())
        analysis['source'] = incident_data.get('source', 'unknown')
        analysis['analyzed_by'] = 'claude-ai-bedrock' if self.use_bedrock else 'claude-ai'
        
        return analysis
    
    def _generate_incident_id(self, incident_data):
        """Generate unique incident ID"""
        data_str = json.dumps(incident_data, sort_keys=True)
        hash_obj = hashlib.md5(data_str.encode())
        return f"INC-{hash_obj.hexdigest()[:12].upper()}"