"""
代理、模型和工具系统集成测试。

测试代理、模型和工具服务之间的交互，验证端到端工作流..."""

import json
import uuid
from pathlib import Path

import pytest

from shared_contracts.core.models.agent_models import AgentCapability, AgentConfig
from shared_contracts.core.models.model_models import (
    ModelCapability,
    ModelConfig,
    ModelProvider,
    ModelType,
)
from shared_contracts.core.models.tool_models import (
    ToolDefinition,
    ToolParameter,
    ToolParameterType,
)
from shared_contracts.monitoring import EventType, ServiceComponent, track_performance
from tests.helpers.utils import load_test_json


def load_json_data(filename):
    """从测试数据目录加载JSON文件。...."""
    test_data_dir = Path(__file__).parent.parent / "tests" / "test_data"
    file_path = test_data_dir / filename
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_calculator_tool_workflow(setup_services):
    """测试包含计算器工具调用的完整工作流。...."""
    # 设置
    services = setup_services
    monitor = services["monitor"]
    model_service = services["model_service"]
    tool_service = services["tool_service"]
    agent_service = services["agent_service"]

    # 1. 注册模型
    model_data = load_json_data("model_config.json")
    model_config = ModelConfig.model_validate(model_data)
    model_response = await model_service.register_model(model_config)
    assert model_response.success, f"模型注册失败: {model_response.error}"

    # 2. 注册工具
    tool_definitions = load_json_data("tool_definitions.json")
    for tool_data in tool_definitions:
        tool_definition = ToolDefinition.model_validate(tool_data)
        tool_response = await tool_service.register_tool(tool_definition)
        assert tool_response.success, f"工具注册失败: {tool_response.error}"

    # 3. 创建代理
    agent_data = load_json_data("agent_config.json")
    agent_config = AgentConfig.model_validate(agent_data)
    agent_response = await agent_service.create_agent(agent_config)
    assert agent_response.success, f"代理创建失败: {agent_response.error}"
    agent_id = agent_response.data.agent_id

    # 4. 执行计算器工具调用流程
    with track_performance("calculator_workflow", ServiceComponent.AGENT_CORE) as span:
        # 4.1 发送包含计算器工具指令的消息
        calc_message = "Please use the calculator tool to add 5 and 3."
        calc_response = await agent_service.process_message(
            agent_id=agent_id, message=calc_message
        )
        
        # 设置跟踪数据
        span.add_data({
            "agent_id": str(agent_id),
            "message_type": "calculator"
        })

    # 验证响应
    assert calc_response.success, f"消息处理失败: {calc_response.error}"
    
    # 验证工具结果
    assert "tool_results" in calc_response.data, "响应中缺少工具结果"
    assert len(calc_response.data["tool_results"]) > 0, "没有执行计算器工具"
    
    # 验证具体结果
    tool_result = calc_response.data["tool_results"][0]
    assert tool_result["tool_id"] == "calculator", f"错误的工具ID: {tool_result['tool_id']}"
    assert tool_result["result"]["result"] == 8, f"计算结果错误: {tool_result['result']}"
    
    # 验证监控正确记录了事件
    monitor.info(
        "Calculator test completed successfully",
        component=ServiceComponent.TEST,
        event_type=EventType.SYSTEM,
        test_name="test_calculator_tool_workflow",
        agent_id=str(agent_id),
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_weather_tool_workflow(setup_services):
    """测试包含天气工具调用的完整工作流。...."""
    # 设置
    services = setup_services
    monitor = services["monitor"]
    model_service = services["model_service"]
    tool_service = services["tool_service"]
    agent_service = services["agent_service"]

    # 1. 重用已注册的模型和工具
    # 2. 创建新的代理
    agent_data = load_json_data("agent_config.json")
    agent_data["name"] = "Weather Assistant"  # 修改名称以区分
    agent_config = AgentConfig.model_validate(agent_data)
    agent_response = await agent_service.create_agent(agent_config)
    assert agent_response.success, f"代理创建失败: {agent_response.error}"
    agent_id = agent_response.data.agent_id

    # 3. 执行天气工具调用流程
    with track_performance("weather_workflow", ServiceComponent.AGENT_CORE) as span:
        # 3.1 发送包含天气工具指令的消息
        weather_message = "Please use the weather tool to check the weather in Shanghai."  # noqa: E501
        weather_response = await agent_service.process_message(
            agent_id=agent_id, message=weather_message
        )
        
        # 设置跟踪数据
        span.add_data({
            "agent_id": str(agent_id),
            "message_type": "weather"
        })

    # 验证响应
    assert weather_response.success, f"消息处理失败: {weather_response.error}"
    
    # 验证工具结果
    assert "tool_results" in weather_response.data, "响应中缺少工具结果"
    assert len(weather_response.data["tool_results"]) > 0, "没有执行天气工具"
    
    # 验证具体结果
    tool_result = weather_response.data["tool_results"][0]
    assert tool_result["tool_id"] == "weather", f"错误的工具ID: {tool_result['tool_id']}"
    assert tool_result["result"]["location"] == "Shanghai", f"地点错误: {tool_result['result']['location']}"  # noqa: E501
    assert "temperature" in tool_result["result"], "缺少温度信息"
    
    # 验证监控正确记录了事件
    monitor.info(
        "Weather test completed successfully",
        component=ServiceComponent.TEST,
        event_type=EventType.SYSTEM,
        test_name="test_weather_tool_workflow",
        agent_id=str(agent_id),
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_conversation_workflow(setup_services):
    """测试普通对话工作流（不使用工具）。...."""
    # 设置
    services = setup_services
    monitor = services["monitor"]
    agent_service = services["agent_service"]

    # 创建新的代理
    agent_data = load_json_data("agent_config.json")
    agent_data["name"] = "Chat Assistant"  # 修改名称以区分
    agent_config = AgentConfig.model_validate(agent_data)
    agent_response = await agent_service.create_agent(agent_config)
    assert agent_response.success, f"代理创建失败: {agent_response.error}"
    agent_id = agent_response.data.agent_id

    # 执行普通对话流程
    conversation_id = uuid.uuid4()
    
    with track_performance("conversation_workflow", ServiceComponent.AGENT_CORE) as span:  # noqa: E501
        # 发送普通对话消息
        chat_message = "Hello, how are you today?"
        chat_response = await agent_service.process_message(
            agent_id=agent_id, 
            message=chat_message,
            conversation_id=conversation_id
        )
        
        # 设置跟踪数据
        span.add_data({
            "agent_id": str(agent_id),
            "conversation_id": str(conversation_id),
            "message_type": "chat"
        })

    # 验证响应
    assert chat_response.success, f"消息处理失败: {chat_response.error}"
    
    # 验证没有工具调用
    assert "tool_results" in chat_response.data, "响应中缺少工具结果字段"
    assert len(chat_response.data["tool_results"]) == 0, "不应该执行任何工具"
    
    # 验证有消息内容
    assert "message" in chat_response.data, "响应中缺少消息内容"
    assert chat_response.data["message"], "消息内容为空"
    
    # 验证监控正确记录了事件
    monitor.info(
        "Conversation test completed successfully",
        component=ServiceComponent.TEST,
        event_type=EventType.SYSTEM,
        test_name="test_conversation_workflow",
        agent_id=str(agent_id),
        conversation_id=str(conversation_id),
    )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize(
    "message,expected_tool,expected_result",
    [
        ("Add 10 and 20 using the calculator", "calculator", 30),
        ("Multiply 5 and 6 using the calculator", "calculator", 30),
        ("What's the weather in Beijing?", "weather", "Beijing"),
    ],
)
async def test_parametrized_workflows(setup_services, message, expected_tool, expected_result):  # noqa: E501
    """参数化测试不同工具调用场景。...."""
    # 设置
    services = setup_services
    agent_service = services["agent_service"]
    model_service = services["model_service"]
    
    # 为参数化测试准备自定义响应模板
    if "calculator" in message.lower():
        if "add" in message.lower():
            operation = "add"
            values = [int(x) for x in message.lower().split() if x.isdigit()]
            a, b = values if len(values) >= 2 else (10, 20)  # 默认值
        elif "multiply" in message.lower():
            operation = "multiply"
            values = [int(x) for x in message.lower().split() if x.isdigit()]
            a, b = values if len(values) >= 2 else (5, 6)  # 默认值
        else:
            operation = "add"
            a, b = 1, 1
            
        model_service.add_response_template(
            f"custom_{operation}", 
            {
                "content": f"I'll help you {operation} those numbers.",
                "tool_calls": [
                    {
                        "tool_id": "calculator",
                        "parameters": {"operation": operation, "a": a, "b": b},
                    }
                ],
            }
        )
    elif "weather" in message.lower():
        location = "Beijing"
        if "in" in message.lower():
            parts = message.lower().split("in")
            if len(parts) > 1:
                location_part = parts[1].strip().split()
                if location_part:
                    location = location_part[0].strip("?.,!")
        
        model_service.add_response_template(
            "custom_weather", 
            {
                "content": f"I'll check the weather in {location}.",
                "tool_calls": [
                    {"tool_id": "weather", "parameters": {"location": location}}
                ],
            }
        )
    
    # 创建代理
    agent_data = load_json_data("agent_config.json")
    agent_data["name"] = f"Param Test Agent-{expected_tool}"  # 区分不同测试
    agent_config = AgentConfig.model_validate(agent_data)
    agent_response = await agent_service.create_agent(agent_config)
    assert agent_response.success, f"代理创建失败: {agent_response.error}"
    agent_id = agent_response.data.agent_id
    
    # 执行消息处理
    response = await agent_service.process_message(agent_id=agent_id, message=message)
    
    # 验证响应
    assert response.success, f"消息处理失败: {response.error}"
    assert "tool_results" in response.data, "响应中缺少工具结果"
    assert len(response.data["tool_results"]) > 0, f"没有执行{expected_tool}工具"
    
    # 验证工具和结果
    tool_result = response.data["tool_results"][0]
    assert tool_result["tool_id"] == expected_tool, f"错误的工具ID: {tool_result['tool_id']}"
    
    if expected_tool == "calculator":
        assert tool_result["result"]["result"] == expected_result, f"计算结果错误: {tool_result['result']}"  # noqa: E501
    elif expected_tool == "weather":
        assert tool_result["result"]["location"] == expected_result, f"地点错误: {tool_result['result']['location']}"  # noqa: E501
