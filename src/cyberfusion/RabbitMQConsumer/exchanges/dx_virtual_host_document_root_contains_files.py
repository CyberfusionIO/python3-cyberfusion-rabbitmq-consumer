"""Methods for exchange."""

import json
import logging
from pathlib import Path

import pika

from cyberfusion.RabbitMQConsumer.exceptions.dx_virtual_host_document_root_contains_files import (
    VirtualHostDocumentRootContainsFilesError,
)
from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ
from cyberfusion.RabbitMQConsumer.utilities import _prefix_message

logger = logging.getLogger(__name__)


def handle(
    rabbitmq: RabbitMQ,
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    json_body: dict,
) -> None:
    """Handle message."""
    try:
        # Set variables

        document_root = json_body["document_root"]
        file_suffix = json_body["file_suffix"]

        # Set preliminary result

        document_root_contains_files = None

        # Get document root contains files

        logger.info(
            _prefix_message(
                document_root,
                "Getting virtual host document root contains files",
            )
        )

        try:
            document_root_contains_files = bool(
                Path(document_root).rglob(f"*.{file_suffix}")
            )
        except Exception:
            raise VirtualHostDocumentRootContainsFilesError

    except VirtualHostDocumentRootContainsFilesError as e:
        # Log exception

        logger.exception(_prefix_message(document_root, e.result))

    # Publish message

    channel.basic_publish(
        exchange=method.exchange,
        routing_key=properties.reply_to,
        properties=pika.BasicProperties(
            correlation_id=properties.correlation_id,
        ),
        body=json.dumps(
            {"document_root_contains_files": document_root_contains_files}
        ),
    )
