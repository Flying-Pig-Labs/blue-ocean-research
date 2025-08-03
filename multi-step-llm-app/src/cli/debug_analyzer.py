"""
CLI tool for analyzing debug sessions and showing cost savings
"""

import os
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
from rich.text import Text
from rich.markdown import Markdown

from ..utils.debug_config import DebugConfig
from ..utils.debug_cost_tracker import DebugCostTracker
from ..models.logging_models import calculate_api_cost, ModelProvider


class DebugSessionAnalyzer:
    """
    Analyzer for debug session logs and cost data
    """
    
    def __init__(self):
        """Initialize the debug session analyzer"""
        self.console = Console(force_terminal=True, width=120)
        self.debug_log_dir = Path("logs/debug")
    
    def find_debug_sessions(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """Find debug sessions from the last N days"""
        sessions = []
        
        if not self.debug_log_dir.exists():
            self.console.print("[yellow]No debug log directory found[/yellow]")
            return sessions
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Look for debug log files
        for log_file in self.debug_log_dir.glob("debug_*.jsonl"):
            try:
                # Extract timestamp from filename
                timestamp_str = log_file.stem.replace("debug_", "")
                file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                
                if file_date >= cutoff_date:
                    sessions.append({
                        "session_id": timestamp_str,
                        "date": file_date,
                        "debug_log": log_file,
                        "api_log": self.debug_log_dir / f"api_debug_{timestamp_str}.jsonl",
                        "truncation_log": self.debug_log_dir / f"truncations_{timestamp_str}.jsonl"
                    })
            except ValueError:
                # Skip files that don't match expected format
                continue
        
        return sorted(sessions, key=lambda x: x["date"], reverse=True)
    
    def analyze_session(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single debug session"""
        analysis = {
            "session_id": session["session_id"],
            "date": session["date"],
            "duration": 0,
            "api_calls": [],
            "model_switches": [],
            "truncations": [],
            "costs": {
                "actual_cost": 0.0,
                "estimated_production_cost": 0.0,
                "savings": 0.0,
                "savings_percentage": 0.0
            },
            "usage": {
                "total_tokens": 0,
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "blocked_calls": 0
            },
            "components": {},
            "operations": {},
            "models_used": set()
        }
        
        # Analyze main debug log
        if session["debug_log"].exists():
            analysis.update(self._analyze_debug_log(session["debug_log"]))
        
        # Analyze API log
        if session["api_log"].exists():
            api_analysis = self._analyze_api_log(session["api_log"])
            analysis["api_calls"] = api_analysis["calls"]
            analysis["costs"] = api_analysis["costs"]
            analysis["usage"]["total_tokens"] = api_analysis["total_tokens"]
            analysis["usage"]["total_calls"] = len(api_analysis["calls"])
            analysis["usage"]["successful_calls"] = api_analysis["successful_calls"]
            analysis["usage"]["failed_calls"] = api_analysis["failed_calls"]
            analysis["models_used"] = api_analysis["models_used"]
        
        # Analyze truncation log
        if session["truncation_log"].exists():
            analysis["truncations"] = self._analyze_truncation_log(session["truncation_log"])
        
        # Convert sets to lists for JSON serialization
        analysis["models_used"] = list(analysis["models_used"])
        
        return analysis
    
    def _analyze_debug_log(self, log_file: Path) -> Dict[str, Any]:
        """Analyze the main debug log file"""
        events = []
        model_switches = []
        session_start = None
        session_end = None
        components = {}
        operations = {}
        blocked_calls = 0
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        events.append(entry)
                        
                        # Track session timing
                        if entry.get("event") == "debug_session_start":
                            session_start = datetime.fromisoformat(entry["timestamp"])
                        elif entry.get("event") == "debug_session_end":
                            session_end = datetime.fromisoformat(entry["timestamp"])
                        
                        # Track model switches
                        elif entry.get("event") == "model_switch":
                            model_switches.append(entry)
                        
                        # Track component usage
                        elif "component" in entry:
                            comp = entry["component"]
                            if comp not in components:
                                components[comp] = {"events": 0, "operations": set()}
                            components[comp]["events"] += 1
                            if "operation" in entry:
                                components[comp]["operations"].add(entry["operation"])
                        
                        # Track operations
                        if "operation" in entry:
                            op = entry["operation"]
                            if op not in operations:
                                operations[op] = 0
                            operations[op] += 1
                        
                        # Track blocked calls
                        if entry.get("event") == "limit_exceeded":
                            blocked_calls += 1
                        
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass
        
        # Calculate duration
        duration = 0
        if session_start and session_end:
            duration = (session_end - session_start).total_seconds()
        
        # Convert sets to lists
        for comp_data in components.values():
            comp_data["operations"] = list(comp_data["operations"])
        
        return {
            "duration": duration,
            "model_switches": model_switches,
            "components": components,
            "operations": operations,
            "blocked_calls": blocked_calls
        }
    
    def _analyze_api_log(self, log_file: Path) -> Dict[str, Any]:
        """Analyze the API log file"""
        calls = []
        total_tokens = 0
        actual_cost = 0.0
        estimated_production_cost = 0.0
        successful_calls = 0
        failed_calls = 0
        models_used = set()
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        
                        if entry.get("event") == "api_call_success":
                            calls.append(entry)
                            successful_calls += 1
                            total_tokens += entry.get("total_tokens", 0)
                            actual_cost += entry.get("cost", 0)
                            models_used.add(entry.get("model", "unknown"))
                            
                            # Estimate production cost
                            model = entry.get("model", "")
                            production_cost = self._estimate_production_cost(
                                model, entry.get("total_tokens", 0)
                            )
                            estimated_production_cost += production_cost
                            
                        elif entry.get("event") == "api_call_error":
                            failed_calls += 1
                        
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass
        
        # Calculate savings
        savings = estimated_production_cost - actual_cost
        savings_percentage = (savings / estimated_production_cost * 100) if estimated_production_cost > 0 else 0
        
        return {
            "calls": calls,
            "total_tokens": total_tokens,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "models_used": models_used,
            "costs": {
                "actual_cost": actual_cost,
                "estimated_production_cost": estimated_production_cost,
                "savings": savings,
                "savings_percentage": savings_percentage
            }
        }
    
    def _analyze_truncation_log(self, log_file: Path) -> List[Dict[str, Any]]:
        """Analyze the truncation log file"""
        truncations = []
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get("event") == "content_truncation":
                            truncations.append(entry)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass
        
        return truncations
    
    def _estimate_production_cost(self, debug_model: str, total_tokens: int) -> float:
        """Estimate production cost for a debug model call"""
        # Map debug models to typical production models
        production_mapping = {
            "claude-3-haiku-20240307": "claude-3-5-sonnet-20241022",
            "gpt-3.5-turbo": "gpt-4-turbo",
            "command-light": "command"
        }
        
        production_model = production_mapping.get(debug_model, debug_model)
        
        # Rough estimate: 60% prompt tokens, 40% completion tokens
        prompt_tokens = int(total_tokens * 0.6)
        completion_tokens = int(total_tokens * 0.4)
        
        # Determine provider
        if "claude" in production_model:
            provider = ModelProvider.ANTHROPIC
        elif "gpt" in production_model:
            provider = ModelProvider.OPENAI
        else:
            provider = ModelProvider.COHERE
        
        return calculate_api_cost(provider, production_model, prompt_tokens, completion_tokens)
    
    def display_session_summary(self, sessions: List[Dict[str, Any]]):
        """Display summary of all debug sessions"""
        if not sessions:
            self.console.print("[yellow]No debug sessions found[/yellow]")
            return
        
        # Summary table
        table = Table(title="Debug Sessions Summary", show_header=True, header_style="bold cyan")
        table.add_column("Session", style="cyan")
        table.add_column("Date", style="white")
        table.add_column("Duration", style="yellow")
        table.add_column("API Calls", style="green")
        table.add_column("Cost", style="blue")
        table.add_column("Savings", style="magenta")
        table.add_column("Savings %", style="red")
        
        total_cost = 0.0
        total_savings = 0.0
        total_calls = 0
        
        for session in sessions:
            analysis = self.analyze_session(session)
            
            session_cost = analysis["costs"]["actual_cost"]
            session_savings = analysis["costs"]["savings"]
            savings_pct = analysis["costs"]["savings_percentage"]
            
            total_cost += session_cost
            total_savings += session_savings
            total_calls += analysis["usage"]["total_calls"]
            
            table.add_row(
                analysis["session_id"][:12] + "...",
                analysis["date"].strftime("%m-%d %H:%M"),
                f"{analysis['duration']:.0f}s",
                str(analysis["usage"]["total_calls"]),
                f"${session_cost:.3f}",
                f"${session_savings:.3f}",
                f"{savings_pct:.1f}%"
            )
        
        # Add totals row
        total_savings_pct = (total_savings / (total_cost + total_savings) * 100) if (total_cost + total_savings) > 0 else 0
        table.add_row(
            "[bold]TOTAL[/bold]",
            "[bold]---[/bold]",
            "[bold]---[/bold]",
            f"[bold]{total_calls}[/bold]",
            f"[bold]${total_cost:.3f}[/bold]",
            f"[bold]${total_savings:.3f}[/bold]",
            f"[bold]{total_savings_pct:.1f}%[/bold]",
            style="bold"
        )
        
        self.console.print(table)
    
    def display_detailed_analysis(self, session: Dict[str, Any]):
        """Display detailed analysis of a specific session"""
        analysis = self.analyze_session(session)
        
        # Session header
        header_text = (
            f"[bold]Session Analysis: {analysis['session_id']}[/bold]\n"
            f"Date: {analysis['date'].strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Duration: {analysis['duration']:.1f} seconds"
        )
        self.console.print(Panel(header_text, border_style="blue"))
        
        # Cost analysis
        costs = analysis["costs"]
        cost_text = (
            f"[bold green]Actual Cost:[/bold green] ${costs['actual_cost']:.4f}\n"
            f"[bold yellow]Est. Production Cost:[/bold yellow] ${costs['estimated_production_cost']:.4f}\n"
            f"[bold blue]Savings:[/bold blue] ${costs['savings']:.4f} ({costs['savings_percentage']:.1f}%)"
        )
        self.console.print(Panel(cost_text, title="💰 Cost Analysis", border_style="green"))
        
        # Usage statistics
        usage = analysis["usage"]
        usage_text = (
            f"[bold]Total API Calls:[/bold] {usage['total_calls']}\n"
            f"[bold]Successful:[/bold] {usage['successful_calls']}\n"
            f"[bold]Failed:[/bold] {usage['failed_calls']}\n"
            f"[bold]Blocked:[/bold] {usage.get('blocked_calls', 0)}\n"
            f"[bold]Total Tokens:[/bold] {usage['total_tokens']:,}"
        )
        self.console.print(Panel(usage_text, title="📊 Usage Statistics", border_style="yellow"))
        
        # Model switches
        if analysis["model_switches"]:
            switch_table = Table(title="Model Switches", show_header=True)
            switch_table.add_column("From", style="red")
            switch_table.add_column("To", style="green")
            switch_table.add_column("Operation", style="cyan")
            switch_table.add_column("Savings", style="yellow")
            
            for switch in analysis["model_switches"]:
                savings = switch.get("cost_savings_potential", 0) * 100
                switch_table.add_row(
                    switch.get("production_model", "unknown"),
                    switch.get("debug_model", "unknown"),
                    switch.get("operation", "unknown"),
                    f"{savings:.1f}%"
                )
            
            self.console.print(switch_table)
        
        # Components used
        if analysis["components"]:
            comp_table = Table(title="Components Usage", show_header=True)
            comp_table.add_column("Component", style="cyan")
            comp_table.add_column("Events", style="yellow")
            comp_table.add_column("Operations", style="green")
            
            for comp, data in analysis["components"].items():
                operations = ", ".join(data["operations"][:3])  # Show first 3
                if len(data["operations"]) > 3:
                    operations += f" (+{len(data['operations']) - 3} more)"
                
                comp_table.add_row(
                    comp,
                    str(data["events"]),
                    operations
                )
            
            self.console.print(comp_table)
        
        # Content truncations
        if analysis["truncations"]:
            trunc_info = f"[bold]Content Truncations:[/bold] {len(analysis['truncations'])}"
            total_reduction = sum(t.get("reduction_percentage", 0) for t in analysis["truncations"])
            avg_reduction = total_reduction / len(analysis["truncations"])
            trunc_info += f"\n[bold]Average Reduction:[/bold] {avg_reduction:.1f}%"
            
            self.console.print(Panel(trunc_info, title="✂️ Content Truncation", border_style="yellow"))
    
    def export_analysis(self, sessions: List[Dict[str, Any]], output_file: str):
        """Export analysis to file"""
        analysis_data = {
            "export_date": datetime.now().isoformat(),
            "total_sessions": len(sessions),
            "sessions": []
        }
        
        total_cost = 0.0
        total_savings = 0.0
        
        for session in track(sessions, description="Analyzing sessions..."):
            session_analysis = self.analyze_session(session)
            analysis_data["sessions"].append(session_analysis)
            
            total_cost += session_analysis["costs"]["actual_cost"]
            total_savings += session_analysis["costs"]["savings"]
        
        # Add summary
        analysis_data["summary"] = {
            "total_actual_cost": total_cost,
            "total_estimated_savings": total_savings,
            "average_savings_percentage": (total_savings / (total_cost + total_savings) * 100) if (total_cost + total_savings) > 0 else 0
        }
        
        # Export to file
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            json.dump(analysis_data, f, indent=2, default=str)
        
        self.console.print(f"[green]Analysis exported to {output_path}[/green]")
    
    def generate_report(self, sessions: List[Dict[str, Any]]) -> str:
        """Generate a markdown report"""
        if not sessions:
            return "# Debug Session Report\n\nNo debug sessions found."
        
        report = "# Debug Session Analysis Report\n\n"
        report += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Summary
        total_cost = 0.0
        total_savings = 0.0
        total_calls = 0
        total_tokens = 0
        
        for session in sessions:
            analysis = self.analyze_session(session)
            total_cost += analysis["costs"]["actual_cost"]
            total_savings += analysis["costs"]["savings"]
            total_calls += analysis["usage"]["total_calls"]
            total_tokens += analysis["usage"]["total_tokens"]
        
        total_savings_pct = (total_savings / (total_cost + total_savings) * 100) if (total_cost + total_savings) > 0 else 0
        
        report += "## Summary\n\n"
        report += f"- **Total Sessions:** {len(sessions)}\n"
        report += f"- **Total API Calls:** {total_calls:,}\n"
        report += f"- **Total Tokens Used:** {total_tokens:,}\n"
        report += f"- **Total Actual Cost:** ${total_cost:.4f}\n"
        report += f"- **Total Estimated Savings:** ${total_savings:.4f}\n"
        report += f"- **Average Savings Percentage:** {total_savings_pct:.1f}%\n\n"
        
        # Most recent sessions
        report += "## Recent Sessions\n\n"
        for session in sessions[:5]:  # Show last 5 sessions
            analysis = self.analyze_session(session)
            report += f"### {analysis['session_id']}\n"
            report += f"- **Date:** {analysis['date'].strftime('%Y-%m-%d %H:%M:%S')}\n"
            report += f"- **Duration:** {analysis['duration']:.1f} seconds\n"
            report += f"- **API Calls:** {analysis['usage']['total_calls']}\n"
            report += f"- **Cost:** ${analysis['costs']['actual_cost']:.4f}\n"
            report += f"- **Savings:** ${analysis['costs']['savings']:.4f} ({analysis['costs']['savings_percentage']:.1f}%)\n\n"
        
        return report


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Analyze debug sessions and calculate cost savings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show summary of last 7 days
  python -m src.cli.debug_analyzer
  
  # Show summary of last 30 days
  python -m src.cli.debug_analyzer --days 30
  
  # Analyze specific session
  python -m src.cli.debug_analyzer --session 20240803_143022
  
  # Export analysis to JSON
  python -m src.cli.debug_analyzer --export analysis.json
  
  # Generate markdown report
  python -m src.cli.debug_analyzer --report report.md
        """
    )
    
    parser.add_argument("--days", type=int, default=7, 
                       help="Number of days back to analyze (default: 7)")
    parser.add_argument("--session", type=str,
                       help="Analyze specific session ID")
    parser.add_argument("--export", type=str,
                       help="Export analysis to JSON file")
    parser.add_argument("--report", type=str,
                       help="Generate markdown report")
    parser.add_argument("--summary-only", action="store_true",
                       help="Show only summary table")
    
    args = parser.parse_args()
    
    analyzer = DebugSessionAnalyzer()
    
    # Find sessions
    sessions = analyzer.find_debug_sessions(args.days)
    
    if args.session:
        # Analyze specific session
        target_session = None
        for session in sessions:
            if args.session in session["session_id"]:
                target_session = session
                break
        
        if target_session:
            analyzer.display_detailed_analysis(target_session)
        else:
            analyzer.console.print(f"[red]Session {args.session} not found[/red]")
            return
    
    elif args.export:
        # Export analysis
        analyzer.export_analysis(sessions, args.export)
    
    elif args.report:
        # Generate report
        report_content = analyzer.generate_report(sessions)
        with open(args.report, 'w') as f:
            f.write(report_content)
        analyzer.console.print(f"[green]Report generated: {args.report}[/green]")
    
    else:
        # Show summary
        analyzer.display_session_summary(sessions)
        
        if not args.summary_only and sessions:
            # Show detailed analysis of most recent session
            analyzer.console.print("\n[bold]Most Recent Session Details:[/bold]")
            analyzer.display_detailed_analysis(sessions[0])


if __name__ == "__main__":
    main()