#!/usr/bin/env python3
"""
Create GitHub Issues from markdown files
Reads issue content from github-issues/ directory and creates them on GitHub
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Initialize Rich console
console = Console()

# Load environment variables
load_dotenv()

class GitHubIssueCreator:
    """Create GitHub issues from markdown files"""
    
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        if not self.token:
            console.print("[red]Error: GITHUB_TOKEN not found in .env file![/red]")
            console.print("Please add: GITHUB_TOKEN=your_token_here to .env")
            sys.exit(1)
        
        # GitHub API configuration
        self.repo_owner = "Flying-Pig-Labs"
        self.repo_name = "helios"
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
        # Issue configurations
        self.issues = [
            {
                "file": "issue-1-integration-testing.md",
                "title": "Add Integration Testing CLI for Individual Component Testing",
                "labels": ["enhancement", "testing", "developer-tools"],
                "priority": 2
            },
            {
                "file": "issue-2-logging-system.md",
                "title": "Implement Comprehensive Logging System for CLI and File Output",
                "labels": ["enhancement", "logging", "monitoring"],
                "priority": 1
            },
            {
                "file": "issue-3-debug-mode.md",
                "title": "Add DEBUG Mode with Cost-Effective Model Switching",
                "labels": ["enhancement", "cost-optimization", "developer-tools"],
                "priority": 1
            },
            {
                "file": "issue-4-sophisticated-scoring.md",
                "title": "Implement Sophisticated Scoring with Smart Filtering",
                "labels": ["enhancement", "algorithm", "critical"],
                "priority": 3
            },
            {
                "file": "issue-5-mermaid-diagram-fix.md",
                "title": "Fix Mermaid Diagram for Accuracy and Clarity",
                "labels": ["documentation", "bug", "good-first-issue"],
                "priority": 0
            }
        ]
    
    def test_connection(self) -> bool:
        """Test GitHub API connection"""
        try:
            url = f"{self.api_base}/user"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                user_data = response.json()
                console.print(f"[green]✅ Connected as: {user_data.get('login', 'Unknown')}[/green]")
                return True
            else:
                console.print(f"[red]❌ Authentication failed: {response.status_code}[/red]")
                console.print(f"[yellow]Response: {response.text}[/yellow]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Connection error: {e}[/red]")
            return False
    
    def check_existing_issues(self) -> Dict[str, bool]:
        """Check which issues already exist"""
        existing = {}
        
        try:
            url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/issues"
            params = {"state": "all", "per_page": 100}
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                issues = response.json()
                existing_titles = [issue["title"] for issue in issues]
                
                for issue_config in self.issues:
                    existing[issue_config["title"]] = issue_config["title"] in existing_titles
                    
            return existing
            
        except Exception as e:
            console.print(f"[yellow]Warning: Could not check existing issues: {e}[/yellow]")
            return {}
    
    def create_issue(self, config: Dict) -> Optional[Dict]:
        """Create a single GitHub issue"""
        # Read issue content
        issue_file = Path("github-issues") / config["file"]
        if not issue_file.exists():
            console.print(f"[red]Error: Issue file not found: {issue_file}[/red]")
            return None
        
        with open(issue_file, 'r') as f:
            content = f.read()
        
        # Skip the title line if it's in the content
        lines = content.split('\n')
        if lines[0].startswith('#'):
            content = '\n'.join(lines[1:]).strip()
        
        # Prepare issue data
        issue_data = {
            "title": config["title"],
            "body": content,
            "labels": config["labels"]
        }
        
        # Create issue
        try:
            url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/issues"
            response = requests.post(url, headers=self.headers, json=issue_data)
            
            if response.status_code == 201:
                issue = response.json()
                return {
                    "number": issue["number"],
                    "url": issue["html_url"],
                    "title": issue["title"]
                }
            else:
                console.print(f"[red]Failed to create issue: {response.status_code}[/red]")
                console.print(f"[yellow]Response: {response.text}[/yellow]")
                return None
                
        except Exception as e:
            console.print(f"[red]Error creating issue: {e}[/red]")
            return None
    
    def run(self, skip_existing: bool = True, dry_run: bool = False):
        """Create all issues"""
        console.print(Panel.fit(
            "[bold green]GitHub Issue Creator[/bold green]\n"
            f"Repository: {self.repo_owner}/{self.repo_name}",
            border_style="green"
        ))
        
        # Test connection
        console.print("\n[cyan]Testing GitHub connection...[/cyan]")
        if not self.test_connection():
            return
        
        # Check existing issues
        console.print("\n[cyan]Checking existing issues...[/cyan]")
        existing = self.check_existing_issues()
        
        # Sort issues by priority
        sorted_issues = sorted(self.issues, key=lambda x: x["priority"])
        
        # Create issues
        created = []
        skipped = []
        failed = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=False,
        ) as progress:
            
            task = progress.add_task("Creating issues...", total=len(sorted_issues))
            
            for config in sorted_issues:
                title = config["title"]
                
                # Check if should skip
                if skip_existing and existing.get(title, False):
                    skipped.append(title)
                    console.print(f"[yellow]⏭️  Skipping existing issue: {title[:60]}...[/yellow]")
                    progress.update(task, advance=1)
                    continue
                
                # Dry run mode
                if dry_run:
                    console.print(f"[blue]🔍 Would create: {title}[/blue]")
                    progress.update(task, advance=1)
                    continue
                
                # Create issue
                progress.update(task, description=f"Creating: {title[:50]}...")
                result = self.create_issue(config)
                
                if result:
                    created.append(result)
                    console.print(f"[green]✅ Created issue #{result['number']}: {title[:60]}...[/green]")
                    console.print(f"   [dim]URL: {result['url']}[/dim]")
                else:
                    failed.append(title)
                
                progress.update(task, advance=1)
                
                # Rate limiting - GitHub allows 5000 requests/hour but let's be nice
                if not dry_run:
                    time.sleep(1)
        
        # Summary
        console.print("\n" + "="*80)
        console.print(Panel.fit(
            f"[bold]Summary[/bold]\n\n"
            f"✅ Created: {len(created)} issues\n"
            f"⏭️  Skipped: {len(skipped)} existing issues\n"
            f"❌ Failed: {len(failed)} issues",
            border_style="cyan"
        ))
        
        if created:
            console.print("\n[green]Created Issues:[/green]")
            for issue in created:
                console.print(f"  #{issue['number']}: {issue['title'][:60]}...")
                console.print(f"         {issue['url']}")
        
        if failed:
            console.print("\n[red]Failed Issues:[/red]")
            for title in failed:
                console.print(f"  - {title}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Create GitHub issues from markdown files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create all issues (skip existing)
  python create_github_issues.py
  
  # Create all issues (including existing)
  python create_github_issues.py --no-skip
  
  # Dry run - see what would be created
  python create_github_issues.py --dry-run
  
  # Test connection only
  python create_github_issues.py --test
        """
    )
    
    parser.add_argument("--no-skip", action="store_true", 
                       help="Create issues even if they already exist")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be created without actually creating")
    parser.add_argument("--test", action="store_true",
                       help="Test GitHub connection only")
    
    args = parser.parse_args()
    
    # Initialize creator
    creator = GitHubIssueCreator()
    
    if args.test:
        creator.test_connection()
    else:
        creator.run(
            skip_existing=not args.no_skip,
            dry_run=args.dry_run
        )


if __name__ == "__main__":
    main()