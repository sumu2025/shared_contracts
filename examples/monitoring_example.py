"""
示例：使用监控客户端跟踪服务活动

本示例展示如何配置和使用LogFire监控客户端来记录服务活动、性能指标和分布式追踪。
"""

import asyncio
import time
import uuid
from datetime import datetime

from agentforge_contracts.monitoring import (
    EventType,
    LogFireClient,
    LogFireConfig,
    LogLevel,
    ServiceComponent,
    configure_monitor,
    create_trace_context,
    get_monitor,
    trace_method,
    track_performance,
    with_monitoring,
)


# 配置监控客户端
def setup_monitoring():
    """配置并初始化监控客户端"""
    # 通常从环境变量或配置文件中获取这些值
    api_key = "your-logfire-api-key"
    project_id = "your-logfire-project-id"

    # 配置监控
    monitor = configure_monitor(
        service_name="example-service",
        api_key=api_key,
        project_id=project_id,
        environment="development",
        min_log_level=LogLevel.DEBUG,
    )

    return monitor


# 使用装饰器进行监控
@with_monitoring(component=ServiceComponent.AGENT_CORE)
def process_request(request_id, data):
    """处理请求的示例函数"""
    # 获取监控器
    monitor = get_monitor()

    # 记录请求信息
    monitor.info(
        message=f"处理请求 {request_id}",
        component=ServiceComponent.AGENT_CORE,
        event_type=EventType.REQUEST,
        request_id=request_id,
    )

    # 模拟处理
    time.sleep(0.1)
    result = {"request_id": request_id, "processed": True, "items": len(data)}

    # 记录响应信息
    monitor.info(
        message=f"请求 {request_id} 处理完成",
        component=ServiceComponent.AGENT_CORE,
        event_type=EventType.RESPONSE,
        items_processed=len(data),
    )

    return result


# 使用上下文管理器进行性能跟踪
def analyze_data(data):
    """数据分析的示例函数"""
    with track_performance("data_analysis", ServiceComponent.AGENT_CORE) as span:
        # 模拟数据分析
        time.sleep(0.2)
        result = sum(data)

        # 添加额外信息
        span.add_data({"data_points": len(data), "result": result})

        return result


# 在类中使用追踪装饰器
class DataService:
    def __init__(self):
        self.data = {}

    @trace_method(component=ServiceComponent.MODEL_SERVICE)
    def store_data(self, key, value):
        """存储数据"""
        self.data[key] = value
        return {"status": "success", "key": key}

    @trace_method(component=ServiceComponent.MODEL_SERVICE)
    def get_data(self, key):
        """获取数据"""
        if key in self.data:
            return {"status": "success", "key": key, "value": self.data[key]}
        return {"status": "error", "key": key, "message": "Key not found"}


# 异步示例
async def async_example():
    """异步操作的示例"""
    # 获取监控器
    monitor = get_monitor()

    # 创建追踪上下文
    with create_trace_context("async_operation", ServiceComponent.AGENT_CORE) as span:
        # 记录开始信息
        monitor.info(
            message="异步操作开始",
            component=ServiceComponent.AGENT_CORE,
            event_type=EventType.LIFECYCLE,
        )

        # 模拟异步操作
        await asyncio.sleep(0.3)

        # 更新追踪数据
        span.attributes["operation_type"] = "simulation"

        # 记录完成信息
        monitor.info(
            message="异步操作完成",
            component=ServiceComponent.AGENT_CORE,
            event_type=EventType.LIFECYCLE,
        )


# 记录API调用
def call_external_api(api_name, params):
    """调用外部API的示例函数"""
    monitor = get_monitor()

    start_time = time.time()
    try:
        # 模拟API调用
        time.sleep(0.2)
        response = {"status": "success", "data": {"result": "Some result"}}
        status_code = 200

        # 记录API调用
        monitor.record_api_call(
            api_name=api_name,
            status_code=status_code,
            duration_ms=(time.time() - start_time) * 1000,
            component=ServiceComponent.AGENT_CORE,
            request_data=params,
            response_data=response,
        )

        return response
    except Exception as e:
        # 记录错误
        monitor.record_api_call(
            api_name=api_name,
            status_code=500,
            duration_ms=(time.time() - start_time) * 1000,
            component=ServiceComponent.AGENT_CORE,
            request_data=params,
            error=str(e),
        )
        raise


# 主示例函数
async def main():
    # 设置监控
    monitor = setup_monitoring()

    try:
        # 记录服务启动
        monitor.info(
            message="服务启动",
            component=ServiceComponent.SYSTEM,
            event_type=EventType.LIFECYCLE,
            version="1.0.0",
        )

        # 处理请求
        request_id = str(uuid.uuid4())
        data = [1, 2, 3, 4, 5]
        result = process_request(request_id, data)

        # 分析数据
        analysis_result = analyze_data(data)

        # 使用数据服务
        service = DataService()
        service.store_data("key1", "value1")
        retrieved = service.get_data("key1")

        # 调用API
        api_result = call_external_api("example-api", {"param": "value"})

        # 运行异步示例
        await async_example()

        # 记录一些指标
        monitor.record_metric(
            metric_name="processed_items",
            value=len(data),
            tags={"service": "example"},
        )

        # 记录服务停止
        monitor.info(
            message="服务正常停止",
            component=ServiceComponent.SYSTEM,
            event_type=EventType.LIFECYCLE,
        )

        # 刷新和关闭
        monitor.flush()
        monitor.shutdown()

    except Exception as e:
        # 记录错误
        monitor.critical(
            message=f"服务发生错误: {str(e)}",
            component=ServiceComponent.SYSTEM,
            event_type=EventType.EXCEPTION,
            error=str(e),
            error_type=type(e).__name__,
        )

        # 强制刷新和关闭
        monitor.flush()
        monitor.shutdown()
        raise


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
