#!/usr/bin/env python3
"""
Config Loader - Single source of truth for all LLM configurations.
All scripts should import and use this module to get model settings and prompts.
"""

import yaml
import os
from typing import Dict, Any, Optional

class ConfigLoader:
    """Load and manage LLM configurations from llm_config.yaml"""
    
    def __init__(self, config_path: str = "llm_config.yaml"):
        """Initialize the config loader with the YAML file."""
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load the YAML configuration file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def get_model_config(self, stage: str, task: str) -> Dict[str, Any]:
        """
        Get model configuration for a specific stage and task.
        
        Args:
            stage: The pipeline stage (e.g., 'research_analysis', 'jtbd_synthesis')
            task: The specific task within the stage (e.g., 'verticals', 'personas')
        
        Returns:
            Dictionary containing model settings and prompt
        """
        try:
            if '.' in stage:  # Handle nested paths like 'product_ideas.generation'
                parts = stage.split('.')
                config = self.config['models']
                for part in parts:
                    config = config[part]
                return config.get(task, config)
            else:
                return self.config['models'][stage].get(task, self.config['models'][stage])
        except KeyError:
            raise ValueError(f"Configuration not found for stage: {stage}, task: {task}")
    
    def get_prompt(self, stage: str, task: Optional[str] = None) -> str:
        """
        Get the prompt template for a specific stage and task.
        
        Args:
            stage: The pipeline stage
            task: Optional task within the stage
        
        Returns:
            The prompt template string
        """
        config = self.get_model_config(stage, task) if task else self.config['models'][stage]
        return config.get('prompt', '')
    
    def get_model_settings(self, stage: str, task: Optional[str] = None) -> Dict[str, Any]:
        """
        Get just the model settings (without prompt) for a stage/task.
        
        Returns:
            Dictionary with provider, model, temperature, max_tokens, etc.
        """
        config = self.get_model_config(stage, task) if task else self.config['models'][stage]
        return {
            'provider': config.get('provider'),
            'model': config.get('model'),
            'temperature': config.get('temperature', 0.7),
            'max_tokens': config.get('max_tokens', 2000),
            'system_prompt': config.get('system_prompt', None),
            'max_completion_tokens': config.get('max_completion_tokens', None)  # For o1 models
        }
    
    def get_search_config(self, provider: str = 'exa') -> Dict[str, Any]:
        """Get search provider configuration."""
        return self.config.get('search', {}).get(provider, {})
    
    def get_pipeline_config(self, stage_name: str) -> Dict[str, Any]:
        """Get pipeline stage configuration including inputs and outputs."""
        stages = self.config.get('pipeline', {}).get('stages', {})
        return stages.get(stage_name, {})
    
    def get_optimization_settings(self) -> Dict[str, Any]:
        """Get optimization settings for the pipeline."""
        return self.config.get('optimization', {})
    
    def get_rate_limits(self, provider: str) -> Dict[str, Any]:
        """Get rate limiting configuration for a provider."""
        return self.config.get('rate_limits', {}).get(provider, {})
    
    def has_example(self, stage: str, task: Optional[str] = None) -> bool:
        """Check if examples are enabled for a stage/task."""
        config = self.get_model_config(stage, task) if task else self.config['models'][stage]
        return config.get('include_example', True) and bool(config.get('example', ''))
    
    def get_example(self, stage: str, task: Optional[str] = None) -> str:
        """Get the example text for a stage/task."""
        config = self.get_model_config(stage, task) if task else self.config['models'][stage]
        return config.get('example', '') if config.get('include_example', True) else ''
    
    def format_prompt(self, stage: str, task: Optional[str] = None, **kwargs) -> str:
        """
        Format a prompt template with provided variables and optionally inject examples.
        
        Args:
            stage: The pipeline stage
            task: Optional task within the stage
            **kwargs: Variables to inject into the prompt template
        
        Returns:
            Formatted prompt string with example injected if appropriate
        """
        config = self.get_model_config(stage, task) if task else self.config['models'][stage]
        prompt_template = config.get('prompt', '')
        
        # Check if we should include examples
        include_example = config.get('include_example', True)  # Default to True
        example_text = config.get('example', '') if include_example else ''
        
        # Add example to kwargs for template formatting
        kwargs['example'] = example_text
        
        return prompt_template.format(**kwargs)


# Singleton instance for easy import
config = ConfigLoader()


# Helper functions for backward compatibility
def get_model_config(stage: str, task: str = None) -> Dict[str, Any]:
    """Get model configuration for a stage/task."""
    return config.get_model_config(stage, task) if task else config.config['models'][stage]


def get_prompt(stage: str, task: str = None) -> str:
    """Get prompt template for a stage/task."""
    return config.get_prompt(stage, task)


def format_prompt(stage: str, task: str = None, **kwargs) -> str:
    """Format a prompt with variables."""
    return config.format_prompt(stage, task, **kwargs)


# Example usage in scripts:
if __name__ == "__main__":
    # Test the config loader
    config = ConfigLoader()
    
    # Get Stage 1 pain points configuration
    pain_config = config.get_model_config('research_analysis', 'pain_points')
    print(f"Pain Points Model: {pain_config['model']}")
    print(f"Temperature: {pain_config['temperature']}")
    print(f"Include Example: {pain_config.get('include_example', True)}")
    
    # Check if examples are available
    has_example = config.has_example('research_analysis', 'verticals')
    print(f"\nVerticals has example: {has_example}")
    
    # Get and format a prompt with example injection
    prompt = config.format_prompt(
        'research_analysis', 
        'verticals',
        research_content="[Sample research document here]"
    )
    print(f"\nFormatted Prompt Preview:\n{prompt[:300]}...")
    
    # Example without example injection (pain_points has include_example: false)
    prompt_no_example = config.format_prompt(
        'research_analysis',
        'pain_points', 
        research_content="[Sample research document here]"
    )
    print(f"\nPrompt without example (first 200 chars):\n{prompt_no_example[:200]}...")
    
    # Get optimization settings
    opt_settings = config.get_optimization_settings()
    print(f"\nParallel Calls: {opt_settings.get('parallel_calls', 4)}")