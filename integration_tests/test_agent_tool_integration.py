"""
Agent-Tool服务集成测试。

此模块测试Agent服务与Tool服务间通过shared_contracts进行交互的场景。
"""

import uuid
from typing import Any, Dict

import pytest

from shared_contracts.core.interfaces.tool_interface import ToolServiceInterface
from shared_contracts.core.models.agent_models import (
    AgentCapability,
    AgentConfig,
)
from shared_contracts.core.models.base_models import BaseResponse
from shared_contracts.core.models.tool_models import (
    ToolDefinition,
    ToolParameter,
    ToolParameterType,
    ToolResult,
    ToolResultStatus,
)
from shared_contracts.monitoring import (
    ServiceComponent,
    configure_monitor,
    track_performance,
    with_monitoring,
)


# 模拟Tool服务实现
class MockToolService:
    """Tool服务的模拟实现。"""

    def __init__(self):
        """初始化服务。"""
        self.tools = {}

    @with_monitoring(component=ServiceComponent.TOOL_SERVICE)
    async def register_tool(
        self, definition: ToolDefinition
    ) -> BaseResponse[ToolDefinition]:
        """注册一个工具。"""
        self.tools[definition.tool_id] = definition
        return BaseResponse(request_id=uuid.uuid4(), success=True, data=definition)

    @with_monitoring(component=ServiceComponent.TOOL_SERVICE)
    async def get_tool(self, tool_id: str) -> BaseResponse[ToolDefinition]:
        """获取工具定义。"""
        if tool_id not in self.tools:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Tool {tool_id} not found",
            )

        return BaseResponse(
            request_id=uuid.uuid4(), success=True, data=self.tools[tool_id]
        )

    @with_monitoring(component=ServiceComponent.TOOL_SERVICE)
    async def execute_tool(
        self, tool_id: str, parameters: Dict[str, Any]
    ) -> BaseResponse[ToolResult]:
        """执行工具。"""
        # 检查工具是否存在
        if tool_id not in self.tools:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Tool {tool_id} not found",
            )

        # 简单模拟不同工具的行为
        result = None
        request_id = uuid.uuid4()

        if tool_id == "calculator":
            # 计算器工具
            operation = parameters.get("operation")
            a = parameters.get("a", 0)
            b = parameters.get("b", 0)

            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    return BaseResponse(
                        request_id=request_id,
                        success=True,
                        data=ToolResult(
                            tool_id=tool_id,
                            request_id=request_id,
                            status=ToolResultStatus.ERROR,
                            error="Division by zero",
                        ),
                    )
                result = a / b
            else:
                return BaseResponse(
                    request_id=request_id,
                    success=True,
                    data=ToolResult(
                        tool_id=tool_id,
                        request_id=request_id,
                        status=ToolResultStatus.ERROR,
                        error=f"Unknown operation: {operation}",
                    ),
                )

            return BaseResponse(
                request_id=request_id,
                success=True,
                data=ToolResult(
                    tool_id=tool_id,
                    request_id=request_id,
                    status=ToolResultStatus.SUCCESS,
                    data={"result": result},
                ),
            )

        elif tool_id == "weather":
            # 天气工具
            location = parameters.get("location", "unknown")
            return BaseResponse(
                request_id=request_id,
                success=True,
                data=ToolResult(
                    tool_id=tool_id,
                    request_id=request_id,
                    status=ToolResultStatus.SUCCESS,
                    data={
                        "location": location,
                        "temperature": 22,
                        "condition": "sunny",
                        "humidity": 65,
                    },
                ),
            )

        else:
            # 通用响应
            return BaseResponse(
                request_id=request_id,
                success=True,
                data=ToolResult(
                    tool_id=tool_id,
                    request_id=request_id,
                    status=ToolResultStatus.SUCCESS,
                    data={"parameters": parameters},
                ),
            )


# 模拟Agent服务实现
class MockAgentWithTools:
    """具有工具使用能力的Agent服务模拟实现。"""

    def __init__(self, tool_service: ToolServiceInterface):
        """
        初始化服务。

        Args:
            tool_service: Tool服务接口
        """
        self.agents = {}
        self.tool_service = tool_service

    @with_monitoring(component=ServiceComponent.AGENT_CORE)
    async def create_agent(self, config: AgentConfig) -> BaseResponse[AgentConfig]:
        """创建一个代理。"""
        # 检查工具可用性
        for tool_id in config.tools:
            tool_response = await self.tool_service.get_tool(tool_id)
            if not tool_response.success:
                return BaseResponse(
                    request_id=uuid.uuid4(),
                    success=False,
                    error=f"Agent creation failed: Tool {tool_id} not found",
                )

        # 存储代理配置
        agent_id = config.agent_id or uuid.uuid4()
        config.agent_id = agent_id
        self.agents[agent_id] = config

        return BaseResponse(request_id=uuid.uuid4(), success=True, data=config)

    @with_monitoring(component=ServiceComponent.AGENT_CORE)
    async def get_agent(self, agent_id: uuid.UUID) -> BaseResponse[AgentConfig]:
        """获取代理配置。"""
        if agent_id not in self.agents:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Agent {agent_id} not found",
            )

        return BaseResponse(
            request_id=uuid.uuid4(), success=True, data=self.agents[agent_id]
        )

    @with_monitoring(component=ServiceComponent.AGENT_CORE)
    async def use_tool(
        self, agent_id: uuid.UUID, tool_id: str, parameters: Dict[str, Any]
    ) -> BaseResponse[Dict[str, Any]]:
        """
        使用工具。

        此方法会检查代理是否有权限使用该工具，然后调用Tool服务执行工具。
        """
        # 检查代理是否存在
        if agent_id not in self.agents:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Agent {agent_id} not found",
            )

        agent_config = self.agents[agent_id]

        # 检查代理是否具有工具使用能力
        if AgentCapability.TOOL_USE not in agent_config.capabilities:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error="Agent does not have tool use capability",
            )

        # 检查代理是否有权限使用该工具
        if tool_id not in agent_config.tools:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Agent does not have permission to use tool {tool_id}",
            )

        # 调用Tool服务执行工具
        with track_performance("tool_execution", ServiceComponent.AGENT_CORE) as span:
            response = await self.tool_service.execute_tool(
                tool_id=tool_id, parameters=parameters
            )

            span.add_data(
                {
                    "agent_id": str(agent_id),
                    "tool_id": tool_id,
                    "parameters": str(parameters),
                }
            )

        if not response.success:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Failed to execute tool: {response.error}",
            )

        # 处理响应
        tool_result = response.data

        if tool_result.status == ToolResultStatus.ERROR:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=tool_result.error or "Unknown tool error",
            )

        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data={"tool_id": tool_id, "result": tool_result.data},
        )


@pytest.fixture
def setup_monitor():
    """设置监控客户端。"""
    try:
        # 使用内存配置（不实际连接到LogFire）
        # config = LogFireConfig(  # 未使用变量: config
        #     api_key="test_key",
        #     project_id="test_project",
        #     service_name="integration-test",
        #     environment="test",
        #     api_endpoint="memory://logfire",  # 使用内存模式
        # )

        # 配置监控客户端
        monitor = configure_monitor(
            service_name="integration-test",
            api_key="test_key",
            project_id="test_project",
            environment="test",
        )

        yield monitor

        # 测试后刷新并关闭监控客户端
        monitor.flush()
        monitor.shutdown()
    except Exception as e:
        pytest.skip(f"监控设置失败: {e}")


@pytest.mark.asyncio
async def test_agent_tool_integration(setup_monitor):
    """测试Agent服务与Tool服务间的集成。"""
    # 创建Tool服务
    tool_service = MockToolService()

    # 注册计算器工具
    calculator_tool = ToolDefinition(
        tool_id="calculator",
        name="Calculator",
        description="A simple calculator tool",
        version="1.0.0",
    )

    # 添加参数
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

    calculator_tool.parameters.parameters = {
        "operation": operation_param,
        "a": a_param,
        "b": b_param,
    }

    await tool_service.register_tool(calculator_tool)

    # 注册天气工具
    weather_tool = ToolDefinition(
        tool_id="weather",
        name="Weather",
        description="Get weather information for a location",
        version="1.0.0",
    )

    location_param = ToolParameter(
        name="location",
        description="Location to get weather for",
        type=ToolParameterType.STRING,
    )

    weather_tool.parameters.parameters = {"location": location_param}

    await tool_service.register_tool(weather_tool)

    # 创建Agent服务
    agent_service = MockAgentWithTools(tool_service)

    # 创建一个具有工具使用能力的代理
    agent_config = AgentConfig(
        name="Tool User Agent",
        description="An agent that can use tools",
        model_id="gpt-4",  # 虽然没有用到模型服务，但需要指定
        system_prompt="You are a helpful assistant that can use tools.",
        capabilities={AgentCapability.CONVERSATION, AgentCapability.TOOL_USE},
        tools=["calculator", "weather"],  # 允许使用的工具
    )

    response = await agent_service.create_agent(agent_config)
    assert response.success, f"创建代理失败: {response.error}"

    agent_id = response.data.agent_id

    # 测试使用计算器工具
    calc_response = await agent_service.use_tool(
        agent_id=agent_id,
        tool_id="calculator",
        parameters={"operation": "add", "a": 5, "b": 3},
    )

    # 验证计算器工具结果
    assert calc_response.success, f"使用计算器工具失败: {calc_response.error}"
    assert calc_response.data["tool_id"] == "calculator"
    assert calc_response.data["result"]["result"] == 8

    # 测试使用天气工具
    weather_response = await agent_service.use_tool(
        agent_id=agent_id, tool_id="weather", parameters={"location": "Shanghai"}
    )

    # 验证天气工具结果
    assert weather_response.success, f"使用天气工具失败: {weather_response.error}"
    assert weather_response.data["tool_id"] == "weather"
    assert weather_response.data["result"]["location"] == "Shanghai"
    assert "temperature" in weather_response.data["result"]

    # 测试使用未授权的工具（创建一个新工具但不授权给代理）
    new_tool = ToolDefinition(
        tool_id="search", name="Search", description="Search the web", version="1.0.0"
    )

    await tool_service.register_tool(new_tool)

    unauthorized_response = await agent_service.use_tool(
        agent_id=agent_id, tool_id="search", parameters={"query": "test"}
    )

    # 验证未授权工具访问被拒绝
    assert not unauthorized_response.success
    assert "does not have permission" in unauthorized_response.error

    print("集成测试成功完成！")
    print(f"计算器工具结果: {calc_response.data['result']}")
    print(f"天气工具结果: {weather_response.data['result']}")
