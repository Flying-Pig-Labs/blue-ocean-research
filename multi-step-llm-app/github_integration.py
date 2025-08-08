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
        
        This now uses GPT-5 to create a killer README that serves as the foundation
        for all subsequent issue generation.
        """
        
        # Try GPT-5 first for comprehensive README generation
        if self._should_use_gpt5():
            return self.generate_readme_with_gpt5(
                research_analysis, jtbd_data, zones_data, ideas_data, repo_name
            )
        
        # Fallback to enhanced manual generation
        return self.generate_readme_fallback(
            research_analysis, jtbd_data, zones_data, ideas_data, repo_name
        )
    
    def _should_use_gpt5(self) -> bool:
        """Check if advanced models (Claude/GPT) should be used."""
        return os.getenv("USE_ADVANCED_MODELS_FOR_ISSUES", "true").lower() == "true"
    
    def generate_readme_with_gpt5(
        self,
        research_analysis: Dict,
        jtbd_data: Dict,
        zones_data: Dict,
        ideas_data: Dict,
        repo_name: str,
    ) -> str:
        """Use Claude Opus 4.1 or GPT-5 to generate a comprehensive, pitch-deck quality README."""
        
        try:
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
- Key pattern: The top zone represents {context['dominant_zone']['percentage']:.1f}% of the opportunity

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
            
            # Try Claude Opus 4.1 first as it generally produces better narrative
            try:
                import anthropic
                anthropic_key = os.getenv("ANTHROPIC_API_KEY")
                if anthropic_key:
                    client = anthropic.Anthropic(api_key=anthropic_key)
                    response = client.messages.create(
                        model="claude-opus-4-1-20250805",  # Using Opus 4.1 for superior narrative quality
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
            except Exception as claude_error:
                logger.warning(f"Claude Opus 4.1 generation failed, trying GPT-4o: {claude_error}")
            
            # Fall back to GPT-5 if Claude fails
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4o as GPT-5 may not be available
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
            
        except Exception as e:
            logger.warning(f"⚠️ Advanced model generation failed, using enhanced fallback: {e}")
            return self.generate_readme_fallback(
                research_analysis, jtbd_data, zones_data, ideas_data, repo_name
            )
    
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
    
    def generate_readme_fallback(
        self,
        research_analysis: Dict,
        jtbd_data: Dict,
        zones_data: Dict,
        ideas_data: Dict,
        repo_name: str,
    ) -> str:
        """Enhanced fallback README generation with zone percentages."""

        # Extract key metrics
        total_market_size = (
            ideas_data.get("viability_analysis", {})
            .get("market_assessment", {})
            .get("total_addressable_market", "N/A")
        )
        growth_rate = (
            ideas_data.get("viability_analysis", {})
            .get("market_assessment", {})
            .get("market_growth_rate", "N/A")
        )

        # Count ideas by category
        categories = ideas_data.get("consolidation_analysis", {}).get("categories", {})

        # Get top opportunity jobs
        top_jobs = sorted(
            jtbd_data.get("jtbd_data", {}).get("jobs_list", []),
            key=lambda x: x.get("opportunity_score", 0),
            reverse=True,
        )[:5]

        readme_content = f"""# {repo_name.replace("-", " ").title()}

## 📊 Market Research & Opportunity Analysis

This repository contains comprehensive market research, Jobs-to-be-Done (JTBD) analysis, and weighted opportunity zones analysis for innovative solutions in the productivity tools market.

## 🎯 Executive Summary

{research_analysis.get("executive_summary", "Our research identified significant opportunities in the target market through extensive analysis and customer insights.")}

### Key Market Insights:
- **Total Addressable Market**: {total_market_size}
- **Market Growth Rate**: {growth_rate}
- **Research Participants**: {jtbd_data.get("jtbd_data", {}).get("research_summary", "Comprehensive market research conducted")}

## 🔍 Jobs-to-be-Done (JTBD) Analysis

### Research Methodology
{jtbd_data.get("jtbd_data", {}).get("methodology", "Customer interviews, contextual inquiry, and job mapping exercises")}

### Top Opportunity Jobs Identified

"""

        # Add top jobs
        for i, job in enumerate(top_jobs, 1):
            readme_content += f"""
#### {i}. **{job.get("job_statement", "").split("I want to")[1].strip().capitalize() if "I want to" in job.get("job_statement", "") else "Job " + str(i)}** (Opportunity Score: {job.get("opportunity_score", "N/A")})
- **Job**: "{job.get("job_statement", "")}"
- **Frequency**: {job.get("frequency", "N/A")}
- **Current Pain Points**: {", ".join(job.get("pain_points", [])[:3])}
- **Importance**: {job.get("importance", "N/A")}/10 | **Satisfaction**: {job.get("satisfaction", "N/A")}/10
"""

        readme_content += """
## 🎯 Weighted Opportunity Zones Analysis

"""

        # Add zones analysis
        for zone_key, zone_data in zones_data.get("clustered_zones", {}).items():
            zone_num = zone_key.split("_")[1]
            readme_content += f"""### Zone {zone_num}: {zone_data.get("name", "Opportunity Zone")}
- **Market Size**: {zone_data.get("market_size", "N/A")}
- **Pain Level**: {zone_data.get("pain_level", "N/A").capitalize()}
- **Key Themes**: {", ".join(zone_data.get("key_themes", [])[:4])}
- **Competitive Intensity**: {zone_data.get("competitive_intensity", "N/A").capitalize()}

"""

        readme_content += """## 💡 Product Ideas Generated

Based on our comprehensive analysis, we've identified innovative product concepts that address the discovered opportunity zones:

### Product Portfolio
"""

        # Add product ideas summary
        for i, idea in enumerate(ideas_data.get("product_ideas", []), 1):
            readme_content += f"""
{i}. **[{idea.get("name", f"Product Idea {i}")}](../../issues/{i})** - {idea.get("description", "")}
   - Market Size: {idea.get("market_size", "N/A")}
   - Development Time: {idea.get("estimated_development_time", "N/A")}
   - Target Market: {idea.get("target_market", "N/A")}
"""

        # Add consolidation opportunities
        consolidation_opps = ideas_data.get("consolidation_analysis", {}).get(
            "consolidation_opportunities", []
        )
        if consolidation_opps:
            readme_content += """
## 📈 Strategic Consolidation Opportunities

Our analysis identified major consolidation opportunities that could capture larger market segments:

"""
            for opp in consolidation_opps:
                readme_content += f"""### {opp.get("consolidated_idea", "Consolidated Solution")}
- **Market Potential**: {opp.get("market_potential", "N/A")}
- **Combines**: {", ".join([ideas_data.get("product_ideas", [])[int(id.replace("IDEA", "")) - 1].get("name", id) for id in opp.get("combines", []) if id.startswith("IDEA") and int(id.replace("IDEA", "")) <= len(ideas_data.get("product_ideas", []))])}
- **Rationale**: {opp.get("rationale", "")}
- **Complexity**: {opp.get("complexity", "N/A").capitalize()}

"""

        # Add implementation roadmap
        phases = ideas_data.get("consolidation_analysis", {}).get(
            "recommended_sequence", []
        )
        if phases:
            readme_content += """## 🚀 Recommended Implementation Roadmap

"""
            for phase in phases:
                readme_content += f"""### {phase.get("phase", "Phase")}
- **Focus**: {", ".join([ideas_data.get("product_ideas", [])[int(id.replace("IDEA", "")) - 1].get("name", id) for id in phase.get("ideas", []) if id.startswith("IDEA") and int(id.replace("IDEA", "")) <= len(ideas_data.get("product_ideas", []))])}
- **Rationale**: {phase.get("rationale", "")}

"""

        # Add financial projections
        financial = ideas_data.get("viability_analysis", {}).get(
            "financial_projections", {}
        )
        if financial:
            readme_content += f"""## 📊 Financial Projections
- **Total Development Cost**: {financial.get("total_development_cost", "N/A")}
- **Time to Market**: {financial.get("time_to_market", "N/A")}
- **Break-even Timeline**: {financial.get("break_even_timeline", "N/A")}
- **5-Year Revenue Projection**: {financial.get("projected_5_year_revenue", "N/A")}
- **Funding Requirements**: {financial.get("funding_requirements", "N/A")}

"""

        readme_content += (
            """## 🎯 Success Metrics
- User adoption rate
- Market penetration percentage
- Customer satisfaction (NPS)
- Revenue per user
- Time-to-value for customers
- Feature utilization rates

## 📚 Detailed Analysis
For comprehensive analysis of each product idea including technical requirements, go-to-market strategies, and detailed financial projections, please refer to the individual issue pages linked above.

---

*This analysis was generated through AI-powered research synthesis combining market data, customer insights, and competitive analysis to identify the most promising opportunities in the target market.*

*Generated on: """
            + datetime.now().strftime("%Y-%m-%d")
            + "*"
        )

        return readme_content

    def create_issue_content_with_gpt5(
        self, idea: Dict, idea_number: int, jtbd_data: Dict, zone_data: Dict = None
    ) -> Dict[str, str]:
        """Use Claude or GPT to generate a killer GitHub issue that's like a pitch deck in markdown.
        
        This now uses the comprehensive README as context for richer issue generation.
        """
        
        try:
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
            
            # Try Claude first for better narrative quality
            try:
                import anthropic
                anthropic_key = os.getenv("ANTHROPIC_API_KEY")
                if anthropic_key:
                    client = anthropic.Anthropic(api_key=anthropic_key)
                    response = client.messages.create(
                        model="claude-opus-4-1-20250805",  # Using Opus 4.1 for superior pitch deck quality
                        max_tokens=8000,
                        temperature=0.8,
                        system="You are a world-class venture strategist creating definitive pitch decks for breakthrough innovations. Each issue should tell a compelling story that builds excitement and confidence in the opportunity.",
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )
                    gpt5_content = response.content[0].text
                    logger.info(f"✅ Generated compelling issue #{idea_number} with Claude Opus 4.1")
            except Exception as claude_error:
                logger.warning(f"Claude Opus 4.1 generation failed for issue {idea_number}, trying GPT-4o: {claude_error}")
                # Fall back to GPT-4o
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
            
        except Exception as e:
            # Fallback to enhanced manual generation if advanced models fail
            logger.warning(f"Advanced model generation failed for issue {idea_number}, using enhanced fallback: {e}")
            return self.create_issue_content_enhanced_fallback(idea, idea_number, jtbd_data)
    
    def create_issue_content_enhanced_fallback(
        self, idea: Dict, idea_number: int, jtbd_data: Dict
    ) -> Dict[str, str]:
        """Enhanced fallback that still creates a rich pitch-deck-style issue."""
        
        # Map JTBD IDs to actual job statements
        jtbd_map = {
            job["job_id"]: job
            for job in jtbd_data.get("jtbd_data", {}).get("jobs_list", [])
        }

        # Get target jobs details
        target_jobs_details = []
        for job_id in idea.get("target_jobs", []):
            if job_id in jtbd_map:
                job = jtbd_map[job_id]
                target_jobs_details.append(
                    f"- **{job_id}**: {job.get('job_statement', '')} (Opportunity Score: {job.get('opportunity_score', 'N/A')})"
                )
        
        # Generate rich markdown content
        issue_body = f"""# 🚀 {idea.get("name", f"Product Idea {idea_number}")}

> **{idea.get("value_proposition", "Revolutionary solution for the modern market")}**

---

## 📊 Executive Summary

<table>
<tr>
<td><strong>🎯 Market Size</strong></td>
<td>{idea.get("market_size", "$10B+")}</td>
<td><strong>📈 Growth Rate</strong></td>
<td>25-30% CAGR</td>
</tr>
<tr>
<td><strong>⏱️ Time to Market</strong></td>
<td>{idea.get("estimated_development_time", "6-9 months")}</td>
<td><strong>💰 Initial Investment</strong></td>
<td>{idea.get("estimated_cost", "$1-2M")}</td>
</tr>
<tr>
<td><strong>🏆 Competitive Advantage</strong></td>
<td colspan="3">{idea.get("competitive_advantage", "First-mover advantage with proprietary technology")}</td>
</tr>
</table>

---

## 🔥 The Problem

```mermaid
graph LR
    A[Current State] -->|Pain Point 1| B[User Frustration]
    B -->|Pain Point 2| C[Lost Revenue]
    C -->|Pain Point 3| D[Market Gap]
    D -->|Our Solution| E[Success]
    
    style A fill:#ff6b6b
    style B fill:#ff6b6b
    style C fill:#ff6b6b
    style D fill:#feca57
    style E fill:#48dbfb
```

### Jobs-to-be-Done We Solve:
{chr(10).join(target_jobs_details) if target_jobs_details else "- Addressing critical unmet needs in the market"}

---

## 💡 Our Solution

```mermaid
flowchart TB
    subgraph Platform
        A[User Interface] --> B[Core Engine]
        B --> C[AI/ML Layer]
        C --> D[Data Pipeline]
    end
    
    E[Users] --> A
    D --> F[Analytics]
    F --> G[Insights]
    G --> E
    
    style Platform fill:#e8f5e9
    style C fill:#4caf50
```

### 🎯 Key Features
{chr(10).join([f"- ✨ **{feature}**" for feature in idea.get("key_features", ["AI-powered automation", "Real-time collaboration", "Enterprise security", "Seamless integrations", "Advanced analytics"])])}

---

## 📈 Market Opportunity

### TAM - SAM - SOM Analysis

| Metric | Value | Calculation | Growth |
|--------|-------|-------------|--------|
| **TAM** (Total Addressable Market) | **$50B** | Global market size | 25% CAGR |
| **SAM** (Serviceable Addressable Market) | **$15B** | Our target segments | 30% CAGR |
| **SOM** (Serviceable Obtainable Market) | **$500M** | 5-year realistic capture | 40% CAGR |

### 🎯 Target Customer Segments
- **Primary**: {idea.get("target_market", "Enterprise (Fortune 500)")}
- **Secondary**: Mid-market companies (100-1000 employees)
- **Tertiary**: Tech-forward SMBs

---

## 💰 Business Model

```mermaid
graph TD
    A[Customer Acquisition] -->|Free Trial| B[Conversion]
    B -->|Subscription| C[MRR]
    C -->|Upsell| D[Expansion Revenue]
    D -->|Referrals| A
    
    C -->|Churn Prevention| E[Retention]
    E --> C
    
    style C fill:#4caf50
    style D fill:#2196F3
```

### Revenue Streams
| Stream | Model | Price Point | Margin |
|--------|-------|-------------|--------|
| **Core SaaS** | Subscription | $99-999/mo | 85% |
| **Enterprise** | Annual contracts | $50K-500K | 90% |
| **Add-ons** | Usage-based | Variable | 75% |
| **Services** | Implementation | $10K-100K | 60% |

---

## 🚀 Go-to-Market Strategy

<details>
<summary><b>📅 Launch Timeline (Click to expand)</b></summary>

### Phase 1: Foundation (Months 1-3)
- [ ] Complete MVP development
- [ ] Recruit 10 design partners
- [ ] Establish product-market fit
- [ ] Secure seed funding

### Phase 2: Launch (Months 4-6)
- [ ] Public beta release
- [ ] Content marketing campaign
- [ ] First 100 customers
- [ ] Series A fundraising

### Phase 3: Scale (Months 7-12)
- [ ] 1,000 customers
- [ ] International expansion
- [ ] Partner ecosystem
- [ ] Series B positioning

</details>

---

## 🏆 Competitive Analysis

| Feature | Us | Competitor A | Competitor B | Legacy Solution |
|---------|-----|--------------|--------------|-----------------|
| **AI-Powered** | ✅ Advanced | ⚠️ Basic | ❌ None | ❌ None |
| **Real-time** | ✅ <100ms | ⚠️ 1-5s | ⚠️ 2-10s | ❌ Batch |
| **Integrations** | ✅ 500+ | ⚠️ 50+ | ⚠️ 20+ | ❌ Limited |
| **Price** | 💰 Competitive | 💰💰 Premium | 💰 Low | 💰💰💰 Enterprise |
| **UX** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |

---

## 📊 Financial Projections

```mermaid
xychart-beta
    title "5-Year Revenue Projection"
    x-axis [Y1, Y2, Y3, Y4, Y5]
    y-axis "Revenue ($M)" 0 --> 100
    bar [2, 10, 30, 60, 100]
    line [2, 10, 30, 60, 100]
```

### Unit Economics
- **CAC**: $1,500
- **LTV**: $45,000
- **LTV/CAC**: 30x
- **Payback Period**: 6 months
- **Gross Margin**: 85%
- **Net Retention**: 120%

---

## 👥 Team Requirements

### Immediate Hires Needed:

| Role | Level | Skills | Priority |
|------|-------|--------|----------|
| **CTO** | Senior | 10+ years, scaled startups | 🔴 Critical |
| **Head of Product** | Senior | B2B SaaS experience | 🔴 Critical |
| **Lead Engineer** | Senior | Full-stack, AI/ML | 🟡 High |
| **Head of Sales** | Senior | Enterprise sales | 🟡 High |
| **Marketing Lead** | Mid | Growth marketing | 🟢 Medium |

---

## 🎯 Success Metrics

![](https://img.shields.io/badge/MRR-$100K-success)
![](https://img.shields.io/badge/Customers-100-blue)
![](https://img.shields.io/badge/NPS-70+-green)
![](https://img.shields.io/badge/Churn-<5%25-success)

### Key Milestones
- **Q1**: Product-market fit validation ✅
- **Q2**: $100K MRR
- **Q3**: Series A ($10M)
- **Q4**: 1,000 customers

---

## 🚨 Risk Mitigation

<details>
<summary><b>⚠️ Key Risks & Mitigation Strategies</b></summary>

### Technology Risk
- **Risk**: Scaling challenges at 10K users
- **Mitigation**: Microservices architecture from day 1

### Market Risk
- **Risk**: Slower enterprise adoption
- **Mitigation**: Parallel SMB strategy

### Competitive Risk
- **Risk**: Big Tech enters market
- **Mitigation**: Deep vertical integration & network effects

</details>

---

## 💎 Why This Wins

### The Unfair Advantages:
1. **Network Effects**: Each user makes platform more valuable
2. **Data Moat**: Proprietary dataset improves AI continuously
3. **Switching Costs**: Deep integration creates lock-in
4. **Brand**: First-mover advantage in category creation
5. **Team**: Founders have direct domain expertise

---

## 📋 Next Steps

### Immediate Actions:
- [ ] Schedule deep-dive session with investment committee
- [ ] Technical due diligence with CTO
- [ ] Customer reference calls (3 lined up)
- [ ] Review financial model in detail
- [ ] Term sheet discussion

### 📞 Contact for Partnership
**Ready to build the future together?**

[![Schedule Meeting](https://img.shields.io/badge/Schedule-Meeting-blue?style=for-the-badge)](https://calendly.com)
[![Email](https://img.shields.io/badge/Email-Team-green?style=for-the-badge)](mailto:team@venture.com)
[![Deck](https://img.shields.io/badge/Download-Deck-orange?style=for-the-badge)](https://deck.link)

---

*This opportunity won't last. The market is moving fast, and we're positioned to capture it.*

**🚀 Let's build something extraordinary together.**
"""
        
        return {
            "title": f"🚀 {idea.get('name', f'Product Idea {idea_number}')}",
            "body": issue_body
        }
    
    def create_issue_content(
        self, idea: Dict, idea_number: int, jtbd_data: Dict, zone_data: Dict = None
    ) -> Dict[str, str]:
        """Generate issue title and body for a product idea with comprehensive business pitch."""
        
        # Try advanced models first if available
        if self._should_use_gpt5():
            return self.create_issue_content_with_gpt5(idea, idea_number, jtbd_data, zone_data)
        else:
            return self.create_issue_content_enhanced_fallback(idea, idea_number, jtbd_data)

        # Extract comprehensive scoring data if available
        scoring_data = idea.get("scoring", {})
        viability_details = idea.get("viability_details", {})
        
        # Create compelling business pitch
        issue_body = f"""# 🚀 {idea.get("name", f"Product Idea {idea_number}")}

## 📋 Executive Summary

**{idea.get("value_proposition", idea.get("description", ""))}**

This solution addresses critical unmet needs in the market by targeting high-value jobs-to-be-done with an innovative approach that leverages cutting-edge technology and user-centric design principles.

## 🎯 Market Validation & Justification

### Why This Idea Wins

{self._generate_justification(idea, scoring_data)}

### Jobs-to-be-Done Addressed
{chr(10).join(target_jobs_details) if target_jobs_details else "- Addresses broad market needs identified through comprehensive research"}

### Market Evidence
- **Total Addressable Market**: {idea.get("market_size", "Multi-billion dollar opportunity")}
- **Target Customer Segments**: {idea.get("target_market", "Enterprise and SMB segments")}
- **Growth Trajectory**: High-growth market with {idea.get("growth_rate", "20-30%")} annual expansion
- **Competitive Landscape**: {idea.get("competitive_advantage", "Blue ocean opportunity with minimal direct competition")}

## 💎 Unique Value Proposition

### Core Innovation
{idea.get("differentiation", idea.get("value_proposition", "Revolutionary approach to solving persistent market problems"))}

### Key Differentiators
{self._generate_differentiators(idea)}

### Strategic Moat
{self._generate_moat_analysis(idea, viability_details)}

## 🏗️ Product Architecture

### Core Features
{chr(10).join([f"- **{feature}**" for feature in idea.get("key_features", ["AI-powered intelligence", "Real-time collaboration", "Enterprise-grade security", "Seamless integrations", "Advanced analytics"])])}

### Technical Innovation
{self._generate_technical_innovation(idea)}

### User Experience
- Intuitive interface designed for zero learning curve
- Mobile-first architecture with offline capabilities  
- Personalization engine for tailored experiences
- Accessibility-first design principles

## 📊 Business Model & Economics

### Revenue Streams
- **Primary**: {idea.get("revenue_model", "SaaS subscription with tiered pricing")}
- **Secondary**: Professional services, API access, marketplace commissions
- **Future**: Data insights, white-label solutions, ecosystem partnerships

### Unit Economics
- **Customer Acquisition Cost**: ${idea.get("cac", "500-1500")}
- **Lifetime Value**: ${idea.get("ltv", "15000-50000")}
- **Gross Margin**: {idea.get("gross_margin", "70-85%")}
- **Payback Period**: {idea.get("payback", "12-18 months")}

### Financial Projections
- **Year 1**: $2-5M ARR | 100-250 customers
- **Year 2**: $10-20M ARR | 500-1000 customers  
- **Year 3**: $30-50M ARR | 2000-3000 customers
- **Break-even**: {idea.get("break_even", "Month 18-24")}

## 🚀 Go-to-Market Strategy

### Launch Strategy
1. **Phase 1** (Months 1-3): Private beta with design partners
2. **Phase 2** (Months 4-6): Public beta with early adopter program
3. **Phase 3** (Months 7-9): General availability with full feature set
4. **Phase 4** (Months 10-12): Scale and expansion

### Distribution Channels
- Direct sales for enterprise accounts
- Self-service for SMB segment
- Partner channel program
- App marketplace presence
- Content marketing and thought leadership

### Customer Acquisition
- Product-led growth with freemium tier
- Strategic partnerships with complementary solutions
- Developer ecosystem and API strategy
- Community building and user advocacy

## 📈 Implementation Roadmap

### Immediate (0-3 months)
- Validate core assumptions with customer interviews
- Build MVP with essential features
- Recruit founding team members
- Secure initial funding/resources

### Short-term (3-6 months)
- Launch beta program with 10-20 design partners
- Iterate based on user feedback
- Develop go-to-market collateral
- Build initial sales pipeline

### Medium-term (6-12 months)
- Scale to 100+ customers
- Expand feature set based on user demands
- Establish partnerships
- Achieve product-market fit metrics

### Long-term (12+ months)
- International expansion
- Platform ecosystem development
- M&A opportunities
- Category leadership

## 🎯 Success Metrics & KPIs

### Product Metrics
- User activation rate: >60%
- Daily active users growth: 20% MoM
- Feature adoption rate: >40%
- NPS score: >50

### Business Metrics
- Monthly recurring revenue growth: 15-20%
- Customer acquisition cost payback: <18 months
- Gross revenue retention: >90%
- Net revenue retention: >120%

### Market Metrics
- Market share capture: 5-10% in 3 years
- Category awareness: Top 3 brand recognition
- Analyst recognition: Leader quadrant positioning

## 🔬 Feasibility Analysis

### Technical Feasibility: {idea.get("technical_feasibility", 8)}/10
{self._generate_technical_feasibility_analysis(idea, viability_details)}

### Market Readiness: {viability_details.get("market_readiness", 8)}/10
{self._generate_market_readiness_analysis(idea, viability_details)}

### Resource Requirements: {idea.get("resource_requirements", 6)}/10
- **Team**: 8-12 person cross-functional team
- **Timeline**: {idea.get("estimated_development_time", "6-9 months to MVP")}
- **Budget**: {idea.get("estimated_cost", "$1-2M initial investment")}
- **Infrastructure**: Cloud-native, scalable architecture

## ⚠️ Risk Analysis & Mitigation

### Key Risks
1. **Technology Risk**: {self._generate_risk_mitigation("technology", idea)}
2. **Market Risk**: {self._generate_risk_mitigation("market", idea)}
3. **Execution Risk**: {self._generate_risk_mitigation("execution", idea)}
4. **Competitive Risk**: {self._generate_risk_mitigation("competitive", idea)}

## 🏆 Why Prioritize This Idea

### Strategic Alignment
✅ Addresses high-value market opportunity
✅ Leverages emerging technology trends
✅ Creates sustainable competitive advantage
✅ Scalable business model with high margins
✅ Clear path to market leadership

### Innovation Score: {idea.get("innovation_score", 8)}/10
### Viability Score: {idea.get("viability_score", 8)}/10
### Overall Priority: {self._calculate_priority(idea)}

## 📋 Next Steps

1. **Week 1-2**: Conduct 20+ customer validation interviews
2. **Week 3-4**: Develop detailed product requirements document
3. **Week 5-6**: Create interactive prototype for user testing
4. **Week 7-8**: Build business case and secure resources
5. **Week 9-12**: Begin MVP development sprint

---
*Category*: {idea.get("category", "Innovative Solution")}
*Phase*: {self._determine_phase(idea)}
*Confidence Level*: {self._calculate_confidence(idea)}
"""

        return {
            "title": f"💡 {idea.get('name', f'Product Idea {idea_number}')}",
            "body": issue_body,
        }

    def _generate_justification(self, idea: Dict, scoring_data: Dict) -> str:
        """Generate market justification for the idea."""
        justifications = []
        
        if scoring_data.get("composite_score", 0) > 7:
            justifications.append("✅ **Top-tier composite score** indicating exceptional market fit and technical feasibility")
        
        if idea.get("viability_score", 0) > 7:
            justifications.append("✅ **High viability score** validated through comprehensive analysis")
            
        if idea.get("innovation_score", 0) > 7:
            justifications.append("✅ **Breakthrough innovation potential** with first-mover advantage")
            
        if scoring_data.get("is_breakthrough", False):
            justifications.append("✅ **Identified as breakthrough opportunity** with transformative market potential")
            
        if not justifications:
            justifications.append("✅ Solid market opportunity with clear customer need and achievable implementation path")
            
        return "\n".join(justifications)
    
    def _generate_differentiators(self, idea: Dict) -> str:
        """Generate key differentiators for the idea."""
        differentiators = idea.get("key_differentiators", [
            "- 10x improvement in user productivity through AI automation",
            "- First solution to integrate all workflow components seamlessly",
            "- Patent-pending technology for real-time optimization",
            "- Network effects that create increasing value with scale",
            "- Platform approach enabling ecosystem development"
        ])
        
        if isinstance(differentiators, list):
            return "\n".join([f"- {d}" for d in differentiators])
        return differentiators
    
    def _generate_moat_analysis(self, idea: Dict, viability_details: Dict) -> str:
        """Generate competitive moat analysis."""
        moat_score = viability_details.get("competitive_moat", 7)
        
        if moat_score >= 8:
            return "Strong competitive moat through network effects, proprietary technology, and first-mover advantage. High barriers to entry for competitors."
        elif moat_score >= 6:
            return "Solid defensibility through unique technology, brand positioning, and customer lock-in. Moderate barriers to entry."
        else:
            return "Initial competitive advantage through innovation and execution speed. Focus on rapid scaling to build defensibility."
    
    def _generate_technical_innovation(self, idea: Dict) -> str:
        """Generate technical innovation description."""
        innovations = idea.get("technical_innovations", [
            "- Advanced machine learning models for predictive analytics",
            "- Microservices architecture for infinite scalability",
            "- Real-time data processing pipeline with sub-second latency",
            "- Proprietary algorithms for optimization and matching",
            "- Edge computing capabilities for offline functionality"
        ])
        
        if isinstance(innovations, list):
            return "\n".join(innovations)
        return innovations
    
    def _generate_technical_feasibility_analysis(self, idea: Dict, viability_details: Dict) -> str:
        """Generate technical feasibility analysis."""
        score = viability_details.get("technical_feasibility", idea.get("technical_feasibility", 8))
        
        if score >= 8:
            return "Proven technology stack with experienced team. Low technical risk with clear implementation path."
        elif score >= 6:
            return "Solid technical foundation with some innovation required. Manageable technical challenges with mitigation strategies."
        else:
            return "Ambitious technical goals requiring R&D investment. Higher risk offset by transformative potential."
    
    def _generate_market_readiness_analysis(self, idea: Dict, viability_details: Dict) -> str:
        """Generate market readiness analysis."""
        score = viability_details.get("market_readiness", 8)
        
        if score >= 8:
            return "Market showing strong demand signals with early adopters actively seeking solutions. Optimal timing for entry."
        elif score >= 6:
            return "Growing market awareness with increasing pain point recognition. Good window for establishing leadership position."
        else:
            return "Emerging market requiring education and evangelism. Opportunity to define category and set standards."
    
    def _generate_risk_mitigation(self, risk_type: str, idea: Dict) -> str:
        """Generate risk mitigation strategies."""
        strategies = {
            "technology": "Phased development approach with regular validation milestones. Fallback to proven technologies if needed.",
            "market": "Extensive customer validation program with pivot options. Multiple go-to-market channels to reduce dependency.",
            "execution": "Experienced team with relevant domain expertise. Agile methodology with rapid iteration cycles.",
            "competitive": "Fast execution to market with continuous innovation. Building strong customer relationships and network effects."
        }
        
        return strategies.get(risk_type, "Comprehensive risk management framework with regular monitoring and mitigation strategies.")
    
    def _calculate_priority(self, idea: Dict) -> str:
        """Calculate overall priority for the idea."""
        viability = idea.get("viability_score", 5)
        innovation = idea.get("innovation_score", 5)
        market_opp = idea.get("market_opportunity", 5)
        
        avg_score = (viability + innovation + market_opp) / 3
        
        if avg_score >= 8:
            return "🔴 CRITICAL PRIORITY - Immediate action required"
        elif avg_score >= 6.5:
            return "🟡 HIGH PRIORITY - Fast-track development"
        elif avg_score >= 5:
            return "🟢 MEDIUM PRIORITY - Standard development cycle"
        else:
            return "⚪ LOW PRIORITY - Future consideration"
    
    def _calculate_confidence(self, idea: Dict) -> str:
        """Calculate confidence level for the idea."""
        scoring = idea.get("scoring", {})
        confidence = scoring.get("selection_confidence", 7)
        
        if confidence >= 8:
            return "⭐⭐⭐⭐⭐ Very High (90%+)"
        elif confidence >= 6:
            return "⭐⭐⭐⭐ High (75-90%)"
        elif confidence >= 4:
            return "⭐⭐⭐ Medium (50-75%)"
        else:
            return "⭐⭐ Low (Below 50%)"

    def _determine_phase(self, idea: Dict) -> str:
        """Determine implementation phase based on idea characteristics."""
        feasibility = idea.get("technical_feasibility", 5)
        opportunity = idea.get("market_opportunity", 5)
        resources = idea.get("resource_requirements", 5)

        # Quick wins: High feasibility, low resources
        if feasibility >= 7 and resources <= 6:
            return "Phase 1 (Quick Win)"
        # Strategic: High opportunity, moderate effort
        elif opportunity >= 8 and resources <= 7:
            return "Phase 2 (Strategic)"
        # Complex: High value but high effort
        elif opportunity >= 7 and resources >= 8:
            return "Phase 3 (Major Initiative)"
        # Long-term: Everything else
        else:
            return "Phase 4 (Future Consideration)"

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
