"""
核心数据模型

这个模块包含使用pydantic v2定义的共享数据模型。
"""

from shared_contracts.core.models import (
    BaseModel,
    BaseRequest,
    BaseResponse,
    AgentConfig,
    AgentState,
    AgentCapability,
    ToolDefinition,
    ToolResult,
    ToolParameters,
    ModelConfig,
    ModelCapability,
    ModelResponse,
)

__all__ = [
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
]
