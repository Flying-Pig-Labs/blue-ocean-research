# Claude Code Configuration - Multi-Step LLM App

## 🚀 Project Overview

This is a comprehensive 7-stage Python application suite that transforms raw market research into actionable product innovation portfolios with automatic GitHub repository creation. The pipeline leverages multiple AI models (Claude Sonnet/Opus, GPT-4o, OpenAI o1, Cohere) and search APIs (EXA).

## 📊 Pipeline Stages

1. **Research Analysis** (research_analyzer.py) - Pulls from S3, runs 4 parallel LLM calls
2. **JTBD Research** (jobs_researcher.py) - EXA searches + Claude synthesis
3. **JTBD Clustering** (cluster_jtbd.py) - Cohere embeddings + HDBSCAN + GPT-4o
4. **Value Curve Mapping** (value_curve_mapper.py) - EXA + parallel Claude Opus
5. **Product Idea Generation** (product_idea_generator.py) - OpenAI o1 + Claude Opus
6. **Idea Consolidation** (idea_consolidator.py) - Enrichment and portfolio creation
7. **GitHub Repository Creation** (github_integration.py) - **MANDATORY FINAL STEP**

## 🔧 Recent Major Feature: GitHub Integration

### What Was Implemented
- **GitHub Integration Module** (`github_integration.py`):
  - Automatic repository creation (public/private)
  - Comprehensive README generation from all pipeline data
  - Individual GitHub issues for each product idea
  - Smart labeling system (priority, category, phase)
  - Cross-linking between README and issues

- **Product Generator Updates**:
  - Added `--github` flag for repository creation
  - `--repo-name` option for custom naming
  - `--github-private` flag for private repos
  - Automatic aggregation of data from all pipeline stages

- **Testing Infrastructure**:
  - Comprehensive unit tests (`tests/test_github_integration.py`)
  - End-to-end integration test (`tests/test_integration_e2e.py`)
  - Cleanup script (`cleanup_pipeline.py`)
  - All tests use mocked APIs (no real calls)

### Usage
```bash
# Basic GitHub output
python product_idea_generator.py --github --repo-name "my-innovations"

# Private repository
python product_idea_generator.py --github --repo-name "my-innovations" --github-private

# Full pipeline with GitHub
python product_idea_generator.py --input value_curves.json --github --repo-name "market-analysis-2024"
```

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
export EXA_API_KEY=your_key
export COHERE_API_KEY=your_key

# GitHub Integration
export GITHUB_TOKEN=your_github_personal_access_token

# AWS S3 (for research analyzer)
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1
export S3_BUCKET_NAME=your_bucket
export S3_FILE_KEY=path/to/research.json
```

## 📝 Key Implementation Details

### GitHub Integration Architecture
1. **Data Aggregation**: Loads outputs from all previous pipeline stages
2. **README Generation**: Synthesizes comprehensive documentation including:
   - Executive summary from research analysis
   - Top JTBD opportunities with scores
   - Weighted opportunity zones
   - Product portfolio with issue links
   - Strategic consolidation opportunities
   - Implementation roadmap
   - Financial projections

3. **Issue Creation**: Each product idea becomes an issue with:
   - Full product description
   - Mapped JTBDs with opportunity scores
   - Market analysis and sizing
   - Feasibility scores
   - Business case details
   - Implementation priority/phase

4. **Label System**:
   - Priority: high/medium/low (based on market opportunity score)
   - Category: ai-powered, mobile, integration, analytics, security
   - Phase: phase-1 through phase-4 (based on feasibility/effort matrix)
   - Special: quick-win, needs-validation

### Testing Strategy
- **Unit Tests**: Mock all external dependencies (GitHub API, file system)
- **Integration Test**: Runs full pipeline with mocked APIs, verifies outputs
- **Cleanup**: Automated cleanup of all generated files
- **No PyGithub Dependency**: Tests mock the github module to avoid installation issues

## 🚨 Important Notes

1. **GitHub is NOT Optional**: Stage 7 (GitHub repository creation) is the mandatory final step
2. **Token Security**: Never commit GitHub tokens - use environment variables
3. **Rate Limiting**: Built-in delays between issue creation (0.5s)
4. **Error Handling**: Gracefully handles existing repositories
5. **Data Dependencies**: GitHub integration requires outputs from all previous stages

## 🔄 Next Steps / Future Enhancements

- [ ] Milestone creation for implementation phases
- [ ] GitHub Projects integration
- [ ] Wiki page generation
- [ ] Bulk issue management
- [ ] Repository templates
- [ ] Webhook integration for CI/CD

## 📚 Documentation

- Main README has been updated with complete GitHub integration docs
- Created `docs/GITHUB_INTEGRATION.md` with technical details
- Testing section added to README
- Pipeline diagrams updated to show GitHub as final step

## 🐛 Known Issues / Considerations

1. **PyGithub Installation**: On macOS, may need virtual environment due to system Python restrictions
2. **Test Mocking**: Tests mock the github module to avoid dependency issues
3. **File Path Dependencies**: GitHub integration expects specific output filenames from previous stages
4. **API Rate Limits**: GitHub API has rate limits - built-in delays help but may need adjustment for large idea sets

## 🎯 Quick Commands Reference

```bash
# Run full pipeline with GitHub output
python research_analyzer.py && \
python jobs_researcher.py && \
python cluster_jtbd.py pain_points.txt && \
python value_curve_mapper.py opportunity_zones.json && \
python product_idea_generator.py --github --repo-name "innovation-portfolio-$(date +%Y%m%d)"

# Test everything
python -m pytest tests/ -v

# Clean up
python cleanup_pipeline.py --force
```

---

This configuration captures the current state of the GitHub integration feature and provides context for future development work on the multi-step LLM application.