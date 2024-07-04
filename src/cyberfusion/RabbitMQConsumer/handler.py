"""Classes for handling RabbitMQ messages."""

import functools
import json
import logging
import threading
from typing import Any

import pika

from cyberfusion.RabbitMQConsumer.contracts import (
    RPCRequestBase,
    RPCResponseBase,
)
from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ
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
        request: RPCRequestBase,
    ):
        """Set attributes."""
        self.module = module
        self.rabbitmq = rabbitmq
        self.channel = channel
        self.method = method
        self.properties = properties
        self.lock = lock
        self.request = request

    def __call__(self) -> None:
        """Handle message."""
        self._acquire_lock()

        try:
            result = self.module.Handler()(self.request)

            if not isinstance(result, RPCResponseBase):
                raise ValueError("RPC response must be of type RPCResponse")

            dict_ = result.dict()

            logger.info(
                _prefix_message(
                    self.method.exchange,
                    "Sending RPC response. Body: '%s'",
                ),
                dict_,
            )

            self._publish(body=dict_)
        except Exception:
            # Uncaught exceptions raised in threads are not propagated, so they
            # are not visible to the main thread. Therefore, any unhandled exception
            # is logged here.

            logger.exception("Unhandled exception occurred")

            # Send RPC response

            self._publish(
                body=RPCResponseBase(
                    success=False,
                    message="An unexpected error occurred",
                    data=None,
                ).dict()
            )
        finally:
            # Release the lock before acknowledgement. If acknowledgement fails and
            # the message is redelivered, the lock is already released, preventing
            # race conditions.

            self._release_lock()
            self._acknowledge()

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
