"""
Agent service interface definition.
"""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from uuid import UUID

from ..models.agent_models import AgentConfig, AgentState
from ..models.base_models import BaseResponse


@runtime_checkable
class AgentServiceInterface(Protocol):
    """Interface for the agent service."""

    async def create_agent(self, config: AgentConfig) -> BaseResponse[AgentConfig]:
        """
        Create a new agent with the given configuration.

        Args:
            config: Agent configuration

        Returns:
            Response containing the created agent configuration

        Raises:
            ValidationError: If the configuration is invalid
            ServiceError: For other service errors
        """
        ...

    async def get_agent(self, agent_id: UUID) -> BaseResponse[AgentConfig]:
        """
        Get an agent by ID.

        Args:
            agent_id: Agent ID

        Returns:
            Response containing the agent configuration

        Raises:
            NotFoundError: If the agent is not found
            ServiceError: For other service errors
        """
        ...

    async def update_agent(
        self, agent_id: UUID, config_updates: Dict[str, Any]
    ) -> BaseResponse[AgentConfig]:
        """
        Update an agent's configuration.

        Args:
            agent_id: Agent ID
            config_updates: Updates to apply to the configuration

        Returns:
            Response containing the updated agent configuration

        Raises:
            NotFoundError: If the agent is not found
            ValidationError: If the updates are invalid
            ServiceError: For other service errors
        """
        ...

    async def delete_agent(self, agent_id: UUID) -> BaseResponse[bool]:
        """
        Delete an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Response indicating success

        Raises:
            NotFoundError: If the agent is not found
            ServiceError: For other service errors
        """
        ...

    async def list_agents(
        self,
        offset: int = 0,
        limit: int = 100,
        filter_by: Optional[Dict[str, Any]] = None,
    ) -> BaseResponse[List[AgentConfig]]:
        """
        List agents, with optional filtering.

        Args:
            offset: Pagination offset
            limit: Pagination limit
            filter_by: Filter criteria

        Returns:
            Response containing a list of agent configurations

        Raises:
            ValidationError: If the pagination or filter parameters are invalid
            ServiceError: For other service errors
        """
        ...

    async def get_agent_state(self, agent_id: UUID) -> BaseResponse[AgentState]:
        """
        Get an agent's current state.

        Args:
            agent_id: Agent ID

        Returns:
            Response containing the agent state

        Raises:
            NotFoundError: If the agent is not found
            ServiceError: For other service errors
        """
        ...

    async def send_message_to_agent(
        self, agent_id: UUID, message: str, conversation_id: Optional[UUID] = None
    ) -> BaseResponse[Dict[str, Any]]:
        """
        Send a message to an agent.

        Args:
            agent_id: Agent ID
            message: Message content
            conversation_id: Optional conversation ID, if continuing an existing conversation

        Returns:
            Response containing the agent's response

        Raises:
            NotFoundError: If the agent is not found
            ValidationError: If the message is invalid
            ServiceError: For other service errors
        """
        ...
