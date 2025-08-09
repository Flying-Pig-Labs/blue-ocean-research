# Multi-Step LLM Pipeline - Troubleshooting Guide

## Quick Diagnosis

### Pipeline Status Check

```bash
# Get job status
JOB_ID="your-job-id"
API_ENDPOINT="your-api-endpoint"

curl "${API_ENDPOINT}/pipeline/status/${JOB_ID}"
```

### Common Error Patterns

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| `502 Bad Gateway` | Lambda function error | Check CloudWatch logs |
| `Task timed out` | Long-running operation | Increase Lambda timeout |
| `AccessDenied` | Missing IAM permissions | Check IAM roles |
| `SecretNotFound` | Missing API keys | Update Secrets Manager |
| `ThrottlingException` | Rate limits exceeded | Wait and retry |

## Deployment Issues

### SAM Build Failures

**Error**: `Build Failed`
```bash
Error: PythonPipBuilder:ResolveDependencies - Python executable not found
```

**Solution**:
```bash
# Use Docker for consistent builds
sam build --use-container

# Or specify Python path
export PATH="/usr/bin/python3:$PATH"
sam build
```

**Error**: `Template validation error`
```bash
Error: Template format error: Unresolved resource dependencies
```

**Solution**:
```bash
# Validate template syntax
sam validate --template infrastructure/template.yaml

# Check for circular dependencies
grep -n "Ref\|GetAtt" infrastructure/template.yaml
```

### Permission Errors

**Error**: `User is not authorized to perform: cloudformation:CreateStack`

**Solution**:
```bash
# Verify AWS credentials
aws sts get-caller-identity --profile mvp

# Required IAM permissions (attach to your user/role):
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "lambda:*",
        "apigateway:*",
        "dynamodb:*",
        "s3:*",
        "iam:*",
        "secretsmanager:*",
        "states:*",
        "logs:*",
        "events:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### Stack Deployment Failures

**Error**: `Stack rollback in progress`

**Solution**:
```bash
# Check stack events for root cause
aws cloudformation describe-stack-events \
  --stack-name multi-step-llm-pipeline-dev \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]' \
  --profile mvp

# Common fixes:
# 1. Delete failed stack and retry
aws cloudformation delete-stack --stack-name multi-step-llm-pipeline-dev --profile mvp

# 2. Update IAM permissions
# 3. Fix template syntax errors
```

## Runtime Issues

### Pipeline Execution Failures

#### Stage 1: Research Analysis Failures

**Symptoms**:
- Status stuck at "Research Analysis" 
- Error: "Module not found"

**Diagnosis**:
```bash
# Check Lambda logs
aws logs tail /aws/lambda/multi-step-llm-pipeline-research-analysis-production \
  --start-time 2024-08-07T00:00:00 \
  --profile mvp
```

**Common Issues**:
1. **Missing Dependencies**
   ```bash
   # Error in logs: ModuleNotFoundError: No module named 'anthropic'
   
   # Fix: Rebuild with dependencies
   cd infrastructure
   rm -rf layers/dependencies/python/*
   pip install -r ../requirements.txt -t layers/dependencies/python/
   sam build && sam deploy
   ```

2. **API Key Issues**
   ```bash
   # Error: AuthenticationError: Invalid API key
   
   # Fix: Update secrets
   aws secretsmanager put-secret-value \
     --secret-id multi-step-llm-pipeline-dev-secrets \
     --secret-string '{"ANTHROPIC_API_KEY":"sk-ant-api03-..."}' \
     --profile mvp
   ```

#### Stage 2: JTBD Research Failures

**Error**: `EXA API rate limit exceeded`

**Solution**:
```bash
# Implement exponential backoff (already in code)
# Check EXA API usage in their dashboard
# Consider upgrading EXA plan
```

**Error**: `Search results empty`

**Solution**:
```python
# Modify search queries to be more specific
# Check if EXA API is working:
import os
from exa_py import Exa

exa = Exa(api_key=os.getenv('EXA_API_KEY'))
results = exa.search("test query")
print(results)
```

#### Stage 3: Clustering Failures

**Error**: `HDBSCAN clustering failed`

**Diagnosis**:
```bash
# Check if Cohere embeddings are working
curl -X POST "https://api.cohere.ai/v1/embed" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"texts": ["test"], "model": "embed-english-v3.0"}'
```

**Solutions**:
1. **Not enough data points**
   ```python
   # Reduce min_cluster_size in cluster_jtbd.py
   clusterer = hdbscan.HDBSCAN(min_cluster_size=2)  # Was 3
   ```

2. **Memory issues**
   ```yaml
   # Increase Lambda memory in template.yaml
   ClusteringFunction:
     Properties:
       MemorySize: 3008  # Was 2048
   ```

#### Stage 4: Value Curve Mapping Failures

**Error**: `Timeout after 900 seconds`

**Solutions**:
1. **Reduce search scope**
   ```python
   # In value_curve_mapper.py
   search_results = exa.search(query, num_results=3)  # Was 5
   ```

2. **Parallel processing**
   ```python
   # Already implemented - check if working
   with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
       futures = [executor.submit(process_zone, zone) for zone in zones]
   ```

#### Stage 5: Product Idea Generation Failures

**Error**: `OpenAI o1 model timeout`

**Solutions**:
1. **Switch to faster model temporarily**
   ```yaml
   # In llm_config.yaml
   product_ideas:
     generation:
       model: gpt-4o  # Instead of o1-preview-2024-09-12
   ```

2. **Reduce token count**
   ```yaml
   max_completion_tokens: 15000  # Was 30000
   ```

#### Stage 6: Idea Consolidation Failures

**Error**: `Claude API 529 rate limit`

**Solution**:
```python
# Fallback to OpenAI (already implemented)
# Check rate limits on Anthropic console
# Consider upgrading plan
```

#### Stage 7: GitHub Integration Failures

**Error**: `GitHub API rate limit exceeded`

**Solutions**:
1. **Check rate limit status**
   ```bash
   curl -H "Authorization: token YOUR_GITHUB_TOKEN" \
     https://api.github.com/rate_limit
   ```

2. **Implement delays**
   ```python
   # Already in code - verify working
   time.sleep(0.5)  # Between issue creations
   ```

**Error**: `Repository already exists`

**Solution**:
```python
# Handle gracefully (already implemented)
# Check if repo exists before creating
```

### Performance Issues

#### Slow Pipeline Execution

**Diagnosis**:
```bash
# Check Step Functions execution timeline
aws stepfunctions describe-execution \
  --execution-arn "arn:aws:states:us-east-1:123456789012:execution:pipeline:job-123" \
  --profile mvp
```

**Optimizations**:
1. **Increase Lambda memory** (more memory = faster execution)
2. **Optimize API calls** (reduce unnecessary requests)
3. **Implement caching** for repeated operations
4. **Parallel processing** where possible

#### High Costs

**Cost Analysis**:
```bash
# Check AWS Cost Explorer
# Look for highest cost services

# Common cost drivers:
# 1. Lambda execution time
# 2. API calls to LLM providers
# 3. DynamoDB read/write operations
# 4. S3 storage and requests
```

**Cost Optimizations**:
1. **Reduce Lambda memory** if not CPU-bound
2. **Use cheaper LLM models** for non-critical tasks
3. **Implement result caching**
4. **Clean up old data** automatically

### API Gateway Issues

#### 502 Bad Gateway

**Causes**:
1. Lambda function error
2. Lambda timeout
3. Memory limit exceeded

**Diagnosis**:
```bash
# Check API Gateway logs
aws logs tail /aws/apigateway/multi-step-llm-pipeline-api --follow --profile mvp

# Check Lambda logs
aws logs tail /aws/lambda/multi-step-llm-pipeline-starter-production --follow --profile mvp
```

#### CORS Issues

**Error**: `Access to fetch blocked by CORS policy`

**Solution**: Already configured in template.yaml, but verify:
```yaml
Cors:
  AllowMethods: "'GET,POST,PUT,DELETE,OPTIONS'"
  AllowHeaders: "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
  AllowOrigin: "'*'"
```

### DynamoDB Issues

#### Throttling

**Error**: `ProvisionedThroughputExceededException`

**Solution**:
```bash
# Check if using on-demand billing (should auto-scale)
aws dynamodb describe-table --table-name PipelineJobs-production --profile mvp

# If provisioned, increase capacity or switch to on-demand
aws dynamodb modify-table \
  --table-name PipelineJobs-production \
  --billing-mode PAY_PER_REQUEST \
  --profile mvp
```

### S3 Issues

#### Access Denied

**Error**: `S3 access denied for pipeline artifacts`

**Solution**:
```bash
# Check bucket policy and IAM roles
aws s3api get-bucket-policy --bucket your-pipeline-bucket --profile mvp

# Verify Lambda function has S3 permissions in template.yaml
```

## Monitoring and Debugging

### CloudWatch Insights Queries

**Pipeline Execution Errors**:
```sql
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
```

**Slow Operations**:
```sql
fields @timestamp, @duration
| filter @duration > 10000
| sort @duration desc
| limit 50
```

**API Key Issues**:
```sql
fields @timestamp, @message
| filter @message like /API key/ or @message like /Authentication/
| sort @timestamp desc
```

### X-Ray Traces

**View Trace Map**:
1. Go to AWS X-Ray Console
2. Select Service Map
3. Click on services to see trace details
4. Look for high latency or error rates

**Common Patterns**:
- **Cold Starts**: First invocation takes longer
- **API Call Latency**: External API delays
- **Memory Issues**: Garbage collection spikes

### Custom Metrics

**Create Custom Metrics**:
```python
import boto3

cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_data(
    Namespace='Pipeline/Execution',
    MetricData=[
        {
            'MetricName': 'StageExecutionTime',
            'Dimensions': [
                {'Name': 'Stage', 'Value': 'ResearchAnalysis'},
                {'Name': 'Environment', 'Value': 'production'}
            ],
            'Value': execution_time_seconds,
            'Unit': 'Seconds'
        }
    ]
)
```

## Recovery Procedures

### Pipeline Recovery

**Stuck Executions**:
```bash
# Stop stuck execution
aws stepfunctions stop-execution \
  --execution-arn "arn:aws:states:us-east-1:123456789012:execution:pipeline:job-123" \
  --profile mvp

# Restart from specific stage (requires manual intervention)
# Update job status in DynamoDB and restart
```

**Data Corruption**:
```bash
# Restore from DynamoDB point-in-time recovery
aws dynamodb restore-table-to-point-in-time \
  --source-table-name PipelineJobs-production \
  --target-table-name PipelineJobs-production-restored \
  --restore-date-time 2024-08-07T12:00:00.000Z \
  --profile mvp
```

### Infrastructure Recovery

**Complete Stack Failure**:
```bash
# 1. Backup current state (if possible)
aws cloudformation describe-stacks --stack-name multi-step-llm-pipeline-prod > backup.json

# 2. Delete and recreate
aws cloudformation delete-stack --stack-name multi-step-llm-pipeline-prod --profile mvp

# 3. Wait for deletion
aws cloudformation wait stack-delete-complete --stack-name multi-step-llm-pipeline-prod --profile mvp

# 4. Redeploy
sam deploy --config-env production
```

## Prevention Strategies

### Health Checks

**Synthetic Monitoring**:
```python
# Create Lambda function for health checks
import requests
import boto3

def health_check():
    api_endpoint = os.environ['API_ENDPOINT']
    
    # Test basic API health
    response = requests.get(f"{api_endpoint}/health")
    if response.status_code != 200:
        send_alert("API health check failed")
    
    # Test pipeline creation
    test_job = requests.post(
        f"{api_endpoint}/pipeline/start",
        json={"researchDocId": "health-check", "username": "monitor"}
    )
    
    if test_job.status_code not in [200, 202]:
        send_alert("Pipeline creation health check failed")
```

### Automated Recovery

**Auto-restart Failed Jobs**:
```python
# EventBridge rule for failed executions
{
    "Rules": [{
        "EventPattern": {
            "source": ["aws.states"],
            "detail-type": ["Step Functions Execution Status Change"],
            "detail": {
                "status": ["FAILED", "TIMED_OUT", "ABORTED"]
            }
        },
        "Targets": [{
            "Arn": "arn:aws:lambda:us-east-1:123456789012:function:auto-recovery",
            "Id": "AutoRecoveryTarget"
        }]
    }]
}
```

### Capacity Planning

**Monitor Resource Usage**:
1. **Lambda Concurrency**: Set reserved concurrency
2. **DynamoDB Capacity**: Monitor consumed vs provisioned
3. **S3 Storage**: Set up lifecycle policies
4. **API Rate Limits**: Track usage across all providers

## Emergency Contacts

### Escalation Procedures

1. **Level 1**: Check this troubleshooting guide
2. **Level 2**: Review CloudWatch logs and metrics
3. **Level 3**: Contact on-call engineer
4. **Level 4**: Engage vendor support (AWS, Anthropic, OpenAI)

### Vendor Support

**AWS Support**:
- Business hours: AWS Support Console
- After hours: Phone support (if plan includes)

**Anthropic Support**:
- Email: support@anthropic.com
- Status page: https://status.anthropic.com

**OpenAI Support**:
- Help center: https://help.openai.com
- Status page: https://status.openai.com

**Cohere Support**:
- Email: support@cohere.ai
- Status page: https://status.cohere.ai

**EXA Support**:
- Email: support@exa.ai

## Tools and Scripts

### Diagnostic Scripts

**pipeline-doctor.py**:
```python
#!/usr/bin/env python3
"""
Pipeline health diagnostic tool
Usage: python pipeline-doctor.py --environment production
"""

import boto3
import requests
import sys
import argparse

def check_api_health(api_endpoint):
    try:
        response = requests.get(f"{api_endpoint}/health", timeout=10)
        return response.status_code == 200
    except:
        return False

def check_lambda_health(function_name):
    lambda_client = boto3.client('lambda')
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        return response['Configuration']['State'] == 'Active'
    except:
        return False

def check_secrets(secret_name):
    secrets_client = boto3.client('secretsmanager')
    try:
        secrets_client.get_secret_value(SecretId=secret_name)
        return True
    except:
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--environment', required=True)
    args = parser.parse_args()
    
    stack_name = f"multi-step-llm-pipeline-{args.environment}"
    
    # Get stack outputs
    cf = boto3.client('cloudformation')
    stack = cf.describe_stacks(StackName=stack_name)
    outputs = {o['OutputKey']: o['OutputValue'] for o in stack['Stacks'][0]['Outputs']}
    
    # Run checks
    print(f"🏥 Pipeline Health Check - {args.environment}")
    print("=" * 50)
    
    # API Health
    api_healthy = check_api_health(outputs['ApiEndpoint'])
    print(f"API Gateway: {'✅' if api_healthy else '❌'}")
    
    # Lambda Functions
    functions = [
        f"{stack_name}-starter",
        f"{stack_name}-research-analysis",
        # ... add all functions
    ]
    
    for func in functions:
        healthy = check_lambda_health(func)
        print(f"Lambda {func}: {'✅' if healthy else '❌'}")
    
    # Secrets
    secrets_healthy = check_secrets(f"{stack_name}-secrets")
    print(f"Secrets Manager: {'✅' if secrets_healthy else '❌'}")
    
    print("\n" + "=" * 50)
    if all([api_healthy, secrets_healthy]):  # Add all checks
        print("🎉 All systems healthy!")
        sys.exit(0)
    else:
        print("⚠️  Issues detected - check logs for details")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

Make it executable:
```bash
chmod +x pipeline-doctor.py
python pipeline-doctor.py --environment production
```

**log-analyzer.py**:
```python
#!/usr/bin/env python3
"""
Log analysis tool for pipeline debugging
Usage: python log-analyzer.py --job-id job-123 --last-hours 2
"""

import boto3
import json
import argparse
from datetime import datetime, timedelta

def analyze_logs(job_id, hours_back):
    logs_client = boto3.client('logs')
    
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours_back)
    
    # Convert to milliseconds
    start_ms = int(start_time.timestamp() * 1000)
    end_ms = int(end_time.timestamp() * 1000)
    
    query = f"""
    fields @timestamp, @message, @requestId
    | filter @message like /{job_id}/
    | sort @timestamp asc
    """
    
    # Query all Lambda function log groups
    log_groups = [
        '/aws/lambda/multi-step-llm-pipeline-starter-production',
        '/aws/lambda/multi-step-llm-pipeline-research-analysis-production',
        # ... add all log groups
    ]
    
    for log_group in log_groups:
        print(f"\n📋 Analyzing {log_group}")
        print("-" * 60)
        
        try:
            response = logs_client.start_query(
                logGroupName=log_group,
                startTime=start_ms,
                endTime=end_ms,
                queryString=query
            )
            
            query_id = response['queryId']
            
            # Wait for query to complete
            import time
            while True:
                result = logs_client.get_query_results(queryId=query_id)
                if result['status'] == 'Complete':
                    break
                time.sleep(1)
            
            # Print results
            for row in result['results']:
                timestamp = row[0]['value']
                message = row[1]['value']
                print(f"{timestamp}: {message}")
                
        except Exception as e:
            print(f"Error querying {log_group}: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--job-id', required=True)
    parser.add_argument('--last-hours', type=int, default=2)
    args = parser.parse_args()
    
    print(f"🔍 Analyzing logs for job {args.job_id}")
    print(f"📅 Looking back {args.last_hours} hours")
    
    analyze_logs(args.job_id, args.last_hours)

if __name__ == '__main__':
    main()
```

## FAQ

**Q: Why is my pipeline taking longer than 20 minutes?**
A: Check for API rate limits, increase Lambda memory, or reduce scope of operations.

**Q: Can I run multiple pipelines simultaneously?**
A: Yes, but be aware of API rate limits and Lambda concurrency limits.

**Q: How do I update API keys?**
A: Use AWS Secrets Manager - never hardcode keys in your code.

**Q: What's the maximum research document size?**
A: 10MB for S3 uploads, but larger documents may cause timeouts.

**Q: Can I customize the pipeline stages?**
A: Yes, modify the Step Functions definition and corresponding Lambda functions.

**Q: How do I backup my data?**
A: DynamoDB has point-in-time recovery, S3 has versioning, code is in Git.

---

## Getting Help

If this guide doesn't solve your issue:

1. **Search CloudWatch logs** for error details
2. **Check AWS Service Health Dashboard** for service outages
3. **Review recent code changes** that might have introduced issues
4. **Contact the team** with specific error messages and context
5. **Create a GitHub issue** with reproduction steps

Remember: Always include the **job ID**, **environment**, **timestamp**, and **error messages** when asking for help!