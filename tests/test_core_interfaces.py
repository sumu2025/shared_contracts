"""
Tests for core interfaces in agentforge-contracts.
"""

import uuid
from datetime import datetime
from typing import Any, AsyncIterable, Dict, List, Optional

import pytest

from shared_contracts.core.interfaces.agent_interface import AgentServiceInterface
from shared_contracts.core.interfaces.common_errors import (
    AuthenticationError,
    NotFoundError,
    ServiceError,
    ValidationError,
)
from shared_contracts.core.interfaces.model_interface import ModelServiceInterface
from shared_contracts.core.interfaces.tool_interface import ToolServiceInterface
from shared_contracts.core.models.agent_models import (
    AgentCapability,
    AgentConfig,
    AgentState,
    AgentStatus,
)
from shared_contracts.core.models.base_models import BaseResponse
from shared_contracts.core.models.model_models import (
    ModelCapability,
    ModelConfig,
    ModelProvider,
    ModelResponse,
    ModelType,
)
from shared_contracts.core.models.tool_models import (
    ToolDefinition,
    ToolResult,
    ToolResultStatus,
)


class TestServiceInterfaces:
    """Tests for service interfaces."""

    @pytest.mark.asyncio
    async def test_agent_service_interface_implementation(self):
        """Test implementation of AgentServiceInterface."""

        # Create a concrete implementation
        class ConcreteAgentService:
            async def create_agent(
                self, config: AgentConfig
            ) -> BaseResponse[AgentConfig]:
                return BaseResponse(request_id=uuid.uuid4(), success=True, data=config)

            async def get_agent(self, agent_id: uuid.UUID) -> BaseResponse[AgentConfig]:
                # Create a valid AgentConfig with all required fields
                return BaseResponse(
                    request_id=uuid.uuid4(),
                    success=True,
                    data=AgentConfig(
                        name="Test Agent",
                        description="A test agent",
                        model_id="test-model",
                        system_prompt="You are a helpful assistant",
                        capabilities={AgentCapability.CONVERSATION},
                    ),
                )

            async def update_agent(
                self, agent_id: uuid.UUID, config_updates: Dict[str, Any]
            ) -> BaseResponse[AgentConfig]:
                return BaseResponse(
                    request_id=uuid.uuid4(),
                    success=True,
                    data=AgentConfig(
                        name="Updated Agent",
                        description="An updated test agent",
                        model_id="test-model",
                        system_prompt="You are a helpful assistant",
                        capabilities={AgentCapability.CONVERSATION},
                    ),
                )

            async def delete_agent(self, agent_id: uuid.UUID) -> BaseResponse[bool]:
                return BaseResponse(request_id=uuid.uuid4(), success=True, data=True)

            async def list_agents(
                self,
                offset: int = 0,
                limit: int = 100,
                filter_by: Optional[Dict[str, Any]] = None,
            ) -> BaseResponse[List[AgentConfig]]:
                return BaseResponse(
                    request_id=uuid.uuid4(),
                    success=True,
                    data=[
                        AgentConfig(
                            name="Agent 1",
                            description="Test agent 1",
                            model_id="test-model",
                            system_prompt="You are a helpful assistant",
                            capabilities={AgentCapability.CONVERSATION},
                        ),
                        AgentConfig(
                            name="Agent 2",
                            description="Test agent 2",
                            model_id="test-model",
                            system_prompt="You are a helpful assistant",
                            capabilities={AgentCapability.PLANNING},
                        ),
                    ],
                )

            async def get_agent_state(
                self, agent_id: uuid.UUID
            ) -> BaseResponse[AgentState]:
                current_time = datetime.now()
                return BaseResponse(
                    request_id=uuid.uuid4(),
                    success=True,
                    data=AgentState(
                        agent_id=agent_id,
                        status=AgentStatus.READY,
                        created_at=current_time,
                        last_active=current_time,
                    ),
                )

            async def send_message_to_agent(
                self,
                agent_id: uuid.UUID,
                message: str,
                conversation_id: Optional[uuid.UUID] = None,
            ) -> BaseResponse[Dict[str, Any]]:
                return BaseResponse(
                    request_id=uuid.uuid4(),
                    success=True,
                    data={
                        "message": "Response from agent",
                        "conversation_id": str(conversation_id)
                        if conversation_id
                        else str(uuid.uuid4()),
                    },
                )

        # Check that the implementation satisfies the interface
        service = ConcreteAgentService()
        assert isinstance(service, AgentServiceInterface)

        # Call some methods to verify
        agent_config = AgentConfig(
            name="New Agent",
            description="A new test agent",
            model_id="test-model",
            system_prompt="You are a helpful assistant",
            capabilities={AgentCapability.CONVERSATION},
        )

        response = await service.create_agent(agent_config)
        assert response.success is True
        assert response.data.name == "New Agent"

        agent_id = uuid.uuid4()
        response = await service.get_agent_state(agent_id)
        assert response.success is True
        assert response.data.agent_id == agent_id
        assert response.data.status == AgentStatus.READY

    @pytest.mark.asyncio
    async def test_model_service_interface_implementation(self):
        """Test implementation of ModelServiceInterface."""

        # Create a concrete implementation
        class ConcreteModelService:
            async def register_model(
                self, config: ModelConfig
            ) -> BaseResponse[ModelConfig]:
                return BaseResponse(request_id=uuid.uuid4(), success=True, data=config)

            async def get_model(self, model_id: str) -> BaseResponse[ModelConfig]:
                # Create a valid ModelConfig with all required fields
                capabilities = ModelCapability(
                    supports_streaming=True,
                    supports_function_calling=False,
                    supports_json_mode=False,
                    supports_vision=False,
                    max_tokens=1000,
                )

                return BaseResponse(
                    request_id=uuid.uuid4(),
                    success=True,
                    data=ModelConfig(
                        model_id=model_id,
                        provider=ModelProvider.OPENAI,
                        model_type=ModelType.CHAT,
                        display_name="Test Model",
                        capabilities=capabilities,
                        provider_model_id="test-model",
                        api_key_env_var="TEST_API_KEY",
                    ),
                )

            async def update_model(
                self, model_id: str, config_updates: Dict[str, Any]
            ) -> BaseResponse[ModelConfig]:
                capabilities = ModelCapability(
                    supports_streaming=True,
                    supports_function_calling=False,
                    supports_json_mode=False,
                    supports_vision=False,
                    max_tokens=1000,
                )

                return BaseResponse(
                    request_id=uuid.uuid4(),
                    success=True,
                    data=ModelConfig(
                        model_id=model_id,
                        provider=ModelProvider.OPENAI,
                        model_type=ModelType.CHAT,
                        display_name="Updated Model",
                        capabilities=capabilities,
                        provider_model_id="test-model",
                        api_key_env_var="TEST_API_KEY",
                    ),
                )

            async def delete_model(self, model_id: str) -> BaseResponse[bool]:
                return BaseResponse(request_id=uuid.uuid4(), success=True, data=True)

            async def list_models(
                self,
                offset: int = 0,
                limit: int = 100,
                filter_by: Optional[Dict[str, Any]] = None,
            ) -> BaseResponse[List[ModelConfig]]:
                capabilities1 = ModelCapability(
                    supports_streaming=True,
                    supports_function_calling=False,
                    supports_json_mode=False,
                    supports_vision=False,
                    max_tokens=1000,
                )

                capabilities2 = ModelCapability(
                    supports_streaming=True,
                    supports_function_calling=True,
                    supports_json_mode=True,
                    supports_vision=False,
                    max_tokens=2000,
                )

                return BaseResponse(
                    request_id=uuid.uuid4(),
                    success=True,
                    data=[
                        ModelConfig(
                            model_id="model-1",
                            provider=ModelProvider.OPENAI,
                            model_type=ModelType.CHAT,
                            display_name="Model 1",
                            capabilities=capabilities1,
                            provider_model_id="model-1",
                            api_key_env_var="TEST_API_KEY",
                        ),
                        ModelConfig(
                            model_id="model-2",
                            provider=ModelProvider.ANTHROPIC,
                            model_type=ModelType.CHAT,
                            display_name="Model 2",
                            capabilities=capabilities2,
                            provider_model_id="model-2",
                            api_key_env_var="TEST_API_KEY",
                        ),
                    ],
                )

            async def generate_completion(
                self,
                model_id: str,
                prompt: str,
                max_tokens: Optional[int] = None,
                temperature: Optional[float] = None,
                stream: bool = False,
                **options: Any,
            ) -> BaseResponse[ModelResponse]:
                request_id = uuid.uuid4()
                return BaseResponse(
                    request_id=request_id,
                    success=True,
                    data=ModelResponse(
                        model_id=model_id,
                        request_id=request_id,
                        content="Generated completion",
                        usage={
                            "prompt_tokens": 10,
                            "completion_tokens": 5,
                            "total_tokens": 15,
                        },
                        finish_reason="stop",
                    ),
                )

            async def generate_streaming_completion(
                self,
                model_id: str,
                prompt: str,
                max_tokens: Optional[int] = None,
                temperature: Optional[float] = None,
                **options: Any,
            ) -> AsyncIterable[ModelResponse]:
                # In a real implementation, this would be an async generator
                raise NotImplementedError("Not implemented for test")

        # Check that the implementation satisfies the interface
        service = ConcreteModelService()
        assert isinstance(service, ModelServiceInterface)

        # Call some methods to verify
        capabilities = ModelCapability(
            supports_streaming=True,
            supports_function_calling=True,
            supports_json_mode=True,
            supports_vision=False,
            max_tokens=2000,
        )

        model_config = ModelConfig(
            model_id="new-model",
            provider=ModelProvider.OPENAI,
            model_type=ModelType.CHAT,
            display_name="New Model",
            capabilities=capabilities,
            provider_model_id="new-model",
            api_key_env_var="OPENAI_API_KEY",
        )

        response = await service.register_model(model_config)
        assert response.success is True
        assert response.data.model_id == "new-model"

        response = await service.generate_completion(
            model_id="new-model", prompt="Test prompt"
        )
        assert response.success is True
        assert response.data.content == "Generated completion"
        assert response.data.model_id == "new-model"

    @pytest.mark.asyncio
    async def test_tool_service_interface_implementation(self):
        """Test implementation of ToolServiceInterface."""

        # Create a concrete implementation
        class ConcreteToolService:
            async def register_tool(
                self, definition: ToolDefinition
            ) -> BaseResponse[ToolDefinition]:
                return BaseResponse(
                    request_id=uuid.uuid4(), success=True, data=definition
                )

            async def get_tool(self, tool_id: str) -> BaseResponse[ToolDefinition]:
                return BaseResponse(
                    request_id=uuid.uuid4(),
                    success=True,
                    data=ToolDefinition(
                        tool_id=tool_id,
                        name=tool_id,
                        description="Test tool",
                        version="1.0.0",
                    ),
                )

            async def update_tool(
                self, tool_id: str, definition_updates: Dict[str, Any]
            ) -> BaseResponse[ToolDefinition]:
                return BaseResponse(
                    request_id=uuid.uuid4(),
                    success=True,
                    data=ToolDefinition(
                        tool_id=tool_id,
                        name=tool_id,
                        description="Updated test tool",
                        version="1.0.1",
                    ),
                )

            async def delete_tool(self, tool_id: str) -> BaseResponse[bool]:
                return BaseResponse(request_id=uuid.uuid4(), success=True, data=True)

            async def list_tools(
                self,
                offset: int = 0,
                limit: int = 100,
                filter_by: Optional[Dict[str, Any]] = None,
            ) -> BaseResponse[List[ToolDefinition]]:
                return BaseResponse(
                    request_id=uuid.uuid4(),
                    success=True,
                    data=[
                        ToolDefinition(
                            tool_id="tool-1",
                            name="tool-1",
                            description="Tool 1",
                            version="1.0.0",
                        ),
                        ToolDefinition(
                            tool_id="tool-2",
                            name="tool-2",
                            description="Tool 2",
                            version="1.0.0",
                        ),
                    ],
                )

            async def execute_tool(
                self, tool_id: str, parameters: Dict[str, Any], stream: bool = False
            ) -> BaseResponse[ToolResult]:
                request_id = uuid.uuid4()
                return BaseResponse(
                    request_id=request_id,
                    success=True,
                    data=ToolResult(
                        tool_id=tool_id,
                        request_id=request_id,
                        status=ToolResultStatus.SUCCESS,
                        data={"value": "Tool execution result"},
                    ),
                )

            async def execute_streaming_tool(
                self, tool_id: str, parameters: Dict[str, Any]
            ) -> AsyncIterable[ToolResult]:
                # In a real implementation, this would be an async generator
                raise NotImplementedError("Not implemented for test")

            async def get_tool_schema(
                self, tool_id: str
            ) -> BaseResponse[Dict[str, Any]]:
                return BaseResponse(
                    request_id=uuid.uuid4(),
                    success=True,
                    data={
                        "type": "object",
                        "properties": {
                            "param1": {"type": "string"},
                            "param2": {"type": "number"},
                        },
                        "required": ["param1"],
                    },
                )

        # Check that the implementation satisfies the interface
        service = ConcreteToolService()
        assert isinstance(service, ToolServiceInterface)

        # Call some methods to verify
        tool_def = ToolDefinition(
            tool_id="new-tool",
            name="new-tool",
            description="A new test tool",
            version="1.0.0",
        )

        response = await service.register_tool(tool_def)
        assert response.success is True
        assert response.data.name == "new-tool"

        response = await service.execute_tool(
            tool_id="new-tool", parameters={"input": "test input"}
        )
        assert response.success is True
        assert response.data.tool_id == "new-tool"
        assert response.data.status == ToolResultStatus.SUCCESS
        assert response.data.data["value"] == "Tool execution result"


class TestServiceErrors:
    """Tests for service error classes."""

    def test_service_error(self):
        """Test ServiceError."""
        error = ServiceError(
            message="Test error",
            code="test_error",
            status_code=500,
            details={"more": "info"},
        )

        assert error.message == "Test error"
        assert error.code == "test_error"
        assert error.status_code == 500
        assert error.details == {"more": "info"}

        error_dict = error.to_dict()
        assert error_dict["code"] == "test_error"
        assert error_dict["message"] == "Test error"
        assert error_dict["details"] == {"more": "info"}

    def test_not_found_error(self):
        """Test NotFoundError."""
        error = NotFoundError(
            message="Agent not found", resource_type="agent", resource_id="123"
        )

        assert error.message == "Agent not found"
        assert error.code == "not_found"
        assert error.status_code == 404
        assert error.details["resource_type"] == "agent"
        assert error.details["resource_id"] == "123"

    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError(message="Invalid input", field="name")

        assert error.message == "Invalid input"
        assert error.code == "validation_error"
        assert error.status_code == 400
        assert error.details["field"] == "name"

    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError()

        assert error.message == "Authentication failed"
        assert error.code == "authentication_error"
        assert error.status_code == 401

        custom_error = AuthenticationError(
            message="Invalid token", details={"token_type": "expired"}
        )

        assert custom_error.message == "Invalid token"
        assert custom_error.details["token_type"] == "expired"
