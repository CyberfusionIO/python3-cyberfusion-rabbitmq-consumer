"""Methods for exchange."""

import logging
import threading

import pika

from cyberfusion.Common.Systemd import CyberfusionUnit
from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ
from cyberfusion.RabbitMQConsumer.utilities import (
    _prefix_message,
    finish_handle,
    prepare_handle,
)
from cyberfusion.RabbitMQHandlers.exceptions.rabbitmq_consumer import (
    ServiceReloadError,
)

logger = logging.getLogger(__name__)

KEY_IDENTIFIER_EXCLUSIVE = "unit_name"


def handle(
    rabbitmq: RabbitMQ,
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    lock: threading.Lock,
    json_body: dict,
) -> None:
    """Handle message.

    data contains: nothing
    """
    try:
        prepare_handle(
            lock,
            exchange_name=method.exchange,
        )

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

    try:
        finish_handle(
            rabbitmq,
            channel,
            method,
            properties,
            lock,
            body={"success": success, "message": result, "data": {}},
            exchange_name=method.exchange,
        )
    except Exception:
        logger.exception("Finish routine failed")
