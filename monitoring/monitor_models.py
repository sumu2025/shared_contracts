"""
Monitoring data models.
"""

from typing import Dict, Any, List, Optional, Union, Literal
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict

from ..core.models.base_models import BaseModel as ContractBaseModel
from .monitor_types import LogLevel, ServiceComponent, EventType


class MetricValue(ContractBaseModel):
    """Model for a metric value."""
    
    value: float = Field(..., description="Metric value")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp")
    tags: Dict[str, str] = Field(default_factory=dict, description="Metric tags")


class Metric(ContractBaseModel):
    """Model for a metric."""
    
    name: str = Field(..., description="Metric name")
    description: str = Field(..., description="Metric description")
    unit: str = Field(..., description="Metric unit")
    metric_type: Literal["counter", "gauge", "histogram", "summary"] = Field(
        ..., description="Metric type"
    )
    values: List[MetricValue] = Field(default_factory=list, description="Metric values")


class ResourceUsage(ContractBaseModel):
    """Model for resource usage metrics."""
    
    cpu_percent: float = Field(..., description="CPU usage percentage")
    memory_percent: float = Field(..., description="Memory usage percentage")
    memory_rss: int = Field(..., description="Resident set size in bytes")
    disk_io_read: int = Field(..., description="Disk read in bytes")
    disk_io_write: int = Field(..., description="Disk write in bytes")
    network_recv: int = Field(..., description="Network bytes received")
    network_sent: int = Field(..., description="Network bytes sent")
    open_file_descriptors: int = Field(..., description="Number of open file descriptors")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp")


class ServiceHealthStatus(ContractBaseModel):
    """Model for service health status."""
    
    service_id: str = Field(..., description="Service identifier")
    service_name: str = Field(..., description="Service name")
    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        ..., description="Health status"
    )
    message: str = Field(..., description="Status message")
    version: str = Field(..., description="Service version")
    uptime_seconds: int = Field(..., description="Uptime in seconds")
    resource_usage: Optional[ResourceUsage] = Field(None, description="Resource usage")
    checks: Dict[str, bool] = Field(default_factory=dict, description="Health checks")
    last_updated: datetime = Field(
        default_factory=datetime.utcnow, description="Last updated timestamp"
    )


class TraceContext(ContractBaseModel):
    """Model for distributed tracing context."""
    
    trace_id: UUID = Field(default_factory=uuid4, description="Trace identifier")
    parent_span_id: Optional[UUID] = Field(None, description="Parent span identifier")
    span_id: UUID = Field(default_factory=uuid4, description="Span identifier")
    service_name: str = Field(..., description="Service name")
    operation_name: str = Field(..., description="Operation name")
    start_time: datetime = Field(
        default_factory=datetime.utcnow, description="Start timestamp"
    )
    end_time: Optional[datetime] = Field(None, description="End timestamp")
    duration_ms: Optional[float] = Field(None, description="Duration in milliseconds")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Span attributes")
    events: List[Dict[str, Any]] = Field(default_factory=list, description="Span events")
    status: Literal["ok", "error", "unset"] = Field("unset", description="Span status")
    error_message: Optional[str] = Field(None, description="Error message if status is error")


class AlertConfig(ContractBaseModel):
    """Model for alert configuration."""
    
    alert_id: UUID = Field(default_factory=uuid4, description="Alert identifier")
    name: str = Field(..., description="Alert name")
    description: str = Field(..., description="Alert description")
    component: ServiceComponent = Field(..., description="Service component")
    condition: str = Field(..., description="Alert condition expression")
    severity: LogLevel = Field(..., description="Alert severity")
    notification_channels: List[str] = Field(
        default_factory=list, description="Notification channels"
    )
    cooldown_seconds: int = Field(
        default=300, description="Cooldown period in seconds"
    )
    enabled: bool = Field(default=True, description="Whether this alert is enabled")
    tags: List[str] = Field(default_factory=list, description="Alert tags")


class AlertInstance(ContractBaseModel):
    """Model for an alert instance."""
    
    alert_id: UUID = Field(..., description="Alert identifier")
    instance_id: UUID = Field(default_factory=uuid4, description="Alert instance identifier")
    triggered_at: datetime = Field(
        default_factory=datetime.utcnow, description="Triggered timestamp"
    )
    resolved_at: Optional[datetime] = Field(None, description="Resolved timestamp")
    status: Literal["active", "acknowledged", "resolved"] = Field(
        "active", description="Alert status"
    )
    value: float = Field(..., description="Value that triggered the alert")
    message: str = Field(..., description="Alert message")
    component: ServiceComponent = Field(..., description="Service component")
    severity: LogLevel = Field(..., description="Alert severity")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Alert metadata")
    acknowledged_by: Optional[str] = Field(None, description="User who acknowledged the alert")
    acknowledged_at: Optional[datetime] = Field(None, description="Acknowledged timestamp")
    resolution_message: Optional[str] = Field(None, description="Resolution message")


class LogConfig(ContractBaseModel):
    """Model for log configuration."""
    
    service_name: str = Field(..., description="Service name")
    environment: str = Field(default="development", description="Deployment environment")
    min_level: LogLevel = Field(default=LogLevel.INFO, description="Minimum log level")
    include_components: Optional[List[ServiceComponent]] = Field(
        None, description="Components to include (None means all)"
    )
    exclude_components: List[ServiceComponent] = Field(
        default_factory=list, description="Components to exclude"
    )
    include_event_types: Optional[List[EventType]] = Field(
        None, description="Event types to include (None means all)"
    )
    exclude_event_types: List[EventType] = Field(
        default_factory=list, description="Event types to exclude"
    )
    format: Literal["json", "text"] = Field(default="json", description="Log format")
    output: Literal["stdout", "file", "both"] = Field(
        default="stdout", description="Log output destination"
    )
    file_path: Optional[str] = Field(None, description="Log file path when output is file or both")
    max_file_size_mb: int = Field(
        default=10, description="Maximum log file size in MB when output is file or both"
    )
    max_files: int = Field(
        default=5, description="Maximum number of log files when output is file or both"
    )
    additional_fields: Dict[str, Any] = Field(
        default_factory=dict, description="Additional fields to include in all logs"
    )
