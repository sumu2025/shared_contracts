"""
代理服务接口定义

这个模块定义了代理服务的接口和相关类..."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID

from ..models.agent_models import AgentConfig, AgentState
from ..models.base_models import BaseResponse


class AgentCreationResponse(BaseResponse):
    """代理创建响应模型...."""

    agent_id: UUID
    agent_config: AgentConfig


class AgentServiceInterface(ABC):
    """代理服务接口协议...."""

    @abstractmethod
    async def create_agent(self, config: AgentConfig) -> AgentCreationResponse:
        """
        创建新代理

        Args:
            config: 代理配置

        Returns:
            创建响应，包含代理ID和配置

        Raises:
            ValidationError: 如果配置无效
            AuthorizationError: 如果无权创建代理
            DependencyError: 如果依赖服务不可用
     ..."""

    @abstractmethod
    async def get_agent(self, agent_id: UUID) -> AgentConfig:
        """
        获取代理配置

        Args:
            agent_id: 代理ID

        Returns:
            代理配置

        Raises:
            NotFoundError: 如果找不到代理
            AuthorizationError: 如果无权访问代理
     ..."""

    @abstractmethod
    async def update_agent(self, agent_id: UUID, config: AgentConfig) -> AgentConfig:
        """
        更新代理配置

        Args:
            agent_id: 代理ID
            config: 新配置

        Returns:
            更新后的代理配置

        Raises:
            NotFoundError: 如果找不到代理
            ValidationError: 如果配置无效
            AuthorizationError: 如果无权更新代理
     ..."""

    @abstractmethod
    async def delete_agent(self, agent_id: UUID) -> bool:
        """
        删除代理

        Args:
            agent_id: 代理ID

        Returns:
            是否成功删除

        Raises:
            NotFoundError: 如果找不到代理
            AuthorizationError: 如果无权删除代理
     ..."""

    @abstractmethod
    async def list_agents(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[AgentConfig]:
        """
        列出代理

        Args:
            limit: 结果数量限制
            offset: 结果偏移量
            filters: 过滤条件

        Returns:
            代理配置列表

        Raises:
            ValidationError: 如果过滤条件无效
            AuthorizationError: 如果无权列出代理
     ..."""

    @abstractmethod
    async def get_agent_state(self, agent_id: UUID) -> AgentState:
        """
        获取代理状态

        Args:
            agent_id: 代理ID

        Returns:
            代理状态

        Raises:
            NotFoundError: 如果找不到代理
            AuthorizationError: 如果无权访问代理状态
     ..."""

    @abstractmethod
    async def create_conversation(
        self,
        agent_id: UUID,
        initial_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """
        创建新对话

        Args:
            agent_id: 代理ID
            initial_message: 初始消息
            metadata: 对话元数据

        Returns:
            对话ID

        Raises:
            NotFoundError: 如果找不到代理
            ValidationError: 如果参数无效
            AuthorizationError: 如果无权创建对话
     ..."""

    @abstractmethod
    async def send_message(
        self,
        conversation_id: UUID,
        message: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        向对话发送消息

        Args:
            conversation_id: 对话ID
            message: 消息内容
            attachments: 附件列表

        Returns:
            代理响应

        Raises:
            NotFoundError: 如果找不到对话
            ValidationError: 如果消息无效
            AuthorizationError: 如果无权发送消息
     ..."""
