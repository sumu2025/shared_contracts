"""
完整应用示例: AgentForge聊天应用

本示例展示了如何使用shared_contracts构建一个完整的端到端应用，
包括API网关、代理服务、模型服务和工具服务的集成。

该示例实现了一个简单的聊天应用，用户可以与代理进行对话，
代理使用模型生成响应，并在需要时使用工具。
"""

import asyncio
import logging
import os
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, AsyncIterable

# FastAPI用于API网关
from fastapi import FastAPI, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# HTTP客户端
import httpx

# 导入shared_contracts组件
from agentforge_contracts.core.interfaces.agent_interface import AgentServiceInterface
from agentforge_contracts.core.interfaces.model_interface import ModelServiceInterface
from agentforge_contracts.core.interfaces.tool_interface import ToolServiceInterface

from agentforge_contracts.core.models.base_models import BaseResponse
from agentforge_contracts.core.models.agent_models import (
    AgentConfig, AgentState, AgentStatus, AgentCapability
)
from agentforge_contracts.core.models.model_models import (
    ModelConfig, ModelResponse, ModelProvider, ModelType, ModelCapability
)
from agentforge_contracts.core.models.tool_models import (
    ToolDefinition, ToolResult, ToolResultStatus, ToolParameter, 
    ToolParameterType, ToolParameters
)

from agentforge_contracts.monitoring import (
    configure_monitor, ServiceComponent, EventType, with_monitoring,
    track_performance, create_trace_context
)

from agentforge_contracts.utils.validation import validate_parameters
from agentforge_contracts.utils.timing import retry_with_backoff
from agentforge_contracts.utils.serialization import serialize_model, deserialize_model

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("agentforge_app")

# 配置监控客户端
monitor = configure_monitor(
    service_name="agentforge-chat-app",
    api_key=os.environ.get("LOGFIRE_API_KEY", "dummy-key"),
    project_id=os.environ.get("LOGFIRE_PROJECT_ID", "dummy-project"),
    environment=os.environ.get("ENVIRONMENT", "development"),
    version="1.0.0"
)


# ====== 模型服务实现 ======

class SimpleModelService(ModelServiceInterface):
    """简单的模型服务实现。"""
    
    def __init__(self):
        self.models = {}  # 存储模型配置
    
    @with_monitoring(component=ServiceComponent.MODEL_SERVICE)
    async def register_model(self, config: ModelConfig) -> BaseResponse[ModelConfig]:
        """注册模型。"""
        # 存储模型配置
        self.models[config.model_id] = config
        
        # 记录模型注册
        monitor.info(
            message=f"Model registered: {config.model_id}",
            component=ServiceComponent.MODEL_SERVICE,
            event_type=EventType.SYSTEM,
            provider=config.provider,
            model_type=config.model_type
        )
        
        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data=config
        )
    
    @with_monitoring(component=ServiceComponent.MODEL_SERVICE)
    async def get_model(self, model_id: str) -> BaseResponse[ModelConfig]:
        """获取模型配置。"""
        if model_id not in self.models:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error="Model not found"
            )
        
        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data=self.models[model_id]
        )
    
    @with_monitoring(component=ServiceComponent.MODEL_SERVICE)
    @track_performance("model_completion")
    async def generate(self, model_id: str, prompt: str, parameters: Dict[str, Any] = None) -> BaseResponse[ModelResponse]:
        """生成模型响应。"""
        if model_id not in self.models:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error="Model not found"
            )
        
        config = self.models[model_id]
        
        # 创建跟踪上下文
        trace_ctx = create_trace_context()
        
        # 在实际应用中，这里会调用实际的模型API
        # 本示例中，我们模拟模型响应
        monitor.info(
            message=f"Generating response with model: {model_id}",
            component=ServiceComponent.MODEL_SERVICE,
            event_type=EventType.OPERATION,
            model_id=model_id,
            prompt_length=len(prompt),
            trace_id=trace_ctx.trace_id
        )
        
        # 模拟生成延迟
        await asyncio.sleep(0.2)
        
        # 根据不同模型类型模拟不同响应
        if config.model_type == ModelType.CHAT:
            response_text = f"这是{config.model_id}的响应: {prompt[:20]}..."
        elif config.model_type == ModelType.EMBEDDING:
            # 模拟嵌入向量
            response_text = json.dumps([0.1, 0.2, 0.3, 0.4, 0.5])
        else:
            response_text = f"来自{config.model_id}的通用响应"
        
        model_response = ModelResponse(
            model_id=model_id,
            provider=config.provider,
            response=response_text,
            token_usage={
                "prompt_tokens": len(prompt) // 4,
                "completion_tokens": len(response_text) // 4,
                "total_tokens": (len(prompt) + len(response_text)) // 4
            },
            created_at=datetime.now()
        )
        
        monitor.info(
            message=f"Response generated successfully",
            component=ServiceComponent.MODEL_SERVICE,
            event_type=EventType.OPERATION,
            model_id=model_id,
            response_length=len(response_text),
            token_usage=model_response.token_usage,
            trace_id=trace_ctx.trace_id
        )
        
        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data=model_response
        )
    
    @with_monitoring(component=ServiceComponent.MODEL_SERVICE)
    async def stream_generate(self, model_id: str, prompt: str, parameters: Dict[str, Any] = None) -> AsyncIterable[BaseResponse[ModelResponse]]:
        """流式生成模型响应。"""
        if model_id not in self.models:
            yield BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error="Model not found"
            )
            return
        
        config = self.models[model_id]
        
        # 创建跟踪上下文
        trace_ctx = create_trace_context()
        
        monitor.info(
            message=f"Stream generating response with model: {model_id}",
            component=ServiceComponent.MODEL_SERVICE,
            event_type=EventType.OPERATION,
            model_id=model_id,
            prompt_length=len(prompt),
            trace_id=trace_ctx.trace_id
        )
        
        # 模拟流式响应
        response_parts = [
            "这是",
            f"{config.model_id}",
            "的流式",
            "响应",
            f": {prompt[:10]}..."
        ]
        
        token_count = 0
        for part in response_parts:
            # 模拟生成延迟
            await asyncio.sleep(0.1)
            
            token_count += len(part) // 4
            
            model_response = ModelResponse(
                model_id=model_id,
                provider=config.provider,
                response=part,
                token_usage={
                    "prompt_tokens": len(prompt) // 4,
                    "completion_tokens": token_count,
                    "total_tokens": (len(prompt) // 4) + token_count
                },
                created_at=datetime.now()
            )
            
            yield BaseResponse(
                request_id=uuid.uuid4(),
                success=True,
                data=model_response
            )
        
        monitor.info(
            message=f"Stream response generated successfully",
            component=ServiceComponent.MODEL_SERVICE,
            event_type=EventType.OPERATION,
            model_id=model_id,
            response_length=sum(len(part) for part in response_parts),
            token_usage={"completion_tokens": token_count},
            trace_id=trace_ctx.trace_id
        )


# ====== 工具服务实现 ======

class SimpleToolService(ToolServiceInterface):
    """简单的工具服务实现。"""
    
    def __init__(self):
        self.tools = {}  # 存储工具定义
    
    @with_monitoring(component=ServiceComponent.TOOL_SERVICE)
    async def register_tool(self, tool: ToolDefinition) -> BaseResponse[ToolDefinition]:
        """注册工具。"""
        # 存储工具定义
        self.tools[tool.tool_id] = tool
        
        # 记录工具注册
        monitor.info(
            message=f"Tool registered: {tool.tool_id}",
            component=ServiceComponent.TOOL_SERVICE,
            event_type=EventType.SYSTEM,
            tool_id=tool.tool_id
        )
        
        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data=tool
        )
    
    @with_monitoring(component=ServiceComponent.TOOL_SERVICE)
    async def get_tool(self, tool_id: str) -> BaseResponse[ToolDefinition]:
        """获取工具定义。"""
        if tool_id not in self.tools:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error="Tool not found"
            )
        
        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data=self.tools[tool_id]
        )
    
    @with_monitoring(component=ServiceComponent.TOOL_SERVICE)
    async def list_tools(self) -> BaseResponse[List[ToolDefinition]]:
        """列出所有可用工具。"""
        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data=list(self.tools.values())
        )
    
    @with_monitoring(component=ServiceComponent.TOOL_SERVICE)
    @track_performance("tool_execution")
    async def execute_tool(self, tool_id: str, parameters: Dict[str, Any]) -> BaseResponse[ToolResult]:
        """执行工具。"""
        if tool_id not in self.tools:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error="Tool not found"
            )
        
        tool = self.tools[tool_id]
        
        # 创建跟踪上下文
        trace_ctx = create_trace_context()
        
        # 记录工具执行
        monitor.info(
            message=f"Executing tool: {tool_id}",
            component=ServiceComponent.TOOL_SERVICE,
            event_type=EventType.OPERATION,
            tool_id=tool_id,
            parameters=parameters,
            trace_id=trace_ctx.trace_id
        )
        
        # 验证参数
        validation_result = validate_parameters(parameters, tool.parameters)
        if not validation_result.valid:
            error_message = f"Invalid parameters: {validation_result.errors}"
            
            monitor.error(
                message=error_message,
                component=ServiceComponent.TOOL_SERVICE,
                event_type=EventType.ERROR,
                tool_id=tool_id,
                parameters=parameters,
                trace_id=trace_ctx.trace_id
            )
            
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=error_message
            )
        
        # 在实际应用中，这里会执行实际的工具逻辑
        # 本示例中，我们模拟工具执行
        
        # 模拟执行延迟
        await asyncio.sleep(0.3)
        
        # 模拟工具结果
        if tool.tool_id == "calculator":
            # 简单计算器工具
            expression = parameters.get("expression", "")
            try:
                result = str(eval(expression))
                status = ToolResultStatus.SUCCESS
            except Exception as e:
                result = f"计算错误: {str(e)}"
                status = ToolResultStatus.ERROR
        
        elif tool.tool_id == "weather":
            # 模拟天气工具
            location = parameters.get("location", "默认城市")
            result = f"{location}的天气: 晴天，温度25°C"
            status = ToolResultStatus.SUCCESS
        
        else:
            # 通用工具响应
            result = f"执行了{tool.tool_id}工具，参数: {json.dumps(parameters)}"
            status = ToolResultStatus.SUCCESS
        
        tool_result = ToolResult(
            tool_id=tool_id,
            status=status,
            result=result,
            created_at=datetime.now()
        )
        
        monitor.info(
            message=f"Tool executed successfully: {tool_id}",
            component=ServiceComponent.TOOL_SERVICE,
            event_type=EventType.OPERATION,
            tool_id=tool_id,
            result_status=status.value,
            trace_id=trace_ctx.trace_id
        )
        
        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data=tool_result
        )


# ====== 代理服务实现 ======

class SimpleAgentService(AgentServiceInterface):
    """简单的代理服务实现。"""
    
    def __init__(self, model_service: ModelServiceInterface, tool_service: ToolServiceInterface):
        self.agents = {}  # 存储代理配置
        self.agent_states = {}  # 存储代理状态
        self.model_service = model_service
        self.tool_service = tool_service
    
    @with_monitoring(component=ServiceComponent.AGENT_SERVICE)
    async def register_agent(self, config: AgentConfig) -> BaseResponse[AgentConfig]:
        """注册代理。"""
        # 存储代理配置
        self.agents[config.agent_id] = config
        
        # 初始化代理状态
        self.agent_states[config.agent_id] = AgentState(
            agent_id=config.agent_id,
            status=AgentStatus.IDLE,
            current_task=None,
            conversation_history=[],
            last_updated=datetime.now()
        )
        
        # 记录代理注册
        monitor.info(
            message=f"Agent registered: {config.agent_id}",
            component=ServiceComponent.AGENT_SERVICE,
            event_type=EventType.SYSTEM,
            agent_id=config.agent_id
        )
        
        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data=config
        )
    
    @with_monitoring(component=ServiceComponent.AGENT_SERVICE)
    async def get_agent(self, agent_id: str) -> BaseResponse[AgentConfig]:
        """获取代理配置。"""
        if agent_id not in self.agents:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error="Agent not found"
            )
        
        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data=self.agents[agent_id]
        )
    
    @with_monitoring(component=ServiceComponent.AGENT_SERVICE)
    async def get_agent_state(self, agent_id: str) -> BaseResponse[AgentState]:
        """获取代理状态。"""
        if agent_id not in self.agent_states:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error="Agent state not found"
            )
        
        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data=self.agent_states[agent_id]
        )
    
    @with_monitoring(component=ServiceComponent.AGENT_SERVICE)
    @track_performance("agent_process")
    async def process_message(self, agent_id: str, message: str) -> BaseResponse[str]:
        """处理用户消息。"""
        if agent_id not in self.agents:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error="Agent not found"
            )
        
        config = self.agents[agent_id]
        agent_state = self.agent_states[agent_id]
        
        # 创建跟踪上下文
        trace_ctx = create_trace_context()
        
        # 更新代理状态
        agent_state.status = AgentStatus.PROCESSING
        agent_state.last_updated = datetime.now()
        
        # 记录消息处理
        monitor.info(
            message=f"Processing message for agent: {agent_id}",
            component=ServiceComponent.AGENT_SERVICE,
            event_type=EventType.OPERATION,
            agent_id=agent_id,
            message_length=len(message),
            trace_id=trace_ctx.trace_id
        )
        
        # 更新对话历史
        agent_state.conversation_history.append({"role": "user", "content": message})
        
        # 检查是否需要工具调用
        tool_match = None
        available_tools = await self.tool_service.list_tools()
        
        if available_tools.success and available_tools.data:
            for tool in available_tools.data:
                if tool.tool_id in message.lower():
                    tool_match = tool
                    break
        
        response = ""
        
        # 如果需要工具调用
        if tool_match:
            monitor.info(
                message=f"Tool execution identified: {tool_match.tool_id}",
                component=ServiceComponent.AGENT_SERVICE,
                event_type=EventType.OPERATION,
                agent_id=agent_id,
                tool_id=tool_match.tool_id,
                trace_id=trace_ctx.trace_id
            )
            
            # 简单解析参数 (实际应用中应使用模型提取参数)
            parameters = {}
            for param in tool_match.parameters:
                param_marker = f"{param.name}:"
                if param_marker in message:
                    param_value = message.split(param_marker)[1].split(" ")[0]
                    parameters[param.name] = param_value
            
            # 执行工具
            tool_result = await self.tool_service.execute_tool(tool_match.tool_id, parameters)
            
            if tool_result.success:
                # 在响应中加入工具执行结果
                tool_response = f"我使用{tool_match.tool_id}工具获取到的结果是: {tool_result.data.result}"
                
                # 使用模型生成最终响应
                model_response = await self.model_service.generate(
                    config.model_id,
                    f"基于以下工具执行结果，生成友好的回复: {tool_response}\n原始消息: {message}"
                )
                
                if model_response.success:
                    response = model_response.data.response
                else:
                    response = tool_response
            else:
                response = f"执行工具{tool_match.tool_id}失败: {tool_result.error}"
        else:
            # 直接使用模型生成响应
            model_response = await self.model_service.generate(
                config.model_id,
                message
            )
            
            if model_response.success:
                response = model_response.data.response
            else:
                response = f"无法生成响应: {model_response.error}"
        
        # 更新对话历史
        agent_state.conversation_history.append({"role": "assistant", "content": response})
        
        # 更新代理状态
        agent_state.status = AgentStatus.IDLE
        agent_state.last_updated = datetime.now()
        
        monitor.info(
            message=f"Message processed successfully for agent: {agent_id}",
            component=ServiceComponent.AGENT_SERVICE,
            event_type=EventType.OPERATION,
            agent_id=agent_id,
            response_length=len(response),
            trace_id=trace_ctx.trace_id
        )
        
        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data=response
        )
    
    @with_monitoring(component=ServiceComponent.AGENT_SERVICE)
    async def stream_process_message(self, agent_id: str, message: str) -> AsyncIterable[BaseResponse[str]]:
        """流式处理用户消息。"""
        if agent_id not in self.agents:
            yield BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error="Agent not found"
            )
            return
        
        config = self.agents[agent_id]
        agent_state = self.agent_states[agent_id]
        
        # 创建跟踪上下文
        trace_ctx = create_trace_context()
        
        # 更新代理状态
        agent_state.status = AgentStatus.PROCESSING
        agent_state.last_updated = datetime.now()
        
        # 记录消息处理
        monitor.info(
            message=f"Stream processing message for agent: {agent_id}",
            component=ServiceComponent.AGENT_SERVICE,
            event_type=EventType.OPERATION,
            agent_id=agent_id,
            message_length=len(message),
            trace_id=trace_ctx.trace_id
        )
        
        # 更新对话历史
        agent_state.conversation_history.append({"role": "user", "content": message})
        
        # 直接使用模型流式生成响应
        full_response = ""
        async for chunk_response in self.model_service.stream_generate(
            config.model_id,
            message
        ):
            if chunk_response.success:
                chunk = chunk_response.data.response
                full_response += chunk
                
                yield BaseResponse(
                    request_id=uuid.uuid4(),
                    success=True,
                    data=chunk
                )
            else:
                yield BaseResponse(
                    request_id=uuid.uuid4(),
                    success=False,
                    error=f"无法生成响应: {chunk_response.error}"
                )
                return
        
        # 更新对话历史
        agent_state.conversation_history.append({"role": "assistant", "content": full_response})
        
        # 更新代理状态
        agent_state.status = AgentStatus.IDLE
        agent_state.last_updated = datetime.now()
        
        monitor.info(
            message=f"Stream message processed successfully for agent: {agent_id}",
            component=ServiceComponent.AGENT_SERVICE,
            event_type=EventType.OPERATION,
            agent_id=agent_id,
            response_length=len(full_response),
            trace_id=trace_ctx.trace_id
        )


# ====== API网关实现 ======

app = FastAPI(title="AgentForge聊天API")

# 允许CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建服务实例
model_service = SimpleModelService()
tool_service = SimpleToolService()
agent_service = SimpleAgentService(model_service, tool_service)

# 全局会话存储
sessions = {}


@app.on_event("startup")
async def startup_event():
    """应用启动时执行的初始化。"""
    # 注册模型
    await model_service.register_model(
        ModelConfig(
            model_id="gpt-3.5-turbo",
            provider=ModelProvider.OPENAI,
            model_type=ModelType.CHAT,
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.FUNCTION_CALLING
            ],
            parameters={
                "temperature": 0.7,
                "max_tokens": 1000
            },
            description="高性能通用聊天模型"
        )
    )
    
    # 注册工具
    await tool_service.register_tool(
        ToolDefinition(
            tool_id="calculator",
            name="计算器",
            description="执行数学计算",
            parameters=[
                ToolParameter(
                    name="expression",
                    description="要计算的数学表达式",
                    parameter_type=ToolParameterType.STRING,
                    required=True
                )
            ]
        )
    )
    
    await tool_service.register_tool(
        ToolDefinition(
            tool_id="weather",
            name="天气查询",
            description="查询指定位置的天气",
            parameters=[
                ToolParameter(
                    name="location",
                    description="要查询天气的位置",
                    parameter_type=ToolParameterType.STRING,
                    required=True
                )
            ]
        )
    )
    
    # 注册代理
    await agent_service.register_agent(
        AgentConfig(
            agent_id="chat-assistant",
            name="聊天助手",
            description="通用聊天助手",
            model_id="gpt-3.5-turbo",
            capabilities=[
                AgentCapability.CHAT,
                AgentCapability.TOOL_USE
            ],
            parameters={
                "tool_usage_threshold": 0.7,
                "max_tool_uses": 3
            }
        )
    )
    
    logger.info("AgentForge聊天应用初始化完成")


@app.get("/")
async def read_root():
    """API根路径。"""
    return {"message": "欢迎使用AgentForge聊天API"}


@app.post("/chat")
async def chat(request: Request):
    """处理聊天请求。"""
    try:
        data = await request.json()
        session_id = data.get("session_id", str(uuid.uuid4()))
        message = data.get("message", "")
        
        if not message:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "消息不能为空"}
            )
        
        # 创建会话或获取现有会话
        if session_id not in sessions:
            sessions[session_id] = {
                "id": session_id,
                "created_at": datetime.now().isoformat(),
                "messages": []
            }
        
        # 添加用户消息到会话
        sessions[session_id]["messages"].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # 处理消息
        response = await agent_service.process_message("chat-assistant", message)
        
        if response.success:
            # 添加代理响应到会话
            sessions[session_id]["messages"].append({
                "role": "assistant",
                "content": response.data,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "session_id": session_id,
                "message": response.data
            }
        else:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": response.error}
            )
    
    except Exception as e:
        logger.error(f"处理聊天请求时出错: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"内部服务器错误: {str(e)}"}
        )


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket聊天接口。"""
    await websocket.accept()
    
    try:
        # 接收第一条消息，包含会话信息
        data = await websocket.receive_json()
        session_id = data.get("session_id", str(uuid.uuid4()))
        
        # 创建会话或获取现有会话
        if session_id not in sessions:
            sessions[session_id] = {
                "id": session_id,
                "created_at": datetime.now().isoformat(),
                "messages": []
            }
        
        # 发送会话确认
        await websocket.send_json({
            "type": "session",
            "session_id": session_id
        })
        
        # 主消息循环
        while True:
            # 接收消息
            data = await websocket.receive_json()
            message_type = data.get("type", "")
            
            if message_type == "message":
                message = data.get("content", "")
                
                if not message:
                    await websocket.send_json({
                        "type": "error",
                        "error": "消息不能为空"
                    })
                    continue
                
                # 添加用户消息到会话
                sessions[session_id]["messages"].append({
                    "role": "user",
                    "content": message,
                    "timestamp": datetime.now().isoformat()
                })
                
                # 发送正在输入状态
                await websocket.send_json({
                    "type": "status",
                    "status": "typing"
                })
                
                # 流式处理消息
                full_response = ""
                async for chunk_response in agent_service.stream_process_message("chat-assistant", message):
                    if chunk_response.success:
                        chunk = chunk_response.data
                        full_response += chunk
                        
                        await websocket.send_json({
                            "type": "chunk",
                            "content": chunk
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "error": chunk_response.error
                        })
                        break
                
                # 添加完整响应到会话
                sessions[session_id]["messages"].append({
                    "role": "assistant",
                    "content": full_response,
                    "timestamp": datetime.now().isoformat()
                })
                
                # 发送完成状态
                await websocket.send_json({
                    "type": "status",
                    "status": "complete"
                })
            
            elif message_type == "ping":
                # 心跳检测
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket客户端断开连接: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket处理时出错: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "error": f"服务器错误: {str(e)}"
            })
        except:
            pass


# ====== 示例工作流 ======

async def run_example_workflow():
    """运行示例工作流，展示各组件的集成。"""
    print("\n----- 开始运行示例工作流 -----")
    
    # 展示已注册模型
    model_response = await model_service.get_model("gpt-3.5-turbo")
    print(f"\n已注册模型: {model_response.data.model_id}")
    print(f"模型提供商: {model_response.data.provider}")
    print(f"模型类型: {model_response.data.model_type}")
    
    # 展示已注册工具
    tools_response = await tool_service.list_tools()
    print(f"\n已注册工具:")
    for tool in tools_response.data:
        print(f"  - {tool.name} ({tool.tool_id}): {tool.description}")
    
    # 展示已注册代理
    agent_response = await agent_service.get_agent("chat-assistant")
    print(f"\n已注册代理: {agent_response.data.name}")
    print(f"代理描述: {agent_response.data.description}")
    print(f"使用的模型: {agent_response.data.model_id}")
    
    # 示例1: 基本聊天
    print("\n\n示例1: 基本聊天")
    chat_message = "你好，请告诉我今天的日期。"
    print(f"用户: {chat_message}")
    
    chat_response = await agent_service.process_message("chat-assistant", chat_message)
    print(f"助手: {chat_response.data}")
    
    # 示例2: 使用计算器工具
    print("\n\n示例2: 使用计算器工具")
    calc_message = "请帮我计算 123 * 456，使用calculator工具 expression:123*456"
    print(f"用户: {calc_message}")
    
    calc_response = await agent_service.process_message("chat-assistant", calc_message)
    print(f"助手: {calc_response.data}")
    
    # 示例3: 使用天气工具
    print("\n\n示例3: 使用天气工具")
    weather_message = "北京的天气怎么样？使用weather工具 location:北京"
    print(f"用户: {weather_message}")
    
    weather_response = await agent_service.process_message("chat-assistant", weather_message)
    print(f"助手: {weather_response.data}")
    
    # 示例4: 流式响应演示
    print("\n\n示例4: 流式响应演示")
    stream_message = "请给我讲一个简短的故事"
    print(f"用户: {stream_message}")
    
    print("助手: ", end="", flush=True)
    async for chunk_response in agent_service.stream_process_message("chat-assistant", stream_message):
        if chunk_response.success:
            chunk = chunk_response.data
            print(chunk, end="", flush=True)
    
    print("\n\n----- 示例工作流运行完成 -----")
    print("您可以通过HTTP API或WebSocket接口与聊天应用交互")
    print("HTTP API: POST /chat")
    print("WebSocket: /ws/chat")


# ====== 主程序 ======

async def main():
    """
    主程序入口。
    
    在实际应用中，各个服务应在不同的进程或容器中运行。
    此示例将所有组件集成在一个应用中，以演示完整的工作流程。
    """
    print("==== AgentForge完整应用示例 ====")
    print("该示例演示了如何集成AgentForge的所有核心组件，构建一个完整的端到端应用。")
    print("包括代理服务、模型服务、工具服务、API网关和客户端应用。")
    
    # 运行示例工作流
    await run_example_workflow()


if __name__ == "__main__":
    # 运行主程序
    asyncio.run(main())
