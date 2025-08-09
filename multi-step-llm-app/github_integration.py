#!/usr/bin/env python3
"""
GitHub Integration Module - Innovation Portfolio Publishing

This module handles the final stage of the innovation pipeline, transforming 
analysis results into a comprehensive GitHub repository with documentation 
and trackable issues for each product idea.

Key Responsibilities:
- Creates public or private GitHub repositories in specified organization
- Generates comprehensive README with all research insights and findings
- Creates individual GitHub issues for each product idea with full context
- Applies intelligent labeling system (priority, category, phase)
- Links issues back to source JTBDs and opportunity zones

Repository Structure Created:
- README.md: Executive summary, opportunity zones, product portfolio
- Issues: One per product idea with full description and metadata
- Labels: Priority (high/medium/low), Category (ai/mobile/etc), Phase (1-4)

Authentication:
- Uses GitHub Personal Access Token (PAT) from environment
- Supports both organization and personal repositories
- Handles rate limiting with built-in delays

Creative Naming:
- Can generate creative repository names using GPT-3.5-turbo
- Falls back to timestamp-based names if OpenAI unavailable

Note: The main entry point is create_github_project() which orchestrates
the entire repository creation process.
"""

import os
import json
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
from github import Github, GithubException
import time
import random
import openai
import requests


logger = logging.getLogger(__name__)


class GitHubIntegration:
    """Handles GitHub repository creation and management."""

    def __init__(self, github_token: Optional[str] = None, organization: str = "ocean-studio-repos"):
        """Initialize GitHub integration with authentication."""
        self.token = github_token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError(
                "GitHub token is required. Set GITHUB_TOKEN environment variable."
            )

        self.github = Github(self.token)
        self.user = self.github.get_user()
        self.organization_name = organization
        
        try:
            self.organization = self.github.get_organization(organization)
            logger.info(f"Authenticated as GitHub user: {self.user.login}, targeting organization: {organization}")
        except Exception as e:
            logger.warning(f"Could not access organization '{organization}': {e}")
            logger.info(f"Falling back to user account: {self.user.login}")
            self.organization = None
        
        # Initialize OpenAI for creative name generation (using GPT-3.5-turbo for cost efficiency)
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
        
        # Initialize Perplexity API key for deep research
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        if self.perplexity_api_key:
            logger.info("✅ Perplexity API key loaded for deep research validation")

    def check_repo_exists(self, repo_name: str) -> bool:
        """Check if a repository with the given name already exists."""
        try:
            if self.organization:
                self.organization.get_repo(repo_name)
            else:
                self.user.get_repo(repo_name)
            return True
        except:
            return False

    def generate_creative_repo_name(
        self, 
        research_context: Dict[str, Any], 
        max_attempts: int = 5
    ) -> str:
        """
        Generate a creative, unique repository name based on the research content.
        
        Args:
            research_context: Dictionary containing research data (market, ideas, themes, etc.)
            max_attempts: Maximum number of attempts to generate a unique name
            
        Returns:
            A unique, creative repository name
        """
        if not self.openai_api_key:
            # Fallback to timestamp-based name if no OpenAI key
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            return f"innovation-portfolio-{timestamp}"
        
        # Extract key themes from research
        market_domain = research_context.get("market_domain", "innovation")
        key_themes = research_context.get("key_themes", [])
        top_ideas = research_context.get("top_ideas", [])
        industry = research_context.get("industry", "")
        innovation_focus = research_context.get("innovation_focus", "")
        
        # Build context for the LLM
        context_summary = f"""
        Market Domain: {market_domain}
        Industry: {industry}
        Key Themes: {', '.join(key_themes[:3]) if key_themes else 'innovation, technology, solutions'}
        Innovation Focus: {innovation_focus}
        Top Product Ideas: {', '.join([idea.get('name', '') for idea in top_ideas[:3]]) if top_ideas else 'various innovations'}
        """
        
        for attempt in range(max_attempts):
            try:
                # Use GPT-3.5-turbo with HIGH creativity
                prompt = f"""You are a WILDLY creative Silicon Valley startup namer who comes up with BOLD, MEMORABLE, and EXCITING project codenames!

Research context:
{context_summary}

Generate an ULTRA-CREATIVE GitHub repository name that:
- Sounds like a hot startup or secret project codename
- Makes people curious and excited
- Could be a unicorn company name
- Feels innovative, bold, and slightly edgy
- Combines unexpected words in clever ways
- Has energy and momentum

FORBIDDEN boring words: project, repository, research, insights, analytics, data, report, study, market

Think like you're naming the next billion-dollar startup! Be BOLD! Be MEMORABLE!

Examples of the vibe we want:
- neon-phoenix-labs
- quantum-rush-protocol  
- atlas-ignite-engine
- vortex-prime-systems
- nexus-thunder-forge
- crimson-rocket-works
- plasma-shift-dynamics
- titan-pulse-collective
- nova-strike-platform
- hydra-boost-network

Make it {3 + (attempt * 2)}-{15 + (attempt * 3)} characters long.
Variation seed: {datetime.now().microsecond} + attempt {attempt + 1}

OUTPUT ONLY THE NAME (lowercase with hyphens):"""

                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an EXTREMELY creative Silicon Valley startup namer. Be BOLD, WILD, and MEMORABLE! Think like you're naming a secret Google X project or the next unicorn startup. NO BORING NAMES!"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=1.4,  # VERY high temperature for maximum creativity
                    max_tokens=50,
                    presence_penalty=0.8,  # Encourage unique words
                    frequency_penalty=0.8   # Avoid repetition
                )
                
                repo_name = response.choices[0].message.content.strip().lower()
                
                # Clean up the name (ensure URL-safe)
                repo_name = ''.join(c if c.isalnum() or c == '-' else '-' for c in repo_name)
                repo_name = repo_name.strip('-')[:40]  # Max 40 chars
                
                # Check if repo exists
                if not self.check_repo_exists(repo_name):
                    logger.info(f"Generated unique repository name: {repo_name}")
                    return repo_name
                else:
                    logger.info(f"Repository name {repo_name} already exists, trying again...")
                    
            except Exception as e:
                logger.warning(f"Error generating creative name: {e}")
                
        # Final fallback with guaranteed uniqueness
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        fallback_name = f"{market_domain[:20]}-innovation-{timestamp}".lower()
        fallback_name = ''.join(c if c.isalnum() or c == '-' else '-' for c in fallback_name)
        return fallback_name.strip('-')

    def create_repository(
        self, repo_name: str, description: str, private: bool = False
    ) -> Any:
        """Create a new GitHub repository."""
        try:
            # Use organization if available, otherwise use user account
            if self.organization:
                repo = self.organization.create_repo(
                    name=repo_name,
                    description=description,
                    private=private,
                    has_issues=True,
                    has_wiki=False,
                    has_downloads=False,
                    auto_init=False,
                )
                logger.info(f"Created repository in organization: {repo.full_name}")
            else:
                repo = self.user.create_repo(
                    name=repo_name,
                    description=description,
                    private=private,
                    has_issues=True,
                    has_wiki=False,
                    has_downloads=False,
                    auto_init=False,
                )
                logger.info(f"Created repository in user account: {repo.full_name}")
            return repo
        except GithubException as e:
            if e.status == 422 and "already exists" in str(e):
                logger.warning(
                    f"Repository {repo_name} already exists, using existing repo"
                )
                # Try to get existing repo from organization or user
                if self.organization:
                    return self.organization.get_repo(repo_name)
                else:
                    return self.user.get_repo(repo_name)
            else:
                raise

    def generate_readme_content(
        self,
        research_analysis: Dict,
        jtbd_data: Dict,
        zones_data: Dict,
        ideas_data: Dict,
        repo_name: str,
    ) -> str:
        """Generate comprehensive README content from analysis results.
        
        This uses Claude Opus or GPT-4o to create a killer README that serves as the foundation
        for all subsequent issue generation.
        """
        
        return self.generate_readme_with_gpt5(
            research_analysis, jtbd_data, zones_data, ideas_data, repo_name
        )
    
    
    def generate_readme_with_gpt5(
        self,
        research_analysis: Dict,
        jtbd_data: Dict,
        zones_data: Dict,
        ideas_data: Dict,
        repo_name: str,
    ) -> str:
        """Use Claude Opus 4.1 or GPT-5 to generate a comprehensive, pitch-deck quality README."""
        
        # Calculate opportunity zone percentages and idea allocations
        zones_with_percentages = self._calculate_zone_percentages(zones_data)
        
        # Build comprehensive context for ALL zones
        context = self._build_comprehensive_context(
            research_analysis, jtbd_data, zones_data, ideas_data, zones_with_percentages
        )
        
        # Load the FULL original research report if available
        original_research_report = ""
        if os.path.exists("analysis_results.md"):
            with open("analysis_results.md", "r") as f:
                original_research_report = f.read()
                logger.info("Loaded full original research report from analysis_results.md")
        else:
            logger.warning("analysis_results.md not found - using limited research context")
        
        # Extract the original business context from research analysis
        original_business = research_analysis.get("company_name", "the target business")
        business_domain = research_analysis.get("domain", research_analysis.get("industry", ""))
        business_description = research_analysis.get("company_description", "")
        
        prompt = f"""You are creating the definitive research report for a comprehensive market analysis that discovered multiple opportunity zones. Present ALL findings systematically.

================================================================================
ORIGINAL RESEARCH REPORT - THIS IS YOUR PRIMARY CONTEXT
================================================================================
{original_research_report}
================================================================================

CRITICAL CONTEXT - ORIGINAL BUSINESS TARGET:
Company/Business: {original_business}
Domain/Industry: {business_domain}
Description: {business_description}

IMPORTANT: The above research report contains ALL the original insights, pain points, industry verticals, personas, and specific details about {original_business}. 
You MUST use this original research to ground all your analysis and recommendations.

All opportunity zones and product ideas MUST be framed in the context of {original_business} operating in {business_domain}.

COMPLETE RESEARCH CONTEXT:
{json.dumps(context, indent=2)}

Create a comprehensive README with this EXACT structure:

# 🎯 Market Research & Innovation Portfolio for {original_business}

## 🏢 Business Context
Clearly state:
- **Target Business**: {original_business}
- **Industry/Domain**: {business_domain}
- **Strategic Focus**: How this research helps {original_business} navigate market opportunities and challenges

## 1️⃣ Research Overview
Write a narrative explaining what this research was about IN THE CONTEXT OF {original_business}. Include:
- Why {original_business} in {business_domain} commissioned this research
- The scope and methodology relevant to their business
- The key strategic questions for {original_business}
- Why this research matters now for their competitive position

## 2️⃣ Discovery: Pain Points, Solutions & Personas
From the initial research analysis, present:

### 🔴 Pain Points Discovered
List the major pain points identified, using bullet points with severity indicators

### 💡 Solution Types Identified  
Categorize the types of solutions that could address these pains

### 👥 Key Personas
Describe the user personas discovered and their specific needs

## 3️⃣ Research Summary & Analysis
Provide a comprehensive summary of the research findings:
- Key market trends identified
- Technology enablers present
- Competitive landscape gaps
- Market readiness indicators

## 4️⃣ Jobs To Be Done Analysis
Explain the JTBD methodology briefly, then present:

### ⭐ High-Opportunity Jobs (Score > 10)
List the most attractive JTBDs with their scores:
```
Example format:
• "When I [situation], I want to [motivation], so I can [outcome]" 
  📊 Importance: X | Satisfaction: Y | Opportunity: Z
```

### 📊 JTBD Distribution
Show how the {context['metrics']['total_jtbds']} jobs break down by opportunity level

## 5️⃣ Zeitgeist Clustering & Opportunity Zones

### 🔬 Clustering Methodology
Briefly explain how zeitgeist clustering was performed using:
- 8-dimensional pain analysis
- Reddit discussion patterns
- JTBD grouping algorithms

### 🗺️ Opportunity Zones Discovered

Create a visual hierarchy of ALL {len(zones_with_percentages)} zones:

```mermaid
pie title Market Opportunity Distribution
{self._generate_mermaid_pie_chart(zones_with_percentages)}
```

Now detail EACH zone comprehensively:

{self._generate_zone_details_template(zones_with_percentages)}

## 6️⃣ ERRC Grid Analysis

### 📐 What is ERRC?
The Eliminate-Reduce-Raise-Create grid is a strategic framework that identifies:
- **Eliminate**: Industry factors that should be eliminated
- **Reduce**: Factors that should be reduced below industry standard
- **Raise**: Factors that should be raised above industry standard
- **Create**: New factors the industry has never offered

### 📊 ERRC Results by Zone

{self._generate_errc_grid_template(zones_data, ideas_data)}

## 7️⃣ Product Ideas Generated

### 🚀 Strategic Innovation Portfolio for {original_business}

For each opportunity zone, ideas are positioned based on their strategic relevance to {original_business}'s current market position and growth objectives.

{self._generate_ideas_by_zone_template(zones_data, ideas_data)}

## 8️⃣ Final Selection: Top 10 Strategic Initiatives for {original_business}

### ⭐ Selected for Implementation

The following 10 ideas were selected based on weighted market opportunity and strategic relevance to {original_business}:

{self._generate_selected_ideas_list(ideas_data)}

---

## 🎯 Strategic Implications for {original_business}

### Immediate Actions
Based on this research, {original_business} should:
1. **Defend Market Position**: Address competitive threats that pose disruption risk
2. **Optimize Operations**: Implement efficiency improvements for quick gains
3. **Expand Strategically**: Launch new ventures in highest-opportunity zones

### Competitive Positioning
- How {original_business} can leverage its strengths in {business_domain}
- Key partnerships to consider
- Technology investments required
- Market positioning adjustments needed

## 📈 Implementation Roadmap for {original_business}

```mermaid
gantt
    title Strategic Implementation Timeline for {original_business}
    dateFormat  YYYY-MM-DD
    section Defense (RED)
    Threat Mitigation    :2024-01-01, 60d
    section Efficiency (BLACK)
    Operational Improvements :2024-02-01, 120d
    section Growth (WHITE)
    New Venture Launch :2024-04-01, 180d
```

## 📊 Success Metrics for {original_business}

| Metric | Target | Timeline |
|--------|--------|----------|
| Market Penetration | 5% of TAM | 12 months |
| User Acquisition | 10,000 users | 6 months |
| Revenue | $1M ARR | 18 months |
| NPS Score | > 50 | 9 months |

---

## 🏁 Executive Summary for {original_business}

This comprehensive market research for {original_business} in {business_domain} analyzed {context['validation_evidence']['reddit_discussions_analyzed']} Reddit discussions, extracted {context['metrics']['total_jtbds']} jobs-to-be-done, identified {len(zones_with_percentages)} opportunity zones, and generated {context['metrics']['total_ideas_generated']} product ideas.

**Key Takeaways for {original_business}:**
- **Competitive threats to monitor**: [Summarize key disruption risks]
- **Efficiency opportunities identified**: [Summarize operational improvements]  
- **Growth ventures to pursue**: [Summarize expansion opportunities]

The research provides a strategic roadmap for {original_business} to maintain competitive advantage in {business_domain} while identifying new growth opportunities.

---

*Research conducted specifically for {original_business} operating in {business_domain}*

Generate this README with:
- Clear connection to {original_business} throughout
- Strategic framing (RED/BLACK/WHITE team perspectives)
- Actual data from the context
- Mermaid diagrams where specified
- All zones covered with business relevance explained
- Every idea positioned relative to {original_business}'s strategic needs

CRITICAL: Every section must explicitly relate back to {original_business} and their strategic position in {business_domain}. Don't let the analysis drift into generic market opportunities - keep it grounded in the original business context."""
        
        # Use Claude Opus 4.1 for superior narrative quality
        import anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            client = anthropic.Anthropic(api_key=anthropic_key)
            response = client.messages.create(
                model="claude-opus-4-1-20250805",
                max_tokens=8000,
                temperature=0.7,
                system="You are a market research analyst creating a comprehensive report. Cover ALL opportunity zones equally. Use strategic emojis for visual hierarchy. Include actual data, scores, and metrics from the provided context. Create Mermaid diagrams as specified.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            readme_content = response.content[0].text
            logger.info("✅ Generated comprehensive README with Claude Opus 4.1")
            
            # Store the README for use as context in issue generation
            self.gpt5_readme_context = readme_content
            
            return readme_content
        else:
            # Use GPT-4o if no Anthropic key
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a market research analyst creating a comprehensive report. Cover ALL opportunity zones equally. Use strategic emojis for visual hierarchy. Include actual data, scores, and metrics from the provided context. Create Mermaid diagrams as specified."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=8000
            )
            
            readme_content = response.choices[0].message.content
            logger.info("✅ Generated comprehensive README with GPT-4o")
            
            # Store the README for use as context in issue generation
            self.gpt5_readme_context = readme_content
            
            return readme_content
    
    def _calculate_zone_percentages(self, zones_data: Dict) -> List[Dict]:
        """Calculate market opportunity percentages for each zone."""
        zones = zones_data.get("clustered_zones", {})
        
        # Calculate total market opportunity score
        total_score = sum(
            zone.get("market_opportunity_score", 0.5) 
            for zone in zones.values()
        )
        
        zones_with_percentages = []
        for zone_key, zone_data in zones.items():
            score = zone_data.get("market_opportunity_score", 0.5)
            percentage = (score / total_score * 100) if total_score > 0 else 0
            
            # Calculate idea allocation (out of 10 total)
            idea_allocation = max(1, round(10 * percentage / 100)) if percentage > 10 else 0
            
            zones_with_percentages.append({
                "zone_id": zone_key,
                "name": zone_data.get("name", "Opportunity Zone"),
                "market_opportunity_percentage": round(percentage, 1),
                "idea_allocation": idea_allocation,
                "score": score,
                "pain_dimensions": zone_data.get("pain_dimensions", {}),
                "solution_requirements": zone_data.get("solution_requirements", []),
                "key_themes": zone_data.get("key_themes", []),
                "jtbds_addressed": zone_data.get("jtbds_addressed", []),
                "market_size": zone_data.get("market_size", "N/A"),
                "evidence_strength": zone_data.get("evidence_strength", {})
            })
        
        # Sort by percentage (highest first)
        zones_with_percentages.sort(key=lambda x: x["market_opportunity_percentage"], reverse=True)
        
        return zones_with_percentages
    
    def _build_comprehensive_context(self, research_analysis, jtbd_data, zones_data, ideas_data, zones_with_percentages):
        """Build comprehensive context covering ALL zones and findings."""
        
        # Extract actual metrics from the data
        jobs_list = jtbd_data.get("jtbd_data", {}).get("jobs_list", [])
        top_jobs = sorted(jobs_list, key=lambda x: x.get("opportunity_score", 0), reverse=True)[:10]
        
        # Calculate actual underserved metrics
        avg_importance = sum(j.get("importance", 0) for j in jobs_list) / len(jobs_list) if jobs_list else 0
        avg_satisfaction = sum(j.get("satisfaction", 0) for j in jobs_list) / len(jobs_list) if jobs_list else 0
        avg_opportunity = sum(j.get("opportunity_score", 0) for j in jobs_list) / len(jobs_list) if jobs_list else 0
        
        # Get ALL zones with full details
        all_zones_data = []
        for zone_info in zones_with_percentages:
            zone_id = zone_info["zone_id"]
            zone_raw = zones_data.get("clustered_zones", {}).get(zone_id, {})
            
            # Get ERRC data for this zone
            errc_data = None
            if "errc_grids" in ideas_data:
                for errc in ideas_data["errc_grids"]:
                    if errc.get("zone_name") == zone_info["name"]:
                        errc_data = errc
                        break
            
            # Get ideas for this zone
            zone_ideas = []
            selected_ideas = []
            for idea in ideas_data.get("product_ideas", []):
                if idea.get("zone_name") == zone_info["name"]:
                    zone_ideas.append(idea)
                    # Check if this idea is in the final 10
                    if idea in ideas_data.get("product_ideas", [])[:10]:
                        selected_ideas.append(idea)
            
            all_zones_data.append({
                "zone_info": zone_info,
                "raw_data": zone_raw,
                "errc_grid": errc_data,
                "all_ideas": zone_ideas,
                "selected_ideas": selected_ideas,
                "selected_count": len(selected_ideas)
            })
        
        # Count total ideas generated across all zones
        total_ideas_generated = sum(len(z["all_ideas"]) for z in all_zones_data)
        
        return {
            # Research foundation
            "research_analysis": research_analysis,
            
            # All JTBDs data
            "jtbd_data": {
                "all_jobs": jobs_list,
                "top_jobs": top_jobs,
                "high_opportunity_jobs": [j for j in jobs_list if j.get("opportunity_score", 0) > 10],
                "methodology": jtbd_data.get("jtbd_data", {}).get("methodology", "")
            },
            
            # Comprehensive metrics
            "metrics": {
                "total_jtbds": len(jobs_list),
                "total_zones": len(zones_with_percentages),
                "total_ideas_generated": total_ideas_generated,
                "total_ideas_selected": 10,
                "avg_importance": round(avg_importance, 1),
                "avg_satisfaction": round(avg_satisfaction, 1),
                "avg_opportunity_score": round(avg_opportunity, 1),
                "underserved_gap": round(avg_importance - avg_satisfaction, 1)
            },
            
            # All zones with complete data
            "all_zones": all_zones_data,
            "zones_summary": zones_with_percentages,
            
            # Market data
            "market": {
                "tam": ideas_data.get("viability_analysis", {}).get("market_assessment", {}).get("total_addressable_market", "Not specified"),
                "sam": ideas_data.get("viability_analysis", {}).get("market_assessment", {}).get("serviceable_addressable_market", "Not specified"),
                "som": ideas_data.get("viability_analysis", {}).get("market_assessment", {}).get("serviceable_obtainable_market", "Not specified"),
                "growth_rate": ideas_data.get("viability_analysis", {}).get("market_assessment", {}).get("market_growth_rate", "Not specified"),
                "time_to_market": ideas_data.get("viability_analysis", {}).get("financial_projections", {}).get("time_to_market", "Not specified")
            },
            
            # Final selected ideas
            "selected_ideas": ideas_data.get("product_ideas", [])[:10],
            
            # Validation evidence
            "validation_evidence": {
                "reddit_discussions_analyzed": jtbd_data.get("jtbd_data", {}).get("reddit_evidence", {}).get("total_discussions", "500+"),
                "methodology": "Zeitgeist clustering with 8-dimensional pain analysis",
                "clustering_approach": "K-means clustering on Reddit discussions and JTBD patterns"
            }
        }
    
    def _generate_mermaid_pie_chart(self, zones_with_percentages):
        """Generate Mermaid pie chart data for zones."""
        lines = []
        for zone in zones_with_percentages:
            name = zone["name"].replace('"', "'")
            percentage = zone["market_opportunity_percentage"]
            lines.append(f'    "{name}" : {percentage}')
        return '\n'.join(lines)
    
    def _generate_zone_details_template(self, zones_with_percentages):
        """Generate template for zone details section."""
        template_parts = []
        for i, zone in enumerate(zones_with_percentages, 1):
            emoji = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"][i-1] if i <= 9 else "🔟"
            template_parts.append(f"""
### {emoji} Zone {i}: {zone['name']}
- **Market Share**: {zone['market_opportunity_percentage']}% of total opportunity
- **Ideas Allocated**: {zone['idea_allocation']} of 10 total
- **Market Size**: {zone.get('market_size', 'TBD')}
- **Key Themes**: {', '.join(zone.get('key_themes', [])[:3])}
- **Pain Dimensions**: Detail the 8 pain scores
- **Solution Requirements**: List key requirements
- **JTBDs Addressed**: Count and examples""")
        return '\n'.join(template_parts)
    
    def _generate_errc_grid_template(self, zones_data, ideas_data):
        """Generate ERRC grid template for all zones."""
        return """Present the ERRC grid for each zone showing:
- What to Eliminate
- What to Reduce  
- What to Raise
- What to Create

Use actual data from the ERRC analysis performed."""
    
    def _generate_ideas_by_zone_template(self, zones_data, ideas_data):
        """Generate template for ideas organized by zone."""
        return """List ALL ideas generated for each zone, marking selected ones with ⭐:

For each zone:
- List all ideas generated (typically 10 per zone)
- Mark selected ideas with ⭐
- Include brief description of each idea
- Show innovation metrics"""
    
    def _generate_selected_ideas_list(self, ideas_data):
        """Generate the final selected ideas list."""
        return """List the 10 selected ideas with:
1. ⭐ [Idea Name] - [Zone] - [Brief Description]
2. ⭐ [Idea Name] - [Zone] - [Brief Description]
... (continue for all 10)"""
    
    def _format_zone_distribution(self, zone_distribution):
        """Format zone distribution for the prompt."""
        lines = []
        for zone in zone_distribution:
            lines.append(f"- {zone['zone_name']}: {zone['percentage']:.1f}% of market → {zone['ideas_allocated']} ideas")
        return "\n".join(lines)
    
    def submit_to_perplexity_deep_research(self, readme_content: str) -> Dict[str, Any]:
        """Submit README to Perplexity Deep Research for validation and gap analysis.
        
        This performs critical market validation to identify:
        - Research gaps and blind spots
        - Validation requirements before development
        - Competitive intelligence needs
        - Customer discovery priorities
        - Risk factors and kill-switch questions
        """
        
        if not self.perplexity_api_key:
            logger.warning("No Perplexity API key found - skipping deep research validation")
            return None
        
        logger.info("🔬 Submitting to Perplexity Deep Research for validation (this takes 5-6 minutes)...")
        
        # Build the research prompt with the README content
        research_prompt = f"""Market Discovery Report (COMPLETED):
{readme_content}
-
You are a strategic business analyst specializing in market opportunity validation and product-market fit assessment. You will be provided with an auto-generated market discovery report that synthesizes initial research findings about potential business opportunities. These reports typically include product ideation results, innovation scoring, market signals, and preliminary opportunity clustering.
YOUR TASK:
Analyze the market discovery report provided above with a critical, investor-minded perspective to identify what additional research is needed before committing resources to product development. Your analysis should uncover blind spots, validate assumptions, and create a prioritized research roadmap.
ANALYSIS FRAMEWORK:
1. Evidence Quality Assessment
First, evaluate the strength of the existing evidence:

What data is explicitly captured vs. inferred?
What metrics are missing or marked as "awaiting research"?
Where are there logical leaps between data and conclusions?
What percentage of conclusions are supported by quantifiable evidence?
Are there any contradictions or suspicious patterns (e.g., 100% scores, universal convergence)?

2. Critical Gap Analysis
Identify and categorize missing information across these dimensions:
Customer Understanding Gaps:

Jobs-to-be-Done formal capture and validation
Customer segmentation and personas
Pain point quantification (time, money, frequency)
Decision-making process and buying criteria
Willingness to pay and budget availability
Current alternative solutions and switching costs

Market Intelligence Gaps:

TAM/SAM/SOM calculations with methodology
Growth rates and market dynamics
Regulatory environment and upcoming changes
Geographic and vertical market prioritization
Market timing indicators and adoption readiness
Network effects and platform dynamics potential

Competitive Landscape Gaps:

Direct, indirect, and substitute solution mapping
Competitive pricing and business models
Market share distribution and consolidation trends
Failed attempts and lessons learned
Defensibility and moat-building opportunities
Partnership vs. competition dynamics

Technical Feasibility Gaps:

Core technology readiness levels
Integration requirements and API availability
Data availability and quality requirements
Scalability constraints and architecture needs
Security and compliance requirements
Time and cost to MVP/production

Business Model Gaps:

Revenue model validation
Unit economics and path to profitability
Customer acquisition cost and channels
Sales cycle length and complexity
Recurring revenue potential
Platform/marketplace dynamics

3. Risk and Assumption Mapping
Create a hierarchy of risks that need validation:

What assumptions, if wrong, would kill the entire opportunity?
Which risks are existential vs. manageable?
What early indicators could validate or invalidate key assumptions?
Where might the report be suffering from confirmation bias?

4. Research Methodology Recommendations
For each identified gap, specify:

The specific research method to employ (interviews, surveys, data analysis, etc.)
Sample size and selection criteria
Key questions to answer
Success metrics and validation thresholds
Timeline and resource requirements
Dependencies and sequencing

5. Prioritized Research Roadmap
Create a phased approach with clear gates:
Phase 1 - Kill Switch Research (Week 1-2)
What research could quickly invalidate the entire opportunity?
Phase 2 - Core Validation (Week 3-4)
What must be true for any version of this to work?
Phase 3 - Solution Refinement (Week 5-6)
What research will help choose between solution variants?
Phase 4 - Go-to-Market Research (Week 7-8)
What research enables successful launch?
6. Key Questions Generator
Generate 20-30 specific, actionable research questions organized by:

Must answer before proceeding (showstoppers)
Should answer to reduce risk (risk mitigators)
Nice to answer for optimization (accelerators)

7. Red Flag Analysis
Specifically call out concerning patterns:

Unrealistic uniformity (all 100% scores, perfect convergence)
Missing fundamentals (no customer validation, no pricing research)
Solution-first thinking indicators
Market size/opportunity inflation signals
Technical complexity underestimation

8. Quick Win Identification
What research could be done immediately (within 48 hours) to:

Validate or invalidate the core thesis
Generate real customer interest/leads
Test key assumptions with minimal resources
Build momentum and learning velocity

OUTPUT REQUIREMENTS:
Structure your response as:

Executive Summary (3-4 sentences)

Overall assessment of report completeness
Biggest blind spots identified
Critical next steps


Evidence Strength Score (rate 1-10 with justification)
Top 10 Research Priorities (ranked by importance)

Each with: Gap identified | Research method | Timeline | Success metric


Kill Switch Questions (3-5 questions that could invalidate everything)
Research Budget Estimate (rough order of magnitude for comprehensive validation)
Recommended Immediate Actions (3-5 things to do in next 48 hours)
Warning Signs (specific patterns that suggest deeper problems)
Competitive Research Priorities (specific competitors or solutions to investigate)
Customer Discovery Protocol (step-by-step interview guide for first 10 customers)
Success Metrics Framework (what metrics would indicate product-market fit)

ANALYSIS TONE:

Be constructively critical - identify weaknesses without dismissing potential
Balance skepticism with opportunity recognition
Focus on actionable insights over theoretical concerns
Prioritize research that drives go/no-go decisions
Challenge assumptions while remaining solution-oriented

SPECIAL INSTRUCTIONS:

If innovation scores are suspiciously high (>9.0 average), probe for reality distortion
If all ideas converge on one theme, investigate whether research was biased
If formal frameworks (like JTBD) show zero results, treat this as a critical red flag
Pay special attention to discrepancies between claimed innovation and market readiness scores
Question whether "moonshot" classifications are justified or aspirational

Now, analyze the provided market discovery report and deliver your comprehensive research gap analysis and recommendations."""
        
        # Prepare the API request
        url = "https://api.perplexity.ai/chat/completions"
        
        payload = {
            "model": "sonar-deep-research",
            "messages": [
                {"role": "user", "content": research_prompt}
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {self.perplexity_api_key}",
            "Content-Type": "application/json",
        }
        
        try:
            # Make the API request
            start_time = time.time()
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            elapsed_time = time.time() - start_time
            logger.info(f"✅ Perplexity Deep Research completed in {elapsed_time:.1f} seconds")
            
            # Parse the response
            research_data = response.json()
            
            # Extract the research content
            if research_data.get("choices") and len(research_data["choices"]) > 0:
                research_content = research_data["choices"][0]["message"]["content"]
                
                # Log statistics
                if "usage" in research_data:
                    usage = research_data["usage"]
                    logger.info(f"📊 Research Statistics:")
                    logger.info(f"  - Total tokens: {usage.get('total_tokens', 0):,}")
                    logger.info(f"  - Search queries: {usage.get('num_search_queries', 0)}")
                    logger.info(f"  - Reasoning tokens: {usage.get('reasoning_tokens', 0):,}")
                    logger.info(f"  - Citations: {len(research_data.get('search_results', []))}")
                
                return {
                    "success": True,
                    "content": research_content,
                    "search_results": research_data.get("search_results", []),
                    "usage": research_data.get("usage", {}),
                    "elapsed_time": elapsed_time
                }
            else:
                logger.error("No content in Perplexity response")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Perplexity API error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error during Perplexity research: {e}")
            return None
    
    def synthesize_v2_readme(self, original_readme: str, research_results: Dict) -> str:
        """Synthesize v2 README that blends original content with deep research insights.
        
        Uses Claude Opus 4.1 to intelligently merge:
        - Original market discovery findings
        - Perplexity's validation research
        - Gap analysis and risk assessment
        - Enhanced market context
        """
        
        if not research_results or not research_results.get("success"):
            logger.warning("No research results available - using original README")
            return original_readme
        
        logger.info("🎯 Synthesizing v2 README with research validation insights...")
        
        synthesis_prompt = f"""You are creating the definitive v2 version of a market research README that blends original findings with critical validation research.

ORIGINAL README:
{original_readme}

VALIDATION RESEARCH (from Perplexity Deep Research):
{research_results['content']}

SEARCH SOURCES REFERENCED:
{json.dumps(research_results.get('search_results', []), indent=2)}

YOUR TASK:
Create an enhanced v2 README that:
1. Maintains ALL original product ideas and opportunity zones (do not change or remove any)
2. Enriches each section with validation insights from the research
3. Adds new sections for critical gaps and validation requirements
4. Provides honest assessment of risks while maintaining optimism
5. Includes specific next-step research actions for each opportunity zone

STRUCTURE FOR V2 README:

# 🎯 Market Research & Innovation Portfolio (v2 - Research Validated)

## 🔬 Research Validation Summary
[New section summarizing the deep research validation performed, key findings, and confidence level]

[Include all original sections but enhance with research insights:]

## 1️⃣ Research Overview (Enhanced)
[Original content + validation notes about research methodology strengths/gaps]

## 2️⃣ Discovery: Pain Points, Solutions & Personas (Validated)
[Original content + specific validation data about pain severity, persona accuracy]

## 3️⃣ Research Summary & Analysis (Market-Verified)
[Original content + external market data that confirms or challenges findings]

## 4️⃣ Jobs To Be Done Analysis (Gap-Assessed)
[Original JTBDs + identification of which need validation, which are confirmed]

## 5️⃣ Zeitgeist Clustering & Opportunity Zones (Risk-Mapped)
[Original zones + risk assessment and validation requirements for each]

## 6️⃣ ERRC Grid Analysis (Competition-Aware)
[Original ERRC + competitive intelligence gaps and validation needs]

## 7️⃣ Product Ideas Generated (Feasibility-Checked)
[Original ideas unchanged + technical feasibility notes and validation requirements]

## 8️⃣ Final Selection: Top 10 Ideas (Prioritized for Validation)
[Original selection + specific validation steps needed for each]

## 🚨 Critical Research Gaps (New Section)
### Kill-Switch Questions
[3-5 questions that could invalidate the opportunity]

### Must-Validate Assumptions
[Top assumptions that need immediate validation]

### Competitive Blind Spots
[Specific competitors or solutions that need investigation]

## 📋 Validation Roadmap (New Section)
### Phase 1: Immediate Actions (48 hours)
[Specific research tasks that can be done immediately]

### Phase 2: Customer Discovery (Week 1-2)
[Interview protocol and target customer segments]

### Phase 3: Technical Validation (Week 3-4)
[POC requirements and technical feasibility tests]

### Phase 4: Market Validation (Week 5-6)
[Market sizing, pricing, and go-to-market validation]

## 💰 Resource Requirements (New Section)
### Research Budget
[Estimated budget for comprehensive validation]

### Team Needs
[Skills and resources needed for validation]

### Timeline to Validated Concept
[Realistic timeline with validation gates]

## 📊 Success Metrics Enhanced
[Original metrics + specific validation thresholds and measurement methods]

## ⚠️ Risk Assessment Matrix (New Section)
[Visual or structured representation of risks by severity and likelihood]

---

IMPORTANT INSTRUCTIONS:
1. Keep ALL 10 original product ideas exactly as they are
2. Maintain the same opportunity zones and their allocations
3. Add validation context without undermining the original findings
4. Be honest about gaps while maintaining strategic optimism
5. Make the research actionable with specific next steps
6. Use the same emoji system and visual hierarchy as the original
7. Cite specific sources from the search results where relevant

Generate the enhanced v2 README that makes this research investment-ready:"""
        
        # Use Claude Opus 4.1 for synthesis
        import anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            client = anthropic.Anthropic(api_key=anthropic_key)
            response = client.messages.create(
                model="claude-opus-4-1-20250805",
                max_tokens=8000,
                temperature=0.7,
                system="You are a strategic market analyst synthesizing original research with validation insights. Maintain all original ideas while adding critical validation context. Be honest about gaps and risks while preserving the opportunity narrative. Your goal is to create an investment-ready document that acknowledges unknowns while building confidence through a clear validation path.",
                messages=[
                    {"role": "user", "content": synthesis_prompt}
                ]
            )
            v2_readme = response.content[0].text
            logger.info("✅ Synthesized v2 README with research validation")
            return v2_readme
        else:
            # Fallback to GPT-4o if no Anthropic key
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a strategic market analyst synthesizing original research with validation insights. Create an investment-ready document."},
                    {"role": "user", "content": synthesis_prompt}
                ],
                temperature=0.7,
                max_tokens=8000
            )
            v2_readme = response.choices[0].message.content
            logger.info("✅ Synthesized v2 README with GPT-4o")
            return v2_readme

    def create_issue_content_with_gpt5(
        self, idea: Dict, idea_number: int, jtbd_data: Dict, zone_data: Dict = None
    ) -> Dict[str, str]:
        """Use Claude or GPT to generate a killer GitHub issue that's like a pitch deck in markdown.
        
        This now uses the comprehensive README as context for richer issue generation.
        """
        
        # Load the FULL original research report if available  
        original_research_report = ""
        if os.path.exists("analysis_results.md"):
            with open("analysis_results.md", "r") as f:
                original_research_report = f.read()
        
        # Get the zone's percentage and allocation info
        zones_with_percentages = self._calculate_zone_percentages(
            {"clustered_zones": {"zone": zone_data}} if zone_data else {}
        )
        zone_info = zones_with_percentages[0] if zones_with_percentages else {}
        
        # Prepare comprehensive context, including README context
        idea_context = {
            "idea": idea,
            "zone": {
                "data": zone_data if zone_data else {},
                "market_percentage": zone_info.get("market_opportunity_percentage", 0),
                "idea_allocation": zone_info.get("idea_allocation", 1),
                "pain_dimensions": zone_info.get("pain_dimensions", {}),
                "solution_requirements": zone_info.get("solution_requirements", [])
            },
            "jtbd_context": jtbd_data.get("jtbd_data", {}).get("jobs_list", [])[:5],
            "market_signals": {
                "total_addressable_market": idea.get("market_size", "$10B+"),
                "growth_rate": "25-30% CAGR",
                "competitive_landscape": idea.get("competitive_advantage", "Blue ocean opportunity")
            },
            "readme_context": getattr(self, "gpt5_readme_context", "")
        }
        
        prompt = f"""You are creating a GitHub issue that serves as a complete pitch deck for a breakthrough product idea. This issue is part of a portfolio where this opportunity zone represents {zone_info.get('market_percentage', 0):.1f}% of the total market opportunity and has been allocated {zone_info.get('idea_allocation', 1)} of 10 total innovation slots.

================================================================================
ORIGINAL BUSINESS RESEARCH - CRITICAL CONTEXT
================================================================================
{original_research_report[:3000]}  # Include first 3000 chars to avoid token limits
================================================================================

COMPREHENSIVE CONTEXT:
{json.dumps(idea_context, indent=2, default=str)}

CRITICAL CONTEXT FROM RESEARCH:
- This idea addresses an opportunity zone that represents {zone_info.get('market_percentage', 0):.1f}% of the total market
- The zone has {zone_info.get('idea_allocation', 1)} idea slots allocated based on its market importance
- Key pain dimensions in this zone: {', '.join(list(zone_info.get('pain_dimensions', {}).keys())[:3])}
- Solution requirements: {', '.join(zone_info.get('solution_requirements', [])[:3])}

IMPORTANT: The original research report above contains the specific business context. Use it to ground this idea in the reality of the target business and their market.

Create an EXCEPTIONAL GitHub issue that serves as a complete pitch deck. This should be so comprehensive that an investor could make a funding decision based solely on this issue.

STRUCTURE YOUR ISSUE AS:

# 🚀 [Product Name] - [Compelling Tagline]

## 🎯 Executive Summary
[One paragraph that captures everything - the problem, solution, market, and why this wins. MUST reference the original business context from the research.]

## 🏢 Strategic Context for Original Business
[How this idea relates to the original business in the research report and their strategic position]

## 📊 Market Context & Zone Analysis
- Position within opportunity portfolio (this is idea X of {zone_info.get('idea_allocation', 1)} in a zone representing {zone_info.get('market_percentage', 0):.1f}% of market)
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

## 🚀 Call to Action
[Clear next steps for stakeholders]

---
*This opportunity represents {zone_info.get('market_percentage', 0):.1f}% of our total addressable market and is 1 of {zone_info.get('idea_allocation', 1)} strategic initiatives in this zone.*

Make this issue VISUALLY STUNNING and COMPELLING. Use the README context to maintain consistency.

Output the complete markdown content that will be the issue body:"""
        
        # Use Claude Opus 4.1 for superior narrative quality
        import anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            client = anthropic.Anthropic(api_key=anthropic_key)
            response = client.messages.create(
                model="claude-opus-4-1-20250805",
                max_tokens=8000,
                temperature=0.8,
                system="You are a world-class venture strategist creating definitive pitch decks for breakthrough innovations. Each issue should tell a compelling story that builds excitement and confidence in the opportunity.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            gpt5_content = response.content[0].text
            logger.info(f"✅ Generated compelling issue #{idea_number} with Claude Opus 4.1")
        else:
            # Use GPT-4o if no Anthropic key
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a world-class venture strategist creating definitive pitch decks for breakthrough innovations. Each issue should tell a compelling story that builds excitement and confidence in the opportunity."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=8000
            )
            gpt5_content = response.choices[0].message.content
            logger.info(f"✅ Generated compelling issue #{idea_number} with GPT-4o")
        
        # Extract title from the content or generate one
        title = idea.get('name', f'Product Idea {idea_number}')
        if gpt5_content.startswith('#'):
            # Try to extract title from first line
            first_line = gpt5_content.split('\n')[0]
            if first_line.startswith('# '):
                title = first_line[2:].strip()
        
        return {
            "title": title if title.startswith("🚀") else f"🚀 {title}",
            "body": gpt5_content
        }
    
    def create_issue_content(
        self, idea: Dict, idea_number: int, jtbd_data: Dict, zone_data: Dict = None
    ) -> Dict[str, str]:
        """Generate issue title and body for a product idea with comprehensive business pitch."""
        
        return self.create_issue_content_with_gpt5(idea, idea_number, jtbd_data, zone_data)


    def create_labels(self, repo: Any) -> Dict[str, Any]:
        """Create standard labels for the repository."""
        labels = [
            {
                "name": "shark ready 🦈",
                "color": "FBCA04",
                "description": "Ready for the sharks to add their 2 cents",
            },
            {
                "name": "product-idea",
                "color": "0E8A16",
                "description": "Product idea for consideration",
            },
            {
                "name": "high-priority",
                "color": "D93F0B",
                "description": "High priority item",
            },
            {
                "name": "medium-priority",
                "color": "FBCA04",
                "description": "Medium priority item",
            },
            {
                "name": "low-priority",
                "color": "0E8A16",
                "description": "Low priority item",
            },
            {
                "name": "ai-powered",
                "color": "7057FF",
                "description": "AI/ML powered feature",
            },
            {
                "name": "mobile",
                "color": "0052CC",
                "description": "Mobile-related feature",
            },
            {
                "name": "integration",
                "color": "006B75",
                "description": "Integration with other tools",
            },
            {
                "name": "analytics",
                "color": "1D76DB",
                "description": "Analytics and insights",
            },
            {
                "name": "security",
                "color": "D93F0B",
                "description": "Security-related feature",
            },
            {
                "name": "phase-1",
                "color": "0E8A16",
                "description": "Phase 1 implementation",
            },
            {
                "name": "phase-2",
                "color": "FBCA04",
                "description": "Phase 2 implementation",
            },
            {
                "name": "phase-3",
                "color": "0052CC",
                "description": "Phase 3 implementation",
            },
            {
                "name": "phase-4",
                "color": "5319E7",
                "description": "Phase 4 implementation",
            },
            {
                "name": "quick-win",
                "color": "0E8A16",
                "description": "Quick win opportunity",
            },
            {
                "name": "needs-validation",
                "color": "FBCA04",
                "description": "Needs market validation",
            },
        ]

        created_labels = {}
        for label_data in labels:
            try:
                label = repo.create_label(**label_data)
                created_labels[label_data["name"]] = label
                logger.info(f"Created label: {label_data['name']}")
            except GithubException as e:
                if e.status == 422:  # Label already exists
                    try:
                        label = repo.get_label(label_data["name"])
                        created_labels[label_data["name"]] = label
                        logger.info(f"Label already exists: {label_data['name']}")
                    except Exception:
                        pass
                else:
                    logger.error(f"Error creating label {label_data['name']}: {e}")

        return created_labels

    def create_github_project(
        self,
        repo_name: str,
        research_analysis: Dict,
        jtbd_data: Dict,
        zones_data: Dict,
        ideas_data: Dict,
        create_issues: bool = True,
        private: bool = False,
    ) -> Dict[str, Any]:
        """Create complete GitHub project with repo, README, and issues.
        
        Enhanced workflow:
        1. Generate initial README with Claude Opus 4.1
        2. Submit to Perplexity Deep Research for validation (5-6 minutes)
        3. Synthesize v2 README with research insights
        4. Create GitHub repository with v2 README
        5. Create issues for each product idea
        """

        results = {"repo_url": None, "issues_created": [], "errors": []}

        try:
            # Clean repo name
            repo_name = repo_name.lower().replace(" ", "-").replace("_", "-")

            # Step 1: Generate initial README
            logger.info("📝 Step 1: Generating initial README with Claude Opus 4.1...")
            initial_readme = self.generate_readme_content(
                research_analysis=research_analysis,
                jtbd_data=jtbd_data,
                zones_data=zones_data,
                ideas_data=ideas_data,
                repo_name=repo_name,
            )
            
            # Step 2: Submit to Perplexity Deep Research for validation
            logger.info("🔬 Step 2: Submitting to Perplexity Deep Research for validation...")
            research_results = self.submit_to_perplexity_deep_research(initial_readme)
            
            # Step 3: Synthesize v2 README with research insights
            if research_results and research_results.get("success"):
                logger.info("🎯 Step 3: Synthesizing v2 README with research validation...")
                readme_content = self.synthesize_v2_readme(initial_readme, research_results)
                logger.info("✅ Using research-validated v2 README for repository")
            else:
                logger.warning("⚠️ Deep research unavailable - using initial README")
                readme_content = initial_readme
            
            # Step 4: Create repository
            logger.info("📦 Step 4: Creating GitHub repository...")
            repo = self.create_repository(
                repo_name=repo_name,
                description="AI-powered market research and product ideation results (Research Validated)",
                private=private,
            )
            results["repo_url"] = repo.html_url

            # Create labels
            self.create_labels(repo)

            # Step 5: Create README in repository
            logger.info("📄 Step 5: Creating README.md in repository...")
            try:
                repo.create_file(
                    path="README.md",
                    message="Initial commit: Add research-validated market analysis (v2)",
                    content=readme_content,
                    branch="main",
                )
                logger.info("✅ Created README.md with research validation")
            except GithubException as e:
                if e.status == 422:  # File already exists
                    contents = repo.get_contents("README.md")
                    repo.update_file(
                        path="README.md",
                        message="Update market research and analysis",
                        content=readme_content,
                        sha=contents.sha,
                        branch="main",
                    )
                    logger.info("Updated existing README.md")
                else:
                    raise

            # Step 6: Create issues for each product idea
            if create_issues:
                ideas_list = ideas_data.get("product_ideas", [])
                logger.info(f"📋 Step 6: Creating GitHub issues for {len(ideas_list)} product ideas...")
                for i, idea in enumerate(ideas_list, 1):
                    try:
                        # Find the zone data for this idea
                        zone_data = None
                        idea_zone_name = idea.get("zone_name", "")
                        for zone_key, zone_info in zones_data.get("clustered_zones", {}).items():
                            if zone_info.get("name", "") == idea_zone_name:
                                zone_data = zone_info
                                break
                        
                        # Create issue with zone context
                        logger.info(f"Creating issue #{i} for idea: {idea.get('name', 'Unnamed')}")
                        issue_data = self.create_issue_content(idea, i, jtbd_data, zone_data)
                        logger.info(f"Issue data created with title: {issue_data.get('title', 'No title')}")

                        # Determine labels for this issue
                        issue_labels = ["product-idea"]

                        # Add priority label
                        if idea.get("market_opportunity", 0) >= 8:
                            issue_labels.append("high-priority")
                        elif idea.get("market_opportunity", 0) >= 6:
                            issue_labels.append("medium-priority")
                        else:
                            issue_labels.append("low-priority")

                        # Add category-specific labels
                        category = idea.get("category", "").lower()
                        if "ai" in category or "ml" in category:
                            issue_labels.append("ai-powered")
                        if "mobile" in category:
                            issue_labels.append("mobile")
                        if "integration" in category:
                            issue_labels.append("integration")
                        if "analytics" in category:
                            issue_labels.append("analytics")
                        if "security" in category:
                            issue_labels.append("security")

                        # Add phase label based on implementation phase
                        impl_phase = idea.get("implementation_phase", "")
                        if "1" in str(impl_phase) or "quick" in impl_phase.lower():
                            issue_labels.append("phase-1")
                            if "quick" in impl_phase.lower():
                                issue_labels.append("quick-win")
                        elif "2" in str(impl_phase):
                            issue_labels.append("phase-2")
                        elif "3" in str(impl_phase):
                            issue_labels.append("phase-3")
                        elif "4" in str(impl_phase):
                            issue_labels.append("phase-4")

                        # Create the issue
                        issue = repo.create_issue(
                            title=issue_data["title"],
                            body=issue_data["body"],
                            labels=issue_labels,
                        )

                        results["issues_created"].append(
                            {
                                "number": issue.number,
                                "title": issue.title,
                                "url": issue.html_url,
                            }
                        )

                        logger.info(f"Created issue #{issue.number}: {issue.title}")

                        # Add small delay to avoid rate limiting
                        time.sleep(0.5)

                    except Exception as e:
                        error_msg = f"Error creating issue for {idea.get('name', f'idea {i}')}: {str(e)}"
                        logger.error(error_msg)
                        results["errors"].append(error_msg)

            logger.info(f"GitHub project created successfully: {results['repo_url']}")

        except Exception as e:
            error_msg = f"Error creating GitHub project: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)

        return results


def create_github_output(
    research_analysis: Dict,
    jtbd_data: Dict,
    zones_data: Dict,
    ideas_data: Dict,
    repo_name: str = "market-research-insights",
    github_token: Optional[str] = None,
    create_issues: bool = True,
    private: bool = False,
    organization: str = "ocean-studio-repos",
) -> Dict[str, Any]:
    """Main function to create GitHub output from analysis results."""

    try:
        github_integration = GitHubIntegration(github_token, organization)

        results = github_integration.create_github_project(
            repo_name=repo_name,
            research_analysis=research_analysis,
            jtbd_data=jtbd_data,
            zones_data=zones_data,
            ideas_data=ideas_data,
            create_issues=create_issues,
            private=private,
        )

        return {
            "success": len(results.get("errors", [])) == 0,
            "repo_url": results.get("repo_url"),
            "issues_created": len(results.get("issues_created", [])),
            "results": results,
        }

    except Exception as e:
        logger.error(f"Failed to create GitHub output: {str(e)}")
        return {"success": False, "error": str(e), "results": None}
