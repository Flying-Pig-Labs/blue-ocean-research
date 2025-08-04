"""
Configuration settings for the Helios application
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class LoggingMode(str, Enum):
    """Logging output modes"""

    CONSOLE_ONLY = "console"
    FILE_ONLY = "file"
    BOTH = "both"
    DISABLED = "disabled"


@dataclass
class LoggingConfig:
    """Logging configuration settings"""

    # Output modes
    mode: LoggingMode = LoggingMode.BOTH
    console_level: str = "INFO"
    file_level: str = "DEBUG"

    # File settings
    log_dir: str = "logs"
    session_logs: bool = True
    max_log_files: int = 50
    max_file_size_mb: int = 100

    # Console settings
    use_rich: bool = True
    show_progress_bars: bool = True
    colored_output: bool = True

    # API tracking
    track_api_calls: bool = True
    track_costs: bool = True
    track_performance: bool = True

    # Component-specific settings
    component_loggers: Dict[str, str] = None

    def __post_init__(self):
        if self.component_loggers is None:
            self.component_loggers = {
                "news_fetcher": "INFO",
                "preprocessor": "INFO",
                "analysis_pipeline": "INFO",
                "clustering_analysis": "INFO",
                "scoring_llm": "INFO",
                "report_generator": "INFO",
                "research_analyzer": "INFO",
                "main_pipeline": "INFO",
            }


@dataclass
class PipelineConfig:
    """Pipeline configuration settings"""

    # General settings
    pipeline_version: str = "1.0.0"
    max_workers: int = 4
    timeout_seconds: int = 300

    # API settings
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None

    # Default models
    default_anthropic_model: str = "claude-3-5-sonnet-20241022"
    default_openai_model: str = "gpt-4-turbo"
    default_cohere_model: str = "command"

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0
    exponential_backoff: bool = True

    def __post_init__(self):
        # Load API keys from environment if not provided
        if not self.anthropic_api_key:
            self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.cohere_api_key:
            self.cohere_api_key = os.getenv("COHERE_API_KEY")


class Config:
    """Main configuration class"""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration"""
        self.logging = LoggingConfig()
        self.pipeline = PipelineConfig()

        # Load from environment variables
        self._load_from_env()

        # Load from config file if provided
        if config_file:
            self._load_from_file(config_file)

    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Logging configuration
        if os.getenv("LOGGING_MODE"):
            self.logging.mode = LoggingMode(os.getenv("LOGGING_MODE"))

        if os.getenv("LOGGING_CONSOLE_LEVEL"):
            self.logging.console_level = os.getenv("LOGGING_CONSOLE_LEVEL")

        if os.getenv("LOGGING_FILE_LEVEL"):
            self.logging.file_level = os.getenv("LOGGING_FILE_LEVEL")

        if os.getenv("LOG_DIR"):
            self.logging.log_dir = os.getenv("LOG_DIR")

        if os.getenv("DISABLE_RICH"):
            self.logging.use_rich = os.getenv("DISABLE_RICH").lower() != "true"

        if os.getenv("DISABLE_PROGRESS_BARS"):
            self.logging.show_progress_bars = (
                os.getenv("DISABLE_PROGRESS_BARS").lower() != "true"
            )

        # Pipeline configuration
        if os.getenv("MAX_WORKERS"):
            self.pipeline.max_workers = int(os.getenv("MAX_WORKERS"))

        if os.getenv("TIMEOUT_SECONDS"):
            self.pipeline.timeout_seconds = int(os.getenv("TIMEOUT_SECONDS"))

        if os.getenv("MAX_RETRIES"):
            self.pipeline.max_retries = int(os.getenv("MAX_RETRIES"))

    def _load_from_file(self, config_file: str):
        """Load configuration from JSON/YAML file"""
        import json

        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        with open(config_path, "r") as f:
            if config_file.endswith(".json"):
                config_data = json.load(f)
            else:
                raise ValueError(
                    "Only JSON configuration files are currently supported"
                )

        # Update logging config
        if "logging" in config_data:
            logging_data = config_data["logging"]
            for key, value in logging_data.items():
                if hasattr(self.logging, key):
                    setattr(self.logging, key, value)

        # Update pipeline config
        if "pipeline" in config_data:
            pipeline_data = config_data["pipeline"]
            for key, value in pipeline_data.items():
                if hasattr(self.pipeline, key):
                    setattr(self.pipeline, key, value)

    def get_log_directory(self) -> Path:
        """Get the log directory path"""
        log_dir = Path(self.logging.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "logging": {
                "mode": self.logging.mode.value,
                "console_level": self.logging.console_level,
                "file_level": self.logging.file_level,
                "log_dir": self.logging.log_dir,
                "session_logs": self.logging.session_logs,
                "max_log_files": self.logging.max_log_files,
                "max_file_size_mb": self.logging.max_file_size_mb,
                "use_rich": self.logging.use_rich,
                "show_progress_bars": self.logging.show_progress_bars,
                "colored_output": self.logging.colored_output,
                "track_api_calls": self.logging.track_api_calls,
                "track_costs": self.logging.track_costs,
                "track_performance": self.logging.track_performance,
                "component_loggers": self.logging.component_loggers,
            },
            "pipeline": {
                "pipeline_version": self.pipeline.pipeline_version,
                "max_workers": self.pipeline.max_workers,
                "timeout_seconds": self.pipeline.timeout_seconds,
                "default_anthropic_model": self.pipeline.default_anthropic_model,
                "default_openai_model": self.pipeline.default_openai_model,
                "default_cohere_model": self.pipeline.default_cohere_model,
                "max_retries": self.pipeline.max_retries,
                "retry_delay": self.pipeline.retry_delay,
                "exponential_backoff": self.pipeline.exponential_backoff,
            },
        }


# Global configuration instance
default_config = Config()


def get_config() -> Config:
    """Get the global configuration instance"""
    return default_config


def load_config(config_file: Optional[str] = None) -> Config:
    """Load configuration from file"""
    global default_config
    default_config = Config(config_file)
    return default_config
