#!/usr/bin/env python3
"""
Update product_idea_generator.py to use enhanced GitHub integration
"""

import os
import re

# Read the original file
with open("product_idea_generator.py", "r") as f:
    content = f.read()

# New import statement
new_import = """# Import GitHub integration
from github_integration import create_github_output
from create_enhanced_github_repo import EnhancedGitHubIntegration"""

# Replace the import
content = content.replace(
    """# Import GitHub integration
from github_integration import create_github_output""",
    new_import
)

# Find the GitHub integration section and replace it
old_github_section = """            # Call GitHub integration
            try:
                github_result = create_github_output(
                    research_analysis=research_analysis,
                    jtbd_data=jtbd_data,
                    zones_data=zones_data,
                    ideas_data=ideas_data,
                    repo_name=github_repo_name,
                    create_issues=True,
                    private=github_private,
                )

                if github_result["success"]:
                    console.print(
                        f"[green]✅ GitHub repository created: {github_result['repo_url']}[/green]"
                    )
                    console.print(
                        f"[green]✅ Created {github_result['issues_created']} issues[/green]"
                    )
                else:
                    console.print(
                        f"[red]❌ GitHub creation failed: {github_result.get('error', 'Unknown error')}[/red]"
                    )

            except Exception as e:
                console.print(f"[red]❌ GitHub integration error: {str(e)}[/red]")
                console.print(
                    "[yellow]Make sure GITHUB_TOKEN environment variable is set[/yellow]"
                )"""

new_github_section = """            # Track start time for processing duration
            import datetime
            pipeline_start_time = datetime.datetime.now()
            
            # Create appendix files list
            appendix_files_to_upload = [
                (value_curves_file, "Stage 4: Value Curve Analysis"),
                (json_output, "Stage 5: Product Ideas"),
                (comprehensive_json_path, "Stage 5: Comprehensive Analysis"),
                (report_output, "Stage 5: Product Ideas Report"),
            ]
            
            # Add other pipeline files if they exist
            other_files = [
                ("analysis_results.md", "Stage 1: Market Research Analysis"),
                ("jtbd_research.md", "Stage 2: Jobs-to-be-Done Research"),
                ("jtbd_research_pain_points.txt", "Stage 2: Extracted Pain Points"),
                ("opportunity_zones.json", "Stage 3: Clustered Opportunity Zones"),
                ("value_curves_report.md", "Stage 4: Value Curve Report"),
                ("jobs_to_be_done.json", "Structured JTBD Data"),
                ("research_analysis.json", "Research Summary Data"),
            ]
            
            for filename, description in other_files:
                if os.path.exists(filename) and filename not in [f[0] for f in appendix_files_to_upload]:
                    appendix_files_to_upload.append((filename, description))
            
            # Use enhanced GitHub integration
            try:
                # Initialize enhanced GitHub integration
                github_token = os.getenv("GITHUB_TOKEN")
                organization = "ocean-shark-tank"  # Default organization
                
                enhanced_github = EnhancedGitHubIntegration(github_token, organization)
                
                # Create repository
                repo = enhanced_github.create_repository(
                    repo_name=github_repo_name,
                    description="AI-powered innovation pipeline results with market research, JTBD analysis, and product recommendations",
                    private=github_private
                )
                
                # Create labels
                enhanced_github.create_labels(repo)
                
                # Upload appendix files
                console.print("\n[cyan]📁 Creating appendix with research documents...[/cyan]")
                uploaded_files = []
                for filename, description in appendix_files_to_upload:
                    if os.path.exists(filename):
                        try:
                            with open(filename, 'r') as f:
                                file_content = f.read()
                            
                            path = f"appendix/{filename}"
                            repo.create_file(
                                path=path,
                                message=f"Add {description} to appendix",
                                content=file_content,
                                branch="main"
                            )
                            uploaded_files.append((path, description))
                            console.print(f"  ✓ Uploaded {path}")
                            import time
                            time.sleep(0.5)  # Rate limiting
                        except Exception as e:
                            console.print(f"  ✗ Error uploading {filename}: {e}")
                
                # Load pipeline data
                pipeline_data = {
                    "research_analysis": research_analysis,
                    "jtbd_data": jtbd_data,
                    "zones_data": zones_data,
                    "value_curves": {},
                    "product_ideas": ideas_data
                }
                
                # Generate enhanced README
                readme_content = enhanced_github.generate_enhanced_readme(
                    pipeline_data, 
                    github_repo_name, 
                    uploaded_files, 
                    pipeline_start_time
                )
                
                # Create README
                repo.create_file(
                    path="README.md",
                    message="Add comprehensive innovation analysis with full documentation",
                    content=readme_content,
                    branch="main"
                )
                console.print("  ✓ Created enhanced README.md")
                
                # Create issues for product ideas
                console.print("\n[cyan]💡 Creating product idea issues...[/cyan]")
                issues_created = 0
                
                for i, idea in enumerate(ideas_data.get("product_ideas", []), 1):
                    try:
                        issue_data = enhanced_github.create_issue_content(idea, i)
                        
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
                        
                        # Create the issue
                        issue = repo.create_issue(
                            title=issue_data["title"],
                            body=issue_data["body"],
                            labels=issue_labels
                        )
                        
                        console.print(f"  ✓ Created issue #{issue.number}: {issue.title}")
                        issues_created += 1
                        import time
                        time.sleep(0.5)  # Rate limiting
                        
                    except Exception as e:
                        console.print(f"  ✗ Error creating issue for {idea.get('name', f'idea {i}')}: {e}")
                
                console.print(
                    f"[green]✅ Enhanced GitHub repository created: {repo.html_url}[/green]"
                )
                console.print(
                    f"[green]✅ Created {issues_created} issues with {len(uploaded_files)} appendix documents[/green]"
                )
                
            except Exception as e:
                console.print(f"[red]❌ GitHub integration error: {str(e)}[/red]")
                console.print(
                    "[yellow]Make sure GITHUB_TOKEN environment variable is set[/yellow]"
                )"""

# Replace the section
content = content.replace(old_github_section, new_github_section)

# Save as new file
with open("product_idea_generator_enhanced.py", "w") as f:
    f.write(content)

print("Created product_idea_generator_enhanced.py with enhanced GitHub integration")
print("\nTo update the original file, run:")
print("cp product_idea_generator_enhanced.py product_idea_generator.py")