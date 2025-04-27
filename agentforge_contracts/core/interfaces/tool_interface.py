"""
工具服务接口定义

这个模块定义了工具服务的接口和相关类型。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from ..models.base_models import BaseModel, BaseResponse
from ..models.tool_models import ToolDefinition, ToolResult


class ToolExecutionRequest(BaseModel):
    """工具执行请求"""

    tool_id: str
    parameters: Dict[str, Any]
    conversation_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    timeout: Optional[int] = None
    async_execution: bool = False


class ToolExecutionResponse(BaseResponse):
    """工具执行响应"""

    tool_id: str
    result: ToolResult


class ToolServiceInterface(ABC):
    """工具服务接口协议"""

    @abstractmethod
    async def get_tools(
        self, category: Optional[str] = None, enabled_only: bool = True
    ) -> List[ToolDefinition]:
        """
        获取可用工具列表

        Args:
            category: 可选的类别过滤
            enabled_only: 是否只返回已启用的工具

        Returns:
            工具定义列表

        Raises:
            ServiceError: 通用服务错误
        """
        pass

    @abstractmethod
    async def get_tool(self, tool_id: str) -> ToolDefinition:
        """
        获取特定工具定义

        Args:
            tool_id: 工具ID

        Returns:
            工具定义

        Raises:
            NotFoundError: 如果找不到工具
            ServiceError: 通用服务错误
        """
        pass

    @abstractmethod
    async def register_tool(self, definition: ToolDefinition) -> ToolDefinition:
        """
        注册新工具

        Args:
            definition: 工具定义

        Returns:
            注册后的工具定义

        Raises:
            ValidationError: 如果定义无效
            ServiceError: 通用服务错误
        """
        pass

    @abstractmethod
    async def update_tool(
        self, tool_id: str, definition: ToolDefinition
    ) -> ToolDefinition:
        """
        更新工具定义

        Args:
            tool_id: 工具ID
            definition: 新定义

        Returns:
            更新后的工具定义

        Raises:
            NotFoundError: 如果找不到工具
            ValidationError: 如果定义无效
            ServiceError: 通用服务错误
        """
        pass

    @abstractmethod
    async def delete_tool(self, tool_id: str) -> bool:
        """
        删除工具

        Args:
            tool_id: 工具ID

        Returns:
            是否成功删除

        Raises:
            NotFoundError: 如果找不到工具
            ServiceError: 通用服务错误
        """
        pass

    @abstractmethod
    async def execute_tool(
        self, request: ToolExecutionRequest
    ) -> ToolExecutionResponse:
        """
        执行工具

        Args:
            request: 执行请求

        Returns:
            执行响应

        Raises:
            NotFoundError: 如果找不到工具
            ValidationError: 如果请求无效
            ServiceError: 通用服务错误
        """
        pass

    @abstractmethod
    async def get_execution_result(self, execution_id: UUID) -> ToolResult:
        """
        获取异步执行结果

        Args:
            execution_id: 执行ID

        Returns:
            执行结果

        Raises:
            NotFoundError: 如果找不到执行
            ServiceError: 通用服务错误
        """
        pass

    @abstractmethod
    async def cancel_execution(self, execution_id: UUID) -> bool:
        """
        取消工具执行

        Args:
            execution_id: 执行ID

        Returns:
            是否成功取消

        Raises:
            NotFoundError: 如果找不到执行
            ValidationError: 如果执行已完成
            ServiceError: 通用服务错误
        """
        pass
