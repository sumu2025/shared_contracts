"""
工具相关数据模型

定义与工具相关的模型，包括工具定义、参数和结果..."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import Field, field_validator, model_validator

from .base_models import BaseModel


class ParameterType(str, Enum):
    """参数类型枚举...."""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    NULL = "null"


class ToolParameter(BaseModel):
    """工具参数定义...."""

    name: str = Field(..., min_length=1, description="参数名称")

    type: ParameterType = Field(..., description="参数类型")

    description: str = Field(..., description="参数描述")

    required: bool = Field(default=False, description="参数是否必需")

    default: Optional[Any] = Field(default=None, description="默认值")

    enum: Optional[List[Any]] = Field(default=None, description="可能的枚举值列表")

    @model_validator(mode="after")
    def validate_default_type(self) -> "ToolParameter":
        """验证默认值类型与参数类型匹配...."""
        if self.default is not None:
            # 根据参数类型验证默认值
            if self.type == ParameterType.STRING and not isinstance(self.default, str):
                raise ValueError(f"默认值类型应为字符串，而不是 {type(self.default)}")
            elif self.type == ParameterType.INTEGER and not isinstance(
                self.default, int
            ):
                raise ValueError(f"默认值类型应为整数，而不是 {type(self.default)}")
            elif self.type == ParameterType.NUMBER and not isinstance(
                self.default, (int, float)
            ):
                raise ValueError(f"默认值类型应为数字，而不是 {type(self.default)}")
            elif self.type == ParameterType.BOOLEAN and not isinstance(
                self.default, bool
            ):
                raise ValueError(f"默认值类型应为布尔值，而不是 {type(self.default)}")
            elif self.type == ParameterType.ARRAY and not isinstance(
                self.default, list
            ):
                raise ValueError(f"默认值类型应为数组，而不是 {type(self.default)}")
            elif self.type == ParameterType.OBJECT and not isinstance(
                self.default, dict
            ):
                raise ValueError(f"默认值类型应为对象，而不是 {type(self.default)}")

        return self


class ToolDefinition(BaseModel):
    """工具定义模型...."""

    tool_id: str = Field(..., min_length=1, description="工具唯一标识符")

    name: str = Field(..., min_length=1, description="工具名称")

    description: str = Field(..., min_length=1, description="工具描述")

    version: str = Field(..., min_length=1, description="工具版本")

    parameters: List[ToolParameter] = Field(default_factory=list, description="工具参数列表")

    returns: Optional[ToolParameter] = Field(default=None, description="返回值描述")

    category: str = Field(default="uncategorized", description="工具类别")

    is_enabled: bool = Field(default=True, description="工具是否启用")

    metadata: Dict[str, Any] = Field(default_factory=dict, description="工具元数据")

    provider: Optional[str] = Field(default=None, description="工具提供者")

    @field_validator("tool_id")
    @classmethod
    def validate_tool_id(cls, value: str) -> str:
        """验证工具ID格式...."""
        if not value or " " in value:
            raise ValueError("工具ID不能包含空格且不能为空")
        return value


class ToolResult(BaseModel):
    """工具执行结果模型...."""

    tool_id: str = Field(..., min_length=1, description="工具ID")

    execution_id: UUID = Field(default_factory=uuid4, description="执行唯一标识符")

    status: str = Field(..., description="执行状态")

    data: Optional[Any] = Field(default=None, description="返回数据")

    error: Optional[str] = Field(default=None, description="错误信息")

    start_time: datetime = Field(default_factory=datetime.utcnow, description="开始执行时间")

    end_time: Optional[datetime] = Field(default=None, description="结束执行时间")

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        """验证状态值是否有效...."""
        valid_statuses = ["success", "error", "running", "timeout", "cancelled"]
        if value not in valid_statuses:
            raise ValueError(f"无效的状态: {value}. 有效的状态包括: {', '.join(valid_statuses)}")
        return value

    @model_validator(mode="after")
    def validate_result(self) -> "ToolResult":
        """验证结果的一致性...."""
        if self.status == "success" and self.data is None:
            raise ValueError("成功状态必须提供结果数据")

        if self.status == "error" and self.error is None:
            raise ValueError("错误状态必须提供错误信息")

        if self.status not in ["running"] and self.end_time is None:
            # 自动设置结束时间
            self.end_time = datetime.utcnow()

        return self
