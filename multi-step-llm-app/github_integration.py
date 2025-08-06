#!/usr/bin/env python3
"""
GitHub Integration Module

This module handles the creation of GitHub repositories, README generation,
and issue creation based on the analysis results from the multi-step LLM app.
"""

import os
import logging
from typing import Dict, Optional, Any
from datetime import datetime
from github import Github, GithubException
import time


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
        """Generate comprehensive README content from analysis results."""

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

    def create_issue_content(
        self, idea: Dict, idea_number: int, jtbd_data: Dict
    ) -> Dict[str, str]:
        """Generate issue title and body for a product idea."""

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

        issue_body = f"""# Product Idea: {idea.get("name", f"Product Idea {idea_number}")}

## 🎯 Overview
{idea.get("description", "")}

## 🔍 Target Jobs-to-be-Done
{chr(10).join(target_jobs_details) if target_jobs_details else "- No specific JTBD mapped"}

## 💡 Value Proposition
{idea.get("value_proposition", "")}

## 🚀 Key Features
{chr(10).join([f"- {feature}" for feature in idea.get("key_features", [])])}

## 📊 Market Analysis
- **Target Market**: {idea.get("target_market", "N/A")}
- **Market Size**: {idea.get("market_size", "N/A")}
- **Competitive Advantage**: {idea.get("competitive_advantage", "N/A")}

## 🎯 Feasibility Scores
- **Technical Feasibility**: {idea.get("technical_feasibility", "N/A")}/10
- **Market Opportunity**: {idea.get("market_opportunity", "N/A")}/10
- **Resource Requirements**: {idea.get("resource_requirements", "N/A")}/10
- **Risk Level**: {idea.get("risk_level", "N/A")}/10

## 💰 Business Case
- **Estimated Development Time**: {idea.get("estimated_development_time", "N/A")}
- **Estimated Cost**: {idea.get("estimated_cost", "N/A")}
- **Revenue Model**: {idea.get("revenue_model", "N/A")}
- **Go-to-Market Strategy**: {idea.get("go_to_market", "N/A")}

## 📈 Implementation Priority
Based on the impact/effort matrix:
- **Impact**: {"High" if idea.get("market_opportunity", 0) >= 8 else "Medium" if idea.get("market_opportunity", 0) >= 6 else "Low"}
- **Effort**: {"High" if idea.get("resource_requirements", 0) >= 8 else "Medium" if idea.get("resource_requirements", 0) >= 6 else "Low"}
- **Recommended Phase**: {self._determine_phase(idea)}

## 🎯 Success Criteria
- Primary KPIs to track
- Target metrics for success
- Validation milestones

## 🔗 Dependencies
- Technical dependencies
- Market dependencies
- Resource dependencies

## 📋 Next Steps
1. Validate market assumptions
2. Create detailed technical specifications
3. Develop MVP requirements
4. Identify potential partners
5. Create go-to-market plan

---
*Category*: {idea.get("category", "General")}
*Priority*: {"High" if idea.get("market_opportunity", 0) >= 8 else "Medium" if idea.get("market_opportunity", 0) >= 6 else "Low"}
"""

        return {
            "title": f"💡 {idea.get('name', f'Product Idea {idea_number}')}",
            "body": issue_body,
        }

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
                        issue_data = self.create_issue_content(idea, i, jtbd_data)

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
    organization: str = "ocean-shark-tank",
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
