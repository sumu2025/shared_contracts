"""Tests for monitoring components in agentforge-contracts...."""

import uuid
from datetime import datetime

from shared_contracts.monitoring.monitor_interface import MonitorInterface
from shared_contracts.monitoring.monitor_models import (
    AlertConfig,
    AlertInstance,
    LogConfig,
    Metric,
    MetricValue,
    ResourceUsage,
    ServiceHealthStatus,
    TraceContext,
)
from shared_contracts.monitoring.monitor_types import (
    EventType,
    LogLevel,
    MonitorEvent,
    ServiceComponent,
)


class TestMonitorTypes:
    """Tests for monitoring types and enumerations...."""

    def test_log_level_enum(self):
        """Test LogLevel enumeration...."""
        assert LogLevel.DEBUG == "debug"
        assert LogLevel.INFO == "info"
        assert LogLevel.WARNING == "warning"
        assert LogLevel.ERROR == "error"
        assert LogLevel.CRITICAL == "critical"

        # Test conversion to/from string
        assert LogLevel("info") == LogLevel.INFO
        assert LogLevel.WARNING.value == "warning"

    def test_service_component_enum(self):
        """Test ServiceComponent enumeration...."""
        assert ServiceComponent.AGENT_CORE == "agent_core"
        assert ServiceComponent.MODEL_SERVICE == "model_service"
        assert ServiceComponent.TOOL_SERVICE == "tool_service"
        assert ServiceComponent.SYSTEM == "system"

        # Test conversion to/from string
        assert ServiceComponent("database") == ServiceComponent.DATABASE
        assert ServiceComponent.API_GATEWAY.value == "api_gateway"

    def test_event_type_enum(self):
        """Test EventType enumeration...."""
        assert EventType.REQUEST == "request"
        assert EventType.RESPONSE == "response"
        assert EventType.EXCEPTION == "exception"
        assert EventType.SYSTEM == "system"

        # Test conversion to/from string
        assert EventType("metric") == EventType.METRIC
        assert EventType.VALIDATION.value == "validation"

    def test_monitor_event(self):
        """Test MonitorEvent model...."""
        now = datetime.utcnow().timestamp()
        event = MonitorEvent(
            timestamp=now,
            level=LogLevel.INFO,
            component=ServiceComponent.AGENT_CORE,
            event_type=EventType.REQUEST,
            message="Test event",
            data={"key": "value"},
            tags=["test", "event"],
            trace_id="1234567890",
        )

        assert event.timestamp == now
        assert event.level == LogLevel.INFO
        assert event.component == ServiceComponent.AGENT_CORE
        assert event.event_type == EventType.REQUEST
        assert event.message == "Test event"
        assert event.data == {"key": "value"}
        assert "test" in event.tags
        assert event.trace_id == "1234567890"


class TestMonitorModels:
    """Tests for monitoring models...."""

    def test_metric_value(self):
        """Test MetricValue model...."""
        value = MetricValue(value=42.0, tags={"host": "server-1"})

        assert value.value == 42.0
        assert isinstance(value.timestamp, datetime)
        assert value.tags["host"] == "server-1"

    def test_metric(self):
        """Test Metric model...."""
        metric = Metric(
            name="request_count",
            description="Number of requests",
            unit="count",
            metric_type="counter",
            values=[
                MetricValue(value=1.0),
                MetricValue(value=2.0, tags={"endpoint": "/api/v1"}),
            ],
        )

        assert metric.name == "request_count"
        assert metric.unit == "count"
        assert metric.metric_type == "counter"
        assert len(metric.values) == 2
        assert metric.values[1].value == 2.0
        assert metric.values[1].tags["endpoint"] == "/api/v1"

    def test_resource_usage(self):
        """Test ResourceUsage model...."""
        usage = ResourceUsage(
            cpu_percent=25.5,
            memory_percent=40.2,
            memory_rss=1024 * 1024 * 100,  # 100 MB
            disk_io_read=1024 * 1024 * 5,  # 5 MB
            disk_io_write=1024 * 1024 * 2,  # 2 MB
            network_recv=1024 * 100,  # 100 KB
            network_sent=1024 * 50,  # 50 KB
            open_file_descriptors=42,
        )

        assert usage.cpu_percent == 25.5
        assert usage.memory_percent == 40.2
        assert usage.memory_rss == 1024 * 1024 * 100
        assert usage.open_file_descriptors == 42

    def test_service_health_status(self):
        """Test ServiceHealthStatus model...."""
        health = ServiceHealthStatus(
            service_id="agent-service-1",
            service_name="Agent Service",
            status="healthy",
            message="All systems operational",
            version="1.0.0",
            uptime_seconds=3600,
            resource_usage=ResourceUsage(
                cpu_percent=25.5,
                memory_percent=40.2,
                memory_rss=1024 * 1024 * 100,
                disk_io_read=1024 * 1024 * 5,
                disk_io_write=1024 * 1024 * 2,
                network_recv=1024 * 100,
                network_sent=1024 * 50,
                open_file_descriptors=42,
            ),
            checks={"database": True, "api": True, "redis": True},
        )

        assert health.service_id == "agent-service-1"
        assert health.status == "healthy"
        assert health.version == "1.0.0"
        assert health.uptime_seconds == 3600
        assert health.checks["database"] is True
        assert health.resource_usage is not None
        assert health.resource_usage.cpu_percent == 25.5

    def test_trace_context(self):
        """Test TraceContext model...."""
        trace = TraceContext(
            service_name="agent-service", operation_name="process-request"
        )

        assert isinstance(trace.trace_id, uuid.UUID)
        assert trace.parent_span_id is None
        assert isinstance(trace.span_id, uuid.UUID)
        assert trace.service_name == "agent-service"
        assert trace.operation_name == "process-request"
        assert trace.start_time is not None
        assert trace.end_time is None
        assert trace.duration_ms is None
        assert trace.status == "unset"
        assert trace.error_message is None

    def test_alert_config(self):
        """Test AlertConfig model...."""
        alert = AlertConfig(
            name="High CPU Alert",
            description="Alert when CPU usage is too high",
            component=ServiceComponent.AGENT_CORE,
            condition="cpu_percent > 90",
            severity=LogLevel.WARNING,
            notification_channels=["email", "slack"],
            cooldown_seconds=600,
            tags=["performance", "cpu"],
        )

        assert isinstance(alert.alert_id, uuid.UUID)
        assert alert.name == "High CPU Alert"
        assert alert.component == ServiceComponent.AGENT_CORE
        assert alert.condition == "cpu_percent > 90"
        assert alert.severity == LogLevel.WARNING
        assert "email" in alert.notification_channels
        assert alert.cooldown_seconds == 600
        assert "performance" in alert.tags
        assert alert.enabled is True

    def test_alert_instance(self):
        """Test AlertInstance model...."""
        alert_id = uuid.uuid4()
        instance = AlertInstance(
            alert_id=alert_id,
            value=95.2,
            message="CPU usage is 95.2%, exceeding threshold of 90%",
            component=ServiceComponent.AGENT_CORE,
            severity=LogLevel.WARNING,
            metadata={"host": "server-1", "threshold": 90.0},
        )

        assert instance.alert_id == alert_id
        assert isinstance(instance.instance_id, uuid.UUID)
        assert instance.triggered_at is not None
        assert instance.resolved_at is None
        assert instance.status == "active"
        assert instance.value == 95.2
        assert instance.message == "CPU usage is 95.2%, exceeding threshold of 90%"
        assert instance.component == ServiceComponent.AGENT_CORE
        assert instance.severity == LogLevel.WARNING
        assert instance.metadata["host"] == "server-1"
        assert instance.acknowledged_by is None
        assert instance.acknowledged_at is None
        assert instance.resolution_message is None

    def test_log_config(self):
        """Test LogConfig model...."""
        config = LogConfig(
            service_name="agent-service",
            environment="production",
            min_level=LogLevel.INFO,
            include_components=[
                ServiceComponent.AGENT_CORE,
                ServiceComponent.API_GATEWAY,
            ],
            exclude_components=[],
            include_event_types=None,  # All event types
            exclude_event_types=[EventType.METRIC],
            format="json",
            output="both",
            file_path="/var/log/agent-service.log",
            max_file_size_mb=20,
            max_files=10,
            additional_fields={"app_version": "1.0.0", "environment": "production"},
        )

        assert config.service_name == "agent-service"
        assert config.environment == "production"
        assert config.min_level == LogLevel.INFO
        assert ServiceComponent.AGENT_CORE in config.include_components
        assert len(config.exclude_components) == 0
        assert config.include_event_types is None
        assert EventType.METRIC in config.exclude_event_types
        assert config.format == "json"
        assert config.output == "both"
        assert config.file_path == "/var/log/agent-service.log"
        assert config.max_file_size_mb == 20
        assert config.max_files == 10
        assert config.additional_fields["app_version"] == "1.0.0"


class TestMonitorInterface:
    """Tests for monitor interface...."""

    def test_interface_implementation(self):
        """Test implementation of MonitorInterface...."""

        # Create a mock implementation
        class MockMonitor:
            def __init__(self):
                self.logs = []
                self.metrics = {}
                self.health_status = {}
                self.alerts = {}
                self.alert_instances = {}
                self.trace_contexts = {}

            def configure(
                self,
                service_name: str,
                environment: str = "development",
                **options,
            ) -> bool:
                self.service_name = service_name
                self.environment = environment
                self.options = options
                return True

            def log(
                self,
                message: str,
                level: LogLevel = LogLevel.INFO,
                component: ServiceComponent = ServiceComponent.SYSTEM,
                event_type: EventType = EventType.SYSTEM,
                data=None,
                tags=None,
                trace_id=None,
            ) -> None:
                self.logs.append(
                    {
                        "message": message,
                        "level": level,
                        "component": component,
                        "event_type": event_type,
                        "data": data,
                        "tags": tags,
                        "trace_id": trace_id,
                    }
                )

            def debug(self, message, component, event_type, **kwargs):
                self.log(message, LogLevel.DEBUG, component, event_type, kwargs)

            def info(self, message, component, event_type, **kwargs):
                self.log(message, LogLevel.INFO, component, event_type, kwargs)

            def warning(self, message, component, event_type, **kwargs):
                self.log(message, LogLevel.WARNING, component, event_type, kwargs)

            def error(self, message, component, event_type, **kwargs):
                self.log(message, LogLevel.ERROR, component, event_type, kwargs)

            def critical(self, message, component, event_type, **kwargs):
                self.log(message, LogLevel.CRITICAL, component, event_type, kwargs)

            def start_span(self, name, component, event_type, data=None, tags=None):
                span = TraceContext(
                    service_name=self.service_name,
                    operation_name=name,
                )
                self.trace_contexts[span.span_id] = span
                return span

            def end_span(self, span, data=None, status="ok", error_message=None):
                span.end_time = datetime.utcnow()
                span.status = status
                span.error_message = error_message
                if data:
                    span.attributes.update(data)
                return span

            # Implement other required methods as needed for testing
            def record_model_validation(self, *args, **kwargs):
                pass

            def record_api_call(self, *args, **kwargs):
                pass

            def record_performance(self, *args, **kwargs):
                pass

            def register_metric(self, *args, **kwargs):
                return Metric(
                    name="test", description="test", unit="test", metric_type="counter"
                )

            def record_metric(self, *args, **kwargs):
                pass

            def get_metrics(self, *args, **kwargs):
                return []

            def record_health_status(self, *args, **kwargs):
                pass

            def get_health_status(self, *args, **kwargs):
                return ServiceHealthStatus(
                    service_id="test",
                    service_name="test",
                    status="healthy",
                    message="ok",
                    version="1.0",
                    uptime_seconds=0,
                )

            def create_alert(self, *args, **kwargs):
                pass

            def update_alert(self, *args, **kwargs):
                pass

            def delete_alert(self, *args, **kwargs):
                return True

            def get_alerts(self, *args, **kwargs):
                return []

            def get_alert_instances(self, *args, **kwargs):
                return []

            def acknowledge_alert(self, *args, **kwargs):
                pass

            def resolve_alert(self, *args, **kwargs):
                pass

            def update_log_config(self, *args, **kwargs):
                return LogConfig(service_name="test")

            def get_log_config(self):
                return LogConfig(service_name="test")

            def flush(self):
                return True

            def shutdown(self):
                return True

        # Create instance and check it satisfies the interface
        monitor = MockMonitor()
        assert isinstance(monitor, MonitorInterface)

        # Test basic functionality
        assert monitor.configure("test-service", environment="testing")

        monitor.info(
            "Test message",
            component=ServiceComponent.AGENT_CORE,
            event_type=EventType.REQUEST,
            user_id="123",
        )

        assert len(monitor.logs) == 1
        assert monitor.logs[0]["message"] == "Test message"
        assert monitor.logs[0]["level"] == LogLevel.INFO
        assert monitor.logs[0]["component"] == ServiceComponent.AGENT_CORE

        # Test span creation and completion
        span = monitor.start_span(
            "test-operation",
            component=ServiceComponent.AGENT_CORE,
            event_type=EventType.REQUEST,
        )

        assert span.service_name == "test-service"
        assert span.operation_name == "test-operation"

        monitor.end_span(span, status="ok")

        assert span.end_time is not None
        assert span.status == "ok"
