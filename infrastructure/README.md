# Multi-Step LLM Pipeline - AWS Infrastructure

## Overview

This directory contains the complete AWS infrastructure for the Multi-Step LLM Pipeline, implemented using AWS SAM (Serverless Application Model). The infrastructure supports a 7-stage pipeline that transforms research documents into product innovation portfolios with automatic GitHub repository creation.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │    │  Step Functions │    │     Lambda      │
│                 │────│                 │────│   Functions     │
│  REST API       │    │ State Machine   │    │  (7 Stages)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CloudWatch    │    │    DynamoDB     │    │       S3        │
│                 │    │                 │    │                 │
│ Logs & Metrics  │    │  Job Tracking   │    │   Artifacts     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Components

### Core Infrastructure

| Component | Purpose | Configuration |
|-----------|---------|---------------|
| **API Gateway** | External API access | REST API with CORS, rate limiting |
| **Step Functions** | Pipeline orchestration | 7-stage state machine with error handling |
| **Lambda Functions** | Stage processing | 7 functions + utilities (starter, status, logs) |
| **DynamoDB** | Job tracking | On-demand billing, GSI for queries |
| **S3** | Artifact storage | Versioning, lifecycle policies, encryption |
| **Secrets Manager** | API key storage | Secure credential management |

### Monitoring & Observability

| Component | Purpose | Features |
|-----------|---------|----------|
| **CloudWatch** | Logging & metrics | Structured logs, custom metrics, dashboards |
| **X-Ray** | Distributed tracing | End-to-end request tracing |
| **CloudWatch Alarms** | Alerting | Failed executions, high error rates |
| **SNS** | Notifications | Email alerts for critical issues |

### Security

| Component | Purpose | Implementation |
|-----------|---------|----------------|
| **IAM Roles** | Access control | Least-privilege policies |
| **WAF** | Web protection | Rate limiting, common attack protection |
| **VPC** | Network isolation | Optional VPC configuration |
| **Encryption** | Data protection | At-rest and in-transit encryption |

## File Structure

```
infrastructure/
├── template.yaml              # Main SAM template
├── samconfig.toml             # SAM deployment configuration
├── README.md                  # This file
├── src/
│   ├── stepfunctions/
│   │   └── pipeline.asl.json  # Step Functions state machine
│   └── lambda/
│       ├── starter/           # API request handler
│       ├── status/            # Status endpoint handler
│       ├── logs/              # Logs endpoint handler
│       ├── cancel/            # Cancel endpoint handler
│       ├── stages/            # Pipeline stage handlers
│       └── cleanup/           # Automated cleanup
├── layers/
│   ├── dependencies/         # Python dependencies layer
│   └── utils/                # Common utilities layer
└── monitoring/
    └── cloudwatch-dashboard.json  # Dashboard configuration
```

## Environments

### Development
- **Stack**: `multi-step-llm-pipeline-dev`
- **Purpose**: Local development and testing
- **Features**: Fast builds, reduced timeouts
- **Cost**: ~$50-100/month

### Staging
- **Stack**: `multi-step-llm-pipeline-staging`
- **Purpose**: Pre-production testing
- **Features**: Production-like configuration
- **Cost**: ~$100-200/month

### Production
- **Stack**: `multi-step-llm-pipeline-prod`
- **Purpose**: Live production workloads
- **Features**: Full monitoring, WAF, high availability
- **Cost**: ~$200-500/month

## Deployment

### Prerequisites

```bash
# Install required tools
pip install aws-sam-cli==1.100.0
aws configure --profile mvp

# Verify access
aws sts get-caller-identity --profile mvp
```

### Quick Deployment

```bash
# Deploy to development
./scripts/deploy.sh

# Deploy to staging
./scripts/deploy.sh staging

# Deploy to production
./scripts/deploy.sh production
```

### Manual Deployment

```bash
cd infrastructure

# Build
sam build --config-env development

# Deploy
sam deploy --config-env development
```

### CI/CD Deployment

Push to GitHub branches:
- `main` → Production
- `develop` → Staging  
- `feature/*` → Development

## Configuration

### Environment Variables

Set in each Lambda function:
- `ENVIRONMENT`: Environment name (development/staging/production)
- `PIPELINE_TABLE`: DynamoDB table name
- `PIPELINE_BUCKET`: S3 bucket name
- `SECRETS_ARN`: Secrets Manager ARN

### API Keys

Store in AWS Secrets Manager:
```json
{
  "ANTHROPIC_API_KEY": "sk-ant-api03-...",
  "OPENAI_API_KEY": "sk-...",
  "EXA_API_KEY": "...",
  "COHERE_API_KEY": "...", 
  "GITHUB_TOKEN": "ghp_...",
  "PERPLEXITY_KEY": "pplx-..."
}
```

Update secrets:
```bash
aws secretsmanager put-secret-value \
  --secret-id multi-step-llm-pipeline-dev-secrets \
  --secret-string '{"ANTHROPIC_API_KEY":"your-key",...}' \
  --profile mvp
```

## API Endpoints

### Pipeline Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/pipeline/start` | Start new pipeline |
| `GET` | `/pipeline/status/{jobId}` | Get job status |
| `GET` | `/pipeline/logs/{jobId}` | Get job logs |
| `POST` | `/pipeline/cancel/{jobId}` | Cancel job |

### Usage Examples

**Start Pipeline**:
```bash
curl -X POST "https://api.execute-api.us-east-1.amazonaws.com/development/pipeline/start" \
  -H "Content-Type: application/json" \
  -d '{"researchDocId":"test-doc-123","username":"testuser"}'
```

**Check Status**:
```bash
curl "https://api.execute-api.us-east-1.amazonaws.com/development/pipeline/status/job-20240807-abc123"
```

## Monitoring

### CloudWatch Dashboard

Access comprehensive dashboard:
```bash
# Get dashboard URL
aws cloudformation describe-stacks \
  --stack-name multi-step-llm-pipeline-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`DashboardUrl`].OutputValue' \
  --output text
```

### Key Metrics

- **Pipeline Success Rate**: Target >95%
- **Execution Duration**: Target <25 minutes
- **Error Rate**: Target <5%
- **API Response Time**: Target <2 seconds

### Log Analysis

**View Recent Errors**:
```bash
aws logs tail /aws/lambda/multi-step-llm-pipeline-research-analysis-dev \
  --start-time 2024-08-07T00:00:00 \
  --filter-pattern "ERROR" \
  --profile mvp
```

**CloudWatch Insights Query**:
```sql
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
```

## Cost Optimization

### Current Costs (Monthly)

| Environment | Low Usage | Medium Usage | High Usage |
|-------------|-----------|--------------|------------|
| Development | $50 | $100 | $200 |
| Staging | $100 | $200 | $400 |
| Production | $200 | $500 | $1,000 |

### Optimization Strategies

1. **Lambda Memory Tuning**: Right-size memory allocation
2. **Model Selection**: Use cheaper models for simple tasks
3. **Result Caching**: Cache LLM responses
4. **Lifecycle Policies**: Auto-delete old S3 objects
5. **Reserved Capacity**: For predictable workloads

See [Cost Optimization Guide](../docs/COST_OPTIMIZATION.md) for details.

## Security

### IAM Policies

All components use least-privilege access:
- Lambda functions can only access required resources
- API Gateway has rate limiting
- S3 buckets block public access
- Secrets are encrypted at rest

### Network Security

- Optional VPC deployment
- Security groups restrict access
- WAF protection in production
- All data encrypted in transit

### Compliance

- SOC 2 Type II (AWS infrastructure)
- GDPR compliant (configurable data retention)
- HIPAA eligible (with BAA)

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `502 Bad Gateway` | Lambda error | Check CloudWatch logs |
| `Task timed out` | Long operation | Increase timeout |
| `AccessDenied` | IAM issue | Check permissions |
| `SecretNotFound` | Missing keys | Update Secrets Manager |

### Diagnostic Tools

**Health Check**:
```bash
python pipeline-doctor.py --environment production
```

**Log Analysis**:
```bash
python log-analyzer.py --job-id job-123 --last-hours 2
```

See [Troubleshooting Guide](../docs/TROUBLESHOOTING.md) for detailed help.

## Development

### Local Testing

```bash
# Start local API
sam local start-api --config-env development

# Test function locally
sam local invoke ResearchAnalysisFunction \
  --event events/research-analysis.json
```

### Adding New Stages

1. Create Lambda function in `template.yaml`
2. Add handler to `src/lambda/stages/`
3. Update Step Functions definition
4. Deploy and test

### Custom Metrics

```python
import boto3

cloudwatch = boto3.client('cloudwatch')
cloudwatch.put_metric_data(
    Namespace='Pipeline/Custom',
    MetricData=[{
        'MetricName': 'ProcessingTime',
        'Value': execution_time,
        'Unit': 'Seconds'
    }]
)
```

## Maintenance

### Regular Tasks

- **Weekly**: Review error rates and performance
- **Monthly**: Analyze costs and optimize
- **Quarterly**: Update dependencies and security patches

### Updates

```bash
# Update infrastructure
sam deploy --config-env production

# Update secrets
aws secretsmanager put-secret-value --secret-id ... --secret-string ...

# Update configuration
# Edit template.yaml or samconfig.toml and redeploy
```

### Backup & Recovery

- **DynamoDB**: Point-in-time recovery enabled
- **S3**: Versioning and cross-region replication
- **Infrastructure**: Version controlled in Git
- **Secrets**: Manual backup required

## Support

### Documentation

- [Deployment Guide](../docs/DEPLOYMENT.md)
- [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)
- [Cost Optimization Guide](../docs/COST_OPTIMIZATION.md)

### Getting Help

1. Check CloudWatch logs for errors
2. Review troubleshooting guide
3. Check AWS Service Health Dashboard
4. Create GitHub issue with details

### Emergency Procedures

**Critical Failure**:
1. Check system status via dashboard
2. Review recent deployments
3. Execute rollback if needed
4. Contact on-call engineer

**Security Incident**:
1. Rotate compromised credentials
2. Review access logs
3. Update security groups if needed
4. Document incident response

---

## Quick Reference

### Useful Commands

```bash
# Deploy
sam deploy --config-env production

# Check status
aws cloudformation describe-stacks --stack-name multi-step-llm-pipeline-dev

# View logs
aws logs tail /aws/lambda/function-name --follow

# Update secrets
aws secretsmanager put-secret-value --secret-id secret-name --secret-string '{...}'

# Test API
curl -X POST "API_ENDPOINT/pipeline/start" -H "Content-Type: application/json" -d '{...}'
```

### Important ARNs

```bash
# Get key ARNs
aws cloudformation describe-stacks \
  --stack-name multi-step-llm-pipeline-prod \
  --query 'Stacks[0].Outputs'
```

### Environment URLs

| Environment | API Endpoint | Dashboard |
|------------|--------------|-----------|
| Development | `https://api-dev.execute-api.us-east-1.amazonaws.com/development` | [Dashboard](https://console.aws.amazon.com/cloudwatch) |
| Staging | `https://api-staging.execute-api.us-east-1.amazonaws.com/staging` | [Dashboard](https://console.aws.amazon.com/cloudwatch) |
| Production | `https://api-prod.execute-api.us-east-1.amazonaws.com/production` | [Dashboard](https://console.aws.amazon.com/cloudwatch) |