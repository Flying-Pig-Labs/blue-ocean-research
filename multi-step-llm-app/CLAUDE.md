# Claude Code Configuration - Multi-Step LLM App

## 🎯 Project Mission
This is a sophisticated 7-stage market research pipeline that transforms raw research into GitHub repositories with actionable product ideas. The pipeline uses weighted distribution to allocate exactly 10 high-quality ideas across opportunity zones based on market potential.

## 🚨 ABSOLUTELY CRITICAL: NEVER WATER DOWN REQUIREMENTS

**NEVER EVER EVER EVER:**
- Remove required dependencies to make things "simpler"
- Stub out functionality to avoid errors
- Insert randomizers or fake data instead of real implementations
- Drop fields or features randomly just to make the application not error
- Try to trick the user into thinking something works when it doesn't
- Reduce specifications to make something appear to be working
- Comment out functionality that's "problematic"
- Skip implementing required features because they're "difficult"

**THIS IS UNETHICAL BEHAVIOR**. The goal is to make the FULL application work with ALL requirements intact, not to create a facade that appears to work but is missing critical functionality.

If something doesn't fit (like Lambda layer size limits), propose REAL solutions (container images, multiple layers, etc.), don't just delete the requirements!

## 🚨 CRITICAL RULE: ONE SCRIPT ONLY

**THERE IS ONLY ONE SCRIPT FOR RUNNING THE PIPELINE: `run_pipeline.py`**
- This script runs all 7 stages end-to-end
- **DO NOT MODIFY THIS SCRIPT** for deployment - wrap it instead
- With `--use-cache` flag: Uses cached files (skips GitHub creation)
- Without cache: Runs fresh and creates GitHub repo
- **NEVER CREATE ADDITIONAL PIPELINE SCRIPTS**
- **DO NOT DELETE OR RENAME THIS SCRIPT**

## 🏗️ Architecture Overview

This is a comprehensive 7-stage Python application suite that transforms raw market research into actionable product innovation portfolios with automatic GitHub repository creation. The pipeline leverages multiple AI models (Claude Sonnet/Opus, GPT-4o, OpenAI o1, GPT-5, Cohere) and Reddit's PRAW API.

### Key Architectural Decisions
1. **Weighted Distribution System**: Zones get ideas proportional to market opportunity (e.g., 40% zone = 4 of 10 total ideas)
2. **Quality Over Quantity**: Generate 10 ideas per zone internally, select top N based on zone weight
3. **GPT-5 for Premium Content**: README generation (1 call) + pitch-deck issues (10 calls)
4. **No Exa Dependency**: PRAW-based Reddit discovery for authentic discussions
5. **Mandatory GitHub Creation**: Stage 7 is NOT optional - it's the culmination of the pipeline

## 📊 Pipeline Stages (PRAW-Based Flow, No Exa)

1. **Research Analysis** (`research_analyzer.py`)
   - Pulls from S3, runs 4 parallel LLM calls
   - Output: `analysis_results.md`

2. **JTBD Extraction & Reddit Discovery** (`jobs_to_reddit.py`)
   - PRAW-based Reddit API searches
   - Extracts 20-30 JTBDs, finds 500+ discussions
   - Output: `jtbds_*.txt`, `reddit_discussions_*.csv`

3. **Opportunity Zone Discovery** (`opportunity_zone_analyzer.py`)
   - 8-dimensional pain analysis
   - Weighted zones with market percentages
   - Output: `opportunity_zones.json`

4. **Product Idea Generation** (`product_idea_generator.py`)
   - OpenAI o1 for ERRC strategy
   - Claude Opus for 10 ideas per zone
   - **Weighted selection**: Zone% × 10 total ideas
   - Output: `product_ideas.json` (exactly 10 ideas)

5. **Idea Consolidation** (`idea_consolidator.py`)
   - Enrichment and portfolio creation
   - Output: `final_innovation_portfolio.json`

6. **GitHub Repository Creation** (`github_integration.py`)
   - **MANDATORY FINAL STEP**
   - GPT-5: 1 README + 10 issue calls
   - Creates public/private repo with smart labels

## 🚀 AWS Batch Deployment

### Infrastructure Components
- **CDK Stack**: `infrastructure/cdk_batch_pipeline.py`
- **Container**: Fargate with 4 vCPUs, 16GB RAM
- **Wrapper**: `batch_wrapper.py` handles S3 I/O
- **API Gateway**: POST /submit, GET /logs/{researchId}
- **DynamoDB**: Job tracking and research mapping

### Deployment Commands
```bash
# Bootstrap CDK (first time)
make cdk-bootstrap

# Build and push Docker image
make docker

# Deploy CDK stack
make cdk-deploy

# Complete deployment
make deploy
```

### Critical: Pipeline Script Unchanged
- `run_pipeline.py` runs WITHOUT modifications in Batch
- `batch_wrapper.py` acts as adapter for S3/DynamoDB
- GitHub creation happens normally (not skipped!)

## 🔧 Recent Major Features

### GPT-5 Integration (December 2024)
- **Comprehensive README**: Single GPT-5 call generates executive-quality documentation
- **Pitch-Deck Issues**: 10 GPT-5 calls create investor-ready issue descriptions
- **Context Chaining**: README serves as context for issue generation
- **Fallback Handling**: Graceful degradation to GPT-4o if needed

### Weighted Distribution System
- **Market-Based Allocation**: Each zone gets % of 10 total ideas
- **Internal Generation**: 10 ideas created per zone
- **Smart Selection**: Top N selected based on zone weight
- **Quality Assurance**: Ensures exactly 10 high-quality ideas

### Enhanced Pipeline Reliability
- **Wildcard Pattern Support**: Fixed file detection for `jtbds_*.txt`, `reddit_*.csv`
- **Cache Control**: `--use-cache` flag prevents unwanted GitHub creation
- **Error Recovery**: Comprehensive fallback mechanisms
- **Logging**: Detailed progress tracking

## 🧪 Testing

### Run Tests
```bash
# All unit tests
python -m pytest tests/ -v

# GitHub integration tests specifically
python -m pytest tests/test_github_integration.py -v

# End-to-end integration test
python -m pytest tests/test_integration_e2e.py -v

# With coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Cleanup After Pipeline
```bash
# Interactive cleanup
python cleanup_pipeline.py

# Dry run
python cleanup_pipeline.py --dry-run

# Force cleanup
python cleanup_pipeline.py --force
```

## 🔑 Required Environment Variables

```bash
# Core AI APIs
export ANTHROPIC_API_KEY=your_key
export OPENAI_API_KEY=your_key
export COHERE_API_KEY=your_key
# Note: EXA_API_KEY no longer needed with PRAW-based flow!

# GitHub Integration
export GITHUB_TOKEN=your_github_personal_access_token

# Reddit API (optional - has defaults in code)
export REDDIT_CLIENT_ID=your_id
export REDDIT_CLIENT_SECRET=your_secret
export REDDIT_USER_AGENT=your_agent

# AWS S3 (for research analyzer)
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1
export S3_BUCKET_NAME=your_bucket
export S3_FILE_KEY=path/to/research.json
```

## 💡 Key Implementation Insights

### Weighted Distribution Algorithm
```python
# Each zone gets a percentage of 10 total ideas
TOTAL_TARGET_IDEAS = 10
for zone in zones:
    zone_percentage = zone['market_opportunity_score'] / 100
    ideas_to_select = round(zone_percentage * TOTAL_TARGET_IDEAS)
    # Generate 10 internally, select top N
    selected_ideas = zone_ideas[:ideas_to_select]
```

### GPT-5 Integration Pattern
```python
# First: Generate comprehensive README
readme_content = generate_readme_with_gpt5(all_data)

# Then: Use README as context for issues
for idea in ideas:
    issue_content = generate_issue_with_gpt5(idea, readme_context)
```

### File Pattern Handling
```python
# Use glob for timestamp-based files
import glob
jtbd_files = glob.glob('jtbds_*.txt')
reddit_files = glob.glob('reddit_discussions_*.csv')
```

## 🎯 Quick Commands Reference

```bash
# Run full pipeline with GitHub output
make run-fresh  # Fresh data generation
make run        # With caching (skips GitHub)

# Run specific stages
make stage1     # Research analysis
make stage2     # JTBD + Reddit
make stage3     # Opportunity zones
make stage4     # Product ideas
make stage5     # Consolidation
make stage6     # GitHub creation

# AWS Batch deployment
make docker     # Build and push image
make deploy     # Deploy everything

# Testing
python -m pytest tests/ -v
python -m pytest tests/test_github_integration.py -v

# Cleanup
python cleanup_pipeline.py --force
```

## 📋 Testing Checklist

### Before Committing
- [ ] Run unit tests: `python -m pytest tests/ -v`
- [ ] Test pipeline with cache: `make run`
- [ ] Verify output files exist
- [ ] Check logs for errors

### Integration Testing
- [ ] Full pipeline run: `make run-fresh`
- [ ] Verify GitHub repo creation
- [ ] Check all 10 issues created
- [ ] Validate zone weighting (sum = 10)

### AWS Batch Testing
- [ ] Docker build: `make docker-build`
- [ ] Local container test: `make docker-test`
- [ ] CDK diff: `make cdk-diff`
- [ ] Deploy and monitor: `make batch-logs`

## 🔄 Common Issues & Solutions

### Issue: Pipeline creating 35+ ideas instead of 10
**Solution**: Check `TOTAL_TARGET_IDEAS = 10` constant and weighted distribution logic

### Issue: GPT-5 calls failing
**Solution**: Ensure `reasoning_effort="high"` parameter and proper fallback handling

### Issue: GitHub repo created with cached data
**Solution**: Stage 6 checks `use_cache` flag and skips if True

### Issue: CDK deployment fails
**Solution**: Use stable batch constructs from aws-cdk-lib (not alpha)

### Issue: Missing files in pipeline
**Solution**: Use glob patterns for timestamp-based files

## 📚 Documentation Structure

- `README.md` - Comprehensive pipeline overview and usage
- `ARCHITECTURE.md` - System design and technical architecture
- `BATCH_DEPLOYMENT.md` - AWS Batch deployment guide
- `CLAUDE.md` - This file, development guidelines
- `infrastructure/README.md` - CDK infrastructure details
- `docs/` - Additional documentation

## 🚨 Important Notes

1. **GitHub is NOT Optional**: Stage 7 (GitHub repository creation) is the mandatory final step
2. **Token Security**: Never commit GitHub tokens - use environment variables
3. **Rate Limiting**: Built-in delays between API calls
4. **Error Handling**: Gracefully handles existing repositories
5. **Data Dependencies**: GitHub integration requires outputs from all previous stages
6. **10-Idea Limit**: NEVER change this - it's a core requirement
7. **Pipeline Script**: NEVER modify `run_pipeline.py` directly

## 🔄 Next Steps / Future Enhancements

- [ ] Milestone creation for implementation phases
- [ ] GitHub Projects integration
- [ ] Wiki page generation
- [ ] Bulk issue management
- [ ] Repository templates
- [ ] Webhook integration for CI/CD
- [ ] Step Functions orchestration
- [ ] Real-time progress updates

---

**Last Updated**: December 2024  
**Maintainer Notes**: This pipeline is production-ready. The weighted distribution system is critical - never change the 10-idea limit. GitHub creation is mandatory, not optional. The pipeline script (`run_pipeline.py`) must remain unchanged for deployment compatibility.