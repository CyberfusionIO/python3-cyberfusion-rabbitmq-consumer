"""Program to consume RabbitMQ messages."""

import json
import logging
import signal
import sys
from logging.handlers import SMTPHandler
from typing import Optional

import pika
import sdnotify
from systemd.journal import JournalHandler

from cyberfusion.Common import EmailAddresses, get_hostname
from cyberfusion.RabbitMQConsumer.RabbitMQ import (
    RabbitMQ,
    get_config_file_path,
)

importlib = __import__("importlib")

VALUES_SKIP_PRINT = [
    "secret_values",
    "passphrase",
    "password",
    "admin_password",
    "database_user_password",
]

NAME_HOST_SMTP = "smtp.prorelay.nl"
PORT_HOST_SMTP = 587

# Create root logger

print("Configuring root logger...")

root_logger = logging.getLogger()
root_logger.propagate = False
root_logger.setLevel(logging.DEBUG)

# Set hostname for use in handler and formatter

hostname: str = get_hostname()

# Create handlers

systemd_handler = JournalHandler()
systemd_handler.setLevel(logging.INFO)

smtp_handler = SMTPHandler(
    (NAME_HOST_SMTP, PORT_HOST_SMTP),
    EmailAddresses.ENGINEERING,
    [EmailAddresses.ENGINEERING],
    f"[{hostname}] Logging notification from RabbitMQ Consumer",
    credentials=None,
    secure=None,
)
smtp_handler.setLevel(logging.WARNING)

handlers = [systemd_handler, smtp_handler]

# Set email message

email_message = "Dear reader,\n\n"
email_message += "This is process %(process)d reporting %(levelname)s message from the '%(name)s' logger.\n\n"
email_message += "Used config file path:\n\n"
email_message += get_config_file_path() + "\n\n"
email_message += "Message:\n\n"
email_message += "%(message)s\n\n"
email_message += "--\n"
email_message += "With kind regards,\n"
email_message += hostname + "\n\n"

# Create formatters

systemd_formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
smtp_formatter = logging.Formatter(email_message)

# Set handlers formatters

systemd_handler.setFormatter(systemd_formatter)
smtp_handler.setFormatter(smtp_formatter)

# Add handlers to root logger

for h in handlers:
    print("Configuring root logger handler...")

    root_logger.addHandler(h)

    print("Configured root logger handler")

# Log end

print("Configured root logger")

# Create module logger

logger = logging.getLogger(__name__)

# Set handle_sigterm variables

processing = False
shutdown_requested = False


def handle_sigterm(  # type: ignore
    _signal_number: int,
    _frame,  # Ignore lack of type annotation. Not going to import frame stuff
) -> None:
    """Handle SIGTERM."""
    logger.info("Received SIGTERM")

    # If currently processing, delay (handled in callback())

    global processing

    if processing:
        global shutdown_requested

        shutdown_requested = True

        logger.info("Currently processing. Delayed shutdown")

        return

    # If not currently processing, exit

    logger.info("Not currently processing. Exiting directly after SIGTERM...")
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

    logger.info("Received message. Body: '{!r}'".format(print_body))

    # Set processing

    global processing

    processing = True

    # Import exchange module

    exchange_obj = importlib.import_module(
        f"cyberfusion.RabbitMQConsumer.exchanges.{method.exchange}"
    )

    # Call exchange module handle method

    try:
        exchange_obj.handle(rabbitmq, channel, method, properties, json_body)
    except Exception:
        # Catch exceptions we didn't catch in module itself

        logger.exception("Unknown error")

    # Set processing

    processing = False

    # Exit if shutdown requested

    global shutdown_requested

    if shutdown_requested:
        logger.info("Exiting delayed after SIGTERM request...")
        sys.exit(0)


def main() -> None:
    """Spawn relevant class for CLI function."""
    rabbitmq: Optional[RabbitMQ] = None

    try:
        # Set virtual host name

        try:
            virtual_host_name = sys.argv[1]
        except IndexError:
            logger.critical("Specify virtual host as first argument")
            sys.exit(1)

        # Get RabbitMQ object

        rabbitmq = RabbitMQ(virtual_host_name)

        # Configure consuming

        rabbitmq.channel.basic_consume(
            queue=rabbitmq.config["virtual_hosts"][rabbitmq.virtual_host_name][
                "queue"
            ],
            on_message_callback=lambda channel, method, properties, body: callback(
                rabbitmq, channel, method, properties, body.decode("utf-8")
            ),
            auto_ack=True,
        )

        # Notify systemd at startup

        sdnotify.SystemdNotifier().notify("READY=1")

        # Set signal handler

        signal.signal(signal.SIGTERM, handle_sigterm)

        # Start consuming

        rabbitmq.channel.start_consuming()
    finally:
        if rabbitmq:
            # Stop consuming

            logger.info("Stopping consuming...")
            rabbitmq.channel.stop_consuming()

            # Close connection

            logger.info("Closing connection...")
            rabbitmq.connection.close()
