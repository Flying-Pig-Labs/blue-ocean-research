#!/usr/bin/env python3
"""
GitHub Writer Module - Create/Update Repository, README, and Issues

Handles the creation and updating of GitHub repositories with synthesized opportunities.
Provides idempotent operations - updates existing issues by slug, never duplicates.
"""

import os
import json
import logging
import hashlib
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

class GitHubWriter:
    """Handles GitHub repository creation and content management."""
    
    def __init__(self, github_token: str, organization: str = "ocean-studio-repos"):
        """Initialize GitHub writer with authentication."""
        self.token = github_token
        self.organization = organization
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
    def create_repository_name(self, flavor_config: Any) -> str:
        """Create repository name based on flavor configuration."""
        base_name = flavor_config.output.repo_naming_pattern
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        repo_name = base_name.format(
            flavor_name=flavor_config.name,
            timestamp=timestamp
        )
        
        # Sanitize repository name for GitHub requirements
        repo_name = re.sub(r'[^a-zA-Z0-9\-_.]', '-', repo_name)
        repo_name = re.sub(r'-+', '-', repo_name)  # Remove multiple dashes
        repo_name = repo_name.strip('-')  # Remove leading/trailing dashes
        
        return repo_name[:100]  # GitHub limit is 100 characters
    
    def create_or_get_repository(self, repo_name: str, flavor_config: Any) -> Dict[str, Any]:
        """Create repository or get existing one."""
        # Check if repository exists
        repo_url = f"{self.base_url}/repos/{self.organization}/{repo_name}"
        response = requests.get(repo_url, headers=self.headers)
        
        if response.status_code == 200:
            logger.info(f"Repository {repo_name} already exists")
            return response.json()
        
        # Create new repository
        create_url = f"{self.base_url}/orgs/{self.organization}/repos"
        repo_data = {
            "name": repo_name,
            "description": f"{flavor_config.description} - Generated opportunities",
            "private": flavor_config.output.use_private_repo,
            "has_issues": True,
            "has_projects": True,
            "has_wiki": False,
            "auto_init": True,
            "gitignore_template": "Python"
        }
        
        response = requests.post(create_url, headers=self.headers, json=repo_data)
        
        if response.status_code == 201:
            repo_info = response.json()
            logger.info(f"Created repository: {repo_info['html_url']}")
            return repo_info
        else:
            raise Exception(f"Failed to create repository: {response.status_code} - {response.text}")
    
    def generate_readme_content(
        self, 
        opportunities: List[Dict[str, Any]], 
        flavor_config: Any,
        framework_results: List[Any]
    ) -> str:
        """Generate README.md content for the repository."""
        framework_name = flavor_config.framework.framework_type.value.upper()
        schema_type = flavor_config.output.schema_type.value.replace('_', ' ').title()
        
        readme_content = f"""# {flavor_config.name.title().replace('_', ' ')} Opportunities

{flavor_config.description}

## Overview

This repository contains {len(opportunities)} synthesized opportunities generated using the **{framework_name} framework** for {schema_type.lower()} analysis.

### Framework Analysis

**Framework:** {framework_name}  
**Analysis Date:** {datetime.now().strftime('%Y-%m-%d')}  
**Total Opportunity Zones:** {len(framework_results)}  
**Output Schema:** {schema_type}

### Framework Dimensions

"""
        
        # Add framework-specific dimension explanations
        if framework_results:
            sample_result = framework_results[0]
            if hasattr(sample_result, 'scores'):
                readme_content += "| Dimension | Description |\n|-----------|-------------|\n"
                
                dimension_descriptions = {
                    'eliminate': 'Industry factors that should be eliminated completely',
                    'reduce': 'Factors that should be reduced well below industry standards',
                    'raise': 'Factors that should be raised well above industry standards',
                    'create': 'New factors that the industry has never offered',
                    'functional': 'Core functional jobs and tasks to be accomplished',
                    'emotional': 'Emotional outcomes and feelings desired by users',
                    'social': 'Social perception and status considerations',
                    'accessibility': 'Transportation, connectivity, and physical access',
                    'infrastructure': 'Power, telecommunications, and utility infrastructure',
                    'regulatory': 'Regulatory compliance and policy environment',
                    'economic': 'Cost efficiency and financial viability',
                    'environmental': 'Environmental sustainability and climate factors',
                    'performance': 'Speed, efficiency, and capability requirements',
                    'cost': 'Development, manufacturing, and operational costs',
                    'usability': 'User experience and ease of use',
                    'reliability': 'Safety, durability, and dependability',
                    'scalability': 'Growth potential and future expansion'
                }
                
                for dimension in sample_result.scores.keys():
                    description = dimension_descriptions.get(dimension, f"{dimension.replace('_', ' ').title()} analysis dimension")
                    readme_content += f"| **{dimension.replace('_', ' ').title()}** | {description} |\n"
        
        readme_content += f"""

## Opportunities Summary

| ID | Title | Confidence | Zone | Framework Score |
|----|-------|------------|------|-----------------|
"""
        
        # Add opportunities table
        for opp in opportunities:
            title_link = f"[{opp['title']}](../../issues?q=is%3Aissue+{opp['id']})"
            confidence = f"{opp['confidence_score']:.1%}"
            zone_name = opp['zone_name'][:30] + "..." if len(opp['zone_name']) > 30 else opp['zone_name']
            
            # Calculate overall framework score
            framework_scores = opp.get('framework_scores', {})
            avg_score = sum(framework_scores.values()) / len(framework_scores) if framework_scores else 0
            framework_score = f"{avg_score:.1%}"
            
            readme_content += f"| `{opp['id']}` | {title_link} | {confidence} | {zone_name} | {framework_score} |\n"
        
        readme_content += f"""

## Analysis Methodology

### Data Sources
- **Reddit Discussions**: Authentic user conversations and pain points
- **Jobs-to-be-Done Analysis**: Customer need identification and clustering  
- **{framework_name} Framework**: Strategic analysis of opportunity zones
- **AI-Powered Synthesis**: LLM-generated opportunities with validation

### Quality Metrics
- **Evidence-Based**: All opportunities backed by Reddit discussion citations
- **Framework-Validated**: Each opportunity scored across {framework_name} dimensions
- **Confidence Scoring**: Opportunities ranked by confidence and evidence strength
- **Schema Compliance**: All opportunities validated against {schema_type.lower()} schema

### Repository Structure

```
├── README.md (this file)
├── issues/ (10 opportunities as GitHub issues)
├── manifest.json (run metadata and validation hashes)
└── analysis_data/ (source data and framework results)
```

## Issue Labels

This repository uses the following labels for categorization:

"""
        
        # Add issue labels
        for label in flavor_config.output.issue_labels:
            readme_content += f"- `{label}`\n"
        
        readme_content += f"""

## Usage

Each opportunity is documented as a GitHub issue with:

1. **YAML Front Matter**: Structured metadata for programmatic access
2. **Executive Summary**: Business rationale and opportunity description  
3. **Framework Analysis**: Detailed scoring across {framework_name} dimensions
4. **Evidence Citations**: Links to supporting Reddit discussions and data
5. **Implementation Guidance**: Next steps and considerations

## Reproducibility

This analysis is fully reproducible using:
- **Flavor Configuration**: `{flavor_config.name}.yaml`
- **Pipeline Version**: Modular ideation pipeline v2.0
- **Deterministic Processing**: Same inputs produce identical results
- **Audit Trail**: Complete manifest with hashes and timestamps

---

*Generated by [Modular Ideation Pipeline](https://github.com/Flying-Pig-Labs/blue-ocean-research) using the `{flavor_config.name}` flavor*

*Analysis completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}*
"""
        
        return readme_content
    
    def create_or_update_readme(self, repo_info: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Create or update README.md file."""
        repo_full_name = repo_info['full_name']
        
        # Check if README exists
        readme_url = f"{self.base_url}/repos/{repo_full_name}/contents/README.md"
        response = requests.get(readme_url, headers=self.headers)
        
        file_data = {
            "message": "Update README with opportunity analysis",
            "content": content.encode('utf-8').hex()  # GitHub API expects hex-encoded content
        }
        
        if response.status_code == 200:
            # Update existing README
            existing_readme = response.json()
            file_data["sha"] = existing_readme["sha"]
            logger.info("Updating existing README.md")
        else:
            # Create new README
            logger.info("Creating new README.md")
        
        response = requests.put(readme_url, headers=self.headers, json=file_data)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Failed to update README: {response.status_code} - {response.text}")
    
    def generate_issue_slug(self, opportunity: Dict[str, Any]) -> str:
        """Generate URL-safe slug from opportunity title."""
        title = opportunity['title'].lower()
        # Remove special characters and replace spaces with hyphens
        slug = re.sub(r'[^a-z0-9\s-]', '', title)
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'-+', '-', slug)  # Remove multiple hyphens
        return slug.strip('-')[:50]  # Limit length
    
    def generate_issue_body(self, opportunity: Dict[str, Any], flavor_config: Any) -> str:
        """Generate GitHub issue body with YAML front matter."""
        framework_scores = opportunity.get('framework_scores', {})
        
        # YAML front matter
        yaml_frontmatter = f"""---
opportunity_id: {opportunity['id']}
flavor: {flavor_config.name}
schema_type: {flavor_config.output.schema_type.value}
confidence_score: {opportunity['confidence_score']}
zone_id: {opportunity['zone_id']}
zone_name: {opportunity['zone_name']}
framework_scores:
"""
        
        for dimension, score in framework_scores.items():
            yaml_frontmatter += f"  {dimension}: {score}\n"
        
        yaml_frontmatter += f"""created_timestamp: {opportunity['created_timestamp']}
---

"""
        
        # Issue body content
        issue_body = yaml_frontmatter
        
        issue_body += f"""# {opportunity['title']}

## Executive Summary

{opportunity['description']}

## Business Rationale

{opportunity['rationale']}

## Framework Analysis

**Overall Confidence:** {opportunity['confidence_score']:.1%}

### {flavor_config.framework.framework_type.value.upper()} Dimension Scores

| Dimension | Score | Analysis |
|-----------|-------|----------|
"""
        
        # Add framework dimension analysis
        for dimension, score in framework_scores.items():
            dimension_name = dimension.replace('_', ' ').title()
            score_pct = f"{score:.1%}"
            
            # Get analysis from rationales if available (would come from framework results)
            analysis = f"Score indicates {score_pct} strength in this dimension"
            
            issue_body += f"| **{dimension_name}** | {score_pct} | {analysis} |\n"
        
        # Add schema-specific fields
        schema_type = flavor_config.output.schema_type.value
        
        if schema_type == 'business_idea':
            issue_body += f"""

## Business Details

**Target Market:** {opportunity.get('target_market', 'Not specified')}

**Value Proposition:** {opportunity.get('value_proposition', 'Not specified')}

**Revenue Model:** {opportunity.get('revenue_model', 'Not specified')}

**Competitive Advantage:** {opportunity.get('competitive_advantage', 'Not specified')}

**Implementation Timeline:** {opportunity.get('implementation_timeline', 'Not specified')}

**Risk Factors:**
"""
            risk_factors = opportunity.get('risk_factors', [])
            for risk in risk_factors:
                issue_body += f"- {risk}\n"
                
        elif schema_type == 'site_candidate':
            issue_body += f"""

## Site Details

**Location Type:** {opportunity.get('location_type', 'Not specified')}

**Target Business Category:** {opportunity.get('target_business_category', 'Not specified')}

**Accessibility Score:** {opportunity.get('accessibility_score', 'N/A')}

**Site Requirements:**
"""
            site_reqs = opportunity.get('site_requirements', [])
            for req in site_reqs:
                issue_body += f"- {req}\n"
                
        elif schema_type == 'device_spec':
            issue_body += f"""

## Device Specifications

**Device Category:** {opportunity.get('device_category', 'Not specified')}

**Target Population:** {opportunity.get('target_population', 'Not specified')}

**Clinical Indication:** {opportunity.get('clinical_indication', 'Not specified')}

**Regulatory Pathway:** {opportunity.get('regulatory_pathway', 'Not specified')}

**Functional Requirements:**
"""
            func_reqs = opportunity.get('functional_requirements', [])
            for req in func_reqs:
                issue_body += f"- {req}\n"
        
        # Evidence citations
        issue_body += f"""

## Evidence & Citations

This opportunity is supported by the following evidence:

"""
        
        citations = opportunity.get('citations', [])
        for i, citation in enumerate(citations, 1):
            issue_body += f"{i}. {citation}\n"
        
        # Implementation next steps
        issue_body += f"""

## Next Steps

1. **Validation**: Conduct market validation interviews with target users
2. **Competitive Analysis**: Deep dive into competitive landscape
3. **Technical Feasibility**: Assess implementation requirements and constraints
4. **Business Model**: Refine revenue model and go-to-market strategy
5. **Prototype Development**: Build MVP for initial testing

## Metadata

- **Generated by:** Modular Ideation Pipeline
- **Flavor:** `{flavor_config.name}`
- **Analysis Framework:** {flavor_config.framework.framework_type.value.upper()}
- **Confidence Level:** {opportunity['confidence_score']:.1%}
- **Zone Source:** {opportunity['zone_name']}

---

*This opportunity was synthesized from real user discussions and validated using the {flavor_config.framework.framework_type.value.upper()} strategic framework.*
"""
        
        return issue_body
    
    def create_or_update_issue(
        self, 
        repo_info: Dict[str, Any], 
        opportunity: Dict[str, Any], 
        flavor_config: Any
    ) -> Dict[str, Any]:
        """Create or update GitHub issue for opportunity (idempotent)."""
        repo_full_name = repo_info['full_name']
        opportunity_id = opportunity['id']
        
        # Generate issue title with flavor tag
        title = f"[{flavor_config.name}] {opportunity['title']}"
        
        # Check if issue already exists by searching for opportunity_id
        search_url = f"{self.base_url}/search/issues"
        search_params = {
            'q': f'repo:{repo_full_name} in:body {opportunity_id}',
            'type': 'issue'
        }
        
        response = requests.get(search_url, headers=self.headers, params=search_params)
        
        if response.status_code == 200:
            search_results = response.json()
            existing_issues = search_results.get('items', [])
            
            # Filter to exact opportunity_id match
            matching_issues = [
                issue for issue in existing_issues 
                if opportunity_id in issue.get('body', '')
            ]
            
            if matching_issues:
                # Update existing issue
                existing_issue = matching_issues[0]
                issue_number = existing_issue['number']
                
                logger.info(f"Updating existing issue #{issue_number} for opportunity {opportunity_id}")
                
                update_url = f"{self.base_url}/repos/{repo_full_name}/issues/{issue_number}"
                issue_data = {
                    "title": title,
                    "body": self.generate_issue_body(opportunity, flavor_config),
                    "labels": flavor_config.output.issue_labels
                }
                
                response = requests.patch(update_url, headers=self.headers, json=issue_data)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    raise Exception(f"Failed to update issue #{issue_number}: {response.status_code} - {response.text}")
        
        # Create new issue
        logger.info(f"Creating new issue for opportunity {opportunity_id}")
        
        create_url = f"{self.base_url}/repos/{repo_full_name}/issues"
        issue_data = {
            "title": title,
            "body": self.generate_issue_body(opportunity, flavor_config),
            "labels": flavor_config.output.issue_labels
        }
        
        response = requests.post(create_url, headers=self.headers, json=issue_data)
        
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to create issue: {response.status_code} - {response.text}")
    
    def write_github_artifacts(
        self, 
        opportunities: List[Dict[str, Any]], 
        flavor_config: Any,
        framework_results: List[Any]
    ) -> Dict[str, Any]:
        """
        Complete GitHub artifact creation: repository, README, and issues.
        
        Returns:
            Dict with repository info, README info, and issue details
        """
        # Create repository name
        repo_name = self.create_repository_name(flavor_config)
        
        # Create or get repository
        repo_info = self.create_or_get_repository(repo_name, flavor_config)
        
        # Generate and update README
        readme_content = self.generate_readme_content(opportunities, flavor_config, framework_results)
        readme_info = self.create_or_update_readme(repo_info, readme_content)
        
        # Create or update issues
        issue_results = []
        
        for opportunity in opportunities:
            try:
                issue_info = self.create_or_update_issue(repo_info, opportunity, flavor_config)
                issue_results.append({
                    'opportunity_id': opportunity['id'],
                    'issue_number': issue_info['number'],
                    'issue_url': issue_info['html_url'],
                    'title': issue_info['title']
                })
                logger.info(f"Processed issue #{issue_info['number']}: {opportunity['title']}")
                
            except Exception as e:
                logger.error(f"Failed to create/update issue for {opportunity['id']}: {e}")
                issue_results.append({
                    'opportunity_id': opportunity['id'],
                    'error': str(e)
                })
        
        return {
            'repository': {
                'name': repo_info['name'],
                'full_name': repo_info['full_name'],
                'html_url': repo_info['html_url'],
                'private': repo_info['private']
            },
            'readme': {
                'updated': True,
                'size': len(readme_content)
            },
            'issues': issue_results,
            'summary': {
                'total_opportunities': len(opportunities),
                'issues_created_or_updated': len([r for r in issue_results if 'issue_number' in r]),
                'issues_failed': len([r for r in issue_results if 'error' in r])
            }
        }

def write_github_artifacts(
    opportunities: List[Dict[str, Any]], 
    flavor_config: Any,
    framework_results: List[Any],
    github_token: str = None
) -> Dict[str, Any]:
    """
    Main function to create GitHub repository with opportunities.
    
    Args:
        opportunities: List of synthesized opportunity dictionaries
        flavor_config: Complete flavor configuration
        framework_results: Framework analysis results
        github_token: GitHub API token (uses environment variable if not provided)
        
    Returns:
        Dictionary with GitHub artifact creation results
    """
    if not github_token:
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            raise ValueError("GitHub token required - set GITHUB_TOKEN environment variable")
    
    # Use organization from flavor config or default
    organization = getattr(flavor_config.stage_overrides.get('github_integration', {}), 'organization', 'ocean-studio-repos')
    
    writer = GitHubWriter(github_token, organization)
    
    try:
        results = writer.write_github_artifacts(opportunities, flavor_config, framework_results)
        
        logger.info(f"GitHub artifacts created successfully:")
        logger.info(f"  Repository: {results['repository']['html_url']}")
        logger.info(f"  Issues: {results['summary']['issues_created_or_updated']} created/updated")
        
        return results
        
    except Exception as e:
        logger.error(f"GitHub artifact creation failed: {e}")
        raise