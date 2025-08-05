# Pipeline Prompt Improvements Analysis

## Overview
Working backwards from the GitHub output, here are the specific prompt improvements needed at each stage to fix the issues identified in the final report.

## Stage 7: GitHub Integration (fix_github_integration.py)
**Current Issue**: Missing JTBD data shows "Top 0 Opportunity Jobs Identified"

**Root Cause**: The GitHub integration expects JTBD data in a specific format that doesn't match what's actually produced.

**Fix**:
```python
# In load_pipeline_data() method, improve JTBD parsing:
if os.path.exists("jtbd_research.md"):
    # Need to properly extract structured JTBD data with:
    # - job_id
    # - job_statement (actual "When I am..." format)
    # - importance (1-10)
    # - satisfaction (1-10)
    # - opportunity_score (calculated)
    # - frequency
    # - pain_points array
```

## Stage 5: Product Idea Generator (product_idea_generator.py)

### Issue 1: Generic Product Descriptions
**Current Prompt** (line 177-190):
```
Generate exactly 10 innovative product ideas that embody this ERRC strategy. For each idea:
1. Product Name (catchy and memorable)
2. Core Value Proposition (one sentence)
...
```

**Improved Prompt**:
```python
prompt = f"""Based on this ERRC Grid analysis for the '{zone_name}' opportunity zone:

{errc_grid}

Generate exactly 10 SPECIFIC product ideas. For each:

1. Product Name (specific, not generic)
2. One-Line Pitch: Complete this - "We help [specific user] achieve [specific outcome] by [unique method]"
3. Core Features (3-5 SPECIFIC features with technical details):
   - Feature name + how it works technically
   - Example: "AI Property Match Engine - Uses GPT-4 embeddings of user preferences cross-referenced with MLS data"
4. Target Customer: Be specific (e.g., "First-time homebuyers aged 25-35 in urban markets making $50-80k")
5. Market Size: Estimate TAM/SAM with reasoning
6. Competitive Analysis: Name 2-3 actual competitors and how this differs
7. Technical Requirements: Specific tech stack, integrations, data sources
8. Go-to-Market: Specific channels, partnerships, pricing model
9. Success Metrics: 3 specific KPIs with target numbers
10. Innovation Score (1-10) with justification

IMPORTANT: No generic descriptions. Each idea must have concrete, implementable details."""
```

### Issue 2: Missing Viability Details
**Current Prompt** (line 221-235):
```
For each idea, assess:
1. Technical Feasibility (1-10): How achievable with current/near-term technology?
...
```

**Improved Prompt**:
```python
prompt = f"""Evaluate these {len(ideas)} product ideas with SPECIFIC analysis:

{ideas_summary}

For each idea provide:

1. Technical Feasibility (1-10):
   - Required technologies (list specific tools/frameworks)
   - Technical risks and mitigation
   - Development timeline with milestones

2. Market Validation (1-10):
   - Evidence of demand (cite specific data/trends)
   - Early adopter profile
   - MVP validation approach

3. Business Model (1-10):
   - Revenue model with pricing tiers
   - Unit economics estimate
   - Path to profitability timeline

4. Competitive Moat (1-10):
   - Specific barriers to entry
   - Network effects potential
   - IP/patent opportunities

5. Resource Requirements:
   - Team composition (roles needed)
   - Funding needed for MVP/Scale
   - Key partnerships required

Output as structured JSON for parsing."""
```

## Stage 2: JTBD Researcher (jobs_researcher.py)

### Issue: No Structured JTBD Output
**Current Approach**: Extracts patterns but doesn't create proper JTBD statements

**New Method to Add**:
```python
def _synthesize_jtbd_with_claude(self, jobs: List[Dict[str, str]], elements: Dict[str, List[str]]) -> str:
    prompt = """Create a structured JTBD analysis table with EXACTLY this format:

For each job, provide:
- JOB-XXX: Sequential ID
- Job Statement: "When I am [situation], I want to [motivation], so I can [outcome]"
- Frequency: Daily/Weekly/Monthly/Quarterly
- Importance: Score 1-10 with reasoning
- Current Satisfaction: Score 1-10 with evidence
- Pain Points: 3-5 specific frustrations
- Current Solutions: What people use now
- Opportunity Score: Importance + max(Importance - Satisfaction, 0)

Create 15-20 jobs based on the evidence.

Output in this exact format:
JOB-001:
Job Statement: "When I am..."
Frequency: Daily
Importance: 8 (critical for business success)
Satisfaction: 3 (current tools are clunky)
Pain Points:
- Takes 2 hours to complete
- Requires switching between 5 tools
- No mobile access
Current Solutions: Excel spreadsheets, manual processes
Opportunity Score: 13

IMPORTANT: Use actual evidence from the search results, not generic statements."""
```

## Stage 4: Value Curve Mapper (value_curve_mapper.py)

### Issue: Missing Competitive Intelligence
**Current**: Shows competitive landscape URLs but no actual analysis

**Improvement Needed**:
```python
def analyze_competitive_landscape(self, zone_name: str, search_results: List[Dict]) -> Dict:
    prompt = """Analyze the competitive landscape with SPECIFIC details:

1. Market Leaders (name actual companies):
   - Company name, market share, key features
   - Pricing model and tiers
   - Strengths and weaknesses

2. Emerging Players:
   - Specific startups/new entrants
   - Their unique value propositions
   - Funding and traction

3. Market Gaps:
   - Specific unserved segments
   - Feature gaps in current solutions
   - Price points not covered

4. Disruption Opportunities:
   - Specific strategies to differentiate
   - Underserved customer segments
   - Technology advantages available

Output structured data with company names, not generic descriptions."""
```

## Stage 3: Cluster JTBD (Already Fixed)
The clustering fix you implemented is good, but should output more structured data about each cluster.

## Stage 1: Research Analyzer
Should output more structured data that's easier for downstream stages to parse.

## Implementation Priority

1. **Fix JTBD Researcher (Stage 2)** - Most critical gap
   - Add proper JTBD statement generation
   - Include importance/satisfaction scoring
   - Output structured JSON alongside markdown

2. **Enhance Product Idea Generator (Stage 5)**
   - Add specific details to prompts
   - Include competitive analysis
   - Add market sizing

3. **Fix GitHub Integration (Stage 7)**
   - Properly parse all pipeline outputs
   - Handle missing data gracefully
   - Create richer issue content

4. **Improve Value Curve Mapper (Stage 4)**
   - Add actual competitive analysis
   - Include market data
   - Quantify opportunities

## Quick Win: Prompt Templates

Create a `prompts/` directory with improved prompt templates:
- `jtbd_synthesis_prompt.txt`
- `product_ideation_prompt.txt`
- `competitive_analysis_prompt.txt`
- `market_sizing_prompt.txt`

This allows easy iteration without code changes.