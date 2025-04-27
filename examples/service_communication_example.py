"""
示例：服务间通信

本示例展示如何使用shared_contracts模块进行服务间通信，包括HTTP调用和消息队列两种模式。
"""

import asyncio
import uuid
import json
import os
from datetime import datetime

# 导入shared_contracts组件
from agentforge_contracts.core.models.base_models import BaseResponse
from agentforge_contracts.core.models.agent_models import AgentConfig, AgentState, AgentStatus
from agentforge_contracts.core.models.model_models import ModelConfig, ModelProvider, ModelType
from agentforge_contracts.monitoring import (
    configure_monitor,
    ServiceComponent,
    EventType,
    with_monitoring
)
from agentforge_contracts.utils.serialization import serialize_model, deserialize_model

# 模拟HTTP客户端
import httpx


# 配置监控
monitor = configure_monitor(
    service_name="service-communication-example",
    api_key=os.environ.get("LOGFIRE_API_KEY", "dummy-key"),
    project_id=os.environ.get("LOGFIRE_PROJECT_ID", "dummy-project"),
    environment="development"
)


# ====== HTTP通信模式示例 ======

class ServiceClient:
    """服务客户端基类。"""
    
    def __init__(self, base_url: str, service_name: str):
        """初始化客户端。"""
        self.base_url = base_url
        self.service_name = service_name
        self.client = httpx.AsyncClient(base_url=base_url)
    
    async def close(self):
        """关闭客户端。"""
        await self.client.aclose()
    
    async def request(self, method, endpoint, data=None, params=None):
        """发送请求。"""
        try:
            # 记录请求日志
            monitor.info(
                message=f"Sending {method} request to {self.service_name} at {endpoint}",
                component=ServiceComponent.API_GATEWAY,
                event_type=EventType.REQUEST,
                service=self.service_name,
                endpoint=endpoint
            )
            
            # 根据方法发送请求
            if method.upper() == "GET":
                response = await self.client.get(endpoint, params=params)
            elif method.upper() == "POST":
                response = await self.client.post(endpoint, json=data)
            elif method.upper() == "PUT":
                response = await self.client.put(endpoint, json=data)
            elif method.upper() == "DELETE":
                response = await self.client.delete(endpoint)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # 解析响应
            if response.status_code >= 400:
                error_message = f"Service error: {response.status_code} - {response.text}"
                monitor.error(
                    message=error_message,
                    component=ServiceComponent.API_GATEWAY,
                    event_type=EventType.EXCEPTION,
                    service=self.service_name,
                    status_code=response.status_code
                )
                return {"success": False, "error": error_message}
            
            # 记录成功响应
            monitor.info(
                message=f"Received response from {self.service_name}",
                component=ServiceComponent.API_GATEWAY,
                event_type=EventType.RESPONSE,
                service=self.service_name,
                status_code=response.status_code
            )
            
            return response.json()
            
        except Exception as e:
            error_message = f"Request failed: {str(e)}"
            monitor.error(
                message=error_message,
                component=ServiceComponent.API_GATEWAY,
                event_type=EventType.EXCEPTION,
                service=self.service_name,
                error=str(e)
            )
            return {"success": False, "error": error_message}


class AgentServiceClient(ServiceClient):
    """Agent服务客户端。"""
    
    def __init__(self, base_url="http://localhost:8001"):
        """初始化代理服务客户端。"""
        super().__init__(base_url, "agent-service")
    
    async def create_agent(self, config: AgentConfig):
        """创建代理。"""
        return await self.request("POST", "/agents", data=config.model_dump())
    
    async def get_agent(self, agent_id: uuid.UUID):
        """获取代理。"""
        return await self.request("GET", f"/agents/{agent_id}")
    
    async def send_message(self, agent_id: uuid.UUID, message: str, conversation_id=None):
        """向代理发送消息。"""
        data = {"message": message}
        if conversation_id:
            data["conversation_id"] = str(conversation_id)
            
        return await self.request("POST", f"/agents/{agent_id}/messages", data=data)


class ModelServiceClient(ServiceClient):
    """Model服务客户端。"""
    
    def __init__(self, base_url="http://localhost:8002"):
        """初始化模型服务客户端。"""
        super().__init__(base_url, "model-service")
    
    async def register_model(self, config: ModelConfig):
        """注册模型。"""
        return await self.request("POST", "/models", data=config.model_dump())
    
    async def get_model(self, model_id: str):
        """获取模型。"""
        return await self.request("GET", f"/models/{model_id}")
    
    async def generate_completion(self, model_id: str, prompt: str, **options):
        """生成完成。"""
        data = {
            "model_id": model_id,
            "prompt": prompt,
            **options
        }
        return await self.request("POST", "/completions", data=data)


# ====== 消息队列通信模式示例 ======

class MessageQueue:
    """模拟消息队列。"""
    
    def __init__(self):
        self.queues = {}
        self.consumers = {}
    
    async def push(self, queue_name, message):
        """推送消息到队列。"""
        if queue_name not in self.queues:
            self.queues[queue_name] = []
        
        self.queues[queue_name].append(message)
        
        # 通知所有消费者
        if queue_name in self.consumers:
            for consumer in self.consumers[queue_name]:
                await consumer(message)
    
    async def consume(self, queue_name, callback):
        """消费队列消息。"""
        if queue_name not in self.consumers:
            self.consumers[queue_name] = []
        
        self.consumers[queue_name].append(callback)


class MessageQueueClient:
    """消息队列客户端。"""
    
    def __init__(self, message_queue):
        self.message_queue = message_queue
        self.pending_requests = {}
    
    async def send_request(self, service_name, action, data, timeout=5.0):
        """发送请求。"""
        # 生成请求ID
        request_id = str(uuid.uuid4())
        
        # 创建Future
        future = asyncio.get_event_loop().create_future()
        self.pending_requests[request_id] = future
        
        # 构建请求
        request = {
            "request_id": request_id,
            "action": action,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # 设置响应处理器
        async def handle_response(message):
            """处理响应。"""
            message_data = json.loads(message) if isinstance(message, str) else message
            response_id = message_data.get("request_id")
            
            if response_id in self.pending_requests:
                self.pending_requests[response_id].set_result(message_data)
                del self.pending_requests[response_id]
        
        # 订阅响应队列
        response_queue = f"response_{request_id}"
        await self.message_queue.consume(response_queue, handle_response)
        
        # 发送请求
        await self.message_queue.push(f"{service_name}_requests", json.dumps(request))
        
        try:
            # 等待响应
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            del self.pending_requests[request_id]
            return {"success": False, "error": "Request timed out"}


class AgentMQClient:
    """代理服务消息队列客户端。"""
    
    def __init__(self, mq_client):
        self.mq_client = mq_client
    
    async def create_agent(self, config: AgentConfig):
        """创建代理。"""
        serialized = serialize_model(config)
        response = await self.mq_client.send_request(
            "agent", "create_agent", serialized
        )
        
        if response.get("success"):
            return {
                "success": True,
                "data": deserialize_model(AgentConfig, response.get("data"))
            }
        else:
            return {
                "success": False,
                "error": response.get("error")
            }
    
    async def send_message(self, agent_id: uuid.UUID, message: str):
        """向代理发送消息。"""
        data = {
            "agent_id": str(agent_id),
            "message": message
        }
        
        return await self.mq_client.send_request(
            "agent", "send_message", data
        )


# ====== 模拟代理服务 ======

class MockAgentService:
    """模拟的代理服务实现。"""
    
    def __init__(self, message_queue=None):
        self.agents = {}
        self.agent_states = {}
        self.message_queue = message_queue
        
        # 如果提供了消息队列，启动消费者
        if self.message_queue:
            asyncio.create_task(self._start_consumer())
    
    async def _start_consumer(self):
        """启动消息队列消费者。"""
        async def handle_request(message):
            """处理请求。"""
            # 解析请求
            request = json.loads(message) if isinstance(message, str) else message
            request_id = request.get("request_id")
            action = request.get("action")
            data = request.get("data")
            
            # 根据动作处理请求
            if action == "create_agent":
                config = deserialize_model(AgentConfig, data)
                result = await self.create_agent(config)
                serialized_result = {"success": result.success}
                
                if result.success:
                    serialized_result["data"] = serialize_model(result.data)
                else:
                    serialized_result["error"] = result.error
                
                # 发送响应
                await self.message_queue.push(f"response_{request_id}", serialized_result)
                
            elif action == "send_message":
                agent_id = uuid.UUID(data.get("agent_id"))
                message = data.get("message")
                result = await self.send_message_to_agent(agent_id, message)
                
                # 发送响应
                await self.message_queue.push(f"response_{request_id}", {
                    "success": result.success,
                    "data": result.data if result.success else None,
                    "error": result.error if not result.success else None
                })
        
        # 订阅请求队列
        await self.message_queue.consume("agent_requests", handle_request)
    
    @with_monitoring(component=ServiceComponent.AGENT_CORE)
    async def create_agent(self, config: AgentConfig) -> BaseResponse[AgentConfig]:
        """创建代理。"""
        # 确保代理ID
        agent_id = config.agent_id or uuid.uuid4()
        config.agent_id = agent_id
        
        # 存储代理配置
        self.agents[agent_id] = config
        
        # 初始化代理状态
        self.agent_states[agent_id] = AgentState(
            agent_id=agent_id,
            status=AgentStatus.READY,
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        
        # 模拟延迟
        await asyncio.sleep(0.1)
        
        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data=config
        )
    
    @with_monitoring(component=ServiceComponent.AGENT_CORE)
    async def send_message_to_agent(
        self, 
        agent_id: uuid.UUID,
        message: str
    ) -> BaseResponse[dict]:
        """向代理发送消息。"""
        # 检查代理是否存在
        if agent_id not in self.agents:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Agent not found: {agent_id}"
            )
        
        # 获取代理配置和状态
        config = self.agents[agent_id]
        state = self.agent_states[agent_id]
        
        # 更新状态
        state.status = AgentStatus.BUSY
        state.last_active = datetime.now()
        
        try:
            # 模拟处理消息
            await asyncio.sleep(0.2)
            
            # 模拟回复
            response = f"Echo: {message}"
            
            # 更新状态
            state.status = AgentStatus.READY
            
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=True,
                data={
                    "response": response,
                    "conversation_id": str(uuid.uuid4())
                }
            )
            
        except Exception as e:
            # 出错时更新状态
            state.status = AgentStatus.ERROR
            
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Error processing message: {str(e)}"
            )


# ====== HTTP通信示例 ======

async def http_communication_example():
    """使用HTTP进行服务间通信的示例。"""
    print("\n==== HTTP通信示例 ====")
    
    # 创建代理服务客户端
    agent_client = AgentServiceClient()
    
    try:
        # 创建代理配置
        agent_config = AgentConfig(
            name="Test Agent",
            description="A test agent for demonstration",
            model_id="gpt-4",
            system_prompt="You are a helpful assistant."
        )
        
        # 创建代理
        print("Creating agent via HTTP...")
        create_result = await agent_client.create_agent(agent_config)
        
        if create_result.get("success"):
            agent_id = uuid.UUID(create_result.get("data", {}).get("agent_id"))
            print(f"Agent created successfully, ID: {agent_id}")
            
            # 发送消息
            print("Sending message to agent...")
            message_result = await agent_client.send_message(
                agent_id, "Hello, agent!"
            )
            
            if message_result.get("success"):
                print(f"Message sent successfully, response: {message_result.get('data', {}).get('response')}")
            else:
                print(f"Failed to send message: {message_result.get('error')}")
        else:
            print(f"Failed to create agent: {create_result.get('error')}")
    
    finally:
        # 关闭客户端
        await agent_client.close()


# ====== 消息队列通信示例 ======

async def message_queue_example():
    """使用消息队列进行服务间通信的示例。"""
    print("\n==== 消息队列通信示例 ====")
    
    # 创建消息队列
    message_queue = MessageQueue()
    
    # 创建模拟服务
    mock_service = MockAgentService(message_queue)
    
    # 创建消息队列客户端
    mq_client = MessageQueueClient(message_queue)
    agent_mq_client = AgentMQClient(mq_client)
    
    # 创建代理配置
    agent_config = AgentConfig(
        name="MQ Test Agent",
        description="A test agent for message queue demonstration",
        model_id="gpt-4",
        system_prompt="You are a helpful assistant."
    )
    
    # 创建代理
    print("Creating agent via message queue...")
    create_result = await agent_mq_client.create_agent(agent_config)
    
    if create_result.get("success"):
        agent_id = create_result.get("data").agent_id
        print(f"Agent created successfully, ID: {agent_id}")
        
        # 发送消息
        print("Sending message to agent...")
        message_result = await agent_mq_client.send_message(
            agent_id, "Hello from message queue!"
        )
        
        if message_result.get("success"):
            print(f"Message sent successfully, response: {message_result.get('data', {}).get('response')}")
        else:
            print(f"Failed to send message: {message_result.get('error')}")
    else:
        print(f"Failed to create agent: {create_result.get('error')}")


# ====== 主函数 ====

async def main():
    """主函数。"""
    print("==== AgentForge服务通信示例 ====")
    
    # 运行HTTP通信示例
    await http_communication_example()
    
    # 运行消息队列通信示例
    await message_queue_example()


if __name__ == "__main__":
    asyncio.run(main())
