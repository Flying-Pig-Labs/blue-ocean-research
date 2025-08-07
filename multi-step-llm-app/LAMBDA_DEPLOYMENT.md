# Lambda Deployment Guide - Multi-Step LLM Pipeline

## Overview

This document provides comprehensive guidance for deploying the Multi-Step LLM Pipeline as AWS Lambda functions. The pipeline has been completely refactored to run as serverless functions with proper error handling, monitoring, and scalability.

## Architecture

### Lambda Functions

The pipeline consists of 9 Lambda functions:

1. **API Handler** (`lambda_handler.py`) - Manages API Gateway endpoints
2. **Orchestrator** (`lambda_handler.orchestrator_handler`) - Coordinates pipeline execution
3. **Research Analyzer** (`lambda_research_analyzer.py`) - Stage 1: Research analysis with parallel LLM calls
4. **Jobs Researcher** (`lambda_jobs_researcher.py`) - Stage 2: JTBD research using EXA API
5. **Jobs to Reddit** (`lambda_jobs_to_reddit.py`) - Stage 2.5: JTBD extraction & Reddit discovery
6. **JTBD Clustering** (`lambda_cluster_jtbd.py`) - Stage 3: Pain point clustering with HDBSCAN
7. **Opportunity Zones** (`lambda_opportunity_zones.py`) - Stage 3.5: Advanced opportunity analysis
8. **Value Curves** (`lambda_value_curves.py`) - Stage 4: Value curve mapping with EXA search
9. **Product Ideas** (`lambda_product_ideas.py`) - Stage 5: Idea generation with OpenAI o1
10. **Consolidator** (`lambda_consolidator.py`) - Stage 6: Portfolio consolidation

### Key Optimizations

#### Lambda Constraints Handled
- **15-minute timeout limits** - Long-running stages broken into efficient operations
- **10GB memory limit** - Optimized memory allocation per function (512MB - 3GB)
- **512MB /tmp storage** - S3-based file I/O instead of local storage
- **Event payload size limits** - S3 keys used for data passing instead of direct payload
- **Cold starts** - Shared client initialization and Lambda layers

#### Performance Optimizations
- **Parallel processing** - Research analysis uses ThreadPoolExecutor for 4 concurrent LLM calls
- **Memory efficiency** - Streaming S3 operations and optimized data structures
- **Rate limiting** - Built-in delays and retry logic for API calls
- **Connection reuse** - AWS clients initialized outside handler functions
- **Layer optimization** - Common dependencies in shared layer, reduced package sizes

## Deployment

### Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **SAM CLI installed** (https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
3. **Python 3.11+** with pip
4. **Secrets Manager** setup with API keys

### Secrets Management

Create secrets in AWS Secrets Manager:

```bash
aws secretsmanager create-secret \
  --name "pipeline-secrets" \
  --description "API keys for multi-step LLM pipeline" \
  --secret-string '{
    "ANTHROPIC_API_KEY": "your_anthropic_key",
    "OPENAI_API_KEY": "your_openai_key", 
    "EXA_API_KEY": "your_exa_key",
    "COHERE_API_KEY": "your_cohere_key",
    "REDDIT_CLIENT_ID": "your_reddit_client_id",
    "REDDIT_CLIENT_SECRET": "your_reddit_client_secret"
  }'
```

### Deploy Command

```bash
# Quick deployment
./deploy-lambda.sh

# Or manual deployment
sam build --template lambda-template.yaml
sam deploy --guided
```

### Environment Variables

Set these before deployment:

```bash
export AWS_REGION="us-east-1"
export AWS_PROFILE="your-profile"
export ENVIRONMENT="production"  # or staging/development
export SECRETS_ARN="arn:aws:secretsmanager:us-east-1:*:secret:pipeline-secrets*"
```

## API Usage

### Base URL
After deployment, get the API endpoint:
```bash
aws cloudformation describe-stacks --stack-name multi-step-llm-pipeline \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text
```

### Endpoints

#### Start Pipeline
```bash
POST /start-pipeline

{
  "input_data": {
    "title": "Research Title",
    "content": "Research content here...",
    "source": "Optional source info"
  },
  "max_jtbds": 20,      // Optional: max JTBDs to extract (default: 20)
  "max_clusters": 8,     // Optional: max clusters to create (default: 8) 
  "target_ideas": 12,    // Optional: initial ideas to generate (default: 12)
  "final_ideas": 8       // Optional: final filtered ideas (default: 8)
}

Response:
{
  "job_id": "job-1704067200-abc123de",
  "status": "INITIATED",
  "message": "Pipeline started successfully",
  "status_url": "/status/job-1704067200-abc123de"
}
```

#### Get Job Status
```bash
GET /status/{jobId}

Response:
{
  "job_id": "job-1704067200-abc123de",
  "status": "RUNNING",           // INITIATED, RUNNING, COMPLETED, FAILED
  "current_stage": "value_curves",
  "progress_percentage": 75,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:15:00",
  "stages_completed": ["research_analysis", "jobs_research", ...],
  "total_stages": 8,
  "results_location": "s3://bucket/jobs/job-id/final/"  // If completed
}
```

#### Get Job Logs
```bash
GET /logs/{jobId}

Response:
{
  "job_id": "job-1704067200-abc123de",
  "logs": [
    {
      "timestamp": "2024-01-01T00:00:00",
      "level": "INFO",
      "message": "Pipeline job initiated",
      "stage": "orchestrator"
    },
    ...
  ],
  "total_logs": 25
}
```

## Pipeline Stages

### Stage Execution Flow

1. **Research Analysis** (3-5 min)
   - Input: Research JSON from S3
   - Processing: 4 parallel Anthropic API calls
   - Output: `analysis/results.md`

2. **Jobs Research** (5-10 min)
   - Input: Analysis results
   - Processing: EXA search + Claude synthesis
   - Output: `jtbd/research.md`, `jtbd/pain_points.txt`

3. **Jobs to Reddit** (10-15 min)
   - Input: Analysis results  
   - Processing: Claude JTBD extraction + Reddit API search
   - Output: `jtbd/extracted.txt`, `reddit/discussions.csv`

4. **JTBD Clustering** (5-8 min)
   - Input: Pain points text
   - Processing: Cohere embeddings + HDBSCAN clustering + GPT-4o analysis
   - Output: `clusters/opportunity_zones.json`

5. **Opportunity Zones** (10-15 min)
   - Input: JTBDs + Reddit data
   - Processing: Pain dimension analysis with Claude
   - Output: `zones/advanced_analysis.json`

6. **Value Curves** (8-12 min)
   - Input: Opportunity zones
   - Processing: EXA competitive search + Claude analysis
   - Output: `value_curves/analysis.json`, `value_curves/report.md`

7. **Product Ideas** (5-10 min)
   - Input: Value curves
   - Processing: OpenAI o1 generation + Claude enrichment
   - Output: `products/ideas.json`, `products/report.md`

8. **Consolidation** (2-3 min)
   - Input: Product ideas
   - Processing: Portfolio analysis and roadmap creation
   - Output: `final/portfolio.json`, `final/summary.md`

**Total Pipeline Time: 48-86 minutes**

### Memory Allocation by Stage

| Function | Memory | Timeout | Concurrency | Purpose |
|----------|--------|---------|-------------|---------|
| API Handler | 512MB | 30s | Default | API endpoints |
| Orchestrator | 1GB | 15min | 10 | Pipeline coordination |
| Research Analyzer | 1GB | 5min | Default | Parallel LLM calls |
| Jobs Researcher | 2GB | 15min | Default | EXA search + synthesis |
| Jobs to Reddit | 1GB | 15min | Default | JTBD extraction + Reddit |
| JTBD Clustering | 3GB | 15min | Default | ML clustering operations |
| Opportunity Zones | 2GB | 15min | Default | Advanced analysis |
| Value Curves | 2GB | 15min | Default | Competitive analysis |
| Product Ideas | 3GB | 15min | 5 | o1 model processing |
| Consolidator | 1GB | 5min | Default | Portfolio analysis |

## Monitoring & Troubleshooting

### CloudWatch Logs

Each function has dedicated log groups with 14-day retention:
- `/aws/lambda/multi-step-llm-api-handler-production`
- `/aws/lambda/multi-step-llm-orchestrator-production`
- `/aws/lambda/multi-step-llm-research-analyzer-production`
- ... (one for each stage)

### Common Issues

#### 1. API Rate Limits
- **Anthropic**: 50 RPM limit with OpenAI fallback
- **OpenAI**: 60 RPM limit with retry logic
- **EXA**: 100 RPM limit with delays
- **Reddit**: Rate limiting with 0.3s delays

#### 2. Memory Issues
- **JTBD Clustering**: May need full 3GB for large datasets
- **Product Ideas**: o1 model requires significant memory
- Monitor CloudWatch metrics for memory usage

#### 3. Timeout Issues
- **Long stages**: Value curves and opportunity zones may timeout on large datasets
- **Retry logic**: Built-in exponential backoff for API calls
- **Monitoring**: Check execution time metrics in CloudWatch

#### 4. S3 Access
- Ensure S3 bucket policies allow Lambda access
- Check IAM permissions for S3 operations
- Monitor S3 request metrics

### Debugging

#### Check Job Status
```bash
aws dynamodb get-item \
  --table-name PipelineJobs-production \
  --key '{"jobId":{"S":"your-job-id"}}' \
  --output table
```

#### View S3 Contents
```bash
aws s3 ls s3://your-bucket/jobs/your-job-id/ --recursive
```

#### Lambda Function Logs
```bash
aws logs tail /aws/lambda/multi-step-llm-orchestrator-production --since 1h
```

## Cost Optimization

### Lambda Costs
- **API Handler**: ~$0.01 per 1000 requests
- **Pipeline Execution**: ~$5-15 per complete run (depending on data size)
- **Storage**: S3 costs for intermediate files (~$0.01-0.10 per run)

### Optimization Strategies
1. **Right-size memory** - Monitor actual usage and adjust
2. **Layer optimization** - Remove unused dependencies
3. **Concurrent executions** - Limit expensive functions
4. **S3 lifecycle** - Auto-delete old job data after 30 days
5. **DynamoDB** - Pay-per-request pricing with TTL cleanup

## Security

### IAM Permissions
Functions use least-privilege access:
- S3: Read/write to pipeline bucket only
- DynamoDB: CRUD on jobs table only  
- Secrets Manager: Read pipeline secrets only
- Lambda: Invoke specific stage functions only

### Data Protection
- **Encryption at rest**: S3 and DynamoDB with AES-256
- **Encryption in transit**: HTTPS/TLS for all API calls
- **Secrets**: AWS Secrets Manager with rotation
- **VPC**: Optional VPC deployment for network isolation

### API Security
- **CORS**: Configured for cross-origin requests
- **Rate limiting**: API Gateway throttling
- **Authentication**: Can add API keys or JWT validation
- **Input validation**: Request payload validation

## Scaling Considerations

### Horizontal Scaling
- **Concurrent executions**: Each stage can run multiple instances
- **Reserved concurrency**: Limited for expensive functions (Product Ideas: 5)
- **Queue processing**: Could add SQS for batch processing

### Vertical Scaling  
- **Memory**: Can increase up to 10GB for ML operations
- **CPU**: Scales with memory allocation
- **Timeout**: Max 15 minutes per function

### Data Volume Scaling
- **Streaming**: Large files processed via S3 streaming
- **Batch processing**: Could split large datasets across multiple invocations
- **Caching**: Results cached in S3 for reuse

## Future Enhancements

### Potential Improvements
1. **Step Functions**: Replace orchestrator with AWS Step Functions
2. **SQS Integration**: Queue-based processing for better reliability
3. **Container Images**: Use container Lambda for complex ML dependencies
4. **EventBridge**: Event-driven architecture for stage coordination
5. **API Gateway v2**: HTTP APIs for lower latency and cost
6. **GraphQL**: More flexible API querying
7. **WebSocket**: Real-time progress updates

### Monitoring Enhancements
1. **X-Ray Tracing**: Distributed tracing across stages
2. **Custom Metrics**: Business-specific CloudWatch metrics
3. **Alarms**: Automated alerts for failures
4. **Dashboard**: CloudWatch dashboard for pipeline monitoring

## Development Workflow

### Local Testing
Each Lambda handler includes local testing capability:
```bash
python lambda_research_analyzer.py  # Runs test event
```

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Deploy Lambda Pipeline
  run: |
    pip install aws-sam-cli
    ./deploy-lambda.sh
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

### Testing Strategy
1. **Unit Tests**: Mock AWS services with moto
2. **Integration Tests**: End-to-end pipeline testing
3. **Load Tests**: Concurrent execution testing
4. **Error Testing**: Failure scenario validation

---

## Quick Start

1. **Deploy**: `./deploy-lambda.sh`
2. **Test**: Use the provided API examples
3. **Monitor**: Check CloudWatch logs and metrics
4. **Scale**: Adjust memory/timeout based on usage patterns

For additional support, check the CloudWatch logs and DynamoDB job records for detailed execution information.