# AgentForge Shared Contracts

_版本: 1.0.0 | 最后更新: 2025-04-28_

**版本:** 1.0.0  
**最后更新:** 2025-04-28

[![CI Status](https://github.com/agentforge/shared_contracts/workflows/CI/badge.svg)](https://github.com/agentforge/shared_contracts/actions)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![codecov](https://codecov.io/gh/agentforge/shared_contracts/branch/main/graph/badge.svg)](https://codecov.io/gh/agentforge/shared_contracts)

AgentForge共享契约模块(shared_contracts)是一个定义服务间通信接口和数据模型的核心库，旨在确保不同服务组件之间的一致性和互操作性。

## 重要更新：导入路径优化

我们最近对导入路径进行了优化，现在支持两种导入方式：

1. **作为已安装的包导入（推荐）**：
   ```python
   from shared_contracts.core import models
   from shared_contracts.monitoring import LogFireClient
   ```

2. **从项目中直接导入**：
   ```python
   from core import models
   from monitoring import LogFireClient
   ```

为了支持这两种导入方式，我们进行了以下更改：
- 添加了 `shared_contracts` 包结构
- 更新了导入语句以支持两种模式
- 提供了开发模式安装脚本

### 如何设置导入路径

**方法1: 运行开发模式安装脚本**
```bash
# 从项目根目录运行
python setup_dev.py
```

**方法2: 手动安装包**
```bash
pip install -e .
```

## 概述

shared_contracts模块提供以下核心功能：

- **数据模型定义**：使用Pydantic模型定义跨服务的数据结构
- **服务接口规范**：使用Protocol定义服务间通信的标准接口
- **监控集成**：集成LogFire提供全面的监控、日志和跟踪功能
- **实用工具**：提供验证、序列化和其他常用功能的工具函数

该模块遵循契约优先的设计原则，通过明确定义的接口和数据模型，降低了微服务架构中的集成复杂性。

## 安装指南

### 先决条件

- Python 3.10+
- pip 或 poetry

### 使用pip安装

```bash
# 从项目根目录安装
pip install -e .

# 或者指定模块路径
pip install -e /path/to/shared_contracts
```

### 使用poetry安装

```bash
# 从项目根目录安装
cd /path/to/shared_contracts
poetry install
```

## 开发指南

### 设置开发环境

1. 克隆仓库:
   ```bash
   git clone https://github.com/agentforge/shared_contracts.git
   cd shared_contracts
   ```

2. 使用Poetry安装依赖:
   ```bash
   poetry install --with dev
   ```

3. 安装pre-commit钩子:
   ```bash
   poetry run pre-commit install
   ```

### 开发工作流程

1. 创建新分支进行功能开发:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. 本地验证代码:
   ```bash
   # 使用验证脚本运行所有检查
   bash scripts/validate.sh
   
   # 自动格式化代码
   bash scripts/auto_format.sh
   
   # 运行所有测试
   bash scripts/run_tests.sh
   
   # 只运行单元测试
   bash scripts/run_tests.sh --type unit
   
   # 只运行集成测试
   bash scripts/run_tests.sh --type integration
   ```

3. 构建包:
   ```bash
   bash scripts/build.sh
   ```

4. 提交代码:
   ```bash
   git add .
   git commit -m "feat: 添加新功能描述"
   ```
   
   提交消息格式:
   - `feat`: 新功能
   - `fix`: 错误修复
   - `docs`: 文档更改
   - `style`: 格式调整
   - `refactor`: 代码重构
   - `test`: 添加测试
   - `chore`: 构建过程或辅助工具变动

5. 推送分支并创建Pull Request:
   ```bash
   git push origin feature/your-feature-name
   ```

### CI/CD流程

本仓库使用GitHub Actions进行持续集成和部署:

1. **持续集成 (CI)**:
   - 每次推送或PR时自动运行
   - 执行依赖版本检查，确保pydantic>=2.0.0
   - 自动修复代码风格问题，减少格式相关的CI失败
   - 执行类型检查和单元测试
   - 生成覆盖率报告并上传到Codecov

2. **持续部署 (CD)**:
   - 仅在合并到主分支时触发
   - 自动构建包并验证
   - 部署到指定环境(开发、测试或生产)
   - 使用LogFire记录部署状态和性能指标

3. **开发工具**:
   - 提供自动格式化脚本: `./scripts/auto_format.sh`
   - 提供多种特定问题修复脚本: `./scripts/fix_*.sh`
   - 使用pre-commit钩子确保代码质量

详细说明请参阅[CI/CD指南](./docs/ci_cd_guide.md)和[代码风格指南](./docs/guides/code_style_guide.md)。

## 模块结构

```
shared_contracts/
├── core/                    # 核心数据模型和接口
│   ├── models/              # 数据模型定义
│   └── interfaces/          # 服务接口定义
├── monitoring/              # 监控和日志组件  
│   ├── implementations/     # 监控实现(LogFire)
│   └── utils/               # 监控工具函数
├── schemas/                 # JSON Schema定义
├── utils/                   # 通用工具函数
├── scripts/                 # 开发和部署脚本
└── tests/                   # 单元测试和集成测试
```

## 快速入门

### 使用数据模型

```python
from shared_contracts.core.models.agent_models import AgentConfig, AgentCapability
from uuid import uuid4

# 创建代理配置
agent_config = AgentConfig(
    name="Example Agent",
    description="A simple example agent",
    model_id="gpt-4",
    system_prompt="You are a helpful assistant.",
    capabilities={AgentCapability.CONVERSATION, AgentCapability.TOOL_USE},
    tools=["calculator", "weather"]
)

# 验证和使用
print(f"Agent ID: {agent_config.agent_id}")
print(f"Capabilities: {agent_config.capabilities}")
```

### 实现服务接口

```python
from shared_contracts.core.interfaces.agent_interface import AgentServiceInterface
from shared_contracts.core.models.base_models import BaseResponse
from shared_contracts.core.models.agent_models import AgentConfig
import uuid

# 实现代理服务接口
class MyAgentService(AgentServiceInterface):
    async def create_agent(self, config: AgentConfig) -> BaseResponse[AgentConfig]:
        # 实现创建代理的逻辑
        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data=config
        )
    
    # 实现其他接口方法...
```

### 配置监控

```python
from shared_contracts.monitoring import configure_monitor, LogLevel, ServiceComponent, EventType

# 配置监控客户端
monitor = configure_monitor(
    service_name="my-service",
    api_key="your-logfire-api-key",
    project_id="your-project-id",
    environment="development"
)

# 记录事件
monitor.info(
    message="Service started",
    component=ServiceComponent.SYSTEM,
    event_type=EventType.LIFECYCLE
)

# 记录指标
monitor.record_metric(
    metric_name="request_count",
    value=1.0,
    tags={"endpoint": "/api/agent"}
)
```

## 功能概述

### 核心模型

- **Agent模型**: 定义智能代理的配置和状态
- **Model模型**: 定义AI模型的配置和接口
- **Tool模型**: 定义工具的参数和结果

### 服务接口

- **AgentServiceInterface**: 代理服务的接口定义
- **ModelServiceInterface**: 模型服务的接口定义
- **ToolServiceInterface**: 工具服务的接口定义

### 监控功能

- **LogFire集成**: 提供日志、指标和分布式追踪
- **性能跟踪**: 测量和记录操作执行时间
- **错误追踪**: 记录和分析错误事件

## 贡献指南

1. Fork项目
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开Pull Request

## 故障排除

以下是使用shared_contracts模块时可能遇到的常见问题和解决方法：

### 安装问题

#### 依赖冲突

**问题**: 安装时出现依赖包版本冲突。

**解决方法**: 创建新的虚拟环境，指定兼容版本：
```bash
python -m venv fresh_env
source fresh_env/bin/activate  # 在Windows上使用 fresh_env\Scripts\activate
pip install -e .
```

#### Python版本不兼容

**问题**: 出现"Python版本不兼容"错误。

**解决方法**: 确保使用Python 3.10或更高版本。使用pyenv管理多个Python版本：
```bash
pyenv install 3.10.0
pyenv local 3.10.0
```

### 数据模型问题

#### 模型验证错误

**问题**: Pydantic模型验证失败。

**解决方法**: 使用`validate_model`函数获取详细错误信息：
```python
from shared_contracts.utils.validation import validate_model

is_valid, errors = validate_model(my_model)
if not is_valid:
    print(f"Validation errors: {errors}")
```

#### 查看类型操作失败

**问题**: Pydantic v2类型属性访问变化导致错误。

**解决方法**: 确认使用正确的Pydantic v2 API：
```python
# 错误方式: my_model.__fields__

# 正确方式: 
 from pydantic import TypeAdapter
model_type_info = TypeAdapter(MyModel).json_schema()
```

### 监控问题

#### LogFire连接失败

**问题**: 无法连接到LogFire服务。

**解决方法**: 检查API密钥和网络连接，可以使用内存实现作为替代：
```python
from shared_contracts.monitoring.implementations.memory_monitor import MemoryMonitor

# 使用内存监控器

monitor = MemoryMonitor(service_name="my-service")
```

#### 日志没有出现在LogFire中

**问题**: 日志记录了但在LogFire控制台中未显示。

**解决方法**: 确保调用`flush()`和在服务结束时调用`shutdown()`：
```python
# 在程序结束前
monitor.flush()
monitor.shutdown()
```

### 集成问题

#### 服务间通信失败

**问题**: 实现的服务无法正确通信。

**解决方法**: 使用集成测试验证接口实现：
```python
# 查看示例实现和集成测试
# /examples/service_communication_example.py
# /integration_tests/test_agent_model_integration.py
```

## 更多文档

- [核心组件文档](./docs/core.md) - 数据模型和接口详解
- [监控组件文档](./docs/monitoring.md) - LogFire集成指南
- [工具函数文档](./docs/utils.md) - 工具函数使用说明
- [集成指南](./docs/integration.md) - 在服务中使用shared_contracts
- [故障排除指南](./docs/troubleshooting.md) - 详细的故障排除和常见问题解答

## 文档导航

下面的指南将帮助您根据不同需求找到相关文档：

| 如果您需要... | 请参考... |
|-------------|-------------|
| 了解基本数据模型 | [核心组件文档 - 数据模型](./docs/core.md#数据模型) |
| 实现服务接口 | [核心组件文档 - 接口定义](./docs/core.md#接口定义) 和 [集成指南](./docs/integration.md) |
| 配置监控系统 | [监控组件文档 - LogFire集成](./docs/monitoring.md#logfire集成) |
| 进行数据验证 | [工具函数文档 - 验证工具](./docs/utils.md#验证工具) |
| 实现服务间通信 | [集成指南 - 服务间通信模式](./docs/integration.md#服务间通信模式) |
| 查看示例应用 | [examples/complete_application_example.py](./examples/complete_application_example.py)、[examples/model_service_example.py](./examples/model_service_example.py) 和 [examples/tool_service_example.py](./examples/tool_service_example.py) |
| 排查常见问题 | [故障排除指南](./docs/troubleshooting.md) |
| **了解CI/CD流程** | **[新] [CI/CD指南](./docs/ci_cd_guide.md)** |
| **了解代码风格规范** | **[新] [代码风格指南](./docs/guides/code_style_guide.md)** |
| **了解开发流程** | **[新] [开发者指南](./docs/guides/developer_guide.md)** |
| **了解测试标准** | **[新] [测试要求](./docs/testing_requirements.md)** |
