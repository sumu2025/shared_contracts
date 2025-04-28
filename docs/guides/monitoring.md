# 监控指南

本指南介绍如何使用 AgentForge 共享契约库中的监控功能。

## 概述

监控系统提供了统一的日志记录、指标收集和分布式追踪功能，帮助你实时了解服务的运行状况和性能。主要特性包括：

- 结构化日志记录
- 性能指标收集
- 分布式追踪
- 自动配置选项
- LogFire 集成

## 初始化监控

有多种方式配置监控系统：

### 方法 1: 使用环境变量

最简单的方法是使用环境变量和自动配置：

```python
from shared_contracts.monitoring import setup_from_env

# 从环境变量配置
monitor = setup_from_env(service_name="my-service")

# 现在可以使用 monitor 了
monitor.info(
    message="服务已启动",
    component="system",
    event_type="lifecycle",
)
```

相关的环境变量：

- `LOGFIRE_WRITE_TOKEN`: LogFire API 密钥
- `LOGFIRE_PROJECT_ID`: LogFire 项目 ID
- `ENVIRONMENT`: 运行环境 (development, staging, production)

### 方法 2: 直接配置

如果需要更多控制，可以直接创建配置：

```python
from shared_contracts.monitoring.implementations.logfire_config import LogFireConfig
from shared_contracts.monitoring.implementations.logfire_client import LogFireClient
from shared_contracts.monitoring.monitor_types import LogLevel

# 创建配置
config = LogFireConfig(
    api_key="your-api-key",
    project_id="your-project-id",
    service_name="my-service",
    environment="development",
    min_log_level=LogLevel.DEBUG,
)

# 创建客户端
monitor = LogFireClient(config)
```

### 方法 3: 使用配置脚本

对于更复杂的场景，可以使用提供的配置脚本：

```bash
python -m shared_contracts.scripts.setup_monitoring --service-name my-service --environment production
```

## 记录日志

监控系统提供了不同级别的日志方法：

```python
# 基本日志
monitor.log(
    message="用户已登录",
    level=LogLevel.INFO,
    component=ServiceComponent.AUTH,
    event_type=EventType.USER,
    data={"user_id": "123", "login_method": "password"},
    tags=["auth", "login"],
)

# 便捷方法
monitor.debug("调试消息", ServiceComponent.SYSTEM, EventType.SYSTEM)
monitor.info("信息消息", ServiceComponent.API, EventType.REQUEST)
monitor.warning("警告消息", ServiceComponent.DATABASE, EventType.DATA)
monitor.error("错误消息", ServiceComponent.AUTH, EventType.SECURITY)
monitor.critical("严重错误", ServiceComponent.AGENT_CORE, EventType.ERROR)
```

## 分布式追踪

追踪允许你跟踪跨多个服务的操作：

```python
# 创建跟踪上下文
span = monitor.start_span(
    name="process-request",
    component=ServiceComponent.API,
    event_type=EventType.REQUEST,
    data={"request_id": "req-123"},
)

try:
    # 执行操作...
    result = process_data()
    
    # 结束跟踪
    monitor.end_span(
        span=span,
        status="ok",
        data={"result_id": result.id},
    )
except Exception as e:
    # 记录错误
    monitor.end_span(
        span=span,
        status="error",
        error_message=str(e),
    )
    raise
```

## 上下文管理器

对于更简洁的代码，可以使用上下文管理器：

```python
from shared_contracts.monitoring.utils.logger_utils import track_performance
from shared_contracts.monitoring.utils.tracing_utils import create_trace_context

# 性能跟踪
with track_performance("database-query", ServiceComponent.DATABASE) as span:
    # 执行查询...
    results = db.execute_query()
    span.add_data({"record_count": len(results)})

# 追踪上下文
with create_trace_context(
    "process-payment",
    component=ServiceComponent.PAYMENT,
    data={"payment_id": "pay-123"},
) as span:
    # 处理支付...
    span.attributes["amount"] = 99.99
```

## 装饰器

可以使用装饰器自动跟踪函数执行：

```python
from shared_contracts.monitoring.utils.logger_utils import with_monitoring
from shared_contracts.monitoring.utils.tracing_utils import trace_method

# 函数监控
@with_monitoring(component=ServiceComponent.API)
def process_request(request_id, data):
    # 处理请求...
    return result

# 方法追踪
class PaymentService:
    @trace_method(component=ServiceComponent.PAYMENT)
    def process_payment(self, payment_id, amount):
        # 处理支付...
        return receipt
```

## 记录特定事件

监控系统提供了记录特定类型事件的便捷方法：

```python
# 记录 API 调用
monitor.record_api_call(
    api_name="user-service/get-profile",
    status_code=200,
    duration_ms=45.3,
    component=ServiceComponent.API,
    request_data={"user_id": "123"},
    response_data={"name": "张三", "email": "zhang@example.com"},
)

# 记录性能指标
monitor.record_performance(
    operation="database-query",
    duration_ms=120.5,
    component=ServiceComponent.DATABASE,
    success=True,
    details={"query_type": "select", "table": "users", "records": 100},
)

# 记录模型验证
monitor.record_model_validation(
    model_name="User",
    success=True,
    data={"fields": ["name", "email"]},
)
```

## 配置自动监控

如果不想手动配置监控，可以启用自动配置：

```python
from shared_contracts.monitoring.utils.logger_utils import get_monitor

# 获取自动配置的监控实例
monitor = get_monitor()  # 如果未配置，会自动创建一个默认实例

# 现在可以使用 monitor 了
monitor.info(
    message="使用自动配置的监控",
    component="system",
    event_type="system",
)
```

## 最佳实践

- **使用结构化数据**: 始终在 `data` 参数中包含结构化数据，而不是在消息中包含变量。
- **正确分类**: 使用合适的组件和事件类型，保持一致性。
- **跟踪重要操作**: 为关键业务操作创建跟踪跨度，追踪完整流程。
- **记录关键指标**: 使用 `record_performance` 记录关键操作的性能。
- **使用标签**: 添加标签以便于筛选和搜索日志。
- **控制日志级别**: 在生产环境中使用较高的日志级别，避免过多日志。
