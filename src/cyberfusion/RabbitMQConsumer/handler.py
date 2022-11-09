"""Classes for handling RabbitMQ messages."""

import functools
import json
import logging
import threading
from typing import Any

import pika
from cryptography.fernet import Fernet

from cyberfusion.RabbitMQConsumer.RabbitMQ import FERNET_TOKEN_KEYS, RabbitMQ
from cyberfusion.RabbitMQConsumer.utilities import _prefix_message

logger = logging.getLogger(__name__)


class Handler:
    """Class to handle RPC calls."""

    def __init__(
        self,
        *,
        module: Any,
        rabbitmq: RabbitMQ,
        channel: pika.adapters.blocking_connection.BlockingChannel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        lock: threading.Lock,
        json_body: dict,
    ):
        """Set attributes."""
        self.module = module
        self.rabbitmq = rabbitmq
        self.channel = channel
        self.method = method
        self.properties = properties
        self.lock = lock
        self._json_body = json_body

    @property
    def json_body(self) -> dict:
        """Get JSON body with decrypted Fernet tokens."""
        json_body = {}

        for k, v in self._json_body.items():
            if k in FERNET_TOKEN_KEYS:
                if not self.rabbitmq.fernet_key:
                    raise Exception(
                        "Fernet encrypted message requires Fernet key"
                    )

                json_body[k] = (
                    Fernet(self.rabbitmq.fernet_key)
                    .decrypt(v.encode())
                    .decode()
                )
            else:
                json_body[k] = v

        return json_body

    def __call__(self) -> None:
        """Handle message."""
        try:
            self._acquire_lock()

            result = self.module.handle(
                exchange_name=self.method.exchange,
                virtual_host_name=self.rabbitmq.virtual_host_name,
                rabbitmq_config=self.rabbitmq.config["virtual_hosts"],
                json_body=self.json_body,
            )

            self._publish(body=result)

            # Release the lock before acknowledgement. If acknowledgement fails and
            # the message is redelivered, the lock is already released, preventing
            # race conditions.

            self._release_lock()
            self._acknowledge()
        except Exception:
            # Uncaught exceptions raised in threads are not propagated, so they
            # are not visible to the main thread. Therefore, any unhandled exception
            # is logged here.

            logger.exception("Unhandled exception occurred")

    def _acquire_lock(self) -> None:
        """Acquire lock."""
        logger.info(_prefix_message(self.method.exchange, "Acquiring lock..."))

        self.lock.acquire()

        logger.info(_prefix_message(self.method.exchange, "Acquired lock"))

    def _release_lock(self) -> None:
        """Release lock."""
        logger.info(_prefix_message(self.method.exchange, "Releasing lock..."))

        self.lock.release()

        logger.info(_prefix_message(self.method.exchange, "Released lock"))

    def _publish(self, *, body: dict) -> None:
        """Publish result."""
        self.rabbitmq.connection.add_callback_threadsafe(
            functools.partial(
                self.channel.basic_publish,
                exchange=self.method.exchange,
                routing_key=self.properties.reply_to,
                properties=pika.BasicProperties(
                    correlation_id=self.properties.correlation_id,
                    content_type="application/json",
                ),
                body=json.dumps(body),
            )
        )

    def _acknowledge(self) -> None:
        """Acknowledge message."""
        self.rabbitmq.connection.add_callback_threadsafe(
            functools.partial(
                self.channel.basic_ack, delivery_tag=self.method.delivery_tag
            )
        )
