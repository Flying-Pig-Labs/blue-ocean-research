# PipelineBatchJobs DynamoDB Table Documentation

## Table Overview
The `PipelineBatchJobs` table tracks all Innovation Pipeline batch jobs, mapping AWS Batch job IDs to research IDs and storing pipeline execution details including GitHub repository creation results.

## Table Schema

| Field | Type | Example | Description | When Populated/Updated |
|-------|------|---------|-------------|------------------------|
| **jobId** | String (PK) | `"825510a4-9779-4392-9db0-d223ea16de46"` | AWS Batch job ID (UUID) | Created when job starts (batch_wrapper.py) |
| **researchId** | String (GSI) | `"47069bf6-aeda-4c9b-b979-4f4b8daa3a09"` | Research document ID from Color Code system | Set at job creation, never changes |
| **status** | String | `"RUNNING"` | Job status: SUBMITTED, PENDING, RUNNING, SUCCEEDED, FAILED | Updated throughout pipeline execution |
| **startTime** | String (ISO) | `"2025-08-08T20:23:57.233820Z"` | When the job started | Set at job creation |
| **endTime** | String (ISO) | `"2025-08-08T20:45:12.456789Z"` | When the job completed | Set when status becomes SUCCEEDED/FAILED |
| **lastUpdated** | String (ISO) | `"2025-08-08T20:35:00.123456Z"` | Last update timestamp | Updated on every write |
| **username** | String | `"fprior"` | User who initiated the job | Set at job creation from batch environment |
| **jobName** | String | `"pipeline-47069bf6-20250808-203357"` | AWS Batch job name | Set at job creation |
| **currentStage** | String | `"Stage 6: GitHub Integration"` | Current pipeline stage description | Updated as pipeline progresses through stages |
| **overallProgress** | Number | `85` | Overall completion percentage (0-100) | Updated throughout execution |
| **githubRepoUrl** | String | `"https://github.com/ocean-studio-repos/digital-wellness-revolution"` | Created GitHub repository URL | Set after successful Stage 6 completion |
| **githubRepoName** | String | `"digital-wellness-revolution"` | Name of created repository | Set after successful Stage 6 completion |
| **issuesCreated** | Number | `10` | Number of GitHub issues created | Set after successful Stage 6 completion |
| **error** | String | `"Failed to generate product ideas: API rate limit"` | Error message if job failed | Set only on failure |
| **batchJobArn** | String | `"arn:aws:batch:us-east-1:984906149037:job/..."` | Full AWS Batch job ARN | Set after job submission |
| **logStreamName** | String | `"pipeline/default/825510a4-9779-4392-9db0-d223ea16de46"` | CloudWatch log stream | Set when job starts running |
| **logGroupName** | String | `"/aws/batch/job/multi-step-llm"` | CloudWatch log group | Set when job starts running |

## Global Secondary Indexes

| Index Name | Partition Key | Sort Key | Purpose |
|------------|--------------|----------|---------|
| ResearchIdIndex | researchId | - | Query all jobs for a specific research document |
| UsernameIndex | username | startTime | Query all jobs by a specific user |

## Update Flow

### 1. Job Creation (batch_wrapper.py)
```python
job_tracker.create_job(
    job_id="825510a4-9779-4392-9db0-d223ea16de46",
    research_id="47069bf6-aeda-4c9b-b979-4f4b8daa3a09",
    username="fprior",
    job_name="pipeline-47069bf6-20250808-203357"
)
```
Creates initial record with: `jobId`, `researchId`, `status=SUBMITTED`, `startTime`, `username`, `jobName`, `overallProgress=0`

### 2. Pipeline Progress Updates (batch_wrapper.py)
```python
job_tracker.update_job_status(
    job_id="825510a4-9779-4392-9db0-d223ea16de46",
    status="RUNNING",
    current_stage="Stage 4: Product Ideas",
    progress=60
)
```
Updates: `status`, `currentStage`, `overallProgress`, `lastUpdated`

### 3. GitHub Results Update (batch_wrapper.py after reading github_results.json)
```python
job_tracker.update_job_results(
    job_id="825510a4-9779-4392-9db0-d223ea16de46",
    github_repo_url="https://github.com/ocean-studio-repos/digital-wellness-revolution",
    github_repo_name="digital-wellness-revolution",
    issues_created=10
)
```
Updates: `githubRepoUrl`, `githubRepoName`, `issuesCreated`, `lastUpdated`

### 4. Job Completion (batch_wrapper.py)
```python
# Success case
job_tracker.update_job_status(
    job_id="825510a4-9779-4392-9db0-d223ea16de46",
    status="SUCCEEDED",
    current_stage="Pipeline complete",
    progress=100
)

# Failure case
job_tracker.update_job_status(
    job_id="825510a4-9779-4392-9db0-d223ea16de46",
    status="FAILED",
    error="Pipeline failed: No opportunity zones found",
    current_stage="Pipeline failed"
)
```
Updates: `status`, `endTime`, `currentStage`, `overallProgress`, `lastUpdated`, and optionally `error`

## Stage Progress Mapping

| Stage | currentStage Value | overallProgress |
|-------|-------------------|-----------------|
| Start | "Starting pipeline" | 0 |
| Stage 1 | "Stage 1: Research Analysis" | 10 |
| Stage 2 | "Stage 2: JTBD Extraction" | 25 |
| Stage 3 | "Stage 3: Opportunity Zones" | 40 |
| Stage 4 | "Stage 4: Product Ideas" | 60 |
| Stage 5 | "Stage 5: Consolidation" | 75 |
| Stage 6 | "Stage 6: GitHub Integration" | 90 |
| Complete | "Pipeline complete" | 100 |

## Query Patterns

### Get Job by ID
```python
response = table.get_item(Key={'jobId': '825510a4-9779-4392-9db0-d223ea16de46'})
job = response.get('Item')
```

### Get All Jobs for a Research Document
```python
response = table.query(
    IndexName='ResearchIdIndex',
    KeyConditionExpression='researchId = :rid',
    ExpressionAttributeValues={':rid': '47069bf6-aeda-4c9b-b979-4f4b8daa3a09'}
)
jobs = response.get('Items', [])
```

### Get Recent Jobs (for status dashboard)
```python
# Scan with time filter (last 48 hours)
cutoff_time = (datetime.utcnow() - timedelta(hours=48)).isoformat() + 'Z'
response = table.scan(
    FilterExpression='startTime > :cutoff',
    ExpressionAttributeValues={':cutoff': cutoff_time}
)
recent_jobs = response.get('Items', [])
```

## Frontend Integration

The frontend queries this table via Lambda functions:
- **GET /api/status/running** - Returns all recent jobs (last 48 hours)
- **GET /api/plan/async/status/{jobId}** - Returns detailed status for specific job

The Lambda function (`lambda_pipeline_status.py`) maps backend status values to frontend-expected values:
- `SUCCEEDED` → `COMPLETED`
- `SUBMITTED/PENDING/RUNNABLE/STARTING` → `QUEUED`
- `RUNNING` → `RUNNING`
- `FAILED` → `FAILED`

## Important Notes

1. **GitHub Fields**: The `githubRepoUrl`, `githubRepoName`, and `issuesCreated` fields are only populated if Stage 6 completes successfully and creates a repository.

2. **Progress Tracking**: The `overallProgress` field provides a 0-100 percentage for UI progress bars. The `currentStage` provides human-readable status.

3. **Error Handling**: The `error` field is only populated on failure and is truncated to 1000 characters due to DynamoDB attribute size limits.

4. **TTL**: Jobs older than 30 days are automatically deleted via DynamoDB TTL (not shown in schema but configured on table).

5. **Concurrency**: Multiple jobs can run for the same `researchId` - the frontend typically shows the most recent.