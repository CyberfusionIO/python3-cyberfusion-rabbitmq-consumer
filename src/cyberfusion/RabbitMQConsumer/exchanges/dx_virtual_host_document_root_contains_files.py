"""Methods for exchange."""

import json
import logging
from pathlib import Path

import pika

from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ

SUFFIX_FILE_PHP = "php"
SUFFIXES_FILE = [SUFFIX_FILE_PHP]

logger = logging.getLogger(__name__)


def handle(
    rabbitmq: RabbitMQ,
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    json_body: dict,
) -> None:
    """Handle message."""  # noqa: D202

    # Set variables

    document_root = json_body["document_root"]
    file_suffix = json_body["file_suffix"]

    # Get document root contains files

    logger.info(
        f"Getting document root contains files with suffix '{file_suffix}' for virtual host (document root: '{document_root}')"
    )

    # Check file suffix allowed. We have this to discourage
    # using this a lot because of possible blocking I/O

    if file_suffix not in SUFFIXES_FILE:
        logger.info(
            f"Not getting document root contains files with suffix '{file_suffix}' for virtual host (document root: '{document_root}'): file suffix not allowed"
        )

        return

    try:
        # Assume document root does not contain files, let loop prove otherwise

        document_root_contains_files = False

        # Loop through files in document root

        for _path in Path(document_root).rglob(f"*.{file_suffix}"):
            # If we reach this code, we found file. Set to true and stop loop

            document_root_contains_files = True

            break

        logger.info(
            f"Success getting document root contains files with suffix '{file_suffix}' for virtual host (document root: '{document_root}'). Result: {document_root_contains_files}"
        )
    except Exception:
        logger.exception(
            f"Error getting document root contains files with suffix '{file_suffix}' for virtual host (document root: '{document_root}')"
        )

        return

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
