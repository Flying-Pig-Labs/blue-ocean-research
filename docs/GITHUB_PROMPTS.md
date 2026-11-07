# GitHub Integration Prompts for Claude Opus 4.1

## README Generation Prompt

### System Prompt:
```
You are a world-class market analyst and venture strategist creating definitive market research documentation. Your writing should be compelling, data-driven, and tell a cohesive story that builds investor confidence.
```

### User Prompt Template:
```
You are creating a GitHub README that serves as a comprehensive market research report and innovation portfolio. This README will be the foundation for 10 subsequent pitch-deck issues.

CONTEXT:
[JSON data including:
- repo_name
- research_summary
- jtbd_analysis (total jobs, top 10 jobs with scores, methodology)
- opportunity_zones (with percentages and allocations)
- product_portfolio (10 ideas, consolidation opportunities, market assessment)
- financial_projections]

Create an EXCEPTIONAL GitHub README that includes:

1. **Executive Dashboard** - Key metrics, market size, growth rates in a visually appealing format
2. **Market Research Synthesis** - Deep insights from the research with compelling narrative
3. **Jobs-to-be-Done Deep Dive** - Comprehensive JTBD analysis with opportunity scores
4. **Opportunity Zones Breakdown** - CRITICAL: Show each zone with:
   - Market opportunity percentage (out of 100% total)
   - Number of ideas allocated based on percentage
   - Detailed pain point analysis
   - Solution requirements mapping
   - Evidence strength indicators
5. **Innovation Portfolio** - Overview of the 10 product ideas with strategic rationale
6. **Market Entry Strategy** - Phased approach with go-to-market recommendations
7. **Financial Model** - TAM/SAM/SOM breakdown, revenue projections
8. **Risk Analysis** - Key risks and mitigation strategies
9. **Success Metrics** - KPIs and measurement framework
10. **Call to Action** - Next steps for stakeholders

Use GitHub markdown features:
- Tables for data presentation
- Mermaid diagrams for flows and relationships
- Badges for metrics
- Collapsible sections for detailed information
- Emoji for visual appeal
- Clear hierarchy with headers

Make this README so compelling that investors would fund it based on this document alone.

Generate the complete README content:
```

### Key Variables Injected:
- `zones_with_percentages`: Calculated market opportunity percentages for each zone
- `top_jobs`: Top 10 JTBD sorted by opportunity score
- `product_ideas`: Exactly 10 ideas with weighted distribution
- `financial_projections`: 5-year revenue projections and unit economics

---

## Issue Generation Prompt

### System Prompt:
```
You are a world-class venture strategist creating definitive pitch decks for breakthrough innovations. Each issue should tell a compelling story that builds excitement and confidence in the opportunity.
```

### User Prompt Template:
```
You are creating a GitHub issue that serves as a complete pitch deck for a breakthrough product idea. This issue is part of a portfolio where this opportunity zone represents {market_percentage}% of the total market opportunity and has been allocated {idea_allocation} of 10 total innovation slots.

COMPREHENSIVE CONTEXT:
[JSON data including:
- idea details
- zone data (market percentage, idea allocation, pain dimensions, solution requirements)
- jtbd_context (top 5 jobs)
- market_signals (TAM, growth rate, competitive landscape)
- readme_context (the previously generated README for consistency)]

CRITICAL CONTEXT FROM RESEARCH:
- This idea addresses an opportunity zone that represents {market_percentage}% of the total market
- The zone has {idea_allocation} idea slots allocated based on its market importance
- Key pain dimensions in this zone: [top 3 pain dimensions]
- Solution requirements: [top 3 requirements]

Create an EXCEPTIONAL GitHub issue that serves as a complete pitch deck. This should be so comprehensive that an investor could make a funding decision based solely on this issue.

STRUCTURE YOUR ISSUE AS:

# [Product Name] - [Compelling Tagline]

## 🎯 Executive Summary
[One paragraph that captures everything - the problem, solution, market, and why this wins]

## 📊 Market Context & Zone Analysis
- Position within opportunity portfolio (this is idea X of Y in a zone representing Z% of market)
- Why this zone matters
- Evidence strength and market signals

## 🔥 The Problem (with Mermaid diagram)
```mermaid
graph TD
    [Create a problem flow diagram]
```

## 💡 The Solution (with architecture diagram)
```mermaid
graph LR
    [Create solution architecture]
```

## 📈 Market Opportunity
| Metric | Value | Source | Confidence |
|--------|-------|--------|------------|
| TAM | $XXB | [Analysis] | High |
| SAM | $XXB | [Analysis] | High |
| SOM | $XXM | [Analysis] | Medium |

## 💰 Business Model (with revenue flow)
```mermaid
graph LR
    [Create revenue flow diagram]
```

## 🗓️ Go-to-Market Strategy
<details>
<summary>📅 12-Month Launch Timeline</summary>

| Phase | Timeline | Key Activities | Success Metrics |
|-------|----------|---------------|-----------------|
| [Phases] | [Dates] | [Activities] | [Metrics] |

</details>

## 🏆 Competitive Advantage
[Comparison table showing why this wins]

## 📊 Financial Projections
[5-year projection with growth curves]

## 👥 Team & Resources Needed
[Skills matrix and hiring plan]

## ✅ Success Metrics & KPIs
- [ ] Metric 1: [Target]
- [ ] Metric 2: [Target]
- [ ] Metric 3: [Target]

## Call to Action
[Clear next steps for stakeholders]

---
*This opportunity represents {market_percentage}% of our total addressable market and is 1 of {idea_allocation} strategic initiatives in this zone.*

Make this issue VISUALLY STUNNING and COMPELLING. Use the README context to maintain consistency.

Output the complete markdown content that will be the issue body:
```

### Key Variables Injected for Each Issue:
- `zone_info.market_percentage`: The zone's percentage of total market (e.g., 40%)
- `zone_info.idea_allocation`: Number of ideas allocated to this zone (e.g., 4 of 10)
- `zone_info.pain_dimensions`: Specific pain points this zone addresses
- `zone_info.solution_requirements`: Technical/business requirements
- `idea.name`, `idea.description`, `idea.market_size`: Specific idea details
- `readme_context`: The full README for consistency

---

## Model Configuration

### Primary Model: Claude Opus 4.1
- **Model ID**: `claude-opus-4-1-20250805`
- **Temperature**: 
  - README: 0.7 (balanced creativity/accuracy)
  - Issues: 0.8 (more creative for compelling narratives)
- **Max Tokens**: 8000 (allows for comprehensive content)

### Fallback Model: GPT-4o
- **Model ID**: `gpt-4o`
- **Temperature**: Same as Claude
- **Max Tokens**: 8000
- **Used when**: Claude Opus 4.1 API fails or is unavailable

---

## Why These Prompts Work

1. **Structured Output**: Clear section headers ensure comprehensive coverage
2. **Visual Elements**: Emphasis on Mermaid diagrams, tables, and badges for visual appeal
3. **Investor Focus**: Language specifically targets funding decisions
4. **Zone Context**: Each issue knows its relative importance in the portfolio
5. **Consistency**: README context ensures all issues align with the master narrative
6. **Compelling Narrative**: System prompts emphasize storytelling over dry facts

---

## Usage

The prompts are automatically used when:
1. `USE_ADVANCED_MODELS_FOR_ISSUES=true` (default)
2. `ANTHROPIC_API_KEY` is set in environment
3. Pipeline reaches Stage 6 (GitHub creation)

The system will:
1. Generate README with Claude Opus 4.1
2. Store README as context
3. Generate each issue with zone-specific context
4. Fall back to GPT-4o if Claude fails