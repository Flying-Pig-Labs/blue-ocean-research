# Claude Opus 4.1 Prompts for GitHub Integration

## Overview
The GitHub integration now uses **Claude Opus 4.1** (`claude-opus-4-1-20250805`) for generating both README and issue content, with GPT-4o as a fallback.

## 1. README Generation Prompt

### Model Configuration
- **Model**: Claude Opus 4.1 (`claude-opus-4-1-20250805`)
- **Temperature**: 0.7
- **Max Tokens**: 8000
- **Fallback**: GPT-4o

### System Prompt
```
You are a world-class market analyst and venture strategist creating definitive market research documentation. Your writing should be compelling, data-driven, and tell a cohesive story that builds investor confidence.
```

### User Prompt Structure
The prompt includes comprehensive context with:
- Research summary and executive insights
- JTBD analysis with top 10 jobs sorted by opportunity score
- Weighted opportunity zones with market percentages
- Product portfolio of exactly 10 ideas
- Financial projections and market assessment

The prompt requests an exceptional README with:
1. Executive Dashboard with key metrics
2. Market Research Synthesis with compelling narrative
3. Jobs-to-be-Done Deep Dive with scores
4. Opportunity Zones showing:
   - Market opportunity percentage
   - Number of ideas allocated
   - Pain point analysis
   - Solution requirements
5. Innovation Portfolio overview
6. Market Entry Strategy
7. Financial Model (TAM/SAM/SOM)
8. Risk Analysis
9. Success Metrics
10. Call to Action

### Visual Elements Requested
- Tables for data presentation
- Mermaid diagrams for flows
- Badges for metrics
- Collapsible sections
- Emoji for visual appeal
- Clear header hierarchy

## 2. Issue Generation Prompt (Per Product Idea)

### Model Configuration
- **Model**: Claude Opus 4.1 (`claude-opus-4-1-20250805`)
- **Temperature**: 0.8 (higher for more creative narratives)
- **Max Tokens**: 8000
- **Fallback**: GPT-4o

### System Prompt
```
You are a world-class venture strategist creating definitive pitch decks for breakthrough innovations. Each issue should tell a compelling story that builds excitement and confidence in the opportunity.
```

### User Prompt Structure
Each issue prompt includes:
- Complete idea details and specifications
- Zone context showing market percentage (e.g., "40% of total market")
- Number of ideas allocated to zone (e.g., "4 of 10 ideas")
- Pain dimensions and solution requirements
- Top 5 JTBD being addressed
- Market signals (TAM, growth rate, competitive landscape)
- README context for consistency

### Required Issue Structure
```markdown
# 🚀 [Product Name] - [Compelling Tagline]

## 🎯 Executive Summary
[Problem, solution, market, and why this wins]

## 📊 Market Context & Zone Analysis
- Position in portfolio (e.g., "idea 3 of 4 in 40% zone")
- Why this zone matters
- Evidence strength

## 🔥 The Problem
[Mermaid problem flow diagram]

## 💡 The Solution
[Mermaid solution architecture]

## 📈 Market Opportunity
[TAM/SAM/SOM table with confidence levels]

## 💰 Business Model
[Revenue flow diagram]

## 🗓️ Go-to-Market Strategy
[12-month timeline in collapsible section]

## 🏆 Competitive Advantage
[Comparison table]

## 📊 Financial Projections
[5-year growth curves]

## 👥 Team & Resources
[Skills matrix and hiring plan]

## ✅ Success Metrics
[Checkboxes with KPI targets]

## 🚀 Call to Action
[Next steps for stakeholders]
```

## 3. Key Differences from Previous Version

### What Changed:
1. **Model**: Now uses Claude Opus 4.1 instead of Sonnet/GPT-5
2. **Narrative Focus**: Emphasizes compelling storytelling
3. **Visual Elements**: Heavy use of Mermaid diagrams and tables
4. **Zone Context**: Each issue knows its relative market importance
5. **Consistency**: README serves as context for all issues

### Why Opus 4.1:
- Superior narrative quality
- Better understanding of complex market dynamics
- More compelling pitch deck creation
- Consistent tone across all documents
- Better visual element integration

## 4. Example Context Variables

### For README:
```json
{
  "repo_name": "ai-workflow-automation",
  "research_summary": {...},
  "jtbd_analysis": {
    "total_jobs": 25,
    "top_jobs": [...],
    "methodology": "..."
  },
  "opportunity_zones": [
    {
      "name": "Automation Zone",
      "market_opportunity_percentage": 40.5,
      "idea_allocation": 4,
      "pain_dimensions": {...}
    }
  ],
  "product_portfolio": {
    "total_ideas": 10,
    "ideas": [...]
  }
}
```

### For Each Issue:
```json
{
  "idea": {
    "name": "AI Workflow Assistant",
    "description": "...",
    "market_size": "$5B"
  },
  "zone": {
    "market_percentage": 40.5,
    "idea_allocation": 4,
    "pain_dimensions": {...}
  },
  "jtbd_context": [...],
  "readme_context": "[full README for consistency]"
}
```

## 5. Quality Improvements Expected

With Claude Opus 4.1, you should see:
- **More compelling narratives** that tell a story
- **Better investor-focused language** 
- **Richer visual presentations** with proper diagrams
- **Consistent tone** across all documents
- **Zone-aware content** that understands relative importance
- **Pitch-deck quality** issues that could stand alone
- **Data-driven insights** woven into narratives

## 6. Environment Variables

To use these prompts:
```bash
export USE_ADVANCED_MODELS_FOR_ISSUES=true  # Default
export ANTHROPIC_API_KEY=your_key_here
```

## 7. Fallback Behavior

If Claude Opus 4.1 fails:
1. Logs warning with error details
2. Falls back to GPT-4o with same prompts
3. If GPT-4o fails, uses enhanced manual generation
4. All failures are logged but don't break the pipeline