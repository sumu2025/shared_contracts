"""Test for the automatic monitor configuration feature."""

import pytest

from shared_contracts.monitoring.utils.logger_utils import get_monitor


def test_monitor_auto_configuration():
    """Test that get_monitor() automatically configures a monitor if none exists."""
    # This should not raise an exception now
    monitor = get_monitor()
    
    # The monitor should be a working instance
    assert monitor is not None
    
    # Test basic logging functionality
    try:
        from shared_contracts.monitoring.monitor_types import EventType, ServiceComponent
        monitor.info(
            message="Test message", 
            component=ServiceComponent.SYSTEM, 
            event_type=EventType.SYSTEM
        )
        # If we got here without exception, the test passes
        assert True
    except Exception as e:
        pytest.fail(f"Auto-configured monitor failed to log: {e}")

    # Test metrics functionality
    try:
        monitor.record_metric(
            metric_name="test_metric",
            value=1.0,
            tags={"test": "true"}
        )
        # If we got here without exception, the test passes
        assert True
    except Exception as e:
        pytest.fail(f"Auto-configured monitor failed to record metric: {e}")
        
    # Test performance recording
    try:
        from shared_contracts.monitoring.monitor_types import ServiceComponent
        monitor.record_performance(
            operation="test-operation",
            duration_ms=100.0,
            component=ServiceComponent.SYSTEM,
            success=True,
            details={"test": "true"}
        )
        # If we got here without exception, the test passes
        assert True
    except Exception as e:
        pytest.fail(f"Auto-configured monitor failed to record performance: {e}")
