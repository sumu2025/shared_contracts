# 模块间集成测试

此目录包含AgentForge项目中shared_contracts模块的集成测试，用于验证不同模块间的通信和接口一致性。

## 测试场景

1. **Agent-Model交互测试** (`test_agent_model_integration.py`)
   - 测试Agent服务如何调用Model服务进行文本生成
   - 验证数据格式和契约的一致性

2. **Agent-Tool交互测试** (`test_agent_tool_integration.py`)
   - 测试Agent服务如何调用Tool服务执行工具
   - 验证工具参数传递和结果处理

3. **完整工作流测试** (`test_complete_workflow.py`)
   - 模拟完整的Agent、Model和Tool服务交互流程
   - 使用监控工具追踪服务间数据流
   - 验证复杂场景下的错误处理和恢复

## 运行测试

你可以使用以下命令运行集成测试：

```bash
# 运行所有集成测试
cd /Users/peacock/Projects/AgentForge
source .venv/bin/activate
python shared_contracts/integration_tests/run_integration_tests.py

# 显示详细输出
python shared_contracts/integration_tests/run_integration_tests.py -v

# 运行特定测试
python shared_contracts/integration_tests/run_integration_tests.py -t agent_model_integration

# 在第一个失败后停止
python shared_contracts/integration_tests/run_integration_tests.py -x
```

或者使用pytest直接运行：

```bash
cd /Users/peacock/Projects/AgentForge
source .venv/bin/activate
python -m pytest shared_contracts/integration_tests/ -v
```

## 测试设计说明

这些集成测试使用了模拟服务实现，模拟了真实服务间的通信而无需实际部署完整系统。测试验证：

1. **接口合约的一致性**：确保服务之间通过共享契约正确通信
2. **数据传递的完整性**：验证数据在不同服务间的传递保持一致
3. **错误处理**：测试服务间错误传播和恢复机制
4. **监控集成**：验证监控工具能正确追踪服务间数据流

集成测试使用了以下关键技术：

- **异步测试**：使用`pytest-asyncio`处理异步服务调用
- **Mock对象**：模拟外部服务和API
- **装饰器模式**：使用`with_monitoring`追踪服务调用
- **上下文管理器**：使用`track_performance`测量性能

## 注意事项

- 测试不会连接到实际的LogFire服务，而是使用Mock对象模拟监控行为
- 测试可以离线运行，不需要外部网络连接
- 这些测试验证接口合约，不测试具体实现的业务逻辑
