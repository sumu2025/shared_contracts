"""Monitoring interface definition...."""

from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Protocol,
    Union,
    runtime_checkable,
)
from uuid import UUID

from .monitor_models import (
    AlertConfig,
    AlertInstance,
    LogConfig,
    Metric,
    ServiceHealthStatus,
    TraceContext,
)
from .monitor_types import EventType, LogLevel, ServiceComponent


@runtime_checkable
class MonitorInterface(Protocol):
    """Interface for monitoring services...."""

    def configure(
        self,
        service_name: str,
        environment: str = "development",
        **options: Any,
    ) -> bool:
        """
        Configure the monitoring service.

        Args:
            service_name: Name of the service
            environment: Deployment environment
            **options: Additional configuration options

        Returns:
            Whether configuration was successful
     ..."""
        ...

    def log(
        self,
        message: str,
        level: LogLevel = LogLevel.INFO,
        component: ServiceComponent = ServiceComponent.SYSTEM,
        event_type: EventType = EventType.SYSTEM,
        data: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        """
        Log an event.

        Args:
            message: Event message
            level: Log level
            component: Service component
            event_type: Event type
            data: Event data
            tags: Event tags
            trace_id: Trace ID for distributed tracing
     ..."""
        ...

    def debug(
        self,
        message: str,
        component: ServiceComponent,
        event_type: EventType,
        **kwargs: Any,
    ) -> None:
        """
        Log a debug event.

        Args:
            message: Event message
            component: Service component
            event_type: Event type
            **kwargs: Additional event data
     ..."""
        ...

    def info(
        self,
        message: str,
        component: ServiceComponent,
        event_type: EventType,
        **kwargs: Any,
    ) -> None:
        """
        Log an info event.

        Args:
            message: Event message
            component: Service component
            event_type: Event type
            **kwargs: Additional event data
     ..."""
        ...

    def warning(
        self,
        message: str,
        component: ServiceComponent,
        event_type: EventType,
        **kwargs: Any,
    ) -> None:
        """
        Log a warning event.

        Args:
            message: Event message
            component: Service component
            event_type: Event type
            **kwargs: Additional event data
     ..."""
        ...

    def error(
        self,
        message: str,
        component: ServiceComponent,
        event_type: EventType,
        **kwargs: Any,
    ) -> None:
        """
        Log an error event.

        Args:
            message: Event message
            component: Service component
            event_type: Event type
            **kwargs: Additional event data
     ..."""
        ...

    def critical(
        self,
        message: str,
        component: ServiceComponent,
        event_type: EventType,
        **kwargs: Any,
    ) -> None:
        """
        Log a critical event.

        Args:
            message: Event message
            component: Service component
            event_type: Event type
            **kwargs: Additional event data
     ..."""
        ...

    def start_span(
        self,
        name: str,
        component: ServiceComponent,
        event_type: EventType,
        data: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> TraceContext:
        """
        Start a new span for tracing.

        Args:
            name: Span name
            component: Service component
            event_type: Event type
            data: Span data
            tags: Span tags

        Returns:
            A trace context object
     ..."""
        ...

    def end_span(
        self,
        span: TraceContext,
        data: Optional[Dict[str, Any]] = None,
        status: Literal["ok", "error", "unset"] = "ok",
        error_message: Optional[str] = None,
    ) -> None:
        """
        End a span.

        Args:
            span: Trace context object
            data: Additional span data
            status: Span status
            error_message: Error message if status is error
     ..."""
        ...

    def record_model_validation(
        self,
        model_name: str,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        component: ServiceComponent = ServiceComponent.SYSTEM,
    ) -> None:
        """
        Record a model validation event.

        Args:
            model_name: Name of the validated model
            success: Whether validation was successful
            data: Validation data
            error: Error message, if validation failed
            component: Service component
     ..."""
        ...

    def record_api_call(
        self,
        api_name: str,
        status_code: int,
        duration_ms: float,
        component: ServiceComponent,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Record an API call event.

        Args:
            api_name: Name of the API
            status_code: HTTP status code
            duration_ms: Duration in milliseconds
            component: Service component
            request_data: Request data
            response_data: Response data
            error: Error message, if the call failed
     ..."""
        ...

    def record_performance(
        self,
        operation: str,
        duration_ms: float,
        component: ServiceComponent,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record a performance metric.

        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            component: Service component
            success: Whether the operation was successful
            details: Additional details
     ..."""
        ...

    def register_metric(
        self,
        name: str,
        description: str,
        unit: str,
        metric_type: Literal["counter", "gauge", "histogram", "summary"],
    ) -> Metric:
        """
        Register a new metric.

        Args:
            name: Metric name
            description: Metric description
            unit: Metric unit
            metric_type: Metric type

        Returns:
            The registered metric
     ..."""
        ...

    def record_metric(
        self,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Record a metric value.

        Args:
            metric_name: Metric name
            value: Metric value
            tags: Metric tags
     ..."""
        ...

    def get_metrics(
        self,
        filter_by: Optional[Dict[str, Any]] = None,
    ) -> List[Metric]:
        """
        Get metrics, with optional filtering.

        Args:
            filter_by: Filter criteria

        Returns:
            List of metrics
     ..."""
        ...

    def record_health_status(
        self,
        status: ServiceHealthStatus,
    ) -> None:
        """
        Record service health status.

        Args:
            status: Service health status
     ..."""
        ...

    def get_health_status(
        self,
        service_id: Optional[str] = None,
    ) -> Union[ServiceHealthStatus, List[ServiceHealthStatus]]:
        """
        Get service health status.

        Args:
            service_id: Optional service ID to filter by

        Returns:
            Service health status or list of statuses
     ..."""
        ...

    def create_alert(
        self,
        alert_config: AlertConfig,
    ) -> AlertConfig:
        """
        Create a new alert.

        Args:
            alert_config: Alert configuration

        Returns:
            The created alert configuration
     ..."""
        ...

    def update_alert(
        self,
        alert_id: UUID,
        updates: Dict[str, Any],
    ) -> AlertConfig:
        """
        Update an alert configuration.

        Args:
            alert_id: Alert ID
            updates: Updates to apply

        Returns:
            The updated alert configuration
     ..."""
        ...

    def delete_alert(
        self,
        alert_id: UUID,
    ) -> bool:
        """
        Delete an alert.

        Args:
            alert_id: Alert ID

        Returns:
            Whether deletion was successful
     ..."""
        ...

    def get_alerts(
        self,
        filter_by: Optional[Dict[str, Any]] = None,
    ) -> List[AlertConfig]:
        """
        Get alert configurations, with optional filtering.

        Args:
            filter_by: Filter criteria

        Returns:
            List of alert configurations
     ..."""
        ...

    def get_alert_instances(
        self,
        filter_by: Optional[Dict[str, Any]] = None,
    ) -> List[AlertInstance]:
        """
        Get alert instances, with optional filtering.

        Args:
            filter_by: Filter criteria

        Returns:
            List of alert instances
     ..."""
        ...

    def acknowledge_alert(
        self,
        instance_id: UUID,
        acknowledged_by: str,
    ) -> AlertInstance:
        """
        Acknowledge an alert instance.

        Args:
            instance_id: Alert instance ID
            acknowledged_by: User acknowledging the alert

        Returns:
            The updated alert instance
     ..."""
        ...

    def resolve_alert(
        self,
        instance_id: UUID,
        resolution_message: Optional[str] = None,
    ) -> AlertInstance:
        """
        Resolve an alert instance.

        Args:
            instance_id: Alert instance ID
            resolution_message: Optional resolution message

        Returns:
            The updated alert instance
     ..."""
        ...

    def update_log_config(
        self,
        log_config: LogConfig,
    ) -> LogConfig:
        """
        Update log configuration.

        Args:
            log_config: Log configuration

        Returns:
            The updated log configuration
     ..."""
        ...

    def get_log_config(self) -> LogConfig:
        """
        Get current log configuration.

        Returns:
            The current log configuration
     ..."""
        ...

    def flush(self) -> bool:
        """
        Flush all pending logs and metrics.

        Returns:
            Whether flush was successful
     ..."""
        ...

    def shutdown(self) -> bool:
        """
        Shutdown the monitoring service cleanly.

        Returns:
            Whether shutdown was successful
     ..."""
        ...
