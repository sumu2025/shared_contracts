"""
Pytest配置文件，用于配置集成测试的环境。
"""

import os
import sys
from unittest.mock import patch

import pytest


def pytest_configure(config):
    """配置Pytest。"""
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
    """
    # 模拟HTTP客户端的post方法
    with patch("httpx.AsyncClient.post") as mock_post:
        # 设置mock返回成功响应
        mock_response = type("MockResponse", (), {"status_code": 200, "text": "OK"})()
        mock_post.return_value = mock_response
        yield mock_post
