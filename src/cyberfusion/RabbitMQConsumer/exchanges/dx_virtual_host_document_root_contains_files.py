"""Methods for exchange."""

import json
from pathlib import Path

import pika

from cyberfusion.ClusterSupport import ClusterSupport
from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ

SUFFIX_FILE_PHP = "php"
SUFFIXES_FILE = [SUFFIX_FILE_PHP]


def handle(
    rabbitmq: RabbitMQ,
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    json_body: dict,
) -> None:
    """Handle message."""  # noqa: D202

    # Set variables

    file_suffix = json_body["file_suffix"]

    # Get support object

    support = ClusterSupport()

    # Get API object

    obj = support.get_virtual_hosts(id_=json_body["virtual_host_id"])[0]

    # Get document root contains files

    print(
        f"Getting document root contains files with suffix '{file_suffix}' for virtual host with ID '{obj.id}' (document root: '{obj.document_root}')"  # noqa: E501
    )

    # Check file suffix allowed. We have this to discourage
    # using this a lot because of possible blocking I/O

    if file_suffix not in SUFFIXES_FILE:
        print(
            f"Not getting document root contains files with suffix '{file_suffix}' for virtual host with ID '{obj.id}' (document root: '{obj.document_root}'): file suffix not allowed"  # noqa: E501
        )

        return

    try:
        # Assume document root does not contain files, let loop prove otherwise  # noqa: E501

        document_root_contains_files = False

        # Loop through files in document root

        for _path in Path(obj.document_root).rglob(f"*.{file_suffix}"):
            # If we reach this code, we found file. Set to true and stop loop  # noqa: E501

            document_root_contains_files = True

            break

        print(
            f"Success getting document root contains files with suffix '{file_suffix}' for virtual host with ID '{obj.id}' (document root: '{obj.document_root}'). Result: {document_root_contains_files}"  # noqa: E501
        )
    except Exception as e:
        # If action fails, don't crash entire program

        print(
            f"Error getting document root contains files with suffix '{file_suffix}' for virtual host with ID '{obj.id}' (document root: '{obj.document_root}'): {e}"  # noqa: E501
        )

    # Publish message

    channel.basic_publish(
        exchange=method.exchange,
        routing_key=properties.reply_to,
        properties=pika.BasicProperties(
            correlation_id=properties.correlation_id,
        ),
        body=json.dumps(
            {
                "document_root_contains_files": document_root_contains_files  # noqa: E501
            }
        ),
    )
