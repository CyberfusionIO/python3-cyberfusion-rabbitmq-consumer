"""Generic utilities."""

from typing import Optional


def _prefix_message(prefix: Optional[str], result: str) -> str:
    """Add user-specified prefix to message."""
    if prefix:
        return f"[{prefix}] {result}"

    return result
