"""
LogFire client implementation for the AgentForge platform.
"""

import asyncio
import logging
import platform
import socket
import threading
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union

import httpx

from shared_contracts.monitoring.monitor_interface import MonitorInterface
from shared_contracts.monitoring.monitor_models import (
    AlertConfig,
    AlertInstance,
    LogConfig,
    Metric,
    ServiceHealthStatus,
    TraceContext,
)
from shared_contracts.monitoring.monitor_types import (
    EventType,
    LogLevel,
    ServiceComponent,
)

from .logfire_config import LogFireConfig


class LogFireClient(MonitorInterface):
    """
    LogFire client for monitoring and logging.

    This client implements the MonitorInterface and provides integration
    with the LogFire monitoring service.
    """

    def __init__(self, config: LogFireConfig):
        """
        Initialize the LogFire client.

        Args:
            config: Client configuration
        """
        self.config = config
        self.logger = logging.getLogger("logfire")
        self._configure_logger()

        self.service_name = config.service_name
        self.environment = config.environment
        self.api_key = config.api_key
        self.project_id = config.project_id

        # Set up HTTP client
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Add project_id header if specified (for backwards compatibility)
        if self.project_id:
            headers["X-LogFire-Project"] = self.project_id

        self.http_client = httpx.AsyncClient(
            timeout=config.timeout_seconds,
            headers=headers,
            base_url=config.api_endpoint,
        )

        # Set up batching
        self.log_buffer: List[Dict[str, Any]] = []
        self.metric_buffer: List[Dict[str, Any]] = []
        self.flush_lock = threading.Lock()
        self.last_flush = time.time()

        # Metadata
        self.metadata = self._collect_metadata() if config.enable_metadata else {}
        if config.additional_metadata:
            self.metadata.update(config.additional_metadata)

        # Set up flush timer
        self._setup_flush_timer()

        # Store metrics
        self.metrics: Dict[str, Metric] = {}

        # Trace contexts
        self.active_traces: Dict[uuid.UUID, TraceContext] = {}

        # Log config
        self.log_config = LogConfig(
            service_name=config.service_name,
            environment=config.environment,
            min_level=config.min_log_level,
        )

        self.logger.info(
            f"LogFire client initialized for service {self.service_name} in {self.environment} environment"  # noqa: E501
        )

    def _configure_logger(self) -> None:
        """Configure the logger."""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        # Set log level based on config
        level_map = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL,
        }
        self.logger.setLevel(level_map.get(self.config.min_log_level, logging.INFO))

    def _collect_metadata(self) -> Dict[str, Any]:
        """Collect system and runtime metadata."""
        try:
            return {
                "host": {
                    "name": socket.gethostname(),
                    "ip": socket.gethostbyname(socket.gethostname()),
                    "os": platform.system(),
                    "os_version": platform.release(),
                    "platform": platform.platform(),
                },
                "runtime": {
                    "python_version": platform.python_version(),
                    "python_implementation": platform.python_implementation(),
                },
                "service": {
                    "name": self.service_name,
                    "environment": self.environment,
                },
            }
        except Exception as e:
            self.logger.warning(f"Failed to collect metadata: {e}")
            return {
                "service": {
                    "name": self.service_name,
                    "environment": self.environment,
                }
            }

    def _setup_flush_timer(self) -> None:
        """Set up timer to periodically flush logs."""

        def _flush_timer():
            while True:
                time.sleep(self.config.flush_interval_seconds)
                try:
                    current_time = time.time()
                    if (
                        current_time - self.last_flush
                        >= self.config.flush_interval_seconds
                        and (self.log_buffer or self.metric_buffer)
                    ):
                        self.flush()
                except Exception as e:
                    self.logger.error(f"Error in flush timer: {e}")

        self.flush_thread = threading.Thread(target=_flush_timer, daemon=True)
        self.flush_thread.start()

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
        """
        try:
            # Update service info
            self.service_name = service_name
            self.environment = environment

            # Update metadata
            if self.config.enable_metadata:
                self.metadata = self._collect_metadata()
                if self.config.additional_metadata:
                    self.metadata.update(self.config.additional_metadata)

            # Update log config
            self.log_config.service_name = service_name
            self.log_config.environment = environment

            # Process any additional options
            if options:
                for key, value in options.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)

            return True
        except Exception as e:
            self.logger.error(f"Failed to configure LogFire client: {e}")
            return False

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
        """
        # Apply sampling
        if self.config.sample_rate < 1.0 and level != LogLevel.CRITICAL:
            import random

            if random.random() > self.config.sample_rate:
                return

        # Skip if below minimum log level
        level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4,
        }
        if level_order.get(level, 0) < level_order.get(self.config.min_log_level, 1):
            return

        # Create log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "component": component,
            "event_type": event_type,
            "message": message,
            "service": self.service_name,
            "environment": self.environment,
        }

        # Add optional fields
        if data:
            log_entry["data"] = data

        if tags:
            log_entry["tags"] = tags

        if trace_id:
            log_entry["trace_id"] = trace_id

        # Add metadata
        if self.metadata:
            log_entry["metadata"] = self.metadata

        # Add to buffer
        with self.flush_lock:
            self.log_buffer.append(log_entry)

            # Flush if buffer is full
            if len(self.log_buffer) >= self.config.batch_size:
                self._schedule_flush()

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
        """
        self.log(
            message=message,
            level=LogLevel.DEBUG,
            component=component,
            event_type=event_type,
            data=kwargs if kwargs else None,
        )

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
        """
        self.log(
            message=message,
            level=LogLevel.INFO,
            component=component,
            event_type=event_type,
            data=kwargs if kwargs else None,
        )

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
        """
        self.log(
            message=message,
            level=LogLevel.WARNING,
            component=component,
            event_type=event_type,
            data=kwargs if kwargs else None,
        )

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
        """
        self.log(
            message=message,
            level=LogLevel.ERROR,
            component=component,
            event_type=event_type,
            data=kwargs if kwargs else None,
        )

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
        """
        self.log(
            message=message,
            level=LogLevel.CRITICAL,
            component=component,
            event_type=event_type,
            data=kwargs if kwargs else None,
        )

        # Always flush immediately for critical events
        self.flush()

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
        """
        span = TraceContext(
            service_name=self.service_name,
            operation_name=name,
        )

        # Add to active traces
        self.active_traces[span.span_id] = span

        # Log span start
        log_data = {"span_id": str(span.span_id), "trace_id": str(span.trace_id)}
        if data:
            log_data.update(data)

        self.log(
            message=f"Start span: {name}",
            level=LogLevel.DEBUG,
            component=component,
            event_type=event_type,
            data=log_data,
            tags=tags,
            trace_id=str(span.trace_id),
        )

        return span

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
        """
        if span.span_id not in self.active_traces:
            self.logger.warning(f"Attempting to end an unknown span: {span.span_id}")
            return

        # Update span
        span.end_time = datetime.utcnow()
        span.status = status
        span.error_message = error_message

        # Calculate duration
        if span.start_time:
            duration = (span.end_time - span.start_time).total_seconds() * 1000
            span.duration_ms = duration

        # Add additional data
        if data:
            span.attributes.update(data)

        # Log span end
        log_data = {
            "span_id": str(span.span_id),
            "trace_id": str(span.trace_id),
            "duration_ms": span.duration_ms,
            "status": status,
        }
        if error_message:
            log_data["error_message"] = error_message
        if data:
            log_data.update(data)

        level = LogLevel.ERROR if status == "error" else LogLevel.DEBUG

        self.log(
            message=f"End span: {span.operation_name}",
            level=level,
            component=ServiceComponent.SYSTEM,
            event_type=EventType.SYSTEM,
            data=log_data,
            trace_id=str(span.trace_id),
        )

        # Remove from active traces
        del self.active_traces[span.span_id]

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
        """
        log_data = {
            "model_name": model_name,
            "success": success,
        }
        if data:
            log_data.update(data)
        if error:
            log_data["error"] = error

        level = LogLevel.ERROR if not success else LogLevel.INFO
        message = (
            f"Model validation {'succeeded' if success else 'failed'}: {model_name}"
        )

        self.log(
            message=message,
            level=level,
            component=component,
            event_type=EventType.VALIDATION,
            data=log_data,
        )

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
        """
        success = 200 <= status_code < 300

        log_data = {
            "api_name": api_name,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "success": success,
        }

        if request_data:
            # Don't log sensitive information
            safe_request = self._sanitize_data(request_data)
            log_data["request"] = safe_request

        if response_data and (success or self.config.min_log_level == LogLevel.DEBUG):
            # Only include response data for successful requests or in debug mode
            safe_response = self._sanitize_data(response_data)
            log_data["response"] = safe_response

        if error:
            log_data["error"] = error

        level = LogLevel.ERROR if not success else LogLevel.INFO
        message = f"API call to {api_name} {'succeeded' if success else 'failed'} with status {status_code}"  # noqa: E501

        self.log(
            message=message,
            level=level,
            component=component,
            event_type=EventType.REQUEST,
            data=log_data,
        )

        # Also record as a metric
        self.record_metric(
            metric_name="api_call_duration_ms",
            value=duration_ms,
            tags={
                "api_name": api_name,
                "status_code": str(status_code),
                "success": str(success),
                "component": str(component),
            },
        )

    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize data to remove sensitive information.

        Args:
            data: Data to sanitize

        Returns:
            Sanitized data
        """
        sensitive_keys = {
            "password",
            "token",
            "secret",
            "key",
            "apikey",
            "api_key",
            "authorization",
            "auth",
            "credential",
            "credentials",
        }

        result = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                result[key] = "***REDACTED***"
            elif isinstance(value, dict):
                result[key] = self._sanitize_data(value)
            else:
                result[key] = value
        return result

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
        """
        log_data = {
            "operation": operation,
            "duration_ms": duration_ms,
            "success": success,
        }
        if details:
            log_data.update(details)

        level = LogLevel.INFO
        message = f"Performance: {operation} took {duration_ms:.2f}ms"

        self.log(
            message=message,
            level=level,
            component=component,
            event_type=EventType.METRIC,
            data=log_data,
        )

        # Also record as a metric
        self.record_metric(
            metric_name="operation_duration_ms",
            value=duration_ms,
            tags={
                "operation": operation,
                "success": str(success),
                "component": str(component),
            },
        )

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
        """
        metric = Metric(
            name=name,
            description=description,
            unit=unit,
            metric_type=metric_type,
        )

        self.metrics[name] = metric
        return metric

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
        """
        # Create metric if it doesn't exist
        if metric_name not in self.metrics:
            self.register_metric(
                name=metric_name,
                description=f"Auto-registered metric: {metric_name}",
                unit="unspecified",
                metric_type="gauge",
            )

        # Create metric entry
        metric_entry = {
            "name": metric_name,
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.service_name,
            "environment": self.environment,
        }

        if tags:
            metric_entry["tags"] = tags

        # Add to buffer
        with self.flush_lock:
            self.metric_buffer.append(metric_entry)

            # Flush if buffer is full
            if len(self.metric_buffer) >= self.config.batch_size:
                self._schedule_flush()

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
        """
        if not filter_by:
            return list(self.metrics.values())

        result = []
        for metric in self.metrics.values():
            match = True
            for key, value in filter_by.items():
                if hasattr(metric, key) and getattr(metric, key) != value:
                    match = False
                    break
            if match:
                result.append(metric)

        return result

    def record_health_status(
        self,
        status: ServiceHealthStatus,
    ) -> None:
        """
        Record service health status.

        Args:
            status: Service health status
        """
        # Log health status
        log_data = {
            "service_id": status.service_id,
            "status": status.status,
            "message": status.message,
            "version": status.version,
            "uptime_seconds": status.uptime_seconds,
        }

        if status.checks:
            log_data["checks"] = status.checks

        if status.resource_usage:
            log_data["resource_usage"] = {
                "cpu_percent": status.resource_usage.cpu_percent,
                "memory_percent": status.resource_usage.memory_percent,
                "memory_rss": status.resource_usage.memory_rss,
            }

        level = LogLevel.INFO
        if status.status == "degraded":
            level = LogLevel.WARNING
        elif status.status == "unhealthy":
            level = LogLevel.ERROR

        message = f"Health status: {status.status} - {status.message}"

        self.log(
            message=message,
            level=level,
            component=ServiceComponent.SYSTEM,
            event_type=EventType.SYSTEM,
            data=log_data,
        )

        # Record metrics
        if status.resource_usage:
            self.record_metric(
                metric_name="cpu_usage_percent",
                value=status.resource_usage.cpu_percent,
                tags={"service_id": status.service_id},
            )
            self.record_metric(
                metric_name="memory_usage_percent",
                value=status.resource_usage.memory_percent,
                tags={"service_id": status.service_id},
            )
            self.record_metric(
                metric_name="memory_rss_bytes",
                value=float(status.resource_usage.memory_rss),
                tags={"service_id": status.service_id},
            )

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
        """
        # This implementation doesn't store health status
        # In a real implementation, this would query LogFire for health status
        raise NotImplementedError("Health status retrieval not implemented")

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
        """
        # Log alert creation
        self.log(
            message=f"Alert created: {alert_config.name}",
            level=LogLevel.INFO,
            component=ServiceComponent.SYSTEM,
            event_type=EventType.SYSTEM,
            data={
                "alert_id": str(alert_config.alert_id),
                "name": alert_config.name,
                "description": alert_config.description,
                "component": str(alert_config.component),
                "condition": alert_config.condition,
                "severity": str(alert_config.severity),
            },
        )

        # In a real implementation, this would create the alert in LogFire
        return alert_config

    def update_alert(
        self,
        alert_id: uuid.UUID,
        updates: Dict[str, Any],
    ) -> AlertConfig:
        """
        Update an alert configuration.

        Args:
            alert_id: Alert ID
            updates: Updates to apply

        Returns:
            The updated alert configuration
        """
        # This implementation doesn't store alerts
        # In a real implementation, this would update the alert in LogFire
        raise NotImplementedError("Alert updates not implemented")

    def delete_alert(
        self,
        alert_id: uuid.UUID,
    ) -> bool:
        """
        Delete an alert.

        Args:
            alert_id: Alert ID

        Returns:
            Whether deletion was successful
        """
        # Log alert deletion
        self.log(
            message=f"Alert deleted: {alert_id}",
            level=LogLevel.INFO,
            component=ServiceComponent.SYSTEM,
            event_type=EventType.SYSTEM,
            data={"alert_id": str(alert_id)},
        )

        # In a real implementation, this would delete the alert in LogFire
        return True

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
        """
        # This implementation doesn't store alerts
        # In a real implementation, this would query LogFire for alerts
        return []

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
        """
        # This implementation doesn't store alert instances
        # In a real implementation, this would query LogFire for alert instances
        return []

    def acknowledge_alert(
        self,
        instance_id: uuid.UUID,
        acknowledged_by: str,
    ) -> AlertInstance:
        """
        Acknowledge an alert instance.

        Args:
            instance_id: Alert instance ID
            acknowledged_by: User acknowledging the alert

        Returns:
            The updated alert instance
        """
        # Log alert acknowledgement
        self.log(
            message=f"Alert acknowledged: {instance_id}",
            level=LogLevel.INFO,
            component=ServiceComponent.SYSTEM,
            event_type=EventType.SYSTEM,
            data={
                "instance_id": str(instance_id),
                "acknowledged_by": acknowledged_by,
            },
        )

        # In a real implementation, this would acknowledge the alert in LogFire
        raise NotImplementedError("Alert acknowledgement not implemented")

    def resolve_alert(
        self,
        instance_id: uuid.UUID,
        resolution_message: Optional[str] = None,
    ) -> AlertInstance:
        """
        Resolve an alert instance.

        Args:
            instance_id: Alert instance ID
            resolution_message: Optional resolution message

        Returns:
            The updated alert instance
        """
        # Log alert resolution
        log_data = {"instance_id": str(instance_id)}
        if resolution_message:
            log_data["resolution_message"] = resolution_message

        self.log(
            message=f"Alert resolved: {instance_id}",
            level=LogLevel.INFO,
            component=ServiceComponent.SYSTEM,
            event_type=EventType.SYSTEM,
            data=log_data,
        )

        # In a real implementation, this would resolve the alert in LogFire
        raise NotImplementedError("Alert resolution not implemented")

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
        """
        # Update log config
        self.log_config = log_config

        # Log update
        self.log(
            message="Log configuration updated",
            level=LogLevel.INFO,
            component=ServiceComponent.SYSTEM,
            event_type=EventType.SYSTEM,
            data={
                "service_name": log_config.service_name,
                "environment": log_config.environment,
                "min_level": str(log_config.min_level),
                "format": log_config.format,
                "output": log_config.output,
            },
        )

        return log_config

    def get_log_config(self) -> LogConfig:
        """
        Get current log configuration.

        Returns:
            The current log configuration
        """
        return self.log_config

    def _schedule_flush(self) -> None:
        """Schedule a flush to run asynchronously."""
        # Simple implementation: just flush now
        self.flush()

    async def _do_flush(self) -> bool:
        """
        Perform the actual flush to LogFire API.

        Returns:
            Whether the flush was successful
        """
        success = True

        # Send logs
        if self.log_buffer:
            try:
                # Clone and clear buffer
                with self.flush_lock:
                    logs_to_send = list(self.log_buffer)
                    self.log_buffer.clear()

                # Send to LogFire
                response = await self.http_client.post(
                    "/logs",
                    json={"logs": logs_to_send},
                )

                if response.status_code >= 400:
                    self.logger.error(
                        f"Failed to send logs to LogFire: {response.status_code} {response.text}"  # noqa: E501
                    )
                    success = False
            except Exception as e:
                self.logger.error(f"Error sending logs to LogFire: {e}")
                success = False

        # Send metrics
        if self.metric_buffer:
            try:
                # Clone and clear buffer
                with self.flush_lock:
                    metrics_to_send = list(self.metric_buffer)
                    self.metric_buffer.clear()

                # Send to LogFire
                response = await self.http_client.post(
                    "/metrics",
                    json={"metrics": metrics_to_send},
                )

                if response.status_code >= 400:
                    self.logger.error(
                        f"Failed to send metrics to LogFire: {response.status_code} {response.text}"  # noqa: E501
                    )
                    success = False
            except Exception as e:
                self.logger.error(f"Error sending metrics to LogFire: {e}")
                success = False

        return success

    def flush(self) -> bool:
        """
        Flush all pending logs and metrics.

        Returns:
            Whether flush was successful
        """
        # Skip if nothing to flush
        if not self.log_buffer and not self.metric_buffer:
            return True

        # Run in event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create task if loop is already running
                #                 future = asyncio.create_task(self._do_flush())  # 未使用变量: future  # noqa: E501
                # We can't easily wait for the result in this case
                return True
            else:
                # If loop is not running, run until complete
                return loop.run_until_complete(self._do_flush())
        except Exception as e:
            self.logger.error(f"Error in flush: {e}")
            return False
        finally:
            self.last_flush = time.time()

    def shutdown(self) -> bool:
        """
        Shutdown the monitoring service cleanly.

        Returns:
            Whether shutdown was successful
        """
        try:
            # Flush pending logs
            self.flush()

            # Close HTTP client
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.http_client.aclose())
            else:
                loop.run_until_complete(self.http_client.aclose())

            # Log shutdown
            self.logger.info(f"LogFire client for {self.service_name} shut down")

            return True
        except Exception as e:
            self.logger.error(f"Error shutting down LogFire client: {e}")
            return False

    def __del__(self):
        """Clean up resources on deletion."""
        try:
            self.shutdown()
        except Exception:
            pass
