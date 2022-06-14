"""Methods for exchange."""

import logging

from cyberfusion.Common.Systemd import CyberfusionUnit
from cyberfusion.RabbitMQConsumer.utilities import _prefix_message
from cyberfusion.RabbitMQHandlers.exceptions.rabbitmq_consumer import (
    ServiceRestartError,
)

logger = logging.getLogger(__name__)

KEY_IDENTIFIER_EXCLUSIVE = "unit_name"


def handle(
    *,
    exchange_name: str,
    virtual_host_name: str,
    rabbitmq_config: dict,
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
        result = _prefix_message(unit_name, "Service restarted")

        # Get object

        unit = CyberfusionUnit(unit_name)

        # Restart unit

        logger.info(_prefix_message(unit_name, "Restarting service"))

        try:
            unit.restart()
        except Exception:
            raise ServiceRestartError

    except Exception as e:
        # Set result from error and log exception

        success = False
        result = _prefix_message(
            unit_name,
            e.result
            if isinstance(e, ServiceRestartError)
            else "An unexpected exception occurred",
        )

        logger.exception(result)

    return {"success": success, "message": result, "data": {}}
