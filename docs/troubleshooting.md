# 故障排除指南

本文档提供了使用shared_contracts模块时可能遇到的常见问题和解决方案，帮助开发者快速排查和解决问题。

## 目录

- [常见错误消息](#常见错误消息)
- [接口实现问题](#接口实现问题)
- [数据验证问题](#数据验证问题)
- [监控配置问题](#监控配置问题)
- [服务通信错误](#服务通信错误)
- [依赖项问题](#依赖项问题)
- [常见问题解答](#常见问题解答)

## 常见错误消息

本节列出了使用shared_contracts模块时可能遇到的常见错误消息，以及它们的原因和解决方法。

### `ValidationError: field required`

**问题描述**：使用Pydantic模型时，提示某个字段是必需的，但在数据中却缺少。

**错误示例**：
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for AgentConfig
name
  Field required [type=missing, input_value={}, input_type=dict]
```

**原因**：创建模型实例时，没有提供所有必需的字段。

**解决方法**：
1. 检查模型定义，确认哪些字段是必需的
2. 确保在创建模型实例时提供了所有必需字段的值
3. 如果某些字段应该是可选的，在模型定义中将其标记为`Optional`并提供默认值

```python
# 正确示例
from shared_contracts.core.models.agent_models import AgentConfig

agent_config = AgentConfig(
    name="Test Agent",  # 必需字段
    description="A test agent",  # 必需字段
    model_id="gpt-4",  # 必需字段
    system_prompt="You are a helpful assistant."  # 必需字段
)
```

### `ImportError: No module named 'shared_contracts'`

**问题描述**：无法导入shared_contracts模块。

**原因**：
1. shared_contracts包未安装
2. Python环境路径配置不正确
3. 包安装路径不在Python的搜索路径中

**解决方法**：
1. 确认shared_contracts已正确安装：
   ```bash
   pip list | grep shared-contracts
   ```
2. 如果未安装，按照README中的指南进行安装：
   ```bash
   pip install -e /path/to/shared_contracts
   ```
3. 检查Python环境和路径：
   ```python
   import sys
   print(sys.path)
   ```
4. 如果安装路径不在列表中，可以手动添加：
   ```python
   import sys
   sys.path.append('/path/to/shared_contracts')
   ```

### `RuntimeError: Monitor not configured`

**问题描述**：使用监控功能时，提示监控未配置。

**错误示例**：
```
RuntimeError: Monitor not configured. Call configure_monitor() before using monitoring functions.
```

**原因**：尝试使用监控功能（如日志记录、性能跟踪等）前，未先配置监控客户端。

**解决方法**：
1. 在使用任何监控功能前，先配置监控客户端：
   ```python
   from shared_contracts.monitoring import configure_monitor, ServiceComponent, EventType

   monitor = configure_monitor(
       service_name="my-service",
       api_key="your-api-key",  # 可选，本地开发可不提供
       project_id="your-project-id",  # 可选，本地开发可不提供
       environment="development"
   )
   ```
2. 对于本地开发环境，可以不提供API密钥，此时会使用控制台日志记录器：
   ```python
   monitor = configure_monitor(
       service_name="local-dev",
       environment="development"
   )
   ```

### `TypeError: unhashable type: list`

**问题描述**：使用代理模型的capabilities字段时，遇到无法哈希的类型错误。

**错误示例**：
```
TypeError: unhashable type: 'list'
```

**原因**：capabilities字段期望是一个集合（set），但提供了一个列表（list）。

**解决方法**：
1. 确保将capabilities字段定义为集合，而不是列表：
   ```python
   # 错误：使用列表
   agent_config = AgentConfig(
       name="Test Agent",
       capabilities=["conversation", "tool_use"]  # 列表
   )

   # 正确：使用集合
   from shared_contracts.core.models.agent_models import AgentCapability
   
   agent_config = AgentConfig(
       name="Test Agent",
       capabilities={AgentCapability.CONVERSATION, AgentCapability.TOOL_USE}  # 集合
   )
   ```
2. 如果接收到的是字符串列表，需要转换为枚举集合：
   ```python
   capability_strings = ["conversation", "tool_use"]
   capabilities = {AgentCapability(c) for c in capability_strings}
   
   agent_config = AgentConfig(
       name="Test Agent",
       capabilities=capabilities
   )
   ```

## 接口实现问题

本节介绍实现服务接口时可能遇到的问题。

### 未实现所有必需的接口方法

**问题描述**：实现服务接口时，如果未实现所有必需的方法，Python不会在定义类时报错，但会在实例化或使用时引发错误。

**错误示例**：
```
TypeError: Can't instantiate abstract class MyAgentService with abstract methods get_agent, list_agents, send_message_to_agent
```

**原因**：服务接口使用Python的Protocol定义，只有在实际使用时才会检查是否实现了所有必需的方法。

**解决方法**：
1. 查看接口定义文件，确认所有必需方法：
   ```python
   from shared_contracts.core.interfaces.agent_interface import AgentServiceInterface
   
   # 检查接口定义
   print([method for method in dir(AgentServiceInterface) if not method.startswith('_')])
   ```
2. 确保在实现类中实现了所有必需的方法：
   ```python
   class MyAgentService(AgentServiceInterface):
       async def create_agent(self, config: AgentConfig) -> BaseResponse[AgentConfig]:
           # 实现
           ...
       
       async def get_agent(self, agent_id: uuid.UUID) -> BaseResponse[AgentConfig]:
           # 实现
           ...
       
       async def list_agents(self) -> BaseResponse[List[AgentConfig]]:
           # 实现
           ...
       
       async def send_message_to_agent(self, agent_id: uuid.UUID, message: str, conversation_id: Optional[uuid.UUID] = None) -> BaseResponse[Dict[str, Any]]:
           # 实现
           ...
   ```
3. 对于暂时不需要的方法，可以提供一个简单的实现，返回"未实现"错误：
   ```python
   async def some_method(self, *args, **kwargs) -> BaseResponse:
       return BaseResponse(
           request_id=uuid.uuid4(),
           success=False,
           error="Method not implemented"
       )
   ```

### 返回类型不匹配

**问题描述**：实现接口方法时，返回的对象类型与接口定义不匹配。

**错误示例**：
```
TypeError: Expected BaseResponse[AgentConfig], got dict
```

**原因**：接口方法期望返回一个符合类型注解的对象，但实际返回了其他类型。

**解决方法**：
1. 确认接口定义中的返回类型：
   ```python
   async def create_agent(self, config: AgentConfig) -> BaseResponse[AgentConfig]:
       ...
   ```
2. 确保返回的对象符合类型注解：
   ```python
   # 错误：直接返回字典
   return {"success": True, "data": config}
   
   # 正确：返回BaseResponse对象
   return BaseResponse(
       request_id=uuid.uuid4(),
       success=True,
       data=config
   )
   ```
3. 使用类型检查器如mypy进行静态类型检查：
   ```bash
   mypy your_implementation.py
   ```

## 数据验证问题

本节介绍使用shared_contracts模型进行数据验证时可能遇到的问题。

### 模型验证失败但没有明确错误信息

**问题描述**：数据验证失败，但没有提供具体的错误信息。

**原因**：使用了默认的验证方法，没有捕获和处理验证错误。

**解决方法**：
1. 使用utils模块提供的验证工具，获取详细的错误信息：
   ```python
   from shared_contracts.utils.validation import validate_model
   from shared_contracts.core.models.agent_models import AgentConfig
   
   # 创建可能无效的模型
   agent = AgentConfig.construct()  # 跳过验证
   agent.name = ""  # 无效值
   
   # 验证并获取错误信息
   is_valid, errors = validate_model(agent)
   if not is_valid:
       print(f"验证错误: {errors}")
   ```
2. 对于字典数据，使用validate_dict_against_model工具：
   ```python
   from shared_contracts.utils.validation import validate_dict_against_model
   
   data = {"name": "", "model_id": "gpt-4"}
   is_valid, errors = validate_dict_against_model(data, AgentConfig)
   if not is_valid:
       print(f"验证错误: {errors}")
   ```

### 枚举值验证失败

**问题描述**：使用枚举类型时，传入的字符串值无法自动转换为枚举实例。

**错误示例**：
```
ValidationError: 1 validation error for AgentConfig
capabilities -> 0
  Input should be 'AgentCapability' [type=enum, input_value='conversation', input_type=str]
```

**原因**：Pydantic 2.x在处理枚举时更严格，需要显式转换。

**解决方法**：
1. 显式转换字符串为枚举值：
   ```python
   from shared_contracts.core.models.agent_models import AgentCapability
   
   # 错误：直接使用字符串
   capabilities = ["conversation", "tool_use"]
   
   # 正确：转换为枚举
   capabilities = {AgentCapability(c) for c in ["conversation", "tool_use"]}
   ```
2. 使用utils模块的序列化工具进行转换：
   ```python
   from shared_contracts.utils.serialization import deserialize_enum
   from shared_contracts.core.models.agent_models import AgentCapability
   
   str_capabilities = ["conversation", "tool_use"]
   enum_capabilities = deserialize_enum(str_capabilities, AgentCapability)
   ```

## 监控配置问题

本节介绍配置和使用监控功能时可能遇到的问题。

### LogFire连接失败

**问题描述**：配置LogFire监控时连接失败，无法发送日志和指标。

**错误示例**：
```
WARNING - LogFire connection failed: Invalid API key or project ID
```

**原因**：
1. API密钥或项目ID无效
2. 网络连接问题
3. LogFire服务不可用

**解决方法**：
1. 检查API密钥和项目ID是否正确：
   ```python
   monitor = configure_monitor(
       service_name="my-service",
       api_key="your-logfire-api-key",  # 检查密钥是否正确
       project_id="your-logfire-project-id",  # 检查项目ID是否正确
       environment="production"
   )
   ```
2. 开启调试模式，获取详细错误信息：
   ```python
   monitor = configure_monitor(
       service_name="my-service",
       api_key="your-api-key",
       project_id="your-project-id",
       environment="development",
       debug=True  # 开启调试模式
   )
   ```
3. 对于开发环境，可以使用本地日志记录，避免依赖LogFire：
   ```python
   monitor = configure_monitor(
       service_name="local-dev",
       environment="development",
       use_local_logging=True  # 使用本地日志记录
   )
   ```

### 监控装饰器和上下文管理器不可用

**问题描述**：尝试使用监控装饰器或上下文管理器时，功能不可用或报错。

**错误示例**：
```
AttributeError: 'NoneType' object has no attribute 'start_span'
```

**原因**：未正确配置监控客户端，或者没有使用返回的监控实例。

**解决方法**：
1. 确保在使用监控工具前配置监控客户端，并保存返回的实例：
   ```python
   from shared_contracts.monitoring import configure_monitor, with_monitoring
   
   # 配置监控并保存实例
   monitor = configure_monitor(
       service_name="my-service",
       environment="development"
   )
   
   # 使用装饰器
   @with_monitoring(component=ServiceComponent.AGENT_CORE)
   def my_function():
       # ...
   ```
2. 对于上下文管理器，确保使用正确的导入和用法：
   ```python
   from shared_contracts.monitoring import track_performance, ServiceComponent
   
   # 使用上下文管理器
   with track_performance("operation_name", ServiceComponent.AGENT_CORE) as span:
       # 执行操作
       result = perform_operation()
       
       # 添加额外数据
       span.add_data({"result_size": len(result)})
   ```

## 服务通信错误

本节介绍服务间通信时可能遇到的问题。

### HTTP请求失败

**问题描述**：通过HTTP调用其他服务时请求失败。

**错误示例**：
```
httpx.HTTPError: HTTPError: Request failed with status code 404
```

**原因**：
1. 目标服务未运行或不可达
2. URL路径错误
3. 认证问题
4. 请求格式错误

**解决方法**：
1. 检查目标服务是否正在运行，可以使用简单的健康检查：
   ```python
   import httpx
   
   async def check_service_health(base_url):
       try:
           async with httpx.AsyncClient() as client:
               response = await client.get(f"{base_url}/health")
               return response.status_code == 200
       except Exception:
           return False
   ```
2. 验证URL格式是否正确，特别是路径部分：
   ```python
   # 错误：缺少前导斜杠
   url = "http://agent-service:8000api/agents"
   
   # 正确
   url = "http://agent-service:8000/api/agents"
   ```
3. 检查认证头是否正确：
   ```python
   headers = {"Authorization": f"Bearer {api_key}"}
   ```
4. 打印请求详情进行调试：
   ```python
   import json
   
   # 调试请求
   print(f"请求URL: {url}")
   print(f"请求方法: {method}")
   print(f"请求头: {headers}")
   print(f"请求体: {json.dumps(data, indent=2)}")
   ```

### gRPC连接失败

**问题描述**：使用gRPC进行服务通信时连接失败。

**错误示例**：
```
grpc._channel._InactiveRpcError: <_InactiveRpcError of RPC that terminated with:
    status = StatusCode.UNAVAILABLE
    details = "failed to connect to all addresses"
```

**原因**：
1. 目标服务未运行
2. 网络连接问题
3. gRPC配置错误

**解决方法**：
1. 检查目标服务是否正在运行：
   ```python
   # 健康检查
   try:
       response = stub.HealthCheck(empty_pb2.Empty())
       print(f"服务状态: {response.status}")
   except Exception as e:
       print(f"服务不可用: {e}")
   ```
2. 使用安全的通道选项：
   ```python
   # 使用带选项的通道
   channel = grpc.aio.insecure_channel(
       server_address,
       options=[
           ('grpc.enable_retries', 1),
           ('grpc.max_receive_message_length', 100 * 1024 * 1024)  # 100 MB
       ]
   )
   ```
3. 添加超时和重试逻辑：
   ```python
   import asyncio
   
   async def call_with_retry(method, request, max_retries=3, timeout=5.0):
       for attempt in range(max_retries):
           try:
               return await asyncio.wait_for(method(request), timeout=timeout)
           except Exception as e:
               if attempt == max_retries - 1:
                   raise
               await asyncio.sleep(0.5 * (2 ** attempt))  # 指数退避
   ```

### 序列化/反序列化问题

**问题描述**：服务间传递数据时出现序列化或反序列化问题。

**错误示例**：
```
ValueError: Object of type UUID is not JSON serializable
```

**原因**：
1. 使用了不支持直接JSON序列化的类型（如UUID、datetime）
2. 序列化/反序列化方法不匹配

**解决方法**：
1. 使用shared_contracts提供的序列化工具：
   ```python
   from shared_contracts.utils.serialization import serialize_model, deserialize_model
   
   # 序列化模型
   serialized = serialize_model(model_instance, as_json=True)
   
   # 反序列化
   model = deserialize_model(ModelClass, serialized)
   ```
2. 使用自定义JSON编码器：
   ```python
   from shared_contracts.utils.serialization import CustomJSONEncoder
   import json
   
   # 使用自定义编码器序列化
   json_data = json.dumps(data, cls=CustomJSONEncoder)
   ```
3. 显式转换不兼容的类型：
   ```python
   # UUID转字符串
   data["id"] = str(uuid_value)
   
   # datetime转ISO格式字符串
   data["timestamp"] = datetime_value.isoformat()
   ```

## 依赖项问题

本节介绍与依赖项相关的问题。

### 依赖版本冲突

**问题描述**：shared_contracts与项目中的其他依赖版本冲突。

**错误示例**：
```
ImportError: cannot import name 'Field' from 'pydantic'
```

**原因**：
1. Pydantic 1.x和2.x版本API不兼容
2. 其他依赖项可能锁定了旧版本的依赖

**解决方法**：
1. 检查当前安装的依赖版本：
   ```bash
   pip list | grep pydantic
   ```
2. 确保安装了所需版本：
   ```bash
   pip install pydantic>=2.0.0
   ```
3. 使用虚拟环境隔离项目依赖：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```
4. 对于复杂项目，使用依赖管理工具如Poetry：
   ```bash
   poetry add pydantic@^2.0.0
   ```

### 缺少可选依赖

**问题描述**：使用某些功能时，报错缺少依赖。

**错误示例**：
```
ImportError: No module named 'logfire'
```

**原因**：尝试使用需要可选依赖的功能，但未安装相应依赖。

**解决方法**：
1. 安装所需的可选依赖：
   ```bash
   # 监控依赖
   pip install logfire opentelemetry-api opentelemetry-sdk
   
   # gRPC依赖
   pip install grpcio grpcio-tools
   ```
2. 或者使用extras_require安装所有可选依赖：
   ```bash
   pip install -e ".[monitoring,grpc]"
   ```
3. 如果不需要某些功能，可以使用替代实现：
   ```python
   # 不使用LogFire，改用本地日志
   monitor = configure_monitor(
       service_name="my-service",
       use_local_logging=True
   )
   ```

## 常见问题解答

### Q: 如何在本地开发环境中使用shared_contracts而不依赖外部服务？

**A**: 对于本地开发，您可以：

1. 使用本地日志记录而不是LogFire：
   ```python
   from shared_contracts.monitoring import configure_monitor
   
   monitor = configure_monitor(
       service_name="local-dev",
       environment="development",
       use_local_logging=True
   )
   ```

2. 使用内存存储实现服务接口，而不是实际的外部服务：
   ```python
   class InMemoryAgentService(AgentServiceInterface):
       def __init__(self):
           self.agents = {}  # 内存存储
       
       async def create_agent(self, config: AgentConfig) -> BaseResponse[AgentConfig]:
           agent_id = config.agent_id or uuid.uuid4()
           config.agent_id = agent_id
           self.agents[agent_id] = config
           return BaseResponse(request_id=uuid.uuid4(), success=True, data=config)
       
       # 实现其他方法...
   ```

3. 使用模拟HTTP服务器进行测试：
   ```python
   from fastapi import FastAPI
   import uvicorn
   
   app = FastAPI()
   
   @app.post("/api/agents")
   async def create_agent(data: dict):
       return {"success": True, "data": data}
   
   # 在另一个线程中运行
   import threading
   threading.Thread(target=lambda: uvicorn.run(app, host="127.0.0.1", port=8000)).start()
   ```

### Q: 服务接口有哪些实现方式？

**A**: shared_contracts定义的服务接口可以通过多种方式实现：

1. **直接实现**：创建一个实现接口的类
   ```python
   class MyAgentService(AgentServiceInterface):
       # 实现所有方法
   ```

2. **HTTP API**：使用FastAPI或Flask等框架实现HTTP API
   ```python
   app = FastAPI()
   
   @app.post("/agents")
   async def create_agent(data: dict):
       agent_config = AgentConfig.model_validate(data)
       # 处理逻辑
       return {"success": True, "data": agent_config.model_dump()}
   ```

3. **gRPC服务**：使用gRPC实现服务
   ```python
   class AgentServicer(agent_pb2_grpc.AgentServiceServicer):
       async def CreateAgent(self, request, context):
           # 实现逻辑
           return agent_pb2.AgentResponse(success=True, data=...)
   ```

4. **消息队列**：使用消息队列实现异步服务
   ```python
   async def handle_create_agent(message):
       data = json.loads(message)
       # 处理逻辑
       await publish_response({"success": True, "data": ...})
   ```

### Q: 如何优化监控性能以减少对主要业务逻辑的影响？

**A**: 优化监控性能的方法包括：

1. **批处理**：配置批处理参数，减少网络请求数量
   ```python
   monitor = configure_monitor(
       service_name="my-service",
       batch_size=50,  # 每批次最大事件数
       flush_interval_seconds=5.0  # 自动刷新间隔
   )
   ```

2. **采样**：对高频事件进行采样，只记录一部分
   ```python
   monitor = configure_monitor(
       service_name="my-service",
       sample_rate=0.1  # 10%采样率
   )
   ```

3. **异步处理**：确保使用异步方法，不阻塞主线程
   ```python
   # 异步记录日志
   await monitor.ainfo(
       message="操作完成",
       component=ServiceComponent.AGENT_CORE
   )
   ```

4. **日志级别**：调整日志级别，只记录重要事件
   ```python
   monitor = configure_monitor(
       service_name="my-service",
       min_log_level=LogLevel.INFO  # 忽略DEBUG级别日志
   )
   ```

### Q: 我应该在什么时候使用shared_contracts的哪些组件？

**A**: 以下是各组件的使用场景指南：

1. **核心数据模型**：
   - 定义服务间传递的数据结构
   - 验证输入/输出数据
   - 构建API请求/响应

2. **服务接口**：
   - 定义服务API规范
   - 实现微服务
   - 创建客户端适配器

3. **监控组件**：
   - 记录服务日志
   - 跟踪系统性能
   - 分析服务行为
   - 监测系统健康状态

4. **工具函数**：
   - 数据验证和转换
   - 序列化和反序列化
   - 性能测量和优化
   - Schema处理和验证

### Q: shared_contracts是否支持非异步接口？

**A**: shared_contracts主要定义了异步接口，适用于现代异步Web框架。不过，您可以：

1. 创建同步包装器：
   ```python
   def create_agent_sync(service, config):
       """同步包装器，在内部使用事件循环。"""
       import asyncio
       
       loop = asyncio.new_event_loop()
       try:
           return loop.run_until_complete(service.create_agent(config))
       finally:
           loop.close()
   ```

2. 对于监控功能，可以使用同步API：
   ```python
   # 同步日志记录
   monitor.info(
       message="操作完成",
       component=ServiceComponent.AGENT_CORE
   )
   
   # 而不是异步版本
   await monitor.ainfo(...)
   ```

3. 在使用同步Web框架时，可以使用专用线程运行异步操作：
   ```python
   def flask_route_handler():
       import asyncio
       
       loop = asyncio.new_event_loop()
       result = loop.run_until_complete(async_operation())
       loop.close()
       
       return result
   ```

### Q: 如何在生产环境中调试shared_contracts问题？

**A**: 生产环境调试技巧：

1. **增强监控**：临时提高日志级别，捕获更多信息
   ```python
   monitor = configure_monitor(
       service_name="my-service",
       min_log_level=LogLevel.DEBUG,  # 临时提高日志级别
       capture_errors=True  # 捕获和记录所有异常
   )
   ```

2. **添加追踪ID**：使用请求ID跨服务追踪问题
   ```python
   # 客户端传递请求ID
   headers = {"X-Request-ID": str(request_id)}
   
   # 服务端使用请求ID
   request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
   ```

3. **审查日志**：使用LogFire仪表板查看详细日志
   ```python
   # 在日志中添加关键信息，便于搜索
   monitor.info(
       message="处理请求",
       component=ServiceComponent.API_GATEWAY,
       request_id=request_id,
       user_id=user_id,
       operation="create_agent"
   )
   ```

4. **健康检查**：实现和监控详细的健康检查端点
   ```python
   @app.get("/health/detailed")
   async def detailed_health():
       return {
           "service": "agent-service",
           "status": "healthy",
           "dependencies": {
               "model-service": await check_service("model-service"),
               "tool-service": await check_service("tool-service"),
               "database": await check_database()
           },
           "metrics": {
               "uptime": get_uptime(),
               "request_count": request_counter.value,
               "error_rate": calculate_error_rate()
           }
       }
   ```
