from typing import Optional, Any

from pydantic import BaseModel

from cyberfusion.RabbitMQConsumer.contracts import RPCResponseBase, RPCResponseData


class RPCResponseDataValidationError(BaseModel):
    location: tuple[Any, ...]
    message: str
    type: str


class RPCResponseDataValidationErrors(RPCResponseData):
    """Data part of RPC response."""

    errors: list[RPCResponseDataValidationError]


class RPCResponseValidationError(RPCResponseBase):
    """Base attributes for RPC response."""

    data: Optional[RPCResponseDataValidationErrors]
