"""
模拟服务实现。

提供标准化的模拟服务实现，用于集成测试和功能测..."""

import json
import uuid
from typing import Any, Callable, Dict, List, Optional, Union

from shared_contracts.core.models.agent_models import AgentConfig
from shared_contracts.core.models.base_models import BaseResponse
from shared_contracts.core.models.model_models import ModelConfig, ModelResponse
from shared_contracts.core.models.tool_models import (
    ToolDefinition,
    ToolResult,
    ToolResultStatus,
)
from shared_contracts.monitoring import (
    EventType,
    MonitorInterface,
    ServiceComponent,
    with_monitoring,
)


class MockModelService:
    """Model服务的通用模拟实现。...."""

    def __init__(self, monitor: MonitorInterface):
        """初始化服务。...."""
        self.models: Dict[str, ModelConfig] = {}
        self.monitor = monitor
        self.responses: Dict[str, Dict[str, Any]] = {
            # 默认响应模式
            "default": {
                "content": "This is a default response.",
            },
            # 调用计算器工具的响应
            "calculator": {
                "content": "I'll help you with this calculation.",
                "tool_calls": [
                    {
                        "tool_id": "calculator",
                        "parameters": {"operation": "add", "a": 5, "b": 3},
                    }
                ],
            },
            # 调用天气工具的响应
            "weather": {
                "content": "I'll check the weather for you.",
                "tool_calls": [
                    {"tool_id": "weather", "parameters": {"location": "Shanghai"}}
                ],
            },
            # 错误响应
            "error": {
                "content": "I encountered an error.",
                "error": "Simulated model error",
            },
        }

    @with_monitoring(component=ServiceComponent.MODEL_SERVICE)
    async def register_model(self, config: ModelConfig) -> BaseResponse[ModelConfig]:
        """注册一个模型。...."""
        self.models[config.model_id] = config
        self.monitor.info(
            f"Model registered: {config.model_id}",
            component=ServiceComponent.MODEL_SERVICE,
            event_type=EventType.SYSTEM,
            model_id=config.model_id,
        )
        return BaseResponse(request_id=uuid.uuid4(), success=True, data=config)

    @with_monitoring(component=ServiceComponent.MODEL_SERVICE)
    async def get_model(self, model_id: str) -> BaseResponse[ModelConfig]:
        """获取模型配置。...."""
        if model_id not in self.models:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Model {model_id} not found",
                status="error",
            )

        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data=self.models[model_id],
            status="success",
        )

    @with_monitoring(component=ServiceComponent.MODEL_SERVICE)
    async def list_models(self) -> BaseResponse[List[ModelConfig]]:
        """列出所有模型。...."""
        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data=list(self.models.values()),
            status="success",
        )

    @with_monitoring(component=ServiceComponent.MODEL_SERVICE)
    async def generate_completion(
        self,
        model_id: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **options: Any,
    ) -> BaseResponse[ModelResponse]:
        """生成文本完成。...."""
        request_id = uuid.uuid4()

        self.monitor.info(
            f"Generating completion with model {model_id}",
            component=ServiceComponent.MODEL_SERVICE,
            event_type=EventType.REQUEST,
            model_id=model_id,
            prompt_length=len(prompt),
        )

        # 确定响应类型
        response_type = "default"
        if model_id not in self.models:
            return BaseResponse(
                request_id=request_id,
                success=False,
                error=f"Model {model_id} not found",
                status="error",
            )

        if "use the calculator tool" in prompt.lower():
            response_type = "calculator"
        elif "use the weather tool" in prompt.lower():
            response_type = "weather"
        elif "error" in prompt.lower():
            response_type = "error"

        if response_type == "error":
            return BaseResponse(
                request_id=request_id,
                success=False,
                error=self.responses["error"]["error"],
                status="error",
            )

        # 创建响应
        response = ModelResponse(
            model_id=model_id,
            request_id=request_id,
            content=json.dumps(self.responses[response_type]),
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

        return BaseResponse(
            request_id=request_id, success=True, data=response, status="success"
        )

    def add_response_template(self, key: str, template: Dict[str, Any]) -> None:
        """添加自定义响应模板。...."""
        self.responses[key] = template


class MockToolService:
    """Tool服务的通用模拟实现。...."""

    def __init__(self, monitor: MonitorInterface):
        """初始化服务。...."""
        self.tools: Dict[str, ToolDefinition] = {}
        self.monitor = monitor
        self.results: Dict[str, Dict[str, Any]] = {
            # 计算器结果
            "calculator": {
                "add": lambda a, b: {"result": a + b},
                "subtract": lambda a, b: {"result": a - b},
                "multiply": lambda a, b: {"result": a * b},
                "divide": lambda a, b: (
                    {"result": a / b} if b != 0 else {"error": "Division by zero"}
                ),
            },
            # 天气结果
            "weather": lambda location: {
                "location": location,
                "temperature": 22,
                "condition": "sunny",
                "humidity": 65,
            },
            # 通用错误
            "error": {"error": "Simulated tool error"},
        }

    @with_monitoring(component=ServiceComponent.TOOL_SERVICE)
    async def register_tool(
        self, definition: ToolDefinition
    ) -> BaseResponse[ToolDefinition]:
        """注册一个工具。...."""
        self.tools[definition.tool_id] = definition
        self.monitor.info(
            f"Tool registered: {definition.tool_id}",
            component=ServiceComponent.TOOL_SERVICE,
            event_type=EventType.SYSTEM,
            tool_id=definition.tool_id,
        )
        return BaseResponse(
            request_id=uuid.uuid4(), success=True, data=definition, status="success"
        )

    @with_monitoring(component=ServiceComponent.TOOL_SERVICE)
    async def get_tool(self, tool_id: str) -> BaseResponse[ToolDefinition]:
        """获取工具定义。...."""
        if tool_id not in self.tools:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Tool {tool_id} not found",
                status="error",
            )

        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data=self.tools[tool_id],
            status="success",
        )

    @with_monitoring(component=ServiceComponent.TOOL_SERVICE)
    async def list_tools(self) -> BaseResponse[List[ToolDefinition]]:
        """列出所有工具。...."""
        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data=list(self.tools.values()),
            status="success",
        )

    @with_monitoring(component=ServiceComponent.TOOL_SERVICE)
    async def execute_tool(
        self, tool_id: str, parameters: Dict[str, Any]
    ) -> BaseResponse[ToolResult]:
        """执行工具。...."""
        request_id = uuid.uuid4()

        self.monitor.info(
            f"Executing tool: {tool_id}",
            component=ServiceComponent.TOOL_SERVICE,
            event_type=EventType.REQUEST,
            tool_id=tool_id,
            parameters=parameters,
        )

        if tool_id not in self.tools and tool_id != "error":
            return BaseResponse(
                request_id=request_id,
                success=False,
                error=f"Tool {tool_id} not found",
                status="error",
            )

        # 模拟错误
        if tool_id == "error":
            tool_result = ToolResult(
                tool_id=tool_id,
                request_id=request_id,
                status=ToolResultStatus.ERROR,
                error=self.results["error"]["error"],
            )
            return BaseResponse(
                request_id=request_id, success=True, data=tool_result, status="success"
            )

        # 计算器工具
        elif tool_id == "calculator":
            operation = parameters.get("operation")
            a = parameters.get("a", 0)
            b = parameters.get("b", 0)

            if operation not in self.results["calculator"]:
                tool_result = ToolResult(
                    tool_id=tool_id,
                    request_id=request_id,
                    status=ToolResultStatus.ERROR,
                    error=f"Unknown operation: {operation}",
                )
            else:
                result = self.results["calculator"][operation](a, b)
                if "error" in result:
                    tool_result = ToolResult(
                        tool_id=tool_id,
                        request_id=request_id,
                        status=ToolResultStatus.ERROR,
                        error=result["error"],
                    )
                else:
                    tool_result = ToolResult(
                        tool_id=tool_id,
                        request_id=request_id,
                        status=ToolResultStatus.SUCCESS,
                        data=result,
                    )

        # 天气工具
        elif tool_id == "weather":
            location = parameters.get("location", "unknown")
            result = self.results["weather"](location)
            tool_result = ToolResult(
                tool_id=tool_id,
                request_id=request_id,
                status=ToolResultStatus.SUCCESS,
                data=result,
            )

        # 其他工具
        else:
            tool_result = ToolResult(
                tool_id=tool_id,
                request_id=request_id,
                status=ToolResultStatus.SUCCESS,
                data={"parameters": parameters},
            )

        self.monitor.info(
            f"Tool execution completed: {tool_id}",
            component=ServiceComponent.TOOL_SERVICE,
            event_type=EventType.RESPONSE,
            tool_id=tool_id,
            result_status=tool_result.status.value,
        )

        return BaseResponse(
            request_id=request_id, success=True, data=tool_result, status="success"
        )

    def add_result_handler(
        self, tool_id: str, handler: Union[Dict[str, Any], Callable[..., Dict[str, Any]]]  # noqa: E501
    ) -> None:
        """添加自定义结果处理程序。...."""
        self.results[tool_id] = handler


class MockAgentService:
    """Agent服务的通用模拟实现。...."""

    def __init__(
        self,
        model_service: MockModelService,
        tool_service: MockToolService,
        monitor: MonitorInterface,
    ):
        """初始化服务。...."""
        self.agents: Dict[uuid.UUID, AgentConfig] = {}
        self.model_service = model_service
        self.tool_service = tool_service
        self.monitor = monitor
        self.conversations: Dict[uuid.UUID, List[Dict[str, Any]]] = {}

    @with_monitoring(component=ServiceComponent.AGENT_CORE)
    async def create_agent(self, config: AgentConfig) -> BaseResponse[AgentConfig]:
        """创建一个代理。...."""
        agent_id = config.agent_id or uuid.uuid4()
        config.agent_id = agent_id
        self.agents[agent_id] = config

        self.monitor.info(
            f"Agent created: {config.name}",
            component=ServiceComponent.AGENT_CORE,
            event_type=EventType.SYSTEM,
            agent_id=str(agent_id),
            model_id=config.model_id,
        )

        return BaseResponse(
            request_id=uuid.uuid4(), success=True, data=config, status="success"
        )

    @with_monitoring(component=ServiceComponent.AGENT_CORE)
    async def get_agent(self, agent_id: uuid.UUID) -> BaseResponse[AgentConfig]:
        """获取代理配置。...."""
        if agent_id not in self.agents:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Agent {agent_id} not found",
                status="error",
            )

        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data=self.agents[agent_id],
            status="success",
        )

    @with_monitoring(component=ServiceComponent.AGENT_CORE)
    async def list_agents(self) -> BaseResponse[List[AgentConfig]]:
        """列出所有代理。...."""
        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data=list(self.agents.values()),
            status="success",
        )

    @with_monitoring(component=ServiceComponent.AGENT_CORE)
    async def process_message(
        self,
        agent_id: uuid.UUID,
        message: str,
        conversation_id: Optional[uuid.UUID] = None,
    ) -> BaseResponse[Dict[str, Any]]:
        """处理用户消息，包括工具调用...."""
        if agent_id not in self.agents:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Agent {agent_id} not found",
                status="error",
            )

        agent_config = self.agents[agent_id]
        conversation_id = conversation_id or uuid.uuid4()

        # 初始化对话记录
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        # 记录用户消息
        self.conversations[conversation_id].append({"role": "user", "content": message})

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
                status="error",
            )

        # 3. 解析模型响应
        response_json = json.loads(model_response.data.content)
        content = response_json.get("content", "")
        tool_calls = response_json.get("tool_calls", [])

        # 记录助手消息
        self.conversations[conversation_id].append(
            {"role": "assistant", "content": content}
        )

        # 4. 处理工具调用
        tool_results = []

        if tool_calls and "tool_use" in [cap.value for cap in agent_config.capabilities]:  # noqa: E501
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
                tool_response = await self.tool_service.execute_tool(
                    tool_id=tool_id, parameters=parameters
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

        return BaseResponse(
            request_id=uuid.uuid4(), success=True, data=final_response, status="success"
        )

    def get_conversation(
        self, conversation_id: uuid.UUID
    ) -> Optional[List[Dict[str, str]]]:
        """获取对话记录。...."""
        return self.conversations.get(conversation_id)
