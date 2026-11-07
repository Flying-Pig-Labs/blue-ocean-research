"""Data models and enums for pipeline logging infrastructure."""

from datetime import datetime
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field
from enum import Enum


class LogLevel(str, Enum):
    """Log level enumeration"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ComponentType(str, Enum):
    """Component type enumeration"""

    NEWS_FETCHER = "news_fetcher"
    PREPROCESSOR = "preprocessor"
    ANALYSIS_PIPELINE = "analysis_pipeline"
    CLUSTERING_ANALYSIS = "clustering_analysis"
    SCORING_LLM = "scoring_llm"
    REPORT_GENERATOR = "report_generator"
    MAIN_PIPELINE = "main_pipeline"
    RESEARCH_ANALYZER = "research_analyzer"


class ModelProvider(str, Enum):
    """Model provider enumeration"""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    COHERE = "cohere"


class SessionInfo(BaseModel):
    """Session information model"""

    session_id: str = Field(description="Unique session identifier")
    start_time: datetime = Field(description="Session start timestamp")
    end_time: Optional[datetime] = Field(
        default=None, description="Session end timestamp"
    )
    session_dir: str = Field(description="Session log directory path")
    total_api_calls: int = Field(default=0, description="Total API calls in session")
    total_cost: float = Field(default=0.0, description="Total estimated cost in USD")
    total_tokens: int = Field(default=0, description="Total tokens used")
    pipeline_version: str = Field(default="1.0.0", description="Pipeline version")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class APICallLog(BaseModel):
    """API call logging model"""

    call_id: str = Field(description="Unique call identifier")
    timestamp: datetime = Field(description="Call timestamp")
    component: ComponentType = Field(description="Component making the call")
    provider: ModelProvider = Field(description="Model provider")
    model: str = Field(description="Model name/identifier")
    prompt_tokens: int = Field(description="Number of input tokens")
    completion_tokens: int = Field(description="Number of output tokens")
    total_tokens: int = Field(description="Total tokens used")
    estimated_cost: float = Field(description="Estimated cost in USD")
    duration: float = Field(description="Call duration in seconds")
    success: bool = Field(description="Whether the call was successful")
    error_message: Optional[str] = Field(
        default=None, description="Error message if failed"
    )
    request_size: int = Field(description="Request size in bytes")
    response_size: int = Field(description="Response size in bytes")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ComponentLog(BaseModel):
    """Component-specific logging model"""

    component: ComponentType = Field(description="Component name")
    operation: str = Field(description="Operation being performed")
    start_time: datetime = Field(description="Operation start time")
    end_time: Optional[datetime] = Field(default=None, description="Operation end time")
    duration: Optional[float] = Field(
        default=None, description="Operation duration in seconds"
    )
    input_data_size: int = Field(default=0, description="Input data size in bytes")
    output_data_size: int = Field(default=0, description="Output data size in bytes")
    records_processed: int = Field(default=0, description="Number of records processed")
    success: bool = Field(default=True, description="Whether operation was successful")
    error_message: Optional[str] = Field(
        default=None, description="Error message if failed"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class LogEntry(BaseModel):
    """General log entry model"""

    timestamp: datetime = Field(description="Log entry timestamp")
    level: LogLevel = Field(description="Log level")
    component: ComponentType = Field(description="Component that generated the log")
    message: str = Field(description="Log message")
    operation: Optional[str] = Field(default=None, description="Operation context")
    session_id: str = Field(description="Session identifier")
    call_id: Optional[str] = Field(default=None, description="Associated API call ID")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    stack_trace: Optional[str] = Field(
        default=None, description="Stack trace for errors"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ProgressEntry(BaseModel):
    """Progress tracking model"""

    timestamp: datetime = Field(description="Progress timestamp")
    component: ComponentType = Field(description="Component name")
    operation: str = Field(description="Operation being tracked")
    current: int = Field(description="Current progress value")
    total: int = Field(description="Total expected value")
    percentage: float = Field(description="Progress percentage")
    eta: Optional[datetime] = Field(
        default=None, description="Estimated time of completion"
    )
    throughput: Optional[float] = Field(default=None, description="Items per second")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class TokenUsageSummary(BaseModel):
    """Token usage summary model"""

    component: ComponentType = Field(description="Component name")
    total_calls: int = Field(description="Total API calls")
    total_tokens: int = Field(description="Total tokens used")
    prompt_tokens: int = Field(description="Total prompt tokens")
    completion_tokens: int = Field(description="Total completion tokens")
    estimated_cost: float = Field(description="Total estimated cost")
    average_tokens_per_call: float = Field(description="Average tokens per call")
    models_used: List[str] = Field(description="List of models used")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class SessionSummary(BaseModel):
    """Session summary model"""

    session_info: SessionInfo = Field(description="Session information")
    total_duration: float = Field(description="Total session duration in seconds")
    components_used: List[ComponentType] = Field(
        description="Components used in session"
    )
    api_call_summary: List[TokenUsageSummary] = Field(
        description="API usage by component"
    )
    error_count: int = Field(description="Total number of errors")
    warning_count: int = Field(description="Total number of warnings")
    success_rate: float = Field(description="Overall success rate percentage")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# Model pricing data for cost estimation
MODEL_PRICING = {
    ModelProvider.ANTHROPIC: {
        "claude-3-5-sonnet-20241022": {
            "input": 0.003,
            "output": 0.015,
        },  # per 1k tokens
        "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
        "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    },
    ModelProvider.OPENAI: {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
    },
    ModelProvider.COHERE: {
        "command": {"input": 0.001, "output": 0.002},
        "command-light": {"input": 0.0003, "output": 0.0006},
    },
}


def calculate_api_cost(
    provider: ModelProvider, model: str, prompt_tokens: int, completion_tokens: int
) -> float:
    """Calculate estimated API cost"""
    pricing = MODEL_PRICING.get(provider, {}).get(model, {"input": 0, "output": 0})
    input_cost = (prompt_tokens / 1000) * pricing["input"]
    output_cost = (completion_tokens / 1000) * pricing["output"]
    return input_cost + output_cost
