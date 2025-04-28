"""Tests for core data models in agentforge-contracts...."""

import uuid
from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from shared_contracts.core.models.agent_models import (
    AgentCapability,
    AgentConfig,
    AgentState,
    AgentStatus,
)
from shared_contracts.core.models.base_models import (
    BaseModel,
    BaseRequest,
    BaseResponse,
)
from shared_contracts.core.models.model_models import (
    ModelCapability,
    ModelConfig,
    ModelProvider,
    ModelResponse,
    ModelType,
)
from shared_contracts.core.models.tool_models import (
    ToolDefinition,
    ToolParameter,
    ToolParameters,
    ToolParameterType,
    ToolResult,
    ToolResultStatus,
)


class TestBaseModels:
    """Tests for base models...."""

    def test_base_model(self):
        """Test BaseModel validation...."""

        class TestModel(BaseModel):
            name: str
            value: int

        # Valid model
        model = TestModel(name="test", value=42)
        assert model.name == "test"
        assert model.value == 42

        # Extra fields should be rejected
        with pytest.raises(ValidationError):
            TestModel(name="test", value=42, extra_field="should fail")

    def test_base_request(self):
        """Test BaseRequest...."""
        # Default creation
        request = BaseRequest()
        assert isinstance(request.request_id, uuid.UUID)
        assert isinstance(request.timestamp, datetime)

        # Custom values
        custom_id = uuid.uuid4()
        custom_time = datetime.now()
        request = BaseRequest(request_id=custom_id, timestamp=custom_time)
        assert request.request_id == custom_id
        assert request.timestamp == custom_time

    def test_base_response(self):
        """Test BaseResponse...."""
        # Success response
        request_id = uuid.uuid4()
        success_response = BaseResponse[str](
            request_id=request_id, success=True, data="test data"
        )
        assert success_response.request_id == request_id
        assert success_response.success is True
        assert success_response.data == "test data"
        assert success_response.error is None

        # Error response
        error_response = BaseResponse[str](
            request_id=request_id, success=False, error="Something went wrong"
        )
        assert error_response.request_id == request_id
        assert error_response.success is False
        assert error_response.data is None
        assert error_response.error == "Something went wrong"

        # Invalid responses
        with pytest.raises(ValidationError):
            # Success without data
            BaseResponse[str](request_id=request_id, success=True)

        with pytest.raises(ValidationError):
            # Error without error message
            BaseResponse[str](request_id=request_id, success=False)

    def test_serialization_deserialization(self):
        """Test JSON serialization and deserialization...."""
        request_id = uuid.uuid4()
        response = BaseResponse[dict](
            request_id=request_id, success=True, data={"key": "value"}
        )

        # Serialize to JSON
        json_str = response.model_dump_json()

        # Deserialize from JSON
        loaded = BaseResponse.model_validate_json(json_str)

        assert loaded.request_id == response.request_id
        assert loaded.success == response.success
        assert loaded.data == response.data


class TestAgentModels:
    """Tests for agent models...."""

    def test_agent_config(self):
        """Test AgentConfig validation...."""
        # Create a minimal valid config
        config = AgentConfig(
            name="Test Agent",
            description="A test agent",
            model_id="gpt-4",
            system_prompt="You are a helpful assistant",
            capabilities={AgentCapability.CONVERSATION, AgentCapability.TOOL_USE},
        )

        assert config.name == "Test Agent"
        assert config.description == "A test agent"
        assert AgentCapability.CONVERSATION in config.capabilities
        assert config.model_id == "gpt-4"
        assert config.system_prompt == "You are a helpful assistant"

    def test_agent_state(self):
        """Test AgentState...."""
        # Create a state
        current_time = datetime.now()
        state = AgentState(
            agent_id=uuid.uuid4(),
            status=AgentStatus.READY,
            created_at=current_time - timedelta(hours=1),
            last_active=current_time,
        )

        assert state.status == AgentStatus.READY
        assert isinstance(state.last_active, datetime)
        assert isinstance(state.created_at, datetime)

        # Test serialization
        json_str = state.model_dump_json()
        loaded = AgentState.model_validate_json(json_str)

        assert loaded.agent_id == state.agent_id
        assert loaded.status == state.status


class TestToolModels:
    """Tests for tool models...."""

    def test_tool_definition(self):
        """Test ToolDefinition validation...."""
        # Create a tool definition
        tool_def = ToolDefinition(
            tool_id="calculator",
            name="calculator",
            description="A simple calculator tool",
            version="1.0.0",
        )

        # Add parameters
        param1 = ToolParameter(
            name="operation",
            description="Operation to perform",
            type=ToolParameterType.STRING,
            enum=["add", "subtract", "multiply", "divide"],
        )

        param2 = ToolParameter(
            name="a", description="First number", type=ToolParameterType.NUMBER
        )

        param3 = ToolParameter(
            name="b", description="Second number", type=ToolParameterType.NUMBER
        )

        tool_def.parameters.parameters = {"operation": param1, "a": param2, "b": param3}

        assert tool_def.tool_id == "calculator"
        assert tool_def.name == "calculator"
        assert "operation" in tool_def.parameters.parameters

    def test_tool_parameters(self):
        """Test ToolParameters...."""
        # Create parameters
        operation_param = ToolParameter(
            name="operation",
            description="Operation to perform",
            type=ToolParameterType.STRING,
            enum=["add", "subtract", "multiply", "divide"],
        )

        a_param = ToolParameter(
            name="a", description="First number", type=ToolParameterType.NUMBER
        )

        b_param = ToolParameter(
            name="b", description="Second number", type=ToolParameterType.NUMBER
        )

        params = ToolParameters(
            parameters={"operation": operation_param, "a": a_param, "b": b_param}
        )

        # Test to_json_schema
        schema = params.to_json_schema()
        assert schema["type"] == "object"
        assert "operation" in schema["properties"]
        assert "a" in schema["properties"]
        assert "b" in schema["properties"]

    def test_tool_result(self):
        """Test ToolResult...."""
        # Create a success result
        request_id = uuid.uuid4()
        result = ToolResult(
            tool_id="calculator",
            request_id=request_id,
            status=ToolResultStatus.SUCCESS,
            data={"value": 8},
        )

        assert result.tool_id == "calculator"
        assert result.request_id == request_id
        assert result.status == ToolResultStatus.SUCCESS
        assert result.data == {"value": 8}

        # Error result
        error_result = ToolResult(
            tool_id="calculator",
            request_id=uuid.uuid4(),
            status=ToolResultStatus.ERROR,
            error="Division by zero",
        )

        assert error_result.status == ToolResultStatus.ERROR
        assert error_result.error == "Division by zero"
        assert error_result.data is None


class TestModelModels:
    """Tests for model-related models...."""

    def test_model_config(self):
        """Test ModelConfig validation...."""
        # Create a model config with required capabilities model
        capabilities = ModelCapability(
            supports_streaming=True,
            supports_function_calling=True,
            supports_json_mode=True,
            supports_vision=False,
            max_tokens=8192,
        )

        config = ModelConfig(
            model_id="gpt-4",
            provider=ModelProvider.OPENAI,
            model_type=ModelType.CHAT,
            display_name="GPT-4",
            capabilities=capabilities,
            provider_model_id="gpt-4-turbo",
            api_key_env_var="OPENAI_API_KEY",
        )

        assert config.model_id == "gpt-4"
        assert config.provider == ModelProvider.OPENAI
        assert config.model_type == ModelType.CHAT
        assert config.display_name == "GPT-4"
        assert config.capabilities.max_tokens == 8192
        assert config.provider_model_id == "gpt-4-turbo"
        assert config.api_key_env_var == "OPENAI_API_KEY"

    def test_model_response(self):
        """Test ModelResponse...."""
        # Create a response
        request_id = uuid.uuid4()
        response = ModelResponse(
            model_id="gpt-4",
            request_id=request_id,
            content="This is a test response",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            finish_reason="stop",
        )

        assert response.model_id == "gpt-4"
        assert response.request_id == request_id
        assert response.content == "This is a test response"
        assert response.usage["total_tokens"] == 15
        assert response.finish_reason == "stop"
