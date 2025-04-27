# 集成指南

本指南详细说明如何在不同服务中集成和使用shared_contracts模块，包括最佳实践和常见集成模式。

## 目录

- [服务集成概述](#服务集成概述)
- [代理服务集成](#代理服务集成)
- [模型服务集成](#模型服务集成)
- [工具服务集成](#工具服务集成)
- [错误处理和恢复](#错误处理和恢复)
- [监控集成](#监控集成)
- [服务间通信模式](#服务间通信模式)
- [完整示例应用](#完整示例应用)

## 服务集成概述

shared_contracts模块采用契约优先的设计原则，为不同服务组件之间的通信提供标准接口和数据模型。

### 集成步骤概览

1. **导入契约**：在服务中导入所需的接口和数据模型
2. **实现接口**：遵循标准接口实现服务功能
3. **使用数据模型**：使用共享数据模型进行数据验证和转换
4. **集成监控**：添加监控和日志记录
5. **错误处理**：实现标准错误处理机制

### 架构示例

```
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   API网关     │    │    代理服务    │    │    模型服务    │
│  (FastAPI)    │◄───┤  (Interface)  │◄───┤  (Interface)  │
└───────┬───────┘    └───────┬───────┘    └───────────────┘
        │                    │
        │                    ▼
┌───────▼───────┐    ┌───────────────┐
│    用户界面    │    │    工具服务    │
│    (Web/CLI)   │    │  (Interface)  │
└───────────────┘    └───────────────┘
```

### 核心设计原则

- **松耦合**：服务之间只依赖接口，不依赖具体实现
- **强类型**：使用Pydantic模型确保类型安全和数据验证
- **可观测性**：集成监控为所有服务组件提供可观测性
- **故障隔离**：服务间错误不应级联传播

### 依赖关系

集成shared_contracts需要以下依赖项：

```python
# 核心依赖
pydantic>=2.0.0
typing-extensions>=4.0.0
python-dateutil>=2.8.0

# 监控依赖（可选）
logfire>=0.3.0
opentelemetry-api>=1.7.0
opentelemetry-sdk>=1.7.0
```

### 快速开始

1. 安装shared_contracts：

```bash
pip install agentforge-shared-contracts
```

2. 导入所需组件：

```python
# 导入接口
from shared_contracts.core.interfaces.agent_interface import AgentServiceInterface
from shared_contracts.core.interfaces.model_interface import ModelServiceInterface
from shared_contracts.core.interfaces.tool_interface import ToolServiceInterface

# 导入数据模型
from shared_contracts.core.models.agent_models import AgentConfig, AgentState
from shared_contracts.core.models.model_models import ModelConfig, ModelResponse
from shared_contracts.core.models.tool_models import ToolDefinition, ToolResult

# 导入监控组件
from shared_contracts.monitoring import configure_monitor, ServiceComponent, EventType
```

## 代理服务集成

代理服务是AgentForge平台的核心组件，负责协调模型服务和工具服务。

### 实现Agent接口

```python
from shared_contracts.core.interfaces.agent_interface import AgentServiceInterface
from shared_contracts.core.models.base_models import BaseResponse
from shared_contracts.core.models.agent_models import AgentConfig, AgentState, AgentStatus
from shared_contracts.monitoring import (
    configure_monitor, ServiceComponent, EventType, with_monitoring
)
import uuid
from typing import Dict, Any, List, Optional

# 配置监控
monitor = configure_monitor(
    service_name="agent-service",
    api_key="your-api-key",
    project_id="your-project-id",
    environment="production"
)

class AgentService(AgentServiceInterface):
    """代理服务实现。"""
    
    def __init__(self, model_service, tool_service):
        self.agents = {}  # 存储代理配置
        self.agent_states = {}  # 存储代理状态
        self.model_service = model_service  # 模型服务客户端
        self.tool_service = tool_service  # 工具服务客户端
    
    @with_monitoring(component=ServiceComponent.AGENT_CORE)
    async def create_agent(self, config: AgentConfig) -> BaseResponse[AgentConfig]:
        """创建一个新代理。"""
        # 验证模型ID
        model_response = await self.model_service.get_model(config.model_id)
        if not model_response.success:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Invalid model: {model_response.error}"
            )
        
        # 验证工具
        for tool_id in config.tools:
            tool_response = await self.tool_service.get_tool(tool_id)
            if not tool_response.success:
                return BaseResponse(
                    request_id=uuid.uuid4(),
                    success=False,
                    error=f"Invalid tool: {tool_id}"
                )
        
        # 确保代理ID
        agent_id = config.agent_id or uuid.uuid4()
        config.agent_id = agent_id
        
        # 存储代理配置
        self.agents[agent_id] = config
        
        # 初始化代理状态
        self.agent_states[agent_id] = AgentState(
            agent_id=agent_id,
            status=AgentStatus.INITIALIZING,
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        
        # 更新代理状态为就绪
        self.agent_states[agent_id].status = AgentStatus.READY
        
        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data=config
        )
    
    # 实现其他接口方法...
```

### 使用Agent客户端

客户端是服务消费者用来与服务交互的组件。以下是一个使用HTTP的客户端实现：

```python
from shared_contracts.core.interfaces.agent_interface import AgentServiceInterface
from shared_contracts.core.models.agent_models import AgentConfig, AgentCapability
import httpx
import json
import uuid
from typing import Dict, Any, Optional

class AgentServiceClient:
    """代理服务客户端。"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        初始化客户端。
        
        Args:
            base_url: 代理服务的基础URL
            api_key: 可选的API密钥
        """
        self.base_url = base_url
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        self.client = httpx.AsyncClient(base_url=base_url, headers=headers)
    
    async def create_agent(self, config: AgentConfig):
        """创建代理。"""
        response = await self.client.post(
            "/agents",
            json=config.model_dump()
        )
        
        data = response.json()
        if response.status_code == 200 and data["success"]:
            return {
                "success": True,
                "data": AgentConfig.model_validate(data["data"])
            }
        else:
            return {
                "success": False,
                "error": data.get("error", "Unknown error")
            }
    
    # 实现其他客户端方法...
```

### Agent接口最佳实践

1. **状态管理**：保持代理状态的准确性，避免代理在处理请求时永久卡在BUSY状态
2. **工具集成**：验证代理有权限使用的工具，避免未授权的工具调用
3. **会话跟踪**：使用conversation_id跟踪会话，允许多轮对话
4. **模型集成**：代理应通过模型服务接口而非直接调用模型 API
5. **并发控制**：实现资源限制，避免单个代理过度消耗资源

## 模型服务集成

模型服务负责与AI模型交互，通常需要集成外部API。

### 实现Model接口

```python
from shared_contracts.core.interfaces.model_interface import ModelServiceInterface
from shared_contracts.core.models.base_models import BaseResponse
from shared_contracts.core.models.model_models import (
    ModelConfig, ModelResponse, ModelProvider, ModelType, ModelCapability
)
from shared_contracts.monitoring import (
    configure_monitor, ServiceComponent, EventType, track_performance
)
import uuid
import os
import json
import httpx
from typing import Dict, Any, List, Optional, AsyncIterable

# 配置监控
monitor = configure_monitor(
    service_name="model-service",
    api_key="your-api-key",
    project_id="your-project-id",
    environment="production"
)

class OpenAIModelService(ModelServiceInterface):
    """在此实现OpenAI模型服务。"""
    
    def __init__(self):
        self.models = {}  # 存储模型配置
    
    async def register_model(self, config: ModelConfig) -> BaseResponse[ModelConfig]:
        """注册一个模型。"""
        # 检查API密钥环境变量
        env_var = config.api_key_env_var
        api_key = os.environ.get(env_var)
        if not api_key:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Missing API key: Environment variable {env_var} not set"
            )
        
        # 验证模型提供商
        if config.provider != ModelProvider.OPENAI:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Unsupported provider: {config.provider}"
            )
        
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
    
    # 实现其他接口方法...
```

### 模型提供商集成

AgentForge支持多种模型提供商的集成。以下是支持的模型提供商及其集成方式的概览：

1. **OpenAI**：通过官方API集成，支持GPT-3.5、GPT-4等模型
2. **Anthropic**：通过Claude API集成，支持Claude系列模型
3. **HuggingFace**：通过推理API集成，支持开源模型
4. **Azure OpenAI**：通过Azure API集成，支持GPT模型
5. **本地模型**：支持使用LLaMA、Mistral等开源模型的本地部署

每个提供商的集成方式略有不同，但都遵循ModelServiceInterface定义的标准接口。

### 流式响应处理

对于支持流式响应的模型，可以通过以下方式实现：

```python
async def generate_completion_streaming(
    self,
    model_id: str,
    prompt: str,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    **options: Any,
) -> AsyncIterable[ModelResponse]:
    """流式生成文本完成。"""
    # 检查模型是否已注册
    if model_id not in self.models:
        yield BaseResponse(
            request_id=uuid.uuid4(),
            success=False,
            error=f"Model not found: {model_id}"
        )
        return
    
    config = self.models[model_id]
    
    # 准备API调用
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": config.provider_model_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature or config.capabilities.temperature or 0.7,
        "max_tokens": max_tokens or config.capabilities.max_tokens,
        "stream": True
    }
    
    # 异步请求和流式处理
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=config.timeout
        ) as response:
            if response.status_code != 200:
                yield BaseResponse(
                    request_id=uuid.uuid4(),
                    success=False,
                    error=f"API error: {response.status_code}"
                )
                return
            
            content_buffer = ""
            async for line in response.aiter_lines():
                line = line.strip()
                if line.startswith("data:") and not line.endswith("[DONE]"):
                    json_str = line[5:].strip()
                    try:
                        data = json.loads(json_str)
                        chunk = data["choices"][0]["delta"].get("content", "")
                        content_buffer += chunk
                        
                        yield BaseResponse(
                            request_id=uuid.uuid4(),
                            success=True,
                            data=ModelResponse(
                                model_id=model_id,
                                request_id=uuid.uuid4(),
                                content=chunk,
                                is_partial=True,
                                finish_reason=None
                            )
                        )
                    except json.JSONDecodeError:
                        pass
            
            # 发送最终完整响应
            yield BaseResponse(
                request_id=uuid.uuid4(),
                success=True,
                data=ModelResponse(
                    model_id=model_id,
                    request_id=uuid.uuid4(),
                    content=content_buffer,
                    is_partial=False,
                    finish_reason="stop"
                )
            )
```

## 工具服务集成

工具服务为代理提供外部功能访问，如计算、数据检索、API调用等。

### 实现Tool接口

```python
from shared_contracts.core.interfaces.tool_interface import ToolServiceInterface
from shared_contracts.core.models.base_models import BaseResponse
from shared_contracts.core.models.tool_models import (
    ToolDefinition, ToolResult, ToolResultStatus, ToolParameter, ToolParameterType
)
from shared_contracts.monitoring import (
    configure_monitor, ServiceComponent, EventType, with_monitoring
)
import uuid
from typing import Dict, Any, List, Optional, AsyncIterable

# 配置监控
monitor = configure_monitor(
    service_name="tool-service",
    api_key="your-api-key",
    project_id="your-project-id",
    environment="production"
)

class ToolService(ToolServiceInterface):
    """工具服务实现。"""
    
    def __init__(self):
        self.tools = {}  # 存储工具定义
        
        # 注册内置工具
        self._register_built_in_tools()
    
    def _register_built_in_tools(self):
        """注册内置工具。"""
        # 示例：注册计算器工具
        calculator_tool = ToolDefinition(
            tool_id="calculator",
            name="Calculator",
            description="A simple calculator tool",
            version="1.0.0"
        )
        
        # 添加参数
        calculator_tool.parameters.parameters = {
            "operation": ToolParameter(
                name="operation",
                description="Operation to perform",
                type=ToolParameterType.STRING,
                enum=["add", "subtract", "multiply", "divide"]
            ),
            "a": ToolParameter(
                name="a",
                description="First number",
                type=ToolParameterType.NUMBER
            ),
            "b": ToolParameter(
                name="b",
                description="Second number",
                type=ToolParameterType.NUMBER
            )
        }
        
        self.tools[calculator_tool.tool_id] = calculator_tool
    
    @with_monitoring(component=ServiceComponent.TOOL_SERVICE)
    async def execute_tool(
        self, 
        tool_id: str, 
        parameters: Dict[str, Any],
        stream: bool = False
    ) -> BaseResponse[ToolResult]:
        """执行工具。"""
        # 检查工具是否存在
        if tool_id not in self.tools:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Tool not found: {tool_id}"
            )
        
        try:
            # 根据工具类型执行不同操作
            if tool_id == "calculator":
                result = await self._execute_calculator(parameters)
            else:
                # 默认工具执行
                result = {"parameters": parameters, "result": "Tool execution placeholder"}
            
            # 创建成功结果
            tool_result = ToolResult(
                tool_id=tool_id,
                request_id=uuid.uuid4(),
                status=ToolResultStatus.SUCCESS,
                data=result
            )
            
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=True,
                data=tool_result
            )
            
        except Exception as e:
            # 记录执行错误
            tool_result = ToolResult(
                tool_id=tool_id,
                request_id=uuid.uuid4(),
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
            
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=True,  # 注意这里是True，因为服务正常处理了请求，只是工具执行失败
                data=tool_result
            )
```

### 创建自定义工具

创建自定义工具的步骤：

1. **定义工具**：创建ToolDefinition实例
2. **定义参数**：指定工具参数和类型
3. **实现执行逻辑**：创建执行工具的方法
4. **注册工具**：将工具添加到工具服务中

示例—创建一个天气查询工具：

```python
# 定义工具
weather_tool = ToolDefinition(
    tool_id="weather",
    name="Weather Lookup",
    description="Get current weather for a location",
    version="1.0.0"
)

# 定义参数
weather_tool.parameters.parameters = {
    "location": ToolParameter(
        name="location",
        description="City or location name",
        type=ToolParameterType.STRING,
        required=True
    ),
    "units": ToolParameter(
        name="units",
        description="Temperature units",
        type=ToolParameterType.STRING,
        enum=["celsius", "fahrenheit"],
        default="celsius"
    )
}

# 实现执行逻辑
async def execute_weather_tool(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """执行天气查询工具。"""
    location = parameters.get("location")
    units = parameters.get("units", "celsius")
    
    # 这里应调用实际的天气API
    api_url = f"https://api.weatherservice.com/current?location={location}&units={units}"
    async with httpx.AsyncClient() as client:
        response = await client.get(api_url)
        data = response.json()
        
        return {
            "temperature": data["temperature"],
            "condition": data["condition"],
            "humidity": data["humidity"],
            "location": location,
            "units": units
        }
```

### 工具注册和发现

工具服务提供注册和发现机制，使代理能够查找和使用可用工具：

```python
# 注册工具
async def register_tool_endpoint(request: Request):
    """注册新工具的API端点。"""
    tool_data = await request.json()
    tool = ToolDefinition.model_validate(tool_data)
    
    response = await tool_service.register_tool(tool)
    return response.model_dump()

# 列出可用工具
async def list_tools_endpoint():
    """列出所有可用工具的API端点。"""
    response = await tool_service.list_tools()
    return response.model_dump()
```

## 错误处理和恢复

错误处理对于保持服务的健壮性和可靠性至关重要。

### 标准错误处理模式

shared_contracts提供了一组标准错误类型：

```python
from shared_contracts.core.interfaces.common_errors import (
    ServiceError,          # 服务通用错误
    NotFoundError,         # 资源未找到
    ValidationError,       # 数据验证错误
    AuthenticationError,   # 认证错误
    AuthorizationError,    # 授权错误
    RateLimitError,        # 速率限制错误
    DependencyError,       # 依赖服务错误
    TimeoutError,          # 超时错误
)
```

使用标准错误处理函数：

```python
# API错误处理函数
async def handle_api_error(request_id, error):
    """处理API错误并生成标准化响应。"""
    if isinstance(error, NotFoundError):
        return BaseResponse(
            request_id=request_id,
            success=False,
            error=error.message,
            status_code=404
        )
    elif isinstance(error, ValidationError):
        return BaseResponse(
            request_id=request_id,
            success=False,
            error=f"Validation error: {error.message}",
            status_code=400
        )
    elif isinstance(error, AuthenticationError):
        return BaseResponse(
            request_id=request_id,
            success=False,
            error="Authentication failed",
            status_code=401
        )
    elif isinstance(error, ServiceError):
        return BaseResponse(
            request_id=request_id,
            success=False,
            error=error.message,
            status_code=500
        )
    else:
        # 未知错误
        return BaseResponse(
            request_id=request_id,
            success=False,
            error=f"Internal server error: {str(error)}",
            status_code=500
        )
```

### 重试策略

对于不可靠的外部服务，实现指数退避重试：

```python
from shared_contracts.utils.timing import retry_with_backoff

@retry_with_backoff(max_retries=3, initial_delay=0.5, max_delay=5.0)
async def call_external_api(url, data):
    """调用外部API，失败时自动重试。"""
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, timeout=10.0)
        response.raise_for_status()
        return response.json()
```

### 断路器模式

为防止级联故障，可以实现断路器模式：

```python
from shared_contracts.utils.resilience import CircuitBreaker

# 创建断路器
api_circuit = CircuitBreaker(
    failure_threshold=5,       # 5次失败后开路
    recovery_timeout=30.0,     # 30秒后尝试恢复
    name="external-api"
)

async def call_api_with_circuit_breaker(url, data):
    """使用断路器调用API。"""
    # 检查断路器状态
    if not api_circuit.allow_request():
        raise ServiceError("Service temporarily unavailable (circuit open)")
    
    try:
        # 尝试调用API
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, timeout=5.0)
            response.raise_for_status()
            
            # 记录成功
            api_circuit.record_success()
            return response.json()
            
    except Exception as e:
        # 记录失败
        api_circuit.record_failure()
        raise ServiceError(f"API call failed: {str(e)}")
```

## 监控集成

监控集成对于服务可观测性至关重要。AgentForge使用LogFire作为主要监控后端。

### 配置监控

```python
from shared_contracts.monitoring import (
    configure_monitor, 
    ServiceComponent, 
    EventType, 
    LogLevel
)

# 配置监控客户端
monitor = configure_monitor(
    service_name="agent-service",
    api_key="your-logfire-api-key",
    project_id="your-logfire-project-id",
    environment="production",
    version="1.0.0",
    min_log_level=LogLevel.INFO
)
```

### 记录事件

```python
# 记录信息事件
monitor.info(
    message="Agent created successfully",
    component=ServiceComponent.AGENT_CORE,
    event_type=EventType.LIFECYCLE,
    agent_id=str(agent_id),
    model_id=model_id
)

# 记录警告
monitor.warning(
    message="Rate limit approaching",
    component=ServiceComponent.MODEL_SERVICE,
    event_type=EventType.SYSTEM,
    model_id=model_id,
    current_rate=current_rate,
    limit=rate_limit
)

# 记录错误
monitor.error(
    message="Failed to generate completion",
    component=ServiceComponent.MODEL_SERVICE,
    event_type=EventType.EXCEPTION,
    model_id=model_id,
    error=str(error),
    error_type=type(error).__name__
)
```

### 跟踪API调用

```python
# 记录API调用
monitor.record_api_call(
    api_name="generate_completion",
    status_code=200,
    duration_ms=response_time,
    component=ServiceComponent.MODEL_SERVICE,
    request_data={
        "model_id": model_id,
        "prompt_length": len(prompt)
    },
    response_data={
        "completion_length": len(completion),
        "tokens_used": tokens_used
    }
)
```

### 性能跟踪

```python
from shared_contracts.monitoring import track_performance

# 使用上下文管理器跟踪性能
with track_performance("model_inference", ServiceComponent.MODEL_SERVICE) as span:
    # 执行需要跟踪的操作
    result = await expensive_operation()
    
    # 添加额外数据
    span.add_data({
        "operation_type": "inference",
        "model_id": model_id,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens
    })
```

### 使用装饰器跟踪方法

```python
from shared_contracts.monitoring import with_monitoring

class ModelService:
    @with_monitoring(component=ServiceComponent.MODEL_SERVICE)
    async def generate_completion(self, model_id, prompt, **options):
        """生成文本完成。"""
        # 方法自动被监控
        result = await self._call_model_api(model_id, prompt, **options)
        return result
```

### 分布式追踪

在微服务架构中，分布式追踪对于理解请求流非常重要：

```python
from shared_contracts.monitoring import (
    create_trace_context,
    get_current_span,
    set_span_attribute
)

async def process_request(request_data):
    """处理跨服务请求。"""
    # 创建追踪上下文
    with create_trace_context("process_request", ServiceComponent.API_GATEWAY) as span:
        # 添加请求属性
        span.add_data({
            "request_type": request_data["type"],
            "user_id": request_data["user_id"]
        })
        
        # 调用代理服务
        agent_result = await call_agent_service(request_data)
        
        # 添加响应属性
        span.add_data({
            "agent_id": agent_result["agent_id"],
            "status": agent_result["status"]
        })
        
        return agent_result

async def call_agent_service(request_data):
    """调用代理服务，传递追踪上下文。"""
    # 获取当前span
    current_span = get_current_span()
    
    # 传递跟踪上下文
    headers = {
        "X-Trace-ID": current_span.trace_id,
        "X-Span-ID": current_span.span_id
    }
    
    # 调用服务
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://agent-service/api/agents",
            json=request_data,
            headers=headers
        )
        
        return response.json()
```

## 服务间通信模式

在AgentForge架构中，服务可以通过多种方式进行通信。以下是常见的通信模式。

### 直接HTTP调用

最简单的通信方式是使用HTTP/REST API：

```python
import httpx
import json
import uuid

async def call_model_service(model_id, prompt, **options):
    """直接调用模型服务。"""
    request_id = str(uuid.uuid4())
    
    payload = {
        "model_id": model_id,
        "prompt": prompt,
        "request_id": request_id,
        **options
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://model-service:8000/api/completions",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        return response.json()
```

### gRPC服务

对于高性能需求，可以使用gRPC：

```python
# 定义proto文件
"""
syntax = "proto3";

package agentforge;

service ModelService {
    rpc GenerateCompletion (CompletionRequest) returns (CompletionResponse);
    rpc GetModel (GetModelRequest) returns (GetModelResponse);
}

message CompletionRequest {
    string model_id = 1;
    string prompt = 2;
    string request_id = 3;
    int32 max_tokens = 4;
    float temperature = 5;
}

message CompletionResponse {
    bool success = 1;
    string error = 2;
    string content = 3;
    string request_id = 4;
    string finish_reason = 5;
}
"""

# 客户端实现
import grpc
import model_service_pb2
import model_service_pb2_grpc
import uuid

class ModelServiceGrpcClient:
    def __init__(self, server_address):
        self.channel = grpc.aio.insecure_channel(server_address)
        self.stub = model_service_pb2_grpc.ModelServiceStub(self.channel)
    
    async def generate_completion(self, model_id, prompt, **options):
        """生成文本完成。"""
        request = model_service_pb2.CompletionRequest(
            model_id=model_id,
            prompt=prompt,
            request_id=str(uuid.uuid4()),
            max_tokens=options.get("max_tokens", 1000),
            temperature=options.get("temperature", 0.7)
        )
        
        try:
            response = await self.stub.GenerateCompletion(request)
            
            if response.success:
                return {
                    "success": True,
                    "content": response.content,
                    "request_id": response.request_id,
                    "finish_reason": response.finish_reason
                }
            else:
                return {
                    "success": False,
                    "error": response.error,
                    "request_id": response.request_id
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "request_id": str(uuid.uuid4())
            }
```

### 消息队列模式

对于异步通信和松耦合架构，可以使用消息队列：

```python
import asyncio
import json
import uuid
from shared_contracts.utils.serialization import serialize_model, deserialize_model
from shared_contracts.core.models.agent_models import AgentConfig

# 使用Redis作为消息队列示例
import redis.asyncio as redis

class MessageQueueClient:
    def __init__(self, redis_url):
        self.redis = redis.from_url(redis_url)
        self.pending_requests = {}
    
    async def start_consumer(self, response_queue):
        """启动消息消费者。"""
        try:
            while True:
                # 等待响应
                message = await self.redis.blpop(response_queue, timeout=0)
                _, data = message
                
                # 解析响应
                response = json.loads(data)
                request_id = response.get("request_id")
                
                # 如果存在等待的请求，通知它
                if request_id in self.pending_requests:
                    self.pending_requests[request_id].set_result(response)
                    del self.pending_requests[request_id]
        
        except asyncio.CancelledError:
            # 消费者被取消
            pass
    
    async def send_request(self, queue_name, request_data, timeout=30):
        """发送请求并等待响应。"""
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request_data["request_id"] = request_id
        
        # 设置响应队列
        response_queue = f"response:{request_id}"
        
        # 创建Future用于等待响应
        future = asyncio.get_event_loop().create_future()
        self.pending_requests[request_id] = future
        
        # 发送请求
        await self.redis.rpush(queue_name, json.dumps(request_data))
        
        try:
            # 等待响应或超时
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            del self.pending_requests[request_id]
            return {"success": False, "error": "Request timed out"}
    
    async def create_agent(self, config: AgentConfig):
        """创建代理。"""
        # 序列化请求
        request_data = {
            "action": "create_agent",
            "data": serialize_model(config)
        }
        
        # 发送请求并等待响应
        response = await self.send_request("agent_service", request_data)
        
        if response.get("success"):
            # 反序列化响应
            agent_config = deserialize_model(AgentConfig, response.get("data"))
            return {"success": True, "data": agent_config}
        else:
            return {"success": False, "error": response.get("error")}
```

## 完整示例应用

以下示例展示了如何构建一个完整的聊天应用，集成代理服务、模型服务和工具服务。

### API网关集成

```python
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional
import uuid
import os
import httpx
import json

# 导入shared_contracts组件
from shared_contracts.core.models.agent_models import AgentConfig, AgentCapability
from shared_contracts.core.models.model_models import (
    ModelConfig, ModelProvider, ModelType, ModelCapability
)
from shared_contracts.core.models.tool_models import ToolDefinition
from shared_contracts.monitoring import (
    configure_monitor, ServiceComponent, EventType, with_monitoring
)

# 创建应用
app = FastAPI(title="AgentForge API Gateway")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置监控
monitor = configure_monitor(
    service_name="api-gateway",
    api_key=os.environ.get("LOGFIRE_API_KEY"),
    project_id=os.environ.get("LOGFIRE_PROJECT_ID"),
    environment=os.environ.get("ENVIRONMENT", "development")
)

# 服务客户端
class ServiceClient:
    def __init__(self, base_url: str, service_name: str):
        self.base_url = base_url
        self.service_name = service_name
        self.client = httpx.AsyncClient(base_url=base_url)
    
    async def request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None):
        """发送请求到服务。"""
        try:
            if method.upper() == "GET":
                response = await self.client.get(endpoint)
            elif method.upper() == "POST":
                response = await self.client.post(endpoint, json=data)
            elif method.upper() == "PUT":
                response = await self.client.put(endpoint, json=data)
            elif method.upper() == "DELETE":
                response = await self.client.delete(endpoint)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response.json()
        except Exception as e:
            monitor.error(
                message=f"Error calling {self.service_name}: {str(e)}",
                component=ServiceComponent.API_GATEWAY,
                event_type=EventType.EXCEPTION,
                service=self.service_name,
                endpoint=endpoint,
                error=str(e)
            )
            raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")

# 创建服务客户端
agent_client = ServiceClient(
    os.environ.get("AGENT_SERVICE_URL", "http://localhost:8001"),
    "agent-service"
)

model_client = ServiceClient(
    os.environ.get("MODEL_SERVICE_URL", "http://localhost:8002"),
    "model-service"
)

tool_client = ServiceClient(
    os.environ.get("TOOL_SERVICE_URL", "http://localhost:8003"),
    "tool-service"
)

# 依赖项：获取请求ID
async def get_request_id(request: Request):
    if hasattr(request.state, "request_id"):
        return request.state.request_id
    return str(uuid.uuid4())

# API路由
@app.post("/api/agents")
@with_monitoring(component=ServiceComponent.API_GATEWAY)
async def create_agent(agent: Dict[str, Any], request_id: str = Depends(get_request_id)):
    """创建代理。"""
    response = await agent_client.request("POST", "/agents", agent)
    return response

@app.get("/api/agents/{agent_id}")
@with_monitoring(component=ServiceComponent.API_GATEWAY)
async def get_agent(agent_id: str, request_id: str = Depends(get_request_id)):
    """获取代理。"""
    response = await agent_client.request("GET", f"/agents/{agent_id}")
    return response

@app.post("/api/agents/{agent_id}/messages")
@with_monitoring(component=ServiceComponent.API_GATEWAY)
async def send_message(
    agent_id: str, 
    message: Dict[str, Any],
    request_id: str = Depends(get_request_id)
):
    """向代理发送消息。"""
    response = await agent_client.request("POST", f"/agents/{agent_id}/messages", message)
    return response

@app.post("/api/models")
@with_monitoring(component=ServiceComponent.API_GATEWAY)
async def register_model(model: Dict[str, Any], request_id: str = Depends(get_request_id)):
    """注册模型。"""
    response = await model_client.request("POST", "/models", model)
    return response

@app.post("/api/tools")
@with_monitoring(component=ServiceComponent.API_GATEWAY)
async def register_tool(tool: Dict[str, Any], request_id: str = Depends(get_request_id)):
    """注册工具。"""
    response = await tool_client.request("POST", "/tools", tool)
    return response

@app.get("/api/health")
async def health_check():
    """健康检查。"""
    return {
        "status": "healthy",
        "services": {
            "agent_service": "healthy",
            "model_service": "healthy",
            "tool_service": "healthy"
        }
    }

# 启动应用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 客户端 SDK集成

```python
import httpx
import json
import uuid
from typing import Dict, Any, List, Optional, Union

class AgentForgeClient:
    """客户端SDK。"""
    
    def __init__(self, api_url: str, api_key: Optional[str] = None):
        """
        初始化客户端。
        
        Args:
            api_url: API网关的URL
            api_key: 可选的API密钥
        """
        self.api_url = api_url
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        self.client = httpx.AsyncClient(base_url=api_url, headers=headers)
    
    async def create_agent(
        self,
        name: str,
        description: str,
        model_id: str,
        system_prompt: str,
        capabilities: List[str] = ["conversation"],
        tools: List[str] = []
    ) -> Dict[str, Any]:
        """
        创建代理。
        
        Args:
            name: 代理名称
            description: 代理描述
            model_id: 模型ID
            system_prompt: 系统提示词
            capabilities: 代理能力列表
            tools: 工具ID列表
            
        Returns:
            创建结果
        """
        payload = {
            "name": name,
            "description": description,
            "model_id": model_id,
            "system_prompt": system_prompt,
            "capabilities": capabilities,
            "tools": tools
        }
        
        response = await self.client.post("/api/agents", json=payload)
        return response.json()
    
    async def send_message(
        self,
        agent_id: Union[str, uuid.UUID],
        message: str,
        conversation_id: Optional[Union[str, uuid.UUID]] = None
    ) -> Dict[str, Any]:
        """
        向代理发送消息。
        
        Args:
            agent_id: 代理ID
            message: 消息内容
            conversation_id: 可选的对话ID
            
        Returns:
            代理响应
        """
        payload = {
            "message": message
        }
        
        if conversation_id:
            payload["conversation_id"] = str(conversation_id)
        
        response = await self.client.post(
            f"/api/agents/{agent_id}/messages",
            json=payload
        )
        
        return response.json()
```

### 使用示例

```python
# 使用SDK的示例
async def main():
    # 创建客户端
    client = AgentForgeClient("http://localhost:8000")
    
    # 注册模型
    model_result = await client.register_model(
        model_id="gpt-4",
        provider="openai",
        model_type="chat",
        display_name="GPT-4",
        capabilities={
            "supports_streaming": True,
            "supports_function_calling": True,
            "supports_json_mode": True,
            "supports_vision": False,
            "max_tokens": 8192
        },
        provider_model_id="gpt-4-turbo",
        api_key_env_var="OPENAI_API_KEY"
    )
    
    print(f"Model registration result: {model_result}")
    
    # 创建代理
    agent_result = await client.create_agent(
        name="Test Agent",
        description="A test agent",
        model_id="gpt-4",
        system_prompt="You are a helpful assistant.",
        capabilities=["conversation", "tool_use"],
        tools=["calculator", "weather"]
    )
    
    print(f"Agent creation result: {agent_result}")
    
    if agent_result.get("success"):
        agent_id = agent_result["data"]["agent_id"]
        
        # 发送消息
        response = await client.send_message(
            agent_id=agent_id,
            message="Hello, can you help me with a calculation? What is 5 + 3?"
        )
        
        print(f"Agent response: {response}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## 总结

本集成指南向您展示了如何在不同服务中集成和使用shared_contracts模块的各种方式。通过遵循以上模式和最佳实践，你可以构建可靠、可扫展、易于维护的AgentForge应用。

要了解更多信息，请参考examples目录中的代码示例和其他文档，或者查看integration_tests目录中的实际用例。

## 完整示例应用

以下示例展示了如何构建一个完整的聊天应用，集成代理服务、模型服务和工具服务。

### API网关集成

```python
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional
import uuid
import os
import httpx
import json

# 导入shared_contracts组件
from shared_contracts.core.models.agent_models import AgentConfig, AgentCapability
from shared_contracts.core.models.model_models import (
    ModelConfig, ModelProvider, ModelType, ModelCapability
)
from shared_contracts.core.models.tool_models import ToolDefinition
from shared_contracts.monitoring import (
    configure_monitor, ServiceComponent, EventType, with_monitoring
)

# 创建应用
app = FastAPI(title="AgentForge API Gateway")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置监控
monitor = configure_monitor(
    service_name="api-gateway",
    api_key=os.environ.get("LOGFIRE_API_KEY"),
    project_id=os.environ.get("LOGFIRE_PROJECT_ID"),
    environment=os.environ.get("ENVIRONMENT", "development")
)

# 服务客户端
class ServiceClient:
    def __init__(self, base_url: str, service_name: str):
        self.base_url = base_url
        self.service_name = service_name
        self.client = httpx.AsyncClient(base_url=base_url)
    
    async def request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None):
        """发送请求到服务。"""
        try:
            if method.upper() == "GET":
                response = await self.client.get(endpoint)
            elif method.upper() == "POST":
                response = await self.client.post(endpoint, json=data)
            elif method.upper() == "PUT":
                response = await self.client.put(endpoint, json=data)
            elif method.upper() == "DELETE":
                response = await self.client.delete(endpoint)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response.json()
        except Exception as e:
            monitor.error(
                message=f"Error calling {self.service_name}: {str(e)}",
                component=ServiceComponent.API_GATEWAY,
                event_type=EventType.EXCEPTION,
                service=self.service_name,
                endpoint=endpoint,
                error=str(e)
            )
            raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")

# 创建服务客户端
agent_client = ServiceClient(
    os.environ.get("AGENT_SERVICE_URL", "http://localhost:8001"),
    "agent-service"
)

model_client = ServiceClient(
    os.environ.get("MODEL_SERVICE_URL", "http://localhost:8002"),
    "model-service"
)

tool_client = ServiceClient(
    os.environ.get("TOOL_SERVICE_URL", "http://localhost:8003"),
    "tool-service"
)

# 依赖项：获取请求ID
async def get_request_id(request: Request):
    if hasattr(request.state, "request_id"):
        return request.state.request_id
    return str(uuid.uuid4())

# API路由
@app.post("/api/agents")
@with_monitoring(component=ServiceComponent.API_GATEWAY)
async def create_agent(agent: Dict[str, Any], request_id: str = Depends(get_request_id)):
    """创建代理。"""
    response = await agent_client.request("POST", "/agents", agent)
    return response

@app.get("/api/agents/{agent_id}")
@with_monitoring(component=ServiceComponent.API_GATEWAY)
async def get_agent(agent_id: str, request_id: str = Depends(get_request_id)):
    """获取代理。"""
    response = await agent_client.request("GET", f"/agents/{agent_id}")
    return response

@app.post("/api/agents/{agent_id}/messages")
@with_monitoring(component=ServiceComponent.API_GATEWAY)
async def send_message(
    agent_id: str, 
    message: Dict[str, Any],
    request_id: str = Depends(get_request_id)
):
    """向代理发送消息。"""
    response = await agent_client.request("POST", f"/agents/{agent_id}/messages", message)
    return response

@app.post("/api/models")
@with_monitoring(component=ServiceComponent.API_GATEWAY)
async def register_model(model: Dict[str, Any], request_id: str = Depends(get_request_id)):
    """注册模型。"""
    response = await model_client.request("POST", "/models", model)
    return response

@app.post("/api/tools")
@with_monitoring(component=ServiceComponent.API_GATEWAY)
async def register_tool(tool: Dict[str, Any], request_id: str = Depends(get_request_id)):
    """注册工具。"""
    response = await tool_client.request("POST", "/tools", tool)
    return response

@app.get("/api/health")
async def health_check():
    """健康检查。"""
    return {
        "status": "healthy",
        "services": {
            "agent_service": "healthy",
            "model_service": "healthy",
            "tool_service": "healthy"
        }
    }

# 启动应用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 客户端 SDK集成

```python
import httpx
import json
import uuid
from typing import Dict, Any, List, Optional, Union

class AgentForgeClient:
    """客户端SDK。"""
    
    def __init__(self, api_url: str, api_key: Optional[str] = None):
        """
        初始化客户端。
        
        Args:
            api_url: API网关的URL
            api_key: 可选的API密钥
        """
        self.api_url = api_url
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        self.client = httpx.AsyncClient(base_url=api_url, headers=headers)
    
    async def create_agent(
        self,
        name: str,
        description: str,
        model_id: str,
        system_prompt: str,
        capabilities: List[str] = ["conversation"],
        tools: List[str] = []
    ) -> Dict[str, Any]:
        """
        创建代理。
        
        Args:
            name: 代理名称
            description: 代理描述
            model_id: 模型ID
            system_prompt: 系统提示词
            capabilities: 代理能力列表
            tools: 工具ID列表
            
        Returns:
            创建结果
        """
        payload = {
            "name": name,
            "description": description,
            "model_id": model_id,
            "system_prompt": system_prompt,
            "capabilities": capabilities,
            "tools": tools
        }
        
        response = await self.client.post("/api/agents", json=payload)
        return response.json()
    
    async def send_message(
        self,
        agent_id: Union[str, uuid.UUID],
        message: str,
        conversation_id: Optional[Union[str, uuid.UUID]] = None
    ) -> Dict[str, Any]:
        """
        向代理发送消息。
        
        Args:
            agent_id: 代理ID
            message: 消息内容
            conversation_id: 可选的对话ID
            
        Returns:
            代理响应
        """
        payload = {
            "message": message
        }
        
        if conversation_id:
            payload["conversation_id"] = str(conversation_id)
        
        response = await self.client.post(
            f"/api/agents/{agent_id}/messages",
            json=payload
        )
        
        return response.json()
```

### 使用示例

```python
# 使用SDK的示例
async def main():
    # 创建客户端
    client = AgentForgeClient("http://localhost:8000")
    
    # 注册模型
    model_result = await client.register_model(
        model_id="gpt-4",
        provider="openai",
        model_type="chat",
        display_name="GPT-4",
        capabilities={
            "supports_streaming": True,
            "supports_function_calling": True,
            "supports_json_mode": True,
            "supports_vision": False,
            "max_tokens": 8192
        },
        provider_model_id="gpt-4-turbo",
        api_key_env_var="OPENAI_API_KEY"
    )
    
    print(f"Model registration result: {model_result}")
    
    # 创建代理
    agent_result = await client.create_agent(
        name="Test Agent",
        description="A test agent",
        model_id="gpt-4",
        system_prompt="You are a helpful assistant.",
        capabilities=["conversation", "tool_use"],
        tools=["calculator", "weather"]
    )
    
    print(f"Agent creation result: {agent_result}")
    
    if agent_result.get("success"):
        agent_id = agent_result["data"]["agent_id"]
        
        # 发送消息
        response = await client.send_message(
            agent_id=agent_id,
            message="Hello, can you help me with a calculation? What is 5 + 3?"
        )
        
        print(f"Agent response: {response}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## 总结

本集成指南向您展示了如何在不同服务中集成和使用shared_contracts模块的各种方式。通过遵循以上模式和最佳实践，你可以构建可靠、可扫展、易于维护的AgentForge应用。

要了解更多信息，请参考examples目录中的代码示例和其他文档，或者查看integration_tests目录中的集成测试用例。