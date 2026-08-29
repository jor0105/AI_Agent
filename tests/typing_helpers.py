"""Typing helpers for tests that exercise invalid runtime inputs."""

from collections.abc import Callable
from typing import cast


def invoke(callable_: object, *args: object, **kwargs: object) -> object:
    """Invoke a callable whose invalid contract is under test."""
    function = cast(Callable[..., object], callable_)
    return function(*args, **kwargs)
