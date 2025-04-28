"""
模型服务相关数据模型

定义与模型服务相关的数据模型，包括模型配置、能力..."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field, model_validator

from .base_models import BaseModel


class ModelType(str, Enum):
    """模型类型枚举...."""

    TEXT = "text"
    EMBEDDING = "embedding"
    VISION = "vision"
    AUDIO = "audio"
    MULTIMODAL = "multimodal"


class ModelProvider(str, Enum):
    """模型提供者枚举...."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    COHERE = "cohere"
    STABILITY = "stability"
    INTERNAL = "internal"
    CUSTOM = "custom"


class ModelCapability(BaseModel):
    """模型能力模型...."""

    supports_streaming: bool = Field(default=False, description="是否支持流式输出")

    supports_function_calling: bool = Field(default=False, description="是否支持函数调用")

    supports_vision: bool = Field(default=False, description="是否支持视觉输入")

    max_tokens: int = Field(..., gt=0, description="最大tokens数量")

    input_cost_per_token: float = Field(
        default=0.0, ge=0.0, description="输入每token成本（美元）"
    )

    output_cost_per_token: float = Field(
        default=0.0, ge=0.0, description="输出每token成本（美元）"
    )

    supports_tools: bool = Field(default=False, description="是否支持工具使用")

    latency_ms: Optional[int] = Field(default=None, description="平均延迟（毫秒）")

    tokens_per_second: Optional[int] = Field(default=None, description="生成速度（tokens/秒）")

    @model_validator(mode="after")
    def validate_costs(self) -> "ModelCapability":
        """验证成本信息的合理性...."""
        if self.input_cost_per_token < 0 or self.output_cost_per_token < 0:
            raise ValueError("token成本不能为负数")
        return self


class ModelConfig(BaseModel):
    """模型配置模型...."""

    model_id: str = Field(..., min_length=1, description="模型唯一标识符")

    display_name: str = Field(..., min_length=1, description="模型显示名称")

    provider: ModelProvider = Field(..., description="模型提供者")

    model_type: ModelType = Field(..., description="模型类型")

    capabilities: ModelCapability = Field(..., description="模型能力")

    api_key_env_var: Optional[str] = Field(default=None, description="API密钥环境变量名称")

    api_base_url: Optional[str] = Field(default=None, description="API基础URL")

    timeout: int = Field(default=60, ge=1, description="API调用超时（秒）")

    metadata: Dict[str, Any] = Field(default_factory=dict, description="模型元数据")

    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")

    updated_at: Optional[datetime] = Field(default=None, description="最后更新时间")

    cache_ttl: Optional[int] = Field(default=None, description="缓存生存时间（秒）")

    enabled: bool = Field(default=True, description="模型是否启用")

    tags: List[str] = Field(default_factory=list, description="模型标签")

    version: str = Field(default="1.0.0", description="模型版本")

    retry_config: Optional[Dict[str, Any]] = Field(default=None, description="重试配置")

    @model_validator(mode="after")
    def update_timestamps(self) -> "ModelConfig":
        """确保更新时间总是最新的...."""
        self.updated_at = datetime.utcnow()
        return self
