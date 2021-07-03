"""Program to consume RabbitMQ messages."""

import json
import signal
import sys
from typing import Optional

import pika
import sdnotify

from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ

importlib = __import__("importlib")

VALUES_SKIP_PRINT = [
    "secret_values",
    "passphrase",
    "password",
    "admin_password",
    "database_user_password",
]

processing = False
shutdown_requested = False


def handle_sigterm(  # type: ignore
    _signal_number: int,
    _frame,  # Ignore lack of type annotation. Not going to import frame stuff
) -> None:
    """Handle SIGTERM."""
    print("Received SIGTERM")

    # If currently processing, delay (handled in callback())

    global processing

    if processing:
        global shutdown_requested

        shutdown_requested = True

        print("Currently processing. Delayed shutdown")

        return

    # If not currently processing, exit

    print("Not currently processing. Exiting directly after SIGTERM...")
    sys.exit(0)


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

    # Set processing

    global processing

    processing = True

    # Import exchange module

    exchange_obj = importlib.import_module(
        f"cyberfusion.RabbitMQConsumer.exchanges.{method.exchange}"
    )

    # Call exchange module handle method

    exchange_obj.handle(rabbitmq, channel, method, properties, json_body)

    # Set processing

    processing = False

    # Exit if shutdown requested

    global shutdown_requested

    if shutdown_requested:
        print("Exiting delayed after SIGTERM request...")
        sys.exit(0)


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
            queue=rabbitmq.config["virtual_hosts"][rabbitmq.virtual_host_name][
                "queue"
            ],
            on_message_callback=lambda channel, method, properties, body: callback(  # noqa: E501
                rabbitmq, channel, method, properties, body.decode("utf-8")
            ),
            auto_ack=True,
        )

        # Notify systemd at startup

        sdnotify.SystemdNotifier().notify("READY=1")

        # Set signal handler

        signal.signal(signal.SIGTERM, handle_sigterm)

        # Consume

        rabbitmq.channel.start_consuming()
    finally:
        if rabbitmq:
            # Stop consuming

            print("Stopping consuming...")
            rabbitmq.channel.stop_consuming()

            # Close connection

            print("Closing connection...")
            rabbitmq.connection.close()
