import asyncio
import inspect
import random
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, cast

from .logging_config import LoggingConfig

# max_attempts >= 1 is enforced up front, so the retry loop always either
# returns a value or re-raises on the last attempt.
_UNREACHABLE_LOOP_EXIT = 'retry loop exited without returning or raising'


def retry_with_backoff[F: Callable[..., Any]](
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    jitter: bool = True,
    on_retry: Callable[[int, Exception], None] | None = None,
) -> Callable[[F], F]:
    """Retry functions with exponential backoff and jitter.

    Supports both synchronous and asynchronous functions.

    Args:
        max_attempts: The maximum number of attempts.
        initial_delay: The initial delay in seconds.
        backoff_factor: The multiplication factor for the delay at each attempt.
        exceptions: A tuple of exceptions that should trigger a retry.
        jitter: If True, adds random variation to the delay (±10%) to prevent
                the "thundering herd" problem in distributed systems.
        on_retry: An optional callback to be called on each retry, receiving
                  the attempt number and the exception.

    Returns:
        A decorator function.

    Raises:
        ValueError: If `max_attempts` is lower than 1. A non-positive value
            would skip the call entirely and return None, which silently
            breaks callers that expect the wrapped function's result.

    Example:
        >>> @retry_with_backoff(max_attempts=3, initial_delay=1.0, jitter=True)
        ... def api_call():
        ...     return requests.get("https://api.example.com")

    """
    if max_attempts < 1:
        raise ValueError(
            f'max_attempts must be >= 1, got {max_attempts}',
        )

    logger = LoggingConfig.get_logger(__name__)

    def decorator(func: F) -> F:
        if inspect.iscoroutinefunction(func):
            return _build_async_retry_wrapper(
                func,
                max_attempts,
                initial_delay,
                backoff_factor,
                exceptions,
                jitter,
                on_retry,
                logger,
            )
        return _build_sync_retry_wrapper(
            func,
            max_attempts,
            initial_delay,
            backoff_factor,
            exceptions,
            jitter,
            on_retry,
            logger,
        )

    return decorator


def _process_retry_attempt(
    attempt: int,
    max_attempts: int,
    e: Exception,
    delay: float,
    jitter: bool,
    on_retry: Callable[[int, Exception], None] | None,
    logger: Any,
) -> float:
    """Process retry callback, calculate jittered delay, and log attempt."""
    if on_retry:
        try:
            on_retry(attempt, e)
        # User callbacks must never abort the retry loop.
        except Exception as callback_error:
            logger.warning('Error in retry callback: %s', callback_error)

    actual_delay = delay
    if jitter:
        # Jitter prevents synchronized retries; it is not cryptographic.
        jitter_factor = 1 + random.uniform(-0.1, 0.1)  # nosec B311
        actual_delay = delay * jitter_factor

    logger.warning(
        'Attempt %s/%s failed: %s. Waiting %.2fs before retrying...',
        attempt,
        max_attempts,
        e,
        actual_delay,
    )
    return actual_delay


def _build_async_retry_wrapper[F: Callable[..., Any]](
    func: F,
    max_attempts: int,
    initial_delay: float,
    backoff_factor: float,
    exceptions: tuple[type[Exception], ...],
    jitter: bool,
    on_retry: Callable[[int, Exception], None] | None,
    logger: Any,
) -> F:
    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        delay = initial_delay
        for attempt in range(1, max_attempts + 1):
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                if attempt == max_attempts:
                    logger.exception('Failure after %s attempts', max_attempts)
                    raise

                actual_delay = _process_retry_attempt(
                    attempt, max_attempts, e, delay, jitter, on_retry, logger
                )
                await asyncio.sleep(actual_delay)
                delay *= backoff_factor

        raise AssertionError(_UNREACHABLE_LOOP_EXIT)

    return cast(F, async_wrapper)


def _build_sync_retry_wrapper[F: Callable[..., Any]](
    func: F,
    max_attempts: int,
    initial_delay: float,
    backoff_factor: float,
    exceptions: tuple[type[Exception], ...],
    jitter: bool,
    on_retry: Callable[[int, Exception], None] | None,
    logger: Any,
) -> F:
    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        delay = initial_delay
        for attempt in range(1, max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if attempt == max_attempts:
                    logger.exception('Failure after %s attempts', max_attempts)
                    raise

                actual_delay = _process_retry_attempt(
                    attempt, max_attempts, e, delay, jitter, on_retry, logger
                )
                time.sleep(actual_delay)
                delay *= backoff_factor

        raise AssertionError(_UNREACHABLE_LOOP_EXIT)

    return cast(F, sync_wrapper)
