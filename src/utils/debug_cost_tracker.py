"""
Debug cost tracker for monitoring expenses and calculating savings
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
from rich.text import Text

from ..models.logging_models import calculate_api_cost, ModelProvider


@dataclass
class ApiCallRecord:
    """Record of an API call for cost tracking"""

    timestamp: datetime
    operation: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost: float
    duration: float
    success: bool = True


@dataclass
class BlockedCallRecord:
    """Record of a call that was blocked due to limits"""

    timestamp: datetime
    operation: str
    estimated_tokens: int
    estimated_cost: float
    reason: str = "limit_exceeded"


@dataclass
class DebugCostSummary:
    """Summary of debug session costs and savings"""

    session_start: datetime
    total_api_calls: int = 0
    total_cost: float = 0.0
    total_tokens: int = 0
    total_blocked_calls: int = 0
    estimated_savings: float = 0.0
    average_call_cost: float = 0.0
    most_expensive_operation: str = ""
    most_expensive_cost: float = 0.0
    call_records: List[ApiCallRecord] = field(default_factory=list)
    blocked_records: List[BlockedCallRecord] = field(default_factory=list)


class DebugCostTracker:
    """
    Tracks costs and potential savings in debug mode
    """

    def __init__(self):
        """Initialize cost tracker"""
        self.enabled = os.getenv("DEBUG", "").lower() in ["true", "1", "yes", "on"]

        if not self.enabled:
            return

        self.console = Console(force_terminal=True, width=120)
        self.session_start = datetime.now()

        # Cost tracking
        self.api_calls: List[ApiCallRecord] = []
        self.blocked_calls: List[BlockedCallRecord] = []
        self.operation_costs: Dict[str, float] = {}
        self.model_usage: Dict[str, Dict[str, Any]] = {}

        # Savings estimation (comparing to production models)
        self.estimated_production_cost = 0.0
        self.actual_debug_cost = 0.0

        self._log_session_start()

    def _log_session_start(self):
        """Log the start of cost tracking"""
        if not self.enabled:
            return

        self.console.print(
            Panel.fit(
                "[bold green]💰 DEBUG COST TRACKING ENABLED[/bold green]\n"
                f"Session started: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}\n"
                "Monitoring API costs and calculating savings...",
                border_style="green",
            )
        )

    def record_api_call(
        self,
        operation: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float,
        duration: float,
    ):
        """Record a successful API call"""
        if not self.enabled:
            return

        call_record = ApiCallRecord(
            timestamp=datetime.now(),
            operation=operation,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost,
            duration=duration,
            success=True,
        )

        self.api_calls.append(call_record)
        self.actual_debug_cost += cost

        # Track by operation
        if operation not in self.operation_costs:
            self.operation_costs[operation] = 0.0
        self.operation_costs[operation] += cost

        # Track by model
        if model not in self.model_usage:
            self.model_usage[model] = {
                "calls": 0,
                "total_cost": 0.0,
                "total_tokens": 0,
                "avg_duration": 0.0,
            }

        model_stats = self.model_usage[model]
        model_stats["calls"] += 1
        model_stats["total_cost"] += cost
        model_stats["total_tokens"] += prompt_tokens + completion_tokens

        # Update average duration
        old_avg = model_stats["avg_duration"]
        model_stats["avg_duration"] = (
            old_avg * (model_stats["calls"] - 1) + duration
        ) / model_stats["calls"]

        # Estimate production cost for comparison
        production_cost = self._estimate_production_cost(
            model, prompt_tokens, completion_tokens
        )
        self.estimated_production_cost += production_cost

        # Display real-time cost update
        self._display_cost_update(call_record, production_cost)

    def record_failed_call(self, operation: str, error: str):
        """Record a failed API call"""
        if not self.enabled:
            return

        failed_record = ApiCallRecord(
            timestamp=datetime.now(),
            operation=operation,
            model="unknown",
            prompt_tokens=0,
            completion_tokens=0,
            cost=0.0,
            duration=0.0,
            success=False,
        )

        self.api_calls.append(failed_record)

        self.console.print(f"[red]💸 Failed call recorded:[/red] {operation} - {error}")

    def record_blocked_call(
        self,
        operation: str,
        estimated_tokens: int,
        estimated_cost: float,
        reason: str = "limit_exceeded",
    ):
        """Record a call that was blocked due to limits"""
        if not self.enabled:
            return

        blocked_record = BlockedCallRecord(
            timestamp=datetime.now(),
            operation=operation,
            estimated_tokens=estimated_tokens,
            estimated_cost=estimated_cost,
            reason=reason,
        )

        self.blocked_calls.append(blocked_record)

        self.console.print(
            f"[yellow]🚫 Blocked call:[/yellow] {operation} "
            f"[dim](would cost ${estimated_cost:.4f})[/dim]"
        )

    def _estimate_production_cost(
        self, debug_model: str, prompt_tokens: int, completion_tokens: int
    ) -> float:
        """Estimate what this call would have cost with production models"""
        # Map debug models back to typical production models
        production_mapping = {
            "claude-3-haiku-20240307": "claude-3-5-sonnet-20241022",
            "gpt-3.5-turbo": "gpt-4-turbo",
            "command-light": "command",
        }

        production_model = production_mapping.get(debug_model, debug_model)

        # Calculate cost with production model
        if "claude" in production_model:
            provider = ModelProvider.ANTHROPIC
        elif "gpt" in production_model:
            provider = ModelProvider.OPENAI
        else:
            provider = ModelProvider.COHERE

        return calculate_api_cost(
            provider, production_model, prompt_tokens, completion_tokens
        )

    def _display_cost_update(
        self, call_record: ApiCallRecord, estimated_production_cost: float
    ):
        """Display real-time cost update"""
        if not self.enabled:
            return

        savings = estimated_production_cost - call_record.cost
        savings_pct = (
            (savings / estimated_production_cost * 100)
            if estimated_production_cost > 0
            else 0
        )

        self.console.print(
            f"[green]💰 Cost:[/green] ${call_record.cost:.4f} "
            f"[dim](vs ${estimated_production_cost:.4f} production, "
            f"saved ${savings:.4f} / {savings_pct:.1f}%)[/dim]"
        )

    def get_current_cost(self) -> float:
        """Get current session cost"""
        return self.actual_debug_cost

    def get_estimated_savings(self) -> float:
        """Get estimated savings compared to production"""
        return self.estimated_production_cost - self.actual_debug_cost

    def get_savings_percentage(self) -> float:
        """Get savings percentage"""
        if self.estimated_production_cost == 0:
            return 0.0
        return (self.get_estimated_savings() / self.estimated_production_cost) * 100

    def display_real_time_summary(self):
        """Display real-time cost summary"""
        if not self.enabled or not self.api_calls:
            return

        total_calls = len(self.api_calls)
        successful_calls = len([c for c in self.api_calls if c.success])
        current_cost = self.get_current_cost()
        estimated_savings = self.get_estimated_savings()
        savings_pct = self.get_savings_percentage()

        summary_text = (
            f"[bold]Session Summary[/bold]\n"
            f"Calls: {successful_calls}/{total_calls} successful\n"
            f"Cost: ${current_cost:.4f}\n"
            f"Estimated Savings: ${estimated_savings:.4f} ({savings_pct:.1f}%)\n"
            f"Blocked Calls: {len(self.blocked_calls)}"
        )

        self.console.print(
            Panel(summary_text, title="💰 Cost Tracker", border_style="green")
        )

    def display_detailed_breakdown(self):
        """Display detailed cost breakdown"""
        if not self.enabled:
            return

        # Operations table
        if self.operation_costs:
            ops_table = Table(title="Cost by Operation", show_header=True)
            ops_table.add_column("Operation", style="cyan")
            ops_table.add_column("Total Cost", style="green")
            ops_table.add_column("% of Total", style="yellow")

            total_cost = sum(self.operation_costs.values())

            for operation, cost in sorted(
                self.operation_costs.items(), key=lambda x: x[1], reverse=True
            ):
                percentage = (cost / total_cost * 100) if total_cost > 0 else 0
                ops_table.add_row(operation, f"${cost:.4f}", f"{percentage:.1f}%")

            self.console.print(ops_table)

        # Models table
        if self.model_usage:
            models_table = Table(title="Usage by Model", show_header=True)
            models_table.add_column("Model", style="cyan")
            models_table.add_column("Calls", style="yellow")
            models_table.add_column("Total Cost", style="green")
            models_table.add_column("Avg Cost", style="blue")
            models_table.add_column("Total Tokens", style="magenta")
            models_table.add_column("Avg Duration", style="red")

            for model, stats in sorted(
                self.model_usage.items(), key=lambda x: x[1]["total_cost"], reverse=True
            ):
                avg_cost = (
                    stats["total_cost"] / stats["calls"] if stats["calls"] > 0 else 0
                )
                models_table.add_row(
                    model,
                    str(stats["calls"]),
                    f"${stats['total_cost']:.4f}",
                    f"${avg_cost:.4f}",
                    f"{stats['total_tokens']:,}",
                    f"{stats['avg_duration']:.2f}s",
                )

            self.console.print(models_table)

    def get_summary(self) -> DebugCostSummary:
        """Get comprehensive cost summary"""
        if not self.enabled:
            return DebugCostSummary(session_start=datetime.now())

        successful_calls = [c for c in self.api_calls if c.success]
        total_cost = sum(c.cost for c in successful_calls)
        total_tokens = sum(
            c.prompt_tokens + c.completion_tokens for c in successful_calls
        )

        # Find most expensive operation
        most_expensive_op = ""
        most_expensive_cost = 0.0
        if self.operation_costs:
            most_expensive_op = max(self.operation_costs, key=self.operation_costs.get)
            most_expensive_cost = self.operation_costs[most_expensive_op]

        return DebugCostSummary(
            session_start=self.session_start,
            total_api_calls=len(successful_calls),
            total_cost=total_cost,
            total_tokens=total_tokens,
            total_blocked_calls=len(self.blocked_calls),
            estimated_savings=self.get_estimated_savings(),
            average_call_cost=total_cost / len(successful_calls)
            if successful_calls
            else 0.0,
            most_expensive_operation=most_expensive_op,
            most_expensive_cost=most_expensive_cost,
            call_records=self.api_calls,
            blocked_records=self.blocked_calls,
        )

    def generate_cost_report(self) -> Dict[str, Any]:
        """Generate comprehensive cost report"""
        if not self.enabled:
            return {"debug_mode": False}

        session_duration = datetime.now() - self.session_start
        summary = self.get_summary()

        return {
            "debug_mode": True,
            "session_duration_seconds": session_duration.total_seconds(),
            "total_api_calls": summary.total_api_calls,
            "successful_calls": len([c for c in self.api_calls if c.success]),
            "failed_calls": len([c for c in self.api_calls if not c.success]),
            "blocked_calls": summary.total_blocked_calls,
            "costs": {
                "actual_cost": summary.total_cost,
                "estimated_production_cost": self.estimated_production_cost,
                "estimated_savings": summary.estimated_savings,
                "savings_percentage": self.get_savings_percentage(),
                "average_call_cost": summary.average_call_cost,
            },
            "usage": {
                "total_tokens": summary.total_tokens,
                "operations": dict(self.operation_costs),
                "models": dict(self.model_usage),
            },
            "most_expensive": {
                "operation": summary.most_expensive_operation,
                "cost": summary.most_expensive_cost,
            },
        }

    def display_final_report(self):
        """Display final cost tracking report"""
        if not self.enabled:
            return

        session_duration = datetime.now() - self.session_start
        report = self.generate_cost_report()

        # Main summary panel
        summary_text = (
            f"[bold]Final Cost Report[/bold]\n"
            f"Session Duration: {session_duration.total_seconds():.1f}s\n"
            f"Total API Calls: {report['total_api_calls']}\n"
            f"Successful: {report['successful_calls']}\n"
            f"Failed: {report['failed_calls']}\n"
            f"Blocked: {report['blocked_calls']}\n\n"
            f"[bold green]Actual Cost: ${report['costs']['actual_cost']:.4f}[/bold green]\n"
            f"[bold yellow]Est. Production Cost: ${report['costs']['estimated_production_cost']:.4f}[/bold yellow]\n"
            f"[bold blue]Estimated Savings: ${report['costs']['estimated_savings']:.4f} "
            f"({report['costs']['savings_percentage']:.1f}%)[/bold blue]"
        )

        self.console.print(
            Panel(summary_text, title="💰 Debug Cost Report", border_style="green")
        )

        # Detailed breakdown
        self.display_detailed_breakdown()


# Global cost tracker instance
_cost_tracker: Optional[DebugCostTracker] = None


def get_debug_cost_tracker() -> DebugCostTracker:
    """Get the global debug cost tracker instance"""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = DebugCostTracker()
    return _cost_tracker


def initialize_debug_cost_tracker() -> DebugCostTracker:
    """Initialize the global debug cost tracker"""
    global _cost_tracker
    _cost_tracker = DebugCostTracker()
    return _cost_tracker
