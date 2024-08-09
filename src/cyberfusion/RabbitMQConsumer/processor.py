"""Classes for processing RPC requests."""

import functools
import inspect
import logging
import threading
from typing import Any

import pika
from pydantic import ValidationError

from cyberfusion.RabbitMQConsumer.contracts import (
    RPCRequestBase,
    RPCResponseBase,
)
from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ
from cyberfusion.RabbitMQConsumer.types import Locks
from cyberfusion.RabbitMQConsumer.utilities import _prefix_message

logger = logging.getLogger(__name__)


class Processor:
    """Class to process RPC requests, by passing to handler."""

    def __init__(
        self,
        *,
        module: Any,
        rabbitmq: RabbitMQ,
        channel: pika.adapters.blocking_connection.BlockingChannel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        locks: Locks,
        payload: dict,
    ):
        """Set attributes."""
        self.module = module
        self.rabbitmq = rabbitmq
        self.channel = channel
        self.method = method
        self.properties = properties
        self.payload = payload
        self.handler = module.Handler()

        # Add value of lock attribute to locks
        #
        # This prevents conflicts. I.e. the same handler operating on the same object
        # (identified by the lock attribute) simultaneously.
        #
        # If the lock attribute is None, the handler for the exchange not run
        # simultaneously in any case, regardless of the object it operates on
        # (by using the key 'dummy', which would apply to all messages).

        lock_key = self.handler.lock_attribute

        if lock_key is not None:
            lock_value = getattr(self.request, lock_key)
        else:
            lock_value = "dummy"

        if method.exchange not in locks:
            locks[method.exchange] = {}

        if lock_value not in locks[method.exchange]:
            locks[method.exchange][lock_value] = threading.Lock()

        self.lock = locks[method.exchange][lock_value]

    @property
    def request(self) -> RPCRequestBase:
        """Cast JSON body to Pydantic model."""
        request_class = (
            inspect.signature(self.handler.__call__)
            .parameters["request"]
            .annotation
        )

        try:
            return request_class(**self.payload)
        except ValidationError:
            self._publish(
                body=RPCResponseBase(
                    success=False,
                    message="An unexpected error occurred",
                    data=None,
                )
            )

            raise

    def __call__(self) -> None:
        """Process message."""
        self._acquire_lock()

        try:
            result = self.handler(self.request)

            if not isinstance(result, RPCResponseBase):
                raise ValueError("RPC response must be of type RPCResponse")

            self._publish(body=result)
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
                )
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

    def _publish(self, *, body: RPCResponseBase) -> None:
        """Publish result."""
        json_body = body.json()

        logger.info(
            _prefix_message(
                self.method.exchange,
                "Sending RPC response. Body: '%s'",
            ),
            json_body,
        )

        self.rabbitmq.connection.add_callback_threadsafe(
            functools.partial(
                self.channel.basic_publish,
                exchange=self.method.exchange,
                routing_key=self.properties.reply_to,
                properties=pika.BasicProperties(
                    correlation_id=self.properties.correlation_id,
                    content_type="application/json",
                ),
                body=json_body,
            )
        )

    def _acknowledge(self) -> None:
        """Acknowledge message."""
        self.rabbitmq.connection.add_callback_threadsafe(
            functools.partial(
                self.channel.basic_ack, delivery_tag=self.method.delivery_tag
            )
        )