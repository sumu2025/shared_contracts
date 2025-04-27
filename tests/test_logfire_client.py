"""
Tests for LogFire client implementation.
"""

import asyncio
import time
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from shared_contracts.monitoring.implementations.logfire_client import LogFireClient
from shared_contracts.monitoring.implementations.logfire_config import LogFireConfig
from shared_contracts.monitoring.monitor_types import (
    EventType,
    LogLevel,
    ServiceComponent,
)
from shared_contracts.monitoring.utils.logger_utils import (
    configure_monitor,
    get_monitor,
    track_performance,
    with_monitoring,
)
from shared_contracts.monitoring.utils.tracing_utils import (
    create_trace_context,
    get_current_trace,
    trace_method,
)


class TestLogFireClient:
    """Tests for LogFire client implementation."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock LogFire config for testing."""
        return LogFireConfig(
            api_key="test-api-key",
            project_id="test-project",
            service_name="test-service",
            environment="test",
            min_log_level=LogLevel.DEBUG,
            batch_size=10,
            flush_interval_seconds=1.0,
        )

    @pytest.fixture
    def mock_client(self, mock_config):
        """Create a mock LogFire client for testing."""
        with patch("httpx.AsyncClient") as mock_http:
            # Mock the HTTP client
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_http.return_value.post = AsyncMock(return_value=mock_response)

            # Create the client
            client = LogFireClient(mock_config)

            # Replace the HTTP client
            client.http_client = mock_http.return_value

            yield client

    def test_initialization(self, mock_config):
        """Test client initialization."""
        with patch("httpx.AsyncClient") as mock_http:
            client = LogFireClient(mock_config)

            assert client.service_name == "test-service"
            assert client.environment == "test"
            assert client.api_key == "test-api-key"
            assert client.project_id == "test-project"

            # Check that HTTP client was created
            mock_http.assert_called_once()

    def test_log(self, mock_client):
        """Test log method."""
        # Log a message
        mock_client.log(
            message="Test message",
            level=LogLevel.INFO,
            component=ServiceComponent.AGENT_CORE,
            event_type=EventType.REQUEST,
            data={"key": "value"},
            tags=["test"],
        )

        # Check that the message was added to the buffer
        assert len(mock_client.log_buffer) == 1
        log_entry = mock_client.log_buffer[0]

        assert log_entry["message"] == "Test message"
        assert log_entry["level"] == LogLevel.INFO
        assert log_entry["component"] == ServiceComponent.AGENT_CORE
        assert log_entry["event_type"] == EventType.REQUEST
        assert log_entry["data"] == {"key": "value"}
        assert log_entry["tags"] == ["test"]
        assert log_entry["service"] == "test-service"
        assert log_entry["environment"] == "test"

    def test_convenience_methods(self, mock_client):
        """Test convenience logging methods."""
        # Test debug
        mock_client.debug(
            message="Debug message",
            component=ServiceComponent.AGENT_CORE,
            event_type=EventType.REQUEST,
            key="value",
        )

        assert len(mock_client.log_buffer) == 1
        assert mock_client.log_buffer[0]["level"] == LogLevel.DEBUG
        mock_client.log_buffer.clear()

        # Test info
        mock_client.info(
            message="Info message",
            component=ServiceComponent.AGENT_CORE,
            event_type=EventType.REQUEST,
        )

        assert len(mock_client.log_buffer) == 1
        assert mock_client.log_buffer[0]["level"] == LogLevel.INFO
        mock_client.log_buffer.clear()

        # Test warning
        mock_client.warning(
            message="Warning message",
            component=ServiceComponent.AGENT_CORE,
            event_type=EventType.REQUEST,
        )

        assert len(mock_client.log_buffer) == 1
        assert mock_client.log_buffer[0]["level"] == LogLevel.WARNING
        mock_client.log_buffer.clear()

        # Test error
        mock_client.error(
            message="Error message",
            component=ServiceComponent.AGENT_CORE,
            event_type=EventType.REQUEST,
        )

        assert len(mock_client.log_buffer) == 1
        assert mock_client.log_buffer[0]["level"] == LogLevel.ERROR
        mock_client.log_buffer.clear()

        # Test critical (should also flush)
        with patch.object(mock_client, "flush") as mock_flush:
            mock_client.critical(
                message="Critical message",
                component=ServiceComponent.AGENT_CORE,
                event_type=EventType.REQUEST,
            )

            assert len(mock_client.log_buffer) == 1
            assert mock_client.log_buffer[0]["level"] == LogLevel.CRITICAL
            mock_flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_flush(self, mock_client):
        """Test flush method."""
        # Add some logs
        for i in range(5):
            mock_client.log(
                message=f"Test message {i}",
                level=LogLevel.INFO,
                component=ServiceComponent.AGENT_CORE,
                event_type=EventType.REQUEST,
            )

        # Add some metrics
        for i in range(3):
            mock_client.record_metric(
                metric_name="test_metric",
                value=float(i),
                tags={"index": str(i)},
            )

        # Mock the async flush method
        mock_client._do_flush = AsyncMock(return_value=True)

        # Flush
        result = mock_client.flush()

        # Wait for the async task to complete
        await asyncio.sleep(0.1)

        # Check that the flush was successful
        assert result is True
        mock_client._do_flush.assert_called_once()

        # Check that the buffers were cleared
        assert len(mock_client.log_buffer) == 0
        assert len(mock_client.metric_buffer) == 0

    def test_tracing(self, mock_client):
        """Test tracing functionality."""
        # Start a span
        span = mock_client.start_span(
            name="test-operation",
            component=ServiceComponent.AGENT_CORE,
            event_type=EventType.REQUEST,
            data={"key": "value"},
            tags=["test"],
        )

        # Check that span was created
        assert span.service_name == "test-service"
        assert span.operation_name == "test-operation"
        assert span.attributes == {"key": "value"}

        # Check that a debug log was generated
        assert len(mock_client.log_buffer) == 1
        log_entry = mock_client.log_buffer[0]

        assert log_entry["message"] == "Start span: test-operation"
        assert log_entry["level"] == LogLevel.DEBUG
        assert log_entry["trace_id"] == str(span.trace_id)

        # Clear the buffer
        mock_client.log_buffer.clear()

        # End the span
        mock_client.end_span(
            span=span,
            data={"result": "success"},
            status="ok",
        )

        # Check that span was updated
        assert span.end_time is not None
        assert span.status == "ok"
        assert span.attributes == {"key": "value", "result": "success"}
        assert span.duration_ms is not None

        # Check that a debug log was generated
        assert len(mock_client.log_buffer) == 1
        log_entry = mock_client.log_buffer[0]

        assert log_entry["message"] == "End span: test-operation"
        assert log_entry["level"] == LogLevel.DEBUG
        assert log_entry["data"]["span_id"] == str(span.span_id)
        assert log_entry["data"]["trace_id"] == str(span.trace_id)
        assert log_entry["data"]["duration_ms"] == span.duration_ms
        assert log_entry["data"]["status"] == "ok"

    def test_error_handling(self, mock_client):
        """Test error handling in spans."""
        # Start a span
        span = mock_client.start_span(
            name="error-operation",
            component=ServiceComponent.AGENT_CORE,
            event_type=EventType.REQUEST,
        )

        # Clear the buffer
        mock_client.log_buffer.clear()

        # End the span with an error
        mock_client.end_span(
            span=span,
            status="error",
            error_message="Something went wrong",
        )

        # Check that an error log was generated
        assert len(mock_client.log_buffer) == 1
        log_entry = mock_client.log_buffer[0]

        assert log_entry["message"] == "End span: error-operation"
        assert log_entry["level"] == LogLevel.ERROR
        assert log_entry["data"]["error_message"] == "Something went wrong"
        assert log_entry["data"]["status"] == "error"

    def test_record_performance(self, mock_client):
        """Test performance recording."""
        # Record performance
        mock_client.record_performance(
            operation="test-operation",
            duration_ms=123.45,
            component=ServiceComponent.AGENT_CORE,
            success=True,
            details={"records_processed": 100},
        )

        # Check that a log was generated
        assert len(mock_client.log_buffer) == 1
        log_entry = mock_client.log_buffer[0]

        assert "Performance" in log_entry["message"]
        assert log_entry["level"] == LogLevel.INFO
        assert log_entry["component"] == ServiceComponent.AGENT_CORE
        assert log_entry["event_type"] == EventType.METRIC
        assert log_entry["data"]["duration_ms"] == 123.45
        assert log_entry["data"]["success"] is True
        assert log_entry["data"]["records_processed"] == 100

        # Check that a metric was recorded
        assert len(mock_client.metric_buffer) == 1
        metric_entry = mock_client.metric_buffer[0]

        assert metric_entry["name"] == "operation_duration_ms"
        assert metric_entry["value"] == 123.45
        assert metric_entry["tags"]["operation"] == "test-operation"
        assert metric_entry["tags"]["success"] == "True"
        assert metric_entry["tags"]["component"] == "agent_core"

    def test_record_api_call(self, mock_client):
        """Test API call recording."""
        # Record API call
        mock_client.record_api_call(
            api_name="test-api",
            status_code=200,
            duration_ms=42.0,
            component=ServiceComponent.AGENT_CORE,
            request_data={"param": "value"},
            response_data={"result": "success"},
        )

        # Check that a log was generated
        assert len(mock_client.log_buffer) == 1
        log_entry = mock_client.log_buffer[0]

        assert "API call" in log_entry["message"]
        assert log_entry["level"] == LogLevel.INFO
        assert log_entry["component"] == ServiceComponent.AGENT_CORE
        assert log_entry["event_type"] == EventType.REQUEST
        assert log_entry["data"]["api_name"] == "test-api"
        assert log_entry["data"]["status_code"] == 200
        assert log_entry["data"]["duration_ms"] == 42.0
        assert log_entry["data"]["success"] is True
        assert log_entry["data"]["request"] == {"param": "value"}
        assert log_entry["data"]["response"] == {"result": "success"}

        # Check that a metric was recorded
        assert len(mock_client.metric_buffer) == 1
        metric_entry = mock_client.metric_buffer[0]

        assert metric_entry["name"] == "api_call_duration_ms"
        assert metric_entry["value"] == 42.0
        assert metric_entry["tags"]["api_name"] == "test-api"
        assert metric_entry["tags"]["status_code"] == "200"
        assert metric_entry["tags"]["success"] == "True"

    def test_sanitize_data(self, mock_client):
        """Test data sanitization."""
        data = {
            "username": "user123",
            "password": "secret123",
            "api_key": "ABC123",
            "nested": {
                "authorization": "Bearer token",
                "safe": "value",
            },
            "safe": "value",
        }

        sanitized = mock_client._sanitize_data(data)

        assert sanitized["username"] == "user123"
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["api_key"] == "***REDACTED***"
        assert sanitized["nested"]["authorization"] == "***REDACTED***"
        assert sanitized["nested"]["safe"] == "value"
        assert sanitized["safe"] == "value"


class TestMonitorUtils:
    """Tests for monitoring utilities."""

    @pytest.fixture
    def setup_monitor(self):
        """Set up global monitor for testing."""
        with patch(
            "shared_contracts.monitoring.utils.logger_utils.get_monitor"
        ) as mock_get_monitor:
            # Create mock monitor
            mock_monitor = MagicMock()
            mock_monitor.start_span.return_value = MagicMock()
            mock_get_monitor.return_value = mock_monitor

            yield mock_monitor

    def test_track_performance(self, setup_monitor):
        """Test track_performance context manager."""
        mock_monitor = setup_monitor

        # Use context manager
        with track_performance("test-operation", ServiceComponent.AGENT_CORE) as span:
            # Do some work
            time.sleep(0.1)
            span.add_data({"records_processed": 100})

        # Check that span was started
        mock_monitor.start_span.assert_called_once_with(
            name="test-operation",
            component=ServiceComponent.AGENT_CORE,
            event_type=EventType.METRIC,
            data=None,
        )

        # Check that span was ended
        mock_monitor.end_span.assert_called_once()

        # Check that performance was recorded
        mock_monitor.record_performance.assert_called_once()
        assert (
            mock_monitor.record_performance.call_args[1]["operation"]
            == "test-operation"
        )
        assert (
            mock_monitor.record_performance.call_args[1]["component"]
            == ServiceComponent.AGENT_CORE
        )
        assert mock_monitor.record_performance.call_args[1]["success"] is True

    def test_track_performance_exception(self, setup_monitor):
        """Test track_performance with exception."""
        mock_monitor = setup_monitor

        # Use context manager with exception
        with pytest.raises(ValueError):
            with track_performance(
                "error-operation", ServiceComponent.AGENT_CORE
            ) as span:
                span.add_data({"stage": "before-error"})
                raise ValueError("Test error")

        # Check that span was started
        mock_monitor.start_span.assert_called_once()

        # Check that span was ended with error
        mock_monitor.end_span.assert_called_once()
        assert mock_monitor.end_span.call_args[1]["status"] == "error"
        assert "Test error" in mock_monitor.end_span.call_args[1]["error_message"]

        # Check that performance was recorded with error
        mock_monitor.record_performance.assert_called_once()
        assert mock_monitor.record_performance.call_args[1]["success"] is False

    def test_with_monitoring_decorator(self, setup_monitor):
        """Test with_monitoring decorator."""
        mock_monitor = setup_monitor

        # Define a decorated function
        @with_monitoring(component=ServiceComponent.AGENT_CORE)
        def test_function(arg1, arg2=None):
            return arg1 + (arg2 or 0)

        # Call the function
        result = test_function(1, arg2=2)

        # Check the result
        assert result == 3

        # Check that span was started
        mock_monitor.start_span.assert_called_once()
        assert mock_monitor.start_span.call_args[1]["name"] == "test_function"
        assert (
            mock_monitor.start_span.call_args[1]["component"]
            == ServiceComponent.AGENT_CORE
        )

        # Check that span was ended
        mock_monitor.end_span.assert_called_once()
        assert mock_monitor.end_span.call_args[1]["status"] == "ok"

        # Check that performance was recorded
        mock_monitor.record_performance.assert_called_once()
        assert (
            mock_monitor.record_performance.call_args[1]["operation"] == "test_function"
        )
        assert mock_monitor.record_performance.call_args[1]["success"] is True

    def test_trace_method_decorator(self, setup_monitor):
        """Test trace_method decorator."""
        mock_monitor = setup_monitor

        # Define a test class with decorated method
        class TestClass:
            @trace_method(component=ServiceComponent.AGENT_CORE)
            def test_method(self, arg1, arg2=None):
                return arg1 + (arg2 or 0)

        # Create instance and call method
        test_obj = TestClass()
        result = test_obj.test_method(1, arg2=2)

        # Check the result
        assert result == 3

        # Check that span was started
        mock_monitor.start_span.assert_called_once()
        assert mock_monitor.start_span.call_args[1]["name"] == "TestClass.test_method"
        assert (
            mock_monitor.start_span.call_args[1]["component"]
            == ServiceComponent.AGENT_CORE
        )

        # Check that span was ended
        mock_monitor.end_span.assert_called_once()
        assert mock_monitor.end_span.call_args[1]["status"] == "ok"

    def test_create_trace_context(self, setup_monitor):
        """Test create_trace_context function."""
        mock_monitor = setup_monitor

        # Use context manager
        with create_trace_context(
            "test-operation",
            component=ServiceComponent.AGENT_CORE,
            data={"initial": "data"},
        ) as span:
            span.attributes["added"] = "value"

        # Check that span was started
        mock_monitor.start_span.assert_called_once_with(
            name="test-operation",
            component=ServiceComponent.AGENT_CORE,
            event_type=EventType.SYSTEM,
            data={"initial": "data"},
        )

        # Check that span was ended
        mock_monitor.end_span.assert_called_once()
        assert mock_monitor.end_span.call_args[1]["status"] == "ok"
        assert mock_monitor.end_span.call_args[1]["data"]["initial"] == "data"
        assert mock_monitor.end_span.call_args[1]["data"]["added"] == "value"

    def test_nested_traces(self, setup_monitor):
        """Test nested traces."""
        mock_monitor = setup_monitor
        span_instances = []

        # Mock start_span to create distinct span instances
        def mock_start_span(*args, **kwargs):
            span = MagicMock()
            span.span_id = uuid.uuid4()
            span.trace_id = uuid.uuid4()
            span.attributes = kwargs.get("data", {}).copy() or {}
            span_instances.append(span)
            return span

        mock_monitor.start_span.side_effect = mock_start_span

        # Create nested traces
        with create_trace_context("outer", ServiceComponent.AGENT_CORE) as outer_span:
            outer_span.attributes["level"] = "outer"

            with create_trace_context(
                "inner", ServiceComponent.AGENT_CORE
            ) as inner_span:
                inner_span.attributes["level"] = "inner"

        # Check that both spans were created
        assert len(span_instances) == 2

        # Check that outer span was started first
        assert mock_monitor.start_span.call_args_list[0][1]["name"] == "outer"
        assert mock_monitor.start_span.call_args_list[1][1]["name"] == "inner"

        # Check correct end order (inner then outer)
        assert (
            mock_monitor.end_span.call_args_list[0][0][0] == span_instances[1]
        )  # inner
        assert (
            mock_monitor.end_span.call_args_list[1][0][0] == span_instances[0]
        )  # outer
