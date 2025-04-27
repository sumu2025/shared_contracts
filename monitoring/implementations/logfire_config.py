"""
LogFire configuration for the AgentForge platform.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, model_validator

from ..monitor_types import LogLevel


class LogFireConfig(BaseModel):
    """Configuration for LogFire client."""

    api_key: str = Field(..., description="LogFire API key / write token")
    project_id: Optional[str] = Field(
        None, description="LogFire project identifier (optional in newer versions)"
    )
    service_name: str = Field(..., description="Name of the service")
    environment: str = Field(
        default="development", description="Deployment environment"
    )
    min_log_level: LogLevel = Field(
        default=LogLevel.INFO, description="Minimum log level to send to LogFire"
    )
    batch_size: int = Field(
        default=100, description="Maximum number of log entries to batch before sending"
    )
    flush_interval_seconds: float = Field(
        default=5.0, description="Maximum time to wait before flushing logs"
    )
    tags: Dict[str, str] = Field(
        default_factory=dict, description="Global tags to apply to all logs"
    )
    api_endpoint: str = Field(
        default="https://api.logfire.sh/v1", description="LogFire API endpoint"
    )
    timeout_seconds: float = Field(default=10.0, description="Timeout for API requests")
    retry_attempts: int = Field(
        default=3, description="Number of retry attempts for failed API requests"
    )
    enable_metadata: bool = Field(
        default=True, description="Whether to include host and runtime metadata"
    )
    additional_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata to include with all logs"
    )
    sample_rate: float = Field(
        default=1.0, description="Sampling rate for logs (0.0-1.0)"
    )

    @model_validator(mode="after")
    def validate_config(self) -> "LogFireConfig":
        """Validate the configuration."""
        if self.batch_size < 1:
            raise ValueError("batch_size must be at least 1")

        if self.flush_interval_seconds <= 0:
            raise ValueError("flush_interval_seconds must be positive")

        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        if self.retry_attempts < 0:
            raise ValueError("retry_attempts must be non-negative")

        if not (0.0 <= self.sample_rate <= 1.0):
            raise ValueError("sample_rate must be between 0.0 and 1.0")

        return self
