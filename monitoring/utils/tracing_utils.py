"""
Utilities for distributed tracing.
"""

import contextlib
import functools
import inspect
import threading
from typing import (
    Any,
    AsyncContextManager,
    Callable,
    ContextManager,
    Dict,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
)

from ..monitor_interface import MonitorInterface
from ..monitor_models import TraceContext
from ..monitor_types import EventType, ServiceComponent
from .logger_utils import get_monitor

# Type variables for better type hinting
F = TypeVar("F", bound=Callable[..., Any])
T = TypeVar("T")

# Thread-local storage for trace context
_trace_context_local = threading.local()


def trace_method(
    component: ServiceComponent,
    event_type: Optional[EventType] = None,
    include_args: bool = True,
) -> Callable[[F], F]:
    """
    Decorator to add tracing to a method.

    Args:
        component: Service component
        event_type: Event type (defaults to REQUEST for normal methods, RESPONSE for coroutines)
        include_args: Whether to include method arguments in the trace

    Returns:
        Decorated method
    """

    def decorator(method: F) -> F:
        # Determine if the method is a coroutine
        is_coroutine = inspect.iscoroutinefunction(method)

        # Choose default event type if not specified
        nonlocal event_type
        if event_type is None:
            event_type = EventType.RESPONSE if is_coroutine else EventType.REQUEST

        if is_coroutine:

            @functools.wraps(method)
            async def async_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
                # Get class name and method name
                cls_name = self.__class__.__name__
                method_name = method.__name__
                operation_name = f"{cls_name}.{method_name}"

                # Get the monitor
                monitor = get_monitor()

                # Get trace data
                trace_data = {}
                if include_args:
                    # Add simplified argument info
                    for i, arg in enumerate(args):
                        trace_data[f"arg{i}"] = _safe_value(arg)
                    for key, value in kwargs.items():
                        trace_data[key] = _safe_value(value)

                # Start a span
                span = monitor.start_span(
                    name=operation_name,
                    component=component,
                    event_type=cast(EventType, event_type),
                    data=trace_data,
                )

                # Create trace context
                parent_trace = getattr(_trace_context_local, "current_trace", None)
                if parent_trace:
                    span.parent_span_id = parent_trace.span_id
                    # Keep the same trace_id if we're already in a trace
                    span.trace_id = parent_trace.trace_id

                # Set as current trace
                _trace_context_local.current_trace = span

                try:
                    # Call the method
                    result = await method(self, *args, **kwargs)

                    # End span
                    monitor.end_span(span, status="ok")

                    return result
                except Exception as e:
                    # End span with error
                    monitor.end_span(
                        span,
                        status="error",
                        error_message=str(e),
                        data={"error_type": type(e).__name__},
                    )

                    # Re-raise the exception
                    raise
                finally:
                    # Restore parent trace
                    if parent_trace:
                        _trace_context_local.current_trace = parent_trace
                    else:
                        delattr(_trace_context_local, "current_trace")

            return cast(F, async_wrapper)
        else:

            @functools.wraps(method)
            def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
                # Get class name and method name
                cls_name = self.__class__.__name__
                method_name = method.__name__
                operation_name = f"{cls_name}.{method_name}"

                # Get the monitor
                monitor = get_monitor()

                # Get trace data
                trace_data = {}
                if include_args:
                    # Add simplified argument info
                    for i, arg in enumerate(args):
                        trace_data[f"arg{i}"] = _safe_value(arg)
                    for key, value in kwargs.items():
                        trace_data[key] = _safe_value(value)

                # Start a span
                span = monitor.start_span(
                    name=operation_name,
                    component=component,
                    event_type=cast(EventType, event_type),
                    data=trace_data,
                )

                # Create trace context
                parent_trace = getattr(_trace_context_local, "current_trace", None)
                if parent_trace:
                    span.parent_span_id = parent_trace.span_id
                    # Keep the same trace_id if we're already in a trace
                    span.trace_id = parent_trace.trace_id

                # Set as current trace
                _trace_context_local.current_trace = span

                try:
                    # Call the method
                    result = method(self, *args, **kwargs)

                    # End span
                    monitor.end_span(span, status="ok")

                    return result
                except Exception as e:
                    # End span with error
                    monitor.end_span(
                        span,
                        status="error",
                        error_message=str(e),
                        data={"error_type": type(e).__name__},
                    )

                    # Re-raise the exception
                    raise
                finally:
                    # Restore parent trace
                    if parent_trace:
                        _trace_context_local.current_trace = parent_trace
                    else:
                        delattr(_trace_context_local, "current_trace")

            return cast(F, wrapper)

    return decorator


def trace_async_method(
    component: ServiceComponent,
    event_type: Optional[EventType] = None,
    include_args: bool = True,
) -> Callable[[F], F]:
    """
    Decorator to add tracing to an async method.

    This is just an alias for trace_method, but makes the code more readable
    by explicitly indicating that the method is async.

    Args:
        component: Service component
        event_type: Event type (defaults to RESPONSE)
        include_args: Whether to include method arguments in the trace

    Returns:
        Decorated method
    """
    if event_type is None:
        event_type = EventType.RESPONSE

    return trace_method(component, event_type, include_args)


@contextlib.contextmanager
def create_trace_context(
    operation_name: str,
    component: ServiceComponent,
    event_type: EventType = EventType.SYSTEM,
    data: Optional[Dict[str, Any]] = None,
) -> ContextManager[TraceContext]:
    """
    Create a trace context for a block of code.

    Args:
        operation_name: Name of the operation
        component: Service component
        event_type: Event type
        data: Additional data for the trace

    Yields:
        Trace context

    Example:
        ```python
        with create_trace_context("process_request", ServiceComponent.API_GATEWAY) as span:
            # Process the request
            span.attributes["request_id"] = request.id
        ```
    """
    # Get the monitor
    monitor = get_monitor()

    # Start a span
    span = monitor.start_span(
        name=operation_name,
        component=component,
        event_type=event_type,
        data=data,
    )

    # Create trace context
    parent_trace = getattr(_trace_context_local, "current_trace", None)
    if parent_trace:
        span.parent_span_id = parent_trace.span_id
        # Keep the same trace_id if we're already in a trace
        span.trace_id = parent_trace.trace_id

    # Set as current trace
    _trace_context_local.current_trace = span

    try:
        # Yield the span
        yield span

        # End span
        monitor.end_span(span, status="ok", data=span.attributes)
    except Exception as e:
        # End span with error
        monitor.end_span(
            span,
            status="error",
            error_message=str(e),
            data={**span.attributes, "error_type": type(e).__name__},
        )

        # Re-raise the exception
        raise
    finally:
        # Restore parent trace
        if parent_trace:
            _trace_context_local.current_trace = parent_trace
        else:
            delattr(_trace_context_local, "current_trace")


def get_current_trace() -> Optional[TraceContext]:
    """
    Get the current trace context.

    Returns:
        Current trace context, or None if not in a trace
    """
    return getattr(_trace_context_local, "current_trace", None)


def _safe_value(value: Any) -> Any:
    """
    Convert a value to a safe representation for tracing.

    Args:
        value: Value to convert

    Returns:
        Safe representation
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
