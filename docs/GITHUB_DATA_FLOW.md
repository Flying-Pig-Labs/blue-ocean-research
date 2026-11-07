# GitHub Integration Data Flow - Variable Sources

## Overview
The GitHub integration receives data from the previous 5 stages of the pipeline. Here's exactly where each variable comes from:

## Data Flow Architecture

```
Stage 1: Research Analysis → analysis_results.md
Stage 2: JTBD + Reddit → jtbds_*.txt + reddit_discussions_*.csv
Stage 3: Opportunity Zones → opportunity_zones.json
Stage 4: Product Ideas → product_ideas.json
Stage 5: Consolidation → final_innovation_portfolio.json
Stage 6: GitHub Integration (uses all above files)
```

## Variable Sources in `generate_readme_with_gpt5()`

### 1. **zones_with_percentages** (Line 277)
```python
zones_with_percentages = self._calculate_zone_percentages(zones_data)
```

**Source**: `opportunity_zones.json` (from Stage 3: opportunity_zone_analyzer.py)

**Data Structure**:
```json
{
  "clustered_zones": {
    "zone_1": {
      "name": "Workflow Automation",
      "market_opportunity_score": 0.85,  // Used for percentage calculation
      "pain_dimensions": {...},
      "solution_requirements": [...],
      "market_size": "$15B",
      "evidence_strength": {...}
    },
    "zone_2": {...}
  }
}
```

**Calculation** (Lines 387-422):
- Sums all zone scores to get total
- Each zone percentage = (zone_score / total_score) * 100
- Idea allocation = round(10 * percentage / 100)
- Sorted by percentage descending

### 2. **top_jobs** (Lines 285-289)
```python
"top_jobs": sorted(
    jtbd_data.get("jtbd_data", {}).get("jobs_list", []),
    key=lambda x: x.get("opportunity_score", 0),
    reverse=True
)[:10]
```

**Source**: `jtbds_*.txt` (from Stage 2: jobs_to_reddit.py)

**Data Structure**:
```json
{
  "jtbd_data": {
    "jobs_list": [
      {
        "job_id": "JOB001",
        "job_statement": "When I want to automate repetitive tasks",
        "opportunity_score": 8.5,  // Used for sorting
        "importance": 9,
        "satisfaction": 3,
        "frequency": "Daily",
        "pain_points": [...]
      }
    ],
    "methodology": "Customer interviews and contextual inquiry"
  }
}
```

### 3. **product_ideas** (Line 295)
```python
"ideas": ideas_data.get("product_ideas", [])[:10]  # Top 10
```

**Source**: `product_ideas.json` (from Stage 4: product_idea_generator.py)

**Data Structure**:
```json
{
  "product_ideas": [
    {
      "idea_id": "IDEA001",
      "name": "AI Workflow Assistant",
      "description": "Intelligent automation platform",
      "zone_name": "Workflow Automation",  // Links to opportunity zone
      "market_size": "$5B",
      "target_market": "Enterprise",
      "estimated_development_time": "6-9 months",
      "estimated_cost": "$1-2M",
      "key_features": [...],
      "competitive_advantage": "...",
      "viability_score": 8.2,
      "innovation_score": 7.5,
      "market_opportunity": 8.8
    }
  ]
}
```

**Note**: The pipeline generates exactly 10 ideas through weighted distribution:
- Each zone gets ideas proportional to its market percentage
- E.g., 40% zone gets 4 ideas, 30% zone gets 3 ideas, etc.

### 4. **financial_projections** (Line 299)
```python
"financial_projections": ideas_data.get("viability_analysis", {}).get("financial_projections", {})
```

**Source**: `product_ideas.json` (from Stage 4: product_idea_generator.py)

**Data Structure**:
```json
{
  "viability_analysis": {
    "financial_projections": {
      "total_development_cost": "$5-10M",
      "time_to_market": "12-18 months",
      "break_even_timeline": "24 months",
      "projected_5_year_revenue": "$250M",
      "funding_requirements": "$15M Series A",
      "unit_economics": {
        "cac": "$1500",
        "ltv": "$45000",
        "ltv_cac_ratio": 30,
        "gross_margin": "85%"
      }
    },
    "market_assessment": {
      "total_addressable_market": "$50B",
      "serviceable_addressable_market": "$15B",
      "serviceable_obtainable_market": "$500M",
      "market_growth_rate": "25% CAGR"
    }
  }
}
```

### 5. **research_summary** (Line 282)
```python
"research_summary": research_analysis
```

**Source**: `analysis_results.md` (from Stage 1: research_analyzer.py)

**Data Structure** (Markdown file parsed as dict):
```json
{
  "executive_summary": "Market research shows significant opportunity...",
  "key_findings": [...],
  "market_trends": [...],
  "competitive_landscape": {...},
  "recommendations": [...]
}
```

### 6. **consolidation_opportunities** (Line 296)
```python
"consolidation_opportunities": ideas_data.get("consolidation_analysis", {}).get("consolidation_opportunities", [])
```

**Source**: `final_innovation_portfolio.json` (from Stage 5: idea_consolidator.py)

**Data Structure**:
```json
{
  "consolidation_analysis": {
    "consolidation_opportunities": [
      {
        "consolidated_idea": "Unified AI Platform",
        "combines": ["IDEA001", "IDEA003", "IDEA005"],
        "market_potential": "$20B",
        "rationale": "Combining these creates a comprehensive platform",
        "complexity": "high",
        "synergies": [...]
      }
    ],
    "recommended_sequence": [
      {
        "phase": "Phase 1 - Quick Wins",
        "ideas": ["IDEA002", "IDEA004"],
        "rationale": "Low complexity, high impact"
      }
    ]
  }
}
```

## Function Call Chain

1. **Main Pipeline** (`run_pipeline.py`, Lines 692-705):
```python
run_module(
    module_name="github_integration",
    inputs={
        "analysis": "analysis_results.md",         # From Stage 1
        "jtbds": jtbd_file,                       # From Stage 2 (wildcard)
        "reddit": reddit_file,                     # From Stage 2 (wildcard)
        "opportunity_zones": "opportunity_zones.json",  # From Stage 3
        "product_ideas": "product_ideas.json",     # From Stage 4
        "portfolio": "final_innovation_portfolio.json"  # From Stage 5
    }
)
```

2. **GitHub Module Entry** (`github_integration.py`):
```python
def create_github_output(
    research_analysis: Dict,  # Loaded from analysis_results.md
    jtbd_data: Dict,          # Loaded from jtbds_*.txt
    zones_data: Dict,         # Loaded from opportunity_zones.json
    ideas_data: Dict,         # Loaded from product_ideas.json + portfolio.json
    ...
)
```

3. **README Generation** (`generate_readme_with_gpt5`):
- Receives all 4 data dictionaries
- Calculates zone percentages from zones_data
- Extracts top 10 jobs from jtbd_data
- Gets exactly 10 product ideas from ideas_data
- Pulls financial projections from viability_analysis
- Combines everything into context dict
- Sends to Claude Opus 4.1 with comprehensive prompt

## Data Loading Pattern

The pipeline loads files in this sequence:

```python
# Stage 6 entry point
if __name__ == "__main__":
    # Load all output files from previous stages
    with open("analysis_results.md", "r") as f:
        research_analysis = parse_markdown(f.read())
    
    with open(glob.glob("jtbds_*.txt")[0], "r") as f:
        jtbd_data = json.loads(f.read())
    
    with open("opportunity_zones.json", "r") as f:
        zones_data = json.load(f)
    
    with open("product_ideas.json", "r") as f:
        ideas_data = json.load(f)
    
    with open("final_innovation_portfolio.json", "r") as f:
        portfolio = json.load(f)
        # Merge portfolio data into ideas_data
        ideas_data.update(portfolio)
    
    # Call GitHub integration
    create_github_output(
        research_analysis=research_analysis,
        jtbd_data=jtbd_data,
        zones_data=zones_data,
        ideas_data=ideas_data
    )
```

## Key Points

1. **All data comes from previous pipeline stages** - GitHub integration doesn't generate new data, it synthesizes existing outputs

2. **Weighted distribution is pre-calculated** - The 10 ideas are already distributed across zones by Stage 4

3. **Zone percentages are calculated on-the-fly** - Based on market_opportunity_scores from Stage 3

4. **Financial projections come from Stage 4** - The viability analysis is done during idea generation

5. **Consolidation opportunities from Stage 5** - Portfolio optimization happens before GitHub

6. **Everything feeds into Claude Opus 4.1** - All this context creates the comprehensive README and issues