"""Duration unit conversion shared by the provider adapters."""

from typing import Final

NANOSECONDS_PER_MILLISECOND: Final[int] = 1_000_000


def nanoseconds_to_milliseconds(nanoseconds: float | None) -> float | None:
    """Convert a nanosecond duration to milliseconds.

    Ollama reports every timing in nanoseconds while `ChatMetrics` stores
    milliseconds, so both the streaming and non-streaming paths need this
    conversion.

    Args:
        nanoseconds: The duration reported by the provider, or None when the
            provider omitted it.

    Returns:
        The duration in milliseconds, or None when the input was None.
    """
    if nanoseconds is None:
        return None
    return nanoseconds / NANOSECONDS_PER_MILLISECOND
