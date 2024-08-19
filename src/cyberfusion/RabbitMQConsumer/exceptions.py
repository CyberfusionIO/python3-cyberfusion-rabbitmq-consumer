"""Exceptions."""


class VirtualHostNotExistsError(Exception):
    """Virtual host doesn't exist."""

    pass


class FernetKeyMissingError(Exception):
    """Fernet key is missing when a Fernet-encrypted message was received."""

    pass
