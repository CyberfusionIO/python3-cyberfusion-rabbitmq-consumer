"""Exceptions for specific exchange."""


class ServiceReloadError(Exception):
    """Base class for all service reload related exceptions."""

    def __init__(self) -> None:
        """Set message."""
        self.result = "Service could not be reloaded due to error"
