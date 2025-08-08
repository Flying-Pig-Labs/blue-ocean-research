#!/usr/bin/env python3
"""
Enhanced GitHub repository creation with context, appendix, and table of contents
"""

import os
import json
import shutil
from datetime import datetime, timedelta
from github import Github, GithubException
import time

# Import the fixed GitHub integration
from fix_github_integration import FixedGitHubIntegration


class EnhancedGitHubIntegration(FixedGitHubIntegration):
    """Enhanced GitHub integration with appendix and context"""
    
    def create_appendix_files(self, repo):
        """Upload all pipeline documents to appendix directory"""
        appendix_files = [
            ("analysis_results.md", "Stage 1: Market Research Analysis"),
            ("jtbd_research.md", "Stage 2: Jobs-to-be-Done Research"),
            ("jtbd_research_pain_points.txt", "Stage 2: Extracted Pain Points"),
            ("opportunity_zones.json", "Stage 3: Clustered Opportunity Zones"),
            ("value_curves.json", "Stage 4: Value Curve Analysis Data"),
            ("value_curves_report.md", "Stage 4: Value Curve Report"),
            ("product_ideas.json", "Stage 5: Product Ideas"),
            ("product_ideas_comprehensive.json", "Stage 5: Comprehensive Product Analysis"),
            ("jobs_to_be_done.json", "Structured JTBD Data"),
            ("research_analysis.json", "Research Summary Data")
        ]
        
        uploaded_files = []
        
        for filename, description in appendix_files:
            if os.path.exists(filename):
                try:
                    with open(filename, 'r') as f:
                        content = f.read()
                    
                    # Upload to appendix directory
                    path = f"appendix/{filename}"
                    repo.create_file(
                        path=path,
                        message=f"Add {description} to appendix",
                        content=content,
                        branch="main"
                    )
                    uploaded_files.append((path, description))
                    print(f"  ✓ Uploaded {path}")
                    time.sleep(0.5)  # Rate limiting
                except Exception as e:
                    print(f"  ✗ Error uploading {filename}: {e}")
        
        return uploaded_files
    
    def generate_enhanced_readme(self, pipeline_data, repo_name, appendix_files, start_time):
        """Generate README with context, TOC, and all existing content"""
        
        # Calculate processing time
        processing_time = datetime.now() - start_time
        minutes = int(processing_time.total_seconds() / 60)
        
        # Get current date
        report_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        readme_content = f"""# 🚀 Innovation Pipeline Results

## 📋 Report Context

**Generated**: {report_date}  
**Processing Time**: {minutes} minutes by Ocean Studio  
**Pipeline Version**: 7-Stage AI-Powered Innovation Discovery

### 🎯 Purpose of This Document

This document provides **clear, actionable conditions** that innovation teams can use to build products with real market impact. It synthesizes:
- Raw market research data
- Customer pain points and jobs-to-be-done
- Competitive landscape analysis
- Opportunity zones with quantified potential
- Specific product ideas with viability scores

The insights are designed to reduce the risk of building products nobody wants by grounding innovation in actual market needs and validated opportunities.

---

## 📚 Table of Contents

### Research Documentation
All source documents from the 7-stage pipeline are preserved in the `appendix/` directory:

| Document | Description | Stage |
|----------|-------------|-------|
| [📄 Raw Research Data](appendix/raw_research_data.json) | *Original market research from S3 (pending)* | Input |
"""
        
        # Add appendix files to TOC
        for path, description in appendix_files:
            filename = path.split('/')[-1]
            icon = "📊" if filename.endswith('.json') else "📝"
            stage = description.split(':')[0] if ':' in description else "Output"
            readme_content += f"| [{icon} {filename}]({path}) | {description} | {stage} |\n"
        
        readme_content += """
### Quick Navigation
- [Executive Summary](#-executive-summary)
- [Jobs-to-be-Done Analysis](#-jobs-to-be-done-jtbd-analysis)
- [Opportunity Zones](#-opportunity-zones-analysis)
- [Product Portfolio](#-product-portfolio)
- [Implementation Roadmap](#-recommended-implementation-roadmap)
- [Success Metrics](#-success-metrics)

---

"""
        
        # Now add all the original content
        original_readme = super().generate_readme_content(pipeline_data, repo_name)
        
        # Remove the title from original (since we have our own)
        if original_readme.startswith(f"# {repo_name}"):
            lines = original_readme.split('\n')
            original_readme = '\n'.join(lines[1:])
        
        readme_content += original_readme
        
        # Add appendix reference at the bottom
        readme_content += """

---

## 📎 Appendix

All research documents, data files, and intermediate analysis outputs are available in the [`appendix/`](appendix/) directory. These provide full traceability from raw research to final product recommendations.

### Document Structure:
```
appendix/
├── 📄 raw_research_data.json     # Original S3 research data (pending)
├── 📝 analysis_results.md        # Stage 1: Research synthesis
├── 📝 jtbd_research.md          # Stage 2: JTBD discovery
├── 📊 opportunity_zones.json     # Stage 3: Opportunity clustering
├── 📝 value_curves_report.md    # Stage 4: Competitive analysis
├── 📊 product_ideas.json        # Stage 5: Product concepts
└── 📊 [additional files]        # Supporting data and analysis
```

For questions about this analysis or to request additional insights, please contact the Ocean Studio team.

"""
        
        return readme_content
    
    def create_enhanced_github_project(self, repo_name, start_time):
        """Create enhanced GitHub project with appendix"""
        
        results = {"repo_url": None, "issues_created": [], "errors": [], "appendix_files": []}
        
        try:
            # Load pipeline data
            pipeline_data = self.load_pipeline_data()
            
            # Clean repo name
            repo_name = repo_name.lower().replace(" ", "-").replace("_", "-")
            
            # Create repository
            repo = self.create_repository(
                repo_name=repo_name,
                description="AI-powered innovation pipeline results with market research, JTBD analysis, and product recommendations",
                private=False
            )
            results["repo_url"] = repo.html_url
            
            # Create labels
            self.create_labels(repo)
            
            # Upload appendix files first
            print("\n📁 Creating appendix with research documents...")
            appendix_files = self.create_appendix_files(repo)
            results["appendix_files"] = appendix_files
            
            # Generate enhanced README
            readme_content = self.generate_enhanced_readme(pipeline_data, repo_name, appendix_files, start_time)
            
            try:
                repo.create_file(
                    path="README.md",
                    message="Initial commit: Add comprehensive innovation analysis with full documentation",
                    content=readme_content,
                    branch="main"
                )
                print("  ✓ Created enhanced README.md")
            except GithubException as e:
                if e.status == 422:  # File exists
                    contents = repo.get_contents("README.md")
                    repo.update_file(
                        path="README.md",
                        message="Update innovation analysis with enhanced context and documentation",
                        content=readme_content,
                        sha=contents.sha,
                        branch="main"
                    )
                    print("  ✓ Updated README.md")
            
            # Create issues for product ideas
            print("\n💡 Creating product idea issues...")
            product_ideas = pipeline_data.get("product_ideas", {}).get("product_ideas", [])
            
            for i, idea in enumerate(product_ideas, 1):
                try:
                    issue_data = self.create_issue_content(idea, i)
                    
                    # Only assign blue ocean label
                    issue_labels = ["blue ocean 🌊"]
                    
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
                    
                    print(f"  ✓ Created issue #{issue.number}: {issue.title}")
                    time.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    error_msg = f"Error creating issue for idea {i}: {str(e)}"
                    print(f"  ✗ {error_msg}")
                    results["errors"].append(error_msg)
            
            print(f"\n✅ Enhanced GitHub project created successfully!")
            print(f"📍 Repository: {results['repo_url']}")
            
        except Exception as e:
            error_msg = f"Error creating GitHub project: {str(e)}"
            print(f"\n❌ {error_msg}")
            results["errors"].append(error_msg)
        
        return results


def main():
    """Create enhanced GitHub repository"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Create enhanced GitHub repository with context and appendix")
    parser.add_argument("--repo-name", default="innovation-pipeline-enhanced", help="Repository name")
    parser.add_argument("--organization", default="ocean-shark-tank", help="GitHub organization")
    
    args = parser.parse_args()
    
    # Track start time
    start_time = datetime.now()
    
    # Create enhanced GitHub integration
    github_token = os.getenv("GITHUB_TOKEN")
    integration = EnhancedGitHubIntegration(github_token, args.organization)
    
    # Create the enhanced project
    results = integration.create_enhanced_github_project(args.repo_name, start_time)
    
    if results["repo_url"]:
        print(f"\n🎉 Success!")
        print(f"📍 Repository URL: {results['repo_url']}")
        print(f"📁 Appendix files: {len(results['appendix_files'])}")
        print(f"💡 Issues created: {len(results['issues_created'])}")
        
        if results["errors"]:
            print(f"\n⚠️  Some errors occurred:")
            for error in results["errors"]:
                print(f"  - {error}")
    else:
        print(f"\n❌ Failed to create repository")
        if results["errors"]:
            for error in results["errors"]:
                print(f"  - {error}")


if __name__ == "__main__":
    main()