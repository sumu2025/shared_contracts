"""
基础模型定义

这个模块定义了平台中使用的基础数据模型。
所有这些模型都使用pydantic v2实..."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field, field_validator


class BaseModel(PydanticBaseModel):
    """所有模型的基类，定义了共同的配置选项...."""

    # 使用ConfigDict配置模型行为 (pydantic v2风格)
    model_config = ConfigDict(
        # 允许通过别名访问字段
        populate_by_name=True,
        # 验证字段的赋值
        validate_assignment=True,
        # 使用JSON模式的额外属性
        json_schema_extra={"description": "AgentForge平台基础模型"},
        # 不允许额外字段
        extra="forbid",
    )


class BaseRequest(BaseModel):
    """所有请求的基类...."""

    request_id: UUID = Field(default_factory=uuid4, description="请求唯一标识符")

    timestamp: datetime = Field(default_factory=datetime.utcnow, description="请求创建时间戳")

    client_id: Optional[str] = Field(default=None, description="客户端ID，用于追踪请求源")

    trace_id: Optional[str] = Field(default=None, description="分布式追踪ID")


class BaseResponse(BaseModel):
    """所有响应的基类...."""

    request_id: UUID = Field(..., description="对应请求的唯一标识符")

    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应创建时间戳")

    status: str = Field(..., description="响应状态，如'success'或'error'")

    message: Optional[str] = Field(default=None, description="响应消息或状态描述")

    data: Optional[Any] = Field(default=None, description="响应数据")

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        """验证状态字段值是否有效...."""
        valid_statuses = ["success", "error", "pending"]
        if value not in valid_statuses:
            raise ValueError(f"状态必须是以下之一: {', '.join(valid_statuses)}")
        return value


class BaseError(BaseModel):
    """错误信息模型...."""

    error_code: str = Field(..., description="错误代码")

    message: str = Field(..., description="错误描述")

    details: Optional[Dict[str, Any]] = Field(default=None, description="错误详情")

    timestamp: datetime = Field(default_factory=datetime.utcnow, description="错误发生时间")
