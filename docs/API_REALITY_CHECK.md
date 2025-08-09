# API Reality Check: Spec vs Implementation

## The Truth About What Happened

### What I Specified in FRONTEND_API_CONTRACT.md:
I created an idealized API specification based on best practices and what would make a good frontend experience. This included:

1. **`POST /api/plan/async/start`** - Start pipeline
2. **`GET /api/plan/async/status/{jobId}`** - Get detailed status
3. **`GET /api/research/{researchId}/jobs`** - Get jobs for research
4. **`GET /api/status/running`** - Get running/recent jobs
5. **`GET /api/results/{jobId}/download`** - Download results
6. **`GET /api/results/{jobId}/opportunities`** - Get opportunities

### What Actually Exists in AWS:

#### Production Endpoints (Confirmed):
```
POST https://9hv22ga3uh.execute-api.us-east-1.amazonaws.com/prod/submit
GET  https://9hv22ga3uh.execute-api.us-east-1.amazonaws.com/prod/logs/{researchId}
```

#### What We Built (in lambda_job_mapper.py):
```
GET /job/{jobId}                 - Get job details
GET /job/{jobId}/research        - Get research ID for job
GET /research/{researchId}/jobs  - List jobs for research  
GET /status/running              - Get running jobs
```

### The Disconnect:

## 1. Different Endpoint Patterns

**I Specified (idealized):**
- `/api/plan/async/status/{jobId}`
- `/api/status/running`

**Frontend Expected (based on my spec):**
- Exactly what I specified

**Backend Actually Has:**
- `/job/{jobId}` (not `/api/plan/async/status/{jobId}`)
- `/status/running` (without `/api` prefix)

## 2. Different Response Formats

**I Specified in FRONTEND_API_CONTRACT.md:**
```json
// For /api/plan/async/status/{jobId}
{
  "status": "RUNNING",
  "currentStage": "Stage 3: Opportunity Zones",
  "overallProgress": 47,
  "stages": {
    "research_analysis": { "status": "completed" },
    "jtbd_extraction": { "status": "completed" }
  }
}
```

**Frontend Built (more complex):**
```json
{
  "status": "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED",
  "currentStage": 1,  // Numeric stage
  "stageName": "Research Analysis",
  "stageProgress": 75,  // Progress within stage
  "metadata": { ... },
  "stages": [ ... ]  // Array not object
}
```

**Backend Actually Returns:**
```json
{
  "jobId": "...",
  "researchId": "...",
  "status": "SUBMITTED" | "RUNNING" | "SUCCEEDED" | "FAILED",
  "currentStage": "Stage 3: Opportunity Zones",  // String not number
  "overallProgress": 47
  // No stages detail, no metadata wrapper
}
```

## 3. Status Value Mismatches

| Backend | My Spec | Frontend Expects |
|---------|---------|------------------|
| SUCCEEDED | SUCCEEDED | COMPLETED |
| SUBMITTED | RUNNING | QUEUED |
| PENDING | RUNNING | QUEUED |

## The Root Cause:

### What Happened:
1. **I created an idealized spec** without fully checking the existing AWS infrastructure
2. **Frontend developer followed my spec** but enhanced it with additional fields
3. **Backend has simpler implementation** than what I specified
4. **No one validated** the spec against actual deployed services

### The Gaps:

#### Missing Lambda Deployments:
- The `lambda_job_mapper.py` exists but may not be deployed
- No API Gateway routes configured for these endpoints
- The endpoints I specified don't exist in production

#### Different Data Models:
- Frontend expects richer data than backend provides
- Status values don't match
- Response structures are different

## What's Actually Deployed:

### Confirmed Working:
1. **AWS Batch Pipeline** - Runs the actual processing
2. **DynamoDB Tables** - Store job tracking data
3. **Basic API** - `/submit` and `/logs` endpoints

### Not Deployed/Configured:
1. **New Lambda functions** - Created but not deployed
2. **API Gateway routes** - Not configured for new endpoints
3. **Response transformations** - No mapping between formats

## The Fix Required:

### Option 1: Deploy What We Built
1. Deploy `lambda_job_mapper.py` to Lambda
2. Configure API Gateway routes
3. Add response transformation layer

### Option 2: Update Frontend
1. Change frontend to use existing `/submit` and `/logs` endpoints
2. Adjust expectations for response format
3. Remove dependency on non-existent endpoints

### Option 3: Build Bridge Layer
1. Create new Lambda that wraps existing endpoints
2. Transform responses to match frontend expectations
3. Deploy as middleware layer

## Conclusion:

**The documents weren't hallucinated, but they were aspirational.** I designed an ideal API without confirming what was actually deployed. The frontend followed the spec, but the backend reality is simpler than specified.

### Immediate Actions Needed:
1. ✅ Deploy the Lambda function we created
2. ✅ Configure API Gateway routes
3. ✅ Add response transformation for format compatibility
4. ✅ Map status values correctly

Or alternatively:
1. ✅ Update frontend to use existing endpoints
2. ✅ Simplify expectations to match backend capabilities