# Comprehensive Logging System for CLI and File Output

## Overview
Implement an extensive logging system that provides detailed visibility into pipeline execution, with output to both CLI (with rich formatting) and structured log files for debugging and monitoring.

## Problem Statement
Currently, the pipeline provides minimal logging:
- Only basic console output with Rich
- No persistent logs for debugging failures
- No detailed API call tracking
- No performance metrics logging
- Difficult to diagnose issues after execution

## Proposed Solution

### 1. Logging Architecture
```python
import logging
from rich.logging import RichHandler
from pathlib import Path
import json
from datetime import datetime

class PipelineLogger:
    def __init__(self, 
                 name: str,
                 log_dir: str = "logs",
                 console_level: str = "INFO",
                 file_level: str = "DEBUG"):
        
        # Create log directory
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create session directory
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.log_dir / self.session_id
        self.session_dir.mkdir(exist_ok=True)
        
        # Setup loggers
        self.logger = logging.getLogger(name)
        self.api_logger = logging.getLogger(f"{name}.api")
        self.perf_logger = logging.getLogger(f"{name}.performance")
        
        # Console handler with Rich
        console_handler = RichHandler(
            rich_tracebacks=True,
            tracebacks_show_locals=True
        )
        console_handler.setLevel(console_level)
        
        # File handlers
        self.setup_file_handlers()
```

### 2. Log File Structure
```
logs/
└── 20240802_143022/                    # Session timestamp
    ├── pipeline.log                     # Main execution log
    ├── api_calls.jsonl                  # Structured API call logs
    ├── performance.jsonl                # Performance metrics
    ├── errors.log                       # Error-only log
    └── components/                      # Component-specific logs
        ├── research_analyzer.log
        ├── jobs_researcher.log
        ├── cluster_jtbd.log
        ├── value_curve_mapper.log
        ├── product_generator.log
        └── idea_consolidator.log
```

### 3. Logging Levels and Categories

#### Main Pipeline Log Format
```
2024-08-02 14:30:22.123 | INFO     | pipeline.main | Starting pipeline execution
2024-08-02 14:30:22.124 | DEBUG    | pipeline.main | Configuration: {'model': 'claude-3-opus', 'max_tokens': 2000}
2024-08-02 14:30:22.125 | INFO     | research_analyzer | Loading research document from S3
2024-08-02 14:30:23.456 | DEBUG    | research_analyzer | S3 bucket: my-bucket, key: research.json
2024-08-02 14:30:24.789 | INFO     | research_analyzer | Document loaded successfully (size: 15.2 KB)
2024-08-02 14:30:24.790 | INFO     | research_analyzer | Starting parallel analysis with 4 tasks
```

#### API Call Log Format (JSONL)
```json
{"timestamp": "2024-08-02T14:30:25.123Z", "component": "research_analyzer", "api": "anthropic", "model": "claude-3-5-sonnet", "request_id": "req_123", "tokens_in": 1523, "tokens_out": 487, "duration_ms": 1234, "cost": 0.0234, "status": "success"}
{"timestamp": "2024-08-02T14:30:26.456Z", "component": "research_analyzer", "api": "anthropic", "model": "claude-3-opus", "request_id": "req_124", "tokens_in": 1523, "tokens_out": 623, "duration_ms": 1567, "cost": 0.0567, "status": "success"}
```

#### Performance Log Format (JSONL)
```json
{"timestamp": "2024-08-02T14:30:30.123Z", "component": "research_analyzer", "operation": "parallel_analysis", "duration_ms": 5234, "memory_mb": 156, "cpu_percent": 23.4}
{"timestamp": "2024-08-02T14:30:35.456Z", "component": "jobs_researcher", "operation": "exa_search", "query_count": 5, "results_count": 47, "duration_ms": 3456}
```

### 4. Component Integration
```python
# In each component
class ResearchAnalyzer:
    def __init__(self):
        self.logger = PipelineLogger.get_component_logger("research_analyzer")
        self.api_tracker = APICallTracker(self.logger)
        
    def analyze_with_llm(self, task, content):
        self.logger.info(f"Starting analysis: {task.name}")
        self.logger.debug(f"Task details: {task}")
        
        # Track API call
        with self.api_tracker.track_call("anthropic", task.model) as tracker:
            try:
                response = self.client.messages.create(...)
                tracker.set_tokens(
                    tokens_in=response.usage.input_tokens,
                    tokens_out=response.usage.output_tokens
                )
                self.logger.info(f"Analysis complete: {task.name}")
                return response
                
            except Exception as e:
                self.logger.error(f"Analysis failed: {task.name}", exc_info=True)
                tracker.set_error(str(e))
                raise
```

### 5. CLI Output with Rich Formatting
```python
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel

class RichPipelineLogger:
    def __init__(self):
        self.console = Console()
        self.status_table = Table(title="Pipeline Status")
        
    def log_component_start(self, component: str, details: dict):
        self.console.print(Panel(
            f"[bold cyan]{component}[/bold cyan]\n" +
            "\n".join(f"[dim]{k}:[/dim] {v}" for k, v in details.items()),
            border_style="cyan"
        ))
        
    def log_api_call(self, api: str, model: str, tokens: int, duration: float):
        self.console.print(
            f"[yellow]API Call:[/yellow] {api} • "
            f"[blue]Model:[/blue] {model} • "
            f"[green]Tokens:[/green] {tokens} • "
            f"[magenta]Duration:[/magenta] {duration:.2f}s"
        )
```

### 6. Log Analysis Tools
```python
# CLI tool for analyzing logs
class LogAnalyzer:
    def analyze_session(self, session_id: str):
        """Analyze a pipeline session"""
        session_dir = Path("logs") / session_id
        
        # Parse API calls
        api_calls = self.parse_jsonl(session_dir / "api_calls.jsonl")
        
        # Generate summary
        summary = {
            "total_api_calls": len(api_calls),
            "total_tokens": sum(c["tokens_in"] + c["tokens_out"] for c in api_calls),
            "total_cost": sum(c["cost"] for c in api_calls),
            "total_duration": sum(c["duration_ms"] for c in api_calls) / 1000,
            "by_model": self.group_by_model(api_calls),
            "by_component": self.group_by_component(api_calls),
            "errors": self.count_errors(api_calls)
        }
        
        return summary

# Usage
python analyze_logs.py --session 20240802_143022
python analyze_logs.py --tail -f  # Follow current session
python analyze_logs.py --errors-only --last 5  # Show errors from last 5 sessions
```

### 7. Log Rotation and Management
```python
class LogRotator:
    def __init__(self, max_sessions: int = 100, max_size_gb: float = 10.0):
        self.max_sessions = max_sessions
        self.max_size_gb = max_size_gb
        
    def cleanup_old_logs(self):
        """Remove old log sessions based on count and size"""
        log_dir = Path("logs")
        sessions = sorted(log_dir.iterdir(), key=lambda p: p.stat().st_mtime)
        
        # Remove oldest sessions if over limit
        while len(sessions) > self.max_sessions:
            oldest = sessions.pop(0)
            shutil.rmtree(oldest)
            
        # Check total size
        total_size = sum(f.stat().st_size for f in log_dir.rglob("*") if f.is_file())
        if total_size > self.max_size_gb * 1024**3:
            # Remove oldest until under size limit
            ...
```

### 8. Structured Logging for Different Stages
```python
# Stage-specific logging
class StageLogger:
    @contextmanager
    def log_stage(self, stage_name: str, details: dict = None):
        """Log stage start, duration, and completion"""
        self.logger.info(f"Starting stage: {stage_name}")
        if details:
            self.logger.debug(f"Stage details: {json.dumps(details)}")
            
        start_time = time.time()
        try:
            yield
            duration = time.time() - start_time
            self.logger.info(f"Completed stage: {stage_name} (duration: {duration:.2f}s)")
            self.perf_logger.info({
                "stage": stage_name,
                "duration": duration,
                "status": "success"
            })
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Failed stage: {stage_name} (duration: {duration:.2f}s)")
            self.perf_logger.error({
                "stage": stage_name,
                "duration": duration,
                "status": "error",
                "error": str(e)
            })
            raise
```

### 9. Configuration
```yaml
# logging_config.yaml
logging:
  version: 1
  disable_existing_loggers: false
  
  formatters:
    detailed:
      format: '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
      datefmt: '%Y-%m-%d %H:%M:%S.%f'
    
    simple:
      format: '%(levelname)s | %(message)s'
  
  handlers:
    console:
      class: rich.logging.RichHandler
      level: INFO
      formatter: simple
      rich_tracebacks: true
    
    file:
      class: logging.handlers.RotatingFileHandler
      level: DEBUG
      formatter: detailed
      filename: logs/pipeline.log
      maxBytes: 104857600  # 100MB
      backupCount: 10
  
  loggers:
    pipeline:
      level: DEBUG
      handlers: [console, file]
    
    pipeline.api:
      level: DEBUG
      handlers: [api_file]
```

## Benefits

1. **Debugging**: Complete execution history for troubleshooting
2. **Monitoring**: Track performance and costs over time
3. **Compliance**: Audit trail of all API interactions
4. **Optimization**: Identify bottlenecks and inefficiencies
5. **Development**: Better visibility during development
6. **Support**: Detailed logs for investigating user issues

## Implementation Steps

1. Create `PipelineLogger` base class
2. Integrate logging into each component
3. Add API call tracking
4. Implement performance monitoring
5. Create log analysis CLI tools
6. Add log rotation and cleanup
7. Update documentation
8. Add example log configurations

## Success Criteria

- [ ] All components log to both console and files
- [ ] API calls tracked with tokens and costs
- [ ] Performance metrics captured
- [ ] Logs are structured and parseable
- [ ] Log analysis tools available
- [ ] Log rotation prevents disk issues
- [ ] Clear documentation for log interpretation

## Related Issues
- Issue #1: Integration testing will use logging system
- Issue #3: DEBUG mode will increase logging verbosity