# CDK Infrastructure for Multi-Step LLM Pipeline

## Overview

This directory contains the AWS CDK (Cloud Development Kit) infrastructure code for deploying the Multi-Step LLM Pipeline to AWS Batch. The infrastructure is currently deployed to production and integrated with the frontend application.

**Production API**: `https://9hv22ga3uh.execute-api.us-east-1.amazonaws.com/prod/`

## Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌────────────────┐
│  Frontend    │────▶│  API Gateway     │────▶│    Lambda      │
│              │     │  (9hv22ga3uh)    │     │ (CORS-enabled) │
└──────────────┘     └──────────────────┘     └────────────────┘
                                                       │
                                                       ▼
                                                ┌──────────────┐
                                                │  AWS Batch   │
                                                │  (Fargate)   │
                                                └──────────────┘
                                                       │
                                         ┌─────────────┴──────────────┐
                                         ▼                            ▼
                                   ┌──────────┐              ┌──────────────────┐
                                   │    S3    │              │    DynamoDB      │
                                   └──────────┘              │ ResearchReports  │
                                                             └──────────────────┘
```

## Components

### CDK Stack (`cdk_batch_pipeline.py`)

The main CDK stack creates:

1. **VPC and Networking**
   - Private subnets for Batch compute
   - NAT Gateway for outbound internet access (LLM API calls)

2. **AWS Batch Resources**
   - Fargate compute environment (serverless, auto-scaling)
   - Job queue: `multi-step-llm-queue`
   - Job definition: 4 vCPUs, 16GB RAM, 50GB storage
   - 2-hour timeout per job

3. **Lambda Functions (CORS-enabled)**
   - `pipeline-submit-job`: Validates research in ResearchReports table, submits Batch job
   - `pipeline-monitor-logs`: Retrieves job status and CloudWatch logs
   - Both include comprehensive CORS headers for frontend integration

4. **API Gateway**
   - REST API with CORS configuration
   - API ID: `9hv22ga3uh`
   - Endpoints:
     - `POST /submit` - Submit pipeline job
     - `GET /logs/{researchId}` - Get job logs

5. **DynamoDB Tables**
   - `ResearchReports`: Frontend-managed table
     - Primary key: `reportId`
     - Contains: `s3ReportKey`, `status`, `createdAt`, `metadata`
   - `PipelineBatchJobs`: Backend job tracking
     - Primary key: `jobId`
     - GSI: `ResearchIdIndex` on `researchId`

6. **S3 Bucket**
   - Bucket: `multi-step-llm-research-984906149037`
   - Stores input research files
   - Stores pipeline outputs organized by research ID

7. **ECR Repository**
   - Repository: `multi-step-llm-pipeline`
   - Created by `make docker` command
   - Stores containerized pipeline image

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **AWS CDK CLI** installed: `npm install -g aws-cdk`
3. **Python 3.11+** installed
4. **Docker** installed and running
5. **AWS account** with necessary permissions
6. **ECR repository** created by `make docker`

## Deployment

### Quick Deploy

```bash
# From the project root
make deploy
```

This will:
1. Build and push Docker image to ECR
2. Deploy CDK stack with all resources

### Step-by-Step Deployment

1. **Bootstrap CDK** (first time only):
```bash
make cdk-bootstrap
# Or manually:
cdk bootstrap aws://984906149037/us-east-1 --profile mvp
```

2. **Build and push Docker image**:
```bash
make docker
# This creates ECR repository and pushes image
```

3. **Deploy infrastructure**:
```bash
make cdk-deploy
# Or manually:
cd infrastructure
cdk deploy --require-approval never --profile mvp
```

## Common Deployment Issues and Solutions

### ECR Repository Already Exists
- **Issue**: ECR repository `multi-step-llm-pipeline` already exists
- **Solution**: The CDK now imports the existing repository - no action needed

### S3 Bucket Already Exists
- **Issue**: S3 bucket `multi-step-llm-research-984906149037` already exists
- **Solution**: The CDK imports the existing bucket - no action needed

### Job Queue Already Exists
- **Issue**: Batch job queue `multi-step-llm-queue` already exists
- **Solution**: 
  ```bash
  aws batch delete-job-queue --job-queue multi-step-llm-queue --profile mvp
  # Wait for deletion to complete, then redeploy
  ```

### CDK Dependencies Error
- **Issue**: "No matching distribution found for aws-cdk.aws-batch-alpha"
- **Solution**: Requirements have been fixed to use stable constructs
  ```bash
  cd infrastructure
  pip install -r requirements-cdk.txt
  ```

## Integration with Frontend

### CORS Configuration

All Lambda functions include these headers:
```python
{
    'headers': {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
    }
}
```

### Table Integration

The Lambda functions look for research in the `ResearchReports` table:
- Table name: `ResearchReports` (not `PipelineResearch`)
- Key field: `reportId` (not `researchId`)
- S3 key field: `s3ReportKey` (not `s3Key`)

### Common Integration Issues

1. **CORS Errors**
   - All Lambda functions now include CORS headers
   - Check browser console for specific error
   - Verify API Gateway CORS configuration

2. **Research Not Found (404)**
   - Ensure `reportId` exists in ResearchReports table
   - Check that `s3ReportKey` field is populated
   - Verify in DynamoDB console

3. **API 404 Errors**
   - Verify URL: `https://9hv22ga3uh.execute-api.us-east-1.amazonaws.com/prod/`
   - Check endpoint paths: `/submit`, `/logs/{id}`
   - Ensure no double slashes in URL

## Monitoring

### CloudWatch Logs
- Log Group: `/aws/batch/job/multi-step-llm`
- Log Streams: `pipeline/default/{JOB_ID}`
- Retention: 30 days
- Access via API: `GET /logs/{researchId}`

### Batch Console
- View jobs: https://console.aws.amazon.com/batch/
- Job queue: `multi-step-llm-queue`
- Monitor status: SUBMITTED → PENDING → RUNNING → SUCCEEDED/FAILED

### DynamoDB Console
- View tables: https://console.aws.amazon.com/dynamodbv2/
- `ResearchReports`: Check frontend research documents
- `PipelineBatchJobs`: Track job execution

### Useful Commands

```bash
# View recent Batch job logs
make batch-logs

# Check job status
make batch-status

# Submit a test job
make batch-submit

# Test container locally
make docker-test

# View CloudWatch logs
aws logs tail /aws/batch/job/multi-step-llm --follow --profile mvp

# Check DynamoDB items
aws dynamodb scan --table-name ResearchReports --profile mvp
aws dynamodb scan --table-name PipelineBatchJobs --profile mvp
```

## Cost Estimation

Per pipeline run:
- **Batch (Fargate)**: ~$0.20 (10-15 minutes @ 4 vCPU, 16GB)
- **Lambda**: < $0.01 (minimal invocations)
- **API Gateway**: Negligible
- **DynamoDB**: Minimal with on-demand pricing
- **S3**: < $0.01 per run
- **CloudWatch Logs**: < $0.05 per run
- **Total**: ~$0.25-0.30 per pipeline run

Monthly estimates (100 runs):
- Development/Testing: ~$30-50
- Production: ~$50-100

## Security

### Secrets Management
- All API keys stored in AWS Secrets Manager
- Secrets ARN pattern: `arn:aws:secretsmanager:us-east-1:984906149037:secret:{key_name}-*`
- Required secrets:
  - `anthropic_key`
  - `openai_key`
  - `cohere-key`
  - `github_token_blue_ocean`
  - `perplexity-key`

### IAM Roles
- **Task Execution Role**: Pulls images, writes logs, accesses secrets
- **Task Role**: S3 and DynamoDB access for running container
- **Lambda Execution Roles**: Minimal permissions for each function
- All roles follow least-privilege principle

### Network Security
- Batch runs in private VPC subnets
- NAT Gateway provides controlled outbound access
- No inbound internet access to compute resources
- S3 bucket encryption at rest
- DynamoDB encryption enabled

## Files

- `cdk_batch_pipeline.py` - Main CDK stack definition with Lambda functions
- `app.py` - CDK app entry point
- `cdk.json` - CDK configuration
- `requirements-cdk.txt` - Python dependencies for CDK
- `INTEGRATION_GUIDE.md` - Frontend-backend integration documentation
- `CDK_README.md` - This file

## Related Documentation

- [Integration Guide](./INTEGRATION_GUIDE.md) - Detailed frontend integration
- [Batch Deployment Guide](../BATCH_DEPLOYMENT.md) - Complete deployment instructions
- [Architecture](../ARCHITECTURE.md) - System architecture overview
- [Main README](../README.md) - Project overview

## Cleanup

To remove all AWS resources:

```bash
# Complete cleanup
make cdk-destroy

# This will:
# - Delete all AWS resources (except S3 bucket)
# - Retain data in S3 (manual deletion required)

# Manual cleanup if needed:
aws s3 rm s3://multi-step-llm-research-984906149037/ --recursive --profile mvp
aws ecr delete-repository --repository-name multi-step-llm-pipeline --force --profile mvp
```

## Support

For issues:
1. Check CloudWatch Logs for detailed error messages
2. Verify research exists in ResearchReports table
3. Ensure S3 permissions are correctly configured
4. Review Lambda function logs for CORS or execution errors
5. Check the [Integration Guide](./INTEGRATION_GUIDE.md) for frontend issues