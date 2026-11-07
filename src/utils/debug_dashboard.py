"""
Real-time debug dashboard with Rich for monitoring pipeline progress and costs
"""

import os
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    SpinnerColumn,
    TimeRemainingColumn,
)
from rich.text import Text
from rich.align import Align

from .debug_config import get_debug_config
from .debug_cost_tracker import get_debug_cost_tracker
from ..models.logging_models import ComponentType


class DebugDashboard:
    """
    Real-time debug dashboard for monitoring pipeline execution
    """

    def __init__(self):
        """Initialize debug dashboard"""
        self.enabled = os.getenv("DEBUG", "").lower() in ["true", "1", "yes", "on"]

        if not self.enabled:
            return

        self.console = Console(force_terminal=True, width=120)
        self.debug_config = get_debug_config()
        self.cost_tracker = get_debug_cost_tracker()

        # Dashboard state
        self.session_start = datetime.now()
        self.active_operations: Dict[str, Dict[str, Any]] = {}
        self.completed_operations: List[Dict[str, Any]] = []
        self.current_component: Optional[ComponentType] = None

        # Threading for live updates
        self._update_lock = threading.Lock()
        self._live_display: Optional[Live] = None
        self._should_update = True

        # Component progress tracking
        self.component_progress: Dict[ComponentType, Dict[str, Any]] = {}

    @contextmanager
    def live_dashboard(self):
        """Context manager for live dashboard display"""
        if not self.enabled:
            yield
            return

        layout = self._create_layout()

        with Live(
            layout,
            console=self.console,
            refresh_per_second=2,
            screen=True,
            vertical_overflow="visible",
        ) as live:
            self._live_display = live
            try:
                yield self
            finally:
                self._live_display = None
                self._should_update = False

    def _create_layout(self) -> Layout:
        """Create the dashboard layout"""
        layout = Layout()

        # Split into main areas
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=5),
        )

        # Split main area
        layout["main"].split_row(
            Layout(name="left", ratio=2), Layout(name="right", ratio=1)
        )

        # Split left area
        layout["left"].split_column(
            Layout(name="progress", ratio=1), Layout(name="operations", ratio=1)
        )

        # Split right area
        layout["right"].split_column(
            Layout(name="costs", ratio=1), Layout(name="limits", ratio=1)
        )

        return layout

    def _update_layout(self):
        """Update the dashboard layout with current data"""
        if not self._live_display:
            return

        with self._update_lock:
            layout = self._live_display.renderable

            # Header
            layout["header"].update(self._create_header())

            # Progress
            layout["progress"].update(self._create_progress_panel())

            # Operations
            layout["operations"].update(self._create_operations_panel())

            # Costs
            layout["costs"].update(self._create_costs_panel())

            # Limits
            layout["limits"].update(self._create_limits_panel())

            # Footer
            layout["footer"].update(self._create_footer())

    def _create_header(self) -> Panel:
        """Create header panel"""
        session_duration = datetime.now() - self.session_start
        current_comp = (
            self.current_component.value if self.current_component else "None"
        )

        header_text = (
            f"[bold cyan]🐛 DEBUG DASHBOARD[/bold cyan] "
            f"[dim]| Session: {session_duration.total_seconds():.0f}s "
            f"| Current: {current_comp}[/dim]"
        )

        return Panel(Align.center(header_text), style="bold blue", box=None)

    def _create_progress_panel(self) -> Panel:
        """Create progress tracking panel"""
        if not self.component_progress:
            return Panel("No active operations", title="Progress", border_style="dim")

        progress_table = Table(show_header=True, header_style="bold magenta")
        progress_table.add_column("Component", style="cyan")
        progress_table.add_column("Operation", style="white")
        progress_table.add_column("Progress", style="green")
        progress_table.add_column("ETA", style="yellow")

        for component, progress_data in self.component_progress.items():
            if progress_data.get("active", False):
                current = progress_data.get("current", 0)
                total = progress_data.get("total", 1)
                progress_pct = (current / total * 100) if total > 0 else 0

                # Simple ETA calculation
                elapsed = time.time() - progress_data.get("start_time", time.time())
                if current > 0:
                    eta_seconds = (elapsed / current) * (total - current)
                    eta_text = f"{eta_seconds:.0f}s"
                else:
                    eta_text = "calculating..."

                progress_bar = (
                    f"[{'=' * int(progress_pct // 5):10}] {progress_pct:.0f}%"
                )

                progress_table.add_row(
                    component.value,
                    progress_data.get("operation", "Unknown"),
                    progress_bar,
                    eta_text,
                )

        return Panel(progress_table, title="🔄 Progress", border_style="green")

    def _create_operations_panel(self) -> Panel:
        """Create operations tracking panel"""
        ops_table = Table(show_header=True, header_style="bold blue")
        ops_table.add_column("Time", style="dim")
        ops_table.add_column("Operation", style="cyan")
        ops_table.add_column("Status", style="white")
        ops_table.add_column("Duration", style="yellow")

        # Show last 5 completed operations
        recent_ops = self.completed_operations[-5:] if self.completed_operations else []

        for op in recent_ops:
            time_str = op["timestamp"].strftime("%H:%M:%S")
            duration = f"{op.get('duration', 0):.1f}s"
            status = "✅ Success" if op.get("success", True) else "❌ Failed"

            ops_table.add_row(time_str, op["operation"], status, duration)

        # Add active operations
        for op_id, op_data in self.active_operations.items():
            elapsed = time.time() - op_data["start_time"]
            ops_table.add_row(
                "now", op_data["operation"], "🔄 Running", f"{elapsed:.1f}s"
            )

        return Panel(ops_table, title="📋 Operations", border_style="blue")

    def _create_costs_panel(self) -> Panel:
        """Create costs tracking panel"""
        stats = self.debug_config.get_session_stats()

        costs_text = (
            f"[bold]Session Cost:[/bold] ${stats['session_cost']:.4f}\n"
            f"[bold]Limit:[/bold] ${stats['cost_limit']:.2f}\n"
            f"[bold]Remaining:[/bold] ${stats['cost_remaining']:.4f}\n\n"
            f"[bold]Tokens Used:[/bold] {stats['session_tokens']:,}\n"
            f"[bold]Limit:[/bold] {stats['token_limit']:,}\n"
            f"[bold]Remaining:[/bold] {stats['tokens_remaining']:,}\n\n"
            f"[bold]API Calls:[/bold] {stats['session_api_calls']}\n"
            f"[bold]Limit:[/bold] {stats['api_call_limit']}"
        )

        # Add cost savings if available
        cost_report = self.cost_tracker.generate_cost_report()
        if cost_report.get("debug_mode"):
            savings = cost_report["costs"]["estimated_savings"]
            savings_pct = cost_report["costs"]["savings_percentage"]
            costs_text += f"\n\n[bold green]Est. Savings:[/bold green] ${savings:.4f} ({savings_pct:.1f}%)"

        return Panel(costs_text, title="💰 Costs", border_style="green")

    def _create_limits_panel(self) -> Panel:
        """Create limits monitoring panel"""
        stats = self.debug_config.get_session_stats()
        warnings = self.debug_config.should_warn_about_limits()

        # Progress bars for limits
        cost_pct = stats["cost_percentage"]
        token_pct = stats["token_percentage"]
        calls_pct = stats["api_call_percentage"]

        def create_limit_bar(percentage: float, warning: bool) -> str:
            filled = int(percentage // 10)
            bar_style = "red" if warning else "yellow" if percentage > 50 else "green"
            bar = "█" * filled + "░" * (10 - filled)
            return f"[{bar_style}]{bar}[/{bar_style}] {percentage:.1f}%"

        limits_text = (
            f"[bold]Cost Usage:[/bold]\n"
            f"{create_limit_bar(cost_pct, warnings.get('cost', False))}\n\n"
            f"[bold]Token Usage:[/bold]\n"
            f"{create_limit_bar(token_pct, warnings.get('tokens', False))}\n\n"
            f"[bold]API Calls:[/bold]\n"
            f"{create_limit_bar(calls_pct, warnings.get('api_calls', False))}"
        )

        # Add warnings if any
        if any(warnings.values()):
            limits_text += "\n\n[bold red]⚠️  Approaching Limits![/bold red]"

        border_style = "red" if any(warnings.values()) else "yellow"
        return Panel(limits_text, title="⚠️  Limits", border_style=border_style)

    def _create_footer(self) -> Panel:
        """Create footer with quick stats"""
        session_duration = datetime.now() - self.session_start

        footer_text = (
            f"[dim]Session Duration: {session_duration.total_seconds():.0f}s | "
            f"Active Ops: {len(self.active_operations)} | "
            f"Completed: {len(self.completed_operations)} | "
            f"Last Update: {datetime.now().strftime('%H:%M:%S')}[/dim]"
        )

        return Panel(Align.center(footer_text), style="dim", box=None)

    def start_operation(
        self, operation_id: str, operation_name: str, component: ComponentType
    ) -> str:
        """Start tracking an operation"""
        if not self.enabled:
            return operation_id

        with self._update_lock:
            self.active_operations[operation_id] = {
                "operation": operation_name,
                "component": component,
                "start_time": time.time(),
                "timestamp": datetime.now(),
            }
            self.current_component = component

        if self._live_display:
            self._update_layout()

        return operation_id

    def complete_operation(
        self,
        operation_id: str,
        success: bool = True,
        result_data: Optional[Dict[str, Any]] = None,
    ):
        """Complete tracking an operation"""
        if not self.enabled or operation_id not in self.active_operations:
            return

        with self._update_lock:
            op_data = self.active_operations.pop(operation_id)
            duration = time.time() - op_data["start_time"]

            completed_op = {
                "operation": op_data["operation"],
                "component": op_data["component"],
                "duration": duration,
                "success": success,
                "timestamp": datetime.now(),
                "result_data": result_data or {},
            }

            self.completed_operations.append(completed_op)

            # Keep only last 20 completed operations
            if len(self.completed_operations) > 20:
                self.completed_operations = self.completed_operations[-20:]

        if self._live_display:
            self._update_layout()

    def update_component_progress(
        self, component: ComponentType, operation: str, current: int, total: int
    ):
        """Update progress for a component"""
        if not self.enabled:
            return

        with self._update_lock:
            if component not in self.component_progress:
                self.component_progress[component] = {"start_time": time.time()}

            self.component_progress[component].update(
                {
                    "operation": operation,
                    "current": current,
                    "total": total,
                    "active": current < total,
                    "last_update": time.time(),
                }
            )

        if self._live_display:
            self._update_layout()

    def complete_component_progress(self, component: ComponentType):
        """Mark component progress as complete"""
        if not self.enabled:
            return

        with self._update_lock:
            if component in self.component_progress:
                self.component_progress[component]["active"] = False

        if self._live_display:
            self._update_layout()

    def display_quick_summary(self):
        """Display a quick summary without live dashboard"""
        if not self.enabled:
            return

        session_duration = datetime.now() - self.session_start
        stats = self.debug_config.get_session_stats()

        summary_table = Table(title="Debug Session Summary", show_header=True)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")

        summary_table.add_row(
            "Session Duration", f"{session_duration.total_seconds():.1f}s"
        )
        summary_table.add_row("Current Cost", f"${stats['session_cost']:.4f}")
        summary_table.add_row("Tokens Used", f"{stats['session_tokens']:,}")
        summary_table.add_row("API Calls", str(stats["session_api_calls"]))
        summary_table.add_row("Active Operations", str(len(self.active_operations)))
        summary_table.add_row(
            "Completed Operations", str(len(self.completed_operations))
        )

        # Add cost savings
        cost_report = self.cost_tracker.generate_cost_report()
        if cost_report.get("debug_mode"):
            savings = cost_report["costs"]["estimated_savings"]
            summary_table.add_row("Estimated Savings", f"${savings:.4f}")

        self.console.print(summary_table)

    @contextmanager
    def track_operation(self, operation_name: str, component: ComponentType):
        """Context manager for tracking operations"""
        if not self.enabled:
            yield
            return

        operation_id = f"{component.value}_{int(time.time() * 1000)}"

        try:
            self.start_operation(operation_id, operation_name, component)
            yield operation_id
            self.complete_operation(operation_id, success=True)
        except Exception as e:
            self.complete_operation(
                operation_id, success=False, result_data={"error": str(e)}
            )
            raise

    def cleanup(self):
        """Cleanup dashboard resources"""
        if not self.enabled:
            return

        self._should_update = False

        # Display final summary
        self.display_quick_summary()


# Global dashboard instance
_debug_dashboard: Optional[DebugDashboard] = None


def get_debug_dashboard() -> DebugDashboard:
    """Get the global debug dashboard instance"""
    global _debug_dashboard
    if _debug_dashboard is None:
        _debug_dashboard = DebugDashboard()
    return _debug_dashboard


def initialize_debug_dashboard() -> DebugDashboard:
    """Initialize the global debug dashboard"""
    global _debug_dashboard
    _debug_dashboard = DebugDashboard()
    return _debug_dashboard
