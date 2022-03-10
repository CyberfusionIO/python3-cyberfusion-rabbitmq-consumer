"""Exceptions for specific exchange."""


class ConfigurationManagerPresentError(Exception):
    """Base class for all configuration manager present exceptions."""

    def __init__(self) -> None:
        """Set message."""
        self.result = "Unknown error"  # Should be overridden by children
