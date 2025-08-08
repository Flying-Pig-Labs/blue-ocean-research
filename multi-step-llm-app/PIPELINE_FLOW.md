# PRAW-Based Pipeline Flow (No Exa Dependency)

## Overview
This document describes the new streamlined pipeline flow that uses PRAW (Python Reddit API Wrapper) for authentic user data discovery, completely eliminating the dependency on the Exa API.

## Pipeline Stages

### Stage 1: Research Analysis
- **Module**: `research_analyzer.py`
- **Input**: Research document (JSON from S3 or local file)
- **Output**: `analysis_results.md`
- **Process**: 
  - 4 parallel Claude API calls for comprehensive analysis
  - Extracts verticals, personas, pain points, and solution types

### Stage 2: JTBD Extraction & Reddit Discovery (PRAW-based)
- **Module**: `jobs_to_reddit.py`
- **Input**: `analysis_results.md`
- **Outputs**: 
  - `jtbds_*.txt` - Extracted Jobs-to-be-Done statements
  - `reddit_discussions_*.csv` - Authentic Reddit discussions
- **Process**:
  1. Claude extracts 20-30 JTBDs from analysis
  2. Translates each JTBD to Reddit search queries
  3. PRAW searches targeted subreddits for real discussions
  4. No Exa API required!

### Stage 3: Advanced Opportunity Zone Discovery
- **Module**: `opportunity_zone_analyzer.py`
- **Inputs**: 
  - `jtbds_*.txt` from Stage 2
  - `reddit_discussions_*.csv` from Stage 2
- **Output**: `opportunity_zones.json`
- **Process**:
  - Analyzes pain dimensions across JTBDs and Reddit data
  - Creates weighted opportunity zones
  - Uses clustering and semantic analysis

### Stage 4: Product Idea Generation
- **Module**: `product_idea_generator.py`
- **Input**: `opportunity_zones.json`
- **Outputs**: 
  - `product_ideas.json`
  - `product_ideas_report.md`
- **Process**:
  - OpenAI o1 for ERRC analysis
  - Claude Opus for idea generation
  - Viability scoring and filtering

### Stage 5: Idea Consolidation
- **Module**: `idea_consolidator.py`
- **Input**: `product_ideas.json`
- **Outputs**: 
  - `final_innovation_portfolio.json`
  - `final_innovation_portfolio_summary.md`
- **Process**:
  - Enriches product ideas with market justification
  - Adds implementation plans and risk assessment
  - Creates final portfolio

### Stage 6: GitHub Repository Creation
- **Module**: `product_idea_generator.py --github`
- **Inputs**: All previous outputs
- **Output**: GitHub repository with:
  - Comprehensive README
  - Individual issues for each product idea
  - Smart labeling and prioritization

## Key Advantages of PRAW-Based Flow

1. **No Exa API Dependency**: Eliminates expensive API subscription
2. **Authentic User Data**: Direct access to Reddit discussions
3. **Better Context**: Real user frustrations and pain points
4. **Cost Effective**: Only uses Reddit API (free tier available)
5. **More Reliable**: No rate limiting issues from Exa

## Archived Modules (No Longer Used)

The following modules have been moved to the `archive/` directory:
- `jobs_researcher.py` - Old Exa-based JTBD research
- `cluster_jtbd.py` - Basic clustering without Reddit data
- `value_curve_mapper.py` - Exa-based competitive analysis
- Lambda functions for old pipeline stages

## Running the Pipeline

```bash
# Full pipeline (headless mode) - always generates fresh data
python run_pipeline.py

# Use cached files if they exist (faster for testing)
python run_pipeline.py --use-cache

# Interactive mode
python run_pipeline.py --interactive

# Verbose mode (shows LLM prompts/responses)
python run_pipeline.py --verbose

# Custom input
python run_pipeline.py --input my_research.json

# Combine flags as needed
python run_pipeline.py --verbose --use-cache
```

### Cache Behavior

By default, the pipeline **always generates fresh data** for each run. This ensures:
- Fresh Reddit searches with current discussions
- New JTBD extraction based on latest analysis
- Updated opportunity zones

Use `--use-cache` only when:
- Testing downstream stages without regenerating upstream data
- Debugging specific stages
- Working with a known good dataset

When NOT using cache, the pipeline will:
1. Delete old timestamped files (jtbds_*.txt, reddit_discussions_*.csv)
2. Generate completely fresh data
3. Create new timestamped output files

## Required Environment Variables

```bash
# Core AI APIs (still needed)
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
COHERE_API_KEY=your_key

# GitHub (for final stage)
GITHUB_TOKEN=your_token

# Reddit API (optional - has defaults)
REDDIT_CLIENT_ID=your_id
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USER_AGENT=your_agent

# NOT NEEDED ANYMORE:
# EXA_API_KEY - Removed!
```

## Pipeline Flow Diagram

```
Research Analysis
        ↓
JTBD Extraction (Claude)
        ↓
Reddit Discovery (PRAW)
        ↓
Opportunity Zones (Weighted)
        ↓
Product Ideas (o1 + Opus)
        ↓
Consolidation
        ↓
GitHub Repository
```

## Migration Notes

If you have existing code using the old Exa-based flow:
1. All old modules are preserved in `archive/` directory
2. The new flow produces compatible outputs
3. `opportunity_zones.json` format remains the same
4. Product generation stages unchanged

## Performance

- Total pipeline time: ~15-20 minutes
- Reddit search: ~3-5 minutes for 20-30 JTBDs
- No Exa API rate limiting delays
- Parallel processing where possible

## Credential Management

The pipeline loads AWS secrets **once** at startup via `run_pipeline.py`:
- All API keys are loaded from AWS Secrets Manager at the beginning
- Individual modules use environment variables set by the main script
- No duplicate credential loading across modules
- If running modules standalone (for testing), uncomment their credential loading code

This approach:
- Reduces AWS Secrets Manager API calls
- Speeds up pipeline execution
- Ensures consistent credentials across all stages
- Simplifies debugging (credentials load in one place)