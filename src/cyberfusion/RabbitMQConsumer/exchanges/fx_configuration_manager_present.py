"""Methods for exchange."""

import pika

from cyberfusion.Common.Command import CommandNonZeroError, CyberfusionCommand
from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ


def handle(
    rabbitmq: RabbitMQ,
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    body: bytes,
) -> None:
    """Handle message."""

    # Run command

    command = rabbitmq.config["virtual_hosts"][rabbitmq.virtual_host][
        "exchanges"
    ][method.exchange]["command"]

    print(f"Running command: '{command}'")

    try:
        CyberfusionCommand(command)
    except CommandNonZeroError as e:
        # If command fails, don't crash entire program

        print(f"Error running command '{command}': {e}")

    print(f"Success running command: '{command}'")
