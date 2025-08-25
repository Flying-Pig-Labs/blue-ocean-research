"""
User Configuration Manager for Pipeline V2

Handles user preferences for market focus, strategic priorities, and risk appetite.
Provides smart defaults and validation for UI-driven configuration.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json
from pathlib import Path


@dataclass
class UserConfig:
    """User configuration for pipeline customization."""
    
    # Core business configuration (what users actually understand)
    market_focus: str = "general"  # b2b_saas, fintech, healthtech, etc.
    strategic_priority: str = "balanced"  # innovation_first, market_fit_first, feasibility_first
    risk_appetite: str = "balanced"  # conservative, balanced, breakthrough
    
    # Optional advanced configuration
    target_subreddits: Optional[List[str]] = None  # Override default subreddits
    portfolio_size_preference: Optional[int] = None  # Override default 10 ideas
    industry_focus: Optional[List[str]] = None  # Specific industries to emphasize
    
    # UI state (not used by pipeline, but stored for UI persistence)
    ui_preferences: Optional[Dict[str, Any]] = None


class UserConfigManager:
    """
    Manages user configuration with smart defaults and validation.
    
    This class handles the business logic of translating user preferences
    into pipeline-compatible configuration parameters.
    """
    
    # Valid configuration options
    VALID_MARKET_FOCUS = [
        "general", "b2b_saas", "fintech", "healthtech", "edtech", 
        "real_estate", "consumer", "enterprise", "startup"
    ]
    
    VALID_STRATEGIC_PRIORITIES = [
        "innovation_first", "market_fit_first", "feasibility_first", "balanced"
    ]
    
    VALID_RISK_APPETITES = [
        "conservative", "balanced", "breakthrough"
    ]
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize user configuration manager.
        
        Args:
            config_dict: Raw configuration dictionary from UI or file
        """
        self.config = self._build_config(config_dict or {})
        
    def _build_config(self, config_dict: Dict[str, Any]) -> UserConfig:
        """Build and validate user configuration."""
        
        # Extract and validate core configuration
        market_focus = self._validate_choice(
            config_dict.get("market_focus", "general"),
            self.VALID_MARKET_FOCUS,
            "general"
        )
        
        strategic_priority = self._validate_choice(
            config_dict.get("strategic_priority", "balanced"),
            self.VALID_STRATEGIC_PRIORITIES, 
            "balanced"
        )
        
        risk_appetite = self._validate_choice(
            config_dict.get("risk_appetite", "balanced"),
            self.VALID_RISK_APPETITES,
            "balanced"
        )
        
        # Build configuration
        return UserConfig(
            market_focus=market_focus,
            strategic_priority=strategic_priority,
            risk_appetite=risk_appetite,
            target_subreddits=config_dict.get("target_subreddits"),
            portfolio_size_preference=config_dict.get("portfolio_size_preference"),
            industry_focus=config_dict.get("industry_focus"),
            ui_preferences=config_dict.get("ui_preferences", {})
        )
    
    def _validate_choice(self, value: str, valid_options: List[str], default: str) -> str:
        """Validate configuration choice with fallback to default."""
        return value if value in valid_options else default
    
    def get_summary(self) -> str:
        """Get human-readable configuration summary."""
        return (
            f"Market: {self.config.market_focus}, "
            f"Priority: {self.config.strategic_priority}, " 
            f"Risk: {self.config.risk_appetite}"
        )
    
    def get_market_subreddits(self) -> List[str]:
        """Get relevant subreddits based on market focus."""
        
        # Use user-specified subreddits if provided
        if self.config.target_subreddits:
            return self.config.target_subreddits
            
        # Market-specific subreddit mapping
        market_subreddit_map = {
            'b2b_saas': [
                'entrepreneur', 'startups', 'smallbusiness', 'SaaS', 
                'business', 'marketing', 'sales'
            ],
            'fintech': [
                'personalfinance', 'investing', 'financialindependence',
                'CreditCards', 'SecurityCareerAdvice', 'SecurityAnalysis'
            ],
            'healthtech': [
                'health', 'medicine', 'healthcare', 'fitness', 'nutrition',
                'mentalhealth', 'AskDocs'
            ],
            'edtech': [
                'education', 'teachers', 'students', 'online_learning',
                'homeschool', 'AskAcademia', 'college'
            ],
            'real_estate': [
                'realestate', 'realestateinvesting', 'firsttimehomebuyer', 
                'RealEstate', 'landlord', 'investing'
            ],
            'consumer': [
                'buyitforlife', 'frugal', 'anticonsumption', 'products',
                'reviews', 'gadgets', 'HomeImprovement'
            ],
            'enterprise': [
                'business', 'entrepreneur', 'smallbusiness', 'consulting',
                'ProjectManagement', 'sysadmin', 'ITCareerQuestions'
            ],
            'startup': [
                'startups', 'entrepreneur', 'smallbusiness', 'YCombinator',
                'business', 'SideProject', 'juststart'
            ],
            'general': [
                'entrepreneur', 'smallbusiness', 'startups', 'business',
                'personalfinance', 'frugal', 'productivity'
            ]
        }
        
        return market_subreddit_map.get(
            self.config.market_focus, 
            market_subreddit_map['general']
        )
    
    def get_strategic_weights(self) -> Dict[str, float]:
        """Get scoring weights based on strategic priority."""
        
        priority_weight_map = {
            'innovation_first': {
                'innovation_score': 0.45,
                'market_viability': 0.30,
                'technical_feasibility': 0.25,
                'competitive_differentiation': 0.40,
                'time_to_market': 0.20
            },
            'market_fit_first': {
                'market_viability': 0.50,
                'innovation_score': 0.25,
                'technical_feasibility': 0.25,
                'customer_validation': 0.45,
                'revenue_potential': 0.35
            },
            'feasibility_first': {
                'technical_feasibility': 0.45,
                'market_viability': 0.30,
                'innovation_score': 0.25,
                'implementation_complexity': 0.40,
                'resource_requirements': 0.35
            },
            'balanced': {
                'innovation_score': 0.33,
                'market_viability': 0.34,
                'technical_feasibility': 0.33,
                'balanced_approach': 0.40
            }
        }
        
        return priority_weight_map.get(
            self.config.strategic_priority,
            priority_weight_map['balanced']
        )
    
    def get_risk_parameters(self) -> Dict[str, Any]:
        """Get risk and filtering parameters based on risk appetite."""
        
        risk_param_map = {
            'conservative': {
                'excellence_threshold': 7.0,
                'breakthrough_weight': 0.10,
                'moonshot_preservation': 0.05,
                'safety_first': True,
                'prefer_proven_models': True,
                'min_market_validation': 0.7
            },
            'balanced': {
                'excellence_threshold': 6.5,
                'breakthrough_weight': 0.25,
                'moonshot_preservation': 0.15,
                'balanced_portfolio': True,
                'mix_incremental_breakthrough': True,
                'min_market_validation': 0.5
            },
            'breakthrough': {
                'excellence_threshold': 6.0,
                'breakthrough_weight': 0.40,
                'moonshot_preservation': 0.30,
                'innovation_focused': True,
                'embrace_uncertainty': True,
                'min_market_validation': 0.3
            }
        }
        
        return risk_param_map.get(
            self.config.risk_appetite,
            risk_param_map['balanced']
        )
    
    def get_portfolio_preferences(self) -> Dict[str, Any]:
        """Get portfolio composition preferences."""
        
        return {
            'target_size': self.config.portfolio_size_preference or 10,
            'diversity_requirements': self._get_diversity_requirements(),
            'industry_focus': self.config.industry_focus or [],
            'strategic_themes': self._get_strategic_themes()
        }
    
    def _get_diversity_requirements(self) -> Dict[str, Any]:
        """Get diversity requirements based on configuration."""
        
        if self.config.risk_appetite == 'conservative':
            return {
                'min_incremental_ideas': 6,
                'max_moonshot_ideas': 2,
                'require_proven_markets': True
            }
        elif self.config.risk_appetite == 'breakthrough':
            return {
                'min_breakthrough_ideas': 4,
                'max_incremental_ideas': 4, 
                'encourage_unproven_markets': True
            }
        else:  # balanced
            return {
                'balanced_mix': True,
                'incremental_to_breakthrough_ratio': 0.6
            }
    
    def _get_strategic_themes(self) -> List[str]:
        """Get strategic themes based on configuration."""
        
        themes = []
        
        if self.config.strategic_priority == 'innovation_first':
            themes.extend(['disruption', 'emerging_tech', 'new_paradigms'])
        elif self.config.strategic_priority == 'market_fit_first':
            themes.extend(['customer_validation', 'proven_demand', 'scalability'])
        elif self.config.strategic_priority == 'feasibility_first':
            themes.extend(['low_complexity', 'available_resources', 'quick_wins'])
            
        return themes
    
    def save_to_file(self, filepath: str):
        """Save configuration to JSON file."""
        
        config_dict = asdict(self.config)
        
        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'UserConfigManager':
        """Load configuration from JSON file."""
        
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
            
        return cls(config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return asdict(self.config)