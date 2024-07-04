"""Program to consume RabbitMQ messages."""

import inspect
import json
import logging
import signal
import sys
import threading
from types import ModuleType
from typing import Dict, List, Optional

import pika
import sdnotify
from cryptography.fernet import Fernet
from systemd.journal import JournalHandler

from cyberfusion.Common import get_hostname
from cyberfusion.RabbitMQConsumer.contracts import RPCRequestBase
from cyberfusion.RabbitMQConsumer.handler import Handler
from cyberfusion.RabbitMQConsumer.RabbitMQ import FERNET_TOKEN_KEYS, RabbitMQ
from cyberfusion.RabbitMQConsumer.utilities import _prefix_message

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
            "Waiting for thread '%s' to finish before exiting...", thread.name
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

    # Log message

    logger.info(
        _prefix_message(
            method.exchange,
            "Received RPC request. Body: '%s'",
        ),
        body,
    )

    # Decrypt message

    payload = {}

    for k, v in json.loads(body).items():
        if k not in FERNET_TOKEN_KEYS:
            payload[k] = v

            continue

        if not rabbitmq.fernet_key:
            raise Exception("Fernet encrypted message requires Fernet key")

        payload[k] = Fernet(rabbitmq.fernet_key).decrypt(v.encode()).decode()

    # Get Pydantic request model based on handler type annotation

    request_class = (
        inspect.signature(modules[method.exchange].Handler.__call__)
        .parameters["request"]
        .annotation
    )

    # Cast JSON body to Pydantic model

    # TODO handle errors without crashing
    request: RPCRequestBase = request_class(**payload)

    # Add value of lock attribute to locks
    #
    # This prevents conflicts. I.e. the same handler operating on the same object
    # (identified by the lock attribute) simultaneously.
    #
    # If the lock attribute is None, the handle() method for the exchange may
    # not run simultaneously in any case, regardless of the object it operates
    # on.

    global locks

    lock_key = modules[method.exchange].Handler().lock_attribute

    if lock_key is not None:
        lock_value = getattr(request, lock_key)
    else:
        # If value is None, use a dummy value so the logic still works

        lock_value = "dummy"

    if lock_value not in locks[method.exchange]:
        locks[method.exchange][lock_value] = threading.Lock()

    lock = locks[method.exchange][lock_value]

    # Run handler

    handler = Handler(
        module=modules[method.exchange],
        rabbitmq=rabbitmq,
        channel=channel,
        method=method,
        properties=properties,
        lock=lock,
        request=request,
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
            try:
                modules[exchange_name] = importlib.import_module(
                    f"cyberfusion.RabbitMQHandlers.exchanges.{exchange_name}"
                )
            except ModuleNotFoundError:
                logger.warning(
                    "Module for exchange '%s' could not be found, skipping...",
                    exchange_name,
                )

                continue

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
