"""
Monitoring contracts for the AgentForge platform.

This module re-exports monitoring interfaces and models from the shared_contracts package.
"""  # noqa: E501

from shared_contracts.monitoring import (  # 核心接口和类型; 实现; 工具函数
    AlertConfig,
    AlertInstance,
    EventType,
    LogConfig,
    LogFireClient,
    LogFireConfig,
    LogLevel,
    Metric,
    MetricValue,
    MonitorEvent,
    MonitorInterface,
    ResourceUsage,
    ServiceComponent,
    ServiceHealthStatus,
    TraceContext,
    configure_monitor,
    create_trace_context,
    get_current_trace,
    get_monitor,
    log_api_call,
    trace_async_method,
    trace_method,
    track_performance,
    with_monitoring,
)

__all__ = [
    # 核心接口和类型
    "MonitorInterface",
    "LogLevel",
    "ServiceComponent",
    "EventType",
    "MonitorEvent",
    "MetricValue",
    "Metric",
    "ResourceUsage",
    "ServiceHealthStatus",
    "TraceContext",
    "AlertConfig",
    "AlertInstance",
    "LogConfig",
    # 实现
    "LogFireClient",
    "LogFireConfig",
    # 工具函数
    "configure_monitor",
    "get_monitor",
    "with_monitoring",
    "track_performance",
    "log_api_call",
    "trace_method",
    "trace_async_method",
    "create_trace_context",
    "get_current_trace",
]
