# Frontend API Contract - Innovation Pipeline

## Base Configuration
```javascript
const API_BASE_URL = process.env.VITE_API_BASE_URL || 'https://9hv22ga3uh.execute-api.us-east-1.amazonaws.com/prod';
const POLLING_INTERVAL = 3000; // 3 seconds
```

## 1. Pipeline Initiation

### Start Pipeline (Async)
**Endpoint**: `POST /api/plan/async/start`

**Request**:
```json
{
  "metadata": {
    "title": "Q1 2025 Market Research",
    "domain": "productivity-tools",
    "teamName": "Innovation Lab",
    "description": "Analysis of productivity tool market gaps",
    "visibility": "private"
  },
  "readmeContent": "# Market Research\n\n## Executive Summary\n..."
}
```

**Response** (200 OK):
```json
{
  "jobId": "abc123-def456-789",
  "researchId": "research-2025-01-08-xyz",
  "status": "SUBMITTED",
  "message": "Pipeline started successfully",
  "estimatedCompletionTime": "15-20 minutes",
  "pollUrl": "/api/plan/async/status/abc123-def456-789"
}
```

**Error Response** (400/500):
```json
{
  "error": "Invalid input",
  "message": "Research content is required",
  "code": "MISSING_CONTENT"
}
```

## 2. Progress Monitoring

### Get Job Status
**Endpoint**: `GET /api/plan/async/status/{jobId}`

**Response** (200 OK):
```json
{
  "jobId": "abc123-def456-789",
  "researchId": "research-2025-01-08-xyz",
  "status": "RUNNING",
  "overallProgress": 47,
  "currentStage": "Stage 3: Opportunity Zones",
  "startTime": "2025-01-08T15:30:00Z",
  "elapsedMinutes": 7.3,
  "stages": {
    "research_analysis": {
      "status": "completed",
      "duration": 2.1,
      "output": {
        "keyFindings": 5,
        "painPoints": 12,
        "opportunities": 8
      }
    },
    "jtbd_extraction": {
      "status": "completed",
      "duration": 3.2,
      "output": {
        "jobsIdentified": 27,
        "redditDiscussions": 523,
        "averageImportance": 8.2,
        "averageSatisfaction": 3.1
      }
    },
    "opportunity_zones": {
      "status": "running",
      "duration": 1.0,
      "output": null
    },
    "product_ideas": {
      "status": "pending",
      "duration": null,
      "output": null
    },
    "consolidation": {
      "status": "pending",
      "duration": null,
      "output": null
    },
    "github_creation": {
      "status": "pending",
      "duration": null,
      "output": null
    }
  }
}
```

**Status Values**:
- `SUBMITTED` - Job queued
- `PENDING` - Waiting for resources
- `RUNNING` - Actively processing
- `SUCCEEDED` - Completed successfully
- `FAILED` - Pipeline failed

### Get Job Results (When Complete)
**Endpoint**: `GET /api/plan/async/status/{jobId}`

**Response when SUCCEEDED**:
```json
{
  "jobId": "abc123-def456-789",
  "researchId": "research-2025-01-08-xyz",
  "status": "SUCCEEDED",
  "overallProgress": 100,
  "currentStage": "Pipeline Complete",
  "startTime": "2025-01-08T15:30:00Z",
  "endTime": "2025-01-08T15:48:32Z",
  "elapsedMinutes": 18.5,
  "results": {
    "githubRepository": {
      "url": "https://github.com/innovation-lab/productivity-ventures-2025",
      "name": "productivity-ventures-2025",
      "visibility": "private",
      "issuesCreated": 10,
      "createdAt": "2025-01-08T15:48:30Z"
    },
    "summary": {
      "opportunityZones": 4,
      "totalMarketSize": "$15.2B",
      "productIdeas": 10,
      "topOpportunity": {
        "name": "AI Workflow Assistant",
        "marketShare": 40,
        "estimatedRevenue": "$6.1B"
      }
    },
    "artifacts": {
      "analysisResults": "s3://bucket/outputs/research-id/analysis_results.md",
      "opportunityZones": "s3://bucket/outputs/research-id/opportunity_zones.json",
      "productIdeas": "s3://bucket/outputs/research-id/product_ideas.json",
      "portfolio": "s3://bucket/outputs/research-id/final_innovation_portfolio.json"
    }
  }
}
```

## 3. Job History & Management

### Get Jobs for Research
**Endpoint**: `GET /api/research/{researchId}/jobs`

**Response**:
```json
{
  "researchId": "research-2025-01-08-xyz",
  "jobs": [
    {
      "jobId": "abc123-def456-789",
      "startTime": "2025-01-08T15:30:00Z",
      "endTime": "2025-01-08T15:48:32Z",
      "status": "SUCCEEDED",
      "elapsedMinutes": 18.5,
      "githubRepoUrl": "https://github.com/innovation-lab/productivity-ventures-2025",
      "issuesCreated": 10
    },
    {
      "jobId": "earlier-job-123",
      "startTime": "2025-01-08T10:00:00Z",
      "endTime": "2025-01-08T10:05:00Z",
      "status": "FAILED",
      "elapsedMinutes": 5.0,
      "error": "Stage 3 failed: list index out of range"
    }
  ],
  "count": 2
}
```

### Get Running Jobs
**Endpoint**: `GET /api/status/running`

**Response**:
```json
{
  "status": "RUNNING",
  "jobs": [
    {
      "jobId": "job-1",
      "researchId": "research-1",
      "username": "john.doe",
      "startTime": "2025-01-08T15:30:00Z",
      "currentStage": "Stage 4: Product Ideas",
      "overallProgress": 65
    },
    {
      "jobId": "job-2",
      "researchId": "research-2",
      "username": "jane.smith",
      "startTime": "2025-01-08T15:25:00Z",
      "currentStage": "Stage 2: JTBD Extraction",
      "overallProgress": 25
    }
  ],
  "count": 2
}
```

## 4. Data Retrieval

### Download Artifacts
**Endpoint**: `GET /api/results/{jobId}/download`

**Query Parameters**:
- `format`: `json` | `markdown` | `zip` (default: zip)
- `artifact`: `all` | `analysis` | `zones` | `ideas` | `portfolio` (default: all)

**Response**: Binary file download or JSON

### Get Specific Results
**Endpoint**: `GET /api/results/{jobId}/opportunities`

**Response**:
```json
{
  "jobId": "abc123-def456-789",
  "opportunityZones": [
    {
      "name": "Workflow Automation & Context Sharing",
      "marketOpportunityPercentage": 40,
      "marketSize": "$6.1B",
      "painDimensions": {
        "timing_coordination": 9.2,
        "communication_gaps": 8.7,
        "process_complexity": 8.5
      },
      "targetIdeas": 4,
      "keyJobs": [
        "When I need to share context with my team",
        "When I want to automate repetitive workflows"
      ]
    },
    {
      "name": "Knowledge Management",
      "marketOpportunityPercentage": 30,
      "marketSize": "$4.5B",
      "targetIdeas": 3
    }
  ]
}
```

## 5. Frontend State Management

### Polling Implementation
```javascript
const usePipelinePolling = (jobId) => {
  const [status, setStatus] = useState(null);
  const [isComplete, setIsComplete] = useState(false);
  
  useEffect(() => {
    if (!jobId || isComplete) return;
    
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/plan/async/status/${jobId}`);
        const data = await response.json();
        
        setStatus(data);
        
        if (data.status === 'SUCCEEDED' || data.status === 'FAILED') {
          setIsComplete(true);
          clearInterval(interval);
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, POLLING_INTERVAL);
    
    return () => clearInterval(interval);
  }, [jobId, isComplete]);
  
  return { status, isComplete };
};
```

### Error Handling
```javascript
const ERROR_CODES = {
  'MISSING_CONTENT': 'Please provide research content',
  'INVALID_FORMAT': 'File format not supported',
  'QUOTA_EXCEEDED': 'Monthly limit reached',
  'PIPELINE_TIMEOUT': 'Analysis taking longer than expected',
  'GITHUB_CREATION_FAILED': 'Could not create GitHub repository',
  'STAGE_FAILED': 'Pipeline stage failed - check logs'
};

const handleApiError = (error) => {
  const message = ERROR_CODES[error.code] || 'An unexpected error occurred';
  return {
    title: 'Pipeline Error',
    message,
    code: error.code,
    retry: error.code !== 'QUOTA_EXCEEDED'
  };
};
```

## 6. WebSocket Alternative (Future)

### Real-time Updates
```javascript
const ws = new WebSocket('wss://api.innovation-pipeline.com/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    action: 'subscribe',
    jobId: 'abc123-def456-789'
  }));
};

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  // Update types: progress, stage_complete, log, error, complete
  
  switch(update.type) {
    case 'progress':
      setProgress(update.progress);
      break;
    case 'stage_complete':
      setStageResults(update.stage, update.results);
      break;
    case 'complete':
      setFinalResults(update.results);
      break;
  }
};
```

## 7. Authentication Headers

### Request Headers
```javascript
const makeAuthenticatedRequest = async (url, options = {}) => {
  const token = localStorage.getItem('authToken');
  
  return fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'X-Research-Team': teamId,
      ...options.headers
    }
  });
};
```

## 8. Rate Limiting

### Headers Returned
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704748800
```

### Handling Rate Limits
```javascript
const handleRateLimit = (response) => {
  const remaining = response.headers.get('X-RateLimit-Remaining');
  const reset = response.headers.get('X-RateLimit-Reset');
  
  if (remaining === '0') {
    const resetTime = new Date(reset * 1000);
    throw new Error(`Rate limit exceeded. Resets at ${resetTime.toLocaleTimeString()}`);
  }
};
```

## 9. File Upload (S3 Presigned URL)

### Get Upload URL
**Endpoint**: `POST /api/research/upload-url`

**Request**:
```json
{
  "fileName": "market-research.md",
  "fileType": "text/markdown",
  "fileSize": 102400
}
```

**Response**:
```json
{
  "uploadUrl": "https://s3.amazonaws.com/bucket/...",
  "researchId": "research-2025-01-08-xyz",
  "expiresAt": "2025-01-08T16:00:00Z"
}
```

### Upload to S3
```javascript
const uploadFile = async (file, uploadUrl) => {
  const response = await fetch(uploadUrl, {
    method: 'PUT',
    body: file,
    headers: {
      'Content-Type': file.type
    }
  });
  
  if (!response.ok) {
    throw new Error('Upload failed');
  }
  
  return true;
};
```

## 10. Testing & Development

### Mock Responses
```javascript
// Development mode mock
if (import.meta.env.DEV) {
  window.mockPipelineStatus = (progress) => ({
    jobId: 'mock-job-123',
    status: progress < 100 ? 'RUNNING' : 'SUCCEEDED',
    overallProgress: progress,
    currentStage: `Stage ${Math.floor(progress / 20) + 1}`,
    // ... mock data
  });
}
```

### CORS Configuration
All API responses include:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

## Implementation Checklist

### Phase 1 - MVP
- [ ] Implement pipeline start endpoint
- [ ] Basic polling for status
- [ ] Display progress percentage
- [ ] Show GitHub URL when complete

### Phase 2 - Enhanced
- [ ] Detailed stage progress
- [ ] Job history by research
- [ ] Error recovery flows
- [ ] Download artifacts

### Phase 3 - Advanced
- [ ] WebSocket real-time updates
- [ ] Batch operations
- [ ] Team collaboration
- [ ] API key management