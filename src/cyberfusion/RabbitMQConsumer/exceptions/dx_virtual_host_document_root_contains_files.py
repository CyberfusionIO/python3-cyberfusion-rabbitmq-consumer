"""Exceptions for specific exchange."""


class VirtualHostDocumentRootContainsFilesError(Exception):
    """Base class for all virtual host document root contains files exceptions."""

    def __init__(self) -> None:
        """Set message."""
        self.result = "Unknown error"  # Should be overridden by children
