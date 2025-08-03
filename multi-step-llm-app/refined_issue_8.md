# Issue #8: Detour Mode (Deeper Analysis Substitution)

## 🚂 Overview
Enable dynamic substitution of standard LLM calls with deeper research detours using specialized engines (EXA, O1, Perplexity) for richer contextual analysis.

## 🎯 Objectives
- Allow flexible replacement of any pipeline step with research-enhanced versions
- Support multiple research engines with different capabilities
- Maintain output compatibility while enriching content quality
- Enable exploratory analysis without modifying core pipeline

## 🔧 Implementation Details

### Core Components

#### 1. Detour Engine Registry (`src/detour/engine_registry.py`)
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

#### 2. Detour Orchestrator (`src/detour/orchestrator.py`)
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

#### 3. Detour Configuration (`detour_config.yaml`)
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

### CLI Interface

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

### Output Structure
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

## 🤔 Implementation Questions

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

## 📁 Example Detour Outputs

### EXA Research Output
```json
{
  "engine": "exa",
  "timestamp": "2025-01-20T14:30:45Z",
  "query": "pain points in modern software development",
  "sources": [
    {
      "platform": "reddit",
      "subreddit": "r/programming",
      "relevance": 0.92,
      "insights": ["CI/CD complexity", "dependency management"]
    },
    {
      "platform": "hackernews",
      "thread_id": "39192847",
      "relevance": 0.88,
      "insights": ["technical debt", "team communication"]
    }
  ],
  "synthesized_pain_points": [
    {
      "pain_point": "Complex CI/CD pipeline management",
      "evidence_count": 47,
      "severity": "high",
      "sources": ["reddit:15", "hn:12", "twitter:20"]
    }
  ]
}
```

### Comparison Report
```markdown
# Detour Analysis Comparison

## Standard vs EXA-Enhanced Results

### Pain Points Discovered
- **Standard Mode**: 12 pain points
- **EXA Detour**: 23 pain points (+92%)

### Quality Metrics
- **Specificity**: Standard (6.5/10) vs EXA (8.7/10)
- **Evidence-Based**: Standard (4/12) vs EXA (23/23)
- **Actionability**: Standard (7.2/10) vs EXA (8.9/10)

### New Insights from Detour
1. Emerging pain points not in training data
2. Regional variations in pain points
3. Industry-specific nuances
```

## Related Issues
- Issue #2: Logging System - Track detour operations
- Issue #3: Debug Mode - Cost-effective detour testing
- Issue #6: Cost Tracking - Compare detour vs standard costs
- Issue #7: Rerun Step - Combine with detours for experimentation