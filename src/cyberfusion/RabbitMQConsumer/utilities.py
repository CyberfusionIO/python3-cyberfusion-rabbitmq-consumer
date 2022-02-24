"""Generic utilities."""


def _prefix_message(prefix: str, result: str) -> str:
    """Add user-specified prefix to message."""
    return f"[{prefix}] {result}"
