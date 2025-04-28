"""Pytest配置文件，用于配置集成测试的环境...."""

import os
import sys
from unittest.mock import patch

import pytest

from shared_contracts.monitoring import MonitorInterface, configure_monitor
from tests.helpers.fixtures import (
    agent_config,
    calculator_tool,
    current_timestamp,
    data_factory,
    error_response,
    model_capability,
    model_config,
    model_response,
    request_id,
    success_response,
    test_monitor,
    tool_result,
)
from tests.helpers.mock_services import (
    MockAgentService,
    MockModelService,
    MockToolService,
)


def pytest_configure(config):
    """配置Pytest。...."""
    # 将项目根目录添加到Python路径
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)

    # 启用asyncio模式
    config.option.asyncio_mode = "strict"


@pytest.fixture(scope="session", autouse=True)
def mock_logfire_api():
    """
    Mock LogFire API调用，避免在测试中实际调用外部服务。

    此fixture会在所有测试运行前自动应用，防止测试过程中发送实际网络请求。
 ..."""
    # 模拟HTTP客户端的post方法
    with patch("httpx.AsyncClient.post") as mock_post:
        # 设置mock返回成功响应
        mock_response = type("MockResponse", (), {"status_code": 200, "text": "OK"})()
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture(scope="function")
def setup_monitor():
    """设置监控客户端。...."""
    try:
        # 使用内存配置（不实际连接到LogFire）
        monitor = configure_monitor(
            service_name="integration-test",
            api_key="test_key",
            project_id="test_project",
            environment="test",
            use_local_logging=True,
        )

        yield monitor

        # 测试后刷新并关闭监控客户端
        monitor.flush()
        monitor.shutdown()
    except Exception as e:
        pytest.skip(f"监控设置失败: {e}")


@pytest.fixture(scope="function")
def setup_services(setup_monitor):
    """设置模拟服务。...."""
    monitor = setup_monitor
    model_service = MockModelService(monitor)
    tool_service = MockToolService(monitor)
    agent_service = MockAgentService(model_service, tool_service, monitor)

    return {
        "monitor": monitor,
        "model_service": model_service,
        "tool_service": tool_service,
        "agent_service": agent_service,
    }
