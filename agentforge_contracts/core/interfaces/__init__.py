"""
服务接口定义

这个模块包含AgentForge平台的服务接口定义。
"""

from shared_contracts.core.interfaces import (
    AgentServiceInterface,
    ModelServiceInterface,
    ToolServiceInterface,
    ServiceError,
    NotFoundError,
    ValidationError,
    AuthenticationError,
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
