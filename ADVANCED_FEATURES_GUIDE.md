# Advanced Features Guide - Modular Ideation Pipeline

## Overview

The modular ideation pipeline now supports advanced keyword strategy customization and clustering algorithm overrides while maintaining complete backward compatibility. This guide covers the advanced features available in the system.

## 🎯 Key Capabilities Added

### 1. Keyword Strategy Customization per Flavor
- **Seed Terms**: Domain-specific starting terms for query generation
- **Exclusion Terms**: Terms to filter out from queries
- **Query Patterns**: Template-based query generation (e.g., "how to {term}")
- **Synonym Expansion**: Automatic synonym detection using WordNet
- **Stemming**: Word stemming for broader search coverage
- **Entity Extraction**: Extract entities from research reports for query expansion
- **Subreddit Hints**: Domain-specific subreddit targeting

### 2. Clustering Algorithm Overrides
- **Custom Pain Dimension Weights**: Emphasize specific pain dimensions
- **Clustering Parameters**: Algorithm, linkage method, thresholds
- **Quality Controls**: Min cluster size, similarity thresholds
- **Stability Guarantees**: Preserve baseline logic when needed
- **Consistent Output**: Always output in standard format for downstream processing

### 3. Framework Flexibility
- **ERRC**: Blue Ocean Strategy (eliminate, reduce, raise, create)
- **JTBD**: Jobs-to-be-Done framework (functional, emotional, social)
- **Custom**: User-defined analysis frameworks
- **Output Schemas**: Business ideas, site candidates, device specifications

## Advanced Flavor Examples

### Cryptocurrency Mining Site Location Analysis

```yaml
name: "crypto_mining_sites"
description: "Cryptocurrency mining site location analysis with advanced keyword strategy"

reddit_strategy:
  # Domain-specific seed terms
  seed_terms:
    - "mining farm"
    - "ASIC hosting"
    - "electricity rates"
    - "cooling costs"
    - "corruption"    # Political risk factor
    - "tariffs"       # Trade policy impact
    
  # Filter out unwanted content
  exclusion_terms:
    - "scam"
    - "ponzi"
    - "residential"  # Focus on commercial/industrial
    
  # Site location query patterns
  query_patterns:
    - "where to setup {term}"
    - "{term} location requirements"
    - "best states for {term}"
    - "industrial {term} challenges"
    
  # Domain-specific subreddit targeting
  subreddit_hints:
    crypto_mining:
      - "CryptoCurrency"
      - "BitcoinMining"
    industrial_real_estate:
      - "CommercialRealEstate"
      - "datacenter"

framework:
  framework_type: "custom"
  
  # Custom clustering for site location factors
  clustering:
    algorithm: "hierarchical"
    n_zones: 5  # Focused site analysis
    
    # Custom weights for site selection
    pain_dimension_weights:
      "technology_gaps": 2.0      # Critical for mining
      "regulatory_barriers": 1.8  # High regulatory complexity
      "cost_optimization": 1.5    # Electricity costs
      
    preserve_baseline_logic: false  # Use custom clustering

output:
  schema_type: "site_candidate"
  required_fields:
    - "location_type"
    - "power_requirements"
    - "regulatory_compliance_needs"
    - "infrastructure_score"
```

### Medical Device Innovation

```yaml
name: "medical_devices"
description: "Medical device innovation pipeline with JTBD framework"

reddit_strategy:
  seed_terms:
    - "medical device"
    - "patient monitoring"
    - "assistive technology"
    - "clinical workflow"
    - "patient safety"
    
  # Medical precision - no stemming for terminology
  enable_synonyms: true
  enable_stemming: false  # Medical terms are precise
  
  query_patterns:
    - "{term} problems"
    - "{term} user experience"
    - "{term} accessibility"
    - "improving {term}"

framework:
  framework_type: "jobs_to_be_done"
  
  # Medical-specific clustering
  clustering:
    algorithm: "hierarchical"
    n_zones: 6  # More zones for medical diversity
    linkage_method: "complete"  # Stricter clustering
    
    # Medical-specific weights
    pain_dimension_weights:
      "accessibility_barriers": 2.5  # Critical for medical devices
      "safety_concerns": 2.0         # Patient safety paramount
      "usability_issues": 1.8        # Must be intuitive
      
    required_dimensions:  # Must have these dimensions
      - "safety_concerns"
      - "usability_issues"

output:
  schema_type: "device_spec"
  required_fields:
    - "device_category"
    - "clinical_indication"
    - "safety_specifications"
    - "regulatory_pathway"
```

## Keyword Strategy Engine Details

### Architecture

```python
class KeywordStrategyEngine:
    """Generates flavor-customized Reddit search queries."""
    
    def generate_query_set(self, jtbd: str, reddit_strategy, analysis_content: str) -> QuerySet:
        """Complete query generation pipeline:
        1. Extract base keywords from JTBD
        2. Add seed terms from flavor config
        3. Generate base queries
        4. Expand with synonyms (if enabled)
        5. Apply stemming (if enabled)
        6. Apply query patterns
        7. Generate subreddit-specific queries
        8. Filter exclusions
        """
```

### Query Set Structure

```python
@dataclass
class QuerySet:
    """Structured set of Reddit queries for a specific JTBD/flavor."""
    jtbd: str
    base_queries: List[str]          # Core queries from JTBD
    expanded_queries: List[str]      # Synonyms/stemming expansion
    pattern_queries: List[str]       # Template-based queries
    subreddit_specific: Dict[str, List[str]]  # Targeted queries
    excluded_terms_found: List[str]  # Filtered content
```

### Advanced Features

#### Synonym Expansion
```python
# Uses WordNet for intelligent synonym detection
def get_synonyms(self, word: str) -> List[str]:
    """Get synonyms for a word using WordNet."""
    # Returns up to 3 relevant synonyms per word
```

#### Query Pattern Templates
```yaml
query_patterns:
  - "how to {term}"           # Instruction seeking
  - "{term} problems"         # Problem identification  
  - "struggling with {term}"  # Emotional expressions
  - "{term} advice"          # Solution seeking
```

#### Domain-Specific Subreddit Targeting
```yaml
subreddit_hints:
  crypto_mining:
    - "CryptoCurrency"
    - "BitcoinMining"
  industrial_real_estate:
    - "CommercialRealEstate"
    - "datacenter"
```

## Clustering Algorithm Customization

### Configuration Options

```yaml
clustering:
  algorithm: "hierarchical"     # "hierarchical", "kmeans", "dbscan"
  n_zones: 5                   # Number of opportunity zones
  linkage_method: "ward"       # "ward", "complete", "average"
  
  # Advanced parameters
  min_cluster_size: 3          # Minimum items per cluster
  similarity_threshold: 0.8    # Distance threshold for merging
  pain_dimension_threshold: 0.25  # Minimum significance score
  
  # Custom weights for specific pain dimensions
  pain_dimension_weights:
    "technology_gaps": 2.0     # 2x weight for tech issues
    "safety_concerns": 1.8     # High priority for safety
    
  # Quality controls
  required_dimensions:         # Dimensions that must be present
    - "safety_concerns"
  
  # Stability guarantee
  preserve_baseline_logic: false  # Use custom vs. baseline clustering
```

### Stability Guarantees

The clustering system maintains stability through:

1. **Preserve Baseline Logic**: When `preserve_baseline_logic: true`, uses exact current algorithm
2. **Consistent Output Format**: Always outputs standard opportunity zone format
3. **Graceful Fallbacks**: Falls back to baseline parameters if custom config fails
4. **Validation**: All clustering parameters are validated before use

### Pain Dimension Weighting

```python
# Example: Emphasize technology and safety for medical devices
pain_dimension_weights = {
    "technology_gaps": 2.0,      # Critical for device functionality
    "safety_concerns": 1.8,      # Patient safety paramount
    "usability_issues": 1.5,     # User experience important
    "cost_burden": 1.2           # Cost sensitivity in healthcare
}

# Applied during clustering distance calculation
weighted_score = base_score * weight_factor
```

## Testing and Validation

### Comprehensive Test Suite

```bash
python test_modular_system.py

# Tests:
# ✅ Flavor loading and validation
# ✅ Baseline configuration accuracy (12 checks)
# ✅ Prompt preservation
# ✅ Advanced flavor features (5 checks)
# ✅ Keyword strategy engine (2 checks)
```

### Validation Checks

1. **Configuration Validation**: All YAML configs validated on load
2. **Baseline Preservation**: 12-point verification of exact behavior
3. **Advanced Feature Testing**: Seed terms, exclusions, clustering weights
4. **Keyword Engine Testing**: Extraction quality and query generation
5. **Framework Compatibility**: ERRC, JTBD, Custom framework validation

## Usage Examples

### List Available Flavors
```bash
python run_pipeline_modular.py --list-flavors

# Output:
# baseline: Original ERRC-based real estate pipeline ⭐ EXACT reproduction
# crypto_mining_sites: Cryptocurrency mining site location analysis  
# medical_devices: Medical device innovation with JTBD framework
```

### Run with Advanced Features
```bash
# Crypto mining site analysis
python run_pipeline_modular.py --flavor crypto_mining_sites --verbose

# Medical device innovation  
python run_pipeline_modular.py --flavor medical_devices --interactive

# Baseline (exact current behavior)
python run_pipeline_modular.py --flavor baseline
```

### Custom Query Generation
```python
from flavors.keyword_strategy import generate_flavor_queries

# Generate queries for all JTBDs using flavor config
query_sets = generate_flavor_queries(
    jtbds=jtbd_list,
    flavor_config=crypto_flavor,
    analysis_content=research_content
)

# Each JTBD gets customized query set based on flavor
for jtbd_id, query_set in query_sets.items():
    queries = query_set.get_all_queries(limit=10)  # Top 10 queries
    print(f"JTBD {jtbd_id}: {len(queries)} customized queries")
```

## Migration and Compatibility

### Backward Compatibility Guarantee

✅ **Baseline flavor reproduces EXACT current behavior**  
✅ **Original `run_pipeline.py` unchanged**  
✅ **All existing functionality preserved**  
✅ **No breaking changes**  

### Migration Path

1. **Current Users**: Continue using `run_pipeline.py` - no changes required
2. **New Features**: Use `run_pipeline_modular.py` with advanced flavors  
3. **Gradual Adoption**: Test with `--flavor baseline` first
4. **Custom Flavors**: Create domain-specific YAML configurations

## Performance Considerations

### Query Generation
- **Base Keywords**: Limited to top 10 per JTBD
- **Synonym Expansion**: Max 3 synonyms per word (optional)
- **Query Patterns**: Applied to top 5 keywords only
- **Subreddit Targeting**: Max 5 queries per domain

### Clustering Performance  
- **Hierarchical Algorithm**: O(n³) complexity, suitable for <1000 items
- **Custom Weights**: Minimal performance impact
- **Caching**: Pain dimension scores cached per discussion
- **Parallel Processing**: Perplexity API calls parallelized

### Memory Usage
- **Query Sets**: ~1KB per JTBD with full expansion
- **Clustering Data**: ~10MB for typical 500 discussions
- **Model Context**: Flavor configs loaded once, reused

The modular system is production-ready with comprehensive testing, validation, and performance optimization while maintaining complete backward compatibility with the baseline pipeline.