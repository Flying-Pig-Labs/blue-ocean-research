"""
Base class for debug-aware components with model switching and token limiting
"""

import os
import time
from typing import Optional, Dict, Any, Union
from abc import ABC, abstractmethod
from contextlib import contextmanager

from .debug_config import get_debug_config, DebugConfig
from .debug_logger import get_debug_logger, DebugLogger
from .debug_cost_tracker import get_debug_cost_tracker, DebugCostTracker
from ..models.logging_models import ComponentType, ModelProvider, calculate_api_cost


class DebugAwareComponent(ABC):
    """
    Base class for components that need debug-aware model switching and cost tracking
    """
    
    def __init__(self, component_type: ComponentType, logger=None):
        """
        Initialize debug-aware component
        
        Args:
            component_type: The type of component for logging
            logger: Optional pipeline logger instance
        """
        self.component_type = component_type
        self.pipeline_logger = logger
        
        # Debug infrastructure
        self.debug_config = get_debug_config()
        self.debug_logger = get_debug_logger()
        self.cost_tracker = get_debug_cost_tracker()
        
        # Track if debug mode is enabled
        self.debug_enabled = self.debug_config.enabled
        
        if self.debug_enabled:
            self.debug_logger.log_component_init(component_type)
    
    def get_debug_model(self, production_model: str, operation: Optional[str] = None) -> str:
        """
        Get the appropriate model for the current context
        
        Args:
            production_model: The model that would be used in production
            operation: Optional operation context for smarter model selection
            
        Returns:
            Model name to actually use (debug or production)
        """
        if not self.debug_enabled:
            return production_model
        
        debug_model = self.debug_config.get_debug_model(production_model, operation)
        
        if debug_model != production_model:
            self.debug_logger.log_model_switch(
                production_model, debug_model, operation, self.component_type
            )
        
        return debug_model
    
    def check_token_limits(self, estimated_tokens: int, operation: str = "API call") -> bool:
        """
        Check if the operation would exceed token limits
        
        Args:
            estimated_tokens: Estimated tokens for the operation
            operation: Description of the operation
            
        Returns:
            True if within limits, False if would exceed
        """
        if not self.debug_enabled:
            return True
        
        # Estimate cost based on cheapest debug model (Haiku)
        estimated_cost = calculate_api_cost(
            ModelProvider.ANTHROPIC, 
            "claude-3-haiku-20240307", 
            estimated_tokens // 2,  # Rough split between input/output
            estimated_tokens // 2
        )
        
        within_limits = self.debug_config.check_limits_before_call(
            estimated_tokens, estimated_cost
        )
        
        if not within_limits:
            self.debug_logger.log_limit_exceeded(
                estimated_tokens, estimated_cost, operation, self.component_type
            )
            
            # Update cost tracker
            self.cost_tracker.record_blocked_call(
                operation, estimated_tokens, estimated_cost
            )
        
        return within_limits
    
    def should_warn_about_limits(self) -> bool:
        """Check if we should warn about approaching limits"""
        if not self.debug_enabled:
            return False
        
        warnings = self.debug_config.should_warn_about_limits()
        return any(warnings.values())
    
    def get_token_limit_for_operation(self, operation: str) -> int:
        """
        Get the token limit for a specific operation
        
        Args:
            operation: Operation name
            
        Returns:
            Token limit for this operation
        """
        if not self.debug_enabled:
            return 100000  # No limit in production mode
        
        # Use single call limit as base
        base_limit = self.debug_config.limits.max_single_call_tokens
        
        # Adjust based on operation type
        if any(keyword in operation.lower() for keyword in ['simple', 'quick', 'test']):
            return min(base_limit // 2, 500)
        elif any(keyword in operation.lower() for keyword in ['complex', 'detailed']):
            return base_limit
        else:
            return base_limit // 2
    
    @contextmanager
    def debug_api_call(self, model: str, operation: str, estimated_prompt_tokens: int = 0):
        """
        Context manager for debug-aware API calls
        
        Args:
            model: Model being used
            operation: Operation description
            estimated_prompt_tokens: Estimated input tokens
        """
        start_time = time.time()
        call_data = {
            "model": model,
            "operation": operation,
            "component": self.component_type,
            "start_time": start_time,
            "estimated_prompt_tokens": estimated_prompt_tokens
        }
        
        # Pre-call logging and checks
        if self.debug_enabled:
            self.debug_logger.log_api_call_start(
                model, operation, self.component_type, estimated_prompt_tokens
            )
        
        try:
            yield call_data
            
            # Post-call success handling
            duration = time.time() - start_time
            actual_prompt_tokens = call_data.get("actual_prompt_tokens", estimated_prompt_tokens)
            completion_tokens = call_data.get("completion_tokens", 0)
            total_tokens = actual_prompt_tokens + completion_tokens
            
            # Calculate cost
            provider = self._get_provider_from_model(model)
            cost = calculate_api_cost(provider, model, actual_prompt_tokens, completion_tokens)
            
            # Update debug stats
            if self.debug_enabled:
                self.debug_config.update_session_stats(total_tokens, cost)
                self.cost_tracker.record_api_call(
                    operation, model, actual_prompt_tokens, completion_tokens, cost, duration
                )
                self.debug_logger.log_api_call_success(
                    model, operation, self.component_type, total_tokens, cost, duration
                )
            
            # Log to pipeline logger if available
            if self.pipeline_logger:
                self.pipeline_logger.log_api_call(
                    self.component_type, provider, model,
                    actual_prompt_tokens, completion_tokens, duration,
                    success=True
                )
            
        except Exception as e:
            # Post-call error handling
            duration = time.time() - start_time
            error_msg = str(e)
            
            if self.debug_enabled:
                self.cost_tracker.record_failed_call(operation, error_msg)
                self.debug_logger.log_api_call_error(
                    model, operation, self.component_type, error_msg, duration
                )
            
            # Log to pipeline logger if available
            if self.pipeline_logger:
                provider = self._get_provider_from_model(model)
                self.pipeline_logger.log_api_call(
                    self.component_type, provider, model,
                    estimated_prompt_tokens, 0, duration,
                    success=False, error_message=error_msg
                )
            
            raise
    
    def _get_provider_from_model(self, model: str) -> ModelProvider:
        """Determine provider from model name"""
        if "claude" in model.lower():
            return ModelProvider.ANTHROPIC
        elif "gpt" in model.lower():
            return ModelProvider.OPENAI
        elif "command" in model.lower():
            return ModelProvider.COHERE
        else:
            return ModelProvider.ANTHROPIC  # Default fallback
    
    def truncate_content_for_debug(self, content: str, operation: str) -> str:
        """
        Truncate content based on debug token limits
        
        Args:
            content: Content to potentially truncate
            operation: Operation context
            
        Returns:
            Potentially truncated content
        """
        if not self.debug_enabled:
            return content
        
        # Rough token estimation (4 chars = 1 token)
        estimated_tokens = len(content) // 4
        token_limit = self.get_token_limit_for_operation(operation)
        
        # Reserve some tokens for the prompt and response
        content_token_limit = int(token_limit * 0.7)  # 70% for content
        
        if estimated_tokens > content_token_limit:
            # Calculate character limit
            char_limit = content_token_limit * 4
            truncated_content = content[:char_limit]
            
            self.debug_logger.log_content_truncation(
                original_length=len(content),
                truncated_length=len(truncated_content),
                operation=operation,
                component=self.component_type
            )
            
            return truncated_content + "\n\n[CONTENT TRUNCATED FOR DEBUG MODE]"
        
        return content
    
    def get_debug_summary(self) -> Dict[str, Any]:
        """Get debug summary for this component"""
        if not self.debug_enabled:
            return {"debug_mode": False}
        
        return {
            "debug_mode": True,
            "component_type": self.component_type.value,
            "session_stats": self.debug_config.get_session_stats(),
            "cost_tracker_summary": self.cost_tracker.get_summary(),
            "warnings": self.debug_config.should_warn_about_limits()
        }
    
    @abstractmethod
    def get_default_model(self) -> str:
        """
        Get the default production model for this component
        Must be implemented by subclasses
        """
        pass
    
    def should_skip_operation_for_debug(self, operation: str, estimated_cost: float = 0.0) -> bool:
        """
        Determine if an operation should be skipped in debug mode
        
        Args:
            operation: Operation description
            estimated_cost: Estimated cost of the operation
            
        Returns:
            True if operation should be skipped
        """
        if not self.debug_enabled:
            return False
        
        # Skip if it would exceed limits
        if not self.debug_config.check_limits_before_call(estimated_cost=estimated_cost):
            return True
        
        # Skip expensive operations if we're close to limits
        if (estimated_cost > 0.5 and  # High cost operation
            self.debug_config.is_approaching_limits(threshold=0.7)):  # Close to limits
            self.debug_logger.log_operation_skipped(
                operation, estimated_cost, self.component_type, "approaching_limits"
            )
            return True
        
        return False
    
    def create_debug_prompt_suffix(self) -> str:
        """Create a suffix to add to prompts in debug mode"""
        if not self.debug_enabled:
            return ""
        
        stats = self.debug_config.get_session_stats()
        return (
            f"\n\n[DEBUG MODE: Keep response concise. "
            f"Session tokens: {stats['session_tokens']}/{stats['token_limit']}, "
            f"Cost: ${stats['session_cost']:.3f}/${stats['cost_limit']:.2f}]"
        )


class DebugModelSwitcher:
    """
    Utility class for model switching logic
    """
    
    @staticmethod
    def switch_model_for_operation(
        component: DebugAwareComponent,
        base_model: str,
        operation: str,
        content_length: int = 0
    ) -> str:
        """
        Switch model based on operation characteristics
        
        Args:
            component: The debug-aware component
            base_model: Base model to potentially switch from
            operation: Operation being performed
            content_length: Length of content being processed
            
        Returns:
            Appropriate model for the operation
        """
        debug_config = component.debug_config
        
        if not debug_config.enabled:
            return base_model
        
        # Estimate tokens from content
        estimated_tokens = content_length // 4 if content_length > 0 else 500
        
        # Check if we can afford the base model
        provider = component._get_provider_from_model(base_model)
        estimated_cost = calculate_api_cost(
            provider, base_model, estimated_tokens // 2, estimated_tokens // 2
        )
        
        # If base model would exceed limits, force switch to cheaper option
        if not debug_config.check_limits_before_call(estimated_tokens, estimated_cost):
            cheaper_model = debug_config.get_debug_model(base_model, operation)
            return cheaper_model
        
        # Otherwise use normal debug model selection
        return debug_config.get_debug_model(base_model, operation)