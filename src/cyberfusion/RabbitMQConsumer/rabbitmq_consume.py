"""Program to consume RabbitMQ messages."""

import sys
from typing import Optional

import pika
import sdnotify

from cyberfusion.Common.Command import CommandNonZeroError, CyberfusionCommand
from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ


def callback(
    rabbitmq: RabbitMQ,
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    body: bytes,
) -> None:
    """Callback method for RabbitMQ messages."""  # noqa: D202,D401

    # Print message

    print("Received message. Body: '{!r}'".format(body))

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


def main() -> None:
    """Spawn relevant class for CLI function."""
    rabbitmq: Optional[RabbitMQ] = None

    try:
        # Get RabbitMQ object

        try:
            rabbitmq = RabbitMQ(sys.argv[1])
        except IndexError:
            print("Specify virtual host as first argument")
            sys.exit(1)

        # Consume

        rabbitmq.channel.basic_consume(
            queue=rabbitmq.config["virtual_hosts"][rabbitmq.virtual_host][
                "queue"
            ],
            on_message_callback=lambda channel, method, properties, body: callback(  # noqa: E501
                rabbitmq, channel, method, properties, body
            ),
            auto_ack=True,
        )

        # Notify systemd at startup

        sdnotify.SystemdNotifier().notify("READY=1")

        # Consume

        rabbitmq.channel.start_consuming()

    finally:
        if rabbitmq:
            rabbitmq.channel.stop_consuming()
            rabbitmq.connection.close()
