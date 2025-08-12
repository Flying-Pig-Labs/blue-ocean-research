#!/usr/bin/env python3
"""
Create GitHub Issues - Simple version with no external dependencies
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

# ANSI color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_color(message, color=RESET):
    """Print colored message"""
    print(f"{color}{message}{RESET}")


def load_env():
    """Load environment variables from .env file"""
    env_path = Path(".env")
    if not env_path.exists():
        return {}

    env_vars = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
    return env_vars


class GitHubIssueCreator:
    def __init__(self):
        # Load environment
        env_vars = load_env()
        self.token = env_vars.get("GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")

        if not self.token:
            print_color("Error: GITHUB_TOKEN not found!", RED)
            print("Please add GITHUB_TOKEN=your_token to .env file")
            sys.exit(1)

        # GitHub API configuration
        self.repo_owner = "Flying-Pig-Labs"
        self.repo_name = "helios"
        self.api_base = "https://api.github.com"

        # Issue configurations (simplified - using only common labels)
        self.issues = [
            {
                "file": "issue-5-mermaid-diagram-fix.md",
                "title": "Fix Mermaid Diagram for Accuracy and Clarity",
                "labels": ["documentation", "bug"],
                "priority": 0,
            },
            {
                "file": "issue-2-logging-system.md",
                "title": "Implement Comprehensive Logging System for CLI and File Output",
                "labels": ["enhancement"],
                "priority": 1,
            },
            {
                "file": "issue-3-debug-mode.md",
                "title": "Add DEBUG Mode with Cost-Effective Model Switching",
                "labels": ["enhancement"],
                "priority": 1,
            },
            {
                "file": "issue-1-integration-testing.md",
                "title": "Add Integration Testing CLI for Individual Component Testing",
                "labels": ["enhancement"],
                "priority": 2,
            },
            {
                "file": "issue-4-sophisticated-scoring.md",
                "title": "Implement Sophisticated Scoring with Smart Filtering",
                "labels": ["enhancement"],
                "priority": 3,
            },
        ]

    def api_request(self, method, endpoint, data=None):
        """Make API request to GitHub"""
        url = f"{self.api_base}{endpoint}"

        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
            "User-Agent": "Python-Issue-Creator",
        }

        request = urllib.request.Request(url, headers=headers, method=method)

        if data:
            request.data = json.dumps(data).encode("utf-8")

        try:
            with urllib.request.urlopen(request) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            print_color(f"HTTP Error {e.code}: {error_body}", RED)
            return None
        except Exception as e:
            print_color(f"Error: {e}", RED)
            return None

    def test_connection(self):
        """Test GitHub API connection"""
        print_color("Testing GitHub connection...", CYAN)
        result = self.api_request("GET", "/user")

        if result:
            print_color(f"✅ Connected as: {result.get('login', 'Unknown')}", GREEN)
            return True
        else:
            print_color("❌ Authentication failed", RED)
            return False

    def check_existing_issues(self):
        """Check which issues already exist"""
        print_color("\nChecking existing issues...", CYAN)

        existing = {}
        page = 1

        while True:
            result = self.api_request(
                "GET",
                f"/repos/{self.repo_owner}/{self.repo_name}/issues?state=all&per_page=100&page={page}",
            )
            if not result:
                break

            if not result:  # Empty page means we're done
                break

            for issue in result:
                for issue_config in self.issues:
                    if issue["title"] == issue_config["title"]:
                        existing[issue_config["title"]] = True

            page += 1

            if len(result) < 100:  # Last page
                break

        return existing

    def create_issue(self, config):
        """Create a single GitHub issue"""
        # Read issue content
        issue_file = Path("github-issues") / config["file"]
        if not issue_file.exists():
            print_color(f"Error: Issue file not found: {issue_file}", RED)
            return None

        with open(issue_file, "r") as f:
            content = f.read()

        # Skip the title line if it's in the content
        lines = content.split("\n")
        if lines[0].startswith("#"):
            content = "\n".join(lines[1:]).strip()

        # Prepare issue data
        issue_data = {
            "title": config["title"],
            "body": content,
            "labels": config["labels"],
        }

        # Create issue
        result = self.api_request(
            "POST", f"/repos/{self.repo_owner}/{self.repo_name}/issues", issue_data
        )

        if result:
            return {
                "number": result["number"],
                "url": result["html_url"],
                "title": result["title"],
            }
        else:
            return None

    def run(self, dry_run=False):
        """Create all issues"""
        print_color(f"\n{BOLD}GitHub Issue Creator{RESET}", GREEN)
        print(f"Repository: {self.repo_owner}/{self.repo_name}")
        print("-" * 50)

        # Test connection
        if not self.test_connection():
            return

        # Check existing issues
        existing = self.check_existing_issues()

        # Sort issues by priority
        sorted_issues = sorted(self.issues, key=lambda x: x["priority"])

        # Create issues
        created = []
        skipped = []
        failed = []

        print_color(f"\nProcessing {len(sorted_issues)} issues...\n", CYAN)

        for i, config in enumerate(sorted_issues, 1):
            title = config["title"]
            title_short = title[:60] + "..." if len(title) > 60 else title

            # Check if should skip
            if existing.get(title, False):
                skipped.append(title)
                print_color(
                    f"[{i}/{len(sorted_issues)}] ⏭️  Skipping existing: {title_short}",
                    YELLOW,
                )
                continue

            # Dry run mode
            if dry_run:
                print_color(
                    f"[{i}/{len(sorted_issues)}] 🔍 Would create: {title_short}", BLUE
                )
                continue

            # Create issue
            print(
                f"[{i}/{len(sorted_issues)}] Creating: {title_short}...",
                end="",
                flush=True,
            )
            result = self.create_issue(config)

            if result:
                created.append(result)
                print_color(
                    f"\r[{i}/{len(sorted_issues)}] ✅ Created #{result['number']}: {title_short}",
                    GREEN,
                )
                print(f"     URL: {result['url']}")
            else:
                failed.append(title)
                print_color(
                    f"\r[{i}/{len(sorted_issues)}] ❌ Failed: {title_short}", RED
                )

            # Rate limiting
            if not dry_run and i < len(sorted_issues):
                time.sleep(1)

        # Summary
        print("\n" + "=" * 70)
        print_color(f"{BOLD}Summary{RESET}", CYAN)
        print(f"✅ Created: {len(created)} issues")
        print(f"⏭️  Skipped: {len(skipped)} existing issues")
        print(f"❌ Failed: {len(failed)} issues")

        if created:
            print_color("\nCreated Issues:", GREEN)
            for issue in created:
                print(f"  #{issue['number']}: {issue['title'][:60]}...")
                print(f"         {issue['url']}")

        if failed:
            print_color("\nFailed Issues:", RED)
            for title in failed:
                print(f"  - {title}")


def main():
    """Main entry point"""
    # Simple argument parsing
    dry_run = "--dry-run" in sys.argv
    test_only = "--test" in sys.argv

    if "--help" in sys.argv:
        print("""
GitHub Issue Creator - Simple Version

Usage:
  python create_github_issues_simple.py              # Create issues
  python create_github_issues_simple.py --dry-run    # Show what would be created
  python create_github_issues_simple.py --test       # Test connection only
  python create_github_issues_simple.py --help       # Show this help
""")
        return

    # Initialize creator
    creator = GitHubIssueCreator()

    if test_only:
        creator.test_connection()
    else:
        creator.run(dry_run=dry_run)


if __name__ == "__main__":
    main()
