"""Program to consume RPC requests.

Usage:
  rabbitmq-consumer --virtual-host-name=<virtual-host-name> --config-file-path=<config-file-path>

Options:
  -h --help                                      Show this screen.
  --virtual-host-name=<virtual-host-name>        Name of virtual host. Must be in config.
  --config-file-path=<config-file-path>          Path to config file.
"""

import json
import logging
import os
import signal
import sys
import threading
from types import ModuleType
from typing import Dict, List, Optional

import pika
import sdnotify
from cryptography.fernet import Fernet
from docopt import docopt
from schema import And, Schema

from cyberfusion.RabbitMQConsumer.config import Config
from cyberfusion.RabbitMQConsumer.processor import Processor
from cyberfusion.RabbitMQConsumer.rabbitmq import FERNET_TOKEN_KEYS, RabbitMQ
from cyberfusion.RabbitMQConsumer.types import Locks
from cyberfusion.RabbitMQConsumer.utilities import (
    _prefix_message,
    import_exchange_handler_modules,
)

# Configure logging

root_logger = logging.getLogger()
root_logger.propagate = False
root_logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    "[%(threadName)s] [%(levelname)s] %(name)s: %(message)s"
)
handler.setFormatter(formatter)

root_logger.addHandler(handler)

logger = logging.getLogger(__name__)

# Set default variables

locks = Locks({})
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
    """Pass RabbitMQ message to processor."""

    # Log message

    logger.info(
        _prefix_message(
            method.exchange,
            "Received RPC request (%s). Body: '%s'",
        ),
        properties.correlation_id,
        body,
    )

    # Decrypt request

    payload = {}

    for k, v in json.loads(body).items():
        if k not in FERNET_TOKEN_KEYS:
            payload[k] = v

            continue

        if not rabbitmq.fernet_key:
            raise Exception("Fernet encrypted message requires Fernet key")

        payload[k] = Fernet(rabbitmq.fernet_key).decrypt(v.encode()).decode()

    # Run processor

    try:
        processor = Processor(
            module=modules[method.exchange],
            rabbitmq=rabbitmq,
            channel=channel,
            method=method,
            properties=properties,
            locks=locks,
            payload=payload,
        )
    except Exception:
        logger.exception("Exception initialising processor")

        return

    thread = threading.Thread(
        target=processor,
    )

    thread.start()

    global threads

    threads.append(thread)


def main() -> None:
    """Start RabbitMQ consumer."""
    args = docopt(__doc__)

    schema = Schema(
        {
            "--virtual-host-name": str,
            "--config-file-path": And(
                os.path.exists, error="Config file doesn't exist"
            ),
        }
    )

    args = schema.validate(args)

    # Start RabbitMQ consumer

    rabbitmq: Optional[RabbitMQ] = None

    try:
        # Get objects

        config = Config(args["--config-file-path"])
        rabbitmq = RabbitMQ(args["--virtual-host-name"], config)

        # Import exchange modules

        modules = import_exchange_handler_modules(
            rabbitmq.virtual_host_config.exchanges
        )

        # Configure consuming

        rabbitmq.channel.basic_consume(
            queue=rabbitmq.virtual_host_config.queue,
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
