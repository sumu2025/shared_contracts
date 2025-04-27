"""
Utilities for working with the monitoring client.
"""

import functools
import inspect
import threading
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union, cast

from ..implementations.logfire_client import LogFireClient
from ..implementations.logfire_config import LogFireConfig
from ..monitor_interface import MonitorInterface
from ..monitor_types import EventType, LogLevel, ServiceComponent

# Global monitor instance
_monitor: Optional[MonitorInterface] = None
_monitor_lock = threading.Lock()

# Type variables for better type hinting
F = TypeVar("F", bound=Callable[..., Any])
T = TypeVar("T")


def configure_monitor(
    service_name: str,
    api_key: str,
    project_id: str,
    environment: str = "development",
    **options: Any,
) -> MonitorInterface:
    """
    Configure the global monitor instance.

    Args:
        service_name: Name of the service
        api_key: LogFire API key
        project_id: LogFire project ID
        environment: Deployment environment
        **options: Additional configuration options

    Returns:
        The configured monitor instance
    """
    global _monitor

    with _monitor_lock:
        # Create config
        config = LogFireConfig(
            api_key=api_key,
            project_id=project_id,
            service_name=service_name,
            environment=environment,
            **options,
        )

        # Create client
        _monitor = LogFireClient(config)

        return _monitor


def get_monitor() -> MonitorInterface:
    """
    Get the global monitor instance.

    Returns:
        The monitor instance

    Raises:
        RuntimeError: If the monitor has not been configured
    """
    global _monitor

    if _monitor is None:
        raise RuntimeError(
            "Monitor has not been configured. Call configure_monitor first."
        )

    return _monitor


def with_monitoring(
    component: ServiceComponent,
    event_type: Optional[EventType] = None,
) -> Callable[[F], F]:
    """
    Decorator to add monitoring to a function.

    Args:
        component: Service component
        event_type: Event type (defaults to REQUEST for normal functions, RESPONSE for coroutines)

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        # Determine if the function is a coroutine
        is_coroutine = inspect.iscoroutinefunction(func)

        # Choose default event type if not specified
        nonlocal event_type
        if event_type is None:
            event_type = EventType.RESPONSE if is_coroutine else EventType.REQUEST

        if is_coroutine:

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                monitor = get_monitor()
                start_time = time.time()

                # Get the bound function name (including class name if method)
                func_name = _get_function_name(func, args)

                # Start a span
                span = monitor.start_span(
                    name=func_name,
                    component=component,
                    event_type=cast(EventType, event_type),
                    data=_safe_args_to_dict(func, args, kwargs),
                )

                try:
                    # Call the function
                    result = await func(*args, **kwargs)

                    # Record success
                    duration_ms = (time.time() - start_time) * 1000
                    monitor.record_performance(
                        operation=func_name,
                        duration_ms=duration_ms,
                        component=component,
                        success=True,
                    )

                    # End span
                    monitor.end_span(span, status="ok")

                    return result
                except Exception as e:
                    # Record failure
                    duration_ms = (time.time() - start_time) * 1000
                    monitor.record_performance(
                        operation=func_name,
                        duration_ms=duration_ms,
                        component=component,
                        success=False,
                        details={"error": str(e), "error_type": type(e).__name__},
                    )

                    # End span with error
                    monitor.end_span(
                        span,
                        status="error",
                        error_message=str(e),
                        data={"error_type": type(e).__name__},
                    )

                    # Re-raise the exception
                    raise

            return cast(F, async_wrapper)
        else:

            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                monitor = get_monitor()
                start_time = time.time()

                # Get the bound function name (including class name if method)
                func_name = _get_function_name(func, args)

                # Start a span
                span = monitor.start_span(
                    name=func_name,
                    component=component,
                    event_type=cast(EventType, event_type),
                    data=_safe_args_to_dict(func, args, kwargs),
                )

                try:
                    # Call the function
                    result = func(*args, **kwargs)

                    # Record success
                    duration_ms = (time.time() - start_time) * 1000
                    monitor.record_performance(
                        operation=func_name,
                        duration_ms=duration_ms,
                        component=component,
                        success=True,
                    )

                    # End span
                    monitor.end_span(span, status="ok")

                    return result
                except Exception as e:
                    # Record failure
                    duration_ms = (time.time() - start_time) * 1000
                    monitor.record_performance(
                        operation=func_name,
                        duration_ms=duration_ms,
                        component=component,
                        success=False,
                        details={"error": str(e), "error_type": type(e).__name__},
                    )

                    # End span with error
                    monitor.end_span(
                        span,
                        status="error",
                        error_message=str(e),
                        data={"error_type": type(e).__name__},
                    )

                    # Re-raise the exception
                    raise

            return cast(F, wrapper)

    return decorator


@contextmanager
def track_performance(
    operation_name: str,
    component: ServiceComponent,
    event_type: EventType = EventType.METRIC,
    extra_data: Optional[Dict[str, Any]] = None,
):
    """
    Context manager to track the performance of a block of code.

    Args:
        operation_name: Name of the operation
        component: Service component
        event_type: Event type
        extra_data: Additional data to log

    Example:
        ```python
        with track_performance("process_data", ServiceComponent.AGENT_CORE) as span:
            # Do some work
            span.add_data({"records_processed": 100})
        ```
    """
    monitor = get_monitor()
    start_time = time.time()

    # Start a span
    span = monitor.start_span(
        name=operation_name,
        component=component,
        event_type=event_type,
        data=extra_data,
    )

    # Create a helper to add data to the span
    class SpanContext:
        def add_data(self, data: Dict[str, Any]) -> None:
            """Add data to the span."""
            span.attributes.update(data)

    span_context = SpanContext()

    try:
        # Yield the span context
        yield span_context

        # Record success
        duration_ms = (time.time() - start_time) * 1000
        monitor.record_performance(
            operation=operation_name,
            duration_ms=duration_ms,
            component=component,
            success=True,
            details=span.attributes,
        )

        # End span
        monitor.end_span(span, status="ok", data=span.attributes)
    except Exception as e:
        # Record failure
        duration_ms = (time.time() - start_time) * 1000
        monitor.record_performance(
            operation=operation_name,
            duration_ms=duration_ms,
            component=component,
            success=False,
            details={
                **span.attributes,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )

        # End span with error
        monitor.end_span(
            span,
            status="error",
            error_message=str(e),
            data={**span.attributes, "error_type": type(e).__name__},
        )

        # Re-raise the exception
        raise


def log_api_call(
    api_name: str,
    status_code: int,
    duration_ms: float,
    component: ServiceComponent,
    request_data: Optional[Dict[str, Any]] = None,
    response_data: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> None:
    """
    Log an API call.

    This is a convenience wrapper around monitor.record_api_call.

    Args:
        api_name: Name of the API
        status_code: HTTP status code
        duration_ms: Duration in milliseconds
        component: Service component
        request_data: Request data
        response_data: Response data
        error: Error message, if the call failed
    """
    monitor = get_monitor()
    monitor.record_api_call(
        api_name=api_name,
        status_code=status_code,
        duration_ms=duration_ms,
        component=component,
        request_data=request_data,
        response_data=response_data,
        error=error,
    )


def _get_function_name(func: Callable[..., Any], args: tuple) -> str:
    """
    Get the bound function name, including class name if method.

    Args:
        func: Function
        args: Function arguments

    Returns:
        Function name
    """
    if args and hasattr(args[0], "__class__"):
        # This might be a method, check if the function is defined in the class
        cls = args[0].__class__
        if hasattr(cls, func.__name__):
            method = getattr(cls, func.__name__)
            if getattr(method, "__func__", None) is func:
                return f"{cls.__name__}.{func.__name__}"

    return func.__name__


def _safe_args_to_dict(
    func: Callable[..., Any], args: tuple, kwargs: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Convert function arguments to a dictionary, safely handling non-serializable values.

    Args:
        func: Function
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Dictionary of arguments
    """
    # Skip self or cls for methods
    if args and hasattr(args[0], "__class__"):
        cls = args[0].__class__
        if hasattr(cls, func.__name__):
            method = getattr(cls, func.__name__)
            if getattr(method, "__func__", None) is func:
                args = args[1:]

    # Get function signature
    try:
        sig = inspect.signature(func)
        parameters = list(sig.parameters.keys())

        # Build args dict
        args_dict = {}

        # Add positional args
        for i, arg in enumerate(args):
            if i < len(parameters):
                param_name = parameters[i]
                args_dict[param_name] = _safe_serialize(arg)

        # Add keyword args
        for key, value in kwargs.items():
            args_dict[key] = _safe_serialize(value)

        return args_dict
    except Exception:
        # Fall back to just counting args
        return {f"arg{i}": _safe_serialize(arg) for i, arg in enumerate(args)} | {
            key: _safe_serialize(value) for key, value in kwargs.items()
        }


def _safe_serialize(value: Any) -> Any:
    """
    Safely serialize a value for logging.

    Args:
        value: Value to serialize

    Returns:
        Serializable value
    """
    if value is None:
        return None
    elif isinstance(value, (str, int, float, bool)):
        return value
    elif isinstance(value, (list, tuple)):
        return f"[{type(value).__name__}:{len(value)}]"
    elif isinstance(value, dict):
        return f"[dict:{len(value)}]"
    else:
        # Just use the type name for other objects
        return f"[{type(value).__name__}]"
