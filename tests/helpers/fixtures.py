"""
通用测试夹具。

这个模块提供了跨多个测试文件使用的共享夹具，包括模拟对象和测试数..."""

import os
import uuid
from datetime import datetime
from typing import Any, Dict, Generator, Optional
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

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
    ToolParameter,
    ToolParameterType,
    ToolResult,
    ToolResultStatus,
)
from shared_contracts.monitoring import (
    MonitorInterface,
    ServiceComponent,
    configure_monitor,
)


# 基础夹具
@pytest.fixture
def request_id() -> uuid.UUID:
    """返回固定的请求ID，用于测试中的可预测性。...."""
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def current_timestamp() -> datetime:
    """返回固定的时间戳，用于测试中的可预测性。...."""
    return datetime(2023, 1, 1, 12, 0, 0)


# 模型夹具
@pytest.fixture
def model_capability() -> ModelCapability:
    """创建标准模型能力配置。...."""
    return ModelCapability(
        supports_streaming=True,
        supports_function_calling=True,
        supports_json_mode=True,
        supports_vision=False,
        max_tokens=8192,
    )


@pytest.fixture
def model_config(model_capability: ModelCapability) -> ModelConfig:
    """创建标准模型配置。...."""
    return ModelConfig(
        model_id="test-model",
        provider=ModelProvider.OPENAI,
        model_type=ModelType.CHAT,
        display_name="Test Model",
        capabilities=model_capability,
        provider_model_id="gpt-4",
        api_key_env_var="TEST_API_KEY",
    )


@pytest.fixture
def model_response(request_id: uuid.UUID) -> ModelResponse:
    """创建标准模型响应。...."""
    return ModelResponse(
        model_id="test-model",
        request_id=request_id,
        content="This is a test response",
        usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        finish_reason="stop",
    )


# 代理夹具
@pytest.fixture
def agent_config() -> AgentConfig:
    """创建标准代理配置。...."""
    return AgentConfig(
        name="Test Agent",
        description="A test agent",
        model_id="test-model",
        system_prompt="You are a helpful assistant",
        capabilities={AgentCapability.CONVERSATION, AgentCapability.TOOL_USE},
        tools=["calculator", "weather"],
    )


@pytest.fixture
def agent_state(request_id: uuid.UUID, current_timestamp: datetime) -> AgentState:
    """创建标准代理状态。...."""
    return AgentState(
        agent_id=request_id,
        status=AgentStatus.READY,
        created_at=current_timestamp,
        last_active=current_timestamp,
    )


# 工具夹具
@pytest.fixture
def calculator_tool() -> ToolDefinition:
    """创建计算器工具定义。...."""
    tool = ToolDefinition(
        tool_id="calculator",
        name="Calculator",
        description="A simple calculator tool",
        version="1.0.0",
    )

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

    tool.parameters.parameters = {
        "operation": operation_param,
        "a": a_param,
        "b": b_param,
    }

    return tool


@pytest.fixture
def tool_result(request_id: uuid.UUID) -> ToolResult:
    """创建标准工具结果。...."""
    return ToolResult(
        tool_id="calculator",
        request_id=request_id,
        status=ToolResultStatus.SUCCESS,
        data={"result": 8},
    )


# 响应夹具
@pytest.fixture
def success_response(request_id: uuid.UUID, current_timestamp: datetime) -> BaseResponse:  # noqa: E501
    """创建成功响应。...."""
    return BaseResponse[Dict[str, Any]](
        request_id=request_id,
        timestamp=current_timestamp,
        success=True,
        data={"key": "value"},
        status="success",
    )


@pytest.fixture
def error_response(request_id: uuid.UUID, current_timestamp: datetime) -> BaseResponse:
    """创建错误响应。...."""
    return BaseResponse[Dict[str, Any]](
        request_id=request_id,
        timestamp=current_timestamp,
        success=False,
        error="Test error",
        status="error",
    )


# 监控夹具
@pytest.fixture
def mock_monitor() -> Generator[MonitorInterface, None, None]:
    """创建模拟监控对象。...."""
    with patch("shared_contracts.monitoring.monitor_interface.MonitorInterface") as mock:  # noqa: E501
        monitor = MagicMock()
        mock.return_value = monitor
        yield monitor


@pytest.fixture
def test_monitor() -> Generator[MonitorInterface, None, None]:
    """创建实际的测试监控对象，带内存记录器。...."""
    # 设置测试环境变量
    os.environ["TESTING"] = "1"
    # 配置内存监控
    monitor = configure_monitor(
        service_name="test", environment="test", use_local_logging=True
    )
    yield monitor
    # 清理
    monitor.flush()
    monitor.shutdown()
    if "TESTING" in os.environ:
        del os.environ["TESTING"]


# 模拟服务夹具
@pytest.fixture
def mock_httpx_client() -> Generator[MagicMock, None, None]:
    """模拟HTTP客户端。...."""
    with patch("httpx.AsyncClient") as mock:
        client = MagicMock()
        mock.return_value.__aenter__.return_value = client
        # 设置默认响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.text = '{"success": true}'
        client.post.return_value = mock_response
        client.get.return_value = mock_response
        yield client


# 自定义数据工厂
class DataFactory:
    """创建测试数据的工厂类。...."""

    @staticmethod
    def create_model_dict(model_id: str = "test-model") -> Dict[str, Any]:
        """创建模型配置字典。...."""
        return {
            "model_id": model_id,
            "provider": "openai",
            "model_type": "chat",
            "display_name": f"Test {model_id.title()}",
            "capabilities": {
                "supports_streaming": True,
                "supports_function_calling": True,
                "supports_json_mode": True,
                "supports_vision": False,
                "max_tokens": 8192,
            },
            "provider_model_id": "gpt-4",
            "api_key_env_var": "TEST_API_KEY",
        }

    @staticmethod
    def create_agent_dict(name: str = "Test Agent") -> Dict[str, Any]:
        """创建代理配置字典。...."""
        return {
            "name": name,
            "description": f"A test agent named {name}",
            "model_id": "test-model",
            "system_prompt": "You are a helpful assistant",
            "capabilities": ["conversation", "tool_use"],
            "tools": ["calculator", "weather"],
        }


@pytest.fixture
def data_factory() -> DataFactory:
    """返回数据工厂实例。...."""
    return DataFactory()
