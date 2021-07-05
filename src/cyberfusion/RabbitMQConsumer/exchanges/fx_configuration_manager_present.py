"""Methods for exchange."""

import logging
from typing import Optional

import pika

from cyberfusion.Common.Command import CommandNonZeroError, CyberfusionCommand
from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ

logger = logging.getLogger(__name__)


def handle(
    rabbitmq: RabbitMQ,
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    body: str,
) -> None:
    """Handle message."""  # noqa: D202

    # Get command

    command = rabbitmq.config["virtual_hosts"][rabbitmq.virtual_host_name][
        "exchanges"
    ][method.exchange]["command"]

    logger.info(f"Running command: '{command}'")

    # Run command

    output: Optional[CyberfusionCommand] = None

    try:
        output = CyberfusionCommand(command)
    except CommandNonZeroError:
        logger.error(f"Error running command '{command}'", exc_info=True)
    except Exception:
        logger.exception("Unknown error")

    if output:
        logger.info(f"Success running command: '{command}'")
