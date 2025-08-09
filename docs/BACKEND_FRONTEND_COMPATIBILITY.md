# Backend-Frontend API Compatibility Analysis

## 1. GET /api/status/running Endpoint

### Frontend Expects:
```json
{
  "jobs": [
    {
      "jobId": "uuid-string",
      "researchId": "report-2024-12-15-123456",
      "username": "user123",
      "startTime": "2024-12-15T10:30:00Z",
      "endTime": "2024-12-15T10:52:00Z",
      "status": "SUBMITTED" | "PENDING" | "RUNNING" | "SUCCEEDED" | "FAILED",
      "currentStage": "Innovation Ideation",
      "overallProgress": 45,
      "elapsedMinutes": 12,
      "githubRepoUrl": "https://github.com/user/repo",
      "issuesCreated": 15,
      "error": "Error message"
    }
  ]
}
```

### Backend Currently Provides:
✅ **PARTIALLY SUPPORTED** - The Lambda function exists at `/status/running` but:

**What's Available:**
- ✅ `jobId` - Stored in DynamoDB
- ✅ `researchId` - Stored in DynamoDB
- ✅ `username` - Stored if provided
- ✅ `startTime` - Stored in DynamoDB
- ✅ `endTime` - Set when job completes
- ✅ `status` - Tracked (SUBMITTED, RUNNING, SUCCEEDED, FAILED)
- ✅ `currentStage` - Updated during pipeline execution
- ✅ `overallProgress` - Tracked 0-100
- ✅ `elapsedMinutes` - Calculated in get_job()
- ✅ `githubRepoUrl` - Stored when pipeline completes
- ✅ `issuesCreated` - Stored when pipeline completes
- ✅ `error` - Stored on failure

**Issues:**
- ❌ The endpoint returns ALL running jobs, not recent jobs (last 24-48 hours)
- ❌ Response wraps jobs in `{ "status": "RUNNING", "jobs": [...], "count": n }`
- ⚠️ Need to modify to return just `{ "jobs": [...] }` format
- ⚠️ Should include completed/failed jobs from last 24-48 hours, not just RUNNING

## 2. GET /api/plan/async/status/{jobId} Endpoint

### Frontend Expects:
```json
{
  "jobId": "uuid-string",
  "status": "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED",
  "currentStage": 1,
  "stageName": "Research Analysis",
  "stageProgress": 75,
  "overallProgress": 35,
  "elapsedMinutes": 8,
  "estimatedRemainingMinutes": 14,
  "estimatedTotalMinutes": 22,
  "actualDurationMinutes": 21,
  "metadata": {
    "researchDocId": "report-2024-12-15-123456",
    "startedAt": "2024-12-15T10:30:00Z",
    "username": "user123",
    "jobId": "uuid-string"
  },
  "stages": [...],
  "results": {
    "githubRepoUrl": "...",
    "githubRepoName": "...",
    "issuesCreated": 15,
    "analysisResults": null
  },
  "completedAt": "2024-12-15T10:52:00Z",
  "error": "Error message"
}
```

### Backend Currently Provides:
❌ **NOT IMPLEMENTED** - This specific endpoint doesn't exist in lambda_job_mapper.py

**What We Have Instead:**
- `/job/{jobId}` - Returns job details but in different format
- `/job/{jobId}/research` - Returns just jobId, researchId, status, progress

**What's Missing:**
- ❌ No `/api/plan/async/status/{jobId}` endpoint
- ❌ No stage number (currentStage as integer)
- ❌ No stageProgress (progress within current stage)
- ❌ No time estimates (estimatedRemainingMinutes, estimatedTotalMinutes)
- ❌ No stages array with detailed stage info
- ❌ No metadata wrapper object
- ❌ Status values differ (SUCCEEDED vs COMPLETED)

## 3. Key Gaps to Address

### A. Create New Lambda Endpoints
Need to create or update Lambda functions to provide:

1. **GET /api/status/running** - Modified version that:
   - Returns recent jobs (24-48 hours), not just RUNNING
   - Matches exact response format expected
   - Removes wrapper object

2. **GET /api/plan/async/status/{jobId}** - New endpoint that:
   - Maps to InnovationPipelineJobs data
   - Calculates stage numbers and progress
   - Provides time estimates
   - Uses correct status values (COMPLETED vs SUCCEEDED)

### B. Data Mapping Required

**Status Value Mapping:**
```python
STATUS_MAP = {
    'SUBMITTED': 'QUEUED',
    'PENDING': 'QUEUED',
    'RUNNING': 'RUNNING',
    'SUCCEEDED': 'COMPLETED',
    'FAILED': 'FAILED'
}
```

**Stage Number Mapping:**
```python
STAGE_NUMBERS = {
    'Starting pipeline': 0,
    'Stage 1: Research Analysis': 1,
    'Stage 2: JTBD Extraction': 2,
    'Stage 3: Opportunity Zones': 3,
    'Stage 4: Product Ideas': 4,
    'Stage 5: Consolidation': 5,
    'Stage 6: GitHub Integration': 6
}
```

### C. Time Estimation Logic
Need to add:
```python
def calculate_time_estimates(elapsed_minutes, current_stage, overall_progress):
    # Average pipeline takes 15-20 minutes
    AVERAGE_TOTAL = 18
    
    if overall_progress > 0:
        estimated_total = (elapsed_minutes / overall_progress) * 100
        estimated_remaining = estimated_total - elapsed_minutes
    else:
        estimated_total = AVERAGE_TOTAL
        estimated_remaining = AVERAGE_TOTAL
    
    return {
        'estimatedRemainingMinutes': round(estimated_remaining),
        'estimatedTotalMinutes': round(estimated_total)
    }
```

## 4. Implementation Plan

### Option 1: Update Existing Lambda
Update `lambda_job_mapper.py` to add the missing endpoints and format responses correctly.

### Option 2: Create New Lambda Function
Create `lambda_pipeline_status.py` specifically for frontend compatibility with exact format matching.

### Option 3: API Gateway Transformation
Use API Gateway response mapping templates to transform existing responses to match frontend expectations.

## 5. Quick Fixes Needed

### Immediate Changes for Compatibility:

1. **Update `/status/running` endpoint:**
```python
# In lambda_job_mapper.py
elif path == '/status/running' or path == '/api/status/running':
    # Get recent jobs (last 48 hours), not just RUNNING
    from datetime import timedelta
    cutoff_time = (datetime.utcnow() - timedelta(hours=48)).isoformat() + 'Z'
    
    # Query multiple statuses
    all_jobs = []
    for status in ['RUNNING', 'SUCCEEDED', 'FAILED', 'SUBMITTED', 'PENDING']:
        response = table.query(
            IndexName='status-startTime-index',
            KeyConditionExpression='#status = :status AND startTime > :cutoff',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': status,
                ':cutoff': cutoff_time
            },
            ScanIndexForward=False,
            Limit=20
        )
        all_jobs.extend(response.get('Items', []))
    
    # Sort by startTime descending
    all_jobs.sort(key=lambda x: x.get('startTime', ''), reverse=True)
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({'jobs': all_jobs[:50]}, default=decimal_default)
    }
```

2. **Add `/api/plan/async/status/{jobId}` endpoint:**
```python
elif path.startswith('/api/plan/async/status/'):
    job_id = path.split('/')[-1]
    # Get job and transform to expected format
    job = get_job_with_frontend_format(job_id)
    return {
        'statusCode': 200 if job else 404,
        'headers': headers,
        'body': json.dumps(job or {'error': 'Job not found'}, default=decimal_default)
    }
```

## Summary

**Partially Compatible**: The backend has most of the data needed but:
1. Response formats don't match exactly
2. Some endpoints are missing
3. Status values need mapping
4. Time estimates aren't calculated

**Recommendation**: Create a new Lambda function or update the existing one to provide exact compatibility with frontend expectations.