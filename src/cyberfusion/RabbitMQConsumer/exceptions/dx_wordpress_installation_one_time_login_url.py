"""Exceptions for specific exchange."""


class WordPressOneTimeLoginURLError(Exception):
    """Base class for all WordPress one time login URL exceptions."""

    def __init__(self) -> None:
        """Set message."""
        self.result = "Unknown error"  # Should be overridden by children
