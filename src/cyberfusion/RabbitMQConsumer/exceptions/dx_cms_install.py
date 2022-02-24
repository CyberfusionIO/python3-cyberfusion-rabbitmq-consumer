"""Exceptions for specific exchange."""


class CMSInstallError:
    """Base class for all CMS install related exceptions."""

    def __init__(self) -> None:
        """Set message."""
        self.result = "Unknown error"  # Should be overridden by children


class CMSInstalledError:
    """Raise if CMS is already installed."""

    def __init__(self) -> None:
        """Set message."""
        self.result = "Core already installed, doing nothing"


class WordPressCoreDownloadError:
    """Raise if error occurs during WordPress core download."""

    def __init__(self) -> None:
        """Set message."""
        self.result = "Error downloading core"


class WordPressConfigCreateError:
    """Raise if error occurs during WordPress config create."""

    def __init__(self) -> None:
        """Set message."""
        self.result = "Error creating config"


class WordPressCoreInstallError:
    """Raise if error occurs during WordPress core install."""

    def __init__(self) -> None:
        """Set message."""
        self.result = "Error installing core"
