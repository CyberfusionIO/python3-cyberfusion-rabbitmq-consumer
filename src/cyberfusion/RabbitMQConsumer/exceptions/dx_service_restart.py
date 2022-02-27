"""Exceptions for specific exchange."""


class ServiceRestartError(Exception):
    """Base class for all service restart related exceptions."""

    def __init__(self) -> None:
        """Set message."""
        self.result = "Service could not be restarted due to error"
