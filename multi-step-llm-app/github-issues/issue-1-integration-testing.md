# Integration Testing CLI for Individual Component Testing

## Overview
Add a comprehensive integration testing CLI that allows testing each pipeline component individually with real API calls, helping developers verify behavior and debug issues in isolation.

## Problem Statement
Currently, testing the pipeline requires either:
- Running unit tests (which mock API calls)
- Running the entire pipeline end-to-end (expensive and time-consuming)

There's no middle ground for testing individual components with real API calls to verify actual behavior.

## Proposed Solution

### 1. New CLI Command Structure
```bash
# Test individual components
python test_integration.py --component research-analyzer --input sample_research.json
python test_integration.py --component jobs-researcher --input analysis_results.md
python test_integration.py --component cluster-jtbd --input pain_points.txt
python test_integration.py --component value-curve --input opportunity_zones.json
python test_integration.py --component product-generator --input value_curves.json
python test_integration.py --component idea-consolidator --input product_ideas.json

# Test with custom parameters
python test_integration.py --component research-analyzer \
    --input sample_research.json \
    --output test_output/ \
    --model claude-3-5-sonnet-20241022 \
    --max-tokens 500

# List available test scenarios
python test_integration.py --list-scenarios

# Run predefined test scenario
python test_integration.py --scenario basic-research-test
```

### 2. Test Scenarios Configuration
Create `test_scenarios.yaml`:
```yaml
scenarios:
  basic-research-test:
    component: research-analyzer
    input: tests/fixtures/sample_research.json
    expected_outputs:
      - verticals: 3-5
      - personas: 2-4
      - pain_points: 5-10
      - solutions: 3-6
    validation:
      - check_output_exists: analysis_results.md
      - check_json_structure: true
      - min_content_length: 1000

  jobs-search-test:
    component: jobs-researcher
    input: tests/fixtures/sample_analysis.md
    mock_exa: true  # Use mock EXA responses for consistent testing
    expected_outputs:
      - jobs_found: 10-20
      - pain_points_extracted: 15-30
    validation:
      - check_jtbd_format: true
      - check_pain_points_file: true
```

### 3. Component Test Harness
```python
class IntegrationTestRunner:
    def __init__(self, component: str, debug: bool = False):
        self.component = component
        self.debug = debug
        self.logger = self.setup_logging()
        
    def run_test(self, input_file: str, **kwargs):
        """Run integration test for a single component"""
        # Load component
        component_class = self.load_component(self.component)
        
        # Initialize with test parameters
        instance = component_class(**kwargs)
        
        # Run with timing and monitoring
        start_time = time.time()
        try:
            result = instance.run(input_file)
            duration = time.time() - start_time
            
            # Validate results
            validation_report = self.validate_results(result)
            
            # Generate test report
            self.generate_report({
                'component': self.component,
                'duration': duration,
                'api_calls': self.count_api_calls(),
                'tokens_used': self.count_tokens(),
                'validation': validation_report
            })
            
        except Exception as e:
            self.logger.error(f"Test failed: {e}")
            self.generate_error_report(e)
```

### 4. Test Data Management
```
tests/
├── fixtures/
│   ├── sample_research.json      # Minimal research doc
│   ├── sample_analysis.md        # Pre-generated analysis
│   ├── sample_pain_points.txt    # List of pain points
│   ├── sample_zones.json         # Opportunity zones
│   └── sample_curves.json        # Value curves
├── expected/
│   ├── research_output.json      # Expected structure
│   ├── jobs_output.json          # Expected JTBD format
│   └── ...
└── results/
    └── [timestamp]/              # Test run results
        ├── output/               # Component outputs
        ├── logs/                 # Detailed logs
        └── report.html           # Test report
```

### 5. Interactive Test Mode
```python
# Interactive testing with step-by-step execution
python test_integration.py --component research-analyzer --interactive

> Loading component: research-analyzer
> Input file: sample_research.json
> 
> Step 1: Industry Verticals Analysis
> Model: claude-3-5-sonnet-20241022
> Tokens: 423/500
> [Show response? (y/n)]: y
> [Continue to next step? (y/n)]: y
```

### 6. Validation Framework
```python
class ComponentValidator:
    """Validate component outputs against expectations"""
    
    def validate_research_analyzer(self, output):
        checks = {
            'has_all_sections': self.check_sections(output, 
                ['verticals', 'personas', 'pain_points', 'solutions']),
            'verticals_count': 3 <= len(output.get('verticals', [])) <= 10,
            'personas_have_structure': self.check_persona_structure(output),
            'pain_points_categorized': self.check_pain_point_categories(output),
            'solutions_have_complexity': 'complexity' in str(output.get('solutions', ''))
        }
        return ValidationReport(checks)
```

### 7. Performance Monitoring
```python
class PerformanceMonitor:
    """Track API calls, tokens, and timing"""
    
    def __init__(self):
        self.api_calls = []
        self.token_usage = {}
        self.timings = {}
        
    def track_api_call(self, model, tokens_in, tokens_out, duration):
        self.api_calls.append({
            'timestamp': datetime.now(),
            'model': model,
            'tokens_in': tokens_in,
            'tokens_out': tokens_out,
            'duration': duration
        })
        
    def generate_summary(self):
        return {
            'total_api_calls': len(self.api_calls),
            'total_tokens': sum(c['tokens_in'] + c['tokens_out'] for c in self.api_calls),
            'total_duration': sum(c['duration'] for c in self.api_calls),
            'cost_estimate': self.estimate_cost()
        }
```

## Benefits

1. **Faster Development**: Test components without running full pipeline
2. **Cost Savings**: Test with smaller inputs and controlled scenarios
3. **Debugging**: Isolate issues to specific components
4. **Regression Testing**: Ensure changes don't break existing functionality
5. **Performance Tracking**: Monitor API usage and optimize
6. **Documentation**: Test scenarios serve as usage examples

## Implementation Steps

1. Create `test_integration.py` CLI script
2. Implement component test harness
3. Create test fixtures for each component
4. Build validation framework
5. Add performance monitoring
6. Create test scenarios configuration
7. Generate HTML test reports
8. Add to CI/CD pipeline

## Success Criteria

- [ ] Can test each component individually via CLI
- [ ] Clear pass/fail indicators for each test
- [ ] Performance metrics tracked and reported
- [ ] Test scenarios cover common use cases
- [ ] Interactive mode for debugging
- [ ] Integration with DEBUG mode (see Issue #3)

## Related Issues
- Issue #2: Logging (test results should be logged)
- Issue #3: DEBUG mode (integration tests should respect DEBUG flag)