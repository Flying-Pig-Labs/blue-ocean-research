"""
Debug configuration for cost-effective model switching in DEBUG mode
"""

import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

try:
    import yaml
except ImportError:
    yaml = None

from ..models.logging_models import ModelProvider


class DebugModelMapping(str, Enum):
    """Debug model mapping strategies"""
    HAIKU_ONLY = "haiku_only"  # Use only Haiku for all operations
    SMART_MAPPING = "smart_mapping"  # Intelligent mapping based on task complexity
    TIER_BASED = "tier_based"  # Use tiered approach: haiku -> sonnet -> opus
    CUSTOM = "custom"  # Use custom mapping from config


@dataclass
class DebugLimits:
    """Debug mode limits and thresholds"""
    max_total_tokens: int = 50000  # Max tokens per session
    max_single_call_tokens: int = 1000  # Max tokens per API call
    max_cost_per_session: float = 5.0  # Max cost in USD per session
    max_api_calls: int = 100  # Max API calls per session
    token_warning_threshold: float = 0.8  # Warn at 80% of limits
    cost_warning_threshold: float = 0.8  # Warn at 80% of cost limit


@dataclass
class DebugModelMappings:
    """Model mappings for different operations in debug mode"""
    # Default mappings - production model -> debug model
    model_mappings: Dict[str, str] = None
    
    # Operation-specific mappings
    operation_mappings: Dict[str, str] = None
    
    # Fallback models for different providers
    fallback_models: Dict[ModelProvider, str] = None
    
    def __post_init__(self):
        if self.model_mappings is None:
            self.model_mappings = {
                # Anthropic mappings
                "claude-3-5-sonnet-20241022": "claude-3-haiku-20240307",
                "claude-3-opus-20240229": "claude-3-haiku-20240307",
                "claude-3-sonnet-20240229": "claude-3-haiku-20240307",
                
                # OpenAI mappings
                "gpt-4": "gpt-3.5-turbo",
                "gpt-4-turbo": "gpt-3.5-turbo",
                
                # Cohere mappings
                "command": "command-light"
            }
        
        if self.operation_mappings is None:
            self.operation_mappings = {
                # Simple operations use lightweight models
                "test": "claude-3-haiku-20240307",
                "validation": "claude-3-haiku-20240307",
                "simple_analysis": "claude-3-haiku-20240307",
                
                # Complex operations can use mid-tier models
                "complex_analysis": "claude-3-5-sonnet-20241022",
                "critical_operation": "claude-3-5-sonnet-20241022"
            }
        
        if self.fallback_models is None:
            self.fallback_models = {
                ModelProvider.ANTHROPIC: "claude-3-haiku-20240307",
                ModelProvider.OPENAI: "gpt-3.5-turbo",
                ModelProvider.COHERE: "command-light"
            }


class DebugConfig:
    """
    Debug configuration class for cost-effective model switching
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize debug configuration"""
        self.enabled = self._is_debug_mode()
        self.limits = DebugLimits()
        self.mappings = DebugModelMappings()
        self.mapping_strategy = DebugModelMapping.SMART_MAPPING
        
        # Cost tracking
        self.session_cost = 0.0
        self.session_tokens = 0
        self.session_api_calls = 0
        
        # Configuration file path
        self.config_file = config_file or self._find_config_file()
        
        # Load configuration if file exists
        if self.config_file and Path(self.config_file).exists():
            self._load_config()
    
    def _is_debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        debug_env = os.getenv("DEBUG", "").lower()
        return debug_env in ["true", "1", "yes", "on"]
    
    def _find_config_file(self) -> Optional[str]:
        """Find debug configuration file"""
        possible_paths = [
            "debug_config.yaml",
            "debug_config.yml",
            ".debug_config.yaml",
            os.path.expanduser("~/.helios/debug_config.yaml")
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                return path
        return None
    
    def _load_config(self):
        """Load configuration from YAML file"""
        if yaml is None:
            print(f"Warning: PyYAML not installed. Cannot load debug config from {self.config_file}")
            return
        
        try:
            with open(self.config_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Load limits
            if 'limits' in config_data:
                limits_data = config_data['limits']
                for key, value in limits_data.items():
                    if hasattr(self.limits, key):
                        setattr(self.limits, key, value)
            
            # Load model mappings
            if 'model_mappings' in config_data:
                self.mappings.model_mappings.update(config_data['model_mappings'])
            
            # Load operation mappings
            if 'operation_mappings' in config_data:
                self.mappings.operation_mappings.update(config_data['operation_mappings'])
            
            # Load mapping strategy
            if 'mapping_strategy' in config_data:
                self.mapping_strategy = DebugModelMapping(config_data['mapping_strategy'])
            
        except Exception as e:
            print(f"Warning: Failed to load debug config from {self.config_file}: {e}")
    
    def get_debug_model(self, production_model: str, operation: Optional[str] = None) -> str:
        """
        Get the debug model for a given production model and operation
        
        Args:
            production_model: The production model name
            operation: Optional operation context for smarter mapping
            
        Returns:
            Debug model name to use instead
        """
        if not self.enabled:
            return production_model
        
        # Check operation-specific mapping first
        if operation and operation in self.mappings.operation_mappings:
            return self.mappings.operation_mappings[operation]
        
        # Apply mapping strategy
        if self.mapping_strategy == DebugModelMapping.HAIKU_ONLY:
            return "claude-3-haiku-20240307"
        
        elif self.mapping_strategy == DebugModelMapping.SMART_MAPPING:
            return self._smart_model_mapping(production_model, operation)
        
        elif self.mapping_strategy == DebugModelMapping.TIER_BASED:
            return self._tier_based_mapping(production_model)
        
        else:  # CUSTOM or fallback to direct mapping
            return self.mappings.model_mappings.get(production_model, production_model)
    
    def _smart_model_mapping(self, production_model: str, operation: Optional[str] = None) -> str:
        """Smart mapping based on model capabilities and operation context"""
        # For simple operations or when approaching limits, use Haiku
        if (operation and any(keyword in operation.lower() for keyword in 
                             ['test', 'simple', 'validate', 'quick', 'check']) or
            self.is_approaching_limits()):
            return "claude-3-haiku-20240307"
        
        # For complex operations with budget remaining, allow mid-tier
        if operation and any(keyword in operation.lower() for keyword in 
                           ['complex', 'detailed', 'comprehensive', 'analysis']):
            if self.session_cost < self.limits.max_cost_per_session * 0.5:
                return "claude-3-5-sonnet-20241022"
            else:
                return "claude-3-haiku-20240307"
        
        # Default mapping
        return self.mappings.model_mappings.get(production_model, "claude-3-haiku-20240307")
    
    def _tier_based_mapping(self, production_model: str) -> str:
        """Tier-based mapping with escalation based on session progress"""
        progress = self.session_cost / self.limits.max_cost_per_session
        
        if progress < 0.3:  # Early in session, can use sonnet
            if production_model in ["claude-3-opus-20240229"]:
                return "claude-3-5-sonnet-20241022"
            elif production_model in ["claude-3-5-sonnet-20241022", "claude-3-sonnet-20240229"]:
                return "claude-3-5-sonnet-20241022"
            else:
                return "claude-3-haiku-20240307"
        
        elif progress < 0.7:  # Mid session, prefer haiku but allow sonnet for critical
            return "claude-3-haiku-20240307"
        
        else:  # Late in session, haiku only
            return "claude-3-haiku-20240307"
    
    def is_approaching_limits(self, threshold: float = 0.8) -> bool:
        """Check if we're approaching any limits"""
        return (
            self.session_cost >= self.limits.max_cost_per_session * threshold or
            self.session_tokens >= self.limits.max_total_tokens * threshold or
            self.session_api_calls >= self.limits.max_api_calls * threshold
        )
    
    def check_limits_before_call(self, estimated_tokens: int = 0, estimated_cost: float = 0.0) -> bool:
        """
        Check if a call would exceed limits
        
        Returns:
            True if call is within limits, False if it would exceed them
        """
        if not self.enabled:
            return True
        
        # Check token limits
        if self.session_tokens + estimated_tokens > self.limits.max_total_tokens:
            return False
        
        # Check cost limits
        if self.session_cost + estimated_cost > self.limits.max_cost_per_session:
            return False
        
        # Check API call limits
        if self.session_api_calls + 1 > self.limits.max_api_calls:
            return False
        
        # Check single call token limit
        if estimated_tokens > self.limits.max_single_call_tokens:
            return False
        
        return True
    
    def should_warn_about_limits(self) -> Dict[str, bool]:
        """Check which limits are approaching warning thresholds"""
        warnings = {}
        
        if not self.enabled:
            return warnings
        
        # Cost warning
        cost_ratio = self.session_cost / self.limits.max_cost_per_session
        warnings['cost'] = cost_ratio >= self.limits.cost_warning_threshold
        
        # Token warning
        token_ratio = self.session_tokens / self.limits.max_total_tokens
        warnings['tokens'] = token_ratio >= self.limits.token_warning_threshold
        
        # API calls warning
        call_ratio = self.session_api_calls / self.limits.max_api_calls
        warnings['api_calls'] = call_ratio >= self.limits.token_warning_threshold
        
        return warnings
    
    def update_session_stats(self, tokens_used: int, cost_incurred: float):
        """Update session statistics"""
        if self.enabled:
            self.session_tokens += tokens_used
            self.session_cost += cost_incurred
            self.session_api_calls += 1
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics"""
        return {
            "enabled": self.enabled,
            "session_cost": self.session_cost,
            "session_tokens": self.session_tokens,
            "session_api_calls": self.session_api_calls,
            "cost_limit": self.limits.max_cost_per_session,
            "token_limit": self.limits.max_total_tokens,
            "api_call_limit": self.limits.max_api_calls,
            "cost_remaining": max(0, self.limits.max_cost_per_session - self.session_cost),
            "tokens_remaining": max(0, self.limits.max_total_tokens - self.session_tokens),
            "api_calls_remaining": max(0, self.limits.max_api_calls - self.session_api_calls),
            "cost_percentage": (self.session_cost / self.limits.max_cost_per_session) * 100,
            "token_percentage": (self.session_tokens / self.limits.max_total_tokens) * 100,
            "api_call_percentage": (self.session_api_calls / self.limits.max_api_calls) * 100
        }
    
    def reset_session(self):
        """Reset session statistics"""
        self.session_cost = 0.0
        self.session_tokens = 0
        self.session_api_calls = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization"""
        return {
            "enabled": self.enabled,
            "mapping_strategy": self.mapping_strategy.value,
            "limits": {
                "max_total_tokens": self.limits.max_total_tokens,
                "max_single_call_tokens": self.limits.max_single_call_tokens,
                "max_cost_per_session": self.limits.max_cost_per_session,
                "max_api_calls": self.limits.max_api_calls,
                "token_warning_threshold": self.limits.token_warning_threshold,
                "cost_warning_threshold": self.limits.cost_warning_threshold
            },
            "model_mappings": self.mappings.model_mappings,
            "operation_mappings": self.mappings.operation_mappings,
            "session_stats": self.get_session_stats()
        }


# Global debug config instance
_debug_config: Optional[DebugConfig] = None


def get_debug_config() -> DebugConfig:
    """Get the global debug configuration instance"""
    global _debug_config
    if _debug_config is None:
        _debug_config = DebugConfig()
    return _debug_config


def initialize_debug_config(config_file: Optional[str] = None) -> DebugConfig:
    """Initialize the global debug configuration"""
    global _debug_config
    _debug_config = DebugConfig(config_file)
    return _debug_config


def is_debug_mode() -> bool:
    """Quick check if debug mode is enabled"""
    return get_debug_config().enabled