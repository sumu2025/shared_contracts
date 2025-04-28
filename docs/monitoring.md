# 监控模块文档

_版本: 1.0.1 | 最后更新: 2025-04-29_

监控模块提供了 AgentForge 平台的日志记录、指标收集和分布式追踪功能。该模块与 LogFire 服务集成，为微服务架构提供全面的可观测性。

相关文档:
- [核心组件文档](./core.md) - 了解与监控模块集成的数据模型
- [工具函数文档](./utils.md) - 提供辅助监控的工具函数
- [集成指南](./integration.md) - 实际服务中的监控集成方案

## 目录

- [监控接口](#监控接口)
- [数据模型](#数据模型)
- [LogFire集成](#logfire集成)
- [工具函数](#工具函数)
- [使用示例](#使用示例)
  - [基本日志记录](#基本日志记录)
  - [性能监控](#性能监控)
  - [分布式追踪](#分布式追踪)
  - [API调用记录](#api调用记录)

## 监控接口

`MonitorInterface` 定义了监控服务的标准接口，包括日志记录、指标收集和分布式追踪等功能。

```python
from agentforge_contracts.monitoring import (
    MonitorInterface, 
    LogLevel, 
    ServiceComponent, 
    EventType
)

# 通过接口类型检查
def use_monitor(monitor: MonitorInterface):
    # 记录日志
    monitor.info(
        message="操作完成",
        component=ServiceComponent.AGENT_CORE,
        event_type=EventType.SYSTEM,
        user_id="user123"
    )
    
    # 记录性能指标
    monitor.record_metric(
        metric_name="request_duration",
        value=45.2,  # 毫秒
        tags={"endpoint": "/api/agents", "method": "GET"}
    )
```

主要方法包括：

- **日志方法**：`log`, `debug`, `info`, `warning`, `error`, `critical`
- **追踪方法**：`start_span`, `end_span`
- **指标方法**：`register_metric`, `record_metric`, `get_metrics`
- **健康状态**：`record_health_status`, `get_health_status`
- **告警方法**：`create_alert`, `update_alert`, `delete_alert`, `get_alerts`...

## 数据模型

监控模块定义了多种数据模型用于描述监控相关的结构：

```python
from agentforge_contracts.monitoring import (
    LogLevel, 
    ServiceComponent, 
    EventType, 
    MonitorEvent,
    MetricValue,
    Metric,
    ResourceUsage,
    ServiceHealthStatus,
    TraceContext,
    AlertConfig,
    AlertInstance,
    LogConfig
)

# 创建服务健康状态报告
health_status = ServiceHealthStatus(
    service_id="agent-service-1",
    service_name="Agent Service",
    status="healthy",
    message="All systems operational",
    version="1.0.0",
    uptime_seconds=3600,
    resource_usage=ResourceUsage(
        cpu_percent=25.5,
        memory_percent=40.2,
        memory_rss=104857600,  # 100 MB
        disk_io_read=5242880,  # 5 MB
        disk_io_write=2097152,  # 2 MB
        network_recv=102400,  # 100 KB
        network_sent=51200,    # 50 KB
        open_file_descriptors=42
    ),
    checks={"database": True, "api": True, "redis": True}
)
```

主要模型包括：

- **MonitorEvent**：基础监控事件结构
- **MetricValue**/**Metric**：指标值和指标定义
- **ResourceUsage**：资源使用情况
- **ServiceHealthStatus**：服务健康状态
- **TraceContext**：分布式追踪上下文
- **AlertConfig**/**AlertInstance**：告警配置和实例
- **LogConfig**：日志配置

## LogFire集成

AgentForge 使用 LogFire 作为默认的监控后端。以下是配置和使用 LogFire 客户端的方式：

> **注意：** 自 Python 3.12 起，`datetime.utcnow()` 方法已弃用。本模块使用 `datetime.now(UTC)` 代替，这要求使用 `from datetime import UTC` 导入 UTC 时区常量。

```python
from agentforge_contracts.monitoring import (
    configure_monitor,
    LogFireConfig,
    LogLevel,
    ServiceComponent,
    EventType
)

# 配置LogFire客户端
monitor = configure_monitor(
    service_name="my-service",
    api_key="your-logfire-api-key",
    project_id="your-logfire-project-id",
    environment="production",
    min_log_level=LogLevel.INFO
)

# 记录日志
monitor.info(
    message="服务启动成功",
    component=ServiceComponent.SYSTEM,
    event_type=EventType.LIFECYCLE,
    server_id="sv-123",
    deployment="blue"
)
```

您也可以直接使用 LogFireConfig 进行更详细的配置：

```python
from agentforge_contracts.monitoring.implementations.logfire_config import LogFireConfig
from agentforge_contracts.monitoring.implementations.logfire_client import LogFireClient

# 创建详细配置
config = LogFireConfig(
    api_key="your-api-key",
    project_id="your-project-id",
    service_name="my-service",
    environment="development",
    min_log_level=LogLevel.DEBUG,
    batch_size=50,
    flush_interval_seconds=2.0,
    sample_rate=0.1,  # 采样率10%
    enable_metadata=True,
    additional_metadata={"deployment": "canary", "region": "us-west"}
)

# 创建客户端
client = LogFireClient(config)
```

## 工具函数

监控模块提供了多种实用工具函数，简化了监控的集成：

### 装饰器

```python
from agentforge_contracts.monitoring import (
    with_monitoring, 
    trace_method,
    ServiceComponent,
    EventType
)

# 使用装饰器添加监控
@with_monitoring(component=ServiceComponent.AGENT_CORE)
def process_request(request_id, data):
    # 处理请求...
    return {"status": "success"}

# 特别用于类方法的追踪装饰器
class UserService:
    @trace_method(component=ServiceComponent.API_GATEWAY)
    async def get_user(self, user_id):
        # 获取用户数据...
        return user_data
```

### 上下文管理器

```python
from agentforge_contracts.monitoring import (
    track_performance,
    create_trace_context,
    ServiceComponent,
    EventType
)

# 使用上下文管理器记录性能
def complex_operation():
    with track_performance("data_processing", ServiceComponent.AGENT_CORE) as span:
        # 执行一些工作...
        result = process_data()
        
        # 添加详细信息到span
        span.add_data({"records_processed": 157, "errors": 2})
    
    return result

# 创建分布式追踪上下文
async def process_with_tracing():
    with create_trace_context(
        "process_task", 
        component=ServiceComponent.AGENT_CORE,
        data={"task_id": "123"}
    ) as span:
        # 执行操作并添加追踪数据
        result = await process_step_1()
        span.attributes["step1_result"] = "success"
        
        # 执行下一步
        final = await process_step_2(result)
        span.attributes["processing_time"] = 45.2
    
    return final
```

### 工具方法

```python
from agentforge_contracts.monitoring import (
    get_monitor,
    log_api_call,
    ServiceComponent
)

# 获取全局监控实例
monitor = get_monitor()

# 记录API调用
log_api_call(
    api_name="get_weather",
    status_code=200,
    duration_ms=125.3,
    component=ServiceComponent.AGENT_CORE,
    request_data={"location": "Beijing"},
    response_data={"temperature": 22, "condition": "sunny"}
)
```

## 使用示例

### 基本日志记录

```python
from agentforge_contracts.monitoring import (
    configure_monitor,
    LogLevel,
    ServiceComponent,
    EventType
)

# 配置监控
monitor = configure_monitor(
    service_name="example-service",
    api_key="your-api-key",
    project_id="your-project-id",
    environment="development"
)

# 记录不同级别的日志
monitor.debug(
    "初始化配置", 
    component=ServiceComponent.SYSTEM, 
    event_type=EventType.LIFECYCLE,
    config_file="config.yaml"
)

monitor.info(
    "用户登录成功", 
    component=ServiceComponent.API_GATEWAY, 
    event_type=EventType.AUTH,
    user_id="user123",
    ip_address="192.168.1.1"
)

monitor.warning(
    "请求速率接近限制", 
    component=ServiceComponent.API_GATEWAY, 
    event_type=EventType.SYSTEM,
    current_rate=95,
    limit=100
)

monitor.error(
    "数据库连接失败", 
    component=ServiceComponent.DATABASE, 
    event_type=EventType.EXCEPTION,
    db_host="db.example.com",
    error_code="CONN_REFUSED"
)

monitor.critical(
    "服务不可用", 
    component=ServiceComponent.SYSTEM, 
    event_type=EventType.EXCEPTION,
    affected_services=["auth", "storage"],
    error_details="主数据库崩溃"
)
```

### 性能监控

```python
from agentforge_contracts.monitoring import (
    configure_monitor,
    track_performance,
    ServiceComponent,
    EventType
)
import time

monitor = configure_monitor(
    service_name="example-service",
    api_key="your-api-key",
    project_id="your-project-id",
    environment="development"
)

# 使用上下文管理器跟踪性能
def process_large_file(file_path):
    with track_performance("file_processing", ServiceComponent.AGENT_CORE) as span:
        # 记录开始处理
        start_time = time.time()
        
        # 模拟文件处理
        records = []
        with open(file_path, 'r') as f:
            for i, line in enumerate(f):
                # 处理行...
                records.append(process_line(line))
                
                # 更新追踪信息
                if i % 1000 == 0:
                    span.add_data({"processed_lines": i})
        
        # 添加结果数据
        span.add_data({
            "total_records": len(records),
            "file_size_mb": os.path.getsize(file_path) / (1024 * 1024),
            "processing_time": time.time() - start_time
        })
        
        return records

# 使用装饰器跟踪性能
@with_monitoring(component=ServiceComponent.MODEL_SERVICE)
def generate_embeddings(texts):
    # 生成嵌入向量...
    embeddings = model.encode(texts)
    return embeddings
```

### 分布式追踪

```python
from agentforge_contracts.monitoring import (
    configure_monitor,
    ServiceComponent,
    EventType
)

monitor = configure_monitor(
    service_name="example-service",
    api_key="your-api-key",
    project_id="your-project-id",
    environment="development"
)

async def process_request(request_data):
    # 创建主追踪范围
    main_span = monitor.start_span(
        name="process_request",
        component=ServiceComponent.API_GATEWAY,
        event_type=EventType.REQUEST,
        data={"request_id": request_data.get("id")}
    )
    
    try:
        # 调用认证服务
        auth_result = await authenticate_user(
            request_data["user_id"], 
            request_data["token"],
            trace_id=str(main_span.trace_id)  # 传递追踪ID
        )
        
        # 处理数据
        with monitor.start_span(
            name="process_data", 
            component=ServiceComponent.AGENT_CORE,
            event_type=EventType.SYSTEM,
            parent_span_id=main_span.span_id
        ) as data_span:
            result = process_data(request_data["payload"])
            data_span.attributes["records_processed"] = len(result)
        
        # 完成主追踪范围
        monitor.end_span(
            main_span, 
            status="ok", 
            data={"result_size": len(result)}
        )
        
        return {"success": True, "data": result}
    
    except Exception as e:
        # 记录错误并结束追踪范围
        monitor.end_span(
            main_span,
            status="error",
            error_message=str(e),
            data={"error_type": type(e).__name__}
        )
        raise
```

## 配置和部署检查清单

在生产环境中部署并使用监控功能之前，请进行以下检查：

### 架构检查

- [ ] 确认 Python 版本兼容性（建议 Python 3.10+ 以上，支持 Python 3.12+）
- [ ] 确认 `pydantic` 版本为 2.0 或更高
- [ ] 确保所有依赖项已更新到最新安全版本

### 配置检查

- [ ] LogFire API 密钥已正确配置
- [ ] 环境变量或配置文件中已设置适当的项目 ID
- [ ] 每个服务已设置唯一的服务名称
- [ ] 已根据环境设置适当的日志级别
- [ ] 已考虑性能的批处理大小和刷新间隔

### 安全检查

- [ ] 敏感数据已通过 `_sanitize_data` 方法进行正确过滤
- [ ] API 密钥存储在安全的环境变量或密钥管理服务中
- [ ] 已启用适当的采样率以避免过多的数据传输

### 监控检查

- [ ] 已配置 LogFire 仪表盘以显示关键指标
- [ ] 已设置适当的告警规则和通知渠道
- [ ] 已进行性能测试并设置基准
- [ ] 所有关键操作都已添加适当的性能跟踪

### 环境兼容性

- [ ] 在测试环境中所有监控功能测试通过
- [ ] 可通过配置变量或环境变量禁用监控（必要时）
- [ ] 已测试在网络问题时的内存缓冲并恢复功能

### API调用记录

```python
from agentforge_contracts.monitoring import (
    configure_monitor,
    log_api_call,
    ServiceComponent
)
import requests
import time

monitor = configure_monitor(
    service_name="example-service",
    api_key="your-api-key",
    project_id="your-project-id",
    environment="development"
)

def call_weather_api(location):
    url = f"https://api.weather.com/current?location={location}"
    request_data = {"location": location}
    
    start_time = time.time()
    
    try:
        response = requests.get(url)
        duration_ms = (time.time() - start_time) * 1000
        
        # 记录API调用
        log_api_call(
            api_name="weather_api",
            status_code=response.status_code,
            duration_ms=duration_ms,
            component=ServiceComponent.AGENT_CORE,
            request_data=request_data,
            response_data=response.json() if response.ok else None,
            error=str(response.text) if not response.ok else None
        )
        
        return response.json() if response.ok else None
    
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        
        # 记录失败的API调用
        log_api_call(
            api_name="weather_api",
            status_code=500,
            duration_ms=duration_ms,
            component=ServiceComponent.AGENT_CORE,
            request_data=request_data,
            error=str(e)
        )
        
        raise
```
