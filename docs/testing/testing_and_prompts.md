# Testing and Prompts Documentation

## Overview

This document describes the comprehensive testing suite and prompt management system for the Multi-Step LLM Application pipeline.

## Unit Testing

### Test Coverage

We've added comprehensive unit tests for all modules in the pipeline:

| Module | Test File | Number of Tests | Key Test Areas |
|--------|-----------|-----------------|----------------|
| `main.py` | `test_main.py` | 18 | API init, workflow steps, interactive/headless modes |
| `research_analyzer.py` | `test_research_analyzer.py` | 12 | S3 loading, parallel analysis, error handling |
| `jobs_researcher.py` | `test_jobs_researcher.py` | 13 | EXA search, JTBD extraction, pain points |
| `cluster_jtbd.py` | `test_cluster_jtbd.py` | 11 | Embeddings, clustering, zone generation |
| `value_curve_mapper.py` | `test_value_curve_mapper.py` | 13 | Sequential processing, parallel analysis |
| `product_idea_generator.py` | `test_product_idea_generator.py` | 10 | ERRC grid, idea generation, filtering |
| `idea_consolidator.py` | `test_idea_consolidator.py` | 16 | Portfolio creation, scoring, roadmap |
| `prompt_loader.py` | `test_prompt_loader.py` | 13 | Prompt loading, parsing, caching |

**Total Tests**: 106 unit tests

### Running Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html

# Run specific test file
python -m pytest tests/test_main.py -v
```

### Test Features

1. **Mocking**: All external API calls are mocked for reliable testing
2. **Fixtures**: Reusable test data via pytest fixtures
3. **Error Cases**: Tests for rate limits, API errors, missing files
4. **Edge Cases**: Empty data, malformed inputs, boundary conditions
5. **Integration**: Tests verify component interactions

## Prompt Management

### Directory Structure

All prompts are now externalized in the `prompts/` directory:

```
prompts/
├── 0-main-story-ideation.txt              # Demo workflow
├── 1-research-analyzer-verticals.txt      # Industry analysis
├── 1-research-analyzer-personas.txt       # User personas
├── 1-research-analyzer-pain-points.txt    # Pain points
├── 1-research-analyzer-solutions.txt      # Solutions
├── 2-jobs-researcher-jtbd-table.txt       # JTBD synthesis
├── 3-cluster-jtbd-label.txt              # Cluster labeling
├── 3-cluster-jtbd-zones.txt              # Zone generation
├── 4-value-curve-norms.txt               # Industry norms
├── 4-value-curve-engineering.txt         # Engineering spectrum
├── 5-product-generator-errc.txt          # ERRC grid (o1)
├── 5-product-generator-ideas.txt         # Ideas (Opus)
├── 5-product-generator-viability.txt     # Viability (Opus)
└── README.md                              # Prompt documentation
```

### Using the Prompt Loader

```python
from prompt_loader import PromptLoader

# Initialize loader
loader = PromptLoader()

# Load a prompt with variable substitution
prompt = loader.load_prompt("1-research-analyzer-verticals.txt", {
    "research_content": "Your research document here"
})

# Load and parse system/user prompts
system_prompt, user_prompt = loader.load_and_parse(
    "3-cluster-jtbd-label.txt",
    {"sample_texts": "List of pain points"}
)

# List available prompts
prompts = loader.list_prompts()
```

### Modifying Prompts

1. **No Code Changes Required**: Edit the `.txt` file directly
2. **Variables**: Use `{variable_name}` syntax for substitution
3. **Format**: 
   ```
   SYSTEM: [System role]
   
   USER: [User prompt with {variables}]
   ```
4. **Testing**: Run a sample after modification
5. **Version Control**: Commit prompt changes separately

### Integration with Code

To integrate the prompt loader with existing code:

```python
# Before (embedded prompt)
prompt = "Analyze these pain points..."

# After (externalized prompt)
from prompt_loader import load_prompt
prompt = load_prompt("3-cluster-jtbd-label.txt", sample_texts=texts)
```

## Benefits

### Testing Benefits
- **Reliability**: 106 tests ensure code stability
- **Refactoring Safety**: Tests catch breaking changes
- **Documentation**: Tests serve as usage examples
- **CI/CD Ready**: Automated testing in pipelines
- **Coverage**: Comprehensive edge case handling

### Prompt Management Benefits
- **Flexibility**: Modify prompts without touching code
- **Version Control**: Track prompt evolution separately
- **A/B Testing**: Easy prompt experimentation
- **Clarity**: All prompts in one organized location
- **Reusability**: Share prompts across projects

## Next Steps

### Testing Improvements
1. Add integration tests for full pipeline runs
2. Add performance benchmarks
3. Implement property-based testing
4. Add mutation testing
5. Create test data generators

### Prompt Enhancements
1. Add prompt templates for common patterns
2. Create prompt validation system
3. Build prompt versioning system
4. Add prompt performance metrics
5. Create prompt optimization tools

## Maintenance

### Adding New Tests
1. Create test file: `tests/test_new_module.py`
2. Import module and create test class
3. Add fixtures for test data
4. Write tests for all public methods
5. Test error cases and edge conditions
6. Run with coverage to ensure completeness

### Adding New Prompts
1. Create prompt file: `prompts/X-module-purpose.txt`
2. Follow naming convention: `[step]-[module]-[purpose].txt`
3. Add SYSTEM and USER sections
4. Document variables needed
5. Update `prompts/README.md`
6. Integrate with code using prompt_loader

## Conclusion

With comprehensive testing and externalized prompts, the pipeline is now:
- **More Reliable**: 106 tests ensure stability
- **More Flexible**: Prompts can be modified easily
- **More Maintainable**: Clear separation of concerns
- **More Professional**: Industry-standard practices
- **More Collaborative**: Easy for teams to work on