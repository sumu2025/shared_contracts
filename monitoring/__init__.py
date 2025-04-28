"""Monitoring contracts for the AgentForge platform...."""

# Import implementations
from .implementations.logfire_client import LogFireClient
from .implementations.logfire_config import LogFireConfig
from .monitor_interface import MonitorInterface
from .monitor_models import (
    AlertConfig,
    AlertInstance,
    LogConfig,
    Metric,
    MetricValue,
    ResourceUsage,
    ServiceHealthStatus,
    TraceContext,
)
from .monitor_types import EventType, LogLevel, MonitorEvent, ServiceComponent

# Import setup function
from .setup import setup_from_env

# Import utilities
from .utils.logger_utils import (
    configure_monitor,
    get_monitor,
    log_api_call,
    track_performance,
    with_monitoring,
)
from .utils.tracing_utils import (
    create_trace_context,
    get_current_trace,
    trace_async_method,
    trace_method,
)

__all__ = [
    # Core interfaces and types
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
    # Implementations
    "LogFireClient",
    "LogFireConfig",
    # Utilities
    "configure_monitor",
    "get_monitor",
    "with_monitoring",
    "track_performance",
    "log_api_call",
    "trace_method",
    "trace_async_method",
    "create_trace_context",
    "get_current_trace",
    # Setup helpers
    "setup_from_env",
]
