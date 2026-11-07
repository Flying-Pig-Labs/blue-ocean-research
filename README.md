# Multi-Step LLM Pipeline (Blue Ocean Research)

**Version 1.0** - Production-Ready Innovation Pipeline

A sophisticated 6-stage AI-powered innovation pipeline that transforms raw market research into actionable product ideas with automatic GitHub repository creation. Runs locally via Makefile or remotely via AWS Batch with full frontend integration.

---

## Table of Contents

1. [Overview](#overview)
2. [Pipeline Architecture](#pipeline-architecture)
3. [Local Execution (Happy Path)](#local-execution-happy-path)
4. [AWS Batch Remote Execution](#aws-batch-remote-execution)
5. [Pipeline Stages](#pipeline-stages)
6. [Key Files](#key-files)
7. [Development Workflow](#development-workflow)
8. [Troubleshooting](#troubleshooting)

---

## Overview

This pipeline orchestrates multiple AI models (Claude Sonnet/Opus, GPT-4o, OpenAI o1) to generate exactly **10 high-quality product innovations** distributed across market opportunity zones based on authentic Reddit user discussions.

### Key Features

- **PRAW-Based Reddit Integration**: Authentic user discussions (no Exa API dependency)
- **Weighted Distribution**: Ideas allocated proportionally to market opportunity scores
- **Multi-AI Orchestration**: Claude for analysis, o1 for strategy, GPT for generation
- **GitHub Automation**: Automatic repository creation with pitch-deck quality documentation
- **Dual Execution Modes**: Local development OR AWS Batch production deployment
- **Frontend Integration**: Seamless Color Code Research Hub compatibility

### Technology Stack

- **Python 3.11**: Core runtime
- **AI Models**: Claude Sonnet/Opus, OpenAI GPT-4o/o1, Cohere embeddings
- **Reddit**: PRAW (Python Reddit API Wrapper)
- **Local Execution**: Makefile + virtualenv
- **Remote Execution**: AWS Batch (Fargate), Docker, CDK
- **Storage**: S3, DynamoDB
- **API**: API Gateway + Lambda

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     LOCAL EXECUTION FLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  make run-fresh                                                  │
│       ↓                                                          │
│  [run_pipeline.py] ← THE ONE SCRIPT                              │
│       ↓                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ Stage 1  │→ │ Stage 2  │→ │ Stage 3  │→ │ Stage 4  │         │
│  │ Research │  │ JTBD +   │  │ Opp Zone │  │ Product  │         │
│  │ Analysis │  │ Reddit   │  │ Discovery│  │ Ideas    │         │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘         │
│                                                                  │
│       ↓                                                          │
│  ┌──────────┐  ┌──────────┐                                      │
│  │ Stage 5  │→ │ Stage 6  │                                      │
│  │ Idea     │  │ GitHub   │                                      │
│  │ Consol.  │  │ Repo     │                                      │
│  └──────────┘  └──────────┘                                      │
│                                                                  │
│  Output: Local files + GitHub repository                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   AWS BATCH REMOTE EXECUTION                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  API Gateway /submit (from frontend)                             │
│       ↓                                                          │
│  [Lambda: submit_job]                                            │
│   - Validates research exists in S3                              │
│   - Submits Batch job                                            │
│   - Writes to DynamoDB                                           │
│       ↓                                                          │
│  AWS Batch Job Queue                                             │
│       ↓                                                          │
│  [Fargate Container: 4 vCPU, 16GB RAM]                           │
│       ↓                                                          │
│  [batch_wrapper.py]                                              │
│   - Downloads research from S3                                   │
│   - Calls run_pipeline.py (unmodified)                           │
│   - Uploads outputs to S3                                        │
│   - Updates DynamoDB job status                                  │
│       ↓                                                          │
│  [run_pipeline.py] ← THE SAME SCRIPT                             │
│   (6-stage execution identical to local)                         │
│       ↓                                                          │
│  Output: S3 artifacts + GitHub repository + DynamoDB records     │
│                                                                  │
│  [Lambda: monitor_logs] ← Frontend polls for status              │
│   - Reads DynamoDB                                               │
│   - Returns CloudWatch logs                                      │
│   - Shows progress percentage                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Local Execution (Happy Path)

### Prerequisites

1. **Python 3.11+** installed
2. **AWS CLI** configured with profile `mvp`
3. **API Keys** in AWS Secrets Manager (loaded automatically)
4. **Make** utility (comes with macOS/Linux)

### Quick Start

```bash
# 1. Install dependencies
make install

# 2. Run pipeline with fresh data (recommended)
make run-fresh

# 3. Or run with cached files (faster testing)
make run

# 4. Run with verbose output (see all LLM prompts)
make run-verbose
```

### What Happens Locally

1. **`make run-fresh`** executes:
   ```bash
   python run_pipeline.py --input tests/fixtures/sample_research.json
   ```

2. **run_pipeline.py** orchestrates all stages:
   - Loads API keys from AWS Secrets Manager
   - Executes 6 stages sequentially
   - Creates local output files
   - Optionally creates GitHub repository

3. **Output files created**:
   ```
   analysis_results.md                    # Stage 1: Research insights
   jtbds_YYYYMMDD_HHMMSS.txt             # Stage 2: Jobs-to-be-Done
   reddit_discussions_YYYYMMDD_HHMMSS.csv # Stage 2: Reddit data
   opportunity_zones.json                 # Stage 3: Market opportunities
   product_ideas.json                     # Stage 4: 10 innovative ideas
   final_innovation_portfolio.json        # Stage 5: Enriched portfolio
   github_results.json                    # Stage 6: GitHub repo details
   ```

4. **GitHub repository** created in `ocean-studio-repos` organization:
   - Comprehensive README (GPT-5 generated)
   - 10 issues (one per product idea, GPT-5 enhanced)
   - Smart labels and milestones

### Local Execution Flags

```bash
# Headless mode (default - no user interaction)
make run-fresh

# Interactive mode (prompts between stages)
python run_pipeline.py --interactive

# Verbose mode (show all LLM prompts and responses)
python run_pipeline.py --verbose

# Custom input file
python run_pipeline.py --input path/to/research.json

# Use cached files (skip GitHub creation)
python run_pipeline.py --use-cache

# Skip GitHub repository creation
python run_pipeline.py --skip-github
```

### Local Testing Workflow

```bash
# Run individual stages
make stage1  # Research Analyzer
make stage2  # JTBD + Reddit (PRAW)
make stage3  # Opportunity Zone Discovery
make stage4  # Product Idea Generator
make stage5  # Idea Consolidator
make stage6  # GitHub Integration

# Clean up generated files
make clean

# Full clean (removes venv too)
make clean-all

# Check AWS credentials
make check-env

# Test AWS Secrets Manager access
make test-secrets
```

---

## AWS Batch Remote Execution

### Architecture Components

**run_pipeline.py is NEVER modified for AWS Batch deployment.** All cloud-specific logic lives in batch_wrapper.py.

### Deployment Flow

```bash
# 1. Build and push Docker image
make docker
# - Builds Dockerfile
# - Pushes to ECR: multi-step-llm-pipeline

# 2. Deploy CDK infrastructure
make cdk-deploy
# - Creates VPC, Batch compute environment, job queue
# - Sets up API Gateway + Lambda functions
# - Configures DynamoDB tables
# - Attaches IAM policies
```

### How AWS Batch Execution Works

#### 1. Job Submission (Frontend → Backend)

```
Frontend (Color Code Research Hub)
    ↓
POST /submit
    {
      "researchId": "abc123",
      "team": "blue",
      "username": "fprior"
    }
    ↓
Lambda: pipeline-submit-job
    - Verifies research exists: s3://color-code-research-results-{account}/users/{username}/research/{team}/{researchId}/report.md
    - Submits AWS Batch job
    - Writes to PipelineBatchJobs table
    ↓
Returns: { "jobId": "xyz789", "status": "SUBMITTED" }
```

#### 2. Batch Job Execution

```
AWS Batch Job Queue
    ↓
Fargate Container Starts
    - Image: {account}.dkr.ecr.us-east-1.amazonaws.com/multi-step-llm-pipeline:latest
    - vCPUs: 4
    - Memory: 16GB RAM
    - Storage: 50GB ephemeral
    - Timeout: 2 hours
    ↓
batch_wrapper.py (entrypoint)
    1. Downloads research from S3
    2. Sets environment variables (RESEARCH_ID, JOB_ID, etc.)
    3. Calls: python run_pipeline.py --input /tmp/research_input.md
    4. Monitors execution
    5. Uploads outputs to S3: outputs/{researchId}/
    6. Updates DynamoDB: PipelineBatchJobs
    7. Saves GitHub results: github_results.json
    ↓
run_pipeline.py executes (IDENTICAL to local execution)
    - Stage 1-6 run sequentially
    - Uses AWS Secrets Manager for API keys
    - Creates GitHub repository
    - Returns success/failure
    ↓
batch_wrapper.py finalizes
    - Status: SUCCEEDED or FAILED
    - S3 outputs uploaded
    - DynamoDB updated with GitHub URL
```

#### 3. Status Monitoring (Frontend Polling)

```
Frontend polls every 2 seconds
    ↓
GET /api/plan/async/status/{jobId}
    ↓
Lambda: pipeline_status_lambda
    - Reads PipelineBatchJobs table
    - Gets current Batch job status
    - Fetches CloudWatch logs
    ↓
Returns:
    {
      "status": "RUNNING",
      "currentStage": "Stage 3: Opportunity Zone Discovery",
      "progress_percentage": 45,
      "logs": [...],
      "githubRepoUrl": "https://github.com/ocean-studio-repos/..."
    }
```

### AWS Resources Created

| Resource | Purpose | Cost (Estimated) |
|----------|---------|------------------|
| **VPC + NAT Gateway** | Private networking | ~$45/month (idle) |
| **AWS Batch (Fargate)** | Container execution | ~$0.20/hour per job |
| **ECR Repository** | Docker image storage | ~$0.10/GB/month |
| **DynamoDB Tables** | Job tracking | Pay-per-request |
| **S3 Buckets** | Input/output storage | ~$0.023/GB/month |
| **API Gateway** | REST API | Pay-per-request |
| **Lambda Functions** | API handlers | Pay-per-invocation |
| **CloudWatch Logs** | Execution logs | ~$0.50/GB ingested |

**Per-Run Cost**: ~$2-5 (Fargate + API calls)

### DynamoDB Tables

#### PipelineResearch
```
Partition Key: researchId
Attributes:
  - s3Key: Location of research document
  - username: Owner
  - team: red|black|white|blue
  - createdAt: ISO timestamp
  - ttl: 30-day expiration
```

#### PipelineBatchJobs
```
Partition Key: jobId
GSI: ResearchIdIndex (partition: researchId)
Attributes:
  - jobId: AWS Batch job ID
  - researchId: Reference to research
  - status: SUBMITTED|RUNNING|SUCCEEDED|FAILED
  - currentStage: Human-readable stage name
  - progress_percentage: 0-100
  - githubRepoUrl: Created repository
  - githubRepoName: Repository name
  - issues_created: Count of issues
  - createdAt: Job start time
  - ttl: 30-day expiration
```

#### PipelineRepos
```
Composite Key: repoName (partition) + itemType (sort)
Attributes:
  - repoName: GitHub repository name
  - itemType: "metadata" or "issue_{number}"
  - For metadata: repoUrl, description, createdAt
  - For issues: title, body, labels, state
```

### Infrastructure Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS Account                               │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Frontend: Color Code Research Hub                          │ │
│  │ (React app, deployed separately)                           │ │
│  └───────────┬────────────────────────────────────────────────┘ │
│              │                                                   │
│              │ HTTPS                                             │
│              ↓                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ API Gateway: multi-step-llm-pipeline-api                   │ │
│  │                                                             │ │
│  │  POST /submit                                               │ │
│  │  GET  /api/plan/async/status/{jobId}                        │ │
│  │  GET  /api/status/running                                   │ │
│  │  GET  /api/repos/{repoName}                                 │ │
│  └───────┬────────────────────────┬───────────────────────────┘ │
│          │                        │                             │
│          ↓                        ↓                             │
│  ┌───────────────┐      ┌───────────────────┐                   │
│  │ Lambda:       │      │ Lambda:           │                   │
│  │ submit_job    │      │ pipeline_status   │                   │
│  └───────┬───────┘      └─────────┬─────────┘                   │
│          │                        │                             │
│          ↓                        ↓                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ DynamoDB Tables                                           │   │
│  │  - PipelineResearch (research metadata)                   │   │
│  │  - PipelineBatchJobs (job tracking)                       │   │
│  │  - PipelineRepos (GitHub records)                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ AWS Batch                                                 │   │
│  │  ┌────────────────────────────────────────────────────┐   │   │
│  │  │ Compute Environment: multi-step-llm-compute        │   │   │
│  │  │  Type: FARGATE                                      │   │   │
│  │  │  Max vCPUs: 256                                     │   │   │
│  │  │  Subnets: VPC private subnets                       │   │   │
│  │  └────────────────────────────────────────────────────┘   │   │
│  │  ┌────────────────────────────────────────────────────┐   │   │
│  │  │ Job Queue: multi-step-llm-queue                    │   │   │
│  │  └────────────────────────────────────────────────────┘   │   │
│  │  ┌────────────────────────────────────────────────────┐   │   │
│  │  │ Job Definition: multi-step-llm-pipeline            │   │   │
│  │  │  Platform: Fargate                                  │   │   │
│  │  │  vCPU: 4                                            │   │   │
│  │  │  Memory: 16384 MB                                   │   │   │
│  │  │  Image: ECR multi-step-llm-pipeline:latest          │   │   │
│  │  │  Entrypoint: batch_wrapper.py                       │   │   │
│  │  └────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ S3 Buckets                                                │   │
│  │  - color-code-research-results-{account} (input)          │   │
│  │  - multi-step-llm-research-{account} (output)             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Secrets Manager                                           │   │
│  │  - anthropic_key                                          │   │
│  │  - openai_key                                             │   │
│  │  - cohere-key                                             │   │
│  │  - github_token_blue_ocean                                │   │
│  │  - perplexity-key (optional)                              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ CloudWatch Logs                                           │   │
│  │  - /aws/batch/job/multi-step-llm                          │   │
│  │    (30-day retention)                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ECR Repository                                            │   │
│  │  - multi-step-llm-pipeline                                │   │
│  │    (Docker image with all dependencies)                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Batch Execution Timeline

```
T+0s:    Frontend calls POST /submit
T+1s:    Lambda validates and submits Batch job
T+2s:    Batch job queued (status: SUBMITTED)
T+5s:    Fargate container starts pulling image
T+30s:   Container running, batch_wrapper.py starts
T+35s:   Research downloaded from S3
T+40s:   run_pipeline.py Stage 1 begins
T+2m:    Stage 1 complete (analysis_results.md)
T+5m:    Stage 2 complete (JTBDs + Reddit data)
T+8m:    Stage 3 complete (opportunity zones)
T+12m:   Stage 4 complete (10 product ideas)
T+13m:   Stage 5 complete (portfolio consolidation)
T+15m:   Stage 6 complete (GitHub repository created)
T+15m30s: Outputs uploaded to S3
T+16m:   DynamoDB updated with SUCCEEDED status
T+16m:   Container terminates
```

### Deployment Commands

```bash
# Full deployment workflow
make deploy
# Equivalent to: make docker && make cdk-deploy

# Individual steps
make docker-build       # Build Docker image
make docker-login       # Login to ECR
make docker-push        # Push to ECR registry
make ecr-create         # Create ECR repository (if needed)
make cdk-install        # Install CDK dependencies
make cdk-bootstrap      # Bootstrap CDK (first time only)
make cdk-diff           # Preview infrastructure changes
make cdk-deploy         # Deploy CDK stack
make cdk-destroy        # Destroy all resources

# Monitoring
make batch-logs         # View CloudWatch logs
make batch-status       # Check recent jobs
make docker-info        # Show Docker image info
```

### Testing AWS Batch Locally

```bash
# Test container locally before deploying
make docker-test
# Runs: docker run with all environment variables
```

---

## Pipeline Stages

### Stage 1: Research Analysis
**Module**: `research_analyzer.py`
**AI**: Claude Sonnet
**Input**: Raw market research (JSON or Markdown)
**Output**: `analysis_results.md`

Extracts structured insights:
- Pain points and problems
- User personas and segments
- Existing solutions and gaps
- Market verticals and trends

### Stage 2: JTBD Extraction & Reddit Discovery
**Module**: `jobs_to_reddit.py`
**AI**: Claude Sonnet + PRAW API
**Input**: `analysis_results.md`
**Output**: `jtbds_*.txt`, `reddit_discussions_*.csv`

1. Claude extracts Jobs-to-be-Done from research
2. PRAW searches Reddit for authentic user discussions
3. Creates searchable CSV with post metadata

**Key Point**: Uses native Reddit API (PRAW), not Exa. Removed Perplexity enrichment for performance.

### Stage 3: Opportunity Zone Discovery
**Module**: `opportunity_zone_analyzer.py`
**AI**: Claude Opus + Cohere embeddings
**Input**: JTBDs + Reddit discussions
**Output**: `opportunity_zones.json`

1. Clusters JTBDs using semantic similarity
2. Scores each zone across 8 pain dimensions
3. Assigns market opportunity percentages
4. Calculates idea allocation (sum = 10 ideas)

**Output Structure**:
```json
{
  "zones": [
    {
      "name": "Zone 1: Enterprise Data Integration",
      "market_opportunity_percentage": 35,
      "ideas_to_generate": 4,
      "pain_scores": {...},
      "representative_jtbds": [...]
    }
  ]
}
```

### Stage 4: Product Idea Generation
**Module**: `product_idea_generator.py`
**AI**: OpenAI o1 (strategy) + Claude Opus (ideas)
**Input**: `opportunity_zones.json`
**Output**: `product_ideas.json`, `product_ideas_report.md`

1. For each zone: o1 generates ERRC strategy
2. Claude Opus generates 10 ideas per zone
3. Selects top N ideas based on zone weight
4. Total output: exactly 10 ideas

**Innovation Framework**: Blue Ocean Strategy (Eliminate-Reduce-Raise-Create)

### Stage 5: Idea Consolidation
**Module**: `idea_consolidator.py`
**AI**: Claude Sonnet
**Input**: `product_ideas.json`
**Output**: `final_innovation_portfolio.json`, `final_innovation_portfolio_summary.md`

Enriches portfolio with:
- Cross-idea synthesis
- Market positioning
- Implementation roadmap
- Portfolio narrative

### Stage 6: GitHub Repository Creation
**Module**: `product_idea_generator.py --github`
**AI**: GPT-5
**Input**: All previous outputs
**Output**: GitHub repository in `ocean-studio-repos` org

1. GPT-5 generates comprehensive README (1 call)
2. GPT-5 creates pitch-deck quality issue for each idea (10 calls)
3. Applies smart labels and milestones
4. Saves results to `github_results.json`

**Cost**: ~$0.50-$1.00 in GPT-5 API fees

---

## Key Files

### Core Pipeline Scripts
- **`run_pipeline.py`**: THE ONE SCRIPT - orchestrates all 6 stages (local and remote)
- **`batch_wrapper.py`**: AWS Batch entrypoint, wraps run_pipeline.py for cloud execution
- **`research_analyzer.py`**: Stage 1 implementation
- **`jobs_to_reddit.py`**: Stage 2 implementation
- **`opportunity_zone_analyzer.py`**: Stage 3 implementation
- **`product_idea_generator.py`**: Stage 4 & 6 implementation
- **`idea_consolidator.py`** (archived): Stage 5 implementation (not currently used)

### Infrastructure
- **`Dockerfile`**: Container definition for AWS Batch
- **`infrastructure/cdk_batch_pipeline.py`**: CDK stack (VPC, Batch, API Gateway, Lambda, DynamoDB)
- **`infrastructure/app.py`**: CDK app entrypoint
- **`infrastructure/lambda_pipeline_status.py`**: Status API Lambda
- **`infrastructure/lambda_repo_records.py`**: GitHub records API Lambda

### Configuration
- **`Makefile`**: All build, test, deploy commands
- **`requirements.txt`**: Python dependencies
- **`llm_config.yaml`**: AI model configurations
- **`scoring_config.yaml`**: Opportunity zone scoring weights
- **`debug_config.yaml`**: Debug settings

### Testing
- **`tests/fixtures/sample_research.json`**: Sample input for testing

### Documentation
- **`README.md`**: This file
- **`infrastructure/CDK_README.md`**: CDK-specific documentation
- **`infrastructure/API_ROUTES_DOCUMENTATION.md`**: API endpoint reference
- **`docs/archive/`**: Deprecated files (modular system, test files, etc.)

---

## Development Workflow

### Making Changes to Pipeline Logic

1. **Modify run_pipeline.py or stage modules**
2. **Test locally**:
   ```bash
   make clean
   make run-fresh
   ```
3. **Rebuild Docker image**:
   ```bash
   make docker
   ```
4. **Deploy to AWS Batch**:
   ```bash
   make cdk-deploy
   ```

### Adding a New Pipeline Stage

1. Create new module (e.g., `stage7_module.py`)
2. Add to `run_module()` function in `run_pipeline.py`
3. Add to stage sequence in `main()` function
4. Test locally with `make run-fresh`
5. Redeploy: `make docker && make cdk-deploy`

### Modifying API Endpoints

1. Edit Lambda function code in `infrastructure/cdk_batch_pipeline.py`
2. Or edit external Lambda files: `lambda_*.py`
3. Deploy changes: `make cdk-deploy`
4. Test with curl or frontend

### Debugging AWS Batch Jobs

```bash
# View recent logs
make batch-logs

# Check job status
make batch-status

# Get detailed job info
aws batch describe-jobs --jobs <job-id> --profile mvp

# View specific log stream
aws logs tail /aws/batch/job/multi-step-llm \
  --follow \
  --filter-pattern "ERROR" \
  --profile mvp
```

---

## Troubleshooting

### Local Execution Issues

**Problem**: `ImportError: No module named 'anthropic'`
**Solution**:
```bash
make clean-all
make install
make run-fresh
```

**Problem**: AWS Secrets Manager access denied
**Solution**:
```bash
# Verify AWS credentials
aws sts get-caller-identity --profile mvp

# Test secrets access
make test-secrets

# Check IAM permissions for secretsmanager:GetSecretValue
```

**Problem**: Reddit API rate limiting
**Solution**: PRAW respects Reddit's rate limits. Wait 60 seconds or reduce search scope.

### AWS Batch Issues

**Problem**: Batch job stuck in RUNNABLE state
**Causes**:
- Insufficient compute capacity
- Docker image pull failure
- VPC/subnet misconfiguration

**Solution**:
```bash
# Check compute environment
aws batch describe-compute-environments \
  --compute-environments multi-step-llm-compute \
  --profile mvp

# Check job queue
aws batch describe-job-queues \
  --job-queues multi-step-llm-queue \
  --profile mvp
```

**Problem**: Container fails immediately (FAILED status)
**Solution**:
```bash
# Check CloudWatch logs for startup errors
make batch-logs

# Common causes:
# - Missing environment variables
# - Invalid Secrets Manager ARNs
# - IAM permission issues
# - Docker image not found in ECR
```

**Problem**: Job runs but produces no output
**Solution**:
1. Check S3 permissions in task_role (CDK stack)
2. Verify DynamoDB write permissions
3. Check CloudWatch logs for Python errors
4. Test locally with same input: `make docker-test`

### API Gateway Issues

**Problem**: CORS errors in frontend
**Solution**: CORS is configured in CDK stack. Verify headers in Lambda responses:
```python
{
    'statusCode': 200,
    'headers': {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
    },
    'body': json.dumps(...)
}
```

**Problem**: 502 Bad Gateway
**Causes**:
- Lambda timeout (increase in CDK)
- Lambda crash (check CloudWatch)
- Invalid Lambda response format

### GitHub Integration Issues

**Problem**: GitHub API rate limit exceeded
**Solution**: Wait 1 hour or use different GitHub token with higher limits.

**Problem**: Repository creation fails
**Causes**:
- Invalid GITHUB_TOKEN in Secrets Manager
- Token lacks repo creation permission
- ocean-studio-repos org full (100 repo limit for free tier)

**Solution**:
```bash
# Test GitHub token locally
export GITHUB_TOKEN=$(aws secretsmanager get-secret-value \
  --secret-id github_token_blue_ocean-uv7Z1l \
  --profile mvp \
  --query SecretString \
  --output text | jq -r '.github_token')

gh auth status

# Create test repo
gh repo create test-pipeline-$(date +%s) --public
```

---

## Cost Optimization

### Reducing AWS Costs

1. **Use spot instances** (not yet implemented):
   ```python
   # In CDK: cdk_batch_pipeline.py
   compute_resources={
       "type": "FARGATE_SPOT"  # 70% cost savings
   }
   ```

2. **Reduce NAT Gateway costs**:
   - Use VPC endpoints for S3/DynamoDB (saves NAT data transfer)
   - Or remove NAT and use public subnets (less secure)

3. **Optimize Docker image size**:
   ```bash
   # Current: ~2GB
   # Optimize: Use alpine base, remove unused dependencies
   ```

4. **Enable DynamoDB on-demand** (already configured):
   ```python
   billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
   ```

5. **Set CloudWatch log retention**:
   ```python
   retention=logs.RetentionDays.ONE_MONTH  # Reduces storage costs
   ```

---

## FAQ

**Q: Why is run_pipeline.py called "THE ONE SCRIPT"?**
A: It's the single entry point for the entire pipeline. batch_wrapper.py never modifies it - just calls it with arguments. This ensures local and remote execution are identical.

**Q: What happened to Perplexity AI enrichment?**
A: Commented out in Stage 3 due to 5+ minute timeouts per call. Pipeline works fine without it.

**Q: What happened to Exa API integration?**
A: Removed entirely. Replaced with native Reddit PRAW API for more reliable, authentic discussions.

**Q: Why exactly 10 product ideas?**
A: Business requirement. Zones get ideas proportionally (e.g., 35% opportunity = 3-4 ideas).

**Q: Can I run this without AWS?**
A: Yes! Use `make run-fresh` for fully local execution. Only AWS Secrets Manager is required for API keys (or set env vars manually).

**Q: How long does a full pipeline run take?**
A: Local: 10-15 minutes. AWS Batch: 15-20 minutes (includes container startup).

**Q: What's the difference between `run_pipeline.py` and `run_pipeline_modular.py`?**
A: `run_pipeline_modular.py` was an experimental multi-flavor system. It's deprecated and moved to `docs/archive/`.

**Q: How do I add a new AI model?**
A: Update `llm_config.yaml`, add API key to Secrets Manager, modify relevant stage module.

---

## Support & Contact

- **Repository Issues**: Create issue in this repo
- **Deployment Help**: Check `infrastructure/CDK_README.md`
- **API Documentation**: See `infrastructure/API_ROUTES_DOCUMENTATION.md`

---

## License

Proprietary - All Rights Reserved
