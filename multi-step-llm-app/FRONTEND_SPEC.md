# Frontend Specification - Innovation Pipeline Experience

## Overview
Build a modern, responsive web application that guides users through the Innovation Pipeline - from uploading research to receiving a fully-populated GitHub repository with actionable product ideas.

## Core User Journey

### 1. Research Upload & Input
**Component**: `ResearchUploader`

**User Flow**:
1. User arrives at landing page with clear value proposition
2. Uploads research document (markdown, PDF, or text)
3. Optionally provides metadata (title, domain, team name)
4. Clicks "Start Pipeline" to initiate processing

**UI Requirements**:
- Drag-and-drop file upload zone
- File type validation (.md, .pdf, .txt, .doc)
- Progress indicator for upload
- Metadata form with smart defaults
- Clear CTA button

**API Calls**:
```javascript
// Upload research to S3
POST /api/research/upload
{
  file: File,
  metadata: {
    title: string,
    domain: string,
    teamName: string,
    visibility: 'public' | 'private'
  }
}
Response: {
  researchId: string,
  s3Key: string,
  uploadUrl: string
}

// Start pipeline
POST /api/pipeline/start
{
  researchId: string
}
Response: {
  jobId: string,
  status: 'SUBMITTED',
  estimatedTime: '15-20 minutes'
}
```

### 2. Pipeline Progress Tracking
**Component**: `PipelineTracker`

**Real-time Progress Display**:
```
🚀 Innovation Pipeline Progress

[■■■■■■■□□□□□□□□] 47% Complete
Estimated time remaining: 8 minutes

Current Stage: Analyzing Opportunity Zones
┌──────────────────────────────────────┐
│ ✅ Research Analysis        (2 min)  │
│ ✅ JTBD Extraction          (3 min)  │
│ 🔄 Opportunity Zones        (1 min)  │
│ ⏳ Product Ideation                  │
│ ⏳ Portfolio Consolidation           │
│ ⏳ GitHub Repository                 │
└──────────────────────────────────────┘

Live Insights:
• Found 27 underserved jobs-to-be-done
• Analyzed 523 Reddit discussions
• Identifying 3-5 opportunity zones...
```

**Polling Strategy**:
```javascript
// Poll every 3 seconds for status
GET /api/pipeline/status/{jobId}
Response: {
  jobId: string,
  researchId: string,
  status: 'RUNNING',
  currentStage: 'Stage 3: Opportunity Zones',
  overallProgress: 47,
  elapsedMinutes: 7.3,
  stages: [
    {
      name: 'Research Analysis',
      status: 'completed',
      duration: 2.1,
      insights: {
        keyFindings: 5,
        painPoints: 12
      }
    },
    {
      name: 'JTBD Extraction',
      status: 'completed',
      duration: 3.2,
      insights: {
        jobsFound: 27,
        redditDiscussions: 523
      }
    },
    {
      name: 'Opportunity Zones',
      status: 'running',
      duration: 1.0,
      insights: null
    }
  ]
}
```

**Error Handling**:
- Graceful failure states with clear messaging
- Retry mechanism for transient failures
- Option to download partial results
- Contact support link for persistent issues

### 3. Results Dashboard
**Component**: `ResultsDashboard`

**Layout Structure**:
```
┌─────────────────────────────────────────────┐
│            Pipeline Complete! 🎉            │
├─────────────────────────────────────────────┤
│                                             │
│  GitHub Repository Created                 │
│  ├── 📁 innovation-ventures-2025           │
│  ├── 📄 README.md (Comprehensive)          │
│  └── 🎯 10 Product Ideas (Issues)          │
│                                             │
│  [View Repository] [Download Report]        │
│                                             │
├─────────────────────────────────────────────┤
│  Key Discoveries                           │
│  ┌─────────────┬─────────────┬────────────┤
│  │ Opportunity │ Market Size │ Ideas      │
│  │ Zones: 4    │ $15.2B TAM  │ Generated  │
│  │             │             │ 10         │
│  └─────────────┴─────────────┴────────────┤
│                                             │
│  Top 3 Product Opportunities:              │
│  1. AI Workflow Assistant (40% of market)  │
│  2. Context Sharing Platform (30%)         │
│  3. Team Knowledge Base (20%)              │
│                                             │
└─────────────────────────────────────────────┘
```

**Interactive Elements**:
- Expandable sections for each stage's details
- Download buttons for artifacts (JSON, MD, CSV)
- Share functionality for results
- "Run Another Analysis" CTA

### 4. Pipeline History
**Component**: `PipelineHistory`

**Table View**:
```
Your Pipeline Runs
┌────────────┬──────────────┬─────────┬──────────┬─────────────┐
│ Research   │ Started      │ Status  │ Duration │ Repository  │
├────────────┼──────────────┼─────────┼──────────┼─────────────┤
│ Q1 Market  │ 2 hours ago  │ ✅      │ 18 min   │ [View →]    │
│ Product X  │ Yesterday    │ ✅      │ 22 min   │ [View →]    │
│ User Study │ 3 days ago   │ ❌      │ 5 min    │ [Retry]     │
│ Competitor │ Last week    │ ✅      │ 19 min   │ [View →]    │
└────────────┴──────────────┴─────────┴──────────┴─────────────┘
```

**API Integration**:
```javascript
GET /api/research/{researchId}/jobs
Response: {
  researchId: string,
  jobs: [{
    jobId: string,
    startTime: ISO8601,
    endTime: ISO8601,
    status: string,
    githubRepoUrl: string,
    issuesCreated: number,
    elapsedMinutes: number
  }]
}
```

## Technical Implementation

### State Management
```typescript
interface PipelineState {
  // Current pipeline
  currentJob: {
    jobId: string;
    researchId: string;
    status: JobStatus;
    progress: number;
    currentStage: string;
    startTime: Date;
    stages: StageProgress[];
  };
  
  // Historical data
  pastJobs: Job[];
  
  // UI state
  isPolling: boolean;
  pollInterval: number;
  error: Error | null;
}

enum JobStatus {
  IDLE = 'IDLE',
  SUBMITTED = 'SUBMITTED',
  RUNNING = 'RUNNING',
  SUCCEEDED = 'SUCCEEDED',
  FAILED = 'FAILED'
}
```

### React Component Structure
```jsx
<App>
  <Header />
  <Router>
    <Route path="/" component={LandingPage} />
    <Route path="/upload" component={ResearchUploader} />
    <Route path="/pipeline/:jobId" component={PipelineTracker} />
    <Route path="/results/:jobId" component={ResultsDashboard} />
    <Route path="/history" component={PipelineHistory} />
  </Router>
  <Footer />
</App>
```

### Key React Hooks
```javascript
// Custom hook for pipeline polling
function usePipelineStatus(jobId) {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    if (!jobId) return;
    
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/pipeline/status/${jobId}`);
        const data = await response.json();
        setStatus(data);
        
        // Stop polling if complete
        if (data.status === 'SUCCEEDED' || data.status === 'FAILED') {
          clearInterval(interval);
        }
      } catch (err) {
        setError(err);
      }
    }, 3000); // Poll every 3 seconds
    
    return () => clearInterval(interval);
  }, [jobId]);
  
  return { status, error };
}
```

### Visual Design System

**Color Palette**:
```css
:root {
  --primary: #0066CC;      /* Trust blue */
  --success: #00AA00;      /* Progress green */
  --warning: #FF9900;      /* Alert orange */
  --danger: #CC0000;       /* Error red */
  --neutral-100: #FFFFFF;  /* Background */
  --neutral-200: #F5F5F5;  /* Cards */
  --neutral-800: #2D2D2D;  /* Text */
}
```

**Component Library**: 
- Use Tailwind CSS or Material-UI for rapid development
- Framer Motion for stage transition animations
- React Query for data fetching and caching
- Recharts for opportunity zone visualizations

### Progressive Enhancement

**Stage 1 - MVP**:
- File upload
- Basic progress tracking (percentage only)
- Simple results page with GitHub link

**Stage 2 - Enhanced**:
- Live stage insights during processing
- Detailed results dashboard
- Pipeline history

**Stage 3 - Advanced**:
- Real-time log streaming
- Comparative analysis between runs
- Team collaboration features
- API access for programmatic use

## API Endpoints Summary

### Core Pipeline Operations
```
POST   /api/research/upload           - Upload research document
POST   /api/pipeline/start            - Start pipeline processing
GET    /api/pipeline/status/{jobId}   - Get current job status
GET    /api/pipeline/logs/{jobId}     - Stream job logs (WebSocket)
```

### Job Management
```
GET    /api/job/{jobId}               - Get job details
GET    /api/job/{jobId}/research      - Get research ID for job
GET    /api/job/{jobId}/artifacts     - Download all artifacts (ZIP)
```

### Research Management
```
GET    /api/research/{researchId}           - Get research details
GET    /api/research/{researchId}/jobs      - List all jobs for research
DELETE /api/research/{researchId}           - Delete research and jobs
```

### Results Access
```
GET    /api/results/{jobId}/summary         - Get executive summary
GET    /api/results/{jobId}/opportunities   - Get opportunity zones
GET    /api/results/{jobId}/ideas          - Get product ideas
GET    /api/results/{jobId}/github         - Get GitHub repo details
```

## Error States & Messaging

### User-Friendly Error Messages
```javascript
const ERROR_MESSAGES = {
  UPLOAD_FAILED: "We couldn't upload your file. Please check your connection and try again.",
  PIPELINE_TIMEOUT: "The analysis is taking longer than expected. We'll email you when it's ready.",
  GITHUB_CREATION_FAILED: "We analyzed your research but couldn't create the GitHub repository. You can download the results instead.",
  QUOTA_EXCEEDED: "You've reached your monthly analysis limit. Upgrade to Pro for unlimited analyses.",
  INVALID_FILE: "Please upload a markdown, PDF, or text file under 10MB."
};
```

### Loading States
```javascript
const STAGE_MESSAGES = {
  'Stage 1': [
    "Analyzing market dynamics...",
    "Extracting key insights...",
    "Identifying pain points..."
  ],
  'Stage 2': [
    "Discovering jobs-to-be-done...",
    "Searching Reddit discussions...",
    "Validating user needs..."
  ],
  'Stage 3': [
    "Mapping opportunity zones...",
    "Calculating market potential...",
    "Clustering pain dimensions..."
  ],
  'Stage 4': [
    "Generating product ideas...",
    "Evaluating viability...",
    "Optimizing portfolio mix..."
  ]
};
```

## Performance Considerations

### Optimization Strategies
1. **Lazy Loading**: Load results components only when needed
2. **Request Debouncing**: Prevent excessive API calls during polling
3. **Caching**: Use React Query to cache job results
4. **Progressive Loading**: Show partial results as they become available
5. **WebSocket Option**: For real-time updates instead of polling

### Responsive Design
- Mobile-first approach
- Breakpoints: 640px (sm), 768px (md), 1024px (lg), 1280px (xl)
- Touch-friendly controls (minimum 44px tap targets)
- Optimized for both portrait and landscape orientations

## Analytics & Monitoring

### Key Metrics to Track
```javascript
// User engagement
track('pipeline_started', {
  researchId: string,
  fileSize: number,
  fileType: string
});

track('pipeline_completed', {
  jobId: string,
  duration: number,
  ideasGenerated: number
});

track('github_repo_viewed', {
  repoUrl: string,
  source: 'dashboard' | 'email' | 'direct'
});

// Performance metrics
track('page_load_time', {
  page: string,
  loadTime: number
});

track('api_response_time', {
  endpoint: string,
  responseTime: number
});
```

## Security Considerations

### Authentication & Authorization
- JWT tokens for API authentication
- Refresh token rotation
- Rate limiting per user/IP
- CORS properly configured

### Data Protection
- Encrypt research documents at rest
- Use HTTPS for all communications
- Sanitize user inputs
- Implement CSP headers

## Testing Strategy

### Unit Tests
- Component rendering tests
- Hook behavior tests
- Utility function tests

### Integration Tests
- API integration tests
- File upload flow
- Pipeline tracking flow
- Results display

### E2E Tests
- Complete user journey from upload to GitHub
- Error recovery scenarios
- Browser compatibility

## Deployment Configuration

### Environment Variables
```env
VITE_API_BASE_URL=https://api.innovation-pipeline.com
VITE_WEBSOCKET_URL=wss://ws.innovation-pipeline.com
VITE_POLLING_INTERVAL=3000
VITE_MAX_FILE_SIZE=10485760
VITE_SENTRY_DSN=your-sentry-dsn
VITE_GA_TRACKING_ID=your-ga-id
```

### Build & Deploy
```bash
# Development
npm run dev

# Production build
npm run build

# Deploy to AWS Amplify
git push origin main  # Auto-deploys

# Or deploy to S3/CloudFront
npm run build
aws s3 sync dist/ s3://your-bucket --delete
aws cloudfront create-invalidation --distribution-id YOUR_ID --paths "/*"
```

## Success Criteria

### MVP Launch
- [ ] Users can upload research and start pipeline
- [ ] Progress tracking shows percentage complete
- [ ] Results page shows GitHub repository link
- [ ] Basic error handling implemented

### V1.0 Release
- [ ] All 6 stages show detailed progress
- [ ] Results dashboard with full insights
- [ ] Pipeline history and management
- [ ] Comprehensive error recovery

### Future Enhancements
- [ ] Team collaboration features
- [ ] Comparison between pipeline runs
- [ ] Custom idea filtering/ranking
- [ ] API access for enterprise users
- [ ] White-label options