# Frontend-Backend Integration Guide

## Overview

This guide documents the integration between the frontend application and the Multi-Step LLM Pipeline backend, including API endpoints, data flow, and common integration patterns.

## Production Endpoints

### Base URL
```
https://9hv22ga3uh.execute-api.us-east-1.amazonaws.com/prod/
```

### Available Endpoints

#### 1. Submit Pipeline Job
**Endpoint**: `POST /submit`

**Request Headers**:
```http
Content-Type: application/json
Origin: [your-frontend-domain]
```

**Request Body**:
```json
{
  "researchId": "report-2024-12-15-123456"
}
```

**Response (Success - 200)**:
```json
{
  "jobId": "abc123-def456-789012",
  "jobName": "pipeline-report-2024-12-15-123456-20241215-143022",
  "status": "SUBMITTED",
  "message": "Pipeline job submitted successfully"
}
```

**Response (Error - 404)**:
```json
{
  "error": "Research not found"
}
```

**Response (Error - 400)**:
```json
{
  "error": "Research report exists but has no S3 file associated"
}
```

#### 2. Monitor Job Logs
**Endpoint**: `GET /logs/{researchId}`

**Path Parameters**:
- `researchId`: The report ID from ResearchReports table

**Response (Success - 200)**:
```json
{
  "jobId": "abc123-def456-789012",
  "researchId": "report-2024-12-15-123456",
  "status": "RUNNING",
  "createdAt": "2024-12-15T14:30:22Z",
  "logs": [
    {
      "timestamp": 1702650622000,
      "message": "Starting pipeline..."
    },
    {
      "timestamp": 1702650623000,
      "message": "Stage 1: Research Analysis - Starting..."
    }
  ],
  "logStreamUrl": "https://console.aws.amazon.com/cloudwatch/..."
}
```

**Response (Error - 404)**:
```json
{
  "error": "No job found for this research"
}
```

## DynamoDB Table Structure

### ResearchReports Table (Frontend-Managed)

**Table Name**: `ResearchReports`
**Primary Key**: `reportId` (String)

**Item Structure**:
```json
{
  "reportId": "report-2024-12-15-123456",
  "s3ReportKey": "research/2024-12-15T14:30:22Z/research.json",
  "status": "ready",
  "createdAt": "2024-12-15T14:30:22Z",
  "metadata": {
    "title": "Market Research Report",
    "description": "Analysis of emerging markets",
    "author": "Research Team",
    "tags": ["market-analysis", "innovation"]
  }
}
```

### PipelineBatchJobs Table (Backend-Managed)

**Table Name**: `PipelineBatchJobs`
**Primary Key**: `jobId` (String)
**GSI**: `ResearchIdIndex` on `researchId`

**Item Structure**:
```json
{
  "jobId": "abc123-def456-789012",
  "researchId": "report-2024-12-15-123456",
  "jobName": "pipeline-report-2024-12-15-123456-20241215-143022",
  "status": "RUNNING",
  "createdAt": "2024-12-15T14:30:22Z",
  "batchJobId": "abc123-def456-789012",
  "logStreamName": "pipeline/default/abc123-def456-789012",
  "ttl": 1705242622
}
```

## Frontend Integration Example

### React/TypeScript Example

```typescript
// api.service.ts
const API_BASE_URL = 'https://9hv22ga3uh.execute-api.us-east-1.amazonaws.com/prod';

interface SubmitJobRequest {
  researchId: string;
}

interface SubmitJobResponse {
  jobId: string;
  jobName: string;
  status: string;
  message: string;
}

interface JobLogsResponse {
  jobId: string;
  researchId: string;
  status: string;
  createdAt: string;
  logs: Array<{
    timestamp: number;
    message: string;
  }>;
  logStreamUrl: string;
}

export class PipelineAPI {
  async submitJob(researchId: string): Promise<SubmitJobResponse> {
    const response = await fetch(`${API_BASE_URL}/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ researchId }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to submit job');
    }

    return response.json();
  }

  async getJobLogs(researchId: string): Promise<JobLogsResponse> {
    const response = await fetch(`${API_BASE_URL}/logs/${researchId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch logs');
    }

    return response.json();
  }

  // Poll for job completion
  async pollJobStatus(
    researchId: string,
    onUpdate?: (logs: JobLogsResponse) => void,
    pollInterval = 3000
  ): Promise<JobLogsResponse> {
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const logs = await this.getJobLogs(researchId);
          
          if (onUpdate) {
            onUpdate(logs);
          }

          if (logs.status === 'SUCCEEDED') {
            resolve(logs);
          } else if (logs.status === 'FAILED') {
            reject(new Error('Job failed'));
          } else {
            setTimeout(poll, pollInterval);
          }
        } catch (error) {
          reject(error);
        }
      };

      poll();
    });
  }
}
```

### Usage in React Component

```tsx
import React, { useState } from 'react';
import { PipelineAPI } from './api.service';

const api = new PipelineAPI();

export function PipelineRunner({ researchId }: { researchId: string }) {
  const [status, setStatus] = useState<string>('');
  const [logs, setLogs] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const runPipeline = async () => {
    try {
      setLoading(true);
      setStatus('Submitting job...');
      
      // Submit the job
      const submitResponse = await api.submitJob(researchId);
      setStatus(`Job submitted: ${submitResponse.jobId}`);
      
      // Poll for updates
      await api.pollJobStatus(
        researchId,
        (update) => {
          setStatus(update.status);
          setLogs(update.logs.map(l => l.message));
        },
        3000 // Poll every 3 seconds
      );
      
      setStatus('Pipeline completed successfully!');
    } catch (error) {
      setStatus(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={runPipeline} disabled={loading}>
        {loading ? 'Running...' : 'Run Pipeline'}
      </button>
      
      <div>Status: {status}</div>
      
      <div>
        <h3>Logs:</h3>
        <pre>
          {logs.map((log, i) => (
            <div key={i}>{log}</div>
          ))}
        </pre>
      </div>
    </div>
  );
}
```

## CORS Configuration

The backend Lambda functions include the following CORS headers:

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

**Note**: In production, consider restricting `Access-Control-Allow-Origin` to specific domains rather than using `*`.

## Job Status Values

The pipeline job can have the following status values:

- `SUBMITTED`: Job has been submitted to AWS Batch
- `PENDING`: Job is waiting for resources
- `RUNNABLE`: Job is ready to run
- `STARTING`: Container is starting
- `RUNNING`: Pipeline is executing
- `SUCCEEDED`: Pipeline completed successfully
- `FAILED`: Pipeline encountered an error

## Error Handling

### Common Error Scenarios

1. **Research Not Found (404)**
   - The provided `researchId` doesn't exist in ResearchReports table
   - Solution: Ensure the research report is created before submitting job

2. **Missing S3 Key (400)**
   - Research exists but has no `s3ReportKey` field
   - Solution: Ensure research upload to S3 is complete

3. **No Job Found (404)**
   - No job has been submitted for this research ID
   - Solution: Submit a job first before checking logs

4. **CORS Error**
   - Frontend domain not allowed by CORS policy
   - Solution: Check API Gateway CORS configuration

## Pipeline Output

After successful completion, the pipeline creates the following outputs in S3:

```
s3://multi-step-llm-research-984906149037/outputs/{RESEARCH_ID}/
├── analysis_results.md
├── jtbds_*.txt
├── reddit_discussions_*.csv
├── opportunity_zones.json
├── product_ideas.json
├── final_innovation_portfolio.json
└── final_innovation_portfolio_summary.md
```

Additionally, a GitHub repository is created with:
- Comprehensive README with all research insights
- Individual issues for each product idea
- Smart labeling based on priority and category

## Testing the Integration

### Using cURL

```bash
# Submit a job
curl -X POST https://9hv22ga3uh.execute-api.us-east-1.amazonaws.com/prod/submit \
  -H "Content-Type: application/json" \
  -d '{"researchId": "report-2024-12-15-123456"}'

# Check logs
curl https://9hv22ga3uh.execute-api.us-east-1.amazonaws.com/prod/logs/report-2024-12-15-123456
```

### Using Postman

1. Create a new POST request to `https://9hv22ga3uh.execute-api.us-east-1.amazonaws.com/prod/submit`
2. Set Content-Type header to `application/json`
3. Add body: `{"researchId": "your-report-id"}`
4. Send request and note the jobId
5. Create GET request to `/logs/{researchId}` to monitor progress

## Best Practices

1. **Polling Interval**: Use 3-5 second intervals to avoid overwhelming the API
2. **Error Recovery**: Implement exponential backoff on errors
3. **Timeout Handling**: Set a maximum polling duration (e.g., 30 minutes)
4. **User Feedback**: Show real-time logs to users during execution
5. **Result Caching**: Cache completed job results to avoid re-polling

## Support

For issues or questions about the integration:
1. Check CloudWatch Logs for detailed error messages
2. Verify research exists in ResearchReports table
3. Ensure S3 permissions are correctly configured
4. Review Lambda function logs for CORS or execution errors