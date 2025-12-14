"""Methods for exchange."""

import logging
from enum import Enum
from random import random
from typing import Optional

from pydantic import Field, PositiveInt

from cyberfusion.RabbitMQConsumer.contracts import (
    HandlerBase,
    RPCRequestBase,
    RPCResponseBase,
    RPCResponseData,
)

logger = logging.getLogger(__name__)


class FavouriteFoodEnum(str, Enum):
    """Favourite foods."""

    ONION = "onion"
    ORANGE = "orange"
    BANANA = "banana"


class RPCRequestExample(RPCRequestBase):
    """Data part of RPC request."""

    favourite_food: FavouriteFoodEnum = Field(
        description="Human-readable favourite food."
    )
    chance_percentage: PositiveInt = Field(
        description="Chances of favourite food passing.", default=20
    )

    class Config:
        """Config."""

        json_schema_extra = {
            "examples": [
                {"favourite_food": FavouriteFoodEnum.BANANA},
                {
                    "favourite_food": FavouriteFoodEnum.ONION,
                    "chance_percentage": 50,
                },
            ]
        }


class RPCResponseDataExample(RPCResponseData):
    """Data part of RPC response."""

    tolerable: bool


class RPCResponseExample(RPCResponseBase):
    """Base attributes for RPC response."""

    data: Optional[RPCResponseDataExample]

    class Config:
        """Config."""

        json_schema_extra = {
            "examples": [
                {
                    "_description": "Not tolerable",
                    "success": True,
                    "message": "Determined toleration",
                    "data": {"tolerable": False},
                },
                {
                    "_description": "Tolerable",
                    "success": True,
                    "message": "Determined toleration",
                    "data": {"tolerable": True},
                },
            ]
        }


def determine_toleration(
    favourite_food: FavouriteFoodEnum, chance_percentage: int
) -> bool:
    """Determine if food is tolerable.

    Had this not been an example, you would probably have done some computation
    to get a result.
    """
    if favourite_food in FavouriteFoodEnum.ONION:
        return False

    return random() > (chance_percentage / 100.0)


class Handler(HandlerBase):
    """Class to handle RPC requests."""

    @property
    def lock_attribute(self) -> str:
        """Attribute of RPC request, used for locking.

        If the value matches, no two requests may run simultaneously.
        """
        return "favourite_food"

    def __call__(self, request: RPCRequestExample) -> RPCResponseExample:
        """Handle message."""
        tolerable = determine_toleration(
            request.favourite_food, request.chance_percentage
        )

        return RPCResponseExample(
            success=True,
            message="Determined toleration",
            data=RPCResponseDataExample(tolerable=tolerable),
        )
