"""
Tool service interface definition.
"""

from typing import Any, AsyncIterable, Dict, List, Optional, Protocol, runtime_checkable

from ..models.base_models import BaseResponse
from ..models.tool_models import ToolDefinition, ToolResult


@runtime_checkable
class ToolServiceInterface(Protocol):
    """Interface for the tool service."""

    async def register_tool(
        self, definition: ToolDefinition
    ) -> BaseResponse[ToolDefinition]:
        """
        Register a new tool with the given definition.

        Args:
            definition: Tool definition

        Returns:
            Response containing the registered tool definition

        Raises:
            ValidationError: If the definition is invalid
            ServiceError: For other service errors
        """
        ...

    async def get_tool(self, tool_id: str) -> BaseResponse[ToolDefinition]:
        """
        Get a tool by ID.

        Args:
            tool_id: Tool ID

        Returns:
            Response containing the tool definition

        Raises:
            NotFoundError: If the tool is not found
            ServiceError: For other service errors
        """
        ...

    async def update_tool(
        self, tool_id: str, definition_updates: Dict[str, Any]
    ) -> BaseResponse[ToolDefinition]:
        """
        Update a tool's definition.

        Args:
            tool_id: Tool ID
            definition_updates: Updates to apply to the definition

        Returns:
            Response containing the updated tool definition

        Raises:
            NotFoundError: If the tool is not found
            ValidationError: If the updates are invalid
            ServiceError: For other service errors
        """
        ...

    async def delete_tool(self, tool_id: str) -> BaseResponse[bool]:
        """
        Delete a tool.

        Args:
            tool_id: Tool ID

        Returns:
            Response indicating success

        Raises:
            NotFoundError: If the tool is not found
            ServiceError: For other service errors
        """
        ...

    async def list_tools(
        self,
        offset: int = 0,
        limit: int = 100,
        filter_by: Optional[Dict[str, Any]] = None,
    ) -> BaseResponse[List[ToolDefinition]]:
        """
        List tools, with optional filtering.

        Args:
            offset: Pagination offset
            limit: Pagination limit
            filter_by: Filter criteria

        Returns:
            Response containing a list of tool definitions

        Raises:
            ValidationError: If the pagination or filter parameters are invalid
            ServiceError: For other service errors
        """
        ...

    async def execute_tool(
        self, tool_id: str, parameters: Dict[str, Any], stream: bool = False
    ) -> BaseResponse[ToolResult]:
        """
        Execute a tool with the given parameters.

        Args:
            tool_id: Tool ID
            parameters: Tool parameters
            stream: Whether to stream the result

        Returns:
            Response containing the tool result

        Raises:
            NotFoundError: If the tool is not found
            ValidationError: If the parameters are invalid
            ServiceError: For other service errors
        """
        ...

    async def execute_streaming_tool(
        self, tool_id: str, parameters: Dict[str, Any]
    ) -> AsyncIterable[ToolResult]:
        """
        Execute a tool with the given parameters, streaming the results.

        Args:
            tool_id: Tool ID
            parameters: Tool parameters

        Returns:
            Asynchronous iterable of tool results

        Raises:
            NotFoundError: If the tool is not found
            ValidationError: If the parameters are invalid
            ServiceError: For other service errors
        """
        ...

    async def get_tool_schema(self, tool_id: str) -> BaseResponse[Dict[str, Any]]:
        """
        Get a tool's JSON schema.

        Args:
            tool_id: Tool ID

        Returns:
            Response containing the tool schema

        Raises:
            NotFoundError: If the tool is not found
            ServiceError: For other service errors
        """
        ...
