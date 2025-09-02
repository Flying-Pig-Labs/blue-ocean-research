# Modular Ideation Pipeline System

## Overview

This system modularizes the existing ideation pipeline to support multiple "flavors" while maintaining **100% backward compatibility** with the current baseline behavior.

## 🎯 Key Principle: EXACT Baseline Reproduction

The `baseline` flavor **reproduces the current pipeline behavior exactly**:
- Same prompts (embedded in original modules)
- Same models (`claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`, `gpt-4o`)
- Same parameters (7 zones, 3 discussions per JTBD, exactly 10 ideas)
- Same ERRC framework application
- Same GitHub integration (10 issues, ocean-studio-repos org)
- Same Perplexity AI two-stage enhancement

**Nothing changes functionally** - this is a pure refactor for modularity.

## File Structure

```
blue-ocean-research/
├── run_pipeline.py              # Original pipeline (unchanged)
├── run_pipeline_modular.py      # NEW: Flavor-aware entry point
├── flavors/
│   ├── config_schema.py         # NEW: Configuration system
│   ├── baseline.yaml            # NEW: Exact current behavior
│   └── [future_flavors].yaml    # Future: Other ideation types
└── test_modular_system.py       # NEW: Validation tests
```

## Usage

### Current Users (No Changes Required)
```bash
# Existing usage continues to work
python run_pipeline.py --interactive
python run_pipeline.py --verbose --input custom.json
```

### New Modular Usage
```bash
# Exact same behavior as current pipeline
python run_pipeline_modular.py --flavor baseline --interactive

# List available flavors
python run_pipeline_modular.py --list-flavors

# Future: Other flavors (when implemented)
python run_pipeline_modular.py --flavor site_location --verbose
```

## Baseline Flavor Configuration

The `baseline.yaml` captures the **exact current behavior**:

### Stage Parameters
- **Research Analysis**: `claude-3-5-sonnet-20241022`, temperature=0.7
- **JTBD & Reddit**: Dynamic subreddit discovery + fallback list
- **Opportunity Zones**: 7 zones, max 3 discussions, Perplexity enrichment
- **Idea Generation**: Exactly 10 ideas, weighted distribution, ERRC framework
- **GitHub Integration**: ocean-studio-repos org, exactly 10 issues

### Reddit Strategy (Current Behavior)
```yaml
# Uses EXACT dynamic subreddit discovery as in current jobs_to_reddit.py
subreddit_discovery_prompt: |
  You are a JSON generator specializing in Reddit communities...
  
fallback_subreddits:
  - "RealEstate"
  - "FirstTimeHomeBuyer"
  - "realestateinvesting"
  # ... (exact current fallback list)

search_filters:
  limit: 2          # 2 results per query
  sort: "relevance"
  time_filter: "year"
```

### Framework (Current Behavior)
```yaml
framework:
  framework_type: "errc"  # Blue Ocean Strategy
  analysis_dimensions:    # Exact current pain dimensions
    - "timing_coordination"
    - "financial_stress" 
    - "communication_gaps"
    # ... (all 8 current dimensions)
```

### Models (Current Behavior)
```yaml
default_models:
  research_analysis: "claude-3-5-sonnet-20241022"
  reddit_analysis: "claude-3-5-sonnet-20241022"
  opportunity_zones: "claude-3-5-sonnet-20241022"
  idea_generation: "claude-3-opus-20240229"  # Creative generation
  consolidation: "claude-3-5-sonnet-20241022"
  github_content: "gpt-4o"  # README + issues
```

## Configuration System

### FlavorConfig Schema
- **RedditSearchStrategy**: Subreddit discovery, search parameters
- **FrameworkConfig**: ERRC/JTBD/Custom framework settings  
- **OutputConfig**: Business idea/site candidate/device spec schemas
- **Stage Overrides**: Per-stage parameter customization
- **Model Selection**: AI model choices per pipeline stage

### Validation
All flavors are validated for:
- Required fields presence
- Valid model names
- Consistent parameter ranges
- Framework-specific requirements

## Testing

```bash
# Validate the modular system
python test_modular_system.py

# Expected output:
# ✅ ALL 3 TESTS PASSED!
# 🎯 The modular system is ready for use!
```

Tests verify:
1. **Flavor Loading**: YAML parsing and validation
2. **Baseline Accuracy**: Exact parameter reproduction (12 checks)
3. **Prompt Preservation**: Critical prompts unchanged

## Future Extensibility

The system is designed for easy extension:

### New Flavors
Create `flavors/my_flavor.yaml` with:
- Custom Reddit strategy (different subreddits, search terms)
- Alternative frameworks (JTBD, Lean Canvas, Design Thinking)
- Different output schemas (site candidates, device specs)
- Specialized model choices

### New Frameworks
```yaml
framework:
  framework_type: "custom"
  custom_prompts:
    analysis_prompt: |
      Apply [YOUR FRAMEWORK] to analyze this opportunity...
```

### New Output Types
```yaml
output:
  schema_type: "device_spec"
  required_fields:
    - "hardware_requirements"
    - "sensor_specifications" 
    - "connectivity_options"
```

## Migration Path

1. **Phase 1** (Current): Both entry points work
   - `run_pipeline.py` (original) → unchanged
   - `run_pipeline_modular.py --flavor baseline` → identical output

2. **Phase 2** (Future): Gradual transition
   - New flavors added (`site_location`, `device_design`)
   - Users adopt modular entry point
   - Original entry point remains for compatibility

3. **Phase 3** (Long-term): Full modularization
   - Original pipeline refactored to use flavor system internally
   - Single codebase, multiple flavors
   - Enhanced extensibility

## Backward Compatibility Guarantee

**The baseline flavor will ALWAYS reproduce the current pipeline behavior exactly.**

This ensures:
- Existing users see no changes
- Results remain consistent
- No disruption to workflows
- Confidence in the refactor

## Summary

This modularization:
✅ **Maintains exact current behavior** (baseline flavor)  
✅ **Enables future flexibility** (new flavors)  
✅ **Preserves all existing functionality**  
✅ **Requires no changes from current users**  
✅ **Provides clear migration path** for new features

The system is ready for use with complete confidence that the baseline behavior is preserved exactly.