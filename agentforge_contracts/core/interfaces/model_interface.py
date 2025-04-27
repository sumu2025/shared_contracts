"""
模型服务接口定义

这个模块定义了模型服务的接口和相关类型。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from agentforge_contracts.core.models.base_models import BaseModel, BaseResponse
from agentforge_contracts.core.models.model_models import ModelCapability, ModelConfig, ModelType


class ModelRequest(BaseModel):
    """模型请求基类"""

    model_id: str
    inputs: Union[str, List[str], Dict[str, Any]]
    parameters: Optional[Dict[str, Any]] = None
    stream: bool = False


class ModelResponse(BaseResponse):
    """模型响应基类"""

    model_id: str
    outputs: Union[str, List[str], Dict[str, Any]]
    usage: Dict[str, int]
    model_version: Optional[str] = None
    latency_ms: Optional[int] = None


class ModelServiceInterface(ABC):
    """模型服务接口协议"""

    @abstractmethod
    async def get_models(
        self, model_type: Optional[ModelType] = None, enabled_only: bool = True
    ) -> List[ModelConfig]:
        """
        获取可用模型列表

        Args:
            model_type: 可选的模型类型过滤
            enabled_only: 是否只返回已启用的模型

        Returns:
            模型配置列表

        Raises:
            ServiceError: 通用服务错误
        """

    @abstractmethod
    async def get_model(self, model_id: str) -> ModelConfig:
        """
        获取特定模型配置

        Args:
            model_id: 模型ID

        Returns:
            模型配置

        Raises:
            NotFoundError: 如果找不到模型
            ServiceError: 通用服务错误
        """

    @abstractmethod
    async def register_model(self, config: ModelConfig) -> ModelConfig:
        """
        注册新模型

        Args:
            config: 模型配置

        Returns:
            注册后的模型配置

        Raises:
            ValidationError: 如果配置无效
            ServiceError: 通用服务错误
        """

    @abstractmethod
    async def update_model(self, model_id: str, config: ModelConfig) -> ModelConfig:
        """
        更新模型配置

        Args:
            model_id: 模型ID
            config: 新配置

        Returns:
            更新后的模型配置

        Raises:
            NotFoundError: 如果找不到模型
            ValidationError: 如果配置无效
            ServiceError: 通用服务错误
        """

    @abstractmethod
    async def delete_model(self, model_id: str) -> bool:
        """
        删除模型

        Args:
            model_id: 模型ID

        Returns:
            是否成功删除

        Raises:
            NotFoundError: 如果找不到模型
            ServiceError: 通用服务错误
        """

    @abstractmethod
    async def generate_text(self, request: ModelRequest) -> ModelResponse:
        """
        文本生成

        Args:
            request: 模型请求，包含输入文本和参数

        Returns:
            模型响应，包含生成的文本

        Raises:
            NotFoundError: 如果找不到模型
            ValidationError: 如果请求无效
            ServiceError: 通用服务错误
        """

    @abstractmethod
    async def generate_embeddings(self, request: ModelRequest) -> ModelResponse:
        """
        生成嵌入向量

        Args:
            request: 模型请求，包含输入文本

        Returns:
            模型响应，包含嵌入向量

        Raises:
            NotFoundError: 如果找不到模型
            ValidationError: 如果请求无效
            ServiceError: 通用服务错误
        """

    @abstractmethod
    async def get_model_capabilities(self, model_id: str) -> ModelCapability:
        """
        获取模型能力

        Args:
            model_id: 模型ID

        Returns:
            模型能力

        Raises:
            NotFoundError: 如果找不到模型
            ServiceError: 通用服务错误
        """

    @abstractmethod
    async def check_model_health(self, model_id: str) -> Dict[str, Any]:
        """
        检查模型健康状态

        Args:
            model_id: 模型ID

        Returns:
            健康状态信息

        Raises:
            NotFoundError: 如果找不到模型
            ServiceError: 通用服务错误
        """
