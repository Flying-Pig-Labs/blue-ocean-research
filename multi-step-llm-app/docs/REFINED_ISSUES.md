# Refined GitHub Issues for Multi-Step LLM App

## Issue #6: Cost & Time Estimations

### 📊 Overview
Implement comprehensive cost and time tracking for each pipeline step, providing pre-execution estimates and post-execution actuals to help users understand and optimize their pipeline usage.

### 🎯 Objectives
- Track estimated cost and time for each CLI step before execution
- Optionally display actual costs and times after execution
- Provide dry-run mode for cost estimation without execution
- Enable cost-aware decision making for pipeline runs

### 🔧 Implementation Details

#### Core Components

1. **Cost Estimation Module** (`src/cost_estimation/cost_estimator.py`)
```python
class CostEstimator:
    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost based on model and token counts"""
        pricing = {
            'claude-3-5-sonnet-20241022': {'input': 0.003, 'output': 0.015},
            'claude-3-opus-20240229': {'input': 0.015, 'output': 0.075},
            'gpt-4o': {'input': 0.005, 'output': 0.015},
            'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},
            'exa': {'per_search': 0.01}
        }
        # Implementation here
```

2. **Time Estimation Module** (`src/cost_estimation/time_estimator.py`)
```python
class TimeEstimator:
    def estimate_time(self, model: str, tokens: int, operation: str) -> float:
        """Estimate execution time in seconds"""
        base_times = {
            'claude': 2.0,  # base latency
            'gpt': 1.5,
            'exa': 3.0
        }
        # Time = base + (tokens/1000 * processing_rate)
```

3. **Pre-Run Summary Display**
```
┌─────────────────────────────────────────────┐
│ Step: Extract Personas                      │
│ Model: Claude 3.5 Sonnet                    │
│ Input Tokens: ~4,000                        │
│ Estimated Cost: $0.012                      │
│ Estimated Time: 6.5 seconds                 │
│ Confidence: 85%                             │
└─────────────────────────────────────────────┘
```

#### CLI Integration

```bash
# Show cost estimates before running
python main.py --show-costs

# Track actual costs during execution
python main.py --track-costs

# Dry run mode - estimates only, no execution
python main.py --dry-run

# Export cost metrics
python main.py --export-costs costs_report.json
```

#### Metrics Storage
```json
{
  "session_id": "2025-01-20_14-30-45",
  "estimates": {
    "total_cost": 0.125,
    "total_time": 45.2,
    "by_step": {...}
  },
  "actuals": {
    "total_cost": 0.118,
    "total_time": 42.7,
    "by_step": {...}
  },
  "accuracy": {
    "cost_accuracy": 94.4,
    "time_accuracy": 94.2
  }
}
```

### 🤔 Implementation Questions

1. **How should we handle cost estimation for components that make multiple API calls (e.g., jobs_researcher with EXA searches)?**
   - Should we aggregate all sub-calls or show breakdowns?
   - How do we estimate the number of searches EXA will perform?

2. **What's the best way to estimate token counts before making API calls?**
   - Use tiktoken for accurate OpenAI token counting?
   - Implement character-based approximation for Claude models?
   - How to handle dynamic prompts with variable content?

3. **How should we present cost/time information in different output modes?**
   - Rich tables for terminal output?
   - JSON format for programmatic access?
   - HTML reports for detailed analysis?

4. **Should cost tracking integrate with the existing logging system (Issue #2)?**
   - Store costs in the same session logs?
   - Create separate cost tracking logs?
   - How to correlate costs with debug mode savings?

5. **How do we handle cost estimation for parallel operations?**
   - Show total wall-clock time vs cumulative API time?
   - How to estimate parallelization efficiency?

6. **What level of granularity should we provide for cost breakdowns?**
   - Per-component, per-API-call, or per-operation?
   - Should we track retry costs separately?

7. **How should we implement the confidence level for estimates?**
   - Base on historical accuracy data?
   - Factor in prompt complexity and variability?

8. **Should we implement cost alerts or thresholds?**
   - Warn before expensive operations?
   - Allow setting max cost per session?

9. **How do we handle cost tracking for streaming responses?**
   - Update estimates in real-time?
   - Show running totals during execution?

10. **What additional metrics should we track beyond cost and time?**
    - API call success rates?
    - Token efficiency (output/input ratio)?
    - Cost per successful outcome?

---

## Issue #7: Rerun Specific Step

### 🔄 Overview
Enable users to rerun individual pipeline steps without executing the entire pipeline, leveraging cached intermediate results for efficiency and experimentation.

### 🎯 Objectives
- Support rerunning any pipeline step independently
- Implement robust state caching for all intermediate outputs
- Enable iterative refinement of specific steps
- Maintain full pipeline reproducibility

### 🔧 Implementation Details

#### Core Components

1. **Step Registry** (`src/pipeline/step_registry.py`)
```python
class StepRegistry:
    STEPS = {
        'research_analysis': {
            'function': run_research_analysis,
            'inputs': ['research_doc'],
            'outputs': ['analysis_results.md'],
            'dependencies': []
        },
        'jobs_research': {
            'function': run_jobs_research,
            'inputs': ['analysis_results.md'],
            'outputs': ['jtbd_research.md', 'pain_points.txt'],
            'dependencies': ['research_analysis']
        },
        # ... more steps
    }
```

2. **State Management** (`src/pipeline/state_manager.py`)
```python
class StateManager:
    def save_step_output(self, step_name: str, output: Any, run_id: str = 'default'):
        """Save step output with versioning"""
        
    def load_step_input(self, step_name: str, fresh: bool = False):
        """Load input for a step from cache or regenerate"""
        
    def get_step_metadata(self, step_name: str):
        """Get execution history and metadata"""
```

3. **File Structure**
```
output/
├── runs/
│   ├── default/
│   │   ├── step_01_research_analysis.json
│   │   ├── step_01_research_analysis.metadata.json
│   │   ├── step_02_jobs_research.json
│   │   └── ...
│   └── experiment_1/
│       └── ...
├── cache/
│   └── intermediate/
└── manifests/
    └── run_manifest.json
```

#### CLI Interface

```bash
# List all available steps
python main.py --list-steps

# Rerun specific step using cached inputs
python main.py --rerun jobs_research

# Rerun with fresh inputs (regenerate dependencies)
python main.py --rerun jobs_research --fresh

# Rerun with specific run ID
python main.py --rerun jobs_research --run-id experiment_1

# Interactive rerun with confirmations
python main.py --rerun jobs_research --interactive

# Compare outputs between runs
python main.py --diff jobs_research --run1 default --run2 experiment_1
```

#### Metadata Tracking
```json
{
  "step_name": "jobs_research",
  "run_id": "default",
  "execution_time": "2025-01-20T14:30:45Z",
  "duration_seconds": 12.4,
  "input_hash": "a3f5e8b9...",
  "output_hash": "7d2c9f1a...",
  "model_used": "claude-3-5-sonnet-20241022",
  "cost": 0.023,
  "status": "success",
  "error": null
}
```

### 🤔 Implementation Questions

1. **How should we handle cascading dependencies when rerunning a step?**
   - Automatically invalidate downstream steps?
   - Prompt user to rerun dependent steps?
   - Mark dependent outputs as "stale"?

2. **What's the best strategy for cache invalidation?**
   - Time-based expiration?
   - Content hash comparison?
   - Manual cache clearing?

3. **How do we ensure reproducibility when models or prompts change?**
   - Version prompts alongside outputs?
   - Track model versions used?
   - Store complete execution context?

4. **Should we implement step versioning for A/B testing?**
   - Allow multiple versions of the same step?
   - Compare outputs across versions?
   - How to manage version proliferation?

5. **How do we handle partial failures in multi-output steps?**
   - Save partial outputs?
   - Allow resuming from failure point?
   - Rollback mechanisms?

6. **What's the best way to visualize the pipeline state?**
   - ASCII flow diagram showing cached/fresh steps?
   - Web UI for pipeline visualization?
   - Status indicators in CLI?

7. **How should we implement the --fresh flag logic?**
   - Regenerate just immediate dependencies?
   - Full upstream regeneration?
   - Selective dependency refresh?

8. **Should we support conditional step execution?**
   - Skip steps based on previous outputs?
   - Dynamic pipeline paths?
   - How to track conditional flows?

9. **How do we handle large intermediate files efficiently?**
   - Compress cached outputs?
   - Implement size limits?
   - External storage options?

10. **What additional rerun features would be valuable?**
    - Batch rerun of multiple steps?
    - Scheduled reruns?
    - Rerun with parameter sweeps?

---

## Issue #8: Detour Mode (Deeper Analysis Substitution)

### 🚂 Overview
Enable dynamic substitution of standard LLM calls with deeper research detours using specialized engines (EXA, O1, Perplexity) for richer contextual analysis.

### 🎯 Objectives
- Allow flexible replacement of any pipeline step with research-enhanced versions
- Support multiple research engines with different capabilities
- Maintain output compatibility while enriching content quality
- Enable exploratory analysis without modifying core pipeline

### 🔧 Implementation Details

#### Core Components

1. **Detour Engine Registry** (`src/detour/engine_registry.py`)
```python
class DetourEngine:
    """Base class for detour engines"""
    
    def research(self, query: str, context: Dict) -> ResearchResult:
        """Perform deep research on the query"""
        pass
        
    def synthesize(self, research_result: ResearchResult) -> str:
        """Synthesize research into usable output"""
        pass

class EXAEngine(DetourEngine):
    """Real-time Reddit, forums, interviews"""
    
class O1Engine(DetourEngine):
    """Fact-checked narrative analysis"""
    
class PerplexityEngine(DetourEngine):
    """Conversational research queries"""
```

2. **Detour Orchestrator** (`src/detour/orchestrator.py`)
```python
class DetourOrchestrator:
    def execute_detour(self, 
                      step_name: str, 
                      engine: str, 
                      input_data: Dict,
                      config: DetourConfig) -> Dict:
        """Execute a detour for a specific step"""
        
        # 1. Generate research queries
        queries = self.generate_queries(step_name, input_data)
        
        # 2. Execute research
        research_results = engine.research(queries, context)
        
        # 3. Synthesize results
        synthesized = engine.synthesize(research_results)
        
        # 4. Format for pipeline compatibility
        return self.format_output(step_name, synthesized)
```

3. **Detour Configuration** (`detour_config.yaml`)
```yaml
detour_profiles:
  deep_research:
    pain_points:
      engine: exa
      search_depth: 100
      sources: ["reddit", "hackernews", "twitter"]
      synthesis_model: claude-3-opus-20240229
    
  fact_checked:
    all_steps:
      engine: o1
      verification_level: high
      cross_reference: true
    
  exploratory:
    jobs_research:
      engine: perplexity
      query_style: conversational
      follow_up_depth: 3

engine_settings:
  exa:
    api_key: ${EXA_API_KEY}
    rate_limit: 10
    timeout: 30
    
  o1:
    model: o1-preview
    temperature: 0.2
    
  perplexity:
    model: pplx-70b-online
    search_recency: "week"
```

#### CLI Interface

```bash
# Single step detour
python main.py --detour pain_points:exa

# Multiple step detours
python main.py --detour pain_points:exa --detour jobs_research:perplexity

# Use detour profile
python main.py --detour-profile deep_research

# All steps with same engine
python main.py --detour-all o1

# Interactive detour selection
python main.py --detour-interactive

# Compare standard vs detour outputs
python main.py --detour pain_points:exa --compare-outputs
```

#### Output Structure
```
output/
├── standard/
│   └── step_03_pain_points.json
├── detours/
│   ├── step_03_pain_points.exa.research.json
│   ├── step_03_pain_points.exa.synthesized.json
│   └── step_03_pain_points.exa.metadata.json
└── comparisons/
    └── step_03_pain_points.comparison.html
```

### 🤔 Implementation Questions

1. **How should we handle API rate limits across different detour engines?**
   - Implement per-engine rate limiting?
   - Queue management for bulk detours?
   - Fallback strategies when limits are hit?

2. **What's the best way to maintain output schema compatibility?**
   - Strict schema validation after synthesis?
   - Adapter patterns for each engine?
   - How to handle engine-specific enrichments?

3. **How do we optimize the synthesis prompt for each engine's output format?**
   - Engine-specific synthesis templates?
   - Learning from successful syntheses?
   - Quality scoring mechanisms?

4. **Should detours support chaining (EXA → O1 → Claude)?**
   - How to configure chain sequences?
   - Intermediate result handling?
   - Cost/time implications?

5. **How do we handle detour failures gracefully?**
   - Fallback to standard processing?
   - Partial detour results?
   - Retry strategies?

6. **What metadata should we track for detour operations?**
   - Research sources accessed?
   - Confidence scores?
   - Fact-checking results?

7. **How can we make detour results reproducible?**
   - Cache external API responses?
   - Version detour configurations?
   - Timestamp sensitivity?

8. **Should we implement detour result quality assessment?**
   - Automatic quality scoring?
   - Human-in-the-loop validation?
   - A/B testing frameworks?

9. **How do we handle cost differences between standard and detour modes?**
   - Show cost comparisons upfront?
   - Budget constraints for detours?
   - Cost-benefit analysis?

10. **What advanced detour features should we consider?**
    - Conditional detours based on initial results?
    - Ensemble detours combining multiple engines?
    - Learning optimal detour strategies?

---

## Implementation Priority & Dependencies

### Suggested Implementation Order:
1. **Issue #6 (Cost & Time Estimations)** - Foundational for making informed decisions
2. **Issue #7 (Rerun Specific Step)** - Enables efficient iteration and testing
3. **Issue #8 (Detour Mode)** - Advanced feature building on top of rerun capability

### Cross-Issue Dependencies:
- Cost tracking (Issue #6) should integrate with both rerun (Issue #7) and detour (Issue #8) features
- Rerun infrastructure (Issue #7) provides the caching layer needed for efficient detours (Issue #8)
- All issues should integrate with existing logging (Issue #2) and debug mode (Issue #3) systems

### Shared Components:
- Enhanced step registry with metadata
- Unified state management system
- Common CLI framework extensions
- Integrated reporting and analytics