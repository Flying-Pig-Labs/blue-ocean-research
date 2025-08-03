"""
Comprehensive logging system for the Helios pipeline
"""

import json
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, TextIO, Union
from contextlib import contextmanager
import threading
from concurrent.futures import ThreadPoolExecutor
import logging
import logging.handlers

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, SpinnerColumn
from rich.logging import RichHandler
from rich.text import Text
from rich.markup import escape

from ..models.logging_models import (
    LogEntry, APICallLog, ComponentLog, SessionInfo, ProgressEntry,
    TokenUsageSummary, SessionSummary, LogLevel, ComponentType, 
    ModelProvider, calculate_api_cost
)
from ..config import Config, LoggingMode


class PipelineLogger:
    """
    Comprehensive logging system with Rich console output and structured JSON logging
    """
    
    def __init__(self, config: Optional[Config] = None, session_id: Optional[str] = None):
        """Initialize the pipeline logger"""
        from ..config import get_config
        
        self.config = config or get_config()
        self.session_id = session_id or self._generate_session_id()
        self.start_time = datetime.now()
        
        # Thread-safe containers
        self._lock = threading.Lock()
        self._api_calls: List[APICallLog] = []
        self._component_logs: List[ComponentLog] = []
        self._log_entries: List[LogEntry] = []
        self._progress_entries: List[ProgressEntry] = []
        
        # Rich console setup
        self.console = Console(
            force_terminal=True if self.config.logging.colored_output else None,
            width=120
        )
        
        # Session management
        self.session_info = self._create_session_info()
        self.session_dir = self._setup_session_directory()
        
        # File handlers
        self._log_files: Dict[str, TextIO] = {}
        self._setup_file_logging()
        
        # Standard logging integration
        self._setup_standard_logging()
        
        # Active progress bars
        self._active_progress: Dict[str, Progress] = {}
        
        # Component loggers cache
        self._component_loggers: Dict[ComponentType, logging.Logger] = {}
        
        self.info("Pipeline logger initialized", component=ComponentType.MAIN_PIPELINE)
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"session_{timestamp}_{unique_id}"
    
    def _create_session_info(self) -> SessionInfo:
        """Create session info object"""
        return SessionInfo(
            session_id=self.session_id,
            start_time=self.start_time,
            session_dir=str(self.config.get_log_directory() / f"{self.session_id}"),
            pipeline_version=self.config.pipeline.pipeline_version
        )
    
    def _setup_session_directory(self) -> Path:
        """Setup session-specific log directory"""
        if not self.config.logging.session_logs:
            return self.config.get_log_directory()
        
        timestamp = self.start_time.strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = self.config.get_log_directory() / timestamp
        session_dir.mkdir(parents=True, exist_ok=True)
        
        self.session_info.session_dir = str(session_dir)
        return session_dir
    
    def _setup_file_logging(self):
        """Setup JSON file logging"""
        if self.config.logging.mode in [LoggingMode.FILE_ONLY, LoggingMode.BOTH]:
            # Main session log
            session_log_path = self.session_dir / "session.jsonl"
            self._log_files['session'] = open(session_log_path, 'a', encoding='utf-8')
            
            # API calls log
            api_log_path = self.session_dir / "api_calls.jsonl"
            self._log_files['api'] = open(api_log_path, 'a', encoding='utf-8')
            
            # Component operations log
            component_log_path = self.session_dir / "components.jsonl"
            self._log_files['components'] = open(component_log_path, 'a', encoding='utf-8')
            
            # Progress tracking log
            progress_log_path = self.session_dir / "progress.jsonl"
            self._log_files['progress'] = open(progress_log_path, 'a', encoding='utf-8')
    
    def _setup_standard_logging(self):
        """Setup standard Python logging integration"""
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.logging.file_level))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Add Rich handler for console output
        if self.config.logging.mode in [LoggingMode.CONSOLE_ONLY, LoggingMode.BOTH]:
            if self.config.logging.use_rich:
                rich_handler = RichHandler(
                    console=self.console,
                    level=getattr(logging, self.config.logging.console_level),
                    show_path=False,
                    show_time=True,
                    rich_tracebacks=True
                )
                rich_handler.setFormatter(logging.Formatter("%(message)s"))
                root_logger.addHandler(rich_handler)
        
        # Add file handler
        if self.config.logging.mode in [LoggingMode.FILE_ONLY, LoggingMode.BOTH]:
            file_handler = logging.handlers.RotatingFileHandler(
                self.session_dir / "standard.log",
                maxBytes=self.config.logging.max_file_size_mb * 1024 * 1024,
                backupCount=5
            )
            file_handler.setLevel(getattr(logging, self.config.logging.file_level))
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            root_logger.addHandler(file_handler)
    
    def get_component_logger(self, component: ComponentType) -> logging.Logger:
        """Get a component-specific logger"""
        if component not in self._component_loggers:
            logger = logging.getLogger(f"helios.{component.value}")
            level = self.config.logging.component_loggers.get(
                component.value, 
                self.config.logging.console_level
            )
            logger.setLevel(getattr(logging, level))
            self._component_loggers[component] = logger
        
        return self._component_loggers[component]
    
    def _write_json_log(self, log_type: str, data: Dict[str, Any]):
        """Write JSON log entry to file"""
        if log_type in self._log_files:
            json_line = json.dumps(data, default=str) + '\n'
            self._log_files[log_type].write(json_line)
            self._log_files[log_type].flush()
    
    def log(self, level: LogLevel, message: str, component: ComponentType, 
            operation: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None,
            call_id: Optional[str] = None, stack_trace: Optional[str] = None):
        """General logging method"""
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            component=component,
            message=message,
            operation=operation,
            session_id=self.session_id,
            call_id=call_id,
            metadata=metadata or {},
            stack_trace=stack_trace
        )
        
        with self._lock:
            self._log_entries.append(entry)
        
        # Write to JSON log
        self._write_json_log('session', entry.model_dump())
        
        # Console output
        if self.config.logging.mode in [LoggingMode.CONSOLE_ONLY, LoggingMode.BOTH]:
            self._print_console_log(entry)
        
        # Standard logging
        logger = self.get_component_logger(component)
        getattr(logger, level.value.lower())(
            f"[{operation}] {message}" if operation else message,
            extra={"metadata": metadata}
        )
    
    def _print_console_log(self, entry: LogEntry):
        """Print formatted log entry to console"""
        if not self.config.logging.use_rich:
            return
        
        # Color mapping for log levels
        level_colors = {
            LogLevel.DEBUG: "dim white",
            LogLevel.INFO: "cyan",
            LogLevel.WARNING: "yellow",
            LogLevel.ERROR: "red",
            LogLevel.CRITICAL: "bold red"
        }
        
        color = level_colors.get(entry.level, "white")
        timestamp = entry.timestamp.strftime("%H:%M:%S")
        
        # Format message
        component_text = f"[bold blue]{entry.component.value}[/bold blue]"
        operation_text = f"[dim]({entry.operation})[/dim]" if entry.operation else ""
        message_text = f"[{color}]{escape(entry.message)}[/{color}]"
        
        formatted = f"[dim]{timestamp}[/dim] {component_text} {operation_text} {message_text}"
        
        if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            self.console.print(Panel(formatted, border_style="red"))
        else:
            self.console.print(formatted)
    
    def debug(self, message: str, component: ComponentType, operation: Optional[str] = None, **kwargs):
        """Log debug message"""
        self.log(LogLevel.DEBUG, message, component, operation, **kwargs)
    
    def info(self, message: str, component: ComponentType, operation: Optional[str] = None, **kwargs):
        """Log info message"""
        self.log(LogLevel.INFO, message, component, operation, **kwargs)
    
    def warning(self, message: str, component: ComponentType, operation: Optional[str] = None, **kwargs):
        """Log warning message"""
        self.log(LogLevel.WARNING, message, component, operation, **kwargs)
    
    def error(self, message: str, component: ComponentType, operation: Optional[str] = None, **kwargs):
        """Log error message"""
        self.log(LogLevel.ERROR, message, component, operation, **kwargs)
    
    def critical(self, message: str, component: ComponentType, operation: Optional[str] = None, **kwargs):
        """Log critical message"""
        self.log(LogLevel.CRITICAL, message, component, operation, **kwargs)
    
    @contextmanager
    def log_operation(self, component: ComponentType, operation: str, 
                     input_data_size: int = 0, metadata: Optional[Dict[str, Any]] = None):
        """Context manager for logging component operations"""
        start_time = datetime.now()
        self.info(f"Starting {operation}", component, operation, metadata=metadata)
        
        component_log = ComponentLog(
            component=component,
            operation=operation,
            start_time=start_time,
            input_data_size=input_data_size,
            metadata=metadata or {}
        )
        
        try:
            yield component_log
            
            # Operation completed successfully
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            component_log.end_time = end_time
            component_log.duration = duration
            component_log.success = True
            
            self.info(f"Completed {operation} in {duration:.2f}s", component, operation)
            
        except Exception as e:
            # Operation failed
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            component_log.end_time = end_time
            component_log.duration = duration
            component_log.success = False
            component_log.error_message = str(e)
            
            self.error(f"Failed {operation} after {duration:.2f}s: {e}", component, operation)
            raise
        
        finally:
            with self._lock:
                self._component_logs.append(component_log)
            self._write_json_log('components', component_log.model_dump())
    
    def log_api_call(self, component: ComponentType, provider: ModelProvider, model: str,
                    prompt_tokens: int, completion_tokens: int, duration: float,
                    success: bool = True, error_message: Optional[str] = None,
                    request_size: int = 0, response_size: int = 0) -> str:
        """Log an API call with cost calculation"""
        call_id = str(uuid.uuid4())
        total_tokens = prompt_tokens + completion_tokens
        estimated_cost = calculate_api_cost(provider, model, prompt_tokens, completion_tokens)
        
        api_call = APICallLog(
            call_id=call_id,
            timestamp=datetime.now(),
            component=component,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            duration=duration,
            success=success,
            error_message=error_message,
            request_size=request_size,
            response_size=response_size
        )
        
        with self._lock:
            self._api_calls.append(api_call)
            self.session_info.total_api_calls += 1
            self.session_info.total_cost += estimated_cost
            self.session_info.total_tokens += total_tokens
        
        # Write to API log
        self._write_json_log('api', api_call.model_dump())
        
        # Console output
        if success:
            self.info(
                f"API call completed: {model} ({total_tokens} tokens, ${estimated_cost:.4f})",
                component, "api_call", metadata={
                    "call_id": call_id,
                    "model": model,
                    "tokens": total_tokens,
                    "cost": estimated_cost
                }
            )
        else:
            self.error(
                f"API call failed: {model} - {error_message}",
                component, "api_call", metadata={"call_id": call_id}
            )
        
        return call_id
    
    @contextmanager
    def track_api_call(self, component: ComponentType, provider: ModelProvider, model: str):
        """Context manager for tracking API calls"""
        start_time = time.time()
        call_data = {
            "component": component,
            "provider": provider,
            "model": model,
            "start_time": start_time
        }
        
        try:
            yield call_data
            
            duration = time.time() - start_time
            
            # Extract token information from call_data
            prompt_tokens = call_data.get("prompt_tokens", 0)
            completion_tokens = call_data.get("completion_tokens", 0)
            request_size = call_data.get("request_size", 0)
            response_size = call_data.get("response_size", 0)
            
            self.log_api_call(
                component, provider, model, prompt_tokens, completion_tokens,
                duration, True, None, request_size, response_size
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_api_call(
                component, provider, model, 0, 0, duration, False, str(e)
            )
            raise
    
    def create_progress_bar(self, description: str, total: int, component: ComponentType) -> str:
        """Create a progress bar and return its ID"""
        if not self.config.logging.show_progress_bars:
            return ""
        
        progress_id = str(uuid.uuid4())
        
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self.console
        )
        
        task_id = progress.add_task(description, total=total)
        
        self._active_progress[progress_id] = {
            "progress": progress,
            "task_id": task_id,
            "component": component,
            "description": description,
            "total": total,
            "start_time": datetime.now()
        }
        
        progress.start()
        return progress_id
    
    def update_progress(self, progress_id: str, advance: int = 1, description: Optional[str] = None):
        """Update progress bar"""
        if progress_id not in self._active_progress:
            return
        
        progress_info = self._active_progress[progress_id]
        progress = progress_info["progress"]
        task_id = progress_info["task_id"]
        
        progress.update(task_id, advance=advance)
        
        if description:
            progress.update(task_id, description=description)
        
        # Log progress entry
        current_completed = progress.tasks[task_id].completed
        total = progress_info["total"]
        percentage = (current_completed / total) * 100 if total > 0 else 0
        
        progress_entry = ProgressEntry(
            timestamp=datetime.now(),
            component=progress_info["component"],
            operation=progress_info["description"],
            current=int(current_completed),
            total=total,
            percentage=percentage
        )
        
        with self._lock:
            self._progress_entries.append(progress_entry)
        
        self._write_json_log('progress', progress_entry.model_dump())
    
    def complete_progress(self, progress_id: str):
        """Complete and remove progress bar"""
        if progress_id not in self._active_progress:
            return
        
        progress_info = self._active_progress[progress_id]
        progress = progress_info["progress"]
        
        progress.stop()
        del self._active_progress[progress_id]
    
    def display_session_summary(self):
        """Display a comprehensive session summary"""
        if not self.config.logging.use_rich:
            return
        
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Update session info
        self.session_info.end_time = end_time
        
        # Create summary table
        table = Table(title="Pipeline Session Summary", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        table.add_row("Session ID", self.session_id)
        table.add_row("Duration", f"{total_duration:.2f} seconds")
        table.add_row("Total API Calls", str(self.session_info.total_api_calls))
        table.add_row("Total Tokens", f"{self.session_info.total_tokens:,}")
        table.add_row("Estimated Cost", f"${self.session_info.total_cost:.4f}")
        
        # Error counts
        error_count = len([e for e in self._log_entries if e.level == LogLevel.ERROR])
        warning_count = len([e for e in self._log_entries if e.level == LogLevel.WARNING])
        table.add_row("Errors", str(error_count))
        table.add_row("Warnings", str(warning_count))
        
        # Success rate
        total_operations = len(self._component_logs)
        successful_operations = len([c for c in self._component_logs if c.success])
        success_rate = (successful_operations / total_operations * 100) if total_operations > 0 else 100
        table.add_row("Success Rate", f"{success_rate:.1f}%")
        
        self.console.print(table)
        
        # API calls by component
        if self._api_calls:
            api_table = Table(title="API Usage by Component", show_header=True)
            api_table.add_column("Component", style="cyan")
            api_table.add_column("Calls", style="yellow")
            api_table.add_column("Tokens", style="green")
            api_table.add_column("Cost", style="red")
            
            component_stats = {}
            for call in self._api_calls:
                comp = call.component.value
                if comp not in component_stats:
                    component_stats[comp] = {"calls": 0, "tokens": 0, "cost": 0.0}
                component_stats[comp]["calls"] += 1
                component_stats[comp]["tokens"] += call.total_tokens
                component_stats[comp]["cost"] += call.estimated_cost
            
            for comp, stats in component_stats.items():
                api_table.add_row(
                    comp,
                    str(stats["calls"]),
                    f"{stats['tokens']:,}",
                    f"${stats['cost']:.4f}"
                )
            
            self.console.print(api_table)
    
    def export_session_data(self, export_path: Optional[Path] = None) -> Path:
        """Export complete session data to JSON"""
        if export_path is None:
            export_path = self.session_dir / "session_export.json"
        
        # Create session summary
        end_time = datetime.now() if self.session_info.end_time is None else self.session_info.end_time
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Component usage summary
        components_used = list(set(log.component for log in self._component_logs))
        
        # Token usage by component
        api_summary = {}
        for call in self._api_calls:
            comp = call.component.value
            if comp not in api_summary:
                api_summary[comp] = {
                    "total_calls": 0,
                    "total_tokens": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "estimated_cost": 0.0,
                    "models_used": set()
                }
            api_summary[comp]["total_calls"] += 1
            api_summary[comp]["total_tokens"] += call.total_tokens
            api_summary[comp]["prompt_tokens"] += call.prompt_tokens
            api_summary[comp]["completion_tokens"] += call.completion_tokens
            api_summary[comp]["estimated_cost"] += call.estimated_cost
            api_summary[comp]["models_used"].add(call.model)
        
        # Convert sets to lists for JSON serialization
        for comp_data in api_summary.values():
            comp_data["models_used"] = list(comp_data["models_used"])
        
        # Error and warning counts
        error_count = len([e for e in self._log_entries if e.level == LogLevel.ERROR])
        warning_count = len([e for e in self._log_entries if e.level == LogLevel.WARNING])
        
        # Success rate
        total_ops = len(self._component_logs)
        successful_ops = len([c for c in self._component_logs if c.success])
        success_rate = (successful_ops / total_ops * 100) if total_ops > 0 else 100
        
        export_data = {
            "session_info": self.session_info.model_dump(),
            "summary": {
                "total_duration": total_duration,
                "components_used": [comp.value for comp in components_used],
                "api_usage": api_summary,
                "error_count": error_count,
                "warning_count": warning_count,
                "success_rate": success_rate
            },
            "log_entries": [entry.model_dump() for entry in self._log_entries],
            "api_calls": [call.model_dump() for call in self._api_calls],
            "component_logs": [log.model_dump() for log in self._component_logs],
            "progress_entries": [entry.model_dump() for entry in self._progress_entries]
        }
        
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        self.info(f"Session data exported to {export_path}", ComponentType.MAIN_PIPELINE)
        return export_path
    
    def close(self):
        """Close the logger and cleanup resources"""
        # Complete any active progress bars
        for progress_id in list(self._active_progress.keys()):
            self.complete_progress(progress_id)
        
        # Display session summary
        self.display_session_summary()
        
        # Export session data
        self.export_session_data()
        
        # Log final message before closing files
        self.info("Pipeline logger closed", ComponentType.MAIN_PIPELINE)
        
        # Close file handles
        for file_handle in self._log_files.values():
            file_handle.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Global logger instance
_global_logger: Optional[PipelineLogger] = None


def get_logger() -> Optional[PipelineLogger]:
    """Get the global logger instance"""
    return _global_logger


def initialize_logger(config: Optional[Config] = None, session_id: Optional[str] = None) -> PipelineLogger:
    """Initialize the global logger"""
    global _global_logger
    _global_logger = PipelineLogger(config, session_id)
    return _global_logger


def close_logger():
    """Close the global logger"""
    global _global_logger
    if _global_logger:
        _global_logger.close()
        _global_logger = None