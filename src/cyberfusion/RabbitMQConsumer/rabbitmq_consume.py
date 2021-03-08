"""Program to consume RabbitMQ messages."""

import json
import sys
from typing import Optional

import pika
import sdnotify

from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ

importlib = __import__("importlib")

VALUES_SKIP_PRINT = ["secret_values"]


def callback(
    rabbitmq: RabbitMQ,
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    body: bytes,
) -> None:
    """Callback method for RabbitMQ messages."""  # noqa: D202,D401

    # Cast body

    json_body = json.loads(body)

    # Remove values from body to print

    print_body = {}

    for k, v in json_body.items():
        if k in VALUES_SKIP_PRINT:
            continue

        print_body[k] = v

    # Print message

    print("Received message. Body: '{!r}'".format(print_body))

    # Import exchange module

    exchange_obj = importlib.import_module(
        f"cyberfusion.RabbitMQConsumer.exchanges.{method.exchange}"
    )

    # Call exchange module handle method

    exchange_obj.handle(rabbitmq, channel, method, properties, json_body)


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
                rabbitmq, channel, method, properties, body.decode("utf-8")
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
