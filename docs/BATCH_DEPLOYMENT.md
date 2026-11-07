# AWS Batch Deployment Guide for Multi-Step LLM Pipeline

## Overview

This guide walks through deploying the Multi-Step LLM Pipeline to AWS Batch with API Gateway endpoints for triggering and monitoring jobs. The deployment uses AWS CDK (Cloud Development Kit) for infrastructure as code and maintains the integrity of the original `run_pipeline.py` script by wrapping it with `batch_wrapper.py`.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend  │────▶│ API Gateway  │────▶│   Lambda    │
│             │     │ (9hv22ga3uh) │     │ Functions   │
└─────────────┘     └──────────────┘     └─────────────┘
                                                 │
                                                 ▼
                                          ┌─────────────┐
                                          │ AWS Batch   │
                                          └─────────────┘
                                                 │
                                    ┌────────────┴────────────┐
                                    ▼                         ▼
                              ┌──────────┐            ┌──────────────┐
                              │    S3    │            │  DynamoDB    │
                              └──────────┘            └──────────────┘
```

**Production API Endpoint**: `https://9hv22ga3uh.execute-api.us-east-1.amazonaws.com/prod/`

## Components

1. **API Gateway**: REST API with CORS-enabled endpoints
   - `POST /submit` - Submit a new pipeline job
   - `GET /logs/{researchId}` - Get logs for a research job
   - **API ID**: `9hv22ga3uh`
   - **Full URL**: `https://9hv22ga3uh.execute-api.us-east-1.amazonaws.com/prod/`

2. **Lambda Functions**:
   - `pipeline-submit-job` - Looks up research in ResearchReports table, submits Batch job
   - `pipeline-monitor-logs` - Retrieves job status and CloudWatch logs
   - Both functions include comprehensive CORS headers for frontend integration

3. **AWS Batch**:
   - Fargate compute environment (serverless)
   - Job queue and job definition
   - Runs containerized pipeline with 4 vCPUs and 16GB RAM

4. **DynamoDB Tables**:
   - `ResearchReports` - Frontend-managed table with research documents
     - Primary key: `reportId` (string)
     - Contains: `s3ReportKey`, `status`, `createdAt`, `metadata`
   - `PipelineBatchJobs` - Tracks Batch job runs with research association

5. **S3 Bucket**:
   - Stores research input files
   - Stores pipeline output files organized by research ID

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with credentials
3. **Docker** installed for building container images
4. **Python 3.11+** for CDK
5. **Node.js 18+** for CDK CLI

## Quick Deployment Using Makefile

The easiest way to deploy is using the provided Makefile:

```bash
# Complete deployment (Docker + CDK)
make deploy

# Or step by step:
make cdk-bootstrap  # First time only
make docker         # Build and push image
make cdk-deploy     # Deploy infrastructure
```

## Manual Deployment Steps

### 1. Install CDK CLI

```bash
npm install -g aws-cdk
```

### 2. Bootstrap CDK (first time only)

```bash
make cdk-bootstrap
# Or manually:
cdk bootstrap aws://984906149037/us-east-1 --profile mvp
```

### 3. Build and push Docker image

```bash
make docker
# This runs:
# - docker build with verbose output
# - ECR repository creation
# - docker push to ECR
```

### 4. Deploy CDK Stack

```bash
make cdk-deploy
# Or manually:
cd infrastructure
cdk deploy --require-approval never --profile mvp
```

### 5. Note the outputs

After deployment, you'll see:
- API Gateway URL: `https://9hv22ga3uh.execute-api.us-east-1.amazonaws.com/prod/`
- ECR Repository URI: `984906149037.dkr.ecr.us-east-1.amazonaws.com/multi-step-llm-pipeline`
- Job Queue: `multi-step-llm-queue`
- DynamoDB Tables: 
  - `ResearchReports` (frontend-managed, uses `reportId` as key)
  - `PipelineBatchJobs` (backend job tracking)
- S3 Bucket: `multi-step-llm-research-984906149037`

## Usage

### 1. Frontend creates research in ResearchReports table

The frontend application manages research documents in the `ResearchReports` table:

```python
import boto3
import json
from datetime import datetime, timedelta

# Frontend uploads research file to S3
s3 = boto3.client('s3')
bucket = 'multi-step-llm-research-984906149037'
key = f'research/{datetime.now().isoformat()}/research.json'

with open('sample_research.json', 'rb') as f:
    s3.put_object(Bucket=bucket, Key=key, Body=f)

# Frontend registers in ResearchReports table (NOT PipelineResearch)
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ResearchReports')  # Frontend-managed table

report_id = 'report-2024-12-15-123456'  # Frontend format
table.put_item(
    Item={
        'reportId': report_id,  # Note: 'reportId' not 'researchId'
        's3ReportKey': key,     # Note: 's3ReportKey' not 's3Key'
        'status': 'ready',
        'createdAt': datetime.now().isoformat(),
        'metadata': {
            'title': 'Market Research Report',
            'description': 'Analysis of emerging markets'
        }
    }
)
```

### 2. Submit a pipeline job

```bash
# Using curl with production endpoint
curl -X POST https://9hv22ga3uh.execute-api.us-east-1.amazonaws.com/prod/submit \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3000" \
  -d '{"researchId": "report-2024-12-15-123456"}'

# Note: researchId should match a reportId from ResearchReports table
```

Response:
```json
{
  "jobId": "abc123-def456-...",
  "jobName": "pipeline-RESEARCH-001-20250807-195500",
  "status": "SUBMITTED",
  "message": "Pipeline job submitted successfully"
}
```

### 3. Monitor job logs

```bash
# Get job status and logs using production endpoint
curl https://9hv22ga3uh.execute-api.us-east-1.amazonaws.com/prod/logs/report-2024-12-15-123456

# The endpoint includes CORS headers for frontend access
```

Response:
```json
{
  "jobId": "abc123-def456-...",
  "researchId": "RESEARCH-001",
  "status": "RUNNING",
  "createdAt": "2025-08-07T19:55:00Z",
  "logs": [
    {
      "timestamp": 1691436900000,
      "message": "Starting pipeline..."
    },
    {
      "timestamp": 1691436901000,
      "message": "Loading secrets from AWS Secrets Manager..."
    }
  ],
  "logStreamUrl": "https://console.aws.amazon.com/cloudwatch/..."
}
```

## Critical Design Decisions

### Pipeline Script Integrity
- **`run_pipeline.py` is NEVER modified** for deployment
- **`batch_wrapper.py` acts as an adapter** that:
  - Downloads input from S3
  - Calls `run_pipeline.py` unchanged
  - Uploads outputs to S3
  - Updates job status in DynamoDB
- **GitHub creation is NOT skipped** - it's the mandatory final step

### Environment Variables

The Batch container receives these environment variables:

- `S3_INPUT_KEY` - S3 key of the input research file
- `RESEARCH_ID` - Unique identifier for this research
- `JOB_ID` - Batch job ID for status tracking
- `RESEARCH_BUCKET` - S3 bucket for outputs
- `RESEARCH_TABLE` - DynamoDB table for research data
- `JOBS_TABLE` - DynamoDB table for job tracking

### API Keys from Secrets Manager

The following secrets are automatically injected from AWS Secrets Manager:
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `COHERE_API_KEY`
- `GITHUB_TOKEN`
- `PERPLEXITY_KEY`

## Pipeline Outputs

After successful completion, outputs are stored in S3:

```
s3://multi-step-llm-research-{ACCOUNT}/
  └── outputs/
      └── {RESEARCH_ID}/
          ├── analysis_results.md
          ├── jtbds_*.txt
          ├── reddit_discussions_*.csv
          ├── opportunity_zones.json
          ├── product_ideas.json
          ├── final_innovation_portfolio.json
          └── final_innovation_portfolio_summary.md
```

## Monitoring

### Using Makefile Commands

```bash
# View recent Batch job logs
make batch-logs

# Check job status
make batch-status

# Submit a test job
make batch-submit

# Test container locally
make docker-test
```

### CloudWatch Logs
- Log group: `/aws/batch/job/multi-step-llm`
- Log stream: `pipeline/default/{JOB_ID}`

### Batch Console
View job status at: https://console.aws.amazon.com/batch/home?region=us-east-1#jobs

### DynamoDB Console
Track jobs at: https://console.aws.amazon.com/dynamodbv2/home?region=us-east-1#tables

## Cost Estimation

- **Batch (Fargate)**: ~$0.20 per job (2 hours @ 4 vCPU, 16GB)
- **Lambda**: Minimal (< $0.01 per 1000 invocations)
- **API Gateway**: $3.50 per million requests
- **DynamoDB**: On-demand pricing, minimal for this use case
- **S3**: $0.023 per GB stored
- **CloudWatch Logs**: $0.50 per GB ingested

## Troubleshooting

### CORS Issues
- All Lambda functions now include comprehensive CORS headers
- Headers included: `Access-Control-Allow-Origin: *`, `Access-Control-Allow-Methods: GET,POST,OPTIONS`
- If frontend still gets CORS errors, check API Gateway CORS configuration

### Research Not Found Error
- Lambda now looks in `ResearchReports` table (not `PipelineResearch`)
- Ensure the `reportId` exists in ResearchReports table
- Check that `s3ReportKey` field is populated in the table item

### CDK Dependencies Error
```bash
# If you see "No matching distribution found for aws-cdk.aws-batch-alpha"
# The requirements have been fixed to use stable constructs
cd infrastructure
pip install -r requirements-cdk.txt
```

### Job Fails Immediately
- Check ECR image exists and is tagged correctly
- Verify IAM roles have necessary permissions
- Check secrets in Secrets Manager are accessible
- Ensure `batch_wrapper.py` is included in Docker image

### No Logs Appearing
- Ensure CloudWatch Logs permissions are set
- Check log group exists: `/aws/batch/job/multi-step-llm`
- Verify execution role has logs:CreateLogStream permission

### S3 Access Denied
- Verify task role has S3 read/write permissions
- Check bucket policy allows access from Batch

### API Gateway Timeout
- Lambda functions have 30-second timeout
- For long-running operations, use async pattern

## Cleanup

To remove all resources:

```bash
# Complete cleanup
make cdk-destroy

# This will prompt for confirmation, then:
# - Delete all AWS resources
# - Retain S3 bucket (manual deletion required)

# Manual cleanup if needed:
aws s3 rm s3://multi-step-llm-research-984906149037/ --recursive --profile mvp
aws ecr delete-repository --repository-name multi-step-llm-pipeline --force --profile mvp
```

## Security Considerations

1. **Secrets Management**: All API keys stored in AWS Secrets Manager
2. **Network Isolation**: Batch runs in private VPC subnets
3. **IAM Roles**: Least privilege access for all components
4. **Encryption**: S3 bucket encryption, DynamoDB encryption at rest
5. **CORS Configuration**: Currently allows all origins (`*`) - consider restricting to specific domains in production
6. **API Security**: Consider adding API keys or Cognito authentication for production use

## Next Steps

1. **Add Authentication**: Implement API Gateway authorizers
2. **Cost Optimization**: Use Spot instances for Batch compute
3. **Monitoring**: Set up CloudWatch alarms for job failures
4. **Scaling**: Implement job queuing and priority handling
5. **UI**: Build frontend for submitting and monitoring jobs