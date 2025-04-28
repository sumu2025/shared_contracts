# AgentForge 共享契约库

欢迎使用 AgentForge 共享契约库文档。该库定义了 AgentForge 平台各服务之间通信的接口和数据模型。

## 概述

AgentForge 共享契约库是一组规范化的接口定义和数据模型，用于确保平台各组件之间的互操作性。通过使用共享契约，我们可以：

- 确保服务间通信的类型安全
- 减少重复代码
- 提高系统可维护性
- 简化新服务的集成

## 主要模块

该库包含以下主要模块：

- **core**: 核心模型和接口
- **monitoring**: 监控和日志接口
- **schemas**: 数据验证和模式定义
- **utils**: 通用工具函数

## 快速开始

### 安装

```bash
pip install agentforge-contracts
```

或者使用 Poetry：

```bash
poetry add agentforge-contracts
```

### 基本使用

```python
from shared_contracts.core.models import BaseModel
from shared_contracts.monitoring import setup_from_env

# 配置监控
monitor = setup_from_env(service_name="my-service")

# 使用模型
class User(BaseModel):
    name: str
    email: str
    
# 记录事件
monitor.info(
    message="用户创建成功",
    component="user_service",
    event_type="user_management",
    user_id="123456"
)
```

## 特性

- **基于 Pydantic v2**: 高性能数据验证和序列化
- **类型安全**: 完整的类型注解支持
- **面向契约设计**: 清晰定义服务间接口
- **集成监控**: 统一的日志和监控接口
- **跨服务一致性**: 统一的错误处理和响应格式

## 文档结构

- **[API 参考](api/index.md)**: 详细的 API 文档
- **[指南](guides/index.md)**: 使用指南和最佳实践
- **[示例](examples/index.md)**: 代码示例和用例
- **[开发](development/index.md)**: 开发和贡献指南
