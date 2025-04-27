"""
Monitoring contracts for the AgentForge platform.
"""

from .monitor_interface import MonitorInterface
from .monitor_types import LogLevel, ServiceComponent, EventType, MonitorEvent
from .monitor_models import (
    MetricValue,
    Metric,
    ResourceUsage,
    ServiceHealthStatus,
    TraceContext,
    AlertConfig,
    AlertInstance,
    LogConfig,
)

# Import implementations
from .implementations.logfire_client import LogFireClient
from .implementations.logfire_config import LogFireConfig

# Import utilities
from .utils.logger_utils import (
    configure_monitor,
    get_monitor,
    with_monitoring,
    track_performance,
    log_api_call,
)
from .utils.tracing_utils import (
    trace_method,
    trace_async_method,
    create_trace_context,
    get_current_trace,
)

# Import setup function
from .setup import setup_from_env

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
