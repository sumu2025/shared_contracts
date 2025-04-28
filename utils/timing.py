"""Timing and retry utilities...."""

import asyncio
import functools
import logging
import time
from typing import Any, Callable, List, Optional, TypeVar, Union, cast

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])
AsyncF = TypeVar("AsyncF", bound=Callable[..., Any])

logger = logging.getLogger(__name__)


def timed(func: F) -> F:
    """
    Decorator to measure execution time of a function.
    Works with both synchronous and asynchronous functions.

    Args:
        func: Function to decorate

    Returns:
        Decorated function
 ..."""

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = (end_time - start_time) * 1000
        logger.debug(f"Function {func.__name__} executed in {duration:.2f} ms")
        return result

    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        duration = (end_time - start_time) * 1000
        logger.debug(f"Function {func.__name__} executed in {duration:.2f} ms")
        return result

    if asyncio.iscoroutinefunction(func):
        return cast(F, async_wrapper)
    return cast(F, sync_wrapper)


def measure_execution_time(func_or_name: Union[F, str]) -> Any:
    """
    Measure execution time of a function or code block.

    Can be used as a decorator or a context manager.

    Args:
        func_or_name: Function to decorate or name for the context manager

    Returns:
        Decorated function or context manager

    Example:
        ```python
        # As a decorator
        @measure_execution_time
        def my_function():
            # ...

        # As a context manager
        with measure_execution_time("my operation"):
            # ...
        ```
 ..."""
    # When used as a decorator without arguments
    if callable(func_or_name):
        return timed(func_or_name)

    # When used as a context manager with a name
    name = func_or_name

    class ExecutionTimeContextManager:
        def __init__(self):
            self.start_time = None

        def __enter__(self):
            self.start_time = time.time()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            end_time = time.time()
            duration = (end_time - self.start_time) * 1000
            logger.debug(f"Operation '{name}' executed in {duration:.2f} ms")

    return ExecutionTimeContextManager()


async_timed = timed  # Alias for better readability with async functions


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    expected_exceptions: Optional[List[type]] = None,
) -> Callable[[F], F]:
    """
    Decorator for retrying a function with exponential backoff.
    Works with both synchronous and asynchronous functions.

    Args:
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Factor by which delay increases each retry
        expected_exceptions: Exceptions to catch for retry

    Returns:
        Decorator function
 ..."""
    if expected_exceptions is None:
        expected_exceptions = [Exception]

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception = None

            for retry in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except tuple(expected_exceptions) as e:
                    last_exception = e
                    if retry >= max_retries:
                        break

                    logger.warning(
                        f"Retry {retry+1}/{max_retries} for {func.__name__} after error: {e}"  # noqa: E501
                    )
                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)

            raise last_exception or RuntimeError("Unexpected error in retry")

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception = None

            for retry in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except tuple(expected_exceptions) as e:
                    last_exception = e
                    if retry >= max_retries:
                        break

                    logger.warning(
                        f"Retry {retry+1}/{max_retries} for {func.__name__} after error: {e}"  # noqa: E501
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)

            raise last_exception or RuntimeError("Unexpected error in retry")

        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        return cast(F, sync_wrapper)

    return decorator


class RateLimiter:
    """Rate limiter to control the frequency of operations...."""

    def __init__(self, calls: int, period: float):
        """
        Initialize a rate limiter.

        Args:
            calls: Number of calls allowed in the period
            period: Period in seconds
     ..."""
        self.calls = calls
        self.period = period
        self.timestamps: List[float] = []

    def _clean_old_timestamps(self) -> None:
        """Remove timestamps older than the period...."""
        now = time.time()
        cutoff = now - self.period
        self.timestamps = [t for t in self.timestamps if t > cutoff]

    def can_proceed(self) -> bool:
        """Check if the operation can proceed within the rate limit...."""
        self._clean_old_timestamps()
        return len(self.timestamps) < self.calls

    def acquire(self) -> bool:
        """
        Acquire permission to proceed.

        Returns:
            Whether permission was granted
     ..."""
        if not self.can_proceed():
            return False

        self.timestamps.append(time.time())
        return True

    def wait_time(self) -> float:
        """
        Calculate the time to wait before the next call is allowed.

        Returns:
            Wait time in seconds (0 if can proceed immediately)
     ..."""
        if self.can_proceed():
            return 0.0

        next_available = self.timestamps[0] + self.period
        return max(0.0, next_available - time.time())


def rate_limit(
    calls: int,
    period: float,
) -> Callable[[F], F]:
    """
    Decorator for rate limiting a function.
    Works with both synchronous and asynchronous functions.

    Args:
        calls: Number of calls allowed in the period
        period: Period in seconds

    Returns:
        Decorator function
 ..."""
    limiter = RateLimiter(calls, period)

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            wait_time = limiter.wait_time()
            if wait_time > 0:
                logger.debug(
                    f"Rate limiting {func.__name__}, waiting {wait_time:.2f} seconds"
                )
                time.sleep(wait_time)

            limiter.acquire()
            return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            wait_time = limiter.wait_time()
            if wait_time > 0:
                logger.debug(
                    f"Rate limiting {func.__name__}, waiting {wait_time:.2f} seconds"
                )
                await asyncio.sleep(wait_time)

            limiter.acquire()
            return await func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        return cast(F, sync_wrapper)

    return decorator
