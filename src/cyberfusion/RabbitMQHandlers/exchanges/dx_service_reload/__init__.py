"""Methods for exchange."""

import logging
from typing import Optional

from cyberfusion.Common.Systemd import CyberfusionUnit
from cyberfusion.RabbitMQConsumer.utilities import _prefix_message
from cyberfusion.RabbitMQHandlers.exceptions.rabbitmq_consumer import (
    ServiceReloadError,
)

logger = logging.getLogger(__name__)

KEY_IDENTIFIER_EXCLUSIVE = "unit_name"


def handle(
    *,
    exchange_name: str,
    virtual_host_name: str,
    rabbitmq_config: Optional[dict],
    json_body: dict,
) -> dict:
    """Handle message.

    data contains: nothing
    """
    try:
        # Set variables

        unit_name = json_body["unit_name"]

        # Set preliminary result

        success = True
        result = _prefix_message(unit_name, "Service reloaded")

        # Get object

        unit = CyberfusionUnit(unit_name)

        # Reload unit

        logger.info(_prefix_message(unit_name, "Reloading service"))

        try:
            unit.reload()
        except Exception:
            raise ServiceReloadError

    except Exception as e:
        # Set result from error and log exception

        success = False
        result = _prefix_message(
            unit_name,
            e.result
            if isinstance(e, ServiceReloadError)
            else "An unexpected exception occurred",
        )

        logger.exception(result)

    return {"success": success, "message": result, "data": {}}
