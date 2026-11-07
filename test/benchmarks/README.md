# 🚀 Benchmarking System

The benchmarking system allows you to test different model and prompt configurations for each pipeline step in isolation. This is essential for identifying whether poor results are due to model selection, prompt engineering, or other factors.

## 📋 Overview

When pipeline results are "wonky," you can systematically test different model/prompt combinations to isolate the root cause. Each step can have multiple benchmark variations that test different:

- **Models** (Sonnet vs Haiku vs GPT-4o vs o1-preview)
- **Prompts** (default vs focused vs creative variations)
- **Settings** (temperature, max_tokens, include_example flags)

## 🏗️ Structure

```
test/benchmarks/
├── README.md                    # This file
├── research_analyzer/           # Step name (matches Python script)
│   ├── config.yml              # Benchmark configuration
│   ├── mock_research.json      # Mock input for consistent testing
│   └── results/                # Generated results
│       ├── option1_sonnet_default.txt
│       ├── option2_haiku_cost.txt
│       ├── option3_sonnet_focused.txt
│       ├── option4_gpt4o_alternative.txt
│       └── benchmark_summary.json
└── {other_steps}/              # Add more steps as needed
    ├── config.yml
    ├── mock_input.{ext}
    └── results/
```

## 📝 Configuration Format

Each step's `config.yml` follows this structure:

```yaml
benchmark_name: "Research Analyzer Model + Prompt Comparison"
description: "Test different model/prompt combos for Stage 1"

# Mock input file for consistent testing
mock_input: "mock_research.json"

# Different model + prompt variations to test
options:
  option1_name:
    name: "Human-readable Name"
    description: "What this variation tests"
    overrides:
      # Override any configuration from llm_config.yaml
      research_analysis:
        verticals:
          provider: anthropic
          model: claude-3-5-sonnet-20241022
          temperature: 0.7
          max_tokens: 2000
          include_example: true
          # Optional: Custom prompt (if not specified, uses default)
          prompt: |
            Custom prompt here...
            {research_content}
            
            Be more focused on X...{example}

# Evaluation criteria for manual assessment
evaluation:
  criteria:
    - "Quality metric 1"
    - "Quality metric 2" 
  metrics:
    - name: "Metric Name"
      description: "What to measure"
```

### Key Features:

1. **Flexible Overrides**: Override any setting from `llm_config.yaml`
2. **Optional Prompts**: If no `prompt` specified, uses the default from config
3. **Multiple Tasks**: Can override different tasks within a step (e.g., verticals, personas)
4. **Mock Input**: Consistent input file for reproducible testing

## 🖥️ CLI Usage

### List Available Steps
```bash
python benchmark_runner.py --list-steps
```

### Dry Run (Show Configuration)
```bash
python benchmark_runner.py research_analyzer --dry-run
```

### Run Benchmark
```bash
python benchmark_runner.py research_analyzer
```

## 📊 Results Analysis

Each benchmark option generates:

1. **Individual Result Files** (`results/option_name.txt`):
   - Model configurations used
   - Full LLM output
   - Timing and metadata
   - Error information (if any)

2. **Summary Report** (`results/benchmark_summary.json`):
   - Structured data for all options
   - Timestamps and durations
   - Success/failure status

3. **Manual Review**: Text files are formatted for easy human evaluation

## 🎯 Current Benchmarks

### research_analyzer
Tests Stage 1 parallel decomposition with 4 variations:

- **option1_sonnet_default**: Current production (Sonnet + default prompts)
- **option2_haiku_cost**: Cost-optimized (Haiku + reduced tokens)  
- **option3_sonnet_focused**: Same model + custom focused prompts
- **option4_gpt4o_alternative**: Cross-provider (GPT-4o + custom prompts)

## 🚀 Adding New Benchmarks

1. **Create Directory Structure**:
   ```bash
   mkdir -p test/benchmarks/new_step/results
   ```

2. **Copy Mock Input**:
   ```bash
   cp appropriate_input_file test/benchmarks/new_step/mock_input.json
   ```

3. **Create `config.yml`** following the format above

4. **Add Step Handler** in `benchmark_runner.py`:
   ```python
   def _run_new_step(self, config_loader: ConfigLoader) -> Dict[str, Any]:
       # Implementation here
   ```

## 🔧 Troubleshooting

### Common Issues:

1. **Missing Mock Input**: Ensure the mock input file exists and has valid format
2. **Configuration Errors**: Check YAML syntax and override paths
3. **API Keys**: Verify environment variables are set for the providers being tested
4. **Model Access**: Ensure you have access to the models specified in benchmarks

### Debugging Tips:

- Use `--dry-run` first to validate configuration
- Check `results/benchmark_summary.json` for detailed error information
- Compare model configurations in result files to verify overrides applied correctly

## 💡 Best Practices

1. **Start Small**: Begin with 2-3 variations, expand as needed
2. **Document Changes**: Update descriptions when modifying configurations
3. **Version Control**: Commit benchmark configs alongside code changes
4. **Regular Testing**: Run benchmarks when making significant prompt changes
5. **Cost Awareness**: Include both expensive and cheap model options

## 🔄 Integration with Main Pipeline

The benchmarking system is completely isolated from the main pipeline:

- Uses the same `ConfigLoader` and `llm_config.yaml`
- Applies temporary overrides without modifying original config
- Can test configurations before deploying to production
- Helps optimize cost vs quality tradeoffs

This allows safe experimentation without affecting production pipeline runs.