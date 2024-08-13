"""Contracts."""

from typing import Optional

from pydantic import BaseModel


class RPCResponseData(BaseModel):
    """Data part of RPC response."""

    pass


class RPCResponseBase(BaseModel):
    """Base attributes for RPC response."""

    success: bool
    message: str
    data: Optional[RPCResponseData]


class RPCRequestBase(BaseModel):
    """Base attributes for RPC request."""

    pass


class HandlerBase:
    """Class to handle RPC requests."""

    def __init__(self) -> None:
        """Do nothing."""
        pass

    @property
    def lock_attribute(self) -> Optional[str]:
        """Attribute of RPC request, used for locking.

        If the value matches, no two requests may run simultaneously.
        """
        return None

    def __call__(self, request: RPCRequestBase) -> RPCResponseBase:
        """Handle message."""
        raise NotImplementedError
