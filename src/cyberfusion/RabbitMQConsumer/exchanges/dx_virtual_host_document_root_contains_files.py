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
    """Handle message.

    data contains:
        - document_root_contains_files (bool)
    """
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
            for _ in Path(document_root).rglob(f"*.{file_suffix}"):
                # If this code is reached, the file exists. As we're iterating
                # over a generator, we can't use 'bool(Path(...).rglob(...))'

                document_root_contains_files = True

                break

            # If the value is unchanged, there are no files

            if document_root_contains_files is None:
                document_root_contains_files = False

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
            {
                "data": {
                    "document_root_contains_files": document_root_contains_files
                }
            }
        ),
    )
