"""
Feature flag system for safe flavor deployment and rollout management.
Supports gradual rollout, A/B testing, and emergency rollback capabilities.
"""

import os
import json
import logging
import hashlib
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timezone

@dataclass
class FeatureFlag:
    """Configuration for a feature flag."""
    name: str
    enabled: bool
    rollout_percentage: float  # 0.0 to 100.0
    conditions: Dict[str, Any]  # Additional conditions (user_id, environment, etc.)
    created_at: str
    updated_at: str
    description: str

@dataclass
class RolloutConfig:
    """Configuration for gradual rollout strategy."""
    initial_percentage: float = 5.0
    increment_percentage: float = 10.0
    increment_interval_hours: int = 24
    max_percentage: float = 100.0
    health_check_threshold: float = 95.0  # Success rate required to continue rollout

class FeatureFlagManager:
    """Manages feature flags for safe deployment and rollout."""
    
    def __init__(self, config_path: str = "flavors/feature_flags.json"):
        self.config_path = Path(config_path)
        self.flags: Dict[str, FeatureFlag] = {}
        self.logger = logging.getLogger(__name__)
        self._load_flags()
    
    def _load_flags(self):
        """Load feature flags from configuration file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    self.flags = {
                        name: FeatureFlag(**flag_data)
                        for name, flag_data in data.items()
                    }
                self.logger.info(f"Loaded {len(self.flags)} feature flags")
            else:
                self.logger.info("No feature flags configuration found, starting with empty set")
        except Exception as e:
            self.logger.error(f"Error loading feature flags: {e}")
            self.flags = {}
    
    def _save_flags(self):
        """Save feature flags to configuration file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(
                    {name: asdict(flag) for name, flag in self.flags.items()},
                    f,
                    indent=2
                )
            self.logger.info("Feature flags saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving feature flags: {e}")
    
    def create_flag(self, name: str, enabled: bool = False, 
                   rollout_percentage: float = 0.0, 
                   conditions: Optional[Dict[str, Any]] = None,
                   description: str = ""):
        """Create a new feature flag."""
        now = datetime.now(timezone.utc).isoformat()
        
        flag = FeatureFlag(
            name=name,
            enabled=enabled,
            rollout_percentage=rollout_percentage,
            conditions=conditions or {},
            created_at=now,
            updated_at=now,
            description=description
        )
        
        self.flags[name] = flag
        self._save_flags()
        self.logger.info(f"Created feature flag: {name}")
        return flag
    
    def update_flag(self, name: str, **updates):
        """Update an existing feature flag."""
        if name not in self.flags:
            raise ValueError(f"Feature flag '{name}' not found")
        
        flag = self.flags[name]
        for key, value in updates.items():
            if hasattr(flag, key):
                setattr(flag, key, value)
        
        flag.updated_at = datetime.now(timezone.utc).isoformat()
        self._save_flags()
        self.logger.info(f"Updated feature flag: {name}")
        return flag
    
    def is_enabled(self, flag_name: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if a feature flag is enabled for the given context."""
        if flag_name not in self.flags:
            self.logger.warning(f"Feature flag '{flag_name}' not found, defaulting to False")
            return False
        
        flag = self.flags[flag_name]
        
        # Check if flag is globally disabled
        if not flag.enabled:
            return False
        
        # Check rollout percentage
        if flag.rollout_percentage < 100.0:
            # Use deterministic hash-based selection
            context_str = json.dumps(context or {}, sort_keys=True)
            hash_input = f"{flag_name}:{context_str}"
            hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
            percentage = (hash_value % 10000) / 100.0  # 0.00 to 99.99
            
            if percentage >= flag.rollout_percentage:
                return False
        
        # Check additional conditions
        if flag.conditions and context:
            for condition_key, condition_value in flag.conditions.items():
                if context.get(condition_key) != condition_value:
                    return False
        
        return True
    
    def get_flag_status(self, flag_name: str) -> Optional[FeatureFlag]:
        """Get the status of a specific feature flag."""
        return self.flags.get(flag_name)
    
    def list_flags(self) -> Dict[str, FeatureFlag]:
        """List all feature flags."""
        return self.flags.copy()
    
    def gradual_rollout(self, flag_name: str, config: RolloutConfig):
        """Implement gradual rollout strategy for a feature flag."""
        if flag_name not in self.flags:
            raise ValueError(f"Feature flag '{flag_name}' not found")
        
        flag = self.flags[flag_name]
        current_percentage = flag.rollout_percentage
        
        if current_percentage >= config.max_percentage:
            self.logger.info(f"Rollout complete for {flag_name} at {current_percentage}%")
            return
        
        # Calculate next percentage
        next_percentage = min(
            current_percentage + config.increment_percentage,
            config.max_percentage
        )
        
        # Update rollout percentage
        self.update_flag(flag_name, rollout_percentage=next_percentage)
        
        self.logger.info(
            f"Increased rollout for {flag_name} from {current_percentage}% to {next_percentage}%"
        )
    
    def emergency_rollback(self, flag_name: str):
        """Emergency rollback - immediately disable a feature flag."""
        if flag_name not in self.flags:
            raise ValueError(f"Feature flag '{flag_name}' not found")
        
        self.update_flag(flag_name, enabled=False, rollout_percentage=0.0)
        self.logger.warning(f"Emergency rollback executed for {flag_name}")
    
    def canary_deployment(self, flag_name: str, canary_percentage: float = 1.0,
                         canary_conditions: Optional[Dict[str, Any]] = None):
        """Set up canary deployment for a feature flag."""
        if flag_name not in self.flags:
            raise ValueError(f"Feature flag '{flag_name}' not found")
        
        self.update_flag(
            flag_name,
            enabled=True,
            rollout_percentage=canary_percentage,
            conditions=canary_conditions or {}
        )
        
        self.logger.info(f"Canary deployment started for {flag_name} at {canary_percentage}%")

class FlavorFeatureFlags:
    """Feature flags specifically for flavor system rollout."""
    
    # Flag names
    MODULAR_PIPELINE_ENABLED = "modular_pipeline_enabled"
    SHADOW_RUN_ENABLED = "shadow_run_enabled"
    NEW_KEYWORD_STRATEGY = "new_keyword_strategy_enabled"
    FRAMEWORK_ADAPTERS = "framework_adapters_enabled"
    GITHUB_WRITER_V2 = "github_writer_v2_enabled"
    QA_GUARDRAILS = "qa_guardrails_enabled"
    
    def __init__(self, manager: FeatureFlagManager):
        self.manager = manager
        self._initialize_flags()
    
    def _initialize_flags(self):
        """Initialize flavor-specific feature flags if they don't exist."""
        flags_to_create = [
            (self.MODULAR_PIPELINE_ENABLED, "Enable modular pipeline system"),
            (self.SHADOW_RUN_ENABLED, "Enable shadow run testing alongside original pipeline"),
            (self.NEW_KEYWORD_STRATEGY, "Enable new keyword strategy engine"),
            (self.FRAMEWORK_ADAPTERS, "Enable pluggable framework adapters"),
            (self.GITHUB_WRITER_V2, "Enable new GitHub writer with idempotent operations"),
            (self.QA_GUARDRAILS, "Enable QA guardrails and validation system"),
        ]
        
        for flag_name, description in flags_to_create:
            if flag_name not in self.manager.flags:
                self.manager.create_flag(
                    name=flag_name,
                    enabled=False,
                    rollout_percentage=0.0,
                    description=description
                )
    
    def should_use_modular_pipeline(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if modular pipeline should be used."""
        return self.manager.is_enabled(self.MODULAR_PIPELINE_ENABLED, context)
    
    def should_run_shadow_test(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if shadow run testing should be enabled."""
        return self.manager.is_enabled(self.SHADOW_RUN_ENABLED, context)
    
    def should_use_new_keyword_strategy(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if new keyword strategy should be used."""
        return self.manager.is_enabled(self.NEW_KEYWORD_STRATEGY, context)
    
    def should_use_framework_adapters(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if framework adapters should be used."""
        return self.manager.is_enabled(self.FRAMEWORK_ADAPTERS, context)
    
    def should_use_github_writer_v2(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if new GitHub writer should be used."""
        return self.manager.is_enabled(self.GITHUB_WRITER_V2, context)
    
    def should_use_qa_guardrails(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if QA guardrails should be used."""
        return self.manager.is_enabled(self.QA_GUARDRAILS, context)

# Global feature flag manager instance
_feature_flag_manager = None

def get_feature_flag_manager() -> FeatureFlagManager:
    """Get global feature flag manager instance."""
    global _feature_flag_manager
    if _feature_flag_manager is None:
        _feature_flag_manager = FeatureFlagManager()
    return _feature_flag_manager

def get_flavor_flags() -> FlavorFeatureFlags:
    """Get flavor-specific feature flags."""
    return FlavorFeatureFlags(get_feature_flag_manager())