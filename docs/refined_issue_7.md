# Issue #7: Rerun Specific Step

## 🔄 Overview
Enable users to rerun individual pipeline steps without executing the entire pipeline, leveraging cached intermediate results for efficiency and experimentation.

## 🎯 Objectives
- Support rerunning any pipeline step independently
- Implement robust state caching for all intermediate outputs
- Enable iterative refinement of specific steps
- Maintain full pipeline reproducibility

## 🔧 Implementation Details

### Core Components

#### 1. Step Registry (`src/pipeline/step_registry.py`)
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

#### 2. State Management (`src/pipeline/state_manager.py`)
```python
class StateManager:
    def save_step_output(self, step_name: str, output: Any, run_id: str = 'default'):
        """Save step output with versioning"""
        
    def load_step_input(self, step_name: str, fresh: bool = False):
        """Load input for a step from cache or regenerate"""
        
    def get_step_metadata(self, step_name: str):
        """Get execution history and metadata"""
```

#### 3. File Structure
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

### CLI Interface

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

### Metadata Tracking
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

## 🤔 Implementation Questions

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

## 📁 Additional Features

### Pipeline Visualization
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Research        │ ──> │ Jobs Research   │ ──> │ JTBD Clustering │
│ Analysis        │     │                 │     │                 │
│ ✅ Cached       │     │ 🔄 Rerunning   │     │ ⚠️  Stale       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Diff Output Example
```diff
--- output/runs/default/step_02_jobs_research.json
+++ output/runs/experiment_1/step_02_jobs_research.json
@@ -15,7 +15,7 @@
   "pain_points": [
-    "Manual data entry is time-consuming",
+    "Manual data entry is error-prone and time-consuming",
     "Lack of real-time collaboration tools",
+    "Integration with existing systems is complex"
   ]
```

## Related Issues
- Issue #2: Logging System - Track rerun operations
- Issue #3: Debug Mode - Enable debug for specific reruns
- Issue #4: Integration Testing - Test rerun functionality
- Issue #6: Cost Tracking - Track costs for reruns vs full runs