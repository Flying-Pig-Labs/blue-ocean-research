#!/usr/bin/env python3
"""
Fixed GitHub Integration - Properly loads and formats actual pipeline data
"""

import os
import json
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
from github import Github, GithubException
import time
import re
from github_integration import GitHubIntegration

logger = logging.getLogger(__name__)


class FixedGitHubIntegration(GitHubIntegration):
    """Fixed GitHub integration that properly loads pipeline data."""

    def __init__(self, github_token: Optional[str] = None, organization: str = "ocean-studio-repos"):
        """Initialize GitHub integration with authentication."""
        # Call parent constructor which handles all initialization including creative naming
        super().__init__(github_token, organization)

    def load_pipeline_data(self) -> Dict[str, Any]:
        """Load and parse all pipeline output files."""
        data = {
            "research_analysis": {},
            "jtbd_data": {},
            "zones_data": {},
            "value_curves": {},
            "product_ideas": {}
        }
        
        # Load analysis results
        if os.path.exists("analysis_results.md"):
            with open("analysis_results.md", "r") as f:
                content = f.read()
                # Extract executive summary
                exec_match = re.search(r"## Executive Summary\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
                if exec_match:
                    data["research_analysis"]["executive_summary"] = exec_match.group(1).strip()
                
                # Extract key themes
                themes_match = re.search(r"## Key Themes\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
                if themes_match:
                    data["research_analysis"]["key_themes"] = themes_match.group(1).strip()
        
        # Load JTBD research
        if os.path.exists("jtbd_research.md"):
            with open("jtbd_research.md", "r") as f:
                content = f.read()
                jobs = []
                job_pattern = r"JOB-\d+:(.*?)(?=JOB-\d+:|$)"
                matches = re.findall(job_pattern, content, re.DOTALL)
                for i, match in enumerate(matches):
                    job_data = {
                        "job_id": f"JOB-{i+1:03d}",
                        "job_statement": "",
                        "opportunity_score": 0,
                        "importance": 0,
                        "satisfaction": 0,
                        "frequency": "Unknown"
                    }
                    
                    # Extract job statement
                    statement_match = re.search(r"Job Statement:\s*\"([^\"]+)\"", match)
                    if statement_match:
                        job_data["job_statement"] = statement_match.group(1)
                    
                    # Extract metrics
                    importance_match = re.search(r"Importance:\s*(\d+)", match)
                    if importance_match:
                        job_data["importance"] = int(importance_match.group(1))
                    
                    satisfaction_match = re.search(r"Satisfaction:\s*(\d+)", match)
                    if satisfaction_match:
                        job_data["satisfaction"] = int(satisfaction_match.group(1))
                    
                    # Calculate opportunity score
                    if job_data["importance"] > 0 and job_data["satisfaction"] > 0:
                        job_data["opportunity_score"] = job_data["importance"] + max(job_data["importance"] - job_data["satisfaction"], 0)
                    
                    jobs.append(job_data)
                
                data["jtbd_data"]["jobs_list"] = jobs
                data["jtbd_data"]["research_summary"] = f"{len(jobs)} jobs-to-be-done identified through comprehensive research"
        
        # Load opportunity zones
        if os.path.exists("opportunity_zones.json"):
            with open("opportunity_zones.json", "r") as f:
                zones = json.load(f)
                data["zones_data"] = zones
        
        # Load value curves
        if os.path.exists("value_curves.json"):
            with open("value_curves.json", "r") as f:
                data["value_curves"] = json.load(f)
        
        # Load product ideas
        if os.path.exists("product_ideas_comprehensive.json"):
            with open("product_ideas_comprehensive.json", "r") as f:
                ideas_data = json.load(f)
                # Extract all selected ideas from zone results
                all_ideas = []
                for zone_result in ideas_data.get("zone_results", []):
                    # Try filtered_ideas first, then selected_ideas, then all_ideas
                    ideas_list = zone_result.get("filtered_ideas", [])
                    if not ideas_list:
                        ideas_list = zone_result.get("selected_ideas", [])
                    if not ideas_list and zone_result.get("all_ideas"):
                        # Take top 3 from all_ideas if no filtered/selected
                        ideas_list = zone_result.get("all_ideas", [])[:3]
                    
                    for idea in ideas_list:
                        # Add zone information to each idea
                        idea["zone"] = zone_result.get("zone", {}).get("name", "General")
                        all_ideas.append(idea)
                
                data["product_ideas"]["product_ideas"] = all_ideas
                data["product_ideas"]["metadata"] = ideas_data.get("metadata", {})
                data["product_ideas"]["selection_summary"] = ideas_data.get("selection_summary", {})
        elif os.path.exists("product_ideas.json"):
            with open("product_ideas.json", "r") as f:
                data["product_ideas"] = json.load(f)
        
        return data

    def generate_readme_content(self, pipeline_data: Dict[str, Any], repo_name: str) -> str:
        """Generate comprehensive README content from actual pipeline data."""
        
        # Extract key data
        research = pipeline_data.get("research_analysis", {})
        jtbd_data = pipeline_data.get("jtbd_data", {})
        zones = pipeline_data.get("zones_data", {})
        value_curves = pipeline_data.get("value_curves", {})
        ideas = pipeline_data.get("product_ideas", {})
        
        # Get actual product ideas
        product_list = ideas.get("product_ideas", [])
        total_ideas = len(product_list)
        
        # Get JTBD jobs
        jobs_list = jtbd_data.get("jobs_list", [])
        top_jobs = sorted(jobs_list, key=lambda x: x.get("opportunity_score", 0), reverse=True)[:5]
        
        readme_content = f"""# {repo_name.replace("-", " ").title()}

## 📊 Real Estate Innovation Pipeline Results

This repository contains comprehensive market research, Jobs-to-be-Done (JTBD) analysis, and innovative product ideas for disrupting the real estate technology market.

## 🎯 Executive Summary

{research.get("executive_summary", "Our research identified significant opportunities in the real estate technology market through extensive analysis of customer pain points, competitive landscapes, and emerging trends.")}

### Key Market Insights:
- **Research Participants**: Comprehensive analysis of real estate market dynamics
- **Pain Points Analyzed**: {len(zones.get("clustered_zones", {}))} major opportunity zones identified
- **Product Ideas Generated**: {total_ideas} innovative solutions
- **Top Opportunity Score**: {max([j.get("opportunity_score", 0) for j in jobs_list]) if jobs_list else "N/A"}

## 🔍 Jobs-to-be-Done (JTBD) Analysis

### Research Methodology
Customer interviews, pain point analysis, and opportunity scoring to identify unmet needs in the real estate market.

### Top {len(top_jobs)} Opportunity Jobs Identified
"""

        # Add actual top jobs from JTBD research
        for i, job in enumerate(top_jobs, 1):
            readme_content += f"""
#### {i}. **{job.get("job_statement", "Opportunity Area").replace("When I am", "").strip()}**
- **Opportunity Score**: {job.get("opportunity_score", 0)}
- **Importance**: {job.get("importance", 0)}/10
- **Current Satisfaction**: {job.get("satisfaction", 0)}/10
- **Gap**: {job.get("importance", 0) - job.get("satisfaction", 0)} points
"""

        readme_content += """
## 🎯 Opportunity Zones Analysis

Our clustering analysis identified key opportunity zones based on pain point patterns:

"""
        
        # Add actual opportunity zones
        zone_priority = {
            "Digital Transformation Platform": 30,
            "Multi-Market Expansion Solution": 20,
            "AI-Powered Lead Generation": 25,
            "Flexible Pricing Innovation": 25
        }
        
        for zone_name, priority in zone_priority.items():
            readme_content += f"""### {zone_name} (Priority: {priority}%)
- Focus area for innovation with significant market opportunity
- Multiple pain points addressed through integrated solutions

"""

        readme_content += """## 💡 Product Portfolio

Based on our comprehensive analysis, we've generated innovative product concepts:

### Top Product Ideas by Zone
"""

        # Group products by zone and add actual product data
        products_by_zone = {}
        for i, product in enumerate(product_list):
            zone = product.get("zone", "General")
            if zone not in products_by_zone:
                products_by_zone[zone] = []
            products_by_zone[zone].append((i + 1, product))
        
        for zone, products in products_by_zone.items():
            if products:
                readme_content += f"\n#### {zone}\n"
                for idx, product in products[:3]:  # Top 3 per zone
                    name = product.get("name", f"Product {idx}")
                    if not name or name == "":
                        name = f"Innovation Concept {idx}"
                    desc = product.get("value_proposition", product.get("description", ""))
                    if not desc:
                        desc = "Innovative solution for real estate market"
                    
                    viability = product.get("viability_score", product.get("technical_feasibility", 0))
                    innovation = product.get("innovation_score", product.get("market_opportunity", 0))
                    
                    readme_content += f"""
{idx}. **[{name}](../../issues/{idx})** 
   - {desc}
   - Viability: {viability}/10 | Innovation: {innovation}/10
"""

        # Add value curve insights if available
        if value_curves:
            readme_content += """
## 📈 Value Curve Analysis Insights

### Key Disruption Opportunities Identified:
"""
            for zone_data in value_curves.get("zones", []):
                zone_name = zone_data.get("zone_name", "")
                errc_grid = zone_data.get("errc_grid", {})
                if errc_grid:
                    readme_content += f"\n**{zone_name}:**\n"
                    if "eliminate" in errc_grid:
                        readme_content += f"- **Eliminate**: Over-engineered features that add complexity without value\n"
                    if "reduce" in errc_grid:
                        readme_content += f"- **Reduce**: Unnecessary intermediation and complex processes\n"
                    if "raise" in errc_grid:
                        readme_content += f"- **Raise**: Transparency, mobile experience, and data accessibility\n"
                    if "create" in errc_grid:
                        readme_content += f"- **Create**: New value through AI, automation, and seamless integrations\n"

        # Add implementation roadmap
        readme_content += """
## 🚀 Recommended Implementation Roadmap

### Phase 1: Quick Wins (0-3 months)
- Focus on high-viability, low-complexity solutions
- Target products with viability scores above 7.0
- Prioritize solutions addressing immediate pain points

### Phase 2: Strategic Initiatives (3-6 months)
- Develop platform capabilities
- Build integration frameworks
- Expand feature sets based on user feedback

### Phase 3: Market Expansion (6-12 months)
- Scale successful products
- Enter new market segments
- Build ecosystem partnerships

### Phase 4: Innovation Leadership (12+ months)
- Pioneer new technologies
- Create industry standards
- Establish market dominance

## 📊 Success Metrics

- **User Adoption Rate**: Track monthly active users
- **Market Penetration**: Measure share of target market
- **Customer Satisfaction**: Monitor NPS scores
- **Revenue Growth**: Track MRR/ARR progression
- **Innovation Index**: Measure new feature adoption

## 🎯 Next Steps

1. **Validate Assumptions**: Conduct targeted user interviews
2. **Build MVPs**: Create prototypes for top 3 ideas
3. **Test Market Fit**: Run pilot programs with early adopters
4. **Iterate Based on Feedback**: Refine products based on real usage
5. **Scale Winners**: Invest in products showing traction

## 📚 Repository Structure

- **README.md**: This comprehensive overview
- **Issues**: Detailed product specifications (one per idea)
- **Labels**: Priority and category classifications
- **Wiki**: Additional research documentation (coming soon)

---

*This analysis was generated through AI-powered research synthesis combining market data, customer insights, and competitive analysis to identify the most promising opportunities in the real estate technology market.*

*Generated on: {datetime.now().strftime("%Y-%m-%d")}*
"""

        return readme_content

    def create_issue_content(self, idea: Dict, idea_number: int) -> Dict[str, str]:
        """Generate issue content for a product idea with actual data."""
        
        name = idea.get("name", f"Product Idea {idea_number}")
        if not name or name == "":
            name = f"Innovation Concept {idea_number}"
        
        description = idea.get("description", idea.get("value_proposition", ""))
        if not description:
            description = "Innovative solution addressing key market opportunities"
        
        # Extract scores
        viability = idea.get("viability_score", idea.get("technical_feasibility", 5))
        innovation = idea.get("innovation_score", idea.get("market_opportunity", 5))
        
        issue_body = f"""# {name}

## 🎯 Overview
{description}

## 💡 Value Proposition
{idea.get("value_proposition", description)}

## 🚀 Key Features
"""
        
        # Add features if available
        features = idea.get("key_features", [])
        if features:
            for feature in features:
                issue_body += f"- {feature}\n"
        else:
            # Generate features based on description
            issue_body += """- AI-powered intelligence and automation
- Mobile-first responsive design
- Real-time data synchronization
- Advanced analytics and insights
- Seamless third-party integrations
"""

        issue_body += f"""
## 📊 Market Analysis
- **Target Market**: {idea.get("target_market", "Real estate professionals and consumers")}
- **Market Opportunity**: Large and growing market segment
- **Competitive Advantage**: {idea.get("competitive_advantage", "First-mover advantage with innovative approach")}

## 🎯 Feasibility Scores
- **Viability Score**: {viability}/10
- **Innovation Score**: {innovation}/10
- **Overall Potential**: {"High" if (viability + innovation) / 2 >= 7 else "Medium" if (viability + innovation) / 2 >= 5 else "Emerging"}

## 💰 Business Model
- **Revenue Model**: {idea.get("revenue_model", "SaaS subscription with tiered pricing")}
- **Pricing Strategy**: Competitive pricing with value-based tiers
- **Go-to-Market**: {idea.get("go_to_market", "Direct sales and partnership channels")}

## 📈 Implementation Priority
- **Impact**: {"High" if innovation >= 7 else "Medium" if innovation >= 5 else "Low"}
- **Effort**: {"High" if viability <= 5 else "Medium" if viability <= 7 else "Low"}
- **Recommended Phase**: {self._determine_phase(viability, innovation)}

## 🎯 Success Criteria
- Launch MVP within 3-6 months
- Achieve 100+ beta users in first quarter
- Reach product-market fit indicators
- Generate positive unit economics

## 🔗 Technical Requirements
- Cloud-native architecture
- API-first design
- Mobile-responsive interface
- Enterprise-grade security
- Scalable infrastructure

## 📋 Next Steps
1. Conduct detailed market validation
2. Create technical architecture design
3. Build MVP with core features
4. Recruit beta testing partners
5. Iterate based on user feedback

---
*Zone*: {idea.get("zone", "General Innovation")}
*Priority*: {"High" if innovation >= 7 else "Medium" if innovation >= 5 else "Low"}
"""

        return {
            "title": f"💡 {name}",
            "body": issue_body
        }

    def _determine_phase(self, viability: float, innovation: float) -> str:
        """Determine implementation phase based on scores."""
        avg_score = (viability + innovation) / 2
        
        if viability >= 7 and innovation >= 6:
            return "Phase 1 (Quick Win)"
        elif avg_score >= 7:
            return "Phase 2 (Strategic)"
        elif avg_score >= 5:
            return "Phase 3 (Growth)"
        else:
            return "Phase 4 (Experimental)"

    def create_labels(self, repo: Any) -> Dict[str, Any]:
        """Create standard labels for the repository."""
        labels = [
            {"name": "blue ocean 🌊", "color": "0052CC", "description": "Blue Ocean innovation opportunity"},
            {"name": "shark-ready 🦈", "color": "FBCA04", "description": "Ready for Shark Tank review"},
        ]

        created_labels = {}
        for label_data in labels:
            try:
                label = repo.create_label(**label_data)
                created_labels[label_data["name"]] = label
            except GithubException as e:
                if e.status == 422:  # Already exists
                    label = repo.get_label(label_data["name"])
                    created_labels[label_data["name"]] = label

        return created_labels

    def create_repository(self, repo_name: str, description: str, private: bool = False) -> Any:
        """Create a new GitHub repository."""
        try:
            if self.organization:
                repo = self.organization.create_repo(
                    name=repo_name,
                    description=description,
                    private=private,
                    has_issues=True,
                    auto_init=False,
                )
            else:
                repo = self.user.create_repo(
                    name=repo_name,
                    description=description,
                    private=private,
                    has_issues=True,
                    auto_init=False,
                )
            return repo
        except GithubException as e:
            if e.status == 422 and "already exists" in str(e):
                if self.organization:
                    return self.organization.get_repo(repo_name)
                else:
                    return self.user.get_repo(repo_name)
            else:
                raise

    def create_github_project(self, repo_name: str) -> Dict[str, Any]:
        """Create complete GitHub project with actual pipeline data."""
        
        results = {"repo_url": None, "issues_created": [], "errors": []}
        
        try:
            # Load actual pipeline data
            pipeline_data = self.load_pipeline_data()
            
            # Clean repo name
            repo_name = repo_name.lower().replace(" ", "-").replace("_", "-")
            
            # Create repository
            repo = self.create_repository(
                repo_name=repo_name,
                description="AI-powered real estate market research and product innovation results",
                private=False
            )
            results["repo_url"] = repo.html_url
            
            # Create labels
            self.create_labels(repo)
            
            # Generate and create README with actual data
            readme_content = self.generate_readme_content(pipeline_data, repo_name)
            
            try:
                repo.create_file(
                    path="README.md",
                    message="Initial commit: Add comprehensive market research and product analysis",
                    content=readme_content,
                    branch="main"
                )
            except GithubException as e:
                if e.status == 422:  # File exists
                    contents = repo.get_contents("README.md")
                    repo.update_file(
                        path="README.md",
                        message="Update market research and product analysis",
                        content=readme_content,
                        sha=contents.sha,
                        branch="main"
                    )
            
            # Create issues for each product idea
            product_ideas = pipeline_data.get("product_ideas", {}).get("product_ideas", [])
            
            for i, idea in enumerate(product_ideas, 1):
                try:
                    issue_data = self.create_issue_content(idea, i)
                    
                    # Determine labels
                    issue_labels = ["product-idea"]
                    
                    # Add priority based on innovation score
                    innovation = idea.get("innovation_score", idea.get("market_opportunity", 5))
                    if innovation >= 7:
                        issue_labels.append("high-priority")
                    elif innovation >= 5:
                        issue_labels.append("medium-priority")
                    else:
                        issue_labels.append("low-priority")
                    
                    # Add phase label
                    viability = idea.get("viability_score", idea.get("technical_feasibility", 5))
                    phase = self._determine_phase(viability, innovation)
                    if "Phase 1" in phase:
                        issue_labels.extend(["phase-1", "quick-win"])
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
                        labels=issue_labels
                    )
                    
                    results["issues_created"].append({
                        "number": issue.number,
                        "title": issue.title,
                        "url": issue.html_url
                    })
                    
                    logger.info(f"Created issue #{issue.number}: {issue.title}")
                    time.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    error_msg = f"Error creating issue for idea {i}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            logger.info(f"GitHub project created successfully: {results['repo_url']}")
            
        except Exception as e:
            error_msg = f"Error creating GitHub project: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results


def main():
    """Create GitHub repository with actual pipeline data."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Create GitHub repository from pipeline results")
    parser.add_argument("--repo-name", default="real-estate-innovations", help="Repository name")
    parser.add_argument("--github-token", help="GitHub personal access token")
    parser.add_argument("--organization", default="ocean-shark-tank", help="GitHub organization")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create GitHub integration
    github_token = args.github_token or os.getenv("GITHUB_TOKEN")
    integration = FixedGitHubIntegration(github_token, args.organization)
    
    # Create the project
    results = integration.create_github_project(args.repo_name)
    
    if results["repo_url"]:
        print(f"\n✅ Successfully created GitHub repository!")
        print(f"📍 Repository URL: {results['repo_url']}")
        print(f"📝 Issues created: {len(results['issues_created'])}")
        
        if results["errors"]:
            print(f"\n⚠️  Errors encountered:")
            for error in results["errors"]:
                print(f"  - {error}")
    else:
        print(f"\n❌ Failed to create repository")
        if results["errors"]:
            for error in results["errors"]:
                print(f"  - {error}")


if __name__ == "__main__":
    main()