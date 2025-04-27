# 工具函数文档

_版本: 1.0.0 | 最后更新: 2025-04-26_

工具函数模块提供了一系列实用工具，用于简化AgentForge应用程序的开发过程。这些工具涵盖了模式验证、序列化/反序列化、性能计时和其他常见任务。

相关文档:
- [核心组件文档](./core.md) - 了解如何应用这些工具于核心数据模型
- [监控组件文档](./monitoring.md) - 提供监控相关的工具函数用法
- [集成指南](./integration.md) - 工具函数在实际集成场景中的使用

## 目录

- [模式工具](#模式工具)
- [序列化工具](#序列化工具)
- [验证工具](#验证工具)
- [计时工具](#计时工具)
- [最佳实践](#最佳实践)

## 模式工具

位置: `shared_contracts.utils.schema_utils`

模式工具模块提供了用于处理JSON Schema的功能，支持从Pydantic模型生成Schema以及Schema验证。

### 主要函数

#### `generate_schema_from_model`

从Pydantic模型生成JSON Schema。

```python
from shared_contracts.utils.schema_utils import generate_schema_from_model
from shared_contracts.core.models.agent_models import AgentConfig

# 生成模型的JSON Schema
schema = generate_schema_from_model(AgentConfig)
print(schema)
```

#### `validate_against_schema`

验证数据是否符合指定的JSON Schema。

```python
from shared_contracts.utils.schema_utils import validate_against_schema

# Schema定义
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer", "minimum": 0}
    },
    "required": ["name"]
}

# 验证数据
valid_data = {"name": "John", "age": 30}
invalid_data = {"age": -5}

result1 = validate_against_schema(valid_data, schema)
print(f"Valid data validation: {result1}")  # True

result2, errors = validate_against_schema(invalid_data, schema, return_errors=True)
print(f"Invalid data validation: {result2}")  # False
print(f"Validation errors: {errors}")  # 包含错误详情的列表
```

#### `merge_schemas`

合并多个JSON Schema。

```python
from shared_contracts.utils.schema_utils import merge_schemas

# 两个Schema
schema1 = {
    "type": "object",
    "properties": {
        "name": {"type": "string"}
    },
    "required": ["name"]
}

schema2 = {
    "type": "object",
    "properties": {
        "age": {"type": "integer"}
    },
    "required": ["age"]
}

# 合并Schema
merged = merge_schemas(schema1, schema2)
print(merged)
```

## 序列化工具

位置: `shared_contracts.utils.serialization`

序列化工具提供了用于在不同格式之间转换数据的功能，特别是处理Pydantic模型的序列化和反序列化。

### 主要函数

#### `serialize_model`

将Pydantic模型序列化为字典或JSON字符串。

```python
from shared_contracts.utils.serialization import serialize_model
from shared_contracts.core.models.agent_models import AgentConfig, AgentCapability
import uuid

# 创建模型实例
agent = AgentConfig(
    agent_id=uuid.uuid4(),
    name="Test Agent",
    description="A test agent",
    model_id="gpt-4",
    system_prompt="You are a test assistant.",
    capabilities={AgentCapability.CONVERSATION}
)

# 序列化为字典
dict_data = serialize_model(agent)
print(dict_data)

# 序列化为JSON字符串
json_data = serialize_model(agent, as_json=True, indent=2)
print(json_data)
```

#### `deserialize_model`

从字典或JSON字符串反序列化为Pydantic模型。

```python
from shared_contracts.utils.serialization import deserialize_model
from shared_contracts.core.models.agent_models import AgentConfig

# JSON数据
json_data = """
{
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Test Agent",
  "description": "A test agent",
  "model_id": "gpt-4",
  "system_prompt": "You are a test assistant.",
  "capabilities": ["conversation"],
  "tools": []
}
"""

# 反序列化为模型
agent = deserialize_model(AgentConfig, json_data)
print(f"Agent name: {agent.name}")
print(f"Agent capabilities: {agent.capabilities}")

# 从字典反序列化
dict_data = {
    "agent_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Dict Agent",
    "description": "An agent from dict",
    "model_id": "gpt-4",
    "system_prompt": "You are a dict assistant.",
    "capabilities": ["conversation", "tool_use"]
}

agent2 = deserialize_model(AgentConfig, dict_data)
print(f"Agent2 name: {agent2.name}")
```

#### `serialize_enum`

序列化枚举值。

```python
from shared_contracts.utils.serialization import serialize_enum
from shared_contracts.core.models.agent_models import AgentCapability

# 序列化单个枚举值
enum_value = serialize_enum(AgentCapability.CONVERSATION)
print(enum_value)  # "conversation"

# 序列化枚举集合
enum_set = {AgentCapability.CONVERSATION, AgentCapability.TOOL_USE}
enum_list = serialize_enum(enum_set)
print(enum_list)  # ["conversation", "tool_use"]
```

## 验证工具

位置: `shared_contracts.utils.validation`

验证工具提供了用于验证数据和模型的功能。

### 主要函数

#### `validate_model`

验证模型实例是否有效。

```python
from shared_contracts.utils.validation import validate_model
from shared_contracts.core.models.agent_models import AgentConfig
import uuid

# 有效模型
valid_agent = AgentConfig(
    agent_id=uuid.uuid4(),
    name="Valid Agent",
    description="A valid agent",
    model_id="gpt-4",
    system_prompt="You are a valid assistant."
)

# 验证
is_valid, errors = validate_model(valid_agent)
print(f"Is valid: {is_valid}")  # True
print(f"Errors: {errors}")  # None

# 无效模型 (手动构建，跳过Pydantic验证)
invalid_agent = AgentConfig.construct()
invalid_agent.name = ""  # 名称不能为空

# 验证
is_valid, errors = validate_model(invalid_agent)
print(f"Is valid: {is_valid}")  # False
print(f"Errors: {errors}")  # 包含错误详情
```

#### `validate_dict_against_model`

验证字典是否符合模型定义。

```python
from shared_contracts.utils.validation import validate_dict_against_model
from shared_contracts.core.models.agent_models import AgentConfig

# 有效字典
valid_dict = {
    "name": "Dict Agent",
    "description": "An agent from dict",
    "model_id": "gpt-4",
    "system_prompt": "You are a dict assistant.",
    "capabilities": ["conversation"]
}

# 验证
is_valid, errors = validate_dict_against_model(valid_dict, AgentConfig)
print(f"Is valid: {is_valid}")  # True
print(f"Errors: {errors}")  # None

# 无效字典
invalid_dict = {
    "name": "",  # 名称不能为空
    "description": "Invalid agent"
    # 缺少必需字段
}

# 验证
is_valid, errors = validate_dict_against_model(invalid_dict, AgentConfig)
print(f"Is valid: {is_valid}")  # False
print(f"Errors: {errors}")  # 包含错误详情
```

## 计时工具

位置: `shared_contracts.utils.timing`

计时工具提供了用于测量代码执行时间的功能。

### 主要函数

#### `time_function`

装饰器，用于测量函数执行时间。

```python
from shared_contracts.utils.timing import time_function
import time

@time_function
def slow_function(duration):
    time.sleep(duration)
    return "Done"

# 执行函数
result = slow_function(0.5)
# 输出: "slow_function took 0.502 seconds to execute"
```

#### `TimerContext`

上下文管理器，用于测量代码块执行时间。

```python
from shared_contracts.utils.timing import TimerContext
import time

# 使用上下文管理器测量代码块
with TimerContext("data_processing") as timer:
    # 执行一些操作
    time.sleep(0.3)
    data = process_data()
    
    # 查看当前耗时
    elapsed = timer.elapsed()
    print(f"Elapsed time so far: {elapsed} seconds")
    
    # 继续执行
    time.sleep(0.2)
    result = transform_data(data)

# 输出: "data_processing took 0.504 seconds to execute"

# 获取总耗时
total_time = timer.elapsed()
print(f"Total execution time: {total_time} seconds")
```

## 最佳实践

### 性能考虑

- **批量验证**：对于大量数据的验证，避免单独验证每条记录，而是使用批量验证方法。
- **缓存Schema**：如果需要重复使用同一模型的Schema，应缓存生成的Schema而不是重复生成。

### 错误处理

- 始终检查验证结果，并妥善处理验证错误。
- 对于关键操作，使用try-except捕获反序列化和验证过程中的异常。

```python
from shared_contracts.utils.validation import validate_dict_against_model
from shared_contracts.utils.serialization import deserialize_model
from shared_contracts.core.models.agent_models import AgentConfig

def process_agent_data(data):
    try:
        # 验证数据
        is_valid, errors = validate_dict_against_model(data, AgentConfig)
        if not is_valid:
            return {"success": False, "errors": errors}
        
        # 反序列化为模型
        agent = deserialize_model(AgentConfig, data)
        
        # 处理模型
        result = do_something_with_agent(agent)
        return {"success": True, "result": result}
    
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 组合使用

工具函数通常可以组合使用，以创建更复杂的功能：

```python
from shared_contracts.utils.schema_utils import generate_schema_from_model
from shared_contracts.utils.serialization import serialize_model
from shared_contracts.utils.validation import validate_dict_against_model
from shared_contracts.core.models.agent_models import AgentConfig

# 生成并保存模型Schema
schema = generate_schema_from_model(AgentConfig)
with open("agent_schema.json", "w") as f:
    json.dump(schema, f, indent=2)

# 从用户输入创建代理
def create_agent_from_input(input_data):
    # 验证输入
    is_valid, errors = validate_dict_against_model(input_data, AgentConfig)
    if not is_valid:
        return {"success": False, "errors": errors}
    
    # 创建代理
    agent = AgentConfig(**input_data)
    
    # 序列化为存储格式
    agent_json = serialize_model(agent, as_json=True)
    
    # 存储代理配置
    save_to_database(agent.agent_id, agent_json)
    
    return {"success": True, "agent_id": str(agent.agent_id)}
```

通过组合使用这些工具函数，您可以构建更强大、更可靠的应用程序，同时减少重复代码和常见错误。

## 常见问题与故障排除

下面列出了使用工具函数时可能遇到的一些常见问题及解决方案。

### 序列化问题

#### 问题：序列化复杂对象时出现循环引用错误

```
TypeError: Object of type X is not JSON serializable
```

**解决方案**：
- 使用`serialize_model`函数而非直接使用`json.dumps`
- 确保对象不包含循环引用
- 对于复杂对象，可以使用`CustomJSONEncoder`：

```python
from shared_contracts.utils.serialization import CustomJSONEncoder
import json

# 使用自定义编码器
 json_str = json.dumps(complex_object, cls=CustomJSONEncoder, indent=2)
```

#### 问题：模型升级后的反序列化问题

**解决方案**：
- 使用`model_version`标记序列化的数据版本
- 实现版本迁移函数：

```python
def migrate_data(data, from_version, to_version):
    if from_version == "1.0" and to_version == "2.0":
        # 执行版本间迁移
        data["new_field"] = default_value
        # 移除已废弃的字段
        if "old_field" in data:
            del data["old_field"]
    return data
```

### 验证问题

#### 问题：对大数据集验证时性能低下

**解决方案**：
- 批量验证而非逐条验证
- 对关键字段进行预验证，然后再对完整数据进行验证
- 考虑使用异步验证处理大量记录：

```python
async def validate_batch(items, model_cls, batch_size=100):
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        # 并行验证
        tasks = [validate_dict_against_model(item, model_cls) for item in batch]
        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)
    return results
```

#### 问题：验证错误消息不易理解

**解决方案**：
- 使用`format_validation_errors`函数格式化错误消息：

```python
from shared_contracts.utils.validation import format_validation_errors

# 格式化错误消息
readable_errors = format_validation_errors(validation_errors)
```

### 查询法式问题

#### 问题：查询器执行速度慢

**解决方案**：
- 预编译查询器以提高性能
- 缓存查询结果

```python
from shared_contracts.utils.schema_utils import compile_query_path

# 预编译查询路径
compiled_query = compile_query_path("data.users[*].profile.email")

# 使用编译后的查询器
results = compiled_query.find(data)
```

### 其他常见问题

#### 问题：深度字典更新的冲突处理

**解决方案**：
- 明确指定`overwrite_lists`参数的值：

```python
from shared_contracts.utils.serialization import deep_dict_update

# 合并列表而非覆盖
result = deep_dict_update(base_dict, update_dict, overwrite_lists=False)

# 完全覆盖列表
result = deep_dict_update(base_dict, update_dict, overwrite_lists=True)
```

#### 问题：计时工具在异步代码中的使用

**解决方案**：
- 对于异步函数，使用异步计时装饰器：

```python
from shared_contracts.utils.timing import async_time_function

@async_time_function
async def async_operation():
    await asyncio.sleep(0.5)
    return "result"
```
