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
    json_body: dict,
) -> None:
    """Handle message."""  # noqa: D202

    # Get command

    command = (
        rabbitmq.config["virtual_hosts"][rabbitmq.virtual_host]["exchanges"][
            method.exchange
        ]["command"]
        + " --repository-id="
        + str(json_body["borg_repository_id"])
    )

    print(f"Running command: '{command}'")

    # Run command

    output: Optional[CyberfusionCommand] = None

    try:
        output = CyberfusionCommand(
            command,
            uid=json_body["unix_id"],
            gid=json_body["unix_id"],
        )
    except CommandNonZeroError as e:
        # If command fails, don't crash entire program

        print(f"Error running command '{command}': {e}")

    if output:
        print(f"Success running command: '{command}'")

        # Publish message

        channel.basic_publish(
            exchange=method.exchange,
            routing_key=properties.reply_to,
            properties=pika.BasicProperties(
                correlation_id=properties.correlation_id,
            ),
            body=output.stdout.encode("utf-8"),
        )
