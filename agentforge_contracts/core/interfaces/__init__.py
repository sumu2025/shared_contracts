"""
服务接口定义

这个模块包含AgentForge平台的服务接口定..."""

from shared_contracts.core.interfaces import (
    AgentServiceInterface,
    AuthenticationError,
    ModelServiceInterface,
    NotFoundError,
    ServiceError,
    ToolServiceInterface,
    ValidationError,
)

__all__ = [
    "AgentServiceInterface",
    "ModelServiceInterface",
    "ToolServiceInterface",
    "ServiceError",
    "NotFoundError",
    "ValidationError",
    "AuthenticationError",
]
