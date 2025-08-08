# Multi-Step LLM Pipeline Architecture

## System Overview

The Multi-Step LLM Pipeline is a sophisticated market research and product innovation system that transforms raw research documents into actionable GitHub repositories with prioritized product ideas. The system leverages multiple AI models, real-world data sources, and advanced clustering techniques to identify market opportunities and generate viable product concepts.

## Core Architecture Principles

### 1. Pipeline Architecture
- **Sequential Stages**: Each stage depends on outputs from previous stages
- **Data Transformation**: Progressive refinement from raw text to structured portfolios
- **Modular Design**: Each stage is independently executable for testing/debugging

### 2. Parallel Processing
- **Concurrent API Calls**: Multiple LLM calls execute in parallel where data dependencies allow
- **ThreadPoolExecutor**: Python's concurrent.futures for managing parallel operations
- **Optimal Batching**: Balance between parallelism and API rate limits

### 3. Weighted Distribution System
- **Market-Based Allocation**: Opportunity zones receive product ideas proportional to their market potential
- **10-Idea Budget**: Exactly 10 high-quality ideas distributed across zones
- **Quality Over Quantity**: Internal generation of 10 ideas per zone, then selection of top N based on zone weight

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         INPUT LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│ • S3 Research Documents                                          │
│ • Market Analysis Reports                                        │
│ • User Research Data                                             │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                    ANALYSIS LAYER (Stage 1-2)                    │
├─────────────────────────────────────────────────────────────────┤
│ Research Analyzer:                                               │
│ • 4 Parallel LLM Calls (2 Sonnet, 2 Opus)                      │
│ • Structured Insight Extraction                                  │
│                                                                   │
│ Jobs-to-Reddit:                                                  │
│ • JTBD Extraction via Claude                                     │
│ • Reddit API (PRAW) for Real Discussions                        │
│ • 500+ Thread Analysis                                           │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                  DISCOVERY LAYER (Stage 3)                       │
├─────────────────────────────────────────────────────────────────┤
│ Opportunity Zone Analyzer:                                       │
│ • 8-Dimensional Pain Analysis                                    │
│ • JTBD Vectorization & Clustering                               │
│ • Market Opportunity Scoring                                     │
│ • Zone Weight Calculation (% of 100%)                           │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                  GENERATION LAYER (Stage 4-5)                    │
├─────────────────────────────────────────────────────────────────┤
│ Product Idea Generator:                                          │
│ • OpenAI o1: ERRC Strategy Grid                                 │
│ • Claude Opus: 10 Ideas per Zone                                │
│ • Weighted Selection: Zone% × 10 Total Ideas                    │
│                                                                   │
│ Idea Consolidator:                                               │
│ • Enrichment & Detailing                                        │
│ • Portfolio Assembly                                             │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                    OUTPUT LAYER (Stage 6-7)                      │
├─────────────────────────────────────────────────────────────────┤
│ GitHub Integration:                                              │
│ • GPT-5: Comprehensive README (1 call)                          │
│ • GPT-5: Pitch-Deck Issues (10 calls)                          │
│ • Repository Creation & Population                               │
│ • Smart Labeling & Prioritization                               │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Research Analyzer (`research_analyzer.py`)
**Purpose**: Transform unstructured research into structured insights

**Key Components**:
- **S3 Integration**: Boto3 client for document retrieval
- **Parallel LLM Orchestration**: ThreadPoolExecutor for concurrent API calls
- **Model Strategy**:
  - Claude Sonnet: Industry verticals, user personas (faster, structured extraction)
  - Claude Opus: Pain points, solution types (deeper analysis)

**Output**: `analysis_results.md` - Comprehensive markdown report

### 2. Jobs-to-Reddit Pipeline (`jobs_to_reddit.py`)
**Purpose**: Extract JTBDs and find real-world evidence

**Key Components**:
- **JTBD Extraction**: Claude-powered identification of 20-30 specific jobs
- **Query Translation**: Convert JTBDs to authentic Reddit search terms
- **PRAW Integration**: Reddit API for searching across multiple subreddits
- **Evidence Mapping**: Link discussions back to source JTBDs

**Output**: 
- `jtbds_[timestamp].txt` - Extracted Jobs-to-be-Done
- `reddit_discussions_[timestamp].csv` - Real user discussions

### 3. Opportunity Zone Analyzer (`opportunity_zone_analyzer.py`)
**Purpose**: Identify strategic innovation areas through pain convergence

**Key Components**:
- **Pain Dimension Framework**: 8-dimensional scoring system
- **Vectorization Engine**: Aggregate pain scores into JTBD vectors
- **Clustering Algorithm**: Group JTBDs by shared pain patterns
- **Weighting System**: Calculate market opportunity percentages

**Pain Dimensions**:
1. Timing coordination issues
2. Financial stress points
3. Communication gaps
4. Process complexity
5. Trust and verification issues
6. Technology gaps
7. Decision anxiety
8. Market dynamics

**Output**: `opportunity_zones.json` - Weighted zones with requirements

### 4. Product Idea Generator (`product_idea_generator.py`)
**Purpose**: Generate and filter product ideas based on zone weights

**Key Components**:
- **ERRC Strategy Generator**: OpenAI o1 for strategic framework
- **Idea Generation**: Claude Opus for creative product concepts
- **Viability Scoring**: Multi-dimensional evaluation
- **Weighted Distribution**:
  ```python
  zone_idea_count = round(zone_weight * TOTAL_TARGET_IDEAS)
  selected_ideas = top_n_ideas[:zone_idea_count]
  ```

**Distribution Algorithm**:
1. Generate 10 ideas per zone internally
2. Score and rank all ideas
3. Allocate final 10 spots based on zone percentages
4. Select top N ideas from each zone

**Output**: `product_ideas.json` - Exactly 10 filtered ideas

### 5. Idea Consolidator (`idea_consolidator.py`)
**Purpose**: Transform ideas into comprehensive portfolio

**Key Components**:
- **Enrichment Engine**: Add implementation details, risks, growth potential
- **ERRC Integration**: Connect ideas to strategic framework
- **Market Justification**: Trace back to original pain points
- **Portfolio Assembly**: Create cohesive innovation strategy

**Output**: 
- `final_innovation_portfolio.json` - Complete portfolio
- `final_innovation_portfolio_summary.md` - Executive summary

### 6. GitHub Integration (`github_integration.py`)
**Purpose**: Create actionable GitHub repository with all insights

**Key Components**:
- **GPT-5 Integration**: 
  - 1 call for comprehensive README generation
  - 10 calls for pitch-deck style issues
- **PyGithub**: Repository and issue creation
- **Data Aggregation**: Pull from all pipeline outputs
- **Smart Labeling**: Priority, category, phase assignments

**Label System**:
- **Priority**: Based on market opportunity score (high/medium/low)
- **Category**: ai-powered, mobile, integration, analytics, security
- **Phase**: Implementation phases 1-4
- **Special**: quick-win, needs-validation

**Output**: Complete GitHub repository with README and issues

## Deployment Architecture

### AWS Batch Deployment

```
┌──────────────┐     ┌──────────────────┐     ┌────────────────┐
│  Frontend    │────▶│  API Gateway     │────▶│    Lambda      │
│              │     │  (9hv22ga3uh)    │     │ (CORS-enabled) │
└──────────────┘     └──────────────────┘     └────────────────┘
                                                       │
                                                       ▼
                                                ┌──────────────┐
                                                │  AWS Batch   │
                                                │  (Fargate)   │
                                                └──────────────┘
                                                       │
                                         ┌─────────────┴──────────────┐
                                         ▼                            ▼
                                   ┌──────────┐              ┌──────────────────┐
                                   │    S3    │              │    DynamoDB      │
                                   └──────────┘              │ ResearchReports  │
                                                             └──────────────────┘
```

**Production Endpoints**:
- API Gateway: `https://9hv22ga3uh.execute-api.us-east-1.amazonaws.com/prod/`
- Submit Job: `POST /submit` (expects `{"researchId": "reportId-from-ResearchReports"}`)
- Monitor Logs: `GET /logs/{researchId}`

### Container Architecture
- **Base Image**: `jupyter/scipy-notebook:python-3.11`
- **Entrypoint**: `batch_wrapper.py` (handles S3 I/O, then calls `run_pipeline.py`)
- **Resources**: 4 vCPUs, 16GB RAM, 50GB ephemeral storage
- **Timeout**: 2 hours per job

### Infrastructure as Code (CDK)
- **Stack**: `MultiStepLLMBatchStack`
- **Components**:
  - VPC with private subnets for Batch
  - ECR repository: `multi-step-llm-pipeline`
  - Batch compute environment (Fargate)
  - DynamoDB tables:
    - `ResearchReports`: Frontend-managed (key: `reportId`, contains `s3ReportKey`)
    - `PipelineBatchJobs`: Backend job tracking
  - Lambda functions with CORS headers for frontend integration
  - API Gateway REST API with CORS configuration

## API Architecture

### LLM Model Selection Strategy

| Model | Use Case | Rationale |
|-------|----------|-----------|
| Claude Sonnet | Structured extraction | Fast, cost-effective for defined schemas |
| Claude Opus | Deep analysis, creativity | Superior reasoning and creative generation |
| GPT-4o | Labeling, categorization | Excellent at classification tasks |
| OpenAI o1 | Strategic reasoning | Best for complex analytical frameworks |
| GPT-5 | Premium content generation | Highest quality for customer-facing content |
| Cohere Embed v3 | Vectorization | State-of-the-art embeddings for clustering |

### API Call Patterns

**Parallel Pattern** (Research Analyzer):
```python
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(call_sonnet, prompt1),
        executor.submit(call_sonnet, prompt2),
        executor.submit(call_opus, prompt3),
        executor.submit(call_opus, prompt4)
    ]
    results = [f.result() for f in futures]
```

**Sequential-then-Parallel** (Value Curves):
```python
# Must complete first
search_results = exa_search(query)

# Then parallel
with ThreadPoolExecutor(max_workers=2) as executor:
    norms = executor.submit(analyze_norms, search_results)
    gaps = executor.submit(analyze_gaps, search_results)
```

**Weighted Distribution** (Product Ideas):
```python
TOTAL_TARGET_IDEAS = 10
for zone in zones:
    zone_percentage = zone['market_opportunity_score'] / 100
    ideas_to_select = round(zone_percentage * TOTAL_TARGET_IDEAS)
    # Generate 10 internally, select top N based on weight
```

## Performance Characteristics

### Timing Profile
- **Stage 1**: 30-45 seconds (parallel LLM calls)
- **Stage 2**: 60-90 seconds (Reddit API searches)
- **Stage 3**: 45-60 seconds (clustering + scoring)
- **Stage 4**: 3-4 minutes (idea generation per zone)
- **Stage 5**: 30-45 seconds (consolidation)
- **Stage 6**: 60-90 seconds (GitHub creation with GPT-5)
- **Total**: 10-15 minutes end-to-end

### API Call Distribution
- **Minimum**: ~50 calls (3 zones)
- **Typical**: ~70 calls (5 zones)
- **Maximum**: ~90 calls (8 zones)

### Cost Optimization
- Use cheaper models (Sonnet, GPT-4o) for structured tasks
- Reserve premium models (Opus, o1, GPT-5) for complex reasoning
- Parallel execution reduces wall-clock time without increasing cost
- Caching system for development/testing

## Error Handling & Resilience

### Rate Limit Management
- Exponential backoff with jitter
- Model fallback chains (e.g., Claude → OpenAI)
- Request queuing for burst protection

### Data Validation
- JSON schema validation at each stage
- Graceful degradation on missing data
- Comprehensive error logging

### Recovery Mechanisms
- Stage-level checkpointing
- Partial result handling
- Automatic retry with backoff

## Security Considerations

### Secret Management
- AWS Secrets Manager for API keys
- Environment variable injection in containers
- No hardcoded credentials

### Network Security
- Batch runs in private VPC subnets
- S3 bucket encryption at rest
- DynamoDB encryption enabled

### Access Control
- IAM roles with least privilege
- Separate execution and task roles
- API Gateway authentication ready

## Monitoring & Observability

### Logging
- CloudWatch Logs for all components
- Structured logging with correlation IDs
- Log retention: 30 days

### Metrics
- API call counts and latencies
- Pipeline stage completion times
- Error rates by component

### Alerting Hooks
- Job failure notifications
- API quota warnings
- Cost threshold alerts

## Future Architecture Considerations

### Scalability Enhancements
- Step Functions for orchestration
- SQS for job queuing
- Lambda for lightweight stages

### Performance Optimizations
- Redis caching layer
- Batch prediction APIs
- GPU-accelerated clustering

### Feature Expansions
- WebSocket for real-time updates
- Multi-tenant isolation
- Webhook integrations

## Development Workflow

### Local Development
```bash
# Run with test fixtures
make run

# Run specific stage
make stage4

# Run with verbose output
make run-verbose
```

### Testing
```bash
# Unit tests
python -m pytest tests/ -v

# Integration tests
python -m pytest tests/test_integration_e2e.py -v

# With coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Deployment
```bash
# Build and push Docker image
make docker

# Deploy CDK stack
make cdk-deploy

# Complete deployment
make deploy
```

## Conclusion

The Multi-Step LLM Pipeline architecture represents a sophisticated approach to market research and product innovation. By combining multiple AI models, real-world data sources, and advanced algorithms, it transforms unstructured research into actionable development plans. The weighted distribution system ensures resources are allocated proportionally to market opportunities, while the modular pipeline architecture enables continuous improvement and testing of individual components.