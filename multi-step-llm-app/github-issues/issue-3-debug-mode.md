# DEBUG Mode with Cost-Effective Model Switching and Verbose Logging

## Overview
Implement a DEBUG mode that automatically switches all LLM calls to Claude Sonnet (cheaper model) and enables verbose logging, allowing developers to test the full pipeline flow without incurring high costs from Opus/GPT-4o/o1 models.

## Problem Statement
Testing the full pipeline is expensive because:
- Claude Opus costs ~5x more than Sonnet
- OpenAI o1 is significantly more expensive than GPT-4
- Running multiple iterations during development adds up quickly
- No way to test the complete flow with cheaper alternatives
- Difficult to see detailed execution flow without modifying code

## Proposed Solution

### 1. Environment-Based Debug Mode
```bash
# Run with debug mode
DEBUG=true python research_analyzer.py

# Run integration tests (auto-enables debug)
python test_integration.py --component research-analyzer

# Run full pipeline in debug
DEBUG=true ./run_pipeline.sh

# Disable specific debug features
DEBUG=true DEBUG_USE_SONNET=false python main.py  # Keep original models
DEBUG=true DEBUG_VERBOSE=false python main.py     # Less logging
```

### 2. Model Switching Configuration
```python
class DebugConfig:
    """Configuration for debug mode"""
    
    # Model mappings for debug mode
    MODEL_MAPPINGS = {
        # Anthropic models
        "claude-3-opus-20240229": "claude-3-5-sonnet-20241022",
        "claude-3-opus": "claude-3-5-sonnet-20241022",
        
        # OpenAI models
        "o1-preview": "gpt-4o-mini",
        "o1": "gpt-4o-mini",
        "gpt-4o": "gpt-4o-mini",
        "gpt-4": "gpt-3.5-turbo",
        
        # Already cheap models stay the same
        "claude-3-5-sonnet-20241022": "claude-3-5-sonnet-20241022",
        "gpt-4o-mini": "gpt-4o-mini",
        "gpt-3.5-turbo": "gpt-3.5-turbo"
    }
    
    # Token limits in debug mode (prevent runaway costs)
    DEBUG_TOKEN_LIMITS = {
        "default": 1000,
        "analysis": 500,
        "generation": 800,
        "consolidation": 1200
    }
    
    @classmethod
    def get_debug_model(cls, original_model: str) -> str:
        """Get debug model replacement"""
        if not os.getenv("DEBUG", "").lower() == "true":
            return original_model
            
        if os.getenv("DEBUG_USE_SONNET", "true").lower() == "false":
            return original_model
            
        return cls.MODEL_MAPPINGS.get(original_model, original_model)
```

### 3. Component Integration
```python
# Base class for all components
class DebugAwareComponent:
    def __init__(self):
        self.debug_mode = os.getenv("DEBUG", "").lower() == "true"
        self.logger = self.setup_logging()
        
    def setup_logging(self):
        """Setup logging based on debug mode"""
        level = logging.DEBUG if self.debug_mode else logging.INFO
        
        if self.debug_mode:
            # Add extra handlers for debug mode
            logger.addHandler(self.create_detailed_file_handler())
            logger.addHandler(self.create_api_trace_handler())
            
        return logger
        
    def get_model(self, requested_model: str) -> str:
        """Get model to use (may be replaced in debug mode)"""
        actual_model = DebugConfig.get_debug_model(requested_model)
        
        if actual_model != requested_model:
            self.logger.warning(
                f"DEBUG MODE: Using {actual_model} instead of {requested_model}"
            )
            
        return actual_model
        
    def get_max_tokens(self, requested_tokens: int, operation: str = "default") -> int:
        """Get max tokens (may be limited in debug mode)"""
        if not self.debug_mode:
            return requested_tokens
            
        limit = DebugConfig.DEBUG_TOKEN_LIMITS.get(operation, 1000)
        actual_tokens = min(requested_tokens, limit)
        
        if actual_tokens != requested_tokens:
            self.logger.warning(
                f"DEBUG MODE: Limiting tokens from {requested_tokens} to {actual_tokens}"
            )
            
        return actual_tokens
```

### 4. Verbose Logging in Debug Mode
```python
class DebugLogger:
    """Enhanced logging for debug mode"""
    
    def __init__(self, component_name: str):
        self.component = component_name
        self.debug_mode = os.getenv("DEBUG", "").lower() == "true"
        self.verbose = os.getenv("DEBUG_VERBOSE", "true").lower() == "true"
        
    def log_api_request(self, api: str, model: str, prompt: str, params: dict):
        """Log detailed API request in debug mode"""
        if not self.debug_mode or not self.verbose:
            return
            
        self.logger.debug("="*80)
        self.logger.debug(f"API REQUEST - {api}")
        self.logger.debug(f"Model: {model}")
        self.logger.debug(f"Parameters: {json.dumps(params, indent=2)}")
        self.logger.debug(f"Prompt Preview (first 500 chars):")
        self.logger.debug(prompt[:500] + "..." if len(prompt) > 500 else prompt)
        self.logger.debug("="*80)
        
    def log_api_response(self, api: str, response: Any, duration: float):
        """Log detailed API response in debug mode"""
        if not self.debug_mode or not self.verbose:
            return
            
        self.logger.debug("="*80)
        self.logger.debug(f"API RESPONSE - {api}")
        self.logger.debug(f"Duration: {duration:.2f}s")
        self.logger.debug(f"Response Preview (first 500 chars):")
        response_text = str(response)[:500]
        self.logger.debug(response_text + "..." if len(str(response)) > 500 else response_text)
        self.logger.debug("="*80)
```

### 5. Cost Tracking in Debug Mode
```python
class DebugCostTracker:
    """Track and display cost savings in debug mode"""
    
    COSTS_PER_1K_TOKENS = {
        # Actual costs
        "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
        "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
        "o1-preview": {"input": 0.015, "output": 0.060},
        "gpt-4o": {"input": 0.0025, "output": 0.010},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    }
    
    def __init__(self):
        self.actual_costs = 0.0
        self.debug_costs = 0.0
        self.calls = []
        
    def track_call(self, original_model: str, debug_model: str, 
                   tokens_in: int, tokens_out: int):
        """Track cost difference"""
        original_cost = self.calculate_cost(original_model, tokens_in, tokens_out)
        debug_cost = self.calculate_cost(debug_model, tokens_in, tokens_out)
        
        self.actual_costs += original_cost
        self.debug_costs += debug_cost
        
        self.calls.append({
            "original_model": original_model,
            "debug_model": debug_model,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "saved": original_cost - debug_cost
        })
        
    def print_summary(self):
        """Print cost savings summary"""
        console = Console()
        
        table = Table(title="Debug Mode Cost Savings")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Calls", str(len(self.calls)))
        table.add_row("Would Have Cost", f"${self.actual_costs:.4f}")
        table.add_row("Debug Mode Cost", f"${self.debug_costs:.4f}")
        table.add_row("Total Saved", f"${self.actual_costs - self.debug_costs:.4f}")
        table.add_row("Savings Percentage", f"{((self.actual_costs - self.debug_costs) / self.actual_costs * 100):.1f}%")
        
        console.print(table)
```

### 6. Debug Mode Dashboard
```python
class DebugDashboard:
    """Real-time dashboard for debug mode execution"""
    
    def __init__(self):
        self.console = Console()
        self.layout = self.create_layout()
        
    def create_layout(self):
        """Create rich layout for debug info"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=10)
        )
        
        layout["main"].split_row(
            Layout(name="pipeline", ratio=2),
            Layout(name="stats")
        )
        
        return layout
        
    def update(self, stage: str, api_calls: int, tokens: int, cost_saved: float):
        """Update dashboard with current status"""
        # Header
        self.layout["header"].update(
            Panel("[bold yellow]DEBUG MODE ACTIVE[/bold yellow] - Using Sonnet models")
        )
        
        # Pipeline progress
        self.layout["pipeline"].update(
            Panel(f"Current Stage: [cyan]{stage}[/cyan]")
        )
        
        # Stats
        stats_table = Table()
        stats_table.add_column("Metric")
        stats_table.add_column("Value")
        stats_table.add_row("API Calls", str(api_calls))
        stats_table.add_row("Total Tokens", f"{tokens:,}")
        stats_table.add_row("Cost Saved", f"${cost_saved:.2f}")
        
        self.layout["stats"].update(Panel(stats_table, title="Debug Stats"))
```

### 7. Integration Test Auto-Debug
```python
# In test_integration.py
class IntegrationTestRunner:
    def __init__(self):
        # Auto-enable debug mode for integration tests
        os.environ["DEBUG"] = "true"
        os.environ["DEBUG_LOG_LEVEL"] = "DEBUG"
        
        # But allow override
        if os.getenv("INTEGRATION_TEST_PRODUCTION_MODELS", "false").lower() == "true":
            os.environ["DEBUG_USE_SONNET"] = "false"
```

### 8. Debug Configuration File
```yaml
# debug_config.yaml
debug:
  # Model replacements
  model_mappings:
    expensive_models:
      - claude-3-opus
      - o1-preview
      - gpt-4o
    replacement: claude-3-5-sonnet-20241022
  
  # Token limits by operation
  token_limits:
    research_analysis: 500
    idea_generation: 800
    viability_assessment: 600
    consolidation: 1000
  
  # Logging configuration
  logging:
    level: DEBUG
    include_prompts: true
    include_responses: true
    truncate_at: 500
  
  # Performance limits
  performance:
    max_parallel_calls: 2  # Reduce parallelism in debug
    api_call_delay_ms: 100  # Add delay between calls
    timeout_seconds: 30  # Shorter timeouts
  
  # Features to disable in debug
  disable:
    - image_analysis
    - web_scraping_depth_3
    - advanced_clustering
```

### 9. CLI Integration
```bash
# Debug mode commands
python main.py --debug  # Enable debug mode
python main.py --debug --verbose  # Extra verbose logging
python main.py --debug --no-model-switch  # Debug logging but keep expensive models
python main.py --debug --max-cost 5.00  # Stop if debug cost exceeds $5

# Show debug configuration
python main.py --show-debug-config

# Analyze debug logs
python analyze_debug.py --session last --show-savings
```

## Benefits

1. **Cost Savings**: 80-90% reduction in API costs during development
2. **Faster Development**: Test full pipeline without cost concerns
3. **Better Debugging**: Verbose logging shows complete execution flow
4. **Integration Testing**: Automatic debug mode for tests
5. **Transparency**: Clear indication when debug mode is active
6. **Flexibility**: Granular control over debug features

## Implementation Steps

1. Create `DebugConfig` class with model mappings
2. Implement `DebugAwareComponent` base class
3. Update all components to inherit from base class
4. Add verbose logging methods
5. Create cost tracking system
6. Build debug dashboard
7. Update integration tests
8. Add documentation
9. Create debug analysis tools

## Success Criteria

- [ ] DEBUG=true switches all models to Sonnet/cheaper alternatives
- [ ] Verbose logging shows all API calls and responses
- [ ] Cost savings displayed at end of execution
- [ ] Integration tests automatically use debug mode
- [ ] Clear visual indication when debug mode is active
- [ ] Token limits prevent runaway costs
- [ ] Debug logs are comprehensive but organized

## Related Issues
- Issue #1: Integration tests will auto-enable debug mode
- Issue #2: Logging system will respect debug verbosity settings