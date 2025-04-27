"""
Service interface definitions for the AgentForge platform.
"""

from .agent_interface import AgentServiceInterface
from .common_errors import (
    AuthenticationError,
    NotFoundError,
    ServiceError,
    ValidationError,
)
from .model_interface import ModelServiceInterface
from .tool_interface import ToolServiceInterface

__all__ = [
    "AgentServiceInterface",
    "ModelServiceInterface",
    "ToolServiceInterface",
    "ServiceError",
    "NotFoundError",
    "ValidationError",
    "AuthenticationError",
]
