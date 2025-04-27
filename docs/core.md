# 核心组件详细文档

_版本: 1.0.0 | 最后更新: 2025-04-26_

本文档详细介绍shared_contracts模块中的核心数据模型和接口定义，包括它们的结构、属性和使用方法。

## 目录

- [数据模型](#数据模型)
  - [基础模型](#基础模型)
  - [代理模型](#代理模型)
  - [模型服务模型](#模型服务模型)
  - [工具模型](#工具模型)
- [接口定义](#接口定义)
  - [代理服务接口](#代理服务接口)
  - [模型服务接口](#模型服务接口)
  - [工具服务接口](#工具服务接口)
- [错误处理](#错误处理)
- [最佳实践](#最佳实践)
- [故障排除](#故障排除)
  - [数据模型问题](#数据模型问题)
  - [接口实现问题](#接口实现问题)

## 数据模型

shared_contracts使用Pydantic模型定义跨服务通信的数据结构，确保数据验证和一致性。这些模型可以结合[工具函数文档](./utils.md#序列化工具)中的序列化工具和验证工具一起使用，以实现完整的数据流处理。

### 基础模型

位置: `shared_contracts.core.models.base_models`

#### BaseModel

所有数据模型的基类，提供基本的序列化和验证功能。

```python
from shared_contracts.core.models.base_models import BaseModel

class MyModel(BaseModel):
    name: str
    value: int
```

#### BaseRequest

请求的基本结构，包含请求ID和时间戳。

```python
from shared_contracts.core.models.base_models import BaseRequest

# 创建请求
request = BaseRequest()  # 自动生成请求ID和时间戳
print(f"Request ID: {request.request_id}")
```

#### BaseResponse

响应的基本结构，包含请求ID、成功/失败状态和数据/错误信息。

```python
from shared_contracts.core.models.base_models import BaseResponse
import uuid

# 成功响应
success_response = BaseResponse[str](
    request_id=uuid.uuid4(),
    success=True,
    data="Operation successful"
)

# 错误响应
error_response = BaseResponse[str](
    request_id=uuid.uuid4(),
    success=False,
    error="Operation failed: invalid parameters"
)

# 检查响应
if success_response.success:
    print(f"Success: {success_response.data}")
else:
    print(f"Error: {success_response.error}")
```

### 代理模型

位置: `shared_contracts.core.models.agent_models`

#### AgentCapability

代理能力的枚举类型。

```python
from shared_contracts.core.models.agent_models import AgentCapability

# 可用能力
print(f"Conversation: {AgentCapability.CONVERSATION}")
print(f"Tool Use: {AgentCapability.TOOL_USE}")
print(f"Planning: {AgentCapability.PLANNING}")
print(f"Memory: {AgentCapability.MEMORY}")
```

#### AgentStatus

代理状态的枚举类型。

```python
from shared_contracts.core.models.agent_models import AgentStatus

# 可用状态
print(f"Initializing: {AgentStatus.INITIALIZING}")
print(f"Ready: {AgentStatus.READY}")
print(f"Busy: {AgentStatus.BUSY}")
print(f"Error: {AgentStatus.ERROR}")
print(f"Terminated: {AgentStatus.TERMINATED}")
```

#### AgentConfig

代理配置模型，定义代理的属性和行为。

```python
from shared_contracts.core.models.agent_models import AgentConfig, AgentCapability

# 创建代理配置
config = AgentConfig(
    name="Customer Support Agent",
    description="Agent for handling customer inquiries",
    model_id="gpt-4",
    system_prompt="You are a helpful customer support assistant.",
    capabilities={AgentCapability.CONVERSATION, AgentCapability.TOOL_USE},
    max_tokens_per_response=1024,
    temperature=0.7,
    tools=["knowledge_base", "ticket_system"],
    metadata={"team": "support", "priority": "high"}
)

# 使用配置
print(f"Agent ID: {config.agent_id}")
print(f"Model: {config.model_id}")
print(f"Tools: {config.tools}")
```

#### AgentState

代理状态模型，表示代理的当前运行状态。

```python
from shared_contracts.core.models.agent_models import AgentState, AgentStatus
from datetime import datetime
import uuid

# 创建代理状态
state = AgentState(
    agent_id=uuid.uuid4(),
    status=AgentStatus.READY,
    created_at=datetime.now(),
    last_active=datetime.now(),
    conversation_count=5,
    current_conversation_id=uuid.uuid4()
)

# 检查状态
if state.status == AgentStatus.READY:
    print("Agent is ready to handle requests")
elif state.status == AgentStatus.BUSY:
    print("Agent is currently processing a request")
```

### 模型服务模型

位置: `shared_contracts.core.models.model_models`

#### ModelProvider

模型提供商的枚举类型。

```python
from shared_contracts.core.models.model_models import ModelProvider

# 可用提供商
print(f"OpenAI: {ModelProvider.OPENAI}")
print(f"Anthropic: {ModelProvider.ANTHROPIC}")
print(f"Cohere: {ModelProvider.COHERE}")
print(f"Custom: {ModelProvider.CUSTOM}")
```

#### ModelType

模型类型的枚举类型。

```python
from shared_contracts.core.models.model_models import ModelType

# 可用类型
print(f"Chat: {ModelType.CHAT}")
print(f"Completion: {ModelType.COMPLETION}")
print(f"Embedding: {ModelType.EMBEDDING}")
print(f"Image: {ModelType.IMAGE}")
print(f"Multimodal: {ModelType.MULTIMODAL}")
```

#### ModelCapability

模型能力的模型，描述模型的功能和限制。

```python
from shared_contracts.core.models.model_models import ModelCapability

# 创建模型能力
capabilities = ModelCapability(
    supports_streaming=True,
    supports_function_calling=True,
    supports_json_mode=True,
    supports_vision=False,
    max_tokens=8192,
    input_cost_per_token=0.00001,
    output_cost_per_token=0.00003
)

# 检查能力
if capabilities.supports_function_calling:
    print("Model supports function calling")
```

#### ModelConfig

模型配置模型，定义AI模型的属性和配置。

```python
from shared_contracts.core.models.model_models import (
    ModelConfig, ModelProvider, ModelType, ModelCapability
)

# 创建模型能力
capabilities = ModelCapability(
    supports_streaming=True,
    supports_function_calling=True,
    supports_json_mode=True,
    supports_vision=False,
    max_tokens=8192
)

# 创建模型配置
config = ModelConfig(
    model_id="gpt-4-turbo",
    provider=ModelProvider.OPENAI,
    model_type=ModelType.CHAT,
    display_name="GPT-4 Turbo",
    capabilities=capabilities,
    provider_model_id="gpt-4-turbo",
    api_key_env_var="OPENAI_API_KEY",
    timeout=60,
    retry_count=3
)

# 使用配置
print(f"Model ID: {config.model_id}")
print(f"Provider: {config.provider}")
print(f"Max Tokens: {config.capabilities.max_tokens}")
```

#### ModelResponse

模型响应模型，包含模型生成的内容和元数据。

```python
from shared_contracts.core.models.model_models import ModelResponse
import uuid

# 创建模型响应
response = ModelResponse(
    model_id="gpt-4-turbo",
    request_id=uuid.uuid4(),
    content="This is a response from the model.",
    usage={"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25},
    finish_reason="stop"
)

# 使用响应
print(f"Content: {response.content}")
print(f"Token Usage: {response.usage}")
```

### 工具模型

位置: `shared_contracts.core.models.tool_models`

#### ToolParameterType

工具参数类型的枚举类型。

```python
from shared_contracts.core.models.tool_models import ToolParameterType

# 可用类型
print(f"String: {ToolParameterType.STRING}")
print(f"Integer: {ToolParameterType.INTEGER}")
print(f"Number: {ToolParameterType.NUMBER}")
print(f"Boolean: {ToolParameterType.BOOLEAN}")
print(f"Object: {ToolParameterType.OBJECT}")
```

#### ToolParameter

工具参数的定义模型。

```python
from shared_contracts.core.models.tool_models import ToolParameter, ToolParameterType

# 创建工具参数
param = ToolParameter(
    name="query",
    description="Search query string",
    type=ToolParameterType.STRING,
    required=True,
    min_length=3,
    max_length=100
)

# 数值参数
num_param = ToolParameter(
    name="count",
    description="Number of results to return",
    type=ToolParameterType.INTEGER,
    required=False,
    default=10,
    min_value=1,
    max_value=100
)
```

#### ToolParameters

工具参数集合模型，可转换为JSON Schema格式。

```python
from shared_contracts.core.models.tool_models import (
    ToolParameters, ToolParameter, ToolParameterType
)

# 创建参数集合
params = ToolParameters()

# 添加参数
params.parameters["query"] = ToolParameter(
    name="query",
    description="Search query string",
    type=ToolParameterType.STRING,
    required=True
)

params.parameters["count"] = ToolParameter(
    name="count",
    description="Number of results to return",
    type=ToolParameterType.INTEGER,
    required=False,
    default=10
)

# 转换为JSON Schema
schema = params.to_json_schema()
print(schema)
```

#### ToolDefinition

工具定义模型，描述工具的功能和参数。

```python
from shared_contracts.core.models.tool_models import (
    ToolDefinition, ToolParameter, ToolParameterType
)

# 创建工具定义
tool = ToolDefinition(
    tool_id="search_tool",
    name="Search Tool",
    description="Tool for searching knowledge base",
    version="1.0.0",
    is_streaming=False,
    requires_auth=True
)

# 添加参数
query_param = ToolParameter(
    name="query",
    description="Search query string",
    type=ToolParameterType.STRING
)

count_param = ToolParameter(
    name="count",
    description="Number of results",
    type=ToolParameterType.INTEGER,
    default=10
)

tool.parameters.parameters["query"] = query_param
tool.parameters.parameters["count"] = count_param

# 使用工具定义
print(f"Tool ID: {tool.tool_id}")
print(f"Parameters: {list(tool.parameters.parameters.keys())}")
```

#### ToolResultStatus

工具结果状态的枚举类型。

```python
from shared_contracts.core.models.tool_models import ToolResultStatus

# 可用状态
print(f"Success: {ToolResultStatus.SUCCESS}")
print(f"Error: {ToolResultStatus.ERROR}")
print(f"Partial: {ToolResultStatus.PARTIAL}")
```

#### ToolResult

工具执行结果模型。

```python
from shared_contracts.core.models.tool_models import ToolResult, ToolResultStatus
import uuid

# 成功结果
success_result = ToolResult(
    tool_id="search_tool",
    request_id=uuid.uuid4(),
    status=ToolResultStatus.SUCCESS,
    data={"results": ["item1", "item2"], "total": 2}
)

# 错误结果
error_result = ToolResult(
    tool_id="search_tool",
    request_id=uuid.uuid4(),
    status=ToolResultStatus.ERROR,
    error="Search failed: invalid query"
)

# 检查结果
if success_result.status == ToolResultStatus.SUCCESS:
    print(f"Found {success_result.data['total']} results")
elif error_result.status == ToolResultStatus.ERROR:
    print(f"Error: {error_result.error}")
```

## 接口定义

shared_contracts使用Python Protocol定义服务间通信的标准接口。在实现这些接口时，建议结合[监控组件文档](./monitoring.md)中的监控和日志功能，以提高服务的可观测性和调试能力。

### 代理服务接口

位置: `shared_contracts.core.interfaces.agent_interface`

关于如何在实际服务中实现这些接口的详细示例和最佳实践，请参考[集成指南](./integration.md)文档。

```python
from