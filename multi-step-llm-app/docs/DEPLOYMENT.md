# Multi-Step LLM Pipeline - Deployment Guide

## Overview

This guide covers the complete deployment process for the Multi-Step LLM Pipeline, including infrastructure provisioning, CI/CD setup, monitoring configuration, and operational procedures.

## Architecture

The pipeline consists of:
- **7 Lambda Functions** for each pipeline stage
- **Step Functions State Machine** for orchestration
- **API Gateway** for external access
- **DynamoDB** for job tracking
- **S3** for artifact storage
- **CloudWatch** for monitoring
- **Secrets Manager** for API keys

## Prerequisites

### Required Tools

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install SAM CLI
pip install aws-sam-cli==1.100.0

# Install Python dependencies
pip install -r requirements.txt
```

### AWS Configuration

1. **Create AWS Profile**:
```bash
aws configure --profile mvp
# Enter Access Key, Secret Key, Region (us-east-1), Output format (json)
```

2. **Verify Access**:
```bash
aws sts get-caller-identity --profile mvp
```

3. **Create S3 Bucket for Deployments** (if not exists):
```bash
aws s3 mb s3://sam-deploy-your-org-$(aws sts get-caller-identity --query Account --output text) --profile mvp
```

### API Keys Setup

Create AWS Secrets Manager secrets for each environment:

```bash
# Development
aws secretsmanager create-secret \
  --name "multi-step-llm-pipeline-dev-secrets" \
  --description "API keys for development environment" \
  --secret-string '{
    "ANTHROPIC_API_KEY": "your-anthropic-key",
    "OPENAI_API_KEY": "your-openai-key",
    "EXA_API_KEY": "your-exa-key",
    "COHERE_API_KEY": "your-cohere-key",
    "GITHUB_TOKEN": "your-github-token",
    "PERPLEXITY_KEY": "your-perplexity-key"
  }' \
  --profile mvp

# Staging
aws secretsmanager create-secret \
  --name "multi-step-llm-pipeline-staging-secrets" \
  --description "API keys for staging environment" \
  --secret-string '{...}' \
  --profile mvp

# Production
aws secretsmanager create-secret \
  --name "multi-step-llm-pipeline-prod-secrets" \
  --description "API keys for production environment" \
  --secret-string '{...}' \
  --profile mvp
```

## Deployment Methods

### Method 1: Quick Deployment Script

```bash
# Deploy to development
./scripts/deploy.sh

# Deploy to staging
./scripts/deploy.sh staging

# Deploy to production (with confirmation)
./scripts/deploy.sh production

# Force deploy (skip change detection)
./scripts/deploy.sh production --force-deploy

# Dry run (show what would be deployed)
./scripts/deploy.sh production --dry-run
```

### Method 2: Manual SAM Deployment

```bash
cd infrastructure

# Build
sam build --config-env development

# Deploy
sam deploy --config-env development

# Or deploy with custom parameters
sam deploy \
  --stack-name multi-step-llm-pipeline-dev \
  --parameter-overrides "EnvironmentName=development NotificationEmail=your@email.com" \
  --capabilities CAPABILITY_IAM
```

### Method 3: GitHub Actions CI/CD

1. **Set up GitHub Secrets**:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_ACCESS_KEY_ID_PROD`
   - `AWS_SECRET_ACCESS_KEY_PROD`
   - `NOTIFICATION_EMAIL`
   - All API keys (`ANTHROPIC_API_KEY`, etc.)

2. **Trigger Deployment**:
   - Push to `main` → Production deployment
   - Push to `develop` → Staging deployment
   - Push to feature branches → Development deployment
   - Manual workflow dispatch for custom deployments

## Environment Configuration

### Development
- **Purpose**: Local development and testing
- **Stack**: `multi-step-llm-pipeline-dev`
- **Features**: Fast builds, reduced timeouts, minimal monitoring
- **Cost**: ~$50-100/month

### Staging
- **Purpose**: Pre-production testing
- **Stack**: `multi-step-llm-pipeline-staging`
- **Features**: Production-like configuration, full monitoring
- **Cost**: ~$100-200/month

### Production
- **Purpose**: Live production workloads
- **Stack**: `multi-step-llm-pipeline-prod`
- **Features**: Full monitoring, WAF, high availability, backups
- **Cost**: ~$200-500/month

## Post-Deployment Configuration

### 1. Update API Keys

After deployment, update the secrets with your actual API keys:

```bash
ENVIRONMENT=development  # or staging, production
STACK_NAME="multi-step-llm-pipeline-${ENVIRONMENT}"

aws secretsmanager put-secret-value \
  --secret-id "${STACK_NAME}-secrets" \
  --secret-string '{
    "ANTHROPIC_API_KEY": "sk-ant-api03-...",
    "OPENAI_API_KEY": "sk-...",
    "EXA_API_KEY": "...",
    "COHERE_API_KEY": "...",
    "GITHUB_TOKEN": "ghp_...",
    "PERPLEXITY_KEY": "pplx-..."
  }' \
  --profile mvp
```

### 2. Test Deployment

```bash
# Get API endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name "multi-step-llm-pipeline-dev" \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text \
  --profile mvp)

# Test pipeline creation
curl -X POST "${API_ENDPOINT}/pipeline/start" \
  -H "Content-Type: application/json" \
  -d '{"researchDocId":"test-deployment","username":"testuser"}'

# Expected response:
# {"jobId":"job-20240807-a1b2c3d4","status":"QUEUED",...}

# Check status
JOB_ID="job-20240807-a1b2c3d4"  # Use actual job ID from response
curl "${API_ENDPOINT}/pipeline/status/${JOB_ID}"
```

### 3. Configure Monitoring

Access CloudWatch Dashboard:
```bash
DASHBOARD_URL=$(aws cloudformation describe-stacks \
  --stack-name "multi-step-llm-pipeline-dev" \
  --query 'Stacks[0].Outputs[?OutputKey==`DashboardUrl`].OutputValue' \
  --output text \
  --profile mvp)

echo "Dashboard: $DASHBOARD_URL"
```

## Monitoring and Observability

### CloudWatch Dashboards

Each environment includes a comprehensive dashboard with:
- **Pipeline Execution Metrics**: Success rate, duration, failures
- **Lambda Function Metrics**: Duration, errors, throttles
- **DynamoDB Metrics**: Capacity usage, throttling
- **S3 Metrics**: Storage usage, object count
- **API Gateway Metrics**: Request count, latency, errors
- **Recent Failures Log**: Failed pipeline executions
- **Error Logs**: Lambda function errors and warnings

### Alarms

Key alarms configured:
- **Failed Executions**: Triggers when pipeline executions fail
- **High Error Rate**: Triggers when Lambda error rate exceeds threshold
- **DynamoDB Throttling**: Monitors database performance
- **API Gateway Errors**: Monitors API health

### X-Ray Tracing

Distributed tracing is enabled for:
- All Lambda functions
- Step Functions executions
- API Gateway requests

View traces in AWS X-Ray console to analyze performance bottlenecks.

## Cost Optimization

### Current Costs (Estimated)

| Component | Development | Staging | Production |
|-----------|------------|---------|------------|
| Lambda Compute | $20-40 | $40-80 | $80-150 |
| Step Functions | $5-10 | $10-20 | $20-40 |
| DynamoDB | $5-15 | $15-30 | $30-60 |
| S3 Storage | $5-10 | $10-20 | $20-40 |
| API Gateway | $3-5 | $5-10 | $10-20 |
| CloudWatch | $5-10 | $10-20 | $20-40 |
| **Total** | **$43-90** | **$90-180** | **$180-350** |

### Cost Optimization Strategies

1. **Auto-cleanup**: Old jobs and artifacts are automatically deleted after 30 days
2. **Reserved Concurrency**: Limits to prevent cost overruns
3. **S3 Lifecycle**: Transitions to cheaper storage classes over time
4. **DynamoDB On-Demand**: Pay only for what you use
5. **CloudWatch Log Retention**: Configurable retention periods

### Cost Monitoring

Set up billing alerts:
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "pipeline-monthly-cost-alarm" \
  --alarm-description "Alert when monthly costs exceed $200" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 86400 \
  --threshold 200 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=Currency,Value=USD \
  --evaluation-periods 1 \
  --alarm-actions "arn:aws:sns:us-east-1:ACCOUNT:billing-alerts" \
  --profile mvp
```

## Security

### IAM Roles and Policies

All components use least-privilege IAM policies:
- Lambda functions can only access required resources
- API Gateway has rate limiting and WAF protection (production)
- S3 bucket blocks public access
- DynamoDB table has backup enabled

### Secrets Management

- API keys stored in AWS Secrets Manager
- Automatic rotation supported (configure manually)
- No secrets in code or CloudFormation templates

### Network Security

- Lambda functions can optionally run in VPC
- Security groups restrict network access
- WAF protects API Gateway in production

## Troubleshooting

### Common Deployment Issues

1. **SAM Build Fails**
   ```bash
   # Clear cache and rebuild
   sam build --use-container --cached false
   ```

2. **Permission Denied**
   ```bash
   # Check AWS credentials
   aws sts get-caller-identity --profile mvp
   
   # Verify IAM permissions for CloudFormation, Lambda, etc.
   ```

3. **Template Validation Errors**
   ```bash
   # Validate template
   sam validate --template infrastructure/template.yaml
   ```

4. **Secrets Not Found**
   ```bash
   # Create missing secrets
   aws secretsmanager create-secret --name "missing-secret-name" --profile mvp
   ```

### Runtime Issues

1. **Pipeline Failures**
   - Check CloudWatch logs for each Lambda function
   - Review Step Functions execution history
   - Verify API keys in Secrets Manager

2. **High Costs**
   - Check CloudWatch billing dashboard
   - Review Lambda function duration and memory
   - Look for failed executions causing retries

3. **Performance Issues**
   - Use X-Ray traces to identify bottlenecks
   - Check Lambda memory and timeout settings
   - Monitor DynamoDB throttling

### Rollback Procedures

1. **Quick Rollback**
   ```bash
   # Deploy previous version
   sam deploy --config-env production --parameter-overrides "Version=previous"
   ```

2. **Full Stack Rollback**
   ```bash
   # Delete and recreate (nuclear option)
   aws cloudformation delete-stack --stack-name multi-step-llm-pipeline-prod --profile mvp
   # Then redeploy previous version
   ```

## Maintenance

### Regular Tasks

1. **Monthly**: Review costs and optimize
2. **Weekly**: Check error rates and performance
3. **Daily**: Monitor pipeline success rates

### Updates

1. **Code Updates**: Use CI/CD pipeline
2. **Dependency Updates**: Update requirements.txt and redeploy
3. **Infrastructure Updates**: Update template.yaml and redeploy
4. **API Key Rotation**: Update secrets monthly

### Backup and Recovery

- **DynamoDB**: Point-in-time recovery enabled
- **S3**: Versioning and lifecycle policies
- **Code**: Version controlled in Git
- **Infrastructure**: Infrastructure as Code in CloudFormation

## Advanced Configuration

### Custom Domains

Add custom domain to API Gateway:
```yaml
# In template.yaml
Domain:
  Type: AWS::ApiGateway::DomainName
  Properties:
    DomainName: api.yourcompany.com
    CertificateArn: !Ref SSLCertificate
```

### Blue/Green Deployments

Use SAM gradual deployments:
```yaml
# In template.yaml Globals
Function:
  DeploymentPreference:
    Type: Linear10PercentEvery2Minutes
    Alarms:
      - !Ref ErrorRate
```

### Multi-Region Setup

Deploy to multiple regions for high availability:
```bash
# Deploy to us-west-2
sam deploy --config-env production --region us-west-2
```

## Support

### Getting Help

1. **Documentation**: Check this guide and AWS documentation
2. **Logs**: CloudWatch logs contain detailed error information
3. **Monitoring**: Use CloudWatch dashboard and X-Ray traces
4. **Community**: AWS forums and Stack Overflow

### Contact Information

- **Technical Issues**: Create GitHub issue
- **Security Issues**: Email security team
- **General Questions**: Team Slack channel

---

## Quick Reference

### Useful Commands

```bash
# Deploy to development
./scripts/deploy.sh

# Check stack status
aws cloudformation describe-stacks --stack-name multi-step-llm-pipeline-dev --profile mvp

# View logs
aws logs tail /aws/lambda/multi-step-llm-pipeline-dev-research-analysis --follow --profile mvp

# Update secrets
aws secretsmanager put-secret-value --secret-id stack-secrets --secret-string '{}' --profile mvp

# Test API
curl -X POST "API_ENDPOINT/pipeline/start" -H "Content-Type: application/json" -d '{"researchDocId":"test","username":"user"}'
```

### Environment URLs

| Environment | API Endpoint | Dashboard |
|------------|--------------|-----------|
| Development | `https://api-dev.execute-api.us-east-1.amazonaws.com/development` | [CloudWatch Dashboard](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:) |
| Staging | `https://api-staging.execute-api.us-east-1.amazonaws.com/staging` | [CloudWatch Dashboard](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:) |
| Production | `https://api-prod.execute-api.us-east-1.amazonaws.com/production` | [CloudWatch Dashboard](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:) |