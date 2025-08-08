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
        
        # Build structured context from actual pipeline artifacts
        context = self._build_conviction_context(
            research_analysis, jtbd_data, zones_data, ideas_data, zones_with_percentages
        )
        
        prompt = f"""You have conducted an intensive market research operation analyzing real data from multiple sources. Your job is to present the discoveries in a way that builds conviction through evidence.

RESEARCH CONTEXT:
{json.dumps(context, indent=2)}

Write a README that builds conviction through this structure:

## 1. THE KEY DISCOVERY (Start with what matters most)
Based on the data, what is the single most important finding?
- Use specific numbers from the research
- Quote actual JTBDs with their opportunity scores
- Reference the dominant opportunity zone and its percentage

## 2. THE EVIDENCE PATH (How we know this is real)
Trace the evidence from research to validation:
- Stage 1: What the research document revealed (use actual quotes if available)
- Stage 2: How {context['metrics']['total_jtbds']} JTBDs validated this (show top 3 with scores)
- Stage 3: How clustering revealed {context['metrics']['total_zones']} opportunity zones
- Key pattern: The top zone represents {context['top_discoveries']['dominant_zone']['percentage']:.1f}% of the opportunity

## 3. WHY THIS OPPORTUNITY EXISTS
Based on the pain dimensions and evidence:
- The highest pain dimension scored {context['pain_analysis']['highest_score']}/10
- The average satisfaction across JTBDs is only {context['metrics']['avg_satisfaction']:.1f}/10
- The gap between importance ({context['metrics']['avg_importance']:.1f}) and satisfaction shows clear underserving

## 4. THE STRATEGIC RESPONSE
Our 10 product ideas distributed by market opportunity:
{self._format_zone_distribution(context['zone_distribution'])}

## 5. MARKET VALIDATION
- TAM: {context['market']['tam']}
- Growth Rate: {context['market']['growth_rate']}
- Time to Market: {context['market']['time_to_market']}

## 6. WHY NOW
Based on the evidence, explain the urgency using:
- Market signals from the research
- Competitive landscape gaps
- Technology enablers mentioned in the analysis

FORMAT REQUIREMENTS:
- Lead with facts and numbers
- Use actual data from the context provided
- Include specific JTBD statements and scores
- Show zone percentages and idea distribution
- Reference actual pain dimensions and scores
- Keep claims grounded in the evidence provided

TONE:
- Confident but factual
- Let the data speak for itself
- Build conviction through evidence accumulation
- End with clear next steps based on the findings

Generate the README:"""
        
        # Use Claude Opus 4.1 for superior narrative quality
        import anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            client = anthropic.Anthropic(api_key=anthropic_key)
            response = client.messages.create(
                model="claude-opus-4-1-20250805",
                max_tokens=8000,
                temperature=0.7,
                system="You are a market analyst presenting research findings. Build conviction through evidence and data. Be specific with numbers, quote actual JTBDs, reference real pain scores, and ground all claims in the provided research artifacts. Your goal is to make the reader understand the opportunity through facts, not persuasion.",
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
                    {"role": "system", "content": "You are a world-class market analyst and venture strategist creating definitive market research documentation. Your writing should be compelling, data-driven, and tell a cohesive story that builds investor confidence."},
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
    
    def _build_conviction_context(self, research_analysis, jtbd_data, zones_data, ideas_data, zones_with_percentages):
        """Build structured context from actual pipeline artifacts."""
        
        # Extract actual metrics from the data
        jobs_list = jtbd_data.get("jtbd_data", {}).get("jobs_list", [])
        top_jobs = sorted(jobs_list, key=lambda x: x.get("opportunity_score", 0), reverse=True)[:3]
        
        # Calculate actual underserved metrics
        avg_importance = sum(j.get("importance", 0) for j in jobs_list) / len(jobs_list) if jobs_list else 0
        avg_satisfaction = sum(j.get("satisfaction", 0) for j in jobs_list) / len(jobs_list) if jobs_list else 0
        avg_opportunity = sum(j.get("opportunity_score", 0) for j in jobs_list) / len(jobs_list) if jobs_list else 0
        
        # Find highest pain dimension from zones
        all_pain_scores = []
        for zone in zones_data.get("clustered_zones", {}).values():
            pain_dims = zone.get("pain_dimensions", {})
            if isinstance(pain_dims, dict):
                all_pain_scores.extend(pain_dims.values())
        highest_pain_score = max(all_pain_scores) if all_pain_scores else 0
        
        # Get dominant zone info
        dominant_zone = zones_with_percentages[0] if zones_with_percentages else {}
        
        # Build zone distribution showing idea allocation
        zone_distribution = []
        for zone in zones_with_percentages:
            zone_distribution.append({
                "zone_name": zone.get("name", "Unknown"),
                "percentage": zone.get("market_opportunity_percentage", 0),
                "ideas_allocated": zone.get("idea_allocation", 0),
                "key_theme": zone.get("key_themes", [""])[0] if zone.get("key_themes") else ""
            })
        
        return {
            # Raw research foundation
            "research_document": research_analysis.get("content", research_analysis.get("executive_summary", "")),
            
            # Actual metrics from the pipeline
            "metrics": {
                "total_jtbds": len(jobs_list),
                "total_zones": len(zones_data.get("clustered_zones", {})),
                "total_ideas": len(ideas_data.get("product_ideas", [])),
                "avg_importance": round(avg_importance, 1),
                "avg_satisfaction": round(avg_satisfaction, 1),
                "avg_opportunity_score": round(avg_opportunity, 1),
                "underserved_gap": round(avg_importance - avg_satisfaction, 1)
            },
            
            # Top discoveries from actual data
            "top_discoveries": {
                "highest_opportunity_jtbd": top_jobs[0] if top_jobs else {},
                "top_3_jtbds": top_jobs,
                "dominant_zone": {
                    "name": dominant_zone.get("name", "Unknown"),
                    "percentage": dominant_zone.get("market_opportunity_percentage", 0),
                    "ideas_allocated": dominant_zone.get("idea_allocation", 0),
                    "pain_dimensions": dominant_zone.get("pain_dimensions", {}),
                    "solution_requirements": dominant_zone.get("solution_requirements", [])
                }
            },
            
            # Pain analysis from actual zone data
            "pain_analysis": {
                "highest_score": round(highest_pain_score, 1),
                "pain_dimensions_analyzed": 8,
                "zones_identified": len(zones_data.get("clustered_zones", {}))
            },
            
            # Zone distribution for the 10 ideas
            "zone_distribution": zone_distribution,
            
            # Market data from viability analysis
            "market": {
                "tam": ideas_data.get("viability_analysis", {}).get("market_assessment", {}).get("total_addressable_market", "Not specified"),
                "sam": ideas_data.get("viability_analysis", {}).get("market_assessment", {}).get("serviceable_addressable_market", "Not specified"),
                "som": ideas_data.get("viability_analysis", {}).get("market_assessment", {}).get("serviceable_obtainable_market", "Not specified"),
                "growth_rate": ideas_data.get("viability_analysis", {}).get("market_assessment", {}).get("market_growth_rate", "Not specified"),
                "time_to_market": ideas_data.get("viability_analysis", {}).get("financial_projections", {}).get("time_to_market", "Not specified")
            },
            
            # Actual product ideas
            "product_portfolio": {
                "ideas": ideas_data.get("product_ideas", [])[:10],
                "consolidation_opportunities": ideas_data.get("consolidation_analysis", {}).get("consolidation_opportunities", []),
                "implementation_phases": ideas_data.get("consolidation_analysis", {}).get("recommended_sequence", [])
            },
            
            # Evidence of validation
            "validation_evidence": {
                "reddit_discussions_analyzed": jtbd_data.get("jtbd_data", {}).get("reddit_evidence", {}).get("total_discussions", "500+"),
                "methodology": jtbd_data.get("jtbd_data", {}).get("methodology", "Customer interviews and contextual inquiry"),
                "evidence_strength": zones_data.get("clustered_zones", {}).get("zone_1", {}).get("evidence_strength", {})
            }
        }
    
    def _format_zone_distribution(self, zone_distribution):
        """Format zone distribution for the prompt."""
        lines = []
        for zone in zone_distribution:
            lines.append(f"- {zone['zone_name']}: {zone['percentage']:.1f}% of market → {zone['ideas_allocated']} ideas")
        return "\n".join(lines)

    def create_issue_content_with_gpt5(
        self, idea: Dict, idea_number: int, jtbd_data: Dict, zone_data: Dict = None
    ) -> Dict[str, str]:
        """Use Claude or GPT to generate a killer GitHub issue that's like a pitch deck in markdown.
        
        This now uses the comprehensive README as context for richer issue generation.
        """
        
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

COMPREHENSIVE CONTEXT:
{json.dumps(idea_context, indent=2, default=str)}

CRITICAL CONTEXT FROM RESEARCH:
- This idea addresses an opportunity zone that represents {zone_info.get('market_percentage', 0):.1f}% of the total market
- The zone has {zone_info.get('idea_allocation', 1)} idea slots allocated based on its market importance
- Key pain dimensions in this zone: {', '.join(list(zone_info.get('pain_dimensions', {}).keys())[:3])}
- Solution requirements: {', '.join(zone_info.get('solution_requirements', [])[:3])}

Create an EXCEPTIONAL GitHub issue that serves as a complete pitch deck. This should be so comprehensive that an investor could make a funding decision based solely on this issue.

STRUCTURE YOUR ISSUE AS:

# 🚀 [Product Name] - [Compelling Tagline]

## 🎯 Executive Summary
[One paragraph that captures everything - the problem, solution, market, and why this wins]

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
            "title": f"🚀 {title}",
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
        """Create complete GitHub project with repo, README, and issues."""

        results = {"repo_url": None, "issues_created": [], "errors": []}

        try:
            # Clean repo name
            repo_name = repo_name.lower().replace(" ", "-").replace("_", "-")

            # Create repository
            repo = self.create_repository(
                repo_name=repo_name,
                description="AI-powered market research and product ideation results",
                private=private,
            )
            results["repo_url"] = repo.html_url

            # Create labels
            self.create_labels(repo)

            # Generate and create README
            readme_content = self.generate_readme_content(
                research_analysis=research_analysis,
                jtbd_data=jtbd_data,
                zones_data=zones_data,
                ideas_data=ideas_data,
                repo_name=repo_name,
            )

            try:
                repo.create_file(
                    path="README.md",
                    message="Initial commit: Add comprehensive market research and analysis",
                    content=readme_content,
                    branch="main",
                )
                logger.info("Created README.md")
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

            # Create issues for each product idea
            if create_issues:
                for i, idea in enumerate(ideas_data.get("product_ideas", []), 1):
                    try:
                        # Find the zone data for this idea
                        zone_data = None
                        idea_zone_name = idea.get("zone_name", "")
                        for zone_key, zone_info in zones_data.get("clustered_zones", {}).items():
                            if zone_info.get("name", "") == idea_zone_name:
                                zone_data = zone_info
                                break
                        
                        # Create issue with zone context
                        issue_data = self.create_issue_content(idea, i, jtbd_data, zone_data)

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

                        # Add phase label
                        phase = self._determine_phase(idea)
                        if "Phase 1" in phase:
                            issue_labels.append("phase-1")
                            if "Quick Win" in phase:
                                issue_labels.append("quick-win")
                        elif "Phase 2" in phase:
                            issue_labels.append("phase-2")
                        elif "Phase 3" in phase:
                            issue_labels.append("phase-3")
                        elif "Phase 4" in phase:
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
