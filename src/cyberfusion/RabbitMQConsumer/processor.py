"""Classes for processing RPC requests."""

from typing import List
import functools
import logging
import threading
import traceback
from typing import Any, Optional

import pika
from pydantic import ValidationError

from cyberfusion.RabbitMQConsumer.contracts import (
    RPCRequestBase,
    RPCResponseBase,
)
from cyberfusion.RabbitMQConsumer.log_server_client import LogServerClient
from cyberfusion.RabbitMQConsumer.models import (
    RPCResponseDataValidationErrors,
    RPCResponseDataValidationError,
)
from cyberfusion.RabbitMQConsumer.rabbitmq import RabbitMQ
from cyberfusion.RabbitMQConsumer.types import Locks
from cyberfusion.RabbitMQConsumer.utilities import (
    get_exchange_handler_class_request_model,
    get_exchange_handler_class_response_model,
)

logger = logging.getLogger(__name__)

MESSAGE_UNEXPECTED_ERROR = "An unexpected error occurred"

MESSAGE_VALIDATION_ERROR = "Request validation failed"

RESPONSE_UNEXPECTED_ERROR = RPCResponseBase(
    success=False,
    message=MESSAGE_UNEXPECTED_ERROR,
    data=None,
)


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
        log_server_client: Optional[LogServerClient],
        decrypted_values: List[str],
    ) -> None:
        """Set attributes."""
        self.module = module
        self.rabbitmq = rabbitmq
        self.channel = channel
        self.method = method
        self.properties = properties
        self.payload = payload
        self.log_server_client = log_server_client
        self.decrypted_values = decrypted_values

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
        request_class = get_exchange_handler_class_request_model(self.handler)

        try:
            return request_class(**self.payload)
        except ValidationError as e:
            custom_errors = []

            pydantic_errors = e.errors()

            for pydantic_error in pydantic_errors:
                custom_errors.append(
                    RPCResponseDataValidationError(
                        location=pydantic_error["loc"],
                        message=pydantic_error["msg"],
                        type=pydantic_error["type"],
                    )
                )

            body = RPCResponseBase(
                success=False,
                message=MESSAGE_VALIDATION_ERROR,
                data=RPCResponseDataValidationErrors(errors=custom_errors),
            )

            self._publish(body=body)

            raise

    def __call__(self) -> None:
        """Process message."""
        self._acquire_lock()

        try:
            if self.log_server_client:
                logger.info(
                    self._prefix_message("Shipping RPC request to log server...")
                )

                self.log_server_client.log_rpc_request(
                    correlation_id=self.properties.correlation_id,
                    request_payload=self.request.model_dump(),
                    decrypted_values=self.decrypted_values,
                    exchange_name=self.method.exchange,
                )

                logger.info(self._prefix_message("Shipped RPC request to log server"))

            if not self.rabbitmq.config.mock:
                logger.info(self._prefix_message("Calling RPC handler..."))

                result = self.handler(self.request)

                logger.info(self._prefix_message("Called RPC handler"))
            else:
                logger.info(self._prefix_message("Mocking RPC response..."))

                response_model = get_exchange_handler_class_response_model(self.handler)

                try:
                    from polyfactory.factories.pydantic_factory import ModelFactory
                except ImportError:
                    raise RuntimeError(
                        "Polyfactory not installed, can't mock RPC response"
                    )

                factory = ModelFactory.create_factory(response_model)

                result = factory.build()

                logger.info(self._prefix_message("Mocked RPC response"))

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
                body=RESPONSE_UNEXPECTED_ERROR,
                traceback=traceback.format_exc(),
            )
        finally:
            # Release the lock before acknowledgement. If acknowledgement fails and
            # the message is redelivered, the lock is already released, preventing
            # race conditions.

            self._release_lock()
            self._acknowledge()

    def _prefix_message(self, message: str) -> str:
        """Get prefix for logs about the RPC request being processed."""
        return f"[{self.method.exchange}] [{self.properties.correlation_id}] {message}"

    def _acquire_lock(self) -> None:
        """Acquire lock."""
        logger.info(self._prefix_message("Acquiring lock..."))

        self.lock.acquire()

        logger.info(self._prefix_message("Acquired lock"))

    def _release_lock(self) -> None:
        """Release lock."""
        logger.info(self._prefix_message("Releasing lock..."))

        self.lock.release()

        logger.info(self._prefix_message("Released lock"))

    def _publish(
        self, *, body: RPCResponseBase, traceback: Optional[str] = None
    ) -> None:
        """Publish result."""
        json_body = body.model_dump_json()

        logger.info(
            self._prefix_message(
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

        if self.log_server_client:
            logger.info(self._prefix_message("Shipping RPC response to log server..."))

            self.log_server_client.log_rpc_response(
                correlation_id=self.properties.correlation_id,
                response_payload=body.model_dump(),
                traceback=traceback,
            )

            logger.info(self._prefix_message("Shipped RPC response to log server"))

    def _acknowledge(self) -> None:
        """Acknowledge message."""
        self.rabbitmq.connection.add_callback_threadsafe(
            functools.partial(
                self.channel.basic_ack, delivery_tag=self.method.delivery_tag
            )
        )
