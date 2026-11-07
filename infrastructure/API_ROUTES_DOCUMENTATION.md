# Enhanced API Routes Documentation

## Base URL
```
https://9hv22ga3uh.execute-api.us-east-1.amazonaws.com/prod/
```

## Available Routes

### 1. POST /submit - Submit Pipeline Job (Enhanced)

**Request Body:**
```json
{
  "researchId": "research-123",
  "force": false  // Optional: Override running job check
}
```

**Success Response (200):**
```json
{
  "jobId": "12345678-1234-1234-1234-123456789abc",
  "jobName": "pipeline-research123-20241215-143022",
  "status": "SUBMITTED",
  "message": "Pipeline job submitted successfully",
  "estimatedDuration": "10-15 minutes"
}
```

**Conflict Response (409):**
```json
{
  "error": "A job is already running for this research",
  "existingJobId": "existing-job-id",
  "status": "RUNNING",
  "hint": "Add \"force\": true to override"
}
```

**Error Responses:**
- 400: Invalid request (missing researchId, invalid format)
- 404: Research not found or S3 file missing
- 500: Server error submitting job

---

### 2. GET /status/{jobId} - Direct Job Status

**Response (200):**
```json
{
  "jobId": "12345678-1234-1234-1234-123456789abc",
  "researchId": "research-123",
  "status": "RUNNING",
  "createdAt": "2024-12-15T14:30:22Z",
  "updatedAt": "2024-12-15T14:35:00Z",
  "startedAt": 1702634400000,
  "stoppedAt": null,
  "duration": null
}
```

**Error Responses:**
- 404: Job not found

---

### 3. GET /jobs - List All Jobs

**Query Parameters:**
- `limit`: Max results (1-100, default: 20)
- `status`: Filter by status (SUBMITTED, RUNNING, SUCCEEDED, FAILED)
- `researchId`: Filter by research ID
- `nextToken`: Pagination token

**Response (200):**
```json
{
  "jobs": [
    {
      "jobId": "job-1",
      "researchId": "research-123",
      "status": "SUCCEEDED",
      "createdAt": "2024-12-15T14:30:22Z",
      "updatedAt": "2024-12-15T14:45:00Z"
    },
    {
      "jobId": "job-2",
      "researchId": "research-456",
      "status": "RUNNING",
      "createdAt": "2024-12-15T15:00:00Z",
      "updatedAt": "2024-12-15T15:05:00Z"
    }
  ],
  "count": 2,
  "nextToken": "eyJqb2JJZCI6ICJqb2ItMyJ9"  // Optional, if more results
}
```

---

### 4. DELETE /jobs/{jobId} - Cancel Running Job

**Request Body (Optional):**
```json
{
  "reason": "User requested cancellation"
}
```

**Success Response (200):**
```json
{
  "message": "Job cancelled successfully",
  "jobId": "12345678-1234-1234-1234-123456789abc",
  "status": "CANCELLED"
}
```

**Error Responses:**
- 400: Job already completed
- 404: Job not found
- 500: Failed to cancel

---

### 5. GET /results/{researchId} - Get Pipeline Results

**Response (200):**
```json
{
  "researchId": "research-123",
  "jobId": "successful-job-id",
  "completedAt": "2024-12-15T14:45:00Z",
  "files": [
    {
      "key": "outputs/research-123/final_innovation_portfolio.json",
      "size": 45678,
      "lastModified": "2024-12-15T14:44:50Z",
      "downloadUrl": "https://s3.amazonaws.com/..."  // Presigned URL (1 hour)
    },
    {
      "key": "outputs/research-123/opportunity_zones.json",
      "size": 12345,
      "lastModified": "2024-12-15T14:42:30Z",
      "downloadUrl": "https://s3.amazonaws.com/..."
    }
  ],
  "totalFiles": 2
}
```

**Error Responses:**
- 404: No successful pipeline run found
- 500: Failed to retrieve results

---

### 6. GET /logs/{researchId} - Get Job Logs (Existing)

**Response (200):**
```json
{
  "jobId": "job-id",
  "researchId": "research-123",
  "status": "RUNNING",
  "createdAt": "2024-12-15T14:30:22Z",
  "logs": [
    {
      "timestamp": 1702634400000,
      "message": "Stage 1: Research Analysis started"
    }
  ],
  "logStreamUrl": "https://console.aws.amazon.com/cloudwatch/..."
}
```

---

### 7. GET /health - System Health Check

**Response (200 if healthy, 503 if degraded):**
```json
{
  "status": "healthy",  // or "degraded"
  "timestamp": "2024-12-15T16:00:00Z",
  "checks": {
    "dynamodb": "healthy",
    "batch": "ENABLED"
  },
  "queueStatus": "VALID"
}
```

---

## Status Values

Pipeline jobs progress through these statuses:
1. `SUBMITTED` - Job accepted and queued
2. `PENDING` - Waiting for compute resources
3. `RUNNABLE` - Resources allocated, waiting to start
4. `STARTING` - Container starting up
5. `RUNNING` - Pipeline actively executing
6. `SUCCEEDED` - Completed successfully
7. `FAILED` - Pipeline failed
8. `CANCELLED` - User cancelled the job

## Rate Limiting

Currently not implemented, but planned:
- 10 requests per second per IP
- 100 jobs per day per researchId

## Authentication

Currently open, but planned:
- API Key authentication via `X-Api-Key` header
- JWT tokens for user-specific access

## Webhook Support (Planned)

Future enhancement to support callbacks:
```json
{
  "researchId": "research-123",
  "callbackUrl": "https://your-server.com/webhook",
  "callbackHeaders": {
    "Authorization": "Bearer token"
  }
}
```

## Example Usage

### Complete Workflow
```bash
# 1. Submit a job
curl -X POST https://api.example.com/prod/submit \
  -H "Content-Type: application/json" \
  -d '{"researchId": "research-123"}'

# 2. Check status
curl https://api.example.com/prod/status/job-id-here

# 3. Monitor logs
curl https://api.example.com/prod/logs/research-123

# 4. Get results when complete
curl https://api.example.com/prod/results/research-123

# 5. Cancel if needed
curl -X DELETE https://api.example.com/prod/jobs/job-id-here
```

### Pagination Example
```bash
# First page
curl "https://api.example.com/prod/jobs?limit=10"

# Next page using token
curl "https://api.example.com/prod/jobs?limit=10&nextToken=eyJqb2JJZCI6ICJqb2ItMTEifQ=="
```

### Filtering Example
```bash
# Get all running jobs
curl "https://api.example.com/prod/jobs?status=RUNNING"

# Get jobs for specific research
curl "https://api.example.com/prod/jobs?researchId=research-123"
```