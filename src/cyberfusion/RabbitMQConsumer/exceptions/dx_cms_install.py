"""Exceptions for specific exchange."""


class CMSInstallError(Exception):
    """Base class for all CMS install related exceptions."""

    def __init__(self) -> None:
        """Set message."""
        self.result = "Unknown error"  # Should be overridden by children


class CMSInstalledError(CMSInstallError):
    """Raise if CMS is already installed."""

    def __init__(self) -> None:
        """Set message."""
        self.result = "Core already installed, doing nothing"


class WordPressCoreDownloadError(CMSInstallError):
    """Raise if error occurs during WordPress core download."""

    def __init__(self) -> None:
        """Set message."""
        self.result = "Error downloading core"


class WordPressConfigCreateError(CMSInstallError):
    """Raise if error occurs during WordPress config create."""

    def __init__(self) -> None:
        """Set message."""
        self.result = "Error creating config"


class WordPressCoreInstallError(CMSInstallError):
    """Raise if error occurs during WordPress core install."""

    def __init__(self) -> None:
        """Set message."""
        self.result = "Error installing core"
