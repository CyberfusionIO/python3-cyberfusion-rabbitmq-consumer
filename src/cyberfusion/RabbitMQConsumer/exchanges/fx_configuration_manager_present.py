"""Methods for exchange."""

from typing import Optional

import pika

from cyberfusion.Common.Command import CommandNonZeroError, CyberfusionCommand
from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ


def handle(
    rabbitmq: RabbitMQ,
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    body: str,
) -> None:
    """Handle message."""  # noqa: D202

    # Get command

    command = rabbitmq.config["virtual_hosts"][rabbitmq.virtual_host][
        "exchanges"
    ][method.exchange]["command"]

    print(f"Running command: '{command}'")

    # Run command

    output: Optional[CyberfusionCommand] = None

    try:
        output = CyberfusionCommand(command)
    except CommandNonZeroError as e:
        # If command fails, don't crash entire program

        print(f"Error running command '{command}': {e}")

    if output:
        print(f"Success running command: '{command}'")
