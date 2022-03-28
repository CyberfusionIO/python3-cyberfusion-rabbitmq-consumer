"""Methods for exchange."""

import json
import logging

import pika

from cyberfusion.Common.Systemd import CyberfusionUnit
from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ
from cyberfusion.RabbitMQConsumer.utilities import _prefix_message
from cyberfusion.RabbitMQHandlers.exceptions.rabbitmq_consumer import (
    ServiceRestartError,
)

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
