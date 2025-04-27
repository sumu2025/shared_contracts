"""
完整工作流集成测试。

此模块测试Agent、Model和Tool服务间的完整交互场景，同时使用监控工具追踪数据流。
"""

import json
import uuid
from typing import Any, Dict, Optional

import pytest

from shared_contracts.core.models.agent_models import AgentCapability, AgentConfig
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
    EventType,
    MonitorInterface,
    ServiceComponent,
    configure_monitor,
    track_performance,
    with_monitoring,
)


# 模拟模型服务
class MockModelService:
    """Model服务的模拟实现。"""

    def __init__(self, monitor: MonitorInterface):
        """初始化服务。"""
        self.models = {}
        self.monitor = monitor

    @with_monitoring(component=ServiceComponent.MODEL_SERVICE)
    async def register_model(self, config: ModelConfig) -> BaseResponse[ModelConfig]:
        """注册一个模型。"""
        self.models[config.model_id] = config
        self.monitor.info(
            f"Model registered: {config.model_id}",
            component=ServiceComponent.MODEL_SERVICE,
            event_type=EventType.SYSTEM,
            model_id=config.model_id,
        )
        return BaseResponse(request_id=uuid.uuid4(), success=True, data=config)

    @with_monitoring(component=ServiceComponent.MODEL_SERVICE)
    async def generate_completion(
        self,
        model_id: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **options: Any,
    ) -> BaseResponse[ModelResponse]:
        """生成文本完成。"""
        request_id = uuid.uuid4()

        self.monitor.info(
            f"Generating completion with model {model_id}",
            component=ServiceComponent.MODEL_SERVICE,
            event_type=EventType.REQUEST,
            model_id=model_id,
            prompt_length=len(prompt),
        )

        # 简单模拟模型行为 - 解析工具调用
        if "use the calculator tool" in prompt.lower():
            # 模拟模型识别出需要使用计算器工具
            content = {
                "content": "I'll help you with this calculation.",
                "tool_calls": [
                    {
                        "tool_id": "calculator",
                        "parameters": {"operation": "add", "a": 5, "b": 3},
                    }
                ],
            }
        elif "use the weather tool" in prompt.lower():
            # 模拟模型识别出需要使用天气工具
            content = {
                "content": "I'll check the weather for you.",
                "tool_calls": [
                    {"tool_id": "weather", "parameters": {"location": "Shanghai"}}
                ],
            }
        else:
            # 普通响应
            content = {"content": f"This is a response to: {prompt}"}

        # 创建响应
        response = ModelResponse(
            model_id=model_id,
            request_id=request_id,
            content=json.dumps(content),
            usage={
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": 10,
                "total_tokens": len(prompt.split()) + 10,
            },
            finish_reason="stop",
        )

        self.monitor.info(
            "Completion generated",
            component=ServiceComponent.MODEL_SERVICE,
            event_type=EventType.RESPONSE,
            model_id=model_id,
            response_length=len(response.content),
            usage=response.usage,
        )

        return BaseResponse(request_id=request_id, success=True, data=response)


# 模拟工具服务
class MockToolService:
    """Tool服务的模拟实现。"""

    def __init__(self, monitor: MonitorInterface):
        """初始化服务。"""
        self.tools = {}
        self.monitor = monitor

    @with_monitoring(component=ServiceComponent.TOOL_SERVICE)
    async def register_tool(
        self, definition: ToolDefinition
    ) -> BaseResponse[ToolDefinition]:
        """注册一个工具。"""
        self.tools[definition.tool_id] = definition
        self.monitor.info(
            f"Tool registered: {definition.tool_id}",
            component=ServiceComponent.TOOL_SERVICE,
            event_type=EventType.SYSTEM,
            tool_id=definition.tool_id,
        )
        return BaseResponse(request_id=uuid.uuid4(), success=True, data=definition)

    @with_monitoring(component=ServiceComponent.TOOL_SERVICE)
    async def execute_tool(
        self, tool_id: str, parameters: Dict[str, Any]
    ) -> BaseResponse[ToolResult]:
        """执行工具。"""
        request_id = uuid.uuid4()

        self.monitor.info(
            f"Executing tool: {tool_id}",
            component=ServiceComponent.TOOL_SERVICE,
            event_type=EventType.REQUEST,
            tool_id=tool_id,
            parameters=parameters,
        )

        # 简单模拟不同工具的行为
        result = None

        if tool_id == "calculator":
            # 计算器工具
            operation = parameters.get("operation")
            a = parameters.get("a", 0)
            b = parameters.get("b", 0)

            if operation == "add":
                result = {"result": a + b}
            elif operation == "subtract":
                result = {"result": a - b}
            elif operation == "multiply":
                result = {"result": a * b}
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
                result = {"result": a / b}
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

        elif tool_id == "weather":
            # 天气工具
            location = parameters.get("location", "unknown")
            result = {
                "location": location,
                "temperature": 22,
                "condition": "sunny",
                "humidity": 65,
            }

        else:
            # 通用响应
            result = {"parameters": parameters}

        tool_result = ToolResult(
            tool_id=tool_id,
            request_id=request_id,
            status=ToolResultStatus.SUCCESS,
            data=result,
        )

        self.monitor.info(
            f"Tool execution completed: {tool_id}",
            component=ServiceComponent.TOOL_SERVICE,
            event_type=EventType.RESPONSE,
            tool_id=tool_id,
            result=result,
        )

        return BaseResponse(request_id=request_id, success=True, data=tool_result)


# 模拟代理服务
class MockAgentService:
    """具有完整能力的Agent服务模拟实现。"""

    def __init__(self, model_service, tool_service, monitor: MonitorInterface):
        """
        初始化服务。

        Args:
            model_service: Model服务接口
            tool_service: Tool服务接口
            monitor: 监控接口
        """
        self.agents = {}
        self.model_service = model_service
        self.tool_service = tool_service
        self.monitor = monitor

    @with_monitoring(component=ServiceComponent.AGENT_CORE)
    async def create_agent(self, config: AgentConfig) -> BaseResponse[AgentConfig]:
        """创建一个代理。"""
        agent_id = config.agent_id or uuid.uuid4()
        config.agent_id = agent_id
        self.agents[agent_id] = config

        self.monitor.info(
            f"Agent created: {config.name}",
            component=ServiceComponent.AGENT_CORE,
            event_type=EventType.SYSTEM,
            agent_id=str(agent_id),
            model_id=config.model_id,
            capabilities=[cap for cap in config.capabilities],
        )

        return BaseResponse(request_id=uuid.uuid4(), success=True, data=config)

    @with_monitoring(component=ServiceComponent.AGENT_CORE)
    async def process_message(
        self,
        agent_id: uuid.UUID,
        message: str,
        conversation_id: Optional[uuid.UUID] = None,
    ) -> BaseResponse[Dict[str, Any]]:
        """
        处理用户消息，包括工具调用。

        这是一个完整的工作流，包括：
        1. 调用Model服务生成响应
        2. 解析响应中的工具调用
        3. 调用Tool服务执行工具
        4. 将工具执行结果返回给Model服务
        5. 生成最终响应
        """
        if agent_id not in self.agents:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Agent {agent_id} not found",
            )

        agent_config = self.agents[agent_id]
        conversation_id = conversation_id or uuid.uuid4()

        self.monitor.info(
            f"Processing message for agent {agent_id}",
            component=ServiceComponent.AGENT_CORE,
            event_type=EventType.REQUEST,
            agent_id=str(agent_id),
            conversation_id=str(conversation_id),
            message_length=len(message),
        )

        # 1. 构建提示词
        prompt = f"{agent_config.system_prompt}\n\nUser: {message}\nAssistant:"

        # 2. 调用模型生成响应
        model_response = await self.model_service.generate_completion(
            model_id=agent_config.model_id,
            prompt=prompt,
            max_tokens=agent_config.max_tokens_per_response,
            temperature=agent_config.temperature,
        )

        if not model_response.success:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Failed to generate response: {model_response.error}",
            )

        # 3. 解析模型响应
        response_json = json.loads(model_response.data.content)
        content = response_json.get("content", "")
        tool_calls = response_json.get("tool_calls", [])

        # 4. 处理工具调用
        tool_results = []

        if tool_calls and AgentCapability.TOOL_USE in agent_config.capabilities:
            for tool_call in tool_calls:
                tool_id = tool_call.get("tool_id")
                parameters = tool_call.get("parameters", {})

                # 检查工具权限
                if tool_id not in agent_config.tools:
                    self.monitor.warning(
                        f"Agent attempted to use unauthorized tool: {tool_id}",
                        component=ServiceComponent.AGENT_CORE,
                        event_type=EventType.SYSTEM,
                        agent_id=str(agent_id),
                        tool_id=tool_id,
                    )
                    continue

                # 执行工具
                with track_performance(
                    "tool_execution", ServiceComponent.AGENT_CORE
                ) as span:
                    tool_response = await self.tool_service.execute_tool(
                        tool_id=tool_id, parameters=parameters
                    )

                    span.add_data(
                        {
                            "agent_id": str(agent_id),
                            "tool_id": tool_id,
                            "parameters": str(parameters),
                        }
                    )

                if tool_response.success:
                    tool_results.append(
                        {
                            "tool_id": tool_id,
                            "status": tool_response.data.status,
                            "result": tool_response.data.data
                            if tool_response.data.status == ToolResultStatus.SUCCESS
                            else None,
                            "error": tool_response.data.error
                            if tool_response.data.status == ToolResultStatus.ERROR
                            else None,
                        }
                    )

        # 5. 构建最终响应
        final_response = {
            "message": content,
            "conversation_id": str(conversation_id),
            "usage": model_response.data.usage,
            "tool_results": tool_results,
        }

        self.monitor.info(
            f"Message processing completed for agent {agent_id}",
            component=ServiceComponent.AGENT_CORE,
            event_type=EventType.RESPONSE,
            agent_id=str(agent_id),
            conversation_id=str(conversation_id),
            tool_count=len(tool_results),
        )

        return BaseResponse(request_id=uuid.uuid4(), success=True, data=final_response)


@pytest.fixture
def setup_monitor():
    """设置监控客户端。"""
    try:
        # 使用内存配置（不实际连接到LogFire）
        monitor = configure_monitor(
            service_name="complete-workflow-test",
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
async def test_complete_workflow(setup_monitor):
    """测试完整工作流，包括Agent、Model和Tool服务间的交互。"""
    monitor = setup_monitor

    # 1. 初始化服务
    model_service = MockModelService(monitor)
    tool_service = MockToolService(monitor)
    agent_service = MockAgentService(model_service, tool_service, monitor)

    # 2. 注册模型
    capabilities = ModelCapability(
        supports_streaming=True,
        supports_function_calling=True,
        supports_json_mode=True,
        supports_vision=False,
        max_tokens=4096,
    )

    model_config = ModelConfig(
        model_id="gpt-4",
        provider=ModelProvider.OPENAI,
        model_type=ModelType.CHAT,
        display_name="GPT-4",
        capabilities=capabilities,
        provider_model_id="gpt-4",
        api_key_env_var="OPENAI_API_KEY",
    )

    await model_service.register_model(model_config)

    # 3. 注册工具
    # 计算器工具
    calculator_tool = ToolDefinition(
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

    calculator_tool.parameters.parameters = {
        "operation": operation_param,
        "a": a_param,
        "b": b_param,
    }

    await tool_service.register_tool(calculator_tool)

    # 天气工具
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

    # 4. 创建代理
    agent_config = AgentConfig(
        name="Assistant Agent",
        description="An agent that can use models and tools",
        model_id="gpt-4",
        system_prompt="You are a helpful assistant that can use tools.",
        capabilities={AgentCapability.CONVERSATION, AgentCapability.TOOL_USE},
        tools=["calculator", "weather"],
        max_tokens_per_response=1000,
        temperature=0.7,
    )

    create_response = await agent_service.create_agent(agent_config)
    assert create_response.success, f"创建代理失败: {create_response.error}"

    agent_id = create_response.data.agent_id

    # 5. 测试计算器工具调用
    calc_message = "Please use the calculator tool to add 5 and 3."

    calc_response = await agent_service.process_message(
        agent_id=agent_id, message=calc_message
    )

    assert calc_response.success, f"处理消息失败: {calc_response.error}"
    assert len(calc_response.data["tool_results"]) > 0, "没有执行计算器工具"
    assert calc_response.data["tool_results"][0]["tool_id"] == "calculator"
    assert calc_response.data["tool_results"][0]["result"]["result"] == 8

    # 6. 测试天气工具调用
    weather_message = "Please use the weather tool to check the weather in Shanghai."

    weather_response = await agent_service.process_message(
        agent_id=agent_id, message=weather_message
    )

    assert weather_response.success, f"处理消息失败: {weather_response.error}"
    assert len(weather_response.data["tool_results"]) > 0, "没有执行天气工具"
    assert weather_response.data["tool_results"][0]["tool_id"] == "weather"
    assert weather_response.data["tool_results"][0]["result"]["location"] == "Shanghai"

    # 7. 测试普通对话（不使用工具）
    chat_message = "Hello, how are you today?"

    chat_response = await agent_service.process_message(
        agent_id=agent_id, message=chat_message
    )

    assert chat_response.success, f"处理消息失败: {chat_response.error}"
    assert len(chat_response.data["tool_results"]) == 0, "不应该执行任何工具"
    assert "message" in chat_response.data

    print("完整工作流集成测试成功完成！")
    print(f"计算器调用结果: {calc_response.data['tool_results'][0]['result']}")
    print(f"天气调用结果: {weather_response.data['tool_results'][0]['result']}")
    print(f"普通对话响应: {chat_response.data['message']}")
