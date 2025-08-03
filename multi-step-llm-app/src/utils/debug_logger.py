"""
Debug logger for verbose debugging and API request/response logging
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markup import escape

from ..models.logging_models import ComponentType


class DebugLogger:
    """
    Specialized logger for debug mode with verbose API tracking
    """
    
    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialize debug logger
        
        Args:
            log_dir: Directory for debug logs (default: logs/debug)
        """
        self.enabled = os.getenv("DEBUG", "").lower() in ["true", "1", "yes", "on"]
        
        if not self.enabled:
            return
        
        # Setup logging directory
        self.log_dir = Path(log_dir or "logs/debug")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Console for rich output
        self.console = Console(force_terminal=True, width=120)
        
        # Log files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.debug_log_file = self.log_dir / f"debug_{timestamp}.jsonl"
        self.api_log_file = self.log_dir / f"api_debug_{timestamp}.jsonl"
        self.truncation_log_file = self.log_dir / f"truncations_{timestamp}.jsonl"
        
        # Open file handles
        self.debug_file = open(self.debug_log_file, 'a', encoding='utf-8')
        self.api_file = open(self.api_log_file, 'a', encoding='utf-8')
        self.truncation_file = open(self.truncation_log_file, 'a', encoding='utf-8')
        
        # Tracking
        self.session_start = datetime.now()
        self.api_calls = []
        self.model_switches = []
        self.truncations = []
        
        self._log_debug_session_start()
    
    def _log_debug_session_start(self):
        """Log the start of a debug session"""
        start_info = {
            "event": "debug_session_start",
            "timestamp": self.session_start.isoformat(),
            "log_files": {
                "debug": str(self.debug_log_file),
                "api": str(self.api_log_file),
                "truncations": str(self.truncation_log_file)
            }
        }
        
        self._write_log_entry(start_info, self.debug_file)
        
        # Rich console output
        self.console.print(Panel.fit(
            "[bold cyan]🐛 DEBUG MODE ENABLED[/bold cyan]\n"
            f"Session started: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Debug logs: {self.debug_log_file}",
            border_style="cyan"
        ))
    
    def _write_log_entry(self, entry: Dict[str, Any], file_handle):
        """Write a log entry to file"""
        if not self.enabled:
            return
        
        entry["debug_timestamp"] = datetime.now().isoformat()
        json_line = json.dumps(entry, default=str) + '\n'
        file_handle.write(json_line)
        file_handle.flush()
    
    def log_component_init(self, component_type: ComponentType):
        """Log component initialization in debug mode"""
        if not self.enabled:
            return
        
        entry = {
            "event": "component_init",
            "component": component_type.value,
            "debug_mode": True
        }
        
        self._write_log_entry(entry, self.debug_file)
        
        self.console.print(f"[dim cyan]🔧 Debug-aware component initialized: {component_type.value}[/dim cyan]")
    
    def log_model_switch(self, production_model: str, debug_model: str, 
                        operation: Optional[str], component: ComponentType):
        """Log when a model is switched for debug mode"""
        if not self.enabled:
            return
        
        switch_info = {
            "event": "model_switch",
            "component": component.value,
            "production_model": production_model,
            "debug_model": debug_model,
            "operation": operation,
            "cost_savings_potential": self._calculate_cost_savings(production_model, debug_model)
        }
        
        self.model_switches.append(switch_info)
        self._write_log_entry(switch_info, self.debug_file)
        
        # Rich console output
        savings = switch_info["cost_savings_potential"]
        self.console.print(
            f"[yellow]🔄 Model switch:[/yellow] {production_model} → [green]{debug_model}[/green] "
            f"[dim](~{savings:.1%} cost savings)[/dim]"
        )
    
    def log_api_call_start(self, model: str, operation: str, component: ComponentType, 
                          estimated_tokens: int):
        """Log the start of an API call"""
        if not self.enabled:
            return
        
        call_info = {
            "event": "api_call_start",
            "component": component.value,
            "model": model,
            "operation": operation,
            "estimated_tokens": estimated_tokens,
            "start_time": datetime.now().isoformat()
        }
        
        self._write_log_entry(call_info, self.api_file)
        
        self.console.print(
            f"[blue]📞 API Call:[/blue] {model} for {operation} "
            f"[dim](~{estimated_tokens} tokens)[/dim]"
        )
    
    def log_api_call_success(self, model: str, operation: str, component: ComponentType,
                           total_tokens: int, cost: float, duration: float):
        """Log successful API call completion"""
        if not self.enabled:
            return
        
        call_info = {
            "event": "api_call_success",
            "component": component.value,
            "model": model,
            "operation": operation,
            "total_tokens": total_tokens,
            "cost": cost,
            "duration": duration,
            "end_time": datetime.now().isoformat()
        }
        
        self.api_calls.append(call_info)
        self._write_log_entry(call_info, self.api_file)
        
        self.console.print(
            f"[green]✅ API Success:[/green] {model} "
            f"[dim]({total_tokens} tokens, ${cost:.4f}, {duration:.2f}s)[/dim]"
        )
    
    def log_api_call_error(self, model: str, operation: str, component: ComponentType,
                          error: str, duration: float):
        """Log failed API call"""
        if not self.enabled:
            return
        
        error_info = {
            "event": "api_call_error",
            "component": component.value,
            "model": model,
            "operation": operation,
            "error": error,
            "duration": duration,
            "end_time": datetime.now().isoformat()
        }
        
        self._write_log_entry(error_info, self.api_file)
        
        self.console.print(
            f"[red]❌ API Error:[/red] {model} - {error} "
            f"[dim]({duration:.2f}s)[/dim]"
        )
    
    def log_content_truncation(self, original_length: int, truncated_length: int,
                             operation: str, component: ComponentType):
        """Log content truncation for debug mode"""
        if not self.enabled:
            return
        
        truncation_info = {
            "event": "content_truncation",
            "component": component.value,
            "operation": operation,
            "original_length": original_length,
            "truncated_length": truncated_length,
            "reduction_percentage": ((original_length - truncated_length) / original_length) * 100
        }
        
        self.truncations.append(truncation_info)
        self._write_log_entry(truncation_info, self.truncation_file)
        
        reduction = truncation_info["reduction_percentage"]
        self.console.print(
            f"[yellow]✂️  Content truncated:[/yellow] {original_length:,} → {truncated_length:,} chars "
            f"[dim]({reduction:.1f}% reduction)[/dim]"
        )
    
    def log_limit_exceeded(self, estimated_tokens: int, estimated_cost: float,
                          operation: str, component: ComponentType):
        """Log when limits would be exceeded"""
        if not self.enabled:
            return
        
        limit_info = {
            "event": "limit_exceeded",
            "component": component.value,
            "operation": operation,
            "estimated_tokens": estimated_tokens,
            "estimated_cost": estimated_cost
        }
        
        self._write_log_entry(limit_info, self.debug_file)
        
        self.console.print(
            f"[red]🚫 Limit exceeded:[/red] {operation} "
            f"[dim](would use {estimated_tokens} tokens, ${estimated_cost:.4f})[/dim]"
        )
    
    def log_operation_skipped(self, operation: str, estimated_cost: float,
                            component: ComponentType, reason: str):
        """Log when an operation is skipped"""
        if not self.enabled:
            return
        
        skip_info = {
            "event": "operation_skipped",
            "component": component.value,
            "operation": operation,
            "estimated_cost": estimated_cost,
            "reason": reason
        }
        
        self._write_log_entry(skip_info, self.debug_file)
        
        self.console.print(
            f"[yellow]⏭️  Operation skipped:[/yellow] {operation} "
            f"[dim](reason: {reason}, would cost ${estimated_cost:.4f})[/dim]"
        )
    
    def log_api_request_details(self, model: str, prompt: str, system_prompt: str,
                              max_tokens: int, temperature: float):
        """Log detailed API request information"""
        if not self.enabled:
            return
        
        # Truncate prompts for logging
        truncated_prompt = self._truncate_for_log(prompt, 500)
        truncated_system = self._truncate_for_log(system_prompt, 200)
        
        request_info = {
            "event": "api_request_details",
            "model": model,
            "prompt_preview": truncated_prompt,
            "system_prompt_preview": truncated_system,
            "prompt_length": len(prompt),
            "system_prompt_length": len(system_prompt),
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        self._write_log_entry(request_info, self.api_file)
    
    def log_api_response_details(self, model: str, response: str, 
                               actual_tokens: Optional[int] = None):
        """Log detailed API response information"""
        if not self.enabled:
            return
        
        truncated_response = self._truncate_for_log(response, 500)
        
        response_info = {
            "event": "api_response_details",
            "model": model,
            "response_preview": truncated_response,
            "response_length": len(response),
            "actual_tokens": actual_tokens
        }
        
        self._write_log_entry(response_info, self.api_file)
    
    def _truncate_for_log(self, text: str, max_length: int) -> str:
        """Truncate text for logging purposes"""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "... [TRUNCATED]"
    
    def _calculate_cost_savings(self, production_model: str, debug_model: str) -> float:
        """Calculate potential cost savings from model switch"""
        # Rough cost ratios based on typical pricing
        cost_ratios = {
            "claude-3-opus-20240229": 1.0,
            "claude-3-5-sonnet-20241022": 0.2,
            "claude-3-sonnet-20240229": 0.2,
            "claude-3-haiku-20240307": 0.017,
            "gpt-4": 1.0,
            "gpt-4-turbo": 0.33,
            "gpt-3.5-turbo": 0.05,
            "command": 1.0,
            "command-light": 0.6
        }
        
        production_cost = cost_ratios.get(production_model, 1.0)
        debug_cost = cost_ratios.get(debug_model, 1.0)
        
        if production_cost == 0:
            return 0.0
        
        return 1.0 - (debug_cost / production_cost)
    
    def display_session_summary(self):
        """Display a comprehensive debug session summary"""
        if not self.enabled:
            return
        
        session_duration = datetime.now() - self.session_start
        
        # Create summary table
        table = Table(title="Debug Session Summary", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        table.add_row("Session Duration", f"{session_duration.total_seconds():.1f} seconds")
        table.add_row("API Calls", str(len(self.api_calls)))
        table.add_row("Model Switches", str(len(self.model_switches)))
        table.add_row("Content Truncations", str(len(self.truncations)))
        
        # Calculate total costs and savings
        total_actual_cost = sum(call.get("cost", 0) for call in self.api_calls)
        table.add_row("Total API Cost", f"${total_actual_cost:.4f}")
        
        # Average cost savings from model switches
        if self.model_switches:
            avg_savings = sum(switch["cost_savings_potential"] for switch in self.model_switches) / len(self.model_switches)
            table.add_row("Avg Cost Savings", f"{avg_savings:.1%}")
        
        self.console.print(table)
        
        # Model usage breakdown
        if self.api_calls:
            model_usage = {}
            for call in self.api_calls:
                model = call.get("model", "unknown")
                if model not in model_usage:
                    model_usage[model] = {"calls": 0, "cost": 0.0, "tokens": 0}
                model_usage[model]["calls"] += 1
                model_usage[model]["cost"] += call.get("cost", 0)
                model_usage[model]["tokens"] += call.get("total_tokens", 0)
            
            model_table = Table(title="Model Usage", show_header=True)
            model_table.add_column("Model", style="cyan")
            model_table.add_column("Calls", style="yellow")
            model_table.add_column("Tokens", style="green")
            model_table.add_column("Cost", style="red")
            
            for model, stats in model_usage.items():
                model_table.add_row(
                    model,
                    str(stats["calls"]),
                    f"{stats['tokens']:,}",
                    f"${stats['cost']:.4f}"
                )
            
            self.console.print(model_table)
    
    def close(self):
        """Close debug logger and cleanup"""
        if not self.enabled:
            return
        
        # Log session end
        end_info = {
            "event": "debug_session_end",
            "session_duration": (datetime.now() - self.session_start).total_seconds(),
            "total_api_calls": len(self.api_calls),
            "total_model_switches": len(self.model_switches),
            "total_truncations": len(self.truncations)
        }
        
        self._write_log_entry(end_info, self.debug_file)
        
        # Display summary
        self.display_session_summary()
        
        # Close file handles
        self.debug_file.close()
        self.api_file.close()
        self.truncation_file.close()
        
        self.console.print(f"\n[dim cyan]Debug logs saved to: {self.log_dir}[/dim cyan]")


# Global debug logger instance
_debug_logger: Optional[DebugLogger] = None


def get_debug_logger() -> DebugLogger:
    """Get the global debug logger instance"""
    global _debug_logger
    if _debug_logger is None:
        _debug_logger = DebugLogger()
    return _debug_logger


def initialize_debug_logger(log_dir: Optional[str] = None) -> DebugLogger:
    """Initialize the global debug logger"""
    global _debug_logger
    _debug_logger = DebugLogger(log_dir)
    return _debug_logger


def close_debug_logger():
    """Close the global debug logger"""
    global _debug_logger
    if _debug_logger:
        _debug_logger.close()
        _debug_logger = None