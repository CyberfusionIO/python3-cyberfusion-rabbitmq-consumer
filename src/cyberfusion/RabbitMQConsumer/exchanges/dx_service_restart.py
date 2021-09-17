"""Methods for exchange."""
import logging
from random import randint
from time import sleep

import pika

from cyberfusion.Common.Systemd import CyberfusionUnit
from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ

logger = logging.getLogger(__name__)


def handle(
    rabbitmq: RabbitMQ,
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    json_body: dict,
) -> None:
    """Handle message."""

    # Set variables

    unit_name = json_body["unit_name"]

    # Get object

    unit = CyberfusionUnit(unit_name)

    # Set delay to minimise the chance of restarting services
    # providing the same service on multiple nodes at the same time

    delay = randint(5, 10)  # noqa: S311

    # Restart unit

    print(
        f"Restarting service with unit name '{unit_name}'. Random delay: '{delay}'"
    )

    # Delay

    sleep(delay)

    try:
        unit.restart()

        print(f"Success restarting service with unit name '{unit_name}'")
    except Exception as e:
        # If action fails, don't crash entire program

        print(f"Error restarting service with unit name '{unit_name}': {e}")
