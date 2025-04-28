"""性能测试模块，用于CI/CD流程中的性能监控。"""

import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import pytest
from shared_contracts.monitoring.monitor_types import ServiceComponent
from shared_contracts.monitoring.utils.logger_utils import track_performance


class PerformanceTest:
    """性能测试基类，用于测量函数执行时间和资源使用。"""

    def __init__(
        self,
        name: str,
        threshold_ms: float = 100.0,
        iterations: int = 1000,
        warmup_iterations: int = 100,
    ):
        """
        初始化性能测试。

        Args:
            name: 测试名称
            threshold_ms: 性能阈值（毫秒），超过该值视为失败
            iterations: 测试迭代次数
            warmup_iterations: 预热迭代次数，不计入性能统计
        """
        self.name = name
        self.threshold_ms = threshold_ms
        self.iterations = iterations
        self.warmup_iterations = warmup_iterations
        self.results: List[float] = []

    def run(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        运行性能测试。

        Args:
            func: 要测试的函数
            *args: 传递给函数的位置参数
            **kwargs: 传递给函数的关键字参数

        Returns:
            测试结果统计
        """
        # 预热阶段
        for _ in range(self.warmup_iterations):
            func(*args, **kwargs)

        # 测试阶段
        self.results = []
        for _ in range(self.iterations):
            start_time = time.time()
            func(*args, **kwargs)
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            self.results.append(duration_ms)

        return self.get_stats()

    def run_with_monitor(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        使用监控工具运行性能测试。

        Args:
            func: 要测试的函数
            *args: 传递给函数的位置参数
            **kwargs: 传递给函数的关键字参数

        Returns:
            测试结果统计
        """
        # 预热阶段
        for _ in range(self.warmup_iterations):
            func(*args, **kwargs)

        # 测试阶段
        self.results = []
        for _ in range(self.iterations):
            with track_performance(
                self.name, ServiceComponent.SYSTEM
            ) as span:
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                self.results.append(duration_ms)
                span.add_data({"iteration_duration_ms": duration_ms})
                
        return self.get_stats()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取测试结果统计。

        Returns:
            包含统计信息的字典
        """
        if not self.results:
            return {
                "name": self.name,
                "min": 0,
                "max": 0,
                "avg": 0,
                "median": 0,
                "p95": 0,
                "p99": 0,
                "iterations": 0,
                "passed": False,
            }

        sorted_results = sorted(self.results)
        n = len(sorted_results)
        p95_idx = int(n * 0.95)
        p99_idx = int(n * 0.99)

        stats = {
            "name": self.name,
            "min": round(min(self.results), 3),
            "max": round(max(self.results), 3),
            "avg": round(sum(self.results) / n, 3),
            "median": round(sorted_results[n // 2], 3),
            "p95": round(sorted_results[p95_idx], 3),
            "p99": round(sorted_results[p99_idx], 3),
            "iterations": n,
            "passed": self.avg_duration() <= self.threshold_ms,
        }

        return stats

    def avg_duration(self) -> float:
        """
        获取平均执行时间。

        Returns:
            平均执行时间（毫秒）
        """
        if not self.results:
            return 0.0
        return sum(self.results) / len(self.results)

    def __str__(self) -> str:
        """
        测试结果的字符串表示。

        Returns:
            格式化的测试结果字符串
        """
        stats = self.get_stats()
        result = "通过" if stats["passed"] else "失败"
        return (
            f"性能测试 '{self.name}' - {result}\n"
            f"  平均: {stats['avg']:.3f}ms (阈值: {self.threshold_ms:.3f}ms)\n"
            f"  最小/最大: {stats['min']:.3f}ms / {stats['max']:.3f}ms\n"
            f"  中位数: {stats['median']:.3f}ms\n"
            f"  95/99百分位: {stats['p95']:.3f}ms / {stats['p99']:.3f}ms"
        )


# 测试用例
def test_logfire_client_performance():
    """测试LogFireClient的性能。"""
    from shared_contracts.monitoring.implementations.logfire_client import LogFireClient
    from shared_contracts.monitoring.implementations.logfire_config import LogFireConfig
    from shared_contracts.monitoring.monitor_types import (
        EventType,
        LogLevel,
        ServiceComponent,
    )

    # 创建测试客户端
    config = LogFireConfig(
        api_key="test-key",
        service_name="performance-test",
        environment="test",
        batch_size=100,
        flush_interval_seconds=60,  # 不自动刷新
    )
    client = LogFireClient(config)

    # 1. 测试日志记录性能
    def log_message():
        client.log(
            message="Test message",
            level=LogLevel.INFO,
            component=ServiceComponent.SYSTEM,
            event_type=EventType.SYSTEM,
            data={"test": "value", "number": 123},
        )

    log_test = PerformanceTest(
        name="LogFireClient.log",
        threshold_ms=0.5,  # 0.5毫秒
        iterations=10000,
    )
    log_stats = log_test.run(log_message)
    print(log_test)
    assert log_stats["passed"], f"日志性能测试失败: {log_stats['avg']}ms > {log_test.threshold_ms}ms"

    # 2. 测试span创建性能
    def create_span():
        span = client.start_span(
            name="test-span",
            component=ServiceComponent.SYSTEM,
            event_type=EventType.SYSTEM,
            data={"test": "value"},
        )
        client.end_span(span)

    span_test = PerformanceTest(
        name="LogFireClient.start_span/end_span",
        threshold_ms=1.0,  # 1毫秒
        iterations=5000,
    )
    span_stats = span_test.run(create_span)
    print(span_test)
    assert span_stats["passed"], f"Span性能测试失败: {span_stats['avg']}ms > {span_test.threshold_ms}ms"

    # 3. 批量测试
    def log_batch(count=10):
        for i in range(count):
            client.log(
                message=f"Batch test message {i}",
                level=LogLevel.INFO,
                component=ServiceComponent.SYSTEM,
                event_type=EventType.SYSTEM,
                data={"index": i},
            )

    batch_test = PerformanceTest(
        name="LogFireClient.batch_log",
        threshold_ms=5.0,  # 5毫秒
        iterations=1000,
    )
    batch_stats = batch_test.run(log_batch)
    print(batch_test)
    assert batch_stats["passed"], f"批量日志性能测试失败: {batch_stats['avg']}ms > {batch_test.threshold_ms}ms"

    # 清理
    client.log_buffer.clear()
    client.metric_buffer.clear()


def test_validation_performance():
    """测试验证工具的性能。"""
    from pydantic import BaseModel, Field
    
    from shared_contracts.utils.validation import (
        validate_enum_value,
        validate_model,
        validate_uuid,
    )
    from shared_contracts.monitoring.monitor_types import ServiceComponent

    # 1. 测试模型验证性能
    class TestModel(BaseModel):
        name: str = Field(..., min_length=2, max_length=50)
        age: int = Field(..., ge=0, le=150)
        emails: List[str] = Field(default_factory=list)
        settings: Dict[str, Any] = Field(default_factory=dict)

    test_data = {
        "name": "Test User",
        "age": 30,
        "emails": ["user@example.com", "backup@example.com"],
        "settings": {
            "theme": "dark",
            "notifications": True,
            "preferences": {
                "language": "zh-CN",
                "timezone": "Asia/Shanghai",
            },
        },
    }

    def validate_test_model():
        result = validate_model(TestModel, test_data)
        assert result.valid, f"验证应该成功: {result.errors}"

    model_test = PerformanceTest(
        name="validate_model",
        threshold_ms=1.0,  # 1毫秒
        iterations=10000,
    )
    model_stats = model_test.run(validate_test_model)
    print(model_test)
    assert model_stats["passed"], f"模型验证性能测试失败: {model_stats['avg']}ms > {model_test.threshold_ms}ms"

    # 2. 测试枚举验证性能
    def validate_enum():
        result = validate_enum_value("SYSTEM", ServiceComponent)
        assert result, "枚举验证应该成功"

    enum_test = PerformanceTest(
        name="validate_enum_value",
        threshold_ms=0.1,  # 0.1毫秒
        iterations=10000,
    )
    enum_stats = enum_test.run(validate_enum)
    print(enum_test)
    assert enum_stats["passed"], f"枚举验证性能测试失败: {enum_stats['avg']}ms > {enum_test.threshold_ms}ms"

    # 3. 测试UUID验证性能
    def validate_uuid_test():
        result = validate_uuid("550e8400-e29b-41d4-a716-446655440000")
        assert result, "UUID验证应该成功"

    uuid_test = PerformanceTest(
        name="validate_uuid",
        threshold_ms=0.1,  # 0.1毫秒
        iterations=10000,
    )
    uuid_stats = uuid_test.run(validate_uuid_test)
    print(uuid_test)
    assert uuid_stats["passed"], f"UUID验证性能测试失败: {uuid_stats['avg']}ms > {uuid_test.threshold_ms}ms"


if __name__ == "__main__":
    test_logfire_client_performance()
    test_validation_performance()
    print("所有性能测试通过!")
