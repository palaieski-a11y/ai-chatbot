"""Small utility decorators: retry, timing and log_calls."""

from functools import wraps
import time
import logging
from typing import Callable, Any, Tuple, Type

logger = logging.getLogger(__name__)


def retry(max_attempts: int = 3, delay: float = 0.5, backoff: float = 2.0, exceptions: Tuple[Type[BaseException], ...] = (Exception,)):
    """Retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (including first call).
        delay: Initial delay between attempts in seconds.
        backoff: Multiplier applied to delay after each failure.
        exceptions: Tuple of exception types that trigger a retry.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        logger.exception("Max retry attempts reached")
                        raise
                    logger.warning("Exception occurred: %s. Retrying in %.2fs (attempt %d/%d)", e, current_delay, attempts, max_attempts)
                    time.sleep(current_delay)
                    current_delay *= backoff
        return wrapper

    return decorator


def timing(func: Callable[..., Any]) -> Callable[..., Any]:
    """Measure execution time of synchronous functions.

    Adds a `__last_duration__` attribute to the wrapped function (seconds).
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start
        setattr(wrapper, "__last_duration__", duration)
        logger.debug("%s executed in %.6fs", func.__name__, duration)
        return result

    return wrapper


def log_calls(log_args: bool = False, log_result: bool = False):
    """Decorator to log function calls, arguments and optionally results."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info("Calling %s", func.__name__)
            if log_args:
                logger.debug("Args: %s, Kwargs: %s", args, kwargs)
            result = func(*args, **kwargs)
            if log_result:
                logger.debug("%s returned %s", func.__name__, result)
            return result

        return wrapper

    return decorator
