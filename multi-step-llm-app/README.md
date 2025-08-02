# Multi-Step LLM Application with Anthropic

A Python application suite that demonstrates multi-step LLM workflows using the Anthropic Claude API. Includes a general workflow application, research analyzer with S3 integration and parallel processing, and Jobs-to-be-Done researcher using EXA search.

## Features

### General Workflow Application (`main.py`)
- 🎯 Multi-step LLM workflow execution
- 🖥️ Interactive mode with step-by-step progression
- 🤖 Headless mode for automated execution
- 📝 Context preservation across workflow steps
- 🎨 Rich terminal output with progress indicators
- 💾 Automatic result saving to markdown file
- ⚡ Built-in error handling and rate limit management

### Research Analyzer (`research_analyzer.py`)
- 🪣 S3 integration for pulling research documents
- 🔄 Parallel LLM processing with 4 concurrent calls
- 🧠 Dual model support (Claude Sonnet & Opus)
- 📊 Four analysis types: Industry Verticals, User Personas, Pain Points, Solution Types
- 📄 Automatic result combination and markdown export
- 🏃 High-performance concurrent execution with ThreadPoolExecutor

### Jobs-to-be-Done Researcher (`jobs_researcher.py`)
- 🔍 EXA search integration for real-world customer context
- 🎯 Targeted searches across Reddit, reviews, interviews, news
- 💡 Automatic Jobs-to-be-Done extraction from search results
- 📋 Structured JTBD table generation
- 🤖 Optional Claude-powered synthesis for deeper insights
- 📊 Comprehensive research report with actionable findings
- 📝 Automatic pain point extraction for clustering

### JTBD Clustering Analysis (`cluster_jtbd.py`)
- 🎨 Cohere Embed v3 for state-of-the-art embeddings
- 🧩 HDBSCAN clustering with auto-tuned parameters
- 🏷️ GPT-4o powered cluster labeling
- 🎯 Opportunity zone generation with strategic prioritization
- 📊 JSON output with complete analysis results
- 💯 Percentage-based importance scoring (totaling 100%)

### Value Curve Mapper (`value_curve_mapper.py`)
- 🔍 EXA search for competitive strategy canvas per zone
- 🧠 Claude Opus analysis of industry norms and taboos
- ⚖️ Over/under-engineering spectrum analysis
- 📈 Sequential then parallel processing (EXA → Opus×2)
- 🎯 Value curve disruption opportunities identification
- 📊 Comprehensive strategic insights report

## Installation

1. Clone or create this project:
```bash
cd anthropic-multi-step-app
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Anthropic API key:
```bash
cp .env.example .env
# Edit .env and add your API key
```

## Usage

### General Workflow Application

#### Interactive Mode (Default)
Run the application and inspect each step's output before continuing:
```bash
python main.py
```
- Press Enter after each step to continue
- Type 'q' and press Enter to quit early

#### Headless Mode
Run all steps automatically without user interaction:
```bash
python main.py --headless
```

#### Test API Connection
Verify your API key is working:
```bash
python main.py --test
```

### Research Analyzer

#### Pull from S3 (using .env configuration)
```bash
python research_analyzer.py
```

#### Pull from S3 with custom bucket/key
```bash
python research_analyzer.py --bucket my-bucket --key path/to/research.json
```

#### Use local file instead of S3
```bash
python research_analyzer.py --local example_research.json
```

#### Specify custom output file
```bash
python research_analyzer.py --output my_analysis.md
```

#### Test connections (Anthropic & S3)
```bash
python research_analyzer.py --test
```

### Jobs-to-be-Done Researcher

#### Run JTBD research on analysis results
```bash
python jobs_researcher.py
```

#### Specify custom input/output files
```bash
python jobs_researcher.py --input my_analysis.md --output my_jtbd.md
```

#### Test EXA connection
```bash
python jobs_researcher.py --test
```

### JTBD Clustering Analysis

#### Run clustering on pain points
```bash
python cluster_jtbd.py pain_points.txt
```

#### Specify custom output
```bash
python cluster_jtbd.py pain_points.txt --output my_opportunity_zones.json
```

#### Test API connections (Cohere & OpenAI)
```bash
python cluster_jtbd.py --test
```

### Value Curve Mapping

#### Map value curves for opportunity zones
```bash
python value_curve_mapper.py opportunity_zones.json
```

#### Custom output files
```bash
python value_curve_mapper.py zones.json --json-output curves.json --report-output curves.md
```

#### Test API connections (EXA & Opus)
```bash
python value_curve_mapper.py --test
```

## Example Workflow

The included example demonstrates a creative writing workflow with 5 steps:

1. **Story Ideation** - Generates a unique story concept
2. **Character Development** - Develops the main character
3. **Plot Outline** - Creates a three-act structure
4. **Opening Scene** - Writes the opening scene
5. **Story Analysis** - Analyzes and suggests improvements

Each step builds upon the context from previous steps, creating a cohesive narrative.

## Customizing the Workflow

To create your own workflow, modify the `create_workflow_steps()` method in `main.py`:

```python
def create_workflow_steps(self) -> List[WorkflowStep]:
    return [
        WorkflowStep(
            name="Your Step Name",
            system_prompt="System instructions for Claude",
            user_prompt="What you want Claude to do",
            max_tokens=1000,
            temperature=0.7
        ),
        # Add more steps...
    ]
```

## Output

Results are automatically saved to `workflow_results.md` after completion, containing all step outputs in a formatted markdown file.

## Requirements

- Python 3.8+
- Anthropic API key
- Dependencies listed in requirements.txt

## Environment Variables

### Required
- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)

### Optional (for Research Analyzer)
- `AWS_ACCESS_KEY_ID`: AWS access key for S3
- `AWS_SECRET_ACCESS_KEY`: AWS secret key for S3
- `AWS_REGION`: AWS region (default: us-east-1)
- `S3_BUCKET_NAME`: S3 bucket containing research files
- `S3_FILE_KEY`: Path to research JSON file in S3

### Optional (for Jobs Researcher)
- `EXA_API_KEY`: EXA API key for web search functionality

### Optional (for Clustering Analysis)
- `COHERE_API_KEY`: Cohere API key for embeddings
- `OPENAI_API_KEY`: OpenAI API key for GPT-4o labeling

## Error Handling

The application includes comprehensive error handling for:
- Missing API keys
- Network errors
- Rate limiting
- Invalid responses

## Research Analyzer Details

The research analyzer performs four parallel analyses on your research document:

1. **Industry Verticals** (Claude Sonnet)
   - Identifies distinct industry domains
   - Analyzes differentiating factors
   - Provides structured categorization

2. **User Personas** (Claude Sonnet)
   - Extracts customer/user profiles
   - Details demographics and needs
   - Maps goals and pain points

3. **Pain Points** (Claude Opus)
   - Deep analysis of user challenges
   - Categorizes by severity and impact
   - Identifies both explicit and implicit issues

4. **Solution Types** (Claude Opus)
   - Discovers described solutions
   - Infers potential approaches
   - Evaluates by complexity and effectiveness

### JSON Input Format

The research analyzer expects a JSON file with a `content` field:

```json
{
  "content": "Your research text goes here...",
  "metadata": {
    "optional": "additional fields"
  }
}
```

See `example_research.json` for a complete example.

## Complete Workflow Example

The five applications create a comprehensive research and strategy pipeline:

```bash
# Step 1: Pull research from S3 and analyze
python research_analyzer.py --bucket my-bucket --key research.json

# Step 2: Use analysis to find real-world context
python jobs_researcher.py --input analysis_results.md --output jtbd_research.md

# Step 3: Cluster pain points and identify opportunity zones
python cluster_jtbd.py jtbd_research_pain_points.txt --output opportunity_zones.json

# Step 4: Map value curves for each opportunity zone
python value_curve_mapper.py opportunity_zones.json --output value_curves_report.md

# Step 5: Review strategic insights
cat value_curves_report.md
```

## Jobs Researcher Details

The Jobs-to-be-Done researcher performs targeted searches to find real customer context:

### Search Categories:
1. **Reddit Discussions** - Authentic user frustrations and workflows
2. **Product Reviews** - Comparative analysis and feature gaps
3. **User Interviews** - Deep insights into daily challenges
4. **Industry News** - Market trends and emerging needs
5. **Tutorials/Guides** - Common workarounds indicating unmet needs

### JTBD Output Includes:
- Structured job statements (When I... I want to... So I can...)
- Frequency analysis (Daily/Weekly/Monthly usage patterns)
- Current solution mapping
- Pain level assessment
- Opportunity scoring

### Outputs:
- `jtbd_research.md` - Comprehensive research report
- `jtbd_research_pain_points.txt` - Extracted pain points for clustering

## Clustering Analysis Details

The JTBD clustering analysis uses advanced ML techniques:

### Process:
1. **Embedding**: Cohere Embed v3 creates high-quality vector representations
2. **Clustering**: HDBSCAN automatically finds optimal cluster count
3. **Labeling**: GPT-4o analyzes each cluster for insights
4. **Opportunity Zones**: Strategic prioritization with percentages

### Output Structure:
```json
{
  "metadata": {
    "timestamp": "2024-08-01T10:30:00",
    "n_clusters": 7,
    "n_pain_points": 156
  },
  "clusters": {
    "0": {
      "label": "Authentication Friction",
      "summary": "Users struggle with complex login processes",
      "job_to_be_done": "When I need to access my account, I want to login quickly, so I can start working immediately",
      "severity": "High",
      "size": 23
    }
  },
  "opportunity_zones": {
    "opportunity_zones": [
      {
        "name": "Seamless Authentication",
        "description": "Eliminate login friction across all touchpoints",
        "importance_percentage": 35,
        "potential_impact": "High"
      }
    ]
  }
}
```

## Value Curve Mapping Details

Phase 2 analysis provides deep competitive insights:

### Process Flow:
1. **Sequential First**: EXA searches for competitive landscape
2. **Then Parallel**: Two Claude Opus analyses run simultaneously:
   - Industry norms, taboos, and dogma identification
   - Over/under-engineering spectrum analysis

### Output Includes:
- **Strategy Canvas Data**: Key value dimensions from competitors
- **Industry Sacred Cows**: Assumptions never questioned
- **Engineering Gaps**: What's too complex vs. too simple
- **Disruption Opportunities**: Where to create new value curves

### Strategic Insights:
```json
{
  "zone": "Seamless Authentication",
  "industry_norms": "All competitors require multi-factor auth...",
  "over_engineered": "Biometric systems with 99.99% accuracy that frustrate users...",
  "under_engineered": "Password recovery flows that take days...",
  "value_curve_opportunity": "Eliminate complexity while creating trust..."
}
```

## Performance

The complete pipeline provides:
- **Research Analysis**: 15-30 seconds (4 parallel LLM calls)
- **JTBD Search**: 10-20 seconds (EXA web search)
- **Clustering**: 5-10 seconds (Cohere embeddings)
- **Opportunity Zones**: 10-15 seconds (GPT-4o processing)
- **Value Curve Mapping**: 20-30 seconds per zone (EXA + 2 Opus)
- **Total Pipeline**: ~2-3 minutes for comprehensive strategy analysis

## License

MIT License - Feel free to modify and use as needed.