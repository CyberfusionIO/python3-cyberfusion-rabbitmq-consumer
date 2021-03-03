"""Methods for exchange."""

import json
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

    # Cast body

    json_body = json.loads(body)

    # Get command

    command = (
        rabbitmq.config["virtual_hosts"][rabbitmq.virtual_host]["exchanges"][
            method.exchange
        ]["command"]
        + " --path="
        + json_body["path"]
    )

    print(f"Running command: '{command}'")

    # Run command

    output: Optional[CyberfusionCommand] = None

    try:
        output = CyberfusionCommand(
            command,
            uid=json_body["unix_id"],
            gid=json_body["unix_id"],
            path=json_body["path"],
            environment={"PWD": json_body["path"], "HOME": json_body["home"]},
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
                content_type="application/json",
            ),
            body=output.stdout,
        )
