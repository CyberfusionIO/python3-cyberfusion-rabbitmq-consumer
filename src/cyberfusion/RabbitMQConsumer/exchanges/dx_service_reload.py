"""Methods for exchange."""

import json
import logging

import pika

from cyberfusion.Common.Systemd import CyberfusionUnit
from cyberfusion.RabbitMQConsumer.exceptions.dx_service_reload import (
    ServiceReloadError,
)
from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ
from cyberfusion.RabbitMQConsumer.utilities import _prefix_message

logger = logging.getLogger(__name__)


def handle(
    rabbitmq: RabbitMQ,
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    json_body: dict,
) -> None:
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

    except ServiceReloadError as e:
        # Set result from error and log exception

        success = False
        result = _prefix_message(unit_name, e.result)

        logger.exception(result)

    # Publish result

    channel.basic_publish(
        exchange=method.exchange,
        routing_key=properties.reply_to,
        properties=pika.BasicProperties(
            correlation_id=properties.correlation_id,
            content_type="application/json",
        ),
        body=json.dumps({"success": success, "message": result, "data": {}}),
    )
