"""
Monitoring types and enumerations.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field


class LogLevel(str, Enum):
    """Log level enumeration."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ServiceComponent(str, Enum):
    """Service component enumeration."""

    AGENT_CORE = "agent_core"
    MODEL_SERVICE = "model_service"
    TOOL_SERVICE = "tool_service"
    API_GATEWAY = "api_gateway"
    INFRA = "infrastructure"
    DATABASE = "database"
    MESSAGING = "messaging"
    SYSTEM = "system"


class EventType(str, Enum):
    """Event type enumeration."""

    REQUEST = "request"
    RESPONSE = "response"
    EXCEPTION = "exception"
    METRIC = "metric"
    LIFECYCLE = "lifecycle"
    VALIDATION = "validation"
    AUTH = "authentication"
    SYSTEM = "system"


class MonitorEvent(PydanticBaseModel):
    """Base monitoring event model."""

    timestamp: float = Field(..., description="Event timestamp (Unix time)")
    level: LogLevel = Field(..., description="Log level")
    component: ServiceComponent = Field(..., description="Service component")
    event_type: EventType = Field(..., description="Event type")
    message: str = Field(..., description="Event message")
    data: Optional[Dict[str, Any]] = Field(None, description="Event data")
    tags: List[str] = Field(default_factory=list, description="Event tags")
    trace_id: Optional[str] = Field(
        None, description="Trace ID for distributed tracing"
    )
