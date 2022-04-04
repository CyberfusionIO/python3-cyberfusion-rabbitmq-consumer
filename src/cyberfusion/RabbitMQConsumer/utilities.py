"""Generic utilities."""

import functools
import json
import logging
import threading
from typing import Optional

import pika

from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ

logger = logging.getLogger(__name__)


def _prefix_message(prefix: Optional[str], result: str) -> str:
    """Add user-specified prefix to message."""
    if prefix:
        return f"[{prefix}] {result}"

    return result


def prepare_handle(lock: threading.Lock, *, exchange_name: str) -> None:
    """Prepare for running exchange handle method."""

    # Acquire lock

    logger.info(_prefix_message(exchange_name, "Acquiring lock..."))

    lock.acquire()

    logger.info(_prefix_message(exchange_name, "Acquired lock"))


def finish_handle(
    rabbitmq: RabbitMQ,
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    lock: threading.Lock,
    *,
    body: dict,
    exchange_name: str,
) -> None:
    """Finish running exchange handle method."""

    # Release lock

    logger.info(_prefix_message(exchange_name, "Releasing lock..."))

    lock.release()

    logger.info(_prefix_message(exchange_name, "Released lock"))

    # Publish result

    rabbitmq.connection.add_callback_threadsafe(
        functools.partial(
            channel.basic_publish,
            exchange=method.exchange,
            routing_key=properties.reply_to,
            properties=pika.BasicProperties(
                correlation_id=properties.correlation_id,
                content_type="application/json",
            ),
            body=json.dumps(body),
        )
    )

    # Acknowledge message after processing

    rabbitmq.connection.add_callback_threadsafe(
        functools.partial(channel.basic_ack, delivery_tag=method.delivery_tag)
    )
