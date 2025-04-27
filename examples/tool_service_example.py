"""
示例：工具服务实现

本示例展示如何实现ToolServiceInterface接口，创建和使用自定义工具。
"""

import asyncio
import logging
import math
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List

# 模拟HTTP客户端

# 导入shared_contracts组件
from agentforge_contracts.core.interfaces.tool_interface import ToolServiceInterface
from agentforge_contracts.core.models.base_models import BaseResponse
from agentforge_contracts.core.models.tool_models import (
    ToolDefinition,
    ToolParameter,
    ToolParameters,
    ToolParameterType,
    ToolResult,
    ToolResultStatus,
)
from agentforge_contracts.monitoring import (
    EventType,
    ServiceComponent,
    configure_monitor,
    track_performance,
    with_monitoring,
)
from agentforge_contracts.utils.validation import validate_parameters

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("tool_service_example")

# 配置监控
monitor = configure_monitor(
    service_name="tool-service-example",
    api_key=os.environ.get("LOGFIRE_API_KEY", "dummy-key"),
    project_id=os.environ.get("LOGFIRE_PROJECT_ID", "dummy-project"),
    environment="development",
)


# ====== 工具服务实现 ======


class ToolService(ToolServiceInterface):
    """工具服务实现。"""

    def __init__(self):
        self.tools = {}  # 存储工具定义
        self.tool_executors = {}  # 存储工具执行器

        # 注册内置工具
        self._register_built_in_tools()

    def _register_built_in_tools(self):
        """注册内置工具。"""
        # 注册计算器工具
        self._register_calculator_tool()

        # 注册天气查询工具
        self._register_weather_tool()

        # 注册搜索工具
        self._register_search_tool()

    def _register_calculator_tool(self):
        """注册计算器工具。"""
        # 创建工具定义
        calculator_tool = ToolDefinition(
            tool_id="calculator",
            name="Calculator",
            description="A tool for performing mathematical calculations",
            version="1.0.0",
            parameters=ToolParameters(
                parameters={
                    "operation": ToolParameter(
                        name="operation",
                        description="Mathematical operation to perform",
                        type=ToolParameterType.STRING,
                        enum=[
                            "add",
                            "subtract",
                            "multiply",
                            "divide",
                            "power",
                            "sqrt",
                            "sin",
                            "cos",
                            "tan",
                        ],
                        required=True,
                    ),
                    "a": ToolParameter(
                        name="a",
                        description="First number",
                        type=ToolParameterType.NUMBER,
                        required=True,
                    ),
                    "b": ToolParameter(
                        name="b",
                        description="Second number (not required for sqrt, sin, cos, tan)",  # noqa: E501
                        type=ToolParameterType.NUMBER,
                        required=False,
                    ),
                }
            ),
        )

        # 注册工具
        self.tools[calculator_tool.tool_id] = calculator_tool
        self.tool_executors[calculator_tool.tool_id] = self._execute_calculator

    def _register_weather_tool(self):
        """注册天气查询工具。"""
        # 创建工具定义
        weather_tool = ToolDefinition(
            tool_id="weather",
            name="Weather Tool",
            description="A tool for getting current weather information for a location",
            version="1.0.0",
            parameters=ToolParameters(
                parameters={
                    "location": ToolParameter(
                        name="location",
                        description="City or location name",
                        type=ToolParameterType.STRING,
                        required=True,
                    ),
                    "units": ToolParameter(
                        name="units",
                        description="Temperature units",
                        type=ToolParameterType.STRING,
                        enum=["celsius", "fahrenheit"],
                        default="celsius",
                        required=False,
                    ),
                }
            ),
        )

        # 注册工具
        self.tools[weather_tool.tool_id] = weather_tool
        self.tool_executors[weather_tool.tool_id] = self._execute_weather

    def _register_search_tool(self):
        """注册搜索工具。"""
        # 创建工具定义
        search_tool = ToolDefinition(
            tool_id="search",
            name="Web Search",
            description="A tool for searching the web",
            version="1.0.0",
            parameters=ToolParameters(
                parameters={
                    "query": ToolParameter(
                        name="query",
                        description="Search query",
                        type=ToolParameterType.STRING,
                        required=True,
                    ),
                    "num_results": ToolParameter(
                        name="num_results",
                        description="Number of results to return",
                        type=ToolParameterType.INTEGER,
                        default=3,
                        required=False,
                    ),
                }
            ),
        )

        # 注册工具
        self.tools[search_tool.tool_id] = search_tool
        self.tool_executors[search_tool.tool_id] = self._execute_search

    @with_monitoring(component=ServiceComponent.TOOL_SERVICE)
    async def register_tool(
        self, definition: ToolDefinition
    ) -> BaseResponse[ToolDefinition]:
        """注册新工具。"""
        # 检查工具ID是否已存在
        if definition.tool_id in self.tools:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Tool with ID '{definition.tool_id}' already exists",
            )

        # 存储工具定义
        self.tools[definition.tool_id] = definition

        # 记录工具注册
        monitor.info(
            message=f"Tool registered: {definition.tool_id}",
            component=ServiceComponent.TOOL_SERVICE,
            event_type=EventType.SYSTEM,
            tool_id=definition.tool_id,
            version=definition.version,
        )

        return BaseResponse(request_id=uuid.uuid4(), success=True, data=definition)

    @with_monitoring(component=ServiceComponent.TOOL_SERVICE)
    async def get_tool(self, tool_id: str) -> BaseResponse[ToolDefinition]:
        """获取工具定义。"""
        if tool_id not in self.tools:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Tool not found: {tool_id}",
            )

        return BaseResponse(
            request_id=uuid.uuid4(), success=True, data=self.tools[tool_id]
        )

    @with_monitoring(component=ServiceComponent.TOOL_SERVICE)
    async def list_tools(self) -> BaseResponse[List[ToolDefinition]]:
        """列出所有工具。"""
        return BaseResponse(
            request_id=uuid.uuid4(), success=True, data=list(self.tools.values())
        )

    @with_monitoring(component=ServiceComponent.TOOL_SERVICE)
    async def execute_tool(
        self, tool_id: str, parameters: Dict[str, Any], stream: bool = False
    ) -> BaseResponse[ToolResult]:
        """执行工具。"""
        # 检查工具是否存在
        if tool_id not in self.tools:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Tool not found: {tool_id}",
            )

        tool = self.tools[tool_id]
        request_id = uuid.uuid4()

        # 记录工具执行
        monitor.info(
            message=f"Executing tool: {tool_id}",
            component=ServiceComponent.TOOL_SERVICE,
            event_type=EventType.REQUEST,
            tool_id=tool_id,
            parameters=str(parameters),
            request_id=str(request_id),
        )

        try:
            # 验证参数
            validation_errors = validate_parameters(parameters, tool.parameters)
            if validation_errors:
                error_message = f"Parameter validation failed: {validation_errors}"

                # 记录验证错误
                monitor.warning(
                    message=error_message,
                    component=ServiceComponent.TOOL_SERVICE,
                    event_type=EventType.VALIDATION,
                    tool_id=tool_id,
                    parameters=str(parameters),
                    request_id=str(request_id),
                )

                return BaseResponse(
                    request_id=request_id, success=False, error=error_message
                )

            # 执行工具
            if tool_id in self.tool_executors:
                with track_performance(
                    f"tool_execution_{tool_id}", ServiceComponent.TOOL_SERVICE
                ) as span:
                    span.add_data({"tool_id": tool_id, "parameters": parameters})

                    result = await self.tool_executors[tool_id](parameters)

                    span.add_data({"execution_result": result})
            else:
                result = {
                    "message": "Tool executor not found",
                    "tool_id": tool_id,
                    "parameters": parameters,
                }

            # 创建工具结果
            tool_result = ToolResult(
                tool_id=tool_id,
                request_id=request_id,
                status=ToolResultStatus.SUCCESS,
                data=result,
            )

            # 记录成功执行
            monitor.info(
                message=f"Tool execution successful: {tool_id}",
                component=ServiceComponent.TOOL_SERVICE,
                event_type=EventType.RESPONSE,
                tool_id=tool_id,
                request_id=str(request_id),
                result=str(result),
            )

            return BaseResponse(request_id=request_id, success=True, data=tool_result)

        except Exception as e:
            error_message = f"Error executing tool: {str(e)}"

            # 记录执行错误
            monitor.error(
                message=error_message,
                component=ServiceComponent.TOOL_SERVICE,
                event_type=EventType.EXCEPTION,
                tool_id=tool_id,
                parameters=str(parameters),
                error=str(e),
                request_id=str(request_id),
            )

            # 创建错误结果
            tool_result = ToolResult(
                tool_id=tool_id,
                request_id=request_id,
                status=ToolResultStatus.ERROR,
                error=str(e),
            )

            return BaseResponse(
                request_id=request_id,
                success=True,  # 注意成功指的是服务正常处理了请求，即使工具执行失败
                data=tool_result,
            )

    # ====== 工具执行器 ======

    async def _execute_calculator(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行计算器工具。"""
        operation = parameters.get("operation")
        a = float(parameters.get("a", 0))
        b = float(parameters.get("b", 0)) if "b" in parameters else None

        result = None
        error = None

        try:
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    raise ValueError("Division by zero is not allowed")
                result = a / b
            elif operation == "power":
                result = a**b
            elif operation == "sqrt":
                if a < 0:
                    raise ValueError("Cannot calculate square root of negative number")
                result = math.sqrt(a)
            elif operation == "sin":
                result = math.sin(a)
            elif operation == "cos":
                result = math.cos(a)
            elif operation == "tan":
                result = math.tan(a)
            else:
                raise ValueError(f"Unsupported operation: {operation}")
        except Exception as e:
            error = str(e)

        # 构建响应
        response = {"operation": operation, "parameters": {"a": a}}

        if b is not None:
            response["parameters"]["b"] = b

        if error:
            response["error"] = error
        else:
            response["result"] = result

        return response

    async def _execute_weather(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行天气查询工具。"""
        location = parameters.get("location")
        units = parameters.get("units", "celsius")

        # 在实际应用中，这里应该调用真实的天气API
        # 这里使用模拟数据
        await asyncio.sleep(0.5)  # 模拟API调用延迟

        # 模拟不同城市的天气
        weather_data = {
            "new york": {"temperature": 22, "condition": "Sunny", "humidity": 45},
            "london": {"temperature": 18, "condition": "Cloudy", "humidity": 72},
            "tokyo": {"temperature": 25, "condition": "Rainy", "humidity": 80},
            "paris": {"temperature": 20, "condition": "Partly Cloudy", "humidity": 65},
            "sydney": {"temperature": 28, "condition": "Clear", "humidity": 50},
        }

        # 获取天气数据或使用默认值
        location_lower = location.lower()
        weather = weather_data.get(
            location_lower,
            {"temperature": 20, "condition": "Unknown", "humidity": 60},  # 默认温度
        )

        # 单位转换
        temperature = weather["temperature"]
        if units == "fahrenheit":
            temperature = (temperature * 9 / 5) + 32

        return {
            "location": location,
            "units": units,
            "temperature": temperature,
            "condition": weather["condition"],
            "humidity": weather["humidity"],
            "forecast": "This is a simulated weather forecast. In a real application, this would use an actual weather API.",  # noqa: E501
            "timestamp": datetime.now().isoformat(),
        }

    async def _execute_search(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行搜索工具。"""
        query = parameters.get("query")
        num_results = int(parameters.get("num_results", 3))

        # 在实际应用中，这里应该调用真实的搜索API
        # 这里使用模拟数据
        await asyncio.sleep(0.7)  # 模拟API调用延迟

        # 模拟搜索结果
        search_results = [
            {
                "title": f"Search Result 1 for '{query}'",
                "url": f"https://example.com/result1?q={query}",
                "snippet": f"This is a simulated search result for '{query}'. It would contain a brief excerpt of the content.",  # noqa: E501
            },
            {
                "title": f"Search Result 2 for '{query}'",
                "url": f"https://example.com/result2?q={query}",
                "snippet": f"Another simulated result for '{query}'. In a real application, this would be fetched from a search engine API.",  # noqa: E501
            },
            {
                "title": f"Search Result 3 for '{query}'",
                "url": f"https://example.com/result3?q={query}",
                "snippet": f"Third simulated result for '{query}'. The number of results returned is based on the 'num_results' parameter.",  # noqa: E501
            },
            {
                "title": f"Search Result 4 for '{query}'",
                "url": f"https://example.com/result4?q={query}",
                "snippet": f"Fourth simulated result for '{query}'. This result might not be shown if num_results is less than 4.",  # noqa: E501
            },
            {
                "title": f"Search Result 5 for '{query}'",
                "url": f"https://example.com/result5?q={query}",
                "snippet": f"Fifth simulated result for '{query}'. This is the last of our simulated results.",  # noqa: E501
            },
        ]

        # 限制结果数量
        limited_results = search_results[: min(num_results, len(search_results))]

        return {
            "query": query,
            "num_results": len(limited_results),
            "results": limited_results,
            "disclaimer": "These are simulated search results. In a real application, these would be fetched from a search engine API.",  # noqa: E501
        }


# ====== 示例应用 ======


async def run_example():
    """运行工具服务示例。"""
    print("\n==== AgentForge工具服务示例 ====\n")

    # 创建工具服务
    tool_service = ToolService()

    # 注册自定义工具
    print("注册自定义工具...")

    # 创建翻译工具
    translator_tool = ToolDefinition(
        tool_id="translator",
        name="Language Translator",
        description="A tool for translating text between languages",
        version="1.0.0",
        parameters=ToolParameters(
            parameters={
                "text": ToolParameter(
                    name="text",
                    description="Text to translate",
                    type=ToolParameterType.STRING,
                    required=True,
                ),
                "source_lang": ToolParameter(
                    name="source_lang",
                    description="Source language code (e.g., 'en', 'fr', 'zh')",
                    type=ToolParameterType.STRING,
                    required=True,
                ),
                "target_lang": ToolParameter(
                    name="target_lang",
                    description="Target language code (e.g., 'en', 'fr', 'zh')",
                    type=ToolParameterType.STRING,
                    required=True,
                ),
            }
        ),
    )

    # 注册翻译工具
    translator_result = await tool_service.register_tool(translator_tool)

    if translator_result.success:
        print(f"✅ 翻译工具注册成功: {translator_result.data.tool_id}")

        # 添加翻译工具执行器
        async def execute_translator(parameters: Dict[str, Any]) -> Dict[str, Any]:
            """执行翻译工具。"""
            text = parameters.get("text")
            source_lang = parameters.get("source_lang")
            target_lang = parameters.get("target_lang")

            # 模拟翻译，在实际应用中应调用真实的翻译API
            await asyncio.sleep(0.5)

            # 简单的模拟翻译
            translations = {
                ("en", "zh", "hello"): "你好",
                ("en", "zh", "goodbye"): "再见",
                ("en", "fr", "hello"): "bonjour",
                ("en", "fr", "goodbye"): "au revoir",
                ("zh", "en", "你好"): "hello",
                ("zh", "en", "再见"): "goodbye",
                ("fr", "en", "bonjour"): "hello",
                ("fr", "en", "au revoir"): "goodbye",
            }

            # 查找翻译或返回原文
            translation = translations.get(
                (source_lang, target_lang, text.lower()), f"[{text}]"
            )

            return {
                "original_text": text,
                "source_language": source_lang,
                "target_language": target_lang,
                "translated_text": translation,
                "note": "This is a simulated translation. In a real application, this would use an actual translation API.",  # noqa: E501
            }

        tool_service.tool_executors[translator_tool.tool_id] = execute_translator
    else:
        print(f"❌ 翻译工具注册失败: {translator_result.error}")

    # 列出所有可用工具
    print("\n列出所有可用工具...")
    tools_result = await tool_service.list_tools()

    if tools_result.success:
        for tool in tools_result.data:
            print(f"- {tool.name} ({tool.tool_id}): {tool.description}")

    # 执行计算器工具
    print("\n执行计算器工具...")
    calculator_result = await tool_service.execute_tool(
        tool_id="calculator", parameters={"operation": "multiply", "a": 5, "b": 3}
    )

    if calculator_result.success:
        print(f"计算器结果: {calculator_result.data.data}")
    else:
        print(f"计算器执行失败: {calculator_result.error}")

    # 执行天气工具
    print("\n执行天气工具...")
    weather_result = await tool_service.execute_tool(
        tool_id="weather", parameters={"location": "London", "units": "celsius"}
    )

    if weather_result.success:
        print(f"天气结果: {weather_result.data.data}")
    else:
        print(f"天气工具执行失败: {weather_result.error}")

    # 执行翻译工具
    if translator_result.success:
        print("\n执行翻译工具...")
        translation_result = await tool_service.execute_tool(
            tool_id="translator",
            parameters={"text": "hello", "source_lang": "en", "target_lang": "zh"},
        )

        if translation_result.success:
            print(f"翻译结果: {translation_result.data.data}")
        else:
            print(f"翻译工具执行失败: {translation_result.error}")

    # 执行搜索工具
    print("\n执行搜索工具...")
    search_result = await tool_service.execute_tool(
        tool_id="search", parameters={"query": "AgentForge framework", "num_results": 2}
    )

    if search_result.success:
        print(f"搜索结果数量: {search_result.data.data['num_results']}")
        for i, result in enumerate(search_result.data.data["results"]):
            print(f"  {i+1}. {result['title']}")
            print(f"     URL: {result['url']}")
            print(f"     Snippet: {result['snippet'][:50]}...")
    else:
        print(f"搜索工具执行失败: {search_result.error}")


# ====== 主函数 ======

if __name__ == "__main__":
    # 运行示例
    asyncio.run(run_example())
