# Pipeline Lifecycle Documentation

## Stage 1: Research Analysis (`research_analyzer.py`)
**Pattern Name**: Parallel Decomposition

### Input
- **Source**: Either S3 bucket or local JSON file via `--local` flag
- **Format**: JSON with structure:
  ```json
  {
    "metadata": {...},
    "content": "[Full research document text, can be 10,000+ words]"
  }
  ```
- **Domain**: Domain-agnostic - can be real estate, software, healthcare, any market research

### Processing
1. **Loads research document** from S3 or local file
2. **Executes 4 parallel LLM calls** with the ENTIRE research document as context:

   **Call 1: Industry Verticals (Claude Sonnet)**
   - Prompt: "Within this research document, what distinct industry verticals can you identify?..."
   - Response: Unstructured text identifying market segments

   **Call 2: User Personas (Claude Sonnet)**  
   - Prompt: "Looking at this research document, what user personas or customer segments can you identify?..."
   - Response: Unstructured text describing personas with demographics, needs, goals, pain points

   **Call 3: Pain Points (Claude Opus)**
   - Full prompt structure:
     ```
     Research Document:
     
     [ENTIRE RESEARCH DOCUMENT TEXT]
     
     Within this research document, what are the key pain points that you observe 
     or can infer based on the research presented? Please categorize these pain points 
     by severity, frequency, and impact on users. Include both explicit and implicit 
     pain points you can deduce from the research.
     ```
   - Response: Unstructured text, often numbered list format like:
     - "1. Geographic concentration risk (High frequency, high impact): Description..."
     - "2. Technology infrastructure limitations (High frequency, high impact): Description..."

   **Call 4: Solution Types (Claude Opus)**
   - Prompt: "Based on this research document, what potential solution types or approaches could address the identified needs?..."
   - Response: Unstructured text with solution categories

3. **Combines all 4 responses** via simple string concatenation (NO LLM call):
   - Python function `combine_results()` in research_analyzer.py
   - Simply adds markdown headers and separators between the 4 responses
   - Pure string manipulation, no parsing or processing

### Output
- **File**: `analysis_results.md`
- **Structure**:
  ```markdown
  # Research Analysis Results
  
  Generated on: [timestamp]
  
  ---
  
  ## Industry Verticals
  
  [Unstructured response from Sonnet]
  
  ---
  
  ## User Personas
  
  [Unstructured response from Sonnet]
  
  ---
  
  ## Pain Points
  
  [Unstructured response from Opus]
  
  ---
  
  ## Solution Types
  
  [Unstructured response from Opus]
  
  ---
  ```

### Key Insights
- The prompts do NOT request structured output (no "provide as bullet points" instruction)
- Each LLM has full context of the entire research document
- Responses are intentionally unstructured to allow natural language expression
- The combined markdown preserves the exact LLM responses without parsing

### Common Output Patterns
- Industry Verticals: Often numbered lists with descriptions
- User Personas: Often bullet points with demographic details
- Pain Points: Often numbered items with severity/frequency/impact notation
- Solution Types: Often bullet points or numbered approaches

---

*To be continued with Stage 2 once verified...*