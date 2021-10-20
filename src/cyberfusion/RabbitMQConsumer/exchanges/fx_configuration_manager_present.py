"""Methods for exchange."""

import logging
from typing import Optional

import pika

from cyberfusion.Common.Command import CommandNonZeroError, CyberfusionCommand
from cyberfusion.Common.Cron import CyberfusionTuxisCron
from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ

logger = logging.getLogger(__name__)


def handle(
    rabbitmq: RabbitMQ,
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    body: str,
) -> None:
    """Handle message."""

    # Get command

    command = rabbitmq.config["virtual_hosts"][rabbitmq.virtual_host_name][
        "exchanges"
    ][method.exchange]["command"].split(" ")

    logger.info(f"Running command: '{command}'")

    # Run command

    output: Optional[CyberfusionCommand] = None

    try:
        output = CyberfusionCommand(command)
    except CommandNonZeroError as e:
        # We assume the command is tuxis-cron.
        # Only log error when RC not expected.
        # Otherwise, tuxis-cron should notify us.

        if e.rc not in [
            CyberfusionTuxisCron.RC_WARNINGS,
            CyberfusionTuxisCron.RC_ERRORS,
        ]:
            logger.error(f"Error running command '{command}'", exc_info=True)
        else:
            logger.info(
                f"Error running command '{command}', letting tuxis-cron notify us"
            )

    if output:
        logger.info(f"Success running command: '{command}'")
