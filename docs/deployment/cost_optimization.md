# Multi-Step LLM Pipeline - Cost Optimization Guide

## Cost Overview

### Current Monthly Estimates

| Environment | Low Usage | Medium Usage | High Usage |
|-------------|-----------|--------------|------------|
| **Development** | $50 | $100 | $200 |
| **Staging** | $100 | $200 | $400 |
| **Production** | $200 | $500 | $1,000 |

**Usage Definitions**:
- **Low**: 10 pipelines/month, 50% success rate
- **Medium**: 100 pipelines/month, 80% success rate  
- **High**: 500 pipelines/month, 95% success rate

### Cost Breakdown by Service

#### Production Environment (Medium Usage)

| Service | Monthly Cost | Percentage | Key Factors |
|---------|-------------|------------|-------------|
| **Lambda Functions** | $150-200 | 35% | Execution time, memory allocation |
| **LLM API Calls** | $100-150 | 30% | Token usage, model selection |
| **Step Functions** | $50-75 | 15% | State transitions, execution time |
| **DynamoDB** | $30-50 | 10% | Read/write operations, storage |
| **S3 Storage** | $15-25 | 5% | Object storage, requests |
| **Other (API Gateway, CloudWatch)** | $10-20 | 5% | API calls, logs, monitoring |
| **Total** | $355-520 | 100% | |

## Cost Optimization Strategies

### 1. Lambda Optimization

#### Memory Allocation Tuning

**Current Configuration**:
```yaml
# template.yaml
ResearchAnalysisFunction:
  MemorySize: 1024  # May be over-allocated
```

**Optimization Process**:
```python
# Use CloudWatch to analyze actual memory usage
import boto3

logs_client = boto3.client('logs')

query = """
fields @timestamp, @type, @requestId, @memorySize, @maxMemoryUsed
| filter @type = "REPORT"
| stats max(@maxMemoryUsed) by bin(5m)
"""

# Run query and adjust MemorySize to actual usage + 20% buffer
```

**Recommended Settings**:
```yaml
# Optimized memory allocation
ResearchAnalysisFunction:
  MemorySize: 768  # Down from 1024 (saves ~25%)

JTBDResearchFunction:
  MemorySize: 512  # Down from 1024 (saves ~50%)

ClusteringFunction:
  MemorySize: 1536  # Down from 2048 (saves ~25%)

# Keep high for CPU-intensive tasks
ProductIdeaGenerationFunction:
  MemorySize: 3008  # Keep high - CPU intensive
```

**Potential Savings**: $30-50/month

#### Execution Time Optimization

**Code-Level Optimizations**:
```python
# 1. Connection pooling for HTTP requests
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry_strategy = Retry(total=3, backoff_factor=1)
adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
session.mount("https://", adapter)

# 2. Async operations where possible
import asyncio
import aiohttp

async def parallel_api_calls(requests):
    async with aiohttp.ClientSession() as session:
        tasks = [make_request(session, req) for req in requests]
        results = await asyncio.gather(*tasks)
    return results

# 3. Smart caching
import functools
import time

@functools.lru_cache(maxsize=128)
def cached_embedding(text_hash):
    # Cache embeddings for repeated text
    return generate_embedding(text)
```

**Potential Savings**: $40-60/month

### 2. LLM API Cost Optimization

#### Model Selection Strategy

**Current Usage**:
```yaml
# llm_config.yaml - Current expensive models
models:
  research_analysis:
    verticals:
      model: claude-3-5-sonnet-20241022  # $3/1M input tokens
    
  product_ideas:
    generation:
      model: o1-preview-2024-09-12  # $15/1M input tokens
```

**Optimized Configuration**:
```yaml
# Cost-optimized models
models:
  research_analysis:
    verticals:
      model: claude-3-5-haiku-20241022  # $0.25/1M input tokens (87% savings)
      # Use for simple extraction tasks
    
    personas:
      model: claude-3-5-sonnet-20241022  # Keep premium for complex analysis
      
  product_ideas:
    generation:
      model: gpt-4o  # $2.50/1M input tokens (83% savings from o1)
      # Fallback to o1 only for complex cases
```

**Environment-Specific Models**:
```yaml
environment:
  overrides:
    development:
      default_anthropic_model: "claude-3-5-haiku-20241022"
      default_openai_model: "gpt-4o-mini"
      max_tokens_multiplier: 0.5
    
    production:
      default_anthropic_model: "claude-3-5-sonnet-20241022"
      default_openai_model: "gpt-4o"
      max_tokens_multiplier: 1.0
```

**Token Usage Optimization**:
```python
# 1. Prompt compression
def compress_prompt(prompt, max_tokens=2000):
    """Compress prompts while maintaining quality"""
    if len(prompt.split()) > max_tokens:
        # Keep first and last parts, summarize middle
        words = prompt.split()
        first_part = " ".join(words[:max_tokens//2])
        last_part = " ".join(words[-max_tokens//2:])
        return f"{first_part}\n[... content summarized ...]\n{last_part}"
    return prompt

# 2. Smart truncation
def smart_truncate(text, max_length=4000):
    """Truncate while preserving important content"""
    if len(text) <= max_length:
        return text
    
    # Keep beginning and end, summarize middle
    keep_size = max_length // 3
    return f"{text[:keep_size]}\n\n[Content truncated for brevity]\n\n{text[-keep_size:]}"

# 3. Result caching
import hashlib
import json

def cache_llm_result(prompt, model):
    """Cache LLM results to avoid repeat calls"""
    cache_key = hashlib.sha256(f"{prompt}{model}".encode()).hexdigest()
    
    # Check cache first
    cached_result = get_from_cache(cache_key)
    if cached_result:
        return cached_result
    
    # Make API call and cache result
    result = call_llm(prompt, model)
    save_to_cache(cache_key, result)
    return result
```

**Potential Savings**: $50-100/month

### 3. Infrastructure Cost Optimization

#### DynamoDB Optimization

**Current Configuration**:
```yaml
# Pay-per-request (good for variable workloads)
PipelineJobsTable:
  BillingMode: PAY_PER_REQUEST
```

**Optimization for High Volume**:
```yaml
# Provisioned mode for predictable high volume
PipelineJobsTable:
  BillingMode: PROVISIONED
  ProvisionedThroughput:
    ReadCapacityUnits: 10   # Adjust based on usage
    WriteCapacityUnits: 10
  GlobalSecondaryIndexes:
    - IndexName: ResearchDocIndex
      ProvisionedThroughput:
        ReadCapacityUnits: 5
        WriteCapacityUnits: 5
```

**Auto-scaling Configuration**:
```yaml
# Add auto-scaling for provisioned mode
TableScalingRole:
  Type: AWS::IAM::Role
  Properties:
    AssumeRolePolicyDocument:
      Statement:
        - Effect: Allow
          Principal:
            Service: application-autoscaling.amazonaws.com
          Action: sts:AssumeRole

ReadCapacityScalableTarget:
  Type: AWS::ApplicationAutoScaling::ScalableTarget
  Properties:
    MaxCapacity: 100
    MinCapacity: 5
    ResourceId: !Sub "table/${PipelineJobsTable}"
    RoleARN: !GetAtt TableScalingRole.Arn
    ScalableDimension: dynamodb:table:ReadCapacityUnits
    ServiceNamespace: dynamodb
```

**Potential Savings**: $10-20/month

#### S3 Storage Optimization

**Lifecycle Policies**:
```yaml
# Already configured in template.yaml
LifecycleConfiguration:
  Rules:
    - Id: TransitionToIA
      Status: Enabled
      TransitionInDays: 30
      StorageClass: STANDARD_IA  # 50% cheaper
    
    - Id: TransitionToGlacier
      Status: Enabled
      TransitionInDays: 90
      StorageClass: GLACIER  # 80% cheaper
    
    - Id: DeleteOldObjects
      Status: Enabled
      ExpirationInDays: 365  # Delete after 1 year
```

**Request Optimization**:
```python
# Batch S3 operations to reduce request costs
import boto3
from concurrent.futures import ThreadPoolExecutor

def batch_s3_uploads(files):
    """Upload multiple files in parallel"""
    s3_client = boto3.client('s3')
    
    def upload_file(file_info):
        return s3_client.put_object(
            Bucket=file_info['bucket'],
            Key=file_info['key'],
            Body=file_info['content']
        )
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(upload_file, files))
    
    return results
```

**Potential Savings**: $5-10/month

### 4. Step Functions Optimization

#### State Machine Optimization

**Reduce State Transitions**:
```json
{
  "Comment": "Optimized state machine with fewer transitions",
  "StartAt": "BatchStages1to3",
  "States": {
    "BatchStages1to3": {
      "Type": "Parallel",
      "Branches": [
        {
          "StartAt": "Stage1ResearchAnalysis",
          "States": {
            "Stage1ResearchAnalysis": {
              "Type": "Task",
              "Resource": "${ResearchAnalysisFunction}",
              "End": true
            }
          }
        },
        {
          "StartAt": "PrepareClustering",
          "States": {
            "PrepareClustering": {
              "Type": "Task",
              "Resource": "${PrepareClusteringFunction}",
              "End": true
            }
          }
        }
      ],
      "Next": "Stage4ValueCurveMapping"
    }
  }
}
```

**Express Workflows for Simple Cases**:
```yaml
# For simple, fast operations
SimpleWorkflow:
  Type: AWS::StepFunctions::StateMachine
  Properties:
    StateMachineType: EXPRESS  # 50% cheaper than STANDARD
    RoleArn: !GetAtt StepFunctionRole.Arn
    DefinitionString: !Sub |
      {
        "Comment": "Express workflow for simple operations",
        "StartAt": "QuickProcess",
        "States": {
          "QuickProcess": {
            "Type": "Task",
            "Resource": "${QuickProcessFunction}",
            "End": true
          }
        }
      }
```

**Potential Savings**: $15-25/month

### 5. Development Environment Optimization

#### Scheduled Shutdowns

**Auto-shutdown for Development**:
```yaml
# EventBridge rule to shut down dev environment
DevShutdownRule:
  Type: AWS::Events::Rule
  Properties:
    ScheduleExpression: "cron(0 22 * * 1-5)"  # Shutdown at 10 PM weekdays
    Targets:
      - Arn: !GetAtt ShutdownFunction.Arn
        Id: "ShutdownTarget"

ShutdownFunction:
  Type: AWS::Serverless::Function
  Properties:
    Handler: shutdown.handler
    Runtime: python3.11
    Environment:
      Variables:
        STACK_NAME: !Ref AWS::StackName
    Code:
      ZipFile: |
        import boto3
        
        def handler(event, context):
            # Scale down DynamoDB to minimum
            # Delete CloudWatch logs older than 3 days
            # Put Lambda functions to sleep
            pass
```

**Weekend Pause**:
```python
# Pause non-essential services on weekends
import boto3
import os
from datetime import datetime

def weekend_pause():
    """Pause expensive services on weekends"""
    if datetime.now().weekday() >= 5:  # Saturday = 5, Sunday = 6
        # Scale down DynamoDB
        dynamodb = boto3.client('dynamodb')
        
        # Switch to on-demand (cheaper for low usage)
        dynamodb.modify_table(
            TableName=os.environ['TABLE_NAME'],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Disable non-essential alarms
        cloudwatch = boto3.client('cloudwatch')
        cloudwatch.disable_alarm_actions(
            AlarmNames=['non-essential-alarm-1', 'non-essential-alarm-2']
        )
```

**Potential Savings**: $20-30/month on dev environments

### 6. Monitoring Cost Optimization

#### Log Retention Optimization

**Tiered Retention Policy**:
```yaml
# Different retention for different log types
ApiGatewayLogGroup:
  Properties:
    RetentionInDays: !If [IsProduction, 90, 14]  # Less retention for non-prod

ErrorLogGroup:
  Properties:
    RetentionInDays: 180  # Keep errors longer

DebugLogGroup:
  Properties:
    RetentionInDays: 3   # Short retention for debug logs
```

**Selective Logging**:
```python
import os
import logging

# Only log what you need
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
logging.getLogger().setLevel(LOG_LEVEL)

# Reduce verbose logging in production
if os.getenv('ENVIRONMENT') == 'production':
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
```

**Potential Savings**: $10-15/month

### 7. Advanced Cost Optimization

#### Spot Instance Integration

**For Development/Testing**:
```yaml
# Use Spot instances for batch processing
SpotComputeEnvironment:
  Type: AWS::Batch::ComputeEnvironment
  Properties:
    Type: MANAGED
    State: ENABLED
    ComputeResources:
      Type: EC2
      BidPercentage: 50  # Bid 50% of On-Demand price
      InstanceTypes: [m5.large, m5.xlarge]
      MinvCpus: 0
      MaxvCpus: 100
```

#### Reserved Capacity

**For Predictable Workloads**:
```bash
# Purchase Savings Plans for consistent Lambda usage
aws savingsplans put-provisioned-capacity \
  --savings-plan-offering-id "sp-12345" \
  --commitment 100 \
  --upfront-payment-amount 1000
```

#### Multi-Region Cost Optimization

**Smart Region Selection**:
```python
# Choose cheapest region for non-latency-sensitive operations
REGION_COSTS = {
    'us-east-1': 1.0,      # Baseline
    'us-east-2': 0.95,     # 5% cheaper
    'us-west-2': 1.1,      # 10% more expensive
}

def choose_optimal_region(operation_type):
    if operation_type == 'batch_processing':
        return 'us-east-2'  # Use cheaper region
    else:
        return 'us-east-1'  # Use default region
```

## Cost Monitoring and Alerts

### Budget Setup

```bash
# Create budget with alerts
aws budgets create-budget \
  --account-id 123456789012 \
  --budget '{
    "BudgetName": "Multi-Step-LLM-Pipeline",
    "BudgetLimit": {
      "Amount": "500",
      "Unit": "USD"
    },
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST",
    "CostFilters": {
      "TagKey": ["Project"],
      "TagValue": ["multi-step-llm-pipeline"]
    }
  }' \
  --notifications-with-subscribers '[{
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 80,
      "ThresholdType": "PERCENTAGE"
    },
    "Subscribers": [{
      "SubscriptionType": "EMAIL",
      "Address": "admin@company.com"
    }]
  }]'
```

### Cost Tracking Dashboard

```python
# Create custom cost dashboard
import boto3
import json

cloudwatch = boto3.client('cloudwatch')

dashboard_body = {
    "widgets": [
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AWS/Billing", "EstimatedCharges", "Currency", "USD", "ServiceName", "AWSLambda"],
                    [".", ".", ".", ".", ".", "AmazonDynamoDB"],
                    [".", ".", ".", ".", ".", "AmazonS3"],
                    [".", ".", ".", ".", ".", "AWSStepFunctions"]
                ],
                "period": 86400,
                "stat": "Maximum",
                "region": "us-east-1",
                "title": "Daily Service Costs"
            }
        }
    ]
}

cloudwatch.put_dashboard(
    DashboardName='Pipeline-Costs',
    DashboardBody=json.dumps(dashboard_body)
)
```

### Automated Cost Analysis

```python
#!/usr/bin/env python3
"""
Weekly cost analysis report
Usage: python cost_analyzer.py --environment production
"""

import boto3
import json
from datetime import datetime, timedelta

def analyze_costs(environment):
    ce = boto3.client('ce')  # Cost Explorer
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    
    response = ce.get_cost_and_usage(
        TimePeriod={
            'Start': start_date.strftime('%Y-%m-%d'),
            'End': end_date.strftime('%Y-%m-%d')
        },
        Granularity='DAILY',
        Metrics=['BlendedCost'],
        GroupBy=[
            {'Type': 'DIMENSION', 'Key': 'SERVICE'},
            {'Type': 'TAG', 'Key': 'Environment'}
        ],
        Filter={
            'Tags': {
                'Key': 'Environment',
                'Values': [environment]
            }
        }
    )
    
    # Analyze and report
    total_cost = 0
    service_costs = {}
    
    for result in response['ResultsByTime']:
        for group in result['Groups']:
            service = group['Keys'][0]
            cost = float(group['Metrics']['BlendedCost']['Amount'])
            total_cost += cost
            service_costs[service] = service_costs.get(service, 0) + cost
    
    # Generate report
    print(f"💰 Weekly Cost Report - {environment}")
    print(f"📅 Period: {start_date} to {end_date}")
    print(f"💵 Total Cost: ${total_cost:.2f}")
    print("\n📊 Top Services:")
    
    sorted_services = sorted(service_costs.items(), key=lambda x: x[1], reverse=True)
    for service, cost in sorted_services[:10]:
        percentage = (cost / total_cost) * 100
        print(f"  {service}: ${cost:.2f} ({percentage:.1f}%)")
    
    # Cost optimization recommendations
    if total_cost > 100:  # Threshold for recommendations
        print("\n💡 Cost Optimization Recommendations:")
        
        if service_costs.get('AWSLambda', 0) > 50:
            print("  - Consider optimizing Lambda memory allocation")
        
        if service_costs.get('Amazon DynamoDB', 0) > 30:
            print("  - Review DynamoDB capacity settings")
        
        if service_costs.get('Amazon S3', 0) > 20:
            print("  - Implement S3 lifecycle policies")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--environment', required=True)
    args = parser.parse_args()
    
    analyze_costs(args.environment)
```

## Implementation Roadmap

### Phase 1: Quick Wins (Week 1-2)
- [ ] Optimize Lambda memory allocation
- [ ] Implement result caching for repeated operations
- [ ] Switch to cheaper models for dev/staging
- [ ] Set up cost alerts and budgets
- **Expected Savings**: $50-80/month

### Phase 2: Infrastructure Optimization (Week 3-4)
- [ ] Implement S3 lifecycle policies
- [ ] Optimize DynamoDB capacity
- [ ] Reduce CloudWatch log retention
- [ ] Set up automated shutdowns for dev
- **Expected Savings**: $30-50/month

### Phase 3: Advanced Optimization (Month 2)
- [ ] Implement smart model selection
- [ ] Add comprehensive caching layer
- [ ] Optimize Step Functions workflows
- [ ] Implement weekend pause for non-prod
- **Expected Savings**: $70-100/month

### Phase 4: Long-term Strategy (Month 3+)
- [ ] Implement Spot instances where appropriate
- [ ] Consider Reserved Capacity for predictable workloads
- [ ] Multi-region optimization
- [ ] Advanced monitoring and auto-scaling
- **Expected Savings**: $100-150/month

## Total Cost Savings Potential

| Phase | Implementation Time | Monthly Savings | Cumulative |
|-------|-------------------|-----------------|------------|
| Phase 1 | 2 weeks | $50-80 | $50-80 |
| Phase 2 | 2 weeks | $30-50 | $80-130 |
| Phase 3 | 4 weeks | $70-100 | $150-230 |
| Phase 4 | 8+ weeks | $100-150 | $250-380 |

**Total Potential Savings**: $250-380/month (50-75% cost reduction)

## Measurement and Tracking

### Key Metrics

1. **Cost per Pipeline Execution**
2. **Cost per Successful Pipeline**
3. **Infrastructure Cost vs API Cost Ratio**
4. **Month-over-Month Cost Growth**
5. **Cost per Environment**

### Success Criteria

- **Development**: <$50/month
- **Staging**: <$100/month  
- **Production**: <$300/month
- **Overall**: <$450/month total

### Monthly Review Process

1. **Week 1**: Analyze cost reports
2. **Week 2**: Identify optimization opportunities
3. **Week 3**: Implement quick wins
4. **Week 4**: Plan next month's optimizations

## Conclusion

Cost optimization is an ongoing process. The strategies outlined in this guide can significantly reduce your monthly AWS bill while maintaining or improving performance. Start with the quick wins in Phase 1 and gradually implement more advanced optimizations.

Remember:
- **Monitor continuously**: Set up alerts and regular reviews
- **Optimize incrementally**: Small changes compound over time
- **Measure impact**: Track savings and adjust strategies
- **Balance cost vs performance**: Don't sacrifice reliability for savings

For questions about cost optimization strategies, contact the DevOps team or create a GitHub issue.