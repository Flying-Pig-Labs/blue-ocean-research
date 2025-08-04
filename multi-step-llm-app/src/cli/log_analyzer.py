#!/usr/bin/env python3
"""
CLI tools for analyzing pipeline logs
"""

import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict
import statistics

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
from rich.tree import Tree
from rich.text import Text

from ..models.logging_models import LogLevel, ComponentType, ModelProvider


class LogAnalyzer:
    """CLI tool for analyzing pipeline logs"""

    def __init__(self):
        self.console = Console()

    def load_session_data(self, session_path: Path) -> Dict[str, Any]:
        """Load session data from directory or export file"""
        if session_path.is_file() and session_path.suffix == ".json":
            # Load from export file
            with open(session_path, "r") as f:
                return json.load(f)

        elif session_path.is_dir():
            # Load from session directory
            data = {
                "log_entries": [],
                "api_calls": [],
                "component_logs": [],
                "progress_entries": [],
            }

            # Load each JSONL file
            for file_name, key in [
                ("session.jsonl", "log_entries"),
                ("api_calls.jsonl", "api_calls"),
                ("components.jsonl", "component_logs"),
                ("progress.jsonl", "progress_entries"),
            ]:
                file_path = session_path / file_name
                if file_path.exists():
                    with open(file_path, "r") as f:
                        data[key] = [json.loads(line) for line in f if line.strip()]

            return data

        else:
            raise ValueError(f"Invalid session path: {session_path}")

    def analyze_session_overview(self, data: Dict[str, Any]):
        """Display session overview analysis"""
        self.console.print(
            Panel("[bold green]Session Overview Analysis[/bold green]", expand=False)
        )

        # Basic session info
        session_info = data.get("session_info", {})
        summary = data.get("summary", {})

        overview_table = Table(title="Session Information")
        overview_table.add_column("Metric", style="cyan")
        overview_table.add_column("Value", style="green")

        if session_info:
            overview_table.add_row(
                "Session ID", session_info.get("session_id", "Unknown")
            )
            overview_table.add_row(
                "Start Time", session_info.get("start_time", "Unknown")
            )
            if session_info.get("end_time"):
                overview_table.add_row("End Time", session_info.get("end_time"))
            overview_table.add_row(
                "Total API Calls", str(session_info.get("total_api_calls", 0))
            )
            overview_table.add_row(
                "Total Tokens", f"{session_info.get('total_tokens', 0):,}"
            )
            overview_table.add_row(
                "Total Cost", f"${session_info.get('total_cost', 0):.4f}"
            )

        if summary:
            overview_table.add_row(
                "Duration", f"{summary.get('total_duration', 0):.2f} seconds"
            )
            overview_table.add_row(
                "Success Rate", f"{summary.get('success_rate', 0):.1f}%"
            )
            overview_table.add_row("Errors", str(summary.get("error_count", 0)))
            overview_table.add_row("Warnings", str(summary.get("warning_count", 0)))

        self.console.print(overview_table)

    def analyze_api_usage(self, data: Dict[str, Any]):
        """Analyze API usage patterns"""
        self.console.print(
            Panel("[bold blue]API Usage Analysis[/bold blue]", expand=False)
        )

        api_calls = data.get("api_calls", [])
        if not api_calls:
            self.console.print("[yellow]No API calls found in session data[/yellow]")
            return

        # Group by component
        component_stats = defaultdict(
            lambda: {
                "calls": 0,
                "tokens": 0,
                "cost": 0.0,
                "avg_duration": 0.0,
                "models": set(),
                "providers": set(),
                "failures": 0,
            }
        )

        for call in api_calls:
            comp = call["component"]
            stats = component_stats[comp]

            stats["calls"] += 1
            stats["tokens"] += call.get("total_tokens", 0)
            stats["cost"] += call.get("estimated_cost", 0.0)
            stats["avg_duration"] += call.get("duration", 0.0)
            stats["models"].add(call.get("model", "unknown"))
            stats["providers"].add(call.get("provider", "unknown"))

            if not call.get("success", True):
                stats["failures"] += 1

        # Calculate averages
        for stats in component_stats.values():
            if stats["calls"] > 0:
                stats["avg_duration"] /= stats["calls"]

        # Display component usage table
        usage_table = Table(title="API Usage by Component")
        usage_table.add_column("Component", style="cyan")
        usage_table.add_column("Calls", style="yellow")
        usage_table.add_column("Tokens", style="green")
        usage_table.add_column("Cost", style="red")
        usage_table.add_column("Avg Duration", style="blue")
        usage_table.add_column("Failures", style="red")
        usage_table.add_column("Models", style="magenta")

        for comp, stats in sorted(component_stats.items()):
            usage_table.add_row(
                comp,
                str(stats["calls"]),
                f"{stats['tokens']:,}",
                f"${stats['cost']:.4f}",
                f"{stats['avg_duration']:.2f}s",
                str(stats["failures"]),
                ", ".join(sorted(stats["models"])),
            )

        self.console.print(usage_table)

        # Model usage summary
        model_stats = defaultdict(lambda: {"calls": 0, "tokens": 0, "cost": 0.0})
        for call in api_calls:
            model = call.get("model", "unknown")
            model_stats[model]["calls"] += 1
            model_stats[model]["tokens"] += call.get("total_tokens", 0)
            model_stats[model]["cost"] += call.get("estimated_cost", 0.0)

        model_table = Table(title="Usage by Model")
        model_table.add_column("Model", style="cyan")
        model_table.add_column("Calls", style="yellow")
        model_table.add_column("Tokens", style="green")
        model_table.add_column("Cost", style="red")

        for model, stats in sorted(
            model_stats.items(), key=lambda x: x[1]["cost"], reverse=True
        ):
            model_table.add_row(
                model,
                str(stats["calls"]),
                f"{stats['tokens']:,}",
                f"${stats['cost']:.4f}",
            )

        self.console.print(model_table)

    def analyze_performance(self, data: Dict[str, Any]):
        """Analyze performance metrics"""
        self.console.print(
            Panel("[bold yellow]Performance Analysis[/bold yellow]", expand=False)
        )

        component_logs = data.get("component_logs", [])
        if not component_logs:
            self.console.print(
                "[yellow]No component logs found in session data[/yellow]"
            )
            return

        # Group by component and operation
        perf_stats = defaultdict(
            lambda: {
                "operations": defaultdict(list),
                "total_duration": 0.0,
                "operation_count": 0,
                "failures": 0,
            }
        )

        for log in component_logs:
            comp = log["component"]
            operation = log.get("operation", "unknown")
            duration = log.get("duration", 0.0)
            success = log.get("success", True)

            perf_stats[comp]["operations"][operation].append(duration)
            perf_stats[comp]["total_duration"] += duration
            perf_stats[comp]["operation_count"] += 1

            if not success:
                perf_stats[comp]["failures"] += 1

        # Performance table
        perf_table = Table(title="Performance by Component")
        perf_table.add_column("Component", style="cyan")
        perf_table.add_column("Operations", style="yellow")
        perf_table.add_column("Total Time", style="green")
        perf_table.add_column("Avg Time", style="blue")
        perf_table.add_column("Failures", style="red")
        perf_table.add_column("Success Rate", style="green")

        for comp, stats in sorted(perf_stats.items()):
            total_ops = stats["operation_count"]
            failures = stats["failures"]
            success_rate = (
                ((total_ops - failures) / total_ops * 100) if total_ops > 0 else 100
            )
            avg_time = stats["total_duration"] / total_ops if total_ops > 0 else 0

            perf_table.add_row(
                comp,
                str(total_ops),
                f"{stats['total_duration']:.2f}s",
                f"{avg_time:.2f}s",
                str(failures),
                f"{success_rate:.1f}%",
            )

        self.console.print(perf_table)

        # Detailed operation performance
        self.console.print("\n[bold]Operation Performance Details:[/bold]")

        for comp, stats in perf_stats.items():
            if not stats["operations"]:
                continue

            tree = Tree(f"[bold cyan]{comp}[/bold cyan]")

            for operation, durations in stats["operations"].items():
                if durations:
                    avg_duration = statistics.mean(durations)
                    min_duration = min(durations)
                    max_duration = max(durations)
                    count = len(durations)

                    op_text = (
                        f"[yellow]{operation}[/yellow] "
                        f"(count: {count}, avg: {avg_duration:.2f}s, "
                        f"min: {min_duration:.2f}s, max: {max_duration:.2f}s)"
                    )
                    tree.add(op_text)

            self.console.print(tree)

    def analyze_errors(self, data: Dict[str, Any]):
        """Analyze error patterns"""
        self.console.print(Panel("[bold red]Error Analysis[/bold red]", expand=False))

        log_entries = data.get("log_entries", [])
        errors = [entry for entry in log_entries if entry.get("level") == "ERROR"]
        warnings = [entry for entry in log_entries if entry.get("level") == "WARNING"]

        if not errors and not warnings:
            self.console.print("[green]No errors or warnings found! 🎉[/green]")
            return

        # Error summary
        error_table = Table(title="Error Summary")
        error_table.add_column("Level", style="red")
        error_table.add_column("Count", style="yellow")
        error_table.add_column("Components", style="cyan")

        if errors:
            error_components = set(error["component"] for error in errors)
            error_table.add_row(
                "ERROR", str(len(errors)), ", ".join(sorted(error_components))
            )

        if warnings:
            warning_components = set(warning["component"] for warning in warnings)
            error_table.add_row(
                "WARNING", str(len(warnings)), ", ".join(sorted(warning_components))
            )

        self.console.print(error_table)

        # Recent errors (last 10)
        if errors:
            self.console.print("\n[bold red]Recent Errors:[/bold red]")
            recent_errors = sorted(
                errors, key=lambda x: x.get("timestamp", ""), reverse=True
            )[:10]

            for i, error in enumerate(recent_errors, 1):
                timestamp = error.get("timestamp", "Unknown")
                component = error.get("component", "Unknown")
                message = error.get("message", "No message")
                operation = error.get("operation", "")

                error_text = f"[dim]{timestamp}[/dim] [{component}] "
                if operation:
                    error_text += f"({operation}) "
                error_text += message

                self.console.print(f"{i:2d}. {error_text}")

    def analyze_timeline(self, data: Dict[str, Any]):
        """Analyze session timeline"""
        self.console.print(
            Panel("[bold magenta]Session Timeline[/bold magenta]", expand=False)
        )

        # Combine all events with timestamps
        events = []

        # Add log entries
        for entry in data.get("log_entries", []):
            events.append(
                {
                    "timestamp": entry.get("timestamp"),
                    "type": "log",
                    "level": entry.get("level"),
                    "component": entry.get("component"),
                    "message": entry.get("message"),
                    "operation": entry.get("operation"),
                }
            )

        # Add API calls
        for call in data.get("api_calls", []):
            events.append(
                {
                    "timestamp": call.get("timestamp"),
                    "type": "api_call",
                    "component": call.get("component"),
                    "model": call.get("model"),
                    "tokens": call.get("total_tokens"),
                    "cost": call.get("estimated_cost"),
                    "success": call.get("success"),
                }
            )

        # Add component operations
        for comp_log in data.get("component_logs", []):
            # Start event
            events.append(
                {
                    "timestamp": comp_log.get("start_time"),
                    "type": "operation_start",
                    "component": comp_log.get("component"),
                    "operation": comp_log.get("operation"),
                }
            )

            # End event (if available)
            if comp_log.get("end_time"):
                events.append(
                    {
                        "timestamp": comp_log.get("end_time"),
                        "type": "operation_end",
                        "component": comp_log.get("component"),
                        "operation": comp_log.get("operation"),
                        "duration": comp_log.get("duration"),
                        "success": comp_log.get("success"),
                    }
                )

        # Sort by timestamp
        events.sort(key=lambda x: x.get("timestamp", ""))

        # Display timeline (last 20 events)
        timeline_table = Table(title="Recent Timeline (Last 20 Events)")
        timeline_table.add_column("Time", style="dim")
        timeline_table.add_column("Type", style="yellow")
        timeline_table.add_column("Component", style="cyan")
        timeline_table.add_column("Details", style="white")

        recent_events = events[-20:] if len(events) > 20 else events

        for event in recent_events:
            timestamp = event.get("timestamp", "Unknown")
            if isinstance(timestamp, str) and "T" in timestamp:
                # Parse ISO format and show just time
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    time_str = dt.strftime("%H:%M:%S")
                except (ValueError, TypeError):
                    time_str = timestamp
            else:
                time_str = str(timestamp)

            event_type = event["type"]
            component = event.get("component", "Unknown")

            # Format details based on event type
            if event_type == "log":
                level = event.get("level", "")
                message = event.get("message", "")
                operation = event.get("operation", "")
                details = (
                    f"[{level}] {operation}: {message}"
                    if operation
                    else f"[{level}] {message}"
                )

            elif event_type == "api_call":
                model = event.get("model", "")
                tokens = event.get("tokens", 0)
                cost = event.get("cost", 0)
                success = event.get("success", True)
                status = "✓" if success else "✗"
                details = f"{status} {model} ({tokens} tokens, ${cost:.4f})"

            elif event_type == "operation_start":
                operation = event.get("operation", "")
                details = f"Started: {operation}"

            elif event_type == "operation_end":
                operation = event.get("operation", "")
                duration = event.get("duration", 0)
                success = event.get("success", True)
                status = "✓" if success else "✗"
                details = f"{status} Completed: {operation} ({duration:.2f}s)"

            else:
                details = str(event)

            timeline_table.add_row(time_str, event_type, component, details)

        self.console.print(timeline_table)

    def generate_report(self, session_path: Path, output_file: Optional[Path] = None):
        """Generate comprehensive analysis report"""
        try:
            data = self.load_session_data(session_path)
        except Exception as e:
            self.console.print(f"[red]Error loading session data: {e}[/red]")
            return

        self.console.print(f"[green]Analyzing session: {session_path}[/green]\n")

        # Run all analyses
        self.analyze_session_overview(data)
        self.console.print()
        self.analyze_api_usage(data)
        self.console.print()
        self.analyze_performance(data)
        self.console.print()
        self.analyze_errors(data)
        self.console.print()
        self.analyze_timeline(data)

        # Save report if requested
        if output_file:
            # TODO: Implement report export to file
            self.console.print(
                f"\n[yellow]Report export to file not yet implemented[/yellow]"
            )

    def list_sessions(self, logs_dir: Path):
        """List available sessions"""
        self.console.print(
            Panel("[bold green]Available Sessions[/bold green]", expand=False)
        )

        if not logs_dir.exists():
            self.console.print(f"[red]Logs directory not found: {logs_dir}[/red]")
            return

        sessions = []

        # Find session directories (timestamp format)
        for item in logs_dir.iterdir():
            if item.is_dir() and "_" in item.name:
                sessions.append(item)

        # Find export files
        for item in logs_dir.iterdir():
            if item.is_file() and item.suffix == ".json" and "export" in item.name:
                sessions.append(item)

        if not sessions:
            self.console.print("[yellow]No sessions found[/yellow]")
            return

        sessions_table = Table(title=f"Sessions in {logs_dir}")
        sessions_table.add_column("Session", style="cyan")
        sessions_table.add_column("Type", style="yellow")
        sessions_table.add_column("Modified", style="green")
        sessions_table.add_column("Size", style="blue")

        for session in sorted(sessions, key=lambda x: x.stat().st_mtime, reverse=True):
            session_type = "Directory" if session.is_dir() else "Export File"
            modified = datetime.fromtimestamp(session.stat().st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            if session.is_dir():
                # Calculate directory size
                total_size = sum(
                    f.stat().st_size for f in session.rglob("*") if f.is_file()
                )
                size_str = f"{total_size / 1024:.1f} KB"
            else:
                size_str = f"{session.stat().st_size / 1024:.1f} KB"

            sessions_table.add_row(session.name, session_type, modified, size_str)

        self.console.print(sessions_table)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Analyze Helios pipeline logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all available sessions
  python -m src.cli.log_analyzer list
  
  # Analyze a specific session directory
  python -m src.cli.log_analyzer analyze logs/2024-01-20_14-30-45/
  
  # Analyze a session export file
  python -m src.cli.log_analyzer analyze logs/session_export.json
  
  # Generate report with specific analyses
  python -m src.cli.log_analyzer analyze logs/2024-01-20_14-30-45/ --api --performance --errors
  
  # Export analysis to file
  python -m src.cli.log_analyzer analyze logs/2024-01-20_14-30-45/ --output report.txt
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List available sessions")
    list_parser.add_argument(
        "--logs-dir",
        type=Path,
        default=Path("logs"),
        help="Logs directory (default: logs)",
    )

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a session")
    analyze_parser.add_argument(
        "session", type=Path, help="Session directory or export file"
    )
    analyze_parser.add_argument("--output", type=Path, help="Output file for report")
    analyze_parser.add_argument(
        "--overview", action="store_true", help="Show overview only"
    )
    analyze_parser.add_argument(
        "--api", action="store_true", help="Show API usage only"
    )
    analyze_parser.add_argument(
        "--performance", action="store_true", help="Show performance only"
    )
    analyze_parser.add_argument(
        "--errors", action="store_true", help="Show errors only"
    )
    analyze_parser.add_argument(
        "--timeline", action="store_true", help="Show timeline only"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    analyzer = LogAnalyzer()

    if args.command == "list":
        analyzer.list_sessions(args.logs_dir)

    elif args.command == "analyze":
        if not args.session.exists():
            print(f"Error: Session path not found: {args.session}")
            return

        # If specific analysis requested, run only those
        if any([args.overview, args.api, args.performance, args.errors, args.timeline]):
            try:
                data = analyzer.load_session_data(args.session)

                if args.overview:
                    analyzer.analyze_session_overview(data)
                if args.api:
                    analyzer.analyze_api_usage(data)
                if args.performance:
                    analyzer.analyze_performance(data)
                if args.errors:
                    analyzer.analyze_errors(data)
                if args.timeline:
                    analyzer.analyze_timeline(data)

            except Exception as e:
                print(f"Error analyzing session: {e}")
        else:
            # Run full analysis
            analyzer.generate_report(args.session, args.output)


if __name__ == "__main__":
    main()
