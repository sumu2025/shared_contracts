"""
Agent-Model服务集成测试。

此模块测试Agent服务与Model服务间通过shared_contracts进行交互的场..."""

import uuid
from typing import Any, Dict, Optional

import pytest

from shared_contracts.core.interfaces.model_interface import ModelServiceInterface
from shared_contracts.core.models.agent_models import AgentCapability, AgentConfig
from shared_contracts.core.models.base_models import BaseResponse
from shared_contracts.core.models.model_models import (
    ModelCapability,
    ModelConfig,
    ModelProvider,
    ModelResponse,
    ModelType,
)
from shared_contracts.monitoring import (
    ServiceComponent,
    configure_monitor,
    track_performance,
    with_monitoring,
)


# 模拟Model服务实现
class MockModelService:
    """Model服务的模拟实现。...."""

    def __init__(self):
        """初始化服务。...."""
        self.models = {}

    @with_monitoring(component=ServiceComponent.MODEL_SERVICE)
    async def register_model(self, config: ModelConfig) -> BaseResponse[ModelConfig]:
        """注册一个模型。...."""
        self.models[config.model_id] = config
        return BaseResponse(request_id=uuid.uuid4(), success=True, data=config)

    @with_monitoring(component=ServiceComponent.MODEL_SERVICE)
    async def get_model(self, model_id: str) -> BaseResponse[ModelConfig]:
        """获取模型配置。...."""
        if model_id not in self.models:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Model {model_id} not found",
            )

        return BaseResponse(
            request_id=uuid.uuid4(), success=True, data=self.models[model_id]
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
        # 检查模型是否存在
        if model_id not in self.models:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Model {model_id} not found",
            )

        # 创建响应
        request_id = uuid.uuid4()
        response = ModelResponse(
            model_id=model_id,
            request_id=request_id,
            content=f"Response to: {prompt}",
            usage={
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": 10,
                "total_tokens": len(prompt.split()) + 10,
            },
            finish_reason="stop",
        )

        return BaseResponse(request_id=request_id, success=True, data=response)


# 模拟Agent服务实现
class MockAgentService:
    """Agent服务的模拟实现。...."""

    def __init__(self, model_service: ModelServiceInterface):
        """
        初始化服务。

        Args:
            model_service: Model服务接口
     ..."""
        self.agents = {}
        self.model_service = model_service

    @with_monitoring(component=ServiceComponent.AGENT_CORE)
    async def create_agent(self, config: AgentConfig) -> BaseResponse[AgentConfig]:
        """创建一个代理。...."""
        # 确保模型存在
        model_response = await self.model_service.get_model(config.model_id)
        if not model_response.success:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Agent creation failed: {model_response.error}",
            )

        # 存储代理配置
        agent_id = config.agent_id or uuid.uuid4()
        config.agent_id = agent_id
        self.agents[agent_id] = config

        return BaseResponse(request_id=uuid.uuid4(), success=True, data=config)

    @with_monitoring(component=ServiceComponent.AGENT_CORE)
    async def get_agent(self, agent_id: uuid.UUID) -> BaseResponse[AgentConfig]:
        """获取代理配置。...."""
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
    async def send_message_to_agent(
        self,
        agent_id: uuid.UUID,
        message: str,
        conversation_id: Optional[uuid.UUID] = None,
    ) -> BaseResponse[Dict[str, Any]]:
        """
        向代理发送消息。

        这个方法会调用Model服务生成响应。
     ..."""
        # 检查代理是否存在
        if agent_id not in self.agents:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Agent {agent_id} not found",
            )

        agent_config = self.agents[agent_id]

        # 创建提示词
        prompt = f"{agent_config.system_prompt}\n\nUser: {message}\nAssistant:"

        # 调用模型服务生成响应
        with track_performance("model_request", ServiceComponent.AGENT_CORE) as span:
            response = await self.model_service.generate_completion(
                model_id=agent_config.model_id,
                prompt=prompt,
                max_tokens=agent_config.max_tokens_per_response,
                temperature=agent_config.temperature,
            )

            span.add_data(
                {
                    "agent_id": str(agent_id),
                    "model_id": agent_config.model_id,
                    "prompt_length": len(prompt),
                }
            )

        if not response.success:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Failed to generate response: {response.error}",
            )

        # 处理响应
        conversation_id = conversation_id or uuid.uuid4()

        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data={
                "message": response.data.content,
                "conversation_id": str(conversation_id),
                "usage": response.data.usage,
            },
        )


@pytest.fixture
def setup_monitor():
    """设置监控客户端。...."""
    try:
        # 使用内存配置（不实际连接到LogFire）
        # config = LogFireConfig(  # 未使用变量: config
        #    api_key="test_key",
        #    project_id="test_project",
        #    service_name="integration-test",
        #    environment="test",
        #    api_endpoint="memory://logfire",  # 使用内存模式
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
async def test_agent_model_integration(setup_monitor):
    """测试Agent服务与Model服务间的集成。...."""
    # 创建Model服务
    model_service = MockModelService()

    # 注册一个模型
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

    # 创建Agent服务
    agent_service = MockAgentService(model_service)

    # 创建一个代理
    agent_config = AgentConfig(
        name="Test Agent",
        description="A test agent for integration tests",
        model_id="gpt-4",  # 使用已注册的模型
        system_prompt="You are a helpful assistant.",
        capabilities={AgentCapability.CONVERSATION, AgentCapability.TOOL_USE},
        max_tokens_per_response=1000,
        temperature=0.7,
    )

    response = await agent_service.create_agent(agent_config)
    assert response.success, f"创建代理失败: {response.error}"

    agent_id = response.data.agent_id

    # 向代理发送消息
    message_response = await agent_service.send_message_to_agent(
        agent_id=agent_id, message="Hello, who are you?"
    )

    # 验证交互结果
    assert message_response.success, f"向代理发送消息失败: {message_response.error}"
    assert "message" in message_response.data
    assert "conversation_id" in message_response.data
    assert "usage" in message_response.data

    print("集成测试成功完成！")
    print(f"代理响应: {message_response.data['message']}")
    print(f"Token 使用情况: {message_response.data['usage']}")
