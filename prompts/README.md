# Prompts Directory

This directory contains all the prompts used in the Multi-Step LLM Application pipeline. Each prompt is stored in a separate text file for easy modification and version control.

## Directory Structure

Prompts are organized by pipeline step number and component name:

```
prompts/
├── 0-main-*.txt                    # General workflow demo prompts
├── 1-research-analyzer-*.txt       # Research analysis prompts
├── 2-jobs-researcher-*.txt         # Jobs-to-be-Done research prompts
├── 3-cluster-jtbd-*.txt           # JTBD clustering prompts
├── 4-value-curve-*.txt            # Value curve mapping prompts
├── 5-product-generator-*.txt      # Product idea generation prompts
└── README.md                       # This documentation
```

## Prompt Files

### 0. Main Workflow Demo (main.py)
- `0-main-story-ideation.txt` - Creative writing demo prompt

### 1. Research Analysis (research_analyzer.py)
- `1-research-analyzer-verticals.txt` - Industry verticals identification
- `1-research-analyzer-personas.txt` - User personas extraction
- `1-research-analyzer-pain-points.txt` - Pain points analysis
- `1-research-analyzer-solutions.txt` - Solution types discovery

### 2. Jobs-to-be-Done Research (jobs_researcher.py)
- `2-jobs-researcher-jtbd-table.txt` - JTBD table generation from search results

### 3. JTBD Clustering (cluster_jtbd.py)
- `3-cluster-jtbd-label.txt` - Cluster labeling and analysis
- `3-cluster-jtbd-zones.txt` - Opportunity zone generation

### 4. Value Curve Mapping (value_curve_mapper.py)
- `4-value-curve-norms.txt` - Industry norms and sacred cows analysis
- `4-value-curve-engineering.txt` - Over/under-engineering spectrum

### 5. Product Idea Generation (product_idea_generator.py)
- `5-product-generator-errc.txt` - ERRC grid generation (OpenAI o1)
- `5-product-generator-ideas.txt` - Product ideas generation (Claude Opus)
- `5-product-generator-viability.txt` - Viability assessment (Claude Opus)

## Prompt Format

Each prompt file follows this structure:

```
SYSTEM: [System role and expertise]

USER: [Context variables]
{variable_name}

[Main prompt text with instructions]

[Expected output format]
```

## Variables

Common variables used in prompts:

- `{research_content}` - Raw research document text
- `{zone_name}` - Opportunity zone name
- `{zone_description}` - Zone description
- `{competitive_results}` - Competitive intelligence data
- `{errc_grid}` - ERRC analysis grid
- `{ideas_summary}` - Product ideas list
- `{cluster_summaries}` - Cluster analysis data

## Modifying Prompts

To modify a prompt:

1. Edit the relevant `.txt` file in this directory
2. No code changes needed - prompts are loaded dynamically
3. Test your changes with a sample run
4. Commit the updated prompt files

## Best Practices

1. **Be Specific**: Include clear instructions and expected output format
2. **Use Examples**: When possible, provide examples of desired output
3. **Context Matters**: Always include relevant context from previous steps
4. **Format Output**: Request structured output (JSON, markdown tables, etc.)
5. **System Prompts**: Set appropriate expertise for each task

## Adding New Prompts

When adding new functionality:

1. Create a new prompt file following the naming convention
2. Update this README with the new prompt description
3. Modify the relevant Python file to load from the prompt file
4. Test thoroughly with various inputs

## Performance Tips

1. **Token Efficiency**: Keep prompts concise but complete
2. **Model Selection**: Use appropriate models for each task
3. **Temperature**: Lower for analytical tasks, higher for creative
4. **Output Length**: Set reasonable max_tokens limits

## Version Control

All prompt changes are tracked in git. Use descriptive commit messages:

```bash
git add prompts/1-research-analyzer-verticals.txt
git commit -m "prompt: Enhance verticals analysis with market size criteria"
```