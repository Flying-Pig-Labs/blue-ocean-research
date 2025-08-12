#!/usr/bin/env python3
"""
Pipeline Cleanup Script - Maintenance Utility

Purpose: Safely removes all generated files from pipeline executions while preserving
         source code, configuration, and essential project files.

This utility module provides comprehensive cleanup functionality for the innovation
pipeline, removing all generated outputs while carefully preserving source code,
configuration files, and version control. It's essential for maintaining a clean
workspace between pipeline runs and after testing.

Key Features:
- Pattern-based file matching for comprehensive cleanup
- Preservation list to protect important files
- Dry-run mode for safety verification
- Interactive confirmation to prevent accidents
- Detailed reporting of cleanup actions
- Error handling for locked or protected files

Usage Scenarios:
1. Clean workspace after successful pipeline run
2. Remove test artifacts after test suite execution
3. Reset environment before new pipeline execution
4. Clean up failed pipeline runs
5. Prepare for git commits (remove untracked outputs)

Usage:
    python cleanup_pipeline.py              # Interactive mode with confirmation
    python cleanup_pipeline.py --dry-run    # Preview what would be deleted
    python cleanup_pipeline.py --force      # Skip confirmation (use with caution)
    
Safety Features:
- Never deletes source code files
- Preserves .env and configuration
- Protects .git directory
- Maintains logs directory structure
"""

import os
import glob
import argparse
from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


class PipelineCleanup:
    """
    Orchestrates safe cleanup of pipeline-generated files.
    
    This class manages the identification and removal of all files generated
    during pipeline execution while carefully preserving essential project
    files. It uses pattern matching to identify outputs and maintains
    preservation lists to protect important files.
    
    The cleanup process follows these steps:
    1. Scan directory for files matching cleanup patterns
    2. Filter out preserved files and directories
    3. Present findings to user (or execute in dry-run)
    4. Request confirmation (unless forced)
    5. Remove identified files with error handling
    6. Report results and any errors encountered
    
    Attributes:
        CLEANUP_PATTERNS: List of glob patterns for files to remove
        PRESERVE_FILES: Set of specific files to never delete
        PRESERVE_DIRS: Set of directories to never enter
        dry_run: If True, only preview without deleting
        files_to_remove: List of files identified for removal
        files_removed: List of successfully removed files
        errors: List of (file, error) tuples for failures
        
    Methods:
        find_files_to_clean: Scans for removable files
        is_safe_to_remove: Validates file can be deleted
        clean: Executes the cleanup operation
        display_summary: Shows cleanup results
    """

    # Define file patterns to clean
    # These patterns match all outputs from the 7-stage pipeline
    # Organized by pipeline stage for clarity
    CLEANUP_PATTERNS = [
        # Stage 1: Research Analysis outputs
        "analysis_results.md",              # Primary analysis output
        "analysis_results_*.md",            # Timestamped versions
        # Stage 2: JTBD & Reddit Discovery outputs
        "jtbds_*.txt",                      # Timestamped JTBD files
        "reddit_discussions_*.csv",         # Reddit discussion data
        "reddit_analysis_*.xlsx",           # Optional analysis spreadsheet
        "jtbd_research.md",                 # Legacy format
        "jtbd_research_*.md",               # Legacy timestamped
        "pain_points.txt",                  # Legacy pain points
        "pain_points_*.txt",                # Legacy timestamped
        "*_pain_points.txt",                # Legacy pattern
        # Stage 3: Opportunity Zone Analysis outputs
        "opportunity_zones.json",            # Standard output
        "opportunity_zones_advanced.json",   # Advanced analysis
        "opportunity_zones_*.json",          # Timestamped versions
        # Stage 4: Value Curve Mapping outputs (deprecated)
        "value_curves.json",                 # Legacy value curves
        "value_curves_*.json",               # Legacy timestamped
        "value_curves_report.md",            # Legacy report
        "value_curves_report_*.md",          # Legacy timestamped
        # Stage 4: Product Idea Generation outputs
        "product_ideas.json",                # Primary output (10 ideas)
        "product_ideas_*.json",              # Timestamped versions
        "product_ideas_report.md",           # Human-readable report
        "product_ideas_report_*.md",         # Timestamped reports
        "product_ideas_comprehensive.json",  # Full unfiltered output
        "product_ideas_report_comprehensive.md", # Comprehensive report
        # Stage 5: Idea Consolidation outputs
        "final_innovation_portfolio.json",   # Enriched portfolio
        "final_innovation_portfolio_*.json", # Timestamped versions
        "final_innovation_portfolio_summary.md", # Executive summary
        # Test outputs
        "test_*.json",
        "test_*.md",
        "test_*.txt",
        # Debug and log files
        "debug_*.log",
        "pipeline_*.log",
        "*.log",
        # Temporary files
        "*.tmp",
        ".~*",
        "*~",
    ]

    # Files to preserve (never delete)
    PRESERVE_FILES = {
        "README.md",
        "requirements.txt",
        ".env",
        ".env.example",
        ".gitignore",
        "example_research.json",
    }

    # Directories to preserve
    PRESERVE_DIRS = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        "src",
        "tests",
        "prompts",
        "docs",
        ".claude",
        "logs",  # Preserve logs directory but can clean contents
    }

    def __init__(self, dry_run: bool = False):
        """
        Initialize the pipeline cleanup handler.
        
        Args:
            dry_run: If True, only preview files to be deleted without
                    actually removing them. Useful for verification.
        """
        self.dry_run = dry_run
        self.files_to_remove: List[str] = []
        self.files_removed: List[str] = []
        self.errors: List[tuple[str, str]] = []

    def find_files_to_clean(self) -> None:
        """Find all files matching cleanup patterns"""
        self.files_to_remove = []

        for pattern in self.CLEANUP_PATTERNS:
            matches = glob.glob(pattern)
            for file_path in matches:
                # Check if it's a file and not in preserve list
                if (
                    os.path.isfile(file_path)
                    and os.path.basename(file_path) not in self.PRESERVE_FILES
                    and not any(
                        file_path.startswith(d + "/") for d in self.PRESERVE_DIRS
                    )
                ):
                    self.files_to_remove.append(file_path)

        # Remove duplicates and sort
        self.files_to_remove = sorted(set(self.files_to_remove))

    def display_files_to_clean(self) -> None:
        """Display files that will be cleaned"""
        if not self.files_to_remove:
            console.print("[green]No files to clean up![/green]")
            return

        table = Table(
            title=f"Files to {'Remove' if not self.dry_run else 'be Removed'}"
        )
        table.add_column("File", style="cyan")
        table.add_column("Size", style="yellow", justify="right")

        total_size = 0
        for file_path in self.files_to_remove:
            try:
                size = os.path.getsize(file_path)
                total_size += size
                size_str = self.format_size(size)
                table.add_row(file_path, size_str)
            except OSError:
                table.add_row(file_path, "N/A")

        console.print(table)
        console.print(
            f"\n[bold]Total:[/bold] {len(self.files_to_remove)} files, {self.format_size(total_size)}"
        )

    def clean_files(self) -> None:
        """Remove files (or simulate if dry run)"""
        if self.dry_run:
            console.print("\n[yellow]DRY RUN - No files will be removed[/yellow]")
            return

        console.print("\n[cyan]Removing files...[/cyan]")

        with console.status("[bold green]Cleaning...") as status:
            for file_path in self.files_to_remove:
                try:
                    os.remove(file_path)
                    self.files_removed.append(file_path)
                    status.update(f"[bold green]Removed:[/bold green] {file_path}")
                except Exception as e:
                    self.errors.append((file_path, str(e)))

    def display_results(self) -> None:
        """Display cleanup results"""
        if self.dry_run:
            return

        # Success summary
        if self.files_removed:
            console.print(
                f"\n[green]✓ Successfully removed {len(self.files_removed)} files[/green]"
            )

        # Error summary
        if self.errors:
            console.print(f"\n[red]✗ Failed to remove {len(self.errors)} files:[/red]")
            for file_path, error in self.errors:
                console.print(f"  - {file_path}: {error}")

    def clean_logs_directory(self) -> None:
        """Clean contents of logs directory if it exists"""
        logs_dir = "logs"
        if os.path.exists(logs_dir) and os.path.isdir(logs_dir):
            console.print(f"\n[cyan]Cleaning {logs_dir} directory...[/cyan]")

            for file_name in os.listdir(logs_dir):
                file_path = os.path.join(logs_dir, file_name)
                if os.path.isfile(file_path) and file_name.endswith(".log"):
                    try:
                        if not self.dry_run:
                            os.remove(file_path)
                            console.print(f"  [green]✓[/green] Removed: {file_path}")
                        else:
                            console.print(
                                f"  [yellow]Would remove:[/yellow] {file_path}"
                            )
                    except Exception as e:
                        console.print(
                            f"  [red]✗[/red] Failed to remove {file_path}: {e}"
                        )

    @staticmethod
    def format_size(size: int) -> str:
        """Format file size in human-readable format"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def run(self, interactive: bool = True) -> bool:
        """Run the cleanup process"""
        console.print(
            Panel.fit(
                "[bold blue]Pipeline Output Cleanup[/bold blue]\n"
                "Removes all generated files from pipeline execution",
                border_style="blue",
            )
        )

        # Find files
        self.find_files_to_clean()

        # Display files
        self.display_files_to_clean()

        if not self.files_to_remove:
            return True

        # Confirm if interactive
        if interactive and not self.dry_run:
            confirm = console.input(
                "\n[bold yellow]Proceed with cleanup? [y/N]:[/bold yellow] "
            )
            if confirm.lower() != "y":
                console.print("[red]Cleanup cancelled[/red]")
                return False

        # Clean files
        self.clean_files()

        # Clean logs directory
        self.clean_logs_directory()

        # Display results
        self.display_results()

        return len(self.errors) == 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Clean up pipeline-generated files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be removed without actually removing",
    )

    parser.add_argument(
        "--force", "-f", action="store_true", help="Skip confirmation prompt"
    )

    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")

    args = parser.parse_args()

    # Create cleanup handler
    cleanup = PipelineCleanup(dry_run=args.dry_run)

    # Run cleanup
    success = cleanup.run(interactive=not args.force)

    # Exit with appropriate code
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
