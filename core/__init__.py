"""
Core contracts for the AgentForge platform.

This module includes core data models, interfaces, and constants used across the platform.
"""

from .constants import (
    AGENT_SERVICE_NAME,
    DEFAULT_REQUEST_TIMEOUT,
    DEFAULT_SERVICE_PORT,
    ERROR_CODES,
    HTTP_STATUS_CODES,
    MODEL_SERVICE_NAME,
    TOOL_SERVICE_NAME,
    MessageType,
)
from .interfaces import (
    AgentServiceInterface,
    AuthenticationError,
    ModelServiceInterface,
    NotFoundError,
    ServiceError,
    ToolServiceInterface,
    ValidationError,
)
from .models import (
    AgentCapability,
    AgentConfig,
    AgentState,
    BaseModel,
    BaseRequest,
    BaseResponse,
    ModelCapability,
    ModelConfig,
    ModelResponse,
    ToolDefinition,
    ToolParameters,
    ToolResult,
)

__all__ = [
    # Models
    "BaseModel",
    "BaseRequest",
    "BaseResponse",
    "AgentConfig",
    "AgentState",
    "AgentCapability",
    "ToolDefinition",
    "ToolResult",
    "ToolParameters",
    "ModelConfig",
    "ModelCapability",
    "ModelResponse",
    # Interfaces
    "AgentServiceInterface",
    "ModelServiceInterface",
    "ToolServiceInterface",
    "ServiceError",
    "NotFoundError",
    "ValidationError",
    "AuthenticationError",
    # Constants
    "AGENT_SERVICE_NAME",
    "MODEL_SERVICE_NAME",
    "TOOL_SERVICE_NAME",
    "DEFAULT_SERVICE_PORT",
    "DEFAULT_REQUEST_TIMEOUT",
    "HTTP_STATUS_CODES",
    "ERROR_CODES",
    "MessageType",
]
