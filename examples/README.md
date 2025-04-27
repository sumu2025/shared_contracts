# AgentForge 共享契约库示例

这个目录包含了如何使用AgentForge共享契约库的示例代码。通过这些示例，您可以了解如何使用监控工具、实用函数和其他共享组件。

## 示例列表

### 监控客户端示例 (`monitoring_example.py`)

这个示例展示如何使用LogFire监控客户端记录服务活动、收集指标和实现分布式追踪。

主要功能包括：
- 配置和初始化监控客户端
- 记录不同级别的日志
- 跟踪函数执行性能
- 实现分布式追踪
- 记录API调用
- 收集和发送指标

### 实用工具示例 (`utils_example.py`)

这个示例展示如何使用各种实用工具函数简化开发工作。

主要功能包括：
- Schema工具：从Pydantic模型提取、合并和验证JSON Schema
- 验证工具：验证数据模型、UUID、枚举值等
- 序列化工具：在模型、字典和JSON之间转换
- 计时工具：计时、重试和性能测量

## 如何运行示例

1. 确保已安装所有依赖项：

```bash
cd /path/to/shared_contracts
pip install -e .
```

2. 运行示例：

```bash
# 运行监控示例
python examples/monitoring_example.py

# 运行工具示例
python examples/utils_example.py
```

## 集成指南

### 监控集成

将监控集成到您的服务中，只需要几行代码：

```python
from agentforge_contracts.monitoring import configure_monitor, LogLevel, ServiceComponent

# 配置监控
monitor = configure_monitor(
    service_name="your-service-name",
    api_key="your-logfire-api-key",
    project_id="your-logfire-project-id",
    environment="production",
    min_log_level=LogLevel.INFO,
)

# 记录日志
monitor.info(
    message="服务启动",
    component=ServiceComponent.SYSTEM,
    event_type="lifecycle",
)
```

### 工具函数集成

工具函数可以帮助简化常见操作：

```python
from agentforge_contracts.utils import (
    model_to_json, 
    validate_model, 
    timed
)

# 使用验证工具
result = validate_model(UserModel, user_data)
if result.valid:
    user = result.model
    # 处理有效的用户数据
else:
    # 处理验证错误
    errors = result.errors

# 使用序列化工具
json_data = model_to_json(user_model)

# 使用计时装饰器
@timed
def process_data(data):
    # 处理数据...
    return result
```

## 最佳实践

1. **监控最佳实践**
   - 使用正确的组件和事件类型分类日志
   - 使用追踪装饰器自动监控关键函数
   - 为重要操作添加性能跟踪
   - 在关闭服务前刷新监控数据

2. **工具使用最佳实践**
   - 使用验证工具在API边界验证数据
   - 利用重试机制处理不稳定的外部服务
   - 使用序列化工具处理数据转换
   - 使用Schema工具生成API文档

更多信息，请参考主README文档和源代码注释。
