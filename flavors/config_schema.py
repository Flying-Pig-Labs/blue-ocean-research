#!/usr/bin/env python3
"""
Flavor Configuration Schema - Modular Pipeline System

Defines the schema and validation for YAML-driven ideation flavors.
Each flavor customizes the pipeline behavior while maintaining core structure.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from enum import Enum
import yaml
import os
import logging

logger = logging.getLogger(__name__)

class FrameworkType(Enum):
    """Supported strategic frameworks for ideation."""
    ERRC = "errc"  # Eliminate, Reduce, Raise, Create (Blue Ocean Strategy)
    JTBD = "jobs_to_be_done"  # Jobs-to-be-Done framework
    LEAN_CANVAS = "lean_canvas"  # Lean startup business model canvas
    DESIGN_THINKING = "design_thinking"  # Human-centered design process
    SPEC_TRACE = "spec_trace"  # Medical device SPEC-TRACE framework
    SITE_FEASIBILITY = "site_feasibility"  # Site location feasibility framework
    UNIFY = "unify"  # City revitalization with uncommon alliances framework
    ACQUIRE = "acquire"  # Private equity acquisition analysis framework
    MINING_VIABILITY = "mining_viability"  # Crypto mining viability with 9 core modules
    CUSTOM = "custom"  # Custom framework with user-defined prompts

class OutputSchema(Enum):
    """Supported output schemas for different ideation types."""
    BUSINESS_IDEA = "business_idea"  # Standard business concepts
    SITE_CANDIDATE = "site_candidate"  # Real estate/location opportunities
    DEVICE_SPEC = "device_spec"  # Hardware/IoT device specifications
    SERVICE_BLUEPRINT = "service_blueprint"  # Service design specifications
    PLATFORM_CONCEPT = "platform_concept"  # Digital platform ideas
    REVITALIZATION_INITIATIVE = "revitalization_initiative"  # City revitalization partnerships
    PRELIMINARY_LOI = "preliminary_loi"  # Private equity acquisition LOIs
    MINING_SETUP = "mining_setup"  # Crypto mining setup specifications

@dataclass
class RedditSearchStrategy:
    """Configuration for Reddit keyword generation and search."""
    # Support both old and new fields for backward compatibility
    keyword_extraction_prompt: str = field(default="")
    subreddit_discovery_prompt: str = field(default="")
    
    # Original fields
    subreddit_selection: List[str] = field(default_factory=list)
    fallback_subreddits: List[str] = field(default_factory=list)
    
    search_filters: Dict[str, Any] = field(default_factory=lambda: {
        "min_score": 5,
        "min_comments": 2,
        "time_filter": "month",
        "sort": "top"
    })
    
    # Current pipeline parameters
    max_subreddits: int = 5
    max_queries_per_jtbd: int = 3
    max_posts_per_query: int = 2
    
    # Legacy fields for compatibility
    max_posts_per_keyword: int = 10
    keyword_combinations: bool = True
    
    # NEW: Advanced keyword strategy customization
    seed_terms: List[str] = field(default_factory=list)  # Domain-specific starting terms
    exclusion_terms: List[str] = field(default_factory=list)  # Terms to avoid
    query_patterns: List[str] = field(default_factory=list)  # Template patterns like "how to {term}"
    enable_synonyms: bool = True  # Expand with synonyms
    enable_stemming: bool = True  # Use word stemming for broader matches
    enable_entity_extraction: bool = False  # Extract entities from reports for query expansion
    subreddit_hints: Dict[str, List[str]] = field(default_factory=dict)  # Domain -> subreddit mapping

@dataclass
class ClusteringConfig:
    """Configuration for opportunity zone clustering algorithm."""
    # Core clustering parameters (with current defaults)
    algorithm: str = "hierarchical"  # "hierarchical", "kmeans", "dbscan"
    n_zones: int = 7  # Number of opportunity zones to create
    linkage_method: str = "ward"  # For hierarchical: "ward", "complete", "average"
    
    # Clustering behavior overrides
    min_cluster_size: Optional[int] = None  # Minimum items per cluster
    similarity_threshold: Optional[float] = None
    
    # Generalized dimension weighting (supports different schemes per flavor)
    dimension_weights: Dict[str, float] = field(default_factory=dict)  # Generic dimension weights
    pain_dimension_weights: Dict[str, float] = field(default_factory=dict)  # Legacy baseline pain dimensions
    market_weights: Dict[str, float] = field(default_factory=dict)  # Market-based weighting
    technical_weights: Dict[str, float] = field(default_factory=dict)  # Technical factors
    regulatory_weights: Dict[str, float] = field(default_factory=dict)  # Regulatory considerations
    
    # Filtering thresholds
    pain_dimension_threshold: float = 0.3  # Minimum score to consider significant (legacy compatibility)
    dimension_threshold: float = 0.3  # Minimum score to consider significant
    required_dimensions: List[str] = field(default_factory=list)  # Dimensions that must be present
    
    # Quality controls
    max_discussions_per_jtbd: int = 3  # Limit Reddit discussions per JTBD for performance
    enable_llm_naming: bool = True  # Use LLM to generate unique zone names
    enable_solution_extraction: bool = True  # Extract solution requirements
    
    # Stability guarantees
    preserve_baseline_logic: bool = True  # When True, use exact current clustering approach
    output_format: str = "consistent"  # Always output in standard format for downstream

@dataclass
class FrameworkConfig:
    """Configuration for strategic framework application."""
    framework_type: FrameworkType
    custom_prompts: Dict[str, str] = field(default_factory=dict)
    analysis_dimensions: List[str] = field(default_factory=list)
    output_format: str = "structured_json"
    
    # Advanced framework parameters for custom frameworks
    params: Dict[str, Any] = field(default_factory=dict)
    adapter: str = ""  # Adapter class name for custom frameworks
    
    # ERRC-specific config
    errc_categories: List[str] = field(default_factory=lambda: [
        "eliminate", "reduce", "raise", "create"
    ])
    
    # JTBD-specific config
    jtbd_situations: List[str] = field(default_factory=lambda: [
        "functional", "emotional", "social"
    ])
    
    # Mining viability-specific config
    modules: Dict[str, str] = field(default_factory=dict)  # M1-M9 module definitions
    scoring: Dict[str, Any] = field(default_factory=dict)  # Scoring formula and weights
    viability_weights: Dict[str, float] = field(default_factory=dict)  # Mining dimension weights
    
    # Clustering integration
    clustering: ClusteringConfig = field(default_factory=ClusteringConfig)

@dataclass
class OutputConfig:
    """Configuration for output formatting and structure."""
    schema_type: OutputSchema
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    
    # GitHub repository configuration
    repo_naming_pattern: str = "{flavor_name}-{timestamp}"
    issue_labels: List[str] = field(default_factory=lambda: [
        "innovation", "market-opportunity", "research-backed"
    ])
    use_private_repo: bool = False

@dataclass
class FlavorConfig:
    """Complete flavor configuration defining pipeline behavior."""
    name: str
    description: str
    version: str = "1.0.0"
    
    # Core pipeline components - generalized keyword strategy
    keyword_strategy: Dict[str, Any] = field(default_factory=dict)  # General keyword strategy config
    reddit_strategy: RedditSearchStrategy = field(default_factory=RedditSearchStrategy)  # Legacy compatibility
    framework: FrameworkConfig = field(default_factory=lambda: FrameworkConfig(FrameworkType.ERRC))
    output: OutputConfig = field(default_factory=lambda: OutputConfig(OutputSchema.BUSINESS_IDEA))
    
    # Direct clustering config access (for backward compatibility)
    clustering: Optional[ClusteringConfig] = None
    
    # Mining viability-specific inputs
    user_inputs: Dict[str, Any] = field(default_factory=dict)  # User configuration parameters
    data_connectors: Dict[str, Any] = field(default_factory=dict)  # Data source configurations
    
    # Pipeline stage overrides
    stage_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Model selection (can override per stage)
    default_models: Dict[str, str] = field(default_factory=lambda: {
        "research_analysis": "claude-3-5-sonnet-20241022",
        "reddit_analysis": "claude-3-5-sonnet-20241022",
        "opportunity_zones": "claude-3-5-sonnet-20241022",
        "idea_generation": "claude-3-opus-20240229",
        "consolidation": "claude-3-5-sonnet-20241022",
        "github_content": "gpt-4o"
    })
    
    # Custom prompt templates
    custom_prompts: Dict[str, str] = field(default_factory=dict)
    
    # GitHub configuration (optional)
    github: Dict[str, Any] = field(default_factory=dict)
    
    # PE-specific configurations (optional)
    sources: Dict[str, Any] = field(default_factory=dict)
    thesis_preferences: Dict[str, Any] = field(default_factory=dict)
    enrichment: Dict[str, Any] = field(default_factory=dict)
    synthesis: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'FlavorConfig':
        """Load flavor configuration from YAML file."""
        try:
            with open(yaml_path, 'r') as f:
                data = yaml.safe_load(f)
            
            # Handle current_prompts field (top-level in YAML)
            current_prompts = data.pop('current_prompts', {})
            
            # Convert string enums back to enum objects
            if 'framework' in data and 'framework_type' in data['framework']:
                data['framework']['framework_type'] = FrameworkType(data['framework']['framework_type'])
            
            if 'output' in data and 'schema_type' in data['output']:
                data['output']['schema_type'] = OutputSchema(data['output']['schema_type'])
            
            # Reconstruct nested dataclasses
            if 'reddit_strategy' in data:
                data['reddit_strategy'] = RedditSearchStrategy(**data['reddit_strategy'])
            
            if 'framework' in data:
                # Handle clustering config within framework
                framework_data = data['framework']
                if 'clustering' in framework_data:
                    framework_data['clustering'] = ClusteringConfig(**framework_data['clustering'])
                data['framework'] = FrameworkConfig(**framework_data)
            
            if 'output' in data:
                data['output'] = OutputConfig(**data['output'])
            
            # Handle top-level clustering config
            if 'clustering' in data:
                data['clustering'] = ClusteringConfig(**data['clustering'])
            
            # Create the flavor config
            flavor = cls(**data)
            
            # Add current_prompts as an attribute
            flavor.current_prompts = current_prompts
            
            return flavor
            
        except Exception as e:
            logger.error(f"Failed to load flavor config from {yaml_path}: {e}")
            raise
    
    def to_yaml(self, yaml_path: str):
        """Save flavor configuration to YAML file."""
        try:
            # Convert to dict and handle enums
            data = self.__dict__.copy()
            
            # Convert enums to string values
            if isinstance(data['framework'].framework_type, FrameworkType):
                data['framework'].framework_type = data['framework'].framework_type.value
            
            if isinstance(data['output'].schema_type, OutputSchema):
                data['output'].schema_type = data['output'].schema_type.value
            
            # Convert dataclasses to dicts
            data['reddit_strategy'] = data['reddit_strategy'].__dict__
            
            # Handle nested clustering config
            framework_dict = data['framework'].__dict__.copy()
            if hasattr(data['framework'], 'clustering') and data['framework'].clustering:
                framework_dict['clustering'] = data['framework'].clustering.__dict__
            data['framework'] = framework_dict
            
            data['output'] = data['output'].__dict__
            
            # Handle top-level clustering
            if data.get('clustering'):
                data['clustering'] = data['clustering'].__dict__
            
            os.makedirs(os.path.dirname(yaml_path), exist_ok=True)
            with open(yaml_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2)
                
            logger.info(f"Flavor config saved to {yaml_path}")
            
        except Exception as e:
            logger.error(f"Failed to save flavor config to {yaml_path}: {e}")
            raise
    
    def validate(self) -> List[str]:
        """Validate the flavor configuration and return any errors."""
        errors = []
        
        # Basic validation
        if not self.name.strip():
            errors.append("Flavor name cannot be empty")
        
        if not self.description.strip():
            errors.append("Flavor description cannot be empty")
        
        # Framework validation
        if self.framework.framework_type == FrameworkType.CUSTOM:
            if not self.framework.custom_prompts:
                errors.append("Custom framework requires custom_prompts to be defined")
        
        # Reddit strategy validation - check either subreddit_selection, fallback_subreddits, or subreddit_discovery_prompt
        has_subreddits = (self.reddit_strategy.subreddit_selection or 
                         self.reddit_strategy.fallback_subreddits or
                         self.reddit_strategy.subreddit_discovery_prompt)
        if not has_subreddits:
            errors.append("At least one subreddit source must be specified (subreddit_selection, fallback_subreddits, or subreddit_discovery_prompt)")
        
        if self.reddit_strategy.max_posts_per_keyword < 1:
            errors.append("max_posts_per_keyword must be at least 1")
        
        # Output validation
        if not self.output.required_fields:
            errors.append("At least one required output field must be specified")
        
        return errors

class FlavorRegistry:
    """Registry for managing available flavor configurations."""
    
    def __init__(self, flavors_dir: str = "flavors"):
        self.flavors_dir = flavors_dir
        self._flavors: Dict[str, FlavorConfig] = {}
        self.load_all_flavors()
    
    def load_all_flavors(self):
        """Load all flavor configurations from the flavors directory."""
        if not os.path.exists(self.flavors_dir):
            logger.warning(f"Flavors directory {self.flavors_dir} does not exist")
            return
        
        for file in os.listdir(self.flavors_dir):
            if file.endswith('.yaml') or file.endswith('.yml'):
                try:
                    flavor_path = os.path.join(self.flavors_dir, file)
                    flavor = FlavorConfig.from_yaml(flavor_path)
                    
                    # Validate flavor
                    errors = flavor.validate()
                    if errors:
                        logger.error(f"Invalid flavor {file}: {errors}")
                        continue
                    
                    self._flavors[flavor.name] = flavor
                    logger.info(f"Loaded flavor: {flavor.name}")
                    
                except Exception as e:
                    logger.error(f"Failed to load flavor from {file}: {e}")
    
    def get_flavor(self, name: str) -> Optional[FlavorConfig]:
        """Get a flavor configuration by name."""
        return self._flavors.get(name)
    
    def list_flavors(self) -> List[str]:
        """List all available flavor names."""
        return list(self._flavors.keys())
    
    def register_flavor(self, flavor: FlavorConfig):
        """Register a new flavor configuration."""
        errors = flavor.validate()
        if errors:
            raise ValueError(f"Invalid flavor configuration: {errors}")
        
        self._flavors[flavor.name] = flavor
        logger.info(f"Registered flavor: {flavor.name}")