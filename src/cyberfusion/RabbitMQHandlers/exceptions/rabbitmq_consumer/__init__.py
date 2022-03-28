"""Exceptions for specific module."""


class ServiceRestartError(Exception):
    """Base class for all service restart related exceptions."""

    def __init__(self) -> None:
        """Set message."""
        self.result = "Service could not be restarted due to error"


class ServiceReloadError(Exception):
    """Base class for all service reload related exceptions."""

    def __init__(self) -> None:
        """Set message."""
        self.result = "Service could not be reloaded due to error"


class ConfigurationManagerPresentError(Exception):
    """Base class for all configuration manager present exceptions."""

    def __init__(self) -> None:
        """Set message."""
        self.result = "Unknown error"  # Should be overridden by children
