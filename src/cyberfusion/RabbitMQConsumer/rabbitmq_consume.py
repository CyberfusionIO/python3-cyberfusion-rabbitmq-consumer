"""Program to consume RabbitMQ messages."""

import json
import logging
import signal
import sys
import threading
from types import ModuleType
from typing import Dict, List, Optional

import pika
import sdnotify
from systemd.journal import JournalHandler

from cyberfusion.Common import get_hostname
from cyberfusion.RabbitMQConsumer.handler import Handler
from cyberfusion.RabbitMQConsumer.RabbitMQ import FERNET_TOKEN_KEYS, RabbitMQ

importlib = __import__("importlib")

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

handlers = [systemd_handler]

# Create formatters

systemd_formatter = logging.Formatter(
    "[%(threadName)s] [%(levelname)s] %(name)s: %(message)s"
)

# Set handlers formatters

systemd_handler.setFormatter(systemd_formatter)

# Add handlers to root logger

for h in handlers:
    print("Configuring root logger handler...")

    root_logger.addHandler(h)

    print("Configured root logger handler")

# Log end

print("Configured root logger")

# Create module logger

logger = logging.getLogger(__name__)

# Set default variables

locks: Dict[str, Dict[str, threading.Lock]] = {}
threads: List[threading.Thread] = []


def handle_sigterm(  # type: ignore[no-untyped-def]
    _signal_number: int,
    _frame,
) -> None:
    """Handle SIGTERM."""
    logger.info("Received SIGTERM")

    # Wait for threads to finish. Note that the thread-safe callbacks, which
    # usually includes message acknowledgement, are not executed when exiting,
    # as this happens in the main thread. Therefore, this logic just ensures
    # that the message handle method finished cleanly, but as the message will
    # not be acknowledged, it will likely be called again.

    global threads

    for thread in threads:
        if not thread.is_alive():
            continue

        logger.info(
            f"Waiting for thread '{thread.name}' to finish before exiting..."
        )

        thread.join()

    # Exit after all threads finished

    logger.info("Exiting after SIGTERM...")

    sys.exit(0)


def callback(
    rabbitmq: RabbitMQ,
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    modules: Dict[str, ModuleType],
    body: bytes,
) -> None:
    """Handle RabbitMQ message."""

    # Cast body

    json_body = json.loads(body)

    # Remove values from body to print

    print_body = {}

    for k, v in json_body.items():
        if k in FERNET_TOKEN_KEYS:
            continue

        print_body[k] = v

    # Print message

    logger.info("Received message. Body: '{!r}'".format(print_body))

    # Add value of exclusive key identifier to locks
    #
    # For some exchanges, the handle() method may only run simultaneously when
    # operating on a different object. For example:
    #
    #   >>> dx_service_restart.handle(json_body={"unit_name": "a"})
    #
    # ... may run while:
    #
    #   >>> dx_service_restart.handle(json_body={"unit_name": "b"})
    #
    # is running, but not while another instance with the same signature, i.e.
    #
    #   >>> dx_service_restart.handle(json_body={"unit_name": "a"})
    #
    # is running, as it operates on the same object, and would therefore cause
    # race conditions. The exclusive key identifier is the name of an attribute
    # that identifies the object on which the handle() method operates. A lock
    # is created for the value of each exclusive key identifier that the consumer
    # has come across during runtime.
    #
    # If the exclusive key identifier is None, the handle() method for the exchange
    # may not run simultaneously in any case, regardless of the object it operates
    # on.

    global locks

    lock_key = modules[method.exchange].KEY_IDENTIFIER_EXCLUSIVE

    if lock_key is not None:
        lock_value = json_body[lock_key]
    else:
        # If value is None, use a dummy value so the logic still works

        lock_value = "dummy"

    if lock_value not in locks[method.exchange]:
        locks[method.exchange][lock_value] = threading.Lock()

    lock = locks[method.exchange][lock_value]

    # Create thread for exchange module handle method

    handler = Handler(
        module=modules[method.exchange],
        rabbitmq=rabbitmq,
        channel=channel,
        method=method,
        properties=properties,
        lock=lock,
        json_body=json_body,
    )

    thread = threading.Thread(
        target=handler,
    )

    thread.start()

    global threads

    threads.append(thread)


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

        # Import exchange modules

        modules = {}

        for exchange_name in rabbitmq.exchanges:
            modules[exchange_name] = importlib.import_module(
                f"cyberfusion.RabbitMQHandlers.exchanges.{exchange_name}"
            )

        # Set empty lock list for each exchange

        for exchange_name in rabbitmq.exchanges:
            locks[exchange_name] = {}

        # Configure consuming

        rabbitmq.channel.basic_consume(
            queue=rabbitmq.config["virtual_hosts"][rabbitmq.virtual_host_name][
                "queue"
            ],
            on_message_callback=lambda channel, method, properties, body: callback(
                rabbitmq,
                channel,
                method,
                properties,
                modules,
                body.decode("utf-8"),
            ),
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
